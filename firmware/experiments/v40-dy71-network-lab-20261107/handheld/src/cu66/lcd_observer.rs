//! Bounded LD14 extension client. No arbitrary addresses or allocator usage.
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Io{Busy,Failed,Epoch}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Error{Io,Epoch,Deadline,Unsupported,Busy,Owner,Sequence,Snapshot}
pub trait Bus{fn read(&mut self,o:u32)->Result<u32,Io>;fn write(&mut self,o:u32,v:u32)->Result<(),Io>;fn now(&self)->u64;fn pause(&mut self);}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Command{Snapshot,Pattern(bool)}
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub struct Report{pub sequence:u32,pub frame:u32,pub pixels:[u32;4],pub status:u32}
struct Client<'a,B:Bus>{bus:&'a mut B,end:u64}
impl<B:Bus> Client<'_,B>{
 fn limit(&self)->Result<(),Error>{if self.bus.now()>self.end{Err(Error::Deadline)}else{Ok(())}}
 fn read(&mut self,o:u32)->Result<u32,Error>{loop{self.limit()?;match self.bus.read(o){Ok(v)=>return Ok(v),Err(Io::Busy)=>self.bus.pause(),Err(Io::Epoch)=>return Err(Error::Epoch),Err(Io::Failed)=>return Err(Error::Io)}}}
 fn write(&mut self,o:u32,v:u32)->Result<(),Error>{loop{self.limit()?;match self.bus.write(o,v){Ok(())=>return Ok(()),Err(Io::Busy)=>self.bus.pause(),Err(Io::Epoch)=>return Err(Error::Epoch),Err(Io::Failed)=>return Err(Error::Io)}}}
 fn identity(&mut self)->Result<(),Error>{if self.read(0x380)?!=0x4c443134||self.read(0x3a4)?!=0x10000||self.read(0x3a8)?!=3{Err(Error::Unsupported)}else{Ok(())}}
 fn status(&mut self)->Result<u32,Error>{let s=self.read(0x384)?;if s&16==0{Err(Error::Owner)}else{Ok(s)}}
}
pub fn identify<B:Bus>(bus:&mut B)->Result<(),Error>{let end=bus.now().saturating_add(250_000);Client{bus,end}.identity()}
pub fn run<B:Bus>(bus:&mut B,command:Command,expected_frame:u32)->Result<Report,Error>{
 let end=bus.now().saturating_add(250_000);let mut c=Client{bus,end};c.identity()?;
 if c.status()?&4!=0{return Err(Error::Busy)}
 let sequence=c.read(0x388)?;
 match command{
  Command::Pattern(on)=>{
   c.write(0x380,on as u32)?;
   loop{let s=c.status()?;if s&7==if on{3}else{0}{return Ok(Report{sequence,frame:expected_frame,pixels:[0;4],status:s})}c.bus.pause();}
  }
  Command::Snapshot=>{
   let next=sequence.checked_add(1).ok_or(Error::Sequence)?;
   c.write(0x384,1)?;
   loop{let s=c.status()?;if s&4==0{
    if s&8==0||c.read(0x388)?!=next{return Err(Error::Snapshot)}
    let frame=c.read(0x38c)?;if frame!=expected_frame{return Err(Error::Snapshot)}
    let mut pixels=[0;4];for(i,v)in pixels.iter_mut().enumerate(){*v=c.read(0x390+i as u32*4)?;if *v>0xffffff{return Err(Error::Snapshot)}}
    let after=c.status()?;if after&12!=8||c.read(0x388)?!=next||c.read(0x38c)?!=frame{return Err(Error::Snapshot)}
    return Ok(Report{sequence:next,frame,pixels,status:after});
   }c.bus.pause();}
  }
 }
}

#[cfg(test)]mod tests{
 use super::*;
 struct Fake{now:u64,magic:u32,status:u32,sequence:u32,frame:u32,writes:Vec<(u32,u32)>,pending:u8,stall:bool,epoch:bool,race:bool}
 impl Fake{fn new()->Self{Self{now:0,magic:0x4c443134,status:16,sequence:0,frame:1,writes:Vec::new(),pending:0,stall:false,epoch:false,race:false}}}
 impl Bus for Fake{
  fn now(&self)->u64{self.now}
  fn pause(&mut self){self.now+=1000;if !self.stall&&self.pending>0{self.pending-=1;if self.pending==0{self.status=(self.status&!4)|8;self.sequence+=1}}}
  fn read(&mut self,o:u32)->Result<u32,Io>{if self.epoch{return Err(Io::Epoch)}Ok(match o{0x380=>self.magic,0x384=>self.status,0x388=>self.sequence,0x38c=>{if self.race{self.sequence+=1}self.frame},0x3a4=>0x10000,0x3a8=>3,0x390..=0x39c=>0x123456,_=>panic!("unguarded address")})}
  fn write(&mut self,o:u32,v:u32)->Result<(),Io>{self.writes.push((o,v));match o{0x384=>{assert_eq!(v,1);self.status=(self.status&!8)|4;self.pending=2;},0x380=>{assert!(v<=1);self.status=(self.status&!3)|if v==1{3}else{0}},_=>panic!("unguarded write")};Ok(())}
 }
 #[test]fn snapshot_has_new_sequence_frame_and_exact_four_words(){let mut b=Fake::new();let r=run(&mut b,Command::Snapshot,1).unwrap();assert_eq!(r.pixels,[0x123456;4]);assert_eq!(r.sequence,1);assert_eq!(b.writes,[(0x384,1)]);}
 #[test]fn foreign_image_never_written(){let mut b=Fake::new();b.magic=0;assert_eq!(run(&mut b,Command::Snapshot,1),Err(Error::Unsupported));assert!(b.writes.is_empty());}
 #[test]fn owner_or_busy_denial_never_issues_request(){for s in [0,20]{let mut b=Fake::new();b.status=s;assert!(matches!(run(&mut b,Command::Snapshot,1),Err(Error::Owner|Error::Busy)));assert!(b.writes.is_empty());}}
 #[test]fn pending_timeout_is_bounded_and_not_retried(){let mut b=Fake::new();b.stall=true;assert_eq!(run(&mut b,Command::Snapshot,1),Err(Error::Deadline));assert_eq!(b.writes,[(0x384,1)]);assert!(b.now<=251000);}
 #[test]fn stale_frame_and_torn_snapshot_rejected(){let mut b=Fake::new();assert_eq!(run(&mut b,Command::Snapshot,2),Err(Error::Snapshot));let mut b=Fake::new();b.race=true;assert_eq!(run(&mut b,Command::Snapshot,1),Err(Error::Snapshot));}
 #[test]fn sequence_overflow_refuses_before_write(){let mut b=Fake::new();b.sequence=u32::MAX;assert_eq!(run(&mut b,Command::Snapshot,1),Err(Error::Sequence));assert!(b.writes.is_empty());}
 #[test]fn program_epoch_error_is_not_retried(){let mut b=Fake::new();b.epoch=true;assert_eq!(run(&mut b,Command::Snapshot,1),Err(Error::Epoch));assert!(b.writes.is_empty());}
 #[test]fn pattern_commands_are_only_typed_zero_or_one(){let mut b=Fake::new();run(&mut b,Command::Pattern(true),1).unwrap();run(&mut b,Command::Pattern(false),1).unwrap();assert_eq!(b.writes,[(0x380,1),(0x380,0)]);}
}
