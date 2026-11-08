//! Gamma lifecycle policy, shared by the device and transport-independent tests.
use crate::device::drivers::lcd_gamma::GammaPreset;
use anyhow::Context;

pub trait Panel {
    const SUPPORTED: bool = true;
    type Error: std::error::Error + Send + Sync + 'static;
    fn init(&mut self) -> Result<(), Self::Error>;
    fn gamma(&self) -> GammaPreset;
    fn set_gamma(&mut self, preset: GammaPreset) -> Result<(), Self::Error>;
}

pub trait Store {
    fn get(&self) -> Option<i32>;
    fn set(&self, value: i32);
    fn flush(&self);
}

impl Store for crate::kvs::KvsKey<i32> {
    fn get(&self) -> Option<i32> {
        self.get()
    }
    fn set(&self, value: i32) {
        self.set(&value);
    }
    fn flush(&self) {
        self.flush();
    }
}

pub fn initialize(panel: &mut impl Panel, store: &impl Store) -> anyhow::Result<()> {
    panel.init().context("LCD init")?;
    restore_saved(panel, store)
}

fn restore_saved<P: Panel>(panel: &mut P, store: &impl Store) -> anyhow::Result<()> {
    if !P::SUPPORTED {
        return Ok(());
    }
    let preset = GammaPreset::from_stored(store.get().unwrap_or_default());
    if let Err(error) = panel.set_gamma(preset) {
        log::warn!("Saved LCD gamma could not be applied: {error}; restoring Default");
        panel
            .set_gamma(GammaPreset::Default)
            .context("restore default LCD gamma")?;
        store.set(GammaPreset::Default as i32);
        store.flush();
    }
    Ok(())
}

pub fn change<P: Panel>(
    panel: &mut P,
    store: &impl Store,
    preset: GammaPreset,
) -> anyhow::Result<()> {
    if !P::SUPPORTED {
        anyhow::bail!("LCD gamma is unavailable on this panel");
    }
    let previous = panel.gamma();
    if let Err(error) = panel.set_gamma(preset) {
        if let Err(restore_error) = panel.set_gamma(previous) {
            log::error!("LCD gamma rollback failed: {restore_error}");
        }
        return Err(error).context("set LCD gamma");
    }
    if store.get() != Some(preset as i32) {
        store.set(preset as i32);
        store.flush();
    }
    Ok(())
}

#[cfg(any(feature = "has_ili9488", test))]
impl<
        R: embedded_hal::digital::OutputPin,
        D: embedded_hal::digital::OutputPin,
        S: embedded_hal::spi::SpiDevice,
    > Panel for crate::device::drivers::ili9488::ILI9488<R, D, S>
{
    type Error = crate::device::drivers::ili9488::Error;
    fn init(&mut self) -> Result<(), Self::Error> {
        self.init()
    }
    fn gamma(&self) -> GammaPreset {
        self.gamma()
    }
    fn set_gamma(&mut self, preset: GammaPreset) -> Result<(), Self::Error> {
        self.set_gamma(preset)
    }
}

#[cfg(any(feature = "has_ili9806e", test))]
impl<R: embedded_hal::digital::OutputPin, S: embedded_hal::spi::SpiDevice> Panel
    for crate::device::drivers::ili9806e::ILI9806E<R, S>
{
    type Error = crate::device::drivers::ili9806e::Error;
    fn init(&mut self) -> Result<(), Self::Error> {
        self.init()
    }
    fn gamma(&self) -> GammaPreset {
        self.gamma()
    }
    fn set_gamma(&mut self, preset: GammaPreset) -> Result<(), Self::Error> {
        self.set_gamma(preset)
    }
}

#[cfg(any(feature = "has_st7262", test))]
impl<R: embedded_hal::digital::OutputPin> Panel for crate::device::drivers::st7262::ST7262<R> {
    const SUPPORTED: bool = false;
    type Error = crate::device::drivers::st7262::Error;
    fn init(&mut self) -> Result<(), Self::Error> {
        self.init()
    }
    fn gamma(&self) -> GammaPreset {
        GammaPreset::Default
    }
    fn set_gamma(&mut self, _: GammaPreset) -> Result<(), Self::Error> {
        Err(crate::device::drivers::st7262::Error::GammaUnavailable)
    }
}
