#!/usr/bin/env python3
"""Replay real CP25/JA25 and every rejected inner candidate."""
from pathlib import Path
import json
import numpy as np
import benchmark as p
HERE=Path(__file__).resolve().parent

def check_sources(data):
 for path,digest in data['source_sha256'].items():assert p.n.sha(p.ROOT/path)==digest,path
 assert data['counts']==dict(unique_source_frames=96,selected_packets=192)
 assert len(data['cases'])==4

def replay(data):
 old=p.n.load(p.n.V24/'results.json');packets=rejected=0
 for case in data['cases']:
  receiver=p.m.Receiver(epoch=25);source=next(x for x in old['inputs'] if x['scene']==case['scene']);refid=p.m.NO_REF;slot=0;hudid=p.m.NO_REF
  assert case['profile'] in p.PROFILES and case['policy']==p.PROFILES[case['profile']]
  assert [r['id'] for r in case['rows']]==list(range(48))
  assert [r['id'] for r in case['rows'] if r['key']]==[0,24]
  for row,original in zip(case['rows'],source['rows']):
   key=row['key'];expectedref=p.m.NO_REF if key else refid
   assert row['reference_id']==expectedref and row['hud_reference_id']==(p.m.NO_REF if key else hudid)
   assert row['source_slot']==(255 if key else slot)
   dest=0 if key else 1-slot;assert row['destination_slot']==dest and row['publish'] is True
   pair=p.n.raw(row['packet'],HERE);base=p.n.raw(row['base_packet'],HERE);hud=p.n.raw(row['hud_packet'],HERE)
   assert len(pair)==len(base)+len(hud)+60==row['body_bytes']<=p.m.CAP
   parsed=p.m.parse_pair(pair);assert parsed['base']==base and parsed['hud']==hud
   before=None if key else receiver.banks[slot].planes
   assert row['attempts'][0]['background']==16
   for i,a in enumerate(row['attempts']):
    candidate=p.n.raw(a['packet'],HERE);assert len(candidate)==a['base_bytes']
    assert a['complete_bytes']==len(candidate)+len(hud)+60
    assert a['admitted']==(a['complete_bytes']<=p.m.CAP)
    if not a['admitted']:assert i==0 and a['background']==16;rejected+=1
    output,meta=p.b.decode(candidate,before,expected_epoch=25,expected_reference_id=None if key else expectedref)
    np.testing.assert_array_equal(meta['scale_map'],p.b.roi.declared_map(720,480,p.n.ROIS,8,a['background']))
    assert a['work']['rdo']['lambda_value']==(0 if key else case['policy']['lam'])
   assert row['attempts'][-1]['admitted'] and p.n.raw(row['attempts'][-1]['packet'],HERE)==base
   assert row['selected_background']==row['attempts'][-1]['background']
   assert row['work']['encoder_wall_ms']==row['analysis_wall_ms']+sum(a['encode_wall_ms'] for a in row['attempts'])
   assert row['work']['forward_plane_calls']==3 and row['work']['capped_attempts']==len(row['attempts'])
   decoded,patches,ack=receiver.receive(pair);assert ack==p.n.raw(row['ack'],HERE)
   assert p.m.validate_ack(ack,pair)==row['ack_meta']
   orig=p.n.original(original);bare=p.b.C.corpus.rgb565(p.b.ft.planes_to_rgb(decoded));hybrid=p.n.overlay(bare,tuple(x['words'] for x in patches))
   assert p.n.digest(bare)==row['bare_rgb565_sha256'] and p.n.digest(hybrid)==row['hybrid_rgb565_sha256']
   assert p.n.metric(orig,bare)==row['bare'] and p.n.metric(orig,hybrid)==row['hybrid'] and not row['hybrid']['hud_word_errors']
   assert row['source_input_sha256']==original['input_rgb_sha256'] and row['source_common_yuv_sha256']==original['common_yuv420_u8_sha256']
   refid,hudid,slot=row['id'],row['id'],dest;packets+=1
  assert p.n.summarize(case['rows'])==case['summary']
  assert case['joint_summary']['cap_fit_frames']==48
  assert sum(r['body_bytes'] for r in case['rows'])==case['joint_summary']['complete_bytes']
 assert packets==192
 return dict(selected_pairs=packets,rejected_fine_packets_replayed=rejected,exact_hud_words=192*21120,all_complete_caps_checked=True,all_ACKs_checked=True,hardware_fps_proven=False)

def main():
 data=json.loads((HERE/'results.json').read_text());check_sources(data);print(json.dumps(replay(data),indent=2))
if __name__=='__main__':main()
