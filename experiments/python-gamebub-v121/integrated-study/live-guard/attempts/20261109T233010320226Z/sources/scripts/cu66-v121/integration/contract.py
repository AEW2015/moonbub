#!/usr/bin/env python3
"""Read-only Source B identity and reversible adapter checks."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
HANDOFF = ROOT/'experiments/python-gamebub-v120/handoff.json'
HANDOFF_SHA = '1e1bd0f197b8b44e7113f271f2c68092e6800778bbfb3a5027d05f72f9357459'
QUEUE_ALIAS = 'fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
QUEUE = ROOT/'fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv'
QUEUE_SHA = '69b80d1210dcb17ad0eed0ba24cff68e31fbf213d5984b64ffc32ae213ac8e48'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def verify():
    assert sha(HANDOFF) == HANDOFF_SHA
    assert sha(QUEUE) == QUEUE_SHA
    for origin in load(HANDOFF)['source_origins'].values():
        assert sha(ROOT/origin['path']) == origin['sha256'], origin['path']
    recipe = load(HERE/'derivation.json')
    assert recipe['old_oracle_checks_removed'] == 0 and recipe['exact_source_B_cycle_delta'] == 0
    for record in recipe['sources']:
        original, candidate = ROOT/record['original'], ROOT/record['candidate']
        assert sha(original) == record['original_sha256']
        assert sha(candidate) == record['candidate_sha256']
        text = original.read_text()
        for edit in record['edits']:
            assert text.count(edit['before']) == edit['count']
            text = text.replace(edit['before'], edit['after'])
        assert text == candidate.read_text()
        for edit in reversed(record['edits']):
            assert text.count(edit['after']) == edit['count']
            text = text.replace(edit['after'], edit['before'])
        assert text == original.read_text()
    return recipe


def source_map(sources, origins):
    expected = load(HANDOFF)['source_origins']
    assert len(sources) == len(origins) == 18 and set(origins) == set(expected)
    assert {str(path.relative_to(ROOT)) for path in sources} == {origin['path'] for origin in origins.values()}
    for alias, original in expected.items():
        candidate = origins[alias]
        if alias == QUEUE_ALIAS:
            assert candidate == dict(path=str(QUEUE.relative_to(ROOT)), sha256=sha(QUEUE))
        else:
            assert candidate == original, alias
    return origins


def baseline(stage):
    key = {'control-peer':'peer_qualification', 'spatial':'canonical_and_transport', 'live-guard':'guarded_live_parent'}[stage]
    pin = load(HANDOFF)[key]
    selector = ROOT/pin['path']
    assert sha(selector) == pin['sha256']
    chosen = load(selector)
    raw_path = ROOT/chosen.get('selected_receipt', chosen.get('selected_report', chosen.get('path', '')))
    raw = load(raw_path)
    if 'selected_receipt' in chosen:
        assert raw == {k:v for k,v in chosen.items() if k != 'selected_receipt'}
    else:
        assert sha(raw_path) == chosen.get('selected_report_sha256', chosen.get('sha256'))
    assert raw['status'].startswith('PASS') and raw['actual_RTL_run'] is True
    assert not raw.get('assertions_disabled_or_downgraded', False)
    for name, expected in raw['source_sha256'].items():
        assert sha(ROOT/name) == expected, name
    for name, expected in raw['artifact_sha256'].items():
        assert sha(raw_path.parent/name) == expected, name
    return raw_path, raw


def files():
    result = [HANDOFF, HERE/'contract.py', HERE/'prepare.py', HERE/'collect.py', HERE/'derivation.json']
    result += [ROOT/record['original'] for record in load(HERE/'derivation.json')['sources']]
    for stage in ('spatial', 'control-peer', 'live-guard'):
        pin_key = {'control-peer':'peer_qualification', 'spatial':'canonical_and_transport', 'live-guard':'guarded_live_parent'}[stage]
        result.append(ROOT/load(HANDOFF)[pin_key]['path'])
        result.append(baseline(stage)[0])
    return sorted(set(result))


if __name__ == '__main__':
    verify()
    print('V121_INTEGRATION_CONTRACT_PREPARED_NOT_RUN')
