"""Independent direct43 state/counter oracle on actual motion and fixture packets."""
from pathlib import Path
import json,statistics,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'python-game-stream-rx-v48-study'));import receiver as subject
h=subject.h;before=sys.modules.get('helpers')
try:sys.modules['helpers']=h.old;direct=h.module('motionrx54_verify_direct43',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if before is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=before

def main():
 data=h.load(HERE/'results.json');fixture=h.load(HERE/'fractional.json');assert data['complete'] and len(data['cases'])==9
 for artifact in(data,fixture):
  for p,v in artifact['source_sha256'].items():assert h.sha(ROOT/p)==v,p
 # Recompute directed fixture alternatives against old CS37 coefficient/map/HUD.
 source=h.load(ROOT/fixture['source_folder']/'results.json');original=next(c for c in source['cases'] if c['kind']=='fractional_motion');alternatives=0
 for f,oldrow in zip(fixture['rows'],original['rows'],strict=True):
  old=h.f.parse(h.raw(oldrow['packet'],ROOT/fixture['source_folder']));wire=h.raw(f['packet'],HERE);new=direct.parse(wire)
  for field in('frame_id','reference_id','block_size'):assert new[field]==old[field]
  for x,y in zip(new['coefficients'],old['coefficients'],strict=True):np.testing.assert_array_equal(x,y)
  np.testing.assert_array_equal(new['vectors'],old['vectors']);np.testing.assert_array_equal(new['qmap'],old['qmap']);assert new['hud']==old['hud']
  for axis,(a,c,safe,payload) in enumerate(zip(f['attempts'],old['coefficients'],h.f.f.safe_blocks(),new['plane_payloads'],strict=True)):
   options=[]
   for t in a['trials']:
    target=c[~safe.reshape(-1)] if t['compact'] else c;bw=1 if t['compact'] else 90 if axis==0 else 45;ab=h.raw(t['packet'],HERE);decoded=h.block.frozen.decode(ab,len(target),bw);np.testing.assert_array_equal(decoded,target);assert h.digest(target.astype('<i2').tobytes())==t['coefficient_sha256'];options.append(bytes([6 if t['compact'] else 5])+ab);alternatives+=1
   chosen=min(range(2),key=lambda j:len(options[j]));assert chosen==a['selected'] and options[chosen]==payload
 assert alternatives==36
 frames=nonzero_frames=nonzero=fracY=fracUV=0;direct_ms=[];stream_ms=[]
 for case in data['cases']:
  folder=HERE.parent/case['source_folder']
  if folder==HERE:source_rows=fixture['rows']
  else:
   source=h.load(folder/'results.json');matches=[c for c in source['cases'] if c['scene']==case['scene'] and c.get('policy','global_grid')=='global_grid'];assert len(matches)==1;source_rows=matches[0]['rows']
  assert len(source_rows)==len(case['rows']);a=subject.Receiver();b=direct.Receiver()
  for r,f in zip(case['rows'],source_rows,strict=True):
   assert r['id']==f['id'] and r['source_packet']==f['packet'];packet=h.raw(f['packet'],folder);assert h.digest(packet)==r['source_packet_sha256'];x,px,mx,_=a.receive(packet);y,py,my,_=b.receive(packet)
   for u,v in zip(x,y,strict=True):np.testing.assert_array_equal(u,v)
   for u,v in zip(px,py,strict=True):np.testing.assert_array_equal(u['words'],v['words'])
   for c,tag in zip(my['coefficients'],mx['coefficient_sha256'],strict=True):assert h.digest(c.astype('<i2').tobytes())==tag
   assert mx['coefficient_sha256']==r['coefficient_sha256'];assert h.m.C.reference_tag(x).hex()==r['normalized_tag']==f['normalized_tag'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(x)),tuple(p['words'] for p in px));assert h.f.f.n.digest(display)==r['display_sha256']==f['display_sha256']
   v=my['vectors'];nz=int(np.any(v,axis=2).sum());fy=int(np.any(v%2,axis=2).sum());fc=int(np.any(v%4,axis=2).sum());assert(nz,fy,fc,my['block_size'])==(r['nonzero_vectors'],r['fractional_luma_vectors'],r['fractional_chroma_vectors'],r['block_size']);nonzero_frames+=nz>0;nonzero+=nz;fracY+=fy;fracUV+=fc
   for rep,order in enumerate(r['paired_order']):assert order==(['direct','stream'] if(r['id']+rep)%2==0 else ['stream','direct'])
   for kind,times in r['paired_timing_ms'].items():assert len(times)==3 and all(t>=0 for t in times) and statistics.median(times)==r['paired_median_ms'][kind]
   direct_ms.append(r['paired_median_ms']['direct']);stream_ms.append(r['paired_median_ms']['stream']);frames+=1
 summary=dict(frames=frames,histories=9,frames_with_nonzero_vectors=nonzero_frames,nonzero_vectors=nonzero,fractional_luma_vectors=fracY,fractional_chroma_vectors=fracUV,mean_direct_receive_ms=statistics.mean(direct_ms),mean_stream_receive_ms=statistics.mean(stream_ms),all_exact_coefficients_refs_HUD_display=True);assert summary==data['summary'] and frames==198
 print(json.dumps(dict(**summary,directed_fractional_AB38_alternatives=alternatives,encoding_called=False,target_motion_ports_or_FPS_proven=False)))
if __name__=='__main__':main()
