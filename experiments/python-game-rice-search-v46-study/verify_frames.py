"""Independent complete CS38 winner/causal-state replay, no new encoder import."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];BASE=HERE.parent/'python-game-binary-v38-study';SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=mod('helpers',BASE/'helpers.py');adapter=mod('rice46_independent_frame_adapter',BASE/'frame_verify.py')
def main():
 d=h.load(HERE/'frames.json');search=h.load(HERE/'results.json');prior=h.load(SOURCE/'results.json');frames=oldbytes=newbytes=0
 for p,v in d['source_sha256'].items():assert h.sha(ROOT/p)==v,p
 for case,s,oldcase in zip(d['cases'],search['cases'],prior['cases'],strict=True):
  assert case['scene']==s['scene']==oldcase['scene'];a=adapter.Receiver();b=adapter.Receiver();rows=0;before=after=0
  for r,c,old in zip(case['rows'],s['rows'],oldcase['rows'][:6],strict=True):
   assert r['id']==c['id']==old['id'];original=h.raw(old['packet'],SOURCE);wire=h.raw(r['packet'],HERE);assert r['source_packet']==old['packet'];O=h.f.HEADER;outer=O.unpack_from(original);got=O.unpack_from(wire);assert outer[:11]==got[:11] and outer[12]==got[12]
   ib=original[O.size:O.size+outer[11]];nb=wire[O.size:O.size+got[11]];fields=h.f.m.HEADER.unpack_from(ib);newfields=h.f.m.HEADER.unpack_from(nb);assert fields[:14]==newfields[:14];offset=h.f.m.HEADER.size+fields[12]+fields[13];assert ib[h.f.m.HEADER.size:offset]==nb[h.f.m.HEADER.size:offset];pos=offset;npos=offset
   for axis,(p,size,ng,w) in enumerate(zip(c['planes'],fields[14:17],newfields[14:17],r['planes'],strict=True)):
    previous=ib[pos:pos+size];pos+=size;options=[previous]+[bytes([6 if t['compact'] else 5])+h.raw(t['packet'],HERE) for t in p['alternatives']];selected=min(range(len(options)),key=lambda i:len(options[i]));assert w==dict(plane=axis,option_bytes=list(map(len,options)),selected=selected);assert nb[npos:npos+ng]==options[selected];npos+=ng
   assert pos==len(ib)-4 and npos==len(nb)-4 and original[O.size+outer[11]:-4]==wire[O.size+got[11]:-4]
   x,hx,mx,_=a.receive(wire);y,hy,my,_=b.receive(original)
   for u,v in zip(x,y,strict=True):np.testing.assert_array_equal(u,v)
   for u,v in zip(mx['coefficients'],my['coefficients'],strict=True):np.testing.assert_array_equal(u,v)
   for u,v in zip(hx,hy,strict=True):np.testing.assert_array_equal(u['words'],v['words'])
   assert r['source_quality']==old['quality'];assert h.f.m.C.reference_tag(x).hex()==r['normalized_tag']==old['normalized_tag'];assert r['old_complete_bytes']==len(original) and r['complete_bytes']==len(wire)<=len(original)<=49152 and r['bytes_saved']==len(original)-len(wire)
   before+=len(original);after+=len(wire);rows+=1
  assert case['summary']==dict(frames=rows,old_complete_bytes=before,complete_bytes=after,bytes_saved=before-after);frames+=rows;oldbytes+=before;newbytes+=after
 assert d['summary']==dict(frames=frames,old_complete_bytes=oldbytes,complete_bytes=newbytes,bytes_saved=oldbytes-newbytes)
 print(json.dumps(dict(causal_complete_frames=frames,old_complete_bytes=oldbytes,complete_bytes=newbytes,bytes_saved=oldbytes-newbytes,percent_saved=100*(oldbytes-newbytes)/oldbytes,all_exact_coefficients_refs_HUD_quality=True,actual_fallbacks_and_ties_checked=True,new_encoder_imported=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
