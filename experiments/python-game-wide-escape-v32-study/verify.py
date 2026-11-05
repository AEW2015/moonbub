from pathlib import Path
import json,struct
import numpy as np
import model as m
import importlib.util,sys
_spec=importlib.util.spec_from_file_location('escape32_own_benchmark',Path(__file__).resolve().parent/'benchmark.py')
b=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=b;_spec.loader.exec_module(b)
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
EXPECTED_SCENES=('mass-effect-2600','mass-effect-7200')
EXPECTED_IDS=list(range(12))
def check_completeness(data,old):
 for label,document in [('current',data),('original',old)]:
  cases=document.get('cases')
  if type(cases)is not list or [c.get('scene') for c in cases]!=list(EXPECTED_SCENES):raise ValueError(label+' exact ordered scenes')
  for case in cases:
   rows=case.get('rows')
   if type(rows)is not list or [r.get('id') for r in rows]!=EXPECTED_IDS:raise ValueError(label+' exact ordered 12 IDs')
 for case,prior in zip(data['cases'],old['cases'],strict=True):
  if case['scene']!=prior['scene']:raise ValueError('scene alignment')
  if case['summary']['frames']!=12:raise ValueError('summary frame count')
  for row,original in zip(case['rows'],prior['rows'],strict=True):
   if row['id']!=original['id'] or row['key']!=original['key'] or row['vectors']!=original['wide']['vectors']:raise ValueError('row alignment')
 return True

def validate_final_pins(pins):
 if type(pins)is not dict or not pins:raise ValueError('final source pins required')
 required={HERE/p for p in ['model.py','benchmark.py','verify.py','test_model.py','results.json','README.md','tests.log','verify.log','run.log']}
 for p in HERE.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name!='sourcepins.json':required.add(p)
 if any(p.relative_to(ROOT).as_posix() not in pins for p in required):raise ValueError('incomplete final pins')
 if (HERE/'sourcepins.json').relative_to(ROOT).as_posix() in pins:raise ValueError('source pins self reference')
 for path,digest in pins.items():
  target=ROOT/path
  if Path(path).is_absolute() or not target.resolve().is_relative_to(ROOT) or not target.is_file() or b.sha(target)!=digest:raise ValueError('final source pin mismatch: '+path)
 return len(pins)

def main():
 data=json.loads((HERE/'results.json').read_text());old=json.loads((b.OLD/'results.json').read_text());count=escapes=0
 check_completeness(data,old)
 final_pins=json.loads((HERE/'sourcepins.json').read_text());final_count=validate_final_pins(final_pins)
 for p,h in data['source_sha256'].items():
  assert b.sha(ROOT/p)==h,p
  assert p in final_pins,p
 for case,ocase in zip(data['cases'],old['cases'],strict=True):
  assert case['scene']==ocase['scene'];totals=dict(baseline_actual_complete_budget_bytes=0,raw_complete_budget_bytes=0,escape_hypothetical_complete_budget_bytes=0,raw_motion_bytes=0,escape_motion_bytes=0,escape_count=0)
  for row,prior in zip(case['rows'],ocase['rows'],strict=True):
   packet=b.raw(row['packet'],HERE);expected=np.frombuffer(b.raw(prior['wide']['vectors']),np.int8).reshape(15,23,2);out=m.unpack(packet);np.testing.assert_array_equal(expected,out)
   assert m.pack(expected)==packet
   magic,mw,mh,nb,n,crc=m.HEADER.unpack_from(packet);assert (magic,mw,mh)==(b'WV32',23,15)
   base=m.frozen.unpack_vectors(packet[16:16+nb],23,15);flat=base.reshape(-1,2);last=-1
   for offset in range(16+nb,len(packet),4):
    i,x,y=struct.unpack_from('<Hbb',packet,offset);assert last<i<len(flat) and np.all(flat[i]==0) and 18<max(abs(x),abs(y))<=68;flat[i]=(x,y);last=i
   np.testing.assert_array_equal(base,expected);assert n==row['work']['escape_count'];escapes+=n
   charged=0 if row['key'] else len(packet);assert charged==row['motion_charged_bytes']
   budget=80+row['qmap_bytes']+charged+row['residual_bytes']+row['hud_bytes']+60
   assert budget==row['escape_hypothetical_complete_budget_bytes'];assert prior['wide']['hypothetical_complete_budget_bytes']==row['raw_complete_budget_bytes']
   assert row['wide_hybrid']==prior['wide']['hybrid'] and row['wide_hybrid_sha256']==prior['wide']['hybrid_sha256'] and row['wide_prediction_sse']==prior['wide']['prediction_sse']
   assert row['key']==prior['key'] and row['vectors']==prior['wide']['vectors']
   assert row['residual_bytes']==prior['wide']['residual_bytes'] and row['qmap_bytes']==prior['qmap_bytes'] and row['hud_bytes']==prior['hud_bytes']
   assert row['raw_motion_budget_bytes']==prior['wide']['raw_motion_budget_bytes'] and row['baseline_actual_complete_budget_bytes']==prior['baseline']['actual_complete_budget_bytes']
   assert row['new_total_source_work_ms']==row['wide_original_work_ms']+row['work']['pack_ms']
   for k in totals:totals[k]+=n if k=='escape_count' else row['raw_motion_budget_bytes'] if k=='raw_motion_bytes' else charged if k=='escape_motion_bytes' else row[k]
   count+=1
  for k,v in totals.items():assert case['summary'][k]==v,(k,v)
 assert count==24 and escapes==267,(count,escapes)
 assert [c['summary']['escape_count'] for c in data['cases']]==[114,153]
 print(json.dumps(dict(maps=count,escapes=escapes,source_pins=len(data['source_sha256']),final_source_pins=final_count,exact_scope_verified=True,all_actual_packets_vectors_and_budgets_replayed=True,valid_wide_GM27_frames=0,physical_30fps_proven=False)))
if __name__=='__main__':main()
