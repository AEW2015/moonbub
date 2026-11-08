
pub const MAGIC: u32 = 0x4459_3731;
pub const ABI: u32 = 0x0003_0000;
pub const CAPS: u32 = 0x3f;
pub const CHUNK: usize = 1024;
pub const MAX_PACKET: u32 = 49152;
/// Replaces the receiver's existing packet array; no additional payload storage.
#[repr(align(4))]
pub struct PacketBuffer(pub [u8;CHUNK]);
impl PacketBuffer { pub const fn new()->Self{Self([0;CHUNK])} }
impl Default for PacketBuffer {fn default()->Self{Self::new()}}
const MAX_POLLS: usize = 4096;
const READY: u32 = 4;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Io { Contended, Failed, Epoch, Owner }
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Error { Io, Epoch, Owner, Identity, NotFresh, Bounds, Sequence, Deadline, Fault, Snapshot, Short, Poisoned }

/// Adapter guarantees: Contended means NO transaction/side effect started.
/// Epoch/owner are checked under the same device lock as each SPI transaction.
/// Metadata and payload writes are single complete autoincrement transactions.
/// Any uncertain/partial transfer returns Failed/short, never Contended.
pub trait Bus {
    fn read_words(&mut self, offset: u32, output: &mut [u32]) -> Result<usize, Io>;
    fn write_descriptor(&mut self, words: &[u32; 5]) -> Result<(), Io>;
    fn write_payload_be(&mut self, offset: u32, bytes: &[u8]) -> Result<usize, Io>;
    fn now(&self) -> u64;
    fn yield_now(&mut self);
}

/// Only stage_chunk creates this after exact native-prefix/CRC fence checks.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Stored { generation: u64, ticket: u32, prefix: u32, crc32: u32 }
impl Stored {
    pub fn generation(self) -> u64 { self.generation }
    pub fn ticket(self) -> u32 { self.ticket }
    pub fn prefix(self) -> u32 { self.prefix }
    pub fn crc32(self) -> u32 { self.crc32 }
}

