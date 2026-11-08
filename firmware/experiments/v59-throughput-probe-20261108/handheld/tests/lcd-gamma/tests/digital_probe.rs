use super::*;
use ili9806e::{DigitalGammaProbe, ILI9806E};

#[test]
fn probe_starts_disabled_and_rejects_out_of_range_without_spi() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    assert_eq!(lcd.digital_gamma_probe(), DigitalGammaProbe::default());
    for (red, blue) in [(16, 0), (0, 16), (255, 255)] {
        assert!(lcd.set_digital_gamma_probe(DigitalGammaProbe { enabled: true, red, blue, table: 0 }).is_err());
    }
    assert!(commands(&spi).is_empty());
    assert!(lcd.set_digital_gamma_probe(DigitalGammaProbe {
        enabled: true, table: 4, ..Default::default()
    }).is_err());
    assert!(commands(&spi).is_empty());
}

#[test]
fn full_table_probes_distinguish_macro_micro_and_combined() {
    for table in 1..=3 {
        for (red, blue, packed) in [(15, 0, 0xf0), (0, 15, 0x0f)] {
            let spi = Spi::default();
            let mut lcd = ILI9806E::new(Pin, spi.clone());
            lcd.set_digital_gamma_probe(DigitalGammaProbe { enabled: true, red, blue, table }).unwrap();
            let mut page = 0;
            let mut macro_count = 0;
            let mut micro_count = 0;
            for (address, value) in commands(&spi) {
                if address == 0xff { page = value[4]; }
                else if page == 2 && address < 64 {
                    assert_eq!(value, [if table >= 2 { packed } else { 0 }]);
                    macro_count += 1;
                } else if page == 3 || page == 4 {
                    assert_eq!(value, [if table == 2 { 0 } else { packed }]);
                    micro_count += 1;
                }
            }
            assert_eq!((macro_count, micro_count, page), (64, 256, 0));
        }
    }
}

#[test]
fn probe_programs_complete_tables_before_enabling_with_correct_color_nibbles() {
    for (red, blue) in [(0, 0), (15, 0), (0, 15), (3, 10)] {
        let spi = Spi::default();
        let mut lcd = ILI9806E::new(Pin, spi.clone());
        let probe = DigitalGammaProbe { enabled: true, red, blue, table: 0 };
        lcd.set_digital_gamma_probe(probe).unwrap();
        assert_eq!(lcd.digital_gamma_probe(), probe);
        let mut page = 0;
        let mut counts = [0; 5];
        let mut enabled = false;
        for (cmd, params) in commands(&spi) {
            if cmd == 0xff {
                assert_eq!(&params[..4], &[0xff, 0x98, 6, 4]);
                page = params[4] as usize;
            } else if page == 2 && cmd == 0x40 {
                if params == [1] {
                    assert_eq!(counts, [0, 0, 64, 128, 128]);
                    enabled = true;
                } else {
                    assert_eq!(params, [0]);
                    assert_eq!(counts, [0; 5]);
                }
            } else {
                assert!(!enabled);
                assert!((2..=4).contains(&page));
                assert_eq!(cmd as usize, counts[page]);
                let index = (page.saturating_sub(3)) * 128 + cmd as usize;
                let expected = if page >= 3 && (96..160).contains(&index) {
                    (red << 4) | blue
                } else { 0 };
                assert_eq!(params, [expected]);
                counts[page] += 1;
            }
        }
        assert!(enabled);
        assert_eq!(page, 0);
    }
}

#[test]
fn disabling_probe_only_bypasses_digital_correction() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    lcd.set_digital_gamma_probe(DigitalGammaProbe::default()).unwrap();
    assert_eq!(commands(&spi), vec![
        (0xff, vec![0xff, 0x98, 6, 4, 2]), (0x40, vec![0]),
        (0xff, vec![0xff, 0x98, 6, 4, 0]),
    ]);
}

#[test]
fn every_single_spi_failure_attempts_disable_and_page_zero_cleanup() {
    let probe = DigitalGammaProbe { enabled: true, red: 3, blue: 7, table: 0 };
    let spi = Spi::default();
    ILI9806E::new(Pin, spi.clone()).set_digital_gamma_probe(probe).unwrap();
    let length = commands(&spi).len();
    for failure in 0..length {
        let spi = Spi::default();
        spi.0.borrow_mut().fail_at = Some(failure);
        let mut lcd = ILI9806E::new(Pin, spi.clone());
        assert!(lcd.set_digital_gamma_probe(probe).is_err());
        assert!(!lcd.digital_gamma_probe().enabled);
        let trace = commands(&spi);
        assert_eq!(&trace[trace.len()-3..], &[
            (0xff, vec![0xff, 0x98, 6, 4, 2]), (0x40, vec![0]),
            (0xff, vec![0xff, 0x98, 6, 4, 0]),
        ]);
    }
}

#[test]
fn enabled_probe_is_restored_before_display_on_after_wake() {
    let spi = Spi::default();
    let mut lcd = ILI9806E::new(Pin, spi.clone());
    let probe = DigitalGammaProbe { enabled: true, red: 2, blue: 4, table: 0 };
    lcd.set_digital_gamma_probe(probe).unwrap();
    let expected = commands(&spi);
    spi.0.borrow_mut().writes.clear();
    lcd.exit_sleep().unwrap();
    let trace = commands(&spi);
    assert_eq!(&trace[35..trace.len()-1], &expected);
    assert_eq!(trace.last(), Some(&(0x29, vec![])));
}
