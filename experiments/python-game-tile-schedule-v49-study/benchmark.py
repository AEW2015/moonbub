"""Actual per-tile arithmetic demand, eager versus deferred AC-level prefetch."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
import reader
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);return v
h=module('tile49_frozen_stream48_helpers',HERE.parent/'python-game-stream-rx-v48-study/helpers.py')
previous=sys.modules.get('helpers')
try:sys.modules['helpers']=h;envelope=module('tile49_envelope48',HERE.parent/'python-game-stream-rx-v48-study/envelope.py')
finally:
 if previous is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=previous

def digest(b):return hashlib.sha256(b).hexdigest()
def blob(b):
 stored=zlib.compress(b,9);p='objects/'+digest(stored)+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/p).write_bytes(stored);return dict(path=p,raw_bytes=len(b),raw_sha256=digest(b),stored_sha256=digest(stored))
def pins():
 source=h.load(SOURCE/'results.json');paths={ROOT/p for p in source['source_pins_sha256']};paths|={SOURCE/'results.json',HERE/'reader.py',HERE/'benchmark.py',HERE/'test_reader.py',HERE.parent/'python-game-stream-rx-v48-study/helpers.py',HERE.parent/'python-game-stream-rx-v48-study/envelope.py',HERE.parent/'python-game-block-rx-v44-study/decoder.py',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py'};return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def main():
 before=pins();source=h.load(SOURCE/'results.json');cases=[];counts=dict(frames=0,planes=0,tiles=0,arithmetically_decoded_tiles=0,probability_products=0,renorm_steps=0,first_products=0,second_products=0,dequant_products=0)
 for case in source['cases']:
  rows=[]
  for frame in case['rows'][:24]:
   packet=h.raw(frame['packet'],SOURCE);meta=envelope.parse_envelope(packet);planes=[]
   for axis,(payload,safe,attempt) in enumerate(zip(meta['plane_payloads'],h.f.f.safe_blocks(),frame['attempts'],strict=True)):
    mask=safe.reshape(-1);bw=90 if axis==0 else 45;n=int((~mask).sum()) if payload[0]==6 else len(mask);ab=payload[1:];gold=reader.frozen.decode(ab,n,1 if payload[0]==6 else bw);e=reader.TileReader(ab,n,1 if payload[0]==6 else bw);d=reader.TileReader(ab,n,1 if payload[0]==6 else bw,deferred=True)
    # Columns: 4*(decisions,renorms) for eager, same8 for deferred,
    # mirrored sparse first/second MAC counts, class(0zero/1DC/2complex), consumed.
    trace=np.zeros((len(mask),21),np.uint32);previous_e=np.zeros((4,2),np.int64);previous_d=previous_e.copy();coefficient_hash=hashlib.sha256();consumed=0
    tables=h.m.roi.block_tables(meta['qmap'],720,480,axis)
    for i in range(len(mask)):
     consume=payload[0]==5 or not mask[i]
     if consume:
      a=next(e);b=next(d);np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,gold[consumed]);consumed+=1
     else:a=np.zeros((8,8),np.int16)
     ce=np.asarray(e.counters(),np.int64);cd=np.asarray(d.counters(),np.int64);trace[i,:8]=(ce-previous_e).reshape(-1);trace[i,8:16]=(cd-previous_d).reshape(-1);previous_e=ce;previous_d=cd;trace[i,19]=consume
     assert not mask[i] or not np.any(a);coefficient_hash.update(a.astype('<i2').tobytes());dequant=a.astype(np.int64)*tables[i];nz=np.count_nonzero(dequant);trace[i,20]=nz
     if nz==0:trace[i,18]=0
     elif nz==1 and dequant[0,0]:trace[i,16:18]=1;trace[i,18]=1
     else:
      mid=(dequant@h.sym.ft.Q14+8192)>>14;trace[i,16]=4*nz;trace[i,17]=4*np.count_nonzero(mid);trace[i,18]=2
    assert e.finished and d.finished and e.counters()==d.counters();assert consumed==n
    selected=attempt['trials'][attempt['selected']-1];assert payload[0]==(6 if selected['compact'] else 5);expected=selected['work']['streams']
    for j,w in enumerate(expected):assert tuple(e.counters()[j])==(w['binary_decisions'],w['renorm_steps'])
    desc=blob(trace.astype('<u4').tobytes());planes.append(dict(plane=axis,dispatch=payload[0],blocks=len(mask),decoded_blocks=n,trace=desc,coefficient_sha256=coefficient_hash.hexdigest(),stream_totals=e.counters(),maximum_eager_tile_decisions=int(trace[:,0:8:2].sum(axis=1).max()),maximum_deferred_tile_decisions=int(trace[:,8:16:2].sum(axis=1).max())))
    counts['planes']+=1;counts['tiles']+=len(mask);counts['arithmetically_decoded_tiles']+=n;counts['probability_products']+=int(trace[:,0:8:2].sum());counts['renorm_steps']+=int(trace[:,1:8:2].sum());counts['first_products']+=int(trace[:,16].sum());counts['second_products']+=int(trace[:,17].sum());counts['dequant_products']+=int(trace[:,20].sum())
   rows.append(dict(id=frame['id'],source_packet=frame['packet'],complete_bytes=frame['complete_bytes'],key=meta['key'],planes=planes));counts['frames']+=1
   if frame['id']%6==0:print(json.dumps(dict(scene=case['scene'],frame=frame['id'],tiles=counts['tiles'])),flush=True)
  cases.append(dict(scene=case['scene'],rows=rows));assert pins()==before
 result=dict(schema='gamebub-tile-schedule-v49-traces',source_sha256=before,cases=cases,summary=counts,trace_columns=['eager stream0 decisions','eager stream0 renorm','eager stream1 decisions','eager stream1 renorm','eager stream2 decisions','eager stream2 renorm','eager stream3 decisions','eager stream3 renorm','deferred stream0 decisions','deferred stream0 renorm','deferred stream1 decisions','deferred stream1 renorm','deferred stream2 decisions','deferred stream2 renorm','deferred stream3 decisions','deferred stream3 renorm','mirrored first-pass sparse products','mirrored second-pass sparse products','inverse class 0zero1DC2complex','AB38 tile consumed','nonzero dequantizer products'],scope=['First24framesofeachv40clip;96actualcausalsourceframes,nothardwarecapture.','SameAB38bytes/coefficients;deferonlyfutureACleveldecodeuntilitsblock,notrunsorfourstreamcontexts.','AllselectedAB38encoderdecision/renormtotalsmatch;per-tileplacementisnewactualPythonalgorithmtrace.','Multiplycountslogicalwithsamezero/DCshortcuts;noDSPmappingorcycle/physicalFPSproof.'])
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(counts),flush=True)
if __name__=='__main__':main()
