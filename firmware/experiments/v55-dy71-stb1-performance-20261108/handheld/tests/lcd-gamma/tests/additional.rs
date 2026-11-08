use super::*;
use crate::gamma_control::{self as control, Panel, Store};
use std::{cell::Cell, collections::VecDeque};

#[derive(Debug, PartialEq, Eq)]
enum Event {
    Init,
    Apply(GammaPreset),
    Applied(GammaPreset),
    Read,
    Set(i32, usize),
    Flush,
    Notify,
}
type Events = Rc<RefCell<Vec<Event>>>;

struct MemoryStore {
    cached: Cell<Option<i32>>,
    saved: Cell<Option<i32>>,
    events: Events,
    spi: Option<Spi>,
}
impl Store for MemoryStore {
    fn get(&self) -> Option<i32> {
        self.events.borrow_mut().push(Event::Read);
        self.cached.get()
    }
    fn set(&self, value: i32) {
        let writes = self.spi.as_ref().map_or(0, |s| s.0.borrow().writes.len());
        self.events.borrow_mut().push(Event::Set(value, writes));
        self.cached.set(Some(value));
    }
    fn flush(&self) {
        self.events.borrow_mut().push(Event::Flush);
        self.saved.set(self.cached.get());
    }
}
struct MockPanel {
    current: GammaPreset,
    fail: VecDeque<bool>,
    events: Events,
}
impl Panel for MockPanel {
    type Error = std::io::Error;
    fn init(&mut self) -> Result<(), Self::Error> {
        self.events.borrow_mut().push(Event::Init);
        self.current = GammaPreset::Default;
        Ok(())
    }
    fn gamma(&self) -> GammaPreset {
        self.current
    }
    fn set_gamma(&mut self, preset: GammaPreset) -> Result<(), Self::Error> {
        self.events.borrow_mut().push(Event::Apply(preset));
        if self.fail.pop_front().unwrap_or(false) {
            return Err(std::io::Error::other("injected SPI fault"));
        }
        self.current = preset;
        self.events.borrow_mut().push(Event::Applied(preset));
        Ok(())
    }
}
fn fixture(saved: Option<i32>) -> (MockPanel, MemoryStore, Events) {
    let events = Events::default();
    (
        MockPanel {
            current: GammaPreset::from_stored(saved.unwrap_or_default()),
            fail: VecDeque::new(),
            events: events.clone(),
        },
        MemoryStore {
            cached: Cell::new(saved),
            saved: Cell::new(saved),
            events: events.clone(),
            spi: None,
        },
        events,
    )
}
fn callback(panel: &mut impl Panel, store: &MemoryStore, value: i32) {
    crate::gamma_setting::changed(
        value,
        |preset| control::change(panel, store, preset),
        || store.events.borrow_mut().push(Event::Notify),
    );
}
fn displayed(store: &MemoryStore) -> i32 {
    crate::gamma_setting::selected_value(store.get())
}
fn writes(events: &Events) -> usize {
    events
        .borrow()
        .iter()
        .filter(|e| matches!(e, Event::Set(..) | Event::Flush))
        .count()
}
fn assert_supported_page() {
    let display: Vec<_> = crate::pages::PAGE_ROOT
        .entries
        .iter()
        .filter_map(|e| match e {
            crate::pages::Entry::Subpage {
                name: "Display",
                page,
            } => Some(*page),
            _ => None,
        })
        .collect();
    assert_eq!(display.len(), 1);
    assert_eq!(display[0].name, "Display");
    assert_eq!(display[0].entries.len(), if cfg!(feature = "has_ili9806e") { 5 } else { 1 });
    match &display[0].entries[0] {
        crate::pages::Entry::LcdGamma { choices } => {
            assert_eq!(*choices, &["Default", "Low Gamma", "High Gamma"])
        }
        _ => panic!("Display page must expose the gamma list"),
    }
}

