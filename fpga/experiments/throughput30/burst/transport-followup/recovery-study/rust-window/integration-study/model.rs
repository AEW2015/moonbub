//! Isolated no_std driver + modeled FPGA transaction. Not production firmware.
//!
//! This mock demonstrates only the assumptions described by the tests. It is
//! neither the FPGA RTL nor a timing-accurate QSPI/DMA implementation.
use crate::protocol::{crc_update, Header};
use crate::window::{Error as WindowError, Outcome, Sink, Window};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DriverError { Quarantined, Window(WindowError), Abort }

/// Integration shim that unconditionally aborts an old sink transaction when
/// replacing sessions, including a committed frame still awaiting presentation.
pub struct Driver { window: Window, quarantined: bool }
impl Driver {
    pub fn new(session: u32) -> Self { Self { window: Window::new(session), quarantined: false } }
    pub fn ingest<S: Sink>(&mut self, session:u32, now_us:u64, packet:&[u8], sink:&mut S) -> Result<Outcome,DriverError> {
        if self.quarantined { return Err(DriverError::Quarantined); }
        match self.window.ingest(session,now_us,packet,sink) {
            Ok(x)=>Ok(x), Err(e)=>{if matches!(e,WindowError::Sink|WindowError::Poisoned){self.quarantined=true;}Err(DriverError::Window(e))}
        }
    }
    pub fn tick<S: Sink>(&mut self, session:u32, now_us:u64, sink:&mut S) -> Result<Outcome,DriverError> {
        if self.quarantined { return Err(DriverError::Quarantined); }
        match self.window.tick(session,now_us,sink) {
            Ok(x)=>Ok(x), Err(e)=>{if matches!(e,WindowError::Sink|WindowError::Poisoned){self.quarantined=true;}Err(DriverError::Window(e))}
        }
    }
    pub fn replace_session<S: Sink>(&mut self, session:u32, sink:&mut S) -> Result<(),DriverError> {
        // A completed receiver has active=None while a committed frame can
        // still be pending in FPGA. Clear the sink even in that state.
        if sink.abort().is_err() { self.quarantined=true; return Err(DriverError::Abort); }
        if let Err(e)=self.window.start_session(session,sink) { self.quarantined=true;return Err(DriverError::Window(e)); }
        self.quarantined=false;Ok(())
    }
    pub fn quarantined(&self)->bool {self.quarantined}
}

