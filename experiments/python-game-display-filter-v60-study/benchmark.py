"""Apply the same predeclared display-only filter grid to custom/native cases."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import model as filt
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
io=module('filter60_frozen_quality57_IO',HERE.parent/'python-game-error-quality-v57-study/verify.py');h=io.h;metric=module('filter60_frozen_quality57_metrics',HERE.parent/'python-game-error-quality-v57-study/model.py')
SOURCE=HERE.parent/'python-game-error-quality-v57-study/results.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def plane_digest(planes):return digest(b''.join(p.astype('u1',copy=False).tobytes() for p in planes))
def pins():
 d=h.load(SOURCE);paths={ROOT/p for p in d['source_sha256']};paths|={SOURCE,HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-error-quality-v57-study/verify.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pins();data=h.load(SOURCE);normalized=h.f.f.normalize(tuple(np.zeros(shape,np.int16) for shape in((480,720),(240,360),(240,360))));guard=normalized[0]==128;guard.setflags(write=False);result=[];cache={}
 for ci,case in enumerate(data['cases']):
  if case['scene'] not in cache:cache[case['scene']]=io.originals(case['scene'])
  words,originals=cache[case['scene']];states={p['name']:metric.Diagnostics(h.f.f.n.RECTS) for p in filt.PRESETS};rows={p['name']:[] for p in filt.PRESETS}
  for source,(fid,planes,patches,baseline),original in zip(case['rows'],io.presentations(case,words),originals,strict=True):
   base_hash=plane_digest(planes);assert digest(baseline.astype('<u2').tobytes())==source['display_sha256']
   for preset in filt.PRESETS:
    Y,work=filt.filtered_luma(planes[0],guard,preset);assert plane_digest(planes)==base_hash;display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words'] for p in patches));diagnostic=states[preset['name']].add(original,h.m.C.corpus.expand565(display))
    if preset['name']=='identity':assert diagnostic==source['diagnostic'] and digest(display.astype('<u2').tobytes())==source['display_sha256']
    for patch,(x,y,w,hh) in zip(patches,h.f.f.n.RECTS,strict=True):np.testing.assert_array_equal(display[y:y+hh,x:x+w],patch['words'])
    rows[preset['name']].append(dict(id=fid,reference_input_sha256=base_hash,display_sha256=digest(display.astype('<u2').tobytes()),complete_bytes=source['complete_bytes'],diagnostic=diagnostic,work=work))
  result.append(dict(source_case=ci,scene=case['scene'],kind=case['kind'],policy=case.get('policy',case.get('codec')),codec=case.get('codec'),complete_bytes=case['complete_bytes'],cap_failures=case['cap_failures'],presets=[dict(preset=p,rows=rows[p['name']],summary=states[p['name']].summary()) for p in filt.PRESETS]));assert pins()==before;print(json.dumps(dict(scene=case['scene'],kind=case['kind'],policy=case.get('policy',case.get('codec')),MSE={p:states[p].summary()['active_MSE'] for p in states})),flush=True)
 out=dict(schema='gamebub-display-filter-v60',source_sha256=before,cases=result,excluded_luma_samples=int(guard.sum()),excluded_luma_sha256=digest(guard.tobytes()),scope=['20reusedpolicy/nativeanchorcases×4fixedpresets×24frames=1920displayvariants,not1920uniquecaptures.','FilterlumaONLYfordisplay;immutablecanonical/referenceYUVunchanged,HUPatchesoverlaidexactlyaftercolorconversion.','SamefourpresetgridgiventoALLcustom/nativecases;identitycontrolmustexact57pixels/metrics.','Fixedpresetperdisplayprofilewouldneedconfiguration/negotiation;oracleper-framechoicenotimplementedandnotfreeprotocolmetadata.','PrototypestagesfullYUVplane;streaminglinebuffer/DSP/ports/clockimplementationNOTprovided.','Metricerrorchange/gridjumparedefineddiagnostics,notSSIM/VMAF/subjectiveflickerproof.','Noencodedbytegain,nativecodecfrontier/hardwareFPSclaim;sourcecounterexamplesandallregressionsretained.'])
 (HERE/'results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(source_cases=len(result),fixed_presets=4,display_variants=1920)),flush=True)
if __name__=='__main__':main()
