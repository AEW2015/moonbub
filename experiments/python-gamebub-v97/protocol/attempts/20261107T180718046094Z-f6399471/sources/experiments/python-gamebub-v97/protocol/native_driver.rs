//! Standalone `rustc --test` driver; tests also exercise the retained MSV1 reader.
#[path="../../../firmware/handheld/src/streaming/protocol97.rs"] mod p;
#[path="../../../firmware/handheld/src/streaming/protocol.rs"] mod legacy;
use p::*;
use std::{fs,env};
fn unhex(s:&str)->Vec<u8> { assert_eq!(s.len()%2,0); (0..s.len()).step_by(2).map(|i|u8::from_str_radix(&s[i..i+2],16).unwrap()).collect() }
fn hex(b:&[u8])->String { b.iter().map(|v|format!("{v:02x}")).collect() }
fn setup(epoch:u32, payload:u16, core:u32)->Vec<u8> {
    let mut b=vec![0u8;40]; b[..4].copy_from_slice(b"MB97"); b[4]=97;b[5]=1;
    b[6..8].copy_from_slice(&40u16.to_be_bytes());b[8..12].copy_from_slice(&epoch.to_be_bytes());b[12..16].copy_from_slice(&JPEG.to_be_bytes());
    b[16..18].copy_from_slice(&720u16.to_be_bytes());b[18..20].copy_from_slice(&480u16.to_be_bytes());b[20..24].copy_from_slice(&JPEG_CAP.to_be_bytes());
    b[24..26].copy_from_slice(&payload.to_be_bytes());b[28..32].copy_from_slice(&CAP_JPEG.to_be_bytes());b[32..36].copy_from_slice(&core.to_be_bytes()); b
}
fn packets(data:&[u8],id:u32,epoch:u32,chunk:usize)->Vec<Vec<u8>> {
    data.chunks(chunk).enumerate().map(|(i,part)|{
        let mut b=Vec::new();b.extend(epoch.to_be_bytes());b.extend(id.to_be_bytes());b.extend((i as u16).to_be_bytes());b.push(3);
        b.push((if i==0 {1}else{0}) | (if (i+1)*chunk>=data.len() {2}else{0}));
        if i==0 { b.extend((data.len() as u32).to_be_bytes());b.extend((!crc_update(!0,data)).to_be_bytes());b.extend(1234u64.to_be_bytes()); }
        b.extend(part);b
    }).collect()
}
fn gateway()->Gateway { let mut g=Gateway::default();g.setup(&setup(7,1400,1)).unwrap();g.observe_fifo_free(2048).unwrap();g }
fn accept_complete(g:&mut Gateway,b:&[u8])->Chunk { let (c,t)=g.receive(b).unwrap();g.issue(t).unwrap();g.complete(t.token,true).unwrap();c }
fn commit(g:&mut Gateway)->Frame { let f=g.take_commit().unwrap();g.commit_complete(f.epoch,f.id,g.session().unwrap().core_generation,true).unwrap();f }

