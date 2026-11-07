//! Opt-in V97 native-portable parser and bounded gateway proof; no ESP-IDF.
//! No production register is interpreted as FIFO space. `observe_fifo_free`
//! requires an actual downstream FIFO free-byte observation, never BASE+0x0c.
//! Application must own an aligned receive buffer separately (at most 1428B
//! datagram; the study harness budgets 1432B), abort/drain the sink on
//! `needs_drain`, and send a commit only after `take_commit` succeeds.
pub const SETUP_LEN: usize = 40;
pub const HEADER: usize = 12;
pub const START_LEN: usize = 16;
pub const MAX_PAYLOAD: usize = 1400;
pub const JPEG_CAP: u32 = 262144;
pub const RESEARCH_CAP: u32 = 49152;
pub const JPEG: u32 = 1;
pub const CAP_JPEG: u32 = 1;
pub const CAP_OPAQUE: u32 = 2;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error { Header, Format, Bounds, Capability, Epoch, Core, Sequence, Integrity, WouldBlock, DrainRequired, Completion }
#[derive(Clone, Copy, Default, Debug, PartialEq, Eq)]
pub struct SinkConfig { pub opaque_profile: Option<u32> }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Session { pub epoch: u32, pub profile: u32, pub frame_cap: u32, pub payload_size: u16, pub sink_caps: u32, pub core_generation: u32 }
fn u16at(b: &[u8], n: usize) -> u16 { u16::from_be_bytes(b[n..n+2].try_into().unwrap()) }
fn u32at(b: &[u8], n: usize) -> u32 { u32::from_be_bytes(b[n..n+4].try_into().unwrap()) }
fn newer(a: u32, b: u32) -> bool { let d = a.wrapping_sub(b); d != 0 && d < 0x80000000 }
impl Session {
    pub fn parse(b: &[u8], config: SinkConfig) -> Result<Self, Error> {
        if b.len() != SETUP_LEN { return Err(Error::Header); }
        if &b[..4] != b"MB97" || b[4] != 97 || b[5] != 1 || u16at(b,6) != 40 || u32at(b,36) != 0 { return Err(Error::Format); }
        let s = Self { epoch:u32at(b,8), profile:u32at(b,12), frame_cap:u32at(b,20), payload_size:u16at(b,24), sink_caps:u32at(b,28), core_generation:u32at(b,32) };
        if s.epoch == 0 { return Err(Error::Epoch); }
        if s.core_generation == 0 { return Err(Error::Core); }
        if u16at(b,16) != 720 || u16at(b,18) != 480 || u16at(b,26) != 0 || ![1024,1400].contains(&s.payload_size) { return Err(Error::Format); }
        let research = [u32::from_be_bytes(*b"CS92"), u32::from_be_bytes(*b"CS94"), u32::from_be_bytes(*b"CS95"), u32::from_be_bytes(*b"CS96")];
        if s.profile == JPEG {
            if s.frame_cap != JPEG_CAP || s.sink_caps != CAP_JPEG { return Err(Error::Capability); }
        } else if !research.contains(&s.profile) || config.opaque_profile != Some(s.profile) || s.frame_cap != RESEARCH_CAP || s.sink_caps != CAP_OPAQUE {
            return Err(Error::Capability);
        }
        Ok(s)
    }
    pub fn ack(&self, request: &[u8]) -> [u8; SETUP_LEN] { let mut b=[0;SETUP_LEN]; b.copy_from_slice(request); b[5]=2; b }
}
pub fn crc_update(mut crc:u32, data:&[u8]) -> u32 { for b in data { crc ^= *b as u32; for _ in 0..8 { crc=(crc>>1) ^ (0xedb88320u32 & 0u32.wrapping_sub(crc&1)); } } crc }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frame { pub epoch:u32, pub id:u32, pub length:u32, pub crc:u32, pub capture_us:u64 }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Chunk { pub frame:Frame, pub index:u16, pub offset:u32, pub payload_at:usize, pub count:usize, pub crc_complete:bool }
#[derive(Clone, Copy)]
pub struct Receiver { session:Option<Session>, retired_epoch:Option<u32>, config:SinkConfig, core_generation:u32, active:Option<Frame>, last_id:Option<u32>, offset:u32, index:u16, crc:u32 }
impl Default for Receiver { fn default()->Self { Self::new(SinkConfig::default(),1) } }
impl Receiver {
    pub fn new(config:SinkConfig, core_generation:u32)->Self { Self { session:None,retired_epoch:None,config,core_generation,active:None,last_id:None,offset:0,index:0,crc:!0 } }
    pub fn session(&self)->Option<Session> { self.session }
    pub fn abort(&mut self) { self.active=None; self.offset=0; self.index=0; self.crc=!0; }
    pub fn reset(&mut self) { if let Some(s)=self.session { self.retired_epoch=Some(s.epoch); } self.session=None; self.last_id=None; self.abort(); }
    pub fn core_changed(&mut self, generation:u32) { self.reset(); self.core_generation=generation; }
    pub fn setup(&mut self, b:&[u8])->Result<[u8;40],Error> {
        let s=Session::parse(b,self.config)?;
        if s.core_generation != self.core_generation { return Err(Error::Core); }
        if self.session == Some(s) { return Ok(s.ack(b)); }
        if self.session.map(|x|x.epoch).or(self.retired_epoch).is_some_and(|e|!newer(s.epoch,e)) { return Err(Error::Epoch); }
        self.reset(); self.session=Some(s); Ok(s.ack(b))
    }
    pub fn accept(&mut self,b:&[u8])->Result<Chunk,Error> { let result=self.check(b); if result.is_err() { self.abort(); } result }
    fn check(&mut self,b:&[u8])->Result<Chunk,Error> {
        let s=self.session.ok_or(Error::Epoch)?;
        if b.len()<HEADER { return Err(Error::Header); }
        let epoch=u32at(b,0); let id=u32at(b,4); let index=u16at(b,8); let flags=b[11];
        if epoch != s.epoch { return Err(Error::Epoch); }
        if b[10]!=3 || flags & !3 != 0 || (flags&1!=0)!=(index==0) { return Err(Error::Format); }
        let mut at=HEADER;
        if index==0 {
            if b.len()<HEADER+START_LEN { return Err(Error::Header); }
            if self.last_id.is_some_and(|last|!newer(id,last)) { return Err(Error::Sequence); }
            let length=u32at(b,12);
            if length==0 || length>s.frame_cap { return Err(Error::Bounds); }
            self.active=Some(Frame{epoch,id,length,crc:u32at(b,16),capture_us:u64::from_be_bytes(b[20..28].try_into().unwrap())});
            self.offset=0; self.index=0; self.crc=!0; self.last_id=Some(id); at+=START_LEN;
        }
        let f=self.active.ok_or(Error::Sequence)?;
        if id!=f.id || index!=self.index || (index as u32).checked_mul(s.payload_size as u32)!=Some(self.offset) { return Err(Error::Sequence); }
        let count=b.len()-at;
        if count==0 || count!=(s.payload_size as u32).min(f.length-self.offset) as usize { return Err(Error::Bounds); }
        let done=self.offset+count as u32==f.length;
        if done!=(flags&2!=0) { return Err(Error::Sequence); }
        let offset=self.offset; self.crc=crc_update(self.crc,&b[at..]); self.offset+=count as u32; self.index+=1;
        if done { if !self.crc!=f.crc { return Err(Error::Integrity); } self.active=None; }
        Ok(Chunk{frame:f,index,offset,payload_at:at,count,crc_complete:done})
    }
}
#[repr(align(4))]
#[derive(Clone, Copy)]
struct Aligned([u8;MAX_PAYLOAD]);
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
enum StageState { Free, Ready, Flight }
#[derive(Clone,Copy)]
struct Stage { data:Aligned, len:usize, token:u64, state:StageState }
impl Stage { const EMPTY:Self=Self{data:Aligned([0;MAX_PAYLOAD]),len:0,token:0,state:StageState::Free}; }
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct Transfer { pub slot:usize, pub token:u64, pub logical_len:usize, pub storage_len:usize }
/// Two fixed DMA stages. Copying to these stages is the only payload storage.
/// DMA completion is an explicit ACK; queued/flight bytes remain reserved until
/// ACK. Logical lengths are exact; zero-filled tail alignment is never forwarded.
#[derive(Clone,Copy,Debug,PartialEq,Eq)]
pub struct CreditProbe { ticket:u64, epoch:u32, core_generation:u32, completed_at_request:u64 }
pub struct Gateway { receiver:Receiver, stages:[Stage;2], frame:Option<Frame>, crc_complete:bool, commit_pending:bool, available:u32, serial:u64, credit_serial:u64, pending_probe:Option<CreditProbe>, completed_bytes:u64, needs_drain:bool }
impl Default for Gateway { fn default()->Self { Self::new(SinkConfig::default(),1) } }
impl Gateway {
    pub fn new(config:SinkConfig,core_generation:u32)->Self { Self{receiver:Receiver::new(config,core_generation),stages:[Stage::EMPTY;2],frame:None,crc_complete:false,commit_pending:false,available:0,serial:0,credit_serial:0,pending_probe:None,completed_bytes:0,needs_drain:false} }
    pub fn session(&self)->Option<Session> { self.receiver.session() }
    pub fn needs_drain(&self)->bool { self.needs_drain }
    pub fn reserved_bytes(&self)->u32 { self.stages.iter().filter(|s|s.state!=StageState::Free).map(|s|s.len as u32).sum() }
    pub fn available_bytes(&self)->u32 { self.available }
    pub fn inflight(&self)->usize { self.stages.iter().filter(|s|s.state==StageState::Flight).count() }
    /// Begin an asynchronous FIFO query. Only its newest, single-use response
    /// is accepted. Completed bytes since query issuance are still charged.
    pub fn credit_probe(&mut self)->Result<CreditProbe,Error> {
        if self.needs_drain { return Err(Error::DrainRequired); }
        let s=self.receiver.session().ok_or(Error::Epoch)?;
        self.credit_serial=self.credit_serial.checked_add(1).ok_or(Error::Completion)?;
        let p=CreditProbe{ticket:self.credit_serial,epoch:s.epoch,core_generation:s.core_generation,completed_at_request:self.completed_bytes};
        self.pending_probe=Some(p);Ok(p)
    }
    pub fn credit_response(&mut self,probe:CreditProbe,actual_free:u32)->Result<u32,Error> {
        if self.needs_drain { return Err(Error::DrainRequired); }
        let s=self.receiver.session().ok_or(Error::Epoch)?;
        if self.pending_probe!=Some(probe) || probe.epoch!=s.epoch || probe.core_generation!=s.core_generation { return Err(Error::Completion); }
        self.pending_probe=None;
        let debt=self.reserved_bytes() as u64+self.completed_bytes-probe.completed_at_request;
        self.available=(actual_free as u64).saturating_sub(debt).min(u32::MAX as u64) as u32;Ok(self.available)
    }
    /// Synchronous, ordered actual FIFO observation. The tuple must match the
    /// active session. Never pass remaining-frame bytes from BASE+0x0c here.
    /// Use credit_probe/credit_response for an asynchronous status transaction.
    pub fn observe_fifo_free(&mut self,epoch:u32,core_generation:u32,actual_free:u32)->Result<u32,Error> {
        let s=self.receiver.session().ok_or(Error::Epoch)?;
        if s.epoch!=epoch || s.core_generation!=core_generation { return Err(Error::Completion); }
        let probe=self.credit_probe()?;self.credit_response(probe,actual_free)
    }
    pub fn setup(&mut self,b:&[u8])->Result<[u8;40],Error> {
        if self.needs_drain { return Err(Error::DrainRequired); }
        // Validate first; a malformed setup never cancels an established stream.
        let s=Session::parse(b,self.receiver.config)?;
        if self.receiver.session()==Some(s) { return self.receiver.setup(b); }
        if self.commit_pending { return Err(Error::WouldBlock); }
        if self.frame.is_some() || self.reserved_bytes()!=0 { self.reset(); return Err(Error::DrainRequired); }
        let ack=self.receiver.setup(b)?; self.pending_probe=None; self.available=0; Ok(ack)
    }
    pub fn receive(&mut self,b:&[u8])->Result<(Chunk,Transfer),Error> {
        if self.needs_drain { return Err(Error::DrainRequired); }
        if self.commit_pending { return Err(Error::WouldBlock); }
        // Speculate in a tiny metadata copy. Structural/CRC errors abort even
        // with no credits; legitimate backpressure never consumes parser state.
        let mut candidate=self.receiver;
        let c=match candidate.accept(b) { Ok(c)=>c,Err(e)=>{self.abort_frame();return Err(e)} };
        if self.crc_complete { return Err(Error::WouldBlock); }
        if self.frame.is_some() && c.index==0 { self.abort_frame(); return Err(Error::Sequence); }
        let slot=self.stages.iter().position(|s|s.state==StageState::Free).ok_or(Error::WouldBlock)?;
        if c.count as u32>self.available { return Err(Error::WouldBlock); }
        self.receiver=candidate;
        self.serial=self.serial.checked_add(1).ok_or(Error::Completion)?;
        let stage=&mut self.stages[slot]; stage.data.0[..c.count].copy_from_slice(&b[c.payload_at..]);
        let dma_len=(c.count+3)&!3; stage.data.0[c.count..dma_len].fill(0); stage.len=c.count; stage.token=self.serial; stage.state=StageState::Ready;
        self.available-=c.count as u32; self.frame=Some(c.frame); self.crc_complete=c.crc_complete;
        Ok((c,Transfer{slot,token:self.serial,logical_len:c.count,storage_len:dma_len}))
    }
    fn checked_stage(&self,t:Transfer)->Result<&Stage,Error> {
        let s=self.stages.get(t.slot).ok_or(Error::Completion)?;
        if s.token!=t.token || s.state==StageState::Free || t.logical_len!=s.len || t.storage_len!=((s.len+3)&!3) { return Err(Error::Completion); }
        Ok(s)
    }
    /// Exact logical DMA byte span. Configure SPI transfer length from this
    /// slice; its pointer is 4-byte aligned even for a 1/2/3-byte final tail.
    pub fn transfer_bytes(&self,t:Transfer)->Result<&[u8],Error> { Ok(&self.checked_stage(t)?.data.0[..t.logical_len]) }
    /// Diagnostic storage span including zero padding, never a wire transfer.
    pub fn staging_storage(&self,t:Transfer)->Result<&[u8],Error> { Ok(&self.checked_stage(t)?.data.0[..t.storage_len]) }
    pub fn issue(&mut self,t:Transfer)->Result<(),Error> {
        if self.needs_drain { return Err(Error::DrainRequired); }
        self.checked_stage(t)?;
        if self.stages.iter().any(|s|s.state==StageState::Ready && s.token<t.token) { return Err(Error::Sequence); }
        let s=&mut self.stages[t.slot]; if s.state!=StageState::Ready { return Err(Error::Completion); } s.state=StageState::Flight; Ok(())
    }
    /// ACK means exact logical bytes accepted by the sink in issue order, with
    /// no hidden queue remaining before its commit boundary. Host DMA kickoff
    /// or an ACK issued before a downstream CDC queue drains is insufficient.
    pub fn complete(&mut self,token:u64,success:bool)->Result<(),Error> {
        let slot=self.stages.iter().enumerate().filter(|(_,s)|s.state==StageState::Flight).min_by_key(|(_,s)|s.token).map(|(i,_)|i).ok_or(Error::Completion)?;
        if self.stages[slot].token!=token { return Err(Error::Completion); }
        self.completed_bytes=self.completed_bytes.checked_add(self.stages[slot].len as u64).ok_or(Error::Completion)?;
        self.stages[slot].state=StageState::Free; // ACK releases storage, not FIFO credit.
        if !success { self.abort_frame(); return Err(Error::Completion); } Ok(())
    }
    pub fn commit_ready(&self)->bool { !self.needs_drain && !self.commit_pending && self.frame.is_some() && self.crc_complete && self.reserved_bytes()==0 }
    /// Returned metadata authorizes a commit request, not display publication.
    pub fn take_commit(&mut self)->Option<Frame> { if !self.commit_ready() { return None; } self.commit_pending=true; self.frame }
    /// Authoritative ingress commit ACK, distinct from DMA and publication.
    /// Wrong/replayed tuples are ignored; negative matching ACK aborts/drains.
    pub fn commit_complete(&mut self,epoch:u32,id:u32,core_generation:u32,success:bool)->Result<(),Error> {
        let f=self.frame.ok_or(Error::Completion)?;
        if !self.commit_pending || f.epoch!=epoch || f.id!=id || self.receiver.session().map(|s|s.core_generation)!=Some(core_generation) { return Err(Error::Completion); }
        if !success { self.abort_frame(); return Err(Error::Completion); }
        self.frame=None; self.crc_complete=false; self.commit_pending=false; Ok(())
    }
    pub fn abort_frame(&mut self) { self.receiver.abort(); self.frame=None; self.crc_complete=false; self.commit_pending=false; self.available=0; self.pending_probe=None; self.needs_drain=true; for s in &mut self.stages { if s.state==StageState::Ready { s.state=StageState::Free; } } }
    pub fn reset(&mut self) { self.abort_frame(); self.receiver.reset(); }
    pub fn timeout(&mut self) { self.abort_frame(); }
    pub fn core_changed(&mut self,generation:u32) { self.reset(); self.receiver.core_changed(generation); }
    /// Caller confirms downstream abort was ACKed and all issued DMA has ACKed.
    /// It must never manufacture this fence on a timer or inferred FIFO drain.
    pub fn drained(&mut self)->Result<(),Error> { if self.inflight()!=0 { return Err(Error::DrainRequired); } self.needs_drain=false; self.available=0; Ok(()) }
}
