"""Offline plan by default; explicit reviewed final-v008/v36 one-shot serial fixture.
No programming, reset, updater, radio, SD, lease release or guessed commands.
"""
from pathlib import Path
import argparse,base64,datetime,hashlib,json,re,time
ELF='13278b1f5a16afbcc5c1ed2f3c4c225c628a05b4491cc8e9ec489d02c88d3535'
SOURCE='15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69'
VARIANT='v36-dual-local-fixture-20261106'
GATES=('source_binding','functional','sdk_rtl_pairing','timing_setup_hold_pulse','route','native_drc','cdc_constraints')
COMMANDS=('?','W','Y','?')
class Refusal(RuntimeError):pass

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise Refusal(message)
def load(p):return json.loads(Path(p).read_text())
def verify_qualification(path,receipt_path):
 """Versioned reviewed handoff receipt; no claimed qualification is generated here."""
 path=Path(path).resolve();q=load(path)
 require(q.get('schema')=='MOONBUB_FINAL_V008_FIRST_FIXTURE_QUALIFICATION_V1','Unreviewed qualification schema')
 require(q.get('overall')=='PASS','BIT qualification not PASS')
 require(q.get('source_manifest_sha256')==SOURCE,'Wrong selected source manifest')
 artifacts={}
 for a in q.get('artifacts',[]):
  p=Path(a['path']);p=p if p.is_absolute() else path.parent/p;p=p.resolve()
  require(p.is_file() and digest(p)==a['sha256'],'Artifact hash mismatch: '+str(p));artifacts[a['sha256']]=p
 require(SOURCE in artifacts and ELF in artifacts,'Exact source manifest and ELF artifacts missing')
 bit=q.get('bit_sha256');require(bit in artifacts and artifacts[bit].suffix.lower()=='.bit','Qualified BIT artifact missing')
 require(load(artifacts[SOURCE]).get('top')=='cu71_system_final_v008','Wrong manifest top')
 for gate in GATES:
  g=q.get('checks',{}).get(gate,{})
  require(g.get('status')=='PASS' and g.get('evidence_sha256') in artifacts,'Missing hash-bound gate: '+gate)
 receipt=load(receipt_path)
 require(receipt.get('schema')=='MOONBUB_FIRST_FIXTURE_OPERATOR_RECEIPT_V1','Missing reviewed programming/operator receipt')
 require(receipt.get('qualification_manifest_sha256')==digest(path) and receipt.get('programmed_bit_sha256')==bit,'Programming receipt does not bind qualified BIT')
 require(receipt.get('installed_elf_sha256')==ELF,'Programming receipt ELF mismatch')
 require(receipt.get('profile')=={'magic':'44593731','abi':'00010000','capabilities':'0000000f'},'DY71 programming receipt profile mismatch')
 for name in ('separate_B50_25fps_test_complete','host_senders_stopped','hardware_exclusive','fresh_paired_app_and_fpga_state','camera_coverage_verified','no_held_or_quarantined_lease'):
  require(receipt.get(name) is True,'Operator precondition not verified: '+name)
 require(bool(receipt.get('programming_record_sha256')) and receipt['programming_record_sha256'] in artifacts,'Actual programming record artifact required')
 return {'qualification_sha256':digest(path),'receipt_sha256':digest(receipt_path),'bit_sha256':bit,'ELF_sha256':ELF,'source_manifest_sha256':SOURCE}

def parse_identity(lines):
 captures={}
 for line in lines:
  m=re.search(r'USB_D24 v=1 c=(\d+) g=\d+ e=\d+ f=\d+ p=(\w+) (.*)',line)
  if m:captures.setdefault(m[1],{})[m[2]]=dict(re.findall(r'(\w+)=([^\s]+)',m[3]))
 for _,p in reversed(list(captures.items())):
  if {'reset','variant','memory','elf','end'}<=p.keys():
   require(p['variant'].get('name')==VARIANT,'Runtime firmware variant mismatch')
   require(p['elf'].get('sdk_elf_sha256')==ELF,'Runtime installed ELF identity mismatch')
   return p
 return None

