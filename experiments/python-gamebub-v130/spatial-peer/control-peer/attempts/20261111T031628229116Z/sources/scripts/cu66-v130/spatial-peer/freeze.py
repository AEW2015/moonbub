#!/usr/bin/env python3
"""Freeze/verify the exploratory spatial or peer inputs; no tool execution."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;AREA=ROOT/'experiments/python-gamebub-v130/spatial-peer'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def verify_derivation():
 d=load(HERE/'derivation.json');assert d['original_oracle_checks_removed']==d['added_masks_to_parent_oracles']==0
 for q in d['sources']:
  a,b=ROOT/q['original'],ROOT/q['candidate'];assert sha(a)==q['original_sha256'] and sha(b)==q['candidate_sha256'];t=a.read_text()
  for e in q['edits']:assert t.count(e['before'])==e['count'];t=t.replace(e['before'],e['after'])
  assert t==b.read_text()
  for e in reversed(q['edits']):assert t.count(e['after'])==e['count'];t=t.replace(e['after'],e['before'])
  assert t==a.read_text()
def inputs(stage,files,sources,origins):
 assert stage in ('spatial','peer');verify_derivation();c=load(ROOT/'experiments/python-gamebub-v130/spec-read/composition.json');assert origins==c['source_origins'] and [str(x.relative_to(ROOT))for x in sources]==c['new_actual_order']
 p=ROOT/'experiments/python-gamebub-v130/full-parent/results.json';s=load(p);receipt=ROOT/s['path'];assert s['status']=='PASS_V130_EXPLORATORY_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION' and sha(receipt)==s['sha256'];a=load(ROOT/'experiments/python-gamebub-v130/audit/parent-independent.json');assert a['status']=='PASS_V130_EXPLORATORY_PARENT_EVIDENCE' and a['candidate_receipt']['sha256']==sha(receipt)
 return dict(schema='v130-exploratory-'+stage+'-preflight-v1',status='PREPARED_NOT_RUN',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in sorted(files)},source_origins=origins,rtl_source_order=[str(x.relative_to(ROOT))for x in sources],parent_receipt=dict(path=str(receipt.relative_to(ROOT)),sha256=sha(receipt)),parent_audit=dict(path='experiments/python-gamebub-v130/audit/parent-independent.json',sha256=sha(ROOT/'experiments/python-gamebub-v130/audit/parent-independent.json')),comparator_contract=dict(focused_pair_valid_qualified=['replay_data when replay_rsp_valid','stage_read_data when stage_read_rsp'],new_masks_on_spatial_or_peer_comparators=[],actual_V129_stdout_event_canonical_bytes_exact=True,all_public_ports_cycle_compared=False,invalid_cycle_debug_consumer_contract='unverified'),hardware_contact=False,whole_parent_timing_or_board_qualified=False)
def freeze(stage,files,sources,origins):
 p=AREA/('preflight-'+stage+'.json');assert not p.exists(),'frozen preflight already exists';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(inputs(stage,files,sources,origins),indent=2,sort_keys=True)+'\n');print('V130_'+stage.upper()+'_PREFLIGHT_PREPARED_NOT_RUN',str(p.relative_to(ROOT)),sha(p))
def verify(stage,files,sources,origins):
 p=AREA/('preflight-'+stage+'.json');old=load(p);new=inputs(stage,files,sources,origins);assert old==new,'frozen input, comparator or candidate drift';return old
