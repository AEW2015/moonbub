#!/usr/bin/env python3
"""Independent V128 focused/full evidence checks; immutable V127 comparators."""
import argparse,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v128'
sys.path.insert(0,str(Path(__file__).parent/'integration'))
from contract import BASELINE,BASELINE_SHA,BASELINE_AUDIT,BASELINE_AUDIT_SHA,LEGACY_AUDITOR,LEGACY_AUDITOR_SHA,COMPOSITION,composition,legacy,load,sha,pin,verify

def need(x,message):
 if not x:raise AssertionError(message)

def raw_focused(path,r):
 need(r['schema']=='v128-raw-paired-scratch-and-extracted-algebra-v1'and r['status']=='PASS'and r['actual_RTL_run'] is True,'raw focused gate')
 need(r['all_original_oracles_retained']and not r['assertions_disabled_or_downgraded']and r['new_result_or_owner_forces']==r['declared_public_cycle_delta']==0,'raw assertion/cycle contract')
 need(r['compiled_input_snapshots_unchanged']is True and r['retained_source_snapshots_unchanged']is True,'actual compiled/source snapshots changed')
 need(r['clock_pair_uses_actual_public_begin_and_memory'] is True and r['prepared_phase_domain_is_natural_packets']is False,'raw domain classification')
 checked=[]
 for suite,seeds in [('wire',[128501,128502]),('clock',[128601,128602])]:
  need([x['seed']for x in r[suite+'_runs']]==seeds,'raw exact seed order')
  for verdict in r[suite+'_runs']:
   p=path.parent/(suite+'-'+str(verdict['seed'])+'.jsonl');rows=[json.loads(x)for x in p.read_text().splitlines()]
   need(rows==[verdict]and verdict['status']=='TEST_PASS','raw stdout verdict identity')
   if suite=='wire':
    expected=dict(cases=196608,boundary_cases=131072,random_cases=65536,phase_checks=1572864,selector_mask=3,format_mask=3,phase_mask=255,DUT_clocks=0,new_result_forces=0)
    need(verdict['natural_packets']is False and all(verdict[k]>0 for k in ['coherent_literal_checks','good','bad','selected_only_bad','other_only_bad','high_epoch_cases','high_block_cases','arbitrary_mask_cases']),'raw wire positive/full-width coverage')
    need(verdict['coherent_literal_checks']==16384 and verdict['arbitrary_mask_cases']==180224,'raw exact coherent/arbitrary domains')
   else:
    expected=dict(cases=74,epoch_errors=10,format_errors=50,phase_mask=15,selector_mask=3,format_mask=3,pending_faults=4,wrong_ack_cases=2,cancel_cases=4,unready_offers=2,band_epoch_errors=2,same_edge_accept_faults=2,retries=12,public_cycle_delta=0,prepared_state_forces=0,new_result_forces=0)
    need(verdict['clock_edges']>0 and verdict['eval_checks']>=3*verdict['clock_edges'] and verdict['requests']==verdict['acks']and verdict['requests']>0,'real paired clock/debt coverage')
   need(all(verdict[k]==v for k,v in expected.items()),'raw exact coverage inventory')
   checked.append(dict(kind=suite,seed=verdict['seed'],raw_log_sha256=sha(p),verdict=verdict))
 recipe_path=ROOT/'fpga/experiments/cu66-v128-raw/verification-recipe.json';vr=load(recipe_path)
 for f in vr['fragments']:
  source=ROOT/f['source']['path'];need(pin(source)==f['source']and source.read_text().count(f['fragment'])==1,'raw extracted source fragment binding')
 need(vr['baseline_module_rename_only']and vr['original_assertions_retained']and vr['source_payload_or_owner_forces']==0,'raw source adapter contract')
 for p,h in vr['files'].items():need(sha(ROOT/p)==h,'raw fixture file binding')
 old=ROOT/vr['baseline']['path'];renamed=ROOT/'fpga/experiments/cu66-v128-raw/verification/v128_scratch_baseline.sv'
 need(old.read_text().replace('module packed_scratch_v91g2 (','module v128_scratch_baseline (',1)==renamed.read_text(),'baseline actual scratch namespace-only adaptation')
 cpp=(ROOT/'fpga/experiments/cu66-v128-raw/verification/tb_raw.cpp').read_text();need('__DOT__'not in cpp and 'rootp'not in cpp,'raw C++ may not write private state')
 return dict(receipt=pin(path),runs=checked,source_binding=pin(recipe_path))

