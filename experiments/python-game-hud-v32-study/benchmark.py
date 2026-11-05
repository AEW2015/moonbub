#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys,time,zlib
import numpy as np
import model as m
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=HERE.parent/'python-game-controller-v30-study'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(d,folder):
 q=Path(d['path']);assert not q.is_absolute() and '..' not in q.parts
 packed=(folder/q).read_bytes();assert hashlib.sha256(packed).hexdigest()==d['stored_sha256']
 dc=zlib.decompressobj();raw=dc.decompress(packed,d['raw_bytes']+1)
 assert dc.eof and not dc.unused_data and not dc.unconsumed_tail and len(raw)==d['raw_bytes'] and hashlib.sha256(raw).hexdigest()==d['raw_sha256'];return raw
def blob(data):
 packed=zlib.compress(data,9);name='objects/'+hashlib.sha256(packed).hexdigest()+'.zlib';(HERE/'objects').mkdir(exist_ok=True);(HERE/name).write_bytes(packed)
 return dict(path=name,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest())
def run():
 old=json.loads((OLD/'results.json').read_text());cases=[];paths={OLD/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py'}
 for case in old['cases']:
  if case['policy']!='band_strict':continue
  ref=None;rows=[]
  for r in case['rows']:
   if r['key']:ref=None
   desc=r['hud_packet'];folder=ROOT/desc['directory'];paths.add(folder/desc['path']);baseline=read(desc,folder)
   expected,oldmeta=m.p.decode_hud(baseline,ref,expected_epoch=25,expected_reference_id=None if ref is None else r['reference_id'])
   t=time.perf_counter_ns();packet,work=m.encode_hud(baseline,ref,expected_reference_id=None if ref is None else r['reference_id']);encode_ms=(time.perf_counter_ns()-t)/1e6
   t=time.perf_counter_ns();output,meta=m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=None if ref is None else r['reference_id']);decode_ms=(time.perf_counter_ns()-t)/1e6
   for a,b in zip(output,expected):np.testing.assert_array_equal(a['words'],b['words']);assert a['rect']==b['rect']
   assert m.p.hud_tag(output)==m.p.hud_tag(expected)==oldmeta['reconstructed_tag'] and sum(x['words'].size for x in output)==21120
   rows.append(dict(id=r['id'],key=r['key'],reference_id=r['reference_id'],baseline=desc,packet=blob(packet),baseline_bytes=len(baseline),bytes=len(packet),encode_extra_ms=encode_ms,decode_ms=decode_ms,
                    reference_tag=meta['reference_tag'].hex(),reconstructed_tag=meta['reconstructed_tag'].hex(),exact_hud_words=21120,work=work))
   ref=output
   if (r['id']+1)%12==0:print(json.dumps(dict(scene=case['scene'],frames=r['id']+1)),flush=True)
  total=sum(r['bytes'] for r in rows);baseline=sum(r['baseline_bytes'] for r in rows)
  summary=dict(frames=len(rows),baseline_hud_bytes=baseline,new_hud_bytes=total,saving_bytes=baseline-total,saving_percent=100*(1-total/baseline),
   baseline_HUD_Mbps_at30=baseline*240/len(rows)/1e6,new_HUD_Mbps_at30=total*240/len(rows)/1e6,
   selected_new_frames=sum(r['work']['selected_new'] for r in rows),selected_new_patches=sum(p['selected_kind']==3 for r in rows for p in r['work']['patches']),
   exact_hud_words=21120*len(rows),mean_extra_encode_ms=sum(r['encode_extra_ms'] for r in rows)/len(rows),mean_decode_ms=sum(r['decode_ms'] for r in rows)/len(rows),maximum_packet_bytes=max(r['bytes'] for r in rows))
  cases.append(dict(scene=case['scene'],rows=rows,summary=summary));print(json.dumps(dict(scene=case['scene'],summary=summary)),flush=True)
 paths|={Path(v.__file__).resolve() for v in list(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
 output=dict(schema='gamebub-huffman-HUD-v32',source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},cases=cases,
  scope=['96 actual exact-HUD source decisions with own accepted exact reconstructed HUD reference; no future frame input.',
   'Baseline HU25 packets already constructed; their motion search and original encoding cost excluded, not free complete source service.',
   'New HX32/HS32 syntax requires negotiated host/FPGA support; no native endpoint/FPGA fit/ESP32 memory throughput proof.',
   'Improved HUD must be applied to HEVC/AV1 as well as custom for a fair hybrid comparison; no custom-only bitrate win claimed.'])
 (HERE/'results.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
if __name__=='__main__':run()
