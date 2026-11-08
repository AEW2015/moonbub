//! Persist a pair atomically, only after successful panel application.
use crate::device::gamma::Store;
use crate::device::drivers::ili9806e::{ColorTrim, ILI9806E};
use embedded_hal::{digital::OutputPin, spi::SpiDevice};

pub fn change<R: OutputPin, S: SpiDevice>(lcd: &mut ILI9806E<R, S>, store: &impl Store, trim: ColorTrim) -> anyhow::Result<()> {
    let probe = trim.probe()?;
    let previous = lcd.digital_gamma_probe();
    if let Err(e) = lcd.set_digital_gamma_probe(probe) {
        if let Err(rollback) = lcd.set_digital_gamma_probe(previous) {
            log::error!("LCD color trim rollback failed: {rollback}");
        }
        return Err(e.into());
    }
    let packed = trim.stored()?;
    if store.get() != Some(packed) {
        store.set(packed);
        store.flush();
    }
    Ok(())
}

pub fn restore<R: OutputPin, S: SpiDevice>(lcd: &mut ILI9806E<R, S>, store: &impl Store) -> anyhow::Result<()> {
    let trim = ColorTrim::from_stored(store.get().unwrap_or_default());
    if let Err(e) = lcd.set_digital_gamma_probe(trim.probe()?) {
        log::warn!("Could not restore LCD color trim: {e}; restoring neutral");
        lcd.set_digital_gamma_probe(ColorTrim::default().probe()?)?;
        store.set(0);
        store.flush();
    }
    Ok(())
}
