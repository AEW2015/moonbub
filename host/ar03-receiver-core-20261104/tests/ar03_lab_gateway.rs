#![allow(dead_code)]
#[path = "../handheld/src/streaming/ar03_lab/mod.rs"]
mod ar03_lab;
use ar03_lab::{
    frame::{Control, Frames},
    packet::*,
    wire::{self, Frame, Kind, Query, Receipt, Status},
};
fn request(frame: u32, nonce: u64, slot: u16, total: u32) -> Frame {
    Frame {
        epoch: 1,
        frame,
        nonce,
        slot,
        total,
        body_crc: 0x12345678,
        kind: Kind::Request,
    }
}
fn grant(g: &mut Gateway, f: Frame) -> Frame {
    let Control::Reply(r) = g.frame_control(f).unwrap() else {
        panic!()
    };
    assert_eq!(r.kind, Kind::Grant);
    assert!(g.complete_control(ControlIdentity::Frame(f), ControlDone::ReplyEnqueued));
    r
}
fn data(f: Frame, index: u16, slot: u16, sequence: u64) -> Vec<u8> {
    let count = ((f.total + 1007) / 1008) as u16;
    let size = (f.total - index as u32 * 1008).min(1008) as u16;
    let mut p = Vec::new();
    p.extend(1u32.to_be_bytes());
    p.extend(slot.to_be_bytes());
    p.extend(0u16.to_be_bytes());
    p.extend(sequence.to_be_bytes());
    p.extend(b"GF03");
    p.push(3);
    p.extend(1u32.to_be_bytes());
    p.extend(f.frame.to_be_bytes());
    p.extend(f.total.to_be_bytes());
    p.extend(index.to_be_bytes());
    p.extend(count.to_be_bytes());
    p.extend(size.to_be_bytes());
    p.extend(0x98765432u32.to_be_bytes());
    p.extend(f.body_crc.to_be_bytes());
    p.resize(47 + size as usize, index as u8);
    p
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Mode {
    Normal,
    Unavailable,
    Unknown,
    UnderCapacity,
    DuplicateId,
}
#[derive(Clone, Copy)]
struct Stored {
    identity: Identity,
    lease: BufferLease,
    bytes: [u8; 1055],
    len: usize,
}
struct Fake {
    storage: [Option<Stored>; 5],
    next: u64,
    mode: Mode,
    reserves: u32,
    releases: u32,
    release_unknown: bool,
}
impl Fake {
    fn new() -> Self {
        Self {
            storage: [None; 5],
            next: 1,
            mode: Mode::Normal,
            reserves: 0,
            releases: 0,
            release_unknown: false,
        }
    }
    fn id(&self, identity: Identity) -> u64 {
        self.storage
            .iter()
            .flatten()
            .find(|s| s.identity == identity)
            .unwrap()
            .lease
            .id
    }
    fn bytes(&self, id: u64) -> &[u8] {
        let s = self
            .storage
            .iter()
            .flatten()
            .find(|s| s.lease.id == id)
            .unwrap();
        &s.bytes[..s.len]
    }
}
impl Backend for Fake {
    fn reserve(&mut self, identity: Identity, p: &[u8], fifo: u16) -> Reservation {
        self.reserves += 1;
        if self.mode == Mode::Unavailable {
            return Reservation::Unavailable;
        }
        let Some(slot) = self.storage.iter_mut().find(|s| s.is_none()) else {
            return Reservation::Unavailable;
        };
        let id = if self.mode == Mode::DuplicateId {
            1
        } else {
            self.next
        };
        self.next += 1;
        let lease = BufferLease {
            id,
            datagram_bytes: if self.mode == Mode::UnderCapacity {
                0
            } else {
                p.len() as u16
            },
            fifo_bytes: fifo,
        };
        let mut bytes = [0; 1055];
        bytes[..p.len()].copy_from_slice(p);
        *slot = Some(Stored {
            identity,
            lease,
            bytes,
            len: p.len(),
        });
        if self.mode == Mode::Unknown {
            Reservation::Unknown
        } else {
            Reservation::Owned(lease)
        }
    }
    fn release(&mut self, identity: Identity, lease: BufferLease) -> bool {
        if self.release_unknown {
            return false;
        }
        let Some(s) = self
            .storage
            .iter_mut()
            .find(|s| s.is_some_and(|s| s.identity == identity && s.lease == lease))
        else {
            return false;
        };
        *s = None;
        self.releases += 1;
        true
    }
}
fn complete(g: &mut Gateway, b: &mut Fake, id: Identity) -> Receipt {
    let lease = b.id(id);
    let Completed::Receipt(r) = g.complete(id, lease, Completion::Consumed, b) else {
        panic!()
    };
    r
}
#[test]
fn live_gate_is_closed_and_metadata_bounded() {
    assert!(!ar03_lab::LIVE_PROFILE_ADVERTISED);
    assert!(ar03_lab::authorize_live_profile().is_err());
    assert!(std::mem::size_of::<Gateway>() <= 2048);
    assert_eq!(Gateway::cold_epoch1(true).mailbox_count(), 0);
}
#[test]
fn all_1725_native_controls_parse_exact_fields_and_roundtrip() {
    let bytes = include_bytes!("fixtures/ar03-lab/fg19.bin");
    let rows = include_str!("fixtures/ar03-lab/fg19.tsv");
    let mut count = 0;
    for (row, p) in rows.lines().zip(bytes.chunks_exact(36)) {
        let v: Vec<_> = row.split('\t').collect();
        let f = wire::parse_frame(p).unwrap();
        assert_eq!(
            (
                f.kind as u8,
                f.slot,
                f.epoch,
                f.frame,
                f.nonce,
                f.total,
                f.body_crc
            ),
            (
                v[2].parse().unwrap(),
                v[3].parse().unwrap(),
                v[4].parse().unwrap(),
                v[5].parse().unwrap(),
                v[6].parse().unwrap(),
                v[7].parse().unwrap(),
                v[8].parse().unwrap()
            )
        );
        let mut out = [0xa5; 40];
        assert_eq!(wire::write_frame(f, &mut out), Ok(36));
        assert_eq!(&out[..36], p);
        assert_eq!(&out[36..], &[0xa5; 4]);
        count += 1;
    }
    assert_eq!(count, 1725);
    assert_eq!(bytes.len(), count * 36);
}
#[test]
fn control_corruption_lengths_and_writer_errors_never_mutate_output() {
    let base = &include_bytes!("fixtures/ar03-lab/fg19.bin")[..36];
    for i in 0..36 {
        for bit in 0..8 {
            let mut p = base.to_vec();
            p[i] ^= 1 << bit;
            assert!(wire::parse_frame(&p).is_err());
        }
    }
    for n in 0..36 {
        assert!(wire::parse_frame(&base[..n]).is_err());
        let mut out = [0xa5; 40];
        assert!(wire::write_frame(request(1, 1, 0, 1), &mut out[..n]).is_err());
        assert_eq!(out, [0xa5; 40]);
    }
    for f in [
        request(1, 0, 0, 1),
        request(1, 1, 0, 0),
        request(1, 1, 0, 49153),
        request(1, 1, 2, 1),
    ] {
        let mut out = [0xa5; 40];
        assert!(wire::write_frame(f, &mut out).is_err());
        assert_eq!(out, [0xa5; 40]);
    }
}
#[test]
fn histories_keep_two_owner_bound_without_fabricated_drain() {
    let rows = include_str!("fixtures/ar03-lab/fg19.tsv");
    let bytes = include_bytes!("fixtures/ar03-lab/fg19.bin");
    let mut profile = None;
    let mut ledger = Frames::cold_epoch1(true);
    for (row, p) in rows.lines().zip(bytes.chunks_exact(36)) {
        let v: Vec<_> = row.split('\t').collect();
        let id: u32 = v[0].parse().unwrap();
        if profile != Some(id) {
            ledger = Frames::cold_epoch1(true);
            profile = Some(id)
        }
        let f = wire::parse_frame(p).unwrap();
        let r = ledger.control(f);
        if matches!(
            f.kind,
            Kind::Grant | Kind::Busy | Kind::Release | Kind::Canceled | Kind::Finished
        ) {
            assert_eq!(r, Control::Invalid);
        }
        assert!(!matches!(r,Control::Reply(x)if x.kind==Kind::Release));
        assert!(ledger.count() <= 2);
    }
}
#[test]
fn duplicate_request_other_slot_returns_original_grant_not_c_strict_busy() {
    let mut l = Frames::cold_epoch1(true);
    let q = request(7, 1, 0, 1008);
    let Control::Reply(g) = l.control(q) else {
        panic!()
    };
    assert_eq!(l.control(Frame { slot: 1, ..q }), Control::Reply(g));
    assert_eq!(l.count(), 1);
    assert_eq!(l.owner(0).unwrap().grant, g);
    assert_eq!(l.owner(1), None);
}
#[test]
fn fresh_busy_request_consumes_serial_and_no_wrap_is_invented() {
    let mut l = Frames::cold_epoch1(true);
    assert!(matches!(l.control(request(1,1,0,1)),Control::Reply(f)if f.kind==Kind::Grant));
    assert!(matches!(l.control(request(2,3,0,1)),Control::Reply(f)if f.kind==Kind::Busy));
    assert!(matches!(l.control(request(3,2,1,1)),Control::Reply(f)if f.kind==Kind::Busy));
    assert!(matches!(l.control(request(4,u64::MAX,1,1)),Control::Reply(f)if f.kind==Kind::Grant));
    assert_eq!(l.control(request(5, 0, 1, 1)), Control::Invalid);
}
#[test]
fn five_data_positions_leave_exactly_one_control_path_and_finish_is_not_release() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 6048));
    let mut b = Fake::new();
    for i in 0..5 {
        g.admit(&data(f, i, i, 1), &mut b).unwrap();
    }
    assert_eq!(g.mailbox_count(), 5);
    let finish = f.reply(Kind::Finish, 0);
    assert!(matches!(g.frame_control(finish),Ok(Control::Reply(r))if r.kind==Kind::Finished));
    assert_eq!(g.mailbox_count(), 6);
    assert_eq!(g.packet_count(), 5);
    assert_eq!(g.frame_count(), 1);
    assert!(!g.physical_drain(f));
    assert_eq!(g.take_release(f), None);
    assert!(!g.complete_control(
        ControlIdentity::Frame(Frame { slot: 1, ..finish }),
        ControlDone::ReplyEnqueued
    ));
    assert_eq!(g.mailbox_count(), 6);
    assert!(g.complete_control(ControlIdentity::Frame(finish), ControlDone::ReplyEnqueued));
    assert_eq!(g.mailbox_count(), 5);
    assert_eq!(g.frame_count(), 1);
}
#[test]
fn grammatical_slot_five_is_reserved_by_admission_not_repurposed_as_data() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 1008));
    let mut b = Fake::new();
    let p = data(f, 0, 5, 1);
    assert!(wire::parse_data(&p).is_ok());
    assert_eq!(
        g.admit(&p, &mut b),
        Err(AdmissionError::ReservedControlPosition)
    );
    assert_eq!(b.reserves, 0);
}
#[test]
fn backend_owns_copied_bytes_before_rx_array_reuse_and_completion_matches_golden_pc18() {
    let mut p = include_bytes!("fixtures/ar03-lab/gf03.bin").to_vec();
    let d = wire::parse_data(&p).unwrap();
    let mut g = Gateway::cold_epoch1(true);
    let mut q = request(d.frame, 1, 0, d.total);
    q.body_crc = d.body_crc;
    grant(&mut g, q);
    let mut b = Fake::new();
    let id = g.admit(&p, &mut b).unwrap();
    let lease = b.id(id);
    let before = b.bytes(lease).to_vec();
    p.fill(0xcc);
    assert_eq!(b.bytes(lease), before);
    let r = complete(&mut g, &mut b, id);
    let mut out = [0; 29];
    wire::write_receipt(r, &mut out).unwrap();
    assert_eq!(&out, include_bytes!("fixtures/ar03-lab/pc18.bin"));
    assert_eq!(b.releases, 1);
    assert_eq!(g.packet_count(), 0);
    let query = wire::parse_query(include_bytes!("fixtures/ar03-lab/qc18.bin")).unwrap();
    assert_eq!(
        g.query(query),
        QueryResult::Receipt(Receipt { queried: true, ..r })
    );
    assert_eq!(
        g.complete(id, lease, Completion::Consumed, &mut b),
        Completed::Duplicate
    );
    assert_eq!(b.releases, 1);
}
#[test]
fn unavailable_backend_mutates_no_packet_or_fragment_owner() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 1008));
    let mut b = Fake::new();
    b.mode = Mode::Unavailable;
    assert_eq!(
        g.admit(&data(f, 0, 0, 1), &mut b),
        Err(AdmissionError::NoCapacity)
    );
    assert_eq!(g.packet_count(), 0);
    assert_eq!(g.owner(0).unwrap().observed, 0);
    assert!(
        matches!(g.frame_control(f.reply(Kind::Cancel,0)),Ok(Control::Reply(r))if r.kind==Kind::Canceled)
    );
}
#[test]
fn duplicates_busy_slots_and_fragment_replays_do_not_reserve_again() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 2016));
    let mut b = Fake::new();
    let p = data(f, 0, 0, 1);
    let id = g.admit(&p, &mut b).unwrap();
    assert_eq!(g.admit(&p, &mut b), Err(AdmissionError::Duplicate));
    assert_eq!(
        g.admit(&data(f, 1, 0, 2), &mut b),
        Err(AdmissionError::Busy)
    );
    assert_eq!(
        g.admit(&data(f, 0, 1, 2), &mut b),
        Err(AdmissionError::Duplicate)
    );
    assert_eq!(b.reserves, 1);
    complete(&mut g, &mut b, id);
    assert_eq!(
        g.admit(&data(f, 0, 1, 3), &mut b),
        Err(AdmissionError::Duplicate)
    );
    assert_eq!(b.reserves, 1);
}
#[test]
fn every_wrong_completion_identity_and_buffer_id_preserves_real_lease() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 2016));
    let mut b = Fake::new();
    let id = g.admit(&data(f, 0, 0, 1), &mut b).unwrap();
    let lease = b.id(id);
    let mut wrong = Vec::new();
    let mut x = id;
    x.owner.nonce += 1;
    wrong.push(x);
    let mut x = id;
    x.owner.slot = 1;
    wrong.push(x);
    let mut x = id;
    x.route.frame += 1;
    wrong.push(x);
    let mut x = id;
    x.route.body_crc += 1;
    wrong.push(x);
    let mut x = id;
    x.route.complete_crc += 1;
    wrong.push(x);
    let mut x = id;
    x.route.token_header_crc += 1;
    wrong.push(x);
    let mut x = id;
    x.route.sequence += 1;
    wrong.push(x);
    let mut x = id;
    x.route.index = 1;
    wrong.push(x);
    let mut x = id;
    x.route.packet_slot = 1;
    wrong.push(x);
    for x in wrong {
        assert_eq!(
            g.complete(x, lease, Completion::Consumed, &mut b),
            Completed::Stale
        );
        assert_eq!(g.packet_count(), 1);
        assert_eq!(b.releases, 0);
    }
    assert_eq!(
        g.complete(id, lease + 1, Completion::Consumed, &mut b),
        Completed::Stale
    );
    complete(&mut g, &mut b, id);
    assert_eq!(b.releases, 1);
}
#[test]
fn unknown_reservation_and_insufficient_capacity_keep_bounded_ownership_in_safe_stop() {
    for mode in [Mode::Unknown, Mode::UnderCapacity] {
        let mut g = Gateway::cold_epoch1(true);
        let f = grant(&mut g, request(1, 1, 0, 1008));
        let mut b = Fake::new();
        b.mode = mode;
        assert_eq!(
            g.admit(&data(f, 0, 0, 1), &mut b),
            Err(AdmissionError::Ambiguous)
        );
        assert!(g.stopped());
        assert_eq!(g.packet_count(), 1);
        assert_eq!(g.frame_count(), 1);
        assert_eq!(g.take_release(f), None);
        assert_eq!(b.releases, 0);
    }
}
#[test]
fn duplicate_backend_lease_id_is_ambiguous_and_never_credits_either_owner() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 2016));
    let mut b = Fake::new();
    g.admit(&data(f, 0, 0, 1), &mut b).unwrap();
    b.mode = Mode::DuplicateId;
    assert_eq!(
        g.admit(&data(f, 1, 1, 1), &mut b),
        Err(AdmissionError::Ambiguous)
    );
    assert!(g.stopped());
    assert_eq!(g.packet_count(), 2);
    assert_eq!(b.releases, 0);
}
#[test]
fn unknown_dma_and_unknown_buffer_release_never_create_credit_or_free_other_frame() {
    for unknown_dma in [true, false] {
        let mut g = Gateway::cold_epoch1(true);
        let f = grant(&mut g, request(1, 1, 0, 1008));
        grant(&mut g, request(2, 2, 1, 1008));
        let mut b = Fake::new();
        let id = g.admit(&data(f, 0, 0, 1), &mut b).unwrap();
        let lease = b.id(id);
        b.release_unknown = !unknown_dma;
        assert_eq!(
            g.complete(
                id,
                lease,
                if unknown_dma {
                    Completion::Unknown
                } else {
                    Completion::Consumed
                },
                &mut b
            ),
            Completed::SafeStop
        );
        assert_eq!(g.packet_count(), 1);
        assert_eq!(g.frame_count(), 2);
        assert_eq!(g.query(id.route.query()), QueryResult::Unknown);
        assert_eq!(g.take_release(f), None);
        assert_eq!(b.releases, 0);
    }
}
#[test]
fn pending_and_repeated_queries_do_not_return_or_mutate_data_credit() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 1008));
    let mut b = Fake::new();
    let id = g.admit(&data(f, 0, 0, 1), &mut b).unwrap();
    let q = id.route.query();
    for _ in 0..3 {
        assert_eq!(g.query_control(q), Ok(QueryResult::Pending));
        assert_eq!(g.mailbox_count(), 2);
        let pending_reply = QueryResult::Pending.wire_reply(q);
        assert!(!pending_reply.returns_packet_permit());
        assert_eq!(pending_reply.status, Status::Unknown);
        let mut wire = [0; 29];
        wire::write_receipt(pending_reply, &mut wire).unwrap();
        assert_eq!((wire[11], wire[20]), (1, 2));
        assert!(!g.complete_control(ControlIdentity::Query(q), ControlDone::NoReplyConsumed));
        assert!(g.complete_control(ControlIdentity::Query(q), ControlDone::ReplyEnqueued));
        assert_eq!(g.packet_count(), 1);
    }
    let receipt = complete(&mut g, &mut b, id);
    for _ in 0..3 {
        assert_eq!(
            g.query(q),
            QueryResult::Receipt(Receipt {
                queried: true,
                ..receipt
            })
        );
        assert_eq!(g.packet_count(), 0);
    }
    assert_eq!(b.releases, 1);
    let wrong = Query {
        header_crc: q.header_crc ^ 1,
        ..q
    };
    assert_eq!(g.query(wrong), QueryResult::Unknown);
    let unknown = Receipt {
        key: wrong,
        status: Status::Unknown,
        queried: true,
    };
    assert!(!unknown.returns_packet_permit());
    let mut out = [0; 29];
    wire::write_receipt(unknown, &mut out).unwrap();
    assert_eq!(out[20], 2);
}
#[test]
fn sequence_maximum_does_not_wrap_or_accept_stale_slot_reuse() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 2016));
    let mut b = Fake::new();
    let id = g.admit(&data(f, 0, 0, u64::MAX), &mut b).unwrap();
    complete(&mut g, &mut b, id);
    assert_eq!(
        g.admit(&data(f, 1, 0, 1), &mut b),
        Err(AdmissionError::Stale)
    );
    assert!(matches!(
        g.admit(&data(f, 1, 0, 0), &mut b),
        Err(AdmissionError::Wire(_))
    ));
    assert_eq!(b.reserves, 1);
}
#[test]
fn partial_frame_finish_waits_for_packet_completion_explicit_drain_and_control_reply() {
    let mut g = Gateway::cold_epoch1(true);
    let f = grant(&mut g, request(1, 1, 0, 2016));
    let mut b = Fake::new();
    let id = g.admit(&data(f, 0, 0, 1), &mut b).unwrap();
    let fin = f.reply(Kind::Finish, 0);
    g.frame_control(fin).unwrap();
    assert!(!g.physical_drain(f));
    assert_eq!(g.take_release(f), None);
    complete(&mut g, &mut b, id);
    assert!(g.physical_drain(f));
    assert_eq!(g.take_release(f), None);
    assert!(!g.complete_control(ControlIdentity::Frame(fin), ControlDone::NoReplyConsumed));
    assert!(g.complete_control(ControlIdentity::Frame(fin), ControlDone::ReplyEnqueued));
    let r = g.take_release(f).unwrap();
    assert_eq!(r.kind, Kind::Release);
    assert_eq!(g.frame_count(), 0);
    // Capacity release for drained partial work does not assert successful decode or AF03.
}
#[test]
fn unknown_control_outcome_is_sticky_and_never_invents_reset_credit() {
    let mut g = Gateway::cold_epoch1(true);
    let q = request(1, 1, 0, 1008);
    g.frame_control(q).unwrap();
    assert!(!g.complete_control(ControlIdentity::Frame(q), ControlDone::Unknown));
    assert!(g.stopped());
    assert_eq!((g.frame_count(), g.mailbox_count()), (1, 1));
    assert_eq!(
        g.frame_control(request(2, 2, 1, 1008)),
        Err(AdmissionError::Stopped)
    );
}
#[test]
fn payload_corruption_does_not_masquerade_as_header_integrity_check() {
    let f = request(1, 1, 0, 1008).reply(Kind::Grant, 0);
    let p = data(f, 0, 0, 1);
    let mut corrupt = p.clone();
    corrupt[47] ^= 1;
    assert_eq!(
        wire::parse_data(&p).unwrap(),
        wire::parse_data(&corrupt).unwrap()
    );
}
#[test]
fn fragment_geometry_all_boundaries_are_bounded_and_invalids_reject() {
    for total in [1, 1007, 1008, 1009, 49151, 49152] {
        let f = request(1, 1, 0, total).reply(Kind::Grant, 0);
        for i in 0..((total + 1007) / 1008) as u16 {
            let p = data(f, i, 4, u64::MAX);
            assert!(wire::parse_data(&p).unwrap().matches(&f));
        }
    }
    let f = request(1, 1, 0, 1008).reply(Kind::Grant, 0);
    let p = data(f, 0, 0, 1);
    for n in 0..p.len() {
        assert!(wire::parse_data(&p[..n]).is_err());
    }
    let mut p = p;
    p[6] = 1;
    assert!(wire::parse_data(&p).is_err());
}

