#!/usr/bin/env python3
"""Root-only V117 LIVE parent byte/row control with independently checked bytes."""
import argparse
import collections
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

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT/'fpga/experiments/cu66-v117-live-guard'
AREA = ROOT/'experiments/python-gamebub-v129/integrated-study/live-guard'
SELECT = ROOT/'experiments/python-gamebub-v129/integrated-study/spatial/results.json'
ROW = ROOT/'fpga/experiments/cu66-v116-rowjoin/cu66_row_write_hash_join_v91l.sv'
ROW_PROOF = ROOT/'experiments/python-gamebub-v116/rowjoin/results.json'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def rel(path):
    return str(path.relative_to(ROOT))


def write(path, obj):
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')
    temp.replace(path)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_derivation():
    derivation = load(SRC/'derivation.json')
    for record in derivation['sources']:
        old, new = ROOT/record['source'], ROOT/record['candidate']
        assert sha(old) == record['source_sha256'] and sha(new) == record['candidate_sha256']
        assert (SRC/('frozen_'+old.name)).read_bytes() == old.read_bytes()
        text = old.read_text()
        for edit in record['edits']:
            assert text.count(edit['before']) == 1
            text = text.replace(edit['before'], edit['after'], 1)
        assert text == new.read_text()
        for edit in reversed(record['edits']):
            assert text.count(edit['after']) == 1
            text = text.replace(edit['after'], edit['before'], 1)
        assert text == old.read_text()
        if old.suffix == '.cpp':
            old_checks = collections.Counter(re.findall(r'need\(.*?\);', old.read_text(), re.S))
            new_checks = collections.Counter(re.findall(r'need\(.*?\);', new.read_text(), re.S))
            assert not old_checks-new_checks, list((old_checks-new_checks).elements())
    frozen = derivation['frozen_derivation']
    assert sha(ROOT/frozen['path']) == frozen['sha256']
    for key in ('validator_job_enum','row_debug_owners'):
        pin = derivation[key]
        assert sha(ROOT/pin['path']) == pin['sha256'], key
    return derivation


def proof(selector, source=None):
    chosen = load(selector)
    assert chosen['status'].startswith('PASS'), selector
    path = ROOT/chosen.get('selected_report', chosen.get('path', ''))
    expected = chosen.get('selected_report_sha256', chosen.get('sha256'))
    assert path.is_file() and expected and sha(path) == expected, selector
    raw = load(path)
    assert raw['status'].startswith('PASS') and raw['actual_RTL_run'] is True
    assert raw.get('assertions_disabled_or_downgraded', False) is False
    for name, expected_hash in raw['source_sha256'].items():
        assert sha(ROOT/name) == expected_hash, name
    artifacts = raw.get('artifact_sha256', raw.get('artifacts_sha256', {}))
    assert artifacts, path
    for name, expected_hash in artifacts.items():
        assert sha(path.parent/name) == expected_hash, name
    commands = [c if isinstance(c, list) else c['argv'] for c in raw['commands']]
    compiles = [c for c in commands if 'verilator' in c and '--cc' in c]
    assert compiles and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c for c in compiles)
    assert all('-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS')+1] for c in compiles)
    if source:
        assert raw['source_sha256'][rel(source)] == sha(source)
    return dict(selector=rel(selector), selector_sha256=sha(selector), path=rel(path), sha256=sha(path)), [selector, path]


