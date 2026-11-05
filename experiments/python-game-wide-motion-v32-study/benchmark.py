"""Matched-reference wide-motion feasibility; wide full frames are not serialized."""
from pathlib import Path
import hashlib,json,time,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];r=m.runtime
n=m.load('wide32_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
OLD=HERE.parent/'python-game-controller-v30-study'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def raw(d,folder=OLD):
 p=(folder/d['path']);packed=p.read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256'];a=zlib.decompress(packed);assert len(a)==d['raw_bytes'] and hashlib.sha256(a).hexdigest()==d['raw_sha256'];return a

def blob(a):
 packed=zlib.compress(a,9);path='objects/'+hashlib.sha256(packed).hexdigest()+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
 return dict(path=path,raw_bytes=len(a),raw_sha256=hashlib.sha256(a).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest())
def metric(original,out):
 img=n.overlay(r.C.corpus.rgb565(r.ft.planes_to_rgb(out)),tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS));return n.metric(original,img),n.digest(img)
def main():
 old=json.loads((OLD/'results.json').read_text());inputs=json.loads((n.V24/'results.json').read_text())['inputs'];cases=[];paths={ROOT/p for p in old['source_sha256']};paths|={OLD/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py'}
 for inp in inputs:
  prior=next(c for c in old['cases'] if c['scene']==inp['scene'] and c['policy']=='band_strict');rows=[];ref=None
  for src,pr in zip(inp['rows'][:12],prior['rows'][:12]):
   key=pr['key'];fid=src['id']
   if key:ref=None
   source=n.source(src);original=n.original(src);q=r.roi.declared_map(720,480,n.ROIS,8,pr['selected_background']);qbytes=len(r.roi.pack_map(q));hud=pr['hud_bytes']
   start=time.perf_counter_ns();prep=m.adaptive.analyze_with(r.base,source,ref,epoch=25,frame_id=fid,reference_id=pr['reference_id'],block_size=32,motion_mode='block',motion_precision='half',search_policy='adaptive_zero2')
   bp,baseline,bwork=r.encode_prepared(prep,q);bm,bhash=metric(original,baseline);baseline_ms=(time.perf_counter_ns()-start)/1e6
   bmeta=r.parse(bp);v=bmeta['vectors'];wide_work=dict(beyond_GM27_blocks=0,search_ms=0.,sad_sample_operations=0,reference_sample_fetches=0)
   start=time.perf_counter_ns()
   if key:wide_v=v.copy();prediction=tuple(np.full_like(a,128) for a in source)
   else:wide_v,wide_work=m.estimate(source,ref,v);prediction=m.predict(ref,wide_v)
   payloads,out,work=m.residual(source,prediction,q,key);wm,whash=metric(original,out);incremental_ms=(time.perf_counter_ns()-start)/1e6
   pred_sse=sum(int(np.square(s.astype(np.int64)-p).sum()) for s,p in zip(source,prediction));baseline_prediction_sse=sum(int(np.square(s.astype(np.int64)-p).sum()) for s,p in zip(source,prep.prediction))
   raw_mv=0 if key else 1+wide_v.size
   hypothetical=80+qbytes+raw_mv+work['residual_bytes']+hud+60
   paths.add(OLD/pr['base_packet']['path'])
   record=dict(id=fid,key=key,reference_id=pr['reference_id'],reference_tag=prep.reference_tag.hex(),accepted_reference_packet=pr['base_packet'],source_common_yuv_sha256=src['common_yuv420_u8_sha256'],background=pr['selected_background'],hud_bytes=hud,qmap_bytes=qbytes,
    baseline=dict(base_packet=blob(bp),actual_complete_budget_bytes=len(bp)+hud+60,residual_bytes=sum(bmeta['plane_lengths']),motion_bytes=bmeta['vector_bytes'],hybrid=bm,hybrid_sha256=bhash,prediction_sse=baseline_prediction_sse,analysis=prep.work,encode_work=bwork,total_source_work_ms=baseline_ms),
    wide=dict(vectors=blob(wide_v.tobytes()),payloads=[blob(p) for p in payloads],work=wide_work,residual_work=work,residual_bytes=work['residual_bytes'],raw_motion_budget_bytes=raw_mv,hypothetical_complete_budget_bytes=hypothetical,hybrid=wm,hybrid_sha256=whash,prediction_sse=pred_sse,incremental_work_ms=incremental_ms,total_with_incumbent_work_ms=baseline_ms+incremental_ms,
     prediction_sha256=r.C.reference_tag(prediction).hex(),reconstructed_sha256=r.C.reference_tag(out).hex(),valid_GM27_frame=False))
   rows.append(record)
   # Accepted history always follows the original retained v30 packet, not either trial.
   ref,_=r.decode(raw(pr['base_packet']),ref,expected_epoch=25,expected_reference_id=None if key else pr['reference_id'])
  base=sum(x['baseline']['actual_complete_budget_bytes'] for x in rows);wide=sum(x['wide']['hypothetical_complete_budget_bytes'] for x in rows);samples=sum(x['baseline']['hybrid']['active_channel_samples'] for x in rows)
  summary=dict(frames=12,baseline_complete_budget_bytes=base,wide_hypothetical_complete_budget_bytes=wide,baseline_residual_bytes=sum(x['baseline']['residual_bytes'] for x in rows),wide_residual_bytes=sum(x['wide']['residual_bytes'] for x in rows),baseline_mse=sum(x['baseline']['hybrid']['active_squared_error'] for x in rows)/samples,wide_mse=sum(x['wide']['hybrid']['active_squared_error'] for x in rows)/samples,beyond_GM27_blocks=sum(x['wide']['work']['beyond_GM27_blocks'] for x in rows),P_blocks=11*345,baseline_prediction_sse=sum(x['baseline']['prediction_sse'] for x in rows),wide_prediction_sse=sum(x['wide']['prediction_sse'] for x in rows),baseline_work_ms=sum(x['baseline']['total_source_work_ms'] for x in rows)/12,wide_total_with_incumbent_work_ms=sum(x['wide']['total_with_incumbent_work_ms'] for x in rows)/12,wide_incremental_search_ms=sum(x['wide']['work']['search_ms'] for x in rows)/12)
  cases.append(dict(scene=inp['scene'],rows=rows,summary=summary));print(json.dumps(dict(scene=inp['scene'],summary=summary)),flush=True)
 paths|={Path(v.__file__).resolve() for v in list(__import__('sys').modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
 data=dict(schema='gamebub-wide-motion-v32',source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},cases=cases,scope=['Matched current sources and actual v30 strict accepted histories; noncausal trial reference probe.','Wide±68half-luma coordinates require a new negotiated decoder limit/profile; no valid GM27 wide frame or atomic receiver is implemented.','Residual plane payloads are actually serialized/decoded; wide MV is a conservative raw1+2B/block budget, with80Bnewheader+currentHU25+60Bbinding hypothetical.','Wide total cost pays baseline candidate analysis/encode/quality plus all additional search/transform/rate/quality work. No native hardware/FPS/HEVCAV1 superiority proof.'])
 (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
if __name__=='__main__':main()
