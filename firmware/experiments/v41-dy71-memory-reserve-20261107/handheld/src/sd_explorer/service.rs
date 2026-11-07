use super::{safe_relative_path, Opcode, Status, PAYLOAD_BYTES};
use std::{fs, path::PathBuf, sync::Mutex};

const PAGE_ITEMS: usize = 6;

#[derive(Clone, Debug, PartialEq)]
pub struct Entry { pub name: String, pub directory: bool, pub bytes: u64 }

#[derive(Debug)]
struct Cursor { id: u32, iter: fs::ReadDir, pending: Option<Entry>, exhausted: bool }

static CURSOR: Mutex<Option<Cursor>> = Mutex::new(None);
static NEXT_CURSOR: Mutex<u32> = Mutex::new(1);

pub fn reset_session() { *CURSOR.lock().unwrap() = None; }

fn next_entry(cursor: &mut Cursor) -> Result<Option<Entry>,Status> {
 if cursor.exhausted{return Ok(None)}
 loop {match cursor.iter.next(){
  Some(Ok(item))=>{let name=item.file_name().to_string_lossy().into_owned();if name.starts_with('.') {continue}
   if name.as_bytes().len()>240{return Err(Status::NameTooLong)}
   let meta=item.metadata().map_err(map_error)?;return Ok(Some(Entry{name,directory:meta.is_dir(),bytes:meta.len()}))},
  Some(Err(e))=>return Err(map_error(e)),None=>{cursor.exhausted=true;return Ok(None)}
 }}
}

fn encode_page(cursor: &mut Cursor) -> Result<Vec<u8>,Status> {
 let mut entries=Vec::with_capacity(PAGE_ITEMS);
 if let Some(entry)=cursor.pending.take(){entries.push(entry)}
 while entries.len()<PAGE_ITEMS {match next_entry(cursor)?{Some(entry)=>entries.push(entry),None=>break}}
 if entries.len()==PAGE_ITEMS {cursor.pending=next_entry(cursor)?}
 let eof=cursor.pending.is_none()&&cursor.exhausted;
 let mut out=vec![u8::from(eof),entries.len() as u8,0,0];
 out.extend_from_slice(&cursor.id.to_le_bytes());
 for entry in &entries {
  let name=entry.name.as_bytes();
  out.push(entry.directory as u8);out.push(name.len() as u8);
  out.extend_from_slice(&entry.bytes.to_le_bytes());out.extend_from_slice(name);
 }
 Ok(out)
}

fn listing_path(path: &[u8])->Result<PathBuf,Status>{
 // Empty path means SD root only for directory listing. File operations
 // still require a nonempty, confined relative path.
 if path.is_empty(){Ok(PathBuf::from("/sdcard"))}else{safe_relative_path(path)}
}
fn open_listing(path: &[u8])->(Status,Vec<u8>){
 let root=match listing_path(path){Ok(v)=>v,Err(e)=>return(e,Vec::new())};
 match fs::read_dir(root).map_err(map_error){
  Ok(iter)=>{
   let mut next=NEXT_CURSOR.lock().unwrap();let id=*next;*next=next.wrapping_add(1).max(1);
   let mut cursor=Cursor{id,iter,pending:None,exhausted:false};let response=match encode_page(&mut cursor){Ok(v)=>v,Err(e)=>return(e,Vec::new())};
   *CURSOR.lock().unwrap()=Some(cursor);(Status::Ok,response)
  },Err(e)=>(e,Vec::new())
 }
}

fn next_listing(payload:&[u8])->(Status,Vec<u8>){
 if payload.len()!=4{return(Status::BadRequest,Vec::new())}
 let id=u32::from_le_bytes(payload.try_into().unwrap());
 let mut guard=CURSOR.lock().unwrap();
 match guard.as_mut(){Some(cursor) if cursor.id==id=>match encode_page(cursor){Ok(v)=>(Status::Ok,v),Err(e)=>(e,Vec::new())},_=>(Status::StaleCursor,Vec::new())}
}

fn close_listing(payload:&[u8])->(Status,Vec<u8>){
 if payload.len()!=4{return(Status::BadRequest,Vec::new())}
 let id=u32::from_le_bytes(payload.try_into().unwrap());let mut guard=CURSOR.lock().unwrap();
 if guard.as_ref().map(|c|c.id)!=Some(id){return(Status::StaleCursor,Vec::new())}
 *guard=None;(Status::Ok,Vec::new())
}

fn stat(path:&[u8])->(Status,Vec<u8>){
 let path=match safe_relative_path(path){Ok(v)=>v,Err(e)=>return(e,Vec::new())};
 match fs::metadata(path){Ok(meta)=>{let mut out=vec![meta.is_dir() as u8];out.extend_from_slice(&meta.len().to_le_bytes());(Status::Ok,out)},Err(e)=>(map_error(e),Vec::new())}
}

// READ_CHUNK payload is little-endian u64 offset followed by a relative path.
// Response byte 0 is EOF and remaining bytes are data actually read by ESP32.
fn read_chunk(payload:&[u8])->(Status,Vec<u8>){
 use std::io::{Read,Seek,SeekFrom};
 if payload.len()<9{return(Status::BadRequest,Vec::new())}
 let offset=u64::from_le_bytes(payload[..8].try_into().unwrap());
 let path=match safe_relative_path(&payload[8..]){Ok(v)=>v,Err(e)=>return(e,Vec::new())};
 let mut file=match fs::File::open(path){Ok(v)=>v,Err(e)=>return(map_error(e),Vec::new())};
 if file.seek(SeekFrom::Start(offset)).is_err(){return(Status::IoError,Vec::new())}
 let mut out=vec![0;PAYLOAD_BYTES];
 match file.read(&mut out[1..]){Ok(n)=>{out.truncate(n+1);out[0]=u8::from(n<PAYLOAD_BYTES-1);(Status::Ok,out)},Err(_)=>(Status::IoError,Vec::new())}
}

pub fn response_for(op:Opcode, payload:&[u8])->(Status,Vec<u8>) {
 if payload.len()>PAYLOAD_BYTES{return(Status::BadRequest,Vec::new())}
 match op {
  Opcode::Hello=>(Status::Ok,b"GBMX\x01\x00".to_vec()),
  Opcode::CardStatus=>if PathBuf::from("/sdcard").exists(){(Status::Ok,vec![1])}else{(Status::NoCard,vec![])},
  Opcode::ListOpen=>open_listing(payload),Opcode::ListNext=>next_listing(payload),Opcode::ListClose=>close_listing(payload),
  Opcode::Stat=>stat(payload),Opcode::ReadChunk=>read_chunk(payload),
  Opcode::Cancel=>{reset_session();(Status::Cancelled,Vec::new())}
 }
}

fn map_error(e:std::io::Error)->Status {match e.kind(){std::io::ErrorKind::NotFound=>Status::NotFound,std::io::ErrorKind::NotADirectory=>Status::NotDirectory,_=>Status::IoError}}

#[cfg(test)]
mod tests {
 use super::*;
 #[test]
 fn root_listing_does_not_relax_file_paths(){
  assert_eq!(listing_path(b"").unwrap(),PathBuf::from("/sdcard"));
  assert_eq!(safe_relative_path(b""),Err(Status::InvalidPath));
  assert_eq!(listing_path(b"GBTEST").unwrap(),PathBuf::from("/sdcard/GBTEST"));
  for bad in [b"/".as_slice(),b"../x",b"C:x",b"a\\b",b"a\0b"] {
   assert_eq!(listing_path(bad),Err(Status::InvalidPath));
  }
 }
}