/// Simplified fixed-buffer model. Abort is deliberately idempotent.
/// `vblank` is explicit; real FPGA is autonomous and is not stopped by Driver.
pub struct MockFpga<const N:usize> {
    front:[u8;N],front_len:usize,front_id:Option<u32>,
    staged:[u8;N],staged_len:usize,staged_id:Option<u32>,staged_total:usize,
    receiving:bool,pending:bool,
    pub forced_busy:bool,pub fail_begin:bool,pub fail_forward:bool,
    pub fail_commit_after_accept:bool,pub fail_abort:bool,
    pub begins:u32,pub commits:u32,pub aborts:u32,pub presentations:u32,
}
impl<const N:usize> MockFpga<N> {
    pub fn new(initial:&[u8],initial_id:u32)->Option<Self> {
        if initial.len()>N {return None;}
        let mut f=Self{front:[0;N],front_len:initial.len(),front_id:Some(initial_id),staged:[0;N],
         staged_len:0,staged_id:None,staged_total:0,receiving:false,pending:false,
         forced_busy:false,fail_begin:false,fail_forward:false,fail_commit_after_accept:false,fail_abort:false,
         begins:0,commits:0,aborts:0,presentations:0};
        f.front[..initial.len()].copy_from_slice(initial);Some(f)
    }
    pub fn front(&self)->&[u8] {&self.front[..self.front_len]}
    pub fn front_id(&self)->Option<u32> {self.front_id}
    pub fn pending(&self)->bool {self.pending}
    pub fn receiving(&self)->bool {self.receiving}
    /// Represents an autonomous hardware boundary, not a callback from Driver.
    pub fn vblank(&mut self)->bool {
        if !self.pending {return false;}
        self.front[..self.staged_len].copy_from_slice(&self.staged[..self.staged_len]);
        self.front_len=self.staged_len;self.front_id=self.staged_id;self.pending=false;
        self.presentations+=1;true
    }
}
impl<const N:usize> Sink for MockFpga<N> {
    fn packet(&mut self,h:Header,payload:&[u8],done:bool)->Result<(),()> {
        if h.offset==0 {
            if self.forced_busy||self.receiving||self.pending||h.length as usize>N{return Err(());}
            // Set state before returning an injected begin failure, to model a
            // command that may have reached the FPGA despite an error reply.
            self.receiving=true;self.staged_len=0;self.staged_total=h.length as usize;self.staged_id=Some(h.id);self.begins+=1;
            if self.fail_begin {return Err(());}
        }
        if !self.receiving||self.staged_id!=Some(h.id)||h.offset as usize!=self.staged_len||
           self.staged_len.checked_add(payload.len()).filter(|x|*x<=self.staged_total && *x<=N).is_none(){return Err(());}
        if self.fail_forward {
            let partial=payload.len()/2;self.staged[self.staged_len..self.staged_len+partial].copy_from_slice(&payload[..partial]);
            self.staged_len+=partial;return Err(());
        }
        self.staged[self.staged_len..self.staged_len+payload.len()].copy_from_slice(payload);self.staged_len+=payload.len();
        if done {
            if self.staged_len!=self.staged_total || self.staged_len<4 || self.staged[..2]!=[0xff,0xd8] ||
               self.staged[self.staged_len-2..self.staged_len]!=[0xff,0xd9] ||
               !crc_update(!0,&self.staged[..self.staged_len])!=h.crc{return Err(());}
            self.receiving=false;self.pending=true;self.commits+=1;
            // Model an ambiguous acknowledgement: commit may have succeeded
            // even though the software sees a transport error.
            if self.fail_commit_after_accept {return Err(());}
        }
        Ok(())
    }
    fn abort(&mut self)->Result<(),()> {
        self.aborts+=1;if self.fail_abort {return Err(());}
        self.receiving=false;self.pending=false;self.staged_len=0;self.staged_id=None;Ok(())
    }
}

