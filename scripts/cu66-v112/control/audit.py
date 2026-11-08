#!/usr/bin/env python3
"""Read-only source, recipe, strict-run and immutable-artifact audit."""
import hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v112/control';SRC=ROOT/'fpga/experiments/cu66-v112-control'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 p=Path(__file__).with_name('qualify.py');spec=importlib.util.spec_from_file_location('qualifier',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);recipe=m.verify()
 q=load(AREA/'results.json');assert q['status']=='PASS'and q['actual_RTL_run']and q['frozen_after_focused_PASS']
 receipt=ROOT/q['selected_report'];assert sha(receipt)==q['selected_report_sha256'];r=load(receipt);assert r=={k:v for k,v in q.items()if k not in('selected_report','selected_report_sha256')}
 for n,h in r['source_sha256'].items():
  assert sha(ROOT/n)==h,(n,'source changed');assert sha(receipt.parent/'sources'/n)==h,(n,'snapshot changed')
 for n,h in r['artifacts_sha256'].items():assert sha(receipt.parent/n)==h,(n,'artifact changed')
 assert r['strict_warnings']and not r['warning_suppression']and not r['assertions_disabled_or_downgraded']and r['added_public_cycles']==0
 assert len(r['commands'])==10
 for c in r['commands']:
  a=c['argv'];assert c['exit_code']==0 and a[a.index('--cpus')+1]=='2' and a[a.index('--memory')+1]==a[a.index('--memory-swap')+1]=='8g'
  assert m.IMAGE in a and a[a.index('--network')+1]=='none'
  if '--top-module'in a:
   assert '--assert'in a and '-Wall'in a and not any(x.startswith('-Wno')for x in a)and a[a.index('-j')+1]=='1'
 for name in ('scratch_probe','admission_probe','geometry_probe'):
  log=(receipt.parent/(name+'-compile.log')).read_text();assert '%Warning-'not in log and '%Error'not in log
 assert {x['seed']for x in r['scratch_runs']}=={112101,112102}
 for x in r['scratch_runs']:assert x['status']=='TEST_PASS'and x['full_transactions']==72 and x['corrupt_response_cases']==128 and x['read_owner_cases']==4 and x['bank_mask']==15 and x['offset_mask']==65535
 assert {x['seed']for x in r['admission_runs']}=={112201,112202}
 for x in r['admission_runs']:
  v=x['terminal_verdict'];assert v['status']=='TEST_PASS'and v['cases']==86 and v['positive_cases']==52 and v['negative_cases']==34 and v['directed_checks']==44
  for key,expected in {'coordinate':'PASS','quant':'PASS_INDEPENDENT_PACKET_RUN_FILL_ORACLE','scale':'PASS','mode':'PASS_INDEPENDENT_MODE_PORT_ORACLE'}.items():assert x[key]['status']==expected
 assert {x['seed']for x in r['domain_runs']}=={112301,112302}
 for x in r['domain_runs']:assert x['status']=='TEST_PASS'and x['all_mask_counts']==65536 and x['generic_tiles']==262208 and x['plane_mask']==15 and x['uint32_wrap_tested']
 assert r['test_hierarchy_translation']['semantic_checker_edits']==0 and r['test_hierarchy_translation']['occurrences']==4
 # Rebind the two origins to the actual rejected-at-125 Count composition,
 # so a passing focus proof cannot accidentally qualify V111's header source.
 old=ROOT/'experiments/python-gamebub-v111/native/20261108T183002986106Z/inputs.json';origins=load(old)['source_contract']['source_origins']
 expected_alias={'cs88_admission_v91i2a.sv':'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv','packed_scratch_v91g2.sv':'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'}
 overrides={}
 for name,e in recipe['production'].items():
  alias=expected_alias[name];assert origins[alias]==dict(path=e['original'],sha256=e['original_sha256'])
  overrides[alias]=dict(path=e['candidate'],sha256=e['candidate_sha256'])
 # A structural mux-distribution identity supplements sampled full-body RTL.
 # All non-bank predicate operands are identical; selected bank word and
 # position have exactly their original widths and unsigned/signed casts.
 scratch=(SRC/'packed_scratch_v91g2.sv').read_text()
 local=re.search(r'assign ac_bank_invalid\[validation_bank\]=(.*?);',scratch,re.S).group(1)
 original=next(x['before']for x in recipe['production']['packed_scratch_v91g2.sv']['edits']if x['before'].startswith("if(17'(read_word"))[3:-7]
 normalize=lambda t:re.sub(r'\s+','',t)
 assert normalize(local.replace('bank_word','read_word').replace('bank_position','read_position'))==normalize(original)
 assert "wire [31:0] bank_word=32'(cache_data[validation_bank]>>(8*read_address[3:0]));"in scratch
 assert "wire [31:0] bank_position={13'd0,cache_positions[validation_bank][read_address[3:0]]};"in scratch
 package=load(SRC/'packaging.json');s=(SRC/'cs88_admission_v91i2a.sv').read_bytes();assert package['production_sha256']==hashlib.sha256(s).hexdigest();cuts=[0,*package['split_byte_offsets'],len(s)]
 for i,f in enumerate(package['fragments']):assert len(s[cuts[i]:cuts[i+1]])==f['bytes']and hashlib.sha256(s[cuts[i]:cuts[i+1]]).hexdigest()==f['sha256']
 result=dict(schema='v112-local-control-read-only-audit-v1',status='PASS_SOURCE_AND_FOCUSED_AUDIT',focused_receipt=str(receipt.relative_to(ROOT)),focused_receipt_sha256=sha(receipt),source_origins_control=str(old.relative_to(ROOT)),source_origins_control_sha256=sha(old),source_overrides=overrides,proof_script_sha256=sha(Path(__file__)),files_verified=len(r['source_sha256']),artifacts_verified=len(r['artifacts_sha256']),independent_original_reference=True,public_latency_delta_cycles=0,assertions_disabled_or_downgraded=False,physical_timing_claim=False)
 (AREA/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
