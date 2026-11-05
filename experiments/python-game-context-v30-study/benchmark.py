"""Exact fixed-parameter context deltas versus reoptimized EC26 sizes."""
from pathlib import Path
import hashlib,json,sys,time,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];runtime=m.e.m
OLD=HERE.parent/'python-game-controller-v29-study'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(desc,folder=OLD):
 packed=(folder/desc['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==desc['stored_sha256']
 raw=zlib.decompress(packed);assert len(raw)==desc['raw_bytes'] and hashlib.sha256(raw).hexdigest()==desc['raw_sha256'];return raw
def timed(fn):
 start=time.perf_counter_ns();out=fn();return out,(time.perf_counter_ns()-start)/1e6

def evaluate(coeff,bw,band,blocks,index,plan):
 lo,hi=m.e.ec.BANDS[band];span=hi-lo;candidate=coeff.copy()
 flat=candidate.reshape(-1,64);flat[np.ix_(np.array(blocks),m.e.ec.f.frozen.ZIGZAG[lo:hi])]=0
 start,stop=blocks[0]*span,(blocks[-1]+1)*span
 assert blocks==list(range(blocks[0],blocks[-1]+1))
 query,local_ms=timed(lambda:index.delete_interval(start,stop))
 seq=flat[:,m.e.ec.f.frozen.ZIGZAG[lo:hi]].reshape(-1)
 full_bits,full_ms=timed(lambda:m.full_bits(seq,index.kr,index.kv));assert full_bits==query['new_bits']
 optimized,counter_ms=timed(lambda:m.e.plan_coefficients(candidate,bw))
 encoded,serialize_ms=timed(lambda:m.e.ec.encode_coefficients(candidate,bw,layout=0));assert len(encoded)==optimized['bytes']
 before=runtime.counter.isolated_packet_bytes(coeff[blocks]);after=runtime.counter.isolated_packet_bytes(candidate[blocks])
 fixed_payload=sum(plan['stream_lengths'])+query['delta_stream_bytes']
 fixed_packet=m.e.ec.COEFF.size+4+min(coeff.size*2,fixed_payload)
 assert optimized['bytes']<=fixed_packet
 return dict(blocks=blocks,old_ec26_bytes=plan['bytes'],new_ec26_bytes=optimized['bytes'],actual_saving_bytes=plan['bytes']-optimized['bytes'],
  fixed_parameter_packet_bytes=fixed_packet,fixed_parameter_saving_bytes=plan['bytes']-fixed_packet,
  encoded_sha256=hashlib.sha256(encoded).hexdigest(),candidate_coefficients_sha256=hashlib.sha256(candidate.astype('<i2').tobytes()).hexdigest(),isolated_cp02_saving_bytes=int((before-after).sum()),query=query,parameter_change=optimized['parameters']!=plan['parameters'],
  raw_before=plan['raw'],raw_after=optimized['raw'],local_query_ms=local_ms,full_fixed_recount_ms=full_ms,
  full_optimized_counter_ms=counter_ms,actual_serialize_ms=serialize_ms)

def run():
 data=json.loads((OLD/'results.json').read_text());rows=[];object_paths=set()
 for case in data['cases']:
  if case['policy']!='adaptive_lazy':continue
  for row in case['rows'][:12]:
   packet=read(row['base_packet']);object_paths.add(OLD/row['base_packet']['path']);meta=runtime.parse(packet)
   for plane,coeff in enumerate(meta['coefficients']):
    bw=(720 if plane==0 else 360)//8;plan=m.e.plan_coefficients(coeff,bw)
    assert len(m.e.ec.encode_coefficients(coeff,bw))==plan['bytes']
    band=2;lo,hi=m.e.ec.BANDS[band];zig=coeff.reshape(-1,64)[:,m.e.ec.f.frozen.ZIGZAG[lo:hi]]
    kr,kv=plan['parameters'][band+1];index,setup_ms=timed(lambda:m.BandIndex(zig.reshape(-1),kr,kv))
    active=np.flatnonzero(np.any(zig!=0,axis=1));singles=[]
    if len(active):
     chosen=active[np.unique(np.linspace(0,len(active)-1,min(6,len(active)),dtype=int))].tolist()
     singles=[evaluate(coeff,bw,band,[block],index,plan) for block in chosen]
    adjacent=active[np.isin(active+1,active)];pairs=[]
    chosen=adjacent[np.unique(np.linspace(0,len(adjacent)-1,min(2,len(adjacent)),dtype=int))] if len(adjacent) else []
    for block in chosen:
     a,b=int(block),int(block)+1
     first=evaluate(coeff,bw,band,[a],index,plan);second=evaluate(coeff,bw,band,[b],index,plan);joint=evaluate(coeff,bw,band,[a,b],index,plan)
     pairs.append(dict(first=first,second=second,joint=joint,
      fixed_nonadditive_bits=joint['query']['delta_bits']-first['query']['delta_bits']-second['query']['delta_bits'],
      optimized_nonadditive_saving_bytes=joint['actual_saving_bytes']-first['actual_saving_bytes']-second['actual_saving_bytes']))
    rows.append(dict(scene=case['scene'],id=row['id'],plane=plane,blocks=len(coeff),blocks_w=bw,
     source_packet=dict(row['base_packet'],directory=OLD.relative_to(ROOT).as_posix()),band=band,
     setup_ms=setup_ms,retained_index_bytes=index.array_bytes,singles=singles,pairs=pairs,original_plan=plan,original_fixed_bits=index.bits))
 summaries=[]
 for scene in sorted({r['scene'] for r in rows}):
  selected=[r for r in rows if r['scene']==scene];singles=[s for r in selected for s in r['singles']];pairs=[s for r in selected for s in r['pairs']]
  allq=singles+[p[k] for p in pairs for k in ('first','second','joint')]
  summaries.append(dict(scene=scene,source_frames=12,plane_indexes=len(selected),single_queries=len(singles),pair_queries=len(pairs),
   all_actual_queries=len(allq),local_fixed_exact_queries=len(allq),actual_saving_bytes=sum(s['actual_saving_bytes'] for s in singles),
   fixed_parameter_saving_bytes=sum(s['fixed_parameter_saving_bytes'] for s in singles),
   isolated_cp02_saving_bytes=sum(s['isolated_cp02_saving_bytes'] for s in singles),
   proxy_mismatches=sum(s['actual_saving_bytes']!=s['isolated_cp02_saving_bytes'] for s in singles),
   reselection_queries=sum(s['parameter_change'] for s in allq),
   nonadditive_fixed_pairs=sum(p['fixed_nonadditive_bits']!=0 for p in pairs),
   nonadditive_optimized_pairs=sum(p['optimized_nonadditive_saving_bytes']!=0 for p in pairs),
   mean_setup_ms=sum(r['setup_ms'] for r in selected)/len(selected),mean_local_query_ms=sum(s['local_query_ms'] for s in allq)/len(allq),
   mean_full_fixed_recount_ms=sum(s['full_fixed_recount_ms'] for s in allq)/len(allq),
   mean_full_optimized_counter_ms=sum(s['full_optimized_counter_ms'] for s in allq)/len(allq),
   maximum_retained_index_bytes=max(r['retained_index_bytes'] for r in selected)))
 paths={Path(v.__file__).resolve() for v in list(sys.modules.values()) if hasattr(v,'__file__') and v.__file__ and Path(v.__file__).resolve().is_relative_to(ROOT)}
 paths|=set(HERE.glob('*.py'))|object_paths|{OLD/'results.json'}
 pins={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
 output=dict(schema='gamebub-run-context-v30',source_sha256=pins,rows=rows,summaries=summaries,
  scope=['Independent non-causal coefficient edits; not accepted frame/quality results.',
   'Exact local delta requires fixed Rice parameters/layout0/deletion intervals. Setup is separate.',
   'EC26 counters/serialization reoptimize parameters/raw fallback; isolated CP02 is a comparison proxy.',
   'Independent savings cannot be added into a hypothetical stream. No native/FPGA/physical30fps proof.'])
 (HERE/'results.json').write_text(json.dumps(output,separators=(',',':'))+'\n');print(json.dumps(summaries,indent=2))
if __name__=='__main__':run()
