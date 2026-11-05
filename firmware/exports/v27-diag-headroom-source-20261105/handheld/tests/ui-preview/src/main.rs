use slint::{ComponentHandle, PhysicalSize, Rgb8Pixel};
use slint::platform::WindowAdapter;
use slint::platform::software_renderer::{MinimalSoftwareWindow, RepaintBufferType};
use std::rc::Rc;
slint::include_modules!();
struct Platform(Rc<MinimalSoftwareWindow>);
impl slint::platform::Platform for Platform {
    fn create_window_adapter(&self) -> Result<Rc<dyn slint::platform::WindowAdapter>, slint::PlatformError> {
        Ok(self.0.clone())
    }
}
fn main() {
    let window = MinimalSoftwareWindow::new(RepaintBufferType::NewBuffer);
    slint::platform::set_platform(Box::new(Platform(window.clone()))).unwrap();
    let root = MainWindow::new().unwrap();
    root.show().unwrap();
    // Match firmware: rendering holds Device::lock(), action handlers acquire
    // that lock too. try_lock makes a regression fail instead of hanging.
    let device_lock = Rc::new(std::sync::Mutex::new(()));
    let actions = Rc::new(std::cell::Cell::new(0usize));
    root.global::<Backend>().on_settings_changed({
        let device_lock = device_lock.clone();
        let actions = actions.clone();
        move |_, _| {
            let _guard = device_lock.try_lock().expect("settings action ran while rendering held the device lock");
            actions.set(actions.get() + 1);
        }
    });
    for (width, height) in [(360, 240), (240, 160)] {
        window.set_size(PhysicalSize::new(width, height));
        let mut pixels = vec![Rgb8Pixel::default(); (width * height) as usize];
        for _ in 0..10 {
            for preview in [false, true, false] {
                root.invoke_set_screen(ScreenId::Settings);
                root.global::<Backend>().set_settings_gamma_preview(preview);
                if preview {
                    let entries = ["Correction", "Table", "Red code", "Blue code"].into_iter().enumerate().map(|(i, name)| {
                        SettingEntry {
                            name: name.into(), r#type: SettingType::List,
                            choices: slint::ModelRc::new(slint::VecModel::from(if i == 0 {
                                vec!["Off".into(), "On (test)".into()]
                            } else if i == 1 {
                                ["Micro mid", "Micro all", "Macro all", "Both all"].into_iter().map(Into::into).collect()
                            } else { (0..16).map(|n| slint::SharedString::from(n.to_string())).collect() })),
                            ..Default::default()
                        }
                    }).collect::<Vec<_>>();
                    root.global::<Backend>().set_settings(slint::ModelRc::new(slint::VecModel::from(entries)));
                }
                window.request_redraw();
                window.draw_if_needed(|renderer| { renderer.render(&mut pixels, width as usize); });
                if preview {
                    let entries = ["Gamma", "Red trim", "Blue trim", "Reset color trims", "LCD RGB Lab"]
                        .into_iter().enumerate().map(|(i, name)| SettingEntry {
                            name: name.into(),
                            r#type: if i < 3 { SettingType::List } else { SettingType::Subpage },
                            choices: slint::ModelRc::new(slint::VecModel::from(if i == 0 {
                                ["Default", "Low Gamma", "High Gamma"].into_iter().map(Into::into).collect()
                            } else if i < 3 { (-7..=7).map(|n| slint::SharedString::from(n.to_string())).collect() }
                            else { Vec::new() })),
                            value: SettingValue { int_value: if i == 1 || i == 2 { 7 } else { 0 }, ..Default::default() },
                        }).collect::<Vec<_>>();
                    root.global::<Backend>().set_settings(slint::ModelRc::new(slint::VecModel::from(entries)));
                    window.request_redraw();
                    window.draw_if_needed(|renderer| { renderer.render(&mut pixels, width as usize); });
                    for index in [3, 3, 4, 4] {
                        root.global::<Backend>().set_settings_index(index);
                        window.request_redraw();
                        window.draw_if_needed(|renderer| {
                            let _guard = device_lock.lock().unwrap();
                            renderer.render(&mut pixels, width as usize);
                        });
                        let before = actions.get();
                        window.dispatch_event(slint::platform::WindowEvent::KeyPressed { text: "a".into() });
                        window.dispatch_event(slint::platform::WindowEvent::KeyReleased { text: "a".into() });
                        window.request_redraw();
                        window.draw_if_needed(|renderer| {
                            let _guard = device_lock.lock().unwrap();
                            renderer.render(&mut pixels, width as usize);
                        });
                        assert_eq!(actions.get(), before + 1, "action must fire exactly once");
                    }
                    root.global::<Backend>().set_settings_index(1);
                    window.dispatch_event(slint::platform::WindowEvent::KeyPressed { text: "a".into() });
                    window.dispatch_event(slint::platform::WindowEvent::KeyReleased { text: "a".into() });
                    window.request_redraw();
                    window.draw_if_needed(|renderer| {
                        let _guard = device_lock.lock().unwrap();
                        renderer.render(&mut pixels, width as usize);
                    });
                    let before = actions.get();
                    let right: slint::SharedString = slint::platform::Key::RightArrow.into();
                    window.dispatch_event(slint::platform::WindowEvent::KeyPressed { text: right.clone() });
                    window.dispatch_event(slint::platform::WindowEvent::KeyReleased { text: right });
                    assert_eq!(actions.get(), before + 1, "trim editor must remain usable after actions");
                    window.dispatch_event(slint::platform::WindowEvent::KeyPressed { text: "b".into() });
                    window.dispatch_event(slint::platform::WindowEvent::KeyReleased { text: "b".into() });
                }
                root.invoke_set_screen(ScreenId::MainMenu);
                window.request_redraw();
                window.draw_if_needed(|renderer| { renderer.render(&mut pixels, width as usize); });
            }
        }
    }
    test_value_refresh(&root, &window);
    println!("PASS: Settings actions, trim editing, model refresh after reset, and rejected changes");
}

