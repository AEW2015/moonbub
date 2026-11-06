#!/usr/bin/env python3
"""Bounded V81 wide-fill components; each attempt snapshots exact source bytes."""
from pathlib import Path
import argparse,datetime,hashlib,json,subprocess,time,uuid
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v81'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--case',choices=['reference','memory','all'],default='all');args=p.parse_args()
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
 out=AREA/'component-attempts'/stamp;out.mkdir(parents=True)
 own=[AREA/'prefetch/cu81_reference_prefetch.sv',AREA/'integration/cu81_reference_path.sv',AREA/'integration/tb_reference_path.cpp',AREA/'memory/cu81_memory_system.sv',AREA/'memory/tb_memory_v81.sv',Path(__file__).resolve()]
 frozen=[ROOT/'fpga/experiments/cu66-v74/memory'/s for s in ['cu74_tile_memory.sv','cu74_word_bridge.sv']]+[ROOT/'fpga/experiments/cu66-v72/memory'/s for s in ['cu72_sdram_controller.sv','cu72_sdram_model.sv']]+[ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh']
 pins={str(s.relative_to(ROOT)):sha(s) for s in own+frozen}
 for s in own+frozen:
  q=out/'source'/s.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(s.read_bytes())
 report=dict(schema='cu81-widefill-components-v1',status='FAIL_RETAINED_ATTEMPT',source_sha256=pins,commands=[],cases=[],physical_timing_or_fit_proven=False)
 start=time.monotonic()
 def save():
  report['wall_seconds']=time.monotonic()-start;(out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
 def run(argv,name,timeout=600):
  item=dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=None,timed_out=False);report['commands'].append(item)
  try:
   with (out/name).open('w') as stream:r=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
   item['exit_code']=r.returncode
  except subprocess.TimeoutExpired:item['timed_out']=True
  item['sha256']=sha(out/name);save()
  if item['timed_out'] or item['exit_code']!=0:raise RuntimeError(f'{name} failed; retained evidence in {out}')
  return (out/name).read_text()
 try:
  opts=['verilator','--Wall','-Wno-PINCONNECTEMPTY','-j','1','-DSIMULATION','-I'+str(ROOT/'fpga/experiments/cu66-v70/memory')]
  if args.case in ['all','reference']:
   mdir=f'/build/v81-components-reference-{stamp}'
   run(['docker','exec',CONTAINER,*opts,'--cc','--exe','--build','--top-module','cu81_reference_path','--Mdir',mdir,*map(str,own[:3])],'reference-build.log')
   text=run(['docker','exec',CONTAINER,mdir+'/Vcu81_reference_path'],'reference-run.log',120)
   assert 'REFERENCE_PATH_PASS cases=9' in text and 'FAIL' not in text
   report['cases'].append(dict(case='reference',status='PASS',groups=9,tiles=8100,hidden=294,lookups=7806,physical_model=False));print(text,flush=True)
  if args.case in ['all','memory']:
   for tac in [2,7]:
    mdir=f'/build/v81-components-memory-tac{tac}-{stamp}'
    sources=[own[3],own[4],*frozen[:-1]]
    run(['docker','exec',CONTAINER,*opts,'--binary','--timing','-Wno-BLKSEQ','--top-module','tb_memory_v81',f'-GTAC_NS={tac}.0','--Mdir',mdir,*map(str,sources)],f'memory-tac{tac}-build.log')
    text=run(['docker','exec',CONTAINER,mdir+'/Vtb_memory_v81'],f'memory-tac{tac}-run.log',120)
    assert 'WIDE_MEMORY_V81_PASS' in text and 'FAIL' not in text
    report['cases'].append(dict(case='memory',tac_ns=tac,status='PASS',physical_model=True));print(text,flush=True)
  assert pins=={name:sha(ROOT/name) for name in pins},'sources changed during component attempt'
  report['status']='PASS_WIDEFILL_COMPONENTS';save();(AREA/'component-results.json').write_text(json.dumps(dict(path=str((out/'results.json').relative_to(ROOT)),sha256=sha(out/'results.json'),status=report['status']),indent=2)+'\n')
 except Exception as e:
  report['failure']=repr(e);save();raise
 print(json.dumps(dict(status=report['status'],results_path=str((out/'results.json').relative_to(ROOT)))))
if __name__=='__main__':main()
