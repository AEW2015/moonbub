"""Independent all-point plane/filter/quality replay and postfilter gates."""
from pathlib import Path
from fractions import Fraction
import importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P62=HERE.parent/'python-game-filter-temporal-v62-study'
s=importlib.util.spec_from_file_location('frontier63_verify_frozen62',P62/'verify.py');v=importlib.util.module_from_spec(s);sys.modules[s.name]=v;s.loader.exec_module(v);h=v.h

def main():
 data=h.load(HERE/'results.json');points=v.normalized_native_points();assert len(points)==len(data['cases'])==69;norm=v.f.f.normalize(tuple(np.zeros(shape,np.int16) for shape in((480,720),(240,360),(240,360))));mask=norm[0]==128;cache={};variants=0;decoded=0
 for p,want in data['source_sha256'].items():assert h.sha(ROOT/p)==want,p
 for case,point in zip(data['cases'],points,strict=True):
  original=point['case'];assert(case['source'],case['source_case'])==(point['source'],point['source_case'])
  if not case['supported']:assert not original.get('supported',True);continue
  if case['scene'] not in cache:cache[case['scene']]=v.originals(case['scene'])
  source=cache[case['scene']];meta=dict(case);assert meta['kind']=='native';sse=[0,0];samples=[0,0]
  for fid,pts,planes,patches,canonical,size,packet,quality,display_sha in v.presentations(meta,source):
   _,words,expanded=source[fid];before=[v.digest(p.tobytes()) for p in planes];decoded+=1
   for index,preset in enumerate((v.IDENTITY,v.STRONG)):
    record=case['presets'][index];assert record['preset']==preset;row=record['rows'][fid-24];Y,work=v.oracle_filter(planes[0],mask,preset);display=v.n.overlay(v.m.C.corpus.rgb565(v.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words'] for p in patches));metric=v.io.std.metric(words,display);assert row['quality']==metric and row['id']==fid and row['native_pts']==pts and row['complete_bytes']==size;assert v.digest(display.astype('<u2').tobytes())==row['display_sha256'];assert v.digest(b''.join(p.astype('u1',copy=False).tobytes() for p in planes))==row['reference_input_sha256'];assert [v.digest(p.tobytes()) for p in planes]==before
    if preset['name']=='identity':assert metric==quality and row['display_sha256']==display_sha
    sse[index]+=metric['active_squared_error'];samples[index]+=metric['active_channel_samples'];variants+=1
  for i,p in enumerate(case['presets']):
   rows=p['rows'];expected=dict(frames=24,complete_bytes=sum(r['complete_bytes'] for r in rows),cap_failures=sum(r['complete_bytes']>49152 for r in rows),active_squared_error=sse[i],active_channel_samples=samples[i],active_mse=sse[i]/samples[i],peak_frame_mse=max(r['quality']['active_mse'] for r in rows));assert expected==p['summary']
 assert decoded==1656 and variants==3312
 comparison=h.load(HERE/'comparison.json');custom=h.load(P62/'results.json');expected=[]
 for c in custom['cases']:
  if c['kind']!='custom':continue
  for p in c['presets']:
   target=[r['diagnostic']['active_SSE'] for r in p['rows']];tn=[r['diagnostic']['active_samples'] for r in p['rows']];gate_results={}
   for gate in('mean','mean_and_peak','every_frame'):
    gate_results[gate]={}
    for codec in('libx265','libsvtav1'):
     choices=[]
     for ni,n in enumerate(data['cases']):
      if not n.get('supported') or n['scene']!=c['scene'] or n['codec']!=codec:continue
      for pi,q in enumerate(n['presets']):
       es=[r['quality']['active_squared_error'] for r in q['rows']];ns=[r['quality']['active_channel_samples'] for r in q['rows']];sizes=[r['complete_bytes'] for r in q['rows']];mean=sum(es)*sum(tn)<=sum(target)*sum(ns);peak=max(Fraction(a,b) for a,b in zip(es,ns,strict=True))<=max(Fraction(a,b) for a,b in zip(target,tn,strict=True));every=all(a*d<=c*b for a,b,c,d in zip(es,ns,target,tn,strict=True));ok=mean if gate=='mean' else mean and peak if gate=='mean_and_peak' else every
       if ok and max(sizes)<=49152:choices.append(dict(native_point=ni,source=n['source'],source_case=n['source_case'],codec=codec,parameter=n['parameter'],extra_options=n['extra_options'],bitrate=n['bitrate'],display_preset=q['preset']['name'],complete_bytes=sum(sizes),active_SSE=sum(es),active_samples=sum(ns),active_MSE=sum(es)/sum(ns),peak_frame_MSE=max(r['quality']['active_mse'] for r in q['rows']),preset_order=pi))
     gate_results[gate][codec]=min(choices,key=lambda q:(q['complete_bytes'],q['active_SSE'],q['preset_order'],q['native_point'])) if choices else None
   expected.append(dict(scene=c['scene'],policy=c['policy'],display_preset=p['preset']['name'],custom_complete_bytes=c['complete_bytes'],custom_active_MSE=p['summary']['active_MSE'],custom_peak_frame_MSE=max(r['diagnostic']['active_MSE'] for r in p['rows']),best_sampled_native=gate_results))
 assert expected==comparison['cases']
 for p,want in comparison['source_sha256'].items():assert h.sha(ROOT/p)==want,p
 print(json.dumps(dict(native_points=69,decoded_native_presentations=decoded,display_variants=variants,all_filter_and_quality_samples_independently_rederived=True,postfilter_quality_gates_recomputed=True,custom_comparisons=len(expected),encoded_bytes_unchanged=True,encoding_called=False,optimal_native_frontier_or_hardware_FPS_proven=False)))
if __name__=='__main__':main()
