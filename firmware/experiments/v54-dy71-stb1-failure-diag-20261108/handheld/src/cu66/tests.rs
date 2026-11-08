use super::*;
use std::alloc::{GlobalAlloc,Layout,System};
use std::cell::Cell;
thread_local!{static TRACK:Cell<bool>=const{Cell::new(false)};static ALLOCATIONS:Cell<usize>=const{Cell::new(0)};}
struct CountAlloc;
#[global_allocator]static ALLOCATOR:CountAlloc=CountAlloc;
unsafe impl GlobalAlloc for CountAlloc{
 unsafe fn alloc(&self,l:Layout)->*mut u8{TRACK.with(|t|if t.get(){ALLOCATIONS.with(|n|n.set(n.get()+1))});System.alloc(l)}
 unsafe fn dealloc(&self,p:*mut u8,l:Layout){System.dealloc(p,l)}
 unsafe fn realloc(&self,p:*mut u8,l:Layout,n:usize)->*mut u8{TRACK.with(|t|if t.get(){ALLOCATIONS.with(|v|v.set(v.get()+1))});System.realloc(p,l,n)}
}

#[derive(Default)]
struct Model {
    abi:u32, caps:u32, generation:u64, total:u32, ticket:u32,
    bytes:Vec<u8>, pending:Vec<u8>, descriptor:Option<[u32;5]>,
    time:u64, reads:u32, writes:u32, raw_writes:u32, polls:u32,
    busy_polls:u32, busy_left:u32, flags:u32, native_faults:u32,
    wrong_crc:bool, wrong_gen:bool, wrong_ticket:bool, short_read:bool,
    short_raw:bool, raw_error:Option<Io>, desc_error:Option<Io>,
    read_error:Option<Io>, read_contended:u32, desc_contended:u32, raw_contended:u32,
    busy_sample_late_fields:bool, keep_armed:bool, native_total_delta:u32,
}
impl Model {
    fn fresh()->Self{Self{abi:ABI,caps:CAPS,..Self::default()}}
    fn begin(&mut self,generation:u64,total:usize){self.generation=generation;self.total=total as u32;self.bytes.clear();self.pending.clear();self.descriptor=None;}
    fn drain(&mut self){self.bytes.append(&mut self.pending);self.descriptor=None;}
    fn flags(&self)->u32{
        if self.flags!=0{return self.flags;}
        if self.descriptor.is_some()||self.keep_armed {if self.pending.is_empty(){6}else{10}}else{4}
    }
    fn crc(&self)->u32{crc32(&self.bytes)^(self.wrong_crc as u32)}
    fn writes(&self)->u32{self.writes+self.raw_writes}
}
impl Bus for Model {
    fn now(&self)->u64{self.time}
    fn yield_now(&mut self){self.time+=10;}
    fn read_words(&mut self,o:u32,out:&mut[u32])->Result<usize,Io>{
        self.time+=1;self.reads+=1;
        if self.read_contended!=0{self.read_contended-=1;return Err(Io::Contended);}
        if let Some(e)=self.read_error{return Err(e);}
        if self.short_read{return Ok(out.len().saturating_sub(1));}
        match (o,out.len()){
            (0,3)=>out.copy_from_slice(&[MAGIC,self.abi,self.caps]),
            (0x700,2)=>out.copy_from_slice(&[0x53544231,0x10000]),
            (0x708,6)=>{
                self.polls+=1;
                let first_flags=self.flags();
                if !self.pending.is_empty(){
                    if self.busy_left>0{self.busy_left-=1;}
                    if self.busy_left==0&&!self.keep_armed{self.drain();}
                }
                let flags=if self.busy_sample_late_fields {first_flags}else{self.flags()};
                let ready=self.flags()==4;
                out.copy_from_slice(&[flags,if ready{256}else{0},if ready{self.bytes.len() as u32}else{0},if ready{self.crc()}else{0},self.ticket+u32::from(self.wrong_ticket&&self.ticket>0),0]);
                // Adversarial later beats can look like a newer ready sample;
                // none may be used when the first flags beat was busy.
                if flags!=4&&self.busy_sample_late_fields {out[2]=0xffff;out[3]=0xdeadbeef;}
            }
            (0x708,1)=>out[0]=self.flags(),
            (0x114,2)=>{let g=self.generation+u64::from(self.wrong_gen);out.copy_from_slice(&[g as u32,(g>>32)as u32]);}
            (0x718,1)=>out[0]=self.ticket+u32::from(self.wrong_ticket&&self.ticket>0),
            (0x110,1)=>out[0]=self.native_faults,
            (0x104,4)=>out.copy_from_slice(&[self.bytes.len() as u32,self.total+self.native_total_delta,self.crc(),self.native_faults]),
            _=>panic!("unexpected read {o:x}/{}",out.len()),
        }
        Ok(out.len())
    }
    fn write_descriptor(&mut self,w:&[u32;5])->Result<(),Io>{
        self.time+=1;
        if self.desc_contended>0{self.desc_contended-=1;return Err(Io::Contended);}
        if let Some(e)=self.desc_error{return Err(e);}
        assert_eq!(w[0] as u64|((w[1]as u64)<<32),self.generation);
        assert_eq!(w[2],self.bytes.len()as u32);assert!(w[3]>0&&w[3]<=1024&&w[4]>self.ticket);
        assert!(self.pending.is_empty()&&self.descriptor.is_none());
        self.writes+=1;self.ticket=w[4];self.descriptor=Some(*w);Ok(())
    }
    fn write_payload_be(&mut self,o:u32,b:&[u8])->Result<usize,Io>{
        self.time+=1;
        if self.raw_contended>0{self.raw_contended-=1;return Err(Io::Contended);}
        if let Some(e)=self.raw_error{return Err(e);}
        validate_raw(o,b).unwrap();let d=self.descriptor.unwrap();assert_eq!(b.len(),(d[3] as usize+3)&!3);
        self.raw_writes+=1;
        for chunk in b.chunks_exact(4){let word=u32::from_be_bytes(chunk.try_into().unwrap());self.pending.extend_from_slice(&word.to_le_bytes());}
        self.pending.truncate(d[3]as usize);self.busy_left=self.busy_polls;
        Ok(if self.short_raw{b.len()-1}else{b.len()})
    }
}
fn start(data:&[u8])->(Driver,Model){let mut d=Driver::new();let mut b=Model::fresh();d.identify(&mut b,1_000_000).unwrap();b.begin(0x12345678_abcdef01,data.len());d.bind_packet(&mut b,0x12345678_abcdef01,data.len()as u32,crc32(data),1_000_000).unwrap();(d,b)}
fn data(n:usize)->Vec<u8>{(0..n).map(|i|((i*71+i/13)%256)as u8).collect()}
fn stage(d:&mut Driver,b:&mut Model,bytes:&[u8])->Result<Stored,Error>{let mut storage=PacketBuffer::new();storage.0.fill(0xa5);let buffer=&mut storage.0;buffer[..bytes.len()].copy_from_slice(bytes);let original=*buffer;let r=d.stage_chunk(b,buffer,bytes.len(),1_000_000);assert_eq!(*buffer,original,"source/padding must be restored on success/error");r}

