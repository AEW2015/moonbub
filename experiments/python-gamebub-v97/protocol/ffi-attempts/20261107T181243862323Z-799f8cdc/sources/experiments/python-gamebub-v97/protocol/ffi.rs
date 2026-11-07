//! Native-only C ABI around the identical portable Gateway. Valid-pointer ABI,
//! null/length guards and unwind containment; not an ESP32/RTOS timing emulator.
#[path="../../../firmware/handheld/src/streaming/protocol97.rs"] mod p;
use std::{ffi::c_void,panic::{catch_unwind,AssertUnwindSafe}};
#[repr(C)]
#[derive(Clone,Copy)]
pub struct V97Transfer { token:u64, slot:u32, logical_len:u32, storage_len:u32, reserved:u32 }
#[repr(C)]
#[derive(Clone,Copy)]
pub struct V97Frame { epoch:u32, fid:u32, length:u32, crc:u32, core_generation:u32, reserved:u32, capture_us:u64 }
#[repr(C)]
pub struct V97Chunk { frame:V97Frame, transfer:V97Transfer, index:u32, offset:u32, crc_complete:u32, reserved:u32 }
fn error(e:p::Error)->i32 { use p::Error::*; match e {WouldBlock=>1,DrainRequired=>2,Header=>-10,Format=>-11,Bounds=>-12,Capability=>-13,Epoch=>-14,Core=>-15,Sequence=>-16,Integrity=>-17,Completion=>-18} }
fn guard(f:impl FnOnce()->Result<(),i32>)->i32 {match catch_unwind(AssertUnwindSafe(f)){Ok(Ok(()))=>0,Ok(Err(e))=>e,Err(_)=>-99}}
unsafe fn gateway<'a>(h:*mut c_void)->Result<&'a mut p::Gateway,i32> {if h.is_null(){Err(-1)}else{Ok(&mut *(h as *mut p::Gateway))}}
unsafe fn input<'a>(b:*const u8,n:usize,cap:usize)->Result<&'a [u8],i32>{if n>cap{return Err(-12)}if n==0{return Ok(&[])}if b.is_null(){Err(-1)}else{Ok(std::slice::from_raw_parts(b,n))}}
unsafe fn transfer(t:*const V97Transfer)->Result<p::Transfer,i32>{let t=t.as_ref().ok_or(-1)?;if t.reserved!=0{return Err(-11)}Ok(p::Transfer{token:t.token,slot:t.slot as usize,logical_len:t.logical_len as usize,storage_len:t.storage_len as usize})}
fn frame(f:p::Frame,core:u32)->V97Frame{V97Frame{epoch:f.epoch,fid:f.id,length:f.length,crc:f.crc,core_generation:core,reserved:0,capture_us:f.capture_us}}
#[no_mangle] pub extern "C" fn v97_create(profile:u32,core:u32)->*mut c_void{if core==0{return std::ptr::null_mut()}catch_unwind(||Box::into_raw(Box::new(p::Gateway::new(p::SinkConfig{opaque_profile:if profile==0{None}else{Some(profile)}},core))) as *mut c_void).unwrap_or(std::ptr::null_mut())}
#[no_mangle] pub unsafe extern "C" fn v97_destroy(h:*mut c_void)->i32{guard(||{let g=gateway(h)?;if g.inflight()!=0{return Err(2)}drop(Box::from_raw(h as *mut p::Gateway));Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_setup(h:*mut c_void,b:*const u8,n:usize,ack:*mut u8)->i32{guard(||{if ack.is_null(){return Err(-1)}let a=gateway(h)?.setup(input(b,n,40)?).map_err(error)?;std::ptr::copy_nonoverlapping(a.as_ptr(),ack,40);Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_observe_free(h:*mut c_void,epoch:u32,core:u32,free:u32)->i32{guard(||gateway(h)?.observe_fifo_free(epoch,core,free).map(|_|()).map_err(error))}
#[no_mangle] pub unsafe extern "C" fn v97_receive(h:*mut c_void,b:*const u8,n:usize,out:*mut V97Chunk)->i32{guard(||{if out.is_null(){return Err(-1)}let g=gateway(h)?;if n>p::HEADER+p::START_LEN+p::MAX_PAYLOAD{g.abort_frame();return Err(-12)}let bytes=input(b,n,p::HEADER+p::START_LEN+p::MAX_PAYLOAD)?;let (c,t)=g.receive(bytes).map_err(error)?;*out=V97Chunk{frame:frame(c.frame,g.session().ok_or(-14)?.core_generation),transfer:V97Transfer{token:t.token,slot:t.slot as u32,logical_len:t.logical_len as u32,storage_len:t.storage_len as u32,reserved:0},index:c.index as u32,offset:c.offset,crc_complete:c.crc_complete as u32,reserved:0};Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_transfer_bytes(h:*mut c_void,t:*const V97Transfer)->*const u8{catch_unwind(AssertUnwindSafe(||{let g=gateway(h).ok()?;g.transfer_bytes(transfer(t).ok()?).ok().map(|b|b.as_ptr())})).ok().flatten().unwrap_or(std::ptr::null())}
#[no_mangle] pub unsafe extern "C" fn v97_staging_storage(h:*mut c_void,t:*const V97Transfer)->*const u8{catch_unwind(AssertUnwindSafe(||{let g=gateway(h).ok()?;g.staging_storage(transfer(t).ok()?).ok().map(|b|b.as_ptr())})).ok().flatten().unwrap_or(std::ptr::null())}
#[no_mangle] pub unsafe extern "C" fn v97_issue(h:*mut c_void,t:*const V97Transfer)->i32{guard(||gateway(h)?.issue(transfer(t)?).map_err(error))}
#[no_mangle] pub unsafe extern "C" fn v97_complete(h:*mut c_void,token:u64,success:i32)->i32{guard(||gateway(h)?.complete(token,success!=0).map_err(error))}
#[no_mangle] pub unsafe extern "C" fn v97_take_commit(h:*mut c_void,out:*mut V97Frame)->i32{guard(||{if out.is_null(){return Err(-1)}let g=gateway(h)?;let f=g.take_commit().ok_or(1)?;*out=frame(f,g.session().ok_or(-14)?.core_generation);Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_commit_complete(h:*mut c_void,epoch:u32,fid:u32,core:u32,success:i32)->i32{guard(||gateway(h)?.commit_complete(epoch,fid,core,success!=0).map_err(error))}
#[no_mangle] pub unsafe extern "C" fn v97_abort_frame(h:*mut c_void)->i32{guard(||{gateway(h)?.abort_frame();Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_reset(h:*mut c_void)->i32{guard(||{gateway(h)?.reset();Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_core_changed(h:*mut c_void,core:u32)->i32{guard(||{if core==0{return Err(-15)}gateway(h)?.core_changed(core);Ok(())})}
#[no_mangle] pub unsafe extern "C" fn v97_drained(h:*mut c_void)->i32{guard(||gateway(h)?.drained().map_err(error))}
#[no_mangle] pub unsafe extern "C" fn v97_needs_drain(h:*mut c_void)->i32{match catch_unwind(AssertUnwindSafe(||gateway(h).map(|g|g.needs_drain() as i32))){Ok(Ok(v))=>v,Ok(Err(e))=>e,Err(_)=>-99}}
#[no_mangle] pub unsafe extern "C" fn v97_inflight(h:*mut c_void)->i32{match catch_unwind(AssertUnwindSafe(||gateway(h).map(|g|g.inflight() as i32))){Ok(Ok(v))=>v,Ok(Err(e))=>e,Err(_)=>-99}}
#[no_mangle] pub unsafe extern "C" fn v97_reserved_bytes(h:*mut c_void)->u32{catch_unwind(AssertUnwindSafe(||gateway(h).map(|g|g.reserved_bytes()).unwrap_or(0))).unwrap_or(0)}

