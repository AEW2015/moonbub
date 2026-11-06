#!/usr/bin/env python3
"""Compare original and strict controller with one identical Icarus pin bench."""
import datetime,hashlib,json,shutil,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=AREA/'equivalence-attempts'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 sources=[ROOT/'fpga/rtl/moonshine_sdram.sv',AREA/'controller/moonshine_sdram.sv',AREA/'row_to_sdram.sv',AREA/'sdram_pin_model.sv',AREA/'tb_controller.sv',Path(__file__).resolve()]
 report=dict(schema='cu66-v91l-controller-derivative-equivalence-v1',status='FAIL',seed=912301,t_ac_ns=2,scope='Same pin-level unit bench compares frozen original vs four-edit strict derivative under Icarus; no native replay or hardware equivalence claim.',source_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},commands=[])
 def cmd(argv,log,timeout):
  entry=dict(argv=argv,log=log,exit_code=None);report['commands'].append(entry)
  with (out/log).open('w') as f:r=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=timeout,cwd=ROOT)
  entry['exit_code']=r.returncode
  if r.returncode:raise RuntimeError(f'command exit {r.returncode}: {log}')
 try:
  for p in sources:
   dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  cmd(['iverilog','-V'],'iverilog-version.log',30)
  snapshots=lambda p:str(out/'sources'/p.relative_to(ROOT))
  observed={}
  for name,controller in (('original',sources[0]),('strict',sources[1])):
   executable=out/(name+'.vvp')
   cmd(['iverilog','-g2012','-Wall','-DSIMULATION','-s','tb_controller','-Ptb_controller.T_AC_NS=2.0','-o',str(executable),snapshots(controller),*[snapshots(p) for p in sources[2:5]]],'compile-'+name+'.log',300)
   cmd(['vvp',str(executable),'+SEED=912301'],'simulation-'+name+'.jsonl',300)
   observed[name]=[json.loads(x) for x in (out/('simulation-'+name+'.jsonl')).read_text().splitlines() if x.startswith('{')]
   verdict=[x for x in observed[name] if x['type']=='verdict'];assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS'
   executable.unlink()
  assert observed['original']==observed['strict'],'observable pin/request/response/check trace differs'
  assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in sources}
  report.update(status='PASS_ORIGINAL_STRICT_OBSERVABLE_TRACE_IDENTITY',event_count=len(observed['original']),verdict=observed['original'][-1])
 except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
  (out/'results.json').write_text(json.dumps(report,indent=2)+'\n');(AREA/'equivalence-results.json').write_text(json.dumps(dict(report,selected_report=str((out/'results.json').relative_to(ROOT))),indent=2)+'\n');print('CONTROLLER_EQUIVALENCE',report['status'],out,flush=True)
if __name__=='__main__':main()
