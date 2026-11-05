#!/usr/bin/env python3
"""Independent prediction-stage proof; no receiver/wire changes or FPS claim."""
from pathlib import Path
import hashlib,importlib.util,json,math,statistics,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];SOURCE=HERE.parent/'python-game-binary-qual-v40-study'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
def bound(name,path,helper):
 old=sys.modules.get('helpers')
 try:sys.modules['helpers']=helper;return module(name,path)
 finally:
  if old is None:sys.modules.pop('helpers',None)
  else:sys.modules['helpers']=old
old=module('zero68_independent43',HERE.parent/'python-game-direct-rx-v43-study/verify.py');m,f=old.m,old.f
h=module('zero68_subject_helpers',HERE/'helpers.py');subject=bound('zero68_subject_model',HERE/'model.py',h)
def digest(b):return hashlib.sha256(b).hexdigest()
def base(array):
 result=array
 while isinstance(result.base,np.ndarray):result=result.base
 return result

def check_key(prediction):
 assert type(prediction)is tuple and len(prediction)==3
 owners={}
 for p,shape in zip(prediction,((480,720),(240,360),(240,360)),strict=True):
  assert p.shape==shape and p.dtype==np.int16 and not p.flags.writeable and p.strides==(0,0)
  assert np.all(p==128);owner=base(p);owners[id(owner)]=owner
 assert len(owners)==1 and next(iter(owners.values())).nbytes==2
 return prediction

def same(left,right):old.equal_planes(left,right)
def display(planes,patches):return f.f.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(planes)),tuple(p['words']for p in patches))

def summary_check(actual,rows):
 means={name:statistics.mean(r['median_prediction_ms'][name]for r in rows)for name in ('old','fast')}
 assert actual['frames']==len(rows)and actual['keys']==sum(r['key']for r in rows)and actual['p_frames']==sum(not r['key']for r in rows)
 assert actual['logical_materialized_prediction_bytes_avoided_per_frame']==1036800
 for name,value in means.items():assert math.isclose(actual['mean_paired_median_prediction_ms'][name],value,rel_tol=1e-12,abs_tol=1e-12)
 assert math.isclose(actual['fast_to_old_prediction_ratio'],means['fast']/means['old'],rel_tol=1e-12,abs_tol=1e-12)

def main():
 from unittest.mock import patch
 data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-zero-predict-v68'
 for key in('physical_30fps_proven','new_RTL_implemented','wire_profile_changed'):assert data[key]is False
 for path,want in data['source_sha256'].items():assert digest((ROOT/path).read_bytes())==want,path
 for name in('helpers.py','model.py','benchmark.py','test_model.py'):assert (HERE/name).relative_to(ROOT).as_posix()in data['source_sha256']
 source=json.loads((SOURCE/'results.json').read_text());assert len(source['cases'])==len(data['cases'])==4
 direct=old.direct_module();frames=keys=borrowed=0
 for sourcecase,case in zip(source['cases'],data['cases'],strict=True):
  assert case['scene']==sourcecase['scene']and case['source_folder']==SOURCE.name and len(case['rows'])==len(sourcecase['rows'])
  rx=direct.Receiver()
  for original,row in zip(sourcecase['rows'],case['rows'],strict=True):
   packet=old.raw(original['packet'],SOURCE);reference=rx.ref;before=None if reference is None else digest(b''.join(p.tobytes()for p in reference))
   assert row['source_packet']==original['packet']and row['source_packet_sha256']==digest(packet)
   with old.no_reencode():canonical,hud,meta,_=rx.receive(packet)
   key=meta['key'];fid=meta['frame_id'];bs=meta['block_size'];vectors=meta['vectors']
   assert row['id']==original['id']==fid and row['key']==key and row['block_size']==bs
   assert not np.any(vectors)and row['zero_vectors']is True and row['vector_sha256']==digest(vectors.tobytes())
   expected=tuple(np.full(shape,128,np.int16)for shape in ((480,720),(240,360),(240,360)))if key else m.predict(reference,vectors,bs)
   if key:prediction=check_key(subject.key_prediction());assert row['key_scalar_backing_bytes']==2
   else:
    with patch.object(subject.h.m,'predict',side_effect=AssertionError('zero path called whole legacy predictor')):prediction=subject.predict(reference,vectors,bs)
    assert prediction is reference and all(not p.flags.writeable for p in prediction)and row['key_scalar_backing_bytes']==0
   same(prediction,expected);assert row['borrowed_reference']==(not key)
   assert row['prediction_sha256']==digest(b''.join(p.astype('<i2').tobytes()for p in prediction))
   rebuilt=m.gm.reconstruct(meta['coefficients'],prediction,meta['qmap'],720,480);assert m.C.reference_tag(rebuilt)==meta['base_tag']
   normalized=f.f.normalize(rebuilt);same(normalized,canonical)
   assert row['normalized_tag']==original['normalized_tag']==m.C.reference_tag(normalized).hex()
   shown=display(normalized,hud);assert f.f.n.digest(shown)==row['display_sha256']==original['display_sha256']
   assert row['hud_words_sha256']==digest(b''.join(p['words'].astype('<u2').tobytes()for p in hud))
   after=None if reference is None else digest(b''.join(p.tobytes()for p in reference))
   assert before==after==row['reference_before_sha256']==row['reference_after_sha256']
   for name,values in row['prediction_ms'].items():
    assert name in('old','fast')and len(values)==3 and all(type(v)in(int,float)and math.isfinite(v)and v>0 for v in values)
    assert math.isclose(row['median_prediction_ms'][name],statistics.median(values),rel_tol=1e-12,abs_tol=1e-12)
   assert set(row['prediction_ms'])=={'old','fast'}
   assert row['prediction_order']==[['old','fast']if(fid+i)%2==0 else['fast','old']for i in range(3)]
   assert rx.ref is canonical and rx.rid==rx.last==fid
   frames+=1;keys+=int(key);borrowed+=not key
  summary_check(case['summary'],case['rows']);print(json.dumps(dict(scene=case['scene'],exact_causal_frames=len(case['rows']))),flush=True)
 rows=[r for c in data['cases']for r in c['rows']];summary_check(data['summary'],rows)
 summary_check(data['key_factory_summary'],[r for r in rows if r['key']]);summary_check(data['p_prediction_summary'],[r for r in rows if not r['key']])
 assert frames==457 and keys==20 and borrowed==437
 print(json.dumps(dict(exact_causal_frames=frames,shared_scalar_key_views=keys,borrowed_readonly_P_predictions=borrowed,
  source_pins=len(data['source_sha256']),all_old_prediction_values_exact=True,reconstruction_normalization_HUD_display_reference_exact=True,
  key_scalar_physical_backing_bytes=2,logical_prediction_array_bytes=1036800,nonzero_fractional_fallback_directed_tests=True,
  receiver_or_wire_changed=False,stage_clocks_only=True,full_receive_or_hardware_speedup_proven=False)),flush=True)
if __name__=='__main__':main()
