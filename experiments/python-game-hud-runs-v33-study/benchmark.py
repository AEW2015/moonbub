#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,sys,time,zlib
MODULE_STARTED=time.perf_counter_ns()
import numpy as np
import model as m
MODULE_IMPORT_MS=(time.perf_counter_ns()-MODULE_STARTED)/1e6
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OLD=HERE.parent/'python-game-hud-v32-study'
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
 started=time.perf_counter_ns();old=json.loads((OLD/'results.json').read_text());cases=[]
 paths={OLD/'results.json',*(HERE/f for f in ('baseline.py','model.py','decoder.py','benchmark.py','test_model.py','verify.py','resources.py'))}
 for case in old['cases']:
  ref=None;rows=[]
  for r in case['rows']:
   if r['key']:ref=None
   desc=r['baseline'];folder=ROOT/desc['directory'];paths.add(folder/desc['path']);hu25=read(desc,folder)
   paths.add(OLD/r['packet']['path']);hx32=read(r['packet'],OLD)
   rid=None if ref is None else r['reference_id']
   expected,oldmeta=m.p.decode_hud(hu25,ref,expected_epoch=25,expected_reference_id=rid)
   t=time.perf_counter_ns();packet,work=m.encode_hud(hu25,hx32,ref,expected_reference_id=rid);encode_ms=(time.perf_counter_ns()-t)/1e6
   t=time.perf_counter_ns();output,meta=m.decode_hud(packet,ref,expected_epoch=25,expected_reference_id=rid);decode_ms=(time.perf_counter_ns()-t)/1e6
   for a,b in zip(output,expected):np.testing.assert_array_equal(a['words'],b['words']);assert a['rect']==b['rect']
   assert meta['reconstructed_tag']==oldmeta['reconstructed_tag'] and sum(x['words'].size for x in output)==21120
   rows.append(dict(id=r['id'],key=r['key'],reference_id=r['reference_id'],hu25=desc,v32=r['packet'],packet=blob(packet),hu25_bytes=len(hu25),v32_bytes=len(hx32),bytes=len(packet),
                    encode_extra_ms=encode_ms,decode_ms=decode_ms,reference_tag=meta['reference_tag'].hex(),reconstructed_tag=meta['reconstructed_tag'].hex(),exact_hud_words=21120,work=work))
   ref=output
   if (r['id']+1)%12==0:print(json.dumps(dict(scene=case['scene'],frames=r['id']+1)),flush=True)
  n=len(rows);hu25=sum(r['hu25_bytes'] for r in rows);v32=sum(r['v32_bytes'] for r in rows);total=sum(r['bytes'] for r in rows)
  summary=dict(frames=n,hu25_hud_bytes=hu25,v32_hud_bytes=v32,new_hud_bytes=total,saving_vs_hu25_bytes=hu25-total,saving_vs_v32_bytes=v32-total,
   saving_vs_hu25_percent=100*(1-total/hu25),saving_vs_v32_percent=100*(1-total/v32),new_HUD_Mbps_at30=total*240/n/1e6,
   selected_new_frames=sum(r['work']['selected_new'] for r in rows),selected_run_patches=sum(d['selected_kind']==4 for r in rows for d in r['work']['patches']),
   exact_hud_words=n*21120,mean_extra_encode_ms=sum(r['encode_extra_ms'] for r in rows)/n,mean_decode_ms=sum(r['decode_ms'] for r in rows)/n,
   max_extra_encode_ms=max(r['encode_extra_ms'] for r in rows),maximum_packet_bytes=max(r['bytes'] for r in rows))
  cases.append(dict(scene=case['scene'],rows=rows,summary=summary));print(json.dumps(dict(scene=case['scene'],summary=summary)),flush=True)
 paths|={Path(v.__file__).resolve() for v in list(sys.modules.values()) if getattr(v,'__file__',None) and Path(v.__file__).resolve().is_relative_to(ROOT)}
 output=dict(schema='gamebub-run-HUD-v33',source_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},cases=cases,
  measured_module_import_setup_ms=MODULE_IMPORT_MS,measured_total_benchmark_wall_ms=(time.perf_counter_ns()-started)/1e6,
  timing_contract=dict(paid_extra='Per-frame timer includes both inherited packet decodes, reference binding, every predictor recipe, all three channel schemes, all 15 Rice k sizes, Huffman construction and actual bits, comparisons and sealing.',
   excluded_inherited='HU25 generation/motion search, v32 generation/trials, and source capture were already paid in retained fixtures; none regenerated. Complete sender cost must include or share these.',
   excluded_extra='Module imports measured separately; artifact compression, oracle comparison and source pins excluded from encoder timer but included in benchmark wall. Final results JSON serialization/write follows the benchmark-wall sample. /usr/bin/time in run.log includes full process startup/import/setup/write; tests and verification have separate logs.'),
  scope=['96 retained exact HUD frames; own accepted exact reference resets at retained key boundaries; no future input.',
   'New negotiated HX33/HS33 and patch kind4; original HU25/HX32 syntax unchanged and byte fallback on tie/larger.',
   'Identical improved HUD must accompany custom, HEVC and AV1; common-sidecar savings do not close their basecodec rate gap.',
   'Host prototype only; no fitted hardware, native service timing, ESP32 heap or board proof.'])
 (HERE/'results.json').write_text(json.dumps(output,separators=(',',':'))+'\n')
if __name__=='__main__':run()
