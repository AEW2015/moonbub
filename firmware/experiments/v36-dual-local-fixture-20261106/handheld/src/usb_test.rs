//! Temporary, physically attached USB serial controls for bring-up.
use crate::{device::{drivers::fpga, Device}, streaming, ui};
use std::time::Duration;

pub fn start() {
    std::thread::Builder::new().name("UsbTest".into()).stack_size(6144)
        .spawn(|| { let mut margin = crate::margin_usb::Driver::new(); loop { margin.tick(); crate::cpl1_usb::tick();
            let mut byte = [0u8; 1];
            let mut count = 0usize;
            let rc = unsafe { esp_idf_svc::sys::tinyusb_cdcacm_read(
                esp_idf_svc::sys::tinyusb_cdcacm_itf_t_TINYUSB_CDC_ACM_0,
                byte.as_mut_ptr(), 1, &mut count) };
            if rc == 0 && count == 1 && !margin.command(byte[0]) { command(byte[0]); }
            std::thread::sleep(Duration::from_millis(20));
        }}).expect("USB test thread");
}

fn command(b: u8) {
    match b {
        b'G' => crate::cu66::local_usb::start(),
        b'Y' => crate::cu66::local_usb::start_direct(),
        b'W' => crate::cu66::usb_probe::start(),
        b'P' => crate::cpl1_usb::command(),
        b'M' | b'F' | b'J' | b'K' => crate::video_trace_usb::command(b),
        b'd'|b'a'|b'b'|b'y'=>crate::key_diag_usb::command(b),
        b'?' => crate::usb_diag::runtime(),
        b'i' | b'j' | b'k' => streaming::start_local_loop(b - b'i' + 1),
        b'e' => streaming::stop_local_loop(),
        b'c' => { ui::send(ui::Message::TestShowStreaming); streaming::connect(String::new()); }
        b'x' => streaming::disconnect(),
        b'v' => ui::send(ui::Message::EnterGame),
        b'm' => ui::send(ui::Message::TestShowStreaming),
        b'l' | b'o' => {
            let enabled = b == b'o';
            match streaming::set_overlap_requested(enabled) {
                Ok(()) => log::info!("USB_TRACE overlap_requested_next_session={} (RAM only)", enabled),
                Err(e) => log::warn!("USB_TRACE overlap_change_failed={}", e),
            }
        }
        b'4' | b'6' | b'8' => {
            let depth = match b { b'4' => 4, b'6' => 16, _ => 32 };
            match streaming::set_queue_depth(depth) {
                Ok(()) => log::info!("USB_TRACE queue_depth_next_session={} (RAM only)", depth),
                Err(e) => log::warn!("USB_TRACE queue_depth_change_failed={}", e),
            }
        }
        b'n' | b'p' => {
            let boosted = b == b'p';
            match streaming::set_consumer_boost(boosted) {
                Ok(()) => log::info!("USB_TRACE consumer_boost_next_session={} (RAM only)", boosted),
                Err(e) => log::warn!("USB_TRACE consumer_boost_change_failed={}", e),
            }
        }
        b'z' | b'Z' => {
            let hz = if b == b'z' { 20_000_000 } else { 40_000_000 };
            match streaming::set_stream_write_hz(hz) {
                Ok(()) => log::info!("USB_TRACE stream_write_max_hz_next_session={} (RAM only; physical clock unmeasured)", hz),
                Err(e) => log::warn!("USB_TRACE stream_write_clock_change_failed={}", e),
            }
        }
        b'q' => match streaming::benchmark_qspi() {
            Ok(()) => log::info!("USB_QSPI result=PASS"),
            Err(e) => log::warn!("USB_QSPI result=FAIL reason={}", e),
        },
        b'r' => match streaming::benchmark_crc() {
            Ok(()) => log::info!("USB_CRC result=PASS"),
            Err(e) => log::warn!("USB_CRC result=FAIL reason={}", e),
        },
        // Snapshot only; hot-path telemetry is bounded and never logged per packet.
        b't' => {
            log::info!("USB_TRACE av status={:?}", streaming::audio::stats());
            streaming::audio::log_diagnostics();
            log::info!("USB_TRACE current_source={} packet_queue_and_frame_trace_source=network_only", streaming::telemetry_source());
            log::info!("USB_TRACE stream_write_max_hz={} idf_cached_calculated_khz={:?} (not a physical clock measurement)",
                streaming::stream_write_hz(), streaming::stream_write_calculated_khz());
            log::info!("USB_TRACE overlap_request_active={:?}", streaming::overlap_status());
            crate::usb_diag::video();
            log_fpga_timing();
        }
        // Software DFU exposes a vendor-only interface on this board, not the
        // mass-storage updater; leave reset commands out of unattended tests.
        b's' => {
            log::info!("USB_TRACE av status={:?}", streaming::audio::stats());
            streaming::audio::log_diagnostics();
            let s = streaming::stats();
            log::info!("USB_TEST status={:?} received={} decoded={} displayed={} dropped={} errors={} credits={} source={}",
                s.status, s.received, s.decoded, s.displayed, s.dropped, s.errors, s.credits, s.source);
            log_fpga_status();
        }
        b'A' | b'B' | b'L' | b'R' | b'U' | b'D' | b'H' => {
            let mut buttons = ui::ButtonMap::default();
            let button = match b { b'A'=>ui::Button::A, b'B'=>ui::Button::B,
                b'L'=>ui::Button::Left, b'R'=>ui::Button::Right,
                b'U'=>ui::Button::Up, b'H'=>ui::Button::Home, _=>ui::Button::Down };
            buttons[button] = true;
            ui::send(ui::Message::Button(buttons));
            std::thread::sleep(Duration::from_millis(100));
            ui::send(ui::Message::Button(ui::ButtonMap::default()));
        }
        _ => {}
    }
}

