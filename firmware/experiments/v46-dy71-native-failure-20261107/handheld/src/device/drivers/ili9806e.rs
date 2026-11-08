use std::time::{Duration, Instant};
use thiserror::Error;

use embedded_hal::digital::OutputPin;
use embedded_hal::spi::SpiDevice;

use super::lcd_gamma::{GammaPreset, GammaTables};

// Default is the original vendor initialization, byte for byte.
// Low/High are conservative midtone tuning presets, not calibrated exponents.
// Endpoints, power/VCOM settings and packed gamma fields remain unchanged.
const GAMMA_DEFAULT: GammaTables<16> = GammaTables {
    positive: [
        0x00, 0x13, 0x19, 0x0C, 0x06, 0x0A, 0x06, 0x04, 0x09, 0x08, 0x12, 0x06, 0x0E, 0x0E, 0x09,
        0x00,
    ],
    negative: [
        0x00, 0x0D, 0x18, 0x0D, 0x06, 0x09, 0x07, 0x05, 0x08, 0x0E, 0x12, 0x09, 0x0E, 0x0E, 0x08,
        0x00,
    ],
};
const GAMMA_LOW: GammaTables<16> = GammaTables {
    positive: [
        0x00, 0x13, 0x19, 0x0C, 0x06, 0x0B, 0x07, 0x05, 0x0A, 0x09, 0x13, 0x06, 0x0E, 0x0E, 0x09,
        0x00,
    ],
    negative: [
        0x00, 0x0D, 0x18, 0x0D, 0x06, 0x0A, 0x08, 0x06, 0x09, 0x0F, 0x13, 0x09, 0x0E, 0x0E, 0x08,
        0x00,
    ],
};
const GAMMA_HIGH: GammaTables<16> = GammaTables {
    positive: [
        0x00, 0x13, 0x19, 0x0C, 0x06, 0x09, 0x05, 0x03, 0x08, 0x07, 0x11, 0x06, 0x0E, 0x0E, 0x09,
        0x00,
    ],
    negative: [
        0x00, 0x0D, 0x18, 0x0D, 0x06, 0x08, 0x06, 0x04, 0x07, 0x0D, 0x11, 0x09, 0x0E, 0x0E, 0x08,
        0x00,
    ],
};

fn gamma_tables(preset: GammaPreset) -> &'static GammaTables<16> {
    match preset {
        GammaPreset::Default => &GAMMA_DEFAULT,
        GammaPreset::Low => &GAMMA_LOW,
        GammaPreset::High => &GAMMA_HIGH,
    }
}

/// Duration between successive calls to sleep in / sleep out.
const SLEEP_CHANGE_DELAY: Duration = Duration::from_millis(120);

#[derive(Debug, Error)]
pub enum Error {
    #[error("digital gamma probe codes must be 0..15")]
    InvalidGammaCode,
    #[error("reset error")]
    ResetError,
    #[error("spi error")]
    SpiError,
}

pub struct ILI9806E<PinReset: OutputPin, Spi: SpiDevice> {
    pin_reset: PinReset,
    spi: Spi,
    last_sleep_change: Instant,
    gamma: GammaPreset,
    digital_probe: DigitalGammaProbe,
}

/// Raw diagnostic codes, NOT gamma exponents or validated identity tables.
/// ILITEK datasheet pp.239-250: red is the upper nibble, blue the lower.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct DigitalGammaProbe {
    pub enabled: bool,
    pub red: u8,
    pub blue: u8,
    /// 0: mid micro entries, 1: all micro, 2: all macro, 3: both tables.
    pub table: u8,
}

/// Empirical Rev4 macro encoding: bit 3 selects subtraction, bits 0..2
/// magnitude. Both 0 and 8 appear neutral; always encode neutral as 0.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ColorTrim {
    pub red: i8,
    pub blue: i8,
}

impl ColorTrim {
    pub fn from_stored(value: i32) -> Self {
        if !(0..=255).contains(&value) { return Self::default(); }
        fn decode(n: u8) -> i8 {
            let magnitude = (n & 7) as i8;
            if n & 8 != 0 { -magnitude } else { magnitude }
        }
        Self { red: decode((value >> 4) as u8), blue: decode(value as u8) }
    }

