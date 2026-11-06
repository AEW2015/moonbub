#!/usr/bin/env python3
"""Four hypothetical memory-service replays of the retained hard source."""
import copy,datetime,gzip,hashlib,importlib.util,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
SOURCE=AREA/'attempts/20261106T142747849264Z-3a489e3e'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m

def main():
 scheduler=load('cu87_probe_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py');audit=load('cu87_probe_audit',ROOT/'scripts/cu66-v87/audit_coupled.py')
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'memory-probe-attempts'/f'{stamp}-{uuid.uuid4().hex[:8]}';out.mkdir(parents=True)
 rows=[];pins={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)),str(ROOT.joinpath('experiments/python-gamebub-v83/scheduler.py').relative_to(ROOT)):sha(ROOT/'experiments/python-gamebub-v83/scheduler.py'),str((ROOT/'scripts/cu66-v87/audit_coupled.py').relative_to(ROOT)):sha(ROOT/'scripts/cu66-v87/audit_coupled.py')}
 for cost in ('low','high'):
  path=SOURCE/f'witness-c3-f50-{cost}_lanes2.json.gz';pins[str(path.relative_to(ROOT))]=sha(path)
  with gzip.open(path,'rt') as f:original=json.load(f)
  for reserved in (False,True):
   work=copy.deepcopy(original['workload']);read=write=0
   for j in work['jobs']:
    if j['resource']=='memory':
     assert 'BL8' in j
     if j['kind'] in ('reference_read','HUD_read'):read+=j['BL8']
     elif j['kind'] in ('canonical_write','HUD_write'):write+=j['BL8']
     else:raise AssertionError(j['kind'])
     j['duration']=j['BL8']*12
   work['assumptions'].update(read_service_cycles_per_BL8=12,write_service_cycles_per_BL8=12)
   windows=dict(period=10000,blocked=[(0,2000)]) if reserved else None
   result=scheduler.schedule(work['jobs'],original['capacities'],windows,retain_timeline=True)
   checked=audit.verify(work,result['timeline'],original['capacities'],windows)
   assert result['resources']['memory']['work_cycles']==(read+write)*12
   witness=out/f'witness-{cost}-reserved{int(reserved)}.json.gz'
   with gzip.open(witness,'wt') as f:json.dump(dict(source_witness=str(path.relative_to(ROOT)),read_service=12,write_service=12,windows=windows,capacities=original['capacities'],workload=work,result=result,audit=checked),f,separators=(',',':'))
   rows.append(dict(mutated_workload_sha256=hashlib.sha256(json.dumps(work,sort_keys=True,separators=(',',':')).encode()).hexdigest(),witness=str(witness.relative_to(ROOT)),witness_sha256=sha(witness),cohort=3,fid=50,cost=cost.upper(),lanes=2,read_service=12,write_service=12,reserved20=reserved,read_BL8=read,write_BL8=write,memory_work_cycles=(read+write)*12,finish_cycles=result['finish_cycles'],model_ms=result['finish_cycles']*1e-5,independent_audit=checked,timeline_sha256=hashlib.sha256(json.dumps(result['timeline'],sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 report=dict(schema='cu66-v87-coupled-memory-witness-sensitivity-v1',status='PASS_FOUR_CONDITIONAL_WITNESS_REPLAYS',unique_sources=1,schedules=4,rows=rows,source_sha256=pins,scope='Only retainedC3f50 with hypothetical12-cycle memory service. No fullcorpus deadline or physical controller qualification. Same operations, metadata admission, dequant and context costs retained.')
 (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
 report['selected_attempt']=str((out/'results.json').relative_to(ROOT))
 report['selected_attempt_sha256']=sha(out/'results.json')
 path=AREA/'memory-probe.json'
 if path.exists():assert json.loads(path.read_text())==report
 else:path.write_text(json.dumps(report,indent=2)+'\n')
 print('COUPLED_MEMORY_WITNESS_PROBE_PASS',[(r['cost'],r['reserved20'],r['model_ms']) for r in rows])
if __name__=='__main__':main()
