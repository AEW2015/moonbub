//! Exclusive, fallible native HU owner. This does not install a CU66 network backend.
use core::{ffi::c_void,marker::PhantomData,ptr::NonNull};
extern "C" {fn v46_hud_set_largest_probe(p:*mut c_void,probe:unsafe extern "C" fn()->usize)->i32;fn v46_hud_diagnostics(p:*mut c_void,out:*mut u64,text:*mut u8,cap:usize,length:*mut usize)->i32;fn v41_hud_set_reserve(p:*mut c_void,probe:unsafe extern "C" fn()->usize,reserve:usize)->i32;fn v34_hud_create(budget:usize)->*mut c_void;fn v34_hud_destroy(p:*mut c_void);fn v34_hud_transact(p:*mut c_void,b:*const u8,n:usize,out:*mut u8,cap:usize,written:*mut usize)->i32;fn v34_hud_stats(p:*mut c_void,out:*mut usize)->i32;}
#[derive(Debug)]pub enum Error{Allocation,Protocol,Native}
#[derive(Clone,Copy,Debug)]pub struct Diagnostics{pub native:[u64;24],pub stats:[usize;6],pub text:[u8;96],pub text_length:usize,pub valid:bool,pub stage:u8,pub ffi:i32,pub opcode:u8,pub generation:u64,pub frame:u32,pub reference:u32,pub reply:u32,pub payload_mask:u32,pub written:usize,pub expected_tag:[u8;16],pub observed_tag:[u8;16],pub identity_valid:bool,pub reply_valid:bool,pub tag_valid:bool}
impl Default for Diagnostics{fn default()->Self{Self{native:[0;24],stats:[0;6],text:[0;96],text_length:0,valid:false,stage:0,ffi:0,opcode:0,generation:0,frame:0,reference:0,reply:0,payload_mask:0,written:0,expected_tag:[0;16],observed_tag:[0;16],identity_valid:false,reply_valid:false,tag_valid:false}}}
pub struct Hud{p:NonNull<c_void>,diag:Diagnostics,_exclusive:PhantomData<*mut ()>}
impl Hud{
 pub fn new(budget:usize)->Result<Self,Error>{if budget>131_072{return Err(Error::Allocation)}let p=NonNull::new(unsafe{v34_hud_create(budget)}).ok_or(Error::Allocation)?;Ok(Self{p,diag:Diagnostics::default(),_exclusive:PhantomData})}
 // Stages:1 input framing,2 input response,3 FFI,4 output size,5 output framing,6 output identity,7 reply observed,8 driver payload mismatch.
 pub fn transact<'a>(&mut self,b:&[u8],out:&'a mut[u8])->Result<&'a[u8],Error>{
 self.diag.identity_valid=false;self.diag.reply_valid=false;self.diag.tag_valid=false;self.diag.written=0;self.diag.stage=1;self.diag.ffi=0;self.diag.reply=0;self.diag.payload_mask=0;
 let frame=super::framing::decode(b).map_err(|_|Error::Protocol)?;
 self.diag.identity_valid=true;self.diag.opcode=frame.opcode;self.diag.generation=frame.generation;self.diag.frame=frame.frame;self.diag.reference=frame.reference;
 self.diag.stage=2;if frame.response{return Err(Error::Protocol)}let mut n=0;
 self.diag.stage=3;let rc=unsafe{v34_hud_transact(self.p.as_ptr(),b.as_ptr(),b.len(),out.as_mut_ptr(),out.len(),&mut n)};self.diag.ffi=rc;self.diag.written=n;if rc!=0{return Err(Error::Native)}
 self.diag.stage=4;if n>out.len(){return Err(Error::Native)}let reply=&out[..n];self.validate_reply(frame,reply)?;Ok(reply)}
 fn validate_reply(&mut self,frame:super::framing::Frame<'_>,reply:&[u8])->Result<(),Error>{self.diag.stage=5;let r=super::framing::decode(reply).map_err(|_|Error::Protocol)?;
 self.diag.reply_valid=true;self.diag.reply=r.argument;self.diag.stage=6;if !r.response||r.opcode!=frame.opcode||r.generation!=frame.generation||r.frame!=frame.frame||r.reference!=frame.reference{return Err(Error::Protocol)}self.diag.stage=7;Ok(())}
 #[cfg(test)]pub fn inject_reply_for_test(&mut self,input:&[u8],reply:&[u8])->Result<(),Error>{let frame=super::framing::decode(input).map_err(|_|Error::Protocol)?;self.validate_reply(frame,reply)}
 pub fn payload_tags(&mut self,expected:[u8;16],observed:[u8;16]){self.diag.tag_valid=true;self.diag.expected_tag=expected;self.diag.observed_tag=observed;}
 pub fn payload_failure(&mut self,mask:u32){self.diag.stage=8;self.diag.payload_mask=mask;}
 pub fn observe_largest(&mut self,probe:unsafe extern "C" fn()->usize)->Result<(),Error>{if unsafe{v46_hud_set_largest_probe(self.p.as_ptr(),probe)}!=0{return Err(Error::Allocation)}Ok(())}
 pub fn diagnostics(&self)->Diagnostics{let mut d=self.diag;d.valid=unsafe{v46_hud_diagnostics(self.p.as_ptr(),d.native.as_mut_ptr(),d.text.as_mut_ptr(),d.text.len(),&mut d.text_length)}==0;if let Ok(s)=self.stats(){d.stats=s;}d}
 pub fn reserve_internal_heap(&mut self,probe:unsafe extern "C" fn()->usize,reserve:usize)->Result<(),Error>{if unsafe{v41_hud_set_reserve(self.p.as_ptr(),probe,reserve)}!=0{return Err(Error::Allocation)}Ok(())}
 pub fn stats(&self)->Result<[usize;6],Error>{let mut out=[0;6];if unsafe{v34_hud_stats(self.p.as_ptr(),out.as_mut_ptr())}!=0{return Err(Error::Native)}Ok(out)}
}
impl Drop for Hud{fn drop(&mut self){unsafe{v34_hud_destroy(self.p.as_ptr())}}}