def padding_focused(path,r):
 need(r['schema']=='v128-owned-header-padding-focused-v1'and r['status']=='PASS'and r['actual_RTL_run']is True,'padding focused gate')
 need(r['source_kernel']is True and r['actual_full_admission_FSM']is False and r['original_guards_retained']is True,'padding scope and guards')
 need(r['declared_public_cycle_delta']==0 and r['source_payload_bits_added']==1 and r['new_payload_or_owner_forces']==0,'padding cycle/state contract')
 need([x['seed']for x in r['runs']]==[128701,128702],'padding exact seeds/order')
 checked=[]
 import gzip
 for run in r['runs']:
  seed=run['seed'];log=path.parent/('seed-'+str(seed)+'.log');records=[json.loads(x)for x in log.read_text().splitlines()if x.startswith('{')]
  need(records==[run['verdict']],'padding exact raw terminal record');v=records[0]
  need(v['type']=='v128_padding_clock_verdict'and v['status']=='TEST_PASS'and v['seed']==seed,'padding terminal identity')
  exact=dict(exhaustive_single_byte_cases=3072,random_header_cases=4096,cancel_prefix_cases=84,incomplete_prefix_checks=12,nonwriter_hold_checks=558,nonpadding_writer_hold_checks=6,last_byte_forwarding_cases=2,unowned_canceled_payload_changes=84,completed_headers=7268,public_cycle_delta=0,new_payload_or_owner_forces=0)
  need(all(v[k]==n for k,n in exact.items()),'padding exact coverage inventory')
  need(v['equality_evaluations']==3*v['clock_edges']==v['view_checks']and v['payload_captures']>12*v['completed_headers'],'padding real kernel writer/equality coverage')
  need(v['source_kernel']is True and v['actual_full_admission_FSM']is False and len(v['error_classes'])>=9 and all(v['error_classes'][e]>0 for e in [0,4,5,6,7,8]),'padding source-kernel error priority coverage')
  trace=path.parent/run['retained_trace'];raw=gzip.decompress(trace.read_bytes());need(hashlib.sha256(raw).hexdigest()==run['raw_trace_sha256'],'padding decompressed case trace SHA')
  rows=[json.loads(x)for x in raw.splitlines()];need(len(rows)==run['trace_rows']==7268 and all(x['case']==i+1 for i,x in enumerate(rows)),'padding complete ordered trace')
  checked.append(dict(seed=seed,raw_log_sha256=sha(log),trace=pin(trace),raw_trace_sha256=run['raw_trace_sha256'],terminal=v))
 vr=load(ROOT/'fpga/experiments/cu66-v128-padding/verification-recipe.json')
 need(vr['scoped_source_kernel']and not vr['full_admission_model']and not vr['actual_FSM_executed']and vr['private_new_payload_or_owner_forces']==0,'padding fixture classification')
 for field in ['preparer','original','candidate','target','bench']:need(pin(ROOT/vr[field]['path'])==vr[field],'padding fixture pin '+field)
 need(len(vr['kernel_modules'])==3,'padding three matching-name kernel files')
 for meta in vr['kernel_modules']:need(pin(ROOT/meta['path'])==meta,'padding kernel file pin')
 bundle=''.join((ROOT/meta['path']).read_text()for meta in vr['kernel_modules'])
 need(hashlib.sha256(bundle.encode()).hexdigest()==vr['kernel_bundle_sha256'],'padding lossless kernel bundle')
 old=(ROOT/vr['original']['path']).read_text();new=(ROOT/vr['candidate']['path']).read_text()
 for name,fragment in vr['source_fragments'].items():need(fragment in old or fragment in new,'padding literal source fragment '+name)
 return dict(receipt=pin(path),runs=checked,source_binding=pin(ROOT/'fpga/experiments/cu66-v128-padding/verification-recipe.json'))

def focus_audit(index):
 pmeta=index['stages']['focused'];_,p,r=legacy().resolve_stage(pmeta);legacy().verify_closure(p,r,'V128 aggregate focused')
 need(r['schema']=='v128-separated-raw-padding-focused-aggregate-v1'and r['status']=='PASS'and r['actual_RTL_run']is True,'focused aggregate schema')
 need(r['aggregate_is_single_whole_composition_binary']is False,'focused separate execution classification')
 c=composition();need(r['source_origins']==c['complete_source_origins']and r['proof_roles']==c['proof_roles'],'aggregate current five-source role bindings')
 components={}
 for role,meta in r['focused_components'].items():
  selector=ROOT/meta['selector']['path'];need(pin(selector)==meta['selector'],'focused child selector SHA')
  rawpath=ROOT/meta['receipt']['path'];need(pin(rawpath)==meta['receipt'],'focused child receipt SHA')
  s=load(selector);need(s['path']==meta['receipt']['path']and s['sha256']==meta['receipt']['sha256'],'focused selector binding')
  raw=load(rawpath);legacy().verify_closure(rawpath,raw,role)
  for alias in c['proof_roles'][role]:need(raw['source_sha256'].get(c['source_origins'][alias]['path'])==c['source_origins'][alias]['sha256'],'focused changed origin lacks current execution binding')
  components[role]=raw_focused(rawpath,raw)if role=='raw_validation'else padding_focused(rawpath,raw)
 need(set(components)=={'raw_validation','header_padding'},'focused two component inventory')
 return p,components

