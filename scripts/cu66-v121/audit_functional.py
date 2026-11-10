#!/usr/bin/env python3
"""Independent read-only audit of V121 focused and composed functional receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / 'experiments/python-gamebub-v121/integration/results.json'
HANDOFF = ROOT / 'experiments/python-gamebub-v120/handoff.json'
QUEUE_ALIAS = 'fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
QUEUE_CANDIDATE = 'fpga/experiments/cu66-v121-request/byte_refill_queue_v91i2b.sv'
BASELINE_SELECTORS = {
    'spatial': 'canonical_and_transport',
    'peer': 'peer_qualification',
    'parent': 'guarded_live_parent',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def need(ok, message):
    if not ok:
        raise ValueError(message)


def resolve_baseline(meta):
    """Resolve V120 handoff selector entries in their supported wrapper forms."""
    selector = ROOT / meta['path']
    need(sha(selector) == meta['sha256'], 'V120 baseline selector pin mismatch')
    d = load(selector)
    raw_path = d.get('selected_receipt', d.get('selected_report', d.get('path')))
    need(raw_path, 'V120 baseline selector has no receipt')
    raw_path = ROOT / raw_path
    if 'selected_receipt' in d:
        raw = load(raw_path)
        need(raw == {k: v for k, v in d.items() if k != 'selected_receipt'},
             'V120 selected receipt differs from selector')
    elif 'selected_report' in d:
        need(sha(raw_path) == d['selected_report_sha256'], 'V120 selected report hash mismatch')
        raw = load(raw_path)
    else:
        need(sha(raw_path) == d['sha256'], 'V120 selected receipt hash mismatch')
        raw = load(raw_path)
    return selector, raw_path, raw


def resolve_stage(stage):
    selector = ROOT / stage['path']
    need(sha(selector) == stage['sha256'], 'V121 stage selector hash mismatch: ' + stage['path'])
    selection = load(selector)
    pin = stage['receipt']
    receipt = ROOT / pin['path']
    need(sha(receipt) == pin['sha256'], 'V121 receipt hash mismatch: ' + pin['path'])
    raw = load(receipt)
    if 'selected_receipt' in selection:
        need(selection['selected_receipt'] == pin['path'] and
             raw == {k: v for k, v in selection.items() if k != 'selected_receipt'},
             'V121 selected receipt does not match selector')
    elif 'selected_report' in selection:
        need(selection['selected_report'] == pin['path'] and
             selection['selected_report_sha256'] == pin['sha256'],
             'V121 selected report does not match selector')
        if 'source_sha256' in selection:
            need(raw == {k: v for k, v in selection.items()
                         if k not in ('selected_report', 'selected_report_sha256')},
                 'V121 report receipt differs from selector')
    elif 'path' in selection:
        need(selection['path'] == pin['path'] and selection['sha256'] == pin['sha256'],
             'V121 path receipt does not match selector')
    else:
        need(False, 'V121 stage selector does not identify receipt')
    return selector, receipt, raw


def verify_closure(receipt_path, receipt, label):
    need(receipt.get('actual_RTL_run') is True, label + ' lacks actual RTL run')
    need(str(receipt.get('status', '')).startswith('PASS'), label + ' is not PASS')
    need(receipt.get('assertions_disabled_or_downgraded', False) is False,
         label + ' assertion policy changed')
    sources = receipt.get('source_sha256', {})
    need(bool(sources), label + ' has no source hashes')
    for rel, digest in sources.items():
        p = ROOT / rel
        need(p.is_file() and sha(p) == digest, label + ' source hash mismatch: ' + rel)
    artifacts = receipt.get('artifact_sha256', receipt.get('artifacts_sha256', {}))
    need(bool(artifacts), label + ' has no artifact hashes')
    for rel, digest in artifacts.items():
        p = receipt_path.parent / rel
        need(p.is_file() and sha(p) == digest, label + ' artifact hash mismatch: ' + rel)
    return len(sources), len(artifacts)


def source_identity(receipt, label):
    origins = receipt.get('source_origins')
    need(isinstance(origins, dict) and len(origins) == 18, label + ' does not map all 18 RTL sources')
    base = load(HANDOFF)['source_origins']
    need(set(origins) == set(base), label + ' source alias set differs from Source B')
    changed = []
    for alias, meta in origins.items():
        p = ROOT / meta['path']
        need(p.is_file() and sha(p) == meta['sha256'], label + ' mapped source mismatch: ' + alias)
        if alias == QUEUE_ALIAS:
            need(meta['path'] == QUEUE_CANDIDATE, label + ' refill queue points to unexpected path')
            changed.append(alias)
        else:
            need(meta == base[alias], label + ' changed non-refill source: ' + alias)
    need(changed == [QUEUE_ALIAS], label + ' is not a single-refill-source composition')
    return len(origins), changed


def payload(path, expected_raw=None):
    data = Path(path).read_bytes()
    if data[:2] == b'\x1f\x8b':
        raw = gzip.decompress(data)
    else:
        raw = data
    if expected_raw:
        need(hashlib.sha256(raw).hexdigest() == expected_raw, 'Raw stream hash mismatch: ' + str(path))
    return raw


def compare_packed(v121_receipt, v121_meta, v120_receipt, v120_meta, label):
    a = payload(v121_receipt.parent / v121_meta['path'], v121_meta.get('raw_sha256'))
    b = payload(v120_receipt.parent / v120_meta['path'], v120_meta.get('raw_sha256'))
    need(a == b, label + ' bytes differ from pinned V120 Source B')
    return {'raw_bytes': len(a), 'raw_sha256': hashlib.sha256(a).hexdigest()}


def compare_spatial(v121_path, v121, v120_path, v120):
    checked = []
    for field, prefix in (('runs', 'candidate'), ('transport_runs', 'transport')):
        new_runs, old_runs = v121.get(field, []), v120.get(field, [])
        need(len(new_runs) == len(old_runs) == 2, 'Unexpected spatial ' + field + ' count')
        old_by_seed = {x['seed']: x for x in old_runs}
        for run in new_runs:
            seed = run['seed']; old = old_by_seed[seed]
            log = f'{prefix}-{seed}-simulation.jsonl'
            new_log = v121_path.parent / log
            old_log = v120_path.parent / log
            need(new_log.read_bytes() == old_log.read_bytes(), prefix + ' stdout differs for seed ' + str(seed))
            streams = {}
            for key in ('events', 'canonical_actual'):
                streams[key] = compare_packed(v121_path, run['artifacts'][key], v120_path,
                                              old['artifacts'][key], prefix + ' ' + str(seed) + ' ' + key)
            checked.append({'kind': prefix, 'seed': seed, 'stdout_sha256': sha(new_log), 'streams': streams})
    return checked


def compare_peer(v121_path, v121, v120_path, v120):
    need(len(v121.get('runs', [])) == len(v120.get('runs', [])) == 2, 'Unexpected peer run count')
    old = {x['seed']: x for x in v120['runs']}; checked = []
    for row in v121['runs']:
        seed = row['seed']; need(row == old[seed], 'Peer verdict differs for seed ' + str(seed))
        prefix = f'peer-{seed}'
        log = v121_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v120_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Peer stdout differs for seed ' + str(seed))
        streams = {}
        for suffix in ('events.jsonl', 'canonical.tsv'):
            name = prefix + '-' + suffix + '.gz'
            streams[suffix] = compare_packed(v121_path, {'path': name}, v120_path,
                                             {'path': name}, prefix + ' ' + suffix)
        checked.append({'seed': seed, 'stdout_sha256': sha(log), 'streams': streams})
    return checked


def compare_parent(v121_path, v121, v120_path, v120):
    key = lambda x: (x['variant'], x['seed'], x['profile'])
    old = {key(x): x for x in v120['runs']}
    need(len(v121.get('runs', [])) == len(v120.get('runs', [])) and len(old) == len(v120['runs']),
         'Parent terminal record inventory differs')
    checked = []
    for run in v121['runs']:
        ident = key(run); control = old[ident]
        for field in ('live_case', 'fences', 'service', 'verdict', 'spatial_pipeline', 'parent_guard'):
            need(run[field] == control[field], 'Parent ' + str(ident) + ' differs in ' + field)
        prefix = f"{run['variant']}-{run['seed']}"
        log = v121_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v120_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Parent stdout differs for ' + str(ident))
        streams = {}
        for suffix in ('events.jsonl', 'actual.tsv', 'hashes.jsonl'):
            streams[suffix] = compare_packed(v121_path, run['artifacts'][suffix], v120_path,
                                             control['artifacts'][suffix], str(ident) + ' ' + suffix)
        checked.append({'variant': ident[0], 'seed': ident[1], 'profile': ident[2],
                        'stdout_sha256': sha(log), 'terminal_fields_exact': True, 'streams': streams})
    return checked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--integration', type=Path, default=INTEGRATION)
    ap.add_argument('--output', type=Path, default=ROOT/'experiments/python-gamebub-v121/audit/full-independent.json')
    args = ap.parse_args()
    index_path = args.integration.resolve()
    index = load(index_path)
    need(index['schema'] == 'v121-request-functional-composition-v1' and
         index['status'] == 'PASS_V121_REQUEST_FULL_FUNCTIONAL', 'Integration functional gate is not PASS')
    need(index['all_original_oracles_retained'] is True and index['exact_B_public_cycles'] is True and
         index['assertions_disabled_or_downgraded'] is False, 'Integration contract changed')
    handoff = load(HANDOFF)
    need(len(handoff['source_origins']) == 18, 'V120 handoff source map is not 18 files')
    for alias, meta in handoff['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V120 Source B source drift: ' + alias)
    need(len(index['source_origins']) == 18 and set(index['source_origins']) == set(handoff['source_origins']),
         'V121 composition does not map all Source B files')
    changed = []
    for alias, meta in index['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V121 mapped source drift: ' + alias)
        if alias == QUEUE_ALIAS:
            need(meta['path'] == QUEUE_CANDIDATE and meta['sha256'] != handoff['source_origins'][alias]['sha256'],
                 'V121 refill candidate identity mismatch')
            changed.append(alias)
        else:
            need(meta == handoff['source_origins'][alias], 'Unexpected non-refill source change: ' + alias)
    need(changed == [QUEUE_ALIAS], 'V121 changed more than refill source')

    stage_paths = {}
    stage_receipts = {}
    closure = {}
    for name in ('focused', 'spatial', 'peer', 'parent'):
        meta = index['stages'][name]
        selector, receipt_path, receipt = resolve_stage(meta)
        stage_paths[name] = (selector, receipt_path)
        closure[name] = dict(sources=verify_closure(receipt_path, receipt, name)[0],
                             artifacts=verify_closure(receipt_path, receipt, name)[1])
        if name in ('spatial', 'peer', 'parent'):
            n, delta = source_identity(receipt, name)
            need(receipt['source_origins'] == index['source_origins'], name + ' source map differs from integration')
            closure[name]['source_origin_count'] = n
            closure[name]['changed_aliases'] = delta
        stage_receipts[name] = receipt
    focused_receipt = stage_receipts['focused']
    need(focused_receipt['source_sha256'].get(QUEUE_CANDIDATE) ==
         index['source_origins'][QUEUE_ALIAS]['sha256'],
         'Focused proof is not bound to the selected refill source')
    need(focused_receipt['source_sha256'].get(QUEUE_ALIAS) ==
         handoff['source_origins'][QUEUE_ALIAS]['sha256'],
         'Focused proof baseline queue hash differs from Source B')
    focused_audit = ROOT/'experiments/python-gamebub-v121/audit/focused-independent.json'
    need(focused_audit.is_file() and load(focused_audit)['status'] == 'PASS_INDEPENDENT_V121_FOCUSED_AUDIT',
         'Independent focused audit is missing or failed')

    baseline_receipts = {}
    for name, key in BASELINE_SELECTORS.items():
        _, path, raw = resolve_baseline(handoff[key])
        src_count, art_count = verify_closure(path, raw, 'V120 Source B ' + name)
        baseline_receipts[name] = (path, raw)
        closure['V120_' + name] = {'sources': src_count, 'artifacts': art_count}

    spatial = compare_spatial(stage_paths['spatial'][1], stage_receipts['spatial'],
                              *baseline_receipts['spatial'])
    peer = compare_peer(stage_paths['peer'][1], stage_receipts['peer'], *baseline_receipts['peer'])
    parent = compare_parent(stage_paths['parent'][1], stage_receipts['parent'], *baseline_receipts['parent'])
    result = {
        'schema': 'v121-full-independent-functional-audit-v1',
        'status': 'PASS_INDEPENDENT_V121_FULL_FUNCTIONAL_AUDIT',
        'integration_index': str(index_path.relative_to(ROOT)),
        'integration_index_sha256': sha(index_path),
        'source_B_count': 18,
        'source_B_hashes_match_handoff': True,
        'v121_source_map_count': 18,
        'v121_changed_aliases': changed,
        'stage_source_artifact_closure': closure,
        'spatial_source_B_exact_streams': spatial,
        'peer_source_B_exact_streams': peer,
        'parent_source_B_exact_terminal_streams': parent,
        'exact_comparisons': {
            'spatial_stdout_event_and_canonical_streams': len(spatial),
            'peer_stdout_event_and_canonical_streams': len(peer),
            'parent_stdout_and_terminal_stream_sets': len(parent),
        },
        'limits': [
            'Spatial and peer fixture/profile outputs are repeated Source B golden cases, not new gameplay frames.',
            'Parent comparison establishes internal byte/event/hash/terminal equality for the retained abstract fixtures; it does not establish board timing, silicon performance, physical memory behavior, or production publication.',
            'No build, simulation, Docker, or hardware job was started by this audit.',
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(args.output)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('V121_FUNCTIONAL_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
