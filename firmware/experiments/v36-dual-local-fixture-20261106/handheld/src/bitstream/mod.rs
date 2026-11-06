use std::fs::File;
use std::io::Read;
use std::sync::{Mutex, MutexGuard};
use std::time::Duration;

use crate::bitstream::util::scratch_buffer::ScratchBuffer;
use crate::device::DisplayMode;
use crate::device::{drivers::fpga, Device};
use crate::led;
use crate::ui;

pub mod boot;
pub mod gameboy;
pub mod gba;
pub mod native;

mod util;

// FPGA programming and the retained file readers use bounded chunks.
static SCRATCH: ScratchBuffer<{ 4 * 1024 }> = ScratchBuffer::new();

/// Driver for a specific bitstream.
pub trait Bitstream {
    /// Get the path for the bitstream.
    fn get_bitstream_path(&self) -> &'static str;

    /// Do final initialization after programming the bitstream.
    fn on_after_program(&mut self) -> Result<(), String>;

    /// Set whether the inner design is paused.
    fn set_paused(&mut self, paused: bool) -> Result<(), fpga::Error>;

    /// Reset the inner design, leaving it paused.
    fn reset(&mut self) -> Result<(), fpga::Error>;

    /// Called when a vblank IRQ occurs.
    fn on_vblank_irq(&mut self);
}

/// The current global bitstream, behind a lock.
static CURRENT: Mutex<CurrentBitstream> = Mutex::new(CurrentBitstream::None);

/// Lock and return the current bitstream.
pub fn current() -> MutexGuard<'static, CurrentBitstream> {
    CURRENT.lock().unwrap()
}

fn program_fpga(path: &str, permit:&mut crate::core_admission::ProgramPermit) -> Result<(),String> {
    let file=crate::util::open_system_file(path).map_err(|e|e.to_string())?;
    let mut scratch=SCRATCH.take().ok_or_else(||"FPGA scratch Busy".to_string())?;
    let authorization=permit.authorize_call().map_err(|e|format!("FPGA Busy: {e:?}"))?;
    log::info!("Loading bitstream {}", path);
    led::LedController::set_behavior(led::LedBehavior::LOADING);
    let mut device = Device::lock();
    let display_mode = device.get_display_mode();

    if let DisplayMode::Internal = display_mode {
        // Avoid LCD artifacts during FPGA reprogram.
        device.set_lcd_enabled(false);
        // For some reason, we need to sleep for a short amount of time here
        // (before doing FPGA program), otherwise the LCD won't properly sleep.
        // 2 ms is sometimes sufficient, 5 ms is always sufficient, 10 ms seems to always work.
        std::thread::sleep(Duration::from_millis(10));
    }

    let mut bitstream = heatshrink_decompress_stream(file);

    device
        .fpga
        .program(&mut bitstream, &mut scratch, authorization)
        .map_err(|e|e.to_string())?;
    device.fpga.set_display_mode(display_mode).unwrap();
    device.fpga.enable_interrupt(fpga::Irq::Button).unwrap();
    ui::send(ui::Message::InputState(device.get_input_state().unwrap()));
    ui::send(ui::Message::Redraw);
    led::LedController::set_behavior(led::LedBehavior::OFF);

    if let DisplayMode::Internal = display_mode {
        device.set_lcd_enabled(true);
    }
    Ok(())
}

pub fn program_boot(device: &mut Device, permit:&mut crate::core_admission::ProgramPermit) -> anyhow::Result<()> {
    use anyhow::Context as _;
    let file = crate::util::open_system_file("boot.bit.hs").context("Failed to read bitstream")?;
    let mut bitstream = heatshrink_decompress_stream(file);

    let mut scratch=SCRATCH.take().ok_or_else(||anyhow::anyhow!("FPGA scratch Busy"))?;
    let authorization=permit.authorize_call().map_err(|e|anyhow::anyhow!("FPGA Busy: {e:?}"))?;
    device
        .fpga
        .program(&mut bitstream, &mut scratch,authorization)
        .context("Failed to program FPGA")
}

fn heatshrink_decompress_stream(file: File) -> impl Read {
    // Heatshrink decoder parameters: W=9, L=6 (chosen empirically)
    type HeatshrinkDecoder = heatshrink::decoder::HeatshrinkDecoder<9, 6, 512, 512>;
    let reader = embedded_io_adapters::std::FromStd::new(file);
    let decoder = heatshrink::io::DecoderReader::<_, HeatshrinkDecoder>::new(reader);
    embedded_io_adapters::std::ToStd::new(decoder)
}

pub enum CurrentBitstream {
    None,
    Native,
    Streaming,
    Gameboy(gameboy::Gameboy),
    Gba(gba::Gba),
    // TODO: add "Boot" variant to distinguish between actually None and Boot.
}

impl CurrentBitstream {
    pub fn get(&mut self) -> Option<&mut dyn Bitstream> {
        match self {
            CurrentBitstream::None | CurrentBitstream::Native | CurrentBitstream::Streaming => None,
            CurrentBitstream::Gameboy(x) => Some(x),
            CurrentBitstream::Gba(x) => Some(x),
        }
    }

    fn set(&mut self, new: CurrentBitstream, permit:&mut crate::core_admission::ProgramPermit) -> Result<(), String> {
        *self = new;
        if let Some(bitstream) = self.get() {
            program_fpga(bitstream.get_bitstream_path(),permit)?;
            bitstream.on_after_program()?;
        }
        Ok(())
    }

    /// Ensure the boot is loaded.
    pub fn ensure_boot(&mut self, permit:&mut crate::core_admission::ProgramPermit) -> Result<(), String> {
        match self {
            CurrentBitstream::None => Ok(()),
            _ => {
                program_fpga("boot.bit.hs",permit)?;
                self.set(CurrentBitstream::None,permit)
            }
        }
    }

    /// Ensure the gameboy bitstream is loaded.
    pub fn ensure_gameboy(&mut self, permit:&mut crate::core_admission::ProgramPermit) -> Result<(), String> {
        match self {
            CurrentBitstream::Gameboy(_) => Ok(()),
            _ => {
                let bitstream = gameboy::Gameboy::new();
                self.set(CurrentBitstream::Gameboy(bitstream),permit)
            }
        }
    }

    /// Ensure the GBA bitstream is loaded.
    pub fn ensure_gba(&mut self, permit:&mut crate::core_admission::ProgramPermit) -> Result<(), String> {
        match self {
            CurrentBitstream::Gba(_) => Ok(()),
            _ => {
                let bitstream = gba::Gba::new();
                self.set(CurrentBitstream::Gba(bitstream),permit)
            }
        }
    }
}
