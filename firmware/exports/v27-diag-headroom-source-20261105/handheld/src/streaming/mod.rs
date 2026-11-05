//! Experimental standalone MSV1 source. Sunshine pairing/video are not implemented.
pub mod protocol;
pub mod telemetry;
pub mod rx_queue;
pub mod adpcm;
pub mod av_wire;
pub mod av_session;
pub mod audio_io;
pub mod audio;
pub mod compressed_queue;
pub mod audio_diag;
pub mod service_policy;
pub mod audio_snapshot;
pub mod av_power_save;
pub mod overlap;
pub mod batch;
pub mod control;
mod local;
pub mod local_feed;
mod local_assets;
use anyhow::Context;
use crate::device::{
    drivers::fpga::{FpgaSpiWordSize, SpiCommand},
    Device,
};
use esp_idf_svc::{
    eventloop::EspSystemEventLoop,
    hal::{modem::Modem, units::Hertz},
    wifi::{AuthMethod, BlockingWifi, ClientConfiguration, Configuration, EspWifi},
};
use std::{
    net::{Ipv4Addr, SocketAddr, UdpSocket},
    sync::{
        atomic::{AtomicBool, AtomicU16, AtomicU32, Ordering},
        mpsc, Arc, Mutex, OnceLock,
    },
    time::{Duration, Instant},
};

const BASE: u32 = 0xE0000000;
const TIMEOUT: Duration = Duration::from_millis(500);
static MODEM: OnceLock<Mutex<Option<Modem>>> = OnceLock::new();
enum Source { Network(String), Local(u8) }
static COMMAND: OnceLock<mpsc::SyncSender<(Source, u32)>> = OnceLock::new();
static GENERATION: AtomicU32 = AtomicU32::new(0);
/// Capture-time diagnostic marker only; does not bind retained frame provenance.
pub fn diagnostic_generation()->u32 { GENERATION.load(Ordering::Acquire) }
static BUTTONS: AtomicU16 = AtomicU16::new(0);
static ACTIVE: AtomicBool = AtomicBool::new(false);
static LOCAL_WANTED: AtomicBool = AtomicBool::new(false);
static LOCAL_ACTIVE: AtomicBool = AtomicBool::new(false);
static LOCAL_CONTEXT: AtomicBool = AtomicBool::new(false);
static LOCAL_RECOVERY_FAILED: AtomicBool = AtomicBool::new(false);
static WANTED: AtomicBool = AtomicBool::new(false);
static RESTORING: AtomicBool = AtomicBool::new(false);
static BENCH_ACTIVE: AtomicBool = AtomicBool::new(false);
static OVERLAP_REQUEST: AtomicBool = AtomicBool::new(false);
static OVERLAP_ACTIVE: AtomicBool = AtomicBool::new(false);
static QUEUE_DEPTH: AtomicU32 = AtomicU32::new(4);
static CONSUMER_BOOST: AtomicBool = AtomicBool::new(false);
static STREAM_WRITE_HZ: AtomicU32 = AtomicU32::new(40_000_000);
static RATE_CHANGING: AtomicBool = AtomicBool::new(false);
static CONSUMER_BUSY: AtomicBool = AtomicBool::new(false);
static CONSUMER_SEEN: AtomicBool = AtomicBool::new(false);
static CONSUMER_DEQUEUE_US: AtomicU32 = AtomicU32::new(0);
use crate::core_coordinator::CONTROL;
static STATS: Mutex<Stats> = Mutex::new(Stats::new());
static PRESENTATION_EPOCH: Mutex<telemetry::PresentationEpoch> = Mutex::new(
    telemetry::PresentationEpoch { sequence: 0, baseline_presented: 0, valid: false });
