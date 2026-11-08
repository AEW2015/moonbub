#![allow(dead_code)]
#[path="../handheld/src/cu66/framing.rs"]mod framing;
#[path="../handheld/src/cu66/hud.rs"]mod hud;
#[path="../handheld/src/cu66/local.rs"]mod local;
#[path="../handheld/src/cu66/network_driver.rs"]mod nd;
struct Input{index:usize}
impl nd::Source for Input{
 fn header(&mut self)->Result<nd::Header,nd::Error>{let b=if self.index==0{include_bytes!("../handheld/src/cu66/fixtures/packet0.cu66").as_slice()}else{include_bytes!("../handheld/src/cu66/fixtures/packet1.cu66").as_slice()};let mut prefix=[0;76];prefix.copy_from_slice(&b[..76]);Ok(nd::Header{prefix,length:b.len(),crc:framing::crc32(b)})}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,nd::Error>{let b=if self.index==0{include_bytes!("../handheld/src/cu66/fixtures/packet0.cu66").as_slice()}else{include_bytes!("../handheld/src/cu66/fixtures/packet1.cu66").as_slice()};let n=(b.len()-offset).min(1024);out[..n].copy_from_slice(&b[offset..offset+n]);Ok(n)}
 fn stored(&mut self,_:usize)->Result<(),nd::Error>{Ok(())}
 fn presented(&mut self)->Result<(),nd::Error>{self.index+=1;Ok(())}
}
fn execute(b:&mut impl nd::Bus,h:&mut hud::Hud)->Result<(nd::Report,nd::Completed),nd::Error>{nd::run(b,h,&mut Input{index:0})}

