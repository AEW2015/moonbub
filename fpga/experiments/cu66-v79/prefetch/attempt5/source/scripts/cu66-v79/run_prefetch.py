#!/usr/bin/env python3
"""Qualify the isolated two-slot RTL prefetch prototype with a simple backend."""
import hashlib,json,re,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v79/prefetch'
CONTAINER='gamebub-cu66-v69-build'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 attempt=1
 while (AREA/f'attempt{attempt}').exists():attempt+=1
 out=AREA/f'attempt{attempt}';out.mkdir()
 paths=[AREA/'cu79_reference_prefetch.sv',AREA/'tb_prefetch.cpp',Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh']
 pins={str(p.relative_to(ROOT)):sha(p)for p in paths};commands=[];started=time.monotonic()
 for relative,digest in pins.items():
  saved=out/'source'/relative;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes((ROOT/relative).read_bytes());assert sha(saved)==digest
 report=dict(schema='cu79-reference-prefetch-prototype-v1',status='FAIL_STANDALONE',source_sha256=pins,commands=commands,attempt=attempt)
 def run(argv,name,timeout):
  begin=time.monotonic();code=None;timed_out=False
  try:
   with(out/name).open('w')as stream:r=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
   code=r.returncode
  except subprocess.TimeoutExpired:timed_out=True
  commands.append(dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=code,timed_out=timed_out,timeout_seconds=timeout,wall_seconds=time.monotonic()-begin,sha256=sha(out/name)))
  if timed_out or code:raise RuntimeError(f'{name}: exit={code} timed_out={timed_out}; retained attempt{attempt}')
  return(out/name).read_text()
 try:
  version=run(['docker','exec',CONTAINER,'verilator','--version'],'version.log',30).strip()
  mdir='/build/v79-prefetch'
  run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1','--Wall','--top-module','cu79_reference_prefetch','--Mdir',mdir,'-CFLAGS','-O2 -std=c++17','-I'+str(ROOT/'fpga/experiments/cu66-v70/memory'),str(AREA/'cu79_reference_prefetch.sv'),str(AREA/'tb_prefetch.cpp')],'build.log',300)
  binary_sha=run(['docker','exec',CONTAINER,'sha256sum',mdir+'/Vcu79_reference_prefetch'],'binary.log',30).split()[0]
  log=run(['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=5s','60s',mdir+'/Vcu79_reference_prefetch'],'run.log',70)
  terminal=re.findall(r'^PREFETCH_PASS (.+)$',log,re.M);assert len(terminal)==1 and 'FAIL'not in log
  fields=lambda line:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
  summary=fields(terminal[0]);cases=[line for line in log.splitlines()if line.startswith('PREFETCH_CASE_PASS ')]
  assert len(cases)==summary['cases']==9
  assert summary['hidden_replay_tiles']==8100 and summary['full_replay_tiles']==8100 and summary['read_commands']==32400 and summary['read_beats']==259200
  assert summary['physical_sdram_model']==summary['system_integration']==summary['speedup_proven']==0
  assert pins=={p:sha(ROOT/p)for p in pins},'prefetch sources changed during qualification'
  report.update(status='PASS_STANDALONE_LOGIC_SIMPLE_BACKEND',summary=summary,cases=cases,simulator=version,binary_sha256=binary_sha,resources=dict(reference_slots=2,reference_payload_bits=1024,logical_reference_bytes=128,slot_identity_control_bits=184,candidate_staging_bytes=0,physical_read_outstanding_limit=1),limitations=['Standalone RTL and deterministic simple address-pattern backend only; no actual SDRAM model/controller, decoder, HUD or display integration.','All8100 references are prefetched; no qmap-directed traffic savings.','Caller authenticates candidate completion and translates candidate bank to retirement reference bank; no write_done shim implemented.','Reset requires a joint backend reset; abort instead drains8 actually accepted beats. Missing beats retain ownership until delivery or joint reset.','No latency reduction, sustained source FPS, target Fmax/fit/CDC or hardware proof.'])
 except Exception as error:
  report['failure']=str(error)
  raise
 finally:
  report['wall_seconds']=time.monotonic()-started
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
  (AREA/'results.json').write_text(json.dumps(report,indent=2)+'\n')
 print(f'V79_PREFETCH_PASS cases=9 full_replay_tiles=8100 wall_seconds={report["wall_seconds"]:.3f}')
if __name__=='__main__':main()
