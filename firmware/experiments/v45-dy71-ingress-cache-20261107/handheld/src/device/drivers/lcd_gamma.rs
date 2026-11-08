//! LCD analog gamma selection. Register encodings belong to each panel driver.

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
#[repr(i32)]
pub enum GammaPreset {
    #[default]
    Default = 0,
    Low = 1,
    High = 2,
}

impl GammaPreset {
    pub const CHOICES: &'static [&'static str] = &["Default", "Low Gamma", "High Gamma"];

    /// Stable storage IDs, independent of the driver register tables.
    pub fn from_stored(value: i32) -> Self {
        Self::try_from(value).unwrap_or_default()
    }
}

impl TryFrom<i32> for GammaPreset {
    type Error = ();

    fn try_from(value: i32) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(Self::Default),
            1 => Ok(Self::Low),
            2 => Ok(Self::High),
            _ => Err(()),
        }
    }
}

/// Separate positive and negative polarity curves, in controller register order.
/// Drivers can add presets (or validated custom curves) without changing the UI.
#[allow(dead_code)] // The ST7262 build has no programmable gamma tables.
pub struct GammaTables<const N: usize> {
    pub positive: [u8; N],
    pub negative: [u8; N],
}
