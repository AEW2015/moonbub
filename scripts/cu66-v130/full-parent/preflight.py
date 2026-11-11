#!/usr/bin/env python3
"""Fail-closed V130 parent overlay check; no simulator or vendor tool calls."""
import argparse,hashlib,importlib.util,json,re,runpy,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
AREA=ROOT/'experiments/python-gamebub-v130/full-parent';COMP=ROOT/'experiments/python-gamebub-v130/spec-read/composition.json';BASE=ROOT/'experiments/python-gamebub-v129/integration/results.json';AUDIT=ROOT/'experiments/python-gamebub-v129/audit/full-independent.json'
ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv';PACK=AREA/'packaging.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def pin(p):return dict(path=str(Path(p).relative_to(ROOT)),sha256=sha(p))
def derivation():
 d=load(HERE/'derivation.json');assert d['original_oracle_comparisons_removed']==0
 a=ROOT/d['original'];b=ROOT/d['candidate'];assert sha(a)==d['original_sha256'] and sha(b)==d['candidate_sha256'];t=a.read_text()
 for e in d['edits']:assert t.count(e['before'])==e['count'];t=t.replace(e['before'],e['after'])
 assert t==b.read_text()
 for e in reversed(d['edits']):assert t.count(e['after'])==e['count'];t=t.replace(e['after'],e['before'])
 assert t==a.read_text()
 return d
def overlay(sources,origins,require_proofs=True):
 derivation();c=load(COMP);base=load(BASE);a=load(AUDIT)
 assert c['schema']=='v130-spec-read-candidate-composition-v1' and c['changed_aliases']==[ALIAS] and not c['full_parent_functional_pass'] and not c['hardware_qualification'] and not c['physical_timing_pass']
 assert c['v129_functional_parent']==pin(BASE) and base['status']=='PASS_V129_FULL_FUNCTIONAL' and a['status']=='PASS_INDEPENDENT_V129_FULL_FUNCTIONAL_AUDIT' and a['integration_index_sha256']==sha(BASE)
 assert origins==base['source_origins'] and len(origins)==18 and [str(x.relative_to(ROOT))for x in sources]==base['rtl_source_order']==c['source_order']
 changed=c['source_origins'];assert len(changed)==18 and {x for x in changed if changed[x]!=origins[x]}=={ALIAS}
 for meta in changed.values():assert pin(ROOT/meta['path'])==meta
 expected=c['new_actual_order'];new=[ROOT/x for x in expected];assert len(new)==18
 expected_new=[changed[ALIAS]['path'] if str(x.relative_to(ROOT))==origins[ALIAS]['path'] else str(x.relative_to(ROOT)) for x in sources];assert expected==expected_new
 dp=ROOT/'fpga/experiments/cu66-v130-spec-read/derivation.json';d=load(dp);parent=ROOT/d['parent'];candidate=ROOT/changed[ALIAS]['path'];assert d['parent_sha256']==sha(parent)==origins[ALIAS]['sha256'] and d['candidate_sha256']==sha(candidate)==changed[ALIAS]['sha256']
 text=parent.read_text();assert text.count(d['old_block'])==1;text=text.replace(d['old_block'],d['new_block'],1);assert text==candidate.read_text();assert text.count(d['new_block'])==1 and text.replace(d['new_block'],d['old_block'],1)==parent.read_text() and d['RTL_cycle_delta']==0
 focused=ROOT/c['focused_pair']['path'];assert pin(focused)==c['focused_pair'];f=load(focused);assert f['status']=='PASS' and f['actual_RTL_run'] is True and f['source_snapshot_unchanged'] is True and f['source_sha256'][str(candidate.relative_to(ROOT))]==sha(candidate)
 assert [r['seed']for r in f['runs']]==[130101,130102] and all(r['status']=='PASS' and r['all_nondatabus_outputs_compared'] and r['invalid_databus_qualified'] and r['actual_full_admission_fsm'] for r in f['runs'])
 for name,h in f['source_sha256'].items():assert sha(ROOT/name)==h
 for name,h in f['artifact_sha256'].items():assert sha(focused.parent/name)==h
 cmds=[x['argv'] for x in f['commands']];compiles=[x for x in cmds if 'verilator'in x and '--cc'in x];assert compiles and all('--assert'in x and '-Wall'in x and '-Wno-fatal'not in x and '-CFLAGS'in x and '-Werror'in x[x.index('-CFLAGS')+1] for x in compiles)
 pack=load(PACK);original=c['packaging'];assert pack['production_sha256']==sha(candidate)==original['production_sha256'] and pack['split_byte_offsets']==original['split_byte_offsets'];data=candidate.read_bytes();cuts=[0]+pack['split_byte_offsets']+[len(data)];assert len(pack['fragments'])==3
 for i,(m,source) in enumerate(zip(pack['fragments'],original['fragments'])):
  p=ROOT/source['path'];chunk=data[cuts[i]:cuts[i+1]];assert p.name==m['filename'] and len(chunk)==m['bytes']==source['bytes'] and hashlib.sha256(chunk).hexdigest()==m['sha256']==source['sha256'] and p.read_bytes()==chunk
 files=[COMP,BASE,AUDIT,PACK,dp,focused,HERE/'derivation.json',HERE/'preflight.py',HERE/'qualify.py',candidate]+[ROOT/x['path'] for x in original['fragments']]
 return new,changed,PACK,files