pub fn presentation_epoch() -> telemetry::PresentationEpoch { *PRESENTATION_EPOCH.lock().unwrap() }
static TRACE: Mutex<telemetry::Snapshot> = Mutex::new(telemetry::Snapshot {
    completed: telemetry::FrameTrace { valid: false, id: 0, started_us: 0, last_packet_us: 0, finished_us: 0, packets: 0, bytes: 0, max_interarrival_us: 0, min_interarrival_us: 0, max_queue_residence_us: 0, max_consumer_processing_us: 0, last_consumer_us: 0, max_consumer_gap_us: 0, begin_us: 0, qspi_calls: 0, qspi_total_us: 0, qspi_max_us: 0, lock_total_us: 0, lock_max_us: 0, min_frame_remaining: 0, gap_valid: false, expected_offset: 0, observed_offset: 0 },
    dropped: telemetry::FrameTrace { valid: false, id: 0, started_us: 0, last_packet_us: 0, finished_us: 0, packets: 0, bytes: 0, max_interarrival_us: 0, min_interarrival_us: 0, max_queue_residence_us: 0, max_consumer_processing_us: 0, last_consumer_us: 0, max_consumer_gap_us: 0, begin_us: 0, qspi_calls: 0, qspi_total_us: 0, qspi_max_us: 0, lock_total_us: 0, lock_max_us: 0, min_frame_remaining: 0, gap_valid: false, expected_offset: 0, observed_offset: 0 },
});
pub fn trace() -> telemetry::Snapshot { *TRACE.lock().unwrap() }
#[derive(Clone, Copy, Debug, Default)]
pub struct QueueDrop { pub capacity: u32, pub count: u32, pub first_id: u32, pub first_offset: u32, pub first_valid: bool, pub first_since_consumer_us: u32, pub first_since_producer_us: u32, pub first_consumer_busy: bool, pub first_queued: u32, pub socket_errors: u32, pub producer_stack_low_water: u32, pub consumer_stack_low_water: u32, pub producer_priority: u32, pub consumer_priority: u32 }
static QUEUE_DROP: Mutex<QueueDrop> = Mutex::new(QueueDrop { capacity: 0, count: 0, first_id: 0, first_offset: 0, first_valid: false, first_since_consumer_us: 0, first_since_producer_us: 0, first_consumer_busy: false, first_queued: 0, socket_errors: 0, producer_stack_low_water: 0, consumer_stack_low_water: 0, producer_priority: 0, consumer_priority: 0 });
static PRODUCER_TIMING: Mutex<telemetry::ProducerTiming> = Mutex::new(telemetry::ProducerTiming { datagrams: 0, last_us: 0, min_gap_us: 0, max_gap_us: 0, gaps_below_1000us: 0 });
static QUEUE_COUNTS: OnceLock<Mutex<Option<Arc<rx_queue::Counts>>>> = OnceLock::new();
pub fn queue_trace() -> (QueueDrop, telemetry::ProducerTiming, u32, u32) {
    let q = *QUEUE_DROP.lock().unwrap();
    let guard = QUEUE_COUNTS.get_or_init(|| Mutex::new(None)).lock().unwrap();
    let (used, high) = guard.as_ref().map_or((0, 0), |c|
        (c.queued.load(Ordering::Relaxed), c.high_water.load(Ordering::Relaxed)));
    let timing = *PRODUCER_TIMING.lock().unwrap();
    (q, timing, used, high)
}
/// Diagnostic A/B selection applies only to the next session, never persists.
pub fn set_queue_depth(depth: u32) -> anyhow::Result<()> {
    anyhow::ensure!(telemetry::valid_queue_depth(depth), "Supported queue depths are 4, 16 and 32");
    let _control = CONTROL.lock().unwrap();
    anyhow::ensure!(!has_session() && !RESTORING.load(Ordering::Acquire)
        && !BENCH_ACTIVE.load(Ordering::Acquire), "Stop streaming before selecting queue depth");
    QUEUE_DEPTH.store(depth, Ordering::Release);
    Ok(())
}
pub fn set_consumer_boost(boost: bool) -> anyhow::Result<()> {
    let _control = CONTROL.lock().unwrap();
    anyhow::ensure!(!has_session() && !RESTORING.load(Ordering::Acquire)
        && !BENCH_ACTIVE.load(Ordering::Acquire), "Stop streaming before selecting priority");
    CONSUMER_BOOST.store(boost, Ordering::Release);
    Ok(())
}
/// Test-only volatile selector; never switches an active or restoring session.
pub fn set_stream_write_hz(hz: u32) -> anyhow::Result<()> {
    anyhow::ensure!(telemetry::valid_stream_write_clock(hz), "Unsupported QSPI data-write clock");
    let _maintenance=crate::core_access::MaintenanceGuard::acquire(crate::core_coordinator::Maintenance::Rate)?;
    let _reservation = {
        let _control = CONTROL.lock().unwrap();
        anyhow::ensure!(telemetry::stream_write_change_allowed(has_session(), RESTORING.load(Ordering::Acquire),
            BENCH_ACTIVE.load(Ordering::Acquire)), "Stop streaming and wait for recovery before selecting QSPI rate");
        control::RateReservation::acquire(&RATE_CHANGING).ok_or_else(|| anyhow::anyhow!("QSPI rate change already running"))?
    };
    access(|d| {
        let magic = d.fpga.read_u32(BASE)?;
        if magic != 0x4D425631 { return Ok(()); }
        identity(d)?;
        let caps = d.fpga.read_u32(BASE + 8)?;
        let status = d.fpga.read_u32(BASE + 0x10)?;
        let bench = if caps & 8 != 0 { d.fpga.read_u32(BASE + 0x70)? } else { 0 };
        let (mode, admission, causes) = if caps & overlap::CAP_OVERLAP != 0 {
            let raw_mode = d.fpga.read_u32(BASE + 0x78)?;
            anyhow::ensure!(raw_mode & !1 == 0, "Unknown FPGA mode");
            let mode = if raw_mode & 1 == 0 { overlap::Mode::Legacy } else { overlap::Mode::Overlap };
            if mode == overlap::Mode::Overlap {
                (mode, d.fpga.read_u32(BASE + 0x7c)?, d.fpga.read_u32(BASE + 0x80)?)
            } else { (mode, 0, 0) }
        } else { (overlap::Mode::Legacy, 0, 0) };
        anyhow::ensure!(overlap::peer_rebind_quiescent(mode, status, admission, causes, bench),
            "Streaming FPGA is not quiescent");
        Ok(())
    })?;
    STREAM_WRITE_HZ.store(hz, Ordering::Release);
    Ok(())
}
pub fn stream_write_hz() -> u32 { STREAM_WRITE_HZ.load(Ordering::Acquire) }
pub fn stream_write_calculated_khz() -> anyhow::Result<Option<u32>> {
    let requested = stream_write_hz();
    access(|d| Ok(d.fpga.spi_calculated_khz(Hertz(requested))))
}
/// This experiment is explicit, volatile, and never changes a running session.
pub fn set_overlap_requested(enable: bool) -> anyhow::Result<()> {
    let _control = CONTROL.lock().unwrap();
    anyhow::ensure!(!has_session() && !RESTORING.load(Ordering::Acquire)
        && !BENCH_ACTIVE.load(Ordering::Acquire), "Stop streaming before changing overlap mode");
    OVERLAP_REQUEST.store(enable, Ordering::Release);
    Ok(())
}
pub fn overlap_status() -> (bool, bool) {
    (OVERLAP_REQUEST.load(Ordering::Acquire), OVERLAP_ACTIVE.load(Ordering::Acquire))
}
fn record_queue_drop(bytes: &[u8], now: u64, previous_us: u64, queued: u32) {
    let mut diag = QUEUE_DROP.lock().unwrap();
    diag.count = diag.count.saturating_add(1);
    if !diag.first_valid {
        if let Ok(h) = protocol::Header::parse(bytes) {
            diag.first_id = h.id; diag.first_offset = h.offset; diag.first_valid = true;
            let seen = CONSUMER_SEEN.load(Ordering::Acquire);
            let last = CONSUMER_DEQUEUE_US.load(Ordering::Relaxed);
            diag.first_since_consumer_us = telemetry::since_last_dequeue(now, last, seen);
            diag.first_since_producer_us = now.saturating_sub(previous_us).min(u32::MAX as u64) as u32;
            diag.first_consumer_busy = CONSUMER_BUSY.load(Ordering::Acquire);
            diag.first_queued = queued;
        }
    }
}
fn monotonic_us() -> u64 { unsafe { esp_idf_svc::sys::esp_timer_get_time() as u64 } }
#[derive(Clone)]
pub struct Stats {
    pub status: String,
    pub source: &'static str,
    pub received: u32,
    pub dropped: u32,
    pub errors: u32,
    pub bytes: u64,
    pub displayed: u32,
    pub decoded: u32,
    pub credits: u32,
    pub rx_fps: u32,
    pub display_fps: u32,
    pub bitrate: u32,
}
impl Stats {
    const fn new() -> Self {
        Self {
            status: String::new(),
            source: "idle",
            received: 0,
            dropped: 0,
            errors: 0,
            bytes: 0,
            displayed: 0,
            decoded: 0,
            credits: 0,
            rx_fps: 0,
            display_fps: 0,
            bitrate: 0,
        }
    }
}
fn source_stats(source: &'static str) {
    let mut stats = STATS.lock().unwrap();
    if stats.source != source { *stats = Stats::new(); stats.source = source; }
}
pub fn stats() -> Stats {
    STATS.lock().unwrap().clone()
}
fn status(s: impl Into<String>) {
    STATS.lock().unwrap().status = s.into();
}
pub fn supply_modem(modem: Modem) {
    let _ = MODEM.set(Mutex::new(Some(modem)));
}
pub fn input(mask: u16) {
    BUTTONS.store(mask, Ordering::Relaxed);
}
pub fn telemetry_source() -> &'static str { STATS.lock().unwrap().source }
pub fn local_context() -> bool { LOCAL_CONTEXT.load(Ordering::Acquire) }
pub fn core_replacement_blocked() -> bool {
    has_session() || RESTORING.load(Ordering::Acquire) || LOCAL_RECOVERY_FAILED.load(Ordering::Acquire) || audio::RECOVERY_FAILED.load(Ordering::Acquire)
}
pub fn has_session() -> bool {
    ACTIVE.load(Ordering::Acquire) || WANTED.load(Ordering::Acquire)
}
pub fn disconnect() {
    if control::requires_local_exit(LOCAL_WANTED.load(Ordering::Acquire),LOCAL_ACTIVE.load(Ordering::Acquire),LOCAL_CONTEXT.load(Ordering::Acquire)){exit_to_menu();return;}
    {let mut c=CONTROL.lock().unwrap();disconnect_locked();let _=c.cancel_pending(ACTIVE.load(Ordering::Acquire));}
}
pub fn stop_local_loop(){disconnect();}
fn disconnect_locked(){LOCAL_WANTED.store(false,Ordering::Release);control::cancel(&WANTED,&GENERATION);}
pub fn exit_to_menu(){
    let admitted={let mut c=CONTROL.lock().unwrap();
        if c.restore_begin().is_err(){false}else{RESTORING.store(true,Ordering::Release);disconnect_locked();let _=c.cancel_pending(ACTIVE.load(Ordering::Acquire));true}};
    if !admitted{status("FPGA Busy or recovery unconfirmed; retry/restart");return;}
    let spawned=std::thread::Builder::new().name("StreamExit".into()).stack_size(4096).spawn(||{
        while ACTIVE.load(Ordering::Acquire){std::thread::sleep(Duration::from_millis(20));}
        if LOCAL_RECOVERY_FAILED.load(Ordering::Acquire)||audio::RECOVERY_FAILED.load(Ordering::Acquire){
            CONTROL.lock().unwrap().quarantine();status("FPGA source recovery unconfirmed; restart required");return;
        }
        crate::worker::send(crate::worker::Message::RestoreAfterStreaming);
    });
    if spawned.is_err(){CONTROL.lock().unwrap().quarantine();status("Restore worker unavailable; restart required");}
}
pub fn restored(){
    // UI callback occurs after program callback and all Device/CURRENT guards.
    let ok=CONTROL.lock().unwrap().restore_finished(true).is_ok();
    if ok{LOCAL_CONTEXT.store(false,Ordering::Release);RESTORING.store(false,Ordering::Release);}
}
pub fn connect(host: String) { request_source(Source::Network(host)); }
pub fn start_local_loop(id: u8) {
    if !(1..=3).contains(&id) { status("Invalid local loop"); return; }
    request_source(Source::Local(id));
}
fn request_source(source:Source){
    if let Err(e)=crate::core_access::refuse_diagnostic_peer(){status(e.to_string());return;}
    let local=matches!(source,Source::Local(_));
    let generation={let mut c=CONTROL.lock().unwrap();
        if c.receiver_request().is_err(){drop(c);status("FPGA Busy or diagnostic installed; stop/restart before Connect");return;}
        LOCAL_WANTED.store(local,Ordering::Release);WANTED.store(true,Ordering::Release);
        GENERATION.fetch_add(1,Ordering::AcqRel).wrapping_add(1)};
    if local&&!LOCAL_ACTIVE.load(Ordering::Acquire){crate::ui::send(crate::ui::Message::TestShowStreaming);}
    let tx=COMMAND.get_or_init(||{
        let(tx,rx)=mpsc::sync_channel::<(Source,u32)>(2);
        if std::thread::Builder::new().name("Streaming".into()).stack_size(16*1024).spawn(move||{
            if let Err(e)=worker(rx){CONTROL.lock().unwrap().quarantine();status(format!("Streaming unavailable: {e}"));}
        }).is_err(){CONTROL.lock().unwrap().quarantine();}
        tx
    });
    if tx.try_send((source,generation)).is_err(){
        {let mut c=CONTROL.lock().unwrap();disconnect_locked();let _=c.cancel_pending(ACTIVE.load(Ordering::Acquire));}
        status("Busy: disconnect and retry");
    }
}

