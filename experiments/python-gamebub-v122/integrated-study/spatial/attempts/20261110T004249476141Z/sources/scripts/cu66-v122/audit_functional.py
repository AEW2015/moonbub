#!/usr/bin/env python3
"""Independent read-only audit of V122 focused and composed functional receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / 'experiments/python-gamebub-v122/integration/results.json'
HANDOFF = ROOT / 'experiments/python-gamebub-v121/integration/results.json'
QUEUE_ALIAS = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
QUEUE_CANDIDATE = 'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'
BASELINE_SELECTORS = {
    'spatial': 'spatial',
    'peer': 'peer',
    'parent': 'parent',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def need(ok, message):
    if not ok:
        raise ValueError(message)


def resolve_baseline(meta):
    """Resolve V121 handoff selector entries in their supported wrapper forms."""
    selector = ROOT / meta['path']
    need(sha(selector) == meta['sha256'], 'V121 baseline selector pin mismatch')
    d = load(selector)
    raw_path = d.get('selected_receipt', d.get('selected_report', d.get('path')))
    need(raw_path, 'V121 baseline selector has no receipt')
    raw_path = ROOT / raw_path
    if 'selected_receipt' in d:
        raw = load(raw_path)
        need(raw == {k: v for k, v in d.items() if k != 'selected_receipt'},
             'V121 selected receipt differs from selector')
    elif 'selected_report' in d:
        need(sha(raw_path) == d['selected_report_sha256'], 'V121 selected report hash mismatch')
        raw = load(raw_path)
    else:
        need(sha(raw_path) == d['sha256'], 'V121 selected receipt hash mismatch')
        raw = load(raw_path)
    return selector, raw_path, raw


def resolve_stage(stage):
    selector = ROOT / stage['path']
    need(sha(selector) == stage['sha256'], 'V122 stage selector hash mismatch: ' + stage['path'])
    selection = load(selector)
    pin = stage['receipt']
    receipt = ROOT / pin['path']
    need(sha(receipt) == pin['sha256'], 'V122 receipt hash mismatch: ' + pin['path'])
    raw = load(receipt)
    if 'selected_receipt' in selection:
        need(selection['selected_receipt'] == pin['path'] and
             raw == {k: v for k, v in selection.items() if k != 'selected_receipt'},
             'V122 selected receipt does not match selector')
    elif 'selected_report' in selection:
        need(selection['selected_report'] == pin['path'] and
             selection['selected_report_sha256'] == pin['sha256'],
             'V122 selected report does not match selector')
        if 'source_sha256' in selection:
            need(raw == {k: v for k, v in selection.items()
                         if k not in ('selected_report', 'selected_report_sha256')},
                 'V122 report receipt differs from selector')
    elif 'path' in selection:
        need(selection['path'] == pin['path'] and selection['sha256'] == pin['sha256'],
             'V122 path receipt does not match selector')
    else:
        need(False, 'V122 stage selector does not identify receipt')
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
    commands = [c if isinstance(c, list) else c['argv'] for c in receipt['commands']]
    compiles = [c for c in commands if 'verilator' in c and '--cc' in c]
    need(bool(compiles) and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c for c in compiles), label + ' RTL assertion/warning policy changed')
    executables = [c for c in compiles if '--exe' in c]
    libraries = [c for c in compiles if '--exe' not in c]
    need(bool(executables) and all('-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS')+1] for c in executables), label + ' host warning policy changed')
    need(all('--build' in c and '--top-module' in c and c[c.index('--top-module')+1] == 'v97_forward' for c in libraries), label + ' unexpected generated library build')
    adapters = [c for c in commands if 'g++' in c]
    need(all(all(f in c for f in ('-std=c++17','-O2','-Wall','-Wextra','-Werror')) for c in adapters), label + ' adapter host warning policy changed')
    need((len(libraries) == len(adapters) == 1) if receipt.get('custom_transport_status') else (not libraries and not adapters), label + ' library/adapter inventory changed')
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
            need(meta['path'] == QUEUE_CANDIDATE, label + ' admission queue points to unexpected path')
            changed.append(alias)
        else:
            need(meta == base[alias], label + ' changed non-admission source: ' + alias)
    need(changed == [QUEUE_ALIAS], label + ' is not a single-admission-source composition')
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


def compare_packed(v122_receipt, v122_meta, v121_receipt, v121_meta, label):
    a = payload(v122_receipt.parent / v122_meta['path'], v122_meta.get('raw_sha256'))
    b = payload(v121_receipt.parent / v121_meta['path'], v121_meta.get('raw_sha256'))
    need(a == b, label + ' bytes differ from pinned V121 Source B')
    return {'raw_bytes': len(a), 'raw_sha256': hashlib.sha256(a).hexdigest()}


def compare_spatial(v122_path, v122, v121_path, v121):
    checked = []
    for field, prefix in (('runs', 'candidate'), ('transport_runs', 'transport')):
        new_runs, old_runs = v122.get(field, []), v121.get(field, [])
        need(len(new_runs) == len(old_runs) == 2, 'Unexpected spatial ' + field + ' count')
        old_by_seed = {x['seed']: x for x in old_runs}
        for run in new_runs:
            seed = run['seed']; old = old_by_seed[seed]
            log = f'{prefix}-{seed}-simulation.jsonl'
            new_log = v122_path.parent / log
            old_log = v121_path.parent / log
            need(new_log.read_bytes() == old_log.read_bytes(), prefix + ' stdout differs for seed ' + str(seed))
            streams = {}
            for key in ('events', 'canonical_actual'):
                streams[key] = compare_packed(v122_path, run['artifacts'][key], v121_path,
                                              old['artifacts'][key], prefix + ' ' + str(seed) + ' ' + key)
            checked.append({'kind': prefix, 'seed': seed, 'stdout_sha256': sha(new_log), 'streams': streams})
    return checked


def compare_peer(v122_path, v122, v121_path, v121):
    need(len(v122.get('runs', [])) == len(v121.get('runs', [])) == 2, 'Unexpected peer run count')
    old = {x['seed']: x for x in v121['runs']}; checked = []
    for row in v122['runs']:
        seed = row['seed']; need(row == old[seed], 'Peer verdict differs for seed ' + str(seed))
        prefix = f'peer-{seed}'
        log = v122_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v121_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Peer stdout differs for seed ' + str(seed))
        streams = {}
        for suffix in ('events.jsonl', 'canonical.tsv'):
            name = prefix + '-' + suffix + '.gz'
            streams[suffix] = compare_packed(v122_path, {'path': name}, v121_path,
                                             {'path': name}, prefix + ' ' + suffix)
        checked.append({'seed': seed, 'stdout_sha256': sha(log), 'streams': streams})
    return checked


def compare_parent(v122_path, v122, v121_path, v121):
    key = lambda x: (x['variant'], x['seed'], x['profile'])
    old = {key(x): x for x in v121['runs']}
    need(len(v122.get('runs', [])) == len(v121.get('runs', [])) and len(old) == len(v121['runs']),
         'Parent terminal record inventory differs')
    checked = []
    for run in v122['runs']:
        ident = key(run); control = old[ident]
        for field in ('live_case', 'fences', 'service', 'verdict', 'spatial_pipeline', 'parent_guard'):
            need(run[field] == control[field], 'Parent ' + str(ident) + ' differs in ' + field)
        prefix = f"{run['variant']}-{run['seed']}"
        log = v122_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v121_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Parent stdout differs for ' + str(ident))
        streams = {}
        for suffix in ('events.jsonl', 'actual.tsv', 'hashes.jsonl'):
            streams[suffix] = compare_packed(v122_path, run['artifacts'][suffix], v121_path,
                                             control['artifacts'][suffix], str(ident) + ' ' + suffix)
        checked.append({'variant': ident[0], 'seed': ident[1], 'profile': ident[2],
                        'stdout_sha256': sha(log), 'terminal_fields_exact': True, 'streams': streams})
    return checked


def verify_focused(path, receipt):
    """Check retained raw terminal records independently of runner imports."""
    need(receipt['added_public_cycles'] == receipt['old_require_checks_removed'] == 0,
         'Focused source added cycles or removed checks')
    need(receipt['all_old_require_checks_retained'] is True and
         receipt['candidate_private_comparison_edits'] == receipt['old_private_value_contract_changes'] == 0,
         'Focused private comparisons or old oracle contract changed')
    need(receipt['prepared_fixture_priming_edges_are_natural_cycles'] is False,
         'Prepared fixtures misclassified as natural packets')
    need({r['seed'] for r in receipt['runs']} == {122501,122502} and len(receipt['runs']) == 2,
         'Focused seed inventory changed')
    checked=[]
    fields={'verdict':'terminal_verdict','v119_mode_bound':'owned_mode_bound',
            'v116_chunk_boundaries':'boundary','v120_header_match_verdict':'header_match',
            'v122_bounds_verdict':'bounds'}
    for run in receipt['runs']:
        logfile=path.parent/('simulation-'+str(run['seed'])+'.log')
        rows=[json.loads(line) for line in logfile.read_text().splitlines()]
        for kind,field in fields.items():
            selected=[r for r in rows if r.get('type')==kind]
            need(len(selected)==1 and selected[0]==run[field] and selected[0]['status']=='TEST_PASS',
                 'Focused raw terminal record mismatch: '+kind)
        b=run['bounds'];h=run['header_match'];v=run['terminal_verdict']
        need(b['random_full32_cases']==16384 and b['cancellation_cases']==56 and
             b['full64_high32_cases']>0 and b['uint32_wrap_cases']>0 and b['fixture_priming_edges']>0,
             'Focused full-width/ownership coverage missing')
        need(b['added_natural_public_cycles']==b['old_require_checks_removed']==0 and
             b['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused bounds cycle or fixture contract changed')
        need(h['prepared_full35_cases']==67664 and h['random_full35']==65536 and
             h['owned_consumes']==4096 and h['natural_packets']==h['natural_nonreset_retries']==36 and
             h['high32_alias_rejections']>0 and h['true_cases']>0 and h['false_cases']>0 and
             h['canceled_captures']>0 and h['idle_hold_edges']==135328 and h['fixture_priming_edges']>0 and
             h['added_natural_public_cycles']==h['old_require_checks_removed']==0 and
             h['prepared_predicate_contexts_are_natural_packets'] is False,
             'Inherited header-match coverage or fixture contract changed')
        need(run['boundary']['cases']==25344 and run['boundary']['cancellation_cases']==294 and
             run['owned_mode_bound']['cases']==540 and v['prepared_edges']==348673 and
             v['header_prepared_edges']==738933 and v['scale_prepared_edges']==40585 and
             v['mode_prepared_edges']==158230,
             'Inherited focused oracle coverage changed')
        for field in ('coordinate','quant','scale','mode'):
            need(run[field]['status'].startswith('PASS'),'Focused independent replay failed: '+field)
        checked.append(dict(seed=run['seed'],raw_log_sha256=sha(logfile),
                            terminal_records_exact=len(fields),full_width_bounds=b))
    return checked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--integration', type=Path, default=INTEGRATION)
    ap.add_argument('--output', type=Path, default=ROOT/'experiments/python-gamebub-v122/audit/full-independent.json')
    args = ap.parse_args()
    index_path = args.integration.resolve()
    index = load(index_path)
    need(index['schema'] == 'v122-bounds-functional-composition-v1' and
         index['status'] == 'PASS_V122_BOUNDS_FULL_FUNCTIONAL', 'Integration functional gate is not PASS')
    need(index['all_original_oracles_retained'] is True and index['exact_B_public_cycles'] is True and
         index['assertions_disabled_or_downgraded'] is False, 'Integration contract changed')
    need(sha(HANDOFF) == 'bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689', 'Frozen V121 integration index changed')
    need(index['declared_public_cycle_delta'] == 0, 'Public cycle delta changed')
    handoff = load(HANDOFF)
    need(len(handoff['source_origins']) == 18, 'V121 handoff source map is not 18 files')
    for alias, meta in handoff['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V121 Source B source drift: ' + alias)
    need(len(index['source_origins']) == 18 and set(index['source_origins']) == set(handoff['source_origins']),
         'V122 composition does not map all Source B files')
    changed = []
    for alias, meta in index['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V122 mapped source drift: ' + alias)
        if alias == QUEUE_ALIAS:
            need(meta['path'] == QUEUE_CANDIDATE and meta['sha256'] != handoff['source_origins'][alias]['sha256'],
                 'V122 admission candidate identity mismatch')
            changed.append(alias)
        else:
            need(meta == handoff['source_origins'][alias], 'Unexpected non-admission source change: ' + alias)
    need(changed == [QUEUE_ALIAS], 'V122 changed more than admission source')

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
         'Focused proof is not bound to the selected admission source')
    need(focused_receipt['source_sha256'].get(handoff['source_origins'][QUEUE_ALIAS]['path']) ==
         handoff['source_origins'][QUEUE_ALIAS]['sha256'],
         'Focused proof baseline queue hash differs from Source B')

    focused_checked = verify_focused(stage_paths['focused'][1], focused_receipt)
    baseline_receipts = {}
    for name, key in BASELINE_SELECTORS.items():
        _, path, raw = resolve_baseline(handoff['stages'][key])
        src_count, art_count = verify_closure(path, raw, 'V121 Source B ' + name)
        baseline_receipts[name] = (path, raw)
        closure['V121_' + name] = {'sources': src_count, 'artifacts': art_count}

    spatial = compare_spatial(stage_paths['spatial'][1], stage_receipts['spatial'],
                              *baseline_receipts['spatial'])
    peer = compare_peer(stage_paths['peer'][1], stage_receipts['peer'], *baseline_receipts['peer'])
    parent = compare_parent(stage_paths['parent'][1], stage_receipts['parent'], *baseline_receipts['parent'])
    result = {
        'schema': 'v122-full-independent-functional-audit-v1',
        'status': 'PASS_INDEPENDENT_V122_FULL_FUNCTIONAL_AUDIT',
        'integration_index': str(index_path.relative_to(ROOT)),
        'integration_index_sha256': sha(index_path),
        'source_B_count': 18,
        'source_B_hashes_match_handoff': True,
        'v122_source_map_count': 18,
        'v122_changed_aliases': changed,
        'stage_source_artifact_closure': closure,
        'focused_independent_raw_terminal_checks': focused_checked,
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
        print('V122_FUNCTIONAL_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
