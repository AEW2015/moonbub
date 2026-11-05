use std::cell::RefCell;
use std::rc::Rc;

use super::super::slint::Backend;
use crate::device::Device;
use crate::ui::slint::ScreenId;
use crate::ui::state::{SettingDatetime, SettingEntry, SettingType, SettingValue};
use settings::Page;
use slint::{ComponentHandle, Model, ModelNotify, ModelRc, ModelTracker, ToSharedString};
use time::OffsetDateTime;

use super::UiState;

#[path = "settings/gamma.rs"]
mod gamma;
#[path = "settings/pages.rs"]
mod settings;

pub struct SettingsState {
    model: Option<Rc<SettingsModel>>,
    page: &'static Page,
    stack: Vec<(&'static Page, usize)>,
}

impl Default for SettingsState {
    fn default() -> Self {
        Self {
            model: None,
            page: &settings::PAGE_ROOT,
            stack: Vec::new(),
        }
    }
}

impl SettingsState {
    pub(super) fn stop_probe(&self) {
        #[cfg(feature = "has_ili9806e")]
        if let Some(model) = &self.model {
            let mut probe = model.probe.get();
            if model.page.name == "LCD RGB Lab (raw codes)" {
                probe.enabled = false;
                if let Err(e) = Device::lock().restore_lcd_color_trim() {
                    log::error!("Could not restore saved LCD trims: {e}");
                }
                model.probe.set(probe);
            }
        }
    }
}

impl UiState {
    /// Set up the "Settings" screen.
    pub(super) fn setup_settings(&mut self, state: &Rc<RefCell<UiState>>, _device: &mut Device) {
        let root = self.root.unwrap();
        let backend = root.global::<Backend>();

        let state_ = state.clone();
        backend.on_settings_changed(move |i, value| {
            let mut state = state_.borrow_mut();
            let Some(model) = state.settings.model.as_ref() else {
                return;
            };

            let action = model.changed(i as usize, value);
            match action {
                SettingsAction::None => {}
                SettingsAction::Subpage(page) => {
                    let entry = (state.settings.page, i as usize);
                    state.settings.stack.push(entry);
                    state.set_settings_page(page, 0);
                }
                SettingsAction::Screen(screen_id) => {
                    let root = state.root.unwrap();
                    std::mem::drop(state);
                    root.invoke_set_screen(screen_id);

                    // Workaround for issue where the title doesn't get updated
                    // (it's updated, but it doesn't take effect until the next render)
                    crate::ui::send(crate::ui::Message::Redraw);
                }
            }
        });

        let state_ = state.clone();
        backend.on_settings_back(move || {
            let mut state = state_.borrow_mut();
            state.settings.stop_probe();
            match state.settings.stack.pop() {
                Some(previous) => {
                    state.set_settings_page(previous.0, previous.1);
                    true
                }
                None => false,
            }
        })
    }

    fn set_settings_page(&mut self, page: &'static Page, selected_item: usize) {
        #[cfg(feature = "has_ili9806e")]
        if page.name == "LCD RGB Lab (raw codes)" {
            if let Err(e) = Device::lock().lcd.set_digital_gamma_probe(Default::default()) {
                log::error!("Could not bypass saved trims for lab: {e}");
            }
        }
        log::info!("Settings page: {:?}; stack remaining minimum: {} bytes", page.name,
            unsafe { esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut()) });
        let root = self.root.unwrap();
        let backend = root.global::<Backend>();
        let model = Rc::new(SettingsModel::new(page));
        self.settings.model = Some(model.clone());
        self.settings.page = page;
        backend.set_settings(ModelRc::from(model));
        backend.set_settings_index(selected_item as i32);
        backend.set_settings_gamma_preview(
            page.entries.iter().any(|entry| matches!(entry, settings::Entry::LcdGamma { .. }))
                || page.name == "LCD RGB Lab (raw codes)",
        );

        // Should be in Slint, but there isn't a good way to do it
        let mut title = "Settings".to_shared_string();
        if !page.name.is_empty() {
            title.push_str(": ");
            title.push_str(page.name);
        }
        root.invoke_set_title(title);
    }

    pub(super) fn on_settings_enter(&mut self) {
        self.settings.stack.clear();
        self.set_settings_page(&settings::PAGE_ROOT, 0);
    }
}

pub struct SettingsModel {
    page: &'static settings::Page,
    notify: ModelNotify,
    #[cfg(feature = "has_ili9806e")]
    probe: std::cell::Cell<crate::device::drivers::ili9806e::DigitalGammaProbe>,
}

impl Model for SettingsModel {
    type Data = SettingEntry;

    fn row_count(&self) -> usize {
        self.page.entries.len()
    }

