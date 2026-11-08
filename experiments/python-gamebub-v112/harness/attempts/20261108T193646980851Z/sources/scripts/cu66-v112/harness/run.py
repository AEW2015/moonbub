#!/usr/bin/env python3
"""Bounded deterministic source-adapter/JPEG RTL proof; never guest-time proof."""
import datetime, hashlib, json, re, shutil, struct, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v112/harness'
OLD=ROOT/'fpga/experiments/throughput30/burst'
GUEST=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/live-final-positive')
JPEG=Path('/home/lori/gamebub-tools/esp-emu-study-0510/lcd-bypass/msv1-bridge-multi/src/0000.jpg')
PRIOR=ROOT/'experiments/python-gamebub-v111/harness/attempts/20261108T182424178254Z/adapter-events.jsonl'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def events(trace):
 data=Path(trace).read_bytes();pos=0;payload=[]
 while pos<len(data):
  n=int.from_bytes(data[pos:pos+2],'big');pos+=2
  assert 40<=n<=1064 and pos+n<=len(data)
  payload.append(data[pos+40:pos+n]);pos+=n
 assert len(payload)==26
 body=b''.join(payload);assert len(body)==26159
 result=[b'B'+struct.pack('>IIII',0,0,len(body),0xeceeb9c5)]
 offset=0
 for p in payload:
  result.append(b'D'+struct.pack('>IIIH',len(result),0,offset,len(p))+p);offset+=len(p)
 result.append(b'C'+struct.pack('>II',len(result),0))
 prior=[json.loads(x) for x in PRIOR.read_text().splitlines()]
 assert len(prior)==len(result)==28
 for event,audit in zip(result,prior):assert hashlib.sha256(event).hexdigest()==audit['sha256']
 return result

def schedule(path,base,frames=10,abort=False,corrupt=False,oversize=False):
 rows=[];seq=0
 def add(t,event,frame):
  nonlocal seq
  item=event[:1]+struct.pack('>II',seq,frame)+event[9:];seq+=1
  rows.append((t,item))
 if abort:
  add(25_000_000_000,base[0],99);add(25_010_000_000,base[1],99);add(25_020_000_000,b'A'+b'\0'*8,99)
 for frame in range(frames):
  start=(70_000_000_000 if abort else 25_000_000_000)+frame*40_000_000_000
  for i,event in enumerate(base):
   if corrupt and i==5:event=event[:30]+bytes([event[30]^1])+event[31:]
   add(start+i*10_000_000,event,frame)
 with path.open('w') as f:
  for t,e in rows:f.write(f'{t} {1040 if oversize else len(e)} {e.hex()}\n')
 return [dict(offered_ps=t,sequence=int.from_bytes(e[1:5],'big'),frame=int.from_bytes(e[5:9],'big'),kind=chr(e[0]),length=len(e),sha256=hashlib.sha256(e).hexdigest()) for t,e in rows]

def audit(path,offered):
 records=[json.loads(x) for x in path.read_text().splitlines()]
 assert len(records)==2*len(offered)
 last=0;backpressure=0
 for i,e in enumerate(offered):
  accept,done=records[2*i:2*i+2]
  assert accept['event']=='source_accept' and done['event']=='rtl_service_complete'
  assert accept['sequence']==done['sequence']==i
  assert accept['clock']==done['clock']=='rtl_ps'
  assert last<=accept['time_ps']<=done['time_ps'] and accept['time_ps']>=e['offered_ps']
  assert accept['resident_bytes']==e['length']<=accept['capacity_bytes']==1039
  assert done['status']==0 and done['highwater_bytes']<=1039
  assert done['service_ps']==done['time_ps']-accept['time_ps']
  assert done['source_backpressure_ps']==accept['time_ps']-accept['offered_ps']
  assert accept['offered_ps']==e['offered_ps']
  last=done['time_ps'];backpressure=max(backpressure,done['source_backpressure_ps'])
 return dict(events=len(offered),max_source_backpressure_ps=backpressure,last_time_ps=last,trace_sha256=sha(path))

