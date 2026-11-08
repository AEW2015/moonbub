#![allow(dead_code)]
// Run the production KVS cache/serialization code against an in-memory NVS backend.
extern crate self as embedded_svc;
extern crate self as esp_idf_svc;
mod storage_mock;
pub use storage_mock::{nvs, storage};
mod kvs {
    include!("../../src/kvs/mod.rs");
    #[cfg(test)]
    static TEST_LOCK: std::sync::Mutex<()> = std::sync::Mutex::new(());
    #[cfg(test)]
    static TEST_INIT: std::sync::Once = std::sync::Once::new();

    #[test]
    fn color_trim_pair_survives_actual_kvs_cache_restart_and_reset() {
        let _guard = TEST_LOCK.lock().unwrap();
        TEST_INIT.call_once(|| Kvs::init().unwrap());
        assert_eq!(keys::LCD_COLOR_TRIM.get(), Some(0));
        for packed in [0xf7, 0x7f, 0] {
            keys::LCD_COLOR_TRIM.set(&packed);
            keys::flush_all();
            *keys::LCD_COLOR_TRIM.cache.write().unwrap() = None;
            assert_eq!(keys::LCD_COLOR_TRIM.get(), Some(packed));
        }
    }

    #[test]
    fn gamma_defaults_and_survives_flush_and_cache_restart() {
        let _guard = TEST_LOCK.lock().unwrap();
        TEST_INIT.call_once(|| Kvs::init().unwrap());
        assert_eq!(keys::LCD_GAMMA.get(), Some(0));
        for value in [1, 2, 0] {
            crate::gamma_control::Store::set(&keys::LCD_GAMMA, value);
            crate::gamma_control::Store::flush(&keys::LCD_GAMMA);
            *keys::LCD_GAMMA.cache.write().unwrap() = None;
            assert_eq!(
                crate::gamma_control::Store::get(&keys::LCD_GAMMA),
                Some(value)
            );
        }
        // Also exercise the existing orderly-shutdown flush list.
        keys::LCD_GAMMA.set(&2);
        keys::flush_all();
        *keys::LCD_GAMMA.cache.write().unwrap() = None;
        assert_eq!(keys::LCD_GAMMA.get(), Some(2));
    }
}
#[path = "../../src/device/drivers/ili9488.rs"]
pub mod ili9488;
#[path = "../../src/device/drivers/ili9806e.rs"]
pub mod ili9806e;
#[path = "../../src/device/drivers/lcd_gamma.rs"]
pub mod lcd_gamma;
#[path = "../../src/device/drivers/st7262.rs"]
pub mod st7262;
mod device {
    pub(crate) use crate::gamma_control as gamma;
    pub mod drivers {
        #[allow(unused_imports)] // All adapters are compiled together in the unit-test build.
        pub use crate::{ili9488, ili9806e, lcd_gamma, st7262};
    }
}
mod ui {
    pub mod state {
        // Only this unrelated screen ID is needed by the real settings schema.
        pub enum ScreenId {
            About,
        }
    }
}
#[path = "../../src/device/gamma.rs"]
mod gamma_control;
#[path = "../../src/device/lcd_color_trim.rs"]
mod lcd_color_trim;
#[path = "../../src/ui/state/settings/gamma.rs"]
mod gamma_setting;
#[path = "../../src/ui/state/settings/pages.rs"]
mod pages;

#[cfg(test)]
mod tests {
    use super::*;
    use embedded_hal::{digital, spi};
    use lcd_gamma::GammaPreset;
    use std::{cell::RefCell, convert::Infallible, rc::Rc};

    mod additional;
    mod digital_probe;
    mod color_trim;

    #[derive(Clone, Default)]
    struct Pin;
    impl digital::ErrorType for Pin {
        type Error = Infallible;
    }
    impl digital::OutputPin for Pin {
        fn set_low(&mut self) -> Result<(), Self::Error> {
            Ok(())
        }
        fn set_high(&mut self) -> Result<(), Self::Error> {
            Ok(())
        }
    }

