
use std::sync::atomic::{AtomicUsize, Ordering};
static MIN_FREE:AtomicUsize=AtomicUsize::new(usize::MAX);
mod esp_idf_svc {pub mod sys {
 use super::super::*;
 pub const MALLOC_CAP_INTERNAL:u32=0x800; pub const MALLOC_CAP_8BIT:u32=4;
 pub static FREE_CALLS:AtomicUsize=AtomicUsize::new(0);
 pub static LARGEST_CALLS:AtomicUsize=AtomicUsize::new(0);
 pub static FREE:AtomicUsize=AtomicUsize::new(120000);
 pub static LARGEST:AtomicUsize=AtomicUsize::new(32000);
 pub unsafe fn heap_caps_get_free_size(c:u32)->usize {assert_eq!(c,0x804);FREE_CALLS.fetch_add(1,Ordering::Relaxed);FREE.load(Ordering::Relaxed)}
 pub unsafe fn heap_caps_get_largest_free_block(c:u32)->usize {assert_eq!(c,0x804);LARGEST_CALLS.fetch_add(1,Ordering::Relaxed);LARGEST.load(Ordering::Relaxed)}
}}
unsafe extern "C" fn free_probe()->usize{let n=heap().0;// One exclusive worker updates this diagnostic; use load/store rather than Xtensa atomic-min lowering.
let old=MIN_FREE.load(Ordering::Relaxed);if n<old{MIN_FREE.store(n,Ordering::Relaxed);}n}
unsafe extern "C" fn largest_probe()->usize{heap().1}
fn heap()->(usize,usize){unsafe{let caps=(esp_idf_svc::sys::MALLOC_CAP_INTERNAL|esp_idf_svc::sys::MALLOC_CAP_8BIT)as u32;(esp_idf_svc::sys::heap_caps_get_free_size(caps),esp_idf_svc::sys::heap_caps_get_largest_free_block(caps))}}
const EXPECTED_NORMAL_LARGEST:usize=1;

#[test]fn reserve_samples_and_minimum_unchanged(){unsafe{
 esp_idf_svc::sys::FREE_CALLS.store(0,Ordering::Relaxed);
 esp_idf_svc::sys::LARGEST_CALLS.store(0,Ordering::Relaxed);
 MIN_FREE.store(usize::MAX,Ordering::Relaxed);
 for free in [120000usize,117552,8192,8191,0,35000] {
  esp_idf_svc::sys::FREE.store(free,Ordering::Relaxed);
  assert_eq!(free_probe(),free);
 }
 assert_eq!(MIN_FREE.load(Ordering::Relaxed),0);
 assert_eq!(esp_idf_svc::sys::FREE_CALLS.load(Ordering::Relaxed),6);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*6);
 assert_eq!(largest_probe(),32000);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*6+1);
}}
#[test]fn successful_allocation_callback_cadence(){unsafe{
 esp_idf_svc::sys::FREE_CALLS.store(0,Ordering::Relaxed);
 esp_idf_svc::sys::LARGEST_CALLS.store(0,Ordering::Relaxed);
 for _ in 0..2260 {let _=free_probe();let _=free_probe();}
 assert_eq!(esp_idf_svc::sys::FREE_CALLS.load(Ordering::Relaxed),4520);
 assert_eq!(esp_idf_svc::sys::LARGEST_CALLS.load(Ordering::Relaxed),EXPECTED_NORMAL_LARGEST*4520);
}}