/// Configuration is deliberately local, not a fake discovery/pairing workflow.
fn config(host: &str) -> anyhow::Result<(Ipv4Addr, String, String)> {
    anyhow::ensure!(
        std::fs::metadata("/sdcard/moonshine.cfg")?.len() <= 1024,
        "moonshine.cfg exceeds 1024 bytes"
    );
    use std::io::Read;
    let mut text = String::new();
    std::fs::File::open("/sdcard/moonshine.cfg")?
        .take(1025)
        .read_to_string(&mut text)?;
    anyhow::ensure!(text.len() <= 1024, "moonshine.cfg exceeds 1024 bytes");
    let (mut saved, mut ssid, mut password) = (String::new(), String::new(), String::new());
    for line in text.lines() {
        if let Some((k, v)) = line.trim().split_once('=') {
            match k.trim() {
                "host" => saved = v.trim().into(),
                "ssid" => ssid = v.trim().into(),
                "password" => password = v.into(),
                _ => {}
            }
        }
    }
    let host = if host.trim().is_empty() {
        saved.as_str()
    } else {
        host.trim()
    };
    anyhow::ensure!(
        !ssid.is_empty() && ssid.len() <= 32 && password.len() <= 63,
        "Invalid Wi-Fi credentials"
    );
    Ok((host.parse()?, ssid, password))
}
fn init_wifi() -> anyhow::Result<BlockingWifi<EspWifi<'static>>> {
    memory_probe("before Wi-Fi init");
    let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
    let free = unsafe { esp_idf_svc::sys::heap_caps_get_free_size(caps) };
    let largest = unsafe { esp_idf_svc::sys::heap_caps_get_largest_free_block(caps) };
    anyhow::ensure!(free >= 48 * 1024 && largest >= 8 * 1024,
        "Insufficient memory for Wi-Fi (free={free}, largest={largest}); restart and retry");
    let modem = MODEM
        .get()
        .ok_or_else(|| anyhow::anyhow!("modem not initialized"))?
        .lock()
        .unwrap()
        .take()
        .ok_or_else(|| anyhow::anyhow!("modem already owned"))?;
    let sysloop = EspSystemEventLoop::take()?;
    // Existing KVS owns the NVS partition. Do not take it twice; Wi-Fi uses RAM configuration.
    let wifi = BlockingWifi::wrap(EspWifi::new(modem, sysloop.clone(), None)?, sysloop)?;
    memory_probe("after Wi-Fi init");
    Ok(wifi)
}
fn run_network(wifi: &mut BlockingWifi<EspWifi<'static>>, host: String, generation: u32) -> anyhow::Result<()> {
            status("Reading /sdcard/moonshine.cfg");
            let (host, ssid, password) = config(&host)?;
            let _ = wifi.disconnect();
            let _ = wifi.stop();
            status("Connecting Wi-Fi (2.4 GHz)");
            wifi.set_configuration(&Configuration::Client(ClientConfiguration {
                ssid: ssid
                    .as_str()
                    .try_into()
                    .map_err(|_| anyhow::anyhow!("SSID too long"))?,
                password: password
                    .as_str()
                    .try_into()
                    .map_err(|_| anyhow::anyhow!("Password too long"))?,
                auth_method: if password.is_empty() {
                    AuthMethod::None
                } else {
                    AuthMethod::WPA2Personal
                },
                ..Default::default()
            }))?;
            wifi.start()?;
            memory_probe("Wi-Fi started");
            wifi.connect()?;
            memory_probe("Wi-Fi associated");
            wifi.wait_netif_up()?;
            memory_probe("Wi-Fi connected");
            if GENERATION.load(Ordering::Acquire) != generation {
                return Ok(());
            }
            ensure_core()?;
            memory_probe("streaming core ready");
            session(host, generation)
}
fn worker(rx: mpsc::Receiver<(Source, u32)>) -> anyhow::Result<()> {
    let mut wifi: Option<BlockingWifi<EspWifi<'static>>> = None;
    while let Ok((source, generation)) = rx.recv() {
        {
            let mut coordinator = CONTROL.lock().unwrap();
            if !control::may_admit_source(WANTED.load(Ordering::Acquire), GENERATION.load(Ordering::Acquire), generation,
                RATE_CHANGING.load(Ordering::Acquire), RESTORING.load(Ordering::Acquire), LOCAL_RECOVERY_FAILED.load(Ordering::Acquire) || audio::RECOVERY_FAILED.load(Ordering::Acquire)) { continue; }
            coordinator.source_dequeued();
            if let Err(error)=coordinator.receiver_active(){
                coordinator.receiver_activation_failed();disconnect_locked();ACTIVE.store(false,Ordering::Release);drop(coordinator);
                STATS.lock().unwrap().errors+=1;status(format!("Receiver admission invariant failed: {error:?}; restart required"));continue;
            }
            LOCAL_CONTEXT.store(matches!(source, Source::Local(_)), Ordering::Release);
            LOCAL_ACTIVE.store(matches!(source, Source::Local(_)), Ordering::Release);
            ACTIVE.store(true, Ordering::Release);
        }
        let result = crate::core_access::refuse_diagnostic_peer().and_then(|_|match source {
            Source::Local(id) => local::run(id, generation),
            Source::Network(host) => (|| {
                source_stats("network");
                if wifi.is_none() { wifi = Some(init_wifi()?); }
                run_network(wifi.as_mut().unwrap(), host, generation)
            })(),
        });
        if let Some(wifi) = wifi.as_mut() { let _ = wifi.disconnect(); let _ = wifi.stop(); }
        LOCAL_ACTIVE.store(false, Ordering::Release);
        {let mut c=CONTROL.lock().unwrap();
        let clean=!LOCAL_RECOVERY_FAILED.load(Ordering::Acquire)&&!audio::RECOVERY_FAILED.load(Ordering::Acquire);
        if !clean{c.quarantine();}
        else if !WANTED.load(Ordering::Acquire){let _=c.receiver_stopped(true);}
        // A stopped-but-still-connected/TestReady receiver keeps its lease
        // until existing disconnect cancels WANTED (including setup errors).
        ACTIVE.store(false, Ordering::Release);}
        if let Err(e) = result { STATS.lock().unwrap().errors += 1; status(format!("Stopped: {e}")); }
        else { status("Disconnected; source stopped and remote controls released"); }
    }
    Ok(())
}

