"""Derive separate functional/cadence verdicts from retained producer records."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
d=a.run.resolve();o=a.output.resolve();assert not o.exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=json.loads((d/'result.json').read_text());freeze=json.loads((d/'source-freeze.json').read_text());execution=json.loads((d/'execution.json').read_text())
assert result['status']=='PASS_FUNCTIONAL_KEY_P_CANONICAL_HUD_RGB_READBACK'
assert all(e['returncode']==0 for e in execution)
assert result['source_freeze_sha256']==sha(d/'source-freeze.json')
for name,h in freeze.items():
 f=d/'inputs'/name
 if f.exists():assert sha(f)==h,name
log=(d/'frames.log').read_text();assert 'FAIL'not in log
parse=lambda text:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',text)}
rows=[parse(x)for x in log.splitlines()if x.startswith('SYSTEM_FRAME_PASS')]
last=[parse(x)for x in log.splitlines()if x.startswith('SYSTEM_PASS')];assert len(last)==1
summary=last[0];assert len(rows)==result['frames']==summary['complete_frames'] and len(rows)>=2
assert rows[0]['key']==1 and rows[1]['key']==0 and rows[1]['processor_commit_calls']>=2
assert summary['canonical_bytes_per_frame']==518400 and summary['RGB_words_per_frame']==384000 and summary['HUD_functional_readback_words_per_frame']==21120
control=(d/'control.log').read_text();assert 'SYSTEM_CONTROL_PASS'in control and 'FAIL'not in control
for row in rows:
 row['modeled_transaction_ms_at100MHz']=row['cycles']/100000
 row['modeled_painter_ms_at100MHz']=row['painter_cycles']/100000
o.parent.mkdir(parents=True,exist_ok=True)
o.write_text(json.dumps({'functional':'PASS_ACTUAL_CONTROLLER_KEY_P_FULL_READBACK_AND_COMMIT_RETRY','cadence':'FAIL_UNDERRUNS'if summary['total_underruns']else'NOT_QUALIFIED_SHORT_REPLAY','hardware':False,'target_fit_or_clock':False,'frames':rows,'summary':summary,'producer_bindings':{n:sha(d/n)for n in ['source-freeze.json','execution.json','result.json','control.log','frames.log','simulation-scope.json']},'limits':['Twochronologicalframes,not30fpscampaign','C++HUDCPUtimeoutsideHDL,notESP32endpoint','RGBscalarwritesremainmaskedBL8','Model1psmonitorcompatibilityseparatelydisclosed','Wholeblacklinesarefailedcontent,notcompletecleanpresentations']},indent=2)+'\n')
print('FUNCTIONAL_PASS CADENCE_'+('FAIL_UNDERRUNS'if summary['total_underruns']else'NOT_QUALIFIED'))
