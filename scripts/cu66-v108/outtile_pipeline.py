#!/usr/bin/env python3
"""Qualify composed outtile+capacity RTL against frozen V107 public/canonical streams."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v108/outtile-pipeline'
PARENT = ROOT / 'experiments/python-gamebub-v107/native/20261108T081254078678Z'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, d):
    p.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n')


def memory():
    m = {x.split(':')[0]: int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
    f = next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '))
    return dict(available_bytes=m['MemAvailable'], psi_full_avg10=float(f.split('avg10=')[1].split()[0]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    args = ap.parse_args()
    parent_inputs = PARENT/'inputs.json'
    parent_recipe = PARENT/'recipe-snapshot/inputs.tcl'
    card = json.loads(parent_inputs.read_text())
    aliases = re.findall(r'\{[^{}]*/snapshot/([^{}]+\.sv)\}', parent_recipe.read_text().split('set include_dirs')[0])
    assert len(aliases) == 17 and len(set(aliases)) == 17
    aliases += ['fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']
    baseline_path = ROOT/'experiments/python-gamebub-v107/threshold-pipeline/results.json'
    assert card['behavioral_qualification']['path'] == str(baseline_path.relative_to(ROOT))
    assert sha(baseline_path) == card['behavioral_qualification']['sha256']
    baseline = json.loads(baseline_path.read_text())
    assert baseline['status'] == 'PASS_EXACT_THRESHOLD_CANONICAL' and baseline['actual_RTL_run']
    baseline_receipt = ROOT/baseline['selected_receipt']
    assert {k:v for k,v in baseline.items() if k != 'selected_receipt'} == json.loads(baseline_receipt.read_text())
    sources = []
    replacements = []
    for alias in aliases:
        meta = card['source_origins'][alias]
        origin = ROOT/meta['path']
        assert sha(origin) == meta['sha256'] == baseline['source_sha256'][meta['path']]
        selected = origin
        if origin.parent.name == 'cu66-v107-count-threshold':
            selected = ROOT/'fpga/experiments/cu66-v108-capacity'/origin.name
            replacements.append(dict(original=str(origin.relative_to(ROOT)), candidate=str(selected.relative_to(ROOT))))
        elif origin.parent.name == 'cu66-v107-idct-reset':
            selected = ROOT/'fpga/experiments/cu66-v108-outtile'/origin.name
            replacements.append(dict(original=str(origin.relative_to(ROOT)), candidate=str(selected.relative_to(ROOT))))
        sources.append(selected)
    assert len(replacements) == 5
    if not args.run:
        print('OUTTILE_CAPACITY_CANONICAL_PREPARED_NOT_RUN', json.dumps(replacements))
        return
    focused_path = ROOT/'experiments/python-gamebub-v108/capacity/results.json'
    focused = json.loads(focused_path.read_text())
    assert focused['status'] == 'PASS' and focused['actual_RTL_run']
    for item in focused['production']:
        assert sha(ROOT/item['path']) == item['sha256']
    for p in sources:
        if p.parent.name == 'cu66-v108-capacity':
            assert sha(p) == focused['source_sha256'][str(p.relative_to(ROOT))]
    outtile_focus_path = ROOT/'experiments/python-gamebub-v108/outtile/results.json'
    capacity_canonical_path = ROOT/'experiments/python-gamebub-v108/capacity-pipeline/results.json'
    outtile_focus = json.loads(outtile_focus_path.read_text())
    capacity_canonical = json.loads(capacity_canonical_path.read_text())
    assert outtile_focus['status'] == 'PASS' and outtile_focus['actual_RTL_run']
    assert capacity_canonical['status'] == 'PASS_EXACT_CAPACITY_CANONICAL' and capacity_canonical['actual_RTL_run']
    idct = ROOT/'fpga/experiments/cu66-v108-outtile/cu66_idct8x8.sv'
    assert idct in sources and sha(idct) == outtile_focus['source_sha256'][str(idct.relative_to(ROOT))]
    for p in sources:
        if p.parent.name == 'cu66-v108-capacity':
            assert sha(p) == capacity_canonical['source_sha256'][str(p.relative_to(ROOT))]
    bench = ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
    packaging_path = ROOT/'fpga/experiments/cu66-v107-tables/packaging.json'
    admission = ROOT/'fpga/experiments/cu66-v107-tables/cs88_admission_v91i2a.sv'
    for unchanged in (bench, packaging_path):
        assert sha(unchanged) == baseline['source_sha256'][str(unchanged.relative_to(ROOT))]
    assert admission in sources
    files = sorted(set(sources + [bench, packaging_path, Path(__file__).resolve(), focused_path, outtile_focus_path, capacity_canonical_path, baseline_path, baseline_receipt, parent_inputs, parent_recipe]))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69')/('v108-outtile-canonical-'+stamp)
    build.mkdir()
    mapped = '/build/'+build.name
    r = dict(schema='v108-outtile-capacity-zero-extra-cycle-canonical-v1', status='FAIL', actual_RTL_run=False,
             baseline_reference=dict(path=str(baseline_receipt.relative_to(ROOT)), sha256=sha(baseline_receipt)),
             baseline_reused_actual_RTL=True, baseline_recompiled_or_rerun=False,
             source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files}, rtl_source_order=[str(p.relative_to(ROOT)) for p in sources],
             inputs=baseline['inputs'], replacements=replacements, seeds=baseline['seeds'], commands=[], runs=[], memory_samples=[],
             newly_executed_candidate_case_profiles=0, newly_executed_candidate_directed_checks=0,
             full_frame_publication=False, hardware_contact=False,
             limits=['Frozen V107 actual RTL control reused; only outtile+capacity candidate newly executed.',
                     'Original assertions, all public events/cycles, invalid outputs, counters and canonical goldens retained.',
                     'Uniform -O1 verification build; no throughput, native timing or hardware inference.'])
    start = time.monotonic()

    def command(argv, name, cap):
        gate = memory()
        assert gate['available_bytes'] >= 8*1024**3 and gate['psi_full_avg10'] < 1, gate
        container = 'gamebub-v108-outtile-canonical-'+stamp.lower()+'-'+str(len(r['commands']))
        cmd = ['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2',
               '--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly',
               '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,'gamebub-cu66-v69-tools:20261105',
               'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record = dict(argv=cmd, timeout_seconds=cap, resource_before=gate)
        r['commands'].append(record)
        began = time.monotonic()
        with (out/name).open('w') as log:
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            high = 0
            while proc.poll() is None:
                sample = dict(command=name, elapsed_seconds=time.monotonic()-began, **memory())
                r['memory_samples'].append(sample)
                high = high+1 if sample['psi_full_avg10'] >= 5 else 0
                if sample['available_bytes'] < 4*1024**3 or high >= 2 or sample['elapsed_seconds'] > cap+20:
                    subprocess.run(['docker','stop','--time','5',container], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                    record['resource_stop'] = sample
                    break
                time.sleep(2)
            record.update(exit_code=proc.wait(timeout=20), wall_seconds=time.monotonic()-began)
        assert record['exit_code'] == 0 and 'resource_stop' not in record, name

    try:
        for p in files:
            target = out/'sources'/p.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
        snapshot = lambda p: str(out/'sources'/p.relative_to(ROOT))
        for item,meta in baseline['inputs'].items():
            source = ROOT/meta['source']
            assert sha(source) == meta['sha256']
            data = gzip.decompress(source.read_bytes()) if source.suffix == '.gz' else source.read_bytes()
            (build/item).write_bytes(data)
            assert sha(build/item) == meta['expanded_sha256']
        pack = json.loads(packaging_path.read_text())
        data = admission.read_bytes()
        assert sha(admission) == pack['production_sha256']
        offsets = [0]+pack['split_byte_offsets']+[len(data)]
        fragments = []
        for i,meta in enumerate(pack['fragments']):
            target = build/meta['filename']
            target.write_bytes(data[offsets[i]:offsets[i+1]])
            assert sha(target) == meta['sha256']
            fragments.append(target)
        assert b''.join(p.read_bytes() for p in fragments) == data
        compiled = [mapped+'/'+fragments[0].name if p == admission else snapshot(p) for p in sources if p.suffix == '.sv']
        compiled += [mapped+'/'+p.name for p in fragments[1:]]
        r['lossless_compile_packaging'] = pack
        command(['verilator','--version'], 'version.log', 30)
        command(['verilator','--cc','--exe','--build','-j','1','--output-split','10000','--output-split-cfuncs','1000',
                 '--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','cs88_pipeline_v91k',
                 '--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),
                 '-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -DELASTIC=1',*compiled,snapshot(bench)],'compile.log',900)
        assert '%Warning-' not in (out/'compile.log').read_text()
        r['binary_sha256'] = sha(build/'obj/Vcs88_pipeline_v91k')
        for reference in baseline['runs']:
            seed = reference['seed']
            prefix = 'candidate-'+str(seed)
            command([mapped+'/obj/Vcs88_pipeline_v91k', mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',
                     str(seed), mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
            verdict = [json.loads(line) for line in (out/(prefix+'-simulation.jsonl')).read_text().splitlines() if '"type":"verdict"' in line.replace(' ', '')]
            assert len(verdict) == 1 and verdict[0]['status'] == 'TEST_PASS' and verdict[0]['cases'] == 22 and verdict[0]['directed_checks'] == 21
            assert sha(out/(prefix+'-simulation.jsonl')) == sha(baseline_receipt.parent/(prefix+'-simulation.jsonl')), 'stdout/events/cycles diverged'
            row = dict(seed=seed, verdict=verdict[0], exact_stdout_events_cycles_and_canonical=True, artifacts={})
            for key,suffix in [('events','-events.jsonl'),('canonical_actual','-canonical.tsv')]:
                path = build/(prefix+suffix)
                meta = reference['artifacts'][key]
                frozen = baseline_receipt.parent/meta['path']
                assert sha(frozen) == meta['sha256']
                assert hashlib.sha256(gzip.decompress(frozen.read_bytes())).hexdigest() == meta['raw_sha256']
                assert sha(path) == meta['raw_sha256'], key
                packed = out/(path.name+'.gz')
                packed.write_bytes(gzip.compress(path.read_bytes(),mtime=0))
                row['artifacts'][key] = dict(path=packed.name, sha256=sha(packed), raw_sha256=sha(path))
            r['runs'].append(row)
            r['actual_RTL_run'] = True
            r['newly_executed_candidate_case_profiles'] += 22
            r['newly_executed_candidate_directed_checks'] += 21
        assert r['source_sha256'] == {str(p.relative_to(ROOT)):sha(p) for p in files}
        r['status'] = 'PASS_EXACT_OUTTILE_CAPACITY_CANONICAL'
    except BaseException as e:
        r['error'] = repr(e)
        raise
    finally:
        r['wall_seconds'] = time.monotonic()-start
        r['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'receipt.json',r)
        write(AREA/'results.json',dict(r, selected_receipt=str((out/'receipt.json').relative_to(ROOT))))
        print('V108_OUTTILE_CAPACITY_CANONICAL',r['status'],out,flush=True)


if __name__ == '__main__':
    main()
