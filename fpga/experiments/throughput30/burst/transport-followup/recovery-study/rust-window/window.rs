//! Isolated allocation-free MSV1 reorder prototype. NOT production firmware.
//!
//! `crate::protocol` must be the unmodified Moonbub Rust protocol module.
//! Time is caller-supplied monotonic microseconds. Session labels are local
//! coordination only: unauthenticated MSV1 packets contain no session ID.
use crate::protocol::{Header, Receiver, HEADER, CHUNK};

pub const WINDOW_SLOTS: usize = 4;
pub const PACKET_BYTES: usize = HEADER + CHUNK;
pub const GAP_TIMEOUT_US: u64 = 2_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    WrongSession, ClockRegression, Poisoned, InvalidPacket, StaleFrame,
    MismatchedFrame, Duplicate, WindowOverflow, PreSlotFull, Receiver, Sink,
}

/// Called only after the actual receiver accepts a packet. The sink is
/// responsible for translating SOF/payload/done into its own transaction.
/// Failures invalidate this session; `abort` must discard partially sent data.
pub trait Sink {
    fn packet(&mut self, header: Header, payload: &[u8], done: bool) -> Result<(), ()>;
    fn abort(&mut self) -> Result<(), ()>;
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Outcome {
    pub forwarded: u8,
    pub completed: bool,
    pub gap_expired: bool,
    pub presof_expired: bool,
}

#[derive(Clone, Copy)]
struct Slot { bytes: [u8; PACKET_BYTES], len: usize, since_us: u64 }
impl Slot {
    const fn empty() -> Self { Self { bytes: [0; PACKET_BYTES], len: 0, since_us: 0 } }
    fn clear(&mut self) { self.len = 0; self.since_us = 0; }
    fn header(&self) -> Option<Header> { if self.len == 0 { None } else { Header::parse(&self.bytes[..self.len]).ok() } }
    fn fill(&mut self, packet: &[u8], now_us: u64) {
        self.bytes[..packet.len()].copy_from_slice(packet); self.len = packet.len(); self.since_us = now_us;
    }
}

/// 4 post-SOF slots and 1 pre-SOF slot. `size_of::<Window>()` includes the
/// actual fixed storage; allocate appropriately for the embedded environment.
pub struct Window {
    receiver: Receiver,
    slots: [Slot; WINDOW_SLOTS],
    pre: Slot,
    session: u32,
    active: Option<Header>,
    expected: u32,
    last_id: Option<u32>,
    last_us: Option<u64>,
    poisoned: bool,
}

impl Window {
    pub fn new(session: u32) -> Self {
        Self { receiver: Receiver::default(), slots: [Slot::empty(); WINDOW_SLOTS],
               pre: Slot::empty(), session, active: None, expected: 0, last_id: None,
               last_us: None, poisoned: false }
    }

    /// Start a new locally labeled session after the sink has confirmed abort.
    /// MSV1 itself cannot authenticate or distinguish packets from old sessions.
    pub fn start_session<S: Sink>(&mut self, session: u32, sink: &mut S) -> Result<(), Error> {
        if (self.active.is_some() || self.poisoned) && sink.abort().is_err() {
            self.poisoned = true; return Err(Error::Sink);
        }
        self.receiver = Receiver::default(); self.clear_slots(); self.pre.clear();
        self.session = session; self.active = None; self.expected = 0; self.last_id = None;
        self.last_us = None; self.poisoned = false; Ok(())
    }