    #[derive(Default)]
    struct Trace {
        writes: Vec<Vec<u8>>,
        fail_at: Option<usize>,
    }
    #[derive(Clone, Default)]
    struct Spi(Rc<RefCell<Trace>>);
    impl spi::ErrorType for Spi {
        type Error = spi::ErrorKind;
    }
    impl spi::SpiDevice for Spi {
        fn transaction(&mut self, ops: &mut [spi::Operation<'_, u8>]) -> Result<(), Self::Error> {
            let mut trace = self.0.borrow_mut();
            for op in ops {
                match op {
                    spi::Operation::Write(bytes) => {
                        let index = trace.writes.len();
                        trace.writes.push(bytes.to_vec());
                        if trace.fail_at == Some(index) {
                            return Err(spi::ErrorKind::Other);
                        }
                    }
                    _ => panic!("unexpected SPI operation"),
                }
            }
            Ok(())
        }
    }

    // Original firmware values: independent regression oracle, not imported tables.
    const P9488: [u8; 15] = [0, 8, 12, 2, 14, 4, 48, 69, 71, 4, 12, 10, 46, 52, 15];
    const N9488: [u8; 15] = [0, 17, 13, 1, 15, 5, 57, 54, 81, 6, 15, 13, 51, 55, 15];
    const P9806: [u8; 16] = [0, 19, 25, 12, 6, 10, 6, 4, 9, 8, 18, 6, 14, 14, 9, 0];
    const N9806: [u8; 16] = [0, 13, 24, 13, 6, 9, 7, 5, 8, 14, 18, 9, 14, 14, 8, 0];

    fn decode(bytes: &[u8]) -> (u8, Vec<u8>) {
        let words: Vec<u16> = (0..bytes.len() * 8 / 9)
            .map(|word| {
                (0..9).fold(0, |value, bit| {
                    let i = word * 9 + bit;
                    (value << 1) | ((bytes[i / 8] >> (7 - i % 8)) & 1) as u16
                })
            })
            .collect();
        assert_eq!(words[0] & 0x100, 0);
        assert!(words[1..].iter().all(|w| w & 0x100 != 0));
        (
            words[0] as u8,
            words[1..].iter().map(|w| *w as u8).collect(),
        )
    }
    fn commands(spi: &Spi) -> Vec<(u8, Vec<u8>)> {
        spi.0.borrow().writes.iter().map(|w| decode(w)).collect()
    }

    #[test]
    fn stable_storage_ids_and_unknown_value_fallback() {
        for (id, preset) in [
            (0, GammaPreset::Default),
            (1, GammaPreset::Low),
            (2, GammaPreset::High),
        ] {
            assert_eq!(GammaPreset::from_stored(id), preset);
            assert_eq!(preset as i32, id);
        }
        for id in [-1, 3, i32::MAX] {
            assert_eq!(GammaPreset::from_stored(id), GammaPreset::Default);
            assert!(GammaPreset::try_from(id).is_err());
        }
        assert_eq!(
            GammaPreset::CHOICES,
            &["Default", "Low Gamma", "High Gamma"]
        );
    }

    #[test]
    fn ili9488_init_and_default_restore_original_bytes() {
        let spi = Spi::default();
        let mut lcd = ili9488::ILI9488::new(Pin, Pin, spi.clone());
        lcd.init().unwrap();
        let trace = spi.0.borrow();
        let p = trace.writes.iter().position(|x| x == &[0xE0]).unwrap();
        assert_eq!(trace.writes[p + 1], P9488);
        assert_eq!(trace.writes[p + 2], [0xE1]);
        assert_eq!(trace.writes[p + 3], N9488);
        drop(trace);
        for preset in [GammaPreset::Low, GammaPreset::High, GammaPreset::Default] {
            spi.0.borrow_mut().writes.clear();
            lcd.set_gamma(preset).unwrap();
            let trace = spi.0.borrow();
            assert_eq!(trace.writes.len(), 4);
            assert_eq!(trace.writes[0], [0xE0]);
            assert_eq!(trace.writes[2], [0xE1]);
            for curve in [&trace.writes[1], &trace.writes[3]] {
                let masks = [
                    15, 63, 63, 15, 31, 15, 127, 255, 127, 15, 31, 15, 63, 63, 15,
                ];
                assert_eq!(curve.len(), 15);
                for (value, mask) in curve.iter().zip(masks) {
                    assert_eq!(*value & !mask, 0);
                }
            }
            if preset == GammaPreset::Default {
                assert_eq!(trace.writes[1], P9488);
                assert_eq!(trace.writes[3], N9488);
            } else {
                assert_ne!(trace.writes[1], P9488);
                assert_ne!(trace.writes[3], N9488);
            }
        }
    }

