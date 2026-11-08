#!/usr/bin/env python3
"""Qualify the V112 local-control composition against frozen exact public/canonical streams."""
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
AREA = ROOT / 'experiments/python-gamebub-v112'
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
    ap.add_argument('--variant',choices=('combined',),required=True)
    args = ap.parse_args()
    area = AREA/'canonical'
    parent_inputs = ROOT/'experiments/python-gamebub-v109/native/20261108T121030620057Z/inputs.json'
    parent_receipt = parent_inputs.parent/'receipt.json'
    native = json.loads(parent_receipt.read_text())
    assert sha(parent_inputs) == native['source_manifest_sha256']
    assert native['clock_period_ns']==10.0 and native['clock_loaded_before_synthesis_in_this_run']
    card = json.loads(parent_inputs.read_text())
    order = card['source_order']['rtl_read_order_aliases']
    aliases = order + [n for n in card['source_origins'] if n.endswith('.svh')]
    assert len(aliases) == 18 and len(set(aliases)) == 18
    baseline_path = ROOT/native['source_contract']['canonical_qualification']
    assert sha(baseline_path) == native['source_contract']['canonical_sha256']
    baseline = json.loads(baseline_path.read_text())
    assert baseline['status'] == 'PASS_EXACT_V109_CANONICAL' and baseline['actual_RTL_run']
    baseline_receipt = ROOT/baseline['selected_receipt']
    assert {k:v for k,v in baseline.items() if k != 'selected_receipt'} == json.loads(baseline_receipt.read_text())
    overrides = {}; proof_paths = []
    if args.variant in ('busy','combined'):
        overrides['packed_scratch_v91g2.sv'] = ROOT/'fpga/experiments/cu66-v112-control/packed_scratch_v91g2.sv'
        proof_paths.append(ROOT/'experiments/python-gamebub-v110/cursors/results.json')
    if args.variant in ('fault','combined'):
        overrides.update({n:ROOT/'fpga/experiments/cu66-v110-fault'/n for n in ('cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cs88_pipeline_v91k.sv')})
        proof_paths.append(ROOT/'experiments/python-gamebub-v110/fault/results.json')
    assert args.variant == 'combined', 'Local control experiment composes retained Count baseline and two candidate source bodies'
    overrides['cu66_dequant.sv'] = ROOT/'fpga/experiments/cu66-v110-dequant/cu66_dequant.sv'
    proof_paths.append(ROOT/'experiments/python-gamebub-v110/dequant/results.json')
    overrides['cs88_coefficients_v91k.sv'] = ROOT/'fpga/experiments/cu66-v110-ready/cs88_coefficients_v91k.sv'
    proof_paths.append(ROOT/'experiments/python-gamebub-v110/ready/results.json')
    overrides['br88_rice_elastic.sv'] = ROOT/'fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv'
    proof_paths.append(ROOT/'experiments/python-gamebub-v110/prefix/results.json')
    overrides['br88_packet_ingress_sync_v91h.sv'] = ROOT/'fpga/experiments/cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv'
    proof_paths.append(ROOT/'experiments/python-gamebub-v109/request/results.json')
    overrides['br88_context.sv'] = ROOT/'fpga/experiments/cu66-v110-count-domain/br88_context.sv'
    proof_paths.append(ROOT/'experiments/python-gamebub-v110/count-domain/results.json')
    proof_paths.append(ROOT/'experiments/python-gamebub-v112/control/results.json')
    overrides['cs88_admission_v91i2a.sv'] = ROOT/'fpga/experiments/cu66-v112-control/cs88_admission_v91i2a.sv'
    sources = [];replacements = []
    for alias in aliases:
        meta = card['source_origins'][alias];origin = ROOT/meta['path']
        assert sha(origin) == meta['sha256'] == baseline['source_sha256'][meta['path']]
        selected = overrides.get(origin.name,origin)
        if selected != origin:replacements.append(dict(original=str(origin.relative_to(ROOT)),candidate=str(selected.relative_to(ROOT))))
        sources.append(selected)
    assert len(replacements) == len(overrides)
    if not args.run:
        print('V112_CANONICAL_PREPARED_NOT_RUN',args.variant,json.dumps(replacements));return
    proofs = [json.loads(p.read_text()) for p in proof_paths]
    for proof in proofs:
        assert proof['status'] == 'PASS' and proof['actual_RTL_run']
    for p in overrides.values():
        matches = [q['source_sha256'][str(p.relative_to(ROOT))] for q in proofs if str(p.relative_to(ROOT)) in q['source_sha256']]
        assert matches and all(h == sha(p) for h in matches),str(p)
    bench = ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
    packaging_path = ROOT/'fpga/experiments/cu66-v112-control/packaging.json'
    admission = ROOT/'fpga/experiments/cu66-v112-control/cs88_admission_v91i2a.sv'
    for unchanged in (bench,):
        assert sha(unchanged) == baseline['source_sha256'][str(unchanged.relative_to(ROOT))]
    assert admission in sources
    files = sorted(set(sources + [bench, packaging_path, Path(__file__).resolve(), *proof_paths, baseline_path, baseline_receipt, parent_inputs, parent_receipt]))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = area/'attempts'/stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69')/('v112-control-'+args.variant+'-canonical-'+stamp)
    build.mkdir()
    mapped = '/build/'+build.name
    r = dict(schema='v112-exact-cycle-canonical-v1', variant=args.variant, status='FAIL', actual_RTL_run=False,
             baseline_reference=dict(path=str(baseline_receipt.relative_to(ROOT)), sha256=sha(baseline_receipt)),
             baseline_reused_actual_RTL=True, baseline_recompiled_or_rerun=False,
             source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files}, rtl_source_order=[str(p.relative_to(ROOT)) for p in sources],
             inputs=baseline['inputs'], replacements=replacements, seeds=baseline['seeds'], commands=[], runs=[], memory_samples=[],
             newly_executed_candidate_case_profiles=0, newly_executed_candidate_directed_checks=0,
             full_frame_publication=False, hardware_contact=False,
             limits=['Frozen V109 FETCH actual RTL control reused (it matched V108); only V112 local-control candidate newly executed.',
                     'Original assertions, all public events/cycles, invalid outputs, counters and canonical goldens retained.',
                     'Uniform -O1 verification build; no throughput, native timing or hardware inference.'])
    start = time.monotonic()

    def command(argv, name, cap):
        gate = memory()
        assert gate['available_bytes'] >= 8*1024**3 and gate['psi_full_avg10'] < 1, gate
        container = 'gamebub-v112-control-'+args.variant+'-canonical-'+stamp.lower()+'-'+str(len(r['commands']))
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
        r['status'] = 'PASS_EXACT_V112_CANONICAL'
    except BaseException as e:
        r['error'] = repr(e)
        raise
    finally:
        r['wall_seconds'] = time.monotonic()-start
        r['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'receipt.json',r)
        write(area/'results.json',dict(r, selected_receipt=str((out/'receipt.json').relative_to(ROOT))))
        print('V112_CANONICAL',r['status'],out,flush=True)


if __name__ == '__main__':
    main()