def parse_cpu(lines):
 frames=[x for x in lines if 'USB_CU66_HUD frame='in x]
 caught=[x for x in lines if 'USB_CU66_HUD caught_allocation_failure=true'in x]
 terminal=[x for x in lines if 'USB_CU66_HUD result='in x and 'elapsed_us='in x]
 if not terminal:return None
 require('result=Ok('in terminal[-1],'CPU W failed: '+terminal[-1])
 require(len(frames)==2 and all('read_words=21120'in x for x in frames),'CPU frame/readback rows missing')
 require(len(caught)==1,'CPU deliberate allocator throw/catch proof missing')
 require({re.search(r'read_crc=([0-9a-f]{8})',x)[1] for x in frames if re.search(r'read_crc=([0-9a-f]{8})',x)}=={'358486a6','9b082f5c'},'CPU fixture CRC rows mismatch')
 return {'frame_rows':frames,'first_throw_row':caught[0],'first_throw_heap':{k:number(caught[0],k) for k in ('heap_before_negative','heap_before_throw','heap_after_throw','heap_after_drop')},'terminal_row':terminal[-1],'stack_high_water_raw':number(terminal[-1],'stack_low'),'hardware_access':False,'first_throw_largest_free_block':'not logged by sealed v36 W probe; runtime largest samples are separate','allocator_order':['limit','live','peak','maximum_allocation','allocations','failures']}

def number(line,key):
 m=re.search(r'\b'+re.escape(key)+r'[=:] ?(\d+)',line);return int(m[1])if m else None

def report_arrays(row):
 return {name:[int(v.strip()) for v in body.split(',') if v.strip()] for name,body in re.findall(r'(\w+): \[([^\]]*)\]',row)}

def heap_pairs(row):
 return {name:[int(a),int(b)] for name,a,b in re.findall(r'(heap_before|heap_after)=\((\d+), ?(\d+)\)',row)}

def parse_local(lines):
 terminal=[x for x in lines if 'USB_CU71_LOCAL result='in x and ('report='in x or 'reason='in x)]
 held=[x for x in lines if 'USB_CU71_LOCAL state='in x]
 if not terminal:return None
 row=terminal[-1]
 if 'result=failed'in row and number(row,'writes') not in (None,0) and not held:return None
 if 'result=failed'in row:return {'success':False,'terminal_row':row,'held_row':held[-1]if held else None,'recovery':'preserve native endpoint and lease; no automatic retry or unquarantine'}
 if not held:return None
 require(any('completed_profile=Dy71 success=true'in x for x in lines),'DY71 completion missing')
 expected={'frames':2,'accepted':2,'presented':2,'rejected':0,'underruns':0,'words_written':42240,'words_verified':42240}
 require(all(number(row,k)==v for k,v in expected.items()),'Local fixture report counters do not match required outcomes')
 require('state=completed_held endpoint_retained=true lease_retained=true reconfigure_required=true'in held[-1],'Successful fixture did not retain endpoint and lease')
 return {'success':True,'counters':expected,'report_arrays':report_arrays(row),'heap_free_largest_pairs':heap_pairs(row),'elapsed_us':number(row,'elapsed_us'),'reads':number(row,'reads'),'writes':number(row,'writes'),'terminal_row':row,'held_row':held[-1],'stack_high_water_raw':number(row,'stack_low'),'network_received':'not applicable: local fixture has no network receiver','allocator_order':['limit','live','peak','maximum_allocation','allocations','failures'],'recovery':'paired qualified reconfiguration required; do not retry Y or release lease'}

