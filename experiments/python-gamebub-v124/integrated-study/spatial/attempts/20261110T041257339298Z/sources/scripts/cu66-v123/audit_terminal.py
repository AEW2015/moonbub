#!/usr/bin/env python3
"""Independent read-only terminal native audit; no vendor tools or root parser.

Python 3.10+ verifies hashes and native text/JSON reports. Optional EDIF enrichment
uses Python 3.14's compression.zstd or the optional zstandard package; absence is
reported explicitly and does not prevent core evidence verification.
"""
import argparse
import collections
import datetime
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'experiments/python-gamebub-v123/audit/native-independent.json'
B_HANDOFF = ROOT/'experiments/python-gamebub-v120/handoff.json'
B_RECEIPT = ROOT/'experiments/python-gamebub-v120/repair-study/native/20261109T205145239583Z/receipt.json'
B_OBSERVATION = ROOT/'experiments/python-gamebub-v121/request-inspection/baseline-b125-20261109T233158499545Z/receipt.json'
QUEUE = 'fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
CANDIDATE = 'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'
SCRATCH = 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
ADMISSION = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
V121_INDEX = ROOT/'experiments/python-gamebub-v121/integration/results.json'
V121_NATIVE = ROOT/'experiments/python-gamebub-v121/native/20261109T234502249779Z/receipt.json'
V122_INDEX = ROOT/'experiments/python-gamebub-v122/integration/results.json'
V122_NATIVE = ROOT/'experiments/python-gamebub-v122/native/20261110T011206751721Z/receipt.json'
PART = 'xc7a100tcsg324-1'
IMAGE = 'sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
EXPECTED_SYNTH = 'synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pin(path):
    path = Path(path)
    try:
        name = str(path.resolve().relative_to(ROOT))
    except ValueError:
        name = str(path.resolve())
    return dict(path=name, sha256=sha(path))


def timing(text):
    # Twelve columns under the *design* timing summary, not a clock-group row.
    rows = text.splitlines()
    index = next(i for i, line in enumerate(rows) if line.strip().startswith('WNS(ns)') and 'TNS Failing Endpoints' in line)
    values = next(line.split() for line in rows[index+1:] if re.fullmatch(r'\s*-?\d+\.\d+\s+-?\d+\.\d+\s+\d+\s+\d+\s+-?\d+\.\d+\s+-?\d+\.\d+\s+\d+\s+\d+\s+-?\d+\.\d+\s+-?\d+\.\d+\s+\d+\s+\d+\s*', line))
    names = ['WNS_ns','TNS_ns','setup_failing','setup_total','WHS_ns','THS_ns','hold_failing','hold_total','WPWS_ns','TPWS_ns','pulse_failing','pulse_total']
    integers = {2,3,6,7,10,11}
    return {name:(int(values[i]) if i in integers else float(values[i])) for i,name in enumerate(names)}


def check_timing(text):
    result = {}
    for name, count in re.findall(r'^\d+\. checking ([a-z_]+) \((\d+)\)', text, re.M):
        if name in result:
            assert result[name] == int(count), 'Repeated check_timing sections disagree'
        result[name] = int(count)
    assert len(result) == 12
    return result


def routing(text):
    result = {name.strip():int(count) for name,count in re.findall(r'# (of [^.\n]+)\.+\s*:\s*(\d+)\s*:', text)}
    return dict(reported_net_counts=result, routing_errors=result['of nets with routing errors'],
                routable_nets=result['of routable nets'], fully_routed_nets=result['of fully routed nets'],
                zero_routing_errors=result['of nets with routing errors']==0,
                all_routable_nets_routed=result['of routable nets']==result['of fully routed nets'])


def worst_setup(text):
    def first(pattern):
        return re.search(pattern, text, re.M).group(1)
    return dict(slack_ns=float(first(r'^Slack \([^)]*\)\s*:\s*(-?\d+\.\d+)ns')),
                source=first(r'^  Source:\s*(\S+)'),
                destination=first(r'^  Destination:\s*(\S+)'),
                data_path_delay_ns=float(first(r'^  Data Path Delay:\s*(\d+\.\d+)ns')),
                logic_levels=int(first(r'^  Logic Levels:\s*(\d+)')))


