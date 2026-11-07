//! Lazy network-session AV companion. No video queue or DAC ownership.
use super::{
    adpcm,
    audio_diag::{Diagnostics, Reason, SnapshotFailure},
    audio_io::{self, Feeder, Phase, ResultEvent},
    audio_snapshot, av_power_save,
    av_session::{Event, Session},
    av_wire::{self, Kind},
    compressed_queue::{self, Meta, Queue},
    service_policy::{self, Checkpoint, Pass, Step},
    monotonic_us, Device, DmaBuffer, Ordering, BASE, BUTTONS, GENERATION,
};
use crate::device::drivers::fpga::{FpgaSpiWordSize, SpiCommand};
use esp_idf_svc::hal::units::Hertz;
use std::{
    net::{Ipv4Addr, SocketAddr, UdpSocket},
    sync::{
        atomic::{AtomicBool, AtomicU32},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};
#[derive(Clone, Copy, Debug, Default)]
pub struct Stats {
    pub active: bool,
    pub audio_enabled: bool,
    pub supported: bool,
    pub accepted: u32,
    pub rejected: u32,
    pub gaps: u32,
    pub malformed: u32,
    pub socket_errors: u32,
    pub valid_snapshot: bool,
    pub queued_frames: u32,
    pub played: u32,
    pub underruns: u32,
    pub build: u32,
    pub stack_low_water: u32,
    pub ps_initial: u32,
    pub ps_actual: u32,
    pub ps_entry_errors: u32,
    pub ps_restore_errors: u32,
}
static DIAGNOSTICS: Mutex<Diagnostics> = Mutex::new(Diagnostics::new());
static DIAG_PAGE: AtomicU32 = AtomicU32::new(0);
static STATS: Mutex<Stats> = Mutex::new(Stats {
    active: false,
    audio_enabled: false,
    supported: false,
    accepted: 0,
    rejected: 0,
    gaps: 0,
    malformed: 0,
    socket_errors: 0,
    valid_snapshot: false,
    queued_frames: 0,
    played: 0,
    underruns: 0,
    build: 0,
    stack_low_water: 0,
    ps_initial: 0,
    ps_actual: 0,
    ps_entry_errors: 0,
    ps_restore_errors: 0,
});
pub static RECOVERY_FAILED: AtomicBool = AtomicBool::new(false);
pub fn stats() -> Stats {
    let mut stats = *STATS.lock().unwrap();
    stats.ps_initial = PS_INITIAL.load(Ordering::Relaxed);
    stats.ps_actual = PS_ACTUAL.load(Ordering::Relaxed);
    stats.ps_entry_errors = PS_ENTRY_ERRORS.load(Ordering::Relaxed);
    stats.ps_restore_errors = PS_RESTORE_ERRORS.load(Ordering::Relaxed);
    stats
}
static PS_INITIAL: AtomicU32 = AtomicU32::new(u32::MAX);
static PS_ACTUAL: AtomicU32 = AtomicU32::new(u32::MAX);
static PS_ENTRY_ERRORS: AtomicU32 = AtomicU32::new(0);
static PS_RESTORE_ERRORS: AtomicU32 = AtomicU32::new(0);
struct Radio {
    generation: u32,
}
impl av_power_save::Radio for Radio {
    fn get(&mut self) -> Result<u32, ()> {
        let mut mode = 0;
        let rc = unsafe { esp_idf_svc::sys::esp_wifi_get_ps(&mut mode) };
        log::info!(
            "USB_TRACE av_ps generation={} op=get rc={} actual={:?}",
            self.generation,
            rc,
            if rc == 0 { Some(mode) } else { None }
        );
        if rc == 0 {
            Ok(mode as u32)
        } else {
            Err(())
        }
    }
    fn set(&mut self, mode: u32) -> Result<(), ()> {
        let rc = unsafe { esp_idf_svc::sys::esp_wifi_set_ps(mode as _) };
        log::info!(
            "USB_TRACE av_ps generation={} op=set target={} rc={}",
            self.generation,
            mode,
            rc
        );
        if rc == 0 {
            Ok(())
        } else {
            Err(())
        }
    }
    fn report(&mut self, r: av_power_save::Report) {
        PS_INITIAL.store(r.initial.unwrap_or(u32::MAX), Ordering::Relaxed);
        PS_ACTUAL.store(r.actual.unwrap_or(u32::MAX), Ordering::Relaxed);
        if r.error.is_some() {
            match r.stage {
                av_power_save::Stage::Enter => {
                    PS_ENTRY_ERRORS.fetch_add(1, Ordering::Relaxed);
                }
                av_power_save::Stage::Restore => {
                    PS_RESTORE_ERRORS.fetch_add(1, Ordering::Relaxed);
                    RECOVERY_FAILED.store(true, Ordering::Release);
                }
            }
        }
        log::info!(
            "USB_TRACE av_ps generation={} stage={:?} initial={:?} actual={:?} error={:?}",
            self.generation,
            r.stage,
            r.initial,
            r.actual,
            r.error
        );
    }
}
fn restore_ps(guard: &mut Option<av_power_save::Guard<Radio>>) -> bool {
    if let Some(mut scope) = guard.take() {
        scope.finish().is_ok()
    } else {
        true
    }
}
fn endpoint(peer: SocketAddr) -> u64 {
    match peer {
        SocketAddr::V4(p) => ((u32::from(*p.ip()) as u64) << 16) | p.port() as u64,
        _ => 0,
    }
}
fn address(endpoint: u64) -> SocketAddr {
    SocketAddr::from((Ipv4Addr::from((endpoint >> 16) as u32), endpoint as u16))
}
fn random_cookie() -> u64 {
    loop {
        let value = ((unsafe { esp_idf_svc::sys::esp_random() } as u64) << 32)
            | (unsafe { esp_idf_svc::sys::esp_random() } as u64);
        if value != 0 {
            return value;
        }
    }
}
struct Adapter<'a, 'b>(&'a mut Device<'b>);
impl audio_io::Bus for Adapter<'_, '_> {
    fn read(&mut self, offset: u32) -> Result<u32, ()> {
        self.0.fpga.read_u32(BASE + offset).map_err(|_| ())
    }
    fn write(&mut self, offset: u32, value: u32) -> Result<(), ()> {
        self.0.fpga.write_u32(BASE + offset, value).map_err(|_| ())
    }
    fn pcm(&mut self, data: &[u8]) -> Result<(), ()> {
        self.0
            .fpga
            .spi_write(
                Some(Hertz(40_000_000)),
                SpiCommand {
                    word_size: FpgaSpiWordSize::Bits32,
                    byte_swap: true,
                    increment_address: false,
                },
                BASE + 0x380,
                data,
            )
            .map_err(|_| ())
    }
}
pub struct Guard {
    stop: Arc<AtomicBool>,
    thread: Option<std::thread::JoinHandle<()>>,
}
impl Guard {
    pub fn start(host: Ipv4Addr, generation: u32) -> anyhow::Result<Self> {
        let socket = UdpSocket::bind("0.0.0.0:5534")?;
        socket.set_nonblocking(true)?;
        let caps =
            (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_DMA) as u32;
        unsafe {
            anyhow::ensure!(
                esp_idf_svc::sys::heap_caps_get_free_size(caps) >= 24 * 1024
                    && esp_idf_svc::sys::heap_caps_get_largest_free_block(caps) >= 8 * 1024,
                "Insufficient internal DMA memory for optional AV worker"
            );
        }
        let pcm = DmaBuffer::new(adpcm::PCM_BYTES)?;
        let internal =
            (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
        unsafe {
            anyhow::ensure!(
                esp_idf_svc::sys::heap_caps_get_free_size(internal) >= 28 * 1024,
                "Insufficient internal heap for bounded AV queue"
            );
        }
        // PSRAM remains disabled by the byte-identical SDK; capacity is fixed.
        let mut compressed = Vec::new();
        compressed
            .try_reserve_exact(compressed_queue::STORAGE_BYTES)
            .map_err(|_| anyhow::anyhow!("No internal heap for compressed audio queue"))?;
        compressed.resize(compressed_queue::STORAGE_BYTES, 0u8);
        let epoch = Device::lock().fpga.program_epoch();
        let stop = Arc::new(AtomicBool::new(false));
        let cancel = stop.clone();
        let thread = std::thread::Builder::new()
            .name("AvCompanion".into())
            .stack_size(8192)
            .spawn(move || run(socket, host, generation, epoch, cancel, pcm, compressed))?;
        Ok(Self {
            stop,
            thread: Some(thread),
        })
    }
}
impl Drop for Guard {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Release);
        if let Some(t) = self.thread.take() {
            let joined=t.join().is_ok();
            if !joined {
                RECOVERY_FAILED.store(true, Ordering::Release);
                log::error!("USB_TRACE av result=worker_panicked recovery=unconfirmed");
            }
            crate::core_access::av_drained(joined&&!RECOVERY_FAILED.load(Ordering::Acquire));
        }
    }
}
fn send_input(socket: &UdpSocket, session: &mut Session, stats: &Stats, diag: &mut Diagnostics, scheduled: bool) {
    if let Some((offer, sequence)) = session.next_input() {
        diag.input.attempt(monotonic_us(), scheduled);
        let values = [
            BUTTONS.load(Ordering::Relaxed) as u32,
            stats.accepted,
            stats.rejected,
            if stats.valid_snapshot {
                stats.queued_frames
            } else {
                0
            },
            if stats.valid_snapshot {
                stats.played
            } else {
                0
            },
            if stats.valid_snapshot {
                stats.underruns
            } else {
                0
            },
            1 | if offer.flags == 1 { 2 } else { 0 } | if stats.valid_snapshot { 4 } else { 0 },
            stats.build,
        ];
        let mut payload = [0; 32];
        for (i, v) in values.iter().enumerate() {
            payload[i * 4..i * 4 + 4].copy_from_slice(&v.to_be_bytes());
        }
        let mut out = [0; 80];
        match av_wire::encode(
            Kind::Input,
            offer.cookie,
            sequence,
            0,
            monotonic_us(),
            &payload,
            &mut out,
        ) {
            Ok(bytes) => {
                let result = socket.send_to(bytes, address(offer.endpoint)).map_err(|_| ());
                diag.input.sent(monotonic_us(), sequence, result, bytes.len());
            }
            Err(()) => diag.input.encode_failed(),
        }
    }
}
fn snapshot(stats: &mut Stats, diag: &mut Diagnostics) {
    let started = monotonic_us();
    let result = if let Some(mut d) = Device::try_lock() {
        let observation = audio_snapshot::read(&mut Adapter(&mut d));
        drop(d);
        if let Some(build) = observation.build {
            stats.build = build
        }
        if let Some(supported) = observation.supported {
            stats.supported = supported
        }
        observation.values
    } else {
        Err(SnapshotFailure::LockMiss)
    };
    diag.max_snapshot_us = diag
        .max_snapshot_us
        .max(monotonic_us().saturating_sub(started));
    stats.valid_snapshot = result.is_ok();
    match result {
        Ok(v) => {
            diag.snapshot_ok = diag.snapshot_ok.saturating_add(1);
            stats.queued_frames = v.queued;
            stats.played = v.played;
            stats.underruns = v.underruns;
        }
        Err(reason) => diag.snapshot_failure(reason),
    }
}
fn step(
    feeder: &mut Feeder,
    pcm: &mut DmaBuffer,
    generation: u32,
    cancelling: bool,
    epoch: u32,
    diag: &mut Diagnostics,
) -> (ResultEvent, Step) {
    let started = monotonic_us();
    let previous_phase = feeder.phase;
    if let Some(mut d) = Device::try_lock() {
        let acquired = monotonic_us();
        let actual_epoch = d.fpga.program_epoch();
        let result = audio_io::checked_step(
            feeder,
            &mut Adapter(&mut d),
            pcm.bytes(),
            GENERATION.load(Ordering::Acquire) == generation,
            cancelling,
            epoch,
            actual_epoch,
        );
        let held = monotonic_us().saturating_sub(acquired);
        drop(d);
        let now = monotonic_us();
        diag.step(true, now.saturating_sub(started), held, feeder.phase, now);
        let progress = service_policy::step_outcome(true, feeder.phase != previous_phase, result != ResultEvent::None);
        (result, progress)
    } else {
        let now = monotonic_us();
        diag.step(false, now.saturating_sub(started), 0, feeder.phase, now);
        (ResultEvent::None, service_policy::step_outcome(false, false, false))
    }
}
fn stop_audio(
    feeder: &mut Feeder,
    pcm: &mut DmaBuffer,
    generation: u32,
    epoch: u32,
    diag: &mut Diagnostics,
) -> bool {
    feeder.stop();
    let began = Instant::now();
    while began.elapsed() < Duration::from_millis(500) {
        match step(feeder, pcm, generation, true, epoch, diag).0 {
            ResultEvent::Stopped => return true,
            ResultEvent::Fault => return false,
            _ => {}
        }
        std::thread::sleep(Duration::from_millis(1));
    }
    false
}
fn drop_queued(
    meta: Meta,
    reason: Reason,
    queue_count: usize,
    phase: Phase,
    now: u64,
    stats: &mut Stats,
    diag: &mut Diagnostics,
) {
    stats.rejected = stats.rejected.saturating_add(1);
    // Drop timestamp is fresh ESP time; queue age is receive-handler relative.
    let now = monotonic_us().max(now);
    diag.drop_block(meta.sequence, reason, phase, now, queue_count);
    diag.max_queue_age_us = diag
        .max_queue_age_us
        .max(now.saturating_sub(meta.arrival_us));
}
fn clear_queue(
    queue: &mut Queue,
    reason: Reason,
    phase: Phase,
    now: u64,
    stats: &mut Stats,
    diag: &mut Diagnostics,
) {
    while let Some(meta) = queue.pop() {
        drop_queued(meta, reason, queue.len() + 1, phase, now, stats, diag)
    }
    diag.queued = 0;
}
fn settle(
    pending: &mut Option<u32>,
    stats: &mut Stats,
    committed: bool,
    diag: &mut Diagnostics,
    reason: Reason,
    phase: Phase,
    queued: usize,
    now: u64,
) {
    if let Some(sequence) = *pending {
        if !committed {
            diag.drop_block(sequence, reason, phase, now, queued);
        }
        let _ =
            audio_io::settle_block(pending, &mut stats.accepted, &mut stats.rejected, committed);
        diag.finish_pending(now);
    }
}
fn run(
    socket: UdpSocket,
    host: Ipv4Addr,
    generation: u32,
    epoch: u32,
    stop: Arc<AtomicBool>,
    mut pcm: DmaBuffer,
    mut compressed: Vec<u8>,
) {
    let mut session = Session::new();
    let mut queue = Queue::new();
    let mut diag = Diagnostics::new();
    diag.phase_since = monotonic_us();
    diag.task_priority = unsafe { esp_idf_svc::sys::uxTaskPriorityGet(std::ptr::null_mut()) };
    diag.task_core = unsafe { (esp_idf_svc::sys::xthal_get_prid() >> 13) & 1 } as u32;
    let mut previous_loop = monotonic_us();
    let mut previous_audio = None::<u64>;
    let mut feeder = Feeder::new();
    let mut power_save = None::<av_power_save::Guard<Radio>>;
    let mut ps_unavailable = false;
    let mut stats = Stats::default();
    snapshot(&mut stats, &mut diag);
    let mut dirty = false;
    let mut usable = stats.supported;
    let mut staged_since = None::<Instant>;
    let mut last_audio = None::<u64>;
    let mut pending_audio_seq = None::<u32>;
    let mut snapshot_due = 0;
    let mut received = [0; av_wire::MAX + 1];
    super::memory_probe("AV worker ready");
    log::info!("USB_TRACE av listener=5534 audio_supported={} input_period_ms=20 stack_bytes=8192 dma_bytes=2020",stats.supported);
    log::info!("USB_TRACE av_service schema=1 variant=v22-stream-service-20261104 input_us={} rx_budget_us={} feed_budget_us={} pages=8", service_policy::INPUT_PERIOD_US, service_policy::RX_BUDGET_US, service_policy::FEED_BUDGET_US);
    // Every checkpoint reads fresh ESP time and cancellation state. A lease
    // decision restarts outer cleanup before another network/FPGA operation.
    // Synchronous bus/API actions are not preempted by these decision budgets.
    macro_rules! work_checkpoint {
        ($worker:lifetime) => {{
            let fresh = monotonic_us();
            let cancel = stop.load(Ordering::Acquire) || GENERATION.load(Ordering::Acquire) != generation;
            match service_policy::checkpoint(fresh, cancel, session.active.map(|a| a.lease_us), diag.input.due_us) {
                Checkpoint::Cancel => break $worker,
                Checkpoint::Expired => continue $worker,
                Checkpoint::InputDue => send_input(&socket, &mut session, &stats, &mut diag, true),
                Checkpoint::Continue => {},
            }
            // Input encoding/send may consume time too; budgets use a fresh
            // completion sample rather than the pre-send checkpoint sample.
            monotonic_us()
        }};
    }
    'worker: while !stop.load(Ordering::Acquire) && GENERATION.load(Ordering::Acquire) == generation {
        let now = monotonic_us();
        diag.max_loop_gap_us = diag.max_loop_gap_us.max(now.saturating_sub(previous_loop));
        previous_loop = now;
        diag.phase(feeder.phase, now);
        if session.expire(now) {
            clear_queue(
                &mut queue,
                Reason::SessionEnd,
                feeder.phase,
                now,
                &mut stats,
                &mut diag,
            );
            settle(
                &mut pending_audio_seq,
                &mut stats,
                false,
                &mut diag,
                Reason::SessionEnd,
                feeder.phase,
                queue.len(),
                monotonic_us(),
            );
            if dirty && !stop_audio(&mut feeder, &mut pcm, generation, epoch, &mut diag) {
                RECOVERY_FAILED.store(true, Ordering::Release);
                break;
            }
            dirty = false;
            if !restore_ps(&mut power_save) {
                ps_unavailable = true;
            }
            stats.active = false;
            stats.audio_enabled = false;
            stats.valid_snapshot = false;
            last_audio = None;
            staged_since = None;
            log::info!("USB_TRACE av result=lease_expired");
        }
        let now = work_checkpoint!('worker);
        if last_audio.is_some_and(|t| now.saturating_sub(t) >= 200_000) {
            clear_queue(
                &mut queue,
                Reason::IdleFlush,
                feeder.phase,
                now,
                &mut stats,
                &mut diag,
            );
            settle(
                &mut pending_audio_seq,
                &mut stats,
                false,
                &mut diag,
                Reason::IdleFlush,
                feeder.phase,
                queue.len(),
                monotonic_us(),
            );
            if let Some(a) = session.active {
                feeder.start(a.offer.cookie as u32);
                dirty = true;
                staged_since = Some(Instant::now());
            }
            last_audio = None;
            stats.valid_snapshot = false;
            log::info!("USB_TRACE av result=audio_idle_flush");
        }
        let mut receive_pass = Pass::receive(monotonic_us());
        loop {
            let now = work_checkpoint!('worker);
            if !receive_pass.allow(now) {
                diag.service.rx_budget_ends = diag.service.rx_budget_ends.saturating_add(1);
                break;
            }
            match socket.recv_from(&mut received) {
                Ok((n, peer)) if peer.ip() == std::net::IpAddr::V4(host) => {
                    match av_wire::parse(&received[..n]) {
                        Ok(packet) => {
                            let now = work_checkpoint!('worker);
                            if packet.kind == Kind::Audio {
                                if !session.active.is_some_and(|a| {
                                    a.offer.cookie == packet.cookie
                                        && a.offer.endpoint == endpoint(peer)
                                        && a.offer.flags == 1
                                }) {
                                    diag.stale_or_foreign = diag.stale_or_foreign.saturating_add(1);
                                    continue;
                                }
                                if adpcm::validate(packet.payload).is_err() {
                                    drop_queued(
                                        Meta {
                                            session: packet.cookie,
                                            sequence: packet.sequence,
                                            arrival_us: now,
                                        },
                                        Reason::BadIma,
                                        queue.len(),
                                        feeder.phase,
                                        now,
                                        &mut stats,
                                        &mut diag,
                                    );
                                    continue;
                                }
                            }
                            // Before any Session mutation, Offer or input-only START.
                            if matches!(packet.kind,Kind::Hello|Kind::Start) &&
                                (crate::core_access::refuse_diagnostic_peer().is_err()||!crate::core_access::av_admit()){continue;}
                            if packet.kind == Kind::Hello && packet.flags == 1 && !stats.supported {
                                continue;
                            }
                            let event = session.receive(
                                packet,
                                endpoint(peer),
                                now,
                                if packet.kind == Kind::Hello {
                                    random_cookie()
                                } else {
                                    0
                                },
                            );
                            match event {
                                Event::Offer => {
                                    if let Some(o) = session.pending {
                                        let mut out = [0; 56];
                                        if let Ok(bytes) = av_wire::encode(
                                            Kind::Offer,
                                            o.cookie,
                                            0,
                                            o.flags,
                                            now,
                                            &o.nonce.to_be_bytes(),
                                            &mut out,
                                        ) {
                                            let _ = socket.send_to(bytes, peer);
                                        }
                                    }
                                }
                                Event::Started => {
                                    if ps_unavailable {
                                        session.active = None;
                                        session.pending = None;
                                        continue;
                                    }
                                    match av_power_save::Guard::enter(Radio { generation }) {
                                        Ok(guard) => power_save = Some(guard),
                                        Err(error) => {
                                            session.active = None;
                                            session.pending = None;
                                            stats.active = false;
                                            stats.audio_enabled = false;
                                            ps_unavailable =
                                                PS_RESTORE_ERRORS.load(Ordering::Relaxed) != 0;
                                            log::warn!("USB_TRACE av result=start_refused power_save_error={:?}",error);
                                            continue;
                                        }
                                    }
                                    clear_queue(
                                        &mut queue,
                                        Reason::SessionEnd,
                                        feeder.phase,
                                        now,
                                        &mut stats,
                                        &mut diag,
                                    );
                                    queue = Queue::new();
                                    DIAG_PAGE.store(0, Ordering::Relaxed);
                                    let serial = diag.session_serial.wrapping_add(1);
                                    let priority = diag.task_priority;
                                    let core = diag.task_core;
                                    diag = Diagnostics::new();
                                    diag.session_serial = serial;
                                    diag.task_priority = priority;
                                    diag.task_core = core;
                                    diag.phase_since = now;
                                    previous_audio = None;
                                    stats.accepted = 0;
                                    stats.rejected = 0;
                                    stats.gaps = 0;
                                    stats.active = true;
                                    stats.audio_enabled = packet.flags == 1;
                                    stats.valid_snapshot = false;
                                    last_audio = None;
                                    usable = stats.supported;
                                    if packet.flags == 1 {
                                        feeder.start(packet.cookie as u32);
                                        dirty = true;
                                        staged_since = Some(Instant::now());
                                    }
                                    diag.input.due_us = monotonic_us();
                                    send_input(&socket, &mut session, &stats, &mut diag, true);
                                    log::info!(
                                        "USB_TRACE av result=active audio_enabled={}",
                                        stats.audio_enabled
                                    );
                                }
                                Event::RepeatStart => send_input(&socket, &mut session, &stats, &mut diag, false),
                                Event::Stopped => {
                                    clear_queue(
                                        &mut queue,
                                        Reason::SessionEnd,
                                        feeder.phase,
                                        now,
                                        &mut stats,
                                        &mut diag,
                                    );
                                    settle(
                                        &mut pending_audio_seq,
                                        &mut stats,
                                        false,
                                        &mut diag,
                                        Reason::SessionEnd,
                                        feeder.phase,
                                        queue.len(),
                                        monotonic_us(),
                                    );
                                    if dirty
                                        && !stop_audio(
                                            &mut feeder,
                                            &mut pcm,
                                            generation,
                                            epoch,
                                            &mut diag,
                                        )
                                    {
                                        RECOVERY_FAILED.store(true, Ordering::Release);
                                        break;
                                    }
                                    dirty = false;
                                    if !restore_ps(&mut power_save) {
                                        ps_unavailable = true;
                                    }
                                    stats.active = false;
                                    stats.audio_enabled = false;
                                    stats.valid_snapshot = false;
                                    last_audio = None;
                                    staged_since = None;
                                    log::info!("USB_TRACE av result=stopped");
                                }
                                Event::Audio { gaps } => {
                                    stats.gaps = stats.gaps.saturating_add(gaps);
                                    diag.valid_audio = diag.valid_audio.saturating_add(1);
                                    let arrival = monotonic_us();
                                    if let Some(previous) = previous_audio {
                                        diag.max_arrival_gap_us = diag
                                            .max_arrival_gap_us
                                            .max(arrival.saturating_sub(previous));
                                    }
                                    previous_audio = Some(arrival);
                                    if !usable {
                                        drop_queued(
                                            Meta {
                                                session: packet.cookie,
                                                sequence: packet.sequence,
                                                arrival_us: arrival,
                                            },
                                            Reason::NotUsable,
                                            queue.len(),
                                            feeder.phase,
                                            arrival,
                                            &mut stats,
                                            &mut diag,
                                        );
                                    } else {
                                        if feeder.phase != Phase::Idle {
                                            diag.busy_deferrals =
                                                diag.busy_deferrals.saturating_add(1);
                                        }
                                        let count = queue.len();
                                        if let Ok(evicted) = queue.push(
                                            Meta {
                                                session: packet.cookie,
                                                sequence: packet.sequence,
                                                arrival_us: arrival,
                                            },
                                            packet.payload,
                                            &mut compressed,
                                        ) {
                                            diag.enqueued = diag.enqueued.saturating_add(1);
                                            if let Some(meta) = evicted {
                                                drop_queued(
                                                    meta,
                                                    Reason::QueueFull,
                                                    count,
                                                    feeder.phase,
                                                    arrival,
                                                    &mut stats,
                                                    &mut diag,
                                                );
                                            }
                                        }
                                    }
                                }
                                Event::None => {
                                    if packet.kind == Kind::Audio {
                                        diag.stale_or_foreign =
                                            diag.stale_or_foreign.saturating_add(1);
                                    }
                                }
                            }
                        }
                        Err(()) => {
                            stats.malformed = stats.malformed.saturating_add(1);
                            diag.malformed = diag.malformed.saturating_add(1);
                        }
                    }
                }
                Ok(_) => {}
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(_) => stats.socket_errors = stats.socket_errors.saturating_add(1),
            }
        }
        let work_now = work_checkpoint!('worker);
        while queue.stale(work_now) {
            if let Some(meta) = queue.pop() {
                diag.max_queue_age_us = diag
                    .max_queue_age_us
                    .max(work_now.saturating_sub(meta.arrival_us));
                drop_queued(
                    meta,
                    Reason::QueueAge,
                    queue.len() + 1,
                    feeder.phase,
                    work_now,
                    &mut stats,
                    &mut diag,
                );
            }
        }
        if usable && feeder.phase == Phase::Idle && feeder.active && pending_audio_seq.is_none() {
            if let Some(meta) = queue.front() {
                let age = work_now.saturating_sub(meta.arrival_us);
                diag.max_queue_age_us = diag.max_queue_age_us.max(age);
                if !session
                    .active
                    .is_some_and(|a| a.offer.cookie == meta.session)
                {
                    queue.pop();
                    drop_queued(
                        meta,
                        Reason::SourceMismatch,
                        queue.len() + 1,
                        feeder.phase,
                        work_now,
                        &mut stats,
                        &mut diag,
                    );
                } else if adpcm::decode(queue.bytes(&compressed).unwrap(), pcm.bytes()).is_ok() {
                    let crc = av_wire::crc(pcm.bytes());
                    if feeder.submit(meta.sequence, crc) {
                        queue.pop();
                        diag.dequeued = diag.dequeued.saturating_add(1);
                        pending_audio_seq = Some(meta.sequence);
                        diag.start_pending(meta.sequence, work_now);
                        staged_since = Some(Instant::now());
                    }
                }
            }
        }
        let mut feeder_pass = Pass::feeder(monotonic_us());
        loop {
            let fresh = work_checkpoint!('worker);
            if matches!(feeder.phase, Phase::Idle | Phase::Failed) || !feeder_pass.allow(fresh) {
                break;
            }
            let recovering = matches!(feeder.phase, Phase::Stop | Phase::WaitStop);
            let (event, outcome) = step(&mut feeder, &mut pcm, generation, false, epoch, &mut diag);
            feeder_pass.observe(outcome);
            match event {
                ResultEvent::Committed => {
                    settle(
                        &mut pending_audio_seq,
                        &mut stats,
                        true,
                        &mut diag,
                        Reason::IoUnconfirmed,
                        feeder.phase,
                        queue.len(),
                        monotonic_us(),
                    );
                    last_audio = Some(monotonic_us());
                    staged_since = if feeder.phase == Phase::Arm {
                        Some(Instant::now())
                    } else {
                        None
                    };
                }
                ResultEvent::Rejected => {
                    settle(
                        &mut pending_audio_seq,
                        &mut stats,
                        false,
                        &mut diag,
                        Reason::FpgaFull,
                        feeder.phase,
                        queue.len(),
                        monotonic_us(),
                    );
                    staged_since = None;
                }
                ResultEvent::Online | ResultEvent::Armed => {
                    staged_since = None;
                }
                ResultEvent::Stopped => {
                    last_audio = None;
                    dirty = false;
                    staged_since = None;
                }
                ResultEvent::Fault => {
                    diag.io_faults = diag.io_faults.saturating_add(1);
                    if pending_audio_seq.is_none() {
                        diag.control_faults = diag.control_faults.saturating_add(1);
                    }
                    last_audio = None;
                    settle(
                        &mut pending_audio_seq,
                        &mut stats,
                        false,
                        &mut diag,
                        Reason::IoUnconfirmed,
                        feeder.phase,
                        queue.len(),
                        monotonic_us(),
                    );
                    usable = false;
                    if recovering {
                        RECOVERY_FAILED.store(true, Ordering::Release);
                    } else {
                        feeder.stop();
                        staged_since = Some(Instant::now());
                    }
                    log::warn!("USB_TRACE av result=audio_fault disabled_until_next_session=true");
                    break;
                }
                _ => {}
            }
        }
        diag.service.finish(feeder_pass, monotonic_us());
        let _ = work_checkpoint!('worker);
        if staged_since.is_some_and(|t| t.elapsed() >= Duration::from_millis(500)) {
            if pending_audio_seq.is_none() {
                diag.control_faults = diag.control_faults.saturating_add(1);
            }
            settle(
                &mut pending_audio_seq,
                &mut stats,
                false,
                &mut diag,
                Reason::Timeout,
                feeder.phase,
                queue.len(),
                monotonic_us(),
            );
            last_audio = None;
            usable = false;
            if matches!(feeder.phase, Phase::Stop | Phase::WaitStop) {
                RECOVERY_FAILED.store(true, Ordering::Release);
                break;
            } else {
                feeder.stop();
                staged_since = Some(Instant::now());
            }
            log::warn!("USB_TRACE av result=audio_io_timeout");
        }
        diag.queued = queue.len() as u32;
        diag.queue_high = diag.queue_high.max(queue.high_water as u32);
        let now = work_checkpoint!('worker);
        if now >= snapshot_due {
            snapshot(&mut stats, &mut diag);
            if dirty && !stats.supported {
                RECOVERY_FAILED.store(true, Ordering::Release);
                usable = false;
            }
            diag.task_core = unsafe { (esp_idf_svc::sys::xthal_get_prid() >> 13) & 1 };
            stats.stack_low_water =
                unsafe { esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) };
            *STATS.lock().unwrap() = stats;
            *DIAGNOSTICS.lock().unwrap() = diag;
            snapshot_due = monotonic_us().saturating_add(100_000);
        }
        *DIAGNOSTICS.lock().unwrap() = diag;
        if RECOVERY_FAILED.load(Ordering::Acquire) {
            break;
        }
        std::thread::sleep(Duration::from_millis(1));
    }
    clear_queue(
        &mut queue,
        Reason::Cancel,
        feeder.phase,
        monotonic_us(),
        &mut stats,
        &mut diag,
    );
    settle(
        &mut pending_audio_seq,
        &mut stats,
        false,
        &mut diag,
        Reason::Cancel,
        feeder.phase,
        queue.len(),
        monotonic_us(),
    );
    if dirty && !stop_audio(&mut feeder, &mut pcm, generation, epoch, &mut diag) {
        RECOVERY_FAILED.store(true, Ordering::Release);
    }
    if !restore_ps(&mut power_save){RECOVERY_FAILED.store(true,Ordering::Release);}
    session.active=None;session.pending=None;
    stats.active = false;
    stats.audio_enabled = false;
    stats.valid_snapshot = false;
    *STATS.lock().unwrap() = stats;
    *DIAGNOSTICS.lock().unwrap() = diag;
    super::memory_probe("AV worker stopped");
    log::info!(
        "USB_TRACE av result=worker_stopped recovery_failed={}",
        RECOVERY_FAILED.load(Ordering::Acquire)
    );
}

pub fn log_diagnostics() {
    match DIAG_PAGE.fetch_add(1, Ordering::Relaxed) % 8 {
        0 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.session_serial,
                    d.valid_audio,
                    d.enqueued,
                    d.dequeued,
                    d.queued,
                    d.queue_high,
                    d.busy_deferrals,
                    d.stale_or_foreign,
                    d.malformed,
                )
            };
            log::info!("USB_TRACE avq page=queue serial={} valid={} in={} out={} queued={} high={} busy_defer={} stale_foreign={} malformed={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8);
        }
        1 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.lock_misses,
                    d.max_consecutive_misses,
                    d.successful_steps,
                    d.max_pending_us,
                    d.max_phase_us,
                    d.max_lock_hold_us,
                    d.max_loop_gap_us,
                    d.max_arrival_gap_us,
                    d.task_priority,
                    d.task_core,
                )
            };
            log::info!("USB_TRACE avq page=steps miss={} burst={} steps={} pending_max_us={} phase_max_us={} held_max_us={} loop_gap_us={} arrival_gap_us={} prio={} core_sample={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8,x.9);
        }
        2 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (
                    d.snapshot_ok,
                    d.snapshot_lock_miss,
                    d.snapshot_io,
                    d.snapshot_identity,
                    d.snapshot_offline,
                    d.snapshot_changed,
                    d.snapshot_range,
                    d.max_snapshot_us,
                )
            };
            log::info!("USB_TRACE avq page=snapshot ok={} miss={} io={:?} identity={} offline={} changed={} range={} max_us={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7);
        }
        3 => {
            let x = {
                let d = DIAGNOSTICS.lock().unwrap();
                (d.drops, d.control_faults, d.io_faults, d.max_queue_age_us)
            };
            log::info!("USB_TRACE avq page=drops order=full,age,ima,unusable,fpga,io,timeout,cancel,end,source,idle counts={:?} control_fault={} io_fault={} queue_age_max_us={}",x.0,x.1,x.2,x.3);
        }
        4 => {
            let record = DIAGNOSTICS.lock().unwrap().first;
            log::info!("USB_TRACE avq page=FIRST drop={:?}", record);
        }
        5 => {
            let record = DIAGNOSTICS.lock().unwrap().last;
            log::info!("USB_TRACE avq page=LAST drop={:?}", record);
        }
        6 => {
            let x = { let d = DIAGNOSTICS.lock().unwrap(); let s = d.service;
                (s.passes,s.attempts,s.progress,s.lock_deferrals,s.phase_deferrals,s.attempt_budget_ends,s.time_budget_ends,s.max_pass_us,s.rx_budget_ends) };
            log::info!("USB_TRACE avq page=service passes={} attempts={} progress={} lock_defer={} phase_defer={} attempts_end={} time_end={} max_us={} rx_end={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8);
        }
        _ => {
            let x = { let d = DIAGNOSTICS.lock().unwrap(); let i = d.input;
                (i.attempts,i.sent,i.errors,i.encode_errors,i.short_sends,i.sequence_gaps,i.late_attempts,i.missed_periods,i.max_lateness_us,i.max_success_gap_us) };
            log::info!("USB_TRACE avq page=input attempts={} sent={} errors={} encode={} short={} seq_gaps={} late={} missed_periods={} lateness_max_us={} send_gap_max_us={}",x.0,x.1,x.2,x.3,x.4,x.5,x.6,x.7,x.8,x.9);
        }
    }
}
