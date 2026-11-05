"""Replay all457 canonical outputs into independent ordered hash components."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
# Reuse the frozen67 qualification's scoped legacy decoder only, not its results.
h=module('hash67_qual_helpers',HERE.parent/'python-game-filter-qual-v67-study/helpers.py')
model=module('hash67_owned_tilehash',HERE/'model.py')

def pins():
 p={ROOT/k for k in h.pins()};p|={HERE/n for n in ('model.py','benchmark.py','test_model.py')}
 return {f.relative_to(ROOT).as_posix():h.sha(f) for f in sorted(p)}

def main():
 before=pins();cases=[]
 for case in h.load(h.PACKETS/'results.json')['cases']:
  rx=h.direct.Receiver();rows=[]
  for old in case['rows']:
   canonical,patches,meta,_=rx.receive(h.raw(old['packet'],h.PACKETS))
   assert h.h.m.C.reference_tag(canonical).hex()==old['normalized_tag']
   assert all(p.dtype.kind in ('i','u') and np.all(p>=0) and np.all(p<=255) for p in canonical)
   planes=tuple(p.astype(np.uint8) for p in canonical)
   for p in planes:p.setflags(write=False)
   subjects={d:model.TileHash(d) for d in model.DOMAINS};pauses=0
   for axis,plane in enumerate(planes):
    for y in range(0,plane.shape[0],8):
     for x in range(0,plane.shape[1],8):
      tile=plane[y:y+8,x:x+8]
      for s in subjects.values():
       s.feed(axis,y,x,tile)
       assert s.strip is None or s.strip.nbytes<=5760
      if (y//8+x//8+axis)%19==0:
       for s in subjects.values():
        before_work=s.work();assert s.work()==before_work
       pauses+=1
   full_u8=hashlib.sha256(__import__('struct').pack('<HH',720,480)+b''.join(p.tobytes() for p in planes)).digest()[:16]
   expected={'CS66_i16':bytes.fromhex(old['normalized_tag']),'CU66_u8':full_u8}
   domains={}
   for domain,s in subjects.items():
    tag=s.finish();assert tag==expected[domain] and s.finish()==tag
    work=s.work();assert work['tiles']==8100 and work['canonical_samples']==518400 and work['rows_serialized']==960
    assert work['serialized_bytes']==(1036804 if domain=='CS66_i16' else 518404)
    assert work['maximum_strip_data_bytes']==5760 and work['retained_strip_data_bytes']==0
    domains[domain]=dict(tag=tag.hex(),work=work)
   assert h.h.m.C.reference_tag(canonical).hex()==old['normalized_tag']
   rows.append(dict(id=old['id'],key=meta['key'],source_packet=old['packet'],domains=domains,deterministic_pause_checks=pauses))
  cases.append(dict(scene=case['scene'],rows=rows));print(json.dumps(dict(scene=case['scene'],frames=len(rows))),flush=True)
 assert pins()==before
 frames=sum(len(c['rows']) for c in cases)
 result=dict(schema='gamebub-hash-stream-v67',source_sha256=before,cases=cases,
  summary=dict(causal_source_frames=frames,domain_results=2*frames,tiles_per_domain=8100*frames,canonical_samples_per_domain=518400*frames,
   maximum_strip_data_bytes=5760,maximum_transient_serialized_row_bytes={'CS66_i16':1440,'CU66_u8':720},
   deterministic_pause_checks=sum(r['deterministic_pause_checks'] for c in cases for r in c['rows'])),
  scope=['Orderednormalizeduint8tileinput is reformattedintoexactcanonicalplanarroworder foroneSHA256[:16]context/frame.',
         'One8×widthuint8strip(max5760Blogicaldata);transientserializedrow(max1440/720B),SHAcontext/padding/control/ports/CDCexcludedfromstripbound.',
         'Fullcanonicalplanes areexternalinput/oraclemodels,notownedbyTileHash;noadditionalfulloutputplaneincomponent.',
         'Callerchecksfinalexpectedtagandpublishesbankafterwholeframe/HUDvalidation;thiscomponentdoesnotimplementbankfences.',
         'Pythonpullfeed/pauseandpoisoncontract,notRTLreadyvalid/stall/clock/SHAcore/throughput/BRAMfitproof.',
         'Noencodedbytes/sourcequalitychangesandnonewcompressionclaim.'])
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
