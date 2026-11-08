"""Separate guarded DFU-to-normal reboot candidate. Default dry run never opens USB."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, struct, sys, time
P=Path(__file__).resolve().parent
LIB=Path('C:/moon/publish/host/lab-selftest-v1/dfu_vendor.py')
CLAIMS=Path('C:/moon/maintenance/dfu-normal-reboot-claims-v1')
class Refused(RuntimeError):pass
def need(ok,msg):
 if not ok:raise Refused(msg)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pairs(items):
 out={}
 for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
 return out
def document(path):
 p=Path(path);need(p.stat().st_size<=16*1024*1024,'evidence file too large');return json.loads(p.read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)
def exact_hash(value):
 need(isinstance(value,str)and len(value)==64 and all(c in '0123456789abcdef'for c in value),'full lowercase SHA256 required');return value
def library():
 pins=document(P/'source-hash-pins.json');wanted=[r for r in pins if Path(r['path']).as_posix().endswith(('/usb/control.rs','/usb/mod.rs','/reboot.rs','/dfu_vendor.py'))]
 need(len(wanted)==4,'source control pins missing')
 for row in wanted:need(sha(row['path'])==row['sha256'].lower(),'source hash changed: '+row['path'])
 old=sys.dont_write_bytecode;sys.dont_write_bytecode=True
 try:
  spec=importlib.util.spec_from_file_location('dfu_vendor',LIB);mod=importlib.util.module_from_spec(spec);sys.modules['dfu_vendor']=mod;spec.loader.exec_module(mod)
 finally:sys.dont_write_bytecode=old
 return mod

def validate(d,receipt_path,receipt_sha,plan_path,plan_sha,new_bin,new_sha,apply_journal,journal_sha,expected_elf):
 paths={str(Path(receipt_path).resolve()):exact_hash(receipt_sha),str(Path(plan_path).resolve()):exact_hash(plan_sha),str(Path(new_bin).resolve()):exact_hash(new_sha),str(Path(apply_journal).resolve()):exact_hash(journal_sha)}
 for f,h in paths.items():need(sha(f)==h,'input binding mismatch: '+f)
 exact_hash(expected_elf);receipt=document(receipt_path);plan=document(plan_path);document(plan['backup_path'])
 need(plan==d.make_plan(plan['backup_path'],new_bin,new_sha),'inconsistent app-only plan')
 backup,regions=d.checked_backup(plan['backup_path']);image=d.image(new_bin,new_sha)
 expected={'schema':'moonbub-app-only-verified-v1','result':'VERIFIED_NO_REBOOT','identity':plan['identity'],'plan_sha256':plan_sha,'new_bin_sha256':new_sha,'factory_sha256':plan['expected_factory_sha256'],'dfu_preserved':True,'partition_table_preserved':True,'automatic_retry':False,'post_reboot_ELF_verified':False}
 need(receipt==expected,'exact VERIFIED_NO_REBOOT receipt required')
 lines=Path(apply_journal).read_text(encoding='utf-8-sig').splitlines();need(lines and all(lines),'empty/ambiguous journal')
 rows=[json.loads(line,object_pairs_hook=pairs)for line in lines]
 need(all(isinstance(r,dict)and isinstance(r.get('event'),str)for r in rows),'journal event schema')
 need(not any('error'in r['event']or'fail'in r['event']for r in rows),'apply journal has error')
 starts=[r for r in rows if r['event']=='operation_start'];validated=[r for r in rows if r['event']=='apply_validated'];verified=[r for r in rows if r['event']=='readback_verified']
 need(len(starts)==len(validated)==len(verified)==1 and starts[0].get('action')=='apply','one apply/readback required')
 need(validated[0].get('plan_sha256')==plan_sha and validated[0].get('new_bin_sha256')==new_sha,'journal plan/BIN mismatch')
 terminal=verified[0];need(rows[-1]==terminal and terminal.get('sync')is True,'terminal durable readback event required')
 need(terminal.get('factory_sha256')==plan['expected_factory_sha256']and terminal.get('new_bin_sha256')==new_sha and terminal.get('dfu_preserved')is True and terminal.get('partition_preserved')is True,'journal preservation mismatch')
 # Bind every preserved input before and again after live reads.
 paths[str(Path(plan['backup_path']).resolve())]=sha(plan['backup_path'])
 for row in backup['files'].values():paths[str(Path(row['path']).resolve())]=row['sha256']
 return dict(paths=paths,plan=plan,receipt=receipt,backup=backup,regions=regions,image=image,expected_elf=expected_elf,source_pins=document(P/'source-hash-pins.json'))

def claim_path(v,receipt_hash,root=CLAIMS):
 key=hashlib.sha256(json.dumps({'receipt_sha256':receipt_hash,'identity':v['plan']['identity'],'plan_sha256':v['receipt']['plan_sha256']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return Path(root)/(key+'.json')
def reserve_attempt(path,record):
 path.parent.mkdir(parents=True,exist_ok=True)
 try:
  with path.open('x')as f:json.dump(record,f);f.flush();os.fsync(f.fileno())
 except FileExistsError:raise Refused('receipt/identity/plan already has an attempt; manual review required')

class ReadOnlyTransport:
 """Restrict the existing client's raw transport to READ plus one armed normal reboot."""
 def __init__(self,backend,clock,deadline):self.backend=backend;self.clock=clock;self.deadline=deadline;self.armed=False;self.attempts=0
 def budget(self):need(self.clock()<self.deadline,'overall live-validation deadline')
 def control(self,request,value,length,out=False):
  self.budget()
  if (request,value,length,out)==(1,1,0,True):
   need(self.armed and self.attempts==0,'one explicitly armed reboot only');self.attempts+=1;return self.backend.control(1,1,0,out=True)
  need((request,value,length,out)in[(0,0,24,False),(0x42,0,16,False)],'control request forbidden');r=self.backend.control(request,value,length,out);self.budget();return r
 def write(self,data):
  self.budget();data=bytes(data)
  if data:
   need(len(data)==32,'only READ header or READ ZLP allowed');magic,token,cmd,size,reserved,n,args=struct.unpack('<IIBBHI16s',data)
   need(magic==0x431fd10b and cmd==0x84 and size==8 and reserved==0,'flash mutation forbidden');offset,length=struct.unpack_from('<II',args);need(n==length and args[8:]==bytes(8),'READ header format')
  r=self.backend.write(data);self.budget();return r
 def read(self,n):self.budget();need(0<n<=64,'bounded bulk read');r=self.backend.read(n);self.budget();return r

