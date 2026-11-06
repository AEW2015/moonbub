//! Exclusive, fallible native HU owner. This does not install a CU66 network backend.
use core::{ffi::c_void,marker::PhantomData,ptr::NonNull};
extern "C" {fn v34_hud_create(budget:usize)->*mut c_void;fn v34_hud_destroy(p:*mut c_void);fn v34_hud_transact(p:*mut c_void,b:*const u8,n:usize,out:*mut u8,cap:usize,written:*mut usize)->i32;fn v34_hud_stats(p:*mut c_void,out:*mut usize)->i32;}
#[derive(Debug)]pub enum Error{Allocation,Protocol,Native}
pub struct Hud{p:NonNull<c_void>,_exclusive:PhantomData<*mut ()>}
impl Hud{
 pub fn new(budget:usize)->Result<Self,Error>{if budget>131_072{return Err(Error::Allocation)}let p=NonNull::new(unsafe{v34_hud_create(budget)}).ok_or(Error::Allocation)?;Ok(Self{p,_exclusive:PhantomData})}
 pub fn transact<'a>(&mut self,b:&[u8],out:&'a mut[u8])->Result<&'a[u8],Error>{let frame=super::framing::decode(b).map_err(|_|Error::Protocol)?;if frame.response{return Err(Error::Protocol)}let mut n=0;let rc=unsafe{v34_hud_transact(self.p.as_ptr(),b.as_ptr(),b.len(),out.as_mut_ptr(),out.len(),&mut n)};if rc!=0||n>out.len(){return Err(Error::Native)}let reply=&out[..n];let r=super::framing::decode(reply).map_err(|_|Error::Protocol)?;if !r.response||r.opcode!=frame.opcode||r.generation!=frame.generation||r.frame!=frame.frame||r.reference!=frame.reference{return Err(Error::Protocol)}Ok(reply)}
 pub fn stats(&self)->Result<[usize;6],Error>{let mut out=[0;6];if unsafe{v34_hud_stats(self.p.as_ptr(),out.as_mut_ptr())}!=0{return Err(Error::Native)}Ok(out)}
}
impl Drop for Hud{fn drop(&mut self){unsafe{v34_hud_destroy(self.p.as_ptr())}}}
