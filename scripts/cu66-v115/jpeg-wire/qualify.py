#!/usr/bin/env python3
"""Strict bounded actual pin-to-JPEG RTL experiment; requires Root heavy grant."""
import argparse,datetime,hashlib,importlib.util,json,pathlib,shutil,subprocess,time,sys
sys.dont_write_bytecode=True
R=pathlib.Path(__file__).resolve().parents[3];A=R/'experiments/python-gamebub-v115/jpeg-wire';S=R/'fpga/experiments/cu66-v115-jpeg-wire'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args()
 spec=importlib.util.spec_from_file_location('jpeg_prepare',pathlib.Path(__file__).with_name('prepare.py'));prep=importlib.util.module_from_spec(spec);spec.loader.exec_module(prep);contract,sources=prep.prepare()
 if not args.run:print('PREPARED_NOT_RUN');return
 spec=importlib.util.spec_from_file_location('bounded_resources',R/'scripts/cu66-v114/optimized_spatial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=pathlib.Path('/home/lori/gamebub-build/cu66-v69')/('v115-jpeg-wire-'+stamp);build.mkdir();mapped='/build/'+build.name
 raw=dict(schema='v115-real-qspi-cdc-guarded-jpeg-v1',status='FAIL',actual_RTL_run=False,backend='Verilator',image_id=m.IMAGE,source_sha256=contract['source_sha256'],rtl_source_order=contract['rtl_source_order'],commands=[],runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,contract=contract)
 started=time.monotonic()
 def command(argv,name,cap):
  gate=m.memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v115-jpeg-wire-'+stamp.lower()+'-'+str(len(raw['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,m.IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  c=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);raw['commands'].append(c);t=time.monotonic()
  with(out/name).open('w')as f:
   p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT);high=0
   while p.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-t,**m.memory());raw['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  for rel,digest in raw['source_sha256'].items():
   p=R/rel;assert sha(p)==digest;q=out/'sources'/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  snap=lambda p:str(out/'sources'/p.relative_to(R))
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017','--top-module','jpeg_wire','--Mdir',mapped+'/obj','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror',snap(S/'baseline-lint.vlt'),*[snap(p)for p in sources],snap(S/'tb_jpeg_wire.cpp')],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();raw['binary_sha256']=sha(build/'obj/Vjpeg_wire')
  for phase in [0,1]:
   name='phase-'+str(phase)+'.jsonl';command([mapped+'/obj/Vjpeg_wire',snap(R/'host/fixtures/pattern-msv1-packets.bin'),snap(A/'golden-rgb565.bin'),str(phase)],name,300)
   rows=[json.loads(x)for x in(out/name).read_text().splitlines()];verdict=[x for x in rows if x.get('type')=='verdict'];assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['actual_endpoint_CDC_JPEG'] and verdict[0]['good_frames']==2 and verdict[0]['verified_pixels']==691200 and verdict[0]['bad_crc']==verdict[0]['midreceive_reset_retry']==1
   assert len([x for x in rows if x.get('type')=='frame'and x['status']=='PASS'])==2;raw['runs'].append(dict(phase=phase,**verdict[0]))
  assert raw['source_sha256']=={rel:sha(R/rel)for rel in raw['source_sha256']};raw.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:raw['error']=repr(e);raise
 finally:
  raw['wall_seconds']=time.monotonic()-started;raw['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};save(out/'receipt.json',raw);save(A/'results.json',dict(status=raw['status'],path=str((out/'receipt.json').relative_to(R)),sha256=sha(out/'receipt.json')));print('V115_JPEG_WIRE',raw['status'],out,flush=True)
if __name__=='__main__':main()
