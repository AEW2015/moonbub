#!/usr/bin/env python3
"""Read-only validation of a V130 speculative OOC timing preflight.

Passing this audit authorizes no hardware or full-parent functionality claim.
"""
from pathlib import Path
import argparse, hashlib, json, re, sys
ROOT=Path(__file__).resolve().parents[3]
FLOW=ROOT/'fpga/experiments/cu66-v120-flow'
BASE=ROOT/'experiments/python-gamebub-v120/handoff.json'
Q=ROOT/'experiments/python-gamebub-v129/integration/results.json'
V129_AUDIT=ROOT/'experiments/python-gamebub-v129/audit/full-independent.json'
COMP=ROOT/'experiments/python-gamebub-v130/spec-read/composition.json'
FOCUS=ROOT/'experiments/python-gamebub-v130/spec-read/results.json'
NEGATIVE=ROOT/'experiments/python-gamebub-v130/spec-read/negative/results.json'
NATIVE=Path(__file__).with_name('native.py')
ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
CANDIDATE='fpga/experiments/cu66-v130-spec-read/cs88_admission_v91i2a.sv'
IMAGE='sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def need(b,m):
 if not b:raise ValueError(m)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('preflight',type=Path);ap.add_argument('--auditor',required=True);a=ap.parse_args()
 p=load(a.preflight);baseline=load(BASE);q=load(Q); independent=load(V129_AUDIT); comp=load(COMP); b=Path(p['build_external']).resolve()
 need(p['schema']=='v130-native-preflight-v1' and p['status']=='PREPARED_NOT_RUN','preflight state')
 need(q['status']=='PASS_V129_FULL_FUNCTIONAL' and independent['status']=='PASS_INDEPENDENT_V129_FULL_FUNCTIONAL_AUDIT' and independent['integration_index_sha256']==sha(Q),'V129 baseline proof')
 need(comp['schema']=='v130-spec-read-candidate-composition-v1' and comp['changed_aliases']==[ALIAS] and comp['full_parent_functional_pass'] is False and comp['hardware_qualification'] is False,'composition contract')
 origins=comp['source_origins'];old=q['source_origins'];need(len(origins)==18 and set(origins)==set(old) and {k for k in origins if origins[k]!=old[k]}=={ALIAS},'candidate delta')
 need(origins[ALIAS]['path']==CANDIDATE and p['source_contract']['source_origins']==origins,'candidate path')
 for k,v in origins.items():need(sha(ROOT/v['path'])==v['sha256']==sha(b/'snapshot'/k),'source snapshot '+k)
 parts=comp['packaging']['fragments'];need(b''.join((ROOT/f['path']).read_bytes() for f in parts)==(ROOT/CANDIDATE).read_bytes(),'candidate packaging')
 for f in parts:need(sha(ROOT/f['path'])==f['sha256'] and (ROOT/f['path']).stat().st_size==f['bytes'],'candidate fragment')
 need(p['source_contract']['source_order']==baseline['source_order'],'source order')
 pins=p['source_contract']['proof_pins'];need(pins.get(str(COMP.relative_to(ROOT)))==sha(COMP),'composition pin')
 for sel,expected in ((FOCUS,'PASS'),(NEGATIVE,'PASS_NEGATIVE_CONTROLS')):
  s=load(sel);receipt=ROOT/s['path'];need(s['status']==expected and sha(receipt)==s['sha256'],'receipt selector')
  d=load(receipt);need(d['status']==expected and d['actual_RTL_run'] is True and d['source_snapshot_unchanged'] is True and d['source_sha256'][CANDIDATE]==origins[ALIAS]['sha256'],'focused receipt')
  runs=d.get('runs',[])
  if sel==FOCUS:need({r.get('seed') for r in runs}=={130101,130102} and all(r.get('status')=='PASS' and r.get('same_epoch_retry') is True and r.get('stage_cancel_cases')==6 and r.get('replay_cancel_cases')==6 and r.get('invalid_databus_qualified') is True for r in runs),'focused scenarios')
  else:need({r.get('mutant') for r in runs}=={'unclamped','abort_mask_removed'} and all(r.get('observed_detection') is True and r.get('expected_failure') and r['expected_failure'] in (receipt.parent/('mutant-'+r['mutant']+'.log')).read_text() for r in runs),'mutant evidence')
  need(pins.get(str(sel.relative_to(ROOT)))==sha(sel) and pins.get(str(receipt.relative_to(ROOT)))==sha(receipt),'focused pins')
  for source,h in d['source_sha256'].items():need(sha(ROOT/source)==h==sha(receipt.parent/'sources'/source),'focused source')
  for artifact,h in d['artifact_sha256'].items():need(sha(receipt.parent/artifact)==h,'focused artifact')
  commands=d['commands'];builds=[c for c in commands if 'verilator' in c['argv'] and '--cc' in c['argv']];need(builds,'no compile')
  for cmd in builds:
   c=cmd['argv'];need(cmd['exit_code']==0 and '--assert' in c and '-Wall' in c and '-Wno-fatal' not in c and '-Werror' in c[c.index('-CFLAGS')+1],'compile flags/status')
  sims=[x for x in commands if 'verilator' not in x['argv']];need(len(sims)==2 and all((x['exit_code']==0 if expected=='PASS' else x['exit_code'] not in (0,124,137)) for x in sims),'simulation status')
 need(p['part']=='xc7a100tcsg324-1' and p['top']=='cs88_pipeline_v91k' and p['image_id']==IMAGE and p['clock_period_ns']==8.0 and p['start_mode']=='rtl','device/clock/tool')
 need(p['cpus']==2 and p['max_threads']==2 and p['memory_limit_bytes']==8*1024**3 and p['memory_swap_limit_bytes']==8*1024**3 and p['timeout_seconds']==3600,'resource policy')
 need(p['hardware_contact'] is False and p['bitstream_generated'] is False and p['full_parent_functional_pass'] is False and p['release_qualified'] is False and p['invalid_data_external_consumer_contract']=='UNKNOWN','scope mislabel')
 for n in ('run.tcl','report.tcl'):need(sha(b/n)==p['recipe_sha256'][n]==baseline['recipe_sha256'][n],'recipe '+n)
 need(sha(b/'component.xdc')==sha(FLOW/'clock-125.xdc')==p['recipe_sha256']['component.xdc'],'xdc mismatch')
 need(sha(b/'inputs.tcl')==p['recipe_sha256']['inputs.tcl'],'Tcl hash')
 mapped=Path('/build')/b.name
 def word(s):
  s=str(s);need(not any(c in s for c in '{}\r\n'),'unsafe path');return '{'+s+'}'
 order=baseline['source_order']
 expected=['set part xc7a100tcsg324-1','set trial_id {spec-read-125}','set start_mode {rtl}','set expected_period_ns 8.0','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}', 'set rtl_sources [list '+' '.join(word(mapped/'snapshot'/x) for x in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(word(mapped/'snapshot'/x) for x in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
 need((b/'inputs.tcl').read_text()=='\n'.join(expected)+'\n','Tcl contents')
 run=(b/'run.tcl').read_text();need(run.index('read_xdc $constraint_file')<run.index('synth_design -top'),'xdc ordering')
 forbidden=re.compile(r'\b(set_false_path|set_multicycle_path|set_clock_groups|set_max_delay|set_min_delay|disable_timing|waiver)\b',re.I)
 for n in ('run.tcl','report.tcl','component.xdc'):need(not forbidden.search((b/n).read_text()),'timing exception')
 for rel,digest in p['tooling_sha256'].items():need(sha(ROOT/rel)==digest,'tool hash')
 need(sha(b/'inputs.json')==p['inputs_sha256'] and load(b/'inputs.json')=={k:v for k,v in p.items() if k!='inputs_sha256'},'inputs')
 result={'status':'PASS_V130_NATIVE_PREFLIGHT_AUDIT','auditor':a.auditor,'preflight_sha256':sha(a.preflight),'native_source_sha256':sha(NATIVE),'audit_source_sha256':sha(Path(__file__)),'independent_source_recipe_resource_checks':True,'full_parent_functional_pass':False,'invalid_data_consumer_contract':'UNKNOWN','hardware_qualification':False}
 out=a.preflight.parent/'audit.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(out)
if __name__=='__main__':
 try:main()
 except Exception as e:print('V130_PREFLIGHT_AUDIT_FAIL:',e,file=sys.stderr);raise SystemExit(1)
