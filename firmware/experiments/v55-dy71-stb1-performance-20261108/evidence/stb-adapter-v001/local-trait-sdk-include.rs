#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Error{Io,Contended,Epoch,Identity,NotFresh,Bounds,Sequence,Deadline,MailboxTimeout{operation:u8,sequence:u32},Mailbox{operation:u8,sequence:u32,status:u32},Snapshot,PacketMismatch,Hud,Readback{frame:u32,word:u32,expected:u16,actual:u32},Owner(u32),Counters,Tag,Allocation}
pub trait Bus{
 fn staging_read_words(&mut self,_o:u32,_out:&mut[u32])->Result<usize,Error>{Err(Error::Identity)}
 fn staging_descriptor(&mut self,_words:&[u32;5])->Result<(),Error>{Err(Error::Identity)}
 fn staging_payload_be(&mut self,_o:u32,_bytes:&[u8])->Result<usize,Error>{Err(Error::Identity)}
fn read(&mut self,offset:u32)->Result<u32,Error>;fn write(&mut self,offset:u32,value:u32)->Result<(),Error>;fn now(&self)->u64;fn yield_now(&mut self);
 fn write_words(&mut self,o:u32,words:&[u32])->Result<(),Error>{for(i,&v)in words.iter().enumerate(){self.write(o+i as u32*4,v)?;}Ok(())}
 fn hbu_status_words(&mut self)->Result<[u32;4],Error>{Ok([self.read(0x608)?,self.read(0x610)?,self.read(0x614)?,self.read(0x618)?])}
 fn mailbox_reply(&mut self)->Result<[u32;3],Error>{Ok([self.read(0x28)?,self.read(0x2c)?,self.read(0x30)?])}
 fn bulk_payload_write(&mut self,words:&[u32])->Result<(),Error>{if words.is_empty()||words.len()>128{return Err(Error::Bounds)}for(i,&v)in words.iter().enumerate(){self.write(0x400+i as u32*4,v)?;}Ok(())}
 fn bulk_payload_read(&mut self,words:&mut[u32])->Result<(),Error>{if words.is_empty()||words.len()>128{return Err(Error::Bounds)}for(i,v)in words.iter_mut().enumerate(){*v=self.read(0x400+i as u32*4)?;}Ok(())}
}
