"""Integrated one-tile receive against direct full-array CS38; paired full calls."""
from pathlib import Path
import hashlib,json,statistics,time
import numpy as np
import receiver as stream
h=stream.h;HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
# The frozen direct module expects its own helpers, restored after import.
import sys
previous=sys.modules.get('helpers')
try:
 sys.modules['helpers']=h.old;direct=h.module('stream48_frozen_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if previous is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=previous

def digest(b):return hashlib.sha256(b).hexdigest()
def pins():
 paths={ROOT/p for p in h.old.old.pins()};paths|={HERE/n for n in('helpers.py','envelope.py','receiver.py','benchmark.py','test_receiver.py')};paths|={HERE.parent/'python-game-direct-rx-v43-study/helpers.py',HERE.parent/'python-game-direct-rx-v43-study/receiver.py',HERE.parent/'python-game-block-rx-v44-study/decoder.py',HERE.parent/'python-game-block-rx-v44-study/results.json',HERE.parent/'python-game-symmetric-inverse-v45-study/model.py',HERE.parent/'python-game-symmetric-inverse-v45-study/results.json'}
 for folder in h.old.FOLDERS:
  path=HERE.parent/folder/'results.json';d=h.load(path);paths.add(path);paths|={ROOT/p for p in d.get('source_sha256',d.get('source_pins_sha256',{}))}
 return{p.relative_to(ROOT).as_posix():h.sha(p) for p in sorted(paths)}
def fork(old,kind):
 new=stream.Receiver() if kind=='stream' else direct.Receiver();new.ref,new.rid,new.hud,new.last=old.ref,old.rid,old.hud,old.last;return new

def main():
 before=pins();cases=[];target=HERE/'results.json'
 for foldername in h.old.FOLDERS:
  folder=HERE.parent/foldername;data=h.load(folder/'results.json')
  for case in data['cases']:
   states=dict(stream=stream.Receiver(),direct=direct.Receiver());rows=[]
   for source in case['rows']:
    packet=h.raw(source['packet'],folder);timings=dict(stream=[],direct=[]);orders=[]
    for rep in range(3):
     order=['direct','stream'] if (source['id']+rep)%2==0 else ['stream','direct'];orders.append(order);copies={k:fork(v,k) for k,v in states.items()};out={}
     for kind in order:
      started=time.perf_counter_ns();out[kind]=copies[kind].receive(packet);timings[kind].append((time.perf_counter_ns()-started)/1e6)
     a,pa,ma,_=out['stream'];b,pb,mb,_=out['direct']
     for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y)
     for x,y in zip(pa,pb,strict=True):np.testing.assert_array_equal(x['words'],y['words'])
     for coeff,tag in zip(mb['coefficients'],ma['coefficient_sha256'],strict=True):assert digest(coeff.astype('<i2').tobytes())==tag
     assert h.m.C.reference_tag(a).hex()==source['normalized_tag'];accepted=copies;accepted_meta=ma
    states=accepted
    display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in pa));assert h.f.f.n.digest(display)==source['display_sha256']
    rows.append(dict(id=source['id'],source_packet=source['packet'],source_folder=foldername,source_packet_sha256=digest(packet),normalized_tag=source['normalized_tag'],display_sha256=source['display_sha256'],coefficient_sha256=accepted_meta['coefficient_sha256'],paired_timing_ms=timings,paired_order=orders,paired_median_ms={k:statistics.median(v) for k,v in timings.items()},decode_work=accepted_meta['decode_work']))
    if source['id']%24==0:print(json.dumps(dict(cohort=foldername,scene=case['scene'],frame=source['id'],paired_median_ms=rows[-1]['paired_median_ms'])),flush=True)
   cases.append(dict(source_folder=foldername,scene=case['scene'],rows=rows));assert pins()==before
   target.write_text(json.dumps(dict(schema='gamebub-stream-rx-v48',source_sha256=before,cases=cases,complete=False),indent=2)+'\n')
 allrows=[r for c in cases for r in c['rows']];summary=dict(frames=len(allrows),coefficient_tiles=sum(p['blocks'] for r in allrows for p in r['decode_work']['planes']),coefficient_tiles_decoded=sum(p['consumed_blocks'] for r in allrows for p in r['decode_work']['planes']),mean_direct_receive_ms=statistics.mean(r['paired_median_ms']['direct'] for r in allrows),mean_stream_receive_ms=statistics.mean(r['paired_median_ms']['stream'] for r in allrows),all_exact_coefficients_refs_HUD_display=True)
 assert len(allrows)==577
 target.write_text(json.dumps(dict(schema='gamebub-stream-rx-v48',source_sha256=before,cases=cases,complete=True,summary=summary,scope=['Arithmetic-onlycapabilitydispatch5/6;rejectlegallegacy0..4ratherthanclaimfullCS38compatibility.','Fullreference,reconstructionandnormalizedYUVplanesremainexternal-memorymodels;notwholelocalmemoryfit.','Noarraycoefficientdecoder/fullpredictionplanes;onecoefficienttileplusQ14/predictiontiles,alllatevalidationbeforeatomicpublication.','3alternatingpairedwholecalls;nofasterPythonclaimunlessactualmeasured.','NoRTL,cycles,routedclock,network,QSPI/displayorphysical30fpsproof.']),indent=2)+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
