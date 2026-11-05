#![allow(dead_code)]
#[path = "../handheld/src/streaming/service_policy.rs"]
mod service_policy;

#[path = "../handheld/src/streaming/audio_io.rs"]
mod audio_io;
#[path = "../handheld/src/streaming/av_session.rs"]
mod av_session;
#[path = "../handheld/src/streaming/av_wire.rs"]
mod av_wire;
#[path = "../handheld/src/streaming/audio_diag.rs"]
mod diag;
#[path = "../handheld/src/streaming/protocol.rs"]
mod protocol;
#[path = "../handheld/src/streaming/compressed_queue.rs"]
mod q;
use audio_io::{Bus, Feeder, Phase, ResultEvent as E};
#[derive(Default)]
struct Backend {
    session: u32,
    seq: u32,
    commits: u32,
    result: u32,
    staging: bool,
    queued: u32,
    pcm_writes: u32,
    patterns: Vec<u8>,
}
impl Bus for Backend {
    fn read(&mut self, o: u32) -> Result<u32, ()> {
        Ok(match o {
            0 => 0x4d425631,
            4 => 0x10000,
            0x184 => audio_io::BUILD,
            0x300 => audio_io::MAGIC,
            0x304 => audio_io::SCHEMA,
            0x30c => {
                1 | (self.result << 8)
                    | if self.staging { 2 } else { 0 }
                    | if self.result == 3 { 64 } else { 0 }
            }
            0x320 => 8 - self.queued,
            0x324 => self.commits,
            0x328 => self.seq,
            0x32c => self.session,
            _ => panic!(),
        })
    }
    fn write(&mut self, o: u32, v: u32) -> Result<(), ()> {
        match o {
            0x31c => self.session = v,
            0x310 | 0x318 => {}
            0x314 => self.seq = v,
            0x308 => match v {
                0 => {
                    self.queued = 0;
                    self.staging = false;
                    self.result = 5;
                }
                1 => self.result = 1,
                2 => {
                    self.staging = true;
                    self.result = 2;
                }
                3 => {
                    assert!(self.staging);
                    self.staging = false;
                    self.commits = self.commits.wrapping_add(1);
                    self.result = 3;
                    self.queued += 1;
                }
                _ => panic!(),
            },
            _ => panic!(),
        }
        Ok(())
    }
    fn pcm(&mut self, data: &[u8]) -> Result<(), ()> {
        assert_eq!(data.len(), 2020);
        assert!(self.staging);
        self.pcm_writes += 1;
        self.patterns.push(data[0]);
        Ok(())
    }
}
fn ready() -> (Feeder, Backend) {
    let (mut f, mut b) = (Feeder::new(), Backend::default());
    f.start(9);
    for _ in 0..4 {
        if f.step(&mut b, &[0; 2020]) == E::Online {
            return (f, b);
        }
    }
    panic!()
}

