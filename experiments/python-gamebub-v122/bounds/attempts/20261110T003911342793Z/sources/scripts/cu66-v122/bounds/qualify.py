#!/usr/bin/env python3
"""Strict bounded admission proof. Default verifies recipes; --run needs Root grant."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'fpga/experiments/cu66-v122-bounds'
V=SRC/'verification'
AREA = ROOT / 'experiments/python-gamebub-v122/bounds'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    temp = p.with_name(p.name + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    temp.replace(p)


def verify():
    import re,collections
    inherited=load_module(ROOT/'scripts/cu66-v120/admission_match/qualify.py','v120_frozen_bounds_control')
    inherited.verify()
    recipe=json.loads((SRC/'edit-recipe.json').read_text())
    def reversible(meta):
        before=(ROOT/meta['original']).read_text();text=before
        assert sha(ROOT/meta['original'])==meta['original_sha256']
        for e in meta['edits']:
            assert text.count(e['before'])==1
            text=text.replace(e['before'],e['after'],1)
        assert text==(ROOT/meta['candidate']).read_text() and sha(ROOT/meta['candidate'])==meta['candidate_sha256']
        for e in reversed(meta['edits']):
            assert text.count(e['after'])==1
            text=text.replace(e['after'],e['before'],1)
        assert text==before
    reversible(recipe)
    original=(ROOT/recipe['original']).read_text();candidate=(ROOT/recipe['candidate']).read_text()
    assert recipe['added_source_payload_bits']==226 and recipe['old_private_value_contract_changes']==0 and recipe['old_assertions_removed']==0
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):assert block in candidate
    v=json.loads((SRC/'verification-recipe.json').read_text())
    for meta in v['adapters']:reversible(meta)
    for meta in v['unchanged']:assert sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256']
    needs=lambda text:collections.Counter(re.findall(r'require\(.*?\);',text,re.S))
    for name in ['owner','match']:
        reversible(v[name])
        assert not needs((ROOT/v[name]['original']).read_text())-needs((ROOT/v[name]['candidate']).read_text())
    assert v['old_require_checks_removed']==0
    helper=(V/'bounds_priming.hpp').read_text()
    for name in ['prepared_number_outside','prepared_length_invalid','bounds_cursor_base','bounds_word_base','bounds_length_total','bounds_number_plus12','bounds_owner_valid']:
        assert not re.search(r'QNEW\('+name+r'\)\s*=(?!=)',helper)
        assert 'QBOTH('+name+',' not in helper
    packaging=json.loads((SRC/'packaging.json').read_text());data=(ROOT/recipe['candidate']).read_bytes()
    assert packaging['production_sha256']==sha(ROOT/recipe['candidate'])
    offsets=[0]+packaging['split_byte_offsets']+[len(data)]
    for i,f in enumerate(packaging['fragments']):assert f['bytes']==offsets[i+1]-offsets[i] and hashlib.sha256(data[offsets[i]:offsets[i+1]]).hexdigest()==f['sha256']
    cause=ROOT/'experiments/python-gamebub-v121/native/20261109T234502249779Z/reports/route-setup-paths.rpt'
    assert 'cursor_reg[1]/C' in cause.read_text() and '9.232ns' in cause.read_text()
    return recipe


def memory():
    raw = Path('/proc/meminfo').read_text()
    mem = {x.split(':')[0]:int(x.split()[1])*1024 for x in raw.splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(x for x in pressure.splitlines() if x.startswith('full '))
    # Combined host memory+swap utilization; swap is not added to containers.
    combined = (mem['MemTotal'] - mem['MemAvailable'] + mem['SwapTotal'] - mem['SwapFree']) / (mem['MemTotal'] + mem['SwapTotal'])
    return dict(monotonic=time.monotonic(), available_bytes=mem['MemAvailable'], psi_full_avg10=float(full.split('avg10=')[1].split()[0]),
                combined=combined, meminfo=raw, memory_pressure=pressure)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--root-grant', help='Root-issued heavy-slot grant; required with --run')
    args = ap.parse_args()
    recipe = verify()
    if not args.run:
        print('V122_BOUNDS_PREPARED_NOT_RUN', recipe['candidate_sha256'])
        return
    assert args.root_grant=='ROOT_V122_BOUNDS', 'Exact Root heavy execution grant required'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v122-bounds-' + stamp)
    build.mkdir()
    vectors = ROOT / 'experiments/python-gamebub-v91i/vectors/vectors.txt'
    helper_paths = [ROOT / 'scripts/cu66-v107/tables.py', ROOT / 'scripts/cu66-v100/run_rtl.py',
                    ROOT / 'scripts/cu66-v107/header/replay.py', ROOT / 'scripts/cu66-v107/tables/mode_replay.py',
                    ROOT / 'experiments/python-gamebub-v91i/admission-model.py',
                    ROOT / 'experiments/cu66-native-v69/generated_constants.hpp']
    files = sorted(set([p for p in V.iterdir() if p.is_file()] + [ROOT/recipe['original'],ROOT/recipe['candidate'],SRC/'edit-recipe.json',SRC/'verification-recipe.json',SRC/'packaging.json',ROOT/'docs/cu66-v122/bounds-design.md',ROOT/'scripts/cu66-v122/bounds/prepare.py',ROOT/'scripts/cu66-v120/admission_match/qualify.py',vectors] + helper_paths + [Path(__file__).resolve()]))
    report = dict(schema='v122-bounds-focused-v1', status='RUNNING', actual_RTL_run=False, root_grant=args.root_grant,
                  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files}, commands=[], runs=[],
                  strict_warnings=True, warning_suppression=False, assertions_disabled_or_downgraded=False,
                  old_exact_checker_modified=False, candidate_private_comparison_edits=0, all_old_require_checks_retained=True, old_fixture_preparation_call_sites_added=3,
                  added_public_cycles=0, added_source_payload_bits=226, old_private_value_contract_changes=0, old_require_checks_removed=0, candidate_model_reused=False, fresh_candidate_model_required=True, prepared_fixture_priming_edges_are_natural_cycles=False, candidate=dict(path=recipe['candidate'], sha256=recipe['candidate_sha256']),
                  optimization_note='C++ -O2 accelerates host execution only; no modeled-cycle skipping or FPGA frequency claim.',
                  backend='Verilator 5.020', image=IMAGE, build_external=str(build),
                  limits=['Finite simulation is not formal proof, routed timing closure, CDC or hardware qualification.'])
    started = time.monotonic()

    def persist():
        write(out / 'results.json', report)

    def command(argv, name, cap, simulation=False):
        gate = memory()
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined'] < .85, gate
        container = 'gamebub-v122-bounds-' + stamp.lower() + '-' + str(len(report['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container, '--memory', '8g', '--memory-swap', '8g', '--cpus', '2',
               '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0', '--mount', f'type=bind,src={build},dst=/work',
               '-w', '/work', IMAGE, 'timeout', '--kill-after=5s', str(cap)+'s', *argv]
        entry = dict(argv=cmd, resource_before=gate, timeout_seconds=cap, simulation=simulation)
        report['commands'].append(entry)
        if simulation:
            report['actual_RTL_run'] = True  # Persist BEFORE executing any simulation.
        persist()
        began = time.monotonic()
        process = None
        reason = None
        high_psi = 0
        with (out / name).open('w') as log, (out / (name+'.resources.jsonl')).open('w') as samples:
            try:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    sample = memory()
                    samples.write(json.dumps(sample, sort_keys=True)+'\n')
                    samples.flush()
                    high_psi = high_psi+1 if sample['psi_full_avg10'] >= 5 else 0
                    if sample['available_bytes'] < 4*GIB or sample['combined'] >= .9 or high_psi >= 2:
                        reason = 'RESOURCE_STOP'
                        raise RuntimeError(reason)
                    if time.monotonic()-began > cap+15:
                        reason = 'HOST_WATCHDOG'
                        raise RuntimeError(reason)
                    time.sleep(1)
                entry['exit_code'] = process.wait(timeout=10)
                assert entry['exit_code'] == 0, (name, entry['exit_code'])
            finally:
                if process is not None and process.poll() is None:
                    stopped = subprocess.run(['docker', 'stop', '--time', '3', container], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
                    (out / (name+'.stop.log')).write_bytes(stopped.stdout)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                entry.update(wall_seconds=time.monotonic()-began, stop_reason=reason, resource_after=memory())
                persist()

    try:
        for source in files:
            target = out / 'sources' / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for source in V.iterdir():
            if source.suffix in ('.sv', '.cpp', '.hpp'):
                shutil.copyfile(source, build / source.name)
        # Exact lossless helper sharing; only duplicate module definitions are
        # removed from compile units. Saved adapters and production stay whole.
        for variant in ('original', 'candidate'):
            p = build / ('admission_'+variant+'.sv')
            text = p.read_text()
            a = text.index('module cu66_scale_tdp_v107 (')
            b = text.index('module cu66_mode_store_v107 (')
            for name, piece in [('cu66_scale_tdp_v107.sv', text[a:b]), ('cu66_mode_store_v107.sv', text[b:])]:
                helper = build / name
                if helper.exists():
                    assert helper.read_text() == piece
                else:
                    helper.write_text(piece)
            p.write_text(text[:a])
            assert p.read_text()+(build/'cu66_scale_tdp_v107.sv').read_text()+(build/'cu66_mode_store_v107.sv').read_text() == text
        shutil.copyfile(vectors, build / 'vectors.txt')
        report['compiled_source_sha256'] = {p.name:sha(p) for p in build.iterdir() if p.is_file()}
        command(['verilator', '--version'], 'version.log', 30)
        assert 'Verilator 5.020' in (out / 'version.log').read_text()
        command(['verilator', '--cc', '--exe', '--build', '-j', '1', '--assert', '-Wall', '--public-flat-rw',
                 '--output-split', '10000', '--output-split-cfuncs', '500', '--language', '1800-2017',
                 '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror', '--top-module', 'admission_probe', '--Mdir', '/work/obj',
                 *['/work/'+name for name in ['admission_original.sv', 'admission_candidate.sv', 'cu66_scale_tdp_v107.sv',
                                             'cu66_mode_store_v107.sv', 'admission_probe.sv', 'tb_bounds.cpp']]], 'compile.log', 900)
        assert '%Warning-' not in (out / 'compile.log').read_text()
        report['binary_sha256'] = sha(build / 'obj/Vadmission_probe')
        # Read the unchanged independent replay implementations from snapshots.
        snapshot = out / 'sources'
        sys.path[:0] = [str(snapshot/'scripts/cu66-v100'), str(snapshot/'scripts/cu66-v107/header'), str(snapshot/'scripts/cu66-v107/tables')]
        replay = load_module(snapshot/'scripts/cu66-v107/tables.py', 'v116_frozen_tables')
        for seed in (122501, 122502):
            name = 'simulation-'+str(seed)+'.log'
            command(['/work/obj/Vadmission_probe', '/work/vectors.txt', str(seed)], name, 480, simulation=True)
            rows = [json.loads(line) for line in (out / name).read_text().splitlines()]
            verdict = next(row for row in rows if row.get('type')=='verdict')
            owner=next(row for row in rows if row.get('type')=='v119_mode_bound');assert owner['status']=='TEST_PASS'and owner['cases']==540
            boundary = [row for row in rows if row.get('type') == 'v116_chunk_boundaries']
            assert len(boundary) == 1 and boundary[0]['status'] == 'TEST_PASS' and boundary[0]['cases'] == 25344 and boundary[0]['cancellation_cases'] == 294
            assert verdict['status'] == 'TEST_PASS' and verdict['prepared_edges'] == 348673 and verdict['header_prepared_edges'] == 738933
            assert verdict['scale_prepared_edges'] == 40585 and verdict['mode_prepared_edges'] == 158230
            match=next(row for row in rows if row.get('type')=='v120_header_match_verdict')
            assert match['status']=='TEST_PASS' and match['prepared_full35_cases']==67664 and match['random_full35']==65536 and match['owned_consumes']==4096
            assert match['high32_alias_rejections']>0 and match['true_cases']>0 and match['false_cases']>0 and match['canceled_captures']>0 and match['idle_hold_edges']==135328
            assert match['fixture_priming_edges']>0 and match['natural_packets']==match['natural_nonreset_retries']==36 and match['old_require_checks_removed']==match['added_natural_public_cycles']==0
            assert match['prepared_predicate_contexts_are_natural_packets'] is False
            bounds=next(row for row in rows if row.get('type')=='v122_bounds_verdict')
            assert bounds['status']=='TEST_PASS' and bounds['random_full32_cases']==16384 and bounds['cancellation_cases']==56
            assert bounds['full64_high32_cases']>0 and bounds['uint32_wrap_cases']>0 and bounds['fixture_priming_edges']>0
            assert bounds['added_natural_public_cycles']==bounds['old_require_checks_removed']==0
            assert bounds['prepared_domain_fixtures_are_natural_packets'] is False
            result = dict(bounds=bounds,header_match=match,seed=seed, terminal_verdict=verdict, boundary=boundary[0], owned_mode_bound=owner,
                          coordinate=replay.replay(build/'trace.jsonl', snapshot/vectors.relative_to(ROOT)),
                          quant=replay.quant_replay(build/'trace.jsonl', snapshot/vectors.relative_to(ROOT)),
                          scale=replay.scale_replay(build/'scale-ports.csv'), mode=replay.mode_replay(build/'mode-ports.jsonl', seed))
            report['runs'].append(result)
            for stem in ('trace.jsonl', 'scale-ports.csv', 'mode-ports.jsonl', 'match-natural-trace.jsonl'):
                (build / stem).rename(build / (str(seed)+'-'+stem))
            persist()
        assert report['source_sha256'] == {str(p.relative_to(ROOT)):sha(p) for p in files}, 'sources changed during run'
        assert all(sha(out/'sources'/p.relative_to(ROOT))==sha(p) for p in files), 'snapshot copy mismatch'
        report.update(status='PASS', frozen_after_focused_PASS=True)
    except BaseException as exc:
        report.update(status='FAIL', error_class=type(exc).__name__, error=str(exc))
        raise
    finally:
        for path in sorted([*build.glob('*.jsonl'), *build.glob('*.csv')]):
            with path.open('rb') as source, (out / (path.name+'.gz')).open('wb') as dest:
                with gzip.GzipFile(filename='', fileobj=dest, mode='wb', mtime=0) as zipped:
                    shutil.copyfileobj(source, zipped)
        report['wall_seconds'] = time.monotonic()-started
        report['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'results.json'}
        report['artifacts_sha256'] = report['artifact_sha256']
        persist()
        write(AREA / 'results.json', dict(status=report['status'], actual_RTL_run=report['actual_RTL_run'], selected_report=str((out/'results.json').relative_to(ROOT)), selected_report_sha256=sha(out/'results.json')))
        print('V122_BOUNDS_FOCUSED', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
