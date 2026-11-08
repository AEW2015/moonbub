//! Pure policy for experimental, explicitly opted-in FPGA receive overlap.
//! The registers themselves remain owned by the streaming worker.
pub const CAP_OVERLAP: u32 = 0x20;
pub const SLOT_BYTES: u32 = 128 * 1024;
pub const MAX_BYTES: u32 = 256 * 1024;
pub const SMALL_ADMISSION: u32 = 1;
pub const LARGE_ADMISSION: u32 = 2;
pub const STATUS_READY: u32 = 1;
pub const STATUS_RECEIVING: u32 = 8;
pub const CMD_GLOBAL_ABORT: u32 = 2;
pub const CMD_RX_ABORT: u32 = 16;
pub const FAULT_RX: u32 = 1;
pub const FAULT_DECODER: u32 = 2;
pub const FAULT_TRANSPORT: u32 = 4;

/// Published by FPGA only at presentation. Register 0x58 starts at COMMIT,
/// therefore it includes any READY-slot wait before the decoder claims it.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PresentedTiming {
    pub frame_id: u32,
    pub receive_cycles: u32,
    pub commit_to_decode_complete_cycles_including_queue: u32,
    pub present_wait_cycles: u32,
    pub total_cycles: u32,
}
pub fn coherent_timing(id_before: u32, id_after: u32, count_before: u32, count_after: u32,
    receive: u32, commit_to_decode_complete: u32, present_wait: u32, total: u32) -> Option<PresentedTiming> {
    if count_before == 0 || count_before != count_after || id_before != id_after { return None; }
    Some(PresentedTiming { frame_id: id_before, receive_cycles: receive,
        commit_to_decode_complete_cycles_including_queue: commit_to_decode_complete,
        present_wait_cycles: present_wait, total_cycles: total })
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Mode { Legacy, Overlap }

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PolicyError { Version, Unsupported, Length, Busy, Receiving, BoundsMismatch }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FaultAction { None, ClearRx, StopSession }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CommitOutcome { Accepted, Rejected, Fatal }
pub fn commit_outcome(before: u32, after: u32, causes: u32) -> CommitOutcome {
    match fault_action(causes) {
        FaultAction::StopSession => CommitOutcome::Fatal,
        FaultAction::ClearRx => CommitOutcome::Rejected,
        FaultAction::None if after == before.wrapping_add(1) => CommitOutcome::Accepted,
        FaultAction::None => CommitOutcome::Rejected,
    }
}
/// Legacy cores expose a single sticky fault bit instead of per-cause flags.
/// Acceptance means the frame passed hardware byte-count/CRC/framing checks,
/// not that it decoded or was displayed.
pub fn legacy_commit_outcome(before: u32, after: u32, status: u32) -> CommitOutcome {
    if status & (1 << 2) != 0 { CommitOutcome::Rejected }
    else if after == before.wrapping_add(1) { CommitOutcome::Accepted }
    else { CommitOutcome::Rejected }
}
pub fn fault_action(causes: u32) -> FaultAction {
    if causes & !(FAULT_RX | FAULT_DECODER | FAULT_TRANSPORT) != 0
        || causes & (FAULT_DECODER | FAULT_TRANSPORT) != 0 { FaultAction::StopSession }
    else if causes & FAULT_RX != 0 { FaultAction::ClearRx }
    else { FaultAction::None }
}
pub trait Registers {
    type Error;
    fn read(&mut self, offset: u32) -> Result<u32, Self::Error>;
    fn write(&mut self, offset: u32, value: u32) -> Result<(), Self::Error>;
}
#[derive(Clone, Copy)]
pub struct Metadata { pub id: u32, pub length: u32, pub dimensions: u32, pub crc: u32 }
#[derive(Debug, PartialEq, Eq)]
pub enum StartError<E> { Io(E), Policy(PolicyError), FatalFault(u32), RxFault(u32), DidNotStart }
#[derive(Debug, PartialEq, Eq)]
pub enum AbortError<E> { Io(E), StillActive(u32), Fault(u32), NotReady(u32), StagingBusy(u32) }

/// The read after the ordered control write is a bridge barrier. RX-only
/// verification intentionally permits a concurrent decoder/pending frame.
pub fn abort_and_verify<R: Registers>(r: &mut R, mode: Mode, global: bool)
    -> Result<(), AbortError<R::Error>> {
    let command = abort_command(mode, global);
    r.write(0x24, command).map_err(AbortError::Io)?;
    let status = r.read(0x10).map_err(AbortError::Io)?;
    // Global abort must clear sticky fault as well as all ownership flags;
    // legacy cores have no per-cause register to check separately.
    let owned = if command == CMD_RX_ABORT { STATUS_RECEIVING } else { 2 | 4 | STATUS_RECEIVING | 16 };
    if status & owned != 0 { return Err(AbortError::StillActive(status)); }
    // Legacy READY includes the SDRAM abort barrier. Cleared ownership flags
    // alone do not mean a new frame may safely acquire the back buffer.
    if mode == Mode::Legacy && command == CMD_GLOBAL_ABORT && status & STATUS_READY == 0 {
        return Err(AbortError::NotReady(status));
    }
    if mode == Mode::Overlap {
        let causes = r.read(0x80).map_err(AbortError::Io)?;
        if causes != 0 { return Err(AbortError::Fault(causes)); }
        if command == CMD_GLOBAL_ABORT {
            let admission = r.read(0x7c).map_err(AbortError::Io)?;
            if admission & LARGE_ADMISSION == 0 { return Err(AbortError::StagingBusy(admission)); }
        }
    }
    Ok(())
}

/// Hardware sequence shared by the real driver and the host register mock.
/// A full staging pipeline never causes the existing decoder to be aborted.
pub fn start_overlap<R: Registers>(r: &mut R, m: Metadata, max: u32, slot: u32)
    -> Result<(), StartError<R::Error>> {
    let mut status = r.read(0x10).map_err(StartError::Io)?;
    let causes = r.read(0x80).map_err(StartError::Io)?;
    if fault_action(causes) == FaultAction::StopSession { return Err(StartError::FatalFault(causes)); }
    if status & STATUS_RECEIVING != 0 || causes & FAULT_RX != 0 {
        r.write(0x24, CMD_RX_ABORT).map_err(StartError::Io)?;
        status = r.read(0x10).map_err(StartError::Io)?;
    }
    let admission = r.read(0x7c).map_err(StartError::Io)?;
    can_start(Mode::Overlap, status, admission, m.length, max, slot).map_err(StartError::Policy)?;
    for (offset,value) in [(0x14,m.id),(0x18,m.length),(0x1c,m.dimensions),(0x20,m.crc)] {
        r.write(offset,value).map_err(StartError::Io)?;
    }
    let status = r.read(0x10).map_err(StartError::Io)?;
    let admission = r.read(0x7c).map_err(StartError::Io)?;
    can_start(Mode::Overlap, status, admission, m.length, max, slot).map_err(StartError::Policy)?;
    // Decode/presentation can progress during metadata writes. A hard fault
    // arising in that interval must never be mistaken for admission.
    let causes = r.read(0x80).map_err(StartError::Io)?;
    match fault_action(causes) {
        FaultAction::StopSession => return Err(StartError::FatalFault(causes)),
        FaultAction::ClearRx => return Err(StartError::RxFault(causes)),
        FaultAction::None => {}
    }
    r.write(0x24,1).map_err(StartError::Io)?;
    if r.read(0x10).map_err(StartError::Io)? & STATUS_RECEIVING == 0 { return Err(StartError::DidNotStart); }
    Ok(())
}

/// Never enable new register semantics solely from a version number.
pub fn requested_mode(request: bool, version: u32, caps: u32) -> Result<Mode, PolicyError> {
    if version >> 16 != 1 { return Err(PolicyError::Version); }
    if request && caps & CAP_OVERLAP == 0 { return Err(PolicyError::Unsupported); }
    Ok(if request { Mode::Overlap } else { Mode::Legacy })
}

/// Mode switching is permitted only when all hardware staging ownership is
/// idle; mode-0 core has no staging, and bit0 is its full-pipeline ready flag.
pub fn may_switch(current: Mode, status: u32, admission: u32) -> bool {
    match current {
        Mode::Legacy => status & STATUS_READY != 0,
        Mode::Overlap => admission & LARGE_ADMISSION != 0 && status & (2 | 8 | 16) == 0,
    }
}
/// A replacement sender cannot inherit any in-flight or staged frame from the
/// old source. A previously displayed front buffer is retained; its frame ID
/// must be attributed using the presentation-count epoch, not ID alone.
pub fn peer_rebind_quiescent(mode: Mode, status: u32, admission: u32, causes: u32, bench: u32) -> bool {
    if bench & 1 != 0 || status & 4 != 0 || causes != 0 { return false; }
    match mode {
        Mode::Legacy => status & STATUS_READY != 0,
        Mode::Overlap => may_switch(mode, status, admission),
    }
}

pub fn can_start(mode: Mode, status: u32, admission: u32, length: u32,
                 max: u32, overlap_slot: u32) -> Result<(), PolicyError> {
    if length == 0 || length > max || max > MAX_BYTES { return Err(PolicyError::Length); }
    match mode {
        Mode::Legacy => if status & STATUS_READY != 0 { Ok(()) } else { Err(PolicyError::Busy) },
        Mode::Overlap => {
            if overlap_slot != SLOT_BYTES { return Err(PolicyError::BoundsMismatch); }
            if status & STATUS_RECEIVING != 0 { return Err(PolicyError::Receiving); }
            let required = if length <= overlap_slot { SMALL_ADMISSION } else { LARGE_ADMISSION };
            if admission & required != 0 { Ok(()) } else { Err(PolicyError::Busy) }
        }
    }
}

/// During overlap, packet/CRC failures abort only the receiving slot; global
/// abort remains mandatory for transport corruption or session teardown.
pub fn abort_command(mode: Mode, global: bool) -> u32 {
    if mode == Mode::Overlap && !global { CMD_RX_ABORT } else { CMD_GLOBAL_ABORT }
}

#[cfg(test)]
mod tests {
    #[test] fn legacy_ack_requires_crc_checked_completion_and_no_fault() {
        use super::*;
        assert_eq!(legacy_commit_outcome(7,8,0),CommitOutcome::Accepted);
        assert_eq!(legacy_commit_outcome(u32::MAX,0,0),CommitOutcome::Accepted);
        assert_eq!(legacy_commit_outcome(7,7,0),CommitOutcome::Rejected);
        assert_eq!(legacy_commit_outcome(7,8,4),CommitOutcome::Rejected);
        assert_eq!(legacy_commit_outcome(7,9,0),CommitOutcome::Rejected);
    }
    use super::*;
    #[test] fn timing_labels_include_queue_and_reject_raced_reads() {
        let t=coherent_timing(42,42,8,8,11,22,33,66).unwrap();
        assert_eq!(t.frame_id,42);
        assert_eq!(t.commit_to_decode_complete_cycles_including_queue,22);
        assert_eq!((t.receive_cycles,t.present_wait_cycles,t.total_cycles),(11,33,66));
        assert!(coherent_timing(42,43,8,8,11,22,33,66).is_none());
        assert!(coherent_timing(42,42,8,9,11,22,33,66).is_none());
        assert!(coherent_timing(42,42,0,0,11,22,33,66).is_none());
    }
    #[test] fn version_and_explicit_optin_gate_new_semantics() {
        assert_eq!(requested_mode(false, 0x00010000, 3), Ok(Mode::Legacy));
        assert_eq!(requested_mode(false, 0x00010000, 0x23), Ok(Mode::Legacy));
        assert_eq!(requested_mode(true, 0x00010000, 3), Err(PolicyError::Unsupported));
        assert_eq!(requested_mode(true, 0x00010000, 0x23), Ok(Mode::Overlap));
        assert_eq!(requested_mode(true, 0x00020000, 0x23), Err(PolicyError::Version));
    }
    #[test] fn admission_respects_both_staging_limits_and_ownership() {
        assert_eq!(can_start(Mode::Overlap, 0, 1, SLOT_BYTES, MAX_BYTES, SLOT_BYTES), Ok(()));
        assert_eq!(can_start(Mode::Overlap, 0, 1, SLOT_BYTES+1, MAX_BYTES, SLOT_BYTES), Err(PolicyError::Busy));
        assert_eq!(can_start(Mode::Overlap, 0, 2, MAX_BYTES, MAX_BYTES, SLOT_BYTES), Ok(()));
        assert_eq!(can_start(Mode::Overlap, 8, 3, 64, MAX_BYTES, SLOT_BYTES), Err(PolicyError::Receiving));
        assert_eq!(can_start(Mode::Overlap, 0, 3, 64, MAX_BYTES, 64), Err(PolicyError::BoundsMismatch));
        assert_eq!(can_start(Mode::Overlap, 0, 3, MAX_BYTES+1, MAX_BYTES, SLOT_BYTES), Err(PolicyError::Length));
        assert_eq!(can_start(Mode::Legacy, 0, 3, 64, MAX_BYTES, 0), Err(PolicyError::Busy));
        assert_eq!(can_start(Mode::Legacy, 1, 0, 64, MAX_BYTES, 0), Ok(()));
    }
    #[test] fn abort_scope_and_idle_mode_switch_are_explicit() {
        assert_eq!(abort_command(Mode::Legacy,false),2);
        assert_eq!(abort_command(Mode::Overlap,false),16);
        assert_eq!(abort_command(Mode::Overlap,true),2);
        assert!(!may_switch(Mode::Legacy,0,3));
        assert!(may_switch(Mode::Legacy,1,0));
        assert!(!may_switch(Mode::Overlap,0,1));
        assert!(may_switch(Mode::Overlap,0,2));
        assert!(!may_switch(Mode::Overlap,2,2));
        assert!(!may_switch(Mode::Overlap,8,2));
        assert!(!may_switch(Mode::Overlap,16,2));
    }
    #[test] fn peer_rebind_waits_for_decoder_ready_queue_pending_and_faults() {
        assert!(peer_rebind_quiescent(Mode::Legacy,1,0,0,0));
        assert!(!peer_rebind_quiescent(Mode::Legacy,0,0,0,0));
        assert!(!peer_rebind_quiescent(Mode::Legacy,1|4,0,0,0));
        assert!(peer_rebind_quiescent(Mode::Overlap,1,3,0,0));
        assert!(!peer_rebind_quiescent(Mode::Overlap,2,2,0,0));
        assert!(!peer_rebind_quiescent(Mode::Overlap,16,2,0,0));
        assert!(!peer_rebind_quiescent(Mode::Overlap,1,1,0,0));
        assert!(!peer_rebind_quiescent(Mode::Overlap,1,3,FAULT_RX,0));
        assert!(!peer_rebind_quiescent(Mode::Overlap,1,3,0,1));
    }
    #[test] fn unrelated_decoder_and_transport_faults_are_never_cleared_as_rx() {
        assert_eq!(fault_action(0),FaultAction::None);
        assert_eq!(fault_action(FAULT_RX),FaultAction::ClearRx);
        assert_eq!(fault_action(FAULT_DECODER),FaultAction::StopSession);
        assert_eq!(fault_action(FAULT_RX|FAULT_TRANSPORT),FaultAction::StopSession);
        assert_eq!(fault_action(FAULT_RX|FAULT_DECODER),FaultAction::StopSession);
        assert_eq!(fault_action(8),FaultAction::StopSession);
    }
    #[test] fn ack_requires_fpga_crc_commit_and_handles_counter_wrap() {
        assert_eq!(commit_outcome(9,10,0),CommitOutcome::Accepted);
        assert_eq!(commit_outcome(u32::MAX,0,0),CommitOutcome::Accepted);
        assert_eq!(commit_outcome(9,9,0),CommitOutcome::Rejected);
        assert_eq!(commit_outcome(9,10,FAULT_RX),CommitOutcome::Rejected);
        assert_eq!(commit_outcome(9,10,FAULT_DECODER),CommitOutcome::Fatal);
        assert_eq!(commit_outcome(9,10,FAULT_TRANSPORT|FAULT_RX),CommitOutcome::Fatal);
    }
    #[derive(Default)]
    struct Fake { status:u32, causes:u32, admission:u32, writes:Vec<(u32,u32)>, lose_admission_after_metadata:bool, fault_after_metadata:u32, decoder_intact:bool, ignore_abort:bool, fail_reads:bool, fail_writes:bool }
    impl Registers for Fake {
        type Error = ();
        fn read(&mut self, offset:u32)->Result<u32,()> { if self.fail_reads{return Err(());} Ok(match offset {0x10=>self.status,0x80=>self.causes,0x7c=>self.admission,_=>0}) }
        fn write(&mut self, offset:u32, value:u32)->Result<(),()> {
            if self.fail_writes { return Err(()); }
            self.writes.push((offset,value));
            if offset==0x24 && value==CMD_RX_ABORT && !self.ignore_abort { self.status &= !STATUS_RECEIVING; self.causes &= !FAULT_RX; }
            if offset==0x24 && value==CMD_GLOBAL_ABORT && !self.ignore_abort { self.decoder_intact=false; self.status &= !(2|4|STATUS_RECEIVING|16); self.causes=0; }
            if offset==0x24 && value==1 { self.status |= STATUS_RECEIVING; }
            if offset==0x20 && self.lose_admission_after_metadata { self.admission=0; }
            if offset==0x20 { self.causes |= self.fault_after_metadata; }
            Ok(())
        }
    }
    fn metadata(length:u32)->Metadata { Metadata{id:7,length,dimensions:(720<<16)|480,crc:42} }
    #[test] fn staging_busy_does_not_abort_an_existing_decode() {
        let mut r=Fake{status:2,admission:0,decoder_intact:true,..Fake::default()};
        assert_eq!(start_overlap(&mut r,metadata(10),MAX_BYTES,SLOT_BYTES),Err(StartError::Policy(PolicyError::Busy)));
        assert!(r.writes.is_empty());assert!(r.decoder_intact);
    }
    #[test] fn rx_fault_clears_only_rx_and_preserves_decoder() {
        let mut r=Fake{status:2|8,causes:FAULT_RX,admission:1,decoder_intact:true,..Fake::default()};
        assert_eq!(start_overlap(&mut r,metadata(10),MAX_BYTES,SLOT_BYTES),Ok(()));
        assert_eq!(r.writes[0],(0x24,CMD_RX_ABORT));assert!(r.decoder_intact);
        assert!(!r.writes.contains(&(0x24,CMD_GLOBAL_ABORT)));
    }
    #[test] fn fatal_fault_and_admission_race_never_start_or_abort_decode() {
        let mut fatal=Fake{status:2,causes:FAULT_DECODER,admission:1,decoder_intact:true,..Fake::default()};
        assert_eq!(start_overlap(&mut fatal,metadata(10),MAX_BYTES,SLOT_BYTES),Err(StartError::FatalFault(FAULT_DECODER)));
        assert!(fatal.writes.is_empty());assert!(fatal.decoder_intact);
        let mut race=Fake{status:2,admission:1,decoder_intact:true,lose_admission_after_metadata:true,..Fake::default()};
        assert_eq!(start_overlap(&mut race,metadata(10),MAX_BYTES,SLOT_BYTES),Err(StartError::Policy(PolicyError::Busy)));
        assert!(!race.writes.iter().any(|&(o,_)|o==0x24));assert!(race.decoder_intact);
        let mut late=Fake{status:2,admission:1,decoder_intact:true,fault_after_metadata:FAULT_TRANSPORT,..Fake::default()};
        assert_eq!(start_overlap(&mut late,metadata(10),MAX_BYTES,SLOT_BYTES),Err(StartError::FatalFault(FAULT_TRANSPORT)));
        assert!(!late.writes.iter().any(|&(o,_)|o==0x24));assert!(late.decoder_intact);
    }
    #[test] fn abort_readback_preserves_decoder_and_rejects_unconfirmed_recovery() {
        let mut healthy=Fake{status:2|STATUS_RECEIVING,admission:1,decoder_intact:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut healthy,Mode::Overlap,false),Ok(()));
        assert!(healthy.decoder_intact);assert_eq!(healthy.status,2);
        let mut stuck=Fake{status:2|STATUS_RECEIVING,admission:1,decoder_intact:true,ignore_abort:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut stuck,Mode::Overlap,false),Err(AbortError::StillActive(10)));
        assert!(stuck.decoder_intact);
        let mut busy=Fake{status:0,admission:0,..Fake::default()};
        assert_eq!(abort_and_verify(&mut busy,Mode::Overlap,true),Err(AbortError::StagingBusy(0)));
        let mut hard=Fake{status:2|STATUS_RECEIVING,causes:FAULT_DECODER,admission:1,decoder_intact:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut hard,Mode::Overlap,false),Err(AbortError::Fault(FAULT_DECODER)));
        assert!(hard.decoder_intact);
        let mut broken=Fake{fail_reads:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut broken,Mode::Overlap,false),Err(AbortError::Io(())));
        let mut failed_abort_write=Fake{status:STATUS_RECEIVING,fail_writes:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut failed_abort_write,Mode::Overlap,false),Err(AbortError::Io(())));
        assert_eq!(failed_abort_write.status,STATUS_RECEIVING);
        let mut legacy_fault=Fake{status:1|4,ignore_abort:true,..Fake::default()};
        assert_eq!(abort_and_verify(&mut legacy_fault,Mode::Legacy,true),Err(AbortError::StillActive(5)));
        let mut legacy_barrier=Fake{status:0,..Fake::default()};
        assert_eq!(abort_and_verify(&mut legacy_barrier,Mode::Legacy,true),Err(AbortError::NotReady(0)));
        // Once the external SDRAM drain barrier deasserts, READY makes retry safe.
        legacy_barrier.status=1;
        assert_eq!(abort_and_verify(&mut legacy_barrier,Mode::Legacy,true),Ok(()));
    }
}