// 1–7: use the same callback adapter and selected-value mapping as SettingsModel.
#[test]
fn settings_callback_sends_selected_preset_to_driver() {
    let (mut panel, store, events) = fixture(Some(0));
    callback(&mut panel, &store, 1);
    assert!(events.borrow().contains(&Event::Apply(GammaPreset::Low)));
    assert_eq!(panel.gamma(), GammaPreset::Low);
}
#[test]
fn successful_setting_displays_applied_preset() {
    let (mut panel, store, _) = fixture(Some(0));
    callback(&mut panel, &store, 2);
    assert_eq!(displayed(&store), 2);
    assert_eq!(panel.gamma(), GammaPreset::High);
}
#[test]
fn failed_setting_displays_previous_selection() {
    let (mut panel, store, _) = fixture(Some(1));
    panel.fail = [true, false].into();
    callback(&mut panel, &store, 2);
    assert_eq!(displayed(&store), 1);
    assert_eq!(panel.gamma(), GammaPreset::Low);
}
#[test]
fn failed_setting_notifies_exactly_once() {
    let (mut panel, store, events) = fixture(Some(1));
    panel.fail = [true, true].into();
    callback(&mut panel, &store, 2);
    assert_eq!(
        events
            .borrow()
            .iter()
            .filter(|e| **e == Event::Notify)
            .count(),
        1
    );
}
#[test]
fn invalid_ui_index_has_no_hardware_or_storage_side_effects() {
    let (mut panel, store, events) = fixture(Some(1));
    for value in [-1, 3, i32::MIN, i32::MAX] {
        callback(&mut panel, &store, value);
    }
    assert!(events.borrow().is_empty());
    assert_eq!(store.saved.get(), Some(1));
}
#[test]
fn already_saved_preset_avoids_nvs_writes() {
    let (mut panel, store, events) = fixture(Some(1));
    callback(&mut panel, &store, 1);
    assert_eq!(writes(&events), 0);
    assert_eq!(panel.gamma(), GammaPreset::Low);
}
#[test]
fn rapid_changes_finish_with_high_applied_and_saved() {
    let (mut panel, store, events) = fixture(None);
    for value in [0, 1, 2] {
        callback(&mut panel, &store, value);
    }
    assert_eq!(panel.gamma(), GammaPreset::High);
    assert_eq!(store.saved.get(), Some(2));
    assert_eq!(displayed(&store), 2);
    assert_eq!(
        events
            .borrow()
            .iter()
            .filter(|e| **e == Event::Flush)
            .count(),
        3
    );
}

// 8–10: compile the real settings pages separately for each board feature.
#[test]
#[cfg(feature = "rev4")]
fn rev4_settings_expose_all_three_gamma_presets() {
    assert_supported_page();
}
#[test]
#[cfg(feature = "rev2")]
fn rev2_settings_expose_all_three_gamma_presets() {
    assert_supported_page();
}
#[test]
#[cfg(feature = "rev3")]
fn rev3_settings_have_no_gamma_entry() {
    fn contains_gamma(page: &crate::pages::Page) -> bool {
        page.entries.iter().any(|e| match e {
            crate::pages::Entry::LcdGamma { .. } => true,
            crate::pages::Entry::Subpage { page, .. } => contains_gamma(page),
            _ => false,
        })
    }
    assert!(!contains_gamma(&crate::pages::PAGE_ROOT));
    assert!(!crate::pages::PAGE_ROOT.entries.iter().any(|e| matches!(
        e,
        crate::pages::Entry::Subpage {
            name: "Display",
            ..
        }
    )));
}
#[test]
fn unsupported_panel_rejects_change_without_touching_storage() {
    let (_, store, events) = fixture(Some(1));
    let mut panel = crate::st7262::ST7262::new(Pin);
    assert!(control::change(&mut panel, &store, GammaPreset::High)
        .unwrap_err()
        .to_string()
        .contains("unavailable"));
    assert!(events.borrow().is_empty());
    assert_eq!(store.saved.get(), Some(1));
}

