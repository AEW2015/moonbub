//! USB G: guarded local two-fixture CU71 loader, no network backend or autoprogramming.
use super::local::{self,Bus,Error};
use crate::{core_access::MaintenanceGuard,core_coordinator::{Maintenance,CONTROL},device::{Device,drivers::fpga::{FpgaSpiWordSize,SpiCommand,MAX_SPI_READ_CLOCK}},diag_dispatch::{self,Launcher}};
use std::sync::{mpsc,atomic::{AtomicBool,AtomicU8,Ordering}};
static LAB_READY:AtomicBool=AtomicBool::new(false);
static LAB_REQUEST:AtomicU8=AtomicU8::new(0);
static REQUESTS:diag_dispatch::Requests=diag_dispatch::Requests::new();
const STACK:usize=12_288;
struct Spawn{profile:local::Profile}
impl Launcher for Spawn{
 type Job=MaintenanceGuard;type Sender=mpsc::SyncSender<Self::Job>;
 fn reserve(&mut self)->Result<Self::Job,()>{MaintenanceGuard::acquire(Maintenance::Benchmark).map_err(|_|())}
 fn spawn_empty(&mut self)->Result<Self::Sender,()>{let profile=self.profile;let(tx,rx)=mpsc::sync_channel(1);std::thread::Builder::new().name("Cu71Local".into()).stack_size(STACK).spawn(move||{if let Ok(p)=rx.recv(){worker(p,profile);REQUESTS.finished();}}).map_err(|_|())?;Ok(tx)}
 fn send(&mut self,tx:&Self::Sender,p:Self::Job)->Result<(),Self::Job>{tx.send(p).map_err(|e|e.0)}
 fn release_unissued(&mut self,p:Self::Job)->bool{drop(p);!CONTROL.lock().unwrap().quarantined()}
 fn publish(&mut self,tx:Self::Sender){drop(tx)}
}
fn heap()->(usize,usize){unsafe{let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;(esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps))}}
pub fn start(){start_profile(local::Profile::Cu71)}
pub fn start_direct(){start_profile(local::Profile::Dy71)}
fn start_profile(profile:local::Profile){log::info!("USB_CU71_LOCAL requested_profile={:?} network_capability=false",profile);let(free,largest)=heap();if free<170_000||largest<24_576{log::info!("USB_CU71_LOCAL result=heap_budget free={} largest={} required=170000/24576",free,largest);return}if !crate::streaming::diagnostic_trace_idle(){log::info!("USB_CU71_LOCAL result=busy");return}let result=diag_dispatch::launch(&REQUESTS,&mut Spawn{profile});log::info!("USB_CU71_LOCAL launch={:?} network_capability=false",result);}
pub(crate) struct Adapter<'a>{pub(crate) guard:&'a mut MaintenanceGuard,pub(crate) epoch:Option<u32>,pub(crate) reads:u32,pub(crate) writes:u32,pub(crate) transactions:u32}
impl Bus for Adapter<'_>{
 fn now(&self)->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time().max(0)as u64}}
 fn yield_now(&mut self){std::thread::yield_now();}
 fn read(&mut self,o:u32)->Result<u32,Error>{if o>=0x1000||o&3!=0{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};let epoch=d.fpga.program_epoch();if let Some(old)=self.epoch{if old!=epoch{return Err(Error::Epoch)}}else{self.epoch=Some(epoch)}let r=d.fpga.read_u32(0xe0000000+o).map_err(|_|Error::Io);self.reads=self.reads.saturating_add(1);self.transactions=self.transactions.saturating_add(1);r}
 fn write(&mut self,o:u32,value:u32)->Result<(),Error>{if o>=0x1000||o&3!=0{return Err(Error::Bounds)}let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}self.guard.side_effects_begin();self.writes=self.writes.saturating_add(1);self.transactions=self.transactions.saturating_add(1);d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000000+o,&value.to_be_bytes()).map_err(|_|Error::Io)}
 fn write_words(&mut self,o:u32,words:&[u32])->Result<(),Error>{
  let end=o.checked_add((words.len()as u32).checked_mul(4).ok_or(Error::Bounds)?).ok_or(Error::Bounds)?;
  if words.is_empty()||words.len()>12||o&3!=0||!((o>=0x40&&end<=0x70)||(o==0x20&&words.len()==2)){return Err(Error::Bounds)}
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut b=[0u8;48];for(i,v)in words.iter().enumerate(){b[4*i..4*i+4].copy_from_slice(&v.to_be_bytes());}
  self.guard.side_effects_begin();self.writes=self.writes.saturating_add(words.len()as u32);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_write(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000000+o,&b[..words.len()*4]).map_err(|_|Error::Io)
 }
 fn mailbox_reply(&mut self)->Result<[u32;3],Error>{
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut b=[0u8;12];self.reads=self.reads.saturating_add(3);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000028,&mut b).map_err(|_|Error::Io)?;
  Ok([u32::from_be_bytes(b[..4].try_into().unwrap()),u32::from_be_bytes(b[4..8].try_into().unwrap()),u32::from_be_bytes(b[8..12].try_into().unwrap())])
 }

}
#[inline(never)]fn worker(mut guard:MaintenanceGuard,profile:local::Profile){
 let before=heap();let mut io=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0,transactions:0};
 let mut hud=match super::hud::Hud::new(131072){Ok(h)=>h,Err(e)=>{log::info!("USB_CU71_LOCAL result=allocation reason={:?}",e);return}};
 let result=local::run_with_profile(&mut io,&mut hud,profile);let reads=io.reads;let writes=io.writes;let epoch=io.epoch;drop(io);
 // Completed verifies this fixture outcome; accepted/front leases remain live and are retained.
 // Every attempted mutation retains endpoint+lease; ambiguous errors additionally quarantine explicitly.
 let succeeded=result.is_ok();log::info!("USB_CU71_LOCAL completed_profile={:?} success={}",profile,succeeded);
 let retain=writes!=0;
 let stack=unsafe{esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())};
 match result{Ok((report,_proof))=>log::info!("USB_CU71_LOCAL result=completed report={:?} reads={} writes={} epoch={:?} heap_before={:?} heap_after={:?} stack_low={} throughput_claim=false",report,reads,writes,epoch,before,heap(),stack),Err(reason)=>log::info!("USB_CU71_LOCAL result=failed reason={:?} reads={} writes={} epoch={:?} heap_before={:?} heap_after={:?} stack_low={} recovery=retain_endpoint_and_lease_after_mutation",reason,reads,writes,epoch,before,heap(),stack)}
 if retain{if !succeeded{CONTROL.lock().unwrap().quarantine();}log::info!("USB_CU71_LOCAL state={} endpoint_retained=true lease_retained=true reconfigure_required=true",if succeeded{"completed_held"}else{"quarantined_held"});held_observer(&mut guard,&hud,profile,succeeded,epoch);}
}

