#!/usr/bin/env python3
"""Independent read-only audit of V124 focused and composed functional receipts."""
import argparse
import collections
import re
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
INTEGRATION = ROOT / 'experiments/python-gamebub-v124/integration/results.json'
HANDOFF = ROOT / 'experiments/python-gamebub-v123/integration/results.json'
PRODUCER_ALIAS = 'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
PRODUCER_CANDIDATE = 'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'
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
    """Resolve V123 handoff selector entries in their supported wrapper forms."""
    selector = ROOT / meta['path']
    need(sha(selector) == meta['sha256'], 'V123 baseline selector pin mismatch')
    d = load(selector)
    raw_path = d.get('selected_receipt', d.get('selected_report', d.get('path')))
    need(raw_path, 'V123 baseline selector has no receipt')
    raw_path = ROOT / raw_path
    if 'selected_receipt' in d:
        raw = load(raw_path)
        need(raw == {k: v for k, v in d.items() if k != 'selected_receipt'},
             'V123 selected receipt differs from selector')
    elif 'selected_report' in d:
        need(sha(raw_path) == d['selected_report_sha256'], 'V123 selected report hash mismatch')
        raw = load(raw_path)
    else:
        need(sha(raw_path) == d['sha256'], 'V123 selected receipt hash mismatch')
        raw = load(raw_path)
    return selector, raw_path, raw


def resolve_stage(stage):
    selector = ROOT / stage['path']
    need(sha(selector) == stage['sha256'], 'V124 stage selector hash mismatch: ' + stage['path'])
    selection = load(selector)
    pin = stage['receipt']
    receipt = ROOT / pin['path']
    need(sha(receipt) == pin['sha256'], 'V124 receipt hash mismatch: ' + pin['path'])
    raw = load(receipt)
    if 'selected_receipt' in selection:
        need(selection['selected_receipt'] == pin['path'] and
             raw == {k: v for k, v in selection.items() if k != 'selected_receipt'},
             'V124 selected receipt does not match selector')
    elif 'selected_report' in selection:
        need(selection['selected_report'] == pin['path'] and
             selection['selected_report_sha256'] == pin['sha256'],
             'V124 selected report does not match selector')
        if 'source_sha256' in selection:
            need(raw == {k: v for k, v in selection.items()
                         if k not in ('selected_report', 'selected_report_sha256')},
                 'V124 report receipt differs from selector')
    elif 'path' in selection:
        need(selection['path'] == pin['path'] and selection['sha256'] == pin['sha256'],
             'V124 path receipt does not match selector')
    else:
        need(False, 'V124 stage selector does not identify receipt')
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
        if alias == PRODUCER_ALIAS:
            need(meta['path'] == PRODUCER_CANDIDATE, label + ' producer source points to unexpected path')
            changed.append(alias)
        else:
            need(meta == base[alias], label + ' changed non-producer source: ' + alias)
    need(changed == [PRODUCER_ALIAS], label + ' is not a single-producer-source composition')
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


def compare_packed(v124_receipt, v124_meta, v123_receipt, v123_meta, label):
    a = payload(v124_receipt.parent / v124_meta['path'], v124_meta.get('raw_sha256'))
    b = payload(v123_receipt.parent / v123_meta['path'], v123_meta.get('raw_sha256'))
    need(a == b, label + ' bytes differ from pinned V123 Source B')
    return {'raw_bytes': len(a), 'raw_sha256': hashlib.sha256(a).hexdigest()}


