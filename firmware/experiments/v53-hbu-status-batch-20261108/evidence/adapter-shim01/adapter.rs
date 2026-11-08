
use std::sync::{Mutex,MutexGuard};
#[derive(Debug,PartialEq)]enum Error{Contended,Epoch,Io}
#[derive(PartialEq)]enum FpgaSpiWordSize{Bits32}
struct SpiCommand{word_size:FpgaSpiWordSize,byte_swap:bool,increment_address:bool}
const MAX_SPI_READ_CLOCK:u32=16_000_000;
struct Stub{epoch:u32,words:[u32;5],calls:usize,fail:bool,busy:bool}
static STATE:Mutex<Stub>=Mutex::new(Stub{epoch:3,words:[8,99,17,0x110008,27],calls:0,fail:false,busy:false});
impl Stub{
 fn program_epoch(&self)->u32{self.epoch}
 fn spi_read(&mut self,clock:Option<u32>,command:SpiCommand,address:u32,bytes:&mut[u8])->Result<(),()>{
  assert_eq!(clock,Some(16_000_000));assert!(command.word_size==FpgaSpiWordSize::Bits32);
  assert!(!command.byte_swap&&command.increment_address);assert_eq!(address,0xe0000608);assert_eq!(bytes.len(),20);
  self.calls+=1;if self.fail{return Err(())}
  for(i,w)in self.words.iter().enumerate(){bytes[i*4..i*4+4].copy_from_slice(&w.to_be_bytes())}Ok(())
 }
}
struct Locked{fpga:MutexGuard<'static,Stub>}
struct Device;
impl Device{fn try_lock()->Option<Locked>{let guard=STATE.try_lock().ok()?;if guard.busy{None}else{Some(Locked{fpga:guard})}}}
struct Adapter{epoch:Option<u32>,reads:u32,writes:u32,transactions:u32}
trait Bus{fn hbu_status_words(&mut self)->Result<[u32;4],Error>;}
impl Bus for Adapter {
 fn hbu_status_words(&mut self)->Result<[u32;4],Error>{
  let Some(mut d)=Device::try_lock()else{return Err(Error::Contended)};
  if self.epoch!=Some(d.fpga.program_epoch()){return Err(Error::Epoch)}
  let mut bytes=[0u8;20];self.reads=self.reads.saturating_add(5);self.transactions=self.transactions.saturating_add(1);
  d.fpga.spi_read(Some(MAX_SPI_READ_CLOCK),SpiCommand{word_size:FpgaSpiWordSize::Bits32,byte_swap:false,increment_address:true},0xe0000608,&mut bytes).map_err(|_|Error::Io)?;
  let word=|i:usize|u32::from_be_bytes(bytes[i*4..i*4+4].try_into().unwrap());
  Ok([word(0),word(2),word(3),word(4)])
 }
}
fn setup()->Adapter{let mut s=STATE.lock().unwrap();s.epoch=3;s.calls=0;s.fail=false;s.busy=false;s.words=[8,99,17,0x110008,27];Adapter{epoch:Some(3),reads:0,writes:0,transactions:0}}
#[test]fn one_spi_reads_five_words_maps_only_original_four_checks(){let mut a=setup();assert_eq!(a.hbu_status_words(),Ok([8,17,0x110008,27]));assert_eq!((a.reads,a.writes,a.transactions),(5,0,1));assert_eq!(STATE.lock().unwrap().calls,1);}
#[test]fn busy_has_no_transaction_or_counter_side_effect(){let mut a=setup();STATE.lock().unwrap().busy=true;assert_eq!(a.hbu_status_words(),Err(Error::Contended));assert_eq!((a.reads,a.writes,a.transactions),(0,0,0));assert_eq!(STATE.lock().unwrap().calls,0);}
#[test]fn epoch_mismatch_has_no_spi(){let mut a=setup();a.epoch=Some(2);assert_eq!(a.hbu_status_words(),Err(Error::Epoch));assert_eq!(STATE.lock().unwrap().calls,0);assert_eq!(a.transactions,0);}
#[test]fn missing_epoch_has_no_spi(){let mut a=setup();a.epoch=None;assert_eq!(a.hbu_status_words(),Err(Error::Epoch));assert_eq!(STATE.lock().unwrap().calls,0);}
#[test]fn failed_read_retains_error_and_attempt_count_no_writes(){let mut a=setup();STATE.lock().unwrap().fail=true;assert_eq!(a.hbu_status_words(),Err(Error::Io));assert_eq!((a.reads,a.writes,a.transactions),(5,0,1));assert_eq!(STATE.lock().unwrap().calls,1);}
#[test]fn packed_loaded_is_observational_as_in_original(){let mut a=setup();STATE.lock().unwrap().words[1]=u32::MAX;assert_eq!(a.hbu_status_words(),Ok([8,17,0x110008,27]));}
