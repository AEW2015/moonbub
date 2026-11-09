#!/usr/bin/env python3
"""Read-only independent preflight validation; never launches Vivado."""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('preflight',type=Path);ap.add_argument('--auditor',required=True);a=ap.parse_args()
 p=a.preflight.resolve();p.relative_to(ROOT);d=load(p);policy=ROOT/d['policy']['path'];pol=load(policy)
 assert sha(policy)==d['policy']['sha256'];assert d['status']=='PREPARED_NOT_RUN'
 driver=ROOT/'scripts/cu66-v118/native.py';spec=importlib.util.spec_from_file_location('independent_v118_native_check',driver);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.AREA=p.parent.parent.parent;m.POLICY=policy
 assert m.qualify(d['trial_id'],pol)==d['source_contract'];m.budget(pol,d['trial_id'],ROOT/d['clean_repeat_of']['path']if d['clean_repeat_of']else None,d['source_contract'])
 b=Path(d['build_external']);assert sha(b/'inputs.json')==d['inputs_sha256'];assert load(b/'inputs.json')=={k:v for k,v in d.items()if k!='inputs_sha256'}
 for name,h in d['recipe_sha256'].items():assert sha(b/name)==h,name
 for name,h in d['tooling_sha256'].items():assert sha(ROOT/name)==h,name
 for alias,meta in d['source_contract']['source_origins'].items():assert sha(b/'snapshot'/alias)==sha(ROOT/meta['path'])==meta['sha256']
 run=(b/'run.tcl').read_text();assert run.index('read_xdc $constraint_file')<run.index('synth_design -top')
 for forbidden in ('read_checkpoint','set_false_path','set_multicycle_path','set_max_delay','set_input_delay','set_output_delay','set_clock_uncertainty','DONT_TOUCH','KEEP_HIERARCHY','MAX_FANOUT'):
  assert forbidden not in run and forbidden not in (b/'component.xdc').read_text(),forbidden
 period=d['clock_period_ns'];assert period in (8.0,10.0)
 canonical=m.FLOW/('clock-125.xdc'if period==8.0 else'clock-100.xdc');assert sha(b/'component.xdc')==sha(canonical)==d['tooling_sha256'][str(canonical.relative_to(ROOT))]
 expected='create_clock -name component_clk -period '+('8.000'if period==8.0 else'10.000')
 assert expected in (b/'component.xdc').read_text(),(b/'component.xdc').read_text()
 assert d['start_mode']=='rtl' and d['synth_directive_cli']=='omitted'
 image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','acorn-nexys4-ddr:2026.1'],text=True).strip();assert image==d['image_id']=='sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
 assert pol['max_heavy_jobs']==2 and pol['memory_limit_bytes']==pol['memory_swap_limit_bytes']==8*1024**3
 result=dict(schema='v118-native-preflight-audit-v1',status='PASS_V118_NATIVE_PREFLIGHT_AUDIT',auditor=a.auditor,preflight_sha256=sha(p),policy_sha256=sha(policy),native_source_sha256=sha(driver),audit_source_sha256=sha(Path(__file__)),checks={k:True for k in ('source_snapshots','recipes_and_tooling','functional_proofs','actual_clock_before_synthesis','image_content_id','bounded_resources_and_budget','unchanged_timing_constraints','no_hardware_or_bitstream')})
 out=p.with_name('audit.json');assert not out.exists();out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(out.relative_to(ROOT))
if __name__=='__main__':main()
