#!/usr/bin/env python3
"""Causal fine/coarse cap admission with actual CP25 receipt and JA25 ACK."""
from pathlib import Path
import copy
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

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);sys.modules[name]=obj;spec.loader.exec_module(obj);return obj
n=module('capped25_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
m=module('capped25_combined',HERE.parent/'python-game-combined-motion-v25-study/model.py')
b=m.base
PROFILES={'capped_key_zero':dict(motion='zero',block=16,period=1,bg=16,key_bg=16,roi=8,lam=0,penalty=0,cap_fallback_bg=32),
          'capped_key_zero_rdo1':dict(motion='zero',block=16,period=1,bg=16,key_bg=16,roi=8,lam=1,penalty=0,cap_fallback_bg=32)}

def blob(data):
 stored=zlib.compress(data,9);path='objects/'+hashlib.sha256(stored).hexdigest()+'.zlib'
 (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(stored)
 return dict(path=path,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(stored).hexdigest())

def pins():
 paths={ROOT/p for p in n.pins()}
 paths|={HERE/p for p in ('benchmark.py','verify.py','test_replay.py','README.md')}
 for mod in list(sys.modules.values()):
  p=Path(getattr(mod,'__file__','') or '.')
  if p.is_file() and ROOT in p.resolve().parents and p.suffix=='.py':paths.add(p.resolve())
 return {p.relative_to(ROOT).as_posix():n.sha(p) for p in sorted(paths)}

def select_candidate(prepared,hud,lam):
 """Return actual smallest-priority admitted candidate, paying every attempt."""
 attempts=[];selected=None
 for bg in (16,32):
  mapped=b.roi.declared_map(720,480,n.ROIS,8,bg)
  began=time.perf_counter_ns();packet,expected,work=b.encode_prepared(prepared,mapped,rdo_lambda=lam);wall=(time.perf_counter_ns()-began)/1e6
  complete=len(packet)+len(hud)+m.PAIR.size+4
  admitted=complete<=m.CAP
  attempts.append(dict(background=bg,base_bytes=len(packet),hud_bytes=len(hud),binding_bytes=m.PAIR.size+4,complete_bytes=complete,admitted=admitted,rejection_reason=None if admitted else 'complete_CP25_exceeds_49152',packet=blob(packet),work=work,encode_wall_ms=wall))
  if admitted:selected=(packet,expected,work,bg);break
 if selected is None:raise RuntimeError('all fixed ROI8/bg16,32 attempts exceed complete cap')
 return selected,attempts

def run(inp,profile):
 cfg=PROFILES[profile];receiver=m.Receiver(epoch=25)
 selector=m.ui.PatchSelector(rectangles=n.RECTS)
 ref=None;refid=m.NO_REF;hudref=None;hudid=m.NO_REF;slot=0;rows=[]
 for source in inp['rows']:
  fid=source['id'];key=fid%24==0
  # Reset requests are provisional: sender state is committed only after ACK.
  base_ref=None if key else ref;base_refid=m.NO_REF if key else refid
  hu_ref=None if key else hudref;hu_refid=m.NO_REF if key else hudid
  source_slot=m.NO_SLOT if key else slot;dest=0 if key else 1-slot
  orig=n.original(source);src=n.source(source)
  began=time.perf_counter_ns();pending_selector=copy.deepcopy(selector)
  legacy=pending_selector.select(b.C.corpus.expand565(orig),98304)
  legacy_ms=(time.perf_counter_ns()-began)/1e6
  began=time.perf_counter_ns();hud,hudwork=m.encode_hud(legacy.patches,hu_ref,epoch=25,frame_id=fid,reference_id=hu_refid,motion=not key)
  hud_ms=legacy_ms+(time.perf_counter_ns()-began)/1e6
  began=time.perf_counter_ns();prepared=b.analyze_planes(src,base_ref,epoch=25,frame_id=fid,reference_id=base_refid,block_size=16,motion_mode='zero',penalty=0)
  analysis_ms=(time.perf_counter_ns()-began)/1e6
  (packet,expected,selected_work,bg),attempts=select_candidate(prepared,hud,0 if key else cfg['lam'])
  paid_base_ms=analysis_ms+sum(a['encode_wall_ms'] for a in attempts)
  work=dict(selected_work);work.update(analysis=prepared.work,analysis_paid_separately=False,forward_plane_calls=3,search_ms=prepared.work['search_ms'],transform_ms=prepared.work['transform_ms'],encoder_wall_ms=paid_base_ms,capped_attempts=len(attempts),selected_background=bg)
  began=time.perf_counter_ns();pair=m.encode_pair(packet,hud,epoch=25,frame_id=fid,source_slot=source_slot,destination_slot=dest,publish=True,key=key);bind_ms=(time.perf_counter_ns()-began)/1e6
  assert len(pair)==len(packet)+len(hud)+60<=m.CAP
  began=time.perf_counter_ns();decoded,patches,ack=receiver.receive(pair);receive_ms=(time.perf_counter_ns()-began)/1e6
  began=time.perf_counter_ns();ackmeta=m.validate_ack(ack,pair);ack_ms=(time.perf_counter_ns()-began)/1e6
  for x,y in zip(decoded,expected):np.testing.assert_array_equal(x,y)
  for item,(x,y,w,h) in zip(patches,n.RECTS):np.testing.assert_array_equal(item['words'],orig[y:y+h,x:x+w])
  bare=b.C.corpus.rgb565(b.ft.planes_to_rgb(decoded));hybrid=n.overlay(bare,tuple(p['words'] for p in patches))
  meta=b.parse(packet,expected_epoch=25)
  rows.append(dict(id=fid,key=key,publish=True,source_slot=source_slot,destination_slot=dest,reference_id=base_refid,hud_reference_id=hu_refid,source_input_sha256=source['input_rgb_sha256'],source_common_yuv_sha256=source['common_yuv420_u8_sha256'],base_bytes=len(packet),base_packet=blob(packet),work=work,decode_ms=receive_ms,reconstructed_yuv_tag=meta['reconstructed_tag'].hex(),bare_rgb565_sha256=n.digest(bare),hybrid_rgb565_sha256=n.digest(hybrid),bare=n.metric(orig,bare),hybrid=n.metric(orig,hybrid),hud_packet=blob(hud),hud_bytes=len(hud),hud_work=hudwork,legacy_encode_ms=legacy_ms,hud_encode_ms=hud_ms,packet=blob(pair),body_bytes=len(pair),ack=blob(ack),ack_meta=ackmeta,bind_ms=bind_ms,receive_ms=receive_ms,ack_validation_ms=ack_ms,analysis_wall_ms=analysis_ms,attempts=attempts,selected_background=bg))
  # These ACK-bound publications alone authorize the following source decision.
  ref,refid,hudref,hudid,slot,selector=decoded,fid,patches,fid,dest,pending_selector
 summary=n.summarize(rows)
 total=sum(r['body_bytes'] for r in rows)
 joint=dict(frames=48,complete_bytes=total,coded_body_Mbps_at30=total*5/1e6,max_complete_bytes=max(r['body_bytes'] for r in rows),cap_fit_frames=sum(r['body_bytes']<=m.CAP for r in rows),base_bytes=sum(r['base_bytes'] for r in rows),hud_bytes=sum(r['hud_bytes'] for r in rows),binding_bytes=48*60,active_mse=summary['hybrid']['active_mse'],hud_word_errors=summary['hybrid']['hud_word_errors'],coarse_fallback_frames=[r['id'] for r in rows if r['selected_background']==32],rejected_fine_attempts=sum(not a['admitted'] for r in rows for a in r['attempts']),paid_candidate_encodes=sum(len(r['attempts']) for r in rows),mean_paid_base_encode_ms=sum(r['work']['encoder_wall_ms'] for r in rows)/48,mean_paid_base_hud_encode_ms=sum(r['work']['encoder_wall_ms']+r['hud_encode_ms'] for r in rows)/48,ack_bytes=sum(r['ack']['raw_bytes'] for r in rows))
 case=dict(scene=inp['scene'],profile=profile,policy=cfg,rows=rows,summary=summary,joint_summary=joint)
 print(json.dumps(dict(scene=inp['scene'],profile=profile,summary=summary,joint_summary=joint)),flush=True);return case

def main():
 before=pins();old=n.load(n.V24/'results.json');cases=[]
 data=dict(schema='gamebub-native-motion-v25',experiment='capped-key-v25',source_sha256=before,versions=dict(python=platform.python_version(),numpy=np.__version__),cases=cases,counts=dict(unique_source_frames=96,selected_packets=192),scope=['Fixed two policies,48IDs×2scenes,epoch25,keys0/24,everyframepublish. Native720x480coded/720x405active,offline30IDs/s projection only.','Each source analyzed once;actual fineROI8/bg16 thenonlyon completeCP25overflowcoarseROI8/bg32 share preparedanalysis;all losingpacket/work bytes retained andcharged. RDO disabledkeys.','ExactactualHU25independentkeys, lastACKedHUDotherwise;PusesHD25motion. SerializedCP25,Receiver andJA25validation precede every sender/reference/cache commit.','No nativeESP32/FPGA,radio/QSPI,mappedresource/timing orphysical30fpsclaim. Decode_ms iswholejointreceive,includingHUDvalidation, not standalonebaseonly.','Base encoder_wall_ms charges analysis andallactual encode_prepared attempts,excludingfixtureload,HUD,blobexport,bind andreceive clocks retainedseparately.'])
 for inp in old['inputs']:
  for profile in PROFILES:
   cases.append(run(inp,profile));assert before==pins(),'source changed'
   (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
