"""Own-history error diagnostics and reused matched-mean native prefix anchors."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import model as metrics
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-source-v40-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('error57_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;direct=module('error57_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before
std=module('error57_frozen_native24',HERE.parent/'python-game-standard-v24-study/model.py')
CUSTOM=('python-game-motion-v47-study','python-game-quantized-motion-v53-study')
def digest(b):return hashlib.sha256(b).hexdigest()
def pins():
 paths={ROOT/p for p in h.pins()};paths|={HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',SOURCE/'manifest.json',ROOT/'docs/prototype-v53-native-prefix-comparison.json',ROOT/'experiments/compare_motion_v53.py'}
 for folder in CUSTOM:
  p=HERE.parent/folder/'results.json';d=h.load(p);paths.add(p);paths|={ROOT/p for p in d['source_sha256']}
 for p in('experiments/python-game-native-qual-v40-study/results.json','experiments/python-game-native-cap-v41-study/results.json','experiments/python-game-standard-v24-study/model.py'):paths.add(ROOT/p)
 return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def original_inputs(c):
 words=[];rgb=[]
 for f in c['frames'][:24]:
  canvas=np.frombuffer(h.raw(f['canvas_rgb24'],SOURCE),np.uint8).reshape(480,720,3);a=h.m.C.corpus.rgb565(canvas);assert digest(a.astype('<u2').tobytes())==f['rgb565_sha256'];words.append(a);rgb.append(h.m.C.corpus.expand565(a))
 return words,rgb

def main():
 before=pins();source=h.load(SOURCE/'manifest.json');comparison=h.load(ROOT/'docs/prototype-v53-native-prefix-comparison.json');result=[]
 for src in source['cases']:
  scene=Path(src['media_file']).stem;words,originals=original_inputs(src)
  for folder in CUSTOM:
   data=h.load(HERE.parent/folder/'results.json')
   for c in [c for c in data['cases'] if c['scene']==scene]:
    rx=direct.Receiver();metric=metrics.Diagnostics(h.f.f.n.RECTS);rows=[]
    for f,original in zip(c['rows'],originals,strict=True):
     out,patches,meta,_=rx.receive(h.raw(f['packet'],HERE.parent/folder));display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out)),tuple(p['words'] for p in patches));assert h.f.f.n.digest(display)==f['display_sha256'];r=metric.add(original,h.m.C.corpus.expand565(display));assert r['active_SSE']==f['quality']['active_squared_error'];rows.append(dict(id=f['id'],display_sha256=f['display_sha256'],complete_bytes=f['complete_bytes'],cap_fit=f['complete_bytes']<=49152,diagnostic=r))
    result.append(dict(scene=scene,kind='custom',source_folder=folder,policy=c.get('policy','quantized_mixed_guard'),rows=rows,summary=metric.summary(),complete_bytes=sum(r['complete_bytes'] for r in rows),cap_failures=sum(not r['cap_fit'] for r in rows)))
  ctrl=next(c for c in comparison['cases'] if c['study']=='motion-v47' and c['policy']=='zero' and c['scene']==scene)
  for codec,anchor in ctrl['best_sampled_native']['mean'].items():
   if anchor is None:raise ValueError('no declared mean-quality native anchor')
   native=h.load(ROOT/anchor['source']);c=next(c for c in native['cases'] if c['codec']==codec and c['parameter']==anchor['parameter'] and c.get('extra_options')==anchor['extra_options'] and c.get('scene','mass-effect-combat')==scene)
   folder=(ROOT/anchor['source']).parent;records=c['rows'][:24];packets=[dict(data=h.raw(r['access_unit'],folder),pts=r['pts'],dts=r['dts'],is_key=r['key']) for r in records];extra=h.raw(c['extradata'],folder);outputs,work=std.decode(packets,extra,codec);assert not work['frames_only_at_decode_flush'];metric=metrics.Diagnostics(h.f.f.n.RECTS);rows=[]
   for fid,(f,original,a) in enumerate(zip(records,originals,words,strict=True)):
    patches=tuple(a[y:y+hh,x:x+w] for x,y,w,hh in h.f.f.n.RECTS);display=std.overlay(outputs[fid],patches);assert std.digest(display)==f['display_sha256'];r=metric.add(original,h.m.C.corpus.expand565(display));assert r['active_SSE']==f['metric']['active_squared_error'];rows.append(dict(id=fid,display_sha256=f['display_sha256'],complete_bytes=f['complete_bytes'],cap_fit=f['cap_fit'],diagnostic=r))
   result.append(dict(scene=scene,kind='native',codec=codec,parameter=c['parameter'],extra_options=c.get('extra_options'),source=anchor['source'],anchor_selection='minimum sampled actual prefix bytes under zero47 mean-MSE plus completecap gate',rows=rows,summary=metric.summary(),complete_bytes=sum(r['complete_bytes'] for r in rows),cap_failures=sum(not r['cap_fit'] for r in rows)))
  print(json.dumps(dict(scene=scene,cases=len([c for c in result if c['scene']==scene]))),flush=True)
 assert pins()==before
 output=dict(schema='gamebub-error-quality-v57',source_sha256=before,cases=result,scope=['96actualsourceframesreusedacross20policy/anchorcases;480decodedpresentationsnot480newcaptures.','OriginalexpandedRGB565minusdecodedexpandedRGB565error,active37:442;exactHUDoverlaygivenALLcodecs.','Temporalmetricisfixed-coordinateCHANGEINERROR,notmotioncompensatedflickerorvalidatedsubjectiveperception.','Grid8jumpcomparesadjacentERRORdifferenceson/off8pixelgrid,bothpixelsactiveoutsideHUD;notSSIM/VMAF/perceptualqualityproof.','NativeanchorsareREUSEDactualfirst24AUsselectedunderzero47meanMSE+capgatefromsampled40/41grid;notnewencodes/optimalfrontiers/everyframegate.','Actualsourceshaveunequalcadences/precompression;temporaldiagnosticscomparewithincliponly,notphysical30fps.','NoFPGA/ESP32,gamecontrols,networklatencyorhardwareuserexperienceproof.'])
 (HERE/'results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps([dict(scene=c['scene'],policy=c.get('policy',c.get('codec')),bytes=c['complete_bytes'],MSE=c['summary']['active_MSE'],error_change=c['summary']['coordinate_temporal_error_change_MSE'],grid_jump=c['summary']['grid8_error_jump_MSE'],nongrid_jump=c['summary']['nongrid_error_jump_MSE']) for c in result]),flush=True)
if __name__=='__main__':main()