def compare_spatial(v124_path, v124, v123_path, v123):
    checked = []
    for field, prefix in (('runs', 'candidate'), ('transport_runs', 'transport')):
        new_runs, old_runs = v124.get(field, []), v123.get(field, [])
        need(len(new_runs) == len(old_runs) == 2, 'Unexpected spatial ' + field + ' count')
        old_by_seed = {x['seed']: x for x in old_runs}
        for run in new_runs:
            seed = run['seed']; old = old_by_seed[seed]
            log = f'{prefix}-{seed}-simulation.jsonl'
            new_log = v124_path.parent / log
            old_log = v123_path.parent / log
            need(new_log.read_bytes() == old_log.read_bytes(), prefix + ' stdout differs for seed ' + str(seed))
            streams = {}
            for key in ('events', 'canonical_actual'):
                streams[key] = compare_packed(v124_path, run['artifacts'][key], v123_path,
                                              old['artifacts'][key], prefix + ' ' + str(seed) + ' ' + key)
            checked.append({'kind': prefix, 'seed': seed, 'stdout_sha256': sha(new_log), 'streams': streams})
    return checked


def compare_peer(v124_path, v124, v123_path, v123):
    need(len(v124.get('runs', [])) == len(v123.get('runs', [])) == 2, 'Unexpected peer run count')
    old = {x['seed']: x for x in v123['runs']}; checked = []
    for row in v124['runs']:
        seed = row['seed']; need(row == old[seed], 'Peer verdict differs for seed ' + str(seed))
        prefix = f'peer-{seed}'
        log = v124_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v123_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Peer stdout differs for seed ' + str(seed))
        streams = {}
        for suffix in ('events.jsonl', 'canonical.tsv'):
            name = prefix + '-' + suffix + '.gz'
            streams[suffix] = compare_packed(v124_path, {'path': name}, v123_path,
                                             {'path': name}, prefix + ' ' + suffix)
        checked.append({'seed': seed, 'stdout_sha256': sha(log), 'streams': streams})
    return checked


def compare_parent(v124_path, v124, v123_path, v123):
    key = lambda x: (x['variant'], x['seed'], x['profile'])
    old = {key(x): x for x in v123['runs']}
    need(len(v124.get('runs', [])) == len(v123.get('runs', [])) and len(old) == len(v123['runs']),
         'Parent terminal record inventory differs')
    checked = []
    for run in v124['runs']:
        ident = key(run); control = old[ident]
        for field in ('live_case', 'fences', 'service', 'verdict', 'spatial_pipeline', 'parent_guard'):
            need(run[field] == control[field], 'Parent ' + str(ident) + ' differs in ' + field)
        prefix = f"{run['variant']}-{run['seed']}"
        log = v124_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v123_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Parent stdout differs for ' + str(ident))
        streams = {}
        for suffix in ('events.jsonl', 'actual.tsv', 'hashes.jsonl'):
            streams[suffix] = compare_packed(v124_path, run['artifacts'][suffix], v123_path,
                                             control['artifacts'][suffix], str(ident) + ' ' + suffix)
        checked.append({'variant': ident[0], 'seed': ident[1], 'profile': ident[2],
                        'stdout_sha256': sha(log), 'terminal_fields_exact': True, 'streams': streams})
    return checked


def verify_inherited_bounds(path, receipt):
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


