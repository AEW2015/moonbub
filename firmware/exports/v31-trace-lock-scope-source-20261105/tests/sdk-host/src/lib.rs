#![allow(dead_code)]
#![cfg(test)]
extern crate self as esp_idf_svc;
#[allow(non_snake_case)]
pub mod sys {
    use std::sync::atomic::{AtomicU32, Ordering};
    pub const MALLOC_CAP_INTERNAL: u32 = 1;
    pub const MALLOC_CAP_8BIT: u32 = 2;
    pub static RESOURCE_CALLS: AtomicU32 = AtomicU32::new(0);
    fn worker_only() {
        assert_eq!(std::thread::current().name(), Some("KeyDiag"));
        assert_eq!(crate::core_coordinator::test_control_depth(), 0);
        assert_eq!(crate::device::test_depth(), 0);
        RESOURCE_CALLS.fetch_add(1, Ordering::Relaxed);
    }
    pub unsafe fn uxTaskGetStackHighWaterMark(task: *mut core::ffi::c_void) -> u32 {
        assert!(task.is_null());
        worker_only();
        u32::MAX
    }
    pub unsafe fn heap_caps_get_free_size(caps: u32) -> usize {
        worker_only();
        assert_eq!(caps, 3);
        usize::MAX
    }
    pub unsafe fn heap_caps_get_largest_free_block(caps: u32) -> usize {
        worker_only();
        assert_eq!(caps, 3);
        usize::MAX
    }
    pub unsafe fn esp_timer_get_time() -> i64 {
        static START: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
        START
            .get_or_init(std::time::Instant::now)
            .elapsed()
            .as_micros() as i64
    }
}
struct Capture;
static CAPTURE: Capture = Capture;
static LOGS: std::sync::Mutex<Vec<String>> = std::sync::Mutex::new(Vec::new());
impl log::Log for Capture {
    fn enabled(&self, _: &log::Metadata) -> bool {
        true
    }
    fn log(&self, r: &log::Record) {
        let text = format!("{}", r.args());
        if text.contains("p=key_resource") {
            assert_eq!(std::thread::current().name(), Some("KeyDiag"));
            assert_eq!(core_coordinator::test_control_depth(), 0);
            assert_eq!(device::test_depth(), 0);
            assert!(text.len() + 64 <= 256);
        }
        LOGS.lock().unwrap().push(text);
    }
    fn flush(&self) {}
}
fn install_logger() {
    static INIT: std::sync::Once = std::sync::Once::new();
    INIT.call_once(|| {
        log::set_logger(&CAPTURE).unwrap();
        log::set_max_level(log::LevelFilter::Info);
    });
    LOGS.lock().unwrap().clear();
}

