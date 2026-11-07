#!/usr/bin/env python3
"""Independently replay the selected V103 quant-cell actual-RTL trace."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v103/reconstruct'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selected = AREA / 'results.json'
    summary = json.loads(selected.read_text())
    receipt_path = ROOT / summary['selected_report']
    receipt = json.loads(receipt_path.read_text())
    assert summary['status'] == receipt['status'] == 'PASS'
    assert receipt['actual_RTL_run'] is True
    assert receipt['verification_adapters_preserve_complete_production_body'] is True
    assert receipt['clock_edges'] == 0 and receipt['cases'] == 32768
    assert receipt['strict_warnings'] is True
    assert receipt['assertions_disabled_or_downgraded'] is False
    for name, pin in receipt['artifacts_sha256'].items():
        assert sha(receipt_path.parent / name) == pin, name
    trace = receipt_path.parent / receipt['trace_replay']['path']
    raw = gzip.decompress(trace.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == receipt['trace_replay']['raw_sha256']
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 32768
    boundaries = [0, 89, 90, 179, 180, 269, 270, 5399, 5400, 8189, 8190, 8191]
    for index, row in enumerate(rows):
        plane, tile = divmod(index, 8192)
        assert (row['plane'], row['tile']) == (plane, tile)
        y, x = divmod(tile, 90)
        expected = ((y // 2) * 45 + x // 2) & 2047 if plane == 0 else tile & 2047
        assert row['original'] == row['candidate'] == row['expected'] == expected
    report = {'schema': 'v103-reconstruct-independent-trace-audit-v1',
              'status': 'PASS', 'rows': len(rows), 'clock_edges': 0,
              'receipt': str(receipt_path.relative_to(ROOT)),
              'receipt_sha256': sha(receipt_path), 'trace_sha256': sha(trace),
              'auditor_sha256': sha(Path(__file__).resolve()),
              'oracle': 'Independent row/column quantization-cell coordinates with final unsigned eleven-bit result',
              'boundary_tiles_checked_for_every_plane': boundaries,
              'scope': 'Complete two-state 2-bit-plane by 13-bit-tile function domain. No sequential, mapped-netlist or hardware proof.'}
    (AREA / 'trace-audit.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('PASS_V103_RECONSTRUCT_TRACE', len(rows), 'rows')


if __name__ == '__main__':
    main()