    fn check_clock(&mut self, session: u32, now_us: u64) -> Result<(), Error> {
        if self.poisoned { return Err(Error::Poisoned); }
        if session != self.session { return Err(Error::WrongSession); }
        if self.last_us.is_some_and(|t| now_us < t) { return Err(Error::ClockRegression); }
        self.last_us = Some(now_us); Ok(())
    }
    fn clear_slots(&mut self) { for s in &mut self.slots { s.clear(); } }
    fn same_frame(a: Header, b: Header) -> bool {
        a.id == b.id && a.length == b.length && a.crc == b.crc && a.capture_us == b.capture_us
    }
    fn newer(&self, id: u32) -> bool {
        self.last_id.map_or(true, |old| (id.wrapping_sub(old) as i32) > 0)
    }
    fn abort_active<S: Sink>(&mut self, sink: &mut S, force: bool) -> Result<(), Error> {
        let had = self.active.is_some() || force;
        self.receiver.abort(); self.active = None; self.expected = 0; self.clear_slots();
        if had && sink.abort().is_err() { self.poisoned = true; return Err(Error::Sink); }
        Ok(())
    }
    fn accept_one<S: Sink>(receiver: &mut Receiver, packet: &[u8], sink: &mut S) -> Result<(Header,bool),Error> {
        let (h,done)=receiver.accept(packet).map_err(|_|Error::Receiver)?;
        sink.packet(h, &packet[HEADER..], done).map_err(|_|Error::Sink)?;
        Ok((h,done))
    }
    fn accepted(&mut self, h: Header, done: bool, out: &mut Outcome) {
        if h.offset == 0 { self.last_id=Some(h.id); self.active=Some(h); }
        self.expected=h.offset+u32::from(h.count); out.forwarded=out.forwarded.saturating_add(1);
        if done { self.active=None; self.expected=0; self.clear_slots(); out.completed=true; }
    }
    fn deliver<S: Sink>(&mut self, packet: &[u8], sink: &mut S, out: &mut Outcome) -> Result<(), Error> {
        match Self::accept_one(&mut self.receiver,packet,sink) {
            Ok((h,done)) => { self.accepted(h,done,out); Ok(()) }
            Err(e) => { self.abort_active(sink, true)?; if e==Error::Sink { self.poisoned=true; } Err(e) }
        }
    }
    fn drain<S: Sink>(&mut self, sink: &mut S, out: &mut Outcome) -> Result<(),Error> {
        while self.active.is_some() {
            let index=self.slots.iter().position(|s| s.header().is_some_and(|h|h.offset==self.expected));
            let Some(index)=index else { break; };
            let res={ let s=&self.slots[index]; Self::accept_one(&mut self.receiver,&s.bytes[..s.len],sink) };
            self.slots[index].clear();
            match res {
                Ok((h,done)) => self.accepted(h,done,out),
                Err(e) => { self.abort_active(sink,true)?; if e==Error::Sink {self.poisoned=true;} return Err(e); }
            }
        }
        Ok(())
    }
    fn stage_active<S: Sink>(&mut self, h: Header, packet: &[u8], now_us: u64, sink: &mut S, out: &mut Outcome) -> Result<(),Error> {
        if h.offset < self.expected { self.abort_active(sink,false)?; return Err(Error::Duplicate); }
        // Reject overlapping stored ranges before forwarding; duplicate starts
        // alone do not catch partially overlapping variable-size datagrams.
        let end=h.offset+u32::from(h.count);
        if self.slots.iter().filter_map(|s|s.header()).any(|a| {
            let other_end=a.offset+u32::from(a.count);
            h.offset < other_end && a.offset < end
        }) { self.abort_active(sink,false)?; return Err(Error::Duplicate); }
        if h.offset == self.expected { self.deliver(packet,sink,out)?; return self.drain(sink,out); }
        if h.offset-self.expected > (WINDOW_SLOTS*CHUNK) as u32 {
            self.abort_active(sink,false)?; return Err(Error::WindowOverflow);
        }
        if self.slots.iter().any(|s|s.header().is_some_and(|a|a.offset==h.offset)) {
            self.abort_active(sink,false)?; return Err(Error::Duplicate);
        }
        if let Some(slot)=self.slots.iter_mut().find(|s|s.len==0) { slot.fill(packet,now_us); Ok(()) }
        else { self.abort_active(sink,false)?; Err(Error::WindowOverflow) }
    }

    /// Expire on `>= 2000` microseconds from first observed gap/pre-SOF packet.
    /// Must be called even with no network traffic to enforce the deadline.
    pub fn tick<S: Sink>(&mut self, session: u32, now_us: u64, sink: &mut S) -> Result<Outcome,Error> {
        self.check_clock(session,now_us)?;
        let mut out=Outcome::default();
        if self.pre.len!=0 && now_us-self.pre.since_us>=GAP_TIMEOUT_US { self.pre.clear();out.presof_expired=true; }
        let oldest=self.slots.iter().filter(|s|s.len!=0).map(|s|s.since_us).min();
        if oldest.is_some_and(|t|now_us-t>=GAP_TIMEOUT_US) { self.abort_active(sink,false)?;out.gap_expired=true; }
        Ok(out)
    }

