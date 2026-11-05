#[path="../handheld/src/streaming/telemetry.rs"] pub mod telemetry;
mod streaming {pub use crate::telemetry;}
#[path="../handheld/src/diag_pages.rs"] mod pages;
use std::{alloc::{GlobalAlloc,Layout,System},cell::Cell,sync::atomic::{AtomicUsize,Ordering}};
struct Counter;
thread_local! {static TRACK:Cell<bool>=const{Cell::new(false)};}
static ALLOCATIONS:AtomicUsize=AtomicUsize::new(0);
unsafe impl GlobalAlloc for Counter {
 unsafe fn alloc(&self,layout:Layout)->*mut u8{if TRACK.try_with(|t|t.get()).unwrap_or(false){ALLOCATIONS.fetch_add(1,Ordering::Relaxed);}unsafe{System.alloc(layout)}}
 unsafe fn dealloc(&self,p:*mut u8,layout:Layout){unsafe{System.dealloc(p,layout)}}
 unsafe fn realloc(&self,p:*mut u8,layout:Layout,size:usize)->*mut u8{if TRACK.try_with(|t|t.get()).unwrap_or(false){ALLOCATIONS.fetch_add(1,Ordering::Relaxed);}unsafe{System.realloc(p,layout,size)}}
}
#[global_allocator] static ALLOC:Counter=Counter;
fn context()->pages::Context{pages::Context{capture:u32::MAX,generation:u32::MAX,epoch:u32::MAX,frame:u32::MAX}}
fn frame()->telemetry::FrameTrace{telemetry::FrameTrace{valid:true,id:u32::MAX,started_us:u64::MAX,last_packet_us:u64::MAX,finished_us:u64::MAX,packets:u32::MAX,bytes:u32::MAX,max_interarrival_us:u64::MAX,min_interarrival_us:u64::MAX,max_queue_residence_us:u64::MAX,max_consumer_processing_us:u64::MAX,last_consumer_us:u64::MAX,max_consumer_gap_us:u64::MAX,begin_us:u64::MAX,qspi_calls:u32::MAX,qspi_total_us:u64::MAX,qspi_max_us:u64::MAX,lock_total_us:u64::MAX,lock_max_us:u64::MAX,min_frame_remaining:u32::MAX,gap_valid:true,expected_offset:u32::MAX,observed_offset:u32::MAX}}
fn queue()->pages::QueueSample{pages::QueueSample{capacity:u32::MAX,count:u32::MAX,first_id:u32::MAX,first_offset:u32::MAX,first_valid:true,first_since_consumer_us:u32::MAX,first_since_producer_us:u32::MAX,first_consumer_busy:true,first_queued:u32::MAX,socket_errors:u32::MAX,producer_stack:u32::MAX,consumer_stack:u32::MAX,producer_priority:u32::MAX,consumer_priority:u32::MAX,queued:u32::MAX,high:u32::MAX}}
#[test]fn production_pages_fit_worst_widths_without_heap(){
 let c=context();let t=frame();let q=queue();let prod=telemetry::ProducerTiming{datagrams:u32::MAX,last_us:u64::MAX,min_gap_us:u64::MAX,max_gap_us:u64::MAX,gaps_below_1000us:u32::MAX};
 let text=[b'X' as core::ffi::c_char;32];let date=[b'Y' as core::ffi::c_char;16];let hash=[255;32];
 let mut maximum=0;let mut count=0;
 let mut check=|line:pages::Line|{let s=line.as_str();assert!(s.is_ascii()&&!s.contains(['\r','\n']));assert!(s.starts_with("USB_D24 v=1 c=4294967295 g=4294967295 e=4294967295 f=4294967295 p="));assert!(s.len()+pages::LOG_FRAMING_RESERVE<=256);maximum=maximum.max(s.len());count+=1;};
 TRACK.with(|x|x.set(true));let before=ALLOCATIONS.load(Ordering::Relaxed);
 for completed in [false,true]{for i in 0..7{check(pages::frame(c,completed,i,&t).unwrap());}}
 for i in 0..4{check(pages::queue(c,i,q).unwrap());}
 for i in 0..2{check(pages::producer(c,i,prod).unwrap());}
 for i in 0..3{check(pages::runtime(c,i,u32::MAX,u64::MAX,usize::MAX,usize::MAX,u32::MAX).unwrap());check(pages::app(c,i,&text,&text,&text,&date,&date,&hash).unwrap());}
 check(pages::boundary(c,false,0,0).unwrap());check(pages::boundary(c,true,u32::MAX,u32::MAX).unwrap());
 let after=ALLOCATIONS.load(Ordering::Relaxed);TRACK.with(|x|x.set(false));
 assert_eq!(before,after);assert_eq!(count,28);println!("BOUNDED_PAGES count={} max_payload={} framing={} max_line={} heap_allocations={}",count,maximum,pages::LOG_FRAMING_RESERVE,maximum+pages::LOG_FRAMING_RESERVE,after-before);
}
#[test]fn no_unbounded_c_string_or_control_character_injection(){
 let project=[b'A' as core::ffi::c_char,10,13,0,b'Z' as core::ffi::c_char];let zeros=[0;32];
 let line=pages::app(context(),0,&project,&project,&zeros,&zeros,&zeros,&[0;32]).unwrap();
 assert!(line.as_str().ends_with("project=A__ version=A__"));
 let non_ascii=[255u8];let line=pages::page(context(),"text",format_args!("s={}",pages::Text(&non_ascii))).unwrap();assert!(line.as_str().ends_with("s=_"));
}
#[test]fn overflow_and_non_ascii_are_rejected_without_truncation(){
 assert!(pages::page(context(),"overflow",format_args!("{:0300}",1)).is_err());
 assert!(pages::page(context(),"newline",format_args!("a\nb")).is_err());
 assert!(pages::page(context(),"unicode",format_args!("é")).is_err());
}
#[test]fn full_identity_and_u64_values_are_not_narrowed(){
 let line=pages::frame(context(),true,5,&frame()).unwrap();
 assert!(line.as_str().contains("qspi_max=18446744073709551615 lock_total=18446744073709551615 lock_max=18446744073709551615"));
 let line=pages::app(context(),2,&[],&[],&[],&[],&[],&[0xab;32]).unwrap();assert!(line.as_str().ends_with("abababababababababababababababababababababababababababababababab"));
}
