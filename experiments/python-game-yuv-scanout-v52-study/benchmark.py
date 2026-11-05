"""Exact scanline composition of96 actual decoded CS38 references and HUDs."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time
import numpy as np
import model as scan
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('scanout52_frozen_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;direct=module('scanout52_frozen_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def digest(b):return hashlib.sha256(b).hexdigest()
def pins():
 source=h.load(SOURCE/'results.json');paths={ROOT/p for p in source['source_pins_sha256']};paths|={SOURCE/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-direct-rx-v43-study/helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pins();source=h.load(SOURCE/'results.json');cases=[]
 for case in source['cases']:
  rx=direct.Receiver();rows=[]
  for f in case['rows'][:24]:
   decoded,patches,meta,_=rx.receive(h.raw(f['packet'],SOURCE));planes=tuple(p.astype(np.uint8) for p in decoded)
   for p in planes:p.setflags(write=False)
   expected=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)),tuple(p['words'] for p in patches));digestor=hashlib.sha256();reader=scan.Scanout(planes,patches,h.f.f.n.RECTS);start=time.perf_counter_ns()
   for y,line in enumerate(reader):np.testing.assert_array_equal(line,expected[y]);digestor.update(line.astype('<u2',copy=False).tobytes())
   elapsed=(time.perf_counter_ns()-start)/1e6;tag=digestor.hexdigest();assert tag==f['display_sha256'];rows.append(dict(id=f['id'],source_packet=f['packet'],normalized_tag=f['normalized_tag'],display_sha256=tag,work=reader.work(),scanout_plus_checks_ms=elapsed))
  cases.append(dict(scene=case['scene'],rows=rows));assert pins()==before;print(json.dumps(dict(scene=case['scene'],frames=len(rows))),flush=True)
 rows=[r for c in cases for r in c['rows']];summary=dict(frames=len(rows),lines=sum(r['work']['lines'] for r in rows),exact_RGB565_words=sum(r['work']['RGB565_words_written'] for r in rows),exact_HUD_words=sum(r['work']['HUD_word_reads'] for r in rows),YUV_input_bytes=sum(r['work']['Y_unique_input_bytes']+r['work']['chroma_unique_input_bytes'] for r in rows),mean_scanout_plus_checks_ms=sum(r['scanout_plus_checks_ms'] for r in rows)/len(rows))
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-yuv-scanout-v52',source_sha256=before,cases=cases,summary=summary,scope=['96actualdecodedCS38framesfromfirst24×4v40cohorts,not96hardwarecaptures.','Exactnormativehorizontal-then-verticalchromaaveraging/clamp,integercolorandRGB565HUD.','Generatorholds2rawchromarows/planeandoneoutputline;fullYUV/HUDinputsarecallerownedexternalmodels.','Logicalnative3,600BlinecacheexcludesPythonint32temporaries,inputreference/HUD,validation,registers/CDC/FIFOs/clocking.','Timedlinegenerationincludesassertions/hash,excludesdecode/inputconversion;notpairedunprofiledscanoutorphysicalFPS.','NoRTL,memorycontrollerorpaneltimingimplementation.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
