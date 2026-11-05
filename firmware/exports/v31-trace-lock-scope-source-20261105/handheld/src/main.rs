use anyhow::Context;

use device::Device;

use crate::{
    device::drivers::{fpga, usb},
    ui::UI,
};

mod core_admission;
mod key_diag_core;
mod core_coordinator;
mod core_access;
mod key_diag_usb;
mod diag_dispatch;
mod key_diag_pages;
mod bitstream;
mod cart_backup;
mod control;
mod device;
mod margin;
mod margin_usb;
mod timing;
mod timing_line;
mod fwinfo;
mod hwinfo;
mod input;
mod kvs;
mod led;
mod power;
mod sd_explorer;
mod streaming;
mod usb_test;
mod video_trace_usb;
mod diag_pages;
mod usb_diag;
pub mod ui;
mod util;
mod worker;

enum StartupAction {
    MainMenu,
    RunCartridge,
}

fn get_startup_action() -> StartupAction {
    match kvs::keys::STARTUP_ACTION.get() {
        Some(1) => StartupAction::RunCartridge,
        _ => StartupAction::MainMenu,
    }
}

fn main() -> anyhow::Result<()> {
    esp_idf_svc::sys::link_patches();
    esp_idf_svc::log::EspLogger::initialize_default();
    esp_idf_svc::log::set_target_level("gpio", log::LevelFilter::Warn).unwrap();

    if let Err(e) = usb::configure_usb(usb::UsbMode::ConsoleOnly) {
        log::error!("USB setup failed: {:?}", e);
    }

    log::info!("Hardware version: {}", hwinfo::get_hardware_version());
    log::info!("Reset reason: {}", unsafe { esp_idf_svc::sys::esp_reset_reason() });
    log::info!(target:"diag","USB_D24 v=1 p=boot name={}",diag_pages::VARIANT);
    log::info!("Serial: {}", hwinfo::get_serial_number());
    kvs::Kvs::init()?;

    // Check that the firmware is compatible with the listed revision.
    cfg_if::cfg_if! {
        if #[cfg(feature = "rev1")] {
            let required_revision = 1;
        } else if #[cfg(feature = "rev2")] {
            let required_revision = 2;
        } else if #[cfg(feature = "rev3")] {
            let required_revision = 3;
        } else if #[cfg(feature = "rev4")] {
            let required_revision = 4;
        } else {
            compile_error!("No board revision selected");
        }
    };
    let actual_revision = hwinfo::get_hardware_version().major;
    if actual_revision != required_revision && actual_revision != 0 && actual_revision != 255 {
        anyhow::bail!(
            "Incompatible firmware revision: device={:?} firmware={}",
            actual_revision,
            required_revision
        );
    }

    // Proceed to initialize device.
    Device::init()?;
    let mut startup_permit = crate::core_access::reserve_program(false,false)?;
    let mut device = Device::lock();
    if device.sdcard.is_none() {
        log::warn!("Failed to mount SD card");
    }
    device.set_brightness(kvs::keys::BRIGHTNESS.get().unwrap());

    // Setup workers.
    worker::start();
    power::PowerManager::start(&mut device);

    // Initial programming FPGA
    fn program_fpga(device: &mut Device, permit: &mut crate::core_admission::ProgramPermit) -> anyhow::Result<()> {
        bitstream::program_boot(device,permit)?;
        device.fpga.enable_interrupt(fpga::Irq::Button)?;
        device.lcd.enable_fpga_control()?;
        Ok(())
    }

    match get_startup_action() {
        StartupAction::RunCartridge => (),
        StartupAction::MainMenu => program_fpga(&mut device,&mut startup_permit).context("Failed to program FPGA")?,
    }

    // Setup UI
    let mut ui = UI::new(&mut device);
    std::mem::drop(device);
    crate::core_access::finish_program(startup_permit,true)?;
    if let StartupAction::RunCartridge=get_startup_action(){worker::send(worker::Message::RunCartridge);}
    usb_test::start();

    // Run UI in this thread.
    if let StartupAction::MainMenu = get_startup_action() {
        led::LedController::set_behavior(led::LedBehavior::OFF);
    }
    ui.run();
}
