"""Offline feasibility replay; no wide GM27 frame or receiver is asserted."""
from pathlib import Path
import importlib.util,json,sys,hashlib,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('wide32_verify_bench',HERE/'benchmark.py');t=importlib.util.module_from_spec(s);sys.modules[s.name]=t;s.loader.exec_module(t)
m,r,n=t.m,t.r,t.n

def raw(d,folder=HERE):
 q=Path(d['path']);assert not q.is_absolute() and '..' not in q.parts and 0<=d['raw_bytes']<=1000000
 a=(folder/q).read_bytes();assert hashlib.sha256(a).hexdigest()==d['stored_sha256'];dc=zlib.decompressobj();b=dc.decompress(a,d['raw_bytes']+1)
 assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(b)==d['raw_bytes'] and hashlib.sha256(b).hexdigest()==d['raw_sha256'];return b

def main():
 data=json.loads((HERE/'results.json').read_text())
 assert data['schema']=='gamebub-wide-motion-v32'
 for p,h in data['source_sha256'].items():assert t.sha(ROOT/p)==h,p
 old=json.loads((t.OLD/'results.json').read_text());inputs=json.loads((n.V24/'results.json').read_text())['inputs'];frames=planes=beyond=0
 for case in data['cases']:
  inp=next(x for x in inputs if x['scene']==case['scene']);prior=next(x for x in old['cases'] if x['scene']==case['scene'] and x['policy']=='band_strict');ref=None
  for row,src,pr in zip(case['rows'],inp['rows'],prior['rows']):
   assert row['id']==src['id']==pr['id'];key=row['key'];fid=row['id']
   if key:ref=None
   assert row['accepted_reference_packet']==pr['base_packet']
   source=n.source(src);original=n.original(src);q=r.roi.declared_map(720,480,n.ROIS,8,row['background'])
   prep=m.adaptive.analyze_with(r.base,source,ref,epoch=25,frame_id=fid,reference_id=row['reference_id'],block_size=32,motion_mode='block',motion_precision='half',search_policy='adaptive_zero2')
   packet,baseline,_=r.encode_prepared(prep,q);assert packet==raw(row['baseline']['base_packet']);meta=r.parse(packet)
   assert prep.reference_tag.hex()==row['reference_tag']
   vector=np.frombuffer(raw(row['wide']['vectors']),np.int8).reshape(15,23,2)
   if key:prediction=tuple(np.full_like(x,128) for x in source);assert not np.any(vector)
   else:
    expected,search=m.estimate(source,ref,meta['vectors']);np.testing.assert_array_equal(expected,vector)
    for k,v in search.items():
     if k!='search_ms':assert v==row['wide']['work'][k],k
    assert search['final_sampled_cost']<=search['incumbent_sampled_cost'];prediction=m.predict(ref,vector)
    if np.any(np.abs(vector.astype(np.int16))>18):
     try:r.taps.predict(ref,vector,32)
     except ValueError:pass
     else:raise AssertionError('old GM27 accepted forbiddenwide')
   actual_payloads,expected_out,work=m.residual(source,prediction,q,key)
   coeff=[]
   for plane,desc in enumerate(row['wide']['payloads']):
    payload=raw(desc);assert payload==actual_payloads[plane]
    bw=(720 if plane==0 else 360)//8;count=5400 if plane==0 else 1350
    coeff.append(r.base._decode_plane(payload,count,bw));planes+=1
   out=r.gm.reconstruct(tuple(coeff),prediction,q,720,480)
   for a,b in zip(out,expected_out):np.testing.assert_array_equal(a,b)
   for label,value in (('baseline',baseline),('wide',out)):
    metric,digest=t.metric(original,value);assert metric==row[label]['hybrid'] and digest==row[label]['hybrid_sha256']
   assert r.C.reference_tag(prediction).hex()==row['wide']['prediction_sha256']
   assert r.C.reference_tag(out).hex()==row['wide']['reconstructed_sha256']
   assert work['residual_bytes']==row['wide']['residual_bytes']==sum(d['raw_bytes'] for d in row['wide']['payloads'])
   assert row['wide']['raw_motion_budget_bytes']==(0 if key else 691)
   assert row['wide']['hypothetical_complete_budget_bytes']==80+row['qmap_bytes']+row['wide']['raw_motion_budget_bytes']+row['wide']['residual_bytes']+row['hud_bytes']+60
   assert row['wide']['valid_GM27_frame'] is False
   assert abs(row['wide']['total_with_incumbent_work_ms']-row['baseline']['total_source_work_ms']-row['wide']['incremental_work_ms'])<1e-8
   for label,pred in (('baseline',prep.prediction),('wide',prediction)):
    assert sum(int(np.square(a.astype(np.int64)-b).sum()) for a,b in zip(source,pred))==row[label]['prediction_sse']
   beyond+=row['wide']['work']['beyond_GM27_blocks'];frames+=1
   ref,_=r.decode(raw(pr['base_packet'],t.OLD),ref,expected_epoch=25,expected_reference_id=None if key else row['reference_id'])
  summary=case['summary'];rr=case['rows'];samples=sum(x['baseline']['hybrid']['active_channel_samples'] for x in rr)
  for label,keyname in (('baseline','baseline_mse'),('wide','wide_mse')):assert sum(x[label]['hybrid']['active_squared_error'] for x in rr)/samples==summary[keyname]
  assert sum(x['wide']['work']['beyond_GM27_blocks'] for x in rr)==summary['beyond_GM27_blocks']
  assert sum(x['baseline']['actual_complete_budget_bytes'] for x in rr)==summary['baseline_complete_budget_bytes']
  assert sum(x['wide']['hypothetical_complete_budget_bytes'] for x in rr)==summary['wide_hypothetical_complete_budget_bytes']
 assert frames==24 and planes==72
 print(json.dumps(dict(frames=frames,actual_residual_planes=planes,beyond_GM27_blocks=beyond,source_pins=len(data['source_sha256']),all_vectors_predictions_residuals_metrics_and_own_references_replayed=True,valid_wide_GM27_frames=0,physical_30fps_proven=False)))
if __name__=='__main__':main()
