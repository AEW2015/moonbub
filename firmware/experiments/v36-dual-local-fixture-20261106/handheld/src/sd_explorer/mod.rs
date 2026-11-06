//! SD Explorer mailbox protocol. The ESP32 remains the only FAT filesystem owner.
use std::path::{Component, Path, PathBuf};
pub mod service;
#[cfg(not(test))]
pub mod qspi;

pub const BASE: u32 = 0x0110_0000;
pub const MAGIC: u32 = 0x4742_4d58;
pub const ABI: u32 = 0x0001_0000;
/// Each direction owns a distinct 4 KiB bank; it is not shared with UI state.
pub const PAYLOAD_BYTES: usize = 4096;
pub const REQ_SEQ: u32 = BASE + 0x10;
pub const REQ_OPCODE: u32 = BASE + 0x14;
pub const REQ_LENGTH: u32 = BASE + 0x18;
pub const REQ_COMMIT: u32 = BASE + 0x1c;
pub const RESP_SEQ: u32 = BASE + 0x20;
pub const RESP_STATUS: u32 = BASE + 0x24;
pub const RESP_LENGTH: u32 = BASE + 0x28;
pub const RESP_COMMIT: u32 = BASE + 0x2c;
pub const RESP_ACK: u32 = BASE + 0x30;
pub const REQ_PAYLOAD: u32 = BASE + 0x100;
pub const RESP_PAYLOAD: u32 = BASE + 0x1100;

#[allow(dead_code)]
#[repr(u8)] #[derive(Clone, Copy, Debug, PartialEq)]
pub enum Status { Ok=0, NoCard=1, UsbOwned=2, NotFound=3, NotDirectory=4, InvalidPath=5, NameTooLong=6, Busy=7, BadRequest=8, StaleSession=9, StaleCursor=10, IoError=11, Cancelled=12, Unsupported=13 }
#[repr(u8)] #[derive(Clone, Copy, Debug, PartialEq)]
pub enum Opcode { Hello=1, CardStatus=2, ListOpen=3, ListNext=4, ListClose=5, Stat=6, ReadChunk=7, Cancel=8 }

pub fn safe_relative_path(bytes: &[u8]) -> Result<PathBuf, Status> {
    if bytes.is_empty() || bytes.len() >= 240 || bytes.contains(&0) { return Err(Status::InvalidPath); }
    let text = std::str::from_utf8(bytes).map_err(|_| Status::InvalidPath)?;
    if text.starts_with('/') || text.contains('\\') || text.contains(':') { return Err(Status::InvalidPath); }
    let path = Path::new(text);
    if path.components().any(|c| !matches!(c, Component::Normal(_))) { return Err(Status::InvalidPath); }
    Ok(Path::new("/sdcard").join(path))
}

#[cfg(test)]
mod tests { use super::*;
 #[test] fn rejects_escape_and_accepts_relative() {
  for bad in [b"".as_slice(),b"/system",b"../x",b"a/../b",b"a\\b",b"C:x",b"a\0b", &[b'x';240][..]] { assert_eq!(safe_relative_path(bad),Err(Status::InvalidPath)); }
  assert_eq!(safe_relative_path(b"GBTEST/a file.png").unwrap(),PathBuf::from("/sdcard/GBTEST/a file.png"));
 }
}
