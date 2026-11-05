"""96 later-window frames: row-filter/color/HUD equivalence and bounded caches."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time
import numpy as np
import model as scan
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('stream64_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;direct=module('stream64_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def digest(b):return hashlib.sha256(b).hexdigest()
def pin_sources():
 source=h.load(SOURCE/'results.json');paths={ROOT/p for p in source['source_pins_sha256']};paths|={SOURCE/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-display-filter-v60-study/model.py',HERE.parent/'python-game-display-filter-v60-study/calibration.json',HERE.parent/'python-game-yuv-scanout-v52-study/model.py',HERE.parent/'python-game-direct-rx-v43-study/helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pin_sources();source=h.load(SOURCE/'results.json');calibration=h.load(HERE.parent/'python-game-display-filter-v60-study/calibration.json');preset=calibration['selected_preset'];zeros=tuple(np.zeros(s,np.int16) for s in((480,720),(240,360),(240,360)));mask=h.f.f.normalize(zeros)[0]==128;mask.setflags(write=False);cases=[]
 for c in source['cases']:
  rx=direct.Receiver();rows=[]
  for f in c['rows'][24:48]:
   out,patches,meta,_=rx.receive(h.raw(f['packet'],SOURCE));assert h.m.C.reference_tag(out).hex()==f['normalized_tag'];planes=tuple(p.astype(np.uint8) for p in out)
   for p in planes:p.setflags(write=False)
   beforehash=digest(b''.join(p.tobytes() for p in planes));expectedY,expectedwork=scan.full.filtered_luma(planes[0],mask,preset);expected=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb((expectedY,planes[1],planes[2]))),tuple(p['words'] for p in patches));reader=scan.Scanout(planes,patches,h.f.f.n.RECTS,mask,preset);yh=hashlib.sha256();rh=hashlib.sha256();start=time.perf_counter_ns()
   for y,(Y,RGB) in enumerate(reader):
    np.testing.assert_array_equal(Y,expectedY[y]);np.testing.assert_array_equal(RGB,expected[y]);assert len(reader.luma.cache)<=4 and len(reader.luma.pending)<=1;yh.update(Y.tobytes());rh.update(RGB.astype('<u2',copy=False).tobytes())
   clock=(time.perf_counter_ns()-start)/1e6;work=reader.work()
   for key in('vertical_changed_edges','horizontal_changed_edges','changed_luma_samples'):assert work['luma'][key]==expectedwork[key]
   assert digest(b''.join(p.tobytes() for p in planes))==beforehash;assert h.m.C.reference_tag(out).hex()==f['normalized_tag'];rows.append(dict(id=f['id'],source_packet=f['packet'],input_reference_sha256=beforehash,normalized_tag=f['normalized_tag'],filtered_Y_sha256=yh.hexdigest(),display_sha256=rh.hexdigest(),work=work,scanout_plus_checks_ms=clock))
  cases.append(dict(scene=c['scene'],rows=rows));assert pin_sources()==before;print(json.dumps(dict(scene=c['scene'],frames=len(rows))),flush=True)
 rows=[r for c in cases for r in c['rows']];summary=dict(frames=len(rows),lines=sum(r['work']['lines'] for r in rows),exact_RGB565_words=sum(r['work']['RGB565_words_written'] for r in rows),exact_HUD_words=sum(r['work']['HUD_word_reads'] for r in rows),source_Y_rows_loaded=sum(r['work']['luma']['Y_rows_loaded'] for r in rows),maximum_cached_vertical_rows=max(r['work']['luma']['peak_cached_vertical_rows'] for r in rows),maximum_pending_rows=max(r['work']['luma']['peak_pending_rows'] for r in rows),maximum_lookahead_rows=max(r['work']['luma']['maximum_lookahead_rows'] for r in rows),mean_scanout_plus_checks_ms=sum(r['scanout_plus_checks_ms'] for r in rows)/len(rows))
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-filtered-scanout-v64',source_sha256=before,preset=preset,cases=cases,summary=summary,scope=['96actualsourceIDs24–47 decodedzero40references;laterwindowthan60calibration0–23.','Exactsamefrozen60strongfilterandfrozen52horizontal/verticalchroma,color/HUD;newboundedrowdeliveryonly.','4verticalrows+1pendingrow+ownedoutputY/RGB;logical7200BrowDATAexcludesstaticmask,HUPatches,fullYUVreference,Pythoninttemporaries,CDC/FIFOs/metadata.','FullimmutableYUV/HUDinputsareexternal-bankmodels;frontbankfences/physicalports/timingnotimplemented.','Pulliteratorpause/backpressureisfunctionalmodel,notRTLhandshakeorclock/FPSproof.','Clocksincludeassert/hash,excludeddecode/oraclegeneration;noCPUrateadvantageclaim.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
