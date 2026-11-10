#!/usr/bin/env python3
"""Source/proof-bound V124 fresh-RTL component measurements; no board access."""
import argparse
import datetime
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

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v124'
BUILD = Path('/home/lori/gamebub-build/cu66-v69')
FLOW = ROOT / 'fpga/experiments/cu66-v120-flow'
BASE = ROOT / 'experiments/python-gamebub-v120/handoff.json'
PARENT = ROOT / 'experiments/python-gamebub-v123/integration/results.json'
PARENT_SHA = '0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00'
PROOFS = AREA / 'integration/results.json'
ALIAS = 'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
CANDIDATE = 'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'
IMAGE = 'sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742'
PARSER = ROOT / 'scripts/cu66-v120/admission_repair/native.py'
AUDITOR = Path(__file__).with_name('audit_native.py')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def write(p, d):
    Path(p).write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT))


def pin(p):
    return dict(path=rel(p), sha256=sha(p))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def memory():
    m = {x.split(':')[0]: int(x.split()[1]) * 1024
         for x in Path('/proc/meminfo').read_text().splitlines()}
    pressure = next(x for x in Path('/proc/pressure/memory').read_text().splitlines()
                    if x.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],
                psi_full_avg10=float(pressure.split('avg10=')[1].split()[0]),
                combined_used_fraction=(m['MemTotal'] - m['MemAvailable'] +
                    m['SwapTotal'] - m['SwapFree']) / (m['MemTotal'] + m['SwapTotal']))


