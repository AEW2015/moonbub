//! Two-owner laboratory frame reservations. No packet credit or publication ACK.
use super::wire::{Data, Frame, Kind, NO_SLOT};
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Owner {
    pub grant: Frame,
    pub observed: u64,
    pub finished: bool,
    pub drained: bool,
    pub finish_reply_issued: bool,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Control {
    Reply(Frame),
    NoReply,
    SafeStop,
    Invalid,
}
#[derive(Debug, PartialEq, Eq)]
pub struct Frames {
    slots: [Option<Owner>; 2],
    last_request: u64,
    released: u64,
    safe: bool,
    finish_ack: bool,
}
impl Frames {
    pub const fn cold_epoch1(finish_ack: bool) -> Self {
        Self {
            slots: [None; 2],
            last_request: 0,
            released: 0,
            safe: false,
            finish_ack,
        }
    }
    pub fn owner(&self, slot: u16) -> Option<Owner> {
        self.slots.get(slot as usize).copied().flatten()
    }
    pub fn watermarks(&self) -> (u64, u64) {
        (self.last_request, self.released)
    }
    pub fn count(&self) -> usize {
        self.slots.iter().filter(|s| s.is_some()).count()
    }
    pub fn safe_stop(&mut self) {
        self.safe = true
    }
    pub fn stopped(&self) -> bool {
        self.safe
    }
    pub fn lookup(&self, d: &Data) -> Option<Owner> {
        self.slots
            .iter()
            .flatten()
            .copied()
            .find(|o| d.matches(&o.grant) && !o.drained)
    }
    fn free(&mut self, slot: usize) {
        if let Some(o) = self.slots[slot].take() {
            self.released = self.released.max(o.grant.nonce)
        }
    }
    pub fn control(&mut self, f: Frame) -> Control {
        if !f.basic_valid() || !matches!(f.kind, Kind::Request | Kind::Cancel | Kind::Finish) {
            return Control::Invalid;
        }
        if self.safe {
            return Control::SafeStop;
        }
        if f.kind == Kind::Request {
            if let Some(o) = self
                .slots
                .iter()
                .flatten()
                .find(|o| o.grant.frame == f.frame)
            {
                // Frozen Python identity excludes the requested slot for duplicate REQUEST.
                // This deliberately corrects the native C helper's stricter BUSY divergence.
                return Control::Reply(if o.grant.same_identity(&f) {
                    o.grant
                } else {
                    f.reply(Kind::Busy, NO_SLOT)
                });
            }
            if f.nonce <= self.last_request.max(self.released) {
                return Control::Reply(f.reply(Kind::Busy, NO_SLOT));
            }
            self.last_request = f.nonce;
            if f.slot >= 2 || self.slots[f.slot as usize].is_some() {
                return Control::Reply(f.reply(Kind::Busy, NO_SLOT));
            }
            let grant = f.reply(Kind::Grant, f.slot);
            self.slots[f.slot as usize] = Some(Owner {
                grant,
                observed: 0,
                finished: false,
                drained: false,
                finish_reply_issued: false,
            });
            return Control::Reply(grant);
        }
        let Some(o) = self.slots.get_mut(f.slot as usize).and_then(Option::as_mut) else {
            return Control::Reply(f.reply(Kind::Busy, NO_SLOT));
        };
        if !o.grant.exact_owner(&f) {
            return Control::Reply(f.reply(Kind::Busy, NO_SLOT));
        }
        if f.kind == Kind::Cancel {
            if o.observed != 0 {
                return Control::Reply(f.reply(Kind::Busy, NO_SLOT));
            }
            self.free(f.slot as usize);
            return Control::Reply(f.reply(Kind::Canceled, f.slot));
        }
        o.finished = true;
        if !self.finish_ack {
            return Control::NoReply;
        }
        o.finish_reply_issued = true;
        Control::Reply(f.reply(Kind::Finished, f.slot))
    }
    pub fn observe(&mut self, d: Data) -> bool {
        if self.safe || !d.valid() {
            return false;
        }
        let Some(o) = self
            .slots
            .iter_mut()
            .flatten()
            .find(|o| d.matches(&o.grant) && !o.drained)
        else {
            return false;
        };
        o.observed |= 1u64 << d.index;
        true
    }
    pub fn physical_drain(&mut self, f: Frame) -> bool {
        if self.safe || !f.basic_valid() || !matches!(f.kind, Kind::Grant | Kind::Finish) {
            return false;
        }
        let Some(o) = self.slots.get_mut(f.slot as usize).and_then(Option::as_mut) else {
            return false;
        };
        if !o.grant.exact_owner(&f) {
            return false;
        }
        o.drained = true;
        true
    }
    pub fn take_release(&mut self, f: Frame) -> Option<Frame> {
        if self.safe || !f.basic_valid() || !matches!(f.kind, Kind::Grant | Kind::Finished) {
            return None;
        }
        let o = self.owner(f.slot)?;
        if !o.grant.exact_owner(&f)
            || !o.finished
            || !o.drained
            || (self.finish_ack && !o.finish_reply_issued)
        {
            return None;
        }
        let out = o.grant.reply(Kind::Release, f.slot);
        self.free(f.slot as usize);
        Some(out)
    }
}