    fn row_data(&self, row: usize) -> Option<Self::Data> {
        let entry = self.page.entries.get(row)?;
        let row = match entry {
            #[cfg(feature = "has_ili9806e")]
            settings::Entry::LcdColorTrim { name, channel } => {
                let trim = crate::device::drivers::ili9806e::ColorTrim::from_stored(
                    crate::kvs::keys::LCD_COLOR_TRIM.get().unwrap_or_default());
                SettingEntry { name: (*name).into(), r#type: SettingType::List,
                    value: SettingValue { int_value: 7 + if *channel == 0 { trim.red as i32 } else { trim.blue as i32 }, ..Default::default() },
                    choices: ModelRc::new(slint::VecModel::from((-7..=7).map(|v| {
                        slint::SharedString::from(if v > 0 { format!("+{v}") } else { v.to_string() })
                    }).collect::<Vec<_>>())),
                }
            },
            #[cfg(feature = "has_ili9806e")]
            settings::Entry::ResetColorTrim => SettingEntry {
                name: "Reset color trims".into(), r#type: SettingType::Subpage, ..Default::default()
            },
            #[cfg(feature = "has_ili9806e")]
            settings::Entry::LcdDigitalProbe { name, control, choices } => {
                let probe = self.probe.get();
                SettingEntry {
                    name: (*name).into(), r#type: SettingType::List,
                    value: SettingValue { int_value: match control {
                        0 => probe.enabled as i32, 1 => probe.red as i32, 2 => probe.blue as i32, _ => probe.table as i32,
                    }, ..Default::default() },
                    choices: ModelRc::new(choices.iter().map(|s| slint::SharedString::from(*s)).collect::<slint::VecModel<_>>()),
                }
            },
            settings::Entry::LcdGamma { choices } => SettingEntry {
                name: "Gamma".into(),
                r#type: SettingType::List,
                value: SettingValue {
                    int_value: gamma::selected_value(crate::kvs::keys::LCD_GAMMA.get()),
                    ..SettingValue::default()
                },
                choices: ModelRc::new(
                    choices
                        .iter()
                        .map(|x| slint::SharedString::from(*x))
                        .collect::<slint::VecModel<_>>(),
                ),
            },
            settings::Entry::Checkbox { name, key } => SettingEntry {
                name: (*name).into(),
                r#type: SettingType::Checkbox,
                value: SettingValue {
                    bool_value: key.get().unwrap(),
                    ..SettingValue::default()
                },
                ..Default::default()
            },
            settings::Entry::List { name, key, choices } => SettingEntry {
                name: (*name).into(),
                r#type: SettingType::List,
                value: SettingValue {
                    int_value: key.get().unwrap(),
                    ..SettingValue::default()
                },
                choices: ModelRc::new(
                    choices
                        .iter()
                        .map(|x| slint::SharedString::from(*x))
                        .collect::<slint::VecModel<_>>(),
                ),
            },
            settings::Entry::SystemDatetime { name } => SettingEntry {
                name: (*name).into(),
                r#type: SettingType::Datetime,
                value: SettingValue {
                    datetime_value: {
                        let dt = OffsetDateTime::now_utc();
                        SettingDatetime {
                            year: dt.year(),
                            month: dt.month() as i32,
                            day: dt.day() as i32,
                            hour: dt.hour() as i32,
                            min: dt.minute() as i32,
                            sec: dt.second() as i32,
                        }
                    },
                    ..SettingValue::default()
                },
                ..Default::default()
            },
            settings::Entry::Subpage { name, .. } => SettingEntry {
                name: (*name).into(),
                r#type: SettingType::Subpage,
                ..Default::default()
            },
            settings::Entry::Screen { name, .. } => SettingEntry {
                name: (*name).into(),
                r#type: SettingType::Subpage,
                ..Default::default()
            },
        };
        Some(row)
    }

    fn model_tracker(&self) -> &dyn ModelTracker {
        &self.notify
    }

    fn as_any(&self) -> &dyn core::any::Any {
        // a typical implementation just return `self`
        self
    }
}

impl SettingsModel {
    fn new(page: &'static settings::Page) -> Self {
        SettingsModel {
            page,
            notify: ModelNotify::default(),
            #[cfg(feature = "has_ili9806e")]
            probe: Default::default(),
        }
    }

