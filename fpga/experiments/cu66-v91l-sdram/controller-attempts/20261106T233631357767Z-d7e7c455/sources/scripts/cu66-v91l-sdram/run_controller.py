#!/usr/bin/env python3
"""Retain real SDRAM-controller row-bridge and pin-model simulation evidence."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'fpga/experiments/cu66-v91l-sdram';MODEL=ROOT/'experiments/python-gamebub-v91l-sdram';CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seed',type=int,choices=(912301,912302),default=912301);ap.add_argument('--unit-only',action='store_true');a=ap.parse_args()
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8];out=AREA/'controller-attempts'/stamp;out.mkdir(parents=True)
 sv=[AREA/'controller/moonshine_sdram.sv',AREA/'row_to_sdram.sv',AREA/'sdram_pin_model.sv',AREA/'tb_controller.sv']
 sources=sv+[AREA/'generate_controller.py',AREA/'controller-derivation.json',ROOT/'fpga/rtl/moonshine_sdram.sv',Path(__file__).resolve()]
 inputs=[] if a.unit_only else [MODEL/'vectors/native-rows.hex.gz',MODEL/'traffic-results.json']
 report=dict(schema='cu66-v91l-real-sdram-bridge-v1',status='FAIL',seed=a.seed,source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],modes=[],native_replay=not a.unit_only,byte_rmw_supported=False,physical_hardware_tested=False,full_live_codec_join=False,hardware_distinct_30fps_proven=False,full_frame_decode_under10ms_proven=False,scope='Actual single-word SDRAM controller strict-width derivative, row-to-four-word bridge, 4ns forwarded-clock flight and tAC2/7ns functional pin model. Optional native candidate request replay; not live decoder integration, physical timing signoff or shared traffic qualification.')
 start=time.monotonic();plain=None
 def cmd(argv,log,timeout):
  entry=dict(argv=argv,log=log,exit_code=None);report['commands'].append(entry)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,cwd=ROOT)
  entry['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {out/log}')
 try:
  for p in sources:
   dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  for p in inputs:
   dest=out/'inputs'/p.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  if not a.unit_only:
   packed=out/'inputs/native-rows.hex.gz';plain=out/'native-rows.hex';plain.write_bytes(gzip.decompress(packed.read_bytes()));assert len(plain.read_bytes().splitlines())==140160
   report['native_expansion']=dict(compressed_sha256=sha(packed),raw_sha256=sha(plain),rows=140160)
  cmd(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);cmd(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  snapshot=lambda p:str(out/'sources'/p.relative_to(ROOT))
  for tac in (2,7):
   mode=dict(name='tac'+str(tac),t_ac_ns=tac,status='FAIL',native_rows=140160 if plain and tac==2 else 0);report['modes'].append(mode);build='/build/v91l-sdram-'+stamp+'-tac'+str(tac)
   cmd(['docker','exec',CONTAINER,'verilator','--binary','--timing','--assert','-Wall','-DSIMULATION','-j','2','--top-module','tb_controller','-GT_AC_NS='+str(tac)+'.0','--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*[snapshot(p) for p in sv]],'compile-tac'+str(tac)+'.log',600)
   argv=['docker','exec',CONTAINER,build+'/Vtb_controller','+SEED='+str(a.seed)]
   if mode['native_rows']:argv+=['+NATIVE_ROWS='+str(plain),'+NATIVE_COUNT=140160']
   name='simulation-tac'+str(tac)+'.jsonl';cmd(argv,name,1200)
   rows=[json.loads(x) for x in (out/name).read_text().splitlines() if x.startswith('{')];verdict=[x for x in rows if x['type']=='verdict'];assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS'
   assert verdict[0]['seed']==a.seed and verdict[0]['t_ac_ns']==tac and verdict[0]['native_rows']==mode['native_rows']
   mode.update(status='PASS_REAL_CONTROLLER_AND_ROW_BRIDGE',verdict=verdict[0],checks=[x['name'] for x in rows if x['type']=='check'])
   assert mode['verdict']['checks']==len(mode['checks'])
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['status']='PASS_REAL_CONTROLLER_ROW_WRITES_AND_READ_PROBES'
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  if plain and plain.exists():plain.unlink()
  report['compressed_artifacts']={}
  for p in out.glob('simulation-*.jsonl'):
   raw=p.read_bytes();target=p.with_suffix('.jsonl.gz');target.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(target.read_bytes())==raw;report['compressed_artifacts'][p.name]=dict(path=target.name,gzip_sha256=sha(target),raw_sha256=hashlib.sha256(raw).hexdigest(),rows=sum(1 for x in raw.splitlines() if x.startswith(b'{')));p.unlink()
  report['wall_seconds']=time.monotonic()-start;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'controller-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('SDRAM_CONTROLLER',report['status'],out,flush=True)
if __name__=='__main__':main()