fn test_value_refresh(root: &MainWindow, window: &Rc<MinimalSoftwareWindow>) {
    use slint::{Model, ModelRc, VecModel};
    window.set_size(PhysicalSize::new(360, 240));
    let entries = ["Gamma", "Red trim", "Blue trim", "Reset color trims"].into_iter().enumerate().map(|(i, name)| SettingEntry {
        name: name.into(), r#type: if i == 3 { SettingType::Subpage } else { SettingType::List },
        choices: ModelRc::new(VecModel::from(if i == 0 {
            ["Default", "Low Gamma", "High Gamma"].into_iter().map(slint::SharedString::from).collect::<Vec<_>>()
        } else { (-7..=7).map(|n| slint::SharedString::from(n.to_string())).collect::<Vec<_>>() })),
        value: SettingValue { int_value: if i == 0 { 2 } else { 7 }, ..Default::default() },
    }).collect::<Vec<_>>();
    let model = Rc::new(VecModel::from(entries));
    let requests = Rc::new(std::cell::RefCell::new(Vec::new()));
    let reject = Rc::new(std::cell::Cell::new(false));
    root.global::<Backend>().on_settings_changed({
        let model = model.clone(); let requests = requests.clone(); let reject = reject.clone();
        move |row, value| {
            requests.borrow_mut().push((row, value.int_value));
            if reject.get() { return; }
            if row == 3 {
                for i in [1, 2] {
                    let mut entry = model.row_data(i).unwrap(); entry.value.int_value = 7;
                    model.set_row_data(i, entry);
                }
            } else if (0..3).contains(&row) {
                let mut entry = model.row_data(row as usize).unwrap(); entry.value = value;
                model.set_row_data(row as usize, entry);
            }
        }
    });
    root.invoke_set_screen(ScreenId::Settings);
    root.global::<Backend>().set_settings(model.clone().into());
    root.global::<Backend>().set_settings_gamma_preview(true);
    root.global::<Backend>().set_settings_index(1);
    let render = || {
        let mut pixels = vec![Rgb8Pixel::default(); 360 * 240];
        window.request_redraw();
        window.draw_if_needed(|r| { r.render(&mut pixels, 360); });
        pixels.into_iter().flat_map(|p| [p.r, p.g, p.b]).collect::<Vec<_>>()
    };
    let key = |text: slint::SharedString| {
        window.dispatch_event(slint::platform::WindowEvent::KeyPressed { text: text.clone() });
        window.dispatch_event(slint::platform::WindowEvent::KeyReleased { text });
    };
    let neutral = render();
    key("a".into()); render();
    key(slint::platform::Key::RightArrow.into()); render();
    assert_eq!(requests.borrow().as_slice(), &[(1, 8)], "choice index must not replace the settings row index");
    key("b".into());
    assert_ne!(render(), neutral, "accepted trim edit must update the visible label");
    root.global::<Backend>().set_settings_index(2); render();
    key("a".into()); render();
    key(slint::platform::Key::LeftArrow.into()); render();
    assert_eq!(requests.borrow().last(), Some(&(2, 6)), "blue edit must reach its own row");
    key("b".into()); render();
    root.global::<Backend>().set_settings_index(3); render();
    key("a".into()); render();
    root.global::<Backend>().set_settings_index(1);
    assert_eq!(model.row_data(0).unwrap().value.int_value, 2, "color reset must preserve gamma");
    assert_eq!(model.row_data(1).unwrap().value.int_value, 7);
    assert_eq!(model.row_data(2).unwrap().value.int_value, 7);
    assert!(render() == neutral, "reset must visibly restore neutral labels without reopening Settings");
    reject.set(true);
    key("a".into()); let before_rejected = render();
    key(slint::platform::Key::RightArrow.into());
    assert!(render() == before_rejected, "rejected hardware changes must not change the visible selection");
    key(slint::platform::Key::RightArrow.into()); render();
    assert_eq!(requests.borrow().last(), Some(&(1, 8)), "next edit must use confirmed model value");
    let attaches = Rc::new(std::cell::Cell::new(0));
    root.global::<Backend>().on_main_menu_attach_native({
        let attaches = attaches.clone();
        move || attaches.set(attaches.get() + 1)
    });
    root.invoke_set_screen(ScreenId::MainMenu); render();
    key(slint::platform::Key::DownArrow.into()); render();
    key(slint::platform::Key::DownArrow.into()); render();
    key("a".into()); render();
    assert_eq!(attaches.get(), 1, "Attach must be reachable with D-pad and A");
    let pauses = Rc::new(std::cell::RefCell::new(Vec::new()));
    root.global::<Backend>().on_game_set_paused({
        let pauses = pauses.clone(); move |p| pauses.borrow_mut().push(p)
    });
    let resets = Rc::new(std::cell::Cell::new(0));
    root.global::<Backend>().on_game_reset({ let resets=resets.clone(); move || resets.set(resets.get()+1) });
    root.invoke_set_screen(ScreenId::Game); render();
    key("Home".into()); render();
    key("a".into()); render();
    assert_eq!(pauses.borrow().as_slice(), &[true,false], "Home and Resume must restore app input");
    key("Home".into()); render();
    key(slint::platform::Key::DownArrow.into()); render();
    key("a".into()); render();
    assert_eq!(resets.get(), 1);
    assert_eq!(pauses.borrow().last(), Some(&false));
    key("Power".into()); render();
    assert_eq!(pauses.borrow().last(), Some(&true));
    key("a".into()); render(); // Close power popup (initial focus).
    key("a".into()); render(); // Resume the game pause menu beneath it.
    assert_eq!(pauses.borrow().last(), Some(&false));
    println!("NATIVE_ATTACH_UI_PASS attach home resume reset power_close_resume");
}
