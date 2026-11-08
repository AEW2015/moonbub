#!/usr/bin/env python3
"""Run a bounded qualified V110 native trial with explicit RTL/checkpoint provenance."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v110/count-domain-native'
BUILD_ROOT=Path('/home/lori/gamebub-build/cu66-v69')
TOOLS=Path('/home/lori/acorn-nexys4-ddr/tools')

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def memory():
    info={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
    full=next(line for line in Path('/proc/pressure/memory').read_text().splitlines() if line.startswith('full '))
    return dict(MemAvailable_bytes=info['MemAvailable'],PSI_full_avg10=float(full.split('avg10=')[1].split()[0]))

def timing(data):
    text=data[data.index('| Design Timing Summary'):]
    names=['WNS_ns','TNS_ns','setup_failing','setup_total','WHS_ns','THS_ns','hold_failing','hold_total','WPWS_ns','TPWS_ns','pulse_failing','pulse_total']
    for line in text.splitlines():
        vals=line.split()
        if len(vals)==12 and all(re.fullmatch(r'-?\d+(?:\.\d+)?',x) for x in vals):
            return {k:float(v) if k.endswith('_ns') else int(v) for k,v in zip(names,vals)}
    raise ValueError('No twelve-column native design timing summary')

def route_status(data):
    counts={}
    for line in data.splitlines():
        m=re.match(r'^\s*(.*?)\s*:\s*([0-9,]+)\s*:',line)
        if m:counts[re.sub(r'[.#\s]+',' ',m[1]).strip().lower()]=int(m[2].replace(',',''))
    def one(phrase):
        vals=[v for k,v in counts.items() if re.search(r'\b'+re.escape(phrase)+r'\b',k)]
        assert len(vals)==1,(phrase,counts)
        return vals[0]
    routable,fully,errors=one('routable nets'),one('fully routed nets'),one('routing errors')
    return dict(reported_net_counts=counts,routable_nets=routable,fully_routed_nets=fully,routing_errors=errors,
                all_routable_nets_routed=routable==fully,zero_routing_errors=errors==0)

def timing_checks(data):
    found={}
    for key,value in re.findall(r'checking (\w+) \((\d+)\)',data):found.setdefault(key,set()).add(int(value))
    assert found and all(len(values)==1 for values in found.values()),found
    result={key:next(iter(values)) for key,values in found.items()}
    for key in ('no_clock','unconstrained_internal_endpoints','loops','latch_loops','multiple_clock'):assert key in result,key
    return result

def worst_path(data):
    answer={}
    patterns=dict(slack_ns=r'^Slack \([^\n]+\)\s*:\s*(-?\d+\.\d+)ns',source=r'^\s*Source:\s*(\S+)',destination=r'^\s*Destination:\s*(\S+)',data_path_delay_ns=r'^\s*Data Path Delay:\s*(\d+\.\d+)ns',logic_levels=r'^\s*Logic Levels:\s*(\d+)')
    for key,pattern in patterns.items():
        m=re.search(pattern,data,re.M);assert m,(key,pattern)
        answer[key]=float(m[1]) if key.endswith('_ns') else int(m[1]) if key=='logic_levels' else m[1]
    return answer

def parse_reports(folder):
    summary=timing((folder/'route-timing-summary.rpt').read_text())
    checks=timing_checks((folder/'route-check-timing.rpt').read_text())
    routing=route_status((folder/'route-status.rpt').read_text())
    clocks=(folder/'route-clocks.rpt').read_text()
    clock_rows=re.findall(r'^component_clk\s+([\d.]+)\s+\{([\d.]+)\s+([\d.]+)\}',clocks,re.M)
    clock_ok=len(clock_rows)==1 and [float(x) for x in clock_rows[0]]==[10.0,0.0,5.0]
    passed=(clock_ok and min(summary['WNS_ns'],summary['WHS_ns'],summary['WPWS_ns'])>=0
            and all(summary[x]==0 for x in ('setup_failing','hold_failing','pulse_failing'))
            and all(checks[x]==0 for x in ('no_clock','unconstrained_internal_endpoints','loops','latch_loops','multiple_clock'))
            and routing['all_routable_nets_routed'] and routing['zero_routing_errors'])
    return dict(timing=summary,check_timing=checks,routing=routing,clock_10ns=clock_ok,
                worst_setup_path=worst_path((folder/'route-setup-paths.rpt').read_text()),component_internal_100MHz_pass=passed)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--build',type=Path,required=True);ap.add_argument('--license-file',type=Path,required=True);ap.add_argument('--dispatch',type=Path,required=True);args=ap.parse_args()
    build=args.build.resolve();build.relative_to(BUILD_ROOT);inputs=json.loads((build/'inputs.json').read_text())
    assert inputs['trial_id'].startswith('v110-count-domain-') and inputs['start_mode']=='rtl'
    assert inputs['synth_directive']=='default' and inputs['synth_directive_cli']=='omitted'
    policy=ROOT/inputs['policy_path'];assert sha(policy)==inputs['policy_sha256']
    for pin in (inputs['source_method_control'],inputs['negative_parent_gate']):assert sha(ROOT/pin['path'])==pin['sha256']
    selected=json.loads((ROOT/inputs['source_method_control']['path']).read_text())
    changed=[a for a in inputs['source_sha256'] if inputs['source_sha256'][a]!=selected['source_sha256'][a]]
    assert set(changed)==set(inputs['source_delta_aliases']) and len(changed)==2
    assert selected['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and selected['result']['timing']['WNS_ns']<0
    active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith('gamebub-v')for n in active)<2
    timeout=inputs['timeout_seconds'];assert timeout==3600 and args.license_file.is_file()
    dispatch=json.loads(args.dispatch.read_text());assert dispatch['status']=='DISPATCHED_TO_RUNNER' and dispatch['prepared_inputs_sha256']==sha(build/'inputs.json')
    parent=Path(inputs['parent_synthesis_checkpoint']['external_path']);parent_before=sha(parent)
    assert parent_before==inputs['parent_synthesis_checkpoint']['sha256']
    assert inputs['clock_period_ns']==10.0 and inputs['part']=='xc7a100tcsg324-1' and inputs['closure_files']==18
    source_before={n:sha(build/'snapshot'/n) for n in inputs['source_sha256']};assert source_before==inputs['source_sha256']
    recipe_before={n:sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')};assert recipe_before==inputs['recipe_sha256']
    before=memory();assert before['MemAvailable_bytes']>=8*1024**3 and before['PSI_full_avg10']<1,before
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/stamp;out.mkdir(parents=True);name='gamebub-v110-count-domain-native-'+stamp.lower();mapped=Path('/build')/build.name
    shutil.copyfile(build/'inputs.json',out/'inputs.json');shutil.copytree(build/'snapshot',out/'source-snapshot');(out/'recipe-snapshot').mkdir()
    for n in recipe_before:shutil.copyfile(build/n,out/'recipe-snapshot'/n)
    shutil.copyfile(Path(__file__),out/'run_native.py')
    shutil.copyfile(args.dispatch,out/'predispatch.json')
    image=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','acorn-nexys4-ddr:2026.1'],text=True).strip();assert image.startswith('sha256:')
    cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0',
         '--mount',f'type=bind,src={TOOLS},dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={build},dst={mapped}',
         '--mount',f'type=bind,src={build/"snapshot"},dst={mapped/"snapshot"},readonly','--mount',f'type=bind,src={parent},dst=/parent/synth.dcp,readonly',
         '--mount',f'type=bind,src={args.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly',
         '-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w',str(mapped),image,
         'timeout','--signal=TERM','--kill-after=15s',str(timeout)+'s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source',str(mapped/'run.tcl'),'-tclargs',str(mapped)]
    receipt=dict(schema='v110-count-domain-default-native-trial-v1',synth_directive='default',synth_directive_cli='omitted',source_method_control=inputs['source_method_control'],source_method_control_evidence=inputs['source_method_control_evidence'],negative_parent_gate=inputs['negative_parent_gate'],observability_contract=inputs['observability_contract'],source_delta_aliases=inputs['source_delta_aliases'],qualification_helper=inputs['qualification_helper'],policy_path=inputs['policy_path'],policy_sha256=inputs['policy_sha256'],status='RUNNING',trial_id=inputs['trial_id'],start_mode=inputs['start_mode'],clean_repeat_of=inputs['clean_repeat_of'],directives=inputs['directives'],command=cmd,image_id=image,
        build_external=str(build),container=name,part=inputs['part'],top=inputs['top'],clock_period_ns=10.0,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,memory_swap_limit_bytes=8*1024**3,timeout_seconds=timeout,
        parent_synthesis_checkpoint=inputs['parent_synthesis_checkpoint'],parent_checkpoint_sha256_before=parent_before,parent_clock_loaded_before_synthesis=inputs['source_contract']['parent_clock_loaded_before_synthesis'],
        synthesis_executed=inputs['start_mode']=='rtl',clock_inherited_from_parent_checkpoint=inputs['start_mode']=='checkpoint',clock_loaded_before_synthesis_in_this_run=True if inputs['start_mode']=='rtl' else None,
        native_contract_path=inputs['native_contract_path'],native_contract_sha256=inputs['native_contract_sha256'],source_contract=inputs['source_contract'],source_sha256=inputs['source_sha256'],source_origins=inputs['source_origins'],source_snapshot_readonly_mount=True,
        source_manifest_sha256=sha(build/'inputs.json'),recipe_sha256=recipe_before,runner_sha256=sha(Path(__file__)),predispatch=dict(path=str(args.dispatch.relative_to(ROOT)),sha256=sha(args.dispatch),record=dispatch),resource_before=before,
        existing_legitimate_license_readonly=True,license_contents_logged=False,hostid_or_MAC_changed=False,tools_readonly=True,hardware_contact=False,bitstream_generated=False,board_IO_timing_qualified=False,full_custom_top_qualified=False,hardware_30fps=False,complete_validated_decode_under10ms=False)
    write(out/'receipt.json',receipt);print('V110_NATIVE_BUILD_STARTED',str(out.relative_to(ROOT)),inputs['trial_id'],inputs['start_mode'],flush=True)
    samples=[];started=time.monotonic();last=-30;pressure_count=0;stop=None
    with (out/'vivado.log').open('w') as log,(out/'memory.jsonl').open('w') as telemetry:
        process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        while process.poll() is None:
            elapsed=time.monotonic()-started
            if elapsed-last>=30:
                sample=dict(elapsed_seconds=elapsed,**memory());stats=subprocess.run(['docker','exec',name,'cat','/sys/fs/cgroup/memory.current'],capture_output=True,text=True,timeout=8)
                sample['container_memory_bytes']=int(stats.stdout.strip()) if stats.returncode==0 and stats.stdout.strip().isdigit() else None;samples.append(sample);telemetry.write(json.dumps(sample)+'\n');telemetry.flush();last=elapsed
                pressure_count=pressure_count+1 if sample['PSI_full_avg10']>=5 else 0
                if sample['MemAvailable_bytes']<4*1024**3:stop='HOST_AVAILABLE_BELOW_4GIB'
                if pressure_count>=2:stop='SUSTAINED_HIGH_MEMORY_PRESSURE'
            if elapsed>timeout+45:stop='HOST_WALL_TIMEOUT'
            if stop:subprocess.run(['docker','stop','--time','10',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=20);break
            time.sleep(1)
        try:code=process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker','kill',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
            code=process.wait(timeout=15)
    log_text=(out/'vivado.log').read_text(errors='replace');results=build/'results';artifacts={}
    for p in sorted(results.glob('*')):
        if p.is_file():
            artifacts[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size,external_path=str(p))
            if p.suffix in ('.rpt','.txt','.json','.xdc','.tsv','.log') and p.stat().st_size<95*1024**2:
                target=out/'reports'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
    for p in sorted(build.glob('hs_err_pid*.log')):
        target=out/'crash'/p.name;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target)
    directive_match=re.search(r'Directive used for synth_design is:\s*(\w+)',log_text)
    receipt['observed_synth_directive_log']=directive_match[1] if directive_match else None
    receipt.update(observed_exit_code=code,wall_seconds=time.monotonic()-started,monitor_stop_reason=stop,memory_samples=samples,log_sha256=sha(out/'vivado.log'),artifacts=artifacts,
        parent_checkpoint_sha256_after=sha(parent),parent_checkpoint_unchanged=sha(parent)==parent_before,
        source_snapshot_unchanged=all(sha(build/'snapshot'/n)==h for n,h in source_before.items()),recipe_unchanged=all(sha(build/n)==h for n,h in recipe_before.items()),
        routing_checkpoint_written=(results/'route.dcp').is_file(),synthesis_checkpoint_generated_in_this_run=(results/'synth.dcp').is_file(),component_route_finished=code==0 and 'V110_COMPONENT_ROUTE_FINISHED' in log_text)
    receipt['status']='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' if receipt['component_route_finished'] else 'STOPPED_RESOURCE_OR_TIME_GATE' if stop else 'TOOL_OR_BUILD_FAILED'
    if receipt['component_route_finished']:
        try:receipt['result']=parse_reports(results)
        except Exception as exc:receipt.update(status='ROUTE_FINISHED_REPORT_PARSE_FAILED',report_parse_error=repr(exc))
    rules={}
    if (results/'route-methodology.rpt').is_file():
        for line in (results/'route-methodology.rpt').read_text().splitlines():
            m=re.match(r'^\|\s*(SYNTH-6|TIMING-16|TIMING-18|ULMTCS-1)\s*\|\s*(.*?)\s*\|.*?\|\s*(\d+)\s*\|$',line)
            if m:rules[m[1]]=dict(severity=m[2],listed_checks=int(m[3]))
    report=f"# V110 methodology resolution report\n\nTrial `{inputs['trial_id']}`, mode `{inputs['start_mode']}`; part `{inputs['part']}`.\n"
    report+=f"Synthesis: `default` by omission of -directive; no retiming added. Same-method Default source control: `{inputs['source_method_control']}`.\n\n"
    report+=f"Directives: `{inputs['directives']}`. Status: `{receipt['status']}`.\n\n"
    report+="## Clock and constraints\n\nThe component target remains 100 MHz / 10.000 ns. No clock, I/O, false/multicycle or waiver change was made.\n\n"
    report+="| Aspect | Constraint | Period | Waveform | Clock Definition Object |\n| --- | --- | --- | --- | --- |\n"
    constraint='create_clock -name component_clk -period 10.000 [get_ports clk]'
    for label in ('Before','After'):
        report+=f"| {label} | `{constraint}` | 10.000 ns | {{0.000 5.000}} | component_clk |\n"
    report+="\nSource: `component.xdc` in this build; actual before/after effective constraints and native clock reports are retained in `results/`. No constraint diff is applicable because constraints were not modified.\n\n"
    report+="## Actual native findings\n\n| Rule | Severity | Listed checks | Resolution/scope |\n| --- | --- | ---: | --- |\n"
    actions={'TIMING-16':'Operational control/architecture; setup must pass the fixed clock. No waiver.',
             'TIMING-18':'OOC boundary lacks board I/O contracts. Full-parent constraints remain required; no invented delays.',
             'SYNTH-6':'RAM output-register finding: inspect the actual endpoint/latency contract; no blind output-register insertion.',
             'ULMTCS-1':'Control-set locality/ownership work remains; do not remove functional resets.'}
    for rule,entry in sorted(rules.items()):report+=f"|{rule}|{entry['severity']}|{entry['listed_checks']}|{actions[rule]}|\n"
    report+="\nListed methodology entries are not the count of failing setup endpoints; the native timing summary below is authoritative. Raw methodology/DRC, I/O, CDC, high-fanout, control-set and local-predicate mapping reports remain available.\n\n"
    if 'result' in receipt:
        report+='Measured timing: '+json.dumps(receipt['result']['timing'],sort_keys=True)+'\n\nInternal component 100 MHz: '+str(receipt['result']['component_internal_100MHz_pass'])+'.\n'
        report+=('Setup remains unresolved; positive hold/pulse alone is insufficient.\n' if receipt['result']['timing']['setup_failing'] or receipt['result']['timing']['WNS_ns']<0 else 'This route passes component timing; a fresh RTL validation repeat and complete-parent qualification remain separate gates.\n')
    report+="\n## Waivers and remaining actions\n\nNo waivers were created. Board clocks/I/O/CDC, finite memory/display/reference/HUD/hash service, calibrated validated publication, hardware 30 fps and complete validated decode below 10 ms remain open. This OOC run does not generate a board bitstream or prove hardware performance.\n"
    (build/'METHODOLOGY_RESOLUTION_REPORT.md').write_text(report);(out/'METHODOLOGY_RESOLUTION_REPORT.md').write_text(report)
    receipt['retained_artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='receipt.json'};write(out/'receipt.json',receipt)
    print('V110_NATIVE_BUILD_FINISHED',str(out.relative_to(ROOT)),receipt['status'],code,receipt.get('result',{}).get('timing'),flush=True)
    if code!=0 or receipt['status']!='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':raise SystemExit(code if 0<code<256 else 1)

if __name__=='__main__':main()
