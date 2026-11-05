#!/usr/bin/env python3
"""Frozen-Python semantic replay of exported native fixtures, not C++ timing."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('native69_fixture_export',HERE/'export_fixtures.py');e=importlib.util.module_from_spec(s);sys.modules[s.name]=e;s.loader.exec_module(e)
h,w=e.h,e.w
r66=h.bound('native69_fixture_frozen66_receiver',HERE.parent/'python-game-canonical-tag-v66-study/receiver.py',h)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(desc):
 p=Path(desc['path']);assert not p.is_absolute()and'..'not in p.parts;data=(HERE/p).read_bytes();assert len(data)==desc['bytes']and sha(data)==desc['sha256'];return data

def main():
 m=h.load(HERE/'manifest.json')
 for path,digest in m['source_sha256'].items():assert sha((ROOT/path).read_bytes())==digest,path
 # Independently compare generated constants with their pinned normative source.
 text=(HERE/'generated_constants.hpp').read_text();expected={'PROFILE':np.frombuffer(w.PROFILES['CU66']['profile'],np.uint8),'DCT':h.m.ft.Q14,'QTABLES':np.array([[h.m.ft.qtable(s,bool(c))for s in(8,16,32)]for c in(0,1)]),'RECTS':np.array(h.f.f.n.RECTS)}
 expected.update({'SAFE'+str(i):p.astype(np.uint8).reshape(-1)for i,p in enumerate(h.f.f.safe_blocks())})
 for name,value in expected.items():
  match=re.search(r'\b'+name+r'\[[^;]+?=(\{[^;]+\});',text);assert match,name;actual=json.loads(match[1].replace('{','[').replace('}',']'));np.testing.assert_array_equal(actual,value)
 count=planes=tiles=words=0
 for case in m['cases']:
  rx=r66.Receiver('CU66')
  for row in case['rows']:
   packet=read(row['packet']);out=rx.receive(packet);canonical,patches,meta=out[:3];assert meta['frame_id']==row['id']and meta['key']==row['key'];assert w.tag_u8(canonical).hex()==row['canonical_tag'];assert not np.any(meta['vectors'])
   assert sha(b''.join(p.astype(np.uint8).tobytes()for p in canonical))==row['canonical_yuv_u8_sha256'];assert sha(b''.join(p['words'].astype('<u2').tobytes()for p in patches))==row['hud_words_u16le_sha256'];display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(canonical)),tuple(p['words']for p in patches));assert sha(display.astype('<u2').tobytes())==row['display_rgb565_u16le_sha256']
   for p,safe,full in zip(row['planes'],h.f.f.safe_blocks(),meta['coefficients'],strict=True):
    mask=read(p['safe_hidden_mask']);assert mask==safe.astype(np.uint8).tobytes();assert p['dispatch']in(5,6);raw=zlib.decompress(read(p['expected_coefficients']));assert len(raw)==128*p['blocks']and sha(raw)==p['expected_coefficients_raw_sha256'];decoded=h.arithmetic.decode(read(p['packet']),p['blocks'],p['blocks_w']);assert decoded.astype('<i2').tobytes()==raw;actual=full[~safe.reshape(-1)]if p['dispatch']==6 else full;np.testing.assert_array_equal(decoded,actual);planes+=1;tiles+=len(decoded)
   count+=1;words+=sum(p['words'].size for p in patches)
  print(json.dumps(dict(scene=case['scene'],frames=len(case['rows']))),flush=True)
 negative=h.load(HERE/'negative_manifest.json');assert len(negative['cases'])==28;key=read(negative['seed_key_packet']);valid=0
 for row in negative['cases']:
  data=read(row['packet'])
  if row['valid_frozen_CU66']:
   rx=r66.Receiver('CU66');rx.receive(key);rx.receive(data);valid+=1
 print(json.dumps(dict(frames=count,arithmetic_planes=planes,exact_encoded_coefficient_tiles=tiles,exact_HUD_words=words,source_pins=len(m['source_sha256']),valid_but_native_unsupported_packets=valid,generated_constants_exact=True,current_hardware_support=False)),flush=True)
if __name__=='__main__':main()
