"""Replay all retained local-context recipes and actual entropy constructions."""
from pathlib import Path
import hashlib,json
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
b=m.e.m.load_module('context30_benchmark_replay',HERE/'benchmark.py')

def stable(record):return {k:v for k,v in record.items() if not k.endswith('_ms')}

def main():
 data=json.loads((HERE/'results.json').read_text())
 for rel,sha in data['source_sha256'].items():
  p=Path(rel);assert not p.is_absolute() and '..' not in p.parts
  assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha,rel
 count=pairs=0
 for row in data['rows']:
  src=row['source_packet'];packet=b.read(src,ROOT/src['directory']);meta=b.runtime.parse(packet)
  coeff=meta['coefficients'][row['plane']];bw=row['blocks_w'];plan=m.e.plan_coefficients(coeff,bw)
  assert plan==row['original_plan'];lo,hi=m.e.ec.BANDS[row['band']]
  seq=coeff.reshape(-1,64)[:,m.e.ec.f.frozen.ZIGZAG[lo:hi]].reshape(-1)
  kr,kv=plan['parameters'][row['band']+1];index=m.BandIndex(seq,kr,kv)
  assert index.bits==row['original_fixed_bits'] and index.array_bytes==row['retained_index_bytes']
  records=row['singles']+[p[k] for p in row['pairs'] for k in ('first','second','joint')]
  for record in records:
   actual=b.evaluate(coeff,bw,row['band'],record['blocks'],index,plan)
   assert stable(actual)==stable(record);count+=1
  for pair in row['pairs']:
   a,c,j=(pair[k] for k in ('first','second','joint'))
   assert pair['fixed_nonadditive_bits']==j['query']['delta_bits']-a['query']['delta_bits']-c['query']['delta_bits']
   assert pair['optimized_nonadditive_saving_bytes']==j['actual_saving_bytes']-a['actual_saving_bytes']-c['actual_saving_bytes'];pairs+=1
 assert len(data['rows'])==72 and count==322 and pairs==50
 print(json.dumps(dict(plane_indexes=72,source_frames=24,exact_local_actual_queries=count,adjacent_pairs=pairs,
       source_pins=len(data['source_sha256']),all_fixed_bit_deltas_and_actual_packet_hashes_replayed=True,
       accepted_stream_or_quality_claim=False,physical_30fps_proven=False)))
if __name__=='__main__':main()
