//! Read-only sampled diagnostics. Every Device-independent observation is logged
//! after its own short getter returns; pages are not an atomic cross-task view.
use crate::{diag_pages::{self as pages,Context,Line,QueueSample},streaming};
use core::fmt;
use std::sync::atomic::{AtomicU32,Ordering};
static CAPTURE:AtomicU32=AtomicU32::new(0);
fn context()->Context{Context{capture:CAPTURE.fetch_add(1,Ordering::Relaxed).wrapping_add(1),generation:streaming::diagnostic_generation(),epoch:streaming::presentation_epoch().sequence,frame:0}}
#[inline(never)]
fn emit(line:Result<Line,fmt::Error>){match line{Ok(line)=>log::info!(target:"diag","{}",line.as_str()),Err(_)=>log::warn!(target:"diag","USB_D24 v=1 p=format_error")}}
fn end(c:Context){emit(pages::boundary(c,true,streaming::diagnostic_generation(),streaming::presentation_epoch().sequence));}
#[inline(never)]
pub fn runtime(){
 let c=context();
 unsafe{
  let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;
  let reason=esp_idf_svc::sys::esp_reset_reason();let up=esp_idf_svc::sys::esp_timer_get_time().max(0)as u64;
  emit(pages::runtime(c,0,reason,up,0,0,0));emit(pages::runtime(c,1,reason,up,0,0,0));
  emit(pages::runtime(c,2,reason,up,esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps),esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())));
  let desc=esp_idf_svc::sys::esp_app_get_description();
  if let Some(desc)=desc.as_ref(){
   for p in 0..3{emit(pages::app(c,p,&desc.project_name,&desc.version,&desc.idf_ver,&desc.date,&desc.time,&desc.app_elf_sha256));}
  }else{emit(pages::page(c,"app",format_args!("available=false")));}
 }
 end(c);
}
#[inline(never)]
fn log_frame(mut c:Context,completed:bool,t:&streaming::telemetry::FrameTrace){c.frame=t.id;for p in 0..7{emit(pages::frame(c,completed,p,t));}}
#[inline(never)]
pub fn video(){
 let c=context();emit(pages::boundary(c,false,0,0));
 let traces=streaming::trace();log_frame(c,true,&traces.completed);log_frame(c,false,&traces.dropped);
 let(d,timing,queued,high)=streaming::queue_trace();
 let q=QueueSample{capacity:d.capacity,count:d.count,first_id:d.first_id,first_offset:d.first_offset,first_valid:d.first_valid,first_since_consumer_us:d.first_since_consumer_us,first_since_producer_us:d.first_since_producer_us,first_consumer_busy:d.first_consumer_busy,first_queued:d.first_queued,socket_errors:d.socket_errors,producer_stack:d.producer_stack_low_water,consumer_stack:d.consumer_stack_low_water,producer_priority:d.producer_priority,consumer_priority:d.consumer_priority,queued,high};
 let qctx=Context{frame:d.first_id,..c};for p in 0..4{emit(pages::queue(qctx,p,q));}for p in 0..2{emit(pages::producer(c,p,timing));}
 let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;
 unsafe{emit(pages::runtime(c,2,0,0,esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps),esp_idf_svc::sys::uxTaskGetStackHighWaterMark(std::ptr::null_mut())));}
 end(c);
}
