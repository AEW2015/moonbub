//! Explicit attachment to the existing Rev4 tester loaded through JTAG.
//! The legacy framebuffer signature is compatibility detection, not a unique ID.
use crate::device::{drivers::fpga, Device};
use std::sync::TryLockError;
use std::time::{Duration, Instant};

const ATTACH_TIMEOUT: Duration = Duration::from_millis(250);
const NATIVE_ABI: u32 = 0x5344_4432; // "SDD2"
const MAILBOX_BASE: u32 = 0x0110_0000;
const MAILBOX_MAGIC: u32 = 0x4742_4d58; // "GBMX"
const MAILBOX_ABI: u32 = 0x0001_0000;
const MAILBOX_ATTACH_MARKER: u32 = 0x4154_5443; // "ATTC"

fn deadline(start: Instant) -> Result<(), String> {
    if start.elapsed() >= ATTACH_TIMEOUT {
        Err("Native FPGA attach timed out; app was not entered".into())
    } else {
        Ok(())
    }
}

pub fn attach() -> Result<(), String> {
    let started = Instant::now();
    let mut device = loop {
        match Device::get().try_lock() {
            Ok(device) => break device,
            Err(TryLockError::WouldBlock) => {
                deadline(started)?;
                std::thread::sleep(Duration::from_millis(1));
            }
            Err(TryLockError::Poisoned(_)) => return Err("Device lock is poisoned".into()),
        }
    };
    let dimensions = device.fpga.read_u32(fpga::REG_FB_DIM).map_err(|e| e.to_string())?;
    deadline(started)?;
    if dimensions != (800 << 16 | 480) {
        return Err(format!("Load the Rev4 App Tester via JTAG first (framebuffer {:08X})", dimensions));
    }
    let abi = device.fpga.read_u32(fpga::REG_NATIVE_ABI).map_err(|e| e.to_string())?;
    deadline(started)?;
    if abi != NATIVE_ABI {
        return Err(format!("Native FPGA ABI mismatch (expected {NATIVE_ABI:08X}, got {abi:08X})"));
    }
    let mailbox_magic = device.fpga.read_u32(MAILBOX_BASE).map_err(|e| e.to_string())?;
    deadline(started)?;
    let mailbox_abi = device.fpga.read_u32(MAILBOX_BASE + 4).map_err(|e| e.to_string())?;
    deadline(started)?;
    if mailbox_magic != MAILBOX_MAGIC || mailbox_abi != MAILBOX_ABI {
        return Err(format!(
            "Native mailbox mismatch (magic {mailbox_magic:08X}, ABI {mailbox_abi:08X})"
        ));
    }
    // ESP-owned response metadata is undefined until RESP_COMMIT is set.  A
    // marker here gives JTAG automation positive proof that the installed
    // firmware reached the mailbox through the physical QSPI link.
    device.fpga.write_u32(MAILBOX_BASE + 0x24, MAILBOX_ATTACH_MARKER).map_err(|e| e.to_string())?;
    deadline(started)?;
    device.fpga.enable_interrupt(fpga::Irq::Button).map_err(|e| e.to_string())?;
    deadline(started)?;
    device.fpga.write_u32(fpga::REG_CONTROL, 3).map_err(|e| e.to_string())?;
    deadline(started)?;
    log::info!("Attached to Rev4 native tester ABI SDD2; FPGA configuration preserved");
    Ok(())
}

pub fn control(reset: bool, paused: bool) -> Result<(), fpga::Error> {
    let mut device = Device::lock();
    execute_control(reset, paused, |value| device.fpga.write_u32(fpga::REG_CONTROL, value))
}

fn execute_control<E>(reset: bool, paused: bool, mut write: impl FnMut(u32) -> Result<(), E>) -> Result<(), E> {
    if reset {
        write(0)?;
        // Reset crosses into the 50 MHz CPU domain; hold for many clock cycles.
        std::thread::sleep(std::time::Duration::from_millis(1));
    }
    write(if paused { 2 } else { 3 })
}

#[cfg(test)]
mod tests {
    use super::execute_control;
    #[test]
    fn pause_resume_reset_and_bus_failure() {
        let mut writes = Vec::new();
        for (reset, paused) in [(false, true), (false, false), (true, false)] {
            execute_control(reset, paused, |v| { writes.push(v); Ok::<_, ()>(()) }).unwrap();
        }
        assert_eq!(writes, [2, 3, 0, 3]);
        let mut attempts = 0;
        assert!(execute_control(true, false, |_| { attempts += 1; Err(()) }).is_err());
        assert_eq!(attempts, 1);
    }
}
