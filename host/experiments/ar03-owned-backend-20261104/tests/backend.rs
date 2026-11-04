#![allow(dead_code)]
#[path = "../../../ar03-receiver-core-20261104/handheld/src/streaming/ar03_lab/mod.rs"]
mod ar03_lab;
#[path = "../src/backend.rs"]
mod backend;
use ar03_lab::{frame::Control, packet::*, wire::{self, Frame, Kind, Status}};
use backend::*;
use std::cell::Cell;

struct Fake {
    capacity: Cell<Capacity>, result: Cell<Option<Completion>>, foreign: Cell<u8>,
    retirement: Cell<bool>, reserves: Cell<usize>, retires: Cell<usize>, unknown_poll: Cell<bool>,
}
impl Fake {
    fn new() -> Self { Self { capacity: Cell::new(Capacity::Granted(1)), result: Cell::new(None),
        foreign: Cell::new(0), retirement: Cell::new(true), reserves: Cell::new(0), retires: Cell::new(0), unknown_poll: Cell::new(false) } }
}
impl Fifo for Fake {
    fn reserve_capacity(&mut self, _: Identity, lease: BufferLease) -> Capacity {
        self.reserves.set(self.reserves.get()+1);
        match self.capacity.get() { Capacity::Granted(1) => Capacity::Granted(lease.id), other => other }
    }
    fn poll(&mut self, identity: Identity, lease: BufferLease, ticket: u64) -> Poll {
        if self.unknown_poll.get() { return Poll::Unknown; }
        let Some(result) = self.result.get() else { return Poll::Pending; };
        let mut p = Proof { identity, lease, ticket, result };
        match self.foreign.get() {
            1 => p.identity.owner.nonce ^= 1,
            2 => p.lease.id += 1,
            3 => p.ticket += 1,
            4 => p.identity.route.body_crc ^= 1,
            5 => p.lease.fifo_bytes += 1,
            _ => (),
        }
        Poll::Done(p)
    }
    fn retire(&mut self, _: Proof) -> bool { self.retires.set(self.retires.get()+1); self.retirement.get() }
}
fn grant(g: &mut Gateway, total: u32) -> Frame {
    let f = Frame { epoch:1, frame:7, total, body_crc:0x12345678, nonce:0x100000001,
        slot:0, kind:Kind::Request };
    let Control::Reply(r) = g.frame_control(f).unwrap() else { panic!() };
    assert_eq!(r.kind, Kind::Grant);
    assert!(g.complete_control(ControlIdentity::Frame(f), ControlDone::ReplyEnqueued)); r
}
fn packet(f: Frame, index: u16, slot: u16, sequence: u64) -> Vec<u8> {
    let n=(f.total-index as u32*1008).min(1008) as u16;
    let mut p=Vec::new(); p.extend(1u32.to_be_bytes()); p.extend(slot.to_be_bytes());
    p.extend(0u16.to_be_bytes());p.extend(sequence.to_be_bytes());p.extend(b"GF03");p.push(3);
    for v in [1,f.frame,f.total] {p.extend(v.to_be_bytes());}
    for v in [index, ((f.total+1007)/1008) as u16,n] {p.extend(v.to_be_bytes());}
    p.extend(0x98765432u32.to_be_bytes());p.extend(f.body_crc.to_be_bytes());
    p.resize(47+n as usize,0xa5);p
}
fn setup() -> (Gateway, OwnedBackend<Fake>, Frame) {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,1008);
    (g,OwnedBackend::cold(Fake::new()),f)
}
#[test] fn copied_rx_is_owned_and_token_is_excluded_from_fifo() {
    let (mut g,mut b,f)=setup();let mut p=packet(f,0,0,1);
    let identity=g.admit(&p,&mut b).unwrap();let lease=b.lease(identity).unwrap();
    let expected=p.clone();p.fill(0);
    assert_eq!(b.bytes(identity,lease).unwrap(),expected);
    assert_eq!(b.fifo_payload(identity,lease).unwrap(),&expected[16..]);
    assert_eq!(lease.datagram_bytes,1055);assert_eq!(lease.fifo_bytes,1039);
}
#[test] fn pending_holds_both_owners_and_produces_no_receipt() {
    let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    assert_eq!(b.poll_one(&mut g,id,l),Progress::Pending);
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(!g.physical_drain(f));
}
#[test] fn consumed_and_rejected_follow_transport_status() {
    for (completion,status) in [(Completion::Consumed,Status::Consumed),(Completion::Rejected,Status::Rejected)] {
        let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
        b.transport().result.set(Some(completion));
        let Progress::Completed(Completed::Receipt(r))=b.poll_one(&mut g,id,l)else{panic!()};
        assert_eq!(r.status,status);assert_eq!((b.retained(),g.packet_count()),(0,0));
        assert_eq!(b.poll_one(&mut g,id,l),Progress::Stale);assert_eq!(b.transport().retires.get(),1);
    }
}
#[test] fn no_capacity_acquires_no_ownership() {
    let(mut g,mut b,f)=setup();b.transport().capacity.set(Capacity::Unavailable);
    assert_eq!(g.admit(&packet(f,0,0,1),&mut b),Err(AdmissionError::NoCapacity));
    assert_eq!((b.retained(),g.packet_count()),(0,0));assert!(!g.stopped());
}
#[test] fn ambiguous_reservation_retains_bytes_and_stops() {
    let(mut g,mut b,f)=setup();b.transport().capacity.set(Capacity::Unknown);
    assert_eq!(g.admit(&packet(f,0,0,1),&mut b),Err(AdmissionError::Ambiguous));
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(g.stopped()&&b.stopped());
}
#[test] fn stale_proofs_never_release_current_slot() {
    for mutation in 1..=5 {
        let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
        b.transport().result.set(Some(Completion::Consumed));b.transport().foreign.set(mutation);
        assert_eq!(b.poll_one(&mut g,id,l),Progress::Stale);assert_eq!(b.retained(),1);
        assert_eq!(b.transport().retires.get(),0);assert!(!g.stopped());
        b.transport().foreign.set(0);assert!(matches!(b.poll_one(&mut g,id,l),Progress::Completed(Completed::Receipt(_))));
    }
}
#[test] fn unknown_completion_retains_ownership() {
    let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    b.transport().result.set(Some(Completion::Unknown));assert_eq!(b.poll_one(&mut g,id,l),Progress::SafeStop);
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert_eq!(b.transport().retires.get(),0);
}
#[test] fn unknown_retirement_cannot_recycle_a_completed_buffer() {
    let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    b.transport().result.set(Some(Completion::Consumed));b.transport().retirement.set(false);
    assert_eq!(b.poll_one(&mut g,id,l),Progress::Completed(Completed::SafeStop));
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(b.stopped()&&g.stopped());
}
#[test] fn five_datagrams_are_bounded_and_control_position_is_not_storage() {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,6*1008);let mut b=OwnedBackend::cold(Fake::new());
    for i in 0..5 {g.admit(&packet(f,i,i,1),&mut b).unwrap();}
    assert_eq!((b.retained(),g.packet_count()),(5,5));
    assert_eq!(g.admit(&packet(f,5,5,1),&mut b),Err(AdmissionError::ReservedControlPosition));
    assert_eq!(b.transport().reserves.get(),5);
}
#[test] fn reused_slot_has_new_lease_old_completion_is_stale() {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,2016);let mut b=OwnedBackend::cold(Fake::new());
    let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    b.transport().result.set(Some(Completion::Consumed));b.poll_one(&mut g,id,l);
    let id2=g.admit(&packet(f,1,0,2),&mut b).unwrap();let l2=b.lease(id2).unwrap();assert_ne!(l.id,l2.id);
    assert_eq!(b.poll_one(&mut g,id,l),Progress::Stale);assert_eq!(b.retained(),1);
    assert!(b.bytes(id,l).is_none());assert!(b.bytes(id2,l2).is_some());
}
#[test] fn direct_premature_release_fails_closed() {
    let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    assert!(!Backend::release(&mut b,id,l));assert_eq!(b.retained(),1);assert!(b.stopped());
}
#[test] fn invalid_bytes_never_reach_capacity_adapter() {
    let(g,mut b,f)=setup();let p=packet(f,0,0,1);let route=wire::parse_data(&p).unwrap();let id=Identity{owner:f,route};
    let mut bad=p;bad[16]^=1;
    assert_eq!(Backend::reserve(&mut b,id,&bad,1039),Reservation::Unavailable);
    assert_eq!(b.transport().reserves.get(),0);assert_eq!(g.packet_count(),0);
}
#[test] fn zero_ticket_stops_and_pins_both_ledgers() {
    let(mut g,mut b,f)=setup();b.transport().capacity.set(Capacity::Granted(0));
    assert_eq!(g.admit(&packet(f,0,0,1),&mut b),Err(AdmissionError::Ambiguous));
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(b.stopped()&&g.stopped());
}
#[test] fn duplicate_active_ticket_does_not_recycle_either_packet() {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,2016);let mut b=OwnedBackend::cold(Fake::new());
    b.transport().capacity.set(Capacity::Granted(19));g.admit(&packet(f,0,0,1),&mut b).unwrap();
    assert_eq!(g.admit(&packet(f,1,1,1),&mut b),Err(AdmissionError::Ambiguous));
    assert_eq!((b.retained(),g.packet_count()),(2,2));assert!(b.stopped()&&g.stopped());
}
#[test] fn no_capacity_retry_keeps_the_original_packet_sequence_usable() {
    let(mut g,mut b,f)=setup();let p=packet(f,0,0,1);b.transport().capacity.set(Capacity::Unavailable);
    assert_eq!(g.admit(&p,&mut b),Err(AdmissionError::NoCapacity));
    b.transport().capacity.set(Capacity::Granted(1));let id=g.admit(&p,&mut b).unwrap();
    assert_eq!(b.bytes(id,b.lease(id).unwrap()).unwrap(),p);assert_eq!(b.retained(),1);
}
#[test] fn unknown_poll_is_a_retained_safe_stop() {
    let(mut g,mut b,f)=setup();let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    b.transport().unknown_poll.set(true);assert_eq!(b.poll_one(&mut g,id,l),Progress::SafeStop);
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(b.stopped()&&g.stopped());
}
#[test] fn wrong_fifo_length_is_rejected_before_hardware_reservation() {
    let(g,mut b,f)=setup();let p=packet(f,0,0,1);let id=Identity{owner:f,route:wire::parse_data(&p).unwrap()};
    assert_eq!(Backend::reserve(&mut b,id,&p,1040),Reservation::Unavailable);
    assert_eq!(b.transport().reserves.get(),0);assert_eq!(b.retained(),0);assert_eq!(g.packet_count(),0);
}
#[test] fn short_final_fragment_retains_only_its_exact_byte_range() {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,1009);let mut b=OwnedBackend::cold(Fake::new());
    let p=packet(f,1,0,1);let id=g.admit(&p,&mut b).unwrap();let l=b.lease(id).unwrap();
    assert_eq!((l.datagram_bytes,l.fifo_bytes),(48,32));assert_eq!(b.bytes(id,l).unwrap(),p);
}
#[test] fn pending_poll_budget_exhaustion_retains_owners_and_stops() {
    assert!(OwnedBackend::cold_bounded(Fake::new(),0).is_none());
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,1008);
    let mut b=OwnedBackend::cold_bounded(Fake::new(),3).unwrap();
    let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    for _ in 0..3 {assert_eq!(b.poll_one(&mut g,id,l),Progress::Pending);}
    assert_eq!(b.poll_one(&mut g,id,l),Progress::SafeStop);
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert!(b.stopped()&&g.stopped());
    assert_eq!(b.transport().retires.get(),0);
}
#[test] fn repeated_foreign_proof_is_also_bounded_without_a_credit() {
    let mut g=Gateway::cold_epoch1(true);let f=grant(&mut g,1008);
    let mut b=OwnedBackend::cold_bounded(Fake::new(),2).unwrap();
    let id=g.admit(&packet(f,0,0,1),&mut b).unwrap();let l=b.lease(id).unwrap();
    b.transport().result.set(Some(Completion::Consumed));b.transport().foreign.set(1);
    for _ in 0..2 {assert_eq!(b.poll_one(&mut g,id,l),Progress::Stale);}
    assert_eq!(b.poll_one(&mut g,id,l),Progress::SafeStop);
    assert_eq!((b.retained(),g.packet_count()),(1,1));assert_eq!(b.transport().retires.get(),0);
}
