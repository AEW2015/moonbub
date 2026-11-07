#!/usr/bin/env python3
"""Independently replay retained priority-probe inputs using unsigned32 math."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AREA = ROOT / 'experiments/python-gamebub-v101/scratch'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected(v):
    prefetch, tile, raw, sealed, offer, outstanding, error, reset, abort = v['control']
    cancel = reset or (abort and v['epoch'] == v['abort_epoch'])
    enabled = prefetch and not (tile and not raw) and sealed and not offer and not outstanding and not cancel and error == 0
    valid = segment = address = word = 0

    def miss(band, word_address):
        return not (v['cache_valid'] & (1 << band)) or v['cache_address'][band] != (word_address & 0x3fff0)

    if enabled and v['state'] == 20 and not raw and v['block'] + 1 < v['blocks']:
        word = (32 + (v['block'] + 1) * 2) & 0xffffffff
        if miss(0, word):
            valid, segment, address = 1, 0, word & 0x3fff0
        for band in range(1, 4):
            word = (v['starts'][band] + v['cursors'][band - 1] * 4) & 0xffffffff
            if not valid and v['cursors'][band - 1] < v['counts'][band] and miss(band, word):
                valid, segment, address = 1, band, word & 0x3fff0
    elif enabled and v['state'] == 22 and raw and ((v['block'] * 64 + v['index'] + 1) & 0xffffffff) < ((v['blocks'] * 64) & 0xffffffff):
        word = (32 + ((v['block'] * 64 + v['index'] + 1) & 0xffffffff) * 2) & 0xffffffff
        if miss(0, word):
            valid, segment, address = 1, 0, word & 0x3fff0
    return [valid, segment, address, word]


def main():
    selector = json.loads((AREA / 'probe-results.json').read_text())
    receipt = ROOT / selector['selected_receipt']
    assert sha(receipt) == selector['sha256']
    report = json.loads(receipt.read_text())
    result = {'schema': 'v101-scratch-independent-trace-audit-v1', 'status': 'PASS',
              'auditor': str(Path(__file__).resolve().relative_to(ROOT)),
              'auditor_sha256': sha(Path(__file__)),
              'method': 'Independent Python unsigned32/address/priority replay, separate from the C++ oracle',
              'seed_checks': []}
    total = 0
    for verdict in report['verdicts']:
        path = receipt.parent / f"probe-seed-{verdict['seed']}.jsonl.gz"
        records = [json.loads(line) for line in gzip.decompress(path.read_bytes()).splitlines()]
        assert len(records) == verdict['cases']
        selected = [0] * 4
        for index, record in enumerate(records):
            assert record['case'] == index
            actual = record['actual_and_expected']
            assert expected(record) == actual, (verdict['seed'], index)
            if actual[0]:
                selected[actual[1]] += 1
        assert selected == verdict['selected_segments']
        total += len(records)
        result['seed_checks'].append({'seed': verdict['seed'], 'records_parsed_and_replayed': len(records),
                                      'selected_segments': selected, 'trace': str(path.relative_to(ROOT)), 'sha256': sha(path)})
    frontend = json.loads((AREA / 'frontend-results.json').read_text())
    for directory in [receipt.parent, (ROOT / frontend['selected_receipt']).parent]:
        entries = json.loads((directory / 'artifacts.json').read_text())
        for name, pin in entries.items():
            assert sha(directory / name) == pin['sha256'], (directory, name)
    result['total_replayed_cases'] = total
    (AREA / 'trace-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PASS_INDEPENDENT_PYTHON_TRACE_REPLAY', total)


if __name__ == '__main__':
    main()