#[derive(Debug)]
pub struct Driver {
    generation: u64, total: u32, prefix: u32, crc_internal: u32,
    expected_crc: u32, ticket: u32, identified: bool, active: bool, poisoned: bool,
}
impl Default for Driver { fn default() -> Self { Self::new() } }
impl Driver {
    pub const fn new() -> Self {
        Self { generation:0, total:0, prefix:0, crc_internal:!0,
            expected_crc:0, ticket:0, identified:false, active:false, poisoned:false }
    }
    pub fn is_poisoned(&self) -> bool { self.poisoned }
    pub fn ticket(&self) -> u32 { self.ticket }
    fn usable(&self) -> Result<(), Error> { if self.poisoned { Err(Error::Poisoned) } else { Ok(()) } }
    fn record<T>(&mut self, result: Result<T,Error>) -> Result<T,Error> {
        if result.is_err() { self.poisoned=true; } result
    }
    fn limit<B:Bus>(bus:&B, deadline:u64) -> Result<(),Error> {
        if bus.now()>=deadline { Err(Error::Deadline) } else { Ok(()) }
    }
    fn map_io(io:Io) -> Error { match io { Io::Epoch=>Error::Epoch, Io::Owner=>Error::Owner, _=>Error::Io } }
    fn read<B:Bus>(bus:&mut B, offset:u32, out:&mut[u32], deadline:u64) -> Result<(),Error> {
        for _ in 0..MAX_POLLS {
            Self::limit(bus,deadline)?;
            match bus.read_words(offset,out) {
                Ok(n) => return if n==out.len() { Self::limit(bus,deadline) } else { Err(Error::Short) },
                Err(Io::Contended) => bus.yield_now(),
                Err(e) => return Err(Self::map_io(e)),
            }
        }
        Err(Error::Deadline)
    }
    fn descriptor<B:Bus>(bus:&mut B, words:&[u32;5], deadline:u64) -> Result<(),Error> {
        for _ in 0..MAX_POLLS {
            Self::limit(bus,deadline)?;
            match bus.write_descriptor(words) {
                Ok(()) => return Self::limit(bus,deadline),
                Err(Io::Contended) => bus.yield_now(),
                Err(e) => return Err(Self::map_io(e)),
            }
        }
        Err(Error::Deadline)
    }
    fn payload<B:Bus>(bus:&mut B, bytes:&[u8], deadline:u64) -> Result<(),Error> {
        for _ in 0..MAX_POLLS {
            Self::limit(bus,deadline)?;
            match bus.write_payload_be(0xc00,bytes) {
                Ok(n) => return if n==bytes.len() { Self::limit(bus,deadline) } else { Err(Error::Short) },
                Err(Io::Contended) => bus.yield_now(),
                Err(e) => return Err(Self::map_io(e)),
            }
        }
        Err(Error::Deadline)
    }
    fn snapshot<B:Bus>(&self, bus:&mut B, ticket:u32, prefix:u32, crc:u32, deadline:u64) -> Result<(),Error> {
        for _ in 0..MAX_POLLS {
            let mut sample=[0u32;6];
            Self::read(bus,0x708,&mut sample,deadline)?;
            let flags=sample[0];
            if flags&0x11!=0 { return Err(Error::Fault); }
            if flags&!0x1f!=0 { return Err(Error::Snapshot); }
            // Live sequential reads are NOT atomic. A busy first beat makes all
            // later fields unusable even if drain completes during this read.
            if flags!=READY { bus.yield_now(); continue; }
            let mut confirm=[0]; Self::read(bus,0x708,&mut confirm,deadline)?;
            if confirm[0]&0x11!=0 { return Err(Error::Fault); }
            if confirm[0]!=READY { bus.yield_now(); continue; }
            let mut generation=[0;2];Self::read(bus,0x114,&mut generation,deadline)?;
            let mut last_ticket=[0];Self::read(bus,0x718,&mut last_ticket,deadline)?;
            let mut final_flags=[0];Self::read(bus,0x708,&mut final_flags,deadline)?;
            if final_flags[0]&0x11!=0 { return Err(Error::Fault); }
            if final_flags[0]!=READY { bus.yield_now(); continue; }
            let mut native_faults=[0];Self::read(bus,0x110,&mut native_faults,deadline)?;
            if native_faults[0]!=0 { return Err(Error::Fault); }
            let actual_generation=generation[0] as u64|((generation[1] as u64)<<32);
            if actual_generation!=self.generation || last_ticket[0]!=ticket ||
                sample[1..]!=[256,prefix,crc,ticket,0] { return Err(Error::Snapshot); }
            return Ok(());
        }
        Err(Error::Deadline)
    }
    /// Must run BEFORE the existing mailbox BEGIN. Refuses V027 ABI2 before writes.
    /// A fresh endpoint is required; no silent attach or resetting old tickets.
    pub fn identify<B:Bus>(&mut self,bus:&mut B,deadline:u64)->Result<(),Error> {
        self.usable()?;
        let r=(||{
            if self.identified { return Err(Error::Sequence); }
            let mut root=[0;3];Self::read(bus,0,&mut root,deadline)?;
            if root!=[MAGIC,ABI,CAPS] { return Err(Error::Identity); }
            let mut stb=[0;2];Self::read(bus,0x700,&mut stb,deadline)?;
            if stb!=[0x5354_4231,0x0001_0000] { return Err(Error::Identity); }
            self.snapshot(bus,0,0,0,deadline).map_err(|e|if e==Error::Snapshot {Error::NotFresh}else{e})?;
            let mut native=[0;4];Self::read(bus,0x104,&mut native,deadline)?;
            if native!=[0;4] {return Err(Error::NotFresh);}
            self.identified=true;Ok(())
        })();self.record(r)
    }
    /// Call only AFTER the existing guarded mailbox BEGIN has actually succeeded.
    /// This does not issue/admit a frame or forge a native completion.
    pub fn bind_packet<B:Bus>(&mut self,bus:&mut B,generation:u64,total:u32,expected_crc:u32,deadline:u64)->Result<(),Error> {
        self.usable()?;
        let r=(||{
            if !self.identified || self.active { return Err(Error::Sequence); }
            if total==0 || total>MAX_PACKET || generation==0 || generation<=self.generation { return Err(Error::Bounds); }
            self.generation=generation;self.total=total;self.expected_crc=expected_crc;
            self.prefix=0;self.crc_internal=!0;
            self.snapshot(bus,self.ticket,0,0,deadline)?;
            let mut native=[0;4];Self::read(bus,0x104,&mut native,deadline)?;
            if native!=[0,total,0,0] {return Err(Error::Snapshot);}
            self.active=true;Ok(())
        })();self.record(r)
    }
    /// Reuse the caller's existing packet buffer. Cache HU bytes and the frame's
    /// declared CRC before calling. The valid prefix is restored on every Result.
    /// No additional payload array, Vec, allocator call or scalar fallback.
    pub fn stage_chunk<B:Bus>(&mut self,bus:&mut B,buffer:&mut[u8],valid:usize,deadline:u64)->Result<Stored,Error> {
        self.usable()?;
        let r=(||{
            if !self.identified || !self.active { return Err(Error::Sequence); }
            if valid==0 || valid>CHUNK { return Err(Error::Bounds); }
            let padded=(valid+3)&!3;
            let end=self.prefix.checked_add(valid as u32).ok_or(Error::Bounds)?;
            if padded>buffer.len() || (buffer.as_ptr() as usize)&3!=0 || end>self.total || self.prefix&3!=0 || (valid&3!=0&&end!=self.total) { return Err(Error::Bounds); }
            let ticket=self.ticket.checked_add(1).ok_or(Error::Sequence)?;
            let crc_internal=extend(self.crc_internal,&buffer[..valid]);
            self.snapshot(bus,self.ticket,self.prefix,!self.crc_internal,deadline)?;
            let descriptor=[self.generation as u32,(self.generation>>32) as u32,self.prefix,valid as u32,ticket];
            Self::descriptor(bus,&descriptor,deadline)?;
            // Preserve only the maximum three caller bytes used as final padding.
            let mut tail=[0u8;3];let ntail=padded-valid;
            tail[..ntail].copy_from_slice(&buffer[valid..padded]);buffer[valid..padded].fill(0);
            for word in buffer[..padded].chunks_exact_mut(4) { word.reverse(); }
            let sent=Self::payload(bus,&buffer[..padded],deadline);
            for word in buffer[..padded].chunks_exact_mut(4) { word.reverse(); }
            buffer[valid..padded].copy_from_slice(&tail[..ntail]);
            sent?;
            self.snapshot(bus,ticket,end,!crc_internal,deadline)?;
            self.ticket=ticket;self.prefix=end;self.crc_internal=crc_internal;
            Ok(Stored{generation:self.generation,ticket,prefix:end,crc32:!crc_internal})
        })();self.record(r)
    }
    /// Stored in native packet RAM, not sealed/decoded/presented. The receiver
    /// must still execute and verify its actual mailbox SEAL/START/HUD lifecycle.
    pub fn finish_packet<B:Bus>(&mut self,bus:&mut B,deadline:u64)->Result<Stored,Error> {
        self.usable()?;
        let r=(||{
            if !self.active || self.prefix!=self.total || !self.crc_internal!=self.expected_crc { return Err(Error::Sequence); }
            self.snapshot(bus,self.ticket,self.total,self.expected_crc,deadline)?;
            let mut native=[0;4];Self::read(bus,0x104,&mut native,deadline)?;
            if native!=[self.total,self.total,self.expected_crc,0] {return Err(Error::Snapshot);}
            self.active=false;Ok(Stored{generation:self.generation,ticket:self.ticket,prefix:self.prefix,crc32:!self.crc_internal})
        })();self.record(r)
    }
}

