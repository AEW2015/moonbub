//! CU71 lab-only key/P execution. Scalar, bounded, no UDP or rate capability.
use super::{framing::{crc32,decode},hud::Hud};
pub const MAGIC:u32=0x43553731;pub const ABI:u32=0x10000;
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Profile{Cu71,Dy71,Dy71Bulk}
impl Profile{
 pub const fn magic(self)->u32{match self{Self::Cu71=>0x43553731,Self::Dy71|Self::Dy71Bulk=>0x44593731}}
 pub const fn capabilities(self)->u32{match self{Self::Cu71=>7,Self::Dy71=>15,Self::Dy71Bulk=>31}}
}
const PACKET0:&[u8]=include_bytes!("fixtures/packet0.cu66");const PACKET1:&[u8]=include_bytes!("fixtures/packet1.cu66");
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Error{Io,Contended,Epoch,Identity,NotFresh,Bounds,Sequence,Deadline,MailboxTimeout{operation:u8,sequence:u32},Mailbox{operation:u8,sequence:u32,status:u32},Snapshot,PacketMismatch,Hud,Readback{frame:u32,word:u32,expected:u16,actual:u32},Owner(u32),Counters,Tag,Allocation}
pub trait Bus{fn read(&mut self,offset:u32)->Result<u32,Error>;fn write(&mut self,offset:u32,value:u32)->Result<(),Error>;fn now(&self)->u64;fn yield_now(&mut self);
 fn write_words(&mut self,o:u32,words:&[u32])->Result<(),Error>{for(i,&v)in words.iter().enumerate(){self.write(o+i as u32*4,v)?;}Ok(())}
 // Default model preserves legacy scalar semantics; physical Adapter overrides with one bounded span read.
 fn hbu_status_words(&mut self)->Result<[u32;4],Error>{Ok([self.read(0x608)?,self.read(0x610)?,self.read(0x614)?,self.read(0x618)?])}
 fn mailbox_reply(&mut self)->Result<[u32;3],Error>{Ok([self.read(0x28)?,self.read(0x2c)?,self.read(0x30)?])}
 fn bulk_payload_write(&mut self,words:&[u32])->Result<(),Error>{if words.is_empty()||words.len()>128{return Err(Error::Bounds)}for(i,&v)in words.iter().enumerate(){self.write(0x400+i as u32*4,v)?;}Ok(())}
 fn bulk_payload_read(&mut self,words:&mut[u32])->Result<(),Error>{if words.is_empty()||words.len()>128{return Err(Error::Bounds)}for(i,v)in words.iter_mut().enumerate(){*v=self.read(0x400+i as u32*4)?;}Ok(())}
}
#[derive(Debug,Clone,Copy)]pub struct Report{pub frames:u32,pub accepted:u32,pub presented:u32,pub rejected:u32,pub underruns:u32,pub words_written:u32,pub words_verified:u32,pub elapsed_us:u64,pub hud_cpu_us:[u64;2],pub allocator:[usize;6],pub packet_complete_us:[u64;2],pub admission_us:[u64;2],pub hud_valid_us:[u64;2],pub hud_write_done_us:[u64;2],pub hud_readback_done_us:[u64;2],pub hud_drained_us:[u64;2],pub software_commit_acked_us:[u64;2],pub presentation_observed_us:[u64;2]}
pub struct Completed{_private:()}
#[derive(Clone,Copy)]struct Id{generation:u64,frame:u32,reference:u32}
#[derive(Clone,Copy)]struct Request{id:Id,offset:usize,length:usize,bank:u32,key:bool,tag:[u8;16]}
fn n32(p:&[u8],o:usize)->u32{u32::from_le_bytes(p[o..o+4].try_into().unwrap())}
struct Driver<'a,B:Bus>{profile:Profile,bus:&'a mut B,sequence:u32,deadline:u64,mutated:bool,fields:[Option<u32>;12]}
impl<B:Bus> Driver<'_,B>{
 fn limit(&self)->Result<(),Error>{if self.bus.now()>self.deadline{Err(Error::Deadline)}else{Ok(())}}
 fn r(&mut self,o:u32)->Result<u32,Error>{loop{self.limit()?;match self.bus.read(o){Err(Error::Contended)=>self.bus.yield_now(),r=>return r}}}
 fn w(&mut self,o:u32,v:u32)->Result<(),Error>{loop{self.limit()?;match self.bus.write(o,v){Err(Error::Contended)=>self.bus.yield_now(),r=>{if r.is_ok(){self.mutated=true}return r}}}}
 fn command(&mut self,op:u8,id:Id,arg:[u32;4],tag:[u8;16])->Result<u32,Error>{
  self.limit()?;let next=self.sequence.checked_add(1).ok_or(Error::Sequence)?;if self.r(0x00c)?&1==0{return Err(Error::Sequence)}
  let fields=[id.generation as u32,(id.generation>>32)as u32,id.frame,id.reference,arg[0],arg[1],arg[2],arg[3],u32::from_be_bytes(tag[0..4].try_into().unwrap()),u32::from_be_bytes(tag[4..8].try_into().unwrap()),u32::from_be_bytes(tag[8..12].try_into().unwrap()),u32::from_be_bytes(tag[12..16].try_into().unwrap())];
  for(i,value)in fields.into_iter().enumerate(){if self.fields[i]!=Some(value){self.w(0x40+i as u32*4,value)?;self.fields[i]=Some(value);}}
  self.sequence=next;if self.sequence==0{return Err(Error::Sequence)}
  self.w(0x20,self.sequence)?;self.w(0x24,op as u32)?;let end=self.bus.now().saturating_add(250_000).min(self.deadline);
  loop{let ack=self.r(0x28)?;if ack==self.sequence{let status=self.r(0x2c)?;if status==0{return self.r(0x30)}if status!=1{return Err(Error::Mailbox{operation:op,sequence:self.sequence,status})}}
   else if ack>self.sequence{return Err(Error::Sequence)}
   if self.bus.now()>end{return Err(Error::MailboxTimeout{operation:op,sequence:self.sequence})}self.bus.yield_now();
  }
 }
 fn owner(&mut self)->Result<(bool,u8,u8),Error>{let w=self.r(0x350)?;Ok((w&1!=0,((w>>1)&255)as u8,((w>>9)&255)as u8))}
 fn hud_request(&mut self)->Result<Request,Error>{
  for _ in 0..4{if self.r(0x00c)?&32==0{return Err(Error::Snapshot)}let t=self.r(0x300)?;let lo=self.r(0x304)?;let hi=self.r(0x308)?;let f=self.r(0x30c)?;let rf=self.r(0x310)?;let span=self.r(0x314)?;let flags=self.r(0x318)?;let mut tag=[0;16];for i in 0..4{tag[i*4..i*4+4].copy_from_slice(&self.r(0x31c+i as u32*4)?.to_be_bytes());}if t!=0&&t==self.r(0x300)?&&self.r(0x00c)?&32!=0{return Ok(Request{id:Id{generation:lo as u64|((hi as u64)<<32),frame:f,reference:rf},offset:(span&65535)as usize,length:(span>>16)as usize,bank:flags&3,key:flags&4!=0,tag})}}
  Err(Error::Snapshot)
 }
 fn software(&mut self,hud:&mut Hud,out:&mut[u8;1060],req:&mut[u8;64],id:Id)->Result<bool,Error>{
  if self.r(0x00c)?&64==0{return Ok(false)}let t=self.r(0x330)?;let op=self.r(0x334)?;let lo=self.r(0x338)?;let hi=self.r(0x33c)?;let f=self.r(0x340)?;let rf=self.r(0x344)?;
  if t==0||t!=self.r(0x330)?||self.r(0x00c)?&64==0||id.generation!=(lo as u64|((hi as u64)<<32))||id.frame!=f||id.reference!=rf||!(op==5||op==6){return Err(Error::Snapshot)}
  let n=hc(op as u8,id,0,&[],req);let r=decode(hud.transact(&req[..n],out).map_err(|_|Error::Hud)?).map_err(|_|Error::Hud)?;
  if r.argument!=0||r.payload.len()!=72{return Err(Error::Hud)}
  if op==5{if r.payload[0]!=3||r.payload[1]&28!=16||r.payload[40..48]!=id.generation.to_le_bytes()||n32(r.payload,48)!=id.frame||n32(r.payload,52)!=id.reference{return Err(Error::Hud)}}else if r.payload[0]!=4||r.payload[1]&12!=0||r.payload[8..16]!=id.generation.to_le_bytes()||n32(r.payload,16)!=id.frame||n32(r.payload,20)!=id.reference{return Err(Error::Hud)}
  // A successful native COMMIT/ABORT is real; no fabricated SDK acknowledgment.
  self.command(20,id,[op,1,0,0],[0;16])?;Ok(true)
 }
 fn completed_snapshot(&mut self)->Result<Completed,Error>{self.limit()?;if self.r(0)?!=self.profile.magic()||self.r(4)?!=ABI||self.r(8)?!=self.profile.capabilities()||self.r(0x00c)?!=1||self.owner()?.0||self.r(0x110)?!=0{return Err(Error::Counters)}Ok(Completed{_private:()})}
}
fn hc(op:u8,id:Id,arg:u32,p:&[u8],b:&mut[u8;64])->usize{let n=32+p.len();b.fill(0);b[..4].copy_from_slice(b"HC70");b[4]=1;b[5]=op;b[8..12].copy_from_slice(&(p.len()as u32).to_le_bytes());b[12..20].copy_from_slice(&id.generation.to_le_bytes());b[20..24].copy_from_slice(&id.frame.to_le_bytes());b[24..28].copy_from_slice(&id.reference.to_le_bytes());b[28..32].copy_from_slice(&arg.to_le_bytes());b[32..n].copy_from_slice(p);let c=crc32(&b[..n]);b[n..n+4].copy_from_slice(&c.to_le_bytes());n+4}
fn ok<'a>(hud:&mut Hud,wire:&[u8],out:&'a mut[u8;1060])->Result<super::framing::Frame<'a>,Error>{let r=decode(hud.transact(wire,out).map_err(|_|Error::Hud)?).map_err(|_|Error::Hud)?;if r.argument!=0{return Err(Error::Hud)}Ok(r)}
pub fn run<B:Bus>(bus:&mut B,hud:&mut Hud)->Result<(Report,Completed),Error>{run_with_profile(bus,hud,Profile::Cu71)}
pub fn run_with_profile<B:Bus>(bus:&mut B,hud:&mut Hud,profile:Profile)->Result<(Report,Completed),Error>{
 let began=bus.now();let mut d=Driver{profile,bus,sequence:0,deadline:began.saturating_add(5_000_000),mutated:false,fields:[None;12]};
 if d.r(0)?!=d.profile.magic()||d.r(4)?!=ABI||d.r(8)?!=d.profile.capabilities(){return Err(Error::Identity)}
 d.completed_snapshot()?;if d.r(0x354)?!=0||d.r(0x358)?!=0||d.r(0x35c)?!=0{return Err(Error::NotFresh)}d.sequence=d.r(0x28)?;
 let mut generation=d.r(0x114)?as u64|((d.r(0x118)?as u64)<<32);
 let mut out=[0u8;1060];let mut req=[0u8;64];let mut cpu=[0;2];let mut words_written=0;let mut words_verified=0;let mut packet_complete_us=[0;2];let mut admission_us=[0;2];let mut hud_valid_us=[0;2];let mut hud_write_done_us=[0;2];let mut hud_readback_done_us=[0;2];let mut hud_drained_us=[0;2];let mut software_commit_acked_us=[0;2];let mut presentation_observed_us=[0;2];
 for(index,packet)in[PACKET0,PACKET1].into_iter().enumerate(){
  d.deadline=d.bus.now().saturating_add(30_000_000);generation=generation.checked_add(1).ok_or(Error::Sequence)?;
  let id=Id{generation,frame:n32(packet,8),reference:n32(packet,12)};let checksum=crc32(packet);d.command(1,id,[packet.len()as u32,checksum,0,0],[0;16])?;
  for(offset,bytes)in packet.chunks(4).enumerate(){let expected=(offset*4+bytes.len())as u32;while d.r(0x00c)?&2==0{d.limit()?;d.bus.yield_now()}
   let mut word=[0u8;4];word[..bytes.len()].copy_from_slice(bytes);d.w(0x100,u32::from_le_bytes(word))?;
   loop{let count=d.r(0x104)?;if count==expected{break}if count>expected{return Err(Error::Sequence)}d.bus.yield_now();}
   if offset%64==0{d.bus.yield_now()}
  }
  if d.r(0x104)?!=packet.len()as u32||d.r(0x108)?!=packet.len()as u32||d.r(0x10c)?!=checksum||d.r(0x110)?!=0{return Err(Error::PacketMismatch)}d.command(2,id,[0,checksum,0,0],[0;16])?;packet_complete_us[index]=d.bus.now();
  // This diagnostic profile uses30s ownerwatchdog; SDK observation/drain window is40s.
  d.deadline=d.bus.now().saturating_add(40_000_000);d.command(3,id,[0;4],[0;16])?;admission_us[index]=d.bus.now();
  while d.r(0x00c)?&32==0{let(_,_,reason)=d.owner()?;if reason!=0{return Err(Error::Owner(reason as u32))}d.bus.yield_now();}
  let h=d.hud_request()?;let hu_offset=76+n32(packet,68)as usize;let hu_length=n32(packet,72)as usize;
  if h.id.generation!=generation||h.id.frame!=id.frame||h.id.reference!=id.reference||h.offset!=hu_offset||h.length!=hu_length||h.length>20_000||h.bank>2||h.key!=(packet[5]&1!=0)||h.offset.checked_add(h.length).filter(|n|*n<=packet.len()-4).is_none(){return Err(Error::Snapshot)}
  let mut wire=Vec::new();wire.try_reserve_exact(h.length+36).map_err(|_|Error::Allocation)?;wire.resize(h.length+36,0u8);
  for pos in(0..h.length).step_by(4){let address=h.offset+pos;let base=address.min(packet.len()-4);let bytes=d.command(21,id,[base as u32,0,0,0],[0;16])?.to_le_bytes();let skip=address-base;let count=(h.length-pos).min(4-skip);if bytes[skip..skip+count]!=packet[address..address+count]{return Err(Error::PacketMismatch)}wire[32+pos..32+pos+count].copy_from_slice(&bytes[skip..skip+count]);}
  wire[..4].copy_from_slice(b"HC70");wire[4]=1;wire[5]=1;wire[8..12].copy_from_slice(&(h.length as u32).to_le_bytes());wire[12..20].copy_from_slice(&generation.to_le_bytes());wire[20..24].copy_from_slice(&id.frame.to_le_bytes());wire[24..28].copy_from_slice(&id.reference.to_le_bytes());wire[28..32].copy_from_slice(&(h.key as u32).to_le_bytes());let crc=crc32(&wire[..32+h.length]);wire[32+h.length..].copy_from_slice(&crc.to_le_bytes());
  let start=d.bus.now();let response=ok(hud,&wire,&mut out)?;cpu[index]=d.bus.now().saturating_sub(start);
  if response.payload.len()!=72||response.payload[0]!=1||response.payload[1]&4==0||n32(response.payload,4)!=21120||response.payload[8..16]!=generation.to_le_bytes()||n32(response.payload,16)!=id.frame||n32(response.payload,20)!=id.reference||response.payload[24..40]!=h.tag{return Err(Error::Hud)}drop(wire);hud_valid_us[index]=d.bus.now();
  if d.owner()?.1==11{d.software(hud,&mut out,&mut req,id)?;return Err(Error::Owner(0x80))}
  d.command(16,id,[1,21120,0,0],h.tag)?;
  for offset in(0u32..21120).step_by(512){let count=(21120-offset).min(512);let mut p=[0u8;8];p[..4].copy_from_slice(&offset.to_le_bytes());p[4..].copy_from_slice(&count.to_le_bytes());let n=hc(3,id,0,&p,&mut req);let r=ok(hud,&req[..n],&mut out)?;if r.payload.len()!=count as usize*2{return Err(Error::Hud)}
   for j in 0..count{if j%64==0{if d.owner()?.1==11{d.software(hud,&mut[0;1060],&mut req,id)?;return Err(Error::Owner(0x80))}d.bus.yield_now()}let word=u16::from_le_bytes(r.payload[j as usize*2..j as usize*2+2].try_into().unwrap());d.command(17,id,[offset+j,word as u32,0,0],[0;16])?;words_written+=1;}
  }
  hud_write_done_us[index]=d.bus.now();
  for offset in(0u32..21120).step_by(512){let count=(21120-offset).min(512);let mut p=[0u8;8];p[..4].copy_from_slice(&offset.to_le_bytes());p[4..].copy_from_slice(&count.to_le_bytes());let n=hc(3,id,0,&p,&mut req);let r=ok(hud,&req[..n],&mut out)?;if r.payload.len()!=count as usize*2{return Err(Error::Hud)}
   for j in 0..count{if j%64==0{if d.owner()?.1==11{d.software(hud,&mut[0;1060],&mut req,id)?;return Err(Error::Owner(0x80))}d.bus.yield_now()}let expected=u16::from_le_bytes(r.payload[j as usize*2..j as usize*2+2].try_into().unwrap());let actual=d.command(18,id,[offset+j,0,0,0],[0;16])?;if actual!=expected as u32{return Err(Error::Readback{frame:id.frame,word:offset+j,expected,actual})}words_verified+=1;}
  }
  hud_readback_done_us[index]=d.bus.now();
  // Every actual SDRAM word equals this native tagged candidate. No count-only attestation.
  let mut ack=[0u8;20];ack[..4].copy_from_slice(&21120u32.to_le_bytes());ack[4..].copy_from_slice(&h.tag);let n=hc(4,id,1,&ack,&mut req);ok(hud,&req[..n],&mut out)?;d.command(19,id,[1,21120,h.bank,0],h.tag)?;hud_drained_us[index]=d.bus.now();
  loop{if d.software(hud,&mut out,&mut req,id)?{software_commit_acked_us[index]=d.bus.now();}let(busy,_,reason)=d.owner()?;if reason!=0{return Err(Error::Owner(reason as u32))}if !busy&&d.r(0x00c)?==1&&d.r(0x358)?==index as u32+1{break}d.bus.yield_now();}
  presentation_observed_us[index]=d.bus.now();
  if d.r(0x354)?!=index as u32+1||d.r(0x35c)?!=0{return Err(Error::Counters)}
  let mut tag=[0u8;16];for part in 0..4{d.w(0x200,0x98+part as u32*4)?;tag[(3-part)*4..(4-part)*4].copy_from_slice(&d.r(0x204)?.to_be_bytes());}if tag!=packet[52..68]{return Err(Error::Tag)}for address in[0x01c,0x020]{d.w(0x200,address)?;if d.r(0x204)?!=id.frame{return Err(Error::Counters)}}
 }
 let proof=d.completed_snapshot()?;let report=Report{frames:2,accepted:d.r(0x354)?,presented:d.r(0x358)?,rejected:d.r(0x35c)?,underruns:d.r(0x360)?,words_written,words_verified,elapsed_us:d.bus.now().saturating_sub(began),hud_cpu_us:cpu,allocator:hud.stats().map_err(|_|Error::Hud)?,packet_complete_us,admission_us,hud_valid_us,hud_write_done_us,hud_readback_done_us,hud_drained_us,software_commit_acked_us,presentation_observed_us};Ok((report,proof))
}