def verify_frozen(files):
 f=load(AREA/'preflight.json');assert f['status']=='PREPARED_NOT_RUN' and f['actual_RTL_run'] is False
 actual={str(p.relative_to(ROOT)):sha(p) for p in files};assert actual==f['source_sha256'],'V130 preflight snapshot drift'
 assert sha(BASE)==f['baseline_V129']['sha256'] and sha(AUDIT)==f['baseline_full_audit']['sha256']
 return f

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--write-freeze',action='store_true');a=ap.parse_args();spec=importlib.util.spec_from_file_location('v130_parent_preflight',HERE/'qualify.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 derivation,selected,sources,origins,packaging,pins,proof_files=m.prepare(True);assert origins==load(COMP)['source_origins'];assert len(sources)==18
 endpoints=[ROOT/('fpga/experiments/'+name) for name in ('cu66-v69/hash/cu66_sha256_bytes.sv','cu66-v69/banks/cu66_frame_bank_control.sv','cu66-v91l/cs88_validate_publish_v91l.sv','cu66-v91l-live/cu66_write_hash_join_v91l.sv')]+[m.ROW,m.SRC/'cs88_live_v91l.sv']
 inputs=[ROOT/selected['inputs'][name]['source'] for name in ('cases.tsv','transform_tiles.tsv','canonical_goldens.tsv')]+[ROOT/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz']
 support=[ROOT/('experiments/cu66-native-v69/'+name) for name in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
 initial_selector=ROOT/'experiments/python-gamebub-v116/control-c-study/live-parent/results.json';initial_receipt=ROOT/load(initial_selector)['path']
 bsel=ROOT/'experiments/python-gamebub-v129/integrated-study/live-guard/results.json';brec=ROOT/load(bsel)['path']
 files=sorted(set(sources+endpoints+inputs+support+proof_files+[initial_selector,initial_receipt,packaging,ROOT/'scripts/cu66-v129/integration/spatial.py',ROOT/'docs/cu66-v116/live-parent.md',ROOT/'experiments/python-gamebub-v116/live-parent/preparation.json',*[p for p in m.SRC.iterdir() if p.is_file()],HERE/'qualify.py',*[ROOT/r['source'] for r in derivation['sources']],ROOT/derivation['frozen_derivation']['path'],bsel,brec]))
 frozen={str(p.relative_to(ROOT)):sha(p) for p in files}
 report=dict(schema='v130-exploratory-parent-preflight-v1',status='PREPARED_NOT_RUN',actual_RTL_run=False,source_origins=origins,rtl_source_order=[str(x.relative_to(ROOT))for x in sources],source_sha256=frozen,baseline_V129=pin(BASE),baseline_full_audit=pin(AUDIT),focused_pair=load(COMP)['focused_pair'],packaging=pin(packaging),derivation=pin(HERE/'derivation.json'),seeds=[116701,116702],variants=['byte','row'],comparator_contract=dict(focused_pair_valid_qualified_only=['replay_data when replay_rsp_valid','stage_read_data when stage_read_rsp'],parent_masks=[],parent_exact='V129 six terminal dictionaries and complete event, accepted-output and hash streams',top_level_all_cycle_public_port_equivalence_claim=False,unqualified_debug_consumers='unknown; frame_read_data and stage_read_data may vary without response valid'),hardware_contact=False,full_parent_test_pass=False,full_parent_timing_pass=False)
 if a.write_freeze:
  target=AREA/'preflight.json';assert not target.exists(),'do not overwrite frozen preflight';target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print('V130_PREFLIGHT_PREPARED_NOT_RUN',pin(target))
 else:print('V130_PREFLIGHT_CHECKED_NOT_RUN',len(frozen),'source pins')
if __name__=='__main__':main()