fn memory_probe(stage: &str) {
    let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
    unsafe {
        log::info!("Streaming memory {}: free={} largest={} stack_low_water={}", stage,
            esp_idf_svc::sys::heap_caps_get_free_size(caps),
            esp_idf_svc::sys::heap_caps_get_largest_free_block(caps),
            esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()));
    }
}
fn access<T>(f: impl FnOnce(&mut Device<'static>) -> anyhow::Result<T>) -> anyhow::Result<T> {
    // UI and telemetry briefly own the same device. A single failed try_lock
    // discarded an entire JPEG even when the lock was released immediately.
    // Bound the wait so the network worker cannot queue ahead of UI/input.
    let deadline = Instant::now() + Duration::from_millis(8);
    loop {
        if let Some(mut d) = Device::try_lock() {
            return f(&mut d);
        }
        if Instant::now() >= deadline {
            anyhow::bail!("FPGA busy; frame dropped");
        }
        std::thread::sleep(Duration::from_micros(250));
    }
}
fn identity(d: &mut Device<'static>) -> anyhow::Result<()> {
    anyhow::ensure!(
        d.fpga.read_u32(BASE)? == 0x4D425631 && d.fpga.read_u32(BASE + 4)? >> 16 == 1,
        "Streaming core replaced"
    );
    Ok(())
}
fn ensure_core() -> anyhow::Result<()> {
    crate::core_access::refuse_diagnostic_peer()?;
    let already = access(|d| Ok(d.fpga.read_u32(BASE)? == 0x4D425631))?;
    if !already {
        log::info!("USB_TRACE source={} core_reload=true calibration_settings_reset=true", stats().source);
        status("Loading /sdcard/moonshine.bit (volatile FPGA)");
        let mut file = std::fs::File::open("/sdcard/moonshine.bit")?;
        let mut scratch = DmaBuffer::new(4 * 1024)?;
        let mut permit=crate::core_access::reserve_program(true,false)?;
        let programmed=(||->anyhow::Result<()>{
        let authorization=permit.authorize_call().map_err(|e|anyhow::anyhow!("FPGA Busy: {e:?}"))?;
        let mut d = Device::lock();
        let mode = d.get_display_mode();
        if mode == crate::device::DisplayMode::Internal {
            d.set_lcd_enabled(false);
            std::thread::sleep(Duration::from_millis(10));
        }
        let programmed = d.fpga.program(&mut file, scratch.bytes(),authorization);
        if mode == crate::device::DisplayMode::Internal {
            d.set_lcd_enabled(true);
        }
        programmed?;
        d.fpga.set_display_mode(mode)?;
        d.fpga
            .enable_interrupt(crate::device::drivers::fpga::Irq::Button)?;
        d.fpga.set_system_clock_rate(Hertz(50_000_000));
        Ok(())})();
        let finished=crate::core_access::finish_program(permit,programmed.is_ok());
        programmed?;finished?;
    }
    access(|d| {
        anyhow::ensure!(
            d.fpga.read_u32(BASE)? == 0x4D425631,
            "Wrong FPGA image identity"
        );
        d.fpga
            .write_u32(crate::device::drivers::fpga::REG_CONTROL, 3)?;
        Ok(())
    })?;
    *crate::bitstream::current() = crate::bitstream::CurrentBitstream::Streaming;
    crate::ui::send(crate::ui::Message::Redraw);
    Ok(())
}
#[derive(Clone, Copy)]
struct CoreMode { mode: overlap::Mode, max_bytes: u32, slot_bytes: u32 }

/// Detect support and switch only at a hardware-reported idle boundary.
/// No mode register is touched on legacy cores lacking the capability bit.
fn prepare_mode(generation: u32) -> anyhow::Result<CoreMode> {
    let requested = OVERLAP_REQUEST.load(Ordering::Acquire);
    let (version, caps, max_bytes) = access(|d| {
        identity(d)?;
        Ok((d.fpga.read_u32(BASE + 4)?, d.fpga.read_u32(BASE + 8)?, d.fpga.read_u32(BASE + 0x4c)?))
    })?;
    let mode = overlap::requested_mode(requested, version, caps)
        .map_err(|e| anyhow::anyhow!("Overlap mode unavailable: {e:?}"))?;
    anyhow::ensure!(max_bytes > 0 && max_bytes <= overlap::MAX_BYTES, "Unexpected FPGA frame bound");
    if caps & overlap::CAP_OVERLAP == 0 {
        return Ok(CoreMode { mode: overlap::Mode::Legacy, max_bytes, slot_bytes: 0 });
    }
    let slot_bytes = access(|d| Ok(d.fpga.read_u32(BASE + 0x74)?))?;
    anyhow::ensure!(slot_bytes == overlap::SLOT_BYTES && max_bytes == overlap::MAX_BYTES,
        "Unexpected FPGA overlap slot bounds");
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        anyhow::ensure!(GENERATION.load(Ordering::Acquire) == generation, "Overlap mode change cancelled");
        let done = access(|d| {
            let raw_mode = d.fpga.read_u32(BASE + 0x78)?;
            anyhow::ensure!(raw_mode & !1 == 0, "Unknown FPGA overlap mode bits");
            let current = if raw_mode & 1 == 0 { overlap::Mode::Legacy } else { overlap::Mode::Overlap };
            if current == mode { return Ok(true); }
            let status = d.fpga.read_u32(BASE + 0x10)?;
            let admission = d.fpga.read_u32(BASE + 0x7c)?;
            let benchmark_active = d.fpga.read_u32(BASE + 0x70)? & 1 != 0;
            if benchmark_active || !overlap::may_switch(current, status, admission) { return Ok(false); }
            d.fpga.write_u32(BASE + 0x78, u32::from(mode == overlap::Mode::Overlap))?;
            anyhow::ensure!(d.fpga.read_u32(BASE + 0x78)? & 1 == u32::from(mode == overlap::Mode::Overlap),
                "FPGA refused overlap mode change");
            Ok(true)
        })?;
        if done { return Ok(CoreMode { mode, max_bytes, slot_bytes }); }
        anyhow::ensure!(Instant::now() < deadline, "FPGA remained busy during overlap mode change");
        std::thread::sleep(Duration::from_millis(10));
    }
}

/// Rebinding is allowed only after the previous sender's entire FPGA pipeline
/// is idle, including staged/decoding/pending frames; no global abort is needed.
fn rebind_when_quiescent(core: CoreMode) -> anyhow::Result<bool> {
    access(|d| {
        identity(d)?;
        let mut status = d.fpga.read_u32(BASE + 0x10)?;
        // Legacy core can retain a sticky fault after a decoder error. Its
        // READY bit proves no frame is owned before clearing that idle fault.
        if core.mode == overlap::Mode::Legacy && status & 5 == 5 {
            d.fpga.write_u32(BASE + 0x24, overlap::CMD_GLOBAL_ABORT)?;
            status = d.fpga.read_u32(BASE + 0x10)?;
        }
        let (admission, causes, bench) = if core.mode == overlap::Mode::Overlap {
            (d.fpga.read_u32(BASE + 0x7c)?, d.fpga.read_u32(BASE + 0x80)?,
             d.fpga.read_u32(BASE + 0x70)?)
        } else { (0, 0, 0) };
        if !overlap::peer_rebind_quiescent(core.mode, status, admission, causes, bench) {
            return Ok(false);
        }
        let displayed = d.fpga.read_u32(BASE + 0x34)?;
        PRESENTATION_EPOCH.lock().unwrap().advance(displayed);
        Ok(true)
    })
}

fn wait_for_quiescent_epoch(core: CoreMode, generation: u32) -> anyhow::Result<()> {
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        anyhow::ensure!(protocol::generation_is_current(generation, GENERATION.load(Ordering::Acquire)),
            "Streaming cancelled before source epoch");
        match rebind_when_quiescent(core) {
            Ok(true) => return Ok(()),
            Ok(false) => anyhow::ensure!(Instant::now() < deadline, "FPGA did not become idle before source epoch"),
            Err(e) => if Instant::now() >= deadline { return Err(e.context("FPGA source epoch check failed")); },
        }
        std::thread::sleep(Duration::from_millis(10));
    }
}

