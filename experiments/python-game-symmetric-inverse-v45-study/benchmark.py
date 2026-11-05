"""Every archived full-grid AB38 coefficient trial, actual qmap dequantization."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,time,zlib
import numpy as np
import model as new
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
old=mod('sym45_frozen_arithmetic',HERE.parent/'python-game-binary-v38-study/decoder.py');h=mod('sym45_frozen_helpers',HERE.parent/'python-game-integrated-v38-study/helpers.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 stored=(folder/d['path']).read_bytes();assert digest(stored)==d['stored_sha256'];o=zlib.decompressobj();b=o.decompress(stored,d['raw_bytes']+1);assert o.eof and not o.unused_data and not o.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
def pins():
 d=json.loads((HERE.parent/'python-game-block-rx-v44-study/results.json').read_text());paths={ROOT/p for p in d['source_sha256']};paths|={ROOT/p for p in h.pins()};paths|={HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-block-rx-v44-study/results.json'};return{p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(paths)}
def main():
 before=pins();inputs=json.loads((HERE.parent/'python-game-block-rx-v44-study/results.json').read_text());cache={};rows=[]
 for r in inputs['rows']:
  if r['compact']:continue
  folder=ROOT/r['packet_folder'];key=str(folder)
  if key not in cache:
   d=json.loads((folder/'results.json').read_text());cache[key]={(c['scene'],f['id']):f for c in d['cases'] for f in c['rows']}
  frame=cache[key][r['scene'],r['id']];packet=raw(folder,frame['packet']);O=h.canonical.HEADER;outer=O.unpack_from(packet);assert outer[0]==b'CS38' and zlib.crc32(packet[:-4])==struct.unpack('<I',packet[-4:])[0]
  inner=packet[O.size:O.size+outer[11]];fields=h.m.HEADER.unpack_from(inner);assert fields[0]==b'GS38' and zlib.crc32(inner[:-4])==struct.unpack('<I',inner[-4:])[0]
  qmap=h.m.roi.unpack_map(inner[h.m.HEADER.size:h.m.HEADER.size+fields[12]],45,30);tables=h.m.roi.block_tables(qmap,720,480,r['plane'])
  ab=raw(folder,r['packet']);coeff=old.decode(ab,r['blocks'],r['blocks_w']);assert digest(coeff.astype('<i2',copy=False).tobytes())==r['coefficient_sha256'];a=coeff.astype(np.int64)*tables
  start=time.perf_counter_ns();gold=new.ft.inverse(a);dense_ms=(time.perf_counter_ns()-start)/1e6
  start=time.perf_counter_ns();got=new.inverse(a);symmetric_ms=(time.perf_counter_ns()-start)/1e6;np.testing.assert_array_equal(got,gold)
  work=new.logical_work(a);zero=np.count_nonzero(a,axis=(1,2))==0;dc=(np.count_nonzero(a,axis=(1,2))==1)&(a[:,0,0]!=0);complex_mask=~(zero|dc);aw=new.logical_work(a[complex_mask]);work.update(zero_blocks=int(zero.sum()),DC_blocks=int(dc.sum()),complex_blocks=int(complex_mask.sum()),shortcut_sparse_direct_products=aw['sparse_direct_products']+2*int(dc.sum()),shortcut_sparse_symmetric_products=aw['sparse_symmetric_products']+2*int(dc.sum()))
  # Selected actual tile executions qualify scalar skip/shortcut operation accounting.
  checked=[]
  for kind,mask in(('zero',zero),('DC',dc),('complex',complex_mask)):
   indices=np.flatnonzero(mask)
   if len(indices):
    idx=int(indices[0]);out,w=new.scalar_shortcuts(a[idx]);np.testing.assert_array_equal(out,gold[idx]);checked.append(dict(kind=kind,block=idx,work=w))
  rows.append(dict(cohort=r['cohort'],scene=r['scene'],id=r['id'],plane=r['plane'],blocks=r['blocks'],coefficient_sha256=r['coefficient_sha256'],dequantized_sha256=digest(a.astype('<i8').tobytes()),inverse_sha256=digest(got.astype('<i8').tobytes()),work=work,scalar_checks=checked,dense_NumPy_ms=dense_ms,symmetric_NumPy_ms=symmetric_ms))
  if len(rows)%200==0:print(json.dumps(dict(planes=len(rows))),flush=True)
 assert pins()==before
 keys=('blocks','dense_direct_products','dense_symmetric_products','sparse_direct_products','sparse_symmetric_products','shortcut_sparse_direct_products','shortcut_sparse_symmetric_products','zero_blocks','DC_blocks','complex_blocks')
 summary={k:sum(r['work'][k] for r in rows) for k in keys};summary.update(planes=len(rows),all_exact_Q14_inverses=True,maximum_actual_abs_dequant=max(r['work']['max_abs_dequant'] for r in rows),maximum_actual_abs_mid=max(r['work']['max_abs_mid'] for r in rows),scalar_tile_checks=sum(len(r['scalar_checks']) for r in rows))
 result=dict(schema='gamebub-symmetric-inverse-v45',source_sha256=before,rows=rows,summary=summary,interval_bounds=new.interval_bounds(),scope=['SameAB38packets,actualqmapdequantization,Q14arithmeticandtwooriginalroundingboundaries.','LogicalpairedoutputMACcounts;NumPydensematmulsdonotimplementhardwarezeroskips.','Zero/DCtwo-productshortcutscreditedequallytobothsparsemodels.','NoDSPmapping,laneissue/rounding/control/stallcycles,routedclock,memoryarbitrationorphysical30fpsproof.'])
 (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(summary=summary,bounds=result['interval_bounds'])),flush=True)
if __name__=='__main__':main()
