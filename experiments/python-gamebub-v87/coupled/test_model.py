#!/usr/bin/env python3
"""Small deterministic consumer-credit tests, independent of gameplay corpus."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def scaffold(count,slots,inverse_cycles):
 jobs=[]
 def add(kind,resource,duration,deps=(),**fields):
  ident=len(jobs);jobs.append(dict(id=ident,kind=kind,resource=resource,duration=duration,deps=list(deps),**fields));return ident
 start=add('group_start',None,0,group=0);consumers=[];arrivals=[];done=[];records=[]
 for tile in range(count):
  arrival=add('entropy_tile','entropy',0,[start],tile=tile,group=0);arrivals.append(arrival)
  lookup=add('map_lookup','map_r',1,[arrival,start],tile=tile,group=0)
  inverse=add('inverse','inverse',inverse_cycles,[lookup],tile=tile,group=0);consumers.append(inverse)
  finished=add('reconstruct','reconstruct',1,[inverse],tile=tile,group=0);done.append(finished)
  records.append(dict(tile=tile,producer=arrival,consumer=inverse,bytes=128,release_before_production=None if tile<slots else consumers[tile-slots]))
 end=add('group_release',None,0,done,group=0);complete=add('candidate_complete',None,0,[end])
 return dict(jobs=jobs,groups=[dict(start=start,release=end)],complete=complete,
  counts=dict(inverse_tiles=count,group_payload_buffer_bytes=count*64),assumptions={},
  credits=dict(capacities=dict(reference=slots,inverse=slots,coefficients=slots),constraints=dict(reference=[],inverse=[],coefficients=records)))

def run():
 model=load('cu87_synthetic_model',AREA/'model.py');scheduler=load('cu87_synthetic_scheduler',ROOT/'experiments/python-gamebub-v83/scheduler.py')
 weights=dict(decisions=1,renorm=1,stream_bytes=1,rice_values=1,events=1,raw_bytes=1,header_bytes=1,crc_bytes=1,emits=1,raw_bits=1,prob_init=1)
 checks=[]
 for slots in (1,2,8):
  for lanes in (1,2):
   count=slots+3;zero={k:0 for k in weights};shared=[dict(zero,emits=1) for _ in range(count)]
   contexts=[[dict(zero,decisions=1) for _ in range(4)] for _ in range(count)]
   credited=scaffold(count,slots,1000)
   work=model.couple(credited,shared,contexts,weights,window=slots)
   caps=dict(fetch=1,arithmetic=lanes,emit=1,map_r=1,inverse=1,reconstruct=1,dequant=1)
   result=scheduler.schedule(work['jobs'],caps,retain_timeline=True);audit=model.audit(work,result,lanes)
   rows={r['id']:r for r in result['timeline']};front=work['frontend']
   assert rows[front['setups'][slots]]['start']>=rows[front['consumers'][0]]['finish']
   assert rows[front['setups'][slots]]['start']>rows[front['emits'][0]]['finish']
   assert audit['coefficient_peak_slots']<=slots
   # Remove only downstream credit reuse edges in the comparator: frontend
   # may then run ahead. This is deliberately invalid, not a proposed decoder.
   unbounded=copy.deepcopy(work);by_id={j['id']:j for j in unbounded['jobs']}
   for tile in range(slots,count):
    producer=by_id[front['setups'][tile]];producer['deps'].remove(front['consumers'][tile-slots])
   bad=scheduler.schedule(unbounded['jobs'],caps,retain_timeline=True)
   badrows={r['id']:r for r in bad['timeline']}
   assert badrows[front['setups'][slots]]['start']<rows[front['setups'][slots]]['start']
   try:model.audit(unbounded,bad,lanes)
   except AssertionError:pass
   else:raise AssertionError('unbounded mutation accepted')
   checks.append(dict(name='consumer_backpressure',slots=slots,lanes=lanes,model_finish_cycles=result['finish_cycles'],first_reuse_start=rows[front['setups'][slots]]['start'],unbounded_first_reuse_start=badrows[front['setups'][slots]]['start'],audit=audit))
 # Explicit setup scan sensitivity must causally precede admission.
 base=scaffold(2,2,1);zero={k:0 for k in weights};shared=[dict(zero,emits=1) for _ in range(2)];contexts=[[dict(zero) for _ in range(4)] for _ in range(2)]
 work=model.couple(base,shared,contexts,weights,wire_bytes=123,metadata_bytes=17,window=2,dequant_cycles=64)
 result=scheduler.schedule(work['jobs'],dict(fetch=1,arithmetic=2,emit=1,map_r=1,inverse=1,reconstruct=1,dequant=1),retain_timeline=True)
 rows={r['id']:r for r in result['timeline']};assert rows[work['frontend']['setups'][0]]['start']==140
 assert sum(j['duration'] for j in work['jobs'] if j['kind']=='dequant')==128
 model.audit(work,result,2);checks.append(dict(name='crc_metadata_dequant_causality',crc_bytes=123,metadata_bytes=17,first_setup=140,dequant_work_cycles=128))
 report=dict(schema='cu66-v87-coupled-synthetic-v1',status='PASS',checks=checks,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),AREA/'model.py',ROOT/'experiments/python-gamebub-v83/scheduler.py')},scope='Synthetic dependency/resource tests, not physical timing or gameplay validation.')
 (AREA/'synthetic-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('COUPLED_SYNTHETIC_PASS',len(checks))
if __name__=='__main__':run()
