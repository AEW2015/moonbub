//! Fixed-capacity ownership queue: each token is owned by exactly one stage.
use std::sync::{Arc, atomic::{AtomicU32, Ordering}, mpsc::{self, Receiver, SyncSender, TryRecvError, TrySendError}};

#[derive(Default)]
pub struct Counts { pub queued: AtomicU32, pub high_water: AtomicU32, pub discarded: AtomicU32 }
pub struct Producer<T> { free: Receiver<T>, ready: SyncSender<T>, recycle: SyncSender<T>, pub counts: Arc<Counts> }
pub struct Consumer<T> { ready: Receiver<T>, recycle: SyncSender<T>, pub counts: Arc<Counts> }

pub fn bounded<T>(slots: impl IntoIterator<Item = T>, capacity: usize) -> (Producer<T>, Consumer<T>) {
    assert!(capacity > 0);
    let (free_tx, free_rx) = mpsc::sync_channel(capacity);
    let (ready_tx, ready_rx) = mpsc::sync_channel(capacity);
    let mut n = 0;
    for slot in slots { free_tx.try_send(slot).ok().expect("too many pool slots"); n += 1; }
    assert_eq!(n, capacity);
    let counts = Arc::new(Counts::default());
    (Producer { free: free_rx, ready: ready_tx, recycle: free_tx.clone(), counts: counts.clone() },
     Consumer { ready: ready_rx, recycle: free_tx, counts })
}
impl<T> Producer<T> {
    pub fn take(&self) -> Result<T, TryRecvError> { self.free.try_recv() }
    pub fn submit(&self, token: T) -> Result<(), TrySendError<T>> {
        let n = self.counts.queued.fetch_add(1, Ordering::AcqRel) + 1;
        match self.ready.try_send(token) {
            // Only this producer writes high_water; no atomic max/CAS loop is
            // needed, and the Xtensa backend handles the simple store reliably.
            Ok(()) => { let old = self.counts.high_water.load(Ordering::Relaxed);
                if n > old { self.counts.high_water.store(n, Ordering::Relaxed); } Ok(()) }
            Err(e) => { self.counts.queued.fetch_sub(1, Ordering::AcqRel); Err(e) }
        }
    }
    pub fn recycle(&self, token: T) { let _ = self.recycle.try_send(token); }
    pub fn discard(&self) { self.counts.discarded.fetch_add(1, Ordering::Relaxed); }
}
impl<T> Consumer<T> {
    pub fn recv_timeout(&self, timeout: std::time::Duration) -> Result<T, mpsc::RecvTimeoutError> {
        let token = self.ready.recv_timeout(timeout)?;
        self.counts.queued.fetch_sub(1, Ordering::AcqRel); Ok(token)
    }
    pub fn recycle(&self, token: T) { let _ = self.recycle.try_send(token); }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{collections::HashSet, thread, time::Duration};
    #[test]
    fn bounded_tokens_do_not_alias_and_full_queue_discards() {
        let (p,c) = bounded(0..4, 4);
        let mut owned = HashSet::new();
        for _ in 0..4 { let x=p.take().unwrap(); assert!(owned.insert(x)); p.submit(x).unwrap(); }
        assert!(matches!(p.take(), Err(TryRecvError::Empty))); p.discard();
        assert_eq!(p.counts.discarded.load(Ordering::Relaxed), 1);
        assert_eq!(p.counts.high_water.load(Ordering::Relaxed), 4);
        for _ in 0..4 { let x=c.recv_timeout(Duration::from_millis(1)).unwrap(); assert!(owned.remove(&x)); c.recycle(x); }
        assert!(owned.is_empty()); assert_eq!(p.counts.queued.load(Ordering::Relaxed), 0);
        for _ in 0..4 { assert!(owned.insert(p.take().unwrap())); }
    }
    #[test]
    fn concurrent_recycle_preserves_order_and_terminates() {
        let (p,c) = bounded((0..4).map(|i| (i, 0)), 4);
        let t=thread::spawn(move || {
            for i in 0..1000 {
                let mut x=loop { if let Ok(v)=p.take() { break v; } thread::yield_now(); };
                x.1=i; p.submit(x).unwrap();
            }
        });
        for i in 0..1000 { let x=c.recv_timeout(Duration::from_secs(2)).unwrap(); assert_eq!(x.1,i); c.recycle(x); }
        t.join().unwrap();
    }
    #[test]
    fn shutdown_returns_unsent_token_and_balances_count() {
        let (p,c) = bounded(0..1, 1);
        let token = p.take().unwrap();
        drop(c);
        assert!(matches!(p.submit(token), Err(TrySendError::Disconnected(0))));
        assert_eq!(p.counts.queued.load(Ordering::Relaxed), 0);
    }
    #[test]
    fn sixteen_slot_pool_is_bounded_and_recoverable() {
        let (p,c) = bounded(0..16, 16);
        for _ in 0..16 { let token=p.take().unwrap(); p.submit(token).unwrap(); }
        assert!(matches!(p.take(), Err(TryRecvError::Empty)));
        assert_eq!(p.counts.high_water.load(Ordering::Relaxed), 16);
        for _ in 0..16 { let token=c.recv_timeout(Duration::from_millis(2)).unwrap();c.recycle(token); }
        assert_eq!(p.counts.queued.load(Ordering::Relaxed), 0);
    }
    #[test]
    fn thirty_two_slot_pool_saturates_and_recovers_all_unique_tokens() {
        let (p,c) = bounded(0..32, 32);
        for _ in 0..32 { let token=p.take().unwrap(); p.submit(token).unwrap(); }
        assert!(matches!(p.take(),Err(TryRecvError::Empty))); p.discard();
        assert_eq!(p.counts.high_water.load(Ordering::Relaxed),32);
        assert_eq!(p.counts.discarded.load(Ordering::Relaxed),1);
        let mut seen=HashSet::new();
        for _ in 0..32 { let token=c.recv_timeout(Duration::from_millis(2)).unwrap(); assert!(seen.insert(token)); c.recycle(token); }
        assert_eq!(seen.len(),32); assert_eq!(p.counts.queued.load(Ordering::Relaxed),0);
        for _ in 0..32 { assert!(seen.remove(&p.take().unwrap())); } assert!(seen.is_empty());
    }
}
