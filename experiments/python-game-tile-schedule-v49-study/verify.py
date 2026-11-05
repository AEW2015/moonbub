"""Independent archived-tile coefficient/counter/work-demand replay."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
import reader
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=mod('tile49_verify_stream48_helpers',HERE.parent/'python-game-stream-rx-v48-study/helpers.py');before=sys.modules.get('helpers')
try:sys.modules['helpers']=h;envelope=mod('tile49_verify_envelope48',HERE.parent/'python-game-stream-rx-v48-study/envelope.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def digest(b):return hashlib.sha256(b).hexdigest()
def raw(desc):
 p=Path(desc['path']);assert not p.is_absolute() and '..' not in p.parts;stored=(HERE/p).read_bytes();assert digest(stored)==desc['stored_sha256'];d=zlib.decompressobj();b=d.decompress(stored,desc['raw_bytes']+1);assert d.eof and not d.unused_data and not d.unconsumed_tail and len(b)==desc['raw_bytes'] and digest(b)==desc['raw_sha256'];return b

def main():
 d=h.load(HERE/'results.json');src=h.load(SOURCE/'results.json');totals={k:0 for k in d['summary']}
 for p,s in d['source_sha256'].items():assert h.sha(ROOT/p)==s,p
 for case,source in zip(d['cases'],src['cases'],strict=True):
  assert case['scene']==source['scene'] and len(case['rows'])==24
  for f,old in zip(case['rows'],source['rows'][:24],strict=True):
   assert f['id']==old['id'] and f['source_packet']==old['packet'] and f['complete_bytes']==old['complete_bytes'];meta=envelope.parse_envelope(h.raw(old['packet'],SOURCE));totals['frames']+=1
   for axis,(p,payload,safe,attempt) in enumerate(zip(f['planes'],meta['plane_payloads'],h.f.f.safe_blocks(),old['attempts'],strict=True)):
    mask=safe.reshape(-1);bw=90 if axis==0 else 45;n=int((~mask).sum()) if payload[0]==6 else len(mask);ab=payload[1:];gold=reader.frozen.decode(ab,n,1 if payload[0]==6 else bw);e=reader.TileReader(ab,n,1 if payload[0]==6 else bw);late=reader.TileReader(ab,n,1 if payload[0]==6 else bw,deferred=True);trace=np.frombuffer(raw(p['trace']),'<u4').reshape(len(mask),21);assert p['blocks']==len(mask) and p['decoded_blocks']==n and p['dispatch']==payload[0]
    tables=h.m.roi.block_tables(meta['qmap'],720,480,axis);prev_e=np.zeros((4,2),np.int64);prev_l=prev_e.copy();consumed=0;hashes=hashlib.sha256()
    for i,row in enumerate(trace):
     take=payload[0]==5 or not mask[i]
     if take:a=next(e);b=next(late);np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,gold[consumed]);consumed+=1
     else:a=np.zeros((8,8),np.int16)
     ce=np.asarray(e.counters(),np.int64);cl=np.asarray(late.counters(),np.int64);np.testing.assert_array_equal(row[:8],(ce-prev_e).reshape(-1));np.testing.assert_array_equal(row[8:16],(cl-prev_l).reshape(-1));prev_e=ce;prev_l=cl;assert row[19]==take
     hashes.update(a.astype('<i2').tobytes());a=a.astype(np.int64)*tables[i];nz=int(np.count_nonzero(a));assert row[20]==nz
     if nz==0:expected=(0,0,0)
     elif nz==1 and a[0,0]:expected=(1,1,1)
     else:mid=(a@h.sym.ft.Q14+8192)>>14;expected=(4*nz,4*int(np.count_nonzero(mid)),2)
     assert tuple(row[16:19])==expected
    assert consumed==n and e.finished and late.finished and e.counters()==late.counters();assert tuple(tuple(v) for v in p['stream_totals'])==e.counters();assert hashes.hexdigest()==p['coefficient_sha256']
    selected=attempt['trials'][attempt['selected']-1]
    for j,expected in enumerate(selected['work']['streams']):assert e.counters()[j]==(expected['binary_decisions'],expected['renorm_steps'])
    assert p['maximum_eager_tile_decisions']==int(trace[:,0:8:2].sum(axis=1).max()) and p['maximum_deferred_tile_decisions']==int(trace[:,8:16:2].sum(axis=1).max())
    totals['planes']+=1;totals['tiles']+=len(mask);totals['arithmetically_decoded_tiles']+=n;totals['probability_products']+=int(trace[:,0:8:2].sum());totals['renorm_steps']+=int(trace[:,1:8:2].sum());totals['first_products']+=int(trace[:,16].sum());totals['second_products']+=int(trace[:,17].sum());totals['dequant_products']+=int(trace[:,20].sum())
 assert totals==d['summary'];print(json.dumps(dict(**totals,all_actual_coefficients_and_per_tile_counters_exact=True,final_eager_deferred_arithmetic_work_equal=True,encoder_imported=False,cycle_accurate_RTL_or_physical_FPS_proven=False)))
if __name__=='__main__':main()
