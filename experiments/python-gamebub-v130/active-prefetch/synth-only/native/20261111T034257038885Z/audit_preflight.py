#!/usr/bin/env python3
"""Independent preflight inspection for V130 active-scan synth-only trial."""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];FLOW=ROOT/'fpga/experiments/cu66-v120-flow';PREV=ROOT/'experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json';BASE=ROOT/'experiments/python-gamebub-v120/handoff.json';POS=ROOT/'experiments/python-gamebub-v130/active-prefetch/results.json';NEG=ROOT/'experiments/python-gamebub-v130/active-prefetch/negative/results.json';DER=ROOT/'fpga/experiments/cu66-v130-active-prefetch/derivation.json';CAND=ROOT/'fpga/experiments/cu66-v130-active-prefetch/cs88_admission_v91i2a.sv';NATIVE=Path(__file__).with_name('native.py');ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv';IMAGE='sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742';GIB=1024**3
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
rel=lambda p:str(Path(p).resolve().relative_to(ROOT))
def need(x,msg):
 if not x:raise ValueError(msg)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('preflight',type=Path);ap.add_argument('--auditor',required=True);a=ap.parse_args();p=load(a.preflight);prev=load(PREV);gold=load(BASE);d=load(DER);build=Path(p['build_external']).resolve();orig=ROOT/d['source'];candidate=CAND.read_text();source=orig.read_text()
 need(p['schema']=='v130-active-synth-preflight-v1' and p['status']=='PREPARED_NOT_RUN','preflight status');need(sha(orig)==d['source_sha256'] and sha(CAND)==d['candidate_sha256'],'candidate hash')
 for e in d['edits']:
  need(source.count(e['old'])==1,'forward edit');source=source.replace(e['old'],e['new'],1)
 need(source==candidate,'candidate reconstruction')
 for e in reversed(d['edits']):
  need(source.count(e['new'])==1,'reverse edit');source=source.replace(e['new'],e['old'],1)
 need(source==orig.read_text(),'reverse mismatch')
 base=prev['source_contract']['source_origins'];actual=p['source_contract']['source_origins'];need(len(actual)==18 and set(actual)==set(base) and base[ALIAS]=={'path':rel(orig),'sha256':sha(orig)} and actual[ALIAS]=={'path':rel(CAND),'sha256':sha(CAND)},'18 origin mapping')
 need({k for k in actual if actual[k]!=base[k]}=={ALIAS},'composition delta');need(p['source_contract']['source_order']==prev['source_contract']['source_order']==gold['source_order'],'source order')
 for alias,meta in actual.items():need(sha(ROOT/meta['path'])==meta['sha256']==sha(build/'snapshot'/alias),'source/snapshot '+alias)
 for selector,expected in ((POS,'PASS'),(NEG,'PASS_EXPECTED_FAILURE_DETECTED')):
  x=load(selector);receipt=ROOT/x['path'];need(x['status']==expected and sha(receipt)==x['sha256'] and p['source_contract']['proof_pins'][rel(selector)]==sha(selector) and p['source_contract']['proof_pins'][rel(receipt)]==sha(receipt),'selector/receipt '+expected)
  rec=load(receipt);need(rec['status']==expected and rec['actual_RTL_run'] is True,'executed proof '+expected)
  if selector==POS:
   need(rec['source_snapshot_unchanged'] is True and rec['source_sha256'][rel(CAND)]==sha(CAND),'positive pin')
   for path,h in rec['source_sha256'].items():need(sha(ROOT/path)==h and sha(receipt.parent/'sources'/path)==h,'positive source '+path)
   for path,h in rec['artifact_sha256'].items():need(sha(receipt.parent/path)==h,'positive artifact '+path)
   need(len(rec['runs'])==2 and {r[1]['seed'] for r in rec['runs']}=={130301,130302} and all(r[0]['cases']==6 and r[0]['cancellations']==15 and r[1]['same_epoch_retry'] and r[1]['invalid_databus_qualified'] for r in rec['runs']),'positive scenario coverage')
   commands=[x['argv'] for x in rec['commands'] if 'verilator' in x['argv']];need(bool(commands) and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c and '-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS')+1] for c in commands),'strict compile')
  else:
   need(rec['observed_exit_code'] not in (0,124,137) and rec['stop_reason'] is None and rec['expected_detection'] in (receipt.parent/'simulation.log').read_text() and sha(receipt.parent/'simulation.log')==rec['simulation_log_sha256'],'expected failure evidence')
 need(p['part']=='xc7a100tcsg324-1' and p['top']=='cs88_pipeline_v91k' and p['clock_period_ns']==8.0 and p['start_mode']=='rtl' and p['image_id']==IMAGE,'part clock tool');need(p['cpus']==p['max_threads']==2 and p['memory_limit_bytes']==p['memory_swap_limit_bytes']==8*GIB and p['timeout_seconds']==3600,'resource limits');need(p['route_run'] is False and p['hardware_contact'] is False and p['timing_qualified'] is False,'scope')
 fixed=(FLOW/'run.tcl').read_text();prefix=fixed[:fixed.index('v116_phase OPT_DESIGN')];text=(build/'run.tcl').read_text();need(text.startswith(prefix),'synthesis prefix changed');suffix=text[len(prefix):];need('V130_ACTIVE_SYNTH_ONLY_FINISHED' in suffix and 'active-cell-inventory.tsv' in suffix and not re.search(r'\b(?:set_property|read_xdc|synth_design|opt_design|place_design|route_design|write_bitstream|set_false_path|set_multicycle_path|set_clock_groups)\b',suffix,re.I),'unexpected suffix commands')
 need(sha(build/'report.tcl')==sha(FLOW/'report.tcl') and sha(build/'component.xdc')==sha(FLOW/'clock-125.xdc'),'fixed report or clock drift');need(prefix.index('read_xdc $constraint_file')<prefix.index('synth_design -top'),'clock applied after synth')
 mapped='/build/'+build.name;order=gold['source_order'];w=lambda x:'{'+x+'}'
 expected=['set part xc7a100tcsg324-1','set trial_id {active-synth-125}','set start_mode {rtl}','set expected_period_ns 8.0','set opt_directive {Default}','set place_directive {ExtraNetDelay_high}','set phys_directive {NONE}','set route_directive {Default}','set rtl_sources [list '+' '.join(w(mapped+'/snapshot/'+n) for n in order['rtl_read_order_aliases'])+']','set include_dirs [list '+' '.join(w(mapped+'/snapshot/'+n) for n in order['include_directory_aliases'])+']','set constraint_file '+w(mapped+'/component.xdc')]
 need((build/'inputs.tcl').read_text()=='\n'.join(expected)+'\n','input Tcl content/order')
 for k,h in p['recipe_sha256'].items():need(sha(build/k)==h,'recipe hash '+k)
 for k,h in p['tooling_sha256'].items():need(sha(ROOT/k)==h,'tooling hash '+k)
 need(sha(build/'inputs.json')==p['inputs_sha256'] and load(build/'inputs.json')=={k:v for k,v in p.items() if k!='inputs_sha256'},'input card mismatch')
 result={'schema':'v130-active-synth-preflight-audit-v1','status':'PASS_ACTIVE_SYNTH_PREFLIGHT_AUDIT','auditor':a.auditor,'preflight_sha256':sha(a.preflight),'auditor_sha256':sha(Path(__file__)),'native_sha256':sha(NATIVE),'origin_count':18,'changed_aliases':[ALIAS],'fixed_synthesis_prefix_verified':True,'new_actions':'read-only active-cell inventory, then stop','no_timing_exceptions_added':True,'no_route_or_board_claim':True}
 out=a.preflight.parent/'audit.json';out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(out)
if __name__=='__main__':
 try:main()
 except Exception as e:print('ACTIVE_SYNTH_PREFLIGHT_AUDIT_FAIL:',e,file=sys.stderr);raise SystemExit(1)