def parser():
    spec = importlib.util.spec_from_file_location('retained_v120_report_parser', PARSER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def composition_identity(contract):
    source_bytes = {alias: meta['sha256'] for alias, meta in contract['source_origins'].items()}
    return hashlib.sha256(json.dumps(source_bytes, sort_keys=True).encode()).hexdigest()


def checked_proofs():
    qualified = load(BASE)
    for meta in qualified['source_origins'].values():
        require(sha(ROOT / meta['path']) == meta['sha256'], 'Frozen Source B changed')
    require(sha(PARENT) == PARENT_SHA, 'V123 functional parent index changed')
    base = load(PARENT)
    require(base['status'] == 'PASS_V123_RANK_FULL_FUNCTIONAL', 'Invalid V123 parent')
    for meta in base['source_origins'].values():
        require(sha(ROOT / meta['path']) == meta['sha256'], 'Frozen V123 composition changed')
    q = load(PROOFS)
    require(q['status'] == 'PASS_V124_OWNER_FULL_FUNCTIONAL', 'Functional gate open')
    require(q['all_original_oracles_retained'] and q['exact_B_public_cycles'] and
            q['assertions_disabled_or_downgraded'] is False, 'Functional contract changed')
    origins = q['source_origins']
    require(set(origins) == set(base['source_origins']), 'Source alias map changed')
    require(origins[ALIAS] == pin(ROOT / CANDIDATE), 'Unexpected producer source')
    for alias, meta in origins.items():
        require(sha(ROOT / meta['path']) == meta['sha256'], 'Candidate source drift')
        if alias != ALIAS:
            require(meta == base['source_origins'][alias], 'Unexpected composition change')
    pins = {rel(PROOFS): sha(PROOFS), rel(BASE): sha(BASE), rel(PARENT): sha(PARENT)}
    require(set(q['stages']) == {'focused', 'spatial', 'peer', 'parent'}, 'Missing proof stage')
    for stage, meta in q['stages'].items():
        selected = ROOT / meta['path']
        require(sha(selected) == meta['sha256'], stage + ' selector changed')
        summary = load(selected)
        pins[rel(selected)] = sha(selected)
        receipt = selected
        for key, digest in (('selected_report', 'selected_report_sha256'),
                            ('path', 'sha256'), ('selected_receipt', None)):
            if key in summary and isinstance(summary[key], str):
                receipt = ROOT / summary[key]
                if digest:
                    require(sha(receipt) == summary[digest], stage + ' receipt mismatch')
                break
        d = load(receipt)
        require(d['status'].startswith('PASS') and d.get('actual_RTL_run') is True,
                stage + ' not an executed RTL PASS')
        require(d.get('assertions_disabled_or_downgraded', False) is False,
                stage + ' assertions changed')
        require(d['source_sha256'].get(CANDIDATE) == origins[ALIAS]['sha256'],
                stage + ' not candidate-bound')
        for name, digest in d['source_sha256'].items():
            require(sha(ROOT / name) == digest, stage + ' source drift: ' + name)
        artifacts = d.get('artifact_sha256', d.get('artifacts_sha256', {}))
        require(bool(artifacts), stage + ' missing artifacts')
        for name, digest in artifacts.items():
            require(sha(receipt.parent / name) == digest, stage + ' artifact drift: ' + name)
        require(bool(d['commands']), stage + ' missing executed commands')
        commands = [c if isinstance(c, list) else c['argv'] for c in d['commands']]
        compiles = [c for c in commands if 'verilator' in c and '--cc' in c]
        require(bool(compiles) and all('--assert' in c and '-Wall' in c and
                '-Wno-fatal' not in c for c in compiles), stage + ' strict compile gate')
        executable_compiles = [c for c in compiles if '--exe' in c]
        require(bool(executable_compiles) and all('-CFLAGS' in c and
                '-Werror' in c[c.index('-CFLAGS') + 1] for c in executable_compiles),
                stage + ' executable host warning gate')
        library_compiles = [c for c in compiles if '--exe' not in c]
        for command in library_compiles:
            require('--top-module' in command and
                    command[command.index('--top-module') + 1] == 'v97_forward',
                    stage + ' unexpected non-executable RTL build')
        if library_compiles:
            adapters = [c for c in commands if 'g++' in c]
            require(bool(adapters) and all(all(flag in c for flag in
                ('-std=c++17', '-Wall', '-Wextra', '-Werror')) for c in adapters),
                stage + ' strict transport adapter gate')
        pins[rel(receipt)] = sha(receipt)
    return dict(source_origins=origins, source_order=qualified['source_order'],
                proof_pins=pins, source_B=pin(BASE), functional_parent=pin(PARENT),
                changed_aliases=[ALIAS], public_cycle_contract='exact V123 and Source B',
                whole_parent_clock_qualified=False)


def prepare(a):
    contract = checked_proofs()
    period = 8.0 if a.mhz == 125 else 10.0
    clock = FLOW / ('clock-125.xdc' if a.mhz == 125 else 'clock-100.xdc')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    name = 'v124-owner-' + str(a.mhz) + '-' + stamp + '-' + uuid.uuid4().hex[:6]
    build = BUILD / name
    build.mkdir()
    out = AREA / 'prepared' / name
    out.mkdir(parents=True)
    for alias, meta in contract['source_origins'].items():
        target = build / 'snapshot' / alias
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / meta['path'], target)
    for n in ('run.tcl', 'report.tcl'):
        shutil.copyfile(FLOW / n, build / n)
    shutil.copyfile(clock, build / 'component.xdc')
    mapped = Path('/build') / name
    def word(value):
        require(not any(c in str(value) for c in '{}\r\n'), 'Unsafe Tcl path')
        return '{' + str(value) + '}'
    order = contract['source_order']
    lines = ['set part xc7a100tcsg324-1', 'set trial_id {owner-' + str(a.mhz) + '}',
             'set start_mode {rtl}', 'set expected_period_ns ' + str(period),
             'set opt_directive {Default}', 'set place_directive {ExtraNetDelay_high}',
             'set phys_directive {NONE}', 'set route_directive {Default}',
             'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n)
                 for n in order['rtl_read_order_aliases']) + ']',
             'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n)
                 for n in order['include_directory_aliases']) + ']',
             'set constraint_file ' + word(mapped / 'component.xdc')]
    (build / 'inputs.tcl').write_text('\n'.join(lines) + '\n')
    card = dict(schema='v124-native-preflight-v1', status='PREPARED_NOT_RUN',
                part='xc7a100tcsg324-1', top='cs88_pipeline_v91k',
                clock_period_ns=period, start_mode='rtl', build_external=str(build),
                source_contract=contract, image_id=IMAGE, timeout_seconds=3600,
                recipe_sha256={n: sha(build / n) for n in
                    ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
                tooling_sha256={rel(p): sha(p) for p in (Path(__file__), PARSER, clock, AUDITOR)},
                clean_repeat_of=pin(a.repeat_of) if a.repeat_of else None,
                hardware_contact=False, bitstream_generated=False,
                cpus=2, max_threads=2, memory_limit_bytes=8 * 1024**3,
                memory_swap_limit_bytes=8 * 1024**3, max_heavy_jobs=2,
                synth_directive_cli='omitted', core_recipe_reused_unchanged=True)
    if a.repeat_of:
        require(a.repeat_of.resolve().parent.parent == (AREA / 'native').resolve(),
                'Repeat must name a V124 native receipt')
        old = load(a.repeat_of)
        require(old['result']['component_internal_target_pass'], 'Only positive fresh repeat allowed')
        require(old['clean_repeat_of'] is None, 'Cannot repeat a repeat')
        require(old['source_contract'] == contract and old['clock_period_ns'] == period,
                'Repeat source/clock drift')
        require(old['tooling_sha256'] == card['tooling_sha256'], 'Repeat tooling drift')
        require(all(old['recipe_sha256'][n] == card['recipe_sha256'][n]
                    for n in ('run.tcl', 'report.tcl', 'component.xdc')), 'Repeat recipe drift')
        for name, digest in old['retained_artifact_sha256'].items():
            require(sha(a.repeat_of.parent / name) == digest, 'Repeat parent artifact drift')
    write(build / 'inputs.json', card)
    write(out / 'preflight.json', dict(card, inputs_sha256=sha(build / 'inputs.json')))
    print(rel(out / 'preflight.json'), flush=True)


def run(a):
    preflight = load(a.preflight)
    require(preflight['status'] == 'PREPARED_NOT_RUN', 'Invalid preflight')
    require(preflight['source_contract'] == checked_proofs(), 'Proof/source drift')
    build = Path(preflight['build_external']).resolve()
    build.relative_to(BUILD)
    card = load(build / 'inputs.json')
    require(preflight == dict(card, inputs_sha256=sha(build / 'inputs.json')), 'Input drift')
    for n, h in card['tooling_sha256'].items():
        require(sha(ROOT / n) == h, 'Tooling drift')
    for n, h in card['recipe_sha256'].items():
        require(sha(build / n) == h, 'Recipe drift')
    for alias, meta in card['source_contract']['source_origins'].items():
        require(sha(build / 'snapshot' / alias) == meta['sha256'], 'Snapshot drift')
    audit = load(a.audit)
    require(audit['status'] == 'PASS_V124_NATIVE_PREFLIGHT_AUDIT' and
            audit['preflight_sha256'] == sha(a.preflight) and
            audit['native_source_sha256'] == sha(Path(__file__)) and
            audit['independent_source_recipe_resource_checks'] is True and
            audit.get('audit_source_sha256') == sha(AUDITOR) and
            bool(audit.get('auditor', '').strip()), 'Preflight audit required')
    require(a.license_file.is_file(), 'Existing legitimate license path required')
    actual_image = subprocess.check_output(['docker', 'image', 'inspect', '--format',
                 '{{.Id}}', 'acorn-nexys4-ddr:2026.1'], text=True).strip()
    require(actual_image == card['image_id'] == IMAGE, 'Tool image changed')
    active = subprocess.check_output(['docker', 'ps', '--format', '{{.Names}}'], text=True).splitlines()
    require(sum(bool(re.match(r'^gamebub-v\d+-', n)) for n in active) < 2, 'Heavy slots exhausted')
    before = memory()
    require(before['available_bytes'] >= 8 * 1024**3 and before['psi_full_avg10'] < 1
            and before['combined_used_fraction'] < .85, 'Host memory launch gate')
    # No unchanged-source reroutes: one initial per composition/clock and one
    # positive fresh repeat. A different source must have its own full proofs.
    prior = [load(p) for p in (AREA / 'native').glob('*/receipt.json')]
    same = [p for p in prior if composition_identity(p['source_contract']) ==
            composition_identity(card['source_contract']) and
            p['clock_period_ns'] == card['clock_period_ns']]
    require(len(same) == (1 if card['clean_repeat_of'] else 0), 'Trial budget exhausted')
    require(len({composition_identity(p['source_contract']) for p in prior} |
                {composition_identity(card['source_contract'])}) <= 2,
            'Bounded two-composition V124 study budget exhausted')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'native' / stamp
    out.mkdir(parents=True)
    name = 'gamebub-v124-native-' + stamp.lower()
    mapped = Path('/build') / build.name
    cmd = ['docker', 'run', '--rm', '--init', '--name', name, '--memory', '8g',
           '--memory-swap', '8g', '--cpus', '2', '--pids-limit', '2048',
           '--network', 'host', '--ulimit', 'core=0', '--mount',
           'type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly',
           '--mount', f'type=bind,src={build},dst={mapped}', '--mount',
           f'type=bind,src={build / "snapshot"},dst={mapped / "snapshot"},readonly',
           '--mount', f'type=bind,src={a.license_file.resolve()},dst=/root/.Xilinx/license.dat,readonly',
           '-e', 'LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1',
           '-e', 'XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat', '-w', str(mapped),
           IMAGE, 'timeout', '--kill-after=15s', '3600s',
           '/opt/amd-tools/2026.1/Vivado/bin/vivado', '-mode', 'batch', '-nojournal',
           '-nolog', '-notrace', '-source', str(mapped / 'run.tcl'), '-tclargs', str(mapped)]
    shutil.copytree(build / 'snapshot', out / 'source-snapshot')
    (out / 'recipe-snapshot').mkdir()
    for n in card['recipe_sha256']:
        shutil.copyfile(build / n, out / 'recipe-snapshot' / n)
    shutil.copyfile(a.preflight, out / 'preflight.json')
    shutil.copyfile(a.audit, out / 'audit.json')
    shutil.copyfile(Path(__file__), out / 'native.py')
    shutil.copyfile(AUDITOR, out / 'audit_native.py')
    receipt = dict(card, status='RUNNING', container=name, command=cmd,
                   preflight=pin(a.preflight), audit=pin(a.audit), memory_samples=[],
                   source_snapshot_readonly_mount=True, board_IO_timing_qualified=False,
                   hardware_30fps=False, complete_validated_decode_under10ms=False)
    write(out / 'receipt.json', receipt)
    print('V124_NATIVE_STARTED', rel(out), card['clock_period_ns'], flush=True)
    start = time.monotonic()
    stop, last, high = None, -30, 0
    with (out / 'vivado.log').open('w') as log, (out / 'memory.jsonl').open('w') as telemetry:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            if elapsed - last >= 15:
                m = dict(elapsed_seconds=elapsed, **memory())
                receipt['memory_samples'].append(m)
                telemetry.write(json.dumps(m) + '\n'); telemetry.flush()
                last = elapsed
                high = high + 1 if m['psi_full_avg10'] >= 5 else 0
                if m['available_bytes'] < 4 * 1024**3 or high >= 2 or m['combined_used_fraction'] >= .90:
                    stop = 'HOST_MEMORY_PRESSURE'
            if elapsed > 3645:
                stop = 'HOST_WALL_TIMEOUT'
            if stop:
                subprocess.run(['docker', 'stop', '--time', '10', name], capture_output=True, timeout=20)
                break
            time.sleep(1)
        code = proc.wait(timeout=30)
    text = (out / 'vivado.log').read_text(errors='replace')
    reports = out / 'reports'
    reports.mkdir()
    for p in (build / 'results').glob('*'):
        if p.is_file() and p.suffix in ('.rpt', '.txt', '.tsv', '.json', '.xdc', '.log'):
            shutil.copyfile(p, reports / p.name)
    receipt['external_artifacts'] = {p.name: dict(external_path=str(p), sha256=sha(p),
        bytes=p.stat().st_size) for p in sorted((build / 'results').glob('*')) if p.is_file()}
    commands = re.findall(r'^Command:\s*(synth_design[^\n]*)', text, re.M)
    expected = 'synth_design -top cs88_pipeline_v91k -part xc7a100tcsg324-1 -mode out_of_context -flatten_hierarchy rebuilt'
    complete = code == 0 and 'V120_COMPONENT_ROUTE_FINISHED' in text
    receipt.update(observed_exit_code=code, wall_seconds=time.monotonic() - start,
                   monitor_stop_reason=stop, component_route_finished=complete,
                   synthesis_executed=bool(commands), synthesis_command_lines=commands,
                   observed_default_command_exact=commands == [expected],
                   clock_loaded_before_synthesis_in_this_run=(build / 'run.tcl').read_text().index(
                       'read_xdc $constraint_file') < (build / 'run.tcl').read_text().index('synth_design -top'),
                   source_snapshot_unchanged=all(sha(build / 'snapshot' / n) == m['sha256']
                       for n, m in card['source_contract']['source_origins'].items()),
                   recipe_unchanged=all(sha(build / n) == h for n, h in card['recipe_sha256'].items()),
                   log_sha256=sha(out / 'vivado.log'), checkpoint_read=False)
    receipt['status'] = 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' if complete else (
        'STOPPED_RESOURCE_OR_TIME_GATE' if stop else 'TOOL_OR_BUILD_FAILED')
    if complete:
        try:
            require(commands == [expected] and receipt['source_snapshot_unchanged'] and
                    receipt['recipe_unchanged'], 'Completed route identity changed')
            receipt['result'] = parser().parse_reports(reports, card['clock_period_ns'])
        except Exception as error:
            receipt.update(status='ROUTE_FINISHED_REPORT_PARSE_FAILED',
                           report_parse_error=repr(error))
    (out / 'METHODOLOGY_RESOLUTION_REPORT.md').write_text(
        '# V124 component methodology results\n\n'
        'The retained V120 core Tcl/report recipe runs unchanged on the separately '
        'snapshotted V124 sources. Its log markers retain their historical V120 names.\n\n'
        f"Target: {card['clock_period_ns']} ns. Result: `{json.dumps(receipt.get('result'))}`.\n\n"
        'No timing constraint changes or waivers. Missing external I/O delays remain '
        'an explicit OOC limitation; complete-parent clocks/CDC/memory/display are open. '
        'No board bitstream, hardware FPS or silicon latency claim.\n')
    receipt['retained_artifact_sha256'] = {str(p.relative_to(out)): sha(p)
        for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'receipt.json'}
    write(out / 'receipt.json', receipt)
    print('V124_NATIVE_FINISHED', rel(out), receipt['status'], receipt.get('result'), flush=True)
    if receipt['status'] != 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
        raise SystemExit(1)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    prepare_parser = sub.add_parser('prepare')
    prepare_parser.add_argument('--mhz', type=int, choices=(100, 125), required=True)
    prepare_parser.add_argument('--repeat-of', type=Path)
    run_parser = sub.add_parser('run')
    run_parser.add_argument('--preflight', type=Path, required=True)
    run_parser.add_argument('--audit', type=Path, required=True)
    run_parser.add_argument('--license-file', type=Path, required=True)
    a = p.parse_args()
    (prepare if a.action == 'prepare' else run)(a)


if __name__ == '__main__':
    main()