#[path = "../../../handheld/src/core_access.rs"]
pub mod core_access;
#[path = "../../../handheld/src/core_admission.rs"]
pub mod core_admission;
#[path = "../../../handheld/src/core_coordinator.rs"]
pub mod core_coordinator;
#[path = "../../../handheld/src/diag_dispatch.rs"]
pub mod diag_dispatch;
#[path = "../../../handheld/src/diag_pages.rs"]
pub mod diag_pages;
#[path = "../../../handheld/src/key_diag_core.rs"]
pub mod key_diag_core;
#[path = "../../../handheld/src/key_diag_pages.rs"]
pub mod key_diag_pages;
#[path = "../../../handheld/src/key_diag_usb.rs"]
pub mod key_diag_usb;
#[path = "../../../handheld/src/margin.rs"]
pub mod margin;
#[path = "../../../handheld/src/timing.rs"]
pub mod timing;
pub mod streaming {
    #[path = "../../../../handheld/src/streaming/av_session.rs"]
    pub mod av_session;
    #[path = "../../../../handheld/src/streaming/av_wire.rs"]
    pub mod av_wire;
    #[path = "../../../../handheld/src/streaming/protocol.rs"]
    pub mod protocol;
    #[path = "../../../../handheld/src/streaming/telemetry.rs"]
    pub mod telemetry;
}
/// Device fake exercises the exact production core_access callbacks. It is not
/// the ESP driver: target ABI and actual physical exclusion remain review gates.
pub mod device {
    use std::ops::{Deref, DerefMut};
    use std::sync::{Mutex, MutexGuard};
    pub mod drivers {
        pub mod fpga {
            #[derive(Clone, Copy)]
            pub enum FpgaSpiWordSize {
                Bits32,
            }
            pub struct SpiCommand {
                pub word_size: FpgaSpiWordSize,
                pub byte_swap: bool,
                pub increment_address: bool,
            }
            pub const MAX_SPI_READ_CLOCK: u32 = 16000000;
        }
    }
    pub struct Fpga {
        pub magic: u32,
        pub build: u32,
        pub epoch: u32,
        pub pins: u32,
        pub state: u32,
        pub owner: u64,
        pub sequence: u32,
        pub writes: u32,
    }
    impl Fpga {
        pub fn program_epoch(&self) -> u32 {
            self.epoch
        }
        pub fn spi_write(
            &mut self,
            clock: Option<u32>,
            _: drivers::fpga::SpiCommand,
            address: u32,
            bytes: &[u8],
        ) -> anyhow::Result<()> {
            assert_eq!(crate::core_coordinator::test_control_depth(), 0);
            assert_eq!(clock, Some(16000000));
            assert_eq!(address, 0xe0000408);
            assert_eq!(bytes.len(), 4);
            self.writes += 1;
            match u32::from_be_bytes(bytes.try_into().unwrap()) {
                1 => {
                    self.owner += 1;
                    self.sequence = self.sequence.wrapping_add(1);
                    self.state = 0x13;
                }
                2 => self.state = 0x46,
                4 => self.state = 0,
                _ => panic!("arbitrary write"),
            };
            Ok(())
        }
    }
    impl Fpga {
        pub fn read_u32(&mut self, a: u32) -> anyhow::Result<u32> {
            assert_eq!(crate::core_coordinator::test_control_depth(), 0);
            use crate::key_diag_core::*;
            Ok(match a - 0xe0000000 {
                0 => self.magic,
                4 => SCHEMA,
                8 => 0,
                0x184 => self.build,
                0x400 => MAGIC,
                0x404 => SCHEMA,
                0x40c => self.state,
                0x410 => u32::MAX,
                0x414 => SAMPLES,
                0x418 => FIXTURE_BYTES,
                0x41c => 0,
                0x420 => self.owner as u32,
                0x424 => (self.owner >> 32) as u32,
                0x428 => 1,
                0x42c => 0,
                0x430..=0x43c => {
                    if self.state == 0x46 {
                        0
                    } else {
                        TAG[((a - 0xe0000430) / 4) as usize]
                    }
                }
                0x440 => 0,
                0x444 => self.sequence,
                0x448 => FIXTURE_BYTES,
                0x44c => WATCHDOG,
                _ => 0,
            })
        }
    }