class Capture:
 def __init__(self,serial,out,max_bytes=16*1024*1024):
  self.serial=serial;self.out=out;self.maximum=max_bytes;self.count=0;self.pending=b'';self.lines=[]
  self.raw=(out/'serial.raw').open('wb');self.events=(out/'capture.jsonl').open('w',encoding='utf-8');self.text=(out/'serial.txt').open('w',encoding='utf-8')
 def event(self,kind,**fields):
  self.events.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),monotonic_ns=time.monotonic_ns(),kind=kind,**fields))+'\n');self.events.flush()
 def send(self,command):
  require(command in ('?','W','Y'),'Unapproved command');self.event('command',ascii=command);require(self.serial.write(command.encode())==1,'Short serial write')
 def read(self):
  b=self.serial.read(4096)
  if not b:return
  self.count+=len(b);require(self.count<=self.maximum,'Capture byte bound exceeded; no retry or cleanup')
  self.raw.write(b);self.raw.flush();self.event('receive',base64=base64.b64encode(b).decode());self.pending+=b
  require(len(self.pending)<=65536 or b'\n'in self.pending,'Unbounded unterminated serial line')
  while b'\n'in self.pending:
   line,self.pending=self.pending.split(b'\n',1);require(len(line)<=65536,'Serial line bound exceeded');line=re.sub(r'\x1b\[[0-9;]*m','',line.decode('utf-8',errors='replace').rstrip('\r'));self.lines.append(line);self.text.write(line+'\n');self.text.flush()
   require(not re.search(r'USB_D24 v=1 p=boot|Guru Meditation|Brownout detector|rst:0x|ESP-ROM:',line),'Reboot/panic observed; no reopen/retry')
 def stage(self,command,parser,seconds):
  start=len(self.lines);self.send(command);deadline=time.monotonic()+seconds
  while time.monotonic()<deadline:
   self.read();rows=self.lines[start:]
   if command in ('W','Y'):
    refusal=[x for x in rows if re.search(r'USB_CU(?:66_HUD|71_LOCAL) result=(heap_budget|busy|allocation)',x)]
    require(not refusal,'Worker refused: '+str(refusal))
   value=parser(rows)
   if value is not None:return value
  raise Refusal('Timed out waiting for '+command+'; device state unknown; no automatic retry/reset/lease release')
 def close(self):
  if self.pending:self.event('unterminated_tail',base64=base64.b64encode(self.pending).decode())
  self.raw.close();self.events.close();self.text.close()

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--port');p.add_argument('--qualification-manifest',type=Path);p.add_argument('--operator-receipt',type=Path);a=p.parse_args(argv)
 if not a.execute:
  print(json.dumps(dict(mode='DRY_PLAN_NO_DEVICE_ACCESS',commands=list(COMMANDS),ELF_sha256=ELF,source_manifest_sha256=SOURCE,required_gates=list(GATES),execution_requires=['--execute','--port','--output(new unique directory)','--qualification-manifest','--operator-receipt'],camera='Use fresh physical Razer Kiyo PnP identity and verify full panel coverage externally; never cached index1 SmartConnect',prohibited=['q/QSPI benchmark','DFU/reset','radio/SD writes','JTAG programming','lease release','automatic retry']),indent=2));return 0
 require(all((a.output,a.port,a.qualification_manifest,a.operator_receipt)),'Explicit output/port/qualification/operator receipt required')
 # All offline gates precede import/open; no serial discovery or implicit default COM port.
 gates=verify_qualification(a.qualification_manifest,a.operator_receipt);a.output.mkdir(parents=True,exist_ok=False)
 import serial
 ser=serial.Serial(port=None,baudrate=115200,timeout=0.1,write_timeout=2);ser.dtr=False;ser.rts=False;ser.port=a.port
 result={'status':'INCOMPLETE','bindings':gates,'physical_SPI':'first fixture pending','no_automatic_recovery':True};cap=None
 try:
  ser.open();cap=Capture(ser,a.output);result['initial_runtime']=cap.stage('?',parse_identity,10)
  before=result['initial_runtime']['memory'];require(int(before['free'])>=170000 and int(before['largest'])>=24576,'Insufficient preflight SRAM for Y; W/Y not issued')
  result['CPU_W']=cap.stage('W',parse_cpu,120)
  result['DY_Y']=cap.stage('Y',parse_local,180)
  result['final_runtime']=cap.stage('?',parse_identity,10)
  require(int(result['final_runtime']['reset']['up_us'])>=int(result['initial_runtime']['reset']['up_us']),'Runtime uptime regressed')
  require(result['DY_Y']['success'],'Local fixture failed; retained state must remain held/quarantined')
  result['status']='PASS_PHYSICAL_FIRST_LOCAL_FIXTURE_NOT_NETWORK_OR_30FPS';return 0
 except Exception as e:
  result.update(status='FAIL_OR_UNKNOWN_NO_AUTOMATIC_RECOVERY',reason=str(e));raise
 finally:
  if cap:cap.close()
  if ser.is_open:ser.close()
  (a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
