#!/usr/bin/env python3
"""Small fixed-profile native R/D probe, using exact decoded reference banks."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE=HERE.parent/'python-game-base-motion-v25-study'
STD=HERE.parent/'python-game-standard-v24-study'
HUD=HERE.parent/'python-game-hud-motion-v25-study'
spec=importlib.util.spec_from_file_location('probe25_base', BASE/'model.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
RECTS=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
REGIONS=((16,48,192,80),(160,352,400,80))
POLICIES=(
 ('zero_r8_b16_l0','zero',16,0,8,16,0),
 ('block16_r8_b16_l0','block',16,256,8,16,0),
 ('block32_r8_b16_l0','block',32,512,8,16,0),
 ('zero_r8_b32_l0','zero',16,0,8,32,0),
 ('zero_r8_b16_l4','zero',16,0,8,16,4),
 ('zero_r8_b16_l16','zero',16,0,8,16,16),
 ('block16_r8_b16_l4','block',16,256,8,16,4),
 ('zero_r16_b32_l4','zero',16,0,16,32,4))

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def raw(desc):
 p=Path(desc['path']);assert not p.is_absolute() and '..' not in p.parts
 data=(STD/p).read_bytes();assert hashlib.sha256(data).hexdigest()==desc['stored_sha256']
 dec=zlib.decompressobj();out=dec.decompress(data,desc['raw_bytes']+1)
 assert dec.eof and not dec.unused_data and not dec.unconsumed_tail and len(out)==desc['raw_bytes']
 assert hashlib.sha256(out).hexdigest()==desc['raw_sha256'];return out

def inputs(row):
 words=np.frombuffer(raw(row['original_rgb565']),'<u2').reshape(480,720)
 flat=np.frombuffer(raw(row['common_yuv420_u8']),np.uint8)
 assert flat.size==720*480*3//2
 n=720*480;c=n//4
 planes=(flat[:n].reshape(480,720),flat[n:n+c].reshape(240,360),flat[n+c:].reshape(240,360))
 assert hashlib.sha256(b''.join(p.tobytes() for p in planes)).hexdigest()==row['common_yuv420_u8_sha256']
 return words,planes

def metric(source,display):
 error=(b.C.corpus.expand565(source).astype(np.int32)-b.C.corpus.expand565(display).astype(np.int32)).astype(np.int64)**2
 sse=int(error[37:442].sum());samples=405*720*3
 hud_errors=sum(int(np.count_nonzero(source[y:y+h,x:x+w]!=display[y:y+h,x:x+w])) for x,y,w,h in RECTS)
 return dict(active_squared_error=sse,active_channel_samples=samples,active_mse=sse/samples,hud_word_errors=hud_errors)

def pins(source):
 paths={STD/'results.json',HUD/'results.json',BASE/'model.py',HERE/'probe.py',HERE/'README.md'}
 for scene in source['inputs']:
  for row in scene['rows'][:12]:
   paths|={STD/row[name]['path'] for name in ('original_rgb565','common_yuv420_u8')}
 for module in list(sys.modules.values()):
  p=Path(getattr(module,'__file__','') or '.')
  if p.is_file() and ROOT in p.resolve().parents and p.suffix=='.py':paths.add(p.resolve())
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}

def run(source,policy,hud_rows):
 name,motion,bs,penalty,roi,bg,lam=policy
 mapped=b.roi.declared_map(720,480,REGIONS,roi,bg)
 ref=None;rows=[]
 for i,item in enumerate(source['rows'][:12]):
  original,planes=inputs(item)
  start=time.perf_counter_ns()
  packet,rebuilt,work=b.encode_planes(planes,ref,mapped,epoch=1,frame_id=i,reference_id=b.NO_REF if i==0 else i-1,block_size=bs,motion_mode=motion,penalty=penalty,rdo_lambda=lam)
  encode_ms=(time.perf_counter_ns()-start)/1e6
  start=time.perf_counter_ns()
  decoded,metadata=b.decode(packet,ref,expected_epoch=1,expected_reference_id=None if i==0 else i-1)
  decode_ms=(time.perf_counter_ns()-start)/1e6
  for expected,actual in zip(rebuilt,decoded):np.testing.assert_array_equal(expected,actual)
  start=time.perf_counter_ns()
  display=b.C.corpus.rgb565(b.ft.planes_to_rgb(decoded))
  for x,y,w,h in RECTS:display[y:y+h,x:x+w]=original[y:y+h,x:x+w]
  met=metric(original,display);assert not met['hud_word_errors']
  display_metric_ms=(time.perf_counter_ns()-start)/1e6
  hud_bytes=hud_rows[i]['new_hud_bytes']
  rows.append(dict(id=i,source_input_sha256=item['input_rgb_sha256'],common_yuv_sha256=item['common_yuv420_u8_sha256'],base_bytes=len(packet),projected_hud_bytes=hud_bytes,projected_hybrid_bytes=len(packet)+hud_bytes+57,packet_sha256=hashlib.sha256(packet).hexdigest(),display_rgb565_sha256=digest(display),metric=met,encode_ms=encode_ms,decode_ms=decode_ms,display_metric_ms=display_metric_ms,work=work))
  # Only successfully decoded/reconstructed output is the next ACKed reference.
  ref=decoded
 sse=sum(r['metric']['active_squared_error'] for r in rows);samples=sum(r['metric']['active_channel_samples'] for r in rows)
 summary=dict(frames=len(rows),base_bytes=sum(r['base_bytes'] for r in rows),base_Mbps_at30=sum(r['base_bytes'] for r in rows)*8*30/len(rows)/1e6,projected_hybrid_Mbps_at30=sum(r['projected_hybrid_bytes'] for r in rows)*8*30/len(rows)/1e6,maximum_base_bytes=max(r['base_bytes'] for r in rows),projected_hybrid_cap_fit=sum(r['projected_hybrid_bytes']<=49152 for r in rows),active_mse=sse/samples,active_psnr_db=10*math.log10(65025/(sse/samples)),hud_word_errors=0,key_bytes=rows[0]['base_bytes'],p_mean_bytes=sum(r['base_bytes'] for r in rows[1:])/11,mean_encode_ms=sum(r['encode_ms'] for r in rows)/len(rows),mean_decode_ms=sum(r['decode_ms'] for r in rows)/len(rows),rdo_zeroed_blocks=sum(r['work']['rdo']['zeroed_blocks'] for r in rows),sad_sample_operations=sum(r['work']['search']['sad_sample_operations'] for r in rows))
 result=dict(scene=source['scene'],policy=name,motion_mode=motion,block_size=bs,penalty=penalty,roi_scale=roi,background_scale=bg,rdo_lambda=lam,rows=rows,summary=summary)
 print(json.dumps({k:result[k] for k in ('scene','policy','summary')}),flush=True)
 return result

def main():
 source=load(STD/'results.json');hud=load(HUD/'results.json');before=pins(source);cases=[]
 for scene in source['inputs']:
  hud_rows=next(c['rows'] for c in hud['cases'] if c['name']==scene['scene'])
  for policy in POLICIES:cases.append(run(scene,policy,hud_rows))
  print('SCENE_COMPLETE '+scene['scene'],flush=True)
 assert pins(source)==before,'source changed'
 data=dict(schema='gamebub-base-rdo-probe-v25',source_sha256=before,policies=POLICIES,cases=cases,counts=dict(unique_source_frames=24,encoded_decoded_candidates=24*len(POLICIES)),versions=dict(python=platform.python_version(),numpy=np.__version__),scope=['Exploratory fixed-profile first12 frames per retained native scene, one key0 and eleven P frames. No causal adaptive selection, cap admission, transport or new full48-frame campaign.','Every source encodes and decodes a real GM25 packet; only decoded planes define the next ACKed reference.','RGB565 active720x405 quality against retained original on720x480 canvas, with exact HUD words overlaid. All byte/packet hashes include actual headers and coefficient/motion payloads.','Projected complete hybrid bytes add actual already-retained HD25 cache-projection bytes and57 binding bytes; not a serialized new combined packet. No hardware, native CPU or physical30fps claim.','Source-YUV-SSE skip RDO is lossy and not equal to RGB MSE; measured final RGB565 metrics decide the tradeoff. All one-shot candidate encode/decode costs paid; conversion/quality timing retained separately.'])
 (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