use nd::{Bus,Error};use std::cell::Cell;
fn n32(p:&[u8],o:usize)->u32{u32::from_le_bytes(p[o..o+4].try_into().unwrap())}
struct Fake{time:Cell<u64>,magic:u32,caps:u32,abi:u32,read_contentions:u32,write_contentions:u32,ack:u32,status:u32,data:u32,fields:[u32;12],submit:u32,packet:Vec<u8>,length:u32,crc:u32,loading:bool,sealed:bool,active:bool,hud_pending:bool,soft:bool,accepted:u32,hud:Vec<u16>,writes:u32,reads:u32,drains:u32,diag:u32,ops:Vec<u32>,fault_read:bool,wrong_ticket:bool,lost_ack:bool,postcommit_loss:bool,physical_writes:u32,bulk_offset:u32,bulk_count:u32,bulk_mode:u32,bulk_loaded:usize,bulk_done:bool,bulk_data:Vec<u32>}
impl Fake{fn new()->Self{Self{time:Cell::new(0),magic:nd::Profile::Dy71Bulk.magic(),caps:31,abi:nd::ABI,read_contentions:0,write_contentions:0,ack:0,status:0,data:0,fields:[0;12],submit:0,packet:vec![],length:0,crc:0,loading:false,sealed:false,active:false,hud_pending:false,soft:false,accepted:0,hud:vec![0;21120],writes:0,reads:0,drains:0,diag:0,ops:vec![],fault_read:false,wrong_ticket:false,lost_ack:false,postcommit_loss:false,physical_writes:0,bulk_offset:0,bulk_count:0,bulk_mode:0,bulk_loaded:0,bulk_done:false,bulk_data:vec![0;128]}}fn tick(&self){self.time.set(self.time.get()+1)}fn gen(&self)->u64{self.fields[0]as u64|((self.fields[1]as u64)<<32)}fn frame(&self)->u32{n32(&self.packet,8)}fn reference(&self)->u32{n32(&self.packet,12)}fn hu(&self)->(usize,usize){(76+n32(&self.packet,68)as usize,n32(&self.packet,72)as usize)}fn flags(&self)->u32{1|((self.loading as u32)<<1)|((self.sealed as u32)<<2)|((self.active as u32)<<3)|((self.active as u32)<<4)|((self.hud_pending as u32)<<5)|((self.soft as u32)<<6)}}
impl Bus for Fake{
 fn now(&self)->u64{self.time.get()}fn yield_now(&mut self){self.time.set(self.time.get()+100)}
 fn read(&mut self,o:u32)->Result<u32,Error>{self.tick();if self.read_contentions!=0{self.read_contentions-=1;return Err(Error::Contended)}Ok(match o{0=>self.magic,4=>self.abi,8=>self.caps,0x600=>0x48425531,0x604=>0x10000,0x608=>if self.bulk_mode==1&&self.bulk_done{8}else{0},0x610=>if self.bulk_done{self.bulk_count}else{0},0x614=>(self.bulk_count<<16)|self.bulk_offset,0x618=>self.accepted+1,0x400..=0x5fc=>self.bulk_data[((o-0x400)/4)as usize],0xc=>self.flags(),0x28=>self.ack,0x2c=>self.status,0x30=>self.data,0x104=>self.packet.len()as u32,0x108=>self.length,0x10c=>framing::crc32(&self.packet),0x110=>0,0x114=>self.fields[0],0x118=>self.fields[1],0x300=>self.accepted+1,0x304=>self.fields[0],0x308=>self.fields[1],0x30c=>self.frame(),0x310=>if self.wrong_ticket{123}else{self.reference()},0x314=>{let(a,n)=self.hu();((n as u32)<<16)|a as u32},0x318=>((self.accepted%3)as u32)|(((self.packet[5]&1!=0)as u32)<<2),0x31c..=0x328=>{let(a,_)=self.hu();let off=a+38+(o-0x31c)as usize;u32::from_be_bytes(self.packet[off..off+4].try_into().unwrap())},0x330=>self.accepted+1,0x334=>5,0x338=>self.fields[0],0x33c=>self.fields[1],0x340=>self.frame(),0x344=>self.reference(),0x350=>(self.active as u32)|((if self.soft{10}else{5})<<1),0x354|0x358=>self.accepted,0x35c|0x360=>0,0x204=>{if self.diag==0x01c||self.diag==0x020{return Ok(self.frame())}let part=(self.diag-0x98)/4;let off=52+(3-part)as usize*4;u32::from_be_bytes(self.packet[off..off+4].try_into().unwrap())},_=>panic!("unexpectedread {o:x}")})}
 fn write(&mut self,o:u32,value:u32)->Result<(),Error>{self.tick();if self.write_contentions!=0{self.write_contentions-=1;return Err(Error::Contended)}self.physical_writes+=1;match o{
  0x400..=0x5fc=>{let i=((o-0x400)/4)as usize;assert_eq!(i,self.bulk_loaded);self.bulk_data[i]=value;self.bulk_loaded+=1;},0x40..=0x6c=>self.fields[((o-0x40)/4)as usize]=value,0x20=>self.submit=value,0x200=>self.diag=value,
  0x100=>{assert!(self.loading);let n=(self.length-self.packet.len()as u32).min(4)as usize;self.packet.extend_from_slice(&value.to_le_bytes()[..n]);},
  0x24=>{self.ops.push(value);self.status=0;self.data=0;
   match value{22=>{assert!(self.active&&self.hud_pending);self.bulk_offset=self.fields[4];self.bulk_count=self.fields[5];self.bulk_mode=self.fields[6];assert!(self.bulk_count>0&&self.bulk_count<=256&&self.bulk_offset+self.bulk_count<=21120&&self.bulk_mode<=1);self.bulk_loaded=0;self.bulk_done=false;self.bulk_data.fill(0);},23=>{assert_eq!((self.fields[4],self.fields[5],self.fields[6]),(self.bulk_offset,self.bulk_count,self.bulk_mode));if self.bulk_mode==0{assert_eq!(self.bulk_loaded,(self.bulk_count as usize+1)/2);for j in 0..self.bulk_count as usize{assert_eq!(self.bulk_offset+j as u32,self.writes);self.hud[self.writes as usize]=((self.bulk_data[j/2]>>((j%2)*16))&65535)as u16;self.writes+=1;}}else{for j in 0..self.bulk_count as usize{let k=self.bulk_offset as usize+j;let mut w=self.hud[k];if self.fault_read&&k==1234{w^=1;}self.bulk_data[j/2]|=(w as u32)<<((j%2)*16);self.reads+=1;}}self.bulk_done=true;self.data=self.bulk_count;},1=>{self.packet.clear();self.length=self.fields[4];self.crc=self.fields[5];self.loading=true;},2=>{assert_eq!(framing::crc32(&self.packet),self.crc);self.sealed=true;self.loading=false;},3=>{self.sealed=false;self.active=true;self.hud_pending=true;self.writes=0;self.reads=0;},16=>{assert_eq!(self.fields[4],1);assert_eq!(self.fields[5],21120)},17=>{assert_eq!(self.fields[4],self.writes);self.hud[self.writes as usize]=self.fields[5]as u16;self.writes+=1},18=>{let i=self.fields[4]as usize;self.data=self.hud[i]as u32;if self.fault_read&&i==1234{self.data^=1}self.reads+=1},19=>{assert_eq!(self.writes,21120);assert_eq!(self.reads,21120);self.drains+=1;self.soft=true},20=>{assert_eq!(self.fields[4],5);assert_eq!(self.fields[5],1);self.accepted+=1;self.active=false;self.hud_pending=false;self.soft=false;},21=>{let a=self.fields[4]as usize;self.data=n32(&self.packet,a)},_=>panic!("unexpectedcommand{value}")}
   if !self.lost_ack&&!(self.postcommit_loss&&value==20){self.ack=self.submit;}
  },_=>panic!("unexpectedwrite{o:x}")};Ok(())
 }
}
fn run(b:&mut Fake)->Result<(nd::Report,nd::Completed),Error>{let mut h=hud::Hud::new(98_304).unwrap();execute(b,&mut h)}
#[test]fn actual_native_key_p_all_memory_words(){let mut b=Fake::new();let(r,_proof)=run(&mut b).unwrap();assert_eq!((r.frames,r.accepted,r.presented,r.rejected),(2,2,2,0));assert_eq!((r.words_written,r.words_verified),(42240,42240));assert_eq!(b.drains,2);assert!(!b.active);}
#[test]fn wrong_magic_has_no_writes(){let mut b=Fake::new();b.magic=0;assert!(matches!(run(&mut b),Err(Error::Identity)));assert_eq!(b.physical_writes,0);}
#[test]fn nonfresh_owner_refused_before_writes(){let mut b=Fake::new();b.accepted=1;assert!(matches!(run(&mut b),Err(Error::NotFresh)));assert_eq!(b.physical_writes,0);}
#[test]fn command_sequence_exhaustion_before_writes(){let mut b=Fake::new();b.ack=u32::MAX;assert!(matches!(run(&mut b),Err(Error::Sequence)));assert_eq!(b.physical_writes,0);}
#[test]fn readback_mismatch_never_drains_or_commits(){let mut b=Fake::new();b.fault_read=true;assert!(matches!(run(&mut b),Err(Error::Readback{word:1234,..})));assert_eq!(b.drains,0);assert_eq!(b.accepted,0);assert!(b.active);}
#[test]fn wrong_hud_reference_never_writes_hud(){let mut b=Fake::new();b.wrong_ticket=true;assert!(matches!(run(&mut b),Err(Error::Snapshot)));assert_eq!(b.writes,0);assert_eq!(b.drains,0);}
#[test]fn mailbox_loss_is_bounded_no_fabricated_completion(){let mut b=Fake::new();b.lost_ack=true;assert!(matches!(run(&mut b),Err(Error::MailboxTimeout{..})));assert!(b.time.get()<300_000);assert_eq!(b.accepted,0);}
#[test]fn lost_postcommit_ack_never_rolls_back(){let mut b=Fake::new();b.postcommit_loss=true;assert!(matches!(run(&mut b),Err(Error::MailboxTimeout{..})));assert_eq!(b.accepted,1);assert!(!b.ops.contains(&5));assert!(!b.ops.contains(&4));}

