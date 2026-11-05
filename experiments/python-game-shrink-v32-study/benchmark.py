"""Matched retained references: source-side trials, no causal-default claim."""
from pathlib import Path
import hashlib,json,sys,time,zlib
import numpy as np
import model as b
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];m=b.m
n=m.load_module('shrink32_native',HERE.parent/'python-game-native-motion-v25-study/benchmark.py')
p=m.load_module('shrink32_protocol',HERE.parent/'python-game-runtime-v28-study/protocol.py')
OLD=HERE.parent/'python-game-runtime-v28-study'
POLICIES=('baseline','shrink_strict','shrink_budget')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def blob(data):
 packed=zlib.compress(data,9);path='objects/'+hashlib.sha256(packed).hexdigest()+'.zlib'
 (HERE/'objects').mkdir(exist_ok=True);(HERE/path).write_bytes(packed)
 return dict(path=path,raw_bytes=len(data),raw_sha256=hashlib.sha256(data).hexdigest(),stored_sha256=hashlib.sha256(packed).hexdigest())
def pins():
 old=json.loads((OLD/'results.json').read_text());paths={ROOT/q for q in old['source_sha256']}
 paths|={OLD/'results.json',HERE/'model.py',HERE/'benchmark.py',HERE/'test_model.py',HERE.parent/'python-game-entropy-v29-study/model.py'}
 return {q.relative_to(ROOT).as_posix():sha(q) for q in sorted(paths)}
def hybrid(source,out):
 patches=tuple(source[y:y+h,x:x+w] for x,y,w,h in n.RECTS)
 image=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(out)),patches)
 return image,n.metric(source,image)
def summary(rows,policy):
 rr=[r['candidates'][policy] for r in rows];samples=sum(r['hybrid']['active_channel_samples'] for r in rr)
 return dict(frames=len(rr),complete_bytes=sum(r['complete_bytes'] for r in rr),base_bytes=sum(r['base_bytes'] for r in rr),
 active_mse=sum(r['hybrid']['active_squared_error'] for r in rr)/samples,
 encode_ms=sum(r['encode_ms'] for r in rr)/len(rr),changed_blocks=sum(r['work'].get('changed_blocks',0) for r in rr),
 removed_coefficients=sum(r['work'].get('removed_coefficients',0) for r in rr),changed_coefficients=sum(r['work'].get('changed_coefficients',0) for r in rr),selected_alternative_planes=sum(r['work'].get('selected_alternative_planes',0) for r in rr),
 all_cap_fit=all(r['complete_bytes']<=49152 for r in rr))
def main():
 before=pins();old=json.loads((OLD/'results.json').read_text());inputs=json.loads((n.V24/'results.json').read_text())['inputs'];cases=[]
 for inp in inputs:
  prior=next(c for c in old['cases'] if c['scene']==inp['scene'] and c['policy']=='exhaustive');ref=None;rows=[]
  for src,r in zip(inp['rows'][:12],prior['rows'][:12]):
   fid=src['id'];source=n.source(src);original=n.original(src)
   if r['key']:ref=None
   prepared=m.base.analyze_planes(source,ref,epoch=25,frame_id=fid,reference_id=r['reference_id'],block_size=32,
    motion_mode='zero' if r['selected_kind']=='zero' else 'block',motion_precision='half',penalty=0)
   q=m.roi.declared_map(720,480,n.ROIS,8,r['selected_background']);records={};baseline=None
   order=POLICIES[fid%3:]+POLICIES[:fid%3]
   for policy in order:
    start=time.perf_counter_ns()
    packet,out,work=m.encode_prepared(prepared,q) if policy=='baseline' else b.encode_prepared(prepared,q,policy=policy)
    elapsed=(time.perf_counter_ns()-start)/1e6
    decoded,meta=m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if r['key'] else r['reference_id'])
    for a,c in zip(out,decoded):np.testing.assert_array_equal(a,c)
    image,metric=hybrid(original,out)
    hud=n.raw(r['hud_packet'],ROOT/r['hud_packet']['directory'])
    pair=p.seal(p.PAIR.pack(b'CP27',1,p.PUBLISH|(p.KEY if r['key'] else 0),25,fid,r['source_slot'],r['destination_slot'],len(packet),len(hud),p.digest(packet),p.digest(hud))+packet+hud)
    p.parse_pair(pair)
    records[policy]=dict(base_packet=blob(packet),packet=blob(pair),base_bytes=len(packet),complete_bytes=len(pair),encode_ms=elapsed,work=work,hybrid=metric,
                         hybrid_rgb565_sha256=n.digest(image),reconstructed_tag=meta['reconstructed_tag'].hex())
    if policy=='baseline':baseline=out;assert packet==n.raw(r['base_packet'],OLD)
   for policy in POLICIES[1:]:assert records[policy]['base_bytes']<=records['baseline']['base_bytes']
   rows.append(dict(id=fid,key=r['key'],reference_id=r['reference_id'],source_slot=r['source_slot'],destination_slot=r['destination_slot'],selected_kind=r['selected_kind'],background=r['selected_background'],hud_packet=r['hud_packet'],candidates=records))
   ref=baseline
  item=dict(scene=inp['scene'],rows=rows,summaries={policy:summary(rows,policy) for policy in POLICIES});cases.append(item)
  print(json.dumps(dict(scene=inp['scene'],summaries=item['summaries'])),flush=True)
 assert before==pins()
 data=dict(schema='gamebub-shrink-v32',source_sha256=before,cases=cases,scope=['24 matched-source decisions against retained accepted v28 decoded refs; trial outputs never become laterrefs.',
  'Full720x480 coded/720x405active and exactHUD; GM27 syntax unchanged; actualCP27 envelopes and everytrial paid.',
  'Python host timings, not ESP32/native/FPGA/physical30fps proof; parentcampaign measures causal histories.'])
 (HERE/'results.json').write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
