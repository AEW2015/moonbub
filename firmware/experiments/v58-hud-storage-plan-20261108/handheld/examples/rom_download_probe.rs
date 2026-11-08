//! Emulator-only check of the ESP32-S3 ROM-download reset request.
fn main() {
    esp_idf_svc::sys::link_patches();
    esp_idf_svc::log::EspLogger::initialize_default();
    log::info!("SIM_ROM_DOWNLOAD_REQUEST");
    std::thread::sleep(std::time::Duration::from_millis(100));
    unsafe {
        let reg = 0x6000_812c as *mut u32;
        core::ptr::write_volatile(reg, core::ptr::read_volatile(reg) | 1);
        esp_idf_svc::sys::esp_restart();
    }
}