#[test]fn successful_fixture_retains_actual_native_accepted_cache(){let mut b=Fake::new();let mut h=hud::Hud::new(98_304).unwrap();let(report,_)=execute(&mut b,&mut h).unwrap();assert_eq!(report.accepted,2);let mut req=[0u8;36];req[..4].copy_from_slice(b"HC70");req[4]=1;req[5]=2;let crc=framing::crc32(&req[..32]);req[32..].copy_from_slice(&crc.to_le_bytes());let mut out=[0u8;108];let r=framing::decode(h.transact(&req,&mut out).unwrap()).unwrap();assert_eq!(r.payload[0],3);assert_ne!(r.payload[1]&16,0);assert_eq!(n32(r.payload,48),1);assert!(h.stats().unwrap()[1]>42000);assert!(b.physical_writes<500_000);for i in 0..2{assert!(report.packet_complete_us[i]<report.admission_us[i]);assert!(report.admission_us[i]<=report.hud_valid_us[i]);assert!(report.hud_valid_us[i]<=report.hud_write_done_us[i]);assert!(report.hud_write_done_us[i]<=report.hud_readback_done_us[i]);assert!(report.hud_readback_done_us[i]<=report.hud_drained_us[i]);assert!(report.hud_drained_us[i]<=report.software_commit_acked_us[i]);assert!(report.software_commit_acked_us[i]<=report.presentation_observed_us[i]);}}

