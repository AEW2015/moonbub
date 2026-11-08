//! Restricted local USB commands. No arbitrary address/value or network ABI.
//! Worker is spawned empty; the small permit is sent only after successful spawn.
//! Core is constructed on worker stack, never on the existing USB task stack.
use crate::core_coordinator::CONTROL;
use crate::device::{
    drivers::fpga::{FpgaSpiWordSize, SpiCommand, MAX_SPI_READ_CLOCK},
    Device,
};
use crate::key_diag_core::*;
use std::sync::mpsc;
static REQUESTS: crate::diag_dispatch::Requests = crate::diag_dispatch::Requests::new();
pub const WORKER_STACK_BYTES: usize = 6144;
fn now() -> u64 {
    unsafe { esp_idf_svc::sys::esp_timer_get_time() as u64 }
}
#[inline(never)]
pub fn command(key: u8) {
    match key {
        b'a' => {
            REQUESTS.stop();
        }
        b'b' => {
            REQUESTS.status();
            let quarantined = { CONTROL.lock().unwrap().quarantined() };
            if quarantined {
                log::info!(target:"diag","USB_D24 v=2 p=key state=quarantined recovery=operator_restart");
            } else if !REQUESTS.busy() {
                log::info!(target:"diag","USB_D24 v=2 p=key state=inactive");
            }
        }
        b'y' => {
            REQUESTS.clear();
        }
        b'd' => start(),
        _ => {}
    }
}
struct SdkLauncher;
impl crate::diag_dispatch::Launcher for SdkLauncher {
    type Job = crate::core_admission::DiagnosticPermit;
    type Sender = mpsc::SyncSender<Self::Job>;
    fn reserve(&mut self) -> Result<Self::Job, ()> {
        CONTROL.lock().unwrap().diagnostic().map_err(|_| ())
    }
    fn spawn_empty(&mut self) -> Result<Self::Sender, ()> {
        let (tx, rx) = mpsc::sync_channel(1);
        std::thread::Builder::new()
            .name("KeyDiag".into())
            .stack_size(WORKER_STACK_BYTES)
            .spawn(move || {
                if let Ok(p) = rx.recv() {
                    worker(p)
                }
            })
            .map_err(|_| ())?;
        Ok(tx)
    }
    fn send(&mut self, tx: &Self::Sender, p: Self::Job) -> Result<(), Self::Job> {
        tx.send(p).map_err(|mpsc::SendError(p)| p)
    }
    fn release_unissued(&mut self, p: Self::Job) -> bool {
        CONTROL
            .lock()
            .unwrap()
            .unissued_diagnostic_finished(p)
            .is_ok()
    }
    fn publish(&mut self, tx: Self::Sender) {
        drop(tx);
    }
}
#[inline(never)]
fn start() {
    let result = crate::diag_dispatch::launch(&REQUESTS, &mut SdkLauncher);
    log::info!(target:"diag","USB_D24 v=2 p=key launch={:?}",result);
}
fn transaction(action: Action) -> (Outcome, u32) {
    // Exactly one CSR, no sleep/format/log/control lock inside this scope.
    if let Some(mut d) = Device::try_lock() {
        let epoch = d.fpga.program_epoch();
        let result = match action {
            Action::Read(r) => d
                .fpga
                .read_u32(0xe0000000 + u32::from(r.offset()))
                .map(Outcome::Read),
            Action::Write(c) => d
                .fpga
                .spi_write(
                    Some(MAX_SPI_READ_CLOCK),
                    SpiCommand {
                        word_size: FpgaSpiWordSize::Bits32,
                        byte_swap: false,
                        increment_address: true,
                    },
                    0xe0000000 + u32::from(c.offset()),
                    &c.value().to_be_bytes(),
                )
                .map(|_| Outcome::Written),
        };
        (result.unwrap_or(Outcome::IoError), epoch)
    } else {
        (Outcome::NoLock, 0)
    }
}
#[inline(never)]
fn report(core: &DiagnosticCore) {
    for index in 0..=if core.record().is_some() { 3 } else { 0 } {
        if let Ok(line) = crate::key_diag_pages::page(core, index) {
            log::info!(target:"diag","{}",line.as_str());
        } else {
            log::info!(target:"diag","USB_D24 v=2 p=key state=format_error");
        }
    }
}
/// Samples THIS worker after report returns. Never runs on the USB command
/// task, nor under CONTROL/Device. Watermark units are pinned StackType_t=u8.
#[inline(never)]
fn resource_sample() {
    let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
    let (low, free, largest) = unsafe {
        (
            esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()),
            esp_idf_svc::sys::heap_caps_get_free_size(caps),
            esp_idf_svc::sys::heap_caps_get_largest_free_block(caps),
        )
    };
    if let Ok(line) = crate::key_diag_pages::resource(low, WORKER_STACK_BYTES as u32, free, largest)
    {
        log::info!(target:"diag","{}",line.as_str());
    } else {
        log::info!(target:"diag","USB_D24 v=2 p=key_resource state=format_error");
    }
}
fn worker(p: crate::core_admission::DiagnosticPermit) {
    let deadline = now() + 200000;
    let mut initial_attempts = 0;
    let epoch = loop {
        initial_attempts += 1;
        if let Some(d) = Device::try_lock() {
            break d.fpga.program_epoch();
        }
        if REQUESTS.take_stop() || now() >= deadline || initial_attempts >= 200 {
            let released = {
                CONTROL
                    .lock()
                    .unwrap()
                    .unissued_diagnostic_finished(p)
                    .is_ok()
            };
            if released {
                REQUESTS.finished();
            }
            return;
        }
        std::thread::sleep(std::time::Duration::from_millis(1));
    };
    let mut core = DiagnosticCore::new(p, epoch, now(), Budgets::default());
    let mut previous = core.stage();
    loop {
        if REQUESTS.take_stop() {
            core.request_stop(now());
        }
        if REQUESTS.take_clear() {
            core.request_clear(now());
        }
        if let Some(op) = core.next_operation(now()) {
            let (out, observed_epoch) = transaction(op.action());
            // NoLock did not observe a hardware epoch; retain the last known epoch.
            core.complete(
                op,
                out,
                if matches!(out, Outcome::NoLock) {
                    epoch
                } else {
                    observed_epoch
                },
                now(),
            );
        }
        if REQUESTS.take_status() || core.stage() != previous {
            report(&core);
            resource_sample();
            previous = core.stage();
        }
        if matches!(core.stage(), Stage::Cleared | Stage::Refused) {
            match core.into_exit() {
                Ok((p, proof, _)) => {
                    let released = {
                        CONTROL
                            .lock()
                            .unwrap()
                            .diagnostic_finished(p, proof)
                            .is_ok()
                    };
                    if !released {
                        // Coordinator retains both failed token and proof; never advertise exit.
                        loop {
                            if REQUESTS.take_status() {
                                log::info!(target:"diag","USB_D24 v=2 p=key state=quarantined recovery=operator_restart");
                            }
                            std::thread::sleep(std::time::Duration::from_millis(20));
                        }
                    }
                    break;
                }
                Err(c) => core = c,
            }
        }
        // Quarantine retains Core/permit and reservation. Only an owned STOP retry
        // can recover; unowned boot state requires operator restart. No fake proof.
        std::thread::sleep(std::time::Duration::from_millis(1));
    }
    REQUESTS.finished();
}

#[cfg(test)]
pub fn test_running() -> bool {
    REQUESTS.busy()
}
