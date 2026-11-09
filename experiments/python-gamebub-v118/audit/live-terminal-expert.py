#!/usr/bin/env python3
"""Independent retained-byte/C2/job/semantic review; does not run RTL or Vivado."""
import collections
import gzip
import hashlib
import json
from pathlib import Path

R=Path(__file__).resolve().parents[3]
AREA=R/'experiments/python-gamebub-v118'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def pin(p):return dict(path=str(p.relative_to(R)),sha256=sha(p))
def packed(p,meta):
 assert sha(p)==meta['sha256'];raw=gzip.decompress(p.read_bytes())
 assert hashlib.sha256(raw).hexdigest()==meta['raw_sha256']
 assert len(raw.splitlines())==meta['rows']
 return raw
def sem(rows):
 return collections.Counter(json.dumps({k:v for k,v in q.items()if k not in('first_cycle','last_cycle')},sort_keys=True)for q in rows)
def hashes(canonical,hud,packet):
 context=bytes.fromhex('286386153d5fd535a7aabf60493040f99831315d6e107d7242bc39872b18d6b0')
 def domain(k):return b'CU66V82C2\x00'+k+b'\x00'
 def digest(b):return hashlib.sha256(b).hexdigest()
 jobs=[];nodes={};offset=0;leaf=0
 for plane,tiles in enumerate((5400,1350,1350)):
  for start in range(0,tiles,16):
   count=min(16,tiles-start);width=720 if plane==0 else 360;tile_width=width//8
   # Physical accepted memory is raster order. The validator consumes each
   # complete8x8 tile in tile order; never treat raster bytes as tile-major.
   body=bytes(canonical[offset+(tile//tile_width*8+pixel//8)*width+(tile%tile_width*8+pixel%8)]
              for tile in range(start,start+count)for pixel in range(64))
   message=domain(b'L')+context+bytes([plane])+start.to_bytes(4,'big')+count.to_bytes(2,'big')+body
   h=digest(message);nodes[512+leaf]=bytes.fromhex(h);jobs.append((0,512+leaf,h));leaf+=1
  offset+=tiles*64
 assert leaf==508 and offset==len(canonical)==518400
 for n in range(508,512):
  h=digest(domain(b'E')+context+n.to_bytes(4,'big')+(512).to_bytes(4,'big'))
  nodes[512+n]=bytes.fromhex(h);jobs.append((1,512+n,h))
 width=256;level=1
 while width:
  for index in range(width):
   h=digest(domain(b'N')+level.to_bytes(2,'big')+index.to_bytes(4,'big')+nodes[2*(width+index)]+nodes[2*(width+index)+1])
   nodes[width+index]=bytes.fromhex(h);jobs.append((2,width+index,h))
  width//=2;level+=1
 hud_sha=hashlib.sha256(hud).digest();jobs.append((3,0,hud_sha.hex()))
 # This retained fixture is an independent keyframe: previous root is zero.
 assert packet[5]==1
 seal=digest(domain(b'S')+context+packet[8:16]+packet[5:6]+packet[16:24]+bytes(32)+hud_sha+nodes[1])
 jobs.append((4,0,seal));return jobs,nodes[1].hex(),hud_sha.hex(),seal
def main():
 selector=AREA/'integrated-study/live-guard/results.json';s=load(selector);receipt=R/s['path'];q=load(receipt)
 assert s['sha256']==sha(receipt) and q['status']==s['status'] and q['actual_RTL_run'] is True
 for n,h in q['source_sha256'].items():assert sha(R/n)==h,n
 for n,h in q['artifact_sha256'].items():assert sha(receipt.parent/n)==h,n
 control=q['baseline_B_guard_semantic_parent_control'];old_receipt=R/control['receipt'];old=load(old_receipt)
 assert sha(old_receipt)==control['receipt_sha256'] and sha(R/control['selector'])==control['selector_sha256']
 selected=q['proof_bindings']['selected_component'];spatial=load(R/selected['path'])
 assert sha(R/selected['path'])==selected['sha256'] and sha(R/selected['receipt'])==selected['receipt_sha256']
 assert spatial['source_origins']==q['source_origins']
 for v in q['source_origins'].values():assert sha(R/v['path'])==v['sha256']
 validation=gzip.decompress((R/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz').read_bytes()).decode()
 v=next(line.split('\t')for line in validation.splitlines()if line.startswith('c0_f0\t'));packet=bytes.fromhex(v[3]);hud=bytes.fromhex(v[5])
 canonical_path=R/'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz'
 canonical_rows=gzip.decompress(canonical_path.read_bytes()).decode().splitlines()
 canonical=bytes.fromhex(next(line.split('\t')[-1]for line in canonical_rows if line.startswith('actual_001\t')))
 expected_jobs,root,hud_sha,seal=hashes(canonical,hud,packet)
 assert (root,hud_sha,seal)==(v[8],v[7],v[9])
 reviews=[]
 for row in q['runs']:
  variant,profile=row['variant'],row['profile'];baseline=next(x for x in old['runs']if(x['variant'],x['profile'])==(variant,profile))
  actual=packed(receipt.parent/row['artifacts']['actual.tsv']['path'],row['artifacts']['actual.tsv']).decode().splitlines()
  bodies={a:bytes.fromhex(c)for a,b,c in(map(lambda x:x.split('\t'),actual))}
  assert bodies['actual_001']==canonical and bodies['accepted_actual_001']==canonical+hud
  raw_hash=packed(receipt.parent/row['artifacts']['hashes.jsonl']['path'],row['artifacts']['hashes.jsonl'])
  jobs=[json.loads(x)for x in raw_hash.splitlines()]
  assert [(x['kind'],x['node'],x['digest'])for x in jobs]==expected_jobs
  assert len(jobs)==1025 and all(x['epoch']==row['live_case']['epoch'] for x in jobs)
  assert all(a['cycle']<b['cycle']for a,b in zip(jobs,jobs[1:]))
  ev=[json.loads(x)for x in packed(receipt.parent/row['artifacts']['events.jsonl']['path'],row['artifacts']['events.jsonl']).splitlines()]
  oe=[json.loads(x)for x in packed(old_receipt.parent/baseline['artifacts']['events.jsonl']['path'],baseline['artifacts']['events.jsonl']).splitlines()]
  assert sem(ev)==sem(oe)
  counts=collections.Counter((x['type'],x.get('stage',''))for x in ev)
  assert counts=={('canonical',''):8100,('transform','assemble'):7806,('transform','dequant'):7806,('transform','residual'):7806}
  c,f,g,verdict=row['live_case'],row['fences'],row['parent_guard'],row['verdict']
  assert c['root']==root and c['hud_sha256']==hud_sha and c['seal']==seal
  assert all(f[k]==518400 for k in('canonical_producer_bytes','canonical_request_bytes','canonical_successful_ack_bytes','canonical_hash_bytes'))
  assert all(f[k]==42240 for k in('hud_request_bytes','hud_successful_ack_bytes','hud_hash_bytes'))
  assert f['root_complete']<f['hud_hash_complete']<f['seal_complete']<f['commit']<f['presentation']
  assert f['last_canonical_producer_accept']<=f['last_canonical_successful_ack']<=f['last_canonical_hash_delivery']<=f['root_complete']
  assert f['last_hud_successful_ack']<=f['last_hud_hash_delivery']<=f['hud_hash_complete']
  assert verdict['wrong_ack_owned_write_drained'] and verdict['clean_retry_without_reset'] and verdict['observed_wrong_ack_count']==1
  assert verdict['candidate_write_acks']==verdict['candidate_write_requests']==(70080 if variant=='row'else 560640)
  assert g['raw_local_reads']==g['raw_local_responses']==33384 and type(g['raw_local_pending'])is int and g['raw_local_pending']==0
  assert g['parent_fault_gap_edges']==g['private_residual_handshakes']==1
  assert g['private_local_reads']==g['private_gap_local_responses']==g['revoked_local_responses']==0
  assert g['physical_responses_masked']is False and g['raw_internal_work_blocked_by_observation_masks']is False
  assert verdict['elastic_accepted']==verdict['elastic_delivered']+verdict['elastic_discarded'] and verdict['elastic_discarded']==1
  cycles=c['last_outer_to_commit_cycles'];prior=baseline['live_case']['last_outer_to_commit_cycles']
  assert cycles==c['commit_cycle']-c['last_outer_cycle'] and c['commit_cycle']==f['commit']
  reviews.append(dict(variant=variant,profile=profile,measured_cycles=cycles,v117_cycles=prior,cycle_delta=cycles-prior,cycle_delta_percent=100*(cycles-prior)/prior,conditional_125MHz_ms=cycles/125000,conditional_100MHz_ms=cycles/100000,hash_jobs_recomputed=len(jobs),canonical_semantic_records=counts[('canonical','')],transform_records_per_stage=7806,raw_local_read_response_pairs=33384,final_raw_pending=0))
 assert len(reviews)==4
 for c in q['commands']:
  assert c['exit_code']==0
  args=c['argv'];assert '-Wno-fatal'not in args
  if 'verilator'in args and '--cc'in args:assert '--assert'in args and '-Wall'in args and '-Werror'in args[args.index('-CFLAGS')+1]
 answer=dict(schema='v118-independent-live-terminal-expert-review-v1',status='PASS_V118_LIVE_TERMINAL_EXPERT',reviewer='/root/v118_scratch',receipt=pin(receipt),selector=pin(selector),review_script=pin(Path(__file__).resolve()),checks=dict(all_live_source_pins=True,all_retained_artifact_pins=True,selected18source_identity=True,actual_canonical_and_accepted_bytes=True,all1025hash_jobs_independently_recomputed_each_profile=True,canonical_transform_event_semantics_exact_v117=True,strict_compile_and_original_assertions=True,byte_ACK_hash_publication_fences=True,wrong_ACK_debt_drain_and_clean_retry=True,raw_response_conservation=True,terminal_zero_raw_debt=True),runs=reviews,limits=['ACK bus is checked by retained independent C++ whole-owner/byte/ledger assertions; no full per-cycle external ACK bus trace exists for a separate Python replay.','These four profiles contain one keyframe plus wrong-ACK recovery each; no sustained distinct-frame30fps or worst-case gameplay bound.','No private cancel-gap local read or revoked response occurred in these four fixtures; do not claim that gap was exercised.','Software HUD semantic decoding and finite abstract16bit single-lease memory service remain; actual RTL SHA/C2/HUD/seal validation is included.','Conditional125/100MHz conversions are arithmetic only; component OOC routing does not establish full-parent clock or hardware performance.'],hardware_30fps=False,validated_decode_under10ms=False,full_parent_routed_timing=False)
 path=AREA/'audit/live-terminal-expert.json';path.write_text(json.dumps(answer,indent=2,sort_keys=True)+'\n');print(path,sha(path))
if __name__=='__main__':main()
