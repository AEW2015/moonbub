#!/usr/bin/env python3
"""Read-only binding to V128, plus the two reversible V129 source edits."""
import hashlib,importlib.util,json,runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
AREA=ROOT/'experiments/python-gamebub-v129'
BASELINE=ROOT/'experiments/python-gamebub-v128/integration/results.json'
BASELINE_SHA='57b48154c3e7beda86cfe347032e505841bcdb2d35e1b9e8e560f9d134848f20'
BASELINE_AUDIT=ROOT/'experiments/python-gamebub-v128/audit/full-independent.json'
BASELINE_AUDIT_SHA='f36c365c68a54699cb6e25183b2f6be5aa2212101f775b2ea94d4e7dab01637c'
LEGACY_AUDITOR=ROOT/'scripts/cu66-v127/audit_functional.py';LEGACY_AUDITOR_SHA='4e96c701ee5ed5667a5d4a7cd09bc6e6333929df635ac9233a63e7debb5a91bd'
V128_CONTRACT=ROOT/'scripts/cu66-v128/integration/contract.py'
RECIPES=[ROOT/'fpga/experiments/cu66-v129-parser/edit-recipe.json',ROOT/'fpga/experiments/cu66-v129-scratch/edit-recipe.json']
ALIASES=['fpga/experiments/cu66-v91/br88_rice_elastic.sv','fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv']
EXPECTED=['55ae4bb5678626ab37c469d47d3fd9f23d0df920ebca575b38d0e55a114e834f','45d6be3128a8e8840f3033a1205be979340e9744b3989189057cfae96edb63be']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def pin(p):return dict(path=str(Path(p).relative_to(ROOT)),sha256=sha(p))
def legacy():
 assert sha(LEGACY_AUDITOR)==LEGACY_AUDITOR_SHA
 spec=importlib.util.spec_from_file_location('frozen_v127_pure_comparators',LEGACY_AUDITOR);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify_derivation():
 d=load(HERE/'derivation.json');assert d['old_oracle_checks_removed']==d['declared_public_cycle_delta']==0 and len(d['sources'])==4
 for r in d['sources']:
  a,b=ROOT/r['original'],ROOT/r['candidate'];assert sha(a)==r['original_sha256'] and sha(b)==r['candidate_sha256']; t=a.read_text()
  for e in r['edits']:assert t.count(e['before'])==e['count'];t=t.replace(e['before'],e['after'])
  assert t==b.read_text()
  for e in reversed(r['edits']):assert t.count(e['after'])==e['count'];t=t.replace(e['after'],e['before'])
  assert t==a.read_text()
 return d
def composition():
 assert sha(BASELINE)==BASELINE_SHA and sha(BASELINE_AUDIT)==BASELINE_AUDIT_SHA
 old=load(BASELINE);assert old['status']=='PASS_V128_RAW_FULL_FUNCTIONAL' and old['all_original_oracles_retained'] and old['exact_B_public_cycles'] and old['declared_public_cycle_delta']==0 and old['assertions_disabled_or_downgraded'] is False
 v128=runpy.run_path(str(V128_CONTRACT));oldc=v128['composition']();assert oldc['complete_source_origins']==old['source_origins'] and len(old['source_origins'])==18
 origins=dict(old['source_origins']);changes={}
 for idx,p in enumerate(RECIPES):
  r=load(p);alias=ALIASES[idx];before=r['original'] if idx==0 else r['baseline'];after=r['candidate'];assert before==old['source_origins'][alias] and after['sha256']==EXPECTED[idx]
  assert pin(ROOT/before['path'])==before and pin(ROOT/after['path'])==after
  assert (r['alias'] if idx==0 else r['source_alias'])==alias
  assert (r['new_public_cycles'] if idx==0 else r['added_public_cycles'])==0
  t=(ROOT/before['path']).read_text()
  for e in r['edits']:
   a=e['before'] if idx==0 else e['old']; b=e['after'] if idx==0 else e['new']; n=e['count'] if idx==0 else e['occurrences'];assert t.count(a)==n;t=t.replace(a,b)
  assert t==(ROOT/after['path']).read_text()
  for e in reversed(r['edits']):
   a=e['before'] if idx==0 else e['old'];b=e['after'] if idx==0 else e['new'];n=e['count'] if idx==0 else e['occurrences'];assert t.count(b)==n;t=t.replace(b,a)
  assert t==(ROOT/before['path']).read_text();origins[alias]=after;changes[alias]=after
 assert sum(origins[a]!=old['source_origins'][a] for a in origins)==2
 return dict(complete_source_origins=origins,source_origins=changes,declared_public_cycle_delta=0)
def contract_candidates():return [m['path'] for m in composition()['source_origins'].values()]
def verify():
 verify_derivation();c=composition();prior=load(BASELINE_AUDIT)
 assert prior['status']=='PASS_INDEPENDENT_V128_FULL_FUNCTIONAL_AUDIT' and prior['integration_index_sha256']==BASELINE_SHA
 assert prior['exact_comparisons']==dict(spatial_stdout_event_and_canonical_streams=4,peer_stdout_event_and_canonical_streams=2,parent_stdout_and_terminal_stream_sets=4)
 for name,meta in load(BASELINE)['stages'].items():
  _,p,r=legacy().resolve_stage(meta);legacy().verify_closure(p,r,'inherited V128 '+name)
 return c
def source_map(sources,origins):
 c=composition();base=load(BASELINE);assert origins==c['complete_source_origins']
 changes={base['source_origins'][a]['path']:v['path'] for a,v in c['source_origins'].items()};order=[changes.get(p,p) for p in base['rtl_source_order']]
 assert len(sources)==len(origins)==18 and [str(p.relative_to(ROOT)) for p in sources]==order
 return origins
def baseline(stage):
 key={'control-peer':'peer','spatial':'spatial','live-guard':'parent'}[stage];_,p,r=legacy().resolve_stage(load(BASELINE)['stages'][key]);return p,r
def files():
 c=verify();out=[BASELINE,BASELINE_AUDIT,LEGACY_AUDITOR,V128_CONTRACT,HERE/'derivation.json']+RECIPES
 out+=list(HERE.glob('*.py'))+[HERE/'live_guard/qualify.py',ROOT/'scripts/cu66-v128/integration/resource_gate.py']
 out += [ROOT/m['path'] for m in c['complete_source_origins'].values()]
 for meta in load(BASELINE)['stages'].values():
  _,p,_=legacy().resolve_stage(meta);out.extend([ROOT/meta['path'],p])
 return sorted(set(out))
if __name__=='__main__':verify();print('V129_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