def methodology(directory):
    report = (directory/'route-methodology.rpt').read_text()
    summary = {rule:dict(severity=severity.strip(), count=int(count), description=description.strip())
               for rule,severity,description,count in re.findall(r'^\|\s*([A-Z]+-\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(\d+)\s*\|', report, re.M)}
    assert summary
    actual = load(directory/'route-methodology.json')
    table = actual['tables']['Report Summary']
    converted = {}
    for values in table['data']:
        row = dict(zip(table['headers'], values))
        rule, count = row['rule'], int(row['count'])
        assert summary[rule]['severity'] == row['severity'] and summary[rule]['count'] == count
        details = row['details']
        assert len(details) == count
        converted[rule] = dict(summary[rule], details=details)
    assert set(summary) == set(converted)
    assert int(actual['report_header']['Checks found']) == sum(row['count'] for row in summary.values())
    # report_timing_summary precedes the fresh report_methodology in this fixed
    # recipe; its cached methodology table is observed separately, never signoff.
    cached = {rule:int(count) for rule,count in re.findall(r'^([A-Z]+-\d+)\s+\S+\s+.*?\s+(\d+)\s*$', (directory/'route-timing-summary.rpt').read_text(), re.M)}
    return dict(fresh=converted, total=sum(row['count'] for row in converted.values()),
                cached_timing_summary_counts=cached, report=pin(directory/'route-methodology.rpt'),
                json=pin(directory/'route-methodology.json'))


def mapping(checkpoint):
    """Bounded decompression of the actual EDIF; never opens a vendor session."""
    with zipfile.ZipFile(checkpoint) as archive:
        names = [name for name in archive.namelist() if name.endswith('.edf')]
        assert len(names) == 1
        raw = archive.read(names[0])
    if raw.startswith(b'\x28\xb5\x2f\xfd'):
        try:
            from compression import zstd
            raw = zstd.decompress(raw)
            backend = 'Python compression.zstd'
        except ImportError:
            try:
                import zstandard
                import io
                with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)) as reader:
                    raw = reader.read(256*1024*1024+1)
                backend = 'optional zstandard'
            except ImportError:
                return dict(available=False, reason='Zstd EDIF requires Python3.14 compression.zstd or optional zstandard; checkpoint hash/report checks remain available on Python3.10+.')
    else:
        backend = 'plain EDIF'
    assert len(raw) <= 256*1024*1024, 'Bounded EDIF inventory limit exceeded'
    text = raw.decode('utf-8')
    cells = list(re.finditer(r'^   \(cell (\S+) \(celltype GENERIC\)', text, re.M))
    selected = [(i,match) for i,match in enumerate(cells) if match.group(1) == 'byte_refill_queue_v91i2b']
    assert len(selected) == 1
    index, match = selected[0]
    queue = text[match.start():cells[index+1].start() if index+1<len(cells) else len(text)]
    registers = {}
    for name in ('prepared_req_addr','offset','issued'):
        rows = re.findall(r'\(instance \(rename '+name+r'_reg[^\n]*\(cellref (FD\w+)\b', queue)
        registers[name] = dict(count=len(rows), primitives=dict(collections.Counter(rows)))
    def registers_in(cell_name):
        matches=[(i,m) for i,m in enumerate(cells) if m.group(1)==cell_name]
        assert len(matches)==1
        index,match=matches[0]
        block=text[match.start():cells[index+1].start() if index+1<len(cells) else len(text)]
        counts=collections.Counter()
        for renamed,plain,primitive in re.findall(r'\(instance (?:\(rename \S+ "([^"]+)"\)|(\S+)) [^\n]*?\(cellref (FD\w+)\b',block):
            name=renamed or plain
            if '_reg' in name:counts[name.split('_reg',1)[0]]+=1
        return dict(counts)
    admission_registers=registers_in('cs88_admission_v91i2a')
    scratch_registers=registers_in('packed_scratch_v91g2')
    return dict(available=True, backend=backend, decoded_EDIF_bytes=len(raw),
                decoded_EDIF_sha256=hashlib.sha256(raw).hexdigest(), member=names[0],
                queue_cell='byte_refill_queue_v91i2b', queue_registers=registers,
                admission_cell='cs88_admission_v91i2a', admission_FF_register_counts=admission_registers,
                scratch_cell='packed_scratch_v91g2', scratch_FF_register_counts=scratch_registers,
                global_CARRY4_cellrefs=len(re.findall(r'\(cellref CARRY4\b', text)))


