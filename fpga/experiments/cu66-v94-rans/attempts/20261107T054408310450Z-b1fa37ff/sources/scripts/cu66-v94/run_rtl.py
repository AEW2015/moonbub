#!/usr/bin/env python3
"""Standalone Verilator rANS symbol-kernel verification, not Vivado integration."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'fpga/experiments/cu66-v94-rans'
CONTAINER = 'gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pointer = json.loads((ROOT/'experiments/python-gamebub-v94/rtl-vectors/index.json').read_text())
    manifest = ROOT/pointer['selected_report']
    vectors = manifest.with_name('vectors.bin')
    source = json.loads(manifest.read_text())
    assert source['status'] == 'PASS_INDEPENDENT_RANS_RTL_VECTORS'
    assert sha(vectors) == source['vectors_sha256']
    for name, digest in source['source_sha256'].items():
        assert sha(ROOT/name) == digest, ('stale vector source', name)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    paths = [Path(__file__).resolve(), AREA/'rans_symbol.sv', AREA/'tb_rans.cpp', manifest, vectors]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for path in paths:
        target = out/'sources'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    report = dict(schema='cu66-v94-rans-symbol-rtl-v1', status='FAIL', source_sha256=pins,
                  vector_report=str(manifest.relative_to(ROOT)), vector_report_sha256=sha(manifest),
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
        build = '/build/v94-rans-'+stamp
        files = [out/'sources'/p.relative_to(ROOT) for p in (AREA/'rans_symbol.sv', AREA/'tb_rans.cpp')]
        command(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build', '--trace', '--assert', '-Wall',
                 '--top-module', 'rans_symbol', '--Mdir', build, '-j', '2',
                 '-CFLAGS', '-std=c++20 -O2 -Wall -Wextra -Werror', *map(str, files)], 'compile.log', 300)
        command(['docker', 'cp', CONTAINER+':'+build+'/Vrans_symbol', str(out/'simulation.bin')], 'copy.log', 30)
        command(['docker', 'exec', CONTAINER, 'timeout', '120', build+'/Vrans_symbol',
                 str(out/'sources'/vectors.relative_to(ROOT)), str(out/'wave')], 'simulation.jsonl', 150)
        events = [json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines() if line.startswith('{')]
        verdicts = [e for e in events if e['type'] == 'verdict']
        cases = [e for e in events if e['type'] == 'case']
        negative = [e for e in events if e['type'] == 'negative']
        recoveries = [e for e in events if e['type'] == 'recovery']
        assert len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS'
        assert verdicts[0]['vectors'] == source['case_count'] and len(cases) == 3*source['case_count']
        assert len(negative) == verdicts[0]['negative'] == 8 and len(recoveries) == 3
        assert all(verdicts[0]['refill_histogram'])
        assert {(r['scale'], r['lanes']) for r in cases} == {(s, n) for s in (8, 9, 10) for n in (2, 4)}
        assert {r['models'] for r in cases} == {1, 2}
        for row in cases:
            assert row['decode_cycles'] == 4*row['symbols']+row['renorm_bytes']+row['input_stalls']+row['output_stalls']
            assert row['config_cycles'] == row['models']*16+row['lanes']+1
        assert pins == {p: sha(ROOT/p) for p in pins}, 'executed sources changed'
        for wave in out.glob('*.vcd'):
            wave.with_suffix('.vcd.gz').write_bytes(gzip.compress(wave.read_bytes(), mtime=0))
            wave.unlink()
        report.update(status='PASS_RTL_RANS_SYMBOL_KERNEL', verdict=verdicts[0], rows=cases,
                      negative_controls=negative, recoveries=recoveries,
                      total_symbols=sum(r['symbols'] for r in cases),
                      actual_corpus_symbols=source['actual_symbols']*3,
                      fast_decode_cycles=sum(r['decode_cycles'] for r in cases if r['mode'] == 0),
                      fast_symbols=sum(r['symbols'] for r in cases if r['mode'] == 0),
                      exact_cycle_formula='4*symbols + renorm_bytes + observed_input_stalls + observed_output_stalls',
                      vector_case_count=source['case_count'], actual_vector_cases=source['actual_case_count'])
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        report['wall_seconds'] = time.monotonic()-started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out/'results.json').write_text(json.dumps(report, indent=2)+'\n')
        (AREA/'results.json').write_text(json.dumps(dict(report, selected_report=str((out/'results.json').relative_to(ROOT))), indent=2)+'\n')
        print('V94_RTL_REPORT', report['status'], out, flush=True)


if __name__ == '__main__':
    main()
