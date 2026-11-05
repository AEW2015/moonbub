use super::*;
use ili9806e::{ColorTrim, ILI9806E};
use std::cell::Cell;

#[derive(Default)]
struct Store { value: Cell<Option<i32>>, flushes: Cell<usize> }
impl crate::gamma_control::Store for Store {
    fn get(&self) -> Option<i32> { self.value.get() }
    fn set(&self, value: i32) { self.value.set(Some(value)); }
    fn flush(&self) { self.flushes.set(self.flushes.get() + 1); }
}

#[test]
fn all_signed_pairs_round_trip_and_select_macro_only() {
    for red in -7..=7 {
        for blue in -7..=7 {
            let trim = ColorTrim { red, blue };
            let packed = trim.stored().unwrap();
            assert_eq!(ColorTrim::from_stored(packed), trim);
            let probe = trim.probe().unwrap();
            assert_eq!(probe.table, 2);
            assert_eq!(probe.enabled, red != 0 || blue != 0);
            assert_eq!(probe.red & 7, red.unsigned_abs());
            assert_eq!(probe.blue & 7, blue.unsigned_abs());
            assert_eq!(probe.red & 8 != 0, red < 0);
            assert_eq!(probe.blue & 8 != 0, blue < 0);
        }
    }
}

#[test]
fn observed_negative_zero_codes_decode_to_neutral_bypass() {
    for value in [0, 8, 0x80, 0x88, -1, 256, i32::MAX] {
        let trim = ColorTrim::from_stored(value);
        assert_eq!(trim, ColorTrim::default());
        assert_eq!(trim.stored().unwrap(), 0);
        assert!(!trim.probe().unwrap().enabled);
    }
}

#[test]
fn invalid_signed_values_do_not_touch_panel_or_store() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    let store = Store::default();
    for trim in [ColorTrim { red: -8, blue: 0 }, ColorTrim { red: 0, blue: 8 }, ColorTrim { red: i8::MIN, blue: 0 }] {
        assert!(lcd_color_trim::change(&mut lcd, &store, trim).is_err());
    }
    assert!(commands(&spi).is_empty());
    assert_eq!(store.flushes.get(), 0);
}

#[test]
fn pair_is_saved_then_restored_into_a_fresh_panel() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi);
    let store = Store::default();
    let trim = ColorTrim { red: -7, blue: 7 };
    lcd_color_trim::change(&mut lcd, &store, trim).unwrap();
    assert_eq!(store.value.get(), Some(0xf7));
    assert_eq!(store.flushes.get(), 1);
    lcd_color_trim::change(&mut lcd, &store, trim).unwrap();
    assert_eq!(store.flushes.get(), 1);
    let mut fresh = ILI9806E::new(Pin, Spi::default());
    lcd_color_trim::restore(&mut fresh, &store).unwrap();
    assert_eq!(fresh.digital_gamma_probe(), trim.probe().unwrap());
}

#[test]
fn failed_trim_change_rolls_back_without_persisting() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    let store = Store::default();
    let previous = ColorTrim { red: 2, blue: -3 };
    lcd_color_trim::change(&mut lcd, &store, previous).unwrap();
    let count = spi.0.borrow().writes.len();
    spi.0.borrow_mut().fail_at = Some(count + 20);
    assert!(lcd_color_trim::change(&mut lcd, &store, ColorTrim { red: -7, blue: 7 }).is_err());
    assert_eq!(store.value.get(), Some(previous.stored().unwrap()));
    assert_eq!(store.flushes.get(), 1);
    assert_eq!(lcd.digital_gamma_probe(), previous.probe().unwrap());
}

#[test]
fn reset_disables_digital_gamma_and_persists_neutral() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    let store = Store::default();
    lcd_color_trim::change(&mut lcd, &store, ColorTrim { red: 7, blue: -7 }).unwrap();
    spi.0.borrow_mut().writes.clear();
    lcd_color_trim::change(&mut lcd, &store, ColorTrim::default()).unwrap();
    assert_eq!(commands(&spi).len(), 3);
    assert_eq!(commands(&spi)[1], (0x40, vec![0]));
    assert_eq!(store.value.get(), Some(0));
    assert!(!lcd.digital_gamma_probe().enabled);
}

#[test]
fn failed_startup_restore_recovers_to_neutral_and_saves_it() {
    let spi = Spi::default();
    spi.0.borrow_mut().fail_at = Some(20);
    let mut lcd = ILI9806E::new(Pin, spi);
    let store = Store { value: Cell::new(Some(0xf7)), ..Default::default() };
    lcd_color_trim::restore(&mut lcd, &store).unwrap();
    assert_eq!(store.value.get(), Some(0));
    assert!(!lcd.digital_gamma_probe().enabled);
}
