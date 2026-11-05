"""Re-evaluate ALL69 fresh native points with identical fixed display options."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P62=HERE.parent/'python-game-filter-temporal-v62-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('frontier63_frozen62_helpers',P62/'helpers.py');a=h.bound('frontier63_frozen62_adapter',P62/'adapter.py',h);v=module('frontier63_frozen62_verify',P62/'verify.py')

def pins():
 paths={ROOT/p for p in h.pins()};paths|={P62/'results.json',P62/'verify.py',HERE/'benchmark.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pins();native=v.normalized_native_points();mask=h.excluded();presets=h.fixed_presets();cache={};result=[]
 for point in native:
  c=point['case']
  if not c.get('supported',True):result.append(dict(source=point['source'],source_case=point['source_case'],supported=False,error=c['error']));continue
  scene=c['scene']
  if scene not in cache:cache[scene]=a.originals(scene)
  words,rgb=cache[scene];case=dict(kind='native',scene=scene,policy=c['codec'],codec=c['codec'],parameter=c['parameter'],extra_options=c.get('extra_options'),bitrate=c.get('bitrate'),source=point['source'],source_case=point['source_case']);rows={p['name']:[] for p in presets}
  for frame in a.presentations(case,words):
   i=frame['id']-24;ref=h.planes_digest(frame['planes'])
   for preset in presets:
    Y,work=h.filt.filtered_luma(frame['planes'][0],mask,preset);assert h.planes_digest(frame['planes'])==ref;display=h.h.f.f.n.overlay(h.h.m.C.corpus.rgb565(h.h.m.ft.planes_to_rgb((Y,frame['planes'][1],frame['planes'][2]))),tuple(p['words'] for p in frame['patches']));quality=h.io.std.metric(words[i],display)
    if preset['name']=='identity':assert quality==frame['expected_quality']
    rows[preset['name']].append(dict(id=frame['id'],native_pts=frame['native_pts'],complete_bytes=frame['complete_bytes'],reference_input_sha256=ref,display_sha256=h.digest(display.astype('<u2').tobytes()),quality=quality))
  records=[]
  for preset in presets:
   rs=rows[preset['name']];SSE=sum(r['quality']['active_squared_error'] for r in rs);samples=sum(r['quality']['active_channel_samples'] for r in rs);records.append(dict(preset=preset,rows=rs,summary=dict(frames=24,complete_bytes=sum(r['complete_bytes'] for r in rs),cap_failures=sum(r['complete_bytes']>49152 for r in rs),active_squared_error=SSE,active_channel_samples=samples,active_mse=SSE/samples,peak_frame_mse=max(r['quality']['active_mse'] for r in rs))))
  result.append(dict(**case,supported=True,presets=records));assert pins()==before
  print(json.dumps(dict(scene=scene,codec=c['codec'],parameter=c['parameter'],source=point['source'],source_case=point['source_case'])),flush=True)
 assert len(result)==69
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-filter-frontier-v63',source_sha256=before,cases=result,summary=dict(native_points=69,decoded_presentations=1656,display_variants=3312,source_canvases=96),scope=['ALL48fresh61coarsepoints+21fresh61peakcontrols,notnewnativeencodes/optimalfrontier.','Samefrozen60identity/strongoptionsgiventoallnativepointsandcustom62;canonicalinputunchanged,HUPatchesexact.','SourceIDs24–47,nativePTS0–23,allcapfailuresretainedandidentityqualitymustequal61metadata.','Selectioncanapplypostfilterqualitygates;62pre-filteranchorfixedcomparisonkeptseparately.','Noencoding/bitratechange,subjectivequality,FPGAfit,physicalFPSorstandardsdecoderproof.']),indent=2)+'\n');print(json.dumps(dict(native_points=69,decoded_presentations=1656,display_variants=3312)),flush=True)
if __name__=='__main__':main()