fn check_startup(saved: Option<i32>, expected: GammaPreset) {
    let (mut panel, store, events) = fixture(saved);
    control::initialize(&mut panel, &store).unwrap();
    assert_eq!(
        *events.borrow(),
        [
            Event::Init,
            Event::Read,
            Event::Apply(expected),
            Event::Applied(expected)
        ]
    );
    assert_eq!(panel.gamma(), expected);
    assert_eq!(displayed(&store), expected as i32);
}
#[test]
fn startup_without_saved_setting_applies_default_after_init() {
    check_startup(None, GammaPreset::Default);
}
#[test]
fn startup_applies_saved_low_after_init() {
    check_startup(Some(1), GammaPreset::Low);
}
#[test]
fn startup_applies_saved_high_after_init() {
    check_startup(Some(2), GammaPreset::High);
}
#[test]
fn startup_unknown_id_uses_default_and_valid_ui_selection() {
    check_startup(Some(99), GammaPreset::Default);
}
#[test]
fn startup_apply_failure_attempts_default_restore() {
    let (mut panel, store, events) = fixture(Some(2));
    panel.fail = [true, false].into();
    control::initialize(&mut panel, &store).unwrap();
    let applies: Vec<_> = events
        .borrow()
        .iter()
        .filter_map(|e| {
            if let Event::Apply(p) = e {
                Some(*p)
            } else {
                None
            }
        })
        .collect();
    assert_eq!(applies, [GammaPreset::High, GammaPreset::Default]);
}
#[test]
fn successful_startup_fallback_saves_and_displays_default() {
    let (mut panel, store, events) = fixture(Some(1));
    panel.fail = [true, false].into();
    control::initialize(&mut panel, &store).unwrap();
    assert_eq!(panel.gamma(), GammaPreset::Default);
    assert_eq!(store.saved.get(), Some(0));
    assert_eq!(displayed(&store), 0);
    assert_eq!(writes(&events), 2);
}
#[test]
fn failed_startup_fallback_returns_initialization_error() {
    let (mut panel, store, events) = fixture(Some(2));
    panel.fail = [true, true].into();
    let error = control::initialize(&mut panel, &store).unwrap_err();
    assert!(error.to_string().contains("restore default"));
    assert_eq!(store.saved.get(), Some(2));
    assert_eq!(writes(&events), 0);
}

