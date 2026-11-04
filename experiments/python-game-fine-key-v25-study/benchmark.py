#!/usr/bin/env python3
"""Fine-key full native cohorts; keep root benchmark helpers unmodified."""
from pathlib import Path
import hashlib
import importlib.util
import json
import platform
import sys
import time
import zlib
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NATIVE=HERE.parent/'python-game-native-motion-v25-study'
spec=importlib.util.spec_from_file_location('fine25_native_helpers',NATIVE/'benchmark.py')
n=importlib.util.module_from_spec(spec);sys.modules[spec.name]=n;spec.loader.exec_module(n)
b=n.b
PROFILES={
 'finekey_zero':dict(motion='zero',block=16,period=1,bg=16,key_bg=16,roi=8,lam=0,penalty=0),
 'finekey_zero_rdo1':dict(motion='zero',block=16,period=1,bg=16,key_bg=16,roi=8,lam=1,penalty=0),
 'finekey_block32_rdo1':dict(motion='block',block=32,period=1,bg=16,key_bg=16,roi=8,lam=1,penalty=512)}

def blob(data):
 stored=zlib.compress(data,9);path='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
 (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(stored)
 return dict(path=path,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())

def pins():
 paths={ROOT/p for p in n.pins()}
 paths|={NATIVE/'benchmark.py',HERE/'benchmark.py',HERE/'verify.py',HERE/'test_replay.py',HERE/'README.md'}
 for mod in list(sys.modules.values()):
  p=Path(getattr(mod,'__file__','') or '.')
  if p.is_file() and ROOT in p.resolve().parents and p.suffix=='.py':paths.add(p.resolve())
 return {p.relative_to(ROOT).as_posix():n.sha(p) for p in sorted(paths)}

def run(inp,profile):
 cfg=PROFILES[profile];ref=None;refid=b.NO_REF;slot=0;rows=[]
 for row in inp['rows']:
  fid=row['id'];key=fid%24==0
  if key:ref,refid,slot=None,b.NO_REF,0
  source=n.source(row)
  mapped=b.roi.declared_map(720,480,n.ROIS,cfg['roi'],cfg['key_bg'] if key else cfg['bg'])
  packet,expected,work=b.encode_planes(source,ref,mapped,epoch=25,frame_id=fid,reference_id=refid,block_size=cfg['block'],motion_mode=cfg['motion'],penalty=cfg['penalty'],rdo_lambda=0 if key else cfg['lam'])
  began=time.perf_counter_ns();decoded,meta=b.decode(packet,ref,expected_epoch=25,expected_reference_id=None if key else refid);decode_ms=(time.perf_counter_ns()-began)/1e6
  for x,y in zip(decoded,expected):np.testing.assert_array_equal(x,y)
  orig=n.original(row);patches=tuple(orig[y:y+h,x:x+w] for x,y,w,h in n.RECTS)
  bare=b.C.corpus.rgb565(b.ft.planes_to_rgb(decoded));hybrid=n.overlay(bare,patches);dest=0 if key else 1-slot
  rows.append(dict(id=fid,key=key,publish=True,source_slot=255 if key else slot,destination_slot=dest,reference_id=refid,source_input_sha256=row['input_rgb_sha256'],source_common_yuv_sha256=row['common_yuv420_u8_sha256'],base_bytes=len(packet),base_packet=blob(packet),work=work,decode_ms=decode_ms,reconstructed_yuv_tag=meta['reconstructed_tag'].hex(),bare_rgb565_sha256=n.digest(bare),hybrid_rgb565_sha256=n.digest(hybrid),bare=n.metric(orig,bare),hybrid=n.metric(orig,hybrid)))
  ref,refid,slot=decoded,fid,dest
 result=dict(scene=inp['scene'],profile=profile,policy=cfg,rows=rows,summary=n.summarize(rows))
 print(json.dumps(dict(scene=inp['scene'],profile=profile,summary=result['summary'])),flush=True)
 return result

def main():
 before=pins();old=n.load(n.V24/'results.json');cases=[]
 result=dict(schema='gamebub-native-motion-v25',experiment='finekey-v25',source_sha256=before,versions=dict(python=platform.python_version(),numpy=np.__version__),cases=cases,counts=dict(unique_source_frames=96,encoded_decoded_packets=288),scope=['Three fixed full48 profiles on both retained v24native windows,720x480coded/720x405active. Keys0/24 have explicitROI8/bg16 andRDOdisabled.','Epoch25,fid0..47,every successfullydecoded frame publishes the next reconstructedACKreference. No originalsource reference shortcut.','ActualGM25packets are retained with compatible source/destination slots andreferenceIDs. ExactRGB565HUD is overlaid only for quality; actualHU25/CP25combine is parentwork.','All one-shotencode/decode work paid. No physical30fps, nativeESP32/radio/QSPI, timing/FPGAfit or newqualityequivalenceclaim.'])
 for inp in old['inputs']:
  for profile in PROFILES:
   cases.append(run(inp,profile));assert before==pins(),'source changed'
   (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