// Explicit local-only USB requests. They never launch a worker, take a peer's
// lease, or touch FPGA registers from the USB task.
pub fn observer_command(key:u8){
 let command=match key{b'N'=>1,b'O'=>2,b'E'=>3,_=>return};
 if !LAB_READY.load(Ordering::Acquire){log::info!("USB_LD14 request={} result=NoHeldObserver",key as char);return}
 if LAB_REQUEST.compare_exchange(0,command,Ordering::AcqRel,Ordering::Acquire).is_err(){log::info!("USB_LD14 request={} result=Busy",key as char);return}
 if !LAB_READY.load(Ordering::Acquire){let _=LAB_REQUEST.compare_exchange(command,0,Ordering::AcqRel,Ordering::Acquire);log::info!("USB_LD14 request={} result=NoHeldObserver",key as char);return}
 log::info!("USB_LD14 request={} result=Queued",key as char);
}
pub fn lcd_power(enabled:bool){
 let Ok(guard)=MaintenanceGuard::acquire(Maintenance::Benchmark)else{log::info!("USB_LCD_PREP enabled={} result=Busy",enabled);return};
 let result=if let Some(mut d)=Device::try_lock(){d.set_lcd_enabled(enabled);true}else{false};
 drop(guard);
 log::info!("USB_LCD_PREP enabled={} applied={} FPGA_write=false",enabled,result);
}
impl super::lcd_observer::Bus for Adapter<'_>{
 fn read(&mut self,o:u32)->Result<u32,super::lcd_observer::Io>{local::Bus::read(self,o).map_err(observer_io)}
 fn write(&mut self,o:u32,v:u32)->Result<(),super::lcd_observer::Io>{local::Bus::write(self,o,v).map_err(observer_io)}
 fn now(&self)->u64{local::Bus::now(self)}
 fn pause(&mut self){std::thread::sleep(std::time::Duration::from_millis(1));}
}
fn observer_io(error:Error)->super::lcd_observer::Io{match error{Error::Contended=>super::lcd_observer::Io::Busy,Error::Epoch=>super::lcd_observer::Io::Epoch,_=>super::lcd_observer::Io::Failed}}
fn held_observer(guard:&mut MaintenanceGuard,hud:&super::hud::Hud,profile:local::Profile,succeeded:bool,epoch:Option<u32>)->!{
 use super::lcd_observer::{self,Command};
 let packet=include_bytes!("fixtures/packet1.cu66");let expected=u32::from_le_bytes(packet[8..12].try_into().unwrap());
 let mut io=Adapter{guard,epoch,reads:0,writes:0,transactions:0};
 let mut available=false;
 if succeeded&&profile==local::Profile::Dy71{
  match lcd_observer::identify(&mut io){
   Ok(())=>match lcd_observer::run(&mut io,Command::Snapshot,expected){
    Ok(report)=>{log::info!("USB_LD14 snapshot={:?} source=pre_panel_RGB held_lease=true",report);available=true;},
    Err(error)=>{log::warn!("USB_LD14 result={:?} quarantine=true",error);CONTROL.lock().unwrap().quarantine();}
   },
   Err(lcd_observer::Error::Unsupported)=>log::info!("USB_LD14 available=false reason=Unsupported"),
   Err(error)=>{log::warn!("USB_LD14 result={:?} quarantine=true",error);CONTROL.lock().unwrap().quarantine();}
  }
 }
 LAB_READY.store(available,Ordering::Release);
 log::info!("USB_LD14 available={} controls=N_snapshot_O_calibration_E_video no_network=true",available);
 loop{
  std::hint::black_box(hud);std::hint::black_box(&io);
  if !available{std::thread::park();continue}
  let key=LAB_REQUEST.swap(0,Ordering::AcqRel);
  let command=match key{1=>Some(Command::Snapshot),2=>Some(Command::Pattern(true)),3=>Some(Command::Pattern(false)),_=>None};
  if let Some(command)=command{match lcd_observer::run(&mut io,command,expected){
   Ok(report)=>log::info!("USB_LD14 command={:?} report={:?} held_lease=true",command,report),
   Err(error)=>{LAB_READY.store(false,Ordering::Release);LAB_REQUEST.store(0,Ordering::Release);available=false;CONTROL.lock().unwrap().quarantine();log::warn!("USB_LD14 command={:?} result={:?} quarantine=true",command,error);}
  }}
  std::thread::sleep(std::time::Duration::from_millis(20));
 }
}
