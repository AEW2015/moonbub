#!/usr/bin/env python3
"""Latency-aware complete canonical comparison of quant-aligned control and elastic candidate."""
import argparse
import datetime
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
sys.dont_write_bytecode=True

ROOT = Path(__file__).resolve().parents[2]
# Read the shared gate without mutating sys.path or colliding with old helpers.
import importlib.util
_gate_spec = importlib.util.spec_from_file_location('v106_shared_gate', ROOT / 'scripts/cu66-v100/run_rtl.py')
_gate = importlib.util.module_from_spec(_gate_spec)
_gate_spec.loader.exec_module(_gate)
resources = _gate.resources
BASELINE = 'eececf35da97c9b14230d464ecde7576cb7840db'
CONTAINER = 'gamebub-cu66-v69-build'
# Load the frozen initial maps by exact file path, avoiding module-name ambiguity.
_parent_spec = importlib.util.spec_from_file_location('v107_quant_control', ROOT / 'scripts/cu66-v107/quant_regress.py')
_parent = importlib.util.module_from_spec(_parent_spec)
_parent_spec.loader.exec_module(_parent)
BASELINE_OVERRIDES = {**_parent.BASELINE_OVERRIDES, **_parent.OVERRIDES['quant-aligned']}
OVERRIDES = {'elastic': {'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv': 'fpga/experiments/cu66-v107-elastic/cs88_pipeline_v91k.sv'}}
ADDITIONAL = ROOT/'fpga/experiments/cu66-v107-elastic/cu66_coefficient_elastic.sv'
LANES = [('elastic','canonical')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def pack(path):
    raw_hash = sha(path)
    target = path.with_suffix(path.suffix + '.gz')
    count = 0
    with path.open('rb') as source, target.open('wb') as dest:
        with gzip.GzipFile(fileobj=dest, mode='wb', filename='', mtime=0) as zipped:
            for line in source:
                if path.suffix == '.jsonl':
                    json.loads(line)
                zipped.write(line)
                count += 1
    require(hashlib.sha256(gzip.decompress(target.read_bytes())).hexdigest() == raw_hash, 'trace compression')
    path.unlink()
    return dict(path=target.name, sha256=sha(target), raw_sha256=raw_hash, records=count)


def compare_semantics(out,seed,cases):
    good={v[0] for v in map(str.split,cases.read_text().splitlines()) if int(v[1])==0}
    grouped={}
    for variant in ('baseline','candidate'):
        streams={}
        for line in (out/(variant+'-'+str(seed)+'-events.jsonl')).open():
            event=json.loads(line)
            if event.get('id') not in good:continue
            key=(event['id'],event.get('memory_profile'),event['type'],event.get('stage'))
            semantic={k:v for k,v in event.items() if k not in ('cycle','first_cycle','last_cycle')}
            streams.setdefault(key,[]).append(semantic)
        grouped[variant]=streams
    require(grouped['baseline'].keys()==grouped['candidate'].keys(),'semantic stream coverage mismatch')
    hashes=[]
    for key,expected in sorted(grouped['baseline'].items(),key=lambda kv:str(kv[0])):
        actual=grouped['candidate'][key];require(expected==actual,'ordered good-frame semantic divergence '+str(key))
        hashes.append({'stream':list(key),'events':len(actual),'sha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    require(len(hashes)>20,'semantic stream coverage floor')
    return {'status':'PASS_ORDERED_SEMANTIC_STREAMS','streams':hashes,'excluded_fields':['cycle','first_cycle','last_cycle'],'bad_frame_policy':'All retained bench goldens/provenance/ownership/order/error/counter/publication checks remain active; incomplete prefixes need not match cycle-dependent lengths.'}

def compare_profiles(out,seed):
    rows={}
    for variant in ('baseline','candidate'):
        rows[variant]={(r['id'],r['memory_profile']):r for r in map(json.loads,(out/(variant+'-'+str(seed)+'-simulation.jsonl')).read_text().splitlines()) if r['type']=='case'}
    require(rows['baseline'].keys()==rows['candidate'].keys(),'case/profile completeness mismatch')
    result=[]
    for key,b in rows['baseline'].items():
        c=rows['candidate'][key];require(b['error']==c['error'] and c['status']=='PASS','case outcome mismatch')
        if c['error']==0:
            for field in ('coefficients','core_starts','refill_bytes','child_epochs','frame_epoch'):
                require(b[field]==c[field],'good frame semantic count/identity '+field)
            require(c['elastic']['accepted']==c['elastic']['delivered']==c['coefficients'] and c['elastic']['discarded']==0 and c['elastic']['final_occupied']==0,'good-frame stage exact input conservation')
        else:
            require(c['elastic']['accepted']==c['elastic']['delivered']+c['elastic']['discarded'] and c['elastic']['final_occupied']==0,'bad-frame explicit owner conservation')
        result.append({'id':key[0],'memory_profile':key[1],'error':c['error'],'baseline_cycles':b['cycles'],'candidate_cycles':c['cycles'],'delta_cycles':c['cycles']-b['cycles'],'candidate_behavioral_ms_at100mhz':c['cycles']/100000,'elastic':c['elastic']})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=OVERRIDES, required=True)
    parser.add_argument('--mode', choices=['fresh', 'canonical'], required=True)
    parser.add_argument('--seeds', type=int, nargs=2, default=[107601, 107602])
    args = parser.parse_args()
    require(len(set(args.seeds)) == 2, 'two distinct seeds required')
    mode = args.mode
    require((args.variant, mode) in LANES, 'lane is outside frozen V107 matrix')
    baseline_overrides = {ROOT / old: ROOT / new for old, new in BASELINE_OVERRIDES.items()}
    overrides = {ROOT / old: ROOT / new for old, new in OVERRIDES[args.variant].items()}
    area = ROOT / 'experiments/python-gamebub-v107/elastic-pipeline'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
    out = area / 'attempts' / stamp
    out.mkdir(parents=True, exist_ok=False)
    top = 'cs88_pipeline_v91j' if mode == 'fresh' else 'cs88_pipeline_v91k'
    cases_count, directed_count = (6, 13) if mode == 'fresh' else (22, 21)
    manifest = json.loads((ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json').read_text())
    if mode == 'canonical':
        rtl = [ROOT / name for name in manifest['rtl_sources']]
    else:
        rtl = [ROOT / ('fpga/experiments/' + name) for name in (
            'cu66-v91/br88_rice_elastic.sv', 'cu66-v91b/br88_context.sv',
            'cu66-v91d/br88_packet_ingress.sv', 'cu66-v91g2/packed_scratch_v91g2.sv',
            'cu66-v91h/br88_packet_ingress_v91h.sv', 'cu66-v91h/br88_packet_ingress_sync_v91h.sv',
            'cu66-v91h/br88_pipeline_v91h.sv', 'cu66-v91i2/cs88_admission_v91i2a.sv',
            'cu66-v91i2b/byte_refill_queue_v91i2b.sv', 'cu66-v91i2b/cs88_pipeline_v91i2b.sv',
            'cu66-v69/inverse/cu66_dequant.sv', 'cu66-v69/inverse/cu66_idct8x8.sv',
            'cu66-v91j/cu66_inverse_stream_v91j.sv', 'cu66-v91j/cs88_pipeline_v91j.sv')]
    bench = ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
    header = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
    sources = sorted(set(rtl + [bench, header, ADDITIONAL, ROOT/'scripts/cu66-v107/quant_regress.py', *baseline_overrides.values(), *overrides.values(), Path(__file__).resolve(),
                               ROOT / 'scripts/cu66-v100/run_rtl.py', ROOT / 'scripts/cu66-v106/regress.py',
                               ROOT / 'scripts/cu66-v106/followup/regress.py', ROOT / 'scripts/cu66-v106/final/regress.py', ROOT / 'scripts/cu66-v106/pipeline/regress.py', ROOT / 'scripts/cu66-v106/locality_final/regress.py']))
    report = dict(schema='v107-latency-aware-elastic-canonical-v1', status='FAIL', mode=mode,
                  baseline_revision=BASELINE, baseline_overrides=BASELINE_OVERRIDES, variant=args.variant, top=top, seeds=args.seeds,
                  candidates=[dict(original=str(old.relative_to(ROOT)), path=str(new.relative_to(ROOT)), sha256=sha(new)) for old,new in overrides.items()],
                  backend='Verilator 5.020 behavioral, explicitly retained historical backend',
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  inputs={}, commands=[], runs=[], actual_RTL_run=False,
                  assertions_disabled_or_downgraded=False,
                  limits=['Component simulation only; no formal/mapped-netlist equivalence.',
                          'Declared one-register latency: exact-cycle comparison is replaced by full-tuple UP/DOWN/DISCARD conservation and ordered semantic/golden checks.',
                          'No full HUD/C2/publication, board CDC or routed timing proof.',
                          'No hardware 30fps or under10ms decode qualification.'])
    plain_inputs = []
    start = time.monotonic()

    def command(argv, name, timeout=900):
        if argv[:3] == ['docker', 'exec', CONTAINER] and name not in ('verilator.log', 'compiler.log'):
            argv = argv[:3] + ['timeout', '--signal=TERM', '--kill-after=5s', str(timeout - 10) + 's'] + argv[3:]
        entry = dict(argv=argv, log=name, timeout_seconds=timeout, exit_code=None)
        report['commands'].append(entry)
        began = time.monotonic()
        with (out / name).open('w') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, timeout=timeout)
        entry.update(exit_code=result.returncode, wall_seconds=time.monotonic() - began)
        require(result.returncode == 0, 'command failed ' + name)

    def input_file(source, name):
        dest = out / 'inputs' / source.name
        shutil.copyfile(source, dest)
        if source.suffix == '.gz':
            plain = out / name
            plain.write_bytes(gzip.decompress(dest.read_bytes()))
            plain_inputs.append(plain)
        else:
            plain = out / name
            shutil.copyfile(dest, plain)
        report['inputs'][name] = dict(source=str(source.relative_to(ROOT)),
            sha256=sha(dest), expanded_sha256=sha(plain), rows=len(plain.read_bytes().splitlines()))
        return plain

    try:
        report['resource_gate'] = resources()
        for name, digest in manifest['baseline_rtl_sha256'].items():
            require(sha(ROOT / name) == digest, 'frozen RTL changed ' + name)
        for path in set(rtl + [header]):
            original = subprocess.check_output(['git', 'show', BASELINE + ':' + str(path.relative_to(ROOT))], cwd=ROOT)
            require(hashlib.sha256(original).hexdigest() == sha(path), 'baseline source changed')
        for source in sources:
            dest = out / 'sources' / source.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        (out / 'inputs').mkdir()
        if mode == 'fresh':
            inputs = ROOT / 'experiments/python-gamebub-v99/cs88/rtl-facing-attempts/20261107T1909-new-user-q16'
            cases = input_file(inputs / 'cases.tsv.gz', 'cases.tsv')
            transforms = input_file(inputs / 'transform_tiles.tsv.gz', 'transform_tiles.tsv')
            canonical = None
        else:
            cases = input_file(ROOT / 'experiments/python-gamebub-v91i2/vectors/cases.tsv', 'cases.tsv')
            transforms = input_file(ROOT / 'experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz', 'transform_tiles.tsv')
            canonical = input_file(ROOT / 'experiments/python-gamebub-v91k/vectors/canonical_goldens.tsv.gz', 'canonical_goldens.tsv')
        snapshot = lambda p: str(out / 'sources' / p.relative_to(ROOT))
        with Path('/tmp/gamebub-v107-elastic-pipeline.lock').open('a') as lock:
            # This independent pair can queue behind the already-running V107
            # matrix. Bound only the resource-lock wait; no functional retry.
            lock_deadline = time.monotonic() + 1800
            while True:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= lock_deadline:
                        raise RuntimeError('resource lock did not free within 1800 seconds')
                    time.sleep(1)
            command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'verilator.log', 30)
            command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler.log', 30)
            for variant in ('baseline', 'candidate'):
                resources()
                build = '/build/v107-elastic-pipeline-' + stamp + '-' + mode + '-' + variant
                mapping = dict(baseline_overrides)
                if variant == 'candidate':
                    mapping.update(overrides)
                paths = [mapping.get(p, p) for p in rtl]
                if variant=='candidate':paths.append(ADDITIONAL)
                report.setdefault('compile_source_counts',{})[variant]={'rtl':len(paths),'include_headers':1,'closure_files':len(paths)+1}
                require(len(paths)==len(rtl)+(variant=='candidate') and len(paths)+1==(18 if variant=='candidate' else 17),'explicit extra stage source count')
                available=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))
                require(available>=8*1024*1024,'8GiB available RAM launch gate')
                command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build',
                         '-j', '1', '--output-split','10000','--output-split-cfuncs','1000','--assert', '-Wall', '--public-flat-rw', '--language', '1800-2017',
                         '--top-module', top, '--Mdir', build,
                         '-I' + str(out / 'sources/fpga/experiments/cu66-v69/inverse'),
                         '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror -DELASTIC='+('1' if variant=='candidate' else '0'),
                         *[snapshot(p) for p in paths], snapshot(bench)], 'compile-' + variant + '.log', 300)
                require('%Warning-' not in (out / ('compile-' + variant + '.log')).read_text(), 'strict warning policy')
                command(['docker', 'exec', CONTAINER, 'sha256sum', build + '/V' + top], 'binary-' + variant + '.log', 30)
                report.setdefault('binaries', {})[variant] = dict(path=build + '/V' + top,
                    sha256=(out / ('binary-' + variant + '.log')).read_text().split()[0])
            print('V107_COMPILES_PASS', mode, out, flush=True)
            for seed in args.seeds:
                row = dict(seed=seed, variants={}, equalities={})
                for variant in ('baseline', 'candidate'):
                    resources()
                    prefix = variant + '-' + str(seed)
                    events = out / (prefix + '-events.jsonl')
                    actual = out / (prefix + '-canonical.tsv')
                    argv = ['docker', 'exec', CONTAINER, report['binaries'][variant]['path'], str(cases), str(transforms)]
                    argv += [str(canonical)] if canonical else []
                    argv += [str(seed), str(events)] + ([str(actual)] if canonical else [])
                    command(argv, prefix + '-simulation.jsonl')
                    records = [json.loads(line) for line in (out / (prefix + '-simulation.jsonl')).read_text().splitlines()]
                    verdicts = [r for r in records if r['type'] == 'verdict']
                    require(len(verdicts) == 1, 'single terminal verdict required')
                    verdict = verdicts[0]
                    require(verdict['status'] == 'TEST_PASS' and verdict['seed'] == seed and
                            verdict['cases'] == cases_count and verdict['directed_checks'] == directed_count, 'terminal coverage')
                    require(len([r for r in records if r['type'] == 'case']) == cases_count, 'case completeness')
                    require(all(r.get('status') == 'PASS' for r in records if r['type'] in ('case', 'directed')), 'nonpass row')
                    row['variants'][variant] = dict(verdict=verdict)
                    report['actual_RTL_run'] = True
                for key, suffix in [('canonical', '-canonical.tsv')]:
                    row['equalities'][key] = sha(out / ('baseline-' + str(seed) + suffix)) == sha(out / ('candidate-' + str(seed) + suffix))
                    require(row['equalities'][key], 'baseline/candidate divergence ' + key)
                row['semantic_streams']=compare_semantics(out,seed,cases)
                row['case_latency']=compare_profiles(out,seed)
                for variant in ('baseline', 'candidate'):
                    prefix = variant + '-' + str(seed)
                    row['variants'][variant]['events'] = pack(out / (prefix + '-events.jsonl'))
                    if canonical:
                        row['variants'][variant]['canonical_actual'] = pack(out / (prefix + '-canonical.tsv'))
                report['runs'].append(row)
        require(report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'sources changed during test')
        report.update(status='PASS', case_profile_runs=cases_count * 4,
                      directed_checks=directed_count * 4,
                      exact_same_seed_canonical_bytes=True,ordered_good_frame_semantic_streams_equal=True,exact_same_seed_transcripts_events_cycles=False)
    except BaseException as error:
        report.update(status='FAIL', error_class=type(error).__name__, error=str(error))
        raise
    finally:
        for path in plain_inputs:
            path.unlink(missing_ok=True)
        for pattern in ('*-events.jsonl', '*-canonical.tsv'):
            for path in out.glob(pattern):
                report.setdefault('partial_artifacts', []).append(pack(path))
        report['wall_seconds'] = time.monotonic() - start
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        (area / 'results.json').write_text(json.dumps(dict(report, selected_report=str((out / 'results.json').relative_to(ROOT))), indent=2) + '\n')
        print('V107_REGRESSION', mode, report['status'], out, flush=True)


if __name__ == '__main__':
    main()