#[test]fn crc_vectors_and_in_place_endianness(){assert_eq!(crc32(b"123456789"),0xcbf43926);let bytes=[0x11,0x22,0x33,0x44,0xaa];let(mut d,mut b)=start(&bytes);let s=stage(&mut d,&mut b,&bytes).unwrap();assert_eq!(s.prefix(),5);assert_eq!(b.bytes,bytes);assert_eq!(s.crc32(),crc32(&bytes));}
#[test]fn partial_1_2_3_and_full_1024(){for n in [1,2,3,4,1021,1022,1023,1024]{let bytes=data(n);let(mut d,mut b)=start(&bytes);let receipt=stage(&mut d,&mut b,&bytes).unwrap();assert_eq!(receipt.prefix(),n as u32);assert_eq!(b.bytes,bytes);assert_eq!(d.finish_packet(&mut b,1_000_000).unwrap(),receipt);assert_eq!(b.raw_writes,1);}}
#[test]fn maximum_packet_49152(){let bytes=data(49152);let(mut d,mut b)=start(&bytes);for chunk in bytes.chunks(1024){stage(&mut d,&mut b,chunk).unwrap();}let done=d.finish_packet(&mut b,1_000_000).unwrap();assert_eq!(done.prefix(),49152);assert_eq!(done.ticket(),48);assert_eq!(b.bytes,bytes);assert_eq!(b.raw_writes,48);assert_eq!(b.writes,48);}
#[test]fn tickets_persist_across_frames(){let bytes=data(1027);let(mut d,mut b)=start(&bytes);stage(&mut d,&mut b,&bytes[..1024]).unwrap();stage(&mut d,&mut b,&bytes[1024..]).unwrap();d.finish_packet(&mut b,1_000_000).unwrap();let next=data(1);let gen=b.generation+1;b.begin(gen,next.len());d.bind_packet(&mut b,gen,1,crc32(&next),1_000_000).unwrap();assert_eq!(stage(&mut d,&mut b,&next).unwrap().ticket(),3);}
#[test]fn v027_abi2_and_wrong_cap_refused_before_writes(){for (abi,caps) in [(0x20000,0x1f),(ABI,0x1f),(ABI,0x7f)]{let mut d=Driver::new();let mut b=Model::fresh();b.abi=abi;b.caps=caps;assert_eq!(d.identify(&mut b,1000),Err(Error::Identity));assert_eq!(b.writes(),0);assert!(d.is_poisoned());}}
#[test]fn existing_ticket_or_prefix_refused_not_attached(){for dirty in 0..3{let mut d=Driver::new();let mut b=Model::fresh();if dirty==0{b.ticket=9;}else if dirty==1{b.bytes=vec![1,2,3,4];}else{b.generation=2;}assert_eq!(d.identify(&mut b,1000),Err(Error::NotFresh));assert_eq!(b.writes(),0);}}
#[test]fn bind_requires_actual_native_begin_generation_and_length(){let mut d=Driver::new();let mut b=Model::fresh();d.identify(&mut b,1000).unwrap();assert_eq!(d.bind_packet(&mut b,1,4,0,1000),Err(Error::Snapshot));assert_eq!(b.writes(),0);let mut d=Driver::new();let mut b=Model::fresh();d.identify(&mut b,1000).unwrap();b.begin(1,3);assert_eq!(d.bind_packet(&mut b,1,4,0,1000),Err(Error::Snapshot));}
#[test]fn stale_generation_and_ticket_snapshot_refused(){for gen in [true,false]{let bytes=data(4);let(mut d,mut b)=start(&bytes);if gen{b.wrong_gen=true;}else{b.wrong_ticket=true;}assert_eq!(stage(&mut d,&mut b,&bytes),Err(Error::Snapshot));assert!(d.is_poisoned());}}
#[test]fn busy_first_read_ignores_later_ready_fields(){let bytes=data(1024);let(mut d,mut b)=start(&bytes);b.busy_polls=3;b.busy_sample_late_fields=true;let before=b.polls;let s=stage(&mut d,&mut b,&bytes).unwrap();assert_eq!(s.prefix(),1024);assert!(b.polls>=before+4);assert_eq!(b.bytes,bytes);}
#[test]fn ready_prefix_while_armed_is_not_completion(){let bytes=data(4);let(mut d,mut b)=start(&bytes);b.keep_armed=true;assert_eq!(stage(&mut d,&mut b,&bytes),Err(Error::Deadline));assert!(d.is_poisoned());assert!(b.bytes.is_empty());}
#[test]fn corrupt_native_crc_fault_and_transport_flags_fail(){for mode in 0..4{let bytes=data(4);let(mut d,mut b)=start(&bytes);match mode{0=>b.wrong_crc=true,1=>b.flags=1,2=>b.flags=16,_=>b.native_faults=1};let expected=if mode==0{Error::Snapshot}else{Error::Fault};assert_eq!(stage(&mut d,&mut b,&bytes),Err(expected));assert!(d.is_poisoned());}}
#[test]fn final_native_staging_counter_check_is_preserved(){let bytes=data(4);let(mut d,mut b)=start(&bytes);stage(&mut d,&mut b,&bytes).unwrap();b.native_total_delta=1;assert_eq!(d.finish_packet(&mut b,1000),Err(Error::Snapshot));assert!(d.is_poisoned());}
#[test]fn short_raw_and_io_epoch_owner_restore_source_no_retry(){for error in [None,Some(Io::Failed),Some(Io::Epoch),Some(Io::Owner)]{let bytes=data(7);let(mut d,mut b)=start(&bytes);if error.is_none(){b.short_raw=true;}else{b.raw_error=error;}let expected=match error{None=>Error::Short,Some(Io::Epoch)=>Error::Epoch,Some(Io::Owner)=>Error::Owner,_=>Error::Io};assert_eq!(stage(&mut d,&mut b,&bytes),Err(expected));assert!(b.raw_writes<=1);assert_eq!(stage(&mut d,&mut b,&bytes),Err(Error::Poisoned));}}
#[test]fn short_read_descriptor_error_and_epoch_abort(){for mode in 0..3{let bytes=data(4);let(mut d,mut b)=start(&bytes);let expected=match mode{0=>{b.short_read=true;Error::Short},1=>{b.desc_error=Some(Io::Failed);Error::Io},_=>{b.read_error=Some(Io::Epoch);Error::Epoch}};assert_eq!(stage(&mut d,&mut b,&bytes),Err(expected));assert_eq!(b.raw_writes,0);}}
#[test]fn bounded_lock_wait_and_safe_pretransaction_retry(){let bytes=data(4);let(mut d,mut b)=start(&bytes);b.read_contended=2;b.desc_contended=2;b.raw_contended=2;stage(&mut d,&mut b,&bytes).unwrap();assert_eq!(b.writes,1);assert_eq!(b.raw_writes,1);let(mut d,mut b)=start(&bytes);b.read_error=Some(Io::Contended);assert_eq!(stage(&mut d,&mut b,&bytes),Err(Error::Deadline));assert_eq!(b.writes(),0);}
#[test]fn absolute_deadline_and_exhausted_ticket_do_not_write(){let bytes=data(4);let(mut d,mut b)=start(&bytes);let mut buffer=PacketBuffer::new();let now=b.now();assert_eq!(d.stage_chunk(&mut b,&mut buffer.0,4,now),Err(Error::Deadline));assert_eq!(b.writes(),0);let(mut d,mut b)=start(&bytes);d.ticket=u32::MAX;b.ticket=u32::MAX;assert_eq!(stage(&mut d,&mut b,&bytes),Err(Error::Sequence));assert_eq!(b.writes(),0);}
#[test]fn bad_bounds_and_nonfinal_partial_never_write(){for (total,n,cap) in [(5,1,1024),(1024,1025,1028),(1,1,1),(1,0,4)]{let bytes=data(total);let(mut d,mut b)=start(&bytes);let mut buffer=vec![0;cap];assert_eq!(d.stage_chunk(&mut b,&mut buffer,n,1000),Err(Error::Bounds));assert_eq!(b.writes(),0);}}
#[test]fn required_raw_alias_and_small_descriptor_serialization(){let mut bytes=[0u8;20];descriptor_be(&[1,2,3,4,5],&mut bytes);assert_eq!(&bytes[..4],&[0,0,0,1]);assert!(validate_raw(0xc00,&PacketBuffer::new().0).is_ok());assert!(validate_raw(0xc00,&[0;3]).is_err());assert!(validate_raw(0x100,&[0;4]).is_err());assert!(core::mem::size_of::<Driver>()<=48);}
#[test]fn no_allocations_during_actual_identify_bind_stage_and_finish(){
 let mut b=Model::fresh();b.bytes.reserve_exact(1024);b.pending.reserve_exact(1024);let mut d=Driver::new();let mut storage=PacketBuffer::new();storage.0.fill(0x73);let buffer=&mut storage.0;let checksum=crc32(buffer);ALLOCATIONS.with(|n|n.set(0));TRACK.with(|t|t.set(true));
 let result=(||{d.identify(&mut b,10000)?;b.begin(1,1024);d.bind_packet(&mut b,1,1024,checksum,10000)?;let stored=d.stage_chunk(&mut b,buffer,1024,10000)?;let final_receipt=d.finish_packet(&mut b,10000)?;if stored!=final_receipt{return Err(Error::Snapshot)}Ok(())})();
 TRACK.with(|t|t.set(false));assert_eq!(result,Ok(()));assert_eq!(ALLOCATIONS.with(Cell::get),0);assert_eq!(*buffer,[0x73;1024]);
}
#[test]fn finish_requires_whole_packet_crc_and_no_incomplete_ack(){let bytes=data(8);let(mut d,mut b)=start(&bytes);stage(&mut d,&mut b,&bytes[..4]).unwrap();assert_eq!(d.finish_packet(&mut b,1000),Err(Error::Sequence));let(mut d,mut b)=start(&bytes);d.expected_crc^=1;stage(&mut d,&mut b,&bytes).unwrap();assert_eq!(d.finish_packet(&mut b,1000),Err(Error::Sequence));}
#[test]fn concrete_adapter_read_shapes_reject_unrelated_and_oversized_spans(){for(o,n)in[(0,3),(0x700,2),(0x708,6),(0x708,1),(0x114,2),(0x718,1),(0x110,1),(0x104,4)]{assert_eq!(validate_read(o,n),Ok(()));}for(o,n)in[(0,0),(0,4),(0x708,7),(0x100,1),(0x1000,1),(0x701,2),(0x114,3)]{assert_eq!(validate_read(o,n),Err(Error::Bounds));}}
#[test]fn concrete_adapter_descriptor_bounds(){assert_eq!(validate_descriptor(&[1,0,0,1024,1]),Ok(()));assert_eq!(validate_descriptor(&[0,1,49148,3,1]),Ok(()));for w in[[0,0,0,4,1],[1,0,1,4,1],[1,0,0,0,1],[1,0,0,1025,1],[1,0,u32::MAX,4,1],[1,0,49152,4,1],[1,0,0,4,0]]{assert_eq!(validate_descriptor(&w),Err(Error::Bounds));}}

#[test]fn packet_buffer_is_same_1024bytes_with_4byte_alignment_and_unaligned_refused(){
 assert_eq!(core::mem::size_of::<PacketBuffer>(),1024);assert_eq!(core::mem::align_of::<PacketBuffer>(),4);
 let mut packet=PacketBuffer::new();let ptr=packet.0.as_ptr()as usize;assert_eq!(ptr&3,0);
 assert!(validate_raw(0xc00,&packet.0[..4]).is_ok());assert_eq!(validate_raw(0xc00,&packet.0[1..5]),Err(Error::Bounds));
 let data=data(4);let(mut d,mut b)=start(&data);assert_eq!(d.stage_chunk(&mut b,&mut packet.0[1..5],4,1000),Err(Error::Bounds));assert_eq!(b.writes(),0);
}
