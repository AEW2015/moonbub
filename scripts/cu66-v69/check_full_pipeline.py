#!/usr/bin/env python3
"""Verify the full-corpus gate; a smoke PASS is deliberately insufficient."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v69/integration'


def need(condition, message):
    if not condition:
        raise SystemExit('FAIL ' + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log_check(path, *, seed, shared):
    text = path.read_text()
    need('FAIL' not in text, 'failure marker in ' + path.name)
    rows = [dict((k, int(v)) for k, v in re.findall(r'(\w+)=(\d+)', line))
            for line in text.splitlines() if line.startswith('FRAME_PASS')]
    good = [x for x in rows if x['mode'] == 0]
    need(len(good) == 458, '457 frames plus recovery required')
    corpus = good[:-1]
    need(sum(x['key'] for x in corpus) == 20, '20 keys required')
    need(all(x['tiles'] == 8100 and x['error'] == 0 for x in good), 'tile/error counts')
    need(rows[-1] == good[-1] and good[-1]['key'] == 1, 'final key recovery')
    for mode, code in ((1, 0x12), (2, 0x31), (3, 0x33), (4, 0x50), (7, 0x61)):
        need([x['error'] for x in rows if x['mode'] == mode] == [code], 'specific fault code')
    aborts = (5, 6, 8) if seed else ()
    need(len(rows) == 463 + len(aborts), 'unexpected/missing transaction rows')
    for mode in aborts:
        need([x['error'] for x in rows if x['mode'] == mode] == [0], 'abort drain row')
    match = re.search(r'^PASS actual_frames=457 faults=5 aborts=(\d+) recovery=1 '
                      r'seed=(\d+) clocks=(\d+) shared_bus=(\d+) bus_beats=(\d+) '
                      r'display_reserved=(\d+) refresh_reserved=(\d+)$', text, re.M)
    need(match is not None, 'full terminal marker')
    need(int(match[1]) == len(aborts) and int(match[2]) == seed and
         int(match[4]) == int(shared), 'terminal seed/schedule/abort mismatch')
    need((int(match[5]) > 0) == shared, 'bus service counts inconsistent')
    return corpus


def main():
    result = json.loads((AREA / 'results.json').read_text())
    shared = json.loads((AREA / 'results-shared.json').read_text())
    for path, expected in shared['source_sha256'].items():
        need(digest(ROOT / path) == expected, 'input hash ' + path)
    for command in shared['commands']:
        need(command['exit_code'] == 0, 'command exit')
        need(digest(ROOT / command['log']) == command['sha256'], 'log hash')
    run = shared['runs'][0]
    need(run['actual_frames'] == 457 and run['shared_bus'], 'shared full count/schedule')
    argv = shared['commands'][-1]['argv']
    need(argv[-3:] == ['6901', '9999', '--shared-bus'], 'full shared command flags')
    actual_shared = log_check(AREA / 'seed6901-shared.log', seed=6901, shared=True)
    actual_ideal = log_check(AREA / 'seed0.log', seed=0, shared=False)
    need(actual_shared == run['frames'], 'shared per-frame record mismatch')
    need(actual_ideal == result['ideal_control']['frames'], 'ideal per-frame record mismatch')
    need(digest(AREA / 'seed0.log') == result['ideal_control']['log_sha256'], 'ideal log hash')
    need(result['runs'] == shared['runs'] and
         result['source_sha256'] == shared['source_sha256'], 'aggregate binding')
    need([(x['id'], x['key']) for x in actual_ideal] ==
         [(x['id'], x['key']) for x in actual_shared], 'same ordered corpus required')
    print('FULL_PIPELINE_EVIDENCE_PASS schedules=2 frames_per_schedule=457 '
          'tiles_per_frame=8100 faults_per_schedule=5 shared_abort_drains=3 '
          f'input_pins={len(shared["source_sha256"])}')


if __name__ == '__main__':
    main()