    /// Notify that a setting has changed. Returns whether we navigated to a new page.
    fn changed(&self, index: usize, value: SettingValue) -> SettingsAction {
        let Some(entry) = self.page.entries.get(index) else {
            log::info!("Unknown setting changed: {} -> {:?}", index, value);
            return SettingsAction::None;
        };

        match entry {
            #[cfg(feature = "has_ili9806e")]
            settings::Entry::LcdColorTrim { .. } | settings::Entry::ResetColorTrim => {
                use crate::device::drivers::ili9806e::ColorTrim;
                let mut trim = ColorTrim::from_stored(crate::kvs::keys::LCD_COLOR_TRIM.get().unwrap_or_default());
                if let settings::Entry::LcdColorTrim { channel, .. } = entry {
                    if !(0..=14).contains(&value.int_value) { return SettingsAction::None; }
                    let signed = (value.int_value - 7) as i8;
                    if *channel == 0 { trim.red = signed; } else { trim.blue = signed; }
                } else { trim = ColorTrim::default(); }
                if let Err(e) = Device::lock().set_lcd_color_trim(trim) {
                    log::error!("LCD color trim failed: {e}");
                    crate::ui::send(crate::ui::Message::Notification(
                        crate::ui::Notification::new_short("Could not apply color trims".into())));
                }
                for row in 0..self.page.entries.len() { self.notify.row_changed(row); }
            },
            #[cfg(feature = "has_ili9806e")]
            settings::Entry::LcdDigitalProbe { control, choices, .. } => {
                if value.int_value < 0 || value.int_value as usize >= choices.len() {
                    return SettingsAction::None;
                }
                let mut probe = self.probe.get();
                match control {
                    0 => probe.enabled = value.int_value != 0,
                    1 => probe.red = value.int_value as u8,
                    2 => probe.blue = value.int_value as u8,
                    _ => probe.table = value.int_value as u8,
                }
                if probe.enabled || *control == 0 {
                    if let Err(e) = Device::lock().lcd.set_digital_gamma_probe(probe) {
                        log::error!("LCD digital gamma probe failed: {e}");
                        probe.enabled = false;
                        crate::ui::send(crate::ui::Message::Notification(
                            crate::ui::Notification::new_short("LCD probe failed; disabled".into())));
                    }
                }
                self.probe.set(probe);
                self.notify.row_changed(0);
            }
            settings::Entry::LcdGamma { .. } => {
                gamma::changed(
                    value.int_value,
                    |preset| Device::lock().set_lcd_gamma(preset),
                    || {
                        crate::ui::send(crate::ui::Message::Notification(
                            crate::ui::Notification::new_short("Could not apply LCD gamma".into()),
                        ))
                    },
                );
            }
            settings::Entry::Checkbox { key, .. } => key.set(&value.bool_value),
            settings::Entry::List { key, .. } => key.set(&value.int_value),
            settings::Entry::SystemDatetime { .. } => {
                let dt = convert_settings_datetime(&value.datetime_value).unwrap();
                let dt = dt.replace_second(0).unwrap();
                let dt = dt.assume_utc();
                Device::lock().set_datetime(dt);
            }
            settings::Entry::Subpage { page, .. } => {
                return SettingsAction::Subpage(*page);
            }
            settings::Entry::Screen { screen, .. } => {
                return SettingsAction::Screen(*screen);
            }
        }
        self.notify.row_changed(index);
        SettingsAction::None
    }
}

enum SettingsAction {
    None,
    Subpage(&'static Page),
    Screen(ScreenId),
}

/// Helper function used by the UI to be able to correctly modify individual datetime components.
pub fn settings_datetime_add(source: SettingDatetime, delta: SettingDatetime) -> SettingDatetime {
    fn inner(
        source: &SettingDatetime,
        delta: SettingDatetime,
    ) -> time::Result<time::PrimitiveDateTime> {
        let mut dt = convert_settings_datetime(source)?;
        dt = dt.replace_day(1)?; // The day will be re-added later.
        dt = dt.replace_year(((dt.year() as i32) + delta.year).min(2100).max(2000))?;
        if delta.month < 0 {
            dt = dt.replace_month(dt.month().nth_prev((-delta.month) as u8))?;
        } else {
            dt = dt.replace_month(dt.month().nth_next(delta.month as u8))?;
        }
        dt = dt.replace_hour(((dt.hour() as i32) + delta.hour).rem_euclid(24) as u8)?;
        dt = dt.replace_minute(((dt.minute() as i32) + delta.min).rem_euclid(60) as u8)?;
        dt = dt.replace_second(((dt.second() as i32) + delta.sec).rem_euclid(60) as u8)?;
        let day_max = time::util::days_in_month(dt.month(), dt.year()) as i32;
        if delta.day == 0 {
            // If we aren't changing the day, clamp it to the maximum days in the month.
            dt = dt.replace_day(source.day.min(day_max) as u8)?;
        } else {
            dt = dt.replace_day((source.day + delta.day - 1).rem_euclid(day_max) as u8 + 1)?;
        }
        Ok(dt)
    }
    match inner(&source, delta) {
        Ok(dt) => SettingDatetime {
            year: dt.year(),
            month: dt.month() as i32,
            day: dt.day() as i32,
            hour: dt.hour() as i32,
            min: dt.minute() as i32,
            sec: dt.second() as i32,
        },
        Err(_) => {
            log::warn!("Invalid date");
            source
        }
    }
}

fn convert_settings_datetime(source: &SettingDatetime) -> time::Result<time::PrimitiveDateTime> {
    let date = time::Date::from_calendar_date(
        source.year,
        (source.month as u8).try_into()?,
        source.day as u8,
    )?;
    let time = time::Time::from_hms(source.hour as u8, source.min as u8, source.sec as u8)?;
    Ok(time::PrimitiveDateTime::new(date, time))
}
