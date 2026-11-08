//! AV lease/endpoint/replay policy. No socket, FPGA or allocator.
use super::av_wire::{self, Kind, Packet};
#[derive(Clone, Copy, Debug)]
pub struct Offer {
    pub endpoint: u64,
    pub nonce: u64,
    pub cookie: u64,
    pub flags: u32,
    pub began: u64,
}
#[derive(Clone, Copy, Debug)]
pub struct Active {
    pub offer: Offer,
    pub keep_sequence: u32,
    pub lease_us: u64,
    pub audio_sequence: Option<u32>,
    pub input_sequence: u32,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Event {
    None,
    Offer,
    Started,
    RepeatStart,
    Stopped,
    Audio { gaps: u32 },
}
pub struct Session {
    pub pending: Option<Offer>,
    pub active: Option<Active>,
}
impl Session {
    pub const fn new() -> Self {
        Self {
            pending: None,
            active: None,
        }
    }
    pub fn expire(&mut self, now: u64) -> bool {
        if self
            .pending
            .is_some_and(|o| now.saturating_sub(o.began) >= 2_000_000)
        {
            self.pending = None
        }
        if self
            .active
            .is_some_and(|a| now.saturating_sub(a.lease_us) >= 500_000)
        {
            self.active = None;
            self.pending = None;
            true
        } else {
            false
        }
    }
    pub fn receive(&mut self, p: Packet<'_>, endpoint: u64, now: u64, cookie: u64) -> Event {
        match p.kind {
            Kind::Hello => {
                if let Some(a) = self.active {
                    if a.offer.endpoint == endpoint
                        && a.offer.nonce == p.cookie
                        && a.offer.flags == p.flags
                    {
                        self.pending = Some(a.offer);
                        return Event::Offer;
                    }
                    return Event::None;
                }
                if let Some(o) = self.pending {
                    if o.endpoint == endpoint
                        && o.nonce == p.cookie
                        && o.flags == p.flags
                        && now.saturating_sub(o.began) < 2_000_000
                    {
                        return Event::Offer;
                    }
                }
                if cookie == 0 {
                    return Event::None;
                }
                self.pending = Some(Offer {
                    endpoint,
                    nonce: p.cookie,
                    cookie,
                    flags: p.flags,
                    began: now,
                });
                Event::Offer
            }
            Kind::Start => {
                let nonce = u64::from_be_bytes(p.payload.try_into().unwrap());
                if let Some(a) = self.active {
                    if a.offer.endpoint == endpoint
                        && a.offer.cookie == p.cookie
                        && a.offer.nonce == nonce
                        && a.offer.flags == p.flags
                    {
                        return Event::RepeatStart;
                    }
                    return Event::None;
                }
                if let Some(o) = self.pending {
                    if o.endpoint == endpoint
                        && o.cookie == p.cookie
                        && o.nonce == nonce
                        && o.flags == p.flags
                        && now.saturating_sub(o.began) < 2_000_000
                    {
                        self.active = Some(Active {
                            offer: o,
                            keep_sequence: 1,
                            lease_us: now,
                            audio_sequence: None,
                            input_sequence: 0,
                        });
                        self.pending = None;
                        return Event::Started;
                    }
                }
                Event::None
            }
            Kind::Keep | Kind::Stop => {
                if let Some(a) = self.active.as_mut() {
                    if a.offer.endpoint == endpoint
                        && a.offer.cookie == p.cookie
                        && av_wire::newer(p.sequence, a.keep_sequence)
                    {
                        a.keep_sequence = p.sequence;
                        if p.kind == Kind::Stop {
                            self.active = None;
                            self.pending = None;
                            return Event::Stopped;
                        }
                        a.lease_us = now;
                    }
                }
                Event::None
            }
            Kind::Audio => {
                if let Some(a) = self.active.as_mut() {
                    if a.offer.endpoint == endpoint
                        && a.offer.cookie == p.cookie
                        && a.offer.flags == 1
                        && a.audio_sequence
                            .is_none_or(|previous| av_wire::newer(p.sequence, previous))
                    {
                        let gaps = a.audio_sequence.map_or(0, |previous| {
                            p.sequence.wrapping_sub(previous).saturating_sub(1)
                        });
                        a.audio_sequence = Some(p.sequence);
                        return Event::Audio { gaps };
                    }
                }
                Event::None
            }
            _ => Event::None,
        }
    }
    pub fn next_input(&mut self) -> Option<(Offer, u32)> {
        let a = self.active.as_mut()?;
        let seq = a.input_sequence;
        a.input_sequence = seq.wrapping_add(1);
        Some((a.offer, seq))
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn packet(k: Kind, cookie: u64, seq: u32, flags: u32, payload: &[u8]) -> Packet<'_> {
        Packet {
            kind: k,
            cookie,
            sequence: seq,
            flags,
            timestamp: 0,
            payload,
        }
    }
    fn start() -> Session {
        let mut s = Session::new();
        assert_eq!(
            s.receive(packet(Kind::Hello, 10, 0, 1, &[]), 7, 0, 20),
            Event::Offer
        );
        assert_eq!(
            s.receive(packet(Kind::Start, 20, 1, 1, &10u64.to_be_bytes()), 7, 1, 0),
            Event::Started
        );
        s
    }
    #[test]
    fn stale_endpoint_cookie_and_control_do_not_refresh() {
        let mut s = start();
        for (ep, cookie, seq) in [(8, 20, 2), (7, 21, 2), (7, 20, 1), (7, 20, 0)] {
            s.receive(packet(Kind::Keep, cookie, seq, 0, &[]), ep, 400_000, 0);
        }
        assert!(s.expire(500_001));
    }
    #[test]
    fn only_fresh_keep_extends_lease() {
        let mut s = start();
        s.receive(packet(Kind::Keep, 20, 2, 0, &[]), 7, 400_000, 0);
        assert!(!s.expire(800_000));
        s.receive(packet(Kind::Keep, 20, 2, 0, &[]), 7, 850_000, 0);
        assert!(s.expire(900_000));
    }
    #[test]
    fn hello_and_start_retries_do_not_reset_audio_or_lease() {
        let mut s = start();
        assert_eq!(
            s.receive(packet(Kind::Audio, 20, 4, 0, &[0; 512]), 7, 100_000, 0),
            Event::Audio { gaps: 0 }
        );
        s.next_input();
        assert_eq!(
            s.receive(packet(Kind::Hello, 10, 0, 1, &[]), 7, 400_000, 99),
            Event::Offer
        );
        assert_eq!(
            s.receive(
                packet(Kind::Start, 20, 1, 1, &10u64.to_be_bytes()),
                7,
                400_000,
                0
            ),
            Event::RepeatStart
        );
        assert_eq!(s.active.unwrap().input_sequence, 1);
        assert_eq!(s.active.unwrap().audio_sequence, Some(4));
        assert!(s.expire(500_001));
    }
    #[test]
    fn no_live_takeover_offer_expiry_and_nonce_mismatch() {
        let mut s = start();
        assert_eq!(
            s.receive(packet(Kind::Hello, 11, 0, 1, &[]), 7, 2, 99),
            Event::None
        );
        assert_eq!(
            s.receive(packet(Kind::Start, 20, 1, 1, &11u64.to_be_bytes()), 7, 2, 0),
            Event::None
        );
        s.expire(500_001);
        s.receive(packet(Kind::Hello, 11, 0, 0, &[]), 7, 500_002, 99);
        assert_eq!(
            s.receive(
                packet(Kind::Start, 99, 1, 0, &11u64.to_be_bytes()),
                7,
                2_500_002,
                0
            ),
            Event::None
        );
    }
    #[test]
    fn audio_independent_sequence_wrap_gaps_and_no_lease() {
        let mut s = start();
        for (seq, event) in [
            (u32::MAX - 1, Event::Audio { gaps: 0 }),
            (1, Event::Audio { gaps: 2 }),
            (1, Event::None),
            (0, Event::None),
        ] {
            assert_eq!(
                s.receive(packet(Kind::Audio, 20, seq, 0, &[0; 512]), 7, 400_000, 0),
                event
            );
        }
        assert!(s.expire(500_001));
    }
    #[test]
    fn input_sequence_and_stop() {
        let mut s = start();
        assert_eq!(s.next_input().unwrap().1, 0);
        assert_eq!(s.next_input().unwrap().1, 1);
        assert_eq!(
            s.receive(packet(Kind::Stop, 20, 2, 0, &[]), 7, 2, 0),
            Event::Stopped
        );
        assert!(s.next_input().is_none());
    }
}