    pub fn ingest<S: Sink>(&mut self, session: u32, now_us: u64, packet: &[u8], sink: &mut S) -> Result<Outcome,Error> {
        let mut out=self.tick(session,now_us,sink)?;
        let h=match Header::parse(packet) { Ok(h)=>h, Err(_)=>{self.abort_active(sink,false)?;self.pre.clear();return Err(Error::InvalidPacket);} };
        if h.flags & 1 != 0 {
            if !self.newer(h.id) { return Err(Error::StaleFrame); }
            self.abort_active(sink,false)?;
            // Keep a matching pre-SOF packet only; fields must match exactly.
            if self.pre.header().is_some_and(|p| !Self::same_frame(p,h)) { self.pre.clear(); }
            self.deliver(packet,sink,&mut out)?;
            if self.pre.len!=0 && self.active.is_some() {
                let ph=self.pre.header().ok_or(Error::InvalidPacket)?;
                if ph.offset==self.expected {
                    let res={let pre=&self.pre; Self::accept_one(&mut self.receiver,&pre.bytes[..pre.len],sink)};
                    self.pre.clear();
                    match res { Ok((h,done))=>self.accepted(h,done,&mut out), Err(e)=>{self.abort_active(sink,true)?;if e==Error::Sink{self.poisoned=true;}return Err(e);} }
                    self.drain(sink,&mut out)?;
                } else if ph.offset>self.expected && ph.offset-self.expected<=(WINDOW_SLOTS*CHUNK) as u32 {
                    // Preserve the original pre-SOF arrival time as the gap age.
                    let pre=&self.pre; let slot=&mut self.slots[0];
                    slot.bytes[..pre.len].copy_from_slice(&pre.bytes[..pre.len]);
                    slot.len=pre.len;slot.since_us=pre.since_us;self.pre.clear();
                } else {
                    self.pre.clear();self.abort_active(sink,false)?;return Err(Error::WindowOverflow);
                }
            } else if self.pre.len!=0 { self.pre.clear(); }
            return Ok(out);
        }
        if let Some(active)=self.active {
            if Self::same_frame(active,h) { self.stage_active(h,packet,now_us,sink,&mut out)?;return Ok(out); }
            if h.id==active.id { self.abort_active(sink,false)?;return Err(Error::MismatchedFrame); }
        }
        if !self.newer(h.id) { return Err(Error::StaleFrame); }
        if h.offset > (WINDOW_SLOTS*CHUNK) as u32 { return Err(Error::WindowOverflow); }
        if self.pre.len!=0 { return Err(if self.pre.header().is_some_and(|p|p.id==h.id&&p.offset==h.offset) {Error::Duplicate} else {Error::PreSlotFull}); }
        self.pre.fill(packet,now_us);Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::vec::Vec;
    use crate::protocol::crc_update;

    #[derive(Default)]
    struct TestSink { data:Vec<u8>, offsets:Vec<u32>, done:u32, aborted:u32, fail_packet:bool, fail_abort:bool }
    impl Sink for TestSink {
        fn packet(&mut self,h:Header,payload:&[u8],done:bool)->Result<(),()> {
            if self.fail_packet { return Err(()); }
            self.offsets.push(h.offset);self.data.extend_from_slice(payload);self.done+=u32::from(done);Ok(())
        }
        fn abort(&mut self)->Result<(),()> {self.aborted+=1;if self.fail_abort{Err(())}else{Ok(())}}
    }
    fn make_frame(id:u32,len:usize,chunk:usize)->(Vec<u8>,Vec<Vec<u8>>) {
        let data:Vec<u8>=(0..len).map(|i|(i.wrapping_mul(37)%251) as u8).collect();
        let crc=!crc_update(!0,&data);let mut packets=Vec::new();
        for off in (0..len).step_by(chunk) {
            let n=core::cmp::min(chunk,len-off);let mut p=std::vec![0u8;HEADER+n];
            p[..4].copy_from_slice(b"MSV1");p[4]=1;p[5]=1;
            let flags=(if off==0{1u16}else{0})|(if off+n==len{2u16}else{0});
            p[6..8].copy_from_slice(&flags.to_be_bytes());p[8..12].copy_from_slice(&id.to_be_bytes());
            p[12..14].copy_from_slice(&720u16.to_be_bytes());p[14..16].copy_from_slice(&480u16.to_be_bytes());
            p[16..20].copy_from_slice(&(len as u32).to_be_bytes());p[20..24].copy_from_slice(&(off as u32).to_be_bytes());
            p[24..26].copy_from_slice(&(n as u16).to_be_bytes());p[28..32].copy_from_slice(&crc.to_be_bytes());
            p[32..40].copy_from_slice(&987u64.to_be_bytes());p[HEADER..].copy_from_slice(&data[off..off+n]);packets.push(p);
        }
        (data,packets)
    }
    #[test] fn in_order_actual_receiver() {
        let (src,p)=make_frame(1,3500,1000);let mut w=Window::new(7);let mut sink=TestSink::default();
        for (i,packet) in p.iter().enumerate(){let o=w.ingest(7,i as u64,packet,&mut sink).unwrap();assert_eq!(o.completed,i+1==p.len());}
        assert_eq!(sink.data,src);assert_eq!(sink.offsets,[0,1000,2000,3000]);assert_eq!(sink.done,1);assert_eq!(sink.aborted,0);
    }
    #[test] fn adjacent_and_multiple_reorders_drain_in_order() {
        let (src,p)=make_frame(3,4200,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        for (at,index) in [0,3,2,1,4].iter().enumerate(){w.ingest(1,at as u64,&p[*index],&mut s).unwrap();}
        assert_eq!(s.data,src);assert_eq!(s.offsets,[0,1000,2000,3000,4000]);assert_eq!(s.done,1);
    }
    #[test] fn presof_immediate_successor_and_higher_offset() {
        for index in [1usize,2] {
            let (src,p)=make_frame(4,3500,1000);let mut w=Window::new(1);let mut s=TestSink::default();
            w.ingest(1,0,&p[index],&mut s).unwrap();w.ingest(1,1,&p[0],&mut s).unwrap();
            if index==1 {w.ingest(1,2,&p[2],&mut s).unwrap();} else {w.ingest(1,2,&p[1],&mut s).unwrap();}
            w.ingest(1,3,&p[3],&mut s).unwrap();assert_eq!(s.data,src);assert_eq!(s.done,1);
        }
    }
    #[test] fn gap_timeout_is_exact_and_requires_poll_without_traffic() {
        let (_,p)=make_frame(1,3000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,10,&p[0],&mut s).unwrap();w.ingest(1,20,&p[2],&mut s).unwrap();
        assert!(!w.tick(1,2019,&mut s).unwrap().gap_expired);assert_eq!(s.aborted,0);
        assert!(w.tick(1,2020,&mut s).unwrap().gap_expired);assert_eq!(s.aborted,1);
        assert_eq!(w.ingest(1,2021,&p[1],&mut s),Err(Error::StaleFrame));
    }
    #[test] fn presof_expiration_drops_without_aborting_sink() {
        let (_,p)=make_frame(1,2000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,100,&p[1],&mut s).unwrap();assert!(!w.tick(1,2099,&mut s).unwrap().presof_expired);
        assert!(w.tick(1,2100,&mut s).unwrap().presof_expired);assert_eq!(s.aborted,0);
        let o=w.ingest(1,2101,&p[0],&mut s).unwrap();assert_eq!(o.forwarded,1);assert!(!o.completed);
    }
    #[test] fn duplicate_and_out_of_window_abort_without_commit() {
        let (_,p)=make_frame(1,8000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,1,&p[0],&mut s).unwrap();w.ingest(1,2,&p[2],&mut s).unwrap();
        assert_eq!(w.ingest(1,3,&p[2],&mut s),Err(Error::Duplicate));assert_eq!(s.aborted,1);assert_eq!(s.done,0);
        w.start_session(2,&mut s).unwrap();w.ingest(2,4,&p[0],&mut s).unwrap();
        assert_eq!(w.ingest(2,5,&p[7],&mut s),Err(Error::WindowOverflow));assert_eq!(s.aborted,2);
    }
    #[test] fn partially_overlapping_buffered_ranges_abort() {
        let (_,p)=make_frame(1,3500,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,0,&p[0],&mut s).unwrap();w.ingest(1,1,&p[2],&mut s).unwrap();
        let mut overlap=p[1].clone();overlap[20..24].copy_from_slice(&1500u32.to_be_bytes());
        assert_eq!(w.ingest(1,2,&overlap,&mut s),Err(Error::Duplicate));assert_eq!(s.aborted,1);assert_eq!(s.done,0);
    }
    #[test] fn hard_four_slots_abort_on_fifth_held_datagram() {
        let (_,p)=make_frame(1,2048,256);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,0,&p[0],&mut s).unwrap();for i in 2..6 {w.ingest(1,i as u64,&p[i],&mut s).unwrap();}
        assert_eq!(w.ingest(1,6,&p[6],&mut s),Err(Error::WindowOverflow));assert_eq!(s.aborted,1);
    }
    #[test] fn identities_stale_sequence_and_wrap() {
        let (_,a)=make_frame(u32::MAX,2000,1000);let (_,b)=make_frame(0,2000,1000);
        let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,0,&a[0],&mut s).unwrap();w.ingest(1,1,&a[1],&mut s).unwrap();
        w.ingest(1,2,&b[0],&mut s).unwrap();assert_eq!(w.ingest(1,3,&a[0],&mut s),Err(Error::StaleFrame));
        assert_eq!(s.aborted,0);w.ingest(1,4,&b[1],&mut s).unwrap();assert_eq!(s.done,2);
    }
    #[test] fn session_and_clock_regressions_do_not_mutate_active_frame() {
        let (src,p)=make_frame(3,2000,1000);let mut w=Window::new(77);let mut s=TestSink::default();
        w.ingest(77,100,&p[0],&mut s).unwrap();assert_eq!(w.ingest(78,101,&p[1],&mut s),Err(Error::WrongSession));
        assert_eq!(w.ingest(77,99,&p[1],&mut s),Err(Error::ClockRegression));
        w.ingest(77,101,&p[1],&mut s).unwrap();assert_eq!(s.data,src);assert_eq!(s.aborted,0);
    }
    #[test] fn invalid_metadata_aborts_and_receiver_crc_gates_commit() {
        let (_,mut p)=make_frame(1,2000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,0,&p[0],&mut s).unwrap();p[1][28]^=1;
        assert_eq!(w.ingest(1,1,&p[1],&mut s),Err(Error::MismatchedFrame));assert_eq!(s.aborted,1);
        let (_,mut p)=make_frame(2,2000,1000);w.ingest(1,2,&p[0],&mut s).unwrap();p[1][HEADER]^=1;
        assert_eq!(w.ingest(1,3,&p[1],&mut s),Err(Error::Receiver));assert_eq!(s.done,0);assert_eq!(s.aborted,2);
    }
    #[test] fn local_session_reset_discards_held_presof_packet() {
        let (_,p)=make_frame(1,2000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        w.ingest(1,0,&p[1],&mut s).unwrap();w.start_session(2,&mut s).unwrap();
        assert_eq!(w.ingest(1,1,&p[0],&mut s),Err(Error::WrongSession));
        let o=w.ingest(2,1,&p[0],&mut s).unwrap();assert_eq!(o.forwarded,1);assert!(!o.completed);
        assert!(w.ingest(2,2,&p[1],&mut s).unwrap().completed);
    }
    #[test] fn local_session_label_cannot_authenticate_old_wire_packet() {
        let (_,p)=make_frame(1,1000,1000);let mut w=Window::new(1);let mut s=TestSink::default();
        assert!(w.ingest(1,0,&p[0],&mut s).unwrap().completed);w.start_session(2,&mut s).unwrap();
        // MSV1 has no wire session/authentication. Caller labeling an old packet
        // as the new session makes it indistinguishable from a valid new frame.
        assert!(w.ingest(2,0,&p[0],&mut s).unwrap().completed);
    }
    #[test] fn sink_failure_poison_requires_successful_reset() {
        let (_,p)=make_frame(1,1000,1000);let mut w=Window::new(1);let mut s=TestSink{fail_packet:true,..Default::default()};
        assert_eq!(w.ingest(1,0,&p[0],&mut s),Err(Error::Sink));assert_eq!(s.aborted,1);
        assert_eq!(w.tick(1,1,&mut s),Err(Error::Poisoned));s.fail_abort=true;
        assert_eq!(w.start_session(2,&mut s),Err(Error::Sink));s.fail_abort=false;s.fail_packet=false;
        w.start_session(2,&mut s).unwrap();assert!(w.ingest(2,0,&p[0],&mut s).unwrap().completed);
    }
    #[test] fn memory_footprint_is_recorded() {std::println!("WINDOW_SIZE_BYTES={}",core::mem::size_of::<Window>());assert!(core::mem::size_of::<Window>()>=5*PACKET_BYTES);}
}
