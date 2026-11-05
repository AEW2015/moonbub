//! Host concurrency test for the actual bounded ownership queue. The ESP-IDF
//! UDP/QSPI implementation still requires target testing.
#[path = "../handheld/src/streaming/rx_queue.rs"]
mod rx_queue;
use std::{net::UdpSocket, sync::{Arc, atomic::{AtomicBool, Ordering}}, thread, time::{Duration,Instant}};

#[test]
fn udp_burst_is_bounded_and_shutdown_releases_socket() {
    let recv=UdpSocket::bind("127.0.0.1:0").unwrap();
    recv.set_read_timeout(Some(Duration::from_millis(10))).unwrap();
    let dest=recv.local_addr().unwrap();
    let send=UdpSocket::bind("127.0.0.1:0").unwrap();
    let (producer,consumer)=rx_queue::bounded((0..4).map(|_| vec![0u8; 32]),4);
    let stop=Arc::new(AtomicBool::new(false));let done=stop.clone();
    let worker=thread::spawn(move || {
        let mut scratch=[0u8;32];
        while !done.load(Ordering::Acquire) {
            let mut slot=producer.take().ok();
            let data=match slot.as_mut() { Some(s)=>s.as_mut_slice(),None=>&mut scratch };
            match recv.recv_from(data) {
                Ok((n,_)) => {
                    if slot.is_none() { if let Ok(mut free)=producer.take() {free[..n].copy_from_slice(&scratch[..n]);slot=Some(free);} }
                    if let Some(s)=slot { if let Err(e)=producer.submit(s) { producer.discard(); match e { std::sync::mpsc::TrySendError::Full(s)|std::sync::mpsc::TrySendError::Disconnected(s)=>producer.recycle(s) } } } else { producer.discard() }
                },
                Err(e) if matches!(e.kind(),std::io::ErrorKind::WouldBlock|std::io::ErrorKind::TimedOut)=>if let Some(s)=slot {producer.recycle(s)},
                Err(e)=>panic!("UDP receive failed: {e}"),
            }
        }
    });
    // Hold the consumer to force saturation, then verify explicit bounded loss.
    for i in 0..64u8 { send.send_to(&[i],dest).unwrap();thread::sleep(Duration::from_millis(1)); }
    let deadline=Instant::now()+Duration::from_secs(2);
    while consumer.counts.discarded.load(Ordering::Relaxed)==0 && Instant::now()<deadline {thread::yield_now();}
    assert!(consumer.counts.discarded.load(Ordering::Relaxed)>0);
    assert!(consumer.counts.high_water.load(Ordering::Relaxed)<=4);
    for _ in 0..4 { let slot=consumer.recv_timeout(Duration::from_secs(1)).unwrap();consumer.recycle(slot); }
    send.send_to(&[0xee],dest).unwrap();
    let slot=consumer.recv_timeout(Duration::from_secs(2)).unwrap();assert_eq!(slot[0],0xee);consumer.recycle(slot);
    stop.store(true,Ordering::Release);worker.join().unwrap();drop(consumer);
    assert!(UdpSocket::bind(dest).is_ok(),"cancellation must release the UDP socket for reconnect");
}