class Audit:
    def __init__(self):
        self.checks = []

    def check(self, condition, name, detail=None):
        self.checks.append(dict(name=name, passed=bool(condition), detail=detail))

    def hashes(self, entries, prefix, root=ROOT):
        for name, expected in entries.items():
            path = root/name
            self.check(path.is_file() and sha(path)==expected, prefix+': '+name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    receipt_path = args.receipt.resolve()
    receipt = load(receipt_path)
    if receipt['status'] in ('RUNNING','PREPARED_NOT_RUN'):
        raise SystemExit('NOT_TERMINAL: no audit executed or output written')
    audit = Audit()
    result = dict(schema='v123-independent-terminal-native-audit-v1',
                  receipt=pin(receipt_path), auditor_script=pin(Path(__file__)),
                  generated_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  native_status=receipt['status'], checks=audit.checks, errors=[],
                  heavy_job_launched=False, root_parser_imported=False,
                  integrity_status='FAIL', design_timing_pass=None,
                  full_parent_routed_clock_qualified=False, hardware_claim=False)
    try:
        out, reports = receipt_path.parent, receipt_path.parent/'reports'
        build = Path(receipt['build_external'])
        base, old = load(B_HANDOFF), load(B_RECEIPT)
        audit.check(sha(B_RECEIPT)==base['failed_B_125_MHz_receipt']['sha256'], 'Frozen B125 receipt identity')
        audit.check(sha(B_HANDOFF)=='1e1bd0f197b8b44e7113f271f2c68092e6800778bbfb3a5027d05f72f9357459', 'Qualified Source B100 handoff identity')
        audit.check(base['qualified_internal_component_clock_MHz']==100, 'Qualified hardware-integration control remains Source B100')
        qualified_B100=[]
        for label in ('initial_receipt','repeat_receipt'):
            meta=base[label];bp=ROOT/meta['path'];b100=load(bp)
            audit.check(sha(bp)==meta['sha256'], 'Qualified Source B100 receipt identity: '+label)
            audit.hashes(b100['retained_artifact_sha256'], 'Qualified Source B100 artifact '+label, bp.parent)
            bt=timing((bp.parent/'reports/route-timing-summary.rpt').read_text())
            bc=check_timing((bp.parent/'reports/route-check-timing.rpt').read_text())
            br=routing((bp.parent/'reports/route-status.rpt').read_text())
            coverage=all(bc[k]==0 for k in bc if k not in ('no_input_delay','no_output_delay'))
            passed=all(bt[k]>=0 for k in ('WNS_ns','WHS_ns','WPWS_ns')) and all(bt[k]==0 for k in ('TNS_ns','THS_ns','TPWS_ns','setup_failing','hold_failing','pulse_failing')) and coverage and br['zero_routing_errors'] and br['all_routable_nets_routed']
            audit.check(bt==b100['result']['timing'] and passed and b100['result']['component_internal_target_pass'] is True and b100['clock_period_ns']==10.0, 'Independent qualified Source B100 signoff metrics: '+label)
            audit.check(b100['source_contract']['source_origins']==base['source_origins'], 'Qualified Source B100 exact source composition: '+label)
            qualified_B100.append(dict(kind=label,receipt=pin(bp),actual_timing=bt,internal_coverage_pass=coverage,routing=br))
        result['qualified_hardware_integration_control_B100']=qualified_B100
        result['baseline_B125'] = pin(B_RECEIPT)
        v121_native=load(V121_NATIVE)
        audit.check(sha(V121_NATIVE)=='b034c1e3f94a8b751d601da7f431a682ce3cd50a9521494211d04a0706a58379', 'Frozen V121125 QoR receipt identity')
        audit.hashes(v121_native['retained_artifact_sha256'], 'Frozen V121125 artifact', V121_NATIVE.parent)
        v121_timing=timing((V121_NATIVE.parent/'reports/route-timing-summary.rpt').read_text())
        audit.check(v121_timing==v121_native['result']['timing'] and v121_timing['WNS_ns']==-1.347 and v121_timing['TNS_ns']==-3248.192 and v121_timing['setup_failing']==9407, 'Independent current-composition V121125 QoR baseline')
        result['baseline_V121125']=dict(receipt=pin(V121_NATIVE), actual_timing=v121_timing, role='Current composition QoR comparison; failed125MHz timing, not qualified hardware control')
        v122_native=load(V122_NATIVE)
        audit.check(sha(V122_NATIVE)=='4e2385a1b57dd2f9e3a13667052fde8e8969d73580d384926f328bcfbb3364ae', 'Frozen V122125 QoR receipt identity')
        audit.hashes(v122_native['retained_artifact_sha256'], 'Frozen V122125 artifact', V122_NATIVE.parent)
        v122_timing=timing((V122_NATIVE.parent/'reports/route-timing-summary.rpt').read_text())
        audit.check(v122_timing==v122_native['result']['timing'] and v122_timing['WNS_ns']==-1.949 and v122_timing['TNS_ns']==-4597.575 and v122_timing['setup_failing']==11866, 'Independent current-composition V122125 QoR baseline')
        result['baseline_V122125']=dict(receipt=pin(V122_NATIVE), actual_timing=v122_timing, role='Current composition QoR comparison; failed125MHz timing, not qualified hardware control')
        audit.hashes(old['retained_artifact_sha256'], 'Frozen B125 artifact', B_RECEIPT.parent)
        for name, meta in old.get('external_artifacts',old.get('artifacts',{})).items():
            path=Path(meta['external_path'])
            audit.check(path.name==name and path.stat().st_size==meta['bytes'] and sha(path)==meta['sha256'], 'Frozen B125 external artifact/DCP: '+name)
        origins = receipt['source_contract']['source_origins']
        audit.check(len(origins)==18 and set(origins)==set(base['source_origins']), 'Exact eighteen selected aliases')
        v122 = load(V122_INDEX)
        audit.check(sha(V122_INDEX)=='c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4', 'Frozen V122 functional comparison identity')
        changed = [alias for alias in origins if origins[alias] != v122['source_origins'][alias]]
        audit.check(changed==[SCRATCH], 'Only scratch alias changes from V122', changed)
        audit.check(origins[SCRATCH] == dict(path=CANDIDATE, sha256=sha(ROOT/CANDIDATE)), 'Selected frozen scratch rank candidate')
        audit.check(origins[QUEUE]==v122['source_origins'][QUEUE] and origins[QUEUE]['sha256']=='69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48', 'Qualified V121 queue remains unchanged')
        audit.check(origins[ADMISSION]==v122['source_origins'][ADMISSION] and origins[ADMISSION]['sha256']=='54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf', 'Qualified V122 admission bounds remain unchanged')
        for alias, origin in origins.items():
            for path in (ROOT/origin['path'], out/'source-snapshot'/alias, build/'snapshot'/alias):
                audit.check(sha(path)==origin['sha256'], 'Selected source/origin/snapshot: '+str(path))
        actual_aliases = {str(path.relative_to(out/'source-snapshot')) for path in (out/'source-snapshot').rglob('*') if path.is_file()}
        audit.check(actual_aliases==set(origins), 'Retained snapshot contains exactly selected eighteen files')
        audit.hashes({meta['path']:meta['sha256'] for meta in base['source_origins'].values()}, 'Source B remains unchanged')
        audit.hashes(receipt['source_contract']['proof_pins'], 'Functional proof pin')
        audit.hashes(receipt['tooling_sha256'], 'Tooling identity')
        native_pin = receipt['tooling_sha256']['scripts/cu66-v123/native.py']
        audit.check(sha(out/'native.py')==native_pin, 'Actual native dispatcher snapshot')
        for key in ('preflight','audit'):
            meta = receipt[key]
            audit.check(sha(ROOT/meta['path'])==meta['sha256']==sha(out/(key+'.json')), 'Preflight/audit original and retained snapshot: '+key)
        preflight, launch_audit = load(out/'preflight.json'), load(out/'audit.json')
        card = load(build/'inputs.json')
        audit.check(preflight==dict(card,inputs_sha256=sha(build/'inputs.json')), 'Preflight equals prepared card and input hash')
        audit.check(all(receipt[key]==value for key,value in card.items() if key!='status'), 'Terminal declaration preserves every prepared card field')
        audit.check(launch_audit['status']=='PASS_V123_NATIVE_PREFLIGHT_AUDIT' and launch_audit['preflight_sha256']==receipt['preflight']['sha256'] and launch_audit['native_source_sha256']==native_pin and launch_audit['independent_source_recipe_resource_checks'] is True, 'Independent preflight audit binding')
        audit.check(receipt['part']==PART and receipt['top']=='cs88_pipeline_v91k' and receipt['clock_period_ns']==8.0 and receipt['image_id']==IMAGE, 'Declared part/top/8ns/tool image')
        for name, digest in receipt['recipe_sha256'].items():
            audit.check(sha(build/name)==sha(out/'recipe-snapshot'/name)==digest, 'Executed and retained recipe: '+name)
        for name in ('run.tcl','report.tcl','component.xdc'):
            audit.check(receipt['recipe_sha256'][name]==old['recipe_sha256'][name], 'Exact B125 core recipe: '+name)
        tcl=(out/'recipe-snapshot/run.tcl').read_text()
        audit.check(tcl.index('read_xdc $constraint_file')<tcl.index('synth_design -top'), 'Clock registered before synthesis in executed Tcl')
        audit.check('open_checkpoint' not in tcl and 'read_checkpoint' not in tcl and receipt['start_mode']=='rtl' and receipt['checkpoint_read'] is False, 'Fresh RTL synthesis; no checkpoint implementation reuse')
        inputs=(out/'recipe-snapshot/inputs.tcl').read_text()
        audit.check('set part '+PART+'\n' in inputs and 'set expected_period_ns 8.0\n' in inputs and 'set start_mode {rtl}\n' in inputs, 'Actual inputs declare part/8ns/fresh RTL')
        order=receipt['source_contract']['source_order']
        actual_read_order=re.search(r'^set rtl_sources \[list (.*)\]$',inputs,re.M)
        mapped='/build/'+build.name
        audit.check(actual_read_order is not None and re.findall(r'\{([^}]+)\}',actual_read_order.group(1))==[mapped+'/snapshot/'+alias for alias in order['rtl_read_order_aliases']], 'Exact selected seventeen RTL compile order')
        audit.check(order==base['source_order'], 'Source/include order equals Source B')
        expected_mount='type=bind,src='+str(build/'snapshot')+',dst='+mapped+'/snapshot,readonly'
        command=receipt['command']
        audit.check(expected_mount in command and IMAGE in command and command[command.index('--memory')+1]=='8g' and command[command.index('--memory-swap')+1]=='8g' and command[command.index('--cpus')+1]=='2', 'Executed source-readonly mount, image and resource caps')
        audit.check(receipt['max_threads']==2 and receipt['memory_limit_bytes']==8*1024**3 and receipt['memory_swap_limit_bytes']==8*1024**3, 'Recorded bounded resources')
        audit.hashes(receipt['retained_artifact_sha256'], 'Retained native artifact', out)
        actual_retained={str(path.relative_to(out)) for path in out.rglob('*') if path.is_file() and path.name!='receipt.json'}
        audit.check(actual_retained==set(receipt['retained_artifact_sha256']), 'All retained regular artifacts included in hash inventory')
        external=receipt['external_artifacts']
        for name, meta in external.items():
            path=Path(meta['external_path'])
            audit.check(path.parent==build/'results' and path.name==name and path.stat().st_size==meta['bytes'] and sha(path)==meta['sha256'], 'External native artifact/DCP: '+name)
            if (reports/name).is_file():
                audit.check(sha(reports/name)==meta['sha256'], 'Retained report equals actual vendor output: '+name)
        audit.check({'synth.dcp','route.dcp'}.issubset(external), 'Both actual fresh synth/routed checkpoints retained externally')
        log=(out/'vivado.log').read_text(errors='replace')
        synth=re.findall(r'^Command:\s*(synth_design[^\n]*)',log,re.M)
        audit.check(synth==[EXPECTED_SYNTH]==receipt['synthesis_command_lines'], 'Actual exact Default synthesis command', synth)
        audit.check(receipt['observed_default_command_exact']==(synth==[EXPECTED_SYNTH]) and receipt['synthesis_executed']==bool(synth), 'Recorded synthesis flags match actual transcript')
        audit.check(receipt['source_snapshot_unchanged'] is True and receipt['recipe_unchanged'] is True and receipt['clock_loaded_before_synthesis_in_this_run'] is True, 'Recorded source/recipe/clock ordering flags match verified evidence')
        audit.check('Vivado v2026.1' in log and '6511674' in log, 'Actual vendor tool version/build transcript')
        audit.check('Parsing XDC File ['+mapped+'/component.xdc]' in log, 'Synthesis transcript parses the declared component constraint')
        audit.check(not re.search(r'^Command:\s*(?:open_checkpoint|read_checkpoint)\b',log,re.M), 'Transcript contains no checkpoint-based implementation command')
        finished=receipt['observed_exit_code']==0 and 'V120_COMPONENT_ROUTE_FINISHED' in log
        audit.check(finished==receipt['component_route_finished'], 'Terminal completion/exit/marker consistency')
        audit.check(sha(out/'vivado.log')==receipt['log_sha256'], 'Whole vendor transcript identity')
        result['execution']=dict(observed_exit_code=receipt['observed_exit_code'], monitor_stop_reason=receipt['monitor_stop_reason'], route_finished=finished, synthesis_command=synth, clock_before_synthesis_Tcl=True)
        if finished:
            actual_timing=timing((reports/'route-timing-summary.rpt').read_text())
            checks=check_timing((reports/'route-check-timing.rpt').read_text())
            routes=routing((reports/'route-status.rpt').read_text())
            raw_result=receipt.get('result',{})
            worst=worst_setup((reports/'route-setup-paths.rpt').read_text())
            audit.check(raw_result.get('target_period_ns')==8.0 and raw_result.get('target_frequency_MHz')==125.0 and raw_result.get('clock_target_matches') is True, 'Receipt target frequency/period agree with actual fixed clock')
            audit.check(actual_timing==raw_result.get('timing'), 'Independent twelve timing metrics equal receipt')
            audit.check(worst==raw_result.get('worst_setup_path'), 'Independent worst setup path equals receipt')
            audit.check(checks==raw_result.get('check_timing'), 'Independent twelve clock/coverage checks equal receipt')
            audit.check(routes==raw_result.get('routing'), 'Independent route net/error counts equal receipt')
            settings=dict(line.split('\t',1) for line in (reports/'settings.tsv').read_text().splitlines()[1:])
            audit.check(settings['part']==PART and settings['clock']=='component_clk' and float(settings['period_ns'])==8 and settings['tool']=='2026.1' and '6511674' in settings['tool_full'], 'Actual routed part/clock/tool settings')
            audit.check(all(settings[key]==value for key,value in dict(start_mode='rtl',max_threads='2',synth_directive='default',synth_directive_cli='omitted',opt_directive='Default',place_directive='ExtraNetDelay_high',physical_directive='NONE',route_directive='Default').items()), 'Actual fixed synthesis/implementation recipe settings')
            clocks=re.findall(r'^component_clk\s+(\d+\.\d+)\s+\{([^}]+)\}',(reports/'route-clocks.rpt').read_text(),re.M)
            audit.check(len(clocks)==1 and float(clocks[0][0])==8 and [float(value) for value in clocks[0][1].split()]==[0,4], 'Actual routed clock period/waveform')
            audit.check('No valid timing exceptions found.' in (reports/'route-exceptions.rpt').read_text(), 'No timing exceptions introduced')
            coverage=all(checks[key]==0 for key in checks if key not in ('no_input_delay','no_output_delay'))
            design_pass=all(actual_timing[key]>=0 for key in ('WNS_ns','WHS_ns','WPWS_ns')) and all(actual_timing[key]==0 for key in ('TNS_ns','THS_ns','TPWS_ns','setup_failing','hold_failing','pulse_failing')) and coverage and routes['zero_routing_errors'] and routes['all_routable_nets_routed']
            audit.check(design_pass==raw_result.get('component_internal_target_pass'), 'Independent timing-pass classification equals receipt')
            result.update(design_timing_pass=design_pass, actual_timing=actual_timing, actual_check_timing=checks, actual_routing=routes, internal_clock_coverage_pass=coverage,
                          actual_worst_setup_path=worst,
                          external_IO_limitation=dict(no_input_delay=checks['no_input_delay'],no_output_delay=checks['no_output_delay']), timing_delta_from_B125={key:actual_timing[key]-old['result']['timing'][key] for key in actual_timing},
                          timing_delta_from_V121125={key:actual_timing[key]-v121_timing[key] for key in actual_timing},
                          timing_delta_from_V122125={key:actual_timing[key]-v122_timing[key] for key in actual_timing})
            fresh, previous=methodology(reports), methodology(B_RECEIPT.parent/'reports')
            comparison={}
            for rule in sorted(set(fresh['fresh'])|set(previous['fresh'])):
                new=fresh['fresh'].get(rule,dict(count=0,details=[])); prior=previous['fresh'].get(rule,dict(count=0,details=[]))
                appeared=collections.Counter(new['details'])-collections.Counter(prior['details'])
                comparison[rule]=dict(candidate_count=new['count'],B125_count=prior['count'],delta=new['count']-prior['count'],new_detail_records=sum(appeared.values()),new_detail_examples=list(appeared)[:2])
            result['methodology']=dict(candidate=fresh,baseline_B125=previous,comparison=comparison,
                                      fresh_report_used=True,cached_timing_summary_not_used_for_signoff=True,
                                      warnings_waived=False,constraints_or_RTL_modified=False)
            v122_methodology=methodology(V122_NATIVE.parent/'reports')
            v122_comparison={}
            for rule in sorted(set(fresh['fresh'])|set(v122_methodology['fresh'])):
                new=fresh['fresh'].get(rule,dict(count=0,details=[])); prior=v122_methodology['fresh'].get(rule,dict(count=0,details=[]))
                appeared=collections.Counter(new['details'])-collections.Counter(prior['details'])
                v122_comparison[rule]=dict(candidate_count=new['count'],V122125_count=prior['count'],delta=new['count']-prior['count'],new_detail_records=sum(appeared.values()),new_detail_examples=list(appeared)[:2])
            result['methodology']['baseline_V122125']=v122_methodology
            result['methodology']['comparison_V122125']=v122_comparison
            mapped={}
            for stage in ('synth','route'):
                checkpoint=Path(external[stage+'.dcp']['external_path'])
                inventory=mapping(checkpoint)
                report_rows=(reports/(stage+'-carry-inventory.tsv')).read_text().splitlines()[1:]
                audit.check(all(row.split('\t')[1]=='CARRY4' for row in report_rows), 'Mapped carry inventory primitive identities: '+stage)
                inventory['reported_global_CARRY4']=len(report_rows)
                predicates=(reports/(stage+'-local-predicates.tsv')).read_text().splitlines()[1:]
                cursor=[row for row in predicates if '/prepared_req_addr_reg[' in row.split('\t')[0] and row.split('\t')[1].startswith('FD')]
                inventory['reported_prepared_cursor_FFs']=len(cursor)
                if inventory['available']:
                    audit.check(inventory['global_CARRY4_cellrefs']==len(report_rows), 'Independent EDIF global carry count equals mapped report: '+stage)
                    audit.check(inventory['queue_registers']['prepared_req_addr']['count']==len(cursor), 'Independent EDIF cursor FF count equals local inventory: '+stage)
                mapped[stage]=dict(checkpoint=pin(checkpoint),**inventory)
            old_artifacts=old.get('external_artifacts',old.get('artifacts',{}))
            old_dcp=old_artifacts['route.dcp']
            old_external=Path(old_dcp['external_path'])
            audit.check(sha(old_external)==old_dcp['sha256'] and old_external.stat().st_size==old_dcp['bytes'], 'Original B125 routed checkpoint historical pin')
            old_mapping=mapping(old_external)
            old_mapping['checkpoint_observed_now']=pin(old_external)
            old_mapping['historical_receipt_DCP_pin_available']=True
            old_mapping['historical_checkpoint_pin']=old_dcp
            observation=load(B_OBSERVATION)
            audit.check(str(old_external)==observation['checkpoint']['external_path'] and sha(old_external)==observation['checkpoint']['sha256'], 'B125 DCP agrees with separate pre-candidate checkpoint observation')
            old_mapping['separate_V121_baseline_observation']=pin(B_OBSERVATION)
            old_mapping['reported_global_CARRY4']=len((B_RECEIPT.parent/'reports/route-carry-inventory.tsv').read_text().splitlines())-1
            if old_mapping['available']:
                audit.check(old_mapping['global_CARRY4_cellrefs']==old_mapping['reported_global_CARRY4'], 'Observed B125 EDIF carry count equals immutable routed inventory')
            result['mapped_inventory']=dict(candidate=mapped,baseline_B125=old_mapping)
        else:
            result['design_timing_unavailable_reason']='Native job did not complete routing; failure/stop transcript retained and rehashed.'
    except Exception as error:
        result['errors'].append(dict(type=type(error).__name__,message=str(error)))
    failed=[check for check in audit.checks if not check['passed']]
    result['failed_checks']=failed
    result['integrity_status']='PASS' if not failed and not result['errors'] else 'FAIL'
    result['status']='PASS_V123_INDEPENDENT_TERMINAL_EVIDENCE' if result['integrity_status']=='PASS' else 'FAIL_V123_INDEPENDENT_TERMINAL_EVIDENCE'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    attempts=args.output.parent/(args.output.stem+'-attempts')
    attempts.mkdir(exist_ok=True)
    attempt=attempts/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    result['retained_audit_attempt_path']=str(attempt.resolve().relative_to(ROOT))
    payload=json.dumps(result,indent=2,sort_keys=True)+'\n'
    with attempt.open('x') as stream:
        stream.write(payload)
    args.output.write_text(payload)
    print(result['status'],'design_timing_pass='+str(result['design_timing_pass']),args.output,sha(args.output))
    if failed or result['errors']:
        print(json.dumps(dict(failed_checks=failed,errors=result['errors']),indent=2))
        raise SystemExit(1)


if __name__=='__main__':
    main()
