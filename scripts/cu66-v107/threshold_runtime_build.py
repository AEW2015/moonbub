#!/usr/bin/env python3
"""Prepare one fail-closed RuntimeOptimized trial of the exact qualified threshold RTL."""
import argparse,contextlib,datetime,difflib,hashlib,io,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import threshold_build as frozen
FLOW=ROOT/'fpga/experiments/cu66-v107-threshold-runtime-flow';BASE_FLOW=ROOT/'fpga/experiments/cu66-v107-flow';AREA=ROOT/'experiments/python-gamebub-v107/threshold-runtime'
DEFAULT_OUT=ROOT/'experiments/python-gamebub-v107/native/20261108T073857407909Z'
CANON=ROOT/'experiments/python-gamebub-v107/threshold-pipeline/results.json'
ACTIVATION=ROOT/'experiments/python-gamebub-v107/coordination/threshold-runtime-activation.json'
AUDIT=ROOT/'experiments/python-gamebub-v107/coordination/threshold-runtime-pre-native-audit.json'
DISPATCH=ROOT/'experiments/python-gamebub-v107/coordination/threshold-runtime-dispatch.json'
POLICY=ROOT/'experiments/python-gamebub-v107/study-policy.json'
BUILDER_SHA='e373dbd6203eff4ac6845ffd1b619d6227242a03ae32256650f37f2e1bf2e881'
DEFAULT_INPUTS_SHA='821b64538f021ffcf14d1841e2d7f76339315e13caaee3f24ba8072385a37d51'
SYNTH_BEFORE='synth_design -top cs88_pipeline_v91k -part $part -mode out_of_context -flatten_hierarchy rebuilt -directive Default'
SYNTH_AFTER=SYNTH_BEFORE.removesuffix('Default')+'RuntimeOptimized'
STRATEGY=dict(synth='RuntimeOptimized',opt='Default',place='Default',route='Default')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def rel(p):return str(p.relative_to(ROOT))
def load(p):return json.loads(p.read_text())

def fixed_flow():
 assert sha(Path(frozen.__file__))==BUILDER_SHA,'frozen threshold builder drift'
 old=(BASE_FLOW/'run.tcl').read_text();new=(FLOW/'run.tcl').read_text()
 assert old.count(SYNTH_BEFORE)==1 and new==old.replace(SYNTH_BEFORE,SYNTH_AFTER,1),'flow diff exceeds SYNTH directive'
 assert len([x for x in difflib.ndiff(old.splitlines(),new.splitlines()) if x.startswith(('- ','+ '))])==2
 assert new.index('read_xdc $constraint_file')<new.index(SYNTH_AFTER)
 assert 'set_param general.maxThreads 2' in new
 for command in ('opt_design','place_design','route_design'):assert command+' -directive Default' in new
 for n in ('report.tcl','component.xdc','run_vivado2026.py'):assert sha(BASE_FLOW/n)==sha(FLOW/n),n
 xdc=(FLOW/'component.xdc').read_text();assert 'create_clock -name component_clk -period 10.000 [get_ports clk]' in xdc
 return old,new

def qualification():
 assert sha(DEFAULT_OUT/'inputs.json')==DEFAULT_INPUTS_SHA,'immutable Default8 inputs drift'
 default=load(DEFAULT_OUT/'inputs.json');checked=load(CANON)
 assert checked['status']=='PASS_EXACT_THRESHOLD_CANONICAL' and checked['actual_RTL_run']
 assert len(checked['runs'])==2 and checked['baseline_reused_actual_RTL']
 for r in checked['runs']:assert r['exact_stdout_events_cycles_and_canonical']
 for n,h in checked['source_sha256'].items():assert sha(ROOT/n)==h,('canonical source drift',n)
 expected={n:h for n,h in checked['source_sha256'].items() if Path(n).suffix in ('.sv','.svh')}
 actual={v['path']:v['sha256'] for v in default['source_origins'].values()}
 assert len(expected)==len(default['source_sha256'])==18 and expected==actual
 for n,h in default['source_sha256'].items():
  assert sha(DEFAULT_OUT/'source-snapshot'/n)==h,n
  entry=default['source_origins'][n];assert sha(ROOT/entry['path'])==entry['sha256']==h,n
 for label in ('payload-reset','idct-reset','guard-dsp','meta-flags','plan-prefix','count-threshold'):
  p=ROOT/('experiments/python-gamebub-v107/'+label+'/results.json');proof=load(p)
  assert proof['status']=='PASS' and proof['actual_RTL_run']
  for n,h in proof['source_sha256'].items():assert sha(ROOT/n)==h,('focused source drift',label,n)
 q=default['behavioral_qualification'];assert q['path']==rel(CANON) and q['sha256']==sha(CANON)
 for pathkey,hashkey in (('mapped_unit_path','mapped_unit_sha256'),('activation_path','activation_sha256'),('threshold_native_unit_path','threshold_native_unit_sha256')):assert sha(ROOT/q[pathkey])==q[hashkey]
 return default,checked

