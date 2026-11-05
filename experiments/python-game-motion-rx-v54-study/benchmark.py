"""Actual nonzero/mixed/fractional motion through tiled48 and direct43 receivers."""
from pathlib import Path
import hashlib,json,statistics,sys,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-stream-rx-v48-study'));import receiver as stream
h=stream.h;before=sys.modules.get('helpers')
try:sys.modules['helpers']=h.old;direct=h.module('motionrx54_frozen_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def pins():
 paths={ROOT/p for p in h.old.old.pins()};paths|={HERE/'benchmark.py',HERE/'fractional.py',HERE/'fractional.json',HERE.parent/'python-game-stream-rx-v48-study/receiver.py',HERE.parent/'python-game-stream-rx-v48-study/envelope.py',HERE.parent/'python-game-stream-rx-v48-study/helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py',HERE.parent/'python-game-direct-rx-v43-study/helpers.py',HERE.parent/'python-game-block-rx-v44-study/decoder.py',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py'}
 for folder in('python-game-motion-v47-study','python-game-quantized-motion-v53-study'):
  p=HERE.parent/folder/'results.json';d=h.load(p);paths.add(p);paths|={ROOT/p for p in d['source_sha256']}
 return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def cases():
 result=[]
 for folder in('python-game-motion-v47-study','python-game-quantized-motion-v53-study'):
  for c in h.load(HERE.parent/folder/'results.json')['cases']:
   if folder.endswith('v47-study') and c['policy']!='global_grid':continue
   result.append(dict(source_folder=folder,scene=c['scene'],rows=c['rows']))
 fixture=h.load(HERE/'fractional.json');result.append(dict(source_folder=HERE.name,scene='directed_fractional6',rows=fixture['rows']));return result

def fork(old,kind):
 rx=stream.Receiver() if kind=='stream' else direct.Receiver();rx.ref,rx.rid,rx.hud,rx.last=old.ref,old.rid,old.hud,old.last;return rx

def main():
 before=pins();result=[]
 for case in cases():
  states=dict(stream=stream.Receiver(),direct=direct.Receiver());rows=[];folder=HERE.parent/case['source_folder']
  for source in case['rows']:
   packet=h.raw(source['packet'],folder);timings=dict(stream=[],direct=[]);orders=[]
   for rep in range(3):
    order=['direct','stream'] if(source['id']+rep)%2==0 else ['stream','direct'];orders.append(order);forks={k:fork(v,k) for k,v in states.items()};out={}
    for kind in order:
     start=time.perf_counter_ns();out[kind]=forks[kind].receive(packet);timings[kind].append((time.perf_counter_ns()-start)/1e6)
    a,pa,ma,_=out['stream'];b,pb,mb,_=out['direct']
    for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
    for x,y in zip(pa,pb,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
    for c,tag in zip(mb['coefficients'],ma['coefficient_sha256'],strict=True):assert h.digest(c.astype('<i2').tobytes())==tag
    accepted=forks;ameta=ma;bmeta=mb
   states=accepted;assert h.m.C.reference_tag(a).hex()==source['normalized_tag'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in pa));assert h.f.f.n.digest(display)==source['display_sha256']
   vectors=bmeta['vectors'];rows.append(dict(id=source['id'],source_packet=source['packet'],source_packet_sha256=h.digest(packet),normalized_tag=source['normalized_tag'],display_sha256=source['display_sha256'],coefficient_sha256=ameta['coefficient_sha256'],paired_timing_ms=timings,paired_order=orders,paired_median_ms={k:statistics.median(v) for k,v in timings.items()},nonzero_vectors=int(np.any(vectors,axis=2).sum()),fractional_luma_vectors=int(np.any(vectors%2,axis=2).sum()),fractional_chroma_vectors=int(np.any(vectors%4,axis=2).sum()),block_size=bmeta['block_size'],decode_work=ameta['decode_work']))
   if source['id']%8==0:print(json.dumps(dict(folder=case['source_folder'],scene=case['scene'],frame=source['id'],nonzero=rows[-1]['nonzero_vectors'])),flush=True)
  result.append(dict(source_folder=case['source_folder'],scene=case['scene'],rows=rows));assert pins()==before;(HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-motion-rx-v54',source_sha256=before,cases=result,complete=False),indent=2)+'\n')
 rows=[r for c in result for r in c['rows']];summary=dict(frames=len(rows),histories=len(result),frames_with_nonzero_vectors=sum(r['nonzero_vectors']>0 for r in rows),nonzero_vectors=sum(r['nonzero_vectors'] for r in rows),fractional_luma_vectors=sum(r['fractional_luma_vectors'] for r in rows),fractional_chroma_vectors=sum(r['fractional_chroma_vectors'] for r in rows),mean_direct_receive_ms=statistics.mean(r['paired_median_ms']['direct'] for r in rows),mean_stream_receive_ms=statistics.mean(r['paired_median_ms']['stream'] for r in rows),all_exact_coefficients_refs_HUD_display=True)
 assert len(rows)==198
 (HERE/'results.json').write_text(json.dumps(dict(schema='gamebub-motion-rx-v54',source_sha256=before,cases=result,complete=True,summary=summary,scope=['96fixedgrid47+96mixed53+6directedfractionalfixtures,nothardwarecaptures.','Frozenstream48anddirect43,3alternatingwholecalls;allcoefficients,references,HUD,display,stateexact.','FractionalfixturesactualCS37coefficientsrecodedtoforcedAB38;all36alternativesretained.','Pythonruntimeisdiagnostic;noFPGAfit,ports,routedclock,physicalFPSornewcodecqualityproof.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
