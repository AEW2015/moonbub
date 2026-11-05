#!/usr/bin/env python3
"""SHA byte fixtures: hashlib oracle, NIST known answers, retained canonical keys."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=HERE/'fixtures'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 def add(name,data):
  expected=hashlib.sha256(data).hexdigest();stored=zlib.compress(data,9);path=OUT/(hashlib.sha256(stored).hexdigest()+'.zlib');path.write_bytes(stored)
  rows.append((name,'fixtures/'+path.name,str(len(data)),expected));return expected
 assert add('NIST_empty',b'')=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
 assert add('NIST_abc',b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
 assert add('NIST_two_block',b'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq')=='248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1'
 assert add('NIST_million_a',b'a'*1000000)=='cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0'
 rng=np.random.default_rng(69031)
 for n in(1,2,3,7,15,31,54,55,56,57,63,64,65,119,120,127,128,129,255,256,257,1023,1024,1025):add('boundary_'+str(n),rng.integers(0,256,n,dtype=np.uint8).tobytes())
 for i in range(64):
  n=int(rng.integers(0,4097));add('random69031_'+str(i),rng.integers(0,256,n,dtype=np.uint8).tobytes())
 old=module('hash69_independent43',ROOT/'experiments/python-game-direct-rx-v43-study/verify.py');rx=old.direct_module();source=ROOT/'experiments/python-game-binary-qual-v40-study';data=json.loads((source/'results.json').read_text());canonical=[]
 for case in data['cases']:
  row=case['rows'][0];planes,_,meta,_=rx.Receiver().receive(old.raw(row['packet'],source));assert meta['key']and old.m.C.reference_tag(planes).hex()==row['normalized_tag']
  raw=struct.pack('<HH',720,480)+b''.join(p.astype(np.uint8).tobytes()for p in planes);assert len(raw)==518404
  expected=add('canonical_'+case['scene'],raw);canonical.append(dict(scene=case['scene'],source_packet=row['packet'],sha256=expected,canonical_bytes=len(raw)))
 add('canonical_size_random',struct.pack('<HH',720,480)+rng.integers(0,256,518400,dtype=np.uint8).tobytes())
 add('canonical_size_zero',struct.pack('<HH',720,480)+bytes(518400))
 (HERE/'fixtures.tsv').write_text('\n'.join('\t'.join(r)for r in rows)+'\n')
 sources=[HERE/'export_fixtures.py',source/'results.json',ROOT/'experiments/python-game-direct-rx-v43-study/verify.py']
 (HERE/'fixture-evidence.json').write_text(json.dumps(dict(schema='cu66-sha256-v69-fixtures',cases=len(rows),canonical=canonical,random_seed=69031,
  source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},
  primary_references=['https://csrc.nist.gov/pubs/fips/180-4/upd1/final','https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf'],no_new_game_captures=True),indent=2)+'\n')
 print(json.dumps(dict(cases=len(rows),actual_canonical_messages=4,canonical_message_bytes=518404)))
if __name__=='__main__':main()
