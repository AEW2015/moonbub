#!/usr/bin/env python3
"""Full native RGB565 through retained reader, actual BL8 bridge/controller and timed pins."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91l-converter'
BRIDGE=ROOT/'fpga/experiments/cu66-v91l-readbridge'
SOURCE=ROOT/'fpga/experiments/cu66-v91k-lines/comparison-attempts/20261106T223415479309Z-7a2603de'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',type=int,action='append',choices=(912701,912702));ap.add_argument('--tac',type=int,action='append',choices=(2,7));a=ap.parse_args();seeds=a.seed or [912701,912702];corners=a.tac or [2,7]
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
 out=AREA/'timed-attempts'/stamp;out.mkdir(parents=True)
 sources=[ROOT/'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv',ROOT/'fpga/experiments/cu66-v91k-lines/canonical_line_reader.sv',ROOT/'fpga/experiments/cu66-v91k-lines/canonical_rgb565_lines.sv',ROOT/'fpga/experiments/cu66-v91l-rowpair/tile_rowpair_reader.sv',AREA/'canonical_rgb565_tiled.sv',BRIDGE/'bl8_read_bridge.sv',ROOT/'fpga/experiments/cu66-v91l-writepipe/controller/moonshine_sdram.sv',ROOT/'fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv',AREA/'canonical_rgb565_timed.sv',AREA/'tb_timed.cpp',Path(__file__).resolve()]
 inputs=[SOURCE/'inputs/canonical_actual.tsv.gz',SOURCE/'inputs/rgb_goldens.tsv.gz',SOURCE/'results.json',BRIDGE/'preload.hex.gz',BRIDGE/'fixtures.json']
 report=dict(schema='cu66-v91l-timed-rgb-converter-v1',status='FAIL',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},inputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},commands=[],modes=[],seeds=seeds,t_ac_ns=corners,
  service='Actual frozen writepipe SDRAM controller + taggedBL8bridge + timed functional SDRAM pin model, 100MHz source,4ns forwarded-clock flight,7.75ns read sampling phase. Native memory directly preloaded before fences, no physical writer/livecodec/sharedtraffic.',actual_converter_rtl_join=True,physical_sdram_controller_join=True,shared_service_complete=False,physical_hardware_tested=False,sustained_hardware_30fps_proven=False,validated_full_frame_decode_under10ms_proven=False)
 start=time.monotonic();temporary=[]
 def command(argv,name,timeout):
  entry=dict(argv=argv,log=name,exit_code=None);report['commands'].append(entry)
  with (out/name).open('w') as f:r=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  entry['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {out/name}')
 try:
  for p in sources:
   target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  for p in inputs:
   target=out/'inputs'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  fixtures=json.loads((BRIDGE/'fixtures.json').read_text());assert fixtures['status']=='PASS_PINNED_NATIVE_PRELOAD_AND_LOGICAL_LINES'
  assert fixtures['artifacts']['preload.hex.gz']['gzip_sha256']==sha(BRIDGE/'preload.hex.gz')
  report['input_expansions']=[]
  for name,packed_name in (('canonical_actual.tsv','canonical_actual.tsv.gz'),('rgb_goldens.tsv','rgb_goldens.tsv.gz'),('preload.hex','preload.hex.gz')):
   packed=out/'inputs'/packed_name;plain=out/name;plain.write_bytes(gzip.decompress(packed.read_bytes()));temporary.append(plain);report['input_expansions'].append(dict(path=plain.name,compressed_path=str(packed.relative_to(out)),compressed_sha256=sha(packed),raw_sha256=sha(plain)))
  golden={}
  for line in (out/'rgb_goldens.tsv').read_text().splitlines():
   name,hx=line.split('\t')
   if name in ('actual_001','actual_006'):golden[name]=hashlib.sha256(bytes.fromhex(hx)).hexdigest()
  report['rgb_goldens']=golden
  command(['docker','exec',CONTAINER,'verilator','--version'],'tool-version.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler-version.log',30)
  for tac in corners:
   build='/build/v91l-timed-converter-'+stamp+'-tac'+str(tac);snap=lambda p:str(out/'sources'/p.relative_to(ROOT))
   command(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','--timing','--assert','-Wall','--timescale','1ns/1ps','-DSIMULATION','-j','2','--top-module','canonical_rgb565_timed','-GT_AC_NS='+str(tac)+'.0',"-GRETAIN_ROWS=1'b1",'--Mdir',build,'-CFLAGS','-std=c++20 -O2 -Wall -Wextra -Werror',*[snap(p) for p in sources[:-1]]],'compile-tac'+str(tac)+'.log',600)
   for seed in seeds:
    directory=out/('retained-'+str(seed)+'-tac'+str(tac));directory.mkdir();mode=dict(seed=seed,retain=1,t_ac_ns=tac,status='FAIL',event_log=str(directory.relative_to(out)/'events.jsonl.gz'),pin_log='pins-'+str(seed)+'-tac'+str(tac)+'.jsonl.gz');report['modes'].append(mode)
    command(['docker','exec',CONTAINER,build+'/Vcanonical_rgb565_timed',str(out/'canonical_actual.tsv'),str(out/'rgb_goldens.tsv'),str(directory/'events.jsonl'),str(directory),str(seed),'1','+PRELOAD='+str(out/'preload.hex')],'pins-'+str(seed)+'-tac'+str(tac)+'.jsonl',1200)
    verdict=[];frames=[];checks=[]
    with (directory/'events.jsonl').open() as f:
     for line in f:
      event=json.loads(line)
      if event['type']=='verdict':verdict.append(event)
      elif event['type']=='frame':frames.append(event)
      elif event['type']=='check':assert event['status']=='PASS';checks.append(event['name'])
    assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS' and verdict[0]['seed']==seed and verdict[0]['retain']==1
    assert verdict[0]['checks']==len(checks)==7 and len(frames)==2
    for frame in frames:
     output=directory/frame['output'];frame['output_sha256']=sha(output);assert output.stat().st_size==frame['bytes']==691200 and frame['output_sha256']==golden[frame['name']]
     assert frame['pixels']==345600 and frame['logical_reads']==frame['physical_reads']==32400
    mode.update(status='PASS_ACTUAL_RGB565_THROUGH_TIMED_SDRAM',verdict=verdict[0],frames=frames,checks=checks)
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources};assert report['inputs_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in inputs}
  report['status']='PASS_NATIVE_RGB565_ACTUAL_TIMED_SDRAM'
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  for p in temporary:
   if p.exists():p.unlink()
  report['compressed_artifacts']={}
  for path in [*sorted(out.glob('*/events.jsonl')),*sorted(out.glob('pins-*.jsonl'))]:
   raw=path.read_bytes();packed=path.with_suffix('.jsonl.gz');packed.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(packed.read_bytes())==raw;report['compressed_artifacts'][str(path.relative_to(out))]=dict(path=str(packed.relative_to(out)),gzip_sha256=sha(packed),raw_sha256=hashlib.sha256(raw).hexdigest(),rows=len(raw.splitlines()));path.unlink()
  report['wall_seconds']=time.monotonic()-start;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'timed-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('TIMED_CONVERTER_JOIN',report['status'],out,flush=True)
if __name__=='__main__':main()
