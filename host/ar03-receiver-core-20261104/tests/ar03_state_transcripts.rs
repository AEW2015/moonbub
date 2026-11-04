//! Generated exact model-transcript replay. Reference SHA is frozen in fixture manifest.
#[path = "../handheld/src/streaming/ar03_lab/mod.rs"]
mod ar03_lab;
use ar03_lab::{
    frame::{Control, Frames},
    wire::{self, Frame, Kind},
};
fn encoded(f: Frame) -> Vec<u8> {
    let mut b = [0; 36];
    wire::write_frame(f, &mut b).unwrap();
    b.to_vec()
}
fn control(l: &mut Frames, f: Frame) -> Vec<Vec<u8>> {
    match l.control(f) {
        Control::Reply(r) => vec![encoded(r)],
        _ => vec![],
    }
}
fn poll(l: &mut Frames) -> Vec<Vec<u8>> {
    let mut out = vec![];
    for i in 0..2 {
        if let Some(o) = l.owner(i) {
            if let Some(r) = l.take_release(o.grant) {
                out.push(encoded(r));
            }
        }
    }
    out
}
fn owner(l: &Frames, slot: u16) -> Option<([u64; 6], bool, u64)> {
    l.owner(slot).map(|o| {
        (
            [
                o.grant.epoch as u64,
                o.grant.frame as u64,
                o.grant.nonce,
                o.grant.total as u64,
                o.grant.body_crc as u64,
                o.grant.slot as u64,
            ],
            o.finished,
            o.observed,
        )
    })
}
#[test]
fn transcript_normal_drain_and_stale_completion() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 25571,
            body_crc: 3497821065,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x63, 0xe3,
            0xd0, 0x7c, 0x83, 0x89, 0x16, 0xc9, 0x2e, 0x5c
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    if let Ok(d) = wire::parse_data(&[
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x01, 0x47, 0x46, 0x30, 0x33, 0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x63, 0xe3, 0x00, 0x00, 0x00, 0x1a, 0x03, 0xf0, 0x21, 0x44, 0xdf, 0x1c, 0xd0, 0x7c,
        0x83, 0x89, 0x41, 0x52, 0x30, 0x33, 0x03, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0xff, 0x00, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xee, 0xce, 0xad, 0x33, 0x98, 0x07, 0x07,
        0x28, 0xd0, 0xd8, 0xea, 0xe0, 0x8f, 0xb6, 0x8d, 0x2b, 0x2c, 0x42, 0x00, 0x00, 0x04, 0x76,
        0x21, 0x00, 0x00, 0x47, 0x4d, 0x30, 0x31, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xd0, 0x02, 0xe0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2d,
        0x00, 0x1e, 0x00, 0x52, 0x01, 0x00, 0x00, 0x14, 0x39, 0x00, 0x00, 0xc7, 0x03, 0x00, 0x00,
        0xcd, 0x03, 0x00, 0x00, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x50, 0x43, 0x50, 0x30,
        0x32, 0x01, 0x01, 0x18, 0x15, 0x00, 0x00, 0x5a, 0x00, 0x00, 0x00, 0xa8, 0x09, 0x00, 0x00,
        0x52, 0x2f, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xfd, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x54, 0x00, 0x00, 0x07, 0xfa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
        0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xa8, 0x00, 0x00, 0x0f,
        0xf5, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55,
        0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x55, 0x50, 0x00, 0x00, 0x1f, 0xea, 0xaa, 0xaa, 0xaa,
        0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
        0xaa, 0xaa, 0xaa, 0xa0, 0x00, 0x00, 0x3e, 0xd5, 0x55, 0x2a, 0xbe, 0xaa, 0xaa, 0xaa, 0x22,
        0xaa, 0xa6, 0xea, 0xaa, 0x51, 0x4a, 0xae, 0xab, 0xea, 0xaa, 0xaa, 0xb5, 0x55, 0x55, 0x55,
        0x54, 0x00, 0x00, 0x07, 0xba, 0x52, 0xaa, 0x56, 0x75, 0x55, 0x55, 0x55, 0x10, 0x82, 0x55,
        0x0c, 0x3e, 0xaa, 0xa2, 0x04, 0x95, 0x57, 0x59, 0xfa, 0xa5, 0x7f, 0x55, 0x55, 0x25, 0x75,
        0x55, 0x40, 0x00, 0x00, 0x7b, 0xa4, 0xaa, 0x97, 0xba, 0xaa, 0xaa, 0xaa, 0xaa, 0x20, 0x41,
        0x58, 0xc3, 0xea, 0xaa, 0x20, 0x4b, 0x55, 0x55, 0xb7, 0x54, 0x2a, 0xda, 0xfd, 0x2a, 0x97,
        0x55, 0x75, 0x40, 0x00, 0x00, 0x79, 0x95, 0x52, 0xb7, 0xd5, 0x55, 0x55, 0x55, 0x55, 0x41,
        0x01, 0x21, 0x83, 0xea, 0xaa, 0x10, 0x2e, 0xea, 0xaa, 0xfe, 0x91, 0x2b, 0xe9, 0xb4, 0x55,
        0x55, 0xd5, 0x5d, 0x00, 0x00, 0x01, 0xe5, 0x55, 0x49, 0xba, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
        0xa2, 0x02, 0xc1, 0xf5, 0x55, 0x08, 0x27, 0x51, 0x27, 0x5a, 0x7d, 0x25, 0x4a, 0xec, 0xca,
        0x55, 0x55, 0x5d, 0x5c, 0x00, 0x00, 0x07, 0x95, 0x54, 0x8f, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa,
        0xaa, 0xa4, 0x21, 0xd5, 0x55, 0x08, 0x15, 0xdc, 0x47, 0xd1, 0x3e, 0x4b, 0xea, 0xab, 0x4a,
        0xaa, 0xaa, 0xea, 0xa0, 0x00, 0x00, 0x3b, 0xd4, 0xa6, 0xea, 0xaa, 0xaa, 0xaa, 0xaa, 0xa9,
        0x4a, 0xfa, 0xaa, 0xa9, 0x10, 0x55, 0x52, 0xaf, 0x47, 0x52, 0x7a, 0xae, 0x94, 0xaa, 0xaa,
        0xaa, 0xea, 0x00, 0x00, 0x03, 0xbd, 0x4b, 0x3a, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0x42, 0x91,
        0x67, 0xa3, 0xaa, 0x54, 0x11, 0x55, 0xd2, 0xaa, 0x7d, 0x2f, 0xd4, 0xe8, 0x95, 0x55, 0x55,
        0x55, 0xd0, 0x00, 0x00, 0x1d, 0xe9, 0x4d, 0xd5, 0x55, 0x55, 0x55, 0x55, 0x51, 0x08, 0x92,
        0xad, 0x0c, 0x3a, 0x94, 0x41, 0x2a, 0xea, 0xab, 0x9d, 0x4a, 0xba, 0xed, 0x2a, 0xaa, 0xaa,
        0xba, 0xa0, 0x00, 0x00, 0x3b, 0xd2, 0xce, 0xaa, 0xaa, 0xaa, 0xaa, 0xaa, 0xa1, 0x08, 0x94,
        0xa9, 0x40, 0x1b, 0xa5, 0x08, 0x2a, 0xaa, 0xea, 0xb7, 0x4a, 0xae, 0xae, 0x92, 0xab, 0xaa,
        0xab, 0xa8, 0x00, 0x00, 0x0e, 0xf5, 0x3e, 0xaa, 0xaa, 0xa9, 0x75, 0x55, 0x50, 0x84, 0x4a,
        0x54, 0x90, 0xc0, 0xea, 0x40, 0x94, 0xab, 0xae, 0xad, 0xc9, 0x57, 0x5d, 0x72, 0x55, 0x55,
        0xd5, 0x75, 0x00, 0x00, 0x01, 0xde, 0x4f, 0xea, 0xa9, 0x55, 0x55, 0x75, 0x55, 0x10, 0x85,
        0x49, 0x51, 0x10, 0x00, 0xfa, 0x20, 0x5f, 0x49, 0x5d, 0x53, 0xa9, 0x55, 0xd7, 0x69, 0x2e,
        0xaa, 0xea, 0xab, 0x80, 0x00, 0x00, 0xef, 0x2d, 0xd5, 0xaa, 0x55, 0x2b, 0xbe, 0xaa, 0xa2,
        0x11, 0x29, 0x25, 0x11, 0x01, 0x81, 0xc8, 0x42, 0xaa, 0xaf, 0xa5, 0x3a, 0x55, 0x5d, 0x76,
        0x92, 0xea, 0xbe, 0xea, 0xe4, 0x00, 0x00, 0x07, 0x72, 0x21, 0xfd, 0x54, 0x92, 0xea, 0xaf,
        0xab, 0x94, 0x88, 0x4a, 0x29, 0x22, 0x26, 0x00, 0x3d, 0x02, 0x2e, 0xe5, 0x3a, 0x97, 0xca,
        0xba, 0xbe, 0x5d, 0x57, 0x2a, 0x95, 0x55, 0x40, 0x00, 0x00, 0x73, 0x48, 0x3a, 0xea, 0x89,
        0x2b, 0xaa, 0xba, 0xf9, 0x44,
    ]) {
        l.observe(d);
    }
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step1");
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], false, 1)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 25571,
            body_crc: 3497821065,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x63, 0xe3,
            0xd0, 0x7c, 0x83, 0x89, 0xe6, 0x0b, 0xd6, 0x4a
        ]
        .to_vec()],
        "reply step2"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], false, 1)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 25571,
            body_crc: 3497821065,
            kind: Kind::Finish,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x63, 0xe3,
            0xd0, 0x7c, 0x83, 0x89, 0x67, 0xdf, 0xd5, 0x15
        ]
        .to_vec()],
        "reply step3"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step3");
    assert_eq!(l.stopped(), false, "stop step3");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], true, 1)),
        "owner0 step3"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step3");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step4");
    assert_eq!(l.watermarks(), (1, 0), "watermark step4");
    assert_eq!(l.stopped(), false, "stop step4");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], true, 1)),
        "owner0 step4"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step4");
    l.physical_drain(Frame {
        epoch: 1,
        frame: 0,
        nonce: 1,
        slot: 0,
        total: 25571,
        body_crc: 3497821065,
        kind: Kind::Grant,
    });
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step5");
    assert_eq!(l.watermarks(), (1, 0), "watermark step5");
    assert_eq!(l.stopped(), false, "stop step5");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 25571, 3497821065, 0], true, 1)),
        "owner0 step5"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step5");
    reply = poll(&mut l);
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x63, 0xe3,
            0xd0, 0x7c, 0x83, 0x89, 0xaa, 0x90, 0x73, 0x9b
        ]
        .to_vec()],
        "reply step6"
    );
    assert_eq!(l.watermarks(), (1, 1), "watermark step6");
    assert_eq!(l.stopped(), false, "stop step6");
    assert_eq!(owner(&l, 0), None, "owner0 step6");
    assert_eq!(owner(&l, 1), None, "owner1 step6");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 1,
            nonce: 2,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x13, 0x6e, 0x32, 0xf7
        ]
        .to_vec()],
        "reply step7"
    );
    assert_eq!(l.watermarks(), (2, 1), "watermark step7");
    assert_eq!(l.stopped(), false, "stop step7");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 1, 2, 1008, 305419896, 0], false, 0)),
        "owner0 step7"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step7");
    l.physical_drain(Frame {
        epoch: 1,
        frame: 0,
        nonce: 1,
        slot: 0,
        total: 25571,
        body_crc: 3497821065,
        kind: Kind::Grant,
    });
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step8");
    assert_eq!(l.watermarks(), (2, 1), "watermark step8");
    assert_eq!(l.stopped(), false, "stop step8");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 1, 2, 1008, 305419896, 0], false, 0)),
        "owner0 step8"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step8");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 25571,
            body_crc: 3497821065,
            kind: Kind::Finish,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x63, 0xe3,
            0xd0, 0x7c, 0x83, 0x89, 0xe6, 0x0b, 0xd6, 0x4a
        ]
        .to_vec()],
        "reply step9"
    );
    assert_eq!(l.watermarks(), (2, 1), "watermark step9");
    assert_eq!(l.stopped(), false, "stop step9");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 1, 2, 1008, 305419896, 0], false, 0)),
        "owner0 step9"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step9");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step10");
    assert_eq!(l.watermarks(), (2, 1), "watermark step10");
    assert_eq!(l.stopped(), false, "stop step10");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 1, 2, 1008, 305419896, 0], false, 0)),
        "owner0 step10"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step10");
}
#[test]
fn transcript_drain_before_finish_still_needs_finished() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    l.physical_drain(Frame {
        epoch: 1,
        frame: 0,
        nonce: 1,
        slot: 0,
        total: 1008,
        body_crc: 305419896,
        kind: Kind::Grant,
    });
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step1");
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step2");
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Finish,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xdc, 0x53, 0x3e, 0x38
        ]
        .to_vec()],
        "reply step3"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step3");
    assert_eq!(l.stopped(), false, "stop step3");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], true, 0)),
        "owner0 step3"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step3");
    reply = poll(&mut l);
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x11, 0x1c, 0x98, 0xb6
        ]
        .to_vec()],
        "reply step4"
    );
    assert_eq!(l.watermarks(), (1, 1), "watermark step4");
    assert_eq!(l.stopped(), false, "stop step4");
    assert_eq!(owner(&l, 0), None, "owner0 step4");
    assert_eq!(owner(&l, 1), None, "owner1 step4");
}
#[test]
fn transcript_two_owners_busy_consumes_request_serial() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 1,
            nonce: 2,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xb6, 0xe5, 0xa2, 0xf9
        ]
        .to_vec()],
        "reply step1"
    );
    assert_eq!(l.watermarks(), (2, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(
        owner(&l, 1),
        Some(([1, 1, 2, 1008, 305419896, 1], false, 0)),
        "owner1 step1"
    );
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 2,
            nonce: 3,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xa7, 0x4d, 0x85, 0x26
        ]
        .to_vec()],
        "reply step2"
    );
    assert_eq!(l.watermarks(), (3, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(
        owner(&l, 1),
        Some(([1, 1, 2, 1008, 305419896, 1], false, 0)),
        "owner1 step2"
    );
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 1,
            nonce: 2,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x06, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xb9, 0x28, 0xd2, 0xfd
        ]
        .to_vec()],
        "reply step3"
    );
    assert_eq!(l.watermarks(), (3, 2), "watermark step3");
    assert_eq!(l.stopped(), false, "stop step3");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step3"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step3");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 3,
            nonce: 2,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x37, 0x90, 0x5a, 0x26
        ]
        .to_vec()],
        "reply step4"
    );
    assert_eq!(l.watermarks(), (3, 2), "watermark step4");
    assert_eq!(l.stopped(), false, "stop step4");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step4"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step4");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 3,
            nonce: 4,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x11, 0xc3, 0x4b, 0xb4
        ]
        .to_vec()],
        "reply step5"
    );
    assert_eq!(l.watermarks(), (4, 2), "watermark step5");
    assert_eq!(l.stopped(), false, "stop step5");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step5"
    );
    assert_eq!(
        owner(&l, 1),
        Some(([1, 3, 4, 1008, 305419896, 1], false, 0)),
        "owner1 step5"
    );
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Finish,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xdc, 0x53, 0x3e, 0x38
        ]
        .to_vec()],
        "reply step6"
    );
    assert_eq!(l.watermarks(), (4, 2), "watermark step6");
    assert_eq!(l.stopped(), false, "stop step6");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], true, 0)),
        "owner0 step6"
    );
    assert_eq!(
        owner(&l, 1),
        Some(([1, 3, 4, 1008, 305419896, 1], false, 0)),
        "owner1 step6"
    );
    l.physical_drain(Frame {
        epoch: 1,
        frame: 0,
        nonce: 1,
        slot: 0,
        total: 1008,
        body_crc: 305419896,
        kind: Kind::Grant,
    });
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step7");
    assert_eq!(l.watermarks(), (4, 2), "watermark step7");
    assert_eq!(l.stopped(), false, "stop step7");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], true, 0)),
        "owner0 step7"
    );
    assert_eq!(
        owner(&l, 1),
        Some(([1, 3, 4, 1008, 305419896, 1], false, 0)),
        "owner1 step7"
    );
    reply = poll(&mut l);
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x11, 0x1c, 0x98, 0xb6
        ]
        .to_vec()],
        "reply step8"
    );
    assert_eq!(l.watermarks(), (4, 2), "watermark step8");
    assert_eq!(l.stopped(), false, "stop step8");
    assert_eq!(owner(&l, 0), None, "owner0 step8");
    assert_eq!(
        owner(&l, 1),
        Some(([1, 3, 4, 1008, 305419896, 1], false, 0)),
        "owner1 step8"
    );
}
#[test]
fn transcript_duplicate_request_same_slot() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step1"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xa2, 0x88, 0xb5, 0x75
        ]
        .to_vec()],
        "reply step2"
    );
    assert_eq!(l.watermarks(), (1, 1), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(owner(&l, 0), None, "owner0 step2");
    assert_eq!(owner(&l, 1), None, "owner1 step2");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x5d, 0x87, 0x3d, 0x67
        ]
        .to_vec()],
        "reply step3"
    );
    assert_eq!(l.watermarks(), (1, 1), "watermark step3");
    assert_eq!(l.stopped(), false, "stop step3");
    assert_eq!(owner(&l, 0), None, "owner0 step3");
    assert_eq!(owner(&l, 1), None, "owner1 step3");
}
#[test]
fn transcript_duplicate_request_different_slot() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step1"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step2");
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
}
#[test]
fn transcript_wrong_identity_cannot_release() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Finish,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x5d, 0x87, 0x3d, 0x67
        ]
        .to_vec()],
        "reply step1"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 2,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x00, 0x00, 0x00, 0x02, 0xd8, 0xc4, 0x8d, 0xcf
        ]
        .to_vec()],
        "reply step2"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
    l.physical_drain(Frame {
        epoch: 1,
        frame: 0,
        nonce: 2,
        slot: 0,
        total: 1008,
        body_crc: 305419896,
        kind: Kind::Grant,
    });
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step3");
    assert_eq!(l.watermarks(), (1, 0), "watermark step3");
    assert_eq!(l.stopped(), false, "stop step3");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step3"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step3");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step4");
    assert_eq!(l.watermarks(), (1, 0), "watermark step4");
    assert_eq!(l.stopped(), false, "stop step4");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step4"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step4");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xa2, 0x88, 0xb5, 0x75
        ]
        .to_vec()],
        "reply step5"
    );
    assert_eq!(l.watermarks(), (1, 1), "watermark step5");
    assert_eq!(l.stopped(), false, "stop step5");
    assert_eq!(owner(&l, 0), None, "owner0 step5");
    assert_eq!(owner(&l, 1), None, "owner1 step5");
}
#[test]
fn transcript_reply_kind_is_not_a_request() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Release,
        },
    );
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step1");
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step2");
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
}
#[test]
fn transcript_unknown_grant_outcome_retains_owner() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    l.safe_stop();
    reply = vec![];
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step1");
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), true, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step2");
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), true, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step3");
    assert_eq!(l.watermarks(), (1, 0), "watermark step3");
    assert_eq!(l.stopped(), true, "stop step3");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step3"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step3");
}
#[test]
fn transcript_nonce_exhaustion_does_not_invent_new_epoch() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 18446744073709551615,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x2d, 0x50, 0x5c, 0x08
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (18446744073709551615, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 18446744073709551615, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 18446744073709551615,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Cancel,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0x22, 0x9d, 0x2c, 0x0c
        ]
        .to_vec()],
        "reply step1"
    );
    assert_eq!(
        l.watermarks(),
        (18446744073709551615, 18446744073709551615),
        "watermark step1"
    );
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(owner(&l, 0), None, "owner0 step1");
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 1,
            nonce: 1,
            slot: 1,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x04, 0xff, 0xff, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xda, 0x21, 0xf6, 0x24
        ]
        .to_vec()],
        "reply step2"
    );
    assert_eq!(
        l.watermarks(),
        (18446744073709551615, 18446744073709551615),
        "watermark step2"
    );
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(owner(&l, 0), None, "owner0 step2");
    assert_eq!(owner(&l, 1), None, "owner1 step2");
}
#[test]
fn transcript_wrong_epoch_rejected_before_state_change() {
    let mut l = Frames::cold_epoch1(true);
    let mut reply;
    reply = control(
        &mut l,
        Frame {
            epoch: 1,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Request,
        },
    );
    assert_eq!(
        reply,
        vec![[
            0x46, 0x47, 0x31, 0x39, 0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x03, 0xf0,
            0x12, 0x34, 0x56, 0x78, 0xad, 0x45, 0xc5, 0x71
        ]
        .to_vec()],
        "reply step0"
    );
    assert_eq!(l.watermarks(), (1, 0), "watermark step0");
    assert_eq!(l.stopped(), false, "stop step0");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step0"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step0");
    reply = control(
        &mut l,
        Frame {
            epoch: 2,
            frame: 0,
            nonce: 1,
            slot: 0,
            total: 1008,
            body_crc: 305419896,
            kind: Kind::Finish,
        },
    );
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step1");
    assert_eq!(l.watermarks(), (1, 0), "watermark step1");
    assert_eq!(l.stopped(), false, "stop step1");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step1"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step1");
    reply = poll(&mut l);
    assert_eq!(reply, Vec::<Vec<u8>>::new(), "reply step2");
    assert_eq!(l.watermarks(), (1, 0), "watermark step2");
    assert_eq!(l.stopped(), false, "stop step2");
    assert_eq!(
        owner(&l, 0),
        Some(([1, 0, 1, 1008, 305419896, 0], false, 0)),
        "owner0 step2"
    );
    assert_eq!(owner(&l, 1), None, "owner1 step2");
}
