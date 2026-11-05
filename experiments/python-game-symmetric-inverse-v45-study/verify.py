"""Independent frozen matrix oracle, actual qmap and product-count qualification."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
subject=mod('sym45_verify_subject',HERE/'model.py');old=mod('sym45_verify_arith',HERE.parent/'python-game-binary-v38-study/decoder.py');h=mod('sym45_verify_legacy_helpers',HERE.parent/'python-game-integrated-v38-study/helpers.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 p=Path(d['path']);assert not p.is_absolute() and '..' not in p.parts;stored=(folder/p).read_bytes();assert digest(stored)==d['stored_sha256'];z=zlib.decompressobj();b=z.decompress(stored,d['raw_bytes']+1);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
def main():
 data=json.loads((HERE/'results.json').read_text());inputs=json.loads((HERE.parent/'python-game-block-rx-v44-study/results.json').read_text());source=[r for r in inputs['rows'] if not r['compact']];assert len(source)==len(data['rows'])==1731
 for p,s in data['source_sha256'].items():assert digest((ROOT/p).read_bytes())==s,p
 cache={};totals={k:0 for k in('blocks','dense_direct_products','dense_symmetric_products','sparse_direct_products','sparse_symmetric_products','shortcut_sparse_direct_products','shortcut_sparse_symmetric_products','zero_blocks','DC_blocks','complex_blocks')};scalar=0;maximum=0;maximum_mid=0
 for r,e in zip(data['rows'],source,strict=True):
  assert(r['cohort'],r['scene'],r['id'],r['plane'])==(e['cohort'],e['scene'],e['id'],e['plane']);folder=ROOT/e['packet_folder']
  if str(folder) not in cache:
   d=json.loads((folder/'results.json').read_text());cache[str(folder)]={(c['scene'],f['id']):f for c in d['cases'] for f in c['rows']}
  f=cache[str(folder)][e['scene'],e['id']];wire=raw(folder,f['packet']);outer=h.canonical.HEADER.unpack_from(wire);inner=wire[h.canonical.HEADER.size:h.canonical.HEADER.size+outer[11]];fields=h.m.HEADER.unpack_from(inner);assert fields[0]==b'GS38'
  qmap=h.m.roi.unpack_map(inner[h.m.HEADER.size:h.m.HEADER.size+fields[12]],45,30);tables=h.m.roi.block_tables(qmap,720,480,r['plane']);c=old.decode(raw(folder,e['packet']),e['blocks'],e['blocks_w']);a=c.astype(np.int64)*tables
  assert digest(c.astype('<i2').tobytes())==e['coefficient_sha256']==r['coefficient_sha256'];assert digest(a.astype('<i8').tobytes())==r['dequantized_sha256']
  Q=subject.ft.Q14;mid=(a@Q+8192)>>14;gold=(Q.T@mid+8192)>>14;np.testing.assert_array_equal(subject.inverse(a),gold);assert digest(gold.astype('<i8').tobytes())==r['inverse_sha256']
  nonzero=np.count_nonzero(a,axis=(1,2));zero=nonzero==0;dc=(nonzero==1)&(a[:,0,0]!=0);complex_mask=~(zero|dc);n=len(a);nz_a=int(np.count_nonzero(a));nz_mid=int(np.count_nonzero(mid));complex_nz=int(np.count_nonzero(a[complex_mask]))+int(np.count_nonzero(mid[complex_mask]));DC=int(dc.sum())
  expected=dict(blocks=n,dense_direct_products=1024*n,dense_symmetric_products=512*n,sparse_direct_products=8*(nz_a+nz_mid),sparse_symmetric_products=4*(nz_a+nz_mid),shortcut_sparse_direct_products=8*complex_nz+2*DC,shortcut_sparse_symmetric_products=4*complex_nz+2*DC,zero_blocks=int(zero.sum()),DC_blocks=DC,complex_blocks=int(complex_mask.sum()))
  for k,v in expected.items():assert r['work'][k]==v,(k,r);totals[k]+=v
  for checked in r['scalar_checks']:
   i=checked['block'];out,work=subject.scalar_shortcuts(a[i]);np.testing.assert_array_equal(out,gold[i]);assert work==checked['work'];scalar+=1
  maximum=max(maximum,int(np.abs(a).max()));maximum_mid=max(maximum_mid,int(np.abs(mid).max()))
 for k,v in totals.items():assert data['summary'][k]==v,k
 assert data['summary']['scalar_tile_checks']==scalar and data['summary']['maximum_actual_abs_dequant']==maximum and data['summary']['maximum_actual_abs_mid']==maximum_mid
 assert data['interval_bounds']==subject.interval_bounds();b=data['interval_bounds'];assert b['first_accumulator_signed_bits']==36 and b['second_accumulator_signed_bits']==37
 print(json.dumps(dict(full_AB38_planes=len(source),exact_actual_dequantized_tiles=totals['blocks'],actual_scalar_tile_checks=scalar,shortcut_sparse_direct_products=totals['shortcut_sparse_direct_products'],shortcut_sparse_symmetric_products=totals['shortcut_sparse_symmetric_products'],all_exact_both_rounding_boundaries=True,encoding_called=False,DSP_fit_cycles_or_physical_FPS_proven=False)))
if __name__=='__main__':main()