#[test]
fn lab_frame_identity_reuse_can_bind_unseen_delayed_data_but_live_gate_denies_enable() {
    let mut gateway = Gateway::cold_epoch1(true);
    let first = grant(&mut gateway, request(7, 1, 0, 2016));
    // This datagram exists in the old epoch1 sender history but is never observed.
    let delayed = data(first, 1, 1, 1);
    let mut backend = Fake::new();
    let seen = gateway.admit(&data(first, 0, 0, 1), &mut backend).unwrap();
    complete(&mut gateway, &mut backend, seen);
    let finish = first.reply(Kind::Finish, 0);
    gateway.frame_control(finish).unwrap();
    assert!(gateway.complete_control(ControlIdentity::Frame(finish), ControlDone::ReplyEnqueued));
    assert!(gateway.physical_drain(first));
    assert!(gateway.take_release(first).is_some());
    let second = grant(&mut gateway, request(7, 2, 0, 2016));
    // Frozen FG19 lab grammar permits this reuse. TOKEN/GF03 has no FG19 nonce.
    // A never-observed old slot sequence can therefore bind to the current grant.
    let rebound = gateway.admit(&delayed, &mut backend).unwrap();
    assert_eq!(rebound.owner.nonce, second.nonce);
    assert_ne!(rebound.owner.nonce, first.nonce);
    assert_eq!(rebound.route, wire::parse_data(&delayed).unwrap());
    assert!(ar03_lab::authorize_live_profile().is_err());
    // This is a scope/generation-policy counterexample, not a replay-safety pass.
}
