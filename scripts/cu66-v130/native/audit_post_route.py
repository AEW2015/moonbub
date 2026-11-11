#!/usr/bin/env python3
"""Independently audit retained exploratory V130 native evidence; never runs Vivado or edits reports.

Integrity PASS means evidence is consistent, not that 125 MHz, board timing,
30 fps, or end-to-end decode latency passed. Requires a completed native receipt.
"""
import argparse,datetime,hashlib,importlib.util,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
PREVIOUS=ROOT/'experiments/python-gamebub-v129/native/20261111T003938700577Z/receipt.json'
PREVIOUS_SHA='5576fa6e190f82f0583d3e1b5e94b50757d31e11822dcc2d62590a071f1f3ab1'
PARSERS=ROOT/'scripts/cu66-v128/audit_terminal.py'
PARSERS_SHA='246dfb50cc107cc9c9657a5634a34e6ac639f5396bf1693cd550302378122360'
FUNC=ROOT/'experiments/python-gamebub-v129/integration/results.json'
FUNC_AUDIT=ROOT/'experiments/python-gamebub-v129/audit/full-independent.json'
OUT=ROOT/'experiments/python-gamebub-v130/spec-read/audit/native-post-route-independent.json'
COMPOSITION=ROOT/'experiments/python-gamebub-v130/spec-read/composition.json'
FOCUSED=ROOT/'experiments/python-gamebub-v130/spec-read/results.json'
NEGATIVE=ROOT/'experiments/python-gamebub-v130/spec-read/negative/results.json'
ALIAS='fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
FLOW=ROOT/'fpga/experiments/cu66-v120-flow'
SYNTH='synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def need(ok,msg):
 if not ok:raise AssertionError(msg)
def parsers():
 need(sha(PARSERS)==PARSERS_SHA,'frozen V128 pure parser drift')
 spec=importlib.util.spec_from_file_location('v128_frozen_report_parsers',PARSERS);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inspect_reports(receipt,root,m):
 reports=root/'reports';v=receipt['result'];
 timing=m.timing((reports/'route-timing-summary.rpt').read_text());checks=m.check_timing((reports/'route-check-timing.rpt').read_text());routing=m.routing((reports/'route-status.rpt').read_text());worst=m.worst_setup((reports/'route-setup-paths.rpt').read_text())
 need(timing==v['timing'] and checks==v['check_timing'] and routing==v['routing'] and worst==v['worst_setup_path'],'raw report differs from receipt')
 need(timing['WNS_ns']==worst['slack_ns'],'worst path differs from design summary WNS')
 need(checks['unconstrained_internal_endpoints']==0,'unconstrained internal endpoints')
 need(routing['zero_routing_errors'] and routing['all_routable_nets_routed'],'incomplete or error routing')
 settings=dict(x.split('\t',1) for x in (reports/'settings.tsv').read_text().splitlines()[1:]);need(settings['part']=='xc7a100tcsg324-1' and settings['clock']=='component_clk' and float(settings['period_ns'])==8 and settings['tool']=='2026.1' and '6511674' in settings['tool_full'],'settings part/clock/tool')
 need(all(settings[k]==x for k,x in dict(start_mode='rtl',max_threads='2',synth_directive='default',synth_directive_cli='omitted',opt_directive='Default',place_directive='ExtraNetDelay_high',physical_directive='NONE',route_directive='Default').items()),'settings recipe')
 clocks=re.findall(r'^component_clk\s+(\d+\.\d+)\s+\{([^}]+)\}',(reports/'route-clocks.rpt').read_text(),re.M);need(len(clocks)==1 and float(clocks[0][0])==8 and [float(v)for v in clocks[0][1].split()]==[0.,4.],'clock waveform')
 need('No valid timing exceptions found.' in (reports/'route-exceptions.rpt').read_text(),'timing exceptions reported')
 methodology=m.methodology(reports)
 coverage=all(checks[k]==0 for k in checks if k not in ('no_input_delay','no_output_delay'))
 target=all(timing[k]>=0 for k in ('WNS_ns','WHS_ns','WPWS_ns')) and all(timing[k]==0 for k in ('TNS_ns','THS_ns','TPWS_ns','setup_failing','hold_failing','pulse_failing')) and coverage and routing['zero_routing_errors'] and routing['all_routable_nets_routed']
 need(target==v['component_internal_target_pass'],'computed component target pass differs from receipt')
 return dict(timing=timing,check_timing=checks,routing=routing,worst_setup_path=worst,methodology=methodology,component_internal_target_pass=target,external_io=dict(no_input_delay=checks['no_input_delay'],no_output_delay=checks['no_output_delay']))

