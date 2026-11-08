#![allow(dead_code)]
#[path="../handheld/src/cu66/framing.rs"]mod framing;
#[path="../handheld/src/cu66/hud.rs"]mod hud;
#[path="../handheld/src/cu66/local.rs"]mod local;
#[path="../handheld/src/cu66/stb_failure.rs"]mod stb_failure;
use local::{Bus,Error};use stb_failure::{Context,Snapshot,ALL};
use std::{alloc::{GlobalAlloc,Layout,System},cell::Cell,fmt::{self,Write}};
thread_local!{static TRACK:Cell<bool>=const{Cell::new(false)};static ALLOCATIONS:Cell<usize>=const{Cell::new(0)};}
struct Counter;
#[global_allocator]static ALLOCATOR:Counter=Counter;
unsafe impl GlobalAlloc for Counter{
 unsafe fn alloc(&self,l:Layout)->*mut u8{TRACK.with(|t|if t.get(){ALLOCATIONS.with(|n|n.set(n.get()+1))});System.alloc(l)}
 unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{TRACK.with(|t|if t.get(){ALLOCATIONS.with(|v|v.set(v.get()+1))});System.realloc(p,l,n)}
}
struct Mock{at:u64,delay:u64,errors:[Option<Error>;13],calls:usize,addresses:[u32;13],writes:usize,yields:usize}
impl Mock{fn fresh()->Self{Self{at:1,delay:1,errors:[None;13],calls:0,addresses:[0;13],writes:0,yields:0}}}
impl Bus for Mock{
 fn read(&mut self,o:u32)->Result<u32,Error>{assert!((0x700..=0x730).contains(&o)&&o&3==0);self.addresses[self.calls]=o;self.calls+=1;self.at=self.at.saturating_add(self.delay);let i=((o-0x700)/4)as usize;if let Some(e)=self.errors[i]{Err(e)}else{Ok(0xabc00000+i as u32)}}
 fn write(&mut self,_o:u32,_v:u32)->Result<(),Error>{self.writes+=1;panic!("diagnostic attempted mutation")}
 fn now(&self)->u64{self.at}fn yield_now(&mut self){self.yields+=1;panic!("diagnostic retried/yielded")}
}
fn context()->Context{Context{active:true,ordinal:17,frame:299,generation:0x1234567887654321,phase:2,progress_at_us:1234,stored_prefix:1024,..Context::default()}.with_identity(Some((0x1111222233334444,1794000000123456,300,299)))}
struct Lines{bytes:[[u8;192];4],lengths:[usize;4],next:usize}
impl Lines{fn new()->Self{Self{bytes:[[0;192];4],lengths:[0;4],next:0}}fn push(&mut self,args:fmt::Arguments<'_>){assert!(self.next<4);let mut output=Fixed{bytes:&mut self.bytes[self.next],used:0};output.write_fmt(args).unwrap();self.lengths[self.next]=output.used;self.next+=1;}}
struct Fixed<'a>{bytes:&'a mut[u8],used:usize}
impl Write for Fixed<'_>{fn write_str(&mut self,s:&str)->fmt::Result{if self.used+s.len()>self.bytes.len(){return Err(fmt::Error)}self.bytes[self.used..self.used+s.len()].copy_from_slice(s.as_bytes());self.used+=s.len();Ok(())}}
#[test]fn exactly13_read_attempts_in_bounds_no_write_retry_or_yield(){let mut b=Mock::fresh();let s=Snapshot::read_once(&mut b,context());assert_eq!(b.calls,13);for(i,o)in b.addresses.iter().enumerate(){assert_eq!(*o,0x700+i as u32*4)}assert_eq!((b.writes,b.yields),(0,0));assert_eq!((s.attempted,s.valid,s.result_flags),(ALL,ALL,3));assert_eq!((s.first_error_index,s.first_error_code),(255,0));assert_eq!(s.context,context());assert_eq!((s.start_us,s.end_us),(1,14));}
#[test]fn contention_io_epoch_and_other_errors_are_explicit_without_retry(){let mut b=Mock::fresh();b.errors[0]=Some(Error::Contended);b.errors[3]=Some(Error::Io);b.errors[8]=Some(Error::Epoch);b.errors[12]=Some(Error::Bounds);let s=Snapshot::read_once(&mut b,context());assert_eq!(b.calls,13);assert_eq!(s.valid,ALL&!((1<<0)|(1<<3)|(1<<8)|(1<<12)));assert_eq!((s.first_error_index,s.first_error_code),(0,1));assert_eq!(s.result_flags,9);for i in[0,3,8,12]{assert_eq!(s.values[i],0)}assert_eq!((b.writes,b.yields),(0,0));}
#[test]fn epoch_is_recorded_as_first_reason(){let mut b=Mock::fresh();b.errors[2]=Some(Error::Epoch);let s=Snapshot::read_once(&mut b,context());assert_eq!((s.first_error_index,s.first_error_code),(2,2));assert_ne!(s.result_flags&8,0);}
#[test]fn precall_budget_stops_new_reads_but_is_not_hard_spi_deadline(){let mut b=Mock::fresh();b.delay=25_000;let s=Snapshot::read_once(&mut b,context());assert_eq!(b.calls,1);assert_eq!((s.attempted,s.valid,s.result_flags),(1,1,4));assert_eq!(s.end_us-s.start_us,25_000);assert!(s.end_us-s.start_us>stb_failure::SAMPLE_BUDGET_US);let mut b=Mock::fresh();b.delay=10_000;let s=Snapshot::read_once(&mut b,context());assert_eq!(b.calls,2);assert_eq!((s.attempted,s.valid),(3,3));}
#[test]fn success_path_never_reads_builds_context_or_emits(){let mut b=Mock::fresh();let s=stb_failure::capture(false,&mut b,||panic!("success path built context"));let mut logs=0;if let Some(s)=s{s.lines(|_|logs+=1)}assert_eq!((b.calls,b.writes,b.yields,logs),(0,0,0,0));}
#[test]fn checksum_binds_every_context_field_and_all_values(){let mut b=Mock::fresh();let s=Snapshot::read_once(&mut b,context());let crc=s.checksum();let mut alternatives=[s;12];alternatives[0].context.active=false;alternatives[1].context.ordinal^=1;alternatives[2].context.frame^=1;alternatives[3].context.generation^=1;alternatives[4].context.phase^=1;alternatives[5].context.progress_at_us^=1;alternatives[6].context.stored_prefix^=1;alternatives[7].context.identity_valid=false;alternatives[8].context.session^=1;alternatives[9].context.capture_us^=1;alternatives[10].context.identity_frame^=1;alternatives[11].context.identity_reference^=1;for x in alternatives{assert_ne!(x.checksum(),crc)}for i in 0..13{let mut x=s;x.values[i]^=1;assert_ne!(x.checksum(),crc)}let mut x=s;x.valid^=1;assert_ne!(x.checksum(),crc);x=s;x.start_us^=1;assert_ne!(x.checksum(),crc);x=s;x.end_us^=1;assert_ne!(x.checksum(),crc);x=s;x.first_error_code=4;assert_ne!(x.checksum(),crc);}
#[test]fn context_without_current_identity_stays_explicitly_unbound(){let c=context().with_identity(None);assert!(!c.identity_valid);assert_eq!((c.session,c.capture_us,c.identity_frame,c.identity_reference),(0,0,0,0));assert_eq!(c.frame,299);}
fn max_snapshot()->Snapshot{Snapshot{start_us:u64::MAX,end_us:u64::MAX,attempted:ALL,valid:ALL,result_flags:3,first_error_index:255,first_error_code:0,values:[u32::MAX;13],context:Context{active:true,ordinal:u32::MAX,frame:u32::MAX,generation:u64::MAX,phase:u8::MAX,progress_at_us:u64::MAX,stored_prefix:u32::MAX,..Context::default()}.with_identity(Some((u64::MAX,u64::MAX,u32::MAX,u32::MAX)))}}
#[test]fn four_records_maximum_integer_payloads_at_most192_bytes(){let s=max_snapshot();let mut lines=Lines::new();s.lines(|a|lines.push(a));assert_eq!(lines.next,4);assert_eq!(lines.lengths,[119,186,104,95]);for n in lines.lengths{assert!(n<=192)}assert!(core::mem::size_of::<Snapshot>()<=160);println!("HOST_STB_FAILURE_BYTES {}",core::mem::size_of::<Snapshot>());}
#[test]fn zero_allocations_during_failure_capture_crc_and_four_logs(){let mut b=Mock::fresh();let mut lines=Lines::new();ALLOCATIONS.with(|n|n.set(0));TRACK.with(|t|t.set(true));let s=stb_failure::capture(true,&mut b,context).unwrap();let _=s.checksum();s.lines(|a|lines.push(a));TRACK.with(|t|t.set(false));assert_eq!(ALLOCATIONS.with(Cell::get),0);assert_eq!(lines.next,4);}
#[test]fn emit_fixture_for_host_decoder(){let s=max_snapshot();s.lines(|a|println!("{}",a));let mut b=Mock::fresh();b.errors[3]=Some(Error::Contended);b.errors[7]=Some(Error::Epoch);let s=Snapshot::read_once(&mut b,context());s.lines(|a|println!("{}",a));}