def validate_build(build,default):
 assert build.parent==frozen.BUILD_ROOT and build.name.startswith('v107-threshold-runtime-')
 inp=load(build/'inputs.json')
 assert inp['source_sha256']==default['source_sha256'] and inp['source_origins']==default['source_origins']
 assert inp['RTL_files']==17 and inp['closure_files']==18 and not inp['synth_only']
 for n,h in inp['source_sha256'].items():assert sha(build/'snapshot'/n)==h,n
 for n in ('run.tcl','report.tcl','component.xdc'):assert sha(build/n)==sha(FLOW/n),n
 assert (build/'inputs.tcl').read_text().splitlines()[1]=='set synth_only 0'
 assert sha(build/'run.tcl')!=sha(DEFAULT_OUT/'recipe-snapshot/run.tcl')
 for n in ('report.tcl','component.xdc'):assert sha(build/n)==sha(DEFAULT_OUT/'recipe-snapshot'/n),n
 # All path-free Tcl commands remain exact; only the prepared directory changes.
 old=(DEFAULT_OUT/'recipe-snapshot/inputs.tcl').read_text();new=(build/'inputs.tcl').read_text()
 default_external=Path(load(DEFAULT_OUT/'receipt.json')['build_external']);oldmapped='/build/'+default_external.name;newmapped='/build/'+build.name
 assert new==old.replace(oldmapped,newmapped),'inputs.tcl changed beyond build paths'
 return inp

