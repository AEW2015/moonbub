#!/usr/bin/env python3
"""Separate one-strip early-release schedule experiment; original deadlines retained."""
import hashlib,json,re,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=[H/'tb_service_lookahead_v76.sv',*[R/'fpga/experiments/cu66-v74/memory'/n for n in ('cu74_word_bridge.sv','cu74_memory_system.sv','cu74_tile_memory.sv')],*[R/'fpga/experiments/cu66-v72/memory'/n for n in ('cu72_sdram_controller.sv','cu72_sdram_model.sv')]]
files=src+[H/'tb_service_v76.sv',H/'trace.mem',H/'reference.mem',H/'results.json',Path(__file__).resolve(),R/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh'];pins={str(p.relative_to(R)):sha(p)for p in files};cs=[];runs=[]
def run(argv,name):
 with(H/name).open('w')as f:p=subprocess.run(argv,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 cs.append(dict(argv=argv,log=str((H/name).relative_to(R)),exit_code=p.returncode,sha256=sha(H/name)))
 assert p.returncode==0,(name,p.returncode)
 return(H/name).read_text()
for tac in (2,7):
 mdir='/build/v76-service-lookahead-tac'+str(tac)
 run(['docker','exec','gamebub-cu66-v69-build','verilator','--binary','--timing','--Wall','-Wno-BLKSEQ','--top-module','tb_service_lookahead_v76',f'-GTAC_NS={tac}.0','--Mdir',mdir,'-j','1','-DSIMULATION','-I'+str(R/'fpga/experiments/cu66-v70/memory'),*map(str,src)],f'lookahead-build-tac{tac}.log')
 for route in ((1,0)if tac==2 else(1,)):
  log=run(['docker','exec','gamebub-cu66-v69-build',mdir+'/Vtb_service_lookahead_v76','+TRACE='+str(H/'trace.mem'),'+REF='+str(H/'reference.mem'),f'+ROUTE={route}','+BACKGROUND=1','+ISSUE_GAP=0','+REFBANK=0'],f'lookahead-tac{tac}-route{route}-paced.log')
  assert 'FAIL'not in log and 'FATAL'not in log
  m=re.search(r'^SERVICE_PASS (.+)$',log,re.M);assert m
  row={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',m[1])};rows=[{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}for line in log.splitlines()if line.startswith('SERVICE_STRIP')]
  assert len(rows)==90 and row['compared_words']==280320 and row['bursts']==35040
  start=rows[0]['release_cycle']
  for s in rows:
   assert s['release_cycle']==start+(max(0,s['strip']-1)*147403024)//10000
   assert s['deadline_cycle']==start+((s['strip']+1)*147403024)//10000
  assert sum(s['late_cycles']>0 for s in rows)==row['deadline_misses']
  assert row['drained_w']==row['released_w'] and row['drained_r']==row['released_r']
  row.update(tac_ns=tac,strips_detail=rows,deadline_status='PASS'if row['deadline_misses']==0 else'FAIL',max_service_us=row['max_service_cycles']*.01,lookahead_strips=1)
  runs.append(row);print('LOOKAHEAD_RUN_PASS tac='+str(tac)+' route='+str(route)+' deadline='+row['deadline_status']+' misses='+str(row['deadline_misses']),flush=True)
assert pins=={p:sha(R/p)for p in pins}
d=dict(schema='v76-service-lookahead-v1',status='PASS_FUNCTIONAL_SCHEDULE_REPLAY',scope='Separate one-strip early-release schedule only; current frozen controller/bridge, original deadlines unchanged; no RTLcache/renderer/lease or sustained30fps proof',source_sha256=pins,commands=cs,runs=runs,deadline_ps=147403024,lookahead_strips=1,additional_cache_requirement='Consumer i starts at originaldeadline(i+1)P afterinitialPpreroll; earlyrelease(i-1)P canretain3liveY/chroma generations,requiring29184B structuredcache(3Ycols,3Ccols/plane,4HUDblockcols/rect)andleaseproof; benchmark has no cacheRTL/pixelconsumers',limitations=['35040software-cachemissblocks; exactlysamephysicaladdressorder,consumerbandwidthzero exceptrequest/drain','pacedbackground absolute30fps tileworkload sharedreferencefrontbank0,syntheticstaticprofileIDs not livepacketdecode','onepaneltracecold-start,not steady-state source-switch/cache-invalidation proof','larger prefetch lead requires addedcachememory and ownershipproof, not freeperformance'])
(H/'lookahead-results.json').write_text(json.dumps(d,indent=2)+'\n');print('V76_LOOKAHEAD_FUNCTIONAL_PASS schedule_verdicts_retained=true')
