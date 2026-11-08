"""Compile the actual status-read method against a bounded host SDK shim."""
from pathlib import Path
import hashlib,json,os,subprocess
p=Path(__file__).resolve().parents[1];out=p/'evidence/hbu-adapter-v001';out.mkdir(parents=True,exist_ok=False)
source=p/'handheld/src/cu66/local_usb.rs';text=source.read_text();start=text.index(' fn hbu_status_words(')
begin=text.index('{',start);depth=1;end=begin+1
while depth:
    depth+=(text[end]=='{')-(text[end]=='}');end+=1
method=text[start:end]
prefix='''
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
'''
tests='''
}
fn setup()->Adapter{let mut s=STATE.lock().unwrap();s.epoch=3;s.calls=0;s.fail=false;s.busy=false;s.words=[8,99,17,0x110008,27];Adapter{epoch:Some(3),reads:0,writes:0,transactions:0}}
#[test]fn one_spi_reads_five_words_maps_only_original_four_checks(){let mut a=setup();assert_eq!(a.hbu_status_words(),Ok([8,17,0x110008,27]));assert_eq!((a.reads,a.writes,a.transactions),(5,0,1));assert_eq!(STATE.lock().unwrap().calls,1);}
#[test]fn busy_has_no_transaction_or_counter_side_effect(){let mut a=setup();STATE.lock().unwrap().busy=true;assert_eq!(a.hbu_status_words(),Err(Error::Contended));assert_eq!((a.reads,a.writes,a.transactions),(0,0,0));assert_eq!(STATE.lock().unwrap().calls,0);}
#[test]fn epoch_mismatch_has_no_spi(){let mut a=setup();a.epoch=Some(2);assert_eq!(a.hbu_status_words(),Err(Error::Epoch));assert_eq!(STATE.lock().unwrap().calls,0);assert_eq!(a.transactions,0);}
#[test]fn missing_epoch_has_no_spi(){let mut a=setup();a.epoch=None;assert_eq!(a.hbu_status_words(),Err(Error::Epoch));assert_eq!(STATE.lock().unwrap().calls,0);}
#[test]fn failed_read_retains_error_and_attempt_count_no_writes(){let mut a=setup();STATE.lock().unwrap().fail=true;assert_eq!(a.hbu_status_words(),Err(Error::Io));assert_eq!((a.reads,a.writes,a.transactions),(5,0,1));assert_eq!(STATE.lock().unwrap().calls,1);}
#[test]fn packed_loaded_is_observational_as_in_original(){let mut a=setup();STATE.lock().unwrap().words[1]=u32::MAX;assert_eq!(a.hbu_status_words(),Ok([8,17,0x110008,27]));}
'''
harness=out/'adapter.rs';harness.write_text(prefix+method+tests)
env=dict(os.environ,TEMP='C:/moon/tmp',TMP='C:/moon/tmp')
commands=[[str(Path.home()/'.cargo/bin/rustc.exe'),'+stable','--edition=2021','--test',str(harness),'-o',str(out/'adapter.exe')],[str(out/'adapter.exe'),'--test-threads=1']]
steps=[]
for phase,cmd in zip(['compile','test'],commands):
    proc=subprocess.run(cmd,capture_output=True,text=True,env=env,timeout=60)
    (out/(phase+'.log')).write_text(proc.stdout+proc.stderr)
    steps.append({'phase':phase,'command':cmd,'returncode':proc.returncode})
    (out/'execution.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'harness_sha256':hashlib.sha256(harness.read_bytes()).hexdigest(),'commands':steps},indent=2)+'\n')
    print(phase,proc.returncode,flush=True)
    if proc.returncode:raise SystemExit(proc.stdout+proc.stderr)
