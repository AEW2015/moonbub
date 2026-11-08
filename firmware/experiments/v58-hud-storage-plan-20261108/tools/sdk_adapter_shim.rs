//! Host SDK shim ONLY; generated actual Adapter impl is included unchanged.
#![allow(dead_code)]
use std::sync::{Mutex,MutexGuard,atomic::{AtomicUsize,Ordering}};
mod esp_idf_svc{pub mod sys{pub unsafe fn esp_timer_get_time()->i64{0}}}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum FpgaSpiWordSize{Bits32}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub struct SpiCommand{word_size:FpgaSpiWordSize,byte_swap:bool,increment_address:bool}
pub const MAX_SPI_READ_CLOCK:u32=16_000_000;
pub struct Fpga{epoch:u32,fail:bool,last:Option<(u32,SpiCommand,usize,Vec<u8>)>}
impl Fpga{
 fn program_epoch(&self)->u32{self.epoch}
 fn read_u32(&mut self,_o:u32)->Result<u32,()>{if self.fail{Err(())}else{Ok(0)}}
 fn spi_read(&mut self,clock:Option<u32>,command:SpiCommand,o:u32,b:&mut[u8])->Result<(),()>{assert_eq!(clock,Some(MAX_SPI_READ_CLOCK));if self.fail{return Err(())}self.last=Some((o,command,b.as_ptr()as usize,b.to_vec()));for(i,v)in b.chunks_exact_mut(4).enumerate(){v.copy_from_slice(&(i as u32+1).to_be_bytes())}Ok(())}
 fn spi_write(&mut self,clock:Option<u32>,command:SpiCommand,o:u32,b:&[u8])->Result<(),()>{assert_eq!(clock,Some(MAX_SPI_READ_CLOCK));self.last=Some((o,command,b.as_ptr()as usize,b.to_vec()));if self.fail{Err(())}else{Ok(())}}
}
pub struct Device{fpga:Fpga}
static DEVICE:Mutex<Device>=Mutex::new(Device{fpga:Fpga{epoch:7,fail:false,last:None}});
static LOCK_CALLS:AtomicUsize=AtomicUsize::new(0);
impl Device{fn try_lock()->Option<MutexGuard<'static,Device>>{LOCK_CALLS.fetch_add(1,Ordering::SeqCst);DEVICE.try_lock().ok()}}
pub struct MaintenanceGuard{starts:usize}
impl MaintenanceGuard{fn side_effects_begin(&mut self){self.starts+=1;}}
mod cu66{
 pub mod stb1{include!("stb1-sdk-include.rs");}
 pub mod local{include!("local-trait-sdk-include.rs");}
 pub mod adapter{
  use super::local::{Bus,Error};use crate::{esp_idf_svc,Device,MaintenanceGuard,FpgaSpiWordSize,SpiCommand,MAX_SPI_READ_CLOCK};
  pub struct Adapter<'a>{pub guard:&'a mut MaintenanceGuard,pub epoch:Option<u32>,pub reads:u32,pub writes:u32,pub transactions:u32}
  include!("actual-adapter-sdk-include.rs");
 }
}
use cu66::{adapter::Adapter,local::{Bus,Error}};
static ALIGNED:cu66::stb1::PacketBuffer=cu66::stb1::PacketBuffer::new();
fn raw4()-> &'static[u8]{&ALIGNED.0[..4]}
fn reset(){let mut d=DEVICE.lock().unwrap();d.fpga.epoch=7;d.fpga.fail=false;d.fpga.last=None;LOCK_CALLS.store(0,Ordering::SeqCst);}
#[test]fn actual_bounds_fail_before_lock_or_spi(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(7),reads:0,writes:0,transactions:0};assert_eq!(a.staging_read_words(0x708,&mut[0;7]),Err(Error::Bounds));assert_eq!(a.staging_descriptor(&[1,0,1,4,1]),Err(Error::Bounds));assert_eq!(a.staging_payload_be(0x100,&[0;4]),Err(Error::Bounds));assert_eq!(a.staging_payload_be(0xc00,&[0;3]),Err(Error::Bounds));assert_eq!(LOCK_CALLS.load(Ordering::SeqCst),0);assert_eq!(a.transactions,0);assert_eq!(a.guard.starts,0);}
#[test]fn actual_raw_payload_borrows_same_buffer_no_bounce(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(7),reads:0,writes:0,transactions:0};let mut storage=cu66::stb1::PacketBuffer::new();storage.0.fill(0x61);let bytes=&storage.0;assert_eq!((bytes.as_ptr()as usize)&3,0);assert_eq!(a.staging_payload_be(0xc00,bytes),Ok(1024));let d=DEVICE.lock().unwrap();let(o,c,ptr,v)=d.fpga.last.as_ref().unwrap();assert_eq!(*o,0xe0000c00);assert_eq!(*ptr,bytes.as_ptr()as usize);assert_eq!(*c,SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true});assert_eq!(v.as_slice(),bytes.as_slice());assert_eq!((a.writes,a.transactions,a.guard.starts),(256,1,1));}
#[test]fn actual_descriptor_is_one_be_20byte_transaction(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(7),reads:0,writes:0,transactions:0};a.staging_descriptor(&[1,2,4,1024,9]).unwrap();let d=DEVICE.lock().unwrap();let(o,_,_,v)=d.fpga.last.as_ref().unwrap();assert_eq!(*o,0xe0000720);assert_eq!(v.len(),20);assert_eq!(&v[0..4],&1u32.to_be_bytes());assert_eq!(&v[16..20],&9u32.to_be_bytes());assert_eq!(a.transactions,1);}
#[test]fn actual_epoch_mismatch_never_writes(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(6),reads:0,writes:0,transactions:0};assert_eq!(a.staging_payload_be(0xc00,raw4()),Err(Error::Epoch));assert_eq!(a.staging_descriptor(&[1,0,0,4,1]),Err(Error::Epoch));assert_eq!(a.guard.starts,0);assert!(DEVICE.lock().unwrap().fpga.last.is_none());}
#[test]fn actual_contended_lock_never_starts_side_effects(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(7),reads:0,writes:0,transactions:0};let held=DEVICE.lock().unwrap();assert_eq!(a.staging_payload_be(0xc00,raw4()),Err(Error::Contended));assert_eq!(a.staging_descriptor(&[1,0,0,4,1]),Err(Error::Contended));assert_eq!(a.guard.starts,0);drop(held);}
#[test]fn actual_spi_failure_remains_ambiguous_and_marks_guard(){reset();DEVICE.lock().unwrap().fpga.fail=true;let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:Some(7),reads:0,writes:0,transactions:0};assert_eq!(a.staging_payload_be(0xc00,raw4()),Err(Error::Io));assert_eq!((a.guard.starts,a.transactions),(1,1));}
#[test]fn actual_read_span_be_decode_and_epoch_capture(){reset();let mut guard=MaintenanceGuard{starts:0};let mut a=Adapter{guard:&mut guard,epoch:None,reads:0,writes:0,transactions:0};let mut values=[0;6];assert_eq!(a.staging_read_words(0x708,&mut values),Ok(6));assert_eq!(values,[1,2,3,4,5,6]);assert_eq!(a.epoch,Some(7));assert_eq!((a.reads,a.transactions,a.guard.starts),(6,1,0));}