def verify_inherited_rank(path, receipt):
    """Independently bind every retained rank and inherited raw verdict."""
    need(receipt['schema']=='v123-rank-owned-selected-record-exact-pair-v1' and receipt['suite']=='all',
         'Focused rank suite/schema is incomplete')
    need(receipt['original_assertions_retained'] is True and
         receipt['declared_public_cycle_delta']==receipt['pair_skipped_edges']==0,
         'Focused old assertions/cycle contract changed')
    need(receipt['logical_pending_capacity']==1 and receipt['physical_banks']==2,
         'Focused physical/logical ownership contract changed')
    need({r['seed'] for r in receipt['generic_runs']}=={123301,123302} and len(receipt['generic_runs'])==2,
         'Focused generic seed inventory changed')
    need({r['seed'] for r in receipt['caller_runs']}=={123401,123402} and len(receipt['caller_runs'])==2,
         'Focused actual-caller seed inventory changed')
    fields={'v116b_generic_abort_verdict':'verdict','v116c_record_verdict':'record_verdict',
            'v117_ac_verdict':'ac_verdict','v119_spatial_validation_verdict':'spatial_validation',
            'v123_rank_verdict':'rank_verdict','v115_scratch_prepare_verdict':'inherited_prepare',
            'refined_scratch_slot_verdict':'inherited_slot'}
    checked=[]
    for run in receipt['generic_runs']:
        log=path.parent/('generic-'+str(run['seed'])+'.log')
        rows=[json.loads(line) for line in log.read_text().splitlines() if line.startswith('{')]
        for kind,field in fields.items():
            found=[r for r in rows if r.get('type')==kind]
            need(len(found)==1 and found[0]==run[field] and found[0]['status']=='TEST_PASS',
                 'Focused raw terminal record changed: '+kind)
        rank=run['rank_verdict'];spatial=run['spatial_validation'];ac=run['ac_verdict']
        record=run['record_verdict'];old=run['inherited_prepare'];slot=run['inherited_slot'];v=run['verdict']
        need(rank['full32_cases']==106496 and rank['random_full32_cases']==8192 and
             rank['append_overlap_cases']==7680 and rank['phase_mask']==255 and
             rank['index_mask']==rank['threshold_mask']==2**64-1 and rank['high32_cases']>0 and
             rank['good']>0 and rank['bad']>0 and rank['append_captures']>0 and rank['append_kills']>0 and
             rank['fixture_priming_edges']>0 and rank['public_cycle_delta']==rank['error_cycle_delta']==
             rank['pair_skipped_edges']==rank['old_checks_removed']==0 and
             rank['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused full32/all-rank/APPEND ownership coverage changed')
        need(spatial['full32_cases']==489216 and spatial['phase_mask']==255 and
             spatial['output_plan_cases']==360 and spatial['real_prefetch_requests']==spatial['matching_prefetch_responses'] and
             spatial['real_prefetch_requests']>0 and spatial['public_cycle_delta']==spatial['error_cycle_delta']==spatial['pair_skipped_edges']==0,
             'Inherited full32 spatial/physical prefetch coverage changed')
        need(ac['cases']==10496 and ac['cached_signed13_cases']==8192 and
             ac['cached_signed13_good']==ac['cached_signed13_bad']==4096 and ac['offset_mask']==65535 and
             ac['band_mask']==14 and ac['segment_mask']==ac['format_mask']==15 and ac['pair_skipped_edges']==0 and
             ac['hits']==8960 and ac['misses']==ac['same_edge_prefetch_forwards']==ac['response_errors']==
             ac['wrong_owner_cases']==ac['physical_drains']==192 and ac['kill_cases']==768,
             'Inherited selected AC signed-domain/physical-debt coverage changed')
        need(record['coefficient_domain_cases']==1048576 and record['invalid_coefficient_cases']==983031 and
             record['outer_priority_cases']==15 and record['logical_pending_capacity']==1 and
             record['physical_banks']==2 and record['pair_skipped_edges']==0,
             'Inherited record-domain/priority/ownership coverage changed')
        need(old['full_transactions']==72 and old['corrupt_response_cases']==128 and old['read_owner_cases']==4 and
             old['pending_cancel_cases']==old['stale_pending_abort_checks']==12 and
             old['complete_retry_transactions']==24 and old['dc_line_boundary_transactions']==48 and
             old['paired_candidate_extra_edges']==3*old['paired_accepted_descriptors'] and
             old['poisoned_tuples']==old['paired_accepted_descriptors'],
             'Inherited scratch transaction/drain/retry oracle changed')
        need(slot['natural_pending_kills']==slot['same_object_full_retries']==8 and
             slot['private_storage_event_fixtures']==9 and slot['outer_priority_guard_fixtures']==5 and
             slot['ready_bank_hold_edges']==2 and v['prepared_abort_cases']==90 and
             v['foreign_abort_cases']==36 and v['current_or_reset_cases']==54 and
             v['unsolicited_response_error_cases']==24 and v['pair_skipped_edges']==0 and v['physical_pending_abort_cases']==4,
             'Inherited slot/abort/foreign-owner/physical-debt oracle changed')
        checked.append(dict(kind='generic',seed=run['seed'],raw_log_sha256=sha(log),terminal_records_exact=len(fields),rank_coverage=rank))
    for run in receipt['caller_runs']:
        log=path.parent/('caller-'+str(run['seed'])+'.log')
        rows=[json.loads(line) for line in log.read_text().splitlines() if line.startswith('{')]
        need(rows[-1]==run and run['status']=='TEST_PASS' and run['type']=='verdict',
             'Focused actual-caller raw verdict changed')
        cases=[r for r in rows if r.get('type')=='case']
        need(run['configurations']==2 and run['packets']>0 and run['case_rows']==2*run['packets']==len(cases) and
             run['directed_checks']>=50 and run['sync_staging_checks']>0 and run['caller_prepare_checks']==18,
             'Inherited actual-caller natural/abort/staging coverage changed')
        checked.append(dict(kind='caller',seed=run['seed'],raw_log_sha256=sha(log),case_rows=len(cases),terminal_record_exact=True))
    return checked


def verify_focused(path, receipt):
    """Independently verify owner-lane source/fixtures and retained raw verdicts."""
    need(receipt['schema']=='v124-owner-lanes-existing-edge-operands-focused-v1' and
         receipt['added_public_cycles']==0, 'Focused owner schema/cycle contract changed')
    recipe_path=ROOT/'fpga/experiments/cu66-v124-owner/edit-recipes.json'
    need(receipt['source_sha256'].get(str(recipe_path.relative_to(ROOT)))==sha(recipe_path),
         'Focused owner recipe is not source-bound')
    recipe=load(recipe_path)
    need(recipe['added_registers']==recipe['added_public_cycles']==recipe['old_assertions_removed']==
         recipe['old_require_checks_removed']==0, 'Focused owner source added state/cycles or removed checks')
    need(recipe['synthesis_attribute']==dict(name='keep',value='true',exact_target='tile_owner_match[1:0]',
         bit_count=2,other_directives_added=False), 'Focused KEEP scope changed')
    for meta in [recipe['production']]+recipe['adapters']+recipe['fixture_adapters']:
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        need(sha(before)==meta['original_sha256'] and sha(after)==meta['candidate_sha256'],
             'Focused derivation source hash changed')
        text=before.read_text()
        for edit in meta['edits']:
            need(text.count(edit['before'])==1,'Focused forward derivation is ambiguous')
            text=text.replace(edit['before'],edit['after'],1)
        need(text==after.read_text(),'Focused forward source reconstruction failed')
        for edit in reversed(meta['edits']):
            need(text.count(edit['after'])==1,'Focused reverse derivation is ambiguous')
            text=text.replace(edit['after'],edit['before'],1)
        need(text==before.read_text(),'Focused reverse source reconstruction failed')
    checks=lambda text:collections.Counter(re.findall(r'(?:need|require|require_owner)\(.*?\);',text,re.S))
    for meta in recipe['fixture_adapters']:
        need(not checks((ROOT/meta['original']).read_text())-checks((ROOT/meta['candidate']).read_text()),
             'Focused inherited fixture checks were removed')
    for meta in recipe['unchanged']:
        need(sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256'],
             'Focused unchanged verification source drifted')
    original=(ROOT/recipe['production']['original']).read_text()
    candidate=(ROOT/recipe['production']['candidate']).read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):
        need(block in candidate,'Focused original RTL assertion block changed')
    attrs=lambda text:collections.Counter((re.sub(r'\s+',' ',a).strip(),re.sub(r'\s+',' ',d).strip())
          for a,d in re.findall(r'\(\*(.*?)\*\)\s*([^;]+);',text,re.S))
    need(attrs(candidate)-attrs(original)==collections.Counter({('keep = "true"','logic [1:0] tile_owner_match'):1}) and
         not attrs(original)-attrs(candidate), 'Focused source synthesis-attribute delta exceeds two KEEP bits')
    need({r['seed'] for r in receipt['runs']}=={124101,124102} and len(receipt['runs'])==2,
         'Focused owner generic seed inventory changed')
    need({r['seed'] for r in receipt['caller_runs']}=={124201,124202} and len(receipt['caller_runs'])==2,
         'Focused owner caller seed inventory changed')
    checked=[]
    for run in receipt['runs']:
        log=path.parent/('owner-'+str(run['seed'])+'.log')
        rows=[json.loads(line) for line in log.read_text().splitlines()]
        need(rows==[run['baseline'],run['owner'],run['lanes']] and
             all(r['status']=='TEST_PASS' for r in rows),'Focused raw owner terminal dictionaries changed')
        base,owner,lanes=rows
        need(base['prepared_counter_cases']==2048 and base['cache_beats']>10000 and
             base['public_comparisons']>50000 and owner['type']=='v119_producer_owner' and
             owner['cases']==9216 and owner['random_cases']==250000,
             'Inherited ready/cache/nonce owner coverage changed')
        need(lanes['type']=='v124_owner_lanes_verdict' and lanes['wire_cases']==466944 and
             lanes['random_fullwidth_cases']==65536 and lanes['state_cases']==8192 and
             lanes['mode_mask']==lanes['bank_ready_mask']==lanes['guard_mask']==15 and lanes['emit_mask']==3 and
             lanes['invalid_ready_true']>0 and lanes['unready_ready_true']>0,
             'Focused complete owner-lane/full-width/invalid-context coverage changed')
        need(lanes['clock_cases']==1152 and lanes['error67_cases']==192 and lanes['cancel_cases']==864 and
             lanes['wrap_cases']==16 and lanes['held_edges']==336 and lanes['response_contexts']==224 and
             lanes['added_public_cycles']==lanes['error_cycle_delta']==lanes['pair_skipped_edges']==lanes['old_checks_removed']==0 and
             lanes['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused same-edge error/owner/physical-response/cancel coverage changed')
        checked.append(dict(kind='generic',seed=run['seed'],raw_log_sha256=sha(log),terminal_records_exact=3,owner_lane_coverage=lanes))
    for run in receipt['caller_runs']:
        log=path.parent/('caller-'+str(run['seed'])+'.log')
        rows=[json.loads(line) for line in log.read_text().splitlines()];v=run['verdict']
        need(rows[-1]==v and v['type']=='verdict' and v['status']=='TEST_PASS',
             'Focused actual-controller raw verdict changed')
        cases=[r for r in rows if r.get('type')=='case']
        need(v['vectors']==11 and v['cases']==len(cases)==run['case_rows']==22 and
             v['configurations']==2 and v['directed_checks']>=12 and v['dense_comparisons']>0 and
             v['directed_dense_comparisons']>0 and all(r['status']=='PASS' and not r['pending_drain'] and
             r['requests']==r['acks'] for r in cases), 'Focused actual-controller byte/debt/drain coverage changed')
        checked.append(dict(kind='caller',seed=run['seed'],raw_log_sha256=sha(log),case_rows=len(cases),terminal_record_exact=True))
    return checked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--integration', type=Path, default=INTEGRATION)
    ap.add_argument('--output', type=Path, default=ROOT/'experiments/python-gamebub-v124/audit/full-independent.json')
    args = ap.parse_args()
    index_path = args.integration.resolve()
    index = load(index_path)
    need(index['schema'] == 'v124-owner-functional-composition-v1' and
         index['status'] == 'PASS_V124_OWNER_FULL_FUNCTIONAL', 'Integration functional gate is not PASS')
    need(index['all_original_oracles_retained'] is True and index['exact_B_public_cycles'] is True and
         index['assertions_disabled_or_downgraded'] is False, 'Integration contract changed')
    need(sha(HANDOFF) == '0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00', 'Frozen V123 integration index changed')
    need(index['declared_public_cycle_delta'] == 0, 'Public cycle delta changed')
    handoff = load(HANDOFF)
    need(len(handoff['source_origins']) == 18, 'V123 handoff source map is not 18 files')
    for alias, meta in handoff['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V123 Source B source drift: ' + alias)
    need(len(index['source_origins']) == 18 and set(index['source_origins']) == set(handoff['source_origins']),
         'V124 composition does not map all Source B files')
    changed = []
    for alias, meta in index['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V124 mapped source drift: ' + alias)
        if alias == PRODUCER_ALIAS:
            need(meta['path'] == PRODUCER_CANDIDATE and meta['sha256'] != handoff['source_origins'][alias]['sha256'],
                 'V124 producer candidate identity mismatch')
            changed.append(alias)
        else:
            need(meta == handoff['source_origins'][alias], 'Unexpected non-producer source change: ' + alias)
    need(changed == [PRODUCER_ALIAS], 'V124 changed more than producer source')

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
    need(focused_receipt['source_sha256'].get(PRODUCER_CANDIDATE) ==
         index['source_origins'][PRODUCER_ALIAS]['sha256'],
         'Focused proof is not bound to the selected producer source')
    need(focused_receipt['source_sha256'].get(handoff['source_origins'][PRODUCER_ALIAS]['path']) ==
         handoff['source_origins'][PRODUCER_ALIAS]['sha256'],
         'Focused proof baseline queue hash differs from Source B')

    focused_checked = verify_focused(stage_paths['focused'][1], focused_receipt)
    _, rank_path, rank = resolve_baseline(handoff['stages']['focused'])
    verify_closure(rank_path, rank, 'inherited V123 rank')
    inherited_rank_checked = verify_inherited_rank(rank_path, rank)
    bounds_index_path=ROOT/'experiments/python-gamebub-v122/integration/results.json'
    need(sha(bounds_index_path)=='c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4', 'Frozen V122 bounds index changed')
    _, bounds_path, bounds = resolve_baseline(load(bounds_index_path)['stages']['focused'])
    verify_closure(bounds_path, bounds, 'inherited V122 bounds')
    inherited_bounds_checked = verify_inherited_bounds(bounds_path, bounds)
    baseline_receipts = {}
    for name, key in BASELINE_SELECTORS.items():
        _, path, raw = resolve_baseline(handoff['stages'][key])
        src_count, art_count = verify_closure(path, raw, 'V123 Source B ' + name)
        baseline_receipts[name] = (path, raw)
        closure['V123_' + name] = {'sources': src_count, 'artifacts': art_count}

    spatial = compare_spatial(stage_paths['spatial'][1], stage_receipts['spatial'],
                              *baseline_receipts['spatial'])
    peer = compare_peer(stage_paths['peer'][1], stage_receipts['peer'], *baseline_receipts['peer'])
    parent = compare_parent(stage_paths['parent'][1], stage_receipts['parent'], *baseline_receipts['parent'])
    result = {
        'schema': 'v124-full-independent-functional-audit-v1',
        'status': 'PASS_INDEPENDENT_V124_FULL_FUNCTIONAL_AUDIT',
        'integration_index': str(index_path.relative_to(ROOT)),
        'integration_index_sha256': sha(index_path),
        'source_B_count': 18,
        'source_B_hashes_match_handoff': True,
        'v124_source_map_count': 18,
        'v124_changed_aliases': changed,
        'stage_source_artifact_closure': closure,
        'focused_independent_raw_terminal_checks': focused_checked,
        'inherited_V122_bounds_raw_terminal_checks': inherited_bounds_checked,
        'inherited_V123_rank_raw_terminal_checks': inherited_rank_checked,
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
        print('V124_FUNCTIONAL_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
