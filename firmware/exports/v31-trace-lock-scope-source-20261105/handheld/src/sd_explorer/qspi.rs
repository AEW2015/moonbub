//! Polling endpoint for the native FPGA mailbox. Filesystem work is deliberately
//! performed after releasing Device::lock(), so overlay/input service is not
//! blocked by directory enumeration or file reads.
use super::{service, Opcode, Status, ABI, BASE, MAGIC, PAYLOAD_BYTES, REQ_COMMIT, REQ_LENGTH, REQ_OPCODE, REQ_PAYLOAD, REQ_SEQ, RESP_ACK, RESP_COMMIT, RESP_LENGTH, RESP_PAYLOAD, RESP_SEQ, RESP_STATUS};
use crate::device::Device;
use std::sync::Mutex;

static LAST_REQUEST: Mutex<(u32,u32)> = Mutex::new((0,0));

/// Start a fresh native-attachment epoch.
///
/// A JTAG FPGA reconfiguration resets the volatile mailbox session/sequence
/// counters to their initial values without resetting the ESP32.  Retaining
/// the previous `(session, sequence)` here would therefore make the first
/// request from the new FPGA image look like a duplicate.  Native Attach is
/// the explicit synchronization point between the two devices, so discard
/// the old duplicate-suppression state and any filesystem cursor there.
pub fn reset_attachment() {
    *LAST_REQUEST.lock().unwrap() = (0, 0);
    service::reset_session();
}

pub fn poll_once() {
    let request={
        let mut d=Device::lock();let f=&mut d.fpga;
        if f.read_u32(BASE).ok()!=Some(MAGIC)||f.read_u32(BASE+4).ok()!=Some(ABI){return}
        let session=f.read_u32(BASE+0x0c).unwrap_or(0);
        {
            let mut last=LAST_REQUEST.lock().unwrap();
            if last.0!=session{*last=(session,0);service::reset_session();}
        }
        if let Ok(response)=f.read_u32(RESP_COMMIT){if response!=0&&f.read_u32(RESP_ACK).ok()==Some(response){let _=f.write_u32(RESP_COMMIT,0);}}
        let seq=match f.read_u32(REQ_COMMIT){Ok(v) if v!=0=>v,_=>return};
        if LAST_REQUEST.lock().unwrap().1==seq{return}
        let request_seq=f.read_u32(REQ_SEQ).unwrap_or(0);let opcode=f.read_u32(REQ_OPCODE).unwrap_or(0)as u8;
        let len=f.read_u32(REQ_LENGTH).unwrap_or(u32::MAX)as usize;
        if request_seq!=seq||len>PAYLOAD_BYTES{Some((session,seq,None,Vec::new()))}else{
            let mut payload=vec![0;len];
            for offset in(0..len).step_by(4){let Ok(word)=f.read_u32(REQ_PAYLOAD+offset as u32)else{return};for b in 0..4{if offset+b<len{payload[offset+b]=(word>>(8*b))as u8;}}}
            let op=match opcode{1=>Some(Opcode::Hello),2=>Some(Opcode::CardStatus),3=>Some(Opcode::ListOpen),4=>Some(Opcode::ListNext),5=>Some(Opcode::ListClose),6=>Some(Opcode::Stat),7=>Some(Opcode::ReadChunk),8=>Some(Opcode::Cancel),_=>None};
            Some((session,seq,op,payload))
        }
    };
    let Some((session,seq,op,payload))=request else{return};
    let(status,response)=match op{Some(op)=>service::response_for(op,&payload),None=>(Status::BadRequest,Vec::new())};
    let mut d=Device::lock();let f=&mut d.fpga;
    if f.read_u32(BASE+0x0c).ok()==Some(session){
        if write_response(f,seq,status,&response).unwrap_or(false){*LAST_REQUEST.lock().unwrap()=(session,seq);}
    }
}

fn write_response<'a,P1,P2,P3,P4>(f:&mut crate::device::drivers::fpga::Fpga<'a,P1,P2,P3,P4>,seq:u32,status:Status,payload:&[u8])->Result<bool,crate::device::drivers::fpga::Error>
where P1:embedded_hal::digital::InputPin,P2:embedded_hal::digital::OutputPin,P3:embedded_hal::digital::InputPin,P4:embedded_hal::spi::SpiDevice{
 if f.read_u32(RESP_COMMIT)?!=0{return Ok(false)}
 for offset in(0..payload.len()).step_by(4){let mut word=0u32;for b in 0..4{if offset+b<payload.len(){word|=(payload[offset+b]as u32)<<(8*b)}}f.write_u32(RESP_PAYLOAD+offset as u32,word)?;}
 f.write_u32(RESP_SEQ,seq)?;f.write_u32(RESP_STATUS,status as u32)?;f.write_u32(RESP_LENGTH,payload.len()as u32)?;f.write_u32(RESP_COMMIT,seq)?;let _=f.read_u32(RESP_ACK);Ok(true)
}
