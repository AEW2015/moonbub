//! Adapter used by the settings callback and row model, independent of Slint.
use crate::device::drivers::lcd_gamma::GammaPreset;

pub fn selected_value(stored: Option<i32>) -> i32 {
    GammaPreset::from_stored(stored.unwrap_or_default()) as i32
}

pub fn changed<E: std::fmt::Display>(
    value: i32,
    apply: impl FnOnce(GammaPreset) -> Result<(), E>,
    notify_failure: impl FnOnce(),
) {
    if let Ok(preset) = GammaPreset::try_from(value) {
        if let Err(error) = apply(preset) {
            log::error!("Could not change LCD gamma: {error:#}");
            notify_failure();
        }
    }
}
