#!/usr/bin/env python3
"""Retained packet/reference replay independent of the producer loop."""
from pathlib import Path
import json
import numpy as np
import benchmark as p
HERE=Path(__file__).resolve().parent

def check_sources(data):
 for path,digest in data['source_sha256'].items():assert p.n.sha(p.ROOT/path)==digest,path
 assert data['counts']==dict(unique_source_frames=96,encoded_decoded_packets=288)
 assert len(data['cases'])==6

def check_lineage(data):
 for case in data['cases']:
  assert case['profile'] in p.PROFILES and case['policy']==p.PROFILES[case['profile']]
  assert [r['id'] for r in case['rows']]==list(range(48))
  assert [r['id'] for r in case['rows'] if r['key']]==[0,24]
  refid=p.b.NO_REF;slot=0
  for row in case['rows']:
   if row['key']:refid,slot=p.b.NO_REF,0
   assert row['publish'] is True and row['reference_id']==refid
   assert row['source_slot']==(255 if row['key'] else slot)
   dest=0 if row['key'] else 1-slot;assert row['destination_slot']==dest
   assert row['work']['rdo']['lambda_value']==(0 if row['key'] else case['policy']['lam'])
   assert not row['key'] or row['work']['rdo']['zeroed_blocks']==0
   refid,slot=row['id'],dest

def replay(data):
 old=p.n.load(p.n.V24/'results.json');packets=0;pixels=0
 for case in data['cases']:
  source=next(x for x in old['inputs'] if x['scene']==case['scene']);ref=None
  rebuilt_rows=[]
  for row,origrow in zip(case['rows'],source['rows']):
   key=row['key'];ref=None if key else ref
   assert row['source_input_sha256']==origrow['input_rgb_sha256']
   assert row['source_common_yuv_sha256']==origrow['common_yuv420_u8_sha256']
   packet=p.n.raw(row['base_packet'],HERE);assert len(packet)==row['base_bytes']
   output,meta=p.b.decode(packet,ref,expected_epoch=25,expected_reference_id=None if key else row['reference_id'])
   parsed=p.b.parse(packet,expected_epoch=25)
   mapped=p.b.roi.declared_map(720,480,p.n.ROIS,8,16)
   np.testing.assert_array_equal(parsed['scale_map'],mapped)
   assert meta['reconstructed_tag'].hex()==row['reconstructed_yuv_tag']
   orig=p.n.original(origrow);bare=p.b.C.corpus.rgb565(p.b.ft.planes_to_rgb(output))
   patches=tuple(orig[y:y+h,x:x+w] for x,y,w,h in p.n.RECTS);hybrid=p.n.overlay(bare,patches)
   assert p.n.digest(bare)==row['bare_rgb565_sha256'] and p.n.digest(hybrid)==row['hybrid_rgb565_sha256']
   assert p.n.metric(orig,bare)==row['bare'] and p.n.metric(orig,hybrid)==row['hybrid']
   assert not row['hybrid']['hud_word_errors'];ref=output
   packets+=1;pixels+=720*480
  assert p.n.summarize(case['rows'])==case['summary']
 assert packets==288
 return dict(replayed_packets=packets,verified_pixels=pixels,exact_hud_words=288*21120,keys=[0,24],key_bg=16,epoch=25,hardware_fps_proven=False)

def main():
 data=json.loads((HERE/'results.json').read_text());check_sources(data);check_lineage(data);print(json.dumps(replay(data),indent=2))
if __name__=='__main__':main()