def verify_receipt(p,m,expected_origin=None):
 d=load(p);root=p.parent;need(d['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and d['observed_exit_code']==0 and d['monitor_stop_reason'] is None and d['component_route_finished'] is True,'job did not complete route')
 need(d['clock_period_ns']==8 and d['part']=='xc7a100tcsg324-1' and d['start_mode']=='rtl' and d['max_threads']==2,'part/clock/fresh RTL')
 need(d['hardware_contact'] is False and d['board_IO_timing_qualified'] is False and d['hardware_30fps'] is False and d['complete_validated_decode_under10ms'] is False and d['bitstream_generated'] is False,'incorrect hardware claim')
 need(d['source_snapshot_readonly_mount'] and d['source_snapshot_unchanged'] and d['recipe_unchanged'] and not d['checkpoint_read'],'snapshot/checkpoint contract')
 artifacts=d['retained_artifact_sha256'];actual={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file() and x.name!='receipt.json'};need(actual==set(artifacts),'retained artifact inventory mismatch')
 for name,h in artifacts.items():need(sha(root/name)==h,'retained artifact mismatch: '+name)
 for name,meta in d['external_artifacts'].items():
  x=Path(meta['external_path']);need(x.parent==Path(d['build_external'])/'results' and x.name==name and x.stat().st_size==meta['bytes'] and sha(x)==meta['sha256'],'external artifact mismatch '+name)
  if (root/'reports'/name).is_file():need(sha(root/'reports'/name)==meta['sha256'],'retained report differs '+name)
 need({'synth.dcp','route.dcp'}.issubset(d['external_artifacts']),'missing checkpoints')
 origins=d['source_contract']['source_origins'];need(len(origins)==18,'origin count')
 if expected_origin is not None:need(origins==expected_origin,'candidate composition differs from selected V130 exploratory source map')
 for alias,meta in origins.items():need(sha(ROOT/meta['path'])==meta['sha256'] and sha(root/'source-snapshot'/alias)==meta['sha256'],'source snapshot '+alias)
 for pth,h in d['source_contract']['proof_pins'].items():need(sha(ROOT/pth)==h,'proof pin '+pth)
 recipe=root/'recipe-snapshot'
 for name,h in d['recipe_sha256'].items():need(sha(recipe/name)==h,'recipe snapshot '+name)
 for name in ('run.tcl','report.tcl'):need(sha(recipe/name)==sha(FLOW/name),'fixed core recipe '+name)
 need(sha(recipe/'component.xdc')==sha(FLOW/'clock-125.xdc'),'constraint file changed')
 text=(recipe/'run.tcl').read_text();need(text.index('read_xdc $constraint_file')<text.index('synth_design -top'),'XDC not before synthesis')
 order=d['source_contract']['source_order']['rtl_read_order_aliases'];inputstcl=(recipe/'inputs.tcl').read_text();match=re.search(r'^set rtl_sources \[list (.*)\]$',inputstcl,re.M);need(match is not None,'missing input list')
 mapped='/build/'+Path(d['build_external']).name;need(re.findall(r'\{([^}]+)\}',match.group(1))==[mapped+'/snapshot/'+x for x in order],'actual RTL read order drift')
 cmd=d['command'];need('type=bind,src='+str(Path(d['build_external'])/'snapshot')+',dst='+mapped+'/snapshot,readonly' in cmd and cmd[cmd.index('--memory')+1]=='8g' and cmd[cmd.index('--memory-swap')+1]=='8g' and cmd[cmd.index('--cpus')+1]=='2','command source readonly / resource caps')
 log=(root/'vivado.log').read_text(errors='replace');need(sha(root/'vivado.log')==d['log_sha256'] and 'Vivado v2026.1' in log and '6511674' in log and 'V120_COMPONENT_ROUTE_FINISHED' in log,'transcript identity, version, or completion')
 synth=re.findall(r'^Command:\s*(synth_design[^\n]*)',log,re.M);need(synth==[SYNTH]==d['synthesis_command_lines'] and d['observed_default_command_exact'],'actual synth command');need(not re.search(r'^Command:\s*(?:open_checkpoint|read_checkpoint)\b',log,re.M),'checkpoint-based implementation')
 need('Parsing XDC File ['+mapped+'/component.xdc]' in log,'XDC parse evidence')
 return d,inspect_reports(d,root,m)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--receipt',type=Path);ap.add_argument('--output',type=Path,default=OUT);ap.add_argument('--self-test',action='store_true');a=ap.parse_args();m=parsers()
 need(sha(PREVIOUS)==PREVIOUS_SHA,'V129 baseline receipt drift');old,oldr=verify_receipt(PREVIOUS,m)
 if a.self_test:
  need(oldr['timing']['WNS_ns']==-1.257 and oldr['check_timing']['unconstrained_internal_endpoints']==0,'V129 baseline regression');print('V130_POST_ROUTE_AUDITOR_BASELINE_SELF_TEST_PASS; no V130 run audited');return
 need(a.receipt is not None,'--receipt required for V130 audit')
 idx=load(FUNC);ia=load(FUNC_AUDIT);need(idx['status']=='PASS_V129_FULL_FUNCTIONAL' and ia['status']=='PASS_INDEPENDENT_V129_FULL_FUNCTIONAL_AUDIT' and ia['integration_index_sha256']==sha(FUNC),'V129 functional baseline chain')
 comp=load(COMPOSITION);need(comp['schema']=='v130-spec-read-candidate-composition-v1' and comp['changed_aliases']==[ALIAS] and comp['full_parent_functional_pass'] is False and comp['hardware_qualification'] is False,'speculative candidate scope')
 for selector,status in ((FOCUSED,'PASS'),(NEGATIVE,'PASS_NEGATIVE_CONTROLS')):
  sel=load(selector);path=ROOT/sel['path'];need(sel['status']==status and sel['actual_RTL_run'] is True and sha(path)==sel['sha256'] and load(path)['status']==status,'focused receipt')
 d,new=verify_receipt(a.receipt,m,comp['source_origins'])
 need(d['full_parent_functional_pass'] is False and d['release_qualified'] is False and d['invalid_data_consumer_contract']=='UNKNOWN' and d['invalid_data_external_consumer_contract']=='UNKNOWN','exploratory scope labels missing')
 for p in (FUNC,FUNC_AUDIT,COMPOSITION,FOCUSED,NEGATIVE):need(d['source_contract']['proof_pins'][str(p.relative_to(ROOT))]==sha(p),'source proof pin')
 changed=[k for k in d['source_contract']['source_origins'] if d['source_contract']['source_origins'][k]!=old['source_contract']['source_origins'][k]];need(changed==[ALIAS],'baseline composition delta')
 need(d['source_contract']['source_order']==old['source_contract']['source_order'] and all(d['recipe_sha256'][x]==old['recipe_sha256'][x] for x in ('run.tcl','report.tcl','component.xdc')),'comparison recipe or source order changed')
 metrics={k:new['timing'][k]-oldr['timing'][k] for k in new['timing']}
 result=dict(schema='v130-independent-post-route-audit-v1',status='PASS_V130_INDEPENDENT_POST_ROUTE_EVIDENCE',candidate_receipt=dict(path=str(a.receipt.resolve()),sha256=sha(a.receipt)),baseline_v129_receipt=dict(path=str(PREVIOUS.relative_to(ROOT)),sha256=PREVIOUS_SHA),functional_baseline_index_sha256=sha(FUNC),functional_baseline_audit_sha256=sha(FUNC_AUDIT),composition_sha256=sha(COMPOSITION),focused_sha256=sha(FOCUSED),negative_sha256=sha(NEGATIVE),candidate=new,baseline_v129=oldr,timing_delta_vs_v129=metrics,worst_path_source_changed=new['worst_setup_path']['source']!=oldr['worst_setup_path']['source'],worst_path_destination_changed=new['worst_setup_path']['destination']!=oldr['worst_setup_path']['destination'],changed_aliases=changed,parser_script_sha256=PARSERS_SHA,methodology_fresh=True,report_preserved=True,full_parent_functional_pass=False,invalid_data_consumer_contract='UNKNOWN',release_qualified=False,board_io_timing_qualified=False,hardware_30fps=False,complete_validated_decode_under10ms=False,scope='Exploratory out-of-context component route; no V130 full-parent behavior, invalid-data-consumer, board, or hardware qualification.')
 a.output.parent.mkdir(parents=True,exist_ok=True);attempt=a.output.parent/(a.output.stem+'-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json');payload=json.dumps(result,indent=2,sort_keys=True)+'\n'
 with attempt.open('x') as f:f.write(payload)
 a.output.write_text(payload);print(result['status'],'component_internal_target_pass='+str(new['component_internal_target_pass']),a.output,sha(a.output))
if __name__=='__main__':main()
