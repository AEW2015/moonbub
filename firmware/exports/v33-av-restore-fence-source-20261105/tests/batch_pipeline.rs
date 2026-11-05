#[allow(dead_code)] #[path = "../handheld/src/streaming/protocol.rs"] mod protocol;
#[allow(dead_code)] #[path = "../handheld/src/streaming/batch.rs"] mod batch;
#[allow(dead_code)] #[path = "../handheld/src/streaming/rx_queue.rs"] mod rx_queue;
fn packet(id:u32, offset:usize, all:&[u8], count:usize) -> Vec<u8> {
    let mut p=vec![0u8;40]; p[..4].copy_from_slice(b"MSV1"); p[4]=1; p[5]=1;
    let flags=(if offset==0 {1u16} else {0}) | (if offset+count==all.len() {2} else {0});
    p[6..8].copy_from_slice(&flags.to_be_bytes()); p[8..12].copy_from_slice(&id.to_be_bytes());
    p[12..14].copy_from_slice(&720u16.to_be_bytes()); p[14..16].copy_from_slice(&480u16.to_be_bytes());
    p[16..20].copy_from_slice(&(all.len() as u32).to_be_bytes()); p[20..24].copy_from_slice(&(offset as u32).to_be_bytes());
    p[24..26].copy_from_slice(&(count as u16).to_be_bytes()); p[28..32].copy_from_slice(&(!protocol::crc_update(!0,all)).to_be_bytes());
    p.extend_from_slice(&all[offset..offset+count]); p
}
#[test] fn bounded_batch_preserves_validated_frame_and_eof_flush() {
    let frame:Vec<u8>=(0..15367).map(|x|(x*13) as u8).collect();
    let mut receiver=protocol::Receiver::default(); let mut batch=batch::Batch::default();
    let mut buf=[0;batch::CAPACITY]; let mut sink=Vec::new(); let mut commits=0;
    for offset in (0..frame.len()).step_by(1024) {
        let p=packet(7,offset,&frame,(frame.len()-offset).min(1024));
        let (_,done)=receiver.accept(&p).unwrap(); let data=&p[40..];
        if !batch.fits(data.len()) { sink.extend_from_slice(&buf[..batch.len()]); batch.clear(); }
        batch.append(&mut buf,data,1).unwrap();
        if done || batch.len()==batch::CAPACITY { sink.extend_from_slice(&buf[..batch.len()]); batch.clear(); }
        if done { assert!(batch.is_empty()); commits+=1; }
    }
    assert_eq!(commits,1); assert_eq!(sink,frame);
}
#[test] fn corrupt_or_cancelled_frame_discards_buffer_before_new_frame() {
    let first=vec![7u8;2048]; let second=vec![9u8;512];
    let mut receiver=protocol::Receiver::default(); let mut batch=batch::Batch::default(); let mut buf=[0;batch::CAPACITY];
    let p=packet(1,0,&first,1024); receiver.accept(&p).unwrap(); batch.append(&mut buf,&p[40..],1).unwrap();
    let mut corrupt=packet(1,1024,&first,1024); corrupt[40]^=1;
    assert_eq!(receiver.accept(&corrupt),Err(protocol::Error::Integrity));
    batch.clear(); receiver.abort();
    let next=packet(2,0,&second,second.len()); assert!(receiver.accept(&next).unwrap().1);
    batch.append(&mut buf,&next[40..],2).unwrap(); assert_eq!(&buf[..batch.len()],second);
    batch.clear(); receiver.abort(); assert!(batch.is_empty());
}
#[test] fn queue_saturation_gap_discards_partial_batch_and_next_frame_recovers() {
    use std::{sync::atomic::Ordering, time::Duration};
    let data=vec![11u8; 19*1024]; let (p,c)=rx_queue::bounded((0..16).map(|_|Vec::<u8>::new()),16);
    for offset in (0..16*1024).step_by(1024) {
        let mut token=p.take().unwrap(); token.extend(packet(5,offset,&data,1024)); p.submit(token).unwrap();
    }
    assert!(p.take().is_err()); p.discard(); assert_eq!(p.counts.discarded.load(Ordering::Relaxed),1);
    let mut rx=protocol::Receiver::default(); let mut b=batch::Batch::default(); let mut storage=[0;batch::CAPACITY];
    for _ in 0..16 {
        let token=c.recv_timeout(Duration::from_millis(10)).unwrap(); let (_,done)=rx.accept(&token).unwrap(); assert!(!done);
        if !b.fits(1024) { b.flush(&storage,|_|Ok::<_,()>(())).unwrap(); }
        b.append(&mut storage,&token[40..],0).unwrap(); c.recycle(token);
    }
    let missing_then_next=packet(5,17*1024,&data,1024);
    assert_eq!(rx.accept(&missing_then_next),Err(protocol::Error::Sequence));
    b.clear(); rx.abort();
    let fresh=vec![42;512]; let packet=packet(6,0,&fresh,512);
    assert!(rx.accept(&packet).unwrap().1); b.append(&mut storage,&packet[40..],1).unwrap();
    let sent=b.flush(&storage,|d|Ok::<_,()>(d.to_vec())).unwrap().unwrap(); assert_eq!(sent,fresh);
    assert!(b.is_empty()); assert_eq!(p.counts.queued.load(Ordering::Relaxed),0);
}
