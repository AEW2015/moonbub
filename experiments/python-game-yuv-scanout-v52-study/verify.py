"""Independent frozen whole-frame color oracle versus line/cache ownership."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import model as subject
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=mod('scan52_verify_direct43_helpers',HERE.parent/'python-game-direct-rx-v43-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;decoder=mod('scan52_verify_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 d=h.load(HERE/'results.json');sources=h.load(SOURCE/'results.json');frames=lines=words=HUD=YUV=0
 for p,s in d['source_sha256'].items():assert h.sha(ROOT/p)==s,p
 for c,source in zip(d['cases'],sources['cases'],strict=True):
  assert c['scene']==source['scene'] and len(c['rows'])==24;rx=decoder.Receiver()
  for r,f in zip(c['rows'],source['rows'][:24],strict=True):
   assert r['id']==f['id'] and r['source_packet']==f['packet'];out,patches,meta,_=rx.receive(h.raw(f['packet'],SOURCE));planes=tuple(x.astype(np.uint8) for x in out)
   for p in planes:p.setflags(write=False)
   golden=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out)),tuple(p['words'] for p in patches));scan=subject.Scanout(planes,patches,h.f.f.n.RECTS);hasher=hashlib.sha256();previous_line=None;previous_copy=None
   for y,line in enumerate(scan):
    if previous_line is not None:np.testing.assert_array_equal(previous_line,previous_copy)
    np.testing.assert_array_equal(line,golden[y]);assert line.shape==(720,) and line.dtype==np.uint16;assert all(not np.shares_memory(line,p) for p in planes);hasher.update(line.astype('<u2',copy=False).tobytes());previous_line=line;previous_copy=line.copy()
    for cache in(scan.cb,scan.cr):assert len(cache.cache)<=2 and all(a.shape==(360,) and a.dtype==np.uint8 for a in cache.cache.values())
   assert hasher.hexdigest()==r['display_sha256']==f['display_sha256'];assert h.m.C.reference_tag(out).hex()==r['normalized_tag']==f['normalized_tag'];assert scan.work()==r['work'];w=r['work'];assert w['lines']==480 and w['Cb_row_loads']==w['Cr_row_loads']==240 and w['Y_unique_input_bytes']==345600 and w['chroma_unique_input_bytes']==172800 and w['HUD_word_reads']==21120 and w['RGB565_words_written']==345600 and not w['retained_full_RGB_frame'];frames+=1;lines+=480;words+=345600;HUD+=21120;YUV+=518400
 s=d['summary'];assert(s['frames'],s['lines'],s['exact_RGB565_words'],s['exact_HUD_words'],s['YUV_input_bytes'])==(frames,lines,words,HUD,YUV);assert frames==96
 print(json.dumps(dict(frames=frames,lines=lines,exact_RGB565_words=words,exact_HUD_words=HUD,logical_YUV_scan_read_bytes=YUV,no_retained_full_RGB_frame=True,owned_line_outputs=True,encoder_imported=False,FPGA_line_cache_fit_or_scanout_timing_proven=False)))
if __name__=='__main__':main()