#[cfg(test)]
mod tests {
 use super::*;
 use crate::protocol::HEADER;
 use std::vec::Vec;
 const OLD:&[u8]=b"previous front stays intact";
 fn packets(id:u32,len:usize,chunk:usize)->(Vec<u8>,Vec<Vec<u8>>) {
  assert!(len>=4);let mut data:Vec<u8>=(0..len).map(|i|(i.wrapping_mul(41)%251)as u8).collect();
  data[..2].copy_from_slice(&[0xff,0xd8]);data[len-2..].copy_from_slice(&[0xff,0xd9]);
  let crc=!crc_update(!0,&data);let mut out=Vec::new();
  for off in (0..len).step_by(chunk){let n=core::cmp::min(chunk,len-off);let mut p=std::vec![0u8;HEADER+n];
   p[..4].copy_from_slice(b"MSV1");p[4]=1;p[5]=1;
   let f=(if off==0{1u16}else{0})|(if off+n==len{2u16}else{0});
   p[6..8].copy_from_slice(&f.to_be_bytes());p[8..12].copy_from_slice(&id.to_be_bytes());
   p[12..14].copy_from_slice(&720u16.to_be_bytes());p[14..16].copy_from_slice(&480u16.to_be_bytes());
   p[16..20].copy_from_slice(&(len as u32).to_be_bytes());p[20..24].copy_from_slice(&(off as u32).to_be_bytes());
   p[24..26].copy_from_slice(&(n as u16).to_be_bytes());p[28..32].copy_from_slice(&crc.to_be_bytes());
   p[32..40].copy_from_slice(&100u64.to_be_bytes());p[HEADER..].copy_from_slice(&data[off..off+n]);out.push(p);
  }
  (data,out)
 }
 fn model()->MockFpga<4096>{MockFpga::new(OLD,77).unwrap()}
 fn intact(s:&MockFpga<4096>){assert_eq!(s.front(),OLD);assert_eq!(s.front_id(),Some(77));}
 #[test] fn reordered_data_is_committed_once_then_presented_at_boundary() {
  let (payload,p)=packets(1,2400,600);let mut d=Driver::new(1);let mut s=model();
  for (now,i) in [1usize,0,3,2].iter().enumerate(){d.ingest(1,now as u64,&p[*i],&mut s).unwrap();}
  assert_eq!(s.begins,1);assert_eq!(s.commits,1);assert!(s.pending());intact(&s);
  assert!(s.vblank());assert_eq!(s.front(),payload);assert_eq!(s.front_id(),Some(1));assert_eq!(s.presentations,1);
  assert!(!s.vblank());
 }
 #[test] fn dropped_packet_gap_timeout_aborts_before_presentation() {
  let (_,p)=packets(1,2400,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,10,&p[0],&mut s).unwrap();d.ingest(1,20,&p[2],&mut s).unwrap();
  assert!(!d.tick(1,2019,&mut s).unwrap().gap_expired);assert!(d.tick(1,2020,&mut s).unwrap().gap_expired);
  assert_eq!(s.aborts,1);assert!(!s.pending());assert!(!s.receiving());assert_eq!(s.commits,0);assert!(!s.vblank());intact(&s);
 }
 #[test] fn crc_error_aborts_and_never_commits_bad_frame() {
  let (_,mut p)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&p[0],&mut s).unwrap();p[1][HEADER]^=1;
  assert_eq!(d.ingest(1,1,&p[1],&mut s),Err(DriverError::Window(WindowError::Receiver)));
  assert_eq!(s.aborts,1);assert_eq!(s.commits,0);assert!(!s.vblank());intact(&s);
 }
 #[test] fn new_sof_aborts_old_active_frame_before_next_begin() {
  let (_,a)=packets(1,1200,600);let (b,p)=packets(2,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&a[0],&mut s).unwrap();d.ingest(1,1,&p[0],&mut s).unwrap();
  assert_eq!(s.aborts,1);assert_eq!(s.begins,2);d.ingest(1,2,&p[1],&mut s).unwrap();
  assert!(s.vblank());assert_eq!(s.front(),b);assert_eq!(s.front_id(),Some(2));assert_eq!(s.commits,1);
 }
 #[test] fn bare_window_reset_does_not_cancel_committed_pending_sink() {
  let (old_pending,p)=packets(1,1200,600);let mut w=Window::new(1);let mut s=model();
  for (i,x) in p.iter().enumerate(){w.ingest(1,i as u64,x,&mut s).unwrap();}
  assert!(s.pending());w.start_session(2,&mut s).unwrap();
  // Window tracks input completion, not downstream decoder/presentation state.
  // Without the outer Driver's unconditional sink abort, stale pending data
  // remains eligible for an autonomous display boundary.
  assert!(s.pending());assert!(s.vblank());assert_eq!(s.front(),old_pending);
 }
 #[test] fn replacement_session_invalidates_already_committed_old_pending() {
  let (_,a)=packets(1,1200,600);let (b,p)=packets(2,1200,600);let mut d=Driver::new(1);let mut s=model();
  for (i,x) in a.iter().enumerate(){d.ingest(1,i as u64,x,&mut s).unwrap();}
  assert!(s.pending());assert_eq!(s.commits,1);intact(&s);
  d.replace_session(2,&mut s).unwrap();assert!(!s.pending());assert!(!s.vblank());intact(&s);
  assert_eq!(d.ingest(1,4,&p[0],&mut s),Err(DriverError::Window(WindowError::WrongSession)));
  d.ingest(2,0,&p[0],&mut s).unwrap();d.ingest(2,1,&p[1],&mut s).unwrap();
  assert!(s.vblank());assert_eq!(s.front(),b);assert_eq!(s.front_id(),Some(2));
 }
 #[test] fn replacement_session_aborts_partially_received_data_idempotently() {
  let (_,a)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&a[0],&mut s).unwrap();d.replace_session(2,&mut s).unwrap();
  assert_eq!(s.aborts,2);assert!(!s.receiving());assert!(!s.vblank());intact(&s);
 }
 #[test] fn busy_begin_failure_drops_pending_but_never_corrupts_front() {
  let (_,a)=packets(1,1200,600);let (_,b)=packets(2,1200,600);let mut d=Driver::new(1);let mut s=model();
  for (i,p) in a.iter().enumerate(){d.ingest(1,i as u64,p,&mut s).unwrap();}assert!(s.pending());
  assert_eq!(d.ingest(1,2,&b[0],&mut s),Err(DriverError::Window(WindowError::Sink)));
  assert!(d.quarantined());assert!(!s.pending());assert!(!s.vblank());intact(&s);
  // The conservative forced abort drops the valid pending frame too.
  assert_eq!(s.commits,1);assert_eq!(s.aborts,1);
 }
 #[test] fn failed_begin_or_partial_forward_quarantines_and_preserves_front() {
  for begin in [true,false] {
   let (_,p)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
   if begin{s.fail_begin=true;} else {s.fail_forward=true;}
   assert_eq!(d.ingest(1,0,&p[0],&mut s),Err(DriverError::Window(WindowError::Sink)));
   assert!(d.quarantined());assert!(!s.receiving());assert!(!s.pending());assert!(!s.vblank());intact(&s);
   assert_eq!(d.tick(1,1,&mut s),Err(DriverError::Quarantined));
  }
 }
 #[test] fn ambiguous_commit_failure_with_successful_abort_preserves_front() {
  let (_,p)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&p[0],&mut s).unwrap();s.fail_commit_after_accept=true;
  assert_eq!(d.ingest(1,1,&p[1],&mut s),Err(DriverError::Window(WindowError::Sink)));
  assert!(d.quarantined());assert_eq!(s.commits,1);assert!(!s.pending());assert_eq!(s.aborts,1);assert!(!s.vblank());intact(&s);
 }
 #[test] fn failed_abort_cannot_guarantee_front_is_preserved_at_autonomous_boundary() {
  let (new,p)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&p[0],&mut s).unwrap();s.fail_commit_after_accept=true;s.fail_abort=true;
  assert_eq!(d.ingest(1,1,&p[1],&mut s),Err(DriverError::Window(WindowError::Sink)));
  assert!(d.quarantined());assert!(s.pending());intact(&s);
  // This is a deliberate counterexample: Driver cannot prevent an autonomous
  // boundary if commit succeeded and abort was not confirmed.
  assert!(s.vblank());assert_eq!(s.front(),new);assert_eq!(s.front_id(),Some(1));
 }
 #[test] fn failed_abort_on_session_replacement_quarantines_until_retry() {
  let (_,p)=packets(1,1200,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&p[0],&mut s).unwrap();s.fail_abort=true;
  assert_eq!(d.replace_session(2,&mut s),Err(DriverError::Abort));assert!(d.quarantined());
  assert_eq!(d.ingest(1,1,&p[1],&mut s),Err(DriverError::Quarantined));intact(&s);
  s.fail_abort=false;d.replace_session(2,&mut s).unwrap();assert!(!d.quarantined());assert!(!s.pending());intact(&s);
 }
 #[test] fn duplicate_and_wrong_session_do_not_commit_stale_data() {
  let (_,p)=packets(1,2400,600);let mut d=Driver::new(1);let mut s=model();
  d.ingest(1,0,&p[0],&mut s).unwrap();d.ingest(1,1,&p[2],&mut s).unwrap();
  assert_eq!(d.ingest(2,2,&p[1],&mut s),Err(DriverError::Window(WindowError::WrongSession)));
  assert_eq!(d.ingest(1,2,&p[2],&mut s),Err(DriverError::Window(WindowError::Duplicate)));
  assert!(!s.pending());assert!(!s.vblank());intact(&s);
 }
}
