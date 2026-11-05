#!/usr/bin/env python3
"""Compare actual complete combat packets under explicit source-error gates."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent.parent
FILES=('experiments/python-game-native-cap-v41-study/results.json','experiments/python-game-binary-qual-v40-study/results.json','experiments/compare_native_cap_v41.py')
def main():
 native=json.loads((ROOT/FILES[0]).read_text());custom=json.loads((ROOT/FILES[1]).read_text())['cases'][-1];rows=custom['rows'];sm=custom['summary'];mean=sm['active_mse'];peak=max(r['quality']['active_mse'] for r in rows);points=[]
 for c in native['cases']:
  if not c['supported']:continue
  s=c['summary'];assert len(c['rows'])==len(rows)==100
  every=all(a['metric']['active_squared_error']<=b['quality']['active_squared_error'] for a,b in zip(c['rows'],rows,strict=True))
  points.append(dict(codec=c['codec'],parameter=c['parameter'],extra_options=c['extra_options'],complete_bytes=s['complete_bytes'],active_mse=s['active_mse'],peak_frame_mse=s['peak_frame_mse'],maximum_complete_bytes=s['maximum_complete_bytes'],cap_failures=s['cap_failures'],mean_quality_ok=s['active_mse']<=mean,mean_peak_quality_ok=s['active_mse']<=mean and s['peak_frame_mse']<=peak,every_frame_quality_ok=every))
 winners={}
 for name,field in [('mean','mean_quality_ok'),('mean_and_peak','mean_peak_quality_ok'),('every_frame','every_frame_quality_ok')]:
  winners[name]={}
  for codec in ('libx265','libsvtav1'):
   eligible=[p for p in points if p['codec']==codec and p[field] and not p['cap_failures']];winners[name][codec]=min(eligible,key=lambda p:p['complete_bytes']) if eligible else None
 result=dict(schema='gamebub-native-cap-v41-comparison',source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES},custom=dict(complete_bytes=sm['complete_bytes'],active_mse=mean,peak_frame_mse=peak,maximum_complete_bytes=sm['maximum_complete_bytes']),points=points,best_sampled=winners,scope=['Targetedpostgrid21pointcombatresearch; noexhaustivesearchorindependentvalidationclaim.','EverycandidatechargedactualAU,HX33,80Bmodeledbinding,extradataonce; nohardwaredecoderorphysicalFPSproof.'])
 target=ROOT/'docs/prototype-v41-native-cap-comparison.json'
 if '--check' in sys.argv:assert json.loads(target.read_text())==result
 else:target.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(points=len(points),custom=result['custom'],best_sampled=winners),indent=2))
if __name__=='__main__':main()
