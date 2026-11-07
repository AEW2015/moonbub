//! One failed-frame identity; no allocation, timers, ACK or receiver mutation.
//! Caller may discard only after confirmed recovery, with no active assembler.
use super::protocol::Header;

#[derive(Default)]
pub struct RejectedTail(Option<Header>);

impl RejectedTail {
    /// Install only after the normal first error/abort/rejection path completes.
    pub fn recovered(&mut self, header: Option<Header>) { self.0 = header; }
    pub fn clear(&mut self) { self.0 = None; }
    pub fn discard(&self, header: Header, active: bool) -> bool {
        let Some(failed) = self.0 else { return false; };
        !active && header.offset != 0
            && header.id == failed.id && header.capture_us == failed.capture_us
            && header.width == failed.width && header.height == failed.height
            && header.length == failed.length && header.crc == failed.crc
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::{self, Receiver};

    fn packet(id:u32, capture:u64, offset:usize, data:&[u8]) -> Vec<u8> {
        let end=(offset+1024).min(data.len());
        let mut p=vec![0;40+end-offset];p[..4].copy_from_slice(b"MSV1");p[4]=1;p[5]=1;
        let flags=u16::from(offset==0)|u16::from(end==data.len())<<1;
        p[6..8].copy_from_slice(&flags.to_be_bytes());p[8..12].copy_from_slice(&id.to_be_bytes());
        p[12..14].copy_from_slice(&720u16.to_be_bytes());p[14..16].copy_from_slice(&480u16.to_be_bytes());
        p[16..20].copy_from_slice(&(data.len()as u32).to_be_bytes());p[20..24].copy_from_slice(&(offset as u32).to_be_bytes());
        p[24..26].copy_from_slice(&((end-offset)as u16).to_be_bytes());
        p[28..32].copy_from_slice(&(!protocol::crc_update(!0,data)).to_be_bytes());p[32..40].copy_from_slice(&capture.to_be_bytes());
        p[40..].copy_from_slice(&data[offset..end]);p
    }
    #[test]
    fn failed_frame_tails_bypass_only_after_first_failure_and_recovery() {
        let data=vec![7;16*1024];let mut receiver=Receiver::default();let mut filter=RejectedTail::default();
        let first=packet(27,91,0,&data);let gap=packet(27,91,2048,&data);
        assert!(!filter.discard(Header::parse(&gap).unwrap(),false));
        receiver.accept(&first).unwrap();assert_eq!(receiver.accept(&gap),Err(protocol::Error::Sequence));
        // Models successful physical abort and first rejection send before install.
        filter.recovered(Some(Header::parse(&gap).unwrap()));
        for offset in (3072..data.len()).step_by(1024) {
            let h=Header::parse(&packet(27,91,offset,&data)).unwrap();
            assert!(filter.discard(h,receiver.active_identity().is_some()));
            assert!(!filter.discard(h,true));
        }
        // A newer SOF still reaches the actual parser and completes its CRC.
        for offset in (0..data.len()).step_by(1024) {
            let p=packet(28,92,offset,&data);let h=Header::parse(&p).unwrap();
            assert!(!filter.discard(h,receiver.active_identity().is_some()));
            let (_,done)=receiver.accept(&p).unwrap();if offset==0{filter.clear();}
            assert_eq!(done,offset+1024==data.len());
        }
        assert!(!filter.discard(Header::parse(&gap).unwrap(),false));
    }
    #[test]
    fn every_identity_field_and_sof_active_gate_is_required() {
        let data=vec![4;4096];let h=Header::parse(&packet(0,0,2048,&data)).unwrap();
        let mut f=RejectedTail::default();f.recovered(Some(h));assert!(f.discard(h,false));
        let variants=[Header{id:1,..h},Header{capture_us:1,..h},Header{width:1280,..h},Header{height:720,..h},Header{length:8192,..h},Header{crc:h.crc^1,..h},Header{offset:0,..h}];
        for changed in variants{assert!(!f.discard(changed,false));}
        assert!(!f.discard(h,true));f.recovered(None);assert!(!f.discard(h,false));
    }
    #[test]
    fn malformed_bounds_and_flags_cannot_enter_validated_tail_path() {
        let data=vec![4;4096];let p=packet(9,5,2048,&data);
        for index in [0usize,4,5,6,12,16,20,24,26] {
            let mut bad=p.clone();bad[index]^=0xff;assert!(Header::parse(&bad).is_err(),"byte {index}");
        }
    }
    #[test]
    fn wraparound_and_reused_id_with_new_capture_still_reach_receiver() {
        let data=vec![3;2048];let mut f=RejectedTail::default();
        f.recovered(Some(Header::parse(&packet(u32::MAX,88,1024,&data)).unwrap()));
        let mut rx=Receiver::default();
        for id in [u32::MAX,0,1] {
            for off in [0,1024] {
                let p=packet(id,99,off,&data);let h=Header::parse(&p).unwrap();
                assert!(!f.discard(h,rx.active_identity().is_some()));rx.accept(&p).unwrap();
                if off==0{f.clear();}
            }
        }
    }
}
