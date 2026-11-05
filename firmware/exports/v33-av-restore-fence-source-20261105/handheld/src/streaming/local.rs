//! Flashmapped local calibration source, serialized by the normal source worker.
use super::*;
use super::local_feed::{self,Feed,Progress,Sink};
struct Adapter<'a>{core:CoreMode,generation:u32,dma:&'a mut DmaBuffer,before_decoded:u32,before_presented:u32,fatal:bool}
impl Sink for Adapter<'_>{
 type Error=anyhow::Error;
 fn current(&self,generation:u32)->bool{protocol::generation_is_current(generation,GENERATION.load(Ordering::Acquire))}
 fn ready(&mut self)->anyhow::Result<bool>{access(|d|{
  identity(d)?;let status=d.fpga.read_u32(BASE+0x10)?;
  let(admission,causes,bench)=if self.core.mode==overlap::Mode::Overlap{(d.fpga.read_u32(BASE+0x7c)?,d.fpga.read_u32(BASE+0x80)?,d.fpga.read_u32(BASE+0x70)?)}else{(0,0,0)};
  anyhow::ensure!(status&4==0&&overlap::fault_action(causes)!=overlap::FaultAction::StopSession,"Local FPGA fault status=0x{status:x} causes=0x{causes:x}");
  Ok(overlap::peer_rebind_quiescent(self.core.mode,status,admission,causes,bench))
 })}
 fn begin(&mut self,header:protocol::Header)->anyhow::Result<()>{
  let before=access(|d|{identity(d)?;Ok((d.fpga.read_u32(BASE+0x30)?,d.fpga.read_u32(BASE+0x34)?))})?;
  self.before_decoded=before.0;self.before_presented=before.1;
  super::begin(header,self.core,&mut self.fatal,&mut false,&mut None)
 }
 fn write(&mut self,bytes:&[u8])->anyhow::Result<()>{
  anyhow::ensure!(bytes.len()<=local_feed::CHUNK,"Local DMA chunk bound");
  self.dma.bytes()[..bytes.len()].copy_from_slice(bytes);
  match forward(&self.dma.bytes()[..bytes.len()]){Ok(_)=>Ok(()),Err(ForwardError::Busy)=>anyhow::bail!("Local QSPI device busy"),Err(ForwardError::Credits)=>anyhow::bail!("Local FPGA credits unavailable"),Err(ForwardError::Fpga(e))=>Err(e)}
 }
 fn commit(&mut self)->anyhow::Result<()>{commit_frame(self.core,self.generation,&mut self.fatal)}
 fn presented(&mut self,id:u32)->anyhow::Result<bool>{access(|d|{
  identity(d)?;let status=d.fpga.read_u32(BASE+0x10)?;let causes=if self.core.mode==overlap::Mode::Overlap{d.fpga.read_u32(BASE+0x80)?}else{0};
  anyhow::ensure!(status&4==0&&overlap::fault_action(causes)!=overlap::FaultAction::StopSession,"Local FPGA decode fault status=0x{status:x} causes=0x{causes:x}");
  let decoded=d.fpga.read_u32(BASE+0x30)?;let presented=d.fpga.read_u32(BASE+0x34)?;let last=d.fpga.read_u32(BASE+0x48)?;
  Ok(local_feed::completion_observed(self.before_decoded,self.before_presented,decoded,presented,last,id))
 })}
}
fn update_counters(baseline:(u32,u32))->anyhow::Result<()>{
 let(decoded,presented,credits)=access(|d|{identity(d)?;Ok((d.fpga.read_u32(BASE+0x30)?,d.fpga.read_u32(BASE+0x34)?,d.fpga.read_u32(BASE+0x0c)?))})?;
 let mut stats=STATS.lock().unwrap();stats.decoded=decoded.wrapping_sub(baseline.0);stats.displayed=presented.wrapping_sub(baseline.1);stats.credits=credits;Ok(())
}
pub(super)fn run(id:u8,generation:u32)->anyhow::Result<()>{
 let asset=&local_assets::LOOPS[(id-1)as usize];
 {let mut stats=STATS.lock().unwrap();*stats=Stats::new();stats.source="local";stats.status=format!("Preparing LOCAL {}: no network source",asset.name);}
 BUTTONS.store(0,Ordering::Release);
 let core=match ensure_core().and_then(|_|prepare_mode(generation)){
  Ok(core)=>core,
  Err(error)=>{log::warn!("USB_TRACE local_loop source=local loop={} generation={} result=setup_failed",id,generation);memory_probe("local setup failed");return Err(error)}
 };
 OVERLAP_ACTIVE.store(core.mode==overlap::Mode::Overlap,Ordering::Release);
 let mut baseline=None;
 let result=(||->anyhow::Result<()>{
  wait_for_quiescent_epoch(core,generation)?;
  baseline=Some(access(|d|{identity(d)?;Ok((d.fpga.read_u32(BASE+0x30)?,d.fpga.read_u32(BASE+0x34)?))})?);
  let mut dma=DmaBuffer::new(local_feed::CHUNK)?;
  memory_probe("local DMA ready");
  {let _control=CONTROL.lock().unwrap();if GENERATION.load(Ordering::Acquire)!=generation||RESTORING.load(Ordering::Acquire){return Ok(())}crate::ui::send(crate::ui::Message::EnterGame);}
  status(format!("LOCAL {}: target5fps; source=local",asset.name));
  log::info!("USB_TRACE local_loop source=local loop={} name={} generation={} target_fps=5 dma_bytes=4096 result=started",id,asset.name,generation);
  let mut frame=0u32;let mut due=monotonic_us();let mut last_report=Instant::now();let mut previous_display=0;let mut button_poll=Instant::now();let mut last_polled=None;
  let mut poll_input=||{if button_poll.elapsed()>=Duration::from_millis(50){if let Some(mut d)=Device::try_lock(){if let Ok(state)=d.get_input_state(){if last_polled.as_ref()!=Some(&state){last_polled=Some(state.clone());crate::ui::send(crate::ui::Message::InputState(state));}}}button_poll=Instant::now();}};
  'playing:while GENERATION.load(Ordering::Acquire)==generation{
   while monotonic_us()<due{if GENERATION.load(Ordering::Acquire)!=generation{break 'playing}poll_input();std::thread::sleep(Duration::from_millis(2));}
   let started=monotonic_us();let source=&asset.frames[(frame as usize)%asset.frames.len()];
   let mut feed=Feed::new(source.data,source.crc,0x8000_0000u32.wrapping_add(frame),generation,started).map_err(|e|anyhow::anyhow!("Local frame metadata: {e:?}"))?;
   let mut sink=Adapter{core,generation,dma:&mut dma,before_decoded:0,before_presented:0,fatal:false};
   loop{
    match feed.step(&mut sink,monotonic_us()){
     Ok(Progress::More)=>{},
     Ok(Progress::Committed)=>{let mut stats=STATS.lock().unwrap();stats.received=stats.received.wrapping_add(1);stats.bytes=stats.bytes.saturating_add(source.data.len()as u64);},
     Ok(Progress::Presented)=>break,
     Err(local_feed::Error::Cancelled)=>break 'playing,
     Err(local_feed::Error::Sink(e))=>return Err(e),
     Err(e)=>anyhow::bail!("Local frame failed: {e:?}"),
    }
    poll_input();std::thread::sleep(Duration::from_millis(1));
   }
   update_counters(baseline.unwrap())?;frame=frame.wrapping_add(1);due=local_feed::next_due(started,monotonic_us());
   if last_report.elapsed()>=Duration::from_secs(1){let mut stats=STATS.lock().unwrap();stats.display_fps=((stats.displayed.wrapping_sub(previous_display)as u64)*1_000_000/last_report.elapsed().as_micros().max(1)as u64)as u32;previous_display=stats.displayed;log::info!("USB_TRACE local_loop source=local loop={} generation={} submitted={} decoded={} presented={} target_fps=5",id,generation,stats.received,stats.decoded,stats.displayed);last_report=Instant::now();}
  }Ok(())
 })();
 // Shared worker cannot admit the next source until this verified teardown ends.
 let recovery=abort(core.mode,true);
 OVERLAP_ACTIVE.store(false,Ordering::Release);
 memory_probe("local stopped");
 if let Err(e)=recovery{LOCAL_RECOVERY_FAILED.store(true,Ordering::Release);{let _control=CONTROL.lock().unwrap();disconnect_locked();}log::error!("USB_TRACE local_loop source=local loop={} result=recovery_unconfirmed",id);return Err(e.context("Local teardown unconfirmed; restart required"))}
 if let Some(baseline)=baseline{let _=update_counters(baseline);}
 let stats=stats();log::info!("USB_TRACE local_loop source=local loop={} generation={} submitted={} decoded={} presented={} result=stopped run_ok={} menu_restore_pending={}",id,generation,stats.received,stats.decoded,stats.displayed,result.is_ok(),RESTORING.load(Ordering::Acquire));
 result
}
