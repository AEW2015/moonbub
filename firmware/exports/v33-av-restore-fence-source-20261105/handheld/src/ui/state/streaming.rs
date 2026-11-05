use super::{super::slint::Backend, UiState};
use slint::{ComponentHandle, TimerMode};
use std::{cell::RefCell, rc::Rc, time::Duration};
impl UiState {
    pub(super) fn setup_streaming(&mut self, state: &Rc<RefCell<UiState>>) {
        let root = self.root.unwrap();
        let backend = root.global::<Backend>();
        backend.set_stream_host(
            crate::kvs::keys::STREAM_HOST
                .get()
                .unwrap_or_default()
                .into(),
        );
        let s = state.clone();
        backend.on_stream_connect(move || {
            let r = s.borrow().root.unwrap();
            let host = r.global::<Backend>().get_stream_host().to_string();
            crate::kvs::keys::STREAM_HOST.set(&host);
            crate::kvs::keys::STREAM_HOST.flush();
            crate::streaming::connect(host);
        });
        backend.on_stream_disconnect(crate::streaming::disconnect);
        backend.on_stream_back(crate::streaming::exit_to_menu);
        let s = state.clone();
        backend.on_stream_host_next(move || {
            let root = s.borrow().root.unwrap();
            let b = root.global::<Backend>();
            if b.get_stream_host().is_empty() {
                b.set_stream_host("192.168.1.100".into());
                b.set_stream_host_octet(0);
            } else {
                b.set_stream_host_octet((b.get_stream_host_octet() + 1) % 4);
            }
        });
        let s = state.clone();
        backend.on_stream_host_adjust(move |delta| {
            let root = s.borrow().root.unwrap();
            let b = root.global::<Backend>();
            let ip = b
                .get_stream_host()
                .parse::<std::net::Ipv4Addr>()
                .unwrap_or(std::net::Ipv4Addr::new(192, 168, 1, 100));
            let mut octets = ip.octets();
            let index = b.get_stream_host_octet().clamp(0, 3) as usize;
            octets[index] = (octets[index] as i32 + delta.clamp(-1, 1)).clamp(0, 255) as u8;
            b.set_stream_host(std::net::Ipv4Addr::from(octets).to_string().into());
        });
        let s = state.clone();
        self.streaming_timer.start(TimerMode::Repeated,Duration::from_millis(500),move||{
            let root=s.borrow().root.unwrap();let b=root.global::<Backend>();let t=crate::streaming::stats();
            b.set_stream_status(if t.status.is_empty(){"TEST source only; Wi-Fi config on microSD".into()}else{t.status.into()});
            b.set_stream_diagnostics(format!("{}: RX {}fps / LCD {}fps / {}kbps\nFrames {} / decoded {} / presented {}\nDrops {} / errors {} / free {}B",t.source,t.rx_fps,t.display_fps,t.bitrate,t.received,t.decoded,t.displayed,t.dropped,t.errors,t.credits).into());
        });
    }
}
