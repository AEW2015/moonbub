#!/usr/bin/env python3
"""Finite two-state model of the actual V129 band-end comparison factor."""
import hashlib
import json
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'experiments/python-gamebub-v129/scratch-factor/model.json'
SRC = ROOT / 'fpga/experiments/cu66-v129-scratch/packed_scratch_v91g2.sv'
SEED = 129031
MASK = (1 << 32) - 1


def main():
    subprocess.run(['python3', str(Path(__file__).with_name('prepare.py'))], check=True, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
    rng = random.Random(SEED)
    observed = {'records': 0, 'phase_checks': 0, 'equal': 0, 'unequal': 0,
                'errors_0': 0, 'errors_2': 0, 'errors_4': 0,
                'debug_enqueue_true': 0, 'debug_enqueue_false': 0,
                'full_width_high_bit_differences': 0}
    boundaries = [0, 1, 2, 0x7fffffff, 0x80000000, 0xfffffffe, MASK]
    records = [(w, [w, w ^ (1 << bit), (w+1)&MASK, (w-1)&MASK])
               for w in boundaries for bit in range(32)]
    for _ in range(30000):
        written = rng.getrandbits(32)
        counts = [rng.getrandbits(32) for _ in range(4)]
        counts[rng.randrange(4)] = written
        counts[rng.randrange(4)] = written ^ (1 << rng.randrange(32))
        records.append((written, counts))
    for written, counts in records:
        observed['records'] += 1
        lanes = [written == c for c in counts]
        for phase in range(8):
            old_equal = written == counts[phase & 3]
            new_equal = lanes[phase & 3]
            assert old_equal == new_equal
            observed['phase_checks'] += 1
            observed['equal' if old_equal else 'unequal'] += 1
            if ((written ^ counts[phase & 3]) & 0xffff0000):
                observed['full_width_high_bit_differences'] += 1
            # All original three-way epoch/band/count errors retain priority.
            for epoch_ok, band_ok in ((False, False), (False, True), (True, False), (True, True)):
                old_error = 2 if not epoch_ok else 4 if not band_ok or not old_equal else 0
                new_error = 2 if not epoch_ok else 4 if not band_ok or not new_equal else 0
                assert old_error == new_error
                observed[f'errors_{old_error}'] += 1
                # Exercise original INGEST debug enqueue, including valid and
                # unready contexts; unrelated gates intentionally vary.
                for eligible, coef_valid in ((True, False), (True, True), (False, False)):
                    old_enqueue = eligible and not coef_valid and epoch_ok and band_ok and old_equal
                    new_enqueue = eligible and not coef_valid and epoch_ok and band_ok and new_equal
                    assert old_enqueue == new_enqueue
                    observed['debug_enqueue_true' if old_enqueue else 'debug_enqueue_false'] += 1
    assert all(observed[key] > 0 for key in ('equal','unequal','errors_0','errors_2','errors_4',
               'debug_enqueue_true','debug_enqueue_false','full_width_high_bit_differences'))
    result = dict(schema='v129-scratch-band-count-factor-model-v1', status='PASS_MODEL_ONLY',
                  seed=SEED, counts=observed, actual_RTL_run=False,
                  exhaustive=False, four_state_simulated=False, timing_qualified=False,
                  source=dict(path=str(SRC.relative_to(ROOT)), sha256=hashlib.sha256(SRC.read_bytes()).hexdigest()),
                  model=dict(path=str(Path(__file__).resolve().relative_to(ROOT)),
                             sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
                  expression='written == counts[phase[1:0]] equals (written==counts[0..3])[phase[1:0]]',
                  limitations='Finite sampled two-state arithmetic; no sequential, physical timing or hardware proof.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    assert not OUT.exists(), 'Preserve existing model output'
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
