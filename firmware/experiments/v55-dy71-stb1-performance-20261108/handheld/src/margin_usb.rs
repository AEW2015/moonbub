//! Static fixed state, existing4KiB USB task; no new worker or parser heap.
use crate::{device::Device,margin::{self,Controller,Report},timing,timing_line::{Parser,Event}};
use std::{sync::Mutex,time::{Duration,Instant}};
struct State {margin:Controller,timing:timing::Controller,parser:Parser,started:Option<Instant>,query_both:bool}
static STATE:Mutex<State>=Mutex::new(State{margin:Controller::new(),timing:timing::Controller::new(),parser:Parser::new(),started:None,query_both:false});
enum Completion {Margin(Report),Timing(timing::Report)}
pub struct Driver;
impl Driver {
 pub fn new()->Self{Self}
 pub fn command(&mut self,key:u8)->bool{STATE.lock().unwrap().command(key)}
 pub fn tick(&mut self){STATE.lock().unwrap().tick()}
}
fn now_ms()->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time()as u64/1000}}
impl State {
 fn busy(&self)->bool{self.margin.active()||self.timing.active()}
 fn start_timing(&mut self,key:u8,choice:timing::Choice){if self.busy(){log::info!("USB_TRACE timing key={} result=LocalBusy",key as char);return}match self.timing.request(key,choice){Ok(())=>self.started=Some(Instant::now()),Err(report)=>print_timing(report)}}
 fn command(&mut self,key:u8)->bool{
  match self.parser.feed(key,now_ms()){
   Event::Consumed=>return true,
   Event::Complete(result)=>{match result{Ok(values)=>match timing::Timing::new(values){Ok(target)=>self.start_timing(b'T',timing::Choice::Custom(target)),Err(reason)=>log::info!("USB_TRACE timing key=T result={:?} write_attempted=false",reason)},Err(reason)=>log::info!("USB_TRACE timing key=T line_error={:?} write_attempted=false",reason)}return true},
   Event::Pass=>{}
  }
  if key==b'h'{log::info!("USB_TRACE display_control abi=1 local_loops=1")}
  if key==b'f'||key==b'g'{self.start_timing(key,if key==b'f'{timing::Choice::Official}else{timing::Choice::Current});return true}
  if margin::Action::from_byte(key).is_none(){return false}
  if self.busy(){log::info!("USB_TRACE margin key={} result=LocalBusy",key as char);return true}
  match self.margin.request(key){Ok(true)=>{self.started=Some(Instant::now());self.query_both=key==b'h'},Err(report)=>print_margin(report),_=>{}}true
 }
 fn tick(&mut self){
  if let Some(reason)=self.parser.timeout(now_ms()){log::info!("USB_TRACE timing key=T line_error={:?} discard_until_lf=true",reason)}
  if !self.busy(){return}
  if self.started.is_some_and(|t|t.elapsed()>=Duration::from_millis(500)){
   if let Some(report)=self.margin.expire(){print_margin(report)}if let Some(report)=self.timing.expire(){print_timing(report)}self.started=None;self.query_both=false;return
  }
  // One state transition, <=9 QSPI transactions, no output while Device held.
  let report=if let Some(mut device)=Device::try_lock(){
   struct Adapter<'a,'b>(&'a mut Device<'b>);
   impl margin::Bus for Adapter<'_,'_>{fn read(&mut self,offset:u32)->Result<u32,()>{self.0.fpga.read_u32(margin::BASE+offset).map_err(|_|())}fn write(&mut self,offset:u32,value:u32)->Result<(),()>{self.0.fpga.write_u32(margin::BASE+offset,value).map_err(|_|())}}
   let mut bus=Adapter(&mut device);if self.margin.active(){self.margin.step(&mut bus).map(Completion::Margin)}else{self.timing.step(&mut bus).map(Completion::Timing)}
  }else{None};
  match report{Some(Completion::Margin(report))=>{print_margin(report);self.started=None;if self.query_both{self.query_both=false;self.start_timing(b'h',timing::Choice::Query)}},Some(Completion::Timing(report))=>{print_timing(report);self.started=None;},None=>{}}
 }
}
fn print_margin(report:Report){let s=report.observed;log::info!("USB_TRACE margin key={} target={:?} requested={:?} applied={:?} pending={:?} seq={:?} result={:?} hw_result={:?} write_attempted={}",report.key as char,report.target,s.map(|s|s.requested),s.and_then(|s|s.applied_valid()),s.map(|s|s.pending),s.map(|s|s.sequence),report.outcome,s.map(|s|s.result),report.write_attempted);}
fn print_timing(report:timing::Report){let s=report.status;log::info!("USB_TRACE timing key={} target_h={:?} target_v={:?} applied_h={:?} applied_v={:?} pending={:?} seq={:?} result={:?} hw_result={:?} apply_attempted={}",report.key as char,report.target.map(|v|v.horizontal),report.target.map(|v|v.vertical),report.applied.map(|v|v.horizontal),report.applied.map(|v|v.vertical),s.map(|v|v.pending),s.map(|v|v.sequence),report.outcome,s.map(|v|v.result),report.apply_attempted);}
