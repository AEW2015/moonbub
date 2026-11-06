#!/usr/bin/env python3
"""Bound reference/residual/output staging from retained V83 group lifetimes."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
RTL = ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def peak(intervals):
    events = []
    for start, finish, size in intervals:
        assert 0 <= start <= finish and size >= 0
        if finish > start:
            events.extend(((start, size), (finish, -size)))
    live = maximum = 0
    for _, change in sorted(events):
        live += change
        assert live >= 0
        maximum = max(maximum, live)
    assert live == 0
    return maximum


def analyze(witness, residual_bytes):
    jobs = witness['workload']['jobs']
    rows = {r['id']:r for r in witness['result']['timeline']}
    groups = witness['workload']['groups']
    tile_count = {}
    reconstruct = {}
    for job in jobs:
        if job['kind'] == 'map_lookup':
            tile_count[job['group']] = tile_count.get(job['group'], 0) + 1
        elif job['kind'] == 'reconstruct':
            reconstruct[job['tile']] = rows[job['id']]['finish']
    categories = dict(output_groups=[], reference_inputs=[], inverse_results=[])
    for index, group in enumerate(groups):
        categories['output_groups'].append((rows[group['start']]['start'], rows[group['release']]['finish'], tile_count[index] * 64))
    for job in jobs:
        if job['kind'] not in ('reference_read', 'inverse'):
            continue
        start = rows[job['id']]['finish']
        end = reconstruct.get(job['tile'], rows[groups[job['group']]['release']]['finish'])
        assert rows[groups[job['group']]['start']]['start'] <= start <= end <= rows[groups[job['group']]['release']]['finish']
        category = 'reference_inputs' if job['kind'] == 'reference_read' else 'inverse_results'
        size = 64 if job['kind'] == 'reference_read' else residual_bytes
        categories[category].append((start, end, size))
    slots = witness['config']['group_slots']
    granularity = witness['workload']['assumptions']['granularity']
    capacity = slots * granularity
    bound = capacity * (64 + residual_bytes + 64)
    combined = peak([interval for values in categories.values() for interval in values])
    peaks = {k:peak(v) for k,v in categories.items()}
    assert peaks['output_groups'] <= capacity * 64
    assert peaks['reference_inputs'] <= capacity * 64
    assert peaks['inverse_results'] <= capacity * residual_bytes
    assert combined <= bound
    return dict(configuration=witness['config']['name'], group_slots=slots,
                maximum_admitted_tiles=capacity, stage_peak_bytes=peaks,
                combined_observed_logical_bytes=combined,
                conservative_static_workspace_bytes=bound,
                output_group_allocation_bytes=capacity * 64)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--campaign', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--verify', action='store_true')
    args = p.parse_args()
    # Use the original 24-bit residual interface, not an assumed 8-bit clipped tile.
    width = re.search(r'output\s+logic\s+\[(\d+):0\]\s+out_tile', RTL.read_text())
    assert width and (int(width[1]) + 1) % (64 * 8) == 0
    residual_bytes = (int(width[1]) + 1) // 8
    assert residual_bytes == 192
    assert peak([(0, 4, 64), (4, 9, 192)]) == 192
    assert peak([(0, 5, 64), (2, 6, 192), (3, 4, 64)]) == 320
    witnesses = sorted(args.campaign.glob('witness-*.json.gz'))
    assert len(witnesses) == 4
    rows = []
    for path in witnesses:
        with gzip.open(path, 'rt') as f:
            witness = json.load(f)
        rows.append(dict(path=str(path.relative_to(ROOT)), sha256=sha(path), **analyze(witness, residual_bytes)))
    result = dict(schema='cu66-v83-workspace-v1', status='PASS', residual_tile_bytes=residual_bytes,
                  source_sha256={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__)), str(RTL.relative_to(ROOT)):sha(RTL)},
                  witnesses=rows,
                  allocation_scope='Logical reference-input, signed24 inverse-result and output-group storage for admitted tiles only.',
                  limits=['Four retained native witnesses only for observed peaks; all campaign group rings constrain the conservative allocation bound.',
                          'Reference COPY bytes retained to group release conservatively even if output buffer could alias them.',
                          'Does not include coefficients, dequant staging, inverse working registers, descriptor queues, RAM rounding, hash/context/control, entropy or transport state.',
                          'Python DAG stores many future task descriptors; a hardware implementation needs bounded streaming descriptor/ready state, not this full software graph.',
                          'No RAM-port, FIFO-handshake, physical fit or timing proof.'])
    if args.verify:
        assert json.loads(args.output.read_text()) == result
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('V83_WORKSPACE_PASS witnesses=4 residual_bytes=192 static_four_group_bytes=20480')


if __name__ == '__main__':
    main()
