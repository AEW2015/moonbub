//! Fixed metadata ring over caller-owned internal heap bytes. Never owns PCM.
pub const SLOTS: usize = 4;
pub const BLOCK_BYTES: usize = 512;
pub const STORAGE_BYTES: usize = SLOTS * BLOCK_BYTES;
pub const MAX_AGE_US: u64 = 32_000;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Meta {
    pub session: u64,
    pub sequence: u32,
    pub arrival_us: u64,
}
#[derive(Clone, Copy)]
struct Slot {
    meta: Meta,
}
const EMPTY: Slot = Slot {
    meta: Meta {
        session: 0,
        sequence: 0,
        arrival_us: 0,
    },
};
pub struct Queue {
    slots: [Slot; SLOTS],
    head: usize,
    len: usize,
    pub high_water: usize,
}
impl Queue {
    pub const fn new() -> Self {
        Self {
            slots: [EMPTY; SLOTS],
            head: 0,
            len: 0,
            high_water: 0,
        }
    }
    pub fn len(&self) -> usize {
        self.len
    }
    pub fn front(&self) -> Option<Meta> {
        if self.len == 0 {
            None
        } else {
            Some(self.slots[self.head].meta)
        }
    }
    pub fn pop(&mut self) -> Option<Meta> {
        let meta = self.front()?;
        self.head = (self.head + 1) % SLOTS;
        self.len -= 1;
        Some(meta)
    }
    pub fn stale(&self, now: u64) -> bool {
        self.front()
            .is_some_and(|m| now.saturating_sub(m.arrival_us) >= MAX_AGE_US)
    }
    pub fn push(
        &mut self,
        meta: Meta,
        data: &[u8],
        storage: &mut [u8],
    ) -> Result<Option<Meta>, ()> {
        if data.len() != BLOCK_BYTES || storage.len() != STORAGE_BYTES {
            return Err(());
        }
        let evicted = if self.len == SLOTS { self.pop() } else { None };
        let slot = (self.head + self.len) % SLOTS;
        storage[slot * BLOCK_BYTES..(slot + 1) * BLOCK_BYTES].copy_from_slice(data);
        self.slots[slot] = Slot { meta };
        self.len += 1;
        self.high_water = self.high_water.max(self.len);
        Ok(evicted)
    }
    pub fn bytes<'a>(&self, storage: &'a [u8]) -> Option<&'a [u8]> {
        if self.len == 0 || storage.len() != STORAGE_BYTES {
            return None;
        }
        Some(&storage[self.head * BLOCK_BYTES..(self.head + 1) * BLOCK_BYTES])
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn m(n: u32, t: u64) -> Meta {
        Meta {
            session: 9,
            sequence: n,
            arrival_us: t,
        }
    }
    #[test]
    fn fifo_wrap_and_independent_payloads() {
        let mut q = Queue::new();
        let mut b = [0; STORAGE_BYTES];
        for i in 0..100u32 {
            assert_eq!(q.push(m(i, i as u64), &[i as u8; 512], &mut b), Ok(None));
            assert_eq!(q.front().unwrap().sequence, i);
            assert!(q.bytes(&b).unwrap().iter().all(|x| *x == i as u8));
            assert_eq!(q.pop().unwrap().sequence, i);
            assert_eq!(q.len(), 0);
        }
    }
    #[test]
    fn overflow_replaces_oldest_waiting_never_pcm() {
        let mut q = Queue::new();
        let mut b = [0; STORAGE_BYTES];
        for i in 0..4 {
            assert_eq!(q.push(m(i, 0), &[i as u8; 512], &mut b), Ok(None));
        }
        assert_eq!(q.push(m(4, 1), &[4; 512], &mut b), Ok(Some(m(0, 0))));
        assert_eq!(q.high_water, 4);
        for i in 1..=4 {
            assert_eq!(q.pop().unwrap().sequence, i);
        }
        assert!(q.pop().is_none());
    }
    #[test]
    fn arrival_age_exact_boundary_and_saturating_time() {
        let mut q = Queue::new();
        let mut b = [0; STORAGE_BYTES];
        q.push(m(0, 100), &[0; 512], &mut b).unwrap();
        assert!(!q.stale(0));
        assert!(!q.stale(32_099));
        assert!(q.stale(32_100));
    }
    #[test]
    fn invalid_input_has_no_ring_mutation() {
        let mut q = Queue::new();
        let mut b = [0; STORAGE_BYTES];
        assert!(q.push(m(1, 0), &[0; 511], &mut b).is_err());
        assert!(q.push(m(1, 0), &[0; 512], &mut b[..100]).is_err());
        assert_eq!(q.len(), 0);
    }
    #[test]
    fn clear_is_bounded_and_keeps_source_identity() {
        let mut q = Queue::new();
        let mut b = [0; STORAGE_BYTES];
        for i in 0..4 {
            q.push(m(i, 0), &[0; 512], &mut b).unwrap();
        }
        let mut count = 0;
        while let Some(meta) = q.pop() {
            assert_eq!(meta.session, 9);
            count += 1;
        }
        assert_eq!(count, 4);
    }
}
