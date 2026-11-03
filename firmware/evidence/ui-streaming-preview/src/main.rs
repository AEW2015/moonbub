use slint::{ComponentHandle, PhysicalSize,WindowSize};
use slint::platform::WindowAdapter;
use slint::platform::software_renderer::{LineBufferProvider,RepaintBufferType};
use std::{cell::{Cell, RefCell},rc::Rc,ops::Range};
#[path="../../../handheld/src/ui/slint.rs"]
mod firmware_slint;
use firmware_slint::{MainWindow,Backend,ScreenId,Argb1555,HandheldPlatform,MinimalSoftwareWindow};
struct LineModel{line:Vec<Argb1555>,overlay:Vec<Argb1555>}
thread_local!{static BUFFER:RefCell<LineModel>=RefCell::new(LineModel{line:vec![Argb1555::default();360],overlay:vec![Argb1555::default();360*240]});}
impl LineBufferProvider for &mut LineModel{
    type TargetPixel=Argb1555;
    fn process_line(&mut self,line:usize,range:Range<usize>,render_fn:impl FnOnce(&mut[Self::TargetPixel])){
        let chunk=&mut self.line[range.clone()];render_fn(chunk);
        self.overlay[line*360+range.start..line*360+range.end].copy_from_slice(chunk);
    }
}
fn opaque_count()->usize{BUFFER.with(|b|b.borrow().overlay.iter().filter(|p|p.as_u16()&0x8000!=0).count())}
fn render(root:&MainWindow,window:&Rc<MinimalSoftwareWindow>,lock:&std::sync::Mutex<()>,name:&str)->Vec<u8>{
    slint::platform::update_timers_and_animations();
    window.request_redraw();
    window.draw_if_needed(|renderer|{let _device=lock.lock().unwrap();BUFFER.with(|b|renderer.render_by_line(&mut *b.borrow_mut()));});
    assert_eq!(window.size(),PhysicalSize::new(360,240),"production screen changed requested hardware dimensions");
    let bytes=BUFFER.with(|b|b.borrow().overlay.iter().flat_map(|p|if p.as_u16()&0x8000!=0{[p.red(),p.green(),p.blue()]}else{[0,0,0]}).collect::<Vec<_>>());
    let mut ppm=b"P6\n360 240\n255\n".to_vec();ppm.extend(&bytes);
    std::fs::write(format!("{name}.ppm"),ppm).unwrap();
    let _=root;
    bytes
}
fn key(window:&Rc<MinimalSoftwareWindow>,text:slint::SharedString){
    window.dispatch_event(slint::platform::WindowEvent::KeyPressed{text:text.clone()});
    window.dispatch_event(slint::platform::WindowEvent::KeyReleased{text});
}
fn main(){
    let window=MinimalSoftwareWindow::new(RepaintBufferType::ReusedBuffer);
    slint::platform::set_platform(Box::new(HandheldPlatform{window:window.clone()})).unwrap();
    window.set_size(WindowSize::Physical(PhysicalSize::new(360,240)));
    let root=MainWindow::new().unwrap();root.show().unwrap();
    let lock=Rc::new(std::sync::Mutex::new(()));
    let connects=Rc::new(Cell::new(0));let disconnects=Rc::new(Cell::new(0));let backs=Rc::new(Cell::new(0));
    let host_next=Rc::new(Cell::new(0));let host_adjust=Rc::new(Cell::new(0));let exits=Rc::new(Cell::new(0));
    let screen=Rc::new(RefCell::new(Vec::new()));let pauses=Rc::new(RefCell::new(Vec::new()));
    let b=root.global::<Backend>();
    b.on_screen_enter({let screen=screen.clone();move |id|screen.borrow_mut().push(id)});
    b.on_stream_connect({let n=connects.clone();let lock=lock.clone();move||{let _g=lock.try_lock().expect("connect during render");n.set(n.get()+1)}});
    b.on_stream_disconnect({let n=disconnects.clone();let lock=lock.clone();move||{let _g=lock.try_lock().expect("disconnect during render");n.set(n.get()+1)}});
    b.on_stream_back({let n=backs.clone();let root=root.as_weak();let lock=lock.clone();move||{let _g=lock.try_lock().expect("back during render");n.set(n.get()+1);root.unwrap().invoke_set_screen(ScreenId::MainMenu)}});
    b.on_game_exit({let n=exits.clone();let root=root.as_weak();let lock=lock.clone();move||{let _g=lock.try_lock().expect("exit during render");n.set(n.get()+1);root.unwrap().invoke_set_screen(ScreenId::MainMenu)}});
    b.on_game_set_paused({let pauses=pauses.clone();move|p|pauses.borrow_mut().push(p)});
    b.on_stream_host_next({let n=host_next.clone();let root=root.as_weak();let lock=lock.clone();move||{
        let _g=lock.try_lock().expect("host-next during render");n.set(n.get()+1);let root=root.unwrap();let b=root.global::<Backend>();
        if b.get_stream_host().is_empty(){b.set_stream_host("192.168.1.100".into());b.set_stream_host_octet(0)}else{b.set_stream_host_octet((b.get_stream_host_octet()+1)%4)}
    }});
    b.on_stream_host_adjust({let n=host_adjust.clone();let root=root.as_weak();let lock=lock.clone();move|delta|{
        let _g=lock.try_lock().expect("host-adjust during render");n.set(n.get()+1);let root=root.unwrap();let b=root.global::<Backend>();
        let mut octets=b.get_stream_host().parse::<std::net::Ipv4Addr>().unwrap().octets();
        let i=b.get_stream_host_octet()as usize;octets[i]=(octets[i]as i32+delta).clamp(0,255)as u8;
        b.set_stream_host(std::net::Ipv4Addr::from(octets).to_string().into());
    }});
    b.set_hardware_version("4.1".into());b.set_battery_level(85);b.set_rom_select_is_loading(false);
    b.set_stream_status("MOCK preview: UDP5533 / MJPEG; no audio".into());
    b.set_stream_diagnostics("RX 30fps / LCD 30fps / 12000kbps\nFrames 900 / decoded 900 / presented 900\nDrops 2 / errors 2 / free 262144B".into());
    root.invoke_set_screen(ScreenId::MainMenu);render(&root,&window,&lock,"main-menu");
    // Reach Streaming through the real production main-menu controls.
    key(&window,slint::platform::Key::DownArrow.into());render(&root,&window,&lock,"main-settings-focus");
    key(&window,slint::platform::Key::DownArrow.into());render(&root,&window,&lock,"main-native-focus");
    key(&window,slint::platform::Key::RightArrow.into());render(&root,&window,&lock,"main-streaming-focus");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-default");
    assert_eq!(screen.borrow().last(),Some(&ScreenId::Streaming));
    assert_eq!((connects.get(),disconnects.get(),backs.get()),(0,0,0),"render must never activate actions");
    key(&window,slint::platform::Key::UpArrow.into());render(&root,&window,&lock,"streaming-host-focused");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-host-edit");
    key(&window,slint::platform::Key::RightArrow.into());render(&root,&window,&lock,"streaming-host-right");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-host-next");
    key(&window,slint::platform::Key::LeftArrow.into());render(&root,&window,&lock,"streaming-host-final");
    assert_eq!(b.get_stream_host().as_str(),"193.167.1.100");assert_eq!((host_next.get(),host_adjust.get()),(2,2));
    key(&window,slint::platform::Key::DownArrow.into());render(&root,&window,&lock,"streaming-connect-focus");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-connected");assert_eq!(connects.get(),1);
    key(&window,slint::platform::Key::DownArrow.into());let view=render(&root,&window,&lock,"streaming-view-focus");
    assert!(opaque_count()>50_000,"streaming menu should own opaque overlay pixels");
    key(&window,"a".into());let game=render(&root,&window,&lock,"streaming-game-view");
    assert_eq!(opaque_count(),0,"View must clear all previously opaque physical overlay pixels using the production ARGB1555 line renderer");
    assert_eq!(screen.borrow().last(),Some(&ScreenId::Game));assert_ne!(view,game,"View must hide the menu");
    assert!(game.chunks_exact(3).filter(|p|*p!=[0,0,0]).count()<100,"unpaused Game must render transparent UI");
    key(&window,"Home".into());render(&root,&window,&lock,"streaming-game-pause");assert_eq!(pauses.borrow().last(),Some(&true));
    key(&window,slint::platform::Key::DownArrow.into());render(&root,&window,&lock,"streaming-game-reset-focus");
    key(&window,slint::platform::Key::DownArrow.into());render(&root,&window,&lock,"streaming-game-exit-focus");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-exited");assert_eq!(exits.get(),1);assert_eq!(screen.borrow().last(),Some(&ScreenId::MainMenu));
    root.invoke_set_screen(ScreenId::Streaming);render(&root,&window,&lock,"streaming-reentered");
    key(&window,slint::platform::Key::RightArrow.into());render(&root,&window,&lock,"streaming-disconnect-focus");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-disconnected");assert_eq!(disconnects.get(),1);
    key(&window,slint::platform::Key::RightArrow.into());render(&root,&window,&lock,"streaming-back-focus");
    key(&window,"a".into());render(&root,&window,&lock,"streaming-back");assert_eq!(backs.get(),1);
    println!("STREAMING_UI_PASS 360x240 mainmenu_host_octets_connect_view_home_exit_disconnect_back callbacks_outside_render_lock persistent_production_argb1555_overlay_clears");
}
