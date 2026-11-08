//! Emulator-only Wi-Fi allocation/stack probe. It does not emulate Game Bub peripherals.
use esp_idf_svc::{eventloop::EspSystemEventLoop, hal::peripherals::Peripherals,
    wifi::{AuthMethod, BlockingWifi, ClientConfiguration, Configuration, EspWifi}};

fn memory(stage: &str) {
    let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
    unsafe { log::info!("SIM_MEMORY {stage} free={} largest={} stack_low_water={}",
        esp_idf_svc::sys::heap_caps_get_free_size(caps),
        esp_idf_svc::sys::heap_caps_get_largest_free_block(caps),
        esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())); }
}

fn main() -> anyhow::Result<()> {
    esp_idf_svc::sys::link_patches();
    esp_idf_svc::log::EspLogger::initialize_default();
    let modem = Peripherals::take()?.modem;
    std::thread::Builder::new().name("StreamingSim".into()).stack_size(16 * 1024)
        .spawn(move || -> anyhow::Result<()> {
            // Approximate the full handheld's observed pre-Wi-Fi heap pressure.
            // Artificial chunks do not reproduce the board's fragmentation.
            let caps = (esp_idf_svc::sys::MALLOC_CAP_INTERNAL | esp_idf_svc::sys::MALLOC_CAP_8BIT) as u32;
            let mut reserved = Vec::new();
            while unsafe { esp_idf_svc::sys::heap_caps_get_free_size(caps) } > 84 * 1024 {
                reserved.push(vec![0u8; 16 * 1024]);
            }
            std::hint::black_box(&mut reserved);
            memory("before_wifi");
            let sysloop = EspSystemEventLoop::take()?;
            let mut wifi = BlockingWifi::wrap(EspWifi::new(modem, sysloop.clone(), None)?, sysloop)?;
            memory("after_init");
            wifi.set_configuration(&Configuration::Client(ClientConfiguration {
                ssid: "myssid".try_into().unwrap(),
                password: "mypassword".try_into().unwrap(),
                auth_method: AuthMethod::WPA2Personal,
                ..Default::default()
            }))?;
            wifi.start()?;
            wifi.connect()?;
            wifi.wait_netif_up()?;
            memory("connected");
            let remaining = unsafe { esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) };
            anyhow::ensure!(remaining >= 2048, "StreamingSim task has only {remaining} bytes of stack margin");
            log::info!("SIM_WIFI_CONNECTED");
            std::thread::sleep(std::time::Duration::from_secs(1));
            std::hint::black_box(reserved);
            Ok(())
        })?.join().map_err(|_| anyhow::anyhow!("simulation thread panicked"))??;
    Ok(())
}
