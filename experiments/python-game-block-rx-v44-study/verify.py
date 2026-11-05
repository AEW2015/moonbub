"""Independent retained coefficient oracle and bounded iterator state audit."""
from pathlib import Path
import hashlib,importlib.util,json,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
new=module('blockrx44_independent_subject',HERE/'decoder.py');old=module('blockrx44_independent_golden',HERE.parent/'python-game-binary-v38-study/decoder.py')
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(folder,d):
 p=Path(d['path']);assert not p.is_absolute() and '..' not in p.parts;stored=(folder/p).read_bytes();assert digest(stored)==d['stored_sha256'];o=zlib.decompressobj();b=o.decompress(stored,d['raw_bytes']+1);assert o.eof and not o.unused_data and not o.unconsumed_tail and len(b)==d['raw_bytes'] and digest(b)==d['raw_sha256'];return b
def main():
 d=json.loads((HERE/'results.json').read_text());assert d['complete'] and d['schema']=='gamebub-block-rx-v44'
 for p,h in d['source_sha256'].items():assert digest((ROOT/p).read_bytes())==h,p
 expected=[]
 for cohort in('binary-v38','binary-full-v39','binary-qual-v40'):
  folder=ROOT/'experiments'/('python-game-'+cohort+'-study');source=json.loads((folder/'results.json').read_text())
  for c in source['cases']:
   for f in c['rows']:
    for p in f['attempts']:
     for t in p['trials']:expected.append((cohort,c['scene'],f['id'],p['plane'],t['compact'],folder,t['packet']))
 assert len(expected)==len(d['rows'])==3462;tiles=full=compact=raw_count=0
 for e,r in zip(expected,d['rows'],strict=True):
  assert e[:5]==(r['cohort'],r['scene'],r['id'],r['plane'],r['compact']) and e[6]==r['packet']
  packet=raw(e[5],e[6]);H=old.FRAME.unpack_from(packet);n,bw=H[3:5];assert(n,bw)==(r['blocks'],r['blocks_w'])
  golden=old.decode(packet,n,bw);reader=new.TileReader(packet,n,bw);h=hashlib.sha256()
  # Compare every delivered block immediately; input/oracle arrays are verifier-only.
  for i in range(n):
   block=next(reader);assert block.shape==(8,8) and block.dtype==np.int16 and block.nbytes==128
   np.testing.assert_array_equal(block,golden[i]);h.update(block.astype('<i2',copy=False).tobytes())
   assert not any(isinstance(v,np.ndarray) for v in vars(reader).values()),'iterator retains coefficient array'
  assert reader.finished and not reader.failed
  try:next(reader)
  except StopIteration:pass
  else:raise AssertionError('iterator exceeds declared blocks')
  assert h.hexdigest()==r['coefficient_sha256']==digest(golden.astype('<i2',copy=False).tobytes());assert reader.logical_workspace()==r['workspace']
  w=r['workspace'];assert w['coefficient_tile_bytes']==128 and w['retained_compressed_input_bytes']==len(packet) and w['probability_state_bytes']==(0 if H[2] else 352) and not w['full_coefficient_frame_staged']
  tiles+=n;full+=not r['compact'];compact+=r['compact'];raw_count+=bool(H[2])
 s=d['summary'];assert(s['trials'],s['coefficient_tiles'],s['full_trials'],s['compact_trials'],s['raw_trials'])==(len(expected),tiles,full,compact,raw_count)
 print(json.dumps(dict(replayed_AB38_packets=len(expected),replayed_coefficient_tiles=tiles,full_trials=full,compact_trials=compact,raw_real_trials=raw_count,raw_covered_by_unit_test=True,all_exact_coefficients=True,full_coefficient_frame_staged_by_subject=False,encoding_called=False,target_memory_or_FPS_proven=False)))
if __name__=='__main__':main()
