#!/usr/bin/env python3
"""Replay retained packets independently of candidate construction."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('hud33_own_benchmark',HERE/'benchmark.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
def main():
 data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-run-HUD-v33'
 for rel,sha in data['source_sha256'].items():
  q=Path(rel);assert not q.is_absolute() and '..' not in q.parts;assert b.sha(ROOT/q)==sha,rel
 frames=words=changed=patches=0
 for case in data['cases']:
  assert [r['id'] for r in case['rows']]==list(range(48));ref=None;totals=[0,0,0]
  for row in case['rows']:
   if row['key']:ref=None
   hu25=b.read(row['hu25'],ROOT/row['hu25']['directory']);hx32=b.read(row['v32'],b.OLD);packet=b.read(row['packet'],HERE);rid=None if ref is None else row['reference_id']
   expected,oldmeta=m.p.decode_hud(hu25,ref,expected_epoch=25,expected_reference_id=rid)
   prior,prior_meta=m.old.decode_hud(hx32,ref,expected_epoch=25,expected_reference_id=rid)
   output,meta=m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=rid)
   assert len(packet)==row['bytes']<=len(hx32)==row['v32_bytes']<=len(hu25)==row['hu25_bytes']<=49152
   assert meta['frame_id']==row['id'] and meta['reference_id']==row['reference_id']
   assert meta['reference_tag'].hex()==row['reference_tag'] and meta['reconstructed_tag'].hex()==row['reconstructed_tag']
   assert meta['reconstructed_tag']==oldmeta['reconstructed_tag']==prior_meta['reconstructed_tag']
   assert row['work']['hu25_generation_included'] is False and row['work']['v32_generation_included'] is False
   assert row['work']['selected_new']==(packet[:4]==b'HX33')
   for a,c,e,d,kind,payload in zip(output,expected,prior,row['work']['patches'],meta['types'],meta['payloads']):
    assert a['rect']==c['rect']==e['rect'];np.testing.assert_array_equal(a['words'],c['words']);np.testing.assert_array_equal(a['words'],e['words']);words+=a['words'].size
    assert d['selected_kind']==kind and len(payload)==d['selected_bytes']<=d['v32_bytes']<=d['hu25_bytes']
    eligible=[t['bytes'] for t in d['trials'] if t['bounded_fit']];assert d['selected_bytes']==min([d['v32_bytes'],*eligible])
    for t in d['trials']:
     for channel in t['channels']:
      assert channel['selected']['bytes']==min(v['bytes'] for v in channel['trials'] if 'bytes' in v)
    if kind==4:
     assert payload[:4]==b'HS33' and payload[5]==d['selected_mode'];patches+=1
   if len(packet)==len(hx32):assert packet==hx32
   totals=[a+len(v) for a,v in zip(totals,(hu25,hx32,packet))];changed+=int(packet[:4]==b'HX33');frames+=1;ref=output
  s=case['summary'];assert totals==[s['hu25_hud_bytes'],s['v32_hud_bytes'],s['new_hud_bytes']]
  assert s['saving_vs_v32_bytes']==totals[1]-totals[2] and s['saving_vs_hu25_bytes']==totals[0]-totals[2]
 assert frames==96 and words==96*21120
 print(json.dumps(dict(frames=frames,exact_hud_words=words,new_frames=changed,new_run_patches=patches,source_pins=len(data['source_sha256']),
  all_accepted_references_tags_words_lengths_crc_choices_and_no_growth_replayed=True,hardware_30fps_proven=False)))
if __name__=='__main__':main()
