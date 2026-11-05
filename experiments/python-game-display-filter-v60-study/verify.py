"""Independent scalar filter samples, immutable references, full quality replay."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import model as subject
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
io=module('filter60_verify_quality57_IO',HERE.parent/'python-game-error-quality-v57-study/verify.py');h=io.h

def scalar(plane,excluded,preset,y,x):
 if not preset['strength']:return int(plane[y,x])
 def correction(p1,p0,q0,q1,blocked):
  if blocked or abs(q0-p0)>preset['alpha'] or abs(p0-p1)>preset['beta'] or abs(q1-q0)>preset['beta']:return 0
  return min(preset['strength'],max(-preset['strength'],(3*(q0-p0)+p1-q1+4)//8))
 def vertical(y,x):
  if x%8 not in(0,7):return int(plane[y,x])
  boundary=x+1 if x%8==7 else x
  if not 8<=boundary<720:return int(plane[y,x])
  p1,p0,q0,q1=map(int,plane[y,boundary-2:boundary+2]);delta=correction(p1,p0,q0,q1,bool(np.any(excluded[y,boundary-2:boundary+2])))
  return min(255,max(0,p0+delta if x==boundary-1 else q0-delta))
 if y%8 not in(0,7):return vertical(y,x)
 boundary=y+1 if y%8==7 else y
 if not 8<=boundary<480:return vertical(y,x)
 p1,p0,q0,q1=[vertical(row,x) for row in range(boundary-2,boundary+2)];delta=correction(p1,p0,q0,q1,bool(np.any(excluded[boundary-2:boundary+2,x])))
 return min(255,max(0,p0+delta if y==boundary-1 else q0-delta))

def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 d=h.load(HERE/'results.json');source=h.load(HERE.parent/'python-game-error-quality-v57-study/results.json');assert len(d['cases'])==len(source['cases'])==20;norm=h.f.f.normalize(tuple(np.zeros(s,np.int16) for s in((480,720),(240,360),(240,360))));guard=norm[0]==128;assert digest(guard.tobytes())==d['excluded_luma_sha256'] and int(guard.sum())==d['excluded_luma_samples'];cache={};variants=samples=0
 for p,s in d['source_sha256'].items():assert h.sha(ROOT/p)==s,p
 for ci,(case,old) in enumerate(zip(d['cases'],source['cases'],strict=True)):
  assert case['source_case']==ci and(case['scene'],case['kind'],case['complete_bytes'],case['cap_failures'])==(old['scene'],old['kind'],old['complete_bytes'],old['cap_failures'])
  if case['scene'] not in cache:cache[case['scene']]=io.originals(case['scene'])
  words,originals=cache[case['scene']];previous={p['name']:None for p in subject.PRESETS};metrics={p['name']:[] for p in subject.PRESETS}
  for fid,planes,patches,baseline in io.presentations(old,words):
   original=originals[fid];before=[digest(p.tobytes()) for p in planes]
   for pi,preset in enumerate(subject.PRESETS):
    record=case['presets'][pi];assert record['preset']==preset;r=record['rows'][fid];Y,work=subject.filtered_luma(planes[0],guard,preset);assert [digest(p.tobytes()) for p in planes]==before and work==r['work'];assert digest(b''.join(p.astype('u1',copy=False).tobytes() for p in planes))==r['reference_input_sha256']
    rng=np.random.default_rng(600000+ci*1000+fid);coords=list(zip(rng.integers(0,480,192),rng.integers(0,720,192)))+[(y,x) for y in(7,8,15,16,239,240,471,472) for x in(7,8,15,16,359,360,711,712)]
    for y,x in coords:assert int(Y[y,x])==scalar(planes[0],guard,preset,int(y),int(x));samples+=1
    display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb((Y,planes[1],planes[2]))),tuple(p['words'] for p in patches));assert digest(display.astype('<u2').tobytes())==r['display_sha256'];error,expected=io.equations(original,h.m.C.corpus.expand565(display),previous[preset['name']]);previous[preset['name']]=error;assert expected==r['diagnostic'];metrics[preset['name']].append(expected);assert r['complete_bytes']==old['rows'][fid]['complete_bytes']
    for patch,(x,y,w,hh) in zip(patches,h.f.f.n.RECTS,strict=True):np.testing.assert_array_equal(display[y:y+hh,x:x+w],patch['words'])
    if preset['name']=='identity':assert expected==old['rows'][fid]['diagnostic'] and digest(display.astype('<u2').tobytes())==old['rows'][fid]['display_sha256']
    variants+=1
  for p in case['presets']:assert io.summarize(metrics[p['preset']['name']])==p['summary']
 assert variants==1920 and samples==491520;print(json.dumps(dict(policy_anchor_cases=20,display_variants=variants,source_canvases=96,independent_scalar_filter_samples=samples,all_reference_inputs_immutable=True,all_HUD_words_exact=True,all_quality_equations_rederived=True,encoded_bytes_unchanged=True,encoding_called=False,subjective_quality_or_hardware_FPS_proven=False)))
if __name__=='__main__':main()