#[test]
fn shared_python_wire_vectors_independent_rust_reader() {
    let path=env::var("V97_VECTORS").unwrap();let source=fs::read_to_string(path).unwrap();let mut previous=String::new();let mut r=Receiver::default();
    let mut rows=0; let mut cases=0;let mut done=0;
    for row in source.lines() {
        let v:Vec<_>=row.split('\t').collect();assert_eq!(v.len(),5);let name=v[0];
        if name!=previous { let profile=v[1].parse::<u32>().unwrap();r=Receiver::new(SinkConfig{opaque_profile:if profile==0 {None}else{Some(profile)}},1);previous=name.into();cases+=1; }
        let actual=match v[2] {
            "SETUP"=>match r.setup(&unhex(v[4])) {Ok(ack)=>{assert_eq!(ack[5],2);"OK"},Err(_)=>"ERR"},
            "PACKET"=>match r.accept(&unhex(v[4])) {Ok(c)=>if c.crc_complete {done+=1;"DONE"}else{"MORE"},Err(_)=>"ERR"},
            "RESET"=>{r.reset();"OK"},"TIMEOUT"=>{r.abort();"OK"},"CORE"=>{r.core_changed(v[4].parse().unwrap());"OK"},_=>panic!("unknown action") };
        assert_eq!(actual,v[3],"case {name}, action {}",v[2]);rows+=1;
    }
    println!("shared_vectors cases={cases} rows={rows} complete={done}");assert!(cases>=130);
}
#[test]
fn bounded_aligned_storage_and_exact_final_lengths() {
    assert!(std::mem::size_of::<Gateway>()<3400);
    assert_eq!(std::mem::align_of::<Gateway>()%4,0);
    for n in [1,2,3,1400,1401,1402,1403] {
        let data=vec![0xa5;n];let mut g=gateway();let mut output=Vec::new();
        for b in packets(&data,1,7,1400) {
            g.observe_fifo_free(2048).unwrap();let (c,t)=g.receive(&b).unwrap();
            let exact=g.transfer_bytes(t).unwrap();assert_eq!(exact.len(),c.count);assert_eq!(exact.as_ptr() as usize%4,0);output.extend(exact);
            let storage=g.staging_storage(t).unwrap();assert_eq!(storage.len()%4,0);assert!(storage[c.count..].iter().all(|x|*x==0));
            assert!(!g.commit_ready());g.issue(t).unwrap();assert!(!g.commit_ready());g.complete(t.token,true).unwrap();
        }
        assert_eq!(output,data);assert!(g.commit_ready());assert_eq!(commit(&mut g).length,n as u32);
    }
}
#[test]
fn credits_conserved_and_backpressure_preserves_state() {
    let ps=packets(&vec![3;2801],1,7,1400);let mut g=gateway();let (_,a)=g.receive(&ps[0]).unwrap();
    assert_eq!(g.reserved_bytes(),1400);assert_eq!(g.available_bytes(),648);assert_eq!(g.observe_fifo_free(2048).unwrap(),648);
    assert_eq!(g.receive(&ps[1]),Err(Error::WouldBlock));g.issue(a).unwrap();g.complete(a.token,true).unwrap();
    assert_eq!(g.available_bytes(),648); // Completion never invents FIFO space.
    assert_eq!(g.receive(&ps[1]),Err(Error::WouldBlock));g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&ps[1]);
    accept_complete(&mut g,&ps[2]);assert!(g.commit_ready());commit(&mut g);
}
#[test]
fn two_slots_queue_order_and_held_completion_ack() {
    let ps=packets(&vec![9;2801],1,7,1400);let mut g=gateway();g.observe_fifo_free(4096).unwrap();
    let (_,a)=g.receive(&ps[0]).unwrap();let (_,b)=g.receive(&ps[1]).unwrap();
    assert_eq!(g.receive(&ps[2]),Err(Error::WouldBlock));assert_eq!(g.issue(b),Err(Error::Sequence));
    g.issue(a).unwrap();g.issue(b).unwrap();assert_eq!(g.inflight(),2);assert_eq!(g.complete(b.token,true),Err(Error::Completion));
    g.complete(a.token,true).unwrap();let (_,c)=g.receive(&ps[2]).unwrap();g.issue(c).unwrap();
    assert!(!g.commit_ready());g.complete(b.token,true).unwrap();assert!(!g.commit_ready());g.complete(c.token,true).unwrap();assert!(g.commit_ready());commit(&mut g);
}
#[test]
fn commit_request_requires_matching_ingress_ack() {
    let mut g=gateway();let a=packets(b"a",1,7,1400);let b=packets(b"b",2,7,1400);accept_complete(&mut g,&a[0]);let f=g.take_commit().unwrap();
    assert!(g.take_commit().is_none());assert_eq!(g.receive(&b[0]),Err(Error::WouldBlock));assert_eq!(g.setup(&setup(8,1400,1)),Err(Error::WouldBlock));
    for (epoch,id,core) in [(8,1,1),(7,2,1),(7,1,2),(0,1,1)] {assert_eq!(g.commit_complete(epoch,id,core,true),Err(Error::Completion));assert_eq!(g.receive(&b[0]),Err(Error::WouldBlock));}
    g.commit_complete(f.epoch,f.id,1,true).unwrap();assert_eq!(g.commit_complete(f.epoch,f.id,1,true),Err(Error::Completion));
    accept_complete(&mut g,&b[0]);assert_eq!(commit(&mut g).id,2);
}
#[test]
fn resets_at_every_transfer_phase_keep_fence_and_reject_old_tokens() {
    for phase in 0..5 {
        let mut g=gateway();let ps=packets(b"a",1,7,1400);let mut old=None;
        if phase>=1 { let (_,t)=g.receive(&ps[0]).unwrap();old=Some(t);if phase>=2 {g.issue(t).unwrap();}if phase>=3 {g.complete(t.token,true).unwrap();}if phase>=4 {g.take_commit().unwrap();} }
        g.reset();assert!(g.needs_drain());assert!(!g.commit_ready());assert_eq!(g.setup(&setup(8,1400,1)),Err(Error::DrainRequired));
        if phase==2 {assert_eq!(g.drained(),Err(Error::DrainRequired));g.complete(old.unwrap().token,true).unwrap();}
        g.drained().unwrap();assert_eq!(g.setup(&setup(7,1400,1)),Err(Error::Epoch));g.setup(&setup(8,1400,1)).unwrap();g.observe_fifo_free(2048).unwrap();
        let (_,t)=g.receive(&packets(b"new",0,8,1400)[0]).unwrap();g.issue(t).unwrap();if let Some(old)=old {assert_eq!(g.complete(old.token,true),Err(Error::Completion));}
        g.complete(t.token,true).unwrap();assert_eq!(commit(&mut g).id,0);
    }
}
#[test]
fn timeout_and_core_change_drain_and_recover() {
    let ps=packets(&vec![1;1401],1,7,1400);let mut g=gateway();let (_,t)=g.receive(&ps[0]).unwrap();g.issue(t).unwrap();g.timeout();
    assert_eq!(g.receive(&ps[1]),Err(Error::DrainRequired));assert_eq!(g.drained(),Err(Error::DrainRequired));g.complete(t.token,true).unwrap();g.drained().unwrap();
    g.observe_fifo_free(2048).unwrap();assert_eq!(g.receive(&ps[0]),Err(Error::Sequence));g.drained().unwrap();g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&packets(b"next",2,7,1400)[0]);commit(&mut g);
    g.core_changed(2);g.drained().unwrap();assert_eq!(g.setup(&setup(8,1400,1)),Err(Error::Core));assert_eq!(g.setup(&setup(7,1400,2)),Err(Error::Epoch));
    g.setup(&setup(8,1400,2)).unwrap();g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&packets(b"core2",0,8,1400)[0]);assert_eq!(commit(&mut g).id,0);
}
#[test]
fn crc_bad_never_commit_and_pending_dma_must_drain() {
    let mut ps=packets(&vec![1;1401],1,7,1400);let last=ps[1].len()-1;ps[1][last]^=1;
    let mut g=gateway();let (_,t)=g.receive(&ps[0]).unwrap();g.issue(t).unwrap();g.observe_fifo_free(2048).unwrap();
    assert_eq!(g.receive(&ps[1]),Err(Error::Integrity));assert!(!g.commit_ready());assert!(g.take_commit().is_none());assert_eq!(g.drained(),Err(Error::DrainRequired));
    g.complete(t.token,true).unwrap();g.drained().unwrap();g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&packets(b"recovery",2,7,1400)[0]);commit(&mut g);
}
#[test]
fn malformed_packet_rejected_even_without_credit() {
    let mut g=gateway();g.observe_fifo_free(0).unwrap();let mut b=packets(b"a",1,7,1400).remove(0);b[10]=4;
    assert_eq!(g.receive(&b),Err(Error::Format));assert!(g.needs_drain());g.drained().unwrap();g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&packets(b"ok",2,7,1400)[0]);commit(&mut g);
}
#[test]
fn negative_dma_and_commit_acks_never_promote() {
    let mut g=gateway();let (_,t)=g.receive(&packets(b"a",1,7,1400)[0]).unwrap();g.issue(t).unwrap();assert_eq!(g.complete(t.token,false),Err(Error::Completion));assert!(!g.commit_ready());
    g.drained().unwrap();g.observe_fifo_free(2048).unwrap();accept_complete(&mut g,&packets(b"b",2,7,1400)[0]);let f=g.take_commit().unwrap();
    assert_eq!(g.commit_complete(f.epoch,f.id,1,false),Err(Error::Completion));assert!(g.needs_drain());assert!(g.take_commit().is_none());
}
#[test]
fn malformed_transfer_handle_never_indexes_outside_stage() {
    let mut g=gateway();let (_,t)=g.receive(&packets(b"a",1,7,1400)[0]).unwrap();
    for bad in [Transfer{slot:99,..t},Transfer{token:t.token+1,..t},Transfer{logical_len:1401,..t},Transfer{storage_len:0,..t}] {assert_eq!(g.transfer_bytes(bad),Err(Error::Completion));assert_eq!(g.issue(bad),Err(Error::Completion));}
    g.issue(t).unwrap();assert_eq!(g.issue(t),Err(Error::Completion));g.complete(t.token,true).unwrap();commit(&mut g);
}
#[test]
fn native_gateway_trace_from_shared_payloads() {
    let dir=std::path::PathBuf::from(env::var("V97_DATA").unwrap());let rows=fs::read_to_string(dir.join("trace-inputs.tsv")).unwrap();let mut trace=String::new();let mut frames=0;let mut total=0;
    for row in rows.lines() {
        let v:Vec<_>=row.split('\t').collect();assert_eq!(v.len(),4);let request=unhex(v[1]);let data=fs::read(dir.join(v[2])).unwrap();let wire=fs::read(dir.join(v[3])).unwrap();
        let mut g=Gateway::default();g.setup(&request).unwrap();let mut pos=0;let mut output=Vec::new();let mut started=false;
        trace.push_str(&format!("CORE {}\nGOLDEN {}\n",g.session().unwrap().core_generation,v[2]));
        while pos<wire.len() {let n=u32::from_be_bytes(wire[pos..pos+4].try_into().unwrap()) as usize;pos+=4;let b=&wire[pos..pos+n];pos+=n;
            g.observe_fifo_free(2048).unwrap();let (c,t)=g.receive(b).unwrap();if !started {trace.push_str(&format!("START {} {} {} {:08x}\n",c.frame.epoch,c.frame.id,c.frame.length,c.frame.crc));started=true;}
            output.extend(g.transfer_bytes(t).unwrap());trace.push_str(&format!("DMA {} {} {}\n",c.frame.epoch,t.logical_len,hex(g.staging_storage(t).unwrap())));
            assert!(!g.commit_ready());g.issue(t).unwrap();g.complete(t.token,true).unwrap();
        }
        assert_eq!(output,data);let f=g.take_commit().unwrap();trace.push_str(&format!("COMMIT {} {}\n",f.epoch,f.id));g.commit_complete(f.epoch,f.id,g.session().unwrap().core_generation,true).unwrap();frames+=1;total+=data.len();
    }
    fs::write(dir.join("gateway-trace.txt"),trace).unwrap();fs::write(dir.join("native-metrics.json"),format!("{{\"frames\":{frames},\"logical_bytes\":{total},\"gateway_bytes\":{},\"receiver_bytes\":{},\"gateway_alignment\":{},\"receive_storage_bytes\":1432,\"dma_stages\":2,\"dma_payload_storage_bytes\":2800,\"gateway_plus_receive_bytes\":{},\"legacy_receiver_bytes\":{},\"esp32_timing_measured\":false,\"psram_used\":false}}\n",std::mem::size_of::<Gateway>(),std::mem::size_of::<Receiver>(),std::mem::align_of::<Gateway>(),std::mem::size_of::<Gateway>()+1432,std::mem::size_of::<legacy::Receiver>())).unwrap();
    println!("gateway_trace frames={frames} bytes={total}");assert!(frames>=10);
}
