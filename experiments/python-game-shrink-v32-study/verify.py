"""Retained matched-reference replay with independent block-error/protection checks."""
from pathlib import Path
import importlib.util,json,sys,hashlib,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('shrink32_verify_bench',HERE/'benchmark.py');t=importlib.util.module_from_spec(spec);sys.modules[spec.name]=t;spec.loader.exec_module(t)
b,m,n,p=t.b,t.m,t.n,t.p

def raw(d,folder=HERE):
 path=Path(d['path']);assert not path.is_absolute() and '..' not in path.parts and 0<d['raw_bytes']<=1000000
 packed=(folder/path).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
 dc=zlib.decompressobj();out=dc.decompress(packed,d['raw_bytes']+1)
 assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(out)==d['raw_bytes']
 assert hashlib.sha256(out).hexdigest()==d['raw_sha256'];return out

def block_sse(a):
 h,w=a.shape;v=np.pad(a.astype(np.int64)**2,((0,(-h)%8),(0,(-w)%8)))
 return v.reshape((h+7)//8,8,(w+7)//8,8).sum((1,3)).reshape(-1)

def main():
 data=json.loads((HERE/'results.json').read_text())
 assert data['schema']=='gamebub-shrink-v32'
 for path,sha in data['source_sha256'].items():assert t.sha(ROOT/path)==sha,path
 inputs=json.loads((n.V24/'results.json').read_text())['inputs'];prior=json.loads((t.OLD/'results.json').read_text())['cases']
 frames=packets=changed=0
 for case in data['cases']:
  inp=next(x for x in inputs if x['scene']==case['scene']);old=next(x for x in prior if x['scene']==case['scene'] and x['policy']=='exhaustive');ref=None
  assert [r['id'] for r in case['rows']]==list(range(12))
  for row,src,oldrow in zip(case['rows'],inp['rows'],old['rows']):
   if row['key']:ref=None
   source=n.source(src);original=n.original(src);q=m.roi.declared_map(720,480,n.ROIS,8,row['background'])
   prepared=m.base.analyze_planes(source,ref,epoch=25,frame_id=row['id'],reference_id=row['reference_id'],block_size=32,motion_mode='zero' if row['selected_kind']=='zero' else 'block',motion_precision='half',penalty=0)
   base=raw(row['candidates']['baseline']['base_packet']);assert base==n.raw(oldrow['base_packet'],t.OLD)
   baseout,basemeta=m.decode(base,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
   for policy in t.POLICIES:
    record=row['candidates'][policy];packet=raw(record['base_packet']);pair=raw(record['packet']);parsed=p.parse_pair(pair)
    assert parsed['base']==packet and parsed['hud']==raw(row['hud_packet'],ROOT/row['hud_packet']['directory'])
    assert len(packet)==record['base_bytes'] and len(pair)==record['complete_bytes']<=49152
    out,meta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else row['reference_id'])
    image,metric=t.hybrid(original,out);assert metric==record['hybrid'] and n.digest(image)==record['hybrid_rgb565_sha256']
    assert meta['reconstructed_tag'].hex()==record['reconstructed_tag']
    if policy!='baseline':
     regenerated,expected,work=b.encode_prepared(prepared,q,policy=policy);assert regenerated==packet
     assert len(packet)<=len(base)
     for plane,(v,baseline) in enumerate(zip(out,baseout)):
      original_coeff=basemeta['coefficients'][plane];coeff=meta['coefficients'][plane]
      protect=b.protected_blocks(m,q,720,480,plane)
      np.testing.assert_array_equal(coeff[protect],original_coeff[protect]);np.testing.assert_array_equal(coeff[:,0,0],original_coeff[:,0,0]);np.testing.assert_array_equal(coeff.reshape(-1,64)[:,m.ft.ZIGZAG[:6]],original_coeff.reshape(-1,64)[:,m.ft.ZIGZAG[:6]])
      assert np.all(np.abs(coeff.astype(np.int32))<=np.abs(original_coeff.astype(np.int32)))
      assert np.all((coeff==0)|(np.sign(coeff)==np.sign(original_coeff)))
      old_sse=block_sse(source[plane].astype(np.int64)-baseline);sse=block_sse(source[plane].astype(np.int64)-v)
      allowance=np.zeros_like(old_sse) if policy=='shrink_strict' else np.minimum(old_sse//100,64)
      assert np.all(sse<=old_sse+allowance)
      detail=record['work']['planes'][plane]
      assert detail['selected_bytes']==min(v['bytes'] for v in detail['candidate_plans'])
      assert detail['selected_bytes']<=detail['baseline_bytes']
      assert detail['changed_blocks']==int(np.count_nonzero(np.any(coeff!=original_coeff,axis=(1,2))))
      assert detail['changed_coefficients']==int(np.count_nonzero(coeff!=original_coeff))
      assert detail['removed_coefficients']==int(np.count_nonzero(original_coeff)-np.count_nonzero(coeff))
      changed+=detail['changed_blocks']
     for key in ('changed_blocks','removed_coefficients','changed_coefficients','selected_alternative_planes','ec26_size_counter_calls'):
      assert work[key]==record['work'][key]
    packets+=1
   ref=baseout;frames+=1
  for policy in t.POLICIES:assert t.summary(case['rows'],policy)==case['summaries'][policy]
 assert frames==24 and packets==72
 print(json.dumps(dict(frames=frames,actual_packets=packets,changed_blocks=changed,source_pins=len(data['source_sha256']),all_block_SSE_DC_ROI_counter_choices_and_pixels_replayed=True,physical_30fps_proven=False)))
if __name__=='__main__':main()
