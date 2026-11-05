#!/usr/bin/env python3
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('hud32_own_benchmark',HERE/'benchmark.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
def main():
 data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-huffman-HUD-v32'
 for rel,h in data['source_sha256'].items():
  q=Path(rel);assert not q.is_absolute() and '..' not in q.parts;assert b.sha(ROOT/q)==h,rel
 frames=words=changed=patches=0
 for case in data['cases']:
  assert [r['id'] for r in case['rows']]==list(range(48));ref=None;baseline_total=new_total=0
  for row in case['rows']:
   if row['key']:ref=None
   baseline=b.read(row['baseline'],ROOT/row['baseline']['directory']);packet=b.read(row['packet'],HERE)
   expected,oldmeta=m.p.decode_hud(baseline,ref,expected_epoch=25,expected_reference_id=None if ref is None else row['reference_id'])
   output,meta=m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=None if ref is None else row['reference_id'])
   assert len(packet)==row['bytes']<=len(baseline)==row['baseline_bytes']<=49152
   assert meta['frame_id']==row['id'] and meta['reference_id']==row['reference_id']
   assert meta['reference_tag'].hex()==row['reference_tag'] and meta['reconstructed_tag'].hex()==row['reconstructed_tag']
   assert meta['reconstructed_tag']==oldmeta['reconstructed_tag']
   assert row['work']['baseline_encode_cost_included'] is False and row['work']['baseline_motion_search_reused'] is True
   assert row['work']['selected_new']==(packet[:4]==b'HX32')
   for a,c,d,kind,payload in zip(output,expected,row['work']['patches'],meta['types'],meta['payloads']):
    assert a['rect']==c['rect'];np.testing.assert_array_equal(a['words'],c['words']);words+=a['words'].size
    assert d['selected_kind']==kind and len(payload)==d['selected_bytes']<=d['baseline_bytes']
    if kind==3:
     assert payload[:4]==b'HS32' and payload[5]==d['selected_mode'];patches+=1
   for d in row['work']['patches']:
    eligible=[v['bytes'] for v in d['trials'] if v.get('bounded_fit')]
    assert d['selected_bytes']==min([d['baseline_bytes'],*eligible])
   baseline_total+=len(baseline);new_total+=len(packet);changed+=int(packet[:4]==b'HX32');frames+=1;ref=output
  summary=case['summary'];assert baseline_total==summary['baseline_hud_bytes'] and new_total==summary['new_hud_bytes']
  assert summary['saving_bytes']==baseline_total-new_total and summary['saving_percent']==100*(1-new_total/baseline_total)
  assert summary['new_HUD_Mbps_at30']==new_total*240/48/1e6 and summary['exact_hud_words']==48*21120
 assert frames==96 and words==96*21120
 print(json.dumps(dict(frames=frames,exact_hud_words=words,new_frames=changed,new_huffman_patches=patches,source_pins=len(data['source_sha256']),
                      all_accepted_references_tags_pixel_words_choices_and_bounds_replayed=True,hardware_30fps_proven=False)))
if __name__=='__main__':main()