    #[test]
    fn ili9806_init_and_runtime_write_only_gamma_with_page_restore() {
        let spi = Spi::default();
        let mut lcd = ili9806e::ILI9806E::new(Pin, spi.clone());
        lcd.init().unwrap();
        let init = commands(&spi);
        let start = init.iter().position(|(cmd, _)| *cmd == 0xA0).unwrap();
        for (base, expected) in [(0xA0, P9806), (0xC0, N9806)] {
            for (i, value) in expected.iter().enumerate() {
                assert_eq!(
                    init[start + if base == 0xA0 { i } else { 16 + i }],
                    (base + i as u8, vec![*value])
                );
            }
        }
        let mut distinct = Vec::new();
        for preset in [GammaPreset::Low, GammaPreset::High, GammaPreset::Default] {
            spi.0.borrow_mut().writes.clear();
            lcd.set_gamma(preset).unwrap();
            let cmds = commands(&spi);
            assert_eq!(cmds.len(), 34);
            assert_eq!(cmds[0], (0xFF, vec![0xFF, 0x98, 6, 4, 1]));
            assert_eq!(cmds[33], (0xFF, vec![0xFF, 0x98, 6, 4, 0]));
            let masks = [
                63, 63, 63, 31, 31, 31, 15, 15, 15, 15, 31, 31, 31, 63, 63, 63,
            ];
            for (base, offset, original) in [(0xA0, 1, P9806), (0xC0, 17, N9806)] {
                for i in 0..16 {
                    assert_eq!(cmds[offset + i].0, base + i as u8);
                    assert_eq!(cmds[offset + i].1.len(), 1);
                    assert_eq!(cmds[offset + i].1[0] & !masks[i], 0);
                    if preset == GammaPreset::Default {
                        assert_eq!(cmds[offset + i].1[0], original[i]);
                    }
                }
            }
            assert!(!distinct.contains(&cmds));
            distinct.push(cmds);
        }
    }

    #[test]
    fn ili9806_error_at_every_write_restores_page_and_keeps_last_success() {
        for fail_at in 0..34 {
            let spi = Spi::default();
            let mut lcd = ili9806e::ILI9806E::new(Pin, spi.clone());
            lcd.set_gamma(GammaPreset::Low).unwrap();
            spi.0.borrow_mut().writes.clear();
            spi.0.borrow_mut().fail_at = Some(fail_at);
            assert!(lcd.set_gamma(GammaPreset::High).is_err());
            assert_eq!(lcd.gamma(), GammaPreset::Low);
            assert_eq!(
                commands(&spi).last().unwrap(),
                &(0xFF, vec![0xFF, 0x98, 6, 4, 0])
            );
            spi.0.borrow_mut().fail_at = None;
            lcd.set_gamma(GammaPreset::Low).unwrap();
            assert_eq!(lcd.gamma(), GammaPreset::Low);
        }
    }

    #[test]
    fn ili9488_error_does_not_accept_new_preset() {
        for fail_at in 0..4 {
            let spi = Spi::default();
            let mut lcd = ili9488::ILI9488::new(Pin, Pin, spi.clone());
            lcd.set_gamma(GammaPreset::Low).unwrap();
            spi.0.borrow_mut().writes.clear();
            spi.0.borrow_mut().fail_at = Some(fail_at);
            assert!(lcd.set_gamma(GammaPreset::High).is_err());
            assert_eq!(lcd.gamma(), GammaPreset::Low);
        }
    }

    #[test]
    fn selected_gamma_is_reapplied_before_display_on_after_wake() {
        let spi = Spi::default();
        let mut lcd = ili9806e::ILI9806E::new(Pin, spi.clone());
        lcd.set_gamma(GammaPreset::High).unwrap();
        let expected = commands(&spi);
        spi.0.borrow_mut().writes.clear();
        lcd.exit_sleep().unwrap();
        let woke = commands(&spi);
        assert_eq!(woke[0], (0x11, vec![]));
        assert_eq!(&woke[1..35], expected.as_slice());
        assert_eq!(woke[35], (0x29, vec![]));

        let spi = Spi::default();
        let mut lcd = ili9488::ILI9488::new(Pin, Pin, spi.clone());
        lcd.set_gamma(GammaPreset::High).unwrap();
        let expected = spi.0.borrow().writes.clone();
        spi.0.borrow_mut().writes.clear();
        lcd.exit_sleep().unwrap();
        let trace = spi.0.borrow();
        assert_eq!(trace.writes[0], [0x11]);
        assert_eq!(&trace.writes[1..5], expected.as_slice());
        assert_eq!(trace.writes[5], [0x29]);
    }
}