#[inline(never)]
fn log_fpga_timing() {
    let observation = if let Some(mut d) = Device::try_lock() {
                let base = 0xE000_0000;
                let read = (|| -> anyhow::Result<_> {
                    let capabilities = d.fpga.read_u32(base + 8)?;
                    if capabilities & 4 == 0 { return Ok(None); }
                    // Rebind updates this epoch while holding the same device
                    // lock, so an old visible front frame cannot be attributed
                    // to a new sender solely because its ID was reused.
                    let epoch = streaming::presentation_epoch();
                    let count = d.fpga.read_u32(base + 0x34)?;
                    if count == 0 || !epoch.contains_new_presentation(count) { return Ok(None); }
                    let before = d.fpga.read_u32(base + 0x48)?;
                    let receive = d.fpga.read_u32(base + 0x54)?;
                    let commit_to_decode_complete = d.fpga.read_u32(base + 0x58)?;
                    let present_wait = d.fpga.read_u32(base + 0x5c)?;
                    let total = d.fpga.read_u32(base + 0x60)?;
                    let after = d.fpga.read_u32(base + 0x48)?;
                    let after_count = d.fpga.read_u32(base + 0x34)?;
                    Ok(crate::streaming::overlap::coherent_timing(before, after, count, after_count,
                        receive, commit_to_decode_complete, present_wait, total).map(|timing| (epoch.sequence, timing)))
                })();
        Some(read)
    } else { None };
    // Device guard has been dropped before formatting or USB logging.
    if let Some(read) = observation {
        log::info!("USB_TRACE fpga_epoch_and_cycles_100mhz={:?} (None means unsupported, no current-epoch presentation, or raced)", read);
    } else { log::info!("USB_TRACE fpga_timing=busy"); }
}
#[inline(never)]
fn log_fpga_status() {
    let observation = Device::try_lock().map(|mut d| (
        d.fpga.read_u32(fpga::REG_BUTTON_STATE),
        d.fpga.read_u32(fpga::REG_IRQ_ENABLE),
        d.fpga.read_u32(fpga::REG_IRQ_STATUS),
    ));
    if let Some(x) = observation {
        log::info!("USB_TEST fpga buttons={:?} irq_enable={:?} irq_status={:?}",x.0,x.1,x.2);
    }
    let core = Device::try_lock().and_then(|mut d| {
        if d.fpga.read_u32(0xE000_0000).ok() != Some(0x4D42_5631) { return None; }
        Some((d.fpga.read_u32(0xE000_0010),d.fpga.read_u32(0xE000_002c),
            d.fpga.read_u32(0xE000_0038),d.fpga.read_u32(0xE000_003c),
            d.fpga.read_u32(0xE000_0040),d.fpga.read_u32(0xE000_0044),
            d.fpga.read_u32(0xE000_0050)))
    });
    if let Some(x) = core {
        log::info!("USB_TEST core status={:?} completed={:?} faults={:?} drops={:?} overflow={:?} underruns={:?} transport_overflow={:?}",x.0,x.1,x.2,x.3,x.4,x.5,x.6);
    }
}
