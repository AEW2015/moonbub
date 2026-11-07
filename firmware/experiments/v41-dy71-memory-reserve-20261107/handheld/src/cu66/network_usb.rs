//! Explicit USB ~ launch. No autoload/reprogram, persistent writes or production codec claim.
use super::{local_usb::Adapter,network_driver,network_io,network_wire};
use crate::{core_access::MaintenanceGuard,core_coordinator::{Maintenance,CONTROL},diag_dispatch::{self,Launcher}};
use std::{net::UdpSocket,sync::{mpsc,atomic::{AtomicUsize,Ordering}}};
static MIN_FREE:AtomicUsize=AtomicUsize::new(usize::MAX);
unsafe extern "C" fn free_probe()->usize{let n=heap().0;// One exclusive worker updates this diagnostic; use load/store rather than Xtensa atomic-min lowering.
let old=MIN_FREE.load(Ordering::Relaxed);if n<old{MIN_FREE.store(n,Ordering::Relaxed);}n}
static REQUESTS:diag_dispatch::Requests=diag_dispatch::Requests::new();
struct Spawn;
impl Launcher for Spawn{
 type Job=MaintenanceGuard;type Sender=mpsc::SyncSender<Self::Job>;
 fn reserve(&mut self)->Result<Self::Job,()>{MaintenanceGuard::acquire(Maintenance::Benchmark).map_err(|_|())}
 fn spawn_empty(&mut self)->Result<Self::Sender,()>{let(tx,rx)=mpsc::sync_channel(1);std::thread::Builder::new().name("Dy71NetLab".into()).stack_size(16_384).spawn(move||{if let Ok(guard)=rx.recv(){worker(guard);REQUESTS.finished();}}).map_err(|_|())?;Ok(tx)}
 fn send(&mut self,tx:&Self::Sender,p:Self::Job)->Result<(),Self::Job>{tx.send(p).map_err(|e|e.0)}
 fn release_unissued(&mut self,p:Self::Job)->bool{drop(p);!CONTROL.lock().unwrap().quarantined()}
 fn publish(&mut self,tx:Self::Sender){drop(tx)}
}
pub fn start(){if !crate::streaming::diagnostic_trace_idle(){log::warn!("DY71_NET launch=busy");return}log::info!("DY71_NET launch={:?} lab_only=true frames=2 port=5535",diag_dispatch::launch(&REQUESTS,&mut Spawn));}
fn heap()->(usize,usize){unsafe{let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;(esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps))}}
#[inline(never)]fn worker(mut guard:MaintenanceGuard){
 // Read-only identity validation precedes Wi-Fi/native allocation and every FPGA write.
 let mut io=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0};
 use super::local::Bus;
 let identity=(||{Ok::<_,super::local::Error>((io.read(0)?,io.read(4)?,io.read(8)?,io.read(0xc)?))})();drop(io);
 if identity!=Ok((0x44593731,0x10000,15,1)){log::warn!("DY71_NET result=identity_or_not_fresh value={:?}",identity);return}
 let(mut wifi,host)=match crate::streaming::custom_lab_wifi(){Ok(x)=>x,Err(e)=>{log::warn!("DY71_NET wifi_failed={}",e);return}};
 // Bound allocation failures before mutation. The endpoint itself enforces its 128KiB arena.
 let before=heap();if before.0<114_688||before.1<24_576{log::warn!("DY71_NET result=heap_budget free={} largest={} no_FPGA_writes=true",before.0,before.1);let _=wifi.disconnect();let _=wifi.stop();return}
 let mut hud=match super::hud::Hud::new(98_304){Ok(h)=>h,Err(e)=>{log::warn!("DY71_NET result=allocation reason={:?}",e);return}};
 MIN_FREE.store(usize::MAX,Ordering::Relaxed);
 if hud.reserve_internal_heap(free_probe,8192).is_err(){log::warn!("DY71_NET result=reserve_configuration");return}
 let socket=match UdpSocket::bind((std::net::Ipv4Addr::UNSPECIFIED,network_wire::PORT)){Ok(s)=>s,Err(e)=>{log::warn!("DY71_NET bind_failed={}",e);return}};
 let mut source=match network_io::Input::new(socket,host){Ok(s)=>s,Err(e)=>{log::warn!("DY71_NET socket_failed={}",e);return}};
 log::info!("DY71_NET ready=true host={} port=5535 profile=DY71 frames=2 heap={:?} no_fps_claim=true",host,heap());
 let mut io=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0};
 let result=network_driver::run(&mut io,&mut hud,&mut source);let writes=io.writes;let reads=io.reads;drop(io);
 log::info!("DY71_NET result={:?} reads={} writes={} heap={:?} stack_low={} native_min_free={}",result.as_ref().map(|(r,_)|r),reads,writes,heap(),unsafe{esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())},MIN_FREE.load(Ordering::Relaxed));
 if result.is_err(){source.failed();}
 if writes!=0{
  if result.is_err(){CONTROL.lock().unwrap().quarantine();}
  log::info!("DY71_NET endpoint_retained=true lease_retained=true reconfigure_required=true success={}",result.is_ok());
  if result.is_ok(){source.held();}
  loop{std::hint::black_box(&guard);std::hint::black_box(&hud);std::hint::black_box(&wifi);std::thread::park();}
 }
 let _=wifi.disconnect();let _=wifi.stop();
}