def self_baseline(output):
 need(sha(BASELINE)==BASELINE_SHA and sha(LEGACY_AUDITOR)==LEGACY_AUDITOR_SHA,'frozen V127 baseline pins')
 m=legacy();b=load(BASELINE);resolved={n:m.resolve_stage(v)[1:]for n,v in b['stages'].items()}
 counts={}
 for name,fn in [('spatial',m.compare_spatial),('peer',m.compare_peer),('parent',m.compare_parent)]:
  p,r=resolved[name];m.verify_closure(p,r,'baseline self '+name);counts[name]=len(fn(p,r,p,r))
 need(counts==dict(spatial=4,peer=2,parent=4),'baseline helper exercise counts')
 result=dict(schema='v128-inherited-auditor-baseline-self-check-v1',status='PASS_BASELINE_SELF_CHECK',legacy_auditor=pin(LEGACY_AUDITOR),baseline=pin(BASELINE),raw_comparison_counts=counts,actual_RTL_run=False,hardware_contact=False)
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--integration',type=Path,default=AREA/'integration/results.json');ap.add_argument('--output',type=Path,default=AREA/'audit/full-independent.json');ap.add_argument('--self-baseline',action='store_true');ap.add_argument('--focused-only',action='store_true');a=ap.parse_args()
 if a.self_baseline:r=self_baseline(a.output);print(r['status']);return
 verify();c=composition()
 if a.focused_only:
  selector=AREA/'focused/results.json';s=load(selector);rp=ROOT/s['path'];dummy={'stages':{'focused':dict(path=str(selector.relative_to(ROOT)),sha256=sha(selector),receipt=dict(path=s['path'],sha256=s['sha256']))}}
  _,checked=focus_audit(dummy);result=dict(schema='v128-independent-focused-audit-v1',status='PASS_INDEPENDENT_V128_FOCUSED_AUDIT',focused_receipt=pin(rp),components=checked,source_aliases=sorted(c['source_origins']),declared_public_cycle_delta=0,all_original_oracles_retained=True,assertions_disabled_or_downgraded=False)
 else:
  idx=load(a.integration);need(idx['schema']=='v128-raw-functional-composition-v1'and idx['status']=='PASS_V128_RAW_FULL_FUNCTIONAL','full functional gate')
  need(idx['all_original_oracles_retained']and idx['exact_B_public_cycles']and not idx['assertions_disabled_or_downgraded']and idx['declared_public_cycle_delta']==0,'full functional contract')
  need(set(idx['stages'])=={'focused','spatial','peer','parent'}and idx['source_origins']==c['complete_source_origins'],'four current stages/source map')
  expected=[{load(BASELINE)['source_origins'][alias]['path']:meta['path']for alias,meta in c['source_origins'].items()}.get(p,p)for p in load(BASELINE)['rtl_source_order']];need(idx['rtl_source_order']==expected,'core18 source order')
  focused,components=focus_audit(idx);m=legacy();raws={};closures={}
  for name,meta in idx['stages'].items():
   _,p,r=m.resolve_stage(meta);counts=m.verify_closure(p,r,name);closures[name]=dict(sources=counts[0],artifacts=counts[1]);raws[name]=(p,r)
   if name!='focused':
    need(r['source_origins']==idx['source_origins'],'stage current source map '+name)
    bp,br=m.resolve_stage(load(BASELINE)['stages'][name])[1:];remap={load(BASELINE)['source_origins'][a]['path']:v['path']for a,v in c['source_origins'].items()};need(r['rtl_source_order']==[remap.get(p,p)for p in br['rtl_source_order']],'full stage exact source order '+name)
  checks={}
  for name,fn in [('spatial',m.compare_spatial),('peer',m.compare_peer),('parent',m.compare_parent)]:
   p,r=raws[name];bp,br=m.resolve_stage(load(BASELINE)['stages'][name])[1:];checks[name]=fn(p,r,bp,br)
  counts={k:len(v)for k,v in checks.items()};need(counts==dict(spatial=4,peer=2,parent=4),'full raw comparison counts')
  qualified=load(ROOT/'experiments/python-gamebub-v120/handoff.json');need(len(qualified['source_origins'])==18,'qualified original18')
  for meta in qualified['source_origins'].values():need(sha(ROOT/meta['path'])==meta['sha256'],'qualified Source B file drift')
  result=dict(schema='v128-independent-full-functional-audit-v1',status='PASS_INDEPENDENT_V128_FULL_FUNCTIONAL_AUDIT',integration_index_sha256=sha(a.integration),integration=pin(a.integration),source_B_count=18,source_B_hashes_match_handoff=True,v128_changed_aliases=sorted(c['source_origins']),source_origins=c['complete_source_origins'],source_count=18,focused_components=components,source_artifact_closure=closures,exact_comparisons=dict(spatial_stdout_event_and_canonical_streams=4,peer_stdout_event_and_canonical_streams=2,parent_stdout_and_terminal_stream_sets=4),raw_comparison_evidence=checks,legacy_auditor=pin(LEGACY_AUDITOR),baseline_index=pin(BASELINE),baseline_self_check=pin(AREA/'audit/baseline-self-check.json'),inherited_v127_recheck=pin(AREA/'audit/inherited-v127-recheck.json'),all_original_oracles_retained=True,assertions_disabled_or_downgraded=False,declared_public_cycle_delta=0,hardware_contact=False)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'],sha(a.output))
if __name__=='__main__':main()
