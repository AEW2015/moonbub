#!/usr/bin/env python3
"""Source-backed V101 timing obligations and an OOC recipe; no timing signoff.

Default regenerates the deterministic source audit. --probe performs only a
bounded read-only installed-part query. --prepare copies inputs into a fresh
external directory; it never launches synthesis or hardware programming.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v101/constraints'
RECIPE = ROOT / 'fpga/experiments/cu66-v101-constraints'
FROZEN = ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')
TOP = 'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv'
SCRATCH = 'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv'
CONTAINER = 'gamebub-cu66-v69-vivado'
LAUNCHER = '/opt/Xilinx/2025.2/Vivado/bin/vivado'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def evidence(path, text):
    rows = [{'path': path, 'line': n, 'text': line.strip()}
            for n, line in enumerate((ROOT / path).read_text().splitlines(), 1) if text in line]
    assert rows, (path, text)
    return rows


def ports(path):
    header = re.search(r'module\s+cs88_pipeline_v91k\s*\((.*?)\);', path.read_text(), re.S)[1]
    result = []
    direction = packed = None
    for item in header.split(','):
        item = item.strip()
        decl = re.fullmatch(r'(input|output)\s+logic\s+(signed\s+)?(\[\d+:\d+\]\s*)?(.+)', item)
        if decl:
            direction, signed, packed, item = decl.groups()
        assert direction is not None
        name = re.fullmatch(r'(\w+)\s*(?:\[(\d+):(\d+)\])?', item.strip())
        assert name, item
        width = [int(x) for x in re.findall(r'\d+', packed or '')]
        bits = abs(width[0] - width[1]) + 1 if width else 1
        dimensions = [int(x) for x in name.groups()[1:]] if name[2] is not None else None
        elements = abs(dimensions[0] - dimensions[1]) + 1 if dimensions else 1
        result.append({'name': name[1], 'direction': direction, 'packed_width': bits,
                       'elements': elements, 'total_bits': bits * elements,
                       'unpacked_range': dimensions, 'signed': bool(signed)})
    assert len(result) == 308 and len({p['name'] for p in result}) == 308
    return result


def inventory():
    frozen = json.loads(FROZEN.read_text())
    for name in frozen['rtl_sources'] + frozen['include_headers']:
        assert sha(ROOT / name) == frozen['source_sha256'][name], ('frozen RTL changed', name)
    timing_sources = [
        'fpga/evidence/button_pins_rev4.xdc', 'fpga/evidence/lcd_pins_rev4.xdc',
        'fpga/evidence/sdram_pins_rev4.xdc', 'fpga/scripts/buttons.xdc',
        'fpga/scripts/platform.xdc', 'fpga/scripts/timing.tcl',
        'fpga/scripts/timing-reviewed.tcl', 'fpga/experiments/cu66-v100-baseline/component.xdc']
    board_sources = ['fpga/rtl/' + name for name in ('moonshine_top.sv', 'moonshine_bus_cdc.sv',
        'moonshine_qspi_endpoint.sv', 'moonshine_memory.sv', 'moonshine_sdram.sv',
        'moonshine_lcd.sv', 'esp32_overlay.sv')]
    flows = ['fpga/scripts/build.tcl', 'fpga/scripts/build_final.tcl',
             'fpga/scripts/resume_impl.tcl', 'fpga/scripts/close_timing.tcl']
    other = flows + [
             'fpga/experiments/cu66-v100-baseline/policy.json',
             'experiments/python-gamebub-v99/profile.json', str(FROZEN.relative_to(ROOT))]
    sources = sorted(set(frozen['rtl_sources'] + frozen['include_headers'] + timing_sources + board_sources + other))
    hashes = {name: sha(ROOT / name) for name in sources}
    historical_unchanged = subprocess.run(['git', 'diff', '--quiet', 'e8bb1c9cc3cec6775cf128c8fd538a56f022575f', '--',
                                         *timing_sources, *flows], cwd=ROOT).returncode == 0
    assert historical_unchanged, 'historical timing/flow inputs changed versus V100'
    event_rows = []
    for name in frozen['rtl_sources']:
        text = (ROOT / name).read_text()
        for match in re.finditer(r'\balways(?:_ff)?\s*@\s*\(([^)]+)\)', text):
            event_rows.append({'path': name, 'line': text[:match.start()].count('\n') + 1,
                               'event_expression': match[1].strip()})
    clocks = sorted({event for row in event_rows for event in re.findall(r'\b(?:posedge|negedge)\s+(\w+)', row['event_expression'])})
    assert clocks == ['clk'] and all(re.fullmatch(r'posedge\s+clk', x['event_expression']) for x in event_rows)
    pp = ports(ROOT / TOP)
    existing = json.loads((ROOT / 'experiments/python-gamebub-v100/inventory.json').read_text())
    prior = next(x for x in existing['interfaces']['port_ledger'] if x['module'] == 'cs88_pipeline_v91k')
    assert [x['name'] for x in pp] == [x['name'] for x in prior['ports']]
    command_names = ('create_clock', 'create_generated_clock', 'set_input_delay', 'set_output_delay',
                     'set_false_path', 'set_multicycle_path', 'set_clock_groups', 'set_max_delay', 'set_bus_skew')
    history = []
    for name in timing_sources:
        rows = []
        for n, line in enumerate((ROOT / name).read_text().splitlines(), 1):
            stripped = line.strip()
            for command in command_names:
                if stripped.startswith(command + ' '):
                    rows.append({'line': n, 'command': command, 'text': stripped})
        history.append({'path': name, 'sha256': hashes[name], 'commands': rows,
                        'scope': 'Historical source statements; not elaborated object coverage or current candidate constraints'})
    newxdc = (RECIPE / 'component.xdc').read_text()
    active = '\n'.join(line for line in newxdc.splitlines() if not line.lstrip().startswith('#'))
    run = (RECIPE / 'run.tcl').read_text()
    checks = [
        {'name': 'frozen_rtl_hashes', 'pass': True, 'count': len(frozen['rtl_sources']) + len(frozen['include_headers'])},
        {'name': 'all_selected_clocked_event_expressions_posedge_clk', 'pass': True, 'count': len(event_rows)},
        {'name': 'all_308_public_port_names_in_declared_order', 'pass': True, 'count': len(pp)},
        {'name': 'comparison_clock_loaded_before_synthesis', 'pass': run.index('read_xdc $constraint_file') < run.index('\nsynth_design')},
        {'name': 'no_invented_external_delays_or_exceptions', 'pass': not any(re.search(r'\b' + x + r'\b', active) for x in command_names[2:])},
        {'name': 'only_single_component_clock_definition', 'pass': active.strip() == 'create_clock -name component_clk -period 10.000 [get_ports clk]'},
        {'name': 'historical_constraints_and_flows_unchanged_vs_v100', 'pass': historical_unchanged, 'count': len(timing_sources) + len(flows)}]
    assert all(x['pass'] for x in checks)
    board_text = (ROOT / 'fpga/rtl/moonshine_top.sv').read_text()
    for marker in ('.CLKIN1_PERIOD(20.0)', '.CLKFBOUT_MULT(20)', '.DIVCLK_DIVIDE(1)',
                   '.CLKOUT0_DIVIDE(5)', '.CLKOUT1_DIVIDE(10)', '.CLKOUT2_DIVIDE(10)',
                   '.CLKOUT2_PHASE(279.0)', '.CLKFBOUT_MULT_F(56.375)',
                   '.DIVCLK_DIVIDE(3)', '.CLKOUT0_DIVIDE_F(32.0)'):
        assert marker in board_text, ('clock topology changed; rederive ledger', marker)
    board_clocks = [
        {'name': 'clk50', 'kind': 'primary', 'source': 'clk_50mhz', 'frequency_hz': 50000000, 'period_ns': 20.0,
         'evidence': evidence('fpga/evidence/lcd_pins_rev4.xdc', 'create_clock')},
        {'name': 'clk200', 'kind': 'PLL derived', 'source': 'service_pll.CLKOUT0', 'frequency_hz': 200000000, 'period_ns': 5.0},
        {'name': 'clk100', 'kind': 'PLL derived', 'source': 'service_pll.CLKOUT1', 'frequency_hz': 100000000, 'period_ns': 10.0},
        {'name': 'read_clk100', 'kind': 'PLL derived', 'source': 'service_pll.CLKOUT2', 'frequency_hz': 100000000,
         'period_ns': 10.0, 'phase_degrees': 279.0, 'phase_ns': 7.75},
        {'name': 'pclk', 'kind': 'MMCM derived', 'source': 'panel_mmcm.CLKOUT0',
         'frequency_hz_rational': {'numerator': 50000000 * 56375, 'denominator': 1000 * 3 * 32},
         'frequency_hz': 50000000 * 56.375 / 3 / 32, 'period_ns': 1e9 / (50000000 * 56.375 / 3 / 32)},
        {'name': 'sdram_forwarded', 'kind': 'forwarded output', 'source': 'memory/controller/forward_clock/C',
         'port': 'sdram_clk', 'relationship': 'inverted clk100; historical timing source defines generated clock'},
        {'name': 'lcd_forwarded', 'kind': 'forwarded output', 'source': 'dotclock/C',
         'port': 'lcd_dotclk', 'relationship': 'inverted pclk; historical timing source defines generated clock'}]
    for clock in board_clocks[1:5]:
        clock['evidence'] = evidence('fpga/rtl/moonshine_top.sv', 'PLLE2_BASE' if clock['kind'].startswith('PLL') else 'MMCME2_BASE')
    obligations = [
        {'id': 'OOC_EXTERNAL', 'scope': '307 non-clock public ports', 'status': 'OPEN',
         'required': 'Bind each input/output arrival/required time and external register/service to clk; ready/valid is a functional contract, not an I/O timing constraint.'},
        {'id': 'OOC_RESET', 'scope': 'reset, abort_packet, start and child cancellation', 'status': 'OPEN_INTEGRATION',
         'required': 'Drive controls synchronously to clk or add a proven boundary; pulse widths, reset release, accepted-owner drain and stale-response cancellation must remain valid.'},
        {'id': 'BOARD_OSCILLATOR', 'status': 'OPEN_PHYSICAL', 'required': 'Confirm board revision/part, oscillator tolerance/jitter and actual generated clocks; retain relationships from common primary clock, not blanket asynchronous groups.'},
        {'id': 'SDRAM_IO', 'status': 'OPEN_PHYSICAL', 'required': 'Confirm fitted memory timing/PVT/board flight and skew for min/max IO, 279-degree capture, previous-beat setup and strong hold. Historical 2.0/-1.3 output and 7.0/2.0 input ns are explicitly provisional.'},
        {'id': 'LCD_IO', 'status': 'OPEN_PHYSICAL', 'required': 'Confirm panel/board min/max setup, hold and skew. Historical 2.0/-1.0 ns output values are not established requirements for new hardware.'},
        {'id': 'QSPI_IO', 'status': 'OPEN_PHYSICAL', 'required': 'Confirm ESP32 launch/sample edges, device delays, PCB skew, bidirectional OE turnaround and sampling aperture. SCK is sampled data in clk200 RTL, not an internal fabric clock.'},
        {'id': 'FIFO_GRAY', 'status': 'OPEN_NETLIST', 'required': 'Validate actual first-stage endpoint matches and Gray max-delay/bus-skew constraints; never cut following recovery stages.'},
        {'id': 'MAILBOX_CDC', 'status': 'OPEN_NETLIST', 'required': 'Prove held payload until ACK, toggle synchronizers, reset coherency and destination capture including LCD line/overlay stores.'},
        {'id': 'NETLIST_METHOD', 'status': 'OPEN_NO_CANDIDATE_NETLIST', 'required': 'Run check_timing, report_methodology, report_drc, report_cdc, report_exceptions, clock interactions and min/max paths on the actual candidate. Source scans do not close these.'},
        {'id': 'FULL_CUSTOM_TOP', 'status': 'OPEN', 'required': 'Join actual custom HUD/C2/publication/shared-memory/display/transport and board clocks; current top is an OOC component, existing board image is JPEG/MSV1.'}]
    preflight = AREA / 'tool-preflight.json'
    preflight_ref = {'receipt': str(preflight.relative_to(ROOT)), 'status': 'NOT_RUN'}
    if preflight.exists():
        actual = json.loads(preflight.read_text())
        preflight_ref.update({'status': actual['status'], 'sha256': sha(preflight),
                              'values': actual['values'], 'part_query_complete': actual['part_query_complete']})
    runtime_path = AREA / '2026/results.json'
    runtime_ref = {'receipt': str(runtime_path.relative_to(ROOT)), 'status': 'NOT_RUN'}
    if runtime_path.exists():
        actual = json.loads(runtime_path.read_text())
        runtime_ref.update({'sha256': sha(runtime_path), 'status': actual['status'],
                            'actual_tool_version': actual['actual_tool_version'],
                            'exact_target_count': actual['exact_target_count'],
                            'part_query_complete': actual['part_query_complete']})
    build_path = AREA / '2026-build/results.json'
    build_ref = {'receipt': str(build_path.relative_to(ROOT)), 'status': 'NOT_FINALIZED'}
    synthesized = routed = False
    if build_path.exists():
        actual = json.loads(build_path.read_text())
        build_ref.update({'sha256': sha(build_path), 'status': actual['status']})
        synthesized = actual.get('synthesis_checkpoint_written', False)
        routed = actual.get('component_route_finished', False)
    if synthesized:
        method = next(item for item in obligations if item['id'] == 'NETLIST_METHOD')
        method['status'] = 'OPEN_SYNTHESIS_RESOURCE_BLOCKED' if not routed else 'OPEN_FINDING_REVIEW'
        method['required'] = ('Review and resolve the retained synthesis methodology/DRC/timing findings, '
            'restore device fit, qualify actual I/O contracts, then collect placement/routing and '
            'complete-top CDC/exception evidence. Native component synthesis and its reports already exist.')
    ledger = {'schema': 'v101-constraints-source-audit-v1', 'status': 'PASS_SOURCE_AUDIT_SIGNOFF_OPEN',
        'auditor': {'path': str(Path(__file__).relative_to(ROOT)), 'sha256': sha(__file__)},
        'baseline': 'e8bb1c9cc3cec6775cf128c8fd538a56f022575f',
        'source_sha256': hashes, 'recipe_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(RECIPE.glob('*')) if p.is_file()},
        'component': {'top': 'cs88_pipeline_v91k', 'source': TOP, 'port_count': len(pp), 'ports': pp,
            'input_port_count': sum(p['direction'] == 'input' for p in pp),
            'output_port_count': sum(p['direction'] == 'output' for p in pp),
            'clock': {'name': 'clk', 'period_ns': 10.0, 'kind': 'comparison target only', 'achieved': False},
            'sensitivity_events': event_rows, 'reset_contract': 'All selected clocked source processes are posedge clk. Reset/cancel/start controls are sampled synchronously; assertion processes are included in the static event inventory. No reset synchronizer or asynchronous input contract is provided by this OOC top.',
            'reset_evidence': evidence(TOP, 'if(reset||abort_packet||accepted_start)'),
            'external_delays_qualified': False, 'generated_clocks': []},
        'board': {'source': 'fpga/rtl/moonshine_top.sv', 'existing_image': 'JPEG/MSV1; not integrated custom CS88',
            'clocks': board_clocks, 'relationship': 'Primary and PLL/MMCM generated clocks share clk50; no asynchronous clock grouping is inferred by this audit.',
            'sampled_async_input': {'name': 'mcu_spi_clk', 'destination': 'endpoint.sck_sync in clk200', 'is_fabric_clock_in_reviewed_RTL': False},
            'resets': [{'source': 'service_pll.LOCKED', 'chains': ['rst200', 'rst100'], 'assertion': 'asynchronous on falling locked', 'release': 'four receiving rising edges', 'evidence': evidence('fpga/rtl/moonshine_top.sv', 'always @(posedge clk')},
                       {'source': 'panel_mmcm.LOCKED', 'chains': ['rstpixel'], 'assertion': 'asynchronous on falling plocked', 'release': 'four receiving rising edges', 'evidence': evidence('fpga/rtl/moonshine_top.sv', 'always @(posedge pclk')},
                       {'source': 'read_clk100 capture', 'chains': [], 'assertion': 'dq_capture and dq_retime have no explicit reset; consumer/controller reset gates their use', 'evidence': evidence('fpga/rtl/moonshine_sdram.sv', 'dq_capture<=')}],
            'crossings': [{'source': 'clk200', 'destination': 'clk100', 'kind': 'async FIFO Gray pointers, read/ACK mailbox and overflow Gray', 'rtl': ['fpga/rtl/moonshine_bus_cdc.sv', 'fpga/rtl/moonshine_top.sv']},
                          {'source': 'clk100', 'destination': 'pclk', 'kind': 'dual-clock line banks/tokens/status and underrun Gray return', 'rtl': ['fpga/rtl/moonshine_lcd.sv']},
                          {'source': 'clk200', 'destination': 'pclk', 'kind': 'overlay RAM/control boundary', 'rtl': ['fpga/rtl/esp32_overlay.sv']},
                          {'source': 'SDRAM DQ', 'destination': 'read_clk100 then negedge clk100', 'kind': 'phased capture/retime, related clocks', 'rtl': ['fpga/rtl/moonshine_sdram.sv']}],
            'active_historical_constraint_source_set': ['fpga/evidence/lcd_pins_rev4.xdc', 'fpga/evidence/sdram_pins_rev4.xdc', 'fpga/scripts/buttons.xdc', 'fpga/scripts/platform.xdc', 'fpga/scripts/timing-reviewed.tcl'],
            'active_build_evidence': evidence('fpga/scripts/build_final.tcl', 'timing-reviewed.tcl')},
        'historical_timing_sources': history,
        'historical_flow_hooks': [
            {'path': flows[0], 'sha256': hashes[flows[0]], 'constraint_source': 'fpga/scripts/timing.tcl', 'evidence': evidence(flows[0], 'source [file join $here timing.tcl]')},
            {'path': flows[1], 'sha256': hashes[flows[1]], 'constraint_source': 'fpga/scripts/timing-reviewed.tcl', 'evidence': evidence(flows[1], 'source [file join $here timing-reviewed.tcl]')},
            {'path': flows[2], 'sha256': hashes[flows[2]], 'constraint_source': 'fpga/scripts/timing-reviewed.tcl', 'evidence': evidence(flows[2], 'source [file join $here timing-reviewed.tcl]')},
            {'path': flows[3], 'sha256': hashes[flows[3]], 'constraint_source': 'Inherited exact v3 routed checkpoint; not a new XDC import', 'evidence': evidence(flows[3], 'open_checkpoint')}],
        'historical_SCM_timing_changes': [], 'timing_obligations': obligations,
        'static_checks': checks,
        'tool_preflight': preflight_ref,
        'selected_2026_preflight': runtime_ref, 'actual_vendor_build': build_ref,
        'gates': {'source_inventory_pass': True, 'exact_part_tool_available': runtime_ref['status'] == 'EXACT_TARGET_AVAILABLE',
            'exact_part_synthesis': synthesized, 'placed_and_routed': routed,
            'methodology_DRC_CDC_signoff': False, 'board_IO_delays_qualified': False,
            'hardware_30fps': False, 'complete_validated_decode_under10ms': False},
        'limits': ['Source event/constraint counts are not instantiated register, CDC path or vendor-violation counts.',
                   'Historical board constraints are inventory only, not applied to the OOC candidate.',
                   'No measured board requirements, exception waivers, mapped netlist or timing signoff is manufactured.']}
    write(AREA / 'ledger.json', ledger)
    print('PASS_SOURCE_AUDIT', len(pp), 'ports;', len(event_rows), 'posedge-clk source processes;', len(history), 'timing source files;', len(obligations), 'open timing obligations')


def prepare(path, override):
    path = path.resolve()
    path.relative_to(BUILD_ROOT.resolve())
    assert not path.exists(), 'use a new external build directory'
    frozen = json.loads(FROZEN.read_text())
    path.mkdir(parents=True)
    source_hashes = {}
    names = frozen['rtl_sources'] + frozen['include_headers']
    for name in names:
        source = override.resolve() if override and name == SCRATCH else ROOT / name
        assert source.is_file()
        if override and name == SCRATCH:
            header = lambda text: re.sub(r'\s+', '', text.split(');', 1)[0])
            assert header(source.read_text()) == header((ROOT / SCRATCH).read_text()), 'scratch public declaration changed'
        else:
            assert sha(source) == frozen['source_sha256'][name], ('frozen input changed', name)
        target = path / 'snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        source_hashes[name] = sha(target)
    for name in ('run.tcl', 'report.tcl', 'component.xdc'):
        shutil.copyfile(RECIPE / name, path / name)
    def word(value):
        value = str(value)
        assert not any(x in value for x in '{}\n\r')
        return '{' + value + '}'
    # The existing Vivado container exposes BUILD_ROOT as /build.
    mapped = Path('/build') / path.relative_to(BUILD_ROOT.resolve())
    inputs = ['set part xc7a100tcsg324-1',
        'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in frozen['rtl_sources']) + ']',
        'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in frozen['include_directories']) + ']',
        'set constraint_file ' + word(mapped / 'component.xdc')]
    (path / 'inputs.tcl').write_text('\n'.join(inputs) + '\n')
    write(path / 'inputs.json', {'schema': 'v101-prepared-ooc-inputs-v1', 'frozen_manifest': str(FROZEN.relative_to(ROOT)),
        'frozen_manifest_sha256': sha(FROZEN), 'source_sha256': source_hashes,
        'recipe_sha256': {n: sha(path / n) for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
        'scratch_override': None if override is None else {'path': str(override.resolve()), 'sha256': sha(override)},
        'qualification': 'Prepared inputs only. Override, if present, is an explicit candidate; baseline RTL remains unchanged.'})
    print('PREPARED_ONLY', path)
    if (AREA / '2026/results.json').exists():
        print('python3 fpga/experiments/cu66-v101-constraints/run_vivado2026.py --build', path,
              '--license-file /path/to/existing-legitimate-private-license-file')
    else:
        print('docker exec -w', mapped, CONTAINER, LAUNCHER, '-mode batch -nojournal -nolog -notrace -source run.tcl -tclargs', mapped)


def probe():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    attempt = AREA / 'attempts' / stamp
    attempt.mkdir(parents=True, exist_ok=False)
    external = BUILD_ROOT / ('v101-constraints-query-' + stamp)
    external.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(RECIPE / 'query.tcl', external / 'query.tcl')
    mapped = Path('/build') / external.name
    cmd = ['docker', 'exec', '-w', str(mapped), CONTAINER, LAUNCHER, '-mode', 'batch', '-nojournal', '-nolog', '-notrace', '-source', str(mapped / 'query.tcl')]
    with (attempt / 'query.log').open('w') as log:
        try:
            run = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=65)
            code = run.returncode
        except subprocess.TimeoutExpired:
            code = 'TIMEOUT_65S'
    text = (attempt / 'query.log').read_text()
    values = dict(re.findall(r'^V101_(\w+)=(\S+)', text, re.M))
    complete = code == 0 and 'V101_QUERY_COMPLETE' in text
    obj = {'schema': 'v101-exact-tool-preflight-v1', 'status': 'EXACT_PART_UNAVAILABLE' if complete and values.get('TARGET_COUNT') == '0' else 'QUERY_COMPLETE' if complete else 'TOOL_FAILED',
        'command': cmd, 'observed_exit_code': code, 'values': values, 'part_query_complete': complete,
        'source': str((RECIPE / 'query.tcl').relative_to(ROOT)), 'source_sha256': sha(RECIPE / 'query.tcl'),
        'log': str((attempt / 'query.log').relative_to(ROOT)), 'log_sha256': sha(attempt / 'query.log'),
        'synthesis_started': False, 'placement_started': False, 'routing_started': False,
        'methodology_DRC_CDC_signoff': False, 'board_IO_delays_qualified': False,
        'scope': 'Fresh read-only installed-part query only; no exact part/device substitution or hardware contact.'}
    write(attempt / 'receipt.json', obj)
    write(AREA / 'tool-preflight.json', obj)
    print(obj['status'], values)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--prepare', type=Path)
    parser.add_argument('--scratch-override', type=Path)
    args = parser.parse_args()
    assert not args.scratch_override or args.prepare, '--scratch-override requires --prepare'
    if args.prepare:
        prepare(args.prepare, args.scratch_override)
    elif args.probe:
        probe()
    else:
        inventory()
