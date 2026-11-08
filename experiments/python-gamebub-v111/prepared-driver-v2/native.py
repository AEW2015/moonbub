#!/usr/bin/env python3
"""Prepare/audit-gate bounded fresh-RTL V111 component timing measurements."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v111'
FLOW = ROOT / 'fpga/experiments/cu66-v111-flow'
POLICY = AREA / 'study-policy.json'
BUILD = Path('/home/lori/gamebub-build/cu66-v69')
PARSER = ROOT / 'fpga/experiments/cu66-v110-count-domain-flow/run_native.py'
CANONICAL_HELPER = ROOT / 'scripts/cu66-v110/native_cursors.py'


def sha(p):
    digest = hashlib.sha256()
    with Path(p).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def write(p, value):
    Path(p).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT))


def pin(p):
    return dict(path=rel(p), sha256=sha(p))


def module(p):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('v111_' + p.stem, p)
    answer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(answer)
    return answer


def word(s):
    s = str(s)
    assert not any(c in s for c in '{}\r\n')
    return '{' + s + '}'


def memory():
    return module(PARSER).memory()


def canonical(path, expected_status):
    q = load(path)
    assert q['status'] == expected_status and q['actual_RTL_run'] is True
    assert q['seeds'] == [107601, 107602]
    assert q['newly_executed_candidate_case_profiles'] == 44
    assert q['newly_executed_candidate_directed_checks'] == 42
    receipt = ROOT / q['selected_receipt']
    assert load(receipt) == {k: v for k, v in q.items() if k != 'selected_receipt'}
    for name, expected in q['source_sha256'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in q['artifact_sha256'].items():
        assert sha(receipt.parent / name) == expected, name
    baseline = ROOT / q['baseline_reference']['path']
    assert sha(baseline) == q['baseline_reference']['sha256']
    reference = load(baseline)
    for row in q['runs']:
        old = next(x for x in reference['runs'] if x['seed'] == row['seed'])
        assert row['exact_stdout_events_cycles_and_canonical'] is True
        assert row['verdict'] == old['verdict']
        for name, metadata in row['artifacts'].items():
            data = receipt.parent / metadata['path']
            assert sha(data) == metadata['sha256']
            assert hashlib.sha256(gzip.decompress(data.read_bytes())).hexdigest() == metadata['raw_sha256'] == old['artifacts'][name]['raw_sha256']
    return q


def header_focus(path, policy):
    f = load(path)
    assert f['status'] == 'PASS' and f['actual_RTL_run'] is True
    assert f['added_public_cycles'] == 0 and f['assertions_disabled_or_downgraded'] is False
    selected = ROOT / f['selected_report']
    assert sha(selected) == f['selected_report_sha256']
    for name, expected in f['source_sha256'].items():
        assert sha(ROOT / name) == expected, name
    for name, expected in f['artifacts_sha256'].items():
        assert sha(selected.parent / name) == expected, name
    assert f['source_sha256'][policy['candidate_path']] == sha(ROOT / policy['candidate_path'])
    assert len(f['whole_ingress_runs']) == 2
    assert all(x['status'] == 'TEST_PASS' and x['packets'] >= 76 and x['cancel_retries'] >= 36 for x in f['whole_ingress_runs'])
    return f


def qualify(trial, policy):
    assert trial in policy['trials']
    parent_path = ROOT / policy['frozen_v110_count_receipt']
    assert sha(parent_path) == policy['frozen_v110_count_receipt_sha256']
    parent = load(parent_path)
    assert parent['status'] == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
    assert parent['result']['timing']['WNS_ns'] == -1.022
    assert parent['start_mode'] == 'rtl' and parent['synthesis_executed']
    card_path = parent_path.parent / 'inputs.json'
    assert sha(card_path) == parent['source_manifest_sha256']
    card = load(card_path)
    control_q_path = ROOT / parent['source_contract']['canonical_qualification']
    assert sha(control_q_path) == parent['source_contract']['canonical_sha256']
    control_q = canonical(control_q_path, 'PASS_EXACT_V110_CANONICAL')
    origins = json.loads(json.dumps(parent['source_origins']))
    assert len(origins) == 18 and origins == card['source_origins']
    for metadata in origins.values():
        assert sha(ROOT / metadata['path']) == metadata['sha256']
    proofs = {control_q_path: sha(control_q_path)}
    q = control_q
    if policy['trials'][trial]['source'] == 'header':
        fp = ROOT / policy['focus_path']
        header_focus(fp, policy)
        qp = ROOT / policy['canonical_path']
        q = canonical(qp, 'PASS_EXACT_V111_CANONICAL')
        aliases = card['source_order']['rtl_read_order_aliases'] + [n for n in origins if n.endswith('.svh')]
        assert len(q['rtl_source_order']) == len(aliases) == 18
        origins = {alias: dict(path=name, sha256=sha(ROOT / name)) for alias, name in zip(aliases, q['rtl_source_order'])}
        changed = [alias for alias in origins if origins[alias] != parent['source_origins'][alias]]
        assert changed == [policy['source_delta_alias']]
        assert origins[changed[0]]['path'] == policy['candidate_path']
        assert q['source_sha256'][policy['focus_path']] == sha(fp)
        proofs.update({fp: sha(fp), qp: sha(qp)})
    assert all(q['source_sha256'][m['path']] == m['sha256'] for m in origins.values())
    assert sum(n.endswith('.sv') for n in origins) == 17
    assert sum((ROOT / m['path']).read_text().count(".PREVALIDATED_EVENT_COUNT(1'b1)") for m in origins.values()) == 1
    return dict(parent=pin(parent_path), parent_inputs=pin(card_path), source_origins=origins,
                source_sha256={a: m['sha256'] for a, m in origins.items()}, source_order=card['source_order'],
                proof_pins={rel(p): h for p, h in proofs.items()},
                observability=dict(parent=parent['observability_contract'],
                                   public_latency_delta_cycles=0,
                                   prepared_header=('Not present in unchanged Count baseline.' if policy['trials'][trial]['source'] == 'count' else 'Private stages coherent at an uncancelled consuming HEADER; CRC/basic/sum/raw priority and partial metadata writes remain exact.')))


def budget(policy, trial, repeat_of=None):
    rows = [load(p) for p in (AREA / 'coordination').glob('dispatch-*.json')]
    initial = [r for r in rows if not r['repeat_of']]
    repeats = [r for r in rows if r['repeat_of']]
    if repeat_of:
        assert len(repeats) < policy['max_positive_fresh_repeats'] == 1
        parent = positive_parent(repeat_of)
        assert parent['trial_id'] == trial and parent['clean_repeat_of'] is None
        assert parent['status'] == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'
        assert parent['result']['component_internal_target_pass'] is True
    else:
        assert len(initial) < policy['max_initial_trials'] == 3
        assert not any(r['trial_id'] == trial for r in initial), 'No silent retries'


def positive_parent(path):
    assert path.resolve().parent.parent == (AREA / 'native').resolve()
    r = load(path)
    assert r['status'] == 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and r['observed_exit_code'] == 0
    assert r['component_route_finished'] and r['synthesis_executed'] and r['start_mode'] == 'rtl'
    assert r['clock_loaded_before_synthesis_in_this_run'] and not r['checkpoint_read']
    assert r['source_snapshot_unchanged'] and r['recipe_unchanged'] and r['observed_default_command_exact']
    assert r['clean_repeat_of'] is None and r['result']['component_internal_target_pass'] is True
    assert sha(path.parent / 'vivado.log') == r['log_sha256']
    for name, expected in r['retained_artifact_sha256'].items():
        assert sha(path.parent / name) == expected, name
    assert parse_reports(path.parent / 'reports', r['clock_period_ns']) == r['result']
    return r


def prepare(args):
    policy = load(POLICY)
    contract = qualify(args.trial, policy)
    budget(policy, args.trial, args.repeat_of)
    period = policy['trials'][args.trial]['period_ns']
    clock = FLOW / ('clock-125.xdc' if period == 8.0 else 'clock-100.xdc')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:6]
    name = 'v111-' + args.trial + ('-repeat-' if args.repeat_of else '-') + stamp
    build = BUILD / name
    out = AREA / 'prepared' / name
    build.mkdir()
    out.mkdir(parents=True)
    for alias, metadata in contract['source_origins'].items():
        target = build / 'snapshot' / alias
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / metadata['path'], target)
    for n in ('run.tcl', 'report.tcl'):
        shutil.copyfile(FLOW / n, build / n)
    shutil.copyfile(clock, build / 'component.xdc')
    mapped = Path('/build') / name
    order = contract['source_order']
    lines = ['set part xc7a100tcsg324-1', 'set trial_id ' + word(args.trial), 'set start_mode {rtl}',
             'set expected_period_ns ' + str(period), 'set opt_directive {Default}',
             'set place_directive {ExtraNetDelay_high}', 'set phys_directive {NONE}', 'set route_directive {Default}',
             'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in order['rtl_read_order_aliases']) + ']',
             'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in order['include_directory_aliases']) + ']',
             'set constraint_file ' + word(mapped / 'component.xdc')]
    (build / 'inputs.tcl').write_text('\n'.join(lines) + '\n')
    tooling = [Path(__file__), PARSER, FLOW / 'run.tcl', FLOW / 'report.tcl', clock]
    card = dict(schema='v111-native-preflight-v1', status='PREPARED_NOT_RUN', trial_id=args.trial,
                build_external=str(build), part=policy['part'], top=policy['top'], clock_period_ns=period,
                start_mode='rtl', synth_directive='default', synth_directive_cli='omitted',
                timeout_seconds=policy['native_timeout_seconds'], source_contract=contract,
                policy=pin(POLICY), tooling_sha256={rel(p): sha(p) for p in tooling},
                recipe_sha256={n: sha(build / n) for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
                clean_repeat_of=pin(args.repeat_of) if args.repeat_of else None,
                image_id=subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'acorn-nexys4-ddr:2026.1'], text=True).strip(),
                hardware_contact=False, bitstream_generated=False)
    if args.repeat_of:
        old = positive_parent(args.repeat_of)
        assert old['source_contract'] == contract and old['clock_period_ns'] == period
        assert old['recipe_sha256'] == card['recipe_sha256'] or all(old['recipe_sha256'][n] == card['recipe_sha256'][n] for n in ('run.tcl', 'report.tcl', 'component.xdc'))
        assert old['policy'] == card['policy'] and old['tooling_sha256'] == card['tooling_sha256'] and old['image_id'] == card['image_id']
    write(build / 'inputs.json', card)
    for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl', 'inputs.json'):
        shutil.copyfile(build / n, out / n)
    write(out / 'preflight.json', dict(card, inputs_sha256=sha(build / 'inputs.json')))
    print('PREPARED_NOT_RUN', rel(out / 'preflight.json'), sha(out / 'preflight.json'))


def parse_reports(folder, period):
    raw = module(PARSER)
    summary = raw.timing((folder / 'route-timing-summary.rpt').read_text())
    checks = raw.timing_checks((folder / 'route-check-timing.rpt').read_text())
    routing = raw.route_status((folder / 'route-status.rpt').read_text())
    rows = re.findall(r'^component_clk\s+([\d.]+)\s+\{([\d.]+)\s+([\d.]+)\}', (folder / 'route-clocks.rpt').read_text(), re.M)
    clock_ok = len(rows) == 1 and [float(x) for x in rows[0]] == [period, 0.0, period / 2]
    passed = (clock_ok and min(summary['WNS_ns'], summary['WHS_ns'], summary['WPWS_ns']) >= 0
              and all(summary[k] == 0 for k in ('setup_failing', 'hold_failing', 'pulse_failing'))
              and all(checks[k] == 0 for k in ('no_clock', 'unconstrained_internal_endpoints', 'loops', 'latch_loops', 'multiple_clock'))
              and routing['all_routable_nets_routed'] and routing['zero_routing_errors'])
    return dict(timing=summary, check_timing=checks, routing=routing, clock_target_matches=clock_ok,
                target_period_ns=period, target_frequency_MHz=1000 / period,
                component_internal_target_pass=passed,
                worst_setup_path=raw.worst_path((folder / 'route-setup-paths.rpt').read_text()))


def launch(args):
    pf = load(args.preflight)
    assert pf['status'] == 'PREPARED_NOT_RUN'
    build = Path(pf['build_external']).resolve()
    build.relative_to(BUILD)
    card = load(build / 'inputs.json')
    assert sha(build / 'inputs.json') == pf['inputs_sha256']
    assert pf == dict(card, inputs_sha256=pf['inputs_sha256'])
    assert pin(POLICY) == card['policy']
    policy = load(POLICY)
    assert card['clock_period_ns'] == policy['trials'][card['trial_id']]['period_ns']
    assert card['part'] == policy['part'] and card['top'] == policy['top']
    assert card['start_mode'] == 'rtl' and card['synth_directive'] == 'default' and card['synth_directive_cli'] == 'omitted'
    assert card['timeout_seconds'] == policy['native_timeout_seconds'] == 3600
    assert qualify(card['trial_id'], policy) == card['source_contract']
    repeat = ROOT / card['clean_repeat_of']['path'] if card['clean_repeat_of'] else None
    if repeat:
        assert pin(repeat) == card['clean_repeat_of']
        old = positive_parent(repeat)
        assert old['source_contract'] == card['source_contract'] and old['clock_period_ns'] == card['clock_period_ns']
        assert old['policy'] == card['policy'] and old['tooling_sha256'] == card['tooling_sha256'] and old['image_id'] == card['image_id']
        assert all(old['recipe_sha256'][n] == card['recipe_sha256'][n] for n in ('run.tcl', 'report.tcl', 'component.xdc'))
    budget(policy, card['trial_id'], repeat)
    for n, expected in card['tooling_sha256'].items():
        assert sha(ROOT / n) == expected, n
    for n, expected in card['recipe_sha256'].items():
        assert sha(build / n) == expected, n
    for alias, expected in card['source_contract']['source_sha256'].items():
        assert sha(build / 'snapshot' / alias) == expected, alias
    audit = load(args.audit)
    assert audit['status'] == 'PASS_V111_NATIVE_PREFLIGHT_AUDIT'
    assert audit['preflight_sha256'] == sha(args.preflight) and audit['policy_sha256'] == sha(POLICY)
    active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    assert sum(n.startswith('gamebub-v11') for n in active) < 2, active
    before = memory()
    assert before['MemAvailable_bytes'] >= policy['launch_available_bytes'] and before['PSI_full_avg10'] < 1, before
    assert args.license_file.is_file()
    image = subprocess.check_output(['docker', 'image', 'inspect', '--format', '{{.Id}}', 'acorn-nexys4-ddr:2026.1'], text=True).strip()
    assert image == card['image_id'] and image.startswith('sha256:')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'native' / stamp
    out.mkdir(parents=True)
    coord = AREA / 'coordination'
    coord.mkdir(exist_ok=True)
    reservation = coord / ('dispatch-' + card['trial_id'] + ('-repeat' if repeat else '') + '.json')
    dispatch = dict(status='DISPATCHED_TO_RUNNER', trial_id=card['trial_id'], preflight=pin(args.preflight),
                    audit=pin(args.audit), policy=pin(POLICY), repeat_of=card['clean_repeat_of'], output=rel(out))
    with reservation.open('x') as stream:
        stream.write(json.dumps(dispatch, indent=2, sort_keys=True) + '\n')
    shutil.copytree(build / 'snapshot', out / 'source-snapshot')
    shutil.copyfile(build / 'inputs.json', out / 'inputs.json')
    shutil.copyfile(Path(__file__), out / 'native.py')
    (out / 'recipe-snapshot').mkdir()
    for name in card['recipe_sha256']:
        shutil.copyfile(build / name, out / 'recipe-snapshot' / name)
    name = 'gamebub-v111-native-' + stamp.lower()
    mapped = Path('/build') / build.name
    cmd = ['docker', 'run', '--rm', '--init', '--name', name, '--memory', '8g', '--memory-swap', '8g',
           '--cpus', '2', '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0',
           '--mount', 'type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly',
           '--mount', f'type=bind,src={build},dst={mapped}',
           '--mount', f'type=bind,src={build / "snapshot"},dst={mapped / "snapshot"},readonly',
           '--mount', f'type=bind,src={args.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly',
           '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1', '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat',
           '-w', str(mapped), image, 'timeout', '--kill-after=15s', str(card['timeout_seconds']) + 's',
           '/opt/amd-tools/2026.1/Vivado/bin/vivado', '-mode', 'batch', '-nojournal', '-nolog', '-notrace',
           '-source', str(mapped / 'run.tcl'), '-tclargs', str(mapped)]
    receipt = dict(card, status='RUNNING', command=cmd, container=name, image_id=image, preflight=pin(args.preflight),
                   audit=pin(args.audit), dispatch=pin(reservation), max_threads=2, cpus=2,
                   memory_limit_bytes=8 * 1024**3, memory_swap_limit_bytes=8 * 1024**3,
                   source_snapshot_readonly_mount=True, synthesis_executed=True,
                   clock_loaded_before_synthesis_in_this_run=True, checkpoint_read=False,
                   existing_legitimate_license_readonly=True, license_contents_logged=False,
                   hostid_or_MAC_changed=False, tools_readonly=True, full_custom_top_qualified=False,
                   board_IO_timing_qualified=False, hardware_30fps=False, complete_validated_decode_under10ms=False)
    write(out / 'receipt.json', receipt)
    print('V111_NATIVE_STARTED', rel(out), card['trial_id'], flush=True)
    start = time.monotonic()
    samples = []
    stop = None
    high = 0
    last = -30
    with (out / 'vivado.log').open('w') as log, (out / 'memory.jsonl').open('w') as telemetry:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed - last >= 30:
                sample = dict(elapsed_seconds=elapsed, **memory())
                samples.append(sample)
                telemetry.write(json.dumps(sample) + '\n')
                telemetry.flush()
                last = elapsed
                high = high + 1 if sample['PSI_full_avg10'] >= 5 else 0
                if sample['MemAvailable_bytes'] < 4 * 1024**3 or high >= 2:
                    stop = 'HOST_MEMORY_PRESSURE'
            if elapsed > card['timeout_seconds'] + 45:
                stop = 'HOST_WALL_TIMEOUT'
            if stop:
                subprocess.run(['docker', 'stop', '--time', '10', name], capture_output=True, timeout=20)
                break
            time.sleep(1)
        try:
            code = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(['docker', 'kill', name], capture_output=True, timeout=15)
            code = proc.wait(timeout=15)
    text = (out / 'vivado.log').read_text(errors='replace')
    artifacts = {}
    for p in sorted((build / 'results').glob('*')):
        if p.is_file():
            artifacts[p.name] = dict(external_path=str(p), sha256=sha(p), bytes=p.stat().st_size)
            if p.suffix in ('.rpt', '.txt', '.tsv', '.json', '.xdc', '.log'):
                (out / 'reports').mkdir(exist_ok=True)
                shutil.copyfile(p, out / 'reports' / p.name)
    for p in build.glob('hs_err_pid*.log'):
        (out / 'crash').mkdir(exist_ok=True)
        shutil.copyfile(p, out / 'crash' / p.name)
    commands = re.findall(r'^Command:\s*(synth_design[^\n]*)', text, re.M)
    expected = 'synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt'
    complete = code == 0 and 'V111_COMPONENT_ROUTE_FINISHED' in text
    receipt.update(observed_exit_code=code, wall_seconds=time.monotonic() - start,
                   monitor_stop_reason=stop, memory_samples=samples, artifacts=artifacts,
                   component_route_finished=complete, synthesis_command_lines=commands,
                   observed_default_command_exact=commands == [expected], log_sha256=sha(out / 'vivado.log'),
                   source_snapshot_unchanged=all(sha(build / 'snapshot' / n) == h for n, h in card['source_contract']['source_sha256'].items()),
                   recipe_unchanged=all(sha(build / n) == h for n, h in card['recipe_sha256'].items()))
    receipt['status'] = 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' if complete else 'STOPPED_RESOURCE_OR_TIME_GATE' if stop else 'TOOL_OR_BUILD_FAILED'
    if complete:
        try:
            assert commands == [expected] and receipt['source_snapshot_unchanged'] and receipt['recipe_unchanged']
            receipt['result'] = parse_reports(build / 'results', card['clock_period_ns'])
        except Exception as error:
            receipt.update(status='ROUTE_FINISHED_REPORT_PARSE_FAILED', report_parse_error=repr(error))
    report = ('# V111 component methodology report\n\n'
              f"Trial `{card['trial_id']}`, fresh RTL, `{card['part']}`, target {card['clock_period_ns']} ns.\n\n"
              'Default synthesis by omission; Default opt/route and ExtraNetDelay_high placement. No retiming or timing exception added.\n\n'
              'Actual clocks, before/after XDC, setup/hold/pulse, methodology, DRC, CDC, high-fanout and primitive mapping reports are retained.\n\n'
              f"Status: `{receipt['status']}`. Result: `{json.dumps(receipt.get('result'), sort_keys=True)}`.\n\n"
              'This is OOC component evidence. Missing external I/O requirements and full-parent CDC/memory/display integration remain open. No board bitstream or hardware FPS/latency qualification.\n')
    (out / 'METHODOLOGY_RESOLUTION_REPORT.md').write_text(report)
    receipt['retained_artifact_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'receipt.json'}
    write(out / 'receipt.json', receipt)
    print('V111_NATIVE_FINISHED', rel(out), receipt['status'], receipt.get('result', {}).get('timing'), flush=True)
    if receipt['status'] != 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trial', choices=('count-125', 'header-100', 'header-125'))
    ap.add_argument('--repeat-of', type=Path)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--preflight', type=Path)
    ap.add_argument('--audit', type=Path)
    ap.add_argument('--license-file', type=Path, default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'))
    args = ap.parse_args()
    if args.run:
        assert args.preflight and args.audit and not args.trial and not args.repeat_of
        launch(args)
    else:
        assert args.trial and not args.preflight and not args.audit
        prepare(args)


if __name__ == '__main__':
    main()
