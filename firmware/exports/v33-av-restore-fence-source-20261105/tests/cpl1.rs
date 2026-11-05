#[path="../handheld/src/streaming/telemetry.rs"] pub mod telemetry;
mod streaming {pub use crate::telemetry;}
#[path="../handheld/src/diag_pages.rs"] mod diag_pages;
#[path="../handheld/src/cpl1.rs"] mod cpl1;
use cpl1::*;
struct Fake {words:[u32;40],id:u32,schema:u32,caps:u32,image:u32,ops:Vec<(u32,u32)>,fault:bool,noadvance:bool,torn_at:usize}
impl Fake{fn new()->Self{let mut words=[0;40];words[2]=SCHEMA;words[25]=3;Self{words,id:ID,schema:SCHEMA,caps:0,image:IMAGE,ops:vec![],fault:false,noadvance:false,torn_at:0}}}
impl Bus for Fake{
 fn read(&mut self,o:u32)->Result<u32,()>{self.ops.push((o,0));if self.ops.len()==self.torn_at{self.words[0]=0;}if self.fault{return Err(())}Ok(match o{0=>self.id,4=>self.schema,8=>self.caps,0x184=>self.image,0x500..=0x59c=>self.words[(o as usize-0x500)/4],_=>panic!("unexpected address")})}
 fn capture(&mut self,c:u32)->Result<(),()>{self.ops.push((0x500,c));if self.fault{return Err(())}self.words[0]=c;if !self.noadvance{self.words[1]+=1;}Ok(())}
}
fn begin(f:&mut Fake)->Capture{Capture::begin(f,&mut Cookies::new(),1,9).unwrap()}
fn finish(c:&mut Capture,f:&mut Fake)->Result<Snapshot,Error>{for i in 0..10{if let Some(s)=c.step(f,i+2,9)?{return Ok(s)}}panic!("incomplete")}
#[test]fn exact_order_and_all40(){let mut f=Fake::new();for i in 4..40{f.words[i]=i as u32}f.words[24]=0;f.words[25]=3;f.words[35]=0;f.words[38]=0;f.words[39]=0;let mut c=begin(&mut f);let s=finish(&mut c,&mut f).unwrap();assert_eq!(s.words,f.words);assert_eq!(f.ops.iter().filter(|(_,v)|*v!=0).count(),1);assert_eq!(&f.ops[0..6],&[(0,0),(4,0),(8,0),(0x184,0),(0x500,0),(0x504,0)]);assert_eq!(f.ops.len(),173);}
#[test]fn identity_reject_before_write(){for k in 0..4{let mut f=Fake::new();match k{0=>f.id=0,1=>f.schema=0,2=>f.caps=1,_=>f.image=0};assert!(matches!(Capture::begin(&mut f,&mut Cookies::new(),0,0),Err(Error::Identity)));assert!(f.ops.iter().all(|(_,v)|*v==0));}}
#[test]fn generation_must_advance(){let mut f=Fake::new();f.noadvance=true;let mut c=begin(&mut f);assert_eq!(finish(&mut c,&mut f),Err(Error::Generation));}
#[test]fn reset_rejects_cookie(){let mut f=Fake::new();let mut c=begin(&mut f);c.step(&mut f,2,9).unwrap();f.words[0]=0;f.words[1]=0;assert_eq!(finish(&mut c,&mut f),Err(Error::Cookie));}
#[test]fn other_capture_rejected(){let mut f=Fake::new();let mut c=begin(&mut f);f.words[0]+=1;assert_eq!(finish(&mut c,&mut f),Err(Error::Cookie));}
#[test]fn gen_torn_rejected(){let mut f=Fake::new();let mut c=begin(&mut f);f.words[1]+=1;assert_eq!(finish(&mut c,&mut f),Err(Error::Generation));}
#[test]fn identity_each_group(){let mut f=Fake::new();let mut c=begin(&mut f);c.step(&mut f,2,9).unwrap();f.image=0;assert_eq!(finish(&mut c,&mut f),Err(Error::Identity));}
#[test]fn epoch_and_timeout(){let mut f=Fake::new();let mut c=begin(&mut f);assert_eq!(c.step(&mut f,2,10),Err(Error::Epoch));assert_eq!(c.step(&mut f,500001,9),Err(Error::Timeout));}
#[test]fn quarantine_reserved_exhausted(){for bits in [8,1<<11,1<<12,1<<31]{let mut f=Fake::new();f.words[3]=bits;let mut c=begin(&mut f);assert!(finish(&mut c,&mut f).is_err());}}
#[test]fn reserved_and_invalid_canvas(){for (i,v) in [(25,128),(35,32),(35,16),(38,1),(39,1),(24,1<<31),(35,1)]{let mut f=Fake::new();f.words[i]=v;let mut c=begin(&mut f);assert_eq!(finish(&mut c,&mut f),Err(Error::Flags));}}
#[test]fn actual_crc_not_expected(){let mut f=Fake::new();f.words[32]=1;f.words[33]=0x12345678;f.words[34]=345600;f.words[35]=1;let mut c=begin(&mut f);assert_eq!(finish(&mut c,&mut f).unwrap().canvas_crc(),Some(0x12345678));}
#[test]fn cookie_nonreuse_skips_old(){let mut a=Cookies::new();assert_eq!(a.take(1),Ok(2));assert_eq!(a.take(0),Ok(3));assert_eq!(a.take(4),Ok(5));}
#[test]fn max_generation_refuses_write(){for g in [u32::MAX-1,u32::MAX]{let mut f=Fake::new();f.words[1]=g;assert!(matches!(Capture::begin(&mut f,&mut Cookies::new(),0,0),Err(Error::Generation)));assert!(f.ops.iter().all(|(_,v)|*v==0));}}
#[test]fn io_failure_propagated(){let mut f=Fake::new();let mut c=begin(&mut f);f.fault=true;assert_eq!(finish(&mut c,&mut f),Err(Error::Io));}
#[test]fn all_formatter_pages_bound_and_numeric_limb_order(){let mut s=Snapshot{words:[u32::MAX;40]};s.words[0]=0x1234;s.words[1]=u32::MAX-1;for i in 0..10{let line=page(&s,i).unwrap();assert!(line.as_str().len()<=192);assert!(!line.as_str().contains(['\r','\n']));assert!(line.as_str().contains(&format!("off={:03x}",0x500+i*16)));}assert!(page(&s,10).is_err());}

#[test]fn torn_inside_each_four_word_group_never_publishes(){for group in 0..10{let mut f=Fake::new();let mut c=begin(&mut f);f.torn_at=13+group*16+9;assert_eq!(finish(&mut c,&mut f),Err(Error::Cookie));}}

#[test]fn either_unlocked_rejected_but_incomplete_locked_allowed(){for locks in 0..4{let mut f=Fake::new();f.words[25]=locks;let mut c=begin(&mut f);let r=finish(&mut c,&mut f);assert_eq!(r.is_ok(),locks==3);}}
