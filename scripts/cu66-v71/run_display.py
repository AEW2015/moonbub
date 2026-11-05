#!/usr/bin/env python3
"""Bounded native-rate BL8 scanout checks using explicit Verilator backend."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'fpga/experiments/cu66-v71/display'
CONTAINER = os.environ.get('TASK_CONTAINER', 'gamebub-cu66-v69-build')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source = [HERE / 'cu71_scanout.sv', HERE / 'tb_scanout.cpp',
              ROOT / 'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv',
              Path(__file__).resolve(), HERE / 'tb_scanout_control.sv']
    before = {str(p.relative_to(ROOT)): sha(p) for p in source}
    commands = []

    def run(argv, name, timeout=300):
        path = HERE / name
        with path.open('w') as f:
            result = subprocess.run(argv, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT,
                                    timeout=timeout)
        commands.append({'argv': argv, 'exit_code': result.returncode,
                         'log': str(path.relative_to(ROOT)), 'sha256': sha(path)})
        if result.returncode:
            raise RuntimeError(f'{name}: exit {result.returncode}; retained log')
        return path.read_text()

    run(['docker', 'exec', CONTAINER, 'verilator', '--version'], 'tool-version.log')
    run(['docker', 'exec', CONTAINER, 'verilator', '--cc', '--exe', '--build',
         '-j', '1', '--Wall', '--top-module', 'cu71_scanout', '--Mdir', '/build/v71-display',
         '-CFLAGS', '-O2 -std=c++17', *map(str, source[:3:2]), str(source[1])],
        'build-final.log', 600)
    runs = []
    for seed, option in [(0, ''), (7101, ''), (7102, ''),
                         (7101, '--starve'), (7103, '--faults')]:
        log = run(['docker', 'exec', CONTAINER, '/build/v71-display/Vcu71_scanout',
                   str(seed), *([option] if option else [])],
                  f'scanout-seed{seed}{option}.log')
        assert f'PASS seed={seed} asynchronous_clocks_ps=10000,34058' in log
        assert 'FAIL' not in log
        line = next(s for s in log.splitlines() if s.startswith('TEST_PASS_SCANOUT_BURST'))
        counts = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', line)}
        assert counts['compared_pixels'] == 768000 and counts['complete_frames'] == 2
        assert counts['descriptors_presented'] == 2 and counts['stale_rejections'] == 1
        assert counts['reply_beats'] == counts['burst_requests'] * 8
        if option == '--starve':
            assert counts['underruns'] == counts['black_lines'] > 0
        else:
            assert counts['underruns'] == counts['black_lines'] == 0
            assert counts['burst_requests'] == 86400 and counts['reply_beats'] == 691200
        assert counts['memory_errors'] == (2 if option == '--faults' else 0)
        assert counts['diagnostic_pulses'] == (3 if option == '--faults' else 1)
        runs.append({'seed': seed, 'mode': option or 'normal', **counts})
    controls = [str(source[0]), str(source[2]), str(source[4])]
    run(['docker', 'exec', CONTAINER, 'iverilog', '-g2012', '-s', 'tb_scanout_control',
         '-o', '/build/v71-display-control.vvp', *controls], 'control-iverilog-build.log')
    control_log = run(['docker', 'exec', CONTAINER, 'vvp', '/build/v71-display-control.vvp'],
                      'control-iverilog.log')
    assert 'TEST_PASS_SCANOUT_CONTROL checks=31 early_last=1 gap_cycles=20 reset_flush=1 orphan_ignored=1' in control_log
    assert 'FAIL' not in control_log and 'FATAL' not in control_log
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in source}, 'source mutated'
    result = {'status': 'PASS', 'backend': 'Verilator 5.020',
              'clock_period_ps': {'memory': 10000, 'pixel': 34058},
              'native_panel_H_total': 541, 'native_panel_V_total': 834,
              'native_panel_refresh_Hz': 1e12 / (34058 * 541 * 834),
              'source_sha256': before, 'commands': commands, 'runs': runs,
              'total_complete_rasters': sum(r['complete_frames'] for r in runs),
              'total_compared_pixels': sum(r['compared_pixels'] for r in runs),
              'not_proven': ['actual SDRAM service or shared arbitration',
                            'physical FPGA timing/resource/CDC signoff',
                            '30 fps decoder or end-to-end stream performance'],
              'independent_control_backend': 'Icarus Verilog 12',
              'control_checks': 31,
              'scope': 'Exact asynchronous LCD pixels, bounded bursts, descriptors, and explicit failure behavior'}
    (HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DISPLAY_BURST_PASS runs=5 complete_rasters=10 compared_pixels=3840000')


if __name__ == '__main__':
    main()
