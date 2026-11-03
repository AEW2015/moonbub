//! Experimental standalone MSV1 source. Sunshine pairing/video are not implemented.
pub mod protocol;
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
        mpsc, Mutex, OnceLock,
    },
    time::{Duration, Instant},
};

const BASE: u32 = 0xE0000000;
const TIMEOUT: Duration = Duration::from_millis(500);
static MODEM: OnceLock<Mutex<Option<Modem>>> = OnceLock::new();
static COMMAND: OnceLock<mpsc::SyncSender<(String, u32)>> = OnceLock::new();
static GENERATION: AtomicU32 = AtomicU32::new(0);
static BUTTONS: AtomicU16 = AtomicU16::new(0);
static ACTIVE: AtomicBool = AtomicBool::new(false);
static WANTED: AtomicBool = AtomicBool::new(false);
static RESTORING: AtomicBool = AtomicBool::new(false);
static CONTROL: Mutex<()> = Mutex::new(());
static STATS: Mutex<Stats> = Mutex::new(Stats::new());
#[derive(Clone)]
pub struct Stats {
    pub status: String,
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
pub fn has_session() -> bool {
    ACTIVE.load(Ordering::Acquire) || WANTED.load(Ordering::Acquire)
}
pub fn disconnect() {
    WANTED.store(false, Ordering::Release);
    GENERATION.fetch_add(1, Ordering::AcqRel);
}
/// Stop acknowledgment precedes any replacement of the streaming FPGA image.
/// The wait runs in its own thread, outside UI, worker dispatch, and device locks.
pub fn exit_to_menu() {
    let _control = CONTROL.lock().unwrap();
    if RESTORING.swap(true, Ordering::AcqRel) {
        return;
    }
    disconnect();
    std::thread::Builder::new()
        .name("StreamExit".into())
        .stack_size(4096)
        .spawn(|| {
            while ACTIVE.load(Ordering::Acquire) {
                std::thread::sleep(Duration::from_millis(20));
            }
            crate::worker::send(crate::worker::Message::RestoreAfterStreaming);
        })
        .expect("streaming teardown");
}
pub fn restored() {
    RESTORING.store(false, Ordering::Release);
}
pub fn connect(host: String) {
    let _control = CONTROL.lock().unwrap();
    if RESTORING.load(Ordering::Acquire) {
        status("Restoring boot menu; please wait");
        return;
    }
    WANTED.store(true, Ordering::Release);
    let generation = GENERATION.fetch_add(1, Ordering::AcqRel).wrapping_add(1);
    let tx = COMMAND.get_or_init(|| {
        let (tx, rx) = mpsc::sync_channel::<(String, u32)>(2);
        std::thread::Builder::new()
            .name("Streaming".into())
            .stack_size(16 * 1024)
            .spawn(move || {
                if let Err(e) = worker(rx) {
                    status(format!("Streaming unavailable: {e}"));
                }
            })
            .expect("streaming worker");
        tx
    });
    if tx.try_send((host, generation)).is_err() {
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
fn worker(rx: mpsc::Receiver<(String, u32)>) -> anyhow::Result<()> {
    let modem = MODEM
        .get()
        .ok_or_else(|| anyhow::anyhow!("modem not initialized"))?
        .lock()
        .unwrap()
        .take()
        .ok_or_else(|| anyhow::anyhow!("modem already owned"))?;
    let sysloop = EspSystemEventLoop::take()?;
    // Existing KVS owns the NVS partition. Do not take it twice; Wi-Fi uses RAM configuration.
    let mut wifi = BlockingWifi::wrap(EspWifi::new(modem, sysloop.clone(), None)?, sysloop)?;
    while let Ok((host, generation)) = rx.recv() {
        ACTIVE.store(true, Ordering::Release);
        if GENERATION.load(Ordering::Acquire) != generation {
            ACTIVE.store(false, Ordering::Release);
            continue;
        }
        let result = (|| -> anyhow::Result<()> {
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
            wifi.connect()?;
            wifi.wait_netif_up()?;
            if GENERATION.load(Ordering::Acquire) != generation {
                return Ok(());
            }
            ensure_core()?;
            session(host, generation)
        })();
        let _ = wifi.disconnect();
        let _ = wifi.stop();
        ACTIVE.store(false, Ordering::Release);
        if let Err(e) = result {
            STATS.lock().unwrap().errors += 1;
            status(format!("Stopped: {e}"));
        } else {
            status("Disconnected; remote controls released");
        }
    }
    Ok(())
}
fn access<T>(f: impl FnOnce(&mut Device<'static>) -> anyhow::Result<T>) -> anyhow::Result<T> {
    let mut d = Device::try_lock().ok_or_else(|| anyhow::anyhow!("FPGA busy; frame dropped"))?;
    f(&mut d)
}
fn identity(d: &mut Device<'static>) -> anyhow::Result<()> {
    anyhow::ensure!(
        d.fpga.read_u32(BASE)? == 0x4D425631 && d.fpga.read_u32(BASE + 4)? >> 16 == 1,
        "Streaming core replaced"
    );
    Ok(())
}
fn ensure_core() -> anyhow::Result<()> {
    let already = access(|d| Ok(d.fpga.read_u32(BASE)? == 0x4D425631)).unwrap_or(false);
    if !already {
        status("Loading /sdcard/moonshine.bit (volatile FPGA)");
        let mut file = std::fs::File::open("/sdcard/moonshine.bit")?;
        let mut scratch = DmaBuffer::new(16 * 1024)?;
        let mut d = Device::lock();
        let mode = d.get_display_mode();
        if mode == crate::device::DisplayMode::Internal {
            d.set_lcd_enabled(false);
            std::thread::sleep(Duration::from_millis(10));
        }
        let programmed = d.fpga.program(&mut file, scratch.bytes());
        if mode == crate::device::DisplayMode::Internal {
            d.set_lcd_enabled(true);
        }
        programmed?;
        d.fpga.set_display_mode(mode)?;
        d.fpga
            .enable_interrupt(crate::device::drivers::fpga::Irq::Button)?;
        d.fpga.set_system_clock_rate(Hertz(50_000_000));
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
fn abort() {
    let started = Instant::now();
    while access(|d| {
        identity(d)?;
        d.fpga.write_u32(BASE + 0x24, 2)?;
        Ok(())
    })
    .is_err()
    {
        if started.elapsed() >= Duration::from_millis(100) {
            break;
        }
        std::thread::sleep(Duration::from_millis(1));
    }
}
fn begin(h: protocol::Header) -> anyhow::Result<()> {
    access(|d| {
        anyhow::ensure!(
            d.fpga.read_u32(BASE)? == 0x4D425631,
            "Load the Moonshine FPGA core first"
        );
        anyhow::ensure!(
            d.fpga.read_u32(BASE + 4)? >> 16 == 1,
            "FPGA protocol mismatch"
        );
        anyhow::ensure!(d.fpga.read_u32(BASE + 8)? & 1 != 0, "FPGA JPEG unsupported");
        let mut core_status = d.fpga.read_u32(BASE + 0x10)?;
        if core_status & ((1 << 2) | (1 << 3)) != 0 {
            // A failed transfer or prior disconnected receiver can leave an incomplete frame.
            identity(d)?;
            d.fpga.write_u32(BASE + 0x24, 2)?;
            core_status = d.fpga.read_u32(BASE + 0x10)?;
        }
        anyhow::ensure!(core_status & 1 != 0, "Decoder busy; dropping frame");
        d.fpga.write_u32(BASE + 0x14, h.id)?;
        d.fpga.write_u32(BASE + 0x18, h.length)?;
        d.fpga
            .write_u32(BASE + 0x1C, ((h.width as u32) << 16) | h.height as u32)?;
        d.fpga.write_u32(BASE + 0x20, h.crc)?;
        d.fpga.write_u32(BASE + 0x24, 1)?;
        Ok(())
    })
}
fn forward(payload: &[u8]) -> anyhow::Result<u32> {
    access(|d| {
        identity(d)?;
        let credits = d.fpga.read_u32(BASE + 0x0C)?;
        anyhow::ensure!(credits >= payload.len() as u32, "FPGA credits exhausted");
        d.fpga.spi_write(
            Some(Hertz(40_000_000)),
            SpiCommand {
                word_size: FpgaSpiWordSize::Bits8,
                byte_swap: false,
                increment_address: false,
            },
            BASE + 0x100,
            payload,
        )?;
        Ok(credits - payload.len() as u32)
    })
}
struct DmaBuffer(*mut u8, usize);
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
fn session(host: Ipv4Addr, generation: u32) -> anyhow::Result<()> {
    // A new receiver permits a restarted sender to begin again at frame ID zero.
    let mut receiver = protocol::Receiver::default();
    let socket = UdpSocket::bind("0.0.0.0:5533")?;
    socket.set_read_timeout(Some(Duration::from_millis(20)))?;
    let mut packet = DmaBuffer::new(protocol::HEADER + protocol::CHUNK + 1)?;
    let (mut peer, mut last, mut heartbeat, mut report) =
        (None, Instant::now(), Instant::now(), Instant::now());
    let (mut active, mut id, mut capture) = (false, 0, 0);
    let mut last_dropped_id = None;
    let baseline = stats();
    let (mut prev_frames, mut prev_display, mut prev_bytes) =
        (baseline.received, None::<u32>, baseline.bytes);
    let mut last_buttons = 0u16;
    status("TEST source ready: UDP5533 / MJPEG; no audio");
    while GENERATION.load(Ordering::Acquire) == generation {
        match socket.recv_from(packet.bytes()) {
            Ok((n, from)) => {
                if from.ip() != std::net::IpAddr::V4(host) || peer.is_some_and(|p| p != from) {
                    continue;
                }
                peer = Some(from);
                last = Instant::now();
                let bytes = &packet.bytes()[..n];
                let result = (|| -> anyhow::Result<bool> {
                    let (h, done) = receiver
                        .accept(bytes)
                        .map_err(|e| anyhow::anyhow!("Invalid/lost frame: {e:?}"))?;
                    let previous_id = id;
                    id = h.id;
                    capture = h.capture_us;
                    if h.offset == 0 {
                        if active {
                            abort();
                            note_drop(previous_id, &mut last_dropped_id);
                        }
                        begin(h)?;
                        active = true;
                    }
                    let credits = forward(&bytes[protocol::HEADER..])?;
                    {
                        let mut s = STATS.lock().unwrap();
                        s.credits = credits;
                        s.bytes += h.count as u64;
                    }
                    if done {
                        access(|d| {
                            identity(d)?;
                            d.fpga.write_u32(BASE + 0x24, 4)?;
                            Ok(())
                        })?;
                        active = false;
                        STATS.lock().unwrap().received += 1;
                    }
                    Ok(done)
                })();
                match result {
                    Ok(true) => reply(&socket, from, 0, id, capture, false),
                    Ok(false) => {}
                    Err(e) => {
                        if active {
                            abort();
                        }
                        receiver.abort();
                        active = false;
                        if let Ok(h) = protocol::Header::parse(bytes) {
                            note_drop(h.id, &mut last_dropped_id);
                        }
                        let mut s = STATS.lock().unwrap();
                        s.errors += 1;
                        s.status = e.to_string();
                        drop(s);
                        reply(&socket, from, 1, id, capture, false);
                    }
                }
                // Release the device mutex between every DMA chunk; let UI/input run.
                std::thread::yield_now();
            }
            Err(e)
                if matches!(
                    e.kind(),
                    std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut
                ) => {}
            Err(e) => {
                abort();
                if let Some(p) = peer {
                    reply(&socket, p, 3, id, capture, true);
                }
                return Err(e.into());
            }
        }
        if active && last.elapsed() > TIMEOUT {
            abort();
            receiver.abort();
            active = false;
            note_drop(id, &mut last_dropped_id);
        }
        let buttons = BUTTONS.load(Ordering::Relaxed);
        if buttons != last_buttons || heartbeat.elapsed() >= Duration::from_millis(250) {
            last_buttons = buttons;
            if let Some(p) = peer {
                reply(&socket, p, 0, id, capture, last.elapsed() > TIMEOUT);
            }
            heartbeat = Instant::now();
        }
        if report.elapsed() >= Duration::from_secs(1) {
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
    if active {
        abort();
    }
    if let Some(p) = peer {
        reply(&socket, p, 0, id, capture, true);
    }
    Ok(())
}