    pub fn probe(self) -> Result<DigitalGammaProbe, Error> {
        if !(-7..=7).contains(&self.red) || !(-7..=7).contains(&self.blue) {
            return Err(Error::InvalidGammaCode);
        }
        fn encode(v: i8) -> u8 { if v < 0 { 8 | (-v as u8) } else { v as u8 } }
        Ok(DigitalGammaProbe { enabled: self != Self::default(),
            red: encode(self.red), blue: encode(self.blue), table: 2 })
    }

    pub fn stored(self) -> Result<i32, Error> {
        let probe = self.probe()?;
        Ok(((probe.red << 4) | probe.blue) as i32)
    }
}

impl<PinReset, Spi> ILI9806E<PinReset, Spi>
where
    Spi: SpiDevice,
    PinReset: OutputPin,
{
    pub fn new(pin_reset: PinReset, spi: Spi) -> Self {
        Self {
            pin_reset,
            spi,
            last_sleep_change: Instant::now(),
            gamma: GammaPreset::Default,
            digital_probe: DigitalGammaProbe::default(),
        }
    }

    pub fn init(&mut self) -> Result<(), Error> {
        // Reset the display.
        self.pin_reset.set_high().map_err(|_| Error::ResetError)?;
        std::thread::sleep(Duration::from_millis(1));
        self.pin_reset.set_low().map_err(|_| Error::ResetError)?;
        std::thread::sleep(Duration::from_millis(5));
        self.pin_reset.set_high().map_err(|_| Error::ResetError)?;
        self.last_sleep_change = Instant::now();
        std::thread::sleep(Duration::from_millis(5));
        self.digital_probe = DigitalGammaProbe::default();

        // Change to page 1
        self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x01])?;
        // Output SDA
        self.write_cmd(0x08, &[0x10])?;
        // Display function control 1: DE mode
        self.write_cmd(0x20, &[0x00])?;
        // Display function control 2:
        // Set VSYNC/HSYNC active high (0b11xx)
        // Set data fetched at clock falling edge (0bxx1x)
        // Set data enable polarity active high (0bxxx1)
        self.write_cmd(0x21, &[0b1111])?;
        // Resolution control
        self.write_cmd(0x30, &[0x02])?;
        // Inversion setting: 2 dot
        self.write_cmd(0x31, &[0x00])?;

        // Vendor parameters
        // Source timing adjust
        self.write_cmd(0x60, &[0x07])?;
        self.write_cmd(0x61, &[0x06])?;
        self.write_cmd(0x62, &[0x06])?;
        self.write_cmd(0x63, &[0x04])?;
        // Power control
        self.write_cmd(0x40, &[0x14])?;
        self.write_cmd(0x41, &[0x33])?;
        self.write_cmd(0x42, &[0x01])?;
        self.write_cmd(0x43, &[0x09])?;
        self.write_cmd(0x44, &[0x0A])?;
        self.write_cmd(0x45, &[0x0A])?;
        self.write_cmd(0x50, &[0x78])?;
        self.write_cmd(0x51, &[0x78])?;
        self.write_cmd(0x52, &[0x00])?;
        self.write_cmd(0x53, &[0x3B])?;
        // LVD detect
        self.write_cmd(0x57, &[0x50])?;
        self.write_gamma_tables(&GAMMA_DEFAULT)?;
        self.gamma = GammaPreset::Default;

        // Change to page 7
        self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x07])?;
        self.write_cmd(0x17, &[0x32])?;
        self.write_cmd(0x18, &[0x1D])?;
        self.write_cmd(0x26, &[0xB2])?;
        self.write_cmd(0x02, &[0x77])?;
        self.write_cmd(0xE1, &[0x79])?;
        self.write_cmd(0xE1, &[0x79])?;
        self.write_cmd(0xB3, &[0x10])?;

        // Change to page 6
        self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x06])?;
        self.write_cmd(0x00, &[0x20])?;
        self.write_cmd(0x01, &[0x04])?;
        self.write_cmd(0x02, &[0x00])?;
        self.write_cmd(0x03, &[0x00])?;
        self.write_cmd(0x04, &[0x01])?;
        self.write_cmd(0x05, &[0x01])?;
        self.write_cmd(0x06, &[0x88])?;
        self.write_cmd(0x07, &[0x04])?;
        self.write_cmd(0x08, &[0x01])?;
        self.write_cmd(0x09, &[0x90])?;
        self.write_cmd(0x0A, &[0x03])?;
        self.write_cmd(0x0B, &[0x01])?;
        self.write_cmd(0x0C, &[0x01])?;
        self.write_cmd(0x0D, &[0x01])?;
        self.write_cmd(0x0E, &[0x00])?;
        self.write_cmd(0x0F, &[0x00])?;
        self.write_cmd(0x10, &[0x55])?;
        self.write_cmd(0x11, &[0x53])?;
        self.write_cmd(0x12, &[0x01])?;
        self.write_cmd(0x13, &[0x0D])?;
        self.write_cmd(0x14, &[0x0D])?;
        self.write_cmd(0x15, &[0x43])?;
        self.write_cmd(0x16, &[0x0B])?;
        self.write_cmd(0x17, &[0x00])?;
        self.write_cmd(0x18, &[0x00])?;
        self.write_cmd(0x19, &[0x00])?;
        self.write_cmd(0x1A, &[0x00])?;
        self.write_cmd(0x1B, &[0x00])?;
        self.write_cmd(0x1C, &[0x00])?;
        self.write_cmd(0x1D, &[0x00])?;
        self.write_cmd(0x20, &[0x01])?;
        self.write_cmd(0x21, &[0x23])?;
        self.write_cmd(0x22, &[0x45])?;
        self.write_cmd(0x23, &[0x67])?;
        self.write_cmd(0x24, &[0x01])?;
        self.write_cmd(0x25, &[0x23])?;
        self.write_cmd(0x26, &[0x45])?;
        self.write_cmd(0x27, &[0x67])?;
        self.write_cmd(0x30, &[0x02])?;
        self.write_cmd(0x31, &[0x22])?;
        self.write_cmd(0x32, &[0x11])?;
        self.write_cmd(0x33, &[0xAA])?;
        self.write_cmd(0x34, &[0xBB])?;
        self.write_cmd(0x35, &[0x66])?;
        self.write_cmd(0x36, &[0x00])?;
        self.write_cmd(0x37, &[0x22])?;
        self.write_cmd(0x38, &[0x22])?;
        self.write_cmd(0x39, &[0x22])?;
        self.write_cmd(0x3A, &[0x22])?;
        self.write_cmd(0x3B, &[0x22])?;
        self.write_cmd(0x3C, &[0x22])?;
        self.write_cmd(0x3D, &[0x22])?;
        self.write_cmd(0x3E, &[0x22])?;
        self.write_cmd(0x3F, &[0x22])?;
        self.write_cmd(0x40, &[0x22])?;
        self.write_cmd(0x52, &[0x10])?;
        self.write_cmd(0x53, &[0x12])?;
        self.write_cmd(0x54, &[0x13])?;

        // Change back to page 0 for normal commands
        self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x00])?;
        // Display access control: BGR=0 GS=1
        self.write_cmd(0x36, &[0x01])?;
        // Interface pixel format: 24-bit
        self.write_cmd(0x3A, &[0x70])?;

        Ok(())
    }

    /// Last fully applied preset (also used after wake).
    pub fn gamma(&self) -> GammaPreset {
        self.gamma
    }

    /// Page-1 analog gamma, available in normal operation and sleep.
    pub fn set_gamma(&mut self, preset: GammaPreset) -> Result<(), Error> {
        let result = (|| {
            self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x01])?;
            self.write_gamma_tables(gamma_tables(preset))
        })();
        // Always attempt to restore page 0, even after a failed SPI transaction.
        // Otherwise sleep/display commands could target unrelated page-1 registers.
        let restore = self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x00]);
        result.and(restore)?;
        self.gamma = preset;
        Ok(())
    }

    pub fn digital_gamma_probe(&self) -> DigitalGammaProbe {
        self.digital_probe
    }

    /// Experimental midrange micro-code probe. All tables are initialized before
    /// enabling DGC. Zero-filled entries are a test baseline, not assumed identity.
    /// Disabled mode bypasses DGC and restores the existing analog gamma behavior.
    pub fn set_digital_gamma_probe(&mut self, probe: DigitalGammaProbe) -> Result<(), Error> {
        if probe.red > 15 || probe.blue > 15 || probe.table > 3 {
            return Err(Error::InvalidGammaCode);
        }
        let result = (|| {
            self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x02])?;
            self.write_cmd(0x40, &[0])?;
            if probe.enabled {
                // Complete writes, including first/last entries, follow the
                // datasheet's table-update ordering diagrams.
                for address in 0..64 {
                    let value = if probe.table >= 2 { (probe.red << 4) | probe.blue } else { 0 };
                    self.write_cmd(address, &[value])?;
                }
                for page in [3u8, 4] {
                    self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, page])?;
                    for address in 0..128u8 {
                        let index = (page as usize - 3) * 128 + address as usize;
                        let selected = match probe.table {
                            0 => (96..160).contains(&index),
                            1 | 3 => true,
                            _ => false,
                        };
                        let value = if selected {
                            (probe.red << 4) | probe.blue
                        } else { 0 };
                        self.write_cmd(address, &[value])?;
                    }
                }
                self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x02])?;
                self.write_cmd(0x40, &[1])?;
            }
            self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x00])
        })();
        if result.is_err() {
            // A partial table must never remain enabled. Attempt cleanup even
            // when restoring page zero was the failed operation.
            if self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x02]).is_ok() {
                let _ = self.write_cmd(0x40, &[0]);
            }
            let _ = self.write_cmd(0xFF, &[0xFF, 0x98, 0x06, 0x04, 0x00]);
            self.digital_probe.enabled = false;
            return result;
        }
        self.digital_probe = probe;
        Ok(())
    }

    /// Caller must select page 1. Used at the original position in initialization.
    fn write_gamma_tables(&mut self, tables: &GammaTables<16>) -> Result<(), Error> {
        for (base, curve) in [(0xA0, &tables.positive), (0xC0, &tables.negative)] {
            for (offset, value) in curve.iter().enumerate() {
                self.write_cmd(base + offset as u8, &[*value])?;
            }
        }
        Ok(())
    }

    pub fn enter_sleep(&mut self) -> Result<(), Error> {
        let wait_time = SLEEP_CHANGE_DELAY.saturating_sub(self.last_sleep_change.elapsed());
        std::thread::sleep(wait_time);

        // Display off
        self.write_cmd(0x28, &[])?;

        // Sleep in
        self.write_cmd(0x10, &[])?;
        self.last_sleep_change = Instant::now();

        Ok(())
    }

    pub fn exit_sleep(&mut self) -> Result<(), Error> {
        let wait_time = SLEEP_CHANGE_DELAY.saturating_sub(self.last_sleep_change.elapsed());
        std::thread::sleep(wait_time);

        // Sleep out
        self.write_cmd(0x11, &[])?;
        self.last_sleep_change = Instant::now();

        // Must wait 5ms before sending commands after sleep out.
        std::thread::sleep(Duration::from_millis(5));

        self.set_gamma(self.gamma)?;
        if self.digital_probe.enabled {
            self.set_digital_gamma_probe(self.digital_probe)?;
        }

        // Display on
        self.write_cmd(0x29, &[])?;

        Ok(())
    }

    pub fn write_cmd(&mut self, cmd: u8, params: &[u8]) -> Result<(), Error> {
        // 9-bit spi: D/C bit followed by 8 bits MSB-first
        // Pack everything into bytes.
        let mut data = [0u8; 8];
        if 9 + (9 * params.len()) > data.len() * 8 {
            return Err(Error::SpiError);
        }
        data[0] = cmd >> 1;
        data[1] = (cmd & 1) << 7;
        let mut index: usize = 9;

        let mut push = |bit: u8| {
            data[index / 8] |= (bit & 1) << (7 - (index % 8));
            index += 1;
        };

        for &p in params {
            push(1);
            for i in 0..8 {
                push((p >> (7 - i)) & 1);
            }
        }

        let buf = &data[0..(index + 7) / 8];
        self.spi.write(buf).map_err(|_| Error::SpiError)
    }

    /// Set the LCD to be controlled by the FPGA.
    pub fn enable_fpga_control(&mut self) -> Result<(), Error> {
        // No-op
        Ok(())
    }
}
