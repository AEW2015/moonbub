//! Bounded, frame-local DMA coalescing state. Storage is owned by the caller.
pub const CAPACITY: usize = 4096;
pub const DEADLINE_US: u64 = 1000;
#[derive(Default, Debug)]
pub struct Batch { len: usize, started_us: u64 }
impl Batch {
    pub fn len(&self) -> usize { self.len }
    pub fn is_empty(&self) -> bool { self.len == 0 }
    pub fn fits(&self, n: usize) -> bool { n <= CAPACITY - self.len }
    pub fn due(&self, now_us: u64) -> bool {
        !self.is_empty() && now_us.saturating_sub(self.started_us) >= DEADLINE_US
    }
    pub fn append(&mut self, storage: &mut [u8], bytes: &[u8], now_us: u64) -> Result<(), ()> {
        if storage.len() < CAPACITY || bytes.is_empty() || !self.fits(bytes.len()) { return Err(()); }
        if self.is_empty() { self.started_us = now_us; }
        storage[self.len..self.len + bytes.len()].copy_from_slice(bytes);
        self.len += bytes.len();
        Ok(())
    }
    pub fn clear(&mut self) { self.len = 0; self.started_us = 0; }
    /// A failed transfer retains ownership so the caller must abort and discard;
    /// it must never infer that an ambiguous partial DMA write can be retried.
    pub fn flush<T, E>(&mut self, storage: &[u8], send: impl FnOnce(&[u8]) -> Result<T, E>) -> Result<Option<T>, E> {
        if self.is_empty() { return Ok(None); }
        let sent = send(&storage[..self.len])?;
        self.clear();
        Ok(Some(sent))
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn contiguous_payloads_and_bounds() {
        let mut b = Batch::default(); let mut storage = [0; CAPACITY];
        for i in 0..4 { b.append(&mut storage, &[i;1024], i as u64).unwrap(); }
        assert_eq!(b.len(), CAPACITY); assert!(!b.fits(1));
        assert!(b.append(&mut storage, &[9], 10).is_err());
        for i in 0..4 { assert_eq!(&storage[i*1024..(i+1)*1024], &[i as u8;1024]); }
    }
    #[test] fn timeout_and_discard_do_not_leak_into_next_frame() {
        let mut b = Batch::default(); let mut storage = [0; CAPACITY];
        b.append(&mut storage, b"old", 50).unwrap();
        assert!(!b.due(1049)); assert!(b.due(1050)); b.clear();
        assert!(!b.due(u64::MAX)); b.append(&mut storage,b"new", 2000).unwrap();
        assert_eq!(&storage[..b.len()], b"new"); assert!(!b.due(2500));
    }
    #[test] fn arbitrary_chunks_flush_in_order() {
        let data: Vec<u8> = (0..262144).map(|n| (n*31) as u8).collect();
        let mut b = Batch::default(); let mut storage = [0; CAPACITY]; let mut out = Vec::new();
        for chunk in data.chunks(997) {
            if !b.fits(chunk.len()) { out.extend_from_slice(&storage[..b.len()]); b.clear(); }
            b.append(&mut storage, chunk, 1).unwrap();
        }
        out.extend_from_slice(&storage[..b.len()]); assert_eq!(out, data);
    }
    #[test] fn partial_transfer_error_retains_bytes_for_abort_not_retry() {
        let mut b=Batch::default(); let mut storage=[0;CAPACITY];
        b.append(&mut storage,b"frame-payload",1).unwrap();
        let mut accepted=Vec::new();
        let result=b.flush(&storage,|data| { accepted.extend_from_slice(&data[..4]); Err::<(),_>("transport") });
        assert_eq!(result,Err("transport")); assert_eq!(accepted,b"fram");
        assert_eq!(b.len(),13); b.clear(); // mandatory RX/global abort by owner
        b.append(&mut storage,b"fresh",2).unwrap();
        let got=b.flush(&storage,|data| Ok::<_,()>(data.to_vec())).unwrap().unwrap();
        assert_eq!(got,b"fresh"); assert!(b.is_empty());
        assert_eq!(b.flush(&storage,|_| panic!("empty batch must not send")),Ok::<Option<()>,()>(None));
    }
}
