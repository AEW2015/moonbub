"""Derive bounded-three tests from the preserved pair's real-native/MMIO harness."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]
f=p/'tests/network_driver.rs';s=f.read_text()
s=s.replace('struct Fake{time:', 'struct Fake{lost_commit_frame:Option<u32>,time:')
s=s.replace('Self{time:', 'Self{lost_commit_frame:None,time:')
s=s.replace('if !self.lost_ack&&!(self.postcommit_loss&&value==20)', 'if !self.lost_ack&&!(self.postcommit_loss&&value==20)&&!(self.lost_commit_frame==Some(self.frame())&&value==20)')
s+='''
struct ThreeInput{index:usize,fail_third:bool}
impl ThreeInput{fn bytes(&self)->&'static[u8]{match self.index{0=>include_bytes!("../handheld/src/cu66/fixtures/packet0.cu66"),1=>include_bytes!("../handheld/src/cu66/fixtures/packet1.cu66"),2=>include_bytes!("../handheld/src/cu66/fixtures/packet2.cu66"),_=>panic!("source consumed beyond bounded trial")}}}
impl nd::Source for ThreeInput{
 fn header(&mut self)->Result<nd::Header,Error>{if self.fail_third&&self.index==2{return Err(Error::Deadline)}let b=self.bytes();let mut prefix=[0;76];prefix.copy_from_slice(&b[..76]);Ok(nd::Header{prefix,length:b.len(),crc:framing::crc32(b)})}
 fn read(&mut self,offset:usize,out:&mut[u8;1024])->Result<usize,Error>{let b=self.bytes();let n=(b.len()-offset).min(1024);out[..n].copy_from_slice(&b[offset..offset+n]);Ok(n)}
 fn stored(&mut self,_:usize)->Result<(),Error>{Ok(())}
 fn presented(&mut self)->Result<(),Error>{self.index+=1;Ok(())}
}
#[test]fn actual_native_three_distinct_frames_reuse(){let mut b=dy_fake();let mut h=hud::Hud::new(98304).unwrap();let mut source=ThreeInput{index:0,fail_third:false};let(r,_)=nd::run_sequence(&mut b,&mut h,&mut source,3).unwrap();assert_eq!((r.frames,r.accepted,r.presented,r.rejected,r.words_written,r.words_verified),(3,3,3,0,63360,63360));assert_eq!(source.index,3);assert_eq!(b.drains,3);assert!(!b.active);for i in 0..3{assert!(r.admission_us[i]<=r.hud_pending_us[i]);assert!(r.hud_pending_us[i]<=r.hud_snapshot_us[i]);assert!(r.hud_snapshot_us[i]<=r.hu_extract_start_us[i]);assert!(r.hu_extract_start_us[i]<=r.hu_extract_done_us[i]);assert!(r.hu_extract_done_us[i]<=r.native_start_us[i]);assert!(r.native_start_us[i]<=r.native_done_us[i]);assert!(r.native_done_us[i]<=r.hud_valid_us[i]);assert!(r.hud_write_done_us[i]<=r.hud_readback_done_us[i]);assert!(r.software_commit_acked_us[i]<=r.presentation_observed_us[i]);assert!(r.hu_extract_commands[i]>0);}assert_eq!(b.frame(),2);assert_eq!(b.reference(),1);}
#[test]fn invalid_frame_limits_before_any_writes(){for limit in [0,4,usize::MAX]{let mut b=dy_fake();let mut h=hud::Hud::new(98304).unwrap();assert!(matches!(nd::run_sequence(&mut b,&mut h,&mut ThreeInput{index:0,fail_third:false},limit),Err(Error::Bounds)));assert_eq!(b.physical_writes,0);}}
#[test]fn missing_third_does_not_fake_presentation(){let mut b=dy_fake();let mut h=hud::Hud::new(98304).unwrap();let mut source=ThreeInput{index:0,fail_third:true};assert!(matches!(nd::run_sequence(&mut b,&mut h,&mut source,3),Err(Error::Deadline)));assert_eq!(source.index,2);assert_eq!(b.accepted,2);assert!(!b.active);}
#[test]fn lost_third_commit_ack_does_not_fake_presentation(){let mut b=dy_fake();b.lost_commit_frame=Some(2);let mut h=hud::Hud::new(98304).unwrap();let mut source=ThreeInput{index:0,fail_third:false};assert!(matches!(nd::run_sequence(&mut b,&mut h,&mut source,3),Err(Error::MailboxTimeout{operation:20,..})));assert_eq!(source.index,2);let mut req=[0u8;36];req[..4].copy_from_slice(b"HC70");req[4]=1;req[5]=2;let crc=framing::crc32(&req[..32]);req[32..].copy_from_slice(&crc.to_le_bytes());let mut out=[0u8;108];let response=framing::decode(h.transact(&req,&mut out).unwrap()).unwrap();assert_eq!(n32(response.payload,48),2);}
'''
f.write_text(s)
f=p/'handheld/src/cu66/network_usb.rs';s=f.read_text().replace('profile=DY71_ABI2_BULK_LAB3','profile=dy71-bounded3-v1');f.write_text(s)
print('V44_THREE_TESTS_PREPARED')