#[cfg(test)] mod tests {
    use super::*;
    #[test] fn abi_layout(){assert_eq!(std::mem::size_of::<V97Transfer>(),24);assert_eq!(std::mem::size_of::<V97Frame>(),32);assert_eq!(std::mem::size_of::<V97Chunk>(),72);}
    #[test] fn null_and_length_guards(){unsafe{let n=std::ptr::null_mut();assert_eq!(v97_destroy(n),-1);assert_eq!(v97_setup(n,std::ptr::null(),0,n as *mut u8),-1);assert_eq!(v97_receive(n,std::ptr::null(),0,n as *mut V97Chunk),-1);assert_eq!(v97_issue(n,std::ptr::null()),-1);assert_eq!(v97_complete(n,1,1),-1);assert_eq!(v97_commit_complete(n,1,1,1,1),-1);assert_eq!(v97_take_commit(n,n as *mut V97Frame),-1);assert!(v97_transfer_bytes(n,std::ptr::null()).is_null());assert!(v97_create(0,0).is_null());let h=v97_create(0,1);assert!(!h.is_null());let mut out=std::mem::MaybeUninit::<V97Chunk>::uninit();assert_eq!(v97_receive(h,std::ptr::null(),1429,out.as_mut_ptr()),-12);assert_eq!(v97_needs_drain(h),1);assert_eq!(v97_drained(h),0);assert_eq!(v97_core_changed(h,0),-15);assert_eq!(v97_destroy(h),0);}}
}