pub fn extend(mut state:u32,bytes:&[u8])->u32 {
    for &byte in bytes {state^=byte as u32;for _ in 0..8 {state=(state>>1)^(0xedb8_8320u32.wrapping_mul(state&1));}}
    state
}
pub fn crc32(bytes:&[u8])->u32 { !extend(!0,bytes) }

/// Small adapter serialization helper: metadata only, never packet payload.
pub fn descriptor_be(words:&[u32;5],out:&mut[u8;20]) {
    for (word,bytes) in words.iter().zip(out.chunks_exact_mut(4)) { bytes.copy_from_slice(&word.to_be_bytes()); }
}
/// The existing FPGA SPI API consumes this already transformed raw byte slice.
/// This validator does not copy it or call a scalar fallback.
pub fn validate_raw(offset:u32,bytes:&[u8])->Result<(),Error> {
    if offset!=0xc00 || bytes.is_empty() || bytes.len()>CHUNK || bytes.len()&3!=0 || (bytes.as_ptr()as usize)&3!=0 {Err(Error::Bounds)} else {Ok(())}
}
pub fn validate_read(offset:u32,count:usize)->Result<(),Error> {
    if matches!((offset,count),(0,3)|(0x700,2)|(0x708,6)|(0x708,1)|(0x114,2)|(0x718,1)|(0x110,1)|(0x104,4)) {Ok(())} else {Err(Error::Bounds)}
}
pub fn validate_descriptor(words:&[u32;5])->Result<(),Error> {
    if words[0]|words[1]==0 || words[2]&3!=0 || words[3]==0 || words[3]>1024 ||
        words[2].checked_add(words[3]).filter(|&end|end<=MAX_PACKET).is_none() || words[4]==0 {Err(Error::Bounds)}else{Ok(())}
}

