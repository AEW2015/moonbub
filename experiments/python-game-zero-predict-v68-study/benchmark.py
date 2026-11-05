import json,time,statistics,platform
import numpy as np
import helpers as h
model=h.module('zero68_owned_model',h.HERE/'model.py')

def summary(rows):
 means={n:statistics.mean(r['median_prediction_ms'][n]for r in rows)for n in ('old','fast')}
 return dict(frames=len(rows),keys=sum(r['key']for r in rows),p_frames=sum(not r['key']for r in rows),mean_paired_median_prediction_ms=means,fast_to_old_prediction_ratio=means['fast']/means['old'],logical_materialized_prediction_bytes_avoided_per_frame=1036800)
def main():
 pins=h.pins();cases=[]
 for source in h.load(h.SOURCE/'results.json')['cases']:
  rx=h.rx.Receiver();rows=[]
  for original in source['rows']:
   incoming=rx.ref;before=None if incoming is None else h.digest(b''.join(p.tobytes()for p in incoming));packet=h.raw(original['packet'],h.SOURCE);out=rx.receive(packet);planes,hud,meta=out[:3];key=meta['key'];fid=meta['frame_id'];vectors=meta['vectors'];bs=meta['block_size'];assert not np.any(vectors)
   funcs={'old':lambda:tuple(np.full(s,128,np.int16)for s in model.SHAPES)if key else h.m.predict(incoming,vectors,bs),'fast':lambda:model.key_prediction()if key else model.predict(incoming,vectors,bs)}
   clocks={n:[]for n in funcs};orders=[]
   for rep in range(3):
    order=['old','fast']if (fid+rep)%2==0 else ['fast','old'];orders.append(order);values={}
    for name in order:
     started=time.perf_counter_ns();values[name]=funcs[name]();clocks[name].append((time.perf_counter_ns()-started)/1e6)
    for a,b in zip(values['old'],values['fast'],strict=True):np.testing.assert_array_equal(a,b)
   prediction=values['fast'];assert key or prediction is incoming
   rebuilt=h.m.gm.reconstruct(meta['coefficients'],prediction,meta['qmap'],720,480);assert h.m.C.reference_tag(rebuilt)==meta['base_tag'];normalized=h.f.f.normalize(rebuilt)
   for a,b in zip(normalized,planes,strict=True):np.testing.assert_array_equal(a,b)
   assert h.m.C.reference_tag(normalized).hex()==original['normalized_tag']
   display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(normalized)),tuple(p['words']for p in hud));assert h.f.f.n.digest(display)==original['display_sha256']
   if incoming is not None:assert before==h.digest(b''.join(p.tobytes()for p in incoming))
   rows.append(dict(id=fid,key=key,source_packet=original['packet'],source_packet_sha256=h.digest(packet),normalized_tag=original['normalized_tag'],display_sha256=original['display_sha256'],reference_before_sha256=before,reference_after_sha256=before,prediction_sha256=h.digest(b''.join(p.astype('<i2').tobytes()for p in prediction)),hud_words_sha256=h.digest(b''.join(p['words'].astype('<u2').tobytes()for p in hud)),block_size=bs,vector_sha256=h.digest(vectors.tobytes()),zero_vectors=True,borrowed_reference=not key,key_scalar_backing_bytes=2 if key else 0,prediction_ms=clocks,prediction_order=orders,median_prediction_ms={n:statistics.median(v)for n,v in clocks.items()}))
   if fid%24==0:print(json.dumps(dict(scene=source['scene'],id=fid)),flush=True)
  cases.append(dict(scene=source['scene'],source_folder=h.SOURCE.name,rows=rows,summary=summary(rows)))
 rows=[r for c in cases for r in c['rows']];assert len(rows)==457 and pins==h.pins()
 result=dict(schema='gamebub-zero-predict-v68',source_sha256=pins,cases=cases,summary=summary(rows),key_factory_summary=summary([r for r in rows if r['key']]),p_prediction_summary=summary([r for r in rows if not r['key']]),environment=dict(python=platform.python_version(),numpy=np.__version__),physical_30fps_proven=False,new_RTL_implemented=False,wire_profile_changed=False,scope=['Three alternating paired prediction-stage clocks only. Frozen old causalreceive, comparisons, reconstruct/normalize/HUD/display/hash checks and I/O excluded.','FastP validates readonly int16 shape/range and exact bounded int8 grid insideclock. Keysharedscalar factory separate summary. No fullreceiver speedup/FPS claim.','No actual reference reads/output banks removed; sourceimmutable/referenceownership required. Nonzero maps use unchanged frozen predictor.'])
 (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