def run(d,validated,receipt_path,send_once=False,backend_factory=None,journal=None,clock=time.monotonic,seconds=120,claim_root=CLAIMS):
 v=validated;need(0<seconds<=180,'bounded live deadline required')
 result={'schema':'moonbub-dfu-normal-reboot-v1','result':'DRY_RUN_NO_USB','receipt_sha256':sha(receipt_path),'new_bin_sha256':v['plan']['new_bin_sha256'],'expected_sdk_elf':v['expected_elf'],'control_contract':{'bmRequestType':0x41,'bRequest':1,'wValue':1,'wIndex':0,'payload_bytes':0},'reset_verified':False,'post_reboot_ELF_verified':False,'automatic_retry':False,'flash_writes':False,'installed_updater_source_binding':None,'source_contract_only':True}
 if not send_once:return result
 need(journal is not None and backend_factory is not None,'explicit backend and durable journal required')
 claim=claim_path(v,result['receipt_sha256'],claim_root);need(not claim.exists(),'this receipt already has a reboot attempt; manual review required')
 backend=None;attempted=False
 try:
  backend=backend_factory();io=ReadOnlyTransport(backend,clock,clock()+seconds);client=d.Client(io,timeout=5,journal=journal)
  identity=client.info();need(identity==v['plan']['identity'],'live identity mismatch')
  _,code,_,busy=client.status();need(code==0 and not busy,'updater not healthy/idle')
  factory=client.read(d.FACTORY,d.FACTORY_SIZE);need(hashlib.sha256(factory).hexdigest()==v['plan']['expected_factory_sha256']and factory[:len(v['image'])]==v['image'],'live factory differs from verified new image')
  need(hashlib.sha256(client.read(d.DFU,d.DFU_SIZE)).hexdigest()==v['backup']['files']['dfu']['sha256'],'live updater preservation mismatch')
  part=client.read(d.PARTITION_TABLE,d.PARTITION_SIZE);need(hashlib.sha256(part).hexdigest()==v['backup']['files']['partition']['sha256'],'live partition preservation mismatch');need(d.partitions(part)==v['backup']['probe']['installed_partition_layout'],'live partition layout mismatch')
  need(client.info()==identity,'identity changed before reboot');_,code,_,busy=client.status();need(code==0 and not busy,'updater became busy')
  for path,h in v['paths'].items():need(sha(path)==h,'evidence changed during probe')
  io.budget()
  # Exclusive durable receipt consumption survives ACK/error ambiguity. Never removed here.
  reserve_attempt(claim,dict(result,stage='ATTEMPT_RESERVED',identity=identity))
  journal({'event':'normal_reboot_intent','sync':True,'claim':str(claim),'receipt_sha256':result['receipt_sha256'],'request':1,'value':1,'index':0,'payload_bytes':0})
  io.armed=True;attempted=True
  try:
   answer=io.control(1,1,0,out=True);result.update(result='SENT_UNCONFIRMED',transport_return=int(answer));need(answer==0,'unexpected zero-payload control result')
  except Exception as exc:result.update(result='ATTEMPT_UNCONFIRMED',transport_error=type(exc).__name__,detail=str(exc))
  journal({'event':'normal_reboot_attempt_result','sync':True,**result});return result
 finally:
  if backend is not None:backend.close()


def main():
 a=argparse.ArgumentParser(description=__doc__)
 for name in ['receipt','plan','new-bin','apply-journal']:a.add_argument('--'+name,type=Path,required=True)
 for name in ['receipt-sha256','plan-sha256','new-sha256','apply-journal-sha256','expected-sdk-elf']:a.add_argument('--'+name,required=True)
 a.add_argument('--output',type=Path,required=True);a.add_argument('--send-once',action='store_true');a.add_argument('--libusb-dll',type=Path,default=Path('C:/msys64/ucrt64/bin/libusb-1.0.dll'));args=a.parse_args();need(args.output.resolve().is_relative_to(Path('C:/moon').resolve()),'output must stay under C:/moon')
 d=library();v=validate(d,args.receipt,args.receipt_sha256,args.plan,args.plan_sha256,args.new_bin,args.new_sha256,args.apply_journal,args.apply_journal_sha256,args.expected_sdk_elf)
 with args.output.open('x')as output:
  journal=d.Journal(str(args.output)+'.events.jsonl')if args.send_once else None
  try:r=run(d,v,args.receipt,args.send_once,(lambda:d.UsbBackend(args.libusb_dll))if args.send_once else None,journal)
  except Exception as exc:r={'result':'REFUSED_OR_FAILED_NO_AUTORETRY','error':type(exc).__name__,'detail':str(exc),'reset_verified':False,'post_reboot_ELF_verified':False,'automatic_retry':False};json.dump(r,output,indent=2);raise
  else:json.dump(r,output,indent=2);print(json.dumps(r))
  finally:
   if journal is not None:journal.close()
if __name__=='__main__':main()
