"""Independent complete-frame oracle replay and integrated tile work checks."""
from pathlib import Path
import hashlib,json,statistics,sys
import numpy as np
import receiver as subject
h=subject.h;HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
previous=sys.modules.get('helpers')
try:
 sys.modules['helpers']=h.old;oracle=h.module('stream48_verify_direct43_oracle',HERE.parent/'python-game-direct-rx-v43-study/receiver.py')
finally:
 if previous is None:sys.modules.pop('helpers',None)
 else:sys.modules['helpers']=previous

def digest(b):return hashlib.sha256(b).hexdigest()
def predicted_fetches(vectors,bs,axis,key):
 if key:return 0
 ph,pw=((480,720) if axis==0 else (240,360));block=bs if axis==0 else bs//2;den=2 if axis==0 else 4;total=0
 for my in range(vectors.shape[0]):
  for mx in range(vectors.shape[1]):
   width=min(block,pw-mx*block);height=min(block,ph-my*block);x,y=map(int,vectors[my,mx]);total+=width*height*(1+bool(x%den))*(1+bool(y%den))
 return total

def main():
 d=h.load(HERE/'results.json');assert d['complete'] and d['schema']=='gamebub-stream-rx-v48'
 for p,v in d['source_sha256'].items():assert h.sha(ROOT/p)==v,p
 expected=[]
 for foldername in h.old.FOLDERS:
  src=h.load(HERE.parent/foldername/'results.json')
  for c in src['cases']:expected.append((foldername,c))
 assert len(d['cases'])==len(expected)==8;frames=tiles=consumed=0;dr=[];sr=[]
 for case,(foldername,source) in zip(d['cases'],expected,strict=True):
  assert case['source_folder']==foldername and case['scene']==source['scene'];rx=subject.Receiver();old=oracle.Receiver()
  for row,src in zip(case['rows'],source['rows'],strict=True):
   assert row['id']==src['id'] and row['source_packet']==src['packet'] and row['source_folder']==foldername
   packet=h.raw(src['packet'],HERE.parent/foldername);assert digest(packet)==row['source_packet_sha256'];a,pa,ma,_=rx.receive(packet);b,pb,mb,_=old.receive(packet)
   for x,y in zip(a,b,strict=True):np.testing.assert_array_equal(x,y);assert not x.flags.writeable
   for x,y in zip(pa,pb,strict=True):np.testing.assert_array_equal(x['words'],y['words']);assert not x['words'].flags.writeable
   for axis,(c,tag,pwork) in enumerate(zip(mb['coefficients'],ma['coefficient_sha256'],row['decode_work']['planes'],strict=True)):
    assert digest(c.astype('<i2').tobytes())==tag==row['coefficient_sha256'][axis]
    assert pwork==ma['decode_work']['planes'][axis];assert pwork['blocks']==len(c) and pwork['coefficient_tile_bytes']==128 and not pwork['full_coefficient_array_staged'] and not pwork['full_prediction_array_staged']
    assert pwork['prediction_reference_sample_fetches']==predicted_fetches(mb['vectors'],mb['block_size'],axis,mb['key'])
    safe=h.f.f.safe_blocks()[axis].reshape(-1);visible=int((~safe).sum());assert pwork['consumed_blocks']==(visible if pwork['dispatch']==6 else len(c))
    tables=h.m.roi.block_tables(mb['qmap'],720,480,axis);dequant=c.astype(np.int64)*tables;nonzero=np.count_nonzero(dequant,axis=(1,2));zero=int((nonzero==0).sum());DC=int(((nonzero==1)&(dequant[:,0,0]!=0)).sum());assert pwork['inverse_classes']==dict(zero=zero,DC=DC,complex=len(c)-zero-DC)
    tiles+=len(c);consumed+=pwork['consumed_blocks']
   assert h.m.C.reference_tag(a).hex()==row['normalized_tag']==src['normalized_tag'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(a)),tuple(p['words'] for p in pa));assert h.f.f.n.digest(display)==row['display_sha256']==src['display_sha256']
   assert row['decode_work']['full_coefficient_array_bytes']==row['decode_work']['full_prediction_array_bytes']==row['decode_work']['entropy_reencode_calls']==0
   for rep,order in enumerate(row['paired_order']):assert order==(['direct','stream'] if(row['id']+rep)%2==0 else ['stream','direct'])
   for kind,values in row['paired_timing_ms'].items():assert len(values)==3 and all(x>=0 for x in values) and statistics.median(values)==row['paired_median_ms'][kind]
   frames+=1;dr.append(row['paired_median_ms']['direct']);sr.append(row['paired_median_ms']['stream'])
 s=d['summary'];assert(s['frames'],s['coefficient_tiles'],s['coefficient_tiles_decoded'])==(frames,tiles,consumed);assert s['mean_direct_receive_ms']==statistics.mean(dr) and s['mean_stream_receive_ms']==statistics.mean(sr);assert frames==577
 print(json.dumps(dict(causal_frames=frames,coefficient_tiles_reconstructed=tiles,AB38_tiles_consumed=consumed,all_exact_coefficients_refs_HUD_display=True,full_coefficient_or_prediction_arrays_in_subject=False,readonly_atomically_published_state=True,arithmetic_only_capability=True,encoder_imported=False,FPGA_fit_or_physical30fps_proven=False)))
if __name__=='__main__':main()