#[test]fn lost_commit_ack_retains_actual_native_accepted_cache(){let mut b=Fake::new();b.postcommit_loss=true;let mut h=hud::Hud::new(98_304).unwrap();assert!(matches!(execute(&mut b,&mut h),Err(Error::MailboxTimeout{..})));let mut req=[0u8;36];req[..4].copy_from_slice(b"HC70");req[4]=1;req[5]=2;let crc=framing::crc32(&req[..32]);req[32..].copy_from_slice(&crc.to_le_bytes());let mut out=[0u8;108];let r=framing::decode(h.transact(&req,&mut out).unwrap()).unwrap();assert_eq!(r.payload[0],3);assert_ne!(r.payload[1]&16,0);assert_eq!(n32(r.payload,48),0);assert!(h.stats().unwrap()[1]>42000);}

fn dy_fake()->Fake{let mut b=Fake::new();b.magic=nd::Profile::Dy71.magic();b.caps=31;b}
#[test]fn network_source_native_key_p(){let mut b=dy_fake();let mut h=hud::Hud::new(98_304).unwrap();let(r,_)=execute(&mut b,&mut h).unwrap();assert_eq!((r.accepted,r.presented,r.words_verified),(2,2,42240));}

#[path="../handheld/src/cu66/network_wire.rs"]mod network_wire;
#[path="../handheld/src/cu66/network_io.rs"]mod network_io;
#[test]fn actual_udp_native_key_p(){
 use std::{net::{UdpSocket,Ipv4Addr},process::Command};
 let socket=UdpSocket::bind((Ipv4Addr::LOCALHOST,0)).unwrap();let port=socket.local_addr().unwrap().port();
 let root=std::path::Path::new(env!("V43_ROOT"));let log=root.join("evidence").join(format!("loopback-{}-{}.jsonl",std::process::id(),port));
 let mut child=Command::new("python").arg(root.join("tools/dy71_fixture_sender.py")).args(["--receiver","127.0.0.1","--bind","127.0.0.1","--port"]).arg(port.to_string()).arg("--log").arg(&log).arg(root.join("handheld/src/cu66/fixtures/packet0.cu66")).arg(root.join("handheld/src/cu66/fixtures/packet1.cu66")).spawn().unwrap();
 let mut input=network_io::Input::new(socket,Ipv4Addr::LOCALHOST).unwrap();let mut b=dy_fake();let mut h=hud::Hud::new(98_304).unwrap();
 let outcome=nd::run(&mut b,&mut h,&mut input);if outcome.is_err(){child.kill().ok();}let status=child.wait().unwrap();let(r,_)=outcome.unwrap();assert!(status.success());assert_eq!((r.accepted,r.presented,r.words_verified),(2,2,42240));assert_eq!(std::fs::read_to_string(log).unwrap().lines().count(),2);
}
struct Corrupt{inner:Input}
impl nd::Source for Corrupt{
 fn header(&mut self)->Result<nd::Header,nd::Error>{self.inner.header()}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,nd::Error>{let n=self.inner.read(offset,out)?;if offset==1024{out[0]^=1;}Ok(n)}
 fn stored(&mut self,n:usize)->Result<(),nd::Error>{self.inner.stored(n)}
 fn presented(&mut self)->Result<(),nd::Error>{panic!("must not present corrupt bytes")}
}
#[test]fn altered_network_body_never_starts(){let mut b=dy_fake();let mut h=hud::Hud::new(98_304).unwrap();let r=nd::run(&mut b,&mut h,&mut Corrupt{inner:Input{index:0}});assert!(matches!(r,Err(nd::Error::PacketMismatch)));assert!(!b.ops.contains(&2));assert!(!b.ops.contains(&3));assert_eq!(b.accepted,0);}
use nd as network_driver;

unsafe extern "C" fn insufficient_heap()->usize{4096}
#[test]fn physical_memory_reserve_returns_semantic_failure_before_hud_commit(){let mut b=dy_fake();let mut h=hud::Hud::new(98_304).unwrap();h.reserve_internal_heap(insufficient_heap,8192).unwrap();let r=nd::run(&mut b,&mut h,&mut Input{index:0});assert!(matches!(r,Err(nd::Error::Hud)));assert_eq!(b.accepted,0);assert_eq!(b.writes,0);assert!(!b.ops.contains(&19));assert!(h.stats().unwrap()[5]>0);}
