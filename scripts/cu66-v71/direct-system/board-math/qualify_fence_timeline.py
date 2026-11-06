"""Reconcile observation-only frame/idle records against both frozen core runs."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[4];root=r/'fpga/experiments/cu66-v71/direct-system';d=root/'syncsafe-math-v002';out=d/'qualification-fence-observation-v001.json';assert not out.exists();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();rows={};proofs={};vals=lambda x:{k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',x)}
for name,folder,parent in [('prior','old-fence-three01',root/'board-math-v001/evidence/math-group-three01'),('syncsafe','new-fence-three01',d/'evidence/syncsafe-three01')]:
 p=d/'evidence'/folder;assert json.loads((p/'result.json').read_text())['frames']==3
 for n,h in json.loads((p/'source-freeze.json').read_text()).items():assert sha(r/n)==h,n
 lines=(p/'frames.log').read_text().splitlines();filtered=[x for x in lines if not x.startswith(('DY71_IDLE_FENCE','DY71_FRAME_FENCE','DY71_FENCE_SUMMARY'))];assert filtered==(parent/'frames.log').read_text().splitlines(),'Observer perturbed DUT result'
 rows[name]={'frame_pulses':[vals(x)for x in lines if x.startswith('DY71_FRAME_FENCE')],'pending_idle_changes':[vals(x)for x in lines if x.startswith('DY71_IDLE_FENCE')],'summary':vals(next(x for x in lines if x.startswith('DY71_FENCE_SUMMARY')))}
 for f in [p/'result.json',p/'source-freeze.json',p/'frames.log',p/'execution.json',p/'tb.cpp',parent/'frames.log']:proofs[f.relative_to(r).as_posix()]=sha(f)
a,b=rows['prior'],rows['syncsafe'];assert len(a['frame_pulses'])==len(b['frame_pulses'])==9
deltas=[y['cycle']-x['cycle']for x,y in zip(a['frame_pulses'],b['frame_pulses'])];assert deltas==[4]*9
examples=[]
for x in a['pending_idle_changes']:
 choices=[y for y in b['pending_idle_changes']if all(y[k]==x[k]for k in ['idle','pending','active_generation','front_generation'])and abs(y['cycle']-x['cycle'])<=4]
 if choices:
  y=min(choices,key=lambda e:abs(e['cycle']-x['cycle']));examples.append({'prior':x,'syncsafe':y,'delta_clocks':y['cycle']-x['cycle']})
proofs[Path(__file__).resolve().relative_to(r).as_posix()]=sha(Path(__file__).resolve())
out.write_text(json.dumps({'status':'PASS_NONINVASIVE_NATIVE_FRAME_AND_IDLE_FENCE_OBSERVATIONS','rows':rows,'all_frame_pulse_deltas_clocks':deltas,'matched_pending_idle_examples':examples,'source_quiet_rule_clocks':2,'interpretation':'All nine emitted frame pulses move exactly four clocks. Owner-drain transitions are not uniformly delayed by two clocks: token observation and other drain conditions compose with the quiet qualifier. Native stage/data/ACK/raster observations remain unchanged.','limits':['Pending-idle transition logs bounded to 64 per run','Aggregate idle counters include startup/reset clocks','This cohort does not exercise a skipped busy-frame pulse; separate protocol fixture covers it','Memory-clock observation quantization; no metastability or physical MTBF simulation'],'proofs':proofs,'hardware':False},indent=2)+'\n');print(json.dumps({'qualification':str(out),'sha256':sha(out),'frame_deltas':deltas,'matched_idle_deltas':sorted(set(x['delta_clocks']for x in examples))}))
