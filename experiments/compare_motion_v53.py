#!/usr/bin/env python3
"""Actual first24 native prefixes versus own-history motion policies."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parent.parent
CUSTOM=('motion-v47','guarded-motion-v50','quantized-motion-v53');NATIVE=('experiments/python-game-native-qual-v40-study/results.json','experiments/python-game-native-cap-v41-study/results.json')
def load(p):return json.loads((ROOT/p).read_text())
def summarize_native(c,scene,label):
 r=c['rows'][:24];return dict(scene=scene,codec=c['codec'],parameter=c['parameter'],extra_options=c.get('extra_options'),source=label,complete_bytes=sum(x['complete_bytes'] for x in r),maximum_complete_bytes=max(x['complete_bytes'] for x in r),cap_failures=sum(not x['cap_fit'] for x in r),active_squared_error=sum(x['metric']['active_squared_error'] for x in r),active_channel_samples=sum(x['metric']['active_channel_samples'] for x in r),peak_frame_mse=max(x['metric']['active_mse'] for x in r),per_frame_SSE=[x['metric']['active_squared_error'] for x in r])
def build():
 paths=[*NATIVE,'experiments/compare_motion_v53.py'];points=[]
 for c in load(NATIVE[0])['cases']:
  if c['supported']:points.append(summarize_native(c,c['scene'],NATIVE[0]))
 for c in load(NATIVE[1])['cases']:
  if c['supported']:points.append(summarize_native(c,'mass-effect-combat',NATIVE[1]))
 cases=[]
 for study in CUSTOM:
  p='experiments/python-game-'+study+'-study/results.json';paths.append(p)
  for c in load(p)['cases']:
   rows=c['rows'];assert len(rows)==24 and all(r['accepted'] for r in rows);s=c['summary'];SSE=[r['quality']['active_squared_error'] for r in rows];samples=sum(r['quality']['active_channel_samples'] for r in rows);mean=sum(SSE)/samples;peak=max(r['quality']['active_mse'] for r in rows);native=[q for q in points if q['scene']==c['scene']];gate={}
   for name in('mean','mean_and_peak','every_frame'):
    eligible=[]
    for q in native:
     meanOK=q['active_squared_error']/q['active_channel_samples']<=mean;peakOK=q['peak_frame_mse']<=peak;every=all(a<=b for a,b in zip(q['per_frame_SSE'],SSE,strict=True));ok=meanOK if name=='mean' else meanOK and peakOK if name=='mean_and_peak' else every
     if not q['cap_failures'] and ok:eligible.append(q)
    gate[name]={codec:min((q for q in eligible if q['codec']==codec),key=lambda q:q['complete_bytes'],default=None) for codec in('libx265','libsvtav1')}
   cases.append(dict(study=study,scene=c['scene'],policy=c.get('policy','quantized_mixed_guard'),custom_complete_bytes=s['complete_bytes'],custom_active_mse=mean,custom_peak_frame_mse=peak,custom_maximum_complete_bytes=max(r['complete_bytes'] for r in rows),sampled_native_prefix_points=len(native),best_sampled_native=gate))
 pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths};return dict(schema='gamebub-motion-v53-native-prefix-comparison',source_sha256=pins,cases=cases,native_prefix_points=points,scope=['Actualfirst24sourceframesandexactHUDmatch;nativeAUsareREUSEDprefixesoffrozen40/41encodes,notnewnativeencodes.','OriginalRGB565sourceSSE;separatemean/mean+peak/everyframegatesallrequirecompletecapfit;nointerpolation/optimalencoderclaim.','Own-historycustommotionpoliciesarenotlosslessrecodeequivalents;actualrate/errorreported.','Native80Bbindingisanaccountingmodel;noFPGAstandardsdecoder/portorphysical30fpsproof.'])
def main():
 d=build();p=ROOT/'docs/prototype-v53-native-prefix-comparison.json'
 if '--check' in sys.argv:assert json.loads(p.read_text())==d
 else:p.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps([dict(study=c['study'],scene=c['scene'],policy=c.get('policy','quantized_mixed_guard'),custom_bytes=c['custom_complete_bytes'],custom_MSE=c['custom_active_mse'],native_mean={k:None if v is None else dict(bytes=v['complete_bytes'],parameter=v['parameter'],source=v['source']) for k,v in c['best_sampled_native']['mean'].items()}) for c in d['cases']],indent=2))
if __name__=='__main__':main()