use service_policy::{Checkpoint, Pass, Step, ServiceMetrics, InputMetrics};
fn checkpoint_input(session:&mut av_session::Session,input:&mut InputMetrics,now:u64,cancel:bool)->Checkpoint {
    let decision=service_policy::checkpoint(now,cancel,session.active.map(|a|a.lease_us),input.due_us);
    if decision==Checkpoint::InputDue {
        let (_,seq)=session.next_input().unwrap();input.attempt(now,true);input.sent(now,seq,Ok(80),80);
    }
    decision
}
fn session(now:u64)->av_session::Session {
    use av_wire::Kind;
    let mut s=av_session::Session::new();let mut bytes=[0u8;80];
    let n=av_wire::encode(Kind::Hello,17,0,1,now,&[],&mut bytes).unwrap().len();
    assert_eq!(s.receive(av_wire::parse(&bytes[..n]).unwrap(),9,now,19),av_session::Event::Offer);
    let n=av_wire::encode(Kind::Start,19,1,1,now,&17u64.to_be_bytes(),&mut bytes).unwrap().len();
    assert_eq!(s.receive(av_wire::parse(&bytes[..n]).unwrap(),9,now,0),av_session::Event::Started);s
}
#[test]
fn fifteen_ms_shared_video_lock_stall_does_not_burn_twenty_retries_or_overwrite_pcm(){
 let(mut f,mut bus)=ready();let mut q=q::Queue::new();let mut compressed=vec![0;q::STORAGE_BYTES];
 let mut pcm=vec![0;2020];let mut pending=None;let(mut accepted,mut rejected)=(0,0);let mut arrived=0u64;
 let mut metrics=ServiceMetrics::new();let mut input=InputMetrics::new();let mut session=session(0);
 for tick in (0..80000u64).step_by(1000){
  checkpoint_input(&mut session,&mut input,tick,false);
  if arrived<4 && tick>=arrived*10457 {
   assert!(q.push(q::Meta{session:9,sequence:arrived as u32,arrival_us:tick},&[arrived as u8;512],&mut compressed).unwrap().is_none());arrived+=1;
  }
  assert!(!q.stale(tick));
  if f.phase==Phase::Idle&&f.active&&pending.is_none(){if let Some(m)=q.pop(){pcm.fill(m.sequence as u8);assert!(f.submit(m.sequence,0));pending=Some(m.sequence);}}
  let held_pattern=pcm[0];let mut pass=Pass::feeder(tick);let mut now=tick;
  while !matches!(f.phase,Phase::Idle|Phase::Failed)&&pass.allow(now){
   checkpoint_input(&mut session,&mut input,now,false);
   if tick<15000 {pass.observe(Step::LockMiss);continue;}
   let before=f.phase;let event=f.step(&mut bus,&pcm);pass.observe(service_policy::step_outcome(true,before!=f.phase,event!=E::None));now+=25;
   if event==E::Committed {audio_io::settle_block(&mut pending,&mut accepted,&mut rejected,true);}
  }
  if tick<15000&&pass.attempts>0 {assert_eq!(pass.attempts,1);assert_eq!(pcm[0],held_pattern);assert!(bus.patterns.is_empty());}
  metrics.finish(pass,now);bus.queued=0;
 }
 assert_eq!((accepted,rejected),(4,0));assert_eq!(bus.patterns,vec![0,1,2,3]);assert_eq!(metrics.lock_deferrals,15);
 assert!(input.sent>=4);assert!(input.max_success_gap_us<=20000);assert_eq!(input.errors,0);
}
#[test]
fn service_time_budget_stops_between_actual_feeder_steps_without_losing_pending_owner(){
 let(mut f,mut b)=ready();assert!(f.submit(42,0));let mut p=Pass::feeder(0);let mut now=0;
 while p.allow(now){let old=f.phase;let e=f.step(&mut b,&[42;2020]);p.observe(service_policy::step_outcome(true,old!=f.phase,e!=E::None));now+=600;}
 assert_eq!((p.attempts,p.progress),(4,4));assert_eq!(p.end,Some(service_policy::End::Time));assert_eq!(now,2400);assert_eq!(f.sequence,42);assert_eq!(b.pcm_writes,0);
 // Policy checks between actions: this is intentionally not a hard2ms WCET claim.
}
#[test]
fn fresh_lease_check_interrupts_pass_before_pcm_and_cancel_stop_releases_backend(){
 let(mut f,mut b)=ready();assert!(f.submit(42,0));let mut s=session(0);let mut i=InputMetrics::new();i.due_us=500000;
 let mut pass=Pass::feeder(499950);let mut now=499950;let mut actions=0;
 loop{let c=checkpoint_input(&mut s,&mut i,now,false);if c==Checkpoint::Expired{break;}assert!(pass.allow(now));let before=f.phase;let e=f.step(&mut b,&[42;2020]);pass.observe(service_policy::step_outcome(true,before!=f.phase,e!=E::None));actions+=1;now+=200;}
 assert_eq!(actions,1);assert_eq!(i.sent,0);assert_eq!(b.pcm_writes,0);assert_eq!(f.sequence,42);assert!(s.expire(now));
 f.stop();let mut stopped=false;
 for _ in 0..4{if audio_io::checked_step(&mut f,&mut b,&[42;2020],true,true,1,1)==E::Stopped{stopped=true;break;}}
 assert!(stopped);assert!(!b.staging);assert_eq!(b.pcm_writes,0);
}
#[test]
fn receive_batch_rechecks_input_deadline_and_never_catches_up_with_a_burst(){
 let mut s=session(0);let mut input=InputMetrics::new();input.due_us=20000;
 let mut pass=Pass::receive(19000);let mut now=19000;let mut received=0;
 while pass.allow(now){checkpoint_input(&mut s,&mut input,now,false);received+=1;now+=900;}
 checkpoint_input(&mut s,&mut input,now,false);
 assert_eq!(received,2);assert_eq!(input.sent,1);assert_eq!(input.max_lateness_us,800);assert_eq!(input.due_us,40800);
 assert_eq!(pass.end,Some(service_policy::End::Time));
}
#[test]
fn cancel_precedes_even_due_input_and_generation_change_cannot_submit_more_pcm(){
 let(mut f,mut b)=ready();assert!(f.submit(7,0));let mut s=session(0);let mut input=InputMetrics::new();input.due_us=0;
 assert_eq!(checkpoint_input(&mut s,&mut input,100,true),Checkpoint::Cancel);assert_eq!(input.sent,0);
 let before=f.phase;
 assert_eq!(audio_io::checked_step(&mut f,&mut b,&[7;2020],false,false,1,2),E::None);
 assert_eq!(f.phase,before);assert_eq!(b.pcm_writes,0);
 assert_eq!(audio_io::checked_step(&mut f,&mut b,&[7;2020],true,false,1,2),E::Fault);assert_eq!(b.pcm_writes,0);
}
#[test]
fn no_progress_status_poll_yields_instead_of_repeating_under_device_lock(){
 let mut f=Feeder::new();let mut b=Backend::default();f.start(9);
 assert_eq!(f.step(&mut b,&[0;2020]),E::None);assert_eq!(f.phase,Phase::WaitStop);
 // Force STOP receipt to remain outstanding.
 b.result=0;let mut pass=Pass::feeder(0);assert!(pass.allow(0));let old=f.phase;let e=f.step(&mut b,&[0;2020]);pass.observe(service_policy::step_outcome(true,old!=f.phase,e!=E::None));
 assert_eq!(pass.end,Some(service_policy::End::Deferred));assert!(!pass.allow(10));assert_eq!(pass.attempts,1);assert_eq!(b.pcm_writes,0);
}

#[test]
fn cancellation_of_staged_pcm_aborts_backend_without_replaying_dma(){
 let(mut f,mut b)=ready();assert!(f.submit(42,0));
 while f.phase!=Phase::Pcm{assert_ne!(f.step(&mut b,&[42;2020]),E::Fault);}
 assert!(b.staging);let before=f.phase;
 assert_eq!(audio_io::checked_step(&mut f,&mut b,&[42;2020],false,false,1,1),E::None);
 assert_eq!(f.phase,before);assert_eq!(b.pcm_writes,0);
 f.stop();let mut stopped=false;for _ in 0..4{if audio_io::checked_step(&mut f,&mut b,&[42;2020],false,true,1,1)==E::Stopped{stopped=true;break;}}
 assert!(stopped);assert!(!b.staging);assert_eq!(b.pcm_writes,0);
 let mut pending=Some(42);let(mut a,mut r)=(0,0);assert_eq!(audio_io::settle_block(&mut pending,&mut a,&mut r,false),Some(42));assert_eq!(audio_io::settle_block(&mut pending,&mut a,&mut r,false),None);assert_eq!((a,r),(0,1));
}
