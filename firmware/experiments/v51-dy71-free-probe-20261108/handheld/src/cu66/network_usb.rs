//! Explicit USB ~ launch. No autoload/reprogram, persistent writes or production codec claim.
use super::{local_usb::Adapter,network_driver,network_io,network_wire,report_snapshot};
use crate::{core_access::MaintenanceGuard,core_coordinator::{Maintenance,CONTROL},diag_dispatch::{self,Launcher}};
use std::{net::UdpSocket,sync::{mpsc,atomic::{AtomicBool,AtomicUsize,Ordering}}};
static MIN_FREE:AtomicUsize=AtomicUsize::new(usize::MAX);
unsafe extern "C" fn free_probe()->usize{let n=internal_free();// One exclusive worker updates this diagnostic; use load/store rather than Xtensa atomic-min lowering.
let old=MIN_FREE.load(Ordering::Relaxed);if n<old{MIN_FREE.store(n,Ordering::Relaxed);}n}
unsafe extern "C" fn largest_probe()->usize{internal_largest()}
static REQUESTS:diag_dispatch::Requests=diag_dispatch::Requests::new();
static FINISHED:AtomicBool=AtomicBool::new(false);
pub fn lab_active()->bool{REQUESTS.busy()}
pub fn lab_completed()->bool{REQUESTS.busy()&&FINISHED.load(Ordering::Acquire)}
#[derive(Clone,Copy)]struct Run{count:usize,cached:bool}
struct Job{guard:MaintenanceGuard,run:Run}
struct Spawn{run:Run}
impl Launcher for Spawn{
 type Job=Job;type Sender=mpsc::SyncSender<Self::Job>;
 fn reserve(&mut self)->Result<Self::Job,()>{MaintenanceGuard::acquire(Maintenance::Benchmark).map(|guard|{FINISHED.store(false,Ordering::Release);Job{guard,run:self.run}}).map_err(|_|())}
 fn spawn_empty(&mut self)->Result<Self::Sender,()>{let(tx,rx)=mpsc::sync_channel::<Job>(1);std::thread::Builder::new().name("Dy71NetLab".into()).stack_size(16_384).spawn(move||{if let Ok(guard)=rx.recv(){worker(guard.guard,guard.run);REQUESTS.finished();}}).map_err(|_|())?;Ok(tx)}
 fn send(&mut self,tx:&Self::Sender,p:Self::Job)->Result<(),Self::Job>{tx.send(p).map_err(|e|e.0)}
 fn release_unissued(&mut self,p:Self::Job)->bool{drop(p);!CONTROL.lock().unwrap().quarantined()}
 fn publish(&mut self,tx:Self::Sender){drop(tx)}
}
fn start_run(run:Run){if !crate::streaming::diagnostic_trace_idle(){log::warn!("DY71_NET launch=busy");return}log::info!("DY71_NET launch={:?} lab_only=true frames={} cached={} port=5535",diag_dispatch::launch(&REQUESTS,&mut Spawn{run}),run.count,run.cached);}
pub fn start(){start_run(Run{count:3,cached:true})}
pub fn start_twelve(){start_run(Run{count:12,cached:true})}
pub fn start_scalar(){start_run(Run{count:3,cached:false})}
fn now_ms()->u64{unsafe{esp_idf_svc::sys::esp_timer_get_time()as u64/1000}}
pub fn report_tick(){report_snapshot::tick(now_ms(),|line|log::info!("{}",line));}
pub fn reexport(){log::info!("DY45 REQUEST result={:?}",report_snapshot::request(now_ms()));}
// Keep allocation reserve sampling O(number of heaps); largest-block walks are separate diagnostics.
fn internal_free()->usize{unsafe{esp_idf_svc::sys::heap_caps_get_free_size((esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32)}}
fn internal_largest()->usize{unsafe{esp_idf_svc::sys::heap_caps_get_largest_free_block((esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32)}}
fn heap()->(usize,usize){unsafe{let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;(esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps))}}
#[inline(never)]fn worker(mut guard:MaintenanceGuard,run:Run){
 // Read-only identity validation precedes Wi-Fi/native allocation and every FPGA write.
 let mut io=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0,transactions:0};
 use super::local::Bus;
 let identity=(||{Ok::<_,super::local::Error>((io.read(0)?,io.read(4)?,io.read(8)?,io.read(0xc)?,io.read(0x600)?,io.read(0x604)?))})();drop(io);
 if identity!=Ok((0x44593731,0x20000,31,1,0x48425531,0x10000)){log::warn!("DY71_NET result=identity_or_not_fresh value={:?}",identity);return}
 let(mut wifi,host)=match crate::streaming::custom_lab_wifi(){Ok(x)=>x,Err(e)=>{log::warn!("DY71_NET wifi_failed={}",e);return}};
 // Bound allocation failures before mutation. The endpoint is capped at98,304 bytes; no guard is relaxed for diagnostics.
 let before=heap();if before.0<114_688||before.1<24_576{log::warn!("DY71_NET result=heap_budget free={} largest={} no_FPGA_writes=true",before.0,before.1);let _=wifi.disconnect();let _=wifi.stop();return}
 let mut hud=match super::hud::Hud::new(98_304){Ok(h)=>h,Err(e)=>{log::warn!("DY71_NET result=allocation reason={:?}",e);return}};
 MIN_FREE.store(usize::MAX,Ordering::Relaxed);
 if hud.reserve_internal_heap(free_probe,8192).is_err(){log::warn!("DY71_NET result=reserve_configuration");return}
 if hud.observe_largest(largest_probe).is_err(){log::warn!("DY71_NET result=diagnostic_configuration");return}
 let socket=match UdpSocket::bind((std::net::Ipv4Addr::UNSPECIFIED,network_wire::PORT)){Ok(s)=>s,Err(e)=>{log::warn!("DY71_NET bind_failed={}",e);return}};
 let input=match network_io::Input::new_for_sequence(socket,host,run.count){Ok(s)=>s,Err(e)=>{log::warn!("DY71_NET socket_failed={}",e);return}};
 let mut source=report_snapshot::RecordingSource::new(input);
 log::info!("DY71_NET ready=true host={} port=5535 profile=dy71-sequence-v3 frames={} mode={} heap={:?} no_fps_claim=true",host,run.count,if run.cached{"cached"}else{"scalar"},heap());
 let mut io=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0,transactions:0};
 let result=if run.cached{network_driver::run_cached_sequence(&mut io,&mut hud,&mut source,run.count)}else{network_driver::run_sequence(&mut io,&mut hud,&mut source,run.count)};let fpga=if result.is_err(){Some(report_snapshot::PassiveFpga::read_once(&mut io))}else{None};let writes=io.writes;let reads=io.reads;let transactions=io.transactions;drop(io);
 let after=heap();let health=report_snapshot::Health{reads:reads as u64,writes:writes as u64,qspi:transactions as u64,free:after.0,largest:after.1,stack_low:unsafe{esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())}as usize,min_free:MIN_FREE.load(Ordering::Relaxed)};
 let snapshot=report_snapshot::Snapshot::result(result.as_ref().map(|(report,_)|report),health,source.progress).with_diagnostics(hud.diagnostics(),fpga);
 log::info!("DY45 SAVED result={:?} paced_ms={} read_only_reexport=$",report_snapshot::publish(snapshot,now_ms()),report_snapshot::EXPORT_INTERVAL_MS);
 if result.is_err(){source.inner.failed();}
 FINISHED.store(true,Ordering::Release);
 if writes!=0{
  if result.is_err(){CONTROL.lock().unwrap().quarantine();}
  log::info!("DY71_NET endpoint_retained=true lease_retained=true reconfigure_required=true success={}",result.is_ok());
  if result.is_ok(){source.inner.held();}
  loop{std::hint::black_box(&guard);std::hint::black_box(&hud);std::hint::black_box(&wifi);std::thread::park();}
 }
 let _=wifi.disconnect();let _=wifi.stop();
}