fn abort(mode: overlap::Mode, global: bool) -> anyhow::Result<()> {
    let started = Instant::now();
    loop {
        match access(|d| {
            identity(d)?;
            let mut io_error = false;
            overlap::abort_and_verify(&mut CoreRegisters { device: d, io_error: &mut io_error, observed_status: None }, mode, global)
                .map_err(|e| anyhow::anyhow!("FPGA abort readback: {e:?}"))
        }) {
            Ok(()) => return Ok(()),
            Err(e) if started.elapsed() >= Duration::from_millis(100) => {
                return Err(e.context("FPGA abort could not be confirmed"));
            }
            Err(_) => std::thread::sleep(Duration::from_millis(1)),
        }
    }
}
struct CoreRegisters<'a> { device: &'a mut Device<'static>, io_error: &'a mut bool, observed_status: Option<&'a mut Option<u32>> }
impl overlap::Registers for CoreRegisters<'_> {
    type Error = anyhow::Error;
    fn read(&mut self, offset: u32) -> Result<u32, Self::Error> {
        let value = self.device.fpga.read_u32(BASE + offset).map_err(|e| { *self.io_error = true; anyhow::Error::from(e) })?;
        if offset == 0x10 { if let Some(status) = self.observed_status.as_deref_mut() { *status = Some(value); } }
        Ok(value)
    }
    fn write(&mut self, offset: u32, value: u32) -> Result<(), Self::Error> {
        self.device.fpga.write_u32(BASE + offset, value).map_err(|e| { *self.io_error = true; e.into() })
    }
}
fn begin(h: protocol::Header, core: CoreMode, fatal: &mut bool, accessed: &mut bool,
    busy_diag: &mut Option<telemetry::BusyDiagnostic>) -> anyhow::Result<()> {
    access(|d| {
        *accessed = true;
        if core.mode == overlap::Mode::Overlap {
            if let Err(e) = identity(d) { *fatal = true; return Err(e); }
        } else { identity(d)?; }
        let caps = d.fpga.read_u32(BASE + 8).map_err(|e| {
            if core.mode == overlap::Mode::Overlap { *fatal = true; }
            anyhow::Error::from(e)
        })?;
        anyhow::ensure!(protocol::fpga_supports_dimensions(h.width, h.height, caps),
            "FPGA does not support the requested JPEG dimensions");
        if core.mode == overlap::Mode::Overlap {
            let metadata = overlap::Metadata { id: h.id, length: h.length,
                dimensions: ((h.width as u32) << 16) | h.height as u32, crc: h.crc };
            let mut io_error = false;
            let mut decision_status = None;
            let result = overlap::start_overlap(&mut CoreRegisters { device: d, io_error: &mut io_error, observed_status: Some(&mut decision_status) },
                metadata, core.max_bytes, core.slot_bytes);
            if matches!(&result, Err(overlap::StartError::Policy(overlap::PolicyError::Busy | overlap::PolicyError::Receiving))) {
                *busy_diag = Some(read_busy_diagnostic(d, decision_status));
            }
            if io_error || matches!(&result, Err(overlap::StartError::FatalFault(_))) { *fatal = true; }
            return result.map_err(|e| anyhow::anyhow!("FPGA overlap start: {e:?}"));
        }
        let mut core_status = d.fpga.read_u32(BASE + 0x10)?;
        if core_status & ((1 << 2) | (1 << 3)) != 0 {
            identity(d)?;
            d.fpga.write_u32(BASE + 0x24, overlap::CMD_GLOBAL_ABORT)?;
            core_status = d.fpga.read_u32(BASE + 0x10)?;
        }
        if let Err(e) = overlap::can_start(core.mode, core_status, 0, h.length, core.max_bytes, 0) {
            if matches!(e, overlap::PolicyError::Busy | overlap::PolicyError::Receiving) {
                *busy_diag = Some(read_busy_diagnostic(d, Some(core_status)));
            }
            anyhow::bail!("Decoder unavailable: {e:?}");
        }
        d.fpga.write_u32(BASE + 0x14, h.id)?;
        d.fpga.write_u32(BASE + 0x18, h.length)?;
        d.fpga
            .write_u32(BASE + 0x1C, ((h.width as u32) << 16) | h.height as u32)?;
        d.fpga.write_u32(BASE + 0x20, h.crc)?;
        d.fpga.write_u32(BASE + 0x24, 1)?;
        Ok(())
    })
}
// Individual reads are later observations, not an atomic frame snapshot.
// Only call after failed admission, never on the successful packet path.
fn read_busy_diagnostic(d: &mut Device<'static>, decision_status: Option<u32>) -> telemetry::BusyDiagnostic {
    telemetry::BusyDiagnostic { decision_status,
        accepted_after: d.fpga.read_u32(BASE + 0x2c).ok(),
        decoded_after: d.fpga.read_u32(BASE + 0x30).ok(),
        presented_after: d.fpga.read_u32(BASE + 0x34).ok(),
        ..Default::default() }
}
fn commit_frame(core: CoreMode, generation: u32, fatal_core: &mut bool) -> anyhow::Result<()> {
let mut commit_accessed = false;
let commit_result = access(|d| {
    commit_accessed = true;
    identity(d)?;
    anyhow::ensure!(protocol::generation_is_current(generation, GENERATION.load(Ordering::Acquire)), "Source cancelled before commit write");
    let before = d.fpga.read_u32(BASE + 0x2c)?;
    d.fpga.write_u32(BASE + 0x24, 4)?;
    let accepted = d.fpga.read_u32(BASE + 0x2c)?;
    let (outcome, flags) = if core.mode == overlap::Mode::Overlap {
        let causes = d.fpga.read_u32(BASE + 0x80)?;
        (overlap::commit_outcome(before, accepted, causes), causes)
    } else {
        let status = d.fpga.read_u32(BASE + 0x10)?;
        (overlap::legacy_commit_outcome(before, accepted, status), status)
    };
    Ok((outcome, flags))
});
let (outcome, flags) = match commit_result {
    Ok(result) => result,
    Err(e) => { if core.mode == overlap::Mode::Overlap && commit_accessed { *fatal_core = true; } return Err(e); }
};
    match outcome {
        overlap::CommitOutcome::Accepted => {},
        overlap::CommitOutcome::Rejected => anyhow::bail!("FPGA rejected or did not confirm frame commit: flags=0x{flags:x}"),
        overlap::CommitOutcome::Fatal => {
            *fatal_core = true;
            anyhow::bail!("FPGA decoder/transport fault during commit: causes=0x{flags:x}");
        }
    }
Ok(())
}
enum ForwardError { Busy, Credits, Fpga(anyhow::Error) }
fn forward(payload: &[u8]) -> Result<(u32, u32, u64, u64), ForwardError> {
    let start = Instant::now();
    let deadline = start + Duration::from_millis(8);
    loop {
        if let Some(mut d) = Device::try_lock() {
        let lock_us = start.elapsed().as_micros() as u64;
        identity(&mut d).map_err(ForwardError::Fpga)?;
        let credits = d.fpga.read_u32(BASE + 0x0C).map_err(|e| ForwardError::Fpga(e.into()))?;
        if credits < payload.len() as u32 { return Err(ForwardError::Credits); }
        let qspi_start = Instant::now();
        d.fpga.spi_write(
            Some(Hertz(stream_write_hz())),
            SpiCommand {
                word_size: FpgaSpiWordSize::Bits8,
                byte_swap: false,
                increment_address: false,
            },
            BASE + 0x100,
            payload,
        ).map_err(|e| ForwardError::Fpga(e.into()))?;
        return Ok((credits - payload.len() as u32, credits, lock_us,
                   qspi_start.elapsed().as_micros() as u64));
        }
        if Instant::now() >= deadline { return Err(ForwardError::Busy); }
        std::thread::sleep(Duration::from_micros(250));
    }
}
struct DmaBuffer(*mut u8, usize);
// A DmaBuffer owns one heap allocation, is never cloned, and may only be used
// by the thread currently holding it. Moving it through the pool is safe.
unsafe impl Send for DmaBuffer {}
impl DmaBuffer {
    fn new(len: usize) -> anyhow::Result<Self> {
        let ptr = unsafe {
            esp_idf_svc::sys::heap_caps_malloc(
                len,
                (esp_idf_svc::sys::MALLOC_CAP_DMA | esp_idf_svc::sys::MALLOC_CAP_INTERNAL) as u32,
            )
        } as *mut u8;
        anyhow::ensure!(!ptr.is_null(), "No internal DMA memory");
        Ok(Self(ptr, len))
    }
    fn bytes(&mut self) -> &mut [u8] {
        unsafe { std::slice::from_raw_parts_mut(self.0, self.1) }
    }
}
impl Drop for DmaBuffer {
    fn drop(&mut self) {
        unsafe { esp_idf_svc::sys::heap_caps_free(self.0.cast()) }
    }
}

