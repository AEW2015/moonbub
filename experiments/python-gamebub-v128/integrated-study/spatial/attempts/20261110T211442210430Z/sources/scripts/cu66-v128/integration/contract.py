#!/usr/bin/env python3
"""V128 explicit composition overlay and immutable V127 proof lineage."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
AREA=ROOT/'experiments/python-gamebub-v128'
BASELINE=ROOT/'experiments/python-gamebub-v127/integration/results.json'
BASELINE_SHA='d16589645d3824399a4df4559a84405051547a48e236dc0aa0e1841812f5ce39'
BASELINE_AUDIT=ROOT/'experiments/python-gamebub-v127/audit/full-independent.json'
BASELINE_AUDIT_SHA='494ddd3433304c8bd9e08cd63802646edca9c8ba00a23f48e364ce44eaf38ad6'
LEGACY_AUDITOR=ROOT/'scripts/cu66-v127/audit_functional.py'
LEGACY_AUDITOR_SHA='4e96c701ee5ed5667a5d4a7cd09bc6e6333929df635ac9233a63e7debb5a91bd'
COMPOSITION=ROOT/'fpga/experiments/cu66-v128-raw/selected-composition.json'
RAW_RECIPE=ROOT/'fpga/experiments/cu66-v128-raw/edit-recipe.json'
CHANGES_EXPECTED={
'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv',
'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv',
'fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv',
'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv',
'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def pin(p):return dict(path=str(Path(p).relative_to(ROOT)),sha256=sha(p))
def legacy():
 assert sha(LEGACY_AUDITOR)==LEGACY_AUDITOR_SHA
 spec=importlib.util.spec_from_file_location('frozen_v127_raw_audit',LEGACY_AUDITOR)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def verify_derivation():
 data=load(HERE/'derivation.json');assert data['old_oracle_checks_removed']==data['declared_public_cycle_delta']==0
 assert len(data['sources'])==4
 for r in data['sources']:
  a,b=ROOT/r['original'],ROOT/r['candidate'];assert sha(a)==r['original_sha256'] and sha(b)==r['candidate_sha256']
  text=a.read_text()
  for e in r['edits']:assert text.count(e['before'])==e['count'];text=text.replace(e['before'],e['after'])
  assert text==b.read_text()
  for e in reversed(r['edits']):assert text.count(e['after'])==e['count'];text=text.replace(e['after'],e['before'])
  assert text==a.read_text()
 return data

def composition():
 assert sha(BASELINE)==BASELINE_SHA and sha(BASELINE_AUDIT)==BASELINE_AUDIT_SHA
 old=load(BASELINE);assert old['status']=='PASS_V127_OWNER_FULL_FUNCTIONAL'
 assert old['all_original_oracles_retained'] and old['exact_B_public_cycles'] and old['declared_public_cycle_delta']==0 and old['assertions_disabled_or_downgraded'] is False
 for meta in old['source_origins'].values():assert pin(ROOT/meta['path'])==meta
 c=load(COMPOSITION)
 assert c['schema']=='v128-selected-raw-padding-composition-v1'
 assert c['parent']==pin(BASELINE)
 assert set(c['source_origins'])==set(c['changed_aliases'])==CHANGES_EXPECTED
 assert c['changed_origin_count']==5 and c['unchanged_origin_count']==13
 assert c['declared_public_cycle_delta']==0
 assert len(c['complete_source_origins'])==18 and set(c['complete_source_origins'])==set(old['source_origins'])
 for a,m in c['complete_source_origins'].items():
  assert pin(ROOT/m['path'])==m
  assert m==(c['source_origins'][a] if a in CHANGES_EXPECTED else old['source_origins'][a])
 roles=c['proof_roles'];assert set(roles)=={'raw_validation','header_padding'}
 assert set(roles['raw_validation'])==CHANGES_EXPECTED-{'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'}
 assert roles['header_padding']==['fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv']
 for meta in c['component_recipes'].values():assert pin(ROOT/meta['path'])==meta
 raw=load(ROOT/c['component_recipes']['raw_validation']['path'])
 assert raw['original_assertion_blocks_retained_byte_exact'] is True and raw['declared_public_cycle_delta']==0
 for r in raw['production'].values():
  a,b=ROOT/r['original']['path'],ROOT/r['candidate']['path'];assert pin(a)==r['original'] and pin(b)==r['candidate']
  text=a.read_text()
  for e in r['edits']:assert text.count(e['old'])==e['occurrences'];text=text.replace(e['old'],e['new'])
  assert text==b.read_text()
  for e in reversed(r['edits']):assert text.count(e['new'])==e['occurrences'];text=text.replace(e['new'],e['old'])
  assert text==a.read_text()
 pad=load(ROOT/c['component_recipes']['header_padding']['path'])
 before,after=ROOT/pad['original']['path'],ROOT/pad['candidate']['path']
 assert pin(before)==pad['original'] and pin(after)==pad['candidate']
 text=before.read_text()
 assert len(pad['edits'])==2 and pad['source_payload_bits_added']==1 and pad['source_payload_reset_added'] is False
 assert pad['added_public_cycles']==pad['added_synthesis_attributes']==0
 for e in pad['edits']:assert text.count(e['old'])==1;text=text.replace(e['old'],e['new'])
 assert text==after.read_text()
 for e in reversed(pad['edits']):assert text.count(e['new'])==1;text=text.replace(e['new'],e['old'])
 assert text==before.read_text()
 import re
 oldguards=re.findall(r'`ifndef SYNTHESIS\n.*?`endif',before.read_text(),re.S)
 assert len(oldguards)==16 and all(block in after.read_text()for block in oldguards)
 tail=lambda text:text[re.search(r'^endmodule\s*$',text,re.M).end():]
 assert tail(before.read_text())==tail(after.read_text())
 pkg=load(after.parent/'packaging.json');assert pkg['production_sha256']==sha(after)and pkg['module_count']==3
 cuts=[0]+pkg['split_byte_offsets']+[after.stat().st_size]
 assert len(cuts)==len(pkg['fragments'])+1
 for i,f in enumerate(pkg['fragments']):
  data=after.read_bytes()[cuts[i]:cuts[i+1]];assert f['bytes']==len(data)and f['sha256']==hashlib.sha256(data).hexdigest()
 return c

def contract_candidates():return [m['path']for m in composition()['source_origins'].values()]

def verify():
 verify_derivation();c=composition();prior=load(BASELINE_AUDIT)
 assert prior['status']=='PASS_INDEPENDENT_V127_FULL_FUNCTIONAL_AUDIT' and prior['integration_index_sha256']==BASELINE_SHA
 assert prior['exact_comparisons']==dict(spatial_stdout_event_and_canonical_streams=4,peer_stdout_event_and_canonical_streams=2,parent_stdout_and_terminal_stream_sets=4)
 selfcheck=load(AREA/'audit/baseline-self-check.json');recheck=load(AREA/'audit/inherited-v127-recheck.json')
 assert selfcheck['status']=='PASS_BASELINE_SELF_CHECK'and selfcheck['raw_comparison_counts']==dict(spatial=4,peer=2,parent=4)
 assert selfcheck['legacy_auditor']==pin(LEGACY_AUDITOR)and selfcheck['baseline']==pin(BASELINE)and selfcheck['actual_RTL_run']is False
 assert recheck['status']=='PASS_INDEPENDENT_V127_FULL_FUNCTIONAL_AUDIT'and recheck['integration_index_sha256']==BASELINE_SHA
 assert recheck['exact_comparisons']==prior['exact_comparisons']
 # Do not mutate a frozen auditor namespace. Its read-only closure helpers accept actual paths.
 m=legacy()
 for name,meta in load(BASELINE)['stages'].items():
  _,p,r=m.resolve_stage(meta);m.verify_closure(p,r,'inherited V127 '+name)
 return c

def source_map(sources,origins):
 c=composition();base=load(BASELINE);assert origins==c['complete_source_origins']
 changes={base['source_origins'][a]['path']:v['path'] for a,v in c['source_origins'].items()}
 order=[changes.get(p,p) for p in base['rtl_source_order']]
 assert len(sources)==len(origins)==18 and [str(p.relative_to(ROOT))for p in sources]==order
 return origins

def baseline(stage):
 key={'control-peer':'peer','spatial':'spatial','live-guard':'parent'}[stage]
 _,p,r=legacy().resolve_stage(load(BASELINE)['stages'][key]);return p,r

def files():
 c=verify();out=[BASELINE,BASELINE_AUDIT,LEGACY_AUDITOR,COMPOSITION,RAW_RECIPE,HERE/'derivation.json',ROOT/'docs/cu66-v128/verification-plan.md',ROOT/'scripts/cu66-v128/audit_functional.py']
 out +=list(HERE.glob('*.py'))+[HERE/'live_guard/qualify.py',ROOT/'scripts/cu66-v128/raw/qualify.py']
 out +=[AREA/'audit/baseline-self-check.json',AREA/'audit/inherited-v127-recheck.json']
 out +=[ROOT/m['path']for m in c['component_recipes'].values()]
 out +=[ROOT/m['path']for m in c['complete_source_origins'].values()]
 out +=[ROOT/load(BASELINE)['stages'][name]['path']for name in ['focused','spatial','peer','parent']]
 for name in ['focused','spatial','peer','parent']:
  _,p,_=legacy().resolve_stage(load(BASELINE)['stages'][name]);out.append(p)
 for base in [ROOT/'fpga/experiments/cu66-v128-raw',ROOT/'fpga/experiments/cu66-v128-padding']:
  out+=list(base.glob('*.json'))
 return sorted(set(out))
if __name__=='__main__':verify();print('V128_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