def prepare():
 old,new=fixed_flow();default,_=qualification()
 # Reuse the frozen builder implementation; modify only in-memory globals.
 frozen.FLOW=FLOW;frozen.OVERRIDES={'threshold-runtime':dict(frozen.OVERRIDES['threshold'])}
 before=set(frozen.BUILD_ROOT.glob('v107-threshold-runtime-*'));argv=sys.argv
 try:
  sys.argv=[str(Path(__file__)),'--variant','threshold-runtime','--timeout','3600']
  frozen.main()
 finally:sys.argv=argv
 made=set(frozen.BUILD_ROOT.glob('v107-threshold-runtime-*'))-before;assert len(made)==1;build=made.pop()
 inp=validate_build(build,default)
 inp.update(variant='threshold-runtime',strategy_only=True,production_source_set_ordinal=8,native_attempt_ordinal=9,alternate_synthesis_strategy_ordinal=1,strategy=STRATEGY,runtime_activation_required=True,public_cycle_schedule_unchanged=True,public_cycle_reference='qualified threshold source set',behavioral_qualification=default['behavioral_qualification'],declared_change='Same eighteen qualified threshold files; only SYNTH directive RuntimeOptimized; Default opt/place/route and10ns-before-synthesis unchanged')
 write(build/'inputs.json',inp)
 out=AREA/'prepared'/build.name.removeprefix('v107-threshold-runtime-');out.mkdir(parents=True)
 for source,name in [(BASE_FLOW/'run.tcl','default-run.tcl'),(FLOW/'run.tcl','runtime-run.tcl'),(DEFAULT_OUT/'inputs.json','default-inputs.json'),(build/'inputs.json','prepared-inputs.json')]:shutil.copyfile(source,out/name)
 diff=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='Default/run.tcl',tofile='RuntimeOptimized/run.tcl'));(out/'flow.diff').write_text(diff)
 r=dict(schema='v107-threshold-runtime-preflight-v1',status='PREPARED_NOT_ACTIVATED',actual_native_run=False,variant='threshold-runtime',prepared_build=str(build),prepared_inputs_sha256=sha(build/'inputs.json'),builder=rel(Path(__file__)),builder_sha256=sha(Path(__file__)),frozen_builder=rel(Path(frozen.__file__)),frozen_builder_sha256=BUILDER_SHA,default_inputs=rel(DEFAULT_OUT/'inputs.json'),default_inputs_sha256=DEFAULT_INPUTS_SHA,canonical_qualification=rel(CANON),canonical_sha256=sha(CANON),source_sha256=inp['source_sha256'],source_origins=inp['source_origins'],source_maps_identical_to_Default8=True,closure_files=18,RTL_files=17,flow_before=rel(out/'default-run.tcl'),flow_before_sha256=sha(out/'default-run.tcl'),flow_after=rel(out/'runtime-run.tcl'),flow_after_sha256=sha(out/'runtime-run.tcl'),exact_one_line_flow_diff=diff,preserved_flow_sha256={n:sha(FLOW/n) for n in ('report.tcl','component.xdc','run_vivado2026.py')},prepared_recipe_sha256={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')},strategy=STRATEGY,clock_period_ns=10,max_threads=2,memory_limit_bytes=8*1024**3,cpus=2,timeout_seconds=3600,source_set_ordinal=8,native_attempt_ordinal=9,alternate_strategy_ordinal=1,new_RTL_sources=0,new_clock_or_exception_edits=0,activation_record_required=rel(ACTIVATION),independent_audit_required=rel(AUDIT),one_shot_dispatch=rel(DISPATCH),hardware_contact=False,scope='Prepared strategy-only experiment. No runtime speedup, QoR, routed frequency or hardware qualification result.')
 write(out/'preflight.json',r)
 template=dict(schema='v107-threshold-runtime-activation-v1',enabled=False,variant='threshold-runtime',source_limit=8,native_attempt_limit=9,alternate_strategy_limit=1,native_attempt_ordinal=9,source_set_ordinal=8,heavy_slot_granted=False,prepared_preflight=rel(out/'preflight.json'),prepared_preflight_sha256=sha(out/'preflight.json'),default_inputs=r['default_inputs'],default_inputs_sha256=DEFAULT_INPUTS_SHA,canonical_qualification=rel(CANON),canonical_sha256=sha(CANON),source_sha256=inp['source_sha256'],source_origins=inp['source_origins'],strategy=STRATEGY,clock_period_ns=10,max_threads=2,memory_limit_bytes=8*1024**3,cpus=2,timeout_seconds=3600,decision_utc=None,reason=None,observation_record='experiments/python-gamebub-v107/coordination/threshold-runtime-observation.json',observation_sha256=None,hardware_contact=False)
 write(out/'activation-template.json',template);write(AREA/'prepared.json',dict(status=r['status'],preflight=rel(out/'preflight.json'),preflight_sha256=sha(out/'preflight.json'),prepared_build=str(build),activation_template=rel(out/'activation-template.json'),actual_native_run=False))
 print('THRESHOLD_RUNTIME_PREFLIGHT',rel(out/'preflight.json'),sha(out/'preflight.json'),flush=True)

def launch(preflight_path,license_file):
 fixed_flow();default,_=qualification();p=load(preflight_path);assert p['status']=='PREPARED_NOT_ACTIVATED'
 assert p['builder_sha256']==sha(Path(__file__)) and p['frozen_builder_sha256']==BUILDER_SHA
 build=Path(p['prepared_build']);validate_build(build,default);assert sha(build/'inputs.json')==p['prepared_inputs_sha256']
 activation=load(ACTIVATION);policy=load(POLICY);audit=load(AUDIT)
 assert activation['schema']=='v107-threshold-runtime-activation-v1' and activation['enabled'] is True
 assert policy['threshold_runtime_activation']==activation and policy['max_heavy_jobs']==2 and policy['max_native_seconds']==3600 and policy['clock_period_ns']==10
 exact=dict(variant='threshold-runtime',source_limit=8,native_attempt_limit=9,alternate_strategy_limit=1,native_attempt_ordinal=9,source_set_ordinal=8,heavy_slot_granted=True,prepared_preflight=rel(preflight_path),prepared_preflight_sha256=sha(preflight_path),default_inputs=rel(DEFAULT_OUT/'inputs.json'),default_inputs_sha256=DEFAULT_INPUTS_SHA,canonical_qualification=rel(CANON),canonical_sha256=sha(CANON),source_sha256=default['source_sha256'],source_origins=default['source_origins'],strategy=STRATEGY,clock_period_ns=10,max_threads=2,memory_limit_bytes=8*1024**3,cpus=2,timeout_seconds=3600,hardware_contact=False)
 for k,v in exact.items():assert activation[k]==v,('activation mismatch',k)
 assert activation['decision_utc'] and activation['reason'] and sha(ROOT/activation['observation_record'])==activation['observation_sha256']
 assert audit['status']=='PASS_THRESHOLD_RUNTIME_ACTIVATION_AUDITED' and audit['activation_record']==rel(ACTIVATION) and audit['activation_sha256']==sha(ACTIVATION)
 assert audit['prepared_preflight']==rel(preflight_path) and audit['prepared_preflight_sha256']==sha(preflight_path)
 dispatch=dict(schema='v107-threshold-runtime-one-shot-dispatch-v1',status='ACTIVATED_HANDOFF',activation_record=rel(ACTIVATION),activation_sha256=sha(ACTIVATION),independent_audit=rel(AUDIT),audit_sha256=sha(AUDIT),preflight=rel(preflight_path),preflight_sha256=sha(preflight_path),prepared_build=str(build),native_attempt_ordinal=9,source_set_ordinal=8,alternate_strategy_ordinal=1,source_files=18)
 with DISPATCH.open('x') as f:f.write(json.dumps(dispatch,indent=2,sort_keys=True)+'\n')
 result=subprocess.run([sys.executable,str(FLOW/'run_vivado2026.py'),'--build',str(build),'--license-file',str(license_file),'--timeout','3600'],cwd=ROOT)
 dispatch.update(status='RUNNER_RETURNED',runner_exit_code=result.returncode);write(DISPATCH,dispatch);result.check_returncode()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--variant',choices=['threshold-runtime'],default='threshold-runtime');ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));args=ap.parse_args()
 if args.run:
  assert args.preflight,'--run requires reviewed immutable --preflight';launch(args.preflight.resolve(),args.license_file)
 else:assert args.preflight is None;prepare()
if __name__=='__main__':main()
