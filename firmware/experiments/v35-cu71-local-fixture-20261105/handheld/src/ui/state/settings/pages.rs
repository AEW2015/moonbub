use crate::kvs::{keys, KvsKey};
use crate::ui::state::ScreenId;

pub struct Page {
    pub name: &'static str,
    pub entries: &'static [Entry],
}

pub enum Entry {
    #[cfg(feature = "has_ili9806e")]
    LcdColorTrim { name: &'static str, channel: usize },
    #[cfg(feature = "has_ili9806e")]
    ResetColorTrim,
    #[cfg(feature = "has_ili9806e")]
    LcdDigitalProbe { name: &'static str, control: usize, choices: &'static [&'static str] },
    #[allow(dead_code)] // Not constructed when the panel lacks a control interface.
    LcdGamma {
        choices: &'static [&'static str],
    },
    Checkbox {
        name: &'static str,
        key: &'static KvsKey<bool>,
    },
    List {
        name: &'static str,
        key: &'static KvsKey<i32>,
        choices: &'static [&'static str],
    },
    SystemDatetime {
        name: &'static str,
    },
    Subpage {
        name: &'static str,
        page: &'static Page,
    },
    Screen {
        name: &'static str,
        screen: ScreenId,
    },
}

pub static PAGE_ROOT: Page = Page {
    name: "",
    entries: &[
        Entry::Screen {
            name: "About",
            screen: ScreenId::About,
        },
        Entry::Subpage {
            name: "General",
            page: &PAGE_GENERAL,
        },
        #[cfg(any(feature = "has_ili9488", feature = "has_ili9806e"))]
        Entry::Subpage {
            name: "Display",
            page: &PAGE_DISPLAY,
        },
        Entry::Subpage {
            name: "Core: GB / GBC",
            page: &PAGE_CORE_GB,
        },
        Entry::Subpage {
            name: "Core: GBA",
            page: &PAGE_CORE_GBA,
        },
    ],
};

#[cfg(any(feature = "has_ili9488", feature = "has_ili9806e"))]
pub static PAGE_DISPLAY: Page = Page {
    name: "Display",
    entries: &[Entry::LcdGamma {
        choices: crate::device::drivers::lcd_gamma::GammaPreset::CHOICES,
    },
    #[cfg(feature = "has_ili9806e")]
    Entry::LcdColorTrim { name: "Red trim", channel: 0 },
    #[cfg(feature = "has_ili9806e")]
    Entry::LcdColorTrim { name: "Blue trim", channel: 1 },
    #[cfg(feature = "has_ili9806e")]
    Entry::ResetColorTrim,
    #[cfg(feature = "has_ili9806e")]
    Entry::Subpage { name: "LCD RGB Lab", page: &PAGE_RGB_LAB },
    ],
};

#[cfg(feature = "has_ili9806e")]
pub static PAGE_RGB_LAB: Page = Page {
    name: "LCD RGB Lab (raw codes)",
    entries: &[
        Entry::LcdDigitalProbe { name: "Correction", control: 0, choices: &["Off", "On (test)"] },
        Entry::LcdDigitalProbe { name: "Table", control: 3, choices: &["Micro mid", "Micro all", "Macro all", "Both all"] },
        Entry::LcdDigitalProbe { name: "Red code", control: 1, choices: RAW_CODES },
        Entry::LcdDigitalProbe { name: "Blue code", control: 2, choices: RAW_CODES },
    ],
};
#[cfg(feature = "has_ili9806e")]
const RAW_CODES: &[&str] = &["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"];

pub static PAGE_GENERAL: Page = Page {
    name: "General",
    entries: &[
        Entry::SystemDatetime {
            name: "Date and Time (UTC)",
        },
        Entry::List {
            name: "Startup Action",
            key: &keys::STARTUP_ACTION,
            choices: &["Main Menu", "Run Cartridge"],
        },
    ],
};

pub static PAGE_CORE_GB: Page = Page {
    name: "Core: GB / GBC",
    entries: &[
        Entry::Checkbox {
            name: "Enable GB mode",
            key: &keys::GB_IS_DMG,
        },
        // Entry::Checkbox {
        //     name: "Skip Boot Animation",
        //     key: &keys::GB_SKIP_BOOT_ANIM,
        // },
        Entry::List {
            name: "GBC Color Corrections",
            key: &keys::CGB_COLOR_PROFILE,
            choices: &["None", "GBC", "GBA", "GBA SP"],
        },
        Entry::List {
            name: "GB Color Palette",
            key: &keys::DMG_COLOR_PALETTE,
            choices: &["Grayscale", "DMG Green", "GB Pocket"],
        },
    ],
};

pub static PAGE_CORE_GBA: Page = Page {
    name: "Core: GBA",
    entries: &[
        // Entry::Checkbox {
        //     name: "Skip Boot Animation",
        //     key: &keys::GBA_SKIP_BOOT_ANIM,
        // },
        Entry::List {
            name: "Color Corrections",
            key: &keys::GBA_COLOR_PROFILE,
            choices: &["None", "GBA", "GBA SP", "NDS", "NDS Lite", "NSO GBA"],
        },
        Entry::Checkbox {
            name: "Enable Game Boy Player",
            key: &keys::GBA_ENABLE_GBP,
        },
    ],
};
