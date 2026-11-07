#!/usr/bin/env python3
"""Standalone Verilator rANS symbol-kernel verification, not Vivado integration."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import signal
import struct
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'fpga/experiments/cu66-v94-rans-fast'
BASE = ROOT/'fpga/experiments/cu66-v94-rans'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vectors-index', type=Path, default=ROOT/'experiments/python-gamebub-v94/optimized-rtl-vectors/index.json')
    args = parser.parse_args()
    pointer = json.loads(args.vectors_index.read_text())
    manifest = ROOT/pointer['selected_report']
    vectors = manifest.with_name('vectors.bin')
    source = json.loads(manifest.read_text())
    assert source['status'] == 'PASS_INDEPENDENT_RANS_RTL_VECTORS'
    assert sha(vectors) == source['vectors_sha256']
    for name, digest in source['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale vector source', name)
    base_pointer = json.loads((BASE/'results.json').read_text())
    base_report = ROOT/base_pointer['selected_report']
    base = json.loads(base_report.read_text())
    assert base['status'] == 'PASS_RTL_RANS_SYMBOL_KERNEL'
    for name, digest in base['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('base source changed', name)
    for name, digest in base['artifacts_sha256'].items():
        assert sha(base_report.parent/name) == digest, ('base artifact changed', name)
    base_vector_report = ROOT/base['vector_report']
    base_vectors = base_vector_report.with_name('vectors.bin')
    assert vectors.read_bytes() == base_vectors.read_bytes(), 'whole RV94 bytes must match base'
    assert source['case_count'] == 55, 'frozen 55-case control required'
    # Limit the fork to the authorized source changes. The source checks cover
    # RNG, offered inputs, exact q/state/cursor oracle, negative and cancellation
    # acceptance checks, including the qualified cancellation priority fix.
    expected_tb = (BASE/'tb_rans.cpp').read_text().replace('Vrans_symbol', 'Vrans_symbol_fast')
    expected_tb = expected_tb.replace('timing.cycles==4*c.fields.size()+c.bytes.size()+timing.input_stalls+timing.output_stalls', 'timing.cycles==3*c.fields.size()+c.bytes.size()+timing.refills[1]+timing.refills[2]+timing.input_stalls+timing.output_stalls')
    expected_tb = expected_tb.replace('<<timing.output_stalls<<"}\\n";', '<<timing.output_stalls<<",\\\"refill_histogram\\\":["<<timing.refills[0]<<\',\'<<timing.refills[1]<<\',\'<<timing.refills[2]<<"]}\\n";')
    assert (AREA/'tb_rans.cpp').read_text() == expected_tb, 'unapproved TB fork change'
    data = vectors.read_bytes()
    assert data[:4] == b'RV94'
    count, = struct.unpack_from('<I', data, 4)
    assert count == 55
    position = 8
    expected_histograms = []
    for _ in range(count):
        scale, lanes, models, symbols, nrbytes = struct.unpack_from('<5I', data, position)
        position += 20+16+64+nrbytes
        histogram = [0, 0, 0]
        cursor = 0
        for _ in range(symbols):
            q, lane, state, following = struct.unpack_from('<4I', data, position)
            position += 16
            assert 0 <= following-cursor <= 2
            histogram[following-cursor] += 1
            cursor = following
        assert cursor == nrbytes
        expected_histograms.append(histogram)
    assert position == len(data)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), AREA/'rans_symbol_fast.sv', AREA/'tb_rans.cpp', args.vectors_index.resolve(), manifest, vectors, BASE/'results.json', base_report, BASE/'rans_symbol.sv', BASE/'tb_rans.cpp', base_report.parent/'simulation.bin', base_report.parent/'simulation.jsonl']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for path in paths:
        target = out/'sources'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    report = dict(schema='cu66-v94-rans-fast-symbol-rtl-v1', status='FAIL', source_sha256=pins,
                  vector_report=str(manifest.relative_to(ROOT)), vector_report_sha256=sha(manifest),
                  base_control_report=str(base_report.relative_to(ROOT)), base_control_report_sha256=sha(base_report),
                  base_vector_sha256=sha(base_vectors), identical_whole_RV94_inputs=True,
                  default_promotion=False, routed_clock_qualified=False,
                  critical_path_caveat='Combined multiply/add now feeds the lower-bound comparison in UPDATE; no achieved clock or routed timing qualification.',
                  comparison_scope='Only matched mode0 no-stall rows support cycle percentage comparisons. Stalled seeded runs verify correctness only: RNG advances per clock and clocks differ.',
                  backend='standalone Verilator; no Vivado simulator integration or vendor primitives',
                  scope=['Real RTL CDF lookup, multiply/update, byte renormalization, state interleaving and held symbol output.',
                         'Configurable scale8/9/10, states2/4, models1/2; inline model parsing/CRC/literals/coefficient/pixel/HUD/frame publication are outside the RTL boundary.',
                         'One physical FSM. More interleaved states do not imply parallel symbols per clock.',
                         'Clock-edge counts are not achieved FPGA frequency, routed timing or complete decode latency.'],
                  commands=[], hardware_tested=False, full_frame_RTL=False,
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  logical_model_payload_bits=2*16*(11+11), logical_lane_state_bits=4*32,
                  asserted_coverage='C++ self-checking transaction/state/cursor scoreboards; no formal or line/toggle coverage claim')
    started = time.monotonic()
    previous = signal.getsignal(signal.SIGALRM)
    def expired(_signum, _frame):
        raise TimeoutError('finite fast RTL campaign watchdog')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, 600)

    def command(argv, log, timeout):
        entry = dict(argv=argv, log=log, exit_code=None)
        report['commands'].append(entry)
        with (out/log).open('w') as stream:
            result = subprocess.run(argv, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        entry['exit_code'] = result.returncode
        assert result.returncode == 0, (argv, out/log)

    try:
        command(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'verilator-version.log', 30)
        command(['docker', 'exec', CONTAINER, 'g++', '--version'], 'compiler-version.log', 30)
        build = '/build/v94-rans-fast-'+stamp
        files = [out/'sources'/p.relative_to(ROOT) for p in (AREA/'rans_symbol_fast.sv', AREA/'tb_rans.cpp')]
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '--trace', '--assert', '-Wall',
                 '--top-module', 'rans_symbol_fast', '--Mdir', build, '-j', '2',
                 '-CFLAGS', '-std=c++20 -O2 -Wall -Wextra -Werror', *map(str, files)], 'compile.log', 300)
        command(['docker', 'cp', CONTAINER+':'+build+'/Vrans_symbol_fast', str(out/'simulation.bin')], 'copy.log', 30)
        command(['docker', 'exec', CONTAINER, 'timeout', '120', build+'/Vrans_symbol_fast',
                 str(out/'sources'/vectors.relative_to(ROOT)), str(out/'wave')], 'simulation.jsonl', 150)
        events = [json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines() if line.startswith('{')]
        verdicts = [e for e in events if e['type'] == 'verdict']
        cases = [e for e in events if e['type'] == 'case']
        negative = [e for e in events if e['type'] == 'negative']
        recoveries = [e for e in events if e['type'] == 'recovery']
        canceled_config = [e for e in events if e['type'] == 'cancel_config']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['vectors'] == source['case_count'] and len(cases) == 3*source['case_count']
        assert len(negative) == verdicts[0]['negative'] == 8 and len(recoveries) == 3
        assert len(canceled_config) == 2 and all(r['status'] == 'PASS' for r in canceled_config)
        assert all(verdicts[0]['refill_histogram'])
        assert {(r['scale'], r['lanes']) for r in cases} == {(s, n) for s in (8, 9, 10) for n in (2, 4)}
        assert {r['models'] for r in cases} == {1, 2}
        for row in cases:
            histogram = row['refill_histogram']
            assert histogram == expected_histograms[row['case']]
            assert sum(histogram) == row['symbols'] and histogram[1]+2*histogram[2] == row['renorm_bytes']
            assert row['decode_cycles'] == 3*row['symbols']+row['renorm_bytes']+histogram[1]+histogram[2]+row['input_stalls']+row['output_stalls']
            assert row['config_cycles'] == row['models']*16+row['lanes']+1
        paired = []
        base_rows = {(row['case'], row['mode']): row for row in base['rows']}
        for row in cases:
            prior = base_rows[(row['case'], row['mode'])]
            for key in ('case', 'mode', 'seed', 'scale', 'lanes', 'models', 'symbols', 'renorm_bytes', 'config_cycles'):
                assert row[key] == prior[key], ('base row mismatch', key)
            if row['mode'] == 0:
                assert row['input_stalls'] == row['output_stalls'] == prior['input_stalls'] == prior['output_stalls'] == 0
                delta = prior['decode_cycles']-row['decode_cycles']
                assert delta == row['refill_histogram'][0], 'delta differs from zero-refill symbols'
                paired.append(dict(case=row['case'], symbols=row['symbols'], refill_histogram=row['refill_histogram'], config_cycles=row['config_cycles'],
                                   base_decode_cycles=prior['decode_cycles'], fast_decode_cycles=row['decode_cycles'], saved_cycles=delta,
                                   reduction_percent=100*delta/prior['decode_cycles'] if prior['decode_cycles'] else 0))
        assert len(paired) == 55
        baseline_cycles = sum(row['base_decode_cycles'] for row in paired)
        fast_cycles = sum(row['fast_decode_cycles'] for row in paired)
        saved_cycles = sum(row['saved_cycles'] for row in paired)
        assert pins == {p: sha(ROOT/p) for p in pins}, 'executed sources changed'
        for wave in out.glob('*.vcd'):
            wave.with_suffix('.vcd.gz').write_bytes(gzip.compress(wave.read_bytes(), mtime=0))
            wave.unlink()
        report.update(status='PASS_RTL_RANS_SYMBOL_FAST_KERNEL', verdict=verdicts[0], rows=cases,
                      negative_controls=negative, recoveries=recoveries, canceled_configuration=canceled_config,
                      total_symbols=sum(r['symbols'] for r in cases),
                      actual_corpus_symbols=source['actual_symbols']*3,
                      fast_decode_cycles=sum(r['decode_cycles'] for r in cases if r['mode'] == 0),
                      fast_symbols=sum(r['symbols'] for r in cases if r['mode'] == 0),
                      exact_cycle_formula='3*symbols + renorm_bytes + nonzero_refill_symbols + observed_input_stalls + observed_output_stalls',
                      paired_no_stall_rows=paired, paired_no_stall_summary=dict(base_decode_cycles=baseline_cycles, fast_decode_cycles=fast_cycles, saved_cycles=saved_cycles, reduction_percent=100*saved_cycles/baseline_cycles),
                      vector_case_count=source['case_count'], actual_vector_cases=source['actual_case_count'])
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        (AREA/'results.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')
        print('V94_FAST_RTL_REPORT', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