    pub struct Device {
        pub fpga: Fpga,
    }
    static DEVICE: Mutex<Device> = Mutex::new(Device {
        fpga: Fpga {
            magic: 0x4d425631,
            build: 0x4d424f50,
            epoch: 0,
            pins: 0,
            state: 0,
            owner: 0,
            sequence: 0,
            writes: 0,
        },
    });
    thread_local! {static DEPTH:std::cell::Cell<u32>=const{std::cell::Cell::new(0)};}
    pub fn test_depth() -> u32 {
        DEPTH.with(|n| n.get())
    }
    pub struct Guard(MutexGuard<'static, Device>);
    impl Drop for Guard {
        fn drop(&mut self) {
            DEPTH.with(|n| n.set(n.get() - 1));
        }
    }
    impl Deref for Guard {
        type Target = Device;
        fn deref(&self) -> &Device {
            &self.0
        }
    }
    impl DerefMut for Guard {
        fn deref_mut(&mut self) -> &mut Device {
            &mut self.0
        }
    }
    impl Device {
        pub fn try_lock() -> Option<Guard> {
            assert_eq!(crate::core_coordinator::test_control_depth(), 0);
            DEVICE.try_lock().ok().map(|g| {
                DEPTH.with(|n| n.set(n.get() + 1));
                Guard(g)
            })
        }
        pub fn lock() -> Guard {
            assert_eq!(
                crate::core_coordinator::test_control_depth(),
                0,
                "CONTROL held while Device requested"
            );
            let g = DEVICE.lock().unwrap();
            DEPTH.with(|n| n.set(n.get() + 1));
            Guard(g)
        }
    }
}
#[cfg(test)]
mod adapter_tests {
    use super::*;
    use core_admission::*;
    use core_coordinator::*;
    use diag_dispatch::*;
    fn reset() {
        *CONTROL.lock().unwrap() = Coordinator::new();
        let mut d = device::Device::lock();
        d.fpga.magic = 0x4d425631;
        d.fpga.build = 0x4d424f50;
        d.fpga.pins = 0;
        d.fpga.epoch = 0;
        d.fpga.state = 0;
        d.fpga.owner = 0;
        d.fpga.sequence = 0;
        d.fpga.writes = 0;
    }
    /// Same caller boundary as Boot / CURRENT / receiver call sites: authorization
    /// enters while Device is held, before epoch/pin callbacks, with CONTROL free.
    fn driver(p: &mut ProgramPermit, fail: bool) -> Result<(), String> {
        let authorization = p.authorize_call().map_err(|e| format!("{e:?}"))?;
        let mut d = device::Device::lock();
        assert_eq!(crate::core_coordinator::test_control_depth(), 0);
        let call = authorization.begin().map_err(|e| format!("{e:?}"))?;
        d.fpga.epoch += 1;
        d.fpga.pins += 1;
        if fail {
            return Err("physical failure".into());
        }
        call.succeeded();
        Ok(())
    }
    #[test]
    fn all_three_program_paths_validate_before_side_effects() {
        for site in ["boot", "current", "receiver"] {
            reset();
            let receiver = site == "receiver";
            if receiver {
                let mut c = CONTROL.lock().unwrap();
                c.receiver_request().unwrap();
                c.source_dequeued();
                c.receiver_active().unwrap();
            }
            core_access::program(receiver, false, |p| driver(p, false)).unwrap();
            assert_eq!(device::Device::lock().fpga.pins, 1);
            assert!(!CONTROL.lock().unwrap().admission.program_reserved());
        }
    }
    #[test]
    fn busy_never_invokes_queued_program_callback() {
        reset();
        let _diag = CONTROL.lock().unwrap().diagnostic().unwrap();
        let mut called = false;
        assert!(core_access::program(false, false, |_| {
            called = true;
            Ok(())
        })
        .is_err());
        assert!(!called);
        assert_eq!(device::Device::lock().fpga.epoch, 0);
    }
    #[test]
    fn av_start_before_program_excludes_pins_and_epoch() {
        reset();
        let mut c = CONTROL.lock().unwrap();
        c.receiver_request().unwrap();
        c.av_admit().unwrap();
        drop(c);
        assert!(core_access::program(true, false, |p| driver(p, false)).is_err());
        assert_eq!(device::Device::lock().fpga.pins, 0);
    }
    #[test]
    fn failed_driver_and_failed_post_init_retain_exclusivity() {
        for physical in [false, true] {
            reset();
            assert!(core_access::program(false, false, |p| {
                driver(p, physical)?;
                Err::<(), _>("post-init failure".into())
            })
            .is_err());
            let mut c = CONTROL.lock().unwrap();
            assert!(c.quarantined());
            assert!(c.admission.program_reserved());
            assert!(c.diagnostic().is_err());
        }
    }
    #[test]
    fn pre_sideeffect_file_or_scratch_failure_is_clean() {
        reset();
        assert!(core_access::program::<()>(false, false, |_| Err(
            "file/scratch unavailable".into()
        ))
        .is_err());
        assert!(CONTROL.lock().unwrap().diagnostic().is_ok());
    }
    #[test]
    fn failed_driver_cannot_authorize_a_second_physical_call() {
        reset();
        let mut p = core_access::reserve_program(false, false).unwrap();
        assert!(driver(&mut p, true).is_err());
        assert!(p.authorize_call().is_err());
        assert_eq!(device::Device::lock().fpga.pins, 1);
        assert!(core_access::finish_program(p, false).is_err());
    }
    #[test]
    fn successful_repeated_calls_keep_one_job_reservation() {
        reset();
        core_access::program(false, false, |p| {
            driver(p, false)?;
            assert!(CONTROL.lock().unwrap().diagnostic().is_err());
            driver(p, false)
        })
        .unwrap();
        assert_eq!(device::Device::lock().fpga.pins, 2);
    }
    #[test]
    fn legacy_maintenance_and_diag_are_symmetric() {
        for kind in [
            Maintenance::Benchmark,
            Maintenance::Rate,
            Maintenance::Restore,
        ] {
            reset();
            let guard = core_access::MaintenanceGuard::acquire(kind).unwrap();
            assert!(CONTROL.lock().unwrap().diagnostic().is_err());
            drop(guard);
            let _d = CONTROL.lock().unwrap().diagnostic().unwrap();
            assert!(core_access::MaintenanceGuard::acquire(kind).is_err());
        }
    }
    #[test]
    fn queued_restore_waits_for_full_receiver_av_drain() {
        reset();
        {
            let mut c = CONTROL.lock().unwrap();
            c.receiver_request().unwrap();
            c.source_dequeued();
            c.receiver_active().unwrap();
            c.av_admit().unwrap();
            c.restore_begin().unwrap();
        }
        assert!(core_access::program(false, true, |p| driver(p, false)).is_err());
        core_access::av_drained(true);
        CONTROL.lock().unwrap().receiver_stopped(true).unwrap();
        core_access::program(false, true, |p| driver(p, false)).unwrap();
        CONTROL.lock().unwrap().restore_finished(true).unwrap();
        assert!(CONTROL.lock().unwrap().diagnostic().is_ok());
    }
    fn hello_start(flags: u32, s: &mut streaming::av_session::Session) -> bool {
        use streaming::av_wire::{Kind, Packet};
        if core_access::refuse_diagnostic_peer().is_err() || !core_access::av_admit() {
            return false;
        }
        let p = Packet {
            kind: Kind::Hello,
            cookie: 23,
            sequence: 0,
            flags,
            timestamp: 0,
            payload: &[],
        };
        assert_eq!(s.receive(p, 7, 0, 91), streaming::av_session::Event::Offer);
        let nonce = 23u64.to_be_bytes();
        let start = Packet {
            kind: Kind::Start,
            cookie: 91,
            sequence: 0,
            flags,
            timestamp: 0,
            payload: &nonce,
        };
        assert_eq!(
            s.receive(start, 7, 1, 0),
            streaming::av_session::Event::Started
        );
        true
    }
    #[test]
    fn connected_zero_frame_input_tone_then_video_and_reverse_join() {
        for flags in [0, 1] {
            for av_first in [true, false] {
                reset();
                {
                    let mut c = CONTROL.lock().unwrap();
                    c.receiver_request().unwrap();
                    c.source_dequeued();
                    c.receiver_active().unwrap();
                }
                let mut session = streaming::av_session::Session::new();
                let mut frames = if av_first { 0 } else { 3 };
                assert!(hello_start(flags, &mut session));
                if av_first {
                    assert_eq!(frames, 0);
                    assert!(session.next_input().is_some());
                    frames += 3;
                }
                assert_eq!(frames, 3);
                assert!(session.active.is_some());
                // Video STOP here means no more frames; existing connected receiver survives.
                assert!(session.next_input().is_some());
                assert!(CONTROL.lock().unwrap().diagnostic().is_err());
                session.active = None;
                session.pending = None;
                core_access::av_drained(true);
                CONTROL.lock().unwrap().receiver_stopped(true).unwrap();
                assert!(CONTROL.lock().unwrap().diagnostic().is_ok());
            }
        }
    }
    #[test]
    fn full_disconnect_failed_join_retains_receiver_and_av() {
        reset();
        let mut c = CONTROL.lock().unwrap();
        c.receiver_request().unwrap();
        c.source_dequeued();
        c.receiver_active().unwrap();
        c.av_admit().unwrap();
        drop(c);
        core_access::av_drained(false);
        let mut c = CONTROL.lock().unwrap();
        assert!(c.receiver_stopped(false).is_err());
        assert!(c.quarantined());
        assert!(c.diagnostic().is_err());
        assert!(c.admission.video_phase().is_some());
        assert!(c.admission.av_phase().is_some());
    }
    #[test]
    fn diagnostic_build_refuses_connect_local_and_both_av_flags_before_mutation() {
        for flags in [0, 1] {
            reset();
            {
                let mut d = device::Device::lock();
                d.fpga.magic = key_diag_core::MAGIC;
                d.fpga.build = key_diag_core::BUILD;
            }
            assert!(core_access::refuse_diagnostic_peer().is_err());
            assert!(CONTROL.lock().unwrap().receiver_request().is_err());
            let mut s = streaming::av_session::Session::new();
            assert!(!hello_start(flags, &mut s));
            assert!(s.pending.is_none() && s.active.is_none());
            assert_eq!(device::Device::lock().fpga.pins, 0);
        }
    }
    #[test]
    fn exact_display_pairs_reject_crosses_and_unknown_schema() {
        for m in [0x4d425631, key_diag_core::MAGIC, 0] {
            for b in [0x4d424f49, 0x4d424f50, key_diag_core::BUILD, 0] {
                for schema in [0x10000, 0x10001, 0] {
                    let expected = schema == 0x10000
                        && ((m == 0x4d425631 && (b == 0x4d424f49 || b == 0x4d424f50))
                            || (m == key_diag_core::MAGIC && b == key_diag_core::BUILD));
                    assert_eq!(display_peer(m, schema, b), expected);
                }
            }
        }
    }
    struct LaunchFake {
        a: CoreAdmission,
        fail_spawn: bool,
        fail_send: bool,
        fail_release: bool,
        spawned: u32,
        sent: u32,
        released: u32,
        job: Option<DiagnosticPermit>,
    }
    impl LaunchFake {
        fn new() -> Self {
            Self {
                a: CoreAdmission::new(9),
                fail_spawn: false,
                fail_send: false,
                fail_release: false,
                spawned: 0,
                sent: 0,
                released: 0,
                job: None,
            }
        }
    }
    impl Launcher for LaunchFake {
        type Job = DiagnosticPermit;
        type Sender = ();
        fn reserve(&mut self) -> Result<Self::Job, ()> {
            self.a.reserve_diagnostic().map_err(|_| ())
        }
        fn spawn_empty(&mut self) -> Result<(), ()> {
            self.spawned += 1;
            assert!(self.job.is_none());
            if self.fail_spawn {
                Err(())
            } else {
                Ok(())
            }
        }
        fn send(&mut self, _: &(), job: Self::Job) -> Result<(), Self::Job> {
            if self.fail_send {
                Err(job)
            } else {
                self.sent += 1;
                self.job = Some(job);
                Ok(())
            }
        }
        fn release_unissued(&mut self, p: Self::Job) -> bool {
            if self.fail_release {
                self.job = Some(p);
                return false;
            }
            self.a.release_unissued_diagnostic(p).unwrap();
            self.released += 1;
            true
        }
        fn publish(&mut self, _: ()) {}
    }
    #[test]
    fn lazy_worker_spawn_and_send_fail_return_unissued_token_without_spi() {
        for spawn in [false, true] {
            let mut f = LaunchFake::new();
            f.fail_spawn = spawn;
            f.fail_send = !spawn;
            let r = Requests::new();
            assert_eq!(
                launch(&r, &mut f),
                if spawn {
                    StartResult::SpawnFailed
                } else {
                    StartResult::SendFailed
                }
            );
            assert_eq!(f.released, 1);
            assert_eq!(f.sent, 0);
            assert!(!r.busy());
            assert!(f.a.idle());
        }
    }
    #[test]
    fn single_pending_job_and_stop_never_waits_behind_status() {
        let mut f = LaunchFake::new();
        let r = Requests::new();
        assert_eq!(launch(&r, &mut f), StartResult::Started);
        for _ in 0..10000 {
            r.status();
        }
        r.stop();
        r.clear();
        assert!(r.take_stop());
        assert!(r.take_status());
        assert!(r.take_clear());
        assert_eq!(launch(&r, &mut f), StartResult::Busy);
        assert_eq!(f.spawned, 1);
        assert_eq!(f.sent, 1);
        assert!(f.a.diagnostic_reserved());
    }
    #[test]
    fn worker_exit_without_exit_proof_retains_exclusivity() {
        let mut f = LaunchFake::new();
        let r = Requests::new();
        assert_eq!(launch(&r, &mut f), StartResult::Started);
        drop(f.job.take());
        assert!(f.a.reserve_program().is_err());
        assert!(r.busy());
    }
    #[test]
    fn actual_lazy_worker_start_status_clear_and_teardown_with_fake_device() {
        reset();
        install_logger();
        sys::RESOURCE_CALLS.store(0, std::sync::atomic::Ordering::Relaxed);
        {
            let mut d = device::Device::lock();
            d.fpga.magic = key_diag_core::MAGIC;
            d.fpga.build = key_diag_core::BUILD;
        }
        key_diag_usb::command(b'd');
        let deadline = std::time::Instant::now() + std::time::Duration::from_secs(2);
        while device::Device::lock().fpga.writes == 0 {
            assert!(std::time::Instant::now() < deadline);
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
        // Wait for immutable terminal collection, then explicit CLEAR exits worker.
        std::thread::sleep(std::time::Duration::from_millis(60));
        key_diag_usb::command(b'b');
        key_diag_usb::command(b'y');
        while key_diag_usb::test_running() {
            assert!(std::time::Instant::now() < deadline);
            std::thread::sleep(std::time::Duration::from_millis(1));
        }
        assert!(!CONTROL.lock().unwrap().admission.diagnostic_reserved());
        assert_eq!(device::Device::lock().fpga.writes, 2);
        assert!(sys::RESOURCE_CALLS.load(std::sync::atomic::Ordering::Relaxed) >= 3);
        let logs = LOGS.lock().unwrap();
        let pages: Vec<_> = logs
            .iter()
            .enumerate()
            .filter(|(_, s)| s.contains("p=key_resource "))
            .collect();
        assert!(!pages.is_empty());
        for (index, line) in pages {
            assert!(index > 0);
            assert!(logs[index - 1].starts_with("USB_D24 v=2 p=key"));
            assert!(line.contains("worker=KeyDiag stack_low_bytes=4294967295 declared_bytes=6144"));
            assert!(line.contains("free_internal=18446744073709551615"));
            assert!(line.contains("sampled=true"));
        }
    }
    #[test]
    fn actual_worker_unowned_boot_quarantine_never_claims_success_or_writes() {
        // Pure production FSM version: do not strand a real host background thread.
        let mut a = CoreAdmission::new(101);
        let p = a.reserve_diagnostic().unwrap();
        let mut c = key_diag_core::DiagnosticCore::new(p, 0, 0, key_diag_core::Budgets::default());
        let id = [
            key_diag_core::MAGIC,
            key_diag_core::SCHEMA,
            0,
            key_diag_core::BUILD,
            key_diag_core::MAGIC,
            key_diag_core::SCHEMA,
            key_diag_core::FIXTURE_BYTES,
            key_diag_core::WATCHDOG,
        ];
        for value in id {
            let op = c.next_operation(0).unwrap();
            c.complete(op, key_diag_core::Outcome::Read(value), 0, 0);
        }
        for value in [0x13, 9, 1, 1, 0] {
            let op = c.next_operation(0).unwrap();
            c.complete(op, key_diag_core::Outcome::Read(value), 0, 0);
        }
        assert_eq!(c.stage(), key_diag_core::Stage::Quarantined);
        assert!(c.record().is_none());
        c.request_stop(1);
        assert!(c.next_operation(1).is_none());
        assert!(a.diagnostic_reserved());
    }

    #[test]
    fn bounded_record_pages_cover_maximum_width_fields() {
        use key_diag_core::*;
        let r = Record {
            kind: ResultKind::DataMismatch,
            owner: u64::MAX,
            sequence: u32::MAX,
            status: u32::MAX,
            payload: Payload {
                cycles: u32::MAX,
                samples: u32::MAX,
                bytes: u32::MAX,
                fault: u32::MAX,
                epoch: u32::MAX,
                frame: u32::MAX,
                tag: [u32::MAX; 4],
            },
        };
        for index in 1..=3 {
            let line = key_diag_pages::record_page(&r, index).unwrap();
            assert!(line.as_str().is_ascii());
            assert!(!line.as_str().contains(['\r', '\n']));
            assert!(line.as_str().len() + 64 <= 256);
            println!(
                "key_page index={index} bytes={} with_framing_reserve={}",
                line.as_str().len(),
                line.as_str().len() + 64
            );
        }
    }
    #[test]
    fn source_level_worker_budget_types_are_bounded() {
        use std::mem::size_of;
        println!("HOST_LAYOUT core={} permit={} operation={} coordinator={} line={} requests={} worker_declared={}",size_of::<key_diag_core::DiagnosticCore>(),size_of::<DiagnosticPermit>(),size_of::<key_diag_core::Operation>(),size_of::<Coordinator>(),size_of::<diag_pages::Line>(),size_of::<Requests>(),key_diag_usb::WORKER_STACK_BYTES);
        assert!(size_of::<key_diag_core::DiagnosticCore>() < 1024);
        assert!(size_of::<DiagnosticPermit>() <= 16);
        assert_eq!(key_diag_usb::WORKER_STACK_BYTES, 6144);
    }
    #[test]
    fn failed_diagnostic_release_keeps_returned_context_and_quarantines() {
        let mut foreign = CoreAdmission::new(991);
        let p = foreign.reserve_diagnostic().unwrap();
        let mut core =
            key_diag_core::DiagnosticCore::new(p, 0, 0, key_diag_core::Budgets::default());
        let op = core.next_operation(0).unwrap();
        core.complete(op, key_diag_core::Outcome::Read(0), 0, 0);
        let (p, proof, _) = core.into_exit().unwrap();
        let mut c = Coordinator::new();
        let _own = c.diagnostic().unwrap();
        assert!(c.diagnostic_finished(p, proof).is_err());
        assert!(c.quarantined());
        assert!(c.admission.diagnostic_reserved());
        assert!(c.program(false, false).is_err());
    }
    #[test]
    fn maintenance_guard_error_return_drops_device_and_current_first() {
        reset();
        fn callback() -> Result<(), ()> {
            let _maintenance =
                core_access::MaintenanceGuard::acquire(Maintenance::Benchmark).unwrap();
            let current = std::sync::Mutex::new(());
            let _current = current.lock().unwrap();
            let _device = device::Device::lock();
            Err(())
        }
        assert!(callback().is_err());
        assert!(CONTROL.lock().unwrap().diagnostic().is_ok());
    }

    #[test]
    fn receiver_activation_invariant_failure_retains_lease_without_io() {
        reset();
        {
            let mut c = CONTROL.lock().unwrap();
            c.receiver_request().unwrap();
            c.av_admit().unwrap();
            c.source_dequeued();
            assert_eq!(c.receiver_active(), Err(Error::NeedsCompatibleCore));
            c.receiver_activation_failed();
            assert!(c.quarantined());
            assert!(c.admission.video_phase().is_some());
            assert!(c.admission.av_phase().is_some());
            assert!(c.diagnostic().is_err());
        }
        assert_eq!(device::Device::lock().fpga.writes, 0);
        assert_eq!(device::Device::lock().fpga.pins, 0);
    }

    #[test]
    fn failed_unissued_release_never_advertises_worker_exit() {
        let mut f = LaunchFake::new();
        f.fail_spawn = true;
        f.fail_release = true;
        let r = Requests::new();
        assert_eq!(launch(&r, &mut f), StartResult::Quarantined);
        assert!(r.busy());
        assert!(f.job.is_some());
        assert!(f.a.diagnostic_reserved());
        assert_eq!(f.sent, 0);
        assert_eq!(f.released, 0);
    }
    #[test]
    fn maintenance_side_effects_require_confirmed_stop_before_release() {
        for confirmed in [false, true] {
            reset();
            let mut g = core_access::MaintenanceGuard::acquire(Maintenance::Benchmark).unwrap();
            g.side_effects_begin();
            {
                let _d = device::Device::lock();
                assert_eq!(test_control_depth(), 0);
            }
            if confirmed {
                g.quiescent();
            }
            drop(g);
            let mut c = CONTROL.lock().unwrap();
            assert_eq!(c.quarantined(), !confirmed);
            assert_eq!(c.diagnostic().is_ok(), confirmed);
        }
    }
    struct DisplayBus {
        magic: u32,
        build: u32,
        writes: u32,
    }
    impl margin::Bus for DisplayBus {
        fn read(&mut self, off: u32) -> Result<u32, ()> {
            Ok(match off {
                0 => self.magic,
                4 => 0x10000,
                0x184 => self.build,
                0x08c => margin::MAGIC,
                0x090 => timing::MAGIC,
                0x09c => timing::SCHEMA,
                0x084 => 40,
                0x088 => 0x700 | 40,
                0x0a8 => 0x700,
                0x0a0 => timing::Timing::current().horizontal,
                0x0a4 => timing::Timing::current().vertical,
                _ => 0,
            })
        }
        fn write(&mut self, _: u32, _: u32) -> Result<(), ()> {
            self.writes += 1;
            Ok(())
        }
    }
    #[test]
    fn actual_margin_and_timing_controllers_apply_exact_peer_pair_guard() {
        for magic in [0x4d425631, key_diag_core::MAGIC] {
            for build in [0x4d424f49, 0x4d424f50, key_diag_core::BUILD] {
                let expected = if display_peer(magic, 0x10000, build) {
                    margin::Outcome::Status
                } else {
                    margin::Outcome::Identity
                };
                let mut b = DisplayBus {
                    magic,
                    build,
                    writes: 0,
                };
                let mut m = margin::Controller::new();
                m.request(b'h').unwrap();
                assert_eq!(m.step(&mut b).unwrap().outcome, expected);
                let mut t = timing::Controller::new();
                t.request(b'T', timing::Choice::Query).unwrap();
                let mut result = None;
                for _ in 0..4 {
                    if let Some(r) = t.step(&mut b) {
                        result = Some(r);
                        break;
                    }
                }
                assert_eq!(result.unwrap().outcome, expected);
                assert_eq!(b.writes, 0);
            }
        }
    }
    #[test]
    fn resource_page_maximum_width_and_exact_field_routing() {
        let line = key_diag_pages::resource(u32::MAX, u32::MAX, usize::MAX, usize::MAX).unwrap();
        let text = line.as_str();
        assert!(text.starts_with("USB_D24 v=2 p=key_resource worker=KeyDiag "));
        assert!(text.contains("stack_low_bytes=4294967295 declared_bytes=4294967295"));
        assert!(text
            .contains("free_internal=18446744073709551615 largest_internal=18446744073709551615"));
        assert!(text.ends_with("sampled=true"));
        assert!(!text.contains(['\r', '\n']));
        assert!(text.len() + 64 <= 256);
        println!(
            "RESOURCE_PAGE max_payload={} with_framing_reserve={}",
            text.len(),
            text.len() + 64
        );
    }
}