#[test]
fn partial_runtime_failure_rewrites_both_previous_curves() {
    let (_, store, _) = fixture(Some(1));
    let spi = Spi::default();
    let mut panel = ili9806e::ILI9806E::new(Pin, spi.clone());
    panel.set_gamma(GammaPreset::Low).unwrap();
    let expected = commands(&spi);
    spi.0.borrow_mut().writes.clear();
    spi.0.borrow_mut().fail_at = Some(20); // Positive curve and part of negative written.
    assert!(control::change(&mut panel, &store, GammaPreset::High).is_err());
    let actual = commands(&spi);
    assert_eq!(&actual[actual.len() - 34..], expected.as_slice());
    assert_eq!(panel.gamma(), GammaPreset::Low);

    let spi = Spi::default();
    let mut panel = ili9488::ILI9488::new(Pin, Pin, spi.clone());
    panel.set_gamma(GammaPreset::Low).unwrap();
    let expected = spi.0.borrow().writes.clone();
    spi.0.borrow_mut().writes.clear();
    spi.0.borrow_mut().fail_at = Some(3);
    assert!(control::change(&mut panel, &store, GammaPreset::High).is_err());
    assert_eq!(&spi.0.borrow().writes[4..], expected.as_slice());
}
#[test]
fn failed_runtime_change_neither_sets_nor_flushes_storage() {
    let (mut panel, store, events) = fixture(Some(1));
    panel.fail = [true, false].into();
    assert!(control::change(&mut panel, &store, GammaPreset::High).is_err());
    assert_eq!(store.cached.get(), Some(1));
    assert_eq!(store.saved.get(), Some(1));
    assert_eq!(writes(&events), 0);
}
#[test]
fn failed_rollback_reports_failure_and_preserves_saved_value() {
    let (mut panel, store, events) = fixture(Some(1));
    panel.fail = [true, true].into();
    let error = control::change(&mut panel, &store, GammaPreset::High).unwrap_err();
    assert!(format!("{error:#}").contains("injected SPI fault"));
    assert_eq!(store.saved.get(), Some(1));
    assert_eq!(writes(&events), 0);
    assert_eq!(
        events
            .borrow()
            .iter()
            .filter(|e| matches!(e, Event::Apply(_)))
            .count(),
        2
    );
}
#[test]
fn storage_write_follows_every_lcd_write_including_page_restore() {
    let (_, mut store, events) = fixture(Some(0));
    let spi = Spi::default();
    store.spi = Some(spi.clone());
    let mut panel = ili9806e::ILI9806E::new(Pin, spi.clone());
    control::change(&mut panel, &store, GammaPreset::High).unwrap();
    assert_eq!(
        *events.borrow(),
        [Event::Read, Event::Set(2, 34), Event::Flush]
    );
    assert_eq!(
        commands(&spi).last(),
        Some(&(0xFF, vec![0xFF, 0x98, 6, 4, 0]))
    );
}
#[test]
fn reinitialization_resets_high_to_original_default_curves() {
    let spi = Spi::default();
    let mut lcd = ili9806e::ILI9806E::new(Pin, spi.clone());
    lcd.set_gamma(GammaPreset::High).unwrap();
    spi.0.borrow_mut().writes.clear();
    lcd.init().unwrap();
    assert_eq!(lcd.gamma(), GammaPreset::Default);
    let cmds = commands(&spi);
    let start = cmds.iter().position(|(c, _)| *c == 0xA0).unwrap();
    assert_eq!(
        cmds[start..start + 16]
            .iter()
            .map(|(_, v)| v[0])
            .collect::<Vec<_>>(),
        P9806
    );
    assert_eq!(
        cmds[start + 16..start + 32]
            .iter()
            .map(|(_, v)| v[0])
            .collect::<Vec<_>>(),
        N9806
    );
    let spi = Spi::default();
    let mut lcd = ili9488::ILI9488::new(Pin, Pin, spi.clone());
    lcd.set_gamma(GammaPreset::High).unwrap();
    spi.0.borrow_mut().writes.clear();
    lcd.init().unwrap();
    assert_eq!(lcd.gamma(), GammaPreset::Default);
    let trace = spi.0.borrow();
    let start = trace.writes.iter().position(|v| v == &[0xE0]).unwrap();
    assert_eq!(trace.writes[start + 1], P9488);
    assert_eq!(trace.writes[start + 3], N9488);
}
#[test]
fn wake_gamma_failure_returns_error_before_display_on() {
    let spi = Spi::default();
    let mut lcd = ili9806e::ILI9806E::new(Pin, spi.clone());
    spi.0.borrow_mut().fail_at = Some(10);
    assert!(lcd.exit_sleep().is_err());
    assert!(!commands(&spi).iter().any(|(cmd, _)| *cmd == 0x29));
    let spi = Spi::default();
    let mut lcd = ili9488::ILI9488::new(Pin, Pin, spi.clone());
    spi.0.borrow_mut().fail_at = Some(2);
    assert!(lcd.exit_sleep().is_err());
    assert!(!spi.0.borrow().writes.iter().any(|v| v == &[0x29]));
}
#[test]
fn runtime_gamma_never_resets_or_changes_other_display_controls() {
    #[derive(Clone)]
    struct CountPin(Rc<Cell<usize>>);
    impl digital::ErrorType for CountPin {
        type Error = Infallible;
    }
    impl digital::OutputPin for CountPin {
        fn set_low(&mut self) -> Result<(), Self::Error> {
            self.0.set(self.0.get() + 1);
            Ok(())
        }
        fn set_high(&mut self) -> Result<(), Self::Error> {
            self.0.set(self.0.get() + 1);
            Ok(())
        }
    }
    let reset = Rc::new(Cell::new(0));
    let spi = Spi::default();
    let mut lcd = ili9806e::ILI9806E::new(CountPin(reset.clone()), spi.clone());
    for preset in [GammaPreset::Low, GammaPreset::High, GammaPreset::Default] {
        lcd.set_gamma(preset).unwrap();
    }
    assert_eq!(reset.get(), 0);
    assert!(commands(&spi).iter().all(|(cmd, _)| *cmd == 0xFF
        || (0xA0..=0xAF).contains(cmd)
        || (0xC0..=0xCF).contains(cmd)));
    let spi = Spi::default();
    let mut lcd = ili9488::ILI9488::new(CountPin(reset.clone()), Pin, spi.clone());
    for preset in [GammaPreset::Low, GammaPreset::High, GammaPreset::Default] {
        lcd.set_gamma(preset).unwrap();
    }
    assert_eq!(reset.get(), 0);
    assert_eq!(spi.0.borrow().writes.len(), 12);
    for chunk in spi.0.borrow().writes.chunks(4) {
        assert_eq!(chunk[0], [0xE0]);
        assert_eq!(chunk[2], [0xE1]);
        assert_eq!(chunk[1].len(), 15);
        assert_eq!(chunk[3].len(), 15);
    }
}