def main():
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=AREA/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v112-sync-adapter-'+stamp);build.mkdir()
 snapshots=out/'sources';pins={}
 legacy=(OLD/'live-rtl-bridge/results/rtl-source-sha256-current.txt').read_text().splitlines()
 for line in legacy:
  want,name=line.split(maxsplit=1);assert sha(ROOT/name)==want; pins[name]=want
 selected=list((ROOT/'fpga/experiments/cu66-v112-harness').glob('*'))+list((ROOT/'scripts/cu66-v112/harness').glob('*.py'))
 selected += list((ROOT/'fpga/vendor/core_jpeg/c_model').glob('*'))+[ROOT/'host/evidence/jpeg-c-model-fixed-color-main.cpp',ROOT/'host/evidence/jpeg-c-model-fixed-color-source.cpp',PRIOR]
 for p in selected:
  if p.is_file():pins[str(p.relative_to(ROOT))]=sha(p)
 for n in pins:
  target=snapshots/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,target)
 assert sha(GUEST/'fixture.trace')=='a8ff3d87e165247637d97fd2b56414f54943337ff7cb11102aa73cba26f26e05'
 assert sha(JPEG)=='8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de'
 shutil.copy2(GUEST/'fixture.trace',out/'guest-accepted-fixture.trace');shutil.copy2(JPEG,build/'fixture.jpg')
 base=events(out/'guest-accepted-fixture.trace')
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','gamebub-cu66-v69-tools:20261105'],text=True).strip()
 receipt=dict(schema='v112-clocked-jpeg-source-adapter-v1',status='RUNNING',source_sha256=pins,image_content_id=image,external_build=str(build),commands=[],tests={},guest_event_bytes_reconstructed_and_prior_hash_matched=True,actual_guest_run=False,guest_cpu_time_fidelity='none: source replay; guest not advanced',actual_GP_SPI_DMA=False,full_application=False,sunshine_executed=False,shared_emulator_RTL_time=False,adapter_RTL_common_time='integer picoseconds from Verilator event scheduler',hardware_contact=False,system_FPS_qualified=False,fixture_distinct_frames=1,repeated_fixture_presentations=10,original_guest_event_sha256=[hashlib.sha256(e).hexdigest() for e in base],replay_transform='Overwrite event bytes [1:5] with monotonically increasing big-endian sequence and [5:9] with big-endian frame id; preserve all other bytes, except corruption control flips bit 0 of DATA event 5 byte 30; abort control adds B/D/A prefix frame 99',guest_fixture_trace_sha256=sha(out/'guest-accepted-fixture.trace'),jpeg_fixture_sha256=sha(JPEG))
 def cmd(argv,log,cap=900,env=None):
  name='v112-harness-'+stamp.lower()+'-'+str(len(receipt['commands']))
  command=['docker','run','--rm','--init','--name',name,'--cpus','2','--memory','8g','--memory-swap','8g','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={snapshots},dst={snapshots},readonly','--mount',f'type=bind,src={build},dst={build}','-w',str(build)]
  for k,v in (env or {}).items():command+=['-e',k+'='+str(v)]
  command += [image,'timeout','--kill-after=5s',str(cap)+'s',*map(str,argv)]
  info=dict(argv=command,wall_timeout_seconds=cap);receipt['commands'].append(info);write(out/'receipt.json',receipt)
  started=time.monotonic()
  with (out/log).open('w') as f:result=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=cap+30)
  info.update(exit_code=result.returncode,wall_seconds=time.monotonic()-started);write(out/'receipt.json',receipt)
  return result.returncode
 try:
  assert cmd(['verilator','--version'],'verilator-version.log',30)==0
  assert cmd(['bash',snapshots/'fpga/experiments/cu66-v112-harness/build.sh'],'compile.log',900,{'BUILD_DIR':build/'rtl'})==0
  binary=build/'rtl/obj/Vtb_sync_adapter';receipt['rtl_binary_sha256']=sha(binary)
  assert cmd(['g++','-std=c++17','-O2','-I'+str(snapshots/'fpga/vendor/core_jpeg/c_model'),snapshots/'host/evidence/jpeg-c-model-fixed-color-main.cpp','-o',build/'cmodel'],'cmodel-compile.log',120)==0
  assert cmd([build/'cmodel',build/'fixture.jpg',build/'reference.ppm'],'cmodel.log',60)==0
  magic,dimensions,maximum,rgb=(build/'reference.ppm').read_bytes().split(b'\n',3)
  assert magic==b'P6' and dimensions==b'720 480' and maximum==b'255' and len(rgb)==345600*3
  with (build/'oracle.hex').open('w') as f:
   for x in range(720):
    for y in range(480):
     r,g,b=rgb[3*(y*720+x):3*(y*720+x)+3];f.write(f'{((r>>3)<<11)|((g>>2)<<5)|(b>>3):04x}\n')
  receipt['oracle']=dict(kind='fresh compiled fixed color related C model; not independent codec conformance',ppm_sha256=sha(build/'reference.ppm'),rgb565_sha256=sha(build/'oracle.hex'))
  tests=[('ten-repeated-frames',10,False,False,False),('abort-reset-retry',1,True,False,False),('corruption',1,False,True,False),('oversize-hidden-buffer',1,False,False,True)]
  for test,frames,abort,corrupt,oversize in tests:
   w=build/test;w.mkdir();offered=schedule(w/'schedule.txt',base,frames,abort,corrupt,oversize);write(out/(test+'-schedule.json'),offered)
   rc=cmd([binary,f'+ORACLE={build}/oracle.hex',f'+FRAMES={frames}',f'+RESET_TEST={int(abort)}',f'+CORRUPT_TEST={int(corrupt)}'],test+'.log',900,{'V112_SCHEDULE':w/'schedule.txt','V112_TRACE':w/'trace.jsonl'})
   shutil.copy2(w/'schedule.txt',out/(test+'-schedule.txt'))
   if (w/'trace.jsonl').exists():shutil.copy2(w/'trace.jsonl',out/(test+'-trace.jsonl'))
   log=(out/(test+'.log')).read_text()
   if oversize:
    assert rc!=0 and 'source adapter read error -14' in log
    result=dict(status='PASS_EXPECTED_REJECTION',rejected_before_bounded_body_write=True)
   else:
    assert rc==0
    assert ('TEST_PASS_CORRUPTION_REJECTION' if corrupt else f'TEST_PASS_SYNC_ADAPTER frames={frames}') in log
    result=dict(status='PASS',**audit(out/(test+'-trace.jsonl'),offered))
    if not corrupt:
     assert result['max_source_backpressure_ps']>0
     present=re.findall(r'BRIDGE_PRESENT .*',log);assert len(present)==frames
     result['presentations']=present
   receipt['tests'][test]=result;write(out/'receipt.json',receipt)
  assert all(sha(ROOT/n)==h and sha(snapshots/n)==h for n,h in pins.items())
  receipt.update(status='PASS_EXPLICIT_SOURCE_ADAPTER_JPEG_RTL',compile_warning_count=(out/'compile.log').read_text().count('%Warning-'),source_unchanged=True)
 except Exception as e:
  receipt.update(status='FAIL',error=repr(e));raise
 finally:
  receipt['artifact_sha256']={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='receipt.json'}
  write(out/'receipt.json',receipt);write(AREA/'results.json',dict(schema=receipt['schema'],status=receipt['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),selected_sha256=sha(out/'receipt.json'),actual_guest_run=False,actual_GP_SPI_DMA=False,shared_emulator_RTL_time=False,system_FPS_qualified=False))
  print(receipt['status'],out)
if __name__=='__main__':main()
