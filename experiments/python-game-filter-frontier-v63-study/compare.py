"""Post-display-filter sampled quality gates across all native options."""
from pathlib import Path
import hashlib,json,sys
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def build():
 native=json.loads((HERE/'results.json').read_text());custom_path=HERE.parent/'python-game-filter-temporal-v62-study/results.json';custom=json.loads(custom_path.read_text());cases=[]
 for c in custom['cases']:
  if c['kind']!='custom':continue
  for p in c['presets']:
   target_sse=[r['diagnostic']['active_SSE'] for r in p['rows']];target_samples=[r['diagnostic']['active_samples'] for r in p['rows']];qualified={}
   for gate in('mean','mean_and_peak','every_frame'):
    qualified[gate]={}
    for codec in('libx265','libsvtav1'):
     options=[]
     for i,n in enumerate(native['cases']):
      if not n.get('supported',False) or n['scene']!=c['scene'] or n['codec']!=codec:continue
      for pi,q in enumerate(n['presets']):
       ss=[r['quality']['active_squared_error'] for r in q['rows']];ns=[r['quality']['active_channel_samples'] for r in q['rows']];sizes=[r['complete_bytes'] for r in q['rows']]
       if model.qualifies(ss,ns,sizes,target_sse,target_samples,gate):options.append(dict(native_point=i,source=n['source'],source_case=n['source_case'],codec=codec,parameter=n['parameter'],extra_options=n['extra_options'],bitrate=n['bitrate'],display_preset=q['preset']['name'],complete_bytes=sum(sizes),active_SSE=sum(ss),active_samples=sum(ns),active_MSE=sum(ss)/sum(ns),peak_frame_MSE=max(r['quality']['active_mse'] for r in q['rows']),preset_order=pi))
     qualified[gate][codec]=min(options,key=lambda q:(q['complete_bytes'],q['active_SSE'],q['preset_order'],q['native_point'])) if options else None
   cases.append(dict(scene=c['scene'],policy=c['policy'],display_preset=p['preset']['name'],custom_complete_bytes=c['complete_bytes'],custom_active_MSE=p['summary']['active_MSE'],custom_peak_frame_MSE=max(r['diagnostic']['active_MSE'] for r in p['rows']),best_sampled_native=qualified))
 files=(HERE/'compare.py',HERE/'model.py',HERE/'results.json',custom_path)
 return dict(schema='gamebub-filter-frontier-v63-comparison',source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files},cases=cases,scope=['ALL69measuredfreshnativepointswithidentity/strongdisplayoptions;sampledselection,notoptimalencoderfrontier.','QualitygatesapplyAFTERfilterforcustomandnative;62prefilteranchorsremainfixedandarenotretroactivelycalledmatched.','Onefixeddisplayoptionperpointfor24frames,noper-frameoracle;strongcalibratedonzero0–23,notretuned24–47.','Byteaccountingunchangedbydisplayfilter;noFPGA/ESP32/physicalFPSproof.'])
def main():
 d=build();target=HERE/'comparison.json'
 if '--check'in sys.argv:assert json.loads(target.read_text())==d
 else:target.write_text(json.dumps(d,indent=2)+'\n')
 print(json.dumps([dict(scene=c['scene'],policy=c['policy'],preset=c['display_preset'],custom_bytes=c['custom_complete_bytes'],custom_MSE=c['custom_active_MSE'],native_mean={k:None if v is None else dict(bytes=v['complete_bytes'],MSE=v['active_MSE'],filter=v['display_preset']) for k,v in c['best_sampled_native']['mean'].items()}) for c in d['cases']],indent=2))
if __name__=='__main__':main()