def prepare(require_proofs):
    import runpy
    contract=runpy.run_path(str(ROOT/'scripts/cu66-v129/integration/contract.py'));contract['verify']()
    derivation = verify_derivation()
    spatial_path = ROOT/'scripts/cu66-v129/integration/spatial.py'
    spatial = module(spatial_path, 'v117_live_spatial_contract')
    # This reconstructs the actual final18 aliases and both V116 overrides,
    # without requiring a future summary or inventing its SHA during prep.
    base, _, sources, origins, _, packaging, _ = spatial.prepare(require_proofs)
    assert len(sources) == 18 and len(origins) == 18
    selected = None
    pins = {}
    proof_files = contract['files']()
    if require_proofs:
        selected = load(SELECT)
        assert selected['status'] == 'PASS_V129_FINAL_SPATIAL_CANONICAL' and selected['actual_RTL_run'] is True
        raw = ROOT/selected['selected_receipt']
        assert load(raw) == {k:v for k,v in selected.items() if k != 'selected_receipt'}
        assert selected['source_origins'] == origins and selected['rtl_source_order'] == [rel(p) for p in sources]
        assert selected['lossless_compile_packaging'] == load(packaging)
        for name, expected in selected['source_sha256'].items():
            assert sha(ROOT/name) == expected, name
        assert selected['artifact_sha256']
        for name, expected in selected['artifact_sha256'].items():
            assert sha(raw.parent/name) == expected, name
        pins['selected_component'] = dict(path=rel(SELECT), sha256=sha(SELECT), receipt=rel(raw), receipt_sha256=sha(raw))
        proof_files += [SELECT, raw]
        for selector, source in [(ROOT/'experiments/python-gamebub-v129/parser/results.json', ROOT/'fpga/experiments/cu66-v129-parser/br88_rice_elastic.sv'),
                                 (ROOT/'experiments/python-gamebub-v129/scratch-factor/results.json', ROOT/'fpga/experiments/cu66-v129-scratch/packed_scratch_v91g2.sv'),
                                 (ROOT/'experiments/python-gamebub-v127/owner/results.json', ROOT/'fpga/experiments/cu66-v127-owner/cs88_coefficients_v91k.sv'),
                                 (ROOT/'experiments/python-gamebub-v128/focused/results.json', ROOT/'fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv'),
                                 (ROOT/'experiments/python-gamebub-v128/focused/results.json', ROOT/'fpga/experiments/cu66-v128-raw/br88_pipeline_v91h.sv'),
                                 (ROOT/'experiments/python-gamebub-v128/focused/results.json', ROOT/'fpga/experiments/cu66-v128-raw/br88_packet_ingress_sync_v91h.sv'),
                                 (ROOT/'experiments/python-gamebub-v128/focused/results.json', ROOT/'fpga/experiments/cu66-v128-raw/br88_packet_ingress_v91h.sv'),
                                 (ROOT/'experiments/python-gamebub-v128/focused/results.json', ROOT/'fpga/experiments/cu66-v128-padding/cs88_admission_v91i2a.sv'),
                                 (ROOT/'experiments/python-gamebub-v116/rice/results.json', ROOT/'fpga/experiments/cu66-v116-rice/br88_rice_elastic.sv'),
                                 (ROOT/'experiments/python-gamebub-v125/tile/results.json', ROOT/'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'),
                                 (ROW_PROOF, ROW),
                                 (ROOT/'experiments/python-gamebub-v116/control-b/results.json', ROOT/'fpga/experiments/cu66-v116b-control/packed_scratch_v91g2.sv'),
                                 (ROOT/'experiments/python-gamebub-v116/control-b/results.json', ROOT/'fpga/experiments/cu66-v116b-control/br88_pipeline_v91h.sv'),
                                 (ROOT/'experiments/python-gamebub-v116/domain-b/results.json', ROOT/'fpga/experiments/cu66-v116b-domain/cu66_coefficient_elastic.sv'),
                                 (ROOT/'experiments/python-gamebub-v116/record-c/results.json', ROOT/'fpga/experiments/cu66-v116c-record/packed_scratch_v91g2.sv'),
                                 (ROOT/'experiments/python-gamebub-v123/rank/results.json', ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'),
                                 (ROOT/'experiments/python-gamebub-v120/range/results.json', ROOT/'fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv'),
                                 (ROOT/'experiments/python-gamebub-v117/throughput/inverse/results.json', ROOT/'fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv'),
                                 (ROOT/'experiments/python-gamebub-v119/owner/reconstruct/results.json', ROOT/'fpga/experiments/cu66-v119-owner/cu66_reconstruct_stream_v91k.sv')]:
            pin, files = proof(selector, source)
            pins.setdefault('focused_proofs', []).append(pin)
            proof_files += files
    return derivation, selected or base, sources, origins, packaging, pins, proof_files


def memory():
    raw = Path('/proc/meminfo').read_text()
    m = {line.split(':')[0]:int(line.split()[1])*1024 for line in raw.splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(line for line in pressure.splitlines() if line.startswith('full '))
    return dict(available_bytes=m['MemAvailable'], psi_full_avg10=float(full.split('avg10=')[1].split()[0]),
                combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']),
                meminfo=raw, memory_pressure=pressure)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--root-grant')
    ap.add_argument('--variant', choices=('both', 'byte', 'row'), default='both')
    args = ap.parse_args()
    derivation, selected, sources, origins, packaging_path, pins, proof_files = prepare(args.run)
    if not args.run:
        print('V129_LIVE_PARENT_PREPARED_NOT_RUN', sha(SRC/'cs88_live_v91l.sv'), sha(SRC/'tb_keyframe.cpp'))
        return
    assert args.root_grant=='ROOT_V129_PARENT', 'Exact Root heavy-slot grant required'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69')/('v129-cuts-live-guard-'+stamp)
    build.mkdir()
    mapped = '/build/'+build.name
    endpoints = [ROOT/('fpga/experiments/'+name) for name in ('cu66-v69/hash/cu66_sha256_bytes.sv', 'cu66-v69/banks/cu66_frame_bank_control.sv',
                 'cu66-v91l/cs88_validate_publish_v91l.sv', 'cu66-v91l-live/cu66_write_hash_join_v91l.sv')] + [ROW, SRC/'cs88_live_v91l.sv']
    inputs = [ROOT/selected['inputs'][name]['source'] for name in ('cases.tsv','transform_tiles.tsv','canonical_goldens.tsv')]
    inputs += [ROOT/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz']
    support = [ROOT/('experiments/cu66-native-v69/'+name) for name in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
    initial_selector=ROOT/'experiments/python-gamebub-v116/control-c-study/live-parent/results.json'
    initial_pin=load(initial_selector);initial_receipt=ROOT/initial_pin['path']
    assert sha(initial_receipt)==initial_pin['sha256']
    baseline_B_selector=ROOT/'experiments/python-gamebub-v128/integrated-study/live-guard/results.json'
    baseline_B_pin=load(baseline_B_selector);baseline_B_receipt=ROOT/baseline_B_pin['path']
    assert sha(baseline_B_receipt)==baseline_B_pin['sha256']
    baseline_B=load(baseline_B_receipt)
    assert baseline_B['status']=='PASS_V128_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION'
    assert baseline_B['actual_RTL_run'] is True and len(baseline_B['runs'])==4
    for name,expected in baseline_B['source_sha256'].items():assert sha(ROOT/name)==expected,name
    for name,expected in baseline_B['artifact_sha256'].items():assert sha(baseline_B_receipt.parent/name)==expected,name
    proof_files += [baseline_B_selector,baseline_B_receipt]
    files = sorted(set(sources+endpoints+inputs+support+proof_files+[initial_selector,initial_receipt,packaging_path, ROOT/'scripts/cu66-v129/integration/spatial.py',
                       ROOT/'docs/cu66-v116/live-parent.md', ROOT/'experiments/python-gamebub-v116/live-parent/preparation.json',
                       *[p for p in SRC.iterdir() if p.is_file()], Path(__file__).resolve(),
                       *[ROOT/r['source'] for r in derivation['sources']], ROOT/derivation['frozen_derivation']['path']]))
    report = dict(schema='v120-live-byte-and-three-slot-row-ACK-C2-HUD-v1', status='RUNNING', actual_RTL_run=False,
                  simulation_started=False, backend='Verilator 5.020', image_id=IMAGE, root_grant=args.root_grant,
                  source_sha256={rel(p):sha(p) for p in files}, source_origins=origins, rtl_source_order=[rel(p) for p in sources+endpoints],
                  proof_bindings=pins, dynamic_selected_receipt_binding=True, source_derivation=dict(path=rel(SRC/'derivation.json'), sha256=sha(SRC/'derivation.json')),
                  strict_warnings=True, warning_suppression=False, assertions_disabled_or_downgraded=False,
                  all_original_functional_oracles_retained=True, commands=[], runs=[], compile_variants=[],
                  abstract_publication=True, physical_SDRAM=False, hardware_contact=False, hardware_30fps=False,
                  full_parent_routed_timing=False, full_RTL_HUD_decoder=False,
                  service_contract=dict(queue_bound=1, data_bus_bits=16, data_edges='ceil(request_bytes/2)', fast_overhead_edges=2, stalled_overhead_edges='8+uniform_integer[0,8]'),
                  stalled_profile_comparability='Same bounded service rule and RNG seed; different accepted traffic and RNG draw counts do not produce identical cycle traces.',
                  integrated_fault_scope='Wrong-token ACK with retained physical lease, matching drain, clean retry without reset; integrated bus-error injection is not included. Rowjoin focused proof covers its separate unit fault scope.',
                  contract=derivation['contract'],
                  optimization_note='C++ -O2 accelerates host simulation only; no modeled-cycle skipping or FPGA clock claim.',
                  limits=['Actual selected18-source producer and C2/SHA/HUD validation with software HUD decode and abstract finite service.',
                          'Row scheduling differs from byte control; compare canonical accepted bytes, commitments and physical ownership, not exact cycles.',
                          'No physical SDRAM, full-parent routed timing, ESP32 execution, hardware 30fps or validated decode under10ms claim.'])
    started = time.monotonic()

    def persist():
        write(out/'receipt.json', report)

    def command(argv, name, cap, simulation=False):
        import runpy
        launch_gate_wait_samples = []
        gate = runpy.run_path(str(ROOT/'scripts/cu66-v128/integration/resource_gate.py'))['wait_ready'](memory, launch_gate_wait_samples)
        report.setdefault('launch_gate_waits', []).append(dict(command=name, samples=launch_gate_wait_samples))
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined_used_ratio'] < .85, gate
        container = 'gamebub-v129-cuts-live-guard-'+stamp.lower()+'-'+str(len(report['commands']))
        cmd = ['docker','run','--rm','--init','--name',container,'--cpus','2','--memory','8g','--memory-swap','8g','--pids-limit','2048',
               '--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly',
               '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record = dict(argv=cmd, log=name, timeout_seconds=cap, resource_before=gate, simulation=simulation, launch_gate_wait_samples=launch_gate_wait_samples)
        report['commands'].append(record)
        if simulation:
            report['actual_RTL_run'] = True
            report['simulation_started'] = True
        persist()  # Actual run intent is recorded BEFORE the simulation process.
        began = time.monotonic()
        process = None
        high = 0
        try:
            with (out/name).open('w') as log, (out/(name+'.resources.jsonl')).open('w') as samples:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    sample = dict(elapsed_seconds=time.monotonic()-began, **memory())
                    samples.write(json.dumps(sample, sort_keys=True)+'\n')
                    samples.flush()
                    high = high+1 if sample['psi_full_avg10'] >= 5 else 0
                    if sample['available_bytes'] < 4*GIB or high >= 2 or sample['combined_used_ratio'] >= .9 or sample['elapsed_seconds'] > cap+20:
                        record['resource_stop'] = sample
                        raise RuntimeError('LIVE_RESOURCE_STOP_OR_WATCHDOG '+name)
                    time.sleep(1)
                record['exit_code'] = process.wait(timeout=15)
                assert record['exit_code'] == 0, name
        finally:
            if process is not None and process.poll() is None:
                stopped = subprocess.run(['docker','stop','--time','3',container], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
                (out/(name+'.stop.log')).write_bytes(stopped.stdout)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
            record.update(wall_seconds=time.monotonic()-began, resource_after=memory())
            persist()

    def pack(path):
        data = path.read_bytes()
        target = out/(path.name+'.gz')
        target.write_bytes(gzip.compress(data, mtime=0))
        return dict(path=target.name, sha256=sha(target), raw_sha256=hashlib.sha256(data).hexdigest(), rows=len(data.splitlines()))

    try:
        for source in files:
            target = out/'sources'/source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        snap = lambda p:str(out/'sources'/p.relative_to(ROOT))
        expanded = []
        for source in inputs:
            data = gzip.decompress(source.read_bytes()) if source.suffix == '.gz' else source.read_bytes()
            dest = build/(source.stem if source.suffix == '.gz' else source.name)
            dest.write_bytes(data)
            expanded.append(mapped+'/'+dest.name)
            report.setdefault('expanded_input_sha256', {})[dest.name] = sha(dest)
        packaging = load(packaging_path)
        admission = next(p for p in sources if p.name == 'cs88_admission_v91i2a.sv')
        data = admission.read_bytes()
        assert sha(admission) == packaging['production_sha256']
        cuts = [0]+packaging['split_byte_offsets']+[len(data)]
        fragments = []
        for i, fragment in enumerate(packaging['fragments']):
            piece = data[cuts[i]:cuts[i+1]]
            assert len(piece) == fragment['bytes'] and hashlib.sha256(piece).hexdigest() == fragment['sha256']
            target = build/fragment['filename']
            target.write_bytes(piece)
            fragments.append(target)
            dest = out/'compile-sources'/target.name
            dest.parent.mkdir(exist_ok=True)
            shutil.copyfile(target, dest)
        assert b''.join(p.read_bytes() for p in fragments) == data
        report['lossless_compile_packaging'] = packaging
        sv = [mapped+'/'+p.name if p == admission else snap(p) for p in sources if p.suffix == '.sv']
        sv += [mapped+'/'+p.name for p in fragments[1:]]+[snap(p) for p in endpoints]
        command(['verilator','--version'], 'version.log', 30)
        assert 'Verilator 5.020' in (out/'version.log').read_text()
        canonical = next(line.split('\t')[2] for line in (build/'canonical_goldens.tsv').read_text().splitlines() if line.startswith('actual_001\t'))
        case = next(line.split('\t') for line in (build/'cases.tsv').read_text().splitlines() if line.startswith('actual_001\t'))
        validation = next(line.split('\t') for line in (build/'validation.tsv').read_text().splitlines() if line.startswith('c0_f0\t'))
        variants = [('byte',0),('row',1)] if args.variant == 'both' else [(args.variant,int(args.variant == 'row'))]
        for variant, row_writes in variants:
            obj = mapped+'/'+variant+'-obj'
            command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000',
                     '--language','1800-2017','--top-module','cs88_live_v91l',"-GROW_WRITES=1'b"+str(row_writes),'--Mdir',obj,
                     '-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DELASTIC=1 -DROW_WRITES='+str(row_writes),
                     *sv,snap(SRC/'tb_keyframe.cpp')], variant+'-compile.log', 1200)
            assert '%Warning-' not in (out/(variant+'-compile.log')).read_text()
            report['compile_variants'].append(dict(variant=variant, row_writes=row_writes, binary_sha256=sha(build/(variant+'-obj/Vcs88_live_v91l'))))
            for seed, profile in [(116701,0),(116702,1)]:
                prefix = variant+'-'+str(seed)
                command([obj+'/Vcs88_live_v91l',*expanded,str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-actual.tsv',mapped+'/'+prefix+'-hashes.jsonl',str(profile)],
                        prefix+'-simulation.jsonl', 1200, simulation=True)
                rows = [json.loads(line) for line in (out/(prefix+'-simulation.jsonl')).read_text().splitlines()]
                verdict = [r for r in rows if r.get('type') == 'live_parent_verdict']
                live = [r for r in rows if r.get('type') == 'live_case']
                service = [r for r in rows if r.get('type') == 'live_service_verdict']
                fences = [r for r in rows if r.get('type') == 'live_fences']
                assert len(verdict) == len(live) == len(service) == len(fences) == 1
                v, c, s = verdict[0], live[0], service[0]
                f = fences[0]
                expected_requests = 70080 if row_writes else 560640
                assert v['status'] == s['status'] == 'TEST_PASS' and c['status'] == 'PASS'
                assert v['profile'] == profile and v['keyframes'] == 1 and v['candidate_write_requests'] == v['candidate_write_acks'] == expected_requests
                assert v['hash_deliveries'] == 560640 and v['hash_jobs'] == 1025
                assert v['elastic_accepted'] == v['elastic_delivered']+v['elastic_discarded'] and v['elastic_discarded'] <= 1
                assert v['actual_C2_HUD_seal_validation'] and v['abstract_publication']
                assert v['observed_wrong_ack_count'] == 1 and v['directed_checks'] == 2 and v['wrong_ack_owned_write_drained'] and v['clean_retry_without_reset']
                assert s['row_writes'] == row_writes and s['request_bytes'] == (8 if row_writes else 1)
                assert s['expanded_bytes'] == s['acked_bytes'] == 560640 and s['service_queue_bound'] == 1 and s['service_bus_bits'] == 16
                data_per = 4 if row_writes else 1
                assert s['service_data_edges'] == expected_requests*data_per
                assert s['minimum_service_edges'] >= data_per+(8 if profile else 2)
                if not profile:
                    assert s['maximum_service_edges'] == s['minimum_service_edges'] == data_per+2
                assert f['status'] == 'TEST_PASS'
                assert all(f[key] == 518400 for key in ('canonical_producer_bytes','canonical_request_bytes','canonical_successful_ack_bytes','canonical_hash_bytes'))
                assert all(f[key] == 42240 for key in ('hud_request_bytes','hud_successful_ack_bytes','hud_hash_bytes'))
                assert 0 < f['last_canonical_producer_accept'] <= f['last_canonical_successful_ack'] <= f['last_canonical_hash_delivery'] <= f['root_complete']
                assert f['last_canonical_producer_accept'] <= f['reconstruct_done'] <= f['commit']
                assert 0 < f['last_hud_successful_ack'] <= f['last_hud_hash_delivery'] <= f['hud_hash_complete']
                assert f['root_complete'] < f['hud_hash_complete'] < f['seal_complete'] < f['commit'] < f['presentation']
                assert f['hash_kind_counts'] == [508,4,511,1,1]
                assert len(f['slot_occupancy_edges']) == 4 and f['maximum_slots_owned'] <= (3 if row_writes else 1)
                assert len(f['phase_edges']) == len(f['phase_stalls']) == 9
                assert sum(f['slot_occupancy_edges']) == sum(f['phase_edges'])
                assert all(len(stalls) == 5 and all(0 <= count <= count_edges for count in stalls) for count_edges,stalls in zip(f['phase_edges'],f['phase_stalls']))
                assert 0 <= f['triple_phase_edges'] <= sum(f['phase_edges']) and 0 <= f['triple_transfer_edges'] <= sum(f['phase_edges'])
                assert c['root'] == validation[8] and c['hud_sha256'] == validation[7] and c['seal'] == validation[9]
                actual = [line.split('\t') for line in (build/(prefix+'-actual.tsv')).read_text().splitlines()]
                expected = {'actual_001':canonical,'accepted_actual_001':canonical+validation[5],'qcache_actual_001':case[10]}
                assert len(actual) == 3 and {r[0] for r in actual} == set(expected)
                for name, p, hex_data in actual:
                    assert int(p) == profile and hex_data == expected[name]
                hashes = [json.loads(line) for line in (build/(prefix+'-hashes.jsonl')).read_text().splitlines()]
                assert len(hashes) == 1025
                spatial_rows=[row for row in rows if row.get('type')=='live_spatial_pipeline']
                assert len(spatial_rows)==1
                spatial_metrics=spatial_rows[0]
                assert spatial_metrics['status']=='TEST_PASS' and spatial_metrics['maximum_consecutive_inverse_accepts']>=64
                assert spatial_metrics['different_tile_overlap_edges']>0 and spatial_metrics['residual_canonical_overlap_edges']>=spatial_metrics['different_tile_overlap_edges']
                assert spatial_metrics['cycle_skipping'] is False and spatial_metrics['hardware'] is False
                guards=[row for row in rows if row.get('type')=='parent_guard_verdict']
                assert len(guards)==1 and guards[0]['status']=='TEST_PASS'
                guard=guards[0]
                assert guard['checks']>0 and guard['parent_fault_gap_edges']==1 and guard['private_residual_handshakes']<=1
                assert guard['raw_internal_work_blocked_by_observation_masks'] is False and guard['physical_responses_masked'] is False
                assert guard['original_cancel_need_retained'] is True
                assert guard['raw_local_reads']>0 and guard['raw_local_reads']==guard['raw_local_responses']
                # C++ default bool stream emits JSON integer0/1. Require literal integer0; no pending-owner relaxation.
                assert type(guard['raw_local_pending']) is int and guard['raw_local_pending']==0 and guard['private_gap_local_responses']==guard['private_local_reads']
                report['runs'].append(dict(variant=variant, row_writes=row_writes, seed=seed, profile=profile, verdict=v, parent_guard=guard, live_case=c, service=s, fences=f,
                                          spatial_pipeline=spatial_metrics, canonical_and_accepted_bytes_exact=True, actual_hash_job_records=1025,
                                          artifacts={suffix:pack(build/(prefix+'-'+suffix)) for suffix in ('events.jsonl','actual.tsv','hashes.jsonl')}))
                persist()
        initial_selector=ROOT/'experiments/python-gamebub-v116/control-c-study/live-parent/results.json'
        initial_pin=load(initial_selector);initial_receipt=ROOT/initial_pin['path']
        assert sha(initial_receipt)==initial_pin['sha256']
        initial=load(initial_receipt)
        assert initial['status']=='PASS_V116_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION'
        for run in report['runs']:
            control=next(x for x in initial['runs'] if (x['variant'],x['seed'],x['profile'])==(run['variant'],run['seed'],run['profile']))
            # The original exact-cycle comparator remains frozen in V116 and
            # V117A. B explicitly changes accepted/commit/reconstruction scheduling;
            # preserve semantic bytes/digests/physical ownership, measure new cycles.
            for field in ('root','hud_sha256','seal','status'):
                assert run['live_case'][field]==control['live_case'][field], 'B changed canonical commitment: '+field
            for field in ('canonical_producer_bytes','canonical_request_bytes','canonical_successful_ack_bytes','canonical_hash_bytes','hud_request_bytes','hud_successful_ack_bytes','hud_hash_bytes','hash_kind_counts'):
                assert run['fences'][field]==control['fences'][field], 'B changed accepted/ACK/hash accounting: '+field
            for field in ('candidate_write_requests','candidate_write_acks','hash_deliveries','hash_jobs','actual_C2_HUD_seal_validation','observed_wrong_ack_count','wrong_ack_owned_write_drained','clean_retry_without_reset'):
                assert run['verdict'][field]==control['verdict'][field], 'B changed publication/debt semantics: '+field
            for field in ('row_writes','request_bytes','expanded_bytes','acked_bytes','service_queue_bound','service_bus_bits','service_data_edges'):
                assert run['service'][field]==control['service'][field], 'B changed finite memory-service contract: '+field
            run['baseline_C_comparison']=dict(baseline_last_outer_to_commit_cycles=control['live_case']['last_outer_to_commit_cycles'],candidate_last_outer_to_commit_cycles=run['live_case']['last_outer_to_commit_cycles'],cycle_savings=control['live_case']['last_outer_to_commit_cycles']-run['live_case']['last_outer_to_commit_cycles'],exact_cycle_equivalence=False)
        report['baseline_C_semantic_parent_control']=dict(selector=rel(initial_selector),selector_sha256=sha(initial_selector),receipt=rel(initial_receipt),receipt_sha256=sha(initial_receipt),schedule_contract='New II1 inverse accepted/validated/committed frontier and exactly2 reconstruction owners; no modeled-cycle skipping; original all byte/hash/owner/drain checks and independent canonical goldens retained.',frozen_original_cycle_comparator='scripts/cu66-v116/live-c/qualify.py',exact_cycle_equivalence=False)
        # V120 preserves V119's public schedule. Retain the complete independent
        # byte/hash/ACK/fence/golden checks and all six terminal dictionaries.
        for run in report['runs']:
            control=next(x for x in baseline_B['runs'] if (x['variant'],x['seed'],x['profile'])==(run['variant'],run['seed'],run['profile']))
            for field in ('live_case','fences','service','verdict','spatial_pipeline','parent_guard'):
                assert run[field]==control[field], 'V120 changed exact V119 parent record: '+field
            for suffix in ('events.jsonl','actual.tsv','hashes.jsonl'):
                assert run['artifacts'][suffix]['raw_sha256']==control['artifacts'][suffix]['raw_sha256'], 'V120 changed exact V119 accepted event/value/hash cycles: '+suffix
            for field in ('canonical_producer_bytes','canonical_request_bytes','canonical_successful_ack_bytes','canonical_hash_bytes','hud_request_bytes','hud_successful_ack_bytes','hud_hash_bytes','hash_kind_counts'):
                assert run['fences'][field]==control['fences'][field],field
            run['baseline_V119_comparison']=dict(baseline_cycles=control['live_case']['last_outer_to_commit_cycles'],candidate_cycles=run['live_case']['last_outer_to_commit_cycles'],cycle_delta=run['live_case']['last_outer_to_commit_cycles']-control['live_case']['last_outer_to_commit_cycles'])
        report['baseline_B_guard_exact_parent_control']=dict(selector=rel(baseline_B_selector),selector_sha256=sha(baseline_B_selector),receipt=rel(baseline_B_receipt),receipt_sha256=sha(baseline_B_receipt),exact_cycle_equivalence=True)
        report['V119_all_terminal_records_events_and_hash_cycles_exact']=True
        assert report['source_sha256'] == {rel(p):sha(p) for p in files}, 'source changed during LIVE run'
        report.update(status='PASS_V129_SELECTED_COMPONENT_'+'_'.join(name.upper() for name,_ in variants)+'_ACK_C2_HUD_ABSTRACT_PUBLICATION', qualified_variants=[name for name,_ in variants])
    except BaseException as exc:
        report.update(status='FAIL', error_class=type(exc).__name__, error=str(exc))
        raise
    finally:
        for path in build.glob('*'):
            if path.is_file() and path.name.endswith(('-events.jsonl','-actual.tsv','-hashes.jsonl')) and not (out/(path.name+'.gz')).exists():
                pack(path)
        report['wall_seconds'] = time.monotonic()-started
        report['artifact_sha256'] = {str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'receipt.json'}
        persist()
        write(AREA/'results.json', dict(status=report['status'], actual_RTL_run=report['actual_RTL_run'], path=rel(out/'receipt.json'), sha256=sha(out/'receipt.json')))
        print('V129_LIVE_PARENT', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
