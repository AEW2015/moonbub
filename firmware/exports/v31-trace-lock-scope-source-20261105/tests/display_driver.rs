//! Production frontend exercised with fake MMIO/clock/log sink; no devices.
#![allow(dead_code)]
extern crate self as log;
extern crate self as esp_idf_svc;
use std::sync::{Mutex,OnceLock,atomic::{AtomicI64,Ordering}};
#[macro_export]macro_rules!info{($($arg:tt)*)=>{crate::record(format!($($arg)*))}}
static CLOCK:AtomicI64=AtomicI64::new(0);
pub mod sys{pub unsafe fn esp_timer_get_time()->i64{crate::CLOCK.load(std::sync::atomic::Ordering::Relaxed)}}
#[path="../handheld/src/margin.rs"]mod margin;
#[path="../handheld/src/timing.rs"]mod timing;
#[path="../handheld/src/timing_line.rs"]mod timing_line;
#[path="../handheld/src/margin_usb.rs"]mod margin_usb;
static TEST:Mutex<()>=Mutex::new(());
static LOG:Mutex<Vec<String>>=Mutex::new(Vec::new());
fn record(message:String){assert!(device::state().try_lock().is_ok(),"logging while Device held");LOG.lock().unwrap().push(message);}
pub mod device{
 use super::*;use std::{marker::PhantomData,sync::MutexGuard};
 pub struct Device<'a>{pub fpga:Fake,life:PhantomData<&'a ()>}
 pub struct Fake{pub build:u32,pub margin:u32,pub margin_seq:u8,pub shadow:timing::Timing,pub applied:timing::Timing,pub preset:u8,pub seq:u8,pub writes:Vec<(u32,u32)>}
 impl Default for Fake{fn default()->Self{Self{build:margin::BUILD,margin:20,margin_seq:1,shadow:timing::Timing::current(),applied:timing::Timing::current(),preset:0,seq:1,writes:vec![]}}}
 pub fn state()->&'static Mutex<Device<'static>>{static STATE:OnceLock<Mutex<Device<'static>>>=OnceLock::new();STATE.get_or_init(||Mutex::new(Device{fpga:Fake::default(),life:PhantomData}))}
 impl<'a> Device<'a>{pub fn try_lock()->Option<MutexGuard<'static,Device<'static>>>{state().try_lock().ok()}}
 impl Fake{
  pub fn read_u32(&mut self,address:u32)->Result<u32,()>{Ok(match address-margin::BASE{0=>0x4d425631,4=>0x10000,0x184=>self.build,0x084=>self.margin,0x088=>self.margin|0x700|((self.margin_seq as u32)<<24),0x08c=>margin::MAGIC,0x090=>timing::MAGIC,0x094=>self.shadow.horizontal,0x098=>self.shadow.vertical,0x09c=>timing::SCHEMA,0x0a0=>self.applied.horizontal,0x0a4=>self.applied.vertical,0x0a8=>self.preset as u32|0x700|((self.seq as u32)<<24),off=>panic!("read{off:x}")})}
  pub fn write_u32(&mut self,address:u32,value:u32)->Result<(),()>{let off=address-margin::BASE;self.writes.push((off,value));match off{0x084=>{self.margin=value;self.margin_seq=self.margin_seq.wrapping_add(1)},0x094=>self.shadow.horizontal=value,0x098=>self.shadow.vertical=value,0x09c=>{self.shadow=match value{0=>timing::Timing::current(),1=>timing::Timing::official(),2=>self.shadow,_=>panic!()};self.applied=self.shadow;self.preset=value as u8;self.seq=self.seq.wrapping_add(1)},_=>panic!("write{off:x}")}Ok(())}
 }
}
fn reset()->margin_usb::Driver{CLOCK.store(0,Ordering::Relaxed);device::state().lock().unwrap().fpga=device::Fake::default();LOG.lock().unwrap().clear();margin_usb::Driver::new()}
fn drain(driver:&mut margin_usb::Driver){for _ in 0..20{driver.tick();}}
#[test]fn marker_is_independent_of_discovery_and_h_queries_both(){let _lock=TEST.lock().unwrap();let mut driver=reset();device::state().lock().unwrap().fpga.build=0;assert!(driver.command(b'h'));drain(&mut driver);let logs=LOG.lock().unwrap();assert!(logs.iter().any(|s|s=="USB_TRACE display_control abi=1 local_loops=1"));assert!(logs.iter().any(|s|s.contains("margin key=h")));assert!(logs.iter().any(|s|s.contains("timing key=h")));assert!(device::state().lock().unwrap().fpga.writes.is_empty());}
#[test]fn known48_fails_calibration_controls_closed_but_advertises_local_capability(){let _lock=TEST.lock().unwrap();let mut driver=reset();device::state().lock().unwrap().fpga.build=0x4d424f48;for key in [b'h',b'f',b'g',b'=']{assert!(driver.command(key));drain(&mut driver);}for &byte in b"T4,119,2,4,2,3\n"{assert!(driver.command(byte));}drain(&mut driver);assert!(device::state().lock().unwrap().fpga.writes.is_empty());let logs=LOG.lock().unwrap();assert!(logs.iter().any(|s|s.contains("abi=1 local_loops=1")));assert!(logs.iter().filter(|s|s.contains("result=Identity")).count()>=5);}
#[test]fn real_frontend_consumes_malformed_body_including_legacy_commands(){let _lock=TEST.lock().unwrap();let mut driver=reset();for &byte in b"T4,6,8,c,x,h,f,g\n"{assert!(driver.command(byte));}drain(&mut driver);assert!(device::state().lock().unwrap().fpga.writes.is_empty());assert!(!LOG.lock().unwrap().iter().any(|s|s.contains("display_control abi=")));assert!(!driver.command(b'8'));}
#[test]fn real_frontend_timeout_drain_and_canonical_custom_apply(){let _lock=TEST.lock().unwrap();let mut driver=reset();assert!(driver.command(b'T'));assert!(driver.command(b'4'));CLOCK.store(1_500_000,Ordering::Relaxed);driver.tick();for &byte in b"468cxfgh\n"{assert!(driver.command(byte));}assert!(device::state().lock().unwrap().fpga.writes.is_empty());for &byte in b"T4,119,2,4,2,3\n"{assert!(driver.command(byte));}drain(&mut driver);let d=device::state().lock().unwrap();assert_eq!(d.fpga.applied,timing::Timing::official());assert_eq!(d.fpga.writes,[(0x94,0x0021dc04),(0x98,0x00300804),(0x9c,2)]);}
#[test]fn presets_and_margin_keep_legacy_keys_and_static_driver_storage(){let _lock=TEST.lock().unwrap();let mut driver=reset();for key in [b'f',b'g',b'=',b'|']{assert!(driver.command(key));drain(&mut driver);}assert_eq!(device::state().lock().unwrap().fpga.margin,20);assert_eq!(device::state().lock().unwrap().fpga.applied,timing::Timing::current());for key in b"cxvml o468npzZqrstABLRUDH"{if *key!=b' '{assert!(!driver.command(*key));}}assert_eq!(std::mem::size_of::<margin_usb::Driver>(),0);}

#[test]fn new_audio50_retains_display_controls_and_unknown_build_rejected(){let _lock=TEST.lock().unwrap();let mut driver=reset();device::state().lock().unwrap().fpga.build=0x4d424f50;for key in[b'=',b'f',b'g']{assert!(driver.command(key));drain(&mut driver);}let mut d=device::state().lock().unwrap();assert_eq!(d.fpga.margin,40);assert_eq!(d.fpga.applied,timing::Timing::current());assert_eq!(d.fpga.writes.len(),3);d.fpga.build=0x4d424f51;d.fpga.writes.clear();drop(d);for key in[b'=',b'f',b'g']{assert!(driver.command(key));drain(&mut driver);}assert!(device::state().lock().unwrap().fpga.writes.is_empty());}