struct RxPacket { buffer: DmaBuffer, len: usize, from: SocketAddr, arrival_us: u64 }
struct RxPump {
    queue: rx_queue::Consumer<RxPacket>, stop: Arc<AtomicBool>,
    thread: Option<std::thread::JoinHandle<()>>,
}
impl Drop for RxPump {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Release);
        if let Some(thread) = self.thread.take() { let _ = thread.join(); }
    }
}
impl RxPump {
    #[inline(never)]
    fn new(socket: Arc<UdpSocket>, host: Ipv4Addr) -> anyhow::Result<Self> {
        let depth = QUEUE_DEPTH.load(Ordering::Acquire) as usize;
        let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
        let free = unsafe { esp_idf_svc::sys::heap_caps_get_free_size(caps) };
        let largest = unsafe { esp_idf_svc::sys::heap_caps_get_largest_free_block(caps) };
        let required = 24 * 1024 + batch::CAPACITY + (depth + 1) * (protocol::HEADER + protocol::CHUNK + 1);
        anyhow::ensure!(free as usize >= required && largest >= 8 * 1024,
            "Insufficient internal memory for bounded network queue");
        if depth == 32 {
            let dma_caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_DMA) as u32;
            let dma_free = unsafe { esp_idf_svc::sys::heap_caps_get_free_size(dma_caps) };
            let dma_largest = unsafe { esp_idf_svc::sys::heap_caps_get_largest_free_block(dma_caps) };
            log::info!("USB_TRACE queue32_dma_preflight free={} largest={} required_free={} required_largest={}",
                dma_free, dma_largest, telemetry::QUEUE32_REQUIRED_DMA, telemetry::QUEUE32_REQUIRED_LARGEST);
            anyhow::ensure!(telemetry::queue32_dma_guard(dma_free as usize, dma_largest as usize),
                "Insufficient DMA memory for 32-slot queue (free={dma_free}, largest={dma_largest})");
        }
        let mut slots = Vec::new();
        slots.try_reserve_exact(depth).map_err(|_| anyhow::anyhow!("No memory for queue metadata"))?;
        for _ in 0..depth {
            slots.push(RxPacket { buffer: DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)?,
                len: 0, from: SocketAddr::from(([0, 0, 0, 0], 0)), arrival_us: 0 });
        }
        let mut scratch = DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)?;
        let (producer, queue) = rx_queue::bounded(slots, depth);
        *QUEUE_DROP.lock().unwrap() = QueueDrop { capacity: depth as u32, ..QueueDrop::default() };
        CONSUMER_SEEN.store(false, Ordering::Release);
        CONSUMER_BUSY.store(false, Ordering::Release);
        *PRODUCER_TIMING.lock().unwrap() = telemetry::ProducerTiming::default();
        *QUEUE_COUNTS.get_or_init(|| Mutex::new(None)).lock().unwrap() = Some(queue.counts.clone());
        let stop = Arc::new(AtomicBool::new(false));
        let worker_stop = stop.clone();
        let thread = std::thread::Builder::new().name("StreamRx".into()).stack_size(4096)
            .spawn(move || {
                QUEUE_DROP.lock().unwrap().producer_priority = unsafe {
                    esp_idf_svc::sys::uxTaskPriorityGet(std::ptr::null_mut()) };
                let mut stack_probe = Instant::now();
                let mut timing_probe = Instant::now();
                let mut timing = telemetry::ProducerTiming { min_gap_us: u64::MAX, ..telemetry::ProducerTiming::default() };
                while !worker_stop.load(Ordering::Acquire) {
                    let mut packet = producer.take().ok();
                    let bytes = match packet.as_mut() { Some(p) => p.buffer.bytes(), None => scratch.bytes() };
                    match socket.recv_from(bytes) {
                        Ok((n, from)) if from.ip() == std::net::IpAddr::V4(host) => {
                            let received_at = monotonic_us();
                            let previous_us = if timing.datagrams == 0 { received_at } else { timing.last_us };
                            timing.observe(received_at);
                            // A buffer may have been recycled while recv_from was
                            // waiting in scratch mode. Recover it before dropping.
                            if packet.is_none() {
                                if let Ok(mut free) = producer.take() {
                                    free.buffer.bytes()[..n].copy_from_slice(&scratch.bytes()[..n]);
                                    packet = Some(free);
                                }
                            }
                            if let Some(mut p) = packet {
                                p.len = n; p.from = from; p.arrival_us = received_at;
                                if let Err(e) = producer.submit(p) {
                                    producer.discard();
                                    let mut p = match e { mpsc::TrySendError::Full(p) | mpsc::TrySendError::Disconnected(p) => p };
                                    record_queue_drop(&p.buffer.bytes()[..n], received_at, previous_us,
                                        producer.counts.queued.load(Ordering::Relaxed));
                                    producer.recycle(p);
                                }
                            } else {
                                producer.discard();
                                record_queue_drop(&scratch.bytes()[..n], received_at, previous_us,
                                    producer.counts.queued.load(Ordering::Relaxed));
                            }
                        }
                        Ok(_) => { if let Some(p) = packet { producer.recycle(p); } }
                        Err(e) if matches!(e.kind(), std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut) => {
                            if let Some(p) = packet { producer.recycle(p); }
                        }
                        Err(_) => { if let Some(p) = packet { producer.recycle(p); } QUEUE_DROP.lock().unwrap().socket_errors += 1; break; }
                    }
                    if stack_probe.elapsed() >= Duration::from_secs(1) {
                        QUEUE_DROP.lock().unwrap().producer_stack_low_water = unsafe {
                            esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) };
                        stack_probe = Instant::now();
                    }
                    if timing_probe.elapsed() >= Duration::from_millis(100) {
                        *PRODUCER_TIMING.lock().unwrap() = timing;
                        timing_probe = Instant::now();
                    }
                }
                *PRODUCER_TIMING.lock().unwrap() = timing;
            })?;
        Ok(Self { queue, stop, thread: Some(thread) })
    }
}
// Prevent streaming or core replacement during an idle-only benchmark.
struct BenchGuard(crate::core_access::MaintenanceGuard);
impl Drop for BenchGuard { fn drop(&mut self) { BENCH_ACTIVE.store(false, Ordering::Release); } }
fn begin_idle_benchmark() -> anyhow::Result<BenchGuard> {
    let maintenance=crate::core_access::MaintenanceGuard::acquire(crate::core_coordinator::Maintenance::Benchmark)?;
    {
        let _control = CONTROL.lock().unwrap();
        anyhow::ensure!(!RATE_CHANGING.load(Ordering::Acquire), "QSPI rate change already running");
        anyhow::ensure!(!has_session() && !RESTORING.load(Ordering::Acquire),
            "Disconnect streaming and wait for it to stop before benchmark");
        anyhow::ensure!(!BENCH_ACTIVE.swap(true, Ordering::AcqRel), "Benchmark already running");
    }
    Ok(BenchGuard(maintenance))
}
pub fn benchmark_crc() -> anyhow::Result<()> {
    let _guard = begin_idle_benchmark()?;
    let mut buf = DmaBuffer::new(4096)?;
    for (i, byte) in buf.bytes().iter_mut().enumerate() { *byte = i as u8; }
    const REPEATS: usize = 256;
    let started = Instant::now();
    let mut slow = !0u32;
    for _ in 0..REPEATS { slow = protocol::crc_update_bitwise(slow, buf.bytes()); }
    let slow_us = started.elapsed().as_micros();
    let started = Instant::now();
    let mut fast = !0u32;
    for _ in 0..REPEATS { fast = protocol::crc_update(fast, buf.bytes()); }
    let fast_us = started.elapsed().as_micros();
    let stack = unsafe { esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) };
    log::info!("USB_CRC bytes={} bitwise_us={} table_us={} bitwise={:08x} table={:08x} usb_stack_low_water={}", REPEATS * 4096, slow_us, fast_us, !slow, !fast, stack);
    anyhow::ensure!(slow == fast, "CRC implementations disagree");
    Ok(())
}
fn flush_batch(buf: &mut DmaBuffer, batch: &mut batch::Batch, trace: &mut telemetry::FrameTrace,
    core: CoreMode, fatal: &mut bool) -> anyhow::Result<()> {
    let len = batch.len();
    if len == 0 { return Ok(()); }
    let (credits, before, lock_us, qspi_us) = match batch.flush(buf.bytes(), forward) {
        Ok(Some(v)) => v,
        Ok(None) => return Ok(()),
        Err(ForwardError::Busy) => anyhow::bail!("Device mutex timed out before QSPI; frame dropped"),
        Err(ForwardError::Credits) => anyhow::bail!("FPGA remaining frame bytes exhausted"),
        Err(ForwardError::Fpga(e)) => { if core.mode == overlap::Mode::Overlap { *fatal = true; } return Err(e); }
    };
    trace.transfer(len as u32, before, lock_us, qspi_us);
    let mut stats = STATS.lock().unwrap();
    stats.credits = credits;
    stats.bytes += len as u64;
    Ok(())
}
/// Exercise the FPGA's optional discard sink without altering any video frame.
pub fn benchmark_qspi() -> anyhow::Result<()> {
    let mut guard = begin_idle_benchmark()?;
    access(|d| {
        identity(d)?;
        anyhow::ensure!(d.fpga.read_u32(BASE + 8)? & 8 != 0,
            "FPGA has no isolated QSPI benchmark sink");
        Ok(())
    })?;
    let mut buf = DmaBuffer::new(4096)?;
    for (i, byte) in buf.bytes().iter_mut().enumerate() { *byte = i as u8; }
    const TOTAL: usize = 1024 * 1024;
    let mut crc = !0u32;
    for _ in 0..(TOTAL / 4096) { crc = protocol::crc_update(crc, buf.bytes()); }
    let expected_crc = !crc;
    for size in [256usize, 1024, 4096] {
        let overflow_before = access(|d| {
            let overflow = d.fpga.read_u32(BASE + 0x50)?;
            guard.0.side_effects_begin();
            d.fpga.write_u32(BASE + 0x64, 1)?;
            anyhow::ensure!(d.fpga.read_u32(BASE + 0x70)? & 1 != 0,
                "FPGA sink did not start (core busy)");
            Ok(overflow)
        })?;
        let started = Instant::now();
        let result = (|| -> anyhow::Result<()> {
            for _ in 0..TOTAL / size {
                access(|d| d.fpga.spi_write(Some(Hertz(40_000_000)), SpiCommand {
                    word_size: FpgaSpiWordSize::Bits8, byte_swap: false,
                    increment_address: false,
                }, BASE + 0x104, &buf.bytes()[..size]).map_err(Into::into))?;
            }
            Ok(())
        })();
        let elapsed_us = started.elapsed().as_micros() as u64;
        // Always stop the sink, even after a transfer failure. The ordered read
        // after STOP observes all preceding QSPI writes through the CDC bridge.
        let final_state = access(|d| {
            d.fpga.write_u32(BASE + 0x64, 2)?;
            let active = d.fpga.read_u32(BASE + 0x70)?;
            let count = d.fpga.read_u32(BASE + 0x68)?;
            let actual_crc = d.fpga.read_u32(BASE + 0x6c)?;
            let overflow = d.fpga.read_u32(BASE + 0x50)?;
            Ok((active, count, actual_crc, overflow))
        })?;
        let (active, count, actual_crc, overflow) = final_state;
        if active&1==0{guard.0.quiescent();}
        result?;
        log::info!("USB_QSPI size={} bytes={} elapsed_us={} crc={:08x} expected_crc={:08x} overflow_before={} overflow_after={} active={}",
            size, count, elapsed_us, actual_crc, expected_crc, overflow_before, overflow, active);
        anyhow::ensure!(active & 1 == 0 && count == TOTAL as u32 && actual_crc == expected_crc
            && overflow == overflow_before, "QSPI benchmark count/CRC/overflow mismatch");
    }
    Ok(())
}
fn note_drop(id: u32, last: &mut Option<u32>) {
    if *last != Some(id) {
        STATS.lock().unwrap().dropped += 1;
        *last = Some(id);
    }
}
fn reply(socket: &UdpSocket, peer: SocketAddr, status: u8, id: u32, capture: u64, release: bool) {
    let s = stats();
    let b = protocol::feedback(
        status,
        if release {
            0
        } else {
            BUTTONS.load(Ordering::Relaxed)
        },
        id,
        s.credits,
        s.received,
        s.dropped,
        capture,
    );
    let _ = socket.send_to(&b, peer);
}
struct ConsumerPriorityGuard { previous: u32 }
impl ConsumerPriorityGuard {
    fn enter() -> anyhow::Result<Self> {
        let previous = unsafe { esp_idf_svc::sys::uxTaskPriorityGet(std::ptr::null_mut()) };
        let selected = telemetry::consumer_priority(previous, CONSUMER_BOOST.load(Ordering::Acquire))
            .ok_or_else(|| anyhow::anyhow!("Cannot boost non-default streaming task priority"))?;
        if selected != previous {
            // null selects this streaming worker only, never lwIP/Wi-Fi/UI.
            unsafe { esp_idf_svc::sys::vTaskPrioritySet(std::ptr::null_mut(), selected) };
        }
        QUEUE_DROP.lock().unwrap().consumer_priority = selected;
        Ok(Self { previous })
    }
}
impl Drop for ConsumerPriorityGuard {
    fn drop(&mut self) {
        unsafe { esp_idf_svc::sys::vTaskPrioritySet(std::ptr::null_mut(), self.previous) };
    }
}
struct ConsumerBusyGuard;
impl Drop for ConsumerBusyGuard {
    fn drop(&mut self) { CONSUMER_BUSY.store(false, Ordering::Release); }
}
struct OverlapSessionGuard { mode: overlap::Mode, armed: bool }
impl Drop for OverlapSessionGuard {
    fn drop(&mut self) {
        if self.armed && self.mode == overlap::Mode::Overlap {
            if let Err(e) = abort(self.mode, true) { log::error!("Overlap teardown could not confirm FPGA abort: {}", e); }
        }
        OVERLAP_ACTIVE.store(false, Ordering::Release);
    }
}
#[inline(never)]
fn session(host: Ipv4Addr, generation: u32) -> anyhow::Result<()> {
    // A new receiver permits a restarted sender to begin again at frame ID zero.
    let mut receiver = protocol::Receiver::default();
    let core = prepare_mode(generation)?;
    OVERLAP_ACTIVE.store(core.mode == overlap::Mode::Overlap, Ordering::Release);
    let mut overlap_session = OverlapSessionGuard { mode: core.mode, armed: true };
    wait_for_quiescent_epoch(core, generation)?;
    let socket = Arc::new(UdpSocket::bind("0.0.0.0:5533")?);
    socket.set_read_timeout(Some(Duration::from_millis(20)))?;
    let pump = RxPump::new(socket.clone(), host)?;
    let mut batch_buffer = DmaBuffer::new(batch::CAPACITY)?;
    // This guard drops/joins before queue teardown, ACTIVE release or core replacement.
    let _av = match audio::Guard::start(host, generation) {
        Ok(guard) => Some(guard),
        Err(error) => { log::warn!("USB_TRACE av result=listener_unavailable reason={}", error); None }
    };
    let mut batch = batch::Batch::default();
    // Spawn the producer before changing this task, so its ESP pthread
    // configuration remains independent of the consumer experiment.
    let _priority = ConsumerPriorityGuard::enter()?;
    let (mut peer, mut last, mut heartbeat, mut report) =
        (None, Instant::now(), Instant::now(), Instant::now());
    let (mut active, mut id, mut capture) = (false, 0, 0);
    // Heartbeats describe the last completed frame, never an in-flight frame.
    let mut completed = protocol::CompletedFrame::default();
    let mut last_dropped_id = None;
    let baseline = stats();
    let (mut prev_frames, mut prev_display, mut prev_bytes) =
        (baseline.received, None::<u32>, baseline.bytes);
    let mut last_buttons = 0u16;
    let mut button_poll = Instant::now();
    let mut last_polled = None;
    let mut trace = telemetry::FrameTrace::default();
    let mut last_commit_us = None;
    status("TEST MJPEG UDP5533; optional AV UDP5534");
    while GENERATION.load(Ordering::Acquire) == generation {
        if batch.due(monotonic_us()) && last.elapsed() <= TIMEOUT {
            let mut fatal = false;
            if let Err(e) = flush_batch(&mut batch_buffer, &mut batch, &mut trace, core, &mut fatal) {
                batch.clear();
                let recovery = abort(core.mode, fatal);
                receiver.abort(); active = false;
                note_drop(id, &mut last_dropped_id);
                trace.finish(monotonic_us());
                TRACE.lock().unwrap().dropped = trace;
                if let Some(p) = peer { reply(&socket, p, 1, id, capture, false); }
                recovery.context("Timed DMA flush recovery unconfirmed")?;
                if fatal { return Err(e.context("Timed DMA flush failed")); }
                let mut stats = STATS.lock().unwrap();
                stats.errors += 1;
                stats.status = e.to_string();
            }
        }
        let wait = if batch.is_empty() { Duration::from_millis(20) } else { Duration::from_millis(1) };
        match pump.queue.recv_timeout(wait) {
            Ok(mut packet) => {
                let process_started = monotonic_us();
                CONSUMER_DEQUEUE_US.store(process_started as u32, Ordering::Relaxed);
                CONSUMER_BUSY.store(true, Ordering::Release);
                CONSUMER_SEEN.store(true, Ordering::Release);
                let _busy = ConsumerBusyGuard;
                let from = packet.from;
                if peer.is_some_and(|p| p != from) {
                    if !protocol::can_rebind_peer(active, last.elapsed().as_millis() as u64)
                        || !rebind_when_quiescent(core).unwrap_or(false) {
                        pump.queue.recycle(packet);
                        continue;
                    }
                    if let (Some(old_peer), Some((old_id, old_capture))) = (peer, completed.success_identity()) {
                        reply(&socket, old_peer, 0, old_id, old_capture, true);
                    }
                    receiver = protocol::Receiver::default();
                    completed = protocol::CompletedFrame::default();
                }
                peer = Some(from);
                last = Instant::now();
                let bytes = &packet.buffer.bytes()[..packet.len];
                let expected_offset = receiver.expected_offset();
                let mut start_attempted = false;
                let mut fatal_core = false;
                if let Ok(h) = protocol::Header::parse(bytes) {
                    let now = packet.arrival_us;
                    if h.offset == 0 {
                        // Preserve the superseded incomplete frame before
                        // resetting the trace for the next SOF.
                        if let Some(old) = trace.superseded(active, now) {
                            TRACE.lock().unwrap().dropped = old;
                        }
                        trace.start(h.id, now);
                    }
                    if trace.valid && trace.id == h.id {
                        trace.packet(now);
                        trace.queued(process_started.saturating_sub(now));
                        trace.consumer_started(process_started);
                    }
                }
                let result = (|| -> anyhow::Result<bool> {
                    let (h, done) = receiver
                        .accept(bytes)
                        .map_err(|e| anyhow::anyhow!("Invalid/lost frame: {e:?}"))?;
                    let previous_id = id;
                    id = h.id;
                    capture = h.capture_us;
                    anyhow::ensure!(protocol::generation_is_current(generation, GENERATION.load(Ordering::Acquire)),
                        "Streaming cancelled");
                    if h.offset == 0 {
                        if active {
                            batch.clear();
                            if let Err(e) = abort(core.mode, false) {
                                fatal_core = true;
                                return Err(e);
                            }
                            note_drop(previous_id, &mut last_dropped_id);
                        }
                        let begin_at = Instant::now();
                        let begin_us = monotonic_us();
                        start_attempted = true;
                        let mut begin_accessed = false;
                        let mut busy_diag = None;
                        let begin_result = begin(h, core, &mut fatal_core, &mut begin_accessed, &mut busy_diag);
                        trace.begin_us = begin_at.elapsed().as_micros() as u64;
                        if let Some(mut diag) = busy_diag {
                            diag.sof_dequeue_us = process_started;
                            diag.begin_us = begin_us;
                            diag.prior_commit_confirmed_us = last_commit_us;
                            log::warn!("USB_TRACE decoder_busy frame={} mode={:?} diagnostic={:?} since_prior_commit_confirmed_us={:?} (counter reads are later independent snapshots)",
                                h.id, core.mode, diag, diag.since_prior_commit_confirmed_us());
                        }
                        if begin_result.is_err() && begin_accessed && core.mode == overlap::Mode::Overlap {
                            let causes = access(|d| Ok(d.fpga.read_u32(BASE + 0x80)?));
                            fatal_core |= causes.map_or(true, |c| overlap::fault_action(c) == overlap::FaultAction::StopSession);
                        }
                        begin_result?;
                        active = true;
                    }
                    let payload = &bytes[protocol::HEADER..];
                    if !batch.fits(payload.len()) || batch.due(monotonic_us()) {
                        flush_batch(&mut batch_buffer, &mut batch, &mut trace, core, &mut fatal_core)?;
                    }
                    batch.append(batch_buffer.bytes(), payload, monotonic_us())
                        .map_err(|_| anyhow::anyhow!("Invalid DMA batch"))?;
                    if done || batch.len() == batch::CAPACITY {
                        flush_batch(&mut batch_buffer, &mut batch, &mut trace, core, &mut fatal_core)?;
                    }
                    if done {
                        anyhow::ensure!(protocol::generation_is_current(generation, GENERATION.load(Ordering::Acquire)),
                            "Streaming cancelled before commit");
                        commit_frame(core, generation, &mut fatal_core)?;
                        last_commit_us = Some(monotonic_us());
                        anyhow::ensure!(protocol::generation_is_current(generation, GENERATION.load(Ordering::Acquire)),
                            "Streaming cancelled during commit");
                        active = false;
                        STATS.lock().unwrap().received += 1;
                        completed.commit(h);
                        trace.finish(monotonic_us());
                    }
                    Ok(done)
                })();
                trace.processing(monotonic_us().saturating_sub(process_started));
                match result {
                    Ok(true) => { TRACE.lock().unwrap().completed = trace; reply(&socket, from, 0, id, capture, false); },
                    Ok(false) => {}
                    Err(mut e) => {
                        batch.clear();
                        let inflight = active.then_some((id, capture));
                        let offending = protocol::Header::parse(bytes).ok();
                        let aborted = if fatal_core {
                            abort(core.mode, true)
                        } else if active || (start_attempted && core.mode == overlap::Mode::Overlap) {
                            abort(core.mode, false)
                        } else { Ok(()) };
                        if let Err(abort_error) = aborted {
                            fatal_core = true;
                            e = e.context(format!("FPGA recovery unconfirmed: {abort_error}"));
                        }
                        receiver.abort();
                        active = false;
                        if let Some(h) = offending {
                            if last_dropped_id != Some(h.id) {
                                log::warn!("Streaming frame drop: id={} offset={} expected={:?} reason={}", h.id, h.offset, expected_offset, e);
                                if trace.valid && trace.id == h.id {
                                    trace.gap(expected_offset, h.offset);
                                    trace.finish(monotonic_us());
                                    TRACE.lock().unwrap().dropped = trace;
                                }
                            }
                            note_drop(h.id, &mut last_dropped_id);
                        }
                        let mut s = STATS.lock().unwrap();
                        s.errors += 1;
                        s.status = e.to_string();
                        drop(s);
                        if let Some((failed_id, failed_capture)) = protocol::failure_identity(offending, inflight) {
                            reply(&socket, from, 1, failed_id, failed_capture, false);
                        }
                        if fatal_core { return Err(e); }
                    }
                }
                // Release the device mutex between every DMA chunk; let UI/input run.
                std::thread::yield_now();
                pump.queue.recycle(packet);
            }
            Err(mpsc::RecvTimeoutError::Timeout) => {}
            Err(mpsc::RecvTimeoutError::Disconnected) => {
                let recovery = abort(core.mode, true);
                if let Some(p) = peer {
                    reply(&socket, p, 3, id, capture, true);
                }
                recovery.context("UDP receive worker stopped; FPGA recovery unconfirmed")?;
                anyhow::bail!("UDP receive worker stopped");
            }
        }
        if active && last.elapsed() > TIMEOUT {
            batch.clear();
            if let Err(e) = abort(core.mode, false) {
                note_drop(id, &mut last_dropped_id);
                if let Some(p) = peer { reply(&socket, p, 1, id, capture, true); }
                return Err(e.context("Timed-out frame recovery unconfirmed"));
            }
            receiver.abort();
            active = false;
            note_drop(id, &mut last_dropped_id);
        }
        // Poll as a fallback if an FPGA button interrupt is missed. Keep the
        // device lock nonblocking so this never stalls the UI or packet path.
        if button_poll.elapsed() >= Duration::from_millis(50) {
            if let Some(mut d) = Device::try_lock() {
                if let Ok(state) = d.get_input_state() {
                    if last_polled.as_ref() != Some(&state) {
                        last_polled = Some(state.clone());
                        crate::ui::send(crate::ui::Message::InputState(state));
                    }
                }
            }
            button_poll = Instant::now();
        }
        let buttons = BUTTONS.load(Ordering::Relaxed);
        if buttons != last_buttons || heartbeat.elapsed() >= Duration::from_millis(250) {
            last_buttons = buttons;
            if let (Some(p), Some((finished_id, finished_capture))) = (peer, completed.success_identity()) {
                reply(&socket, p, 0, finished_id, finished_capture, last.elapsed() > TIMEOUT);
            }
            heartbeat = Instant::now();
        }
        if report.elapsed() >= Duration::from_secs(1) {
            // A decoder can fail after COMMIT when no further UDP frame arrives.
            // Stop the session on a hard cause; the guard performs global abort.
            if core.mode == overlap::Mode::Overlap {
                if let Ok(causes) = access(|d| Ok(d.fpga.read_u32(BASE + 0x80)?)) {
                    if overlap::fault_action(causes) == overlap::FaultAction::StopSession {
                        if let Some(p) = peer { reply(&socket, p, 3, id, capture, true); }
                        anyhow::bail!("FPGA asynchronous decoder/transport fault: causes=0x{causes:x}");
                    }
                }
            }
            QUEUE_DROP.lock().unwrap().consumer_stack_low_water = unsafe {
                esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) };
            if let Ok((decoded, displayed, credits)) = access(|d| {
                Ok((
                    d.fpga.read_u32(BASE + 0x30)?,
                    d.fpga.read_u32(BASE + 0x34)?,
                    d.fpga.read_u32(BASE + 0x0C)?,
                ))
            }) {
                let mut s = STATS.lock().unwrap();
                s.decoded = decoded;
                s.displayed = displayed;
                s.credits = credits;
            }
            let mut s = STATS.lock().unwrap();
            let elapsed_us = report.elapsed().as_micros().max(1) as u64;
            s.rx_fps =
                ((s.received.wrapping_sub(prev_frames) as u64) * 1_000_000 / elapsed_us) as u32;
            s.display_fps = prev_display.map_or(0, |previous| {
                ((s.displayed.wrapping_sub(previous) as u64) * 1_000_000 / elapsed_us) as u32
            });
            s.bitrate = ((s.bytes - prev_bytes) * 8 * 1000 / elapsed_us) as u32;
            prev_frames = s.received;
            prev_display = Some(s.displayed);
            prev_bytes = s.bytes;
            report = Instant::now();
        }
    }
    let unfinished = active.then_some((id, capture));
    if active {
        let recovery = abort(core.mode, false);
        note_drop(id, &mut last_dropped_id);
        if let Err(e) = recovery {
            if let Some(p) = peer { reply(&socket, p, 1, id, capture, true); }
            return Err(e.context("Cancelled frame recovery unconfirmed"));
        }
    }
    if let (Some(p), Some((status, frame_id, frame_capture))) = (peer, protocol::shutdown_feedback(&completed, unfinished)) {
        reply(&socket, p, status, frame_id, frame_capture, true);
    }
    if core.mode == overlap::Mode::Overlap {
        abort(core.mode, true).context("Session teardown FPGA recovery unconfirmed")?;
    }
    overlap_session.armed = false;
    Ok(())
}
