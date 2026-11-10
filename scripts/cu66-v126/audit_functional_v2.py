#!/usr/bin/env python3
"""Independent read-only audit of V126 focused and composed functional receipts."""
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
INTEGRATION = ROOT / 'experiments/python-gamebub-v126/integration/results.json'
HANDOFF = ROOT / 'experiments/python-gamebub-v125/integration/results.json'
ADMISSION_ALIAS = 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv'
ADMISSION_CANDIDATE = 'fpga/experiments/cu66-v125-tile/cs88_admission_v91i2a.sv'
PRODUCER_ALIAS = 'fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
PRODUCER_CANDIDATE = 'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'
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
    """Resolve V125 handoff selector entries in their supported wrapper forms."""
    selector = ROOT / meta['path']
    need(sha(selector) == meta['sha256'], 'V125 baseline selector pin mismatch')
    d = load(selector)
    raw_path = d.get('selected_receipt', d.get('selected_report', d.get('path')))
    need(raw_path, 'V125 baseline selector has no receipt')
    raw_path = ROOT / raw_path
    if 'selected_receipt' in d:
        raw = load(raw_path)
        need(raw == {k: v for k, v in d.items() if k != 'selected_receipt'},
             'V125 selected receipt differs from selector')
    elif 'selected_report' in d:
        need(sha(raw_path) == d['selected_report_sha256'], 'V125 selected report hash mismatch')
        raw = load(raw_path)
    else:
        need(sha(raw_path) == d['sha256'], 'V125 selected receipt hash mismatch')
        raw = load(raw_path)
    return selector, raw_path, raw


def resolve_stage(stage):
    selector = ROOT / stage['path']
    need(sha(selector) == stage['sha256'], 'V126 stage selector hash mismatch: ' + stage['path'])
    selection = load(selector)
    pin = stage['receipt']
    receipt = ROOT / pin['path']
    need(sha(receipt) == pin['sha256'], 'V126 receipt hash mismatch: ' + pin['path'])
    raw = load(receipt)
    if 'selected_receipt' in selection:
        need(selection['selected_receipt'] == pin['path'] and
             raw == {k: v for k, v in selection.items() if k != 'selected_receipt'},
             'V126 selected receipt does not match selector')
    elif 'selected_report' in selection:
        need(selection['selected_report'] == pin['path'] and
             selection['selected_report_sha256'] == pin['sha256'],
             'V126 selected report does not match selector')
        if 'source_sha256' in selection:
            need(raw == {k: v for k, v in selection.items()
                         if k not in ('selected_report', 'selected_report_sha256')},
                 'V126 report receipt differs from selector')
    elif 'path' in selection:
        need(selection['path'] == pin['path'] and selection['sha256'] == pin['sha256'],
             'V126 path receipt does not match selector')
    else:
        need(False, 'V126 stage selector does not identify receipt')
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


def compare_packed(v126_receipt, v126_meta, v125_receipt, v125_meta, label):
    a = payload(v126_receipt.parent / v126_meta['path'], v126_meta.get('raw_sha256'))
    b = payload(v125_receipt.parent / v125_meta['path'], v125_meta.get('raw_sha256'))
    need(a == b, label + ' bytes differ from pinned V125 Source B')
    return {'raw_bytes': len(a), 'raw_sha256': hashlib.sha256(a).hexdigest()}


def compare_spatial(v126_path, v126, v125_path, v125):
    checked = []
    for field, prefix in (('runs', 'candidate'), ('transport_runs', 'transport')):
        new_runs, old_runs = v126.get(field, []), v125.get(field, [])
        need(len(new_runs) == len(old_runs) == 2, 'Unexpected spatial ' + field + ' count')
        old_by_seed = {x['seed']: x for x in old_runs}
        for run in new_runs:
            seed = run['seed']; old = old_by_seed[seed]
            log = f'{prefix}-{seed}-simulation.jsonl'
            new_log = v126_path.parent / log
            old_log = v125_path.parent / log
            need(new_log.read_bytes() == old_log.read_bytes(), prefix + ' stdout differs for seed ' + str(seed))
            streams = {}
            for key in ('events', 'canonical_actual'):
                streams[key] = compare_packed(v126_path, run['artifacts'][key], v125_path,
                                              old['artifacts'][key], prefix + ' ' + str(seed) + ' ' + key)
            checked.append({'kind': prefix, 'seed': seed, 'stdout_sha256': sha(new_log), 'streams': streams})
    return checked


def compare_peer(v126_path, v126, v125_path, v125):
    need(len(v126.get('runs', [])) == len(v125.get('runs', [])) == 2, 'Unexpected peer run count')
    old = {x['seed']: x for x in v125['runs']}; checked = []
    for row in v126['runs']:
        seed = row['seed']; need(row == old[seed], 'Peer verdict differs for seed ' + str(seed))
        prefix = f'peer-{seed}'
        log = v126_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v125_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Peer stdout differs for seed ' + str(seed))
        streams = {}
        for suffix in ('events.jsonl', 'canonical.tsv'):
            name = prefix + '-' + suffix + '.gz'
            streams[suffix] = compare_packed(v126_path, {'path': name}, v125_path,
                                             {'path': name}, prefix + ' ' + suffix)
        checked.append({'seed': seed, 'stdout_sha256': sha(log), 'streams': streams})
    return checked


def compare_parent(v126_path, v126, v125_path, v125):
    key = lambda x: (x['variant'], x['seed'], x['profile'])
    old = {key(x): x for x in v125['runs']}
    need(len(v126.get('runs', [])) == len(v125.get('runs', [])) and len(old) == len(v125['runs']),
         'Parent terminal record inventory differs')
    checked = []
    for run in v126['runs']:
        ident = key(run); control = old[ident]
        for field in ('live_case', 'fences', 'service', 'verdict', 'spatial_pipeline', 'parent_guard'):
            need(run[field] == control[field], 'Parent ' + str(ident) + ' differs in ' + field)
        prefix = f"{run['variant']}-{run['seed']}"
        log = v126_path.parent / (prefix + '-simulation.jsonl')
        oldlog = v125_path.parent / (prefix + '-simulation.jsonl')
        need(log.read_bytes() == oldlog.read_bytes(), 'Parent stdout differs for ' + str(ident))
        streams = {}
        for suffix in ('events.jsonl', 'actual.tsv', 'hashes.jsonl'):
            streams[suffix] = compare_packed(v126_path, run['artifacts'][suffix], v125_path,
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


def verify_inherited_owner(path, receipt):
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


def verify_tile_sources(receipt):
    """Independently reconstruct production, pair adapters, and scalar extraction."""
    area=ROOT/'fpga/experiments/cu66-v125-tile'
    for name in ('edit-recipe.json','verification-recipe.json','packaging.json'):
        p=area/name
        need(receipt['source_sha256'].get(str(p.relative_to(ROOT)))==sha(p),
             'Focused tile recipe is not source-bound: '+name)
    production=load(area/'edit-recipe.json');verification=load(area/'verification-recipe.json')
    need(production['schema']=='v125-tile-production-derivation-v1' and
         production['candidate']==ADMISSION_CANDIDATE and
         production['added_source_payload_bits']==3 and
         production['added_public_cycles']==production['added_synthesis_attributes']==
         production['old_assertions_removed']==production['old_private_value_contract_changes']==0,
         'Focused tile production scope changed')
    need(verification['schema']=='v125-tile-verification-derivation-v1' and
         verification['old_require_checks_removed']==verification['new_predicate_or_owner_forces']==0 and
         verification['prepared_key_priming_is_natural_traffic'] is False,
         'Focused tile fixture/oracle contract changed')
    runner_path=ROOT/'scripts/cu66-v125/integration/focused-runner-derivation.json'
    need(receipt['source_sha256'].get(str(runner_path.relative_to(ROOT)))==sha(runner_path),
         'Focused runner derivation is not source-bound')
    runner=load(runner_path)
    need(runner['schema']=='v125-focused-runner-derivation-v1' and
         runner['old_Cpp_require_checks_removed']==0 and runner['all_inherited_replay_oracles_retained'] is True,
         'Focused runner original oracle policy changed')
    need(sha(ROOT/runner['caller_runner_provenance']['path'])==runner['caller_runner_provenance']['sha256'],
         'Focused caller-runner provenance changed')
    records=[dict(original=production['original'],original_sha256=production['original_sha256'],
                  candidate=production['candidate'],candidate_sha256=production['candidate_sha256'],
                  edits=production['edits'])]+verification['adapters']+runner['sources']
    checks=lambda text:collections.Counter(re.findall(r'require\(.*?\);',text,re.S))
    for meta in records:
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        need(sha(before)==meta['original_sha256'] and sha(after)==meta['candidate_sha256'],
             'Focused tile derivation hash changed')
        text=before.read_text()
        for edit in meta['edits']:
            need(text.count(edit['before'])==1,'Focused tile forward derivation is ambiguous')
            text=text.replace(edit['before'],edit['after'],1)
        need(text==after.read_text(),'Focused tile forward reconstruction failed')
        for edit in reversed(meta['edits']):
            need(text.count(edit['after'])==1,'Focused tile reverse derivation is ambiguous')
            text=text.replace(edit['after'],edit['before'],1)
        need(text==before.read_text(),'Focused tile reverse reconstruction failed')
        if before.suffix=='.cpp':
            need(not checks(before.read_text())-checks(after.read_text()),
                 'Focused tile inherited require body removed')
    for meta in verification['unchanged']:
        need(sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256'],
             'Focused tile inherited verification source drifted')
    need(len(verification['new_verification_inputs'])==5,'Focused new verification source inventory changed')
    need(len(verification['new_verification_inputs'])==4,'Focused producer new fixture inventory changed')
    for meta in verification['new_verification_inputs']:
        need(sha(ROOT/meta['path'])==meta['sha256'] and receipt['source_sha256'].get(meta['path'])==meta['sha256'],
             'Focused new verification input drifted or is not source-bound')
    old=(ROOT/production['original']).read_text();new=(ROOT/production['candidate']).read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',old,re.S):
        need(block in new,'Focused tile original RTL assertion block changed')
    attrs=lambda text:collections.Counter(re.sub(r'\s+',' ',a).strip()
                                         for a in re.findall(r'\(\*(.*?)\*\)',text,re.S))
    need(attrs(old)==attrs(new),'Focused tile added or removed a synthesis attribute')
    extraction=verification['scalar_extraction']
    need(extraction['source']==ADMISSION_CANDIDATE and extraction['source_sha256']==sha(ROOT/ADMISSION_CANDIDATE),
         'Focused scalar probe is not extracted from selected admission')
    target=ROOT/extraction['target']
    need(sha(target)==extraction['target_sha256'] and
         target.read_text()==extraction['wrapper']+'\n'.join(extraction['fragments'])+extraction['tail'],
         'Focused scalar extraction bytes changed')
    for fragment in extraction['fragments']:
        need(new.count(fragment)==1,'Focused scalar extraction is absent or ambiguous in production')
    need(len(extraction['terminal_call_fragments'])==2,'Focused terminal successor extraction missing')
    for fragment in extraction['terminal_call_fragments']:
        need(new.count(fragment)==1 and target.read_text().count(fragment)==1,
             'Focused terminal successor call differs from production')
    packaging=load(area/'packaging.json');data=(ROOT/ADMISSION_CANDIDATE).read_bytes()
    need(packaging['schema']=='v125-lossless-admission-packaging-v1' and
         packaging['production_sha256']==hashlib.sha256(data).hexdigest() and
         len(packaging['fragments'])==3,'Focused tile packaging source changed')
    cuts=[0]+packaging['split_byte_offsets']+[len(data)]
    need(len(cuts)==4 and cuts==sorted(cuts),'Focused tile packaging boundaries changed')
    for i,fragment in enumerate(packaging['fragments']):
        piece=data[cuts[i]:cuts[i+1]]
        need(fragment['bytes']==len(piece) and fragment['sha256']==hashlib.sha256(piece).hexdigest(),
             'Focused tile packaging fragment changed')
    return dict(reversible_derivations=len(records),unchanged_files=len(verification['unchanged']),
                exact_scalar_fragments=len(extraction['fragments']),packaging_fragments=3,
                added_production_bits=3,added_synthesis_attributes=0)


def verify_inherited_tile(path, receipt):
    """Independently bind scalar, retained full pair, primer ledger, and caller logs."""
    need(receipt['schema']=='v125-tile-existing-edge-predicates-focused-v1',
         'Focused tile schema changed')
    need(receipt['all_old_require_checks_retained'] is True and
         receipt['added_public_cycles']==receipt['old_require_checks_removed']==
         receipt['old_private_value_contract_changes']==receipt['candidate_private_comparison_edits']==
         receipt['new_predicate_or_owner_forces']==0 and receipt['added_source_payload_bits']==3,
         'Focused tile public cycle, old checker, or source-state contract changed')
    need(receipt['prepared_fixture_priming_edges_are_natural_cycles'] is False,
         'Focused tile prepared clocks misclassified as natural packets')
    derivation=verify_tile_sources(receipt)
    for field,seeds in [('scalar_runs',{125501,125502}),('generic_runs',{125501,125502}),
                        ('caller_runs',{125601,125602})]:
        need(len(receipt[field])==2 and {r['seed']for r in receipt[field]}==seeds,
             'Focused tile seed inventory changed: '+field)
    checked=[]
    values=set(range(8192))
    for bit in range(13,32):
        value=1<<bit;values.update((value-1,value,value+1,value+633,value+1350,value+5400))
    values.update((0xfffffff0,0xfffffff1,0xfffffffe,0xffffffff))
    boundary=4*len(values)*7;cases=boundary+65536
    need(len(values)==8309 and boundary==232652 and cases==298188,
         'Independent scalar dimension calculation changed')
    for run in receipt['scalar_runs']:
        log=path.parent/('scalar-'+str(run['seed'])+'.log')
        rows=[json.loads(line)for line in log.read_text().splitlines()]
        scalar=run['verdict']
        need(rows==[scalar] and scalar['type']=='v125_tile_scalar_verdict' and
             scalar['status']=='TEST_PASS' and scalar['seed']==run['seed'],
             'Focused scalar raw verdict differs from receipt')
        need(scalar['boundary_cases']==boundary and scalar['random_full32_cases']==65536 and
             scalar['cases']==cases and scalar['clock_edges']==1+19*cases+16==5665589 and
             scalar['hold_edges']==2*cases==596376 and scalar['cancel_cases']==7*cases==2087316 and
             scalar['terminal_transition_cases']==8,
             'Focused scalar full32/hold/all-cancel/all-plane transition coverage changed')
        need(all(scalar[k]>0 for k in ('highbit_cases','plane3_cases','uint32_plus16_wrap_cases',
                                      'hidden_true','terminal_true','group_true')) and
             scalar['new_predicate_or_owner_forces']==0 and
             scalar['extracted_domain_is_natural_packets'] is False,
             'Focused scalar truth/wrap/domain contract changed')
        checked.append(dict(kind='scalar',seed=run['seed'],raw_log_sha256=sha(log),
                            verdict=scalar,terminal_record_exact=True))
    fields={'verdict':'terminal_verdict','v119_mode_bound':'owned_mode_bound',
            'v116_chunk_boundaries':'boundary','v120_header_match_verdict':'header_match',
            'v122_bounds_verdict':'bounds','v125_retained_mode_ledger':'mode_ledger',
            'v125_tile_campaign':'tile_campaign','v125_tile_verdict':'tile'}
    for run in receipt['generic_runs']:
        log=path.parent/('generic-'+str(run['seed'])+'.log')
        rows=[json.loads(line)for line in log.read_text().splitlines()]
        for kind,field in fields.items():
            selected=[r for r in rows if r.get('type')==kind]
            need(selected==[run[field]] and selected[0]['status']=='TEST_PASS',
                 'Focused generic raw verdict differs: '+kind)
        v=run['terminal_verdict'];h=run['header_match'];b=run['bounds']
        need(run['boundary']['cases']==25344 and run['boundary']['cancellation_cases']==294 and
             run['owned_mode_bound']['cases']==540 and v['prepared_edges']==348673 and
             v['header_prepared_edges']==738933 and v['scale_prepared_edges']==40585,
             'Focused inherited boundary/mode/quant/header/scale oracle coverage changed')
        need(h['prepared_full35_cases']==67664 and h['random_full35']==65536 and h['owned_consumes']==4096 and
             h['natural_packets']==h['natural_nonreset_retries']==36 and h['idle_hold_edges']==135328 and
             all(h[k]>0 for k in ('high32_alias_rejections','true_cases','false_cases','canceled_captures','fixture_priming_edges')) and
             h['added_natural_public_cycles']==h['old_require_checks_removed']==0 and
             h['prepared_predicate_contexts_are_natural_packets'] is False,
             'Focused inherited header-match/full35/natural/retry coverage changed')
        need(b['random_full32_cases']==16384 and b['cancellation_cases']==56 and
             all(b[k]>0 for k in ('full64_high32_cases','uint32_wrap_cases','fixture_priming_edges')) and
             b['added_natural_public_cycles']==b['old_require_checks_removed']==0 and
             b['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused inherited full32/full64 bounds coverage changed')
        ledger=run['mode_ledger'];campaign=run['tile_campaign'];tile=run['tile']
        need(ledger['semantic_cases']==158228 and ledger['original_clock_edges']==158230 and
             ledger['primer_clock_edges']>0 and ledger['total_clock_edges']==
             ledger['original_clock_edges']+ledger['primer_clock_edges']==v['mode_prepared_edges'],
             'Focused retained mode raw clocks omit real fixture primers')
        modes=[r for r in rows if 'type'not in r and r.get('final_mode_entries')==8100]
        need(modes==[run['raw_mode_verdict']] and modes[0]['status']=='TEST_PASS' and
             modes[0]['cases']==158228 and modes[0]['clock_edges']==ledger['total_clock_edges'],
             'Focused raw mode-port clocks or complete store coverage changed')
        expected=dict(contexts=411,semantic_clock_edges=852,primer_clock_edges=411,total_clock_edges=1263,
                      cancel_cases=189,first_followup_consumes=19,malformed_contexts=3,speculative_mode_checks=2)
        need(all(campaign[k]==value for k,value in expected.items()) and
             campaign['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused prepared campaign/error/speculative-write physical clock coverage changed')
        for field in ('natural_writers','prepared_writers','first_consume_counts','overwritten_before_consume'):
            need(len(tile[field])==9 and all(isinstance(n,int)and n>=0 for n in tile[field]),
                 'Focused writer dimension changed: '+field)
        need(all(a+b>0 for a,b in zip(tile['natural_writers'],tile['prepared_writers'])) and
             all(tile['first_consume_counts'][i]>0 for i in range(7)) and
             tile['first_consume_counts'][7:]==[0,0] and tile['overwritten_before_consume'][7]>0,
             'Focused predecessor/consumed writer/shadowed plane-clear coverage changed')
        need(len(tile['cancel_state_counts'])==33 and
             all(len(row)==8 and all(n>0 for n in row[1:])for row in tile['cancel_state_counts']),
             'Focused all33 original states/all7 cancellation overlap coverage changed')
        need(len(tile['cancel_counts'])==8 and all(n>0 for n in tile['cancel_counts'][1:]) and
             tile['total_primer_clock_edges']==ledger['primer_clock_edges']+411 and
             tile['prepared_monitored_clock_edges']==158228+tile['total_primer_clock_edges']+852 and
             tile['monitored_clock_edges']==tile['natural_clock_edges']+tile['prepared_monitored_clock_edges'] and
             all(tile[k]>0 for k in ('natural_clock_edges','hold_edges','consume_edges','natural_start_edges')),
             'Focused natural/prepared/primer clock ledger or cancellation coverage changed')
        need(tile['new_predicate_or_owner_forces']==tile['old_require_checks_removed']==
             tile['added_natural_public_cycles']==0 and tile['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused tile force/cycle/domain policy changed')
        primer_path=path.parent/(str(run['seed'])+'-tile-primer.jsonl.gz')
        primers=[json.loads(line)for line in payload(primer_path).decode().splitlines()]
        need(len(primers)==tile['total_primer_clock_edges'] and
             all(r['type']=='prepared_key_primer' and r['edge']==i+1 and r['real_writer_state']==8 and
                 r['next_state']==10 and r['equal'] is True for i,r in enumerate(primers)) and
             {r['target_state']for r in primers}=={0,6,10,11},
             'Focused raw trace does not account for every real predecessor primer')
        for field in ('coordinate','quant','scale','mode'):
            need(run[field]['status'].startswith('PASS'),'Focused independent replay failed: '+field)
        checked.append(dict(kind='generic',seed=run['seed'],raw_log_sha256=sha(log),
                            terminal_records_exact=len(fields)+1,primer_trace_sha256=sha(primer_path),
                            raw_primer_edges=len(primers),tile_coverage=tile,campaign=campaign,mode_ledger=ledger))
    for run in receipt['caller_runs']:
        log=path.parent/('caller-'+str(run['seed'])+'.log')
        rows=[json.loads(line)for line in log.read_text().splitlines()];v=run['verdict']
        cases=[r for r in rows if r.get('type')=='case']
        need(rows[-1]==v and v['type']=='verdict' and v['status']=='TEST_PASS' and v['seed']==run['seed'],
             'Focused actual-controller raw verdict changed')
        need(v['vectors']==11 and v['cases']==run['case_rows']==len(cases)==22 and
             v['configurations']==2 and v['directed_checks']>=12 and v['dense_comparisons']>0 and
             v['directed_dense_comparisons']>0 and all(r['status']=='PASS' and not r['pending_drain'] and
             r['requests']==r['acks']for r in cases),
             'Focused actual-controller natural/mapped/dense/physical-debt coverage changed')
        checked.append(dict(kind='caller',seed=run['seed'],raw_log_sha256=sha(log),case_rows=len(cases),
                            terminal_record_exact=True,verdict=v))
    return dict(derivation=derivation,runs=checked,
                scalar_scope='Lossless production scalar/task/terminal-call extraction, not controller packet reachability.',
                prepared_scope='Real predecessor clocks inside explicit prepared contexts, distinct from natural packet cycles.')

def verify_producer_sources(receipt):
    """Independent source/fixture reconstruction, separate from runner imports."""
    area=ROOT/'fpga/experiments/cu66-v126-producer'
    for name in ('edit-recipe.json','verification-recipe.json','packaging.json'):
        path=area/name
        need(receipt['source_sha256'].get(str(path.relative_to(ROOT)))==sha(path),
             'Focused producer recipe is not source-bound: '+name)
    production=load(area/'edit-recipe.json');verification=load(area/'verification-recipe.json')
    need(production['schema']=='v126-producer-production-derivation-v1' and
         production['candidate']==PRODUCER_CANDIDATE and production['added_source_payload_bits']==24 and
         production['unchanged_other_origins']==17 and
         production['added_public_cycles']==production['added_synthesis_attributes']==
         production['old_assertions_removed']==production['old_private_value_contract_changes']==0,
         'Focused producer production scope changed')
    need(verification['schema']=='v126-producer-verification-derivation-v1' and
         verification['old_require_checks_removed']==verification['new_payload_or_owner_forces']==0 and
         verification['prepared_priming_is_natural_traffic'] is False,
         'Focused producer fixture/oracle contract changed')
    checks=lambda text:collections.Counter(re.findall(r'(?:need|require_owner)\(.*?\);',text,re.S))
    for meta in [production]+verification['adapters']:
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        need(sha(before)==meta['original_sha256'] and sha(after)==meta['candidate_sha256'],
             'Focused producer derivation hash changed')
        text=before.read_text()
        for edit in meta['edits']:
            need(text.count(edit['before'])==1,'Focused producer forward edit is ambiguous')
            text=text.replace(edit['before'],edit['after'],1)
        need(text==after.read_text(),'Focused producer forward reconstruction failed')
        for edit in reversed(meta['edits']):
            need(text.count(edit['after'])==1,'Focused producer reverse edit is ambiguous')
            text=text.replace(edit['after'],edit['before'],1)
        need(text==before.read_text(),'Focused producer reverse reconstruction failed')
        if before.suffix in ('.cpp','.hpp'):
            need(not checks(before.read_text())-checks(after.read_text()),
                 'Focused producer inherited need/require body removed')
    for meta in verification['unchanged']:
        need(sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256'],
             'Focused producer unchanged verification source drifted')
    for meta in verification['new_verification_inputs']:
        need(sha(ROOT/meta['path'])==meta['sha256'] and
             receipt['source_sha256'].get(meta['path'])==meta['sha256'],
             'Focused new producer fixture not source-bound')
    new_fields=('prepared_successor_tile','prepared_successor_cell','address_owner_valid','address_owner_frame','address_owner_plane','address_owner_tile','cell_owner_valid','cell_owner_frame','cell_owner_child_epoch','cell_owner_plane','cell_owner_tile','cell_owner_address')
    for meta in verification['new_verification_inputs']:
        text=(ROOT/meta['path']).read_text()
        for name in new_fields:
            need(not re.search(r'(?:NEW|SP)\('+name+r'\)\s*=(?!=)',text) and 'BOTH('+name+','not in text,
                 'Focused new payload/owner forced in authored fixture: '+name)
        need('BS(outstanding,'not in text,'Focused authored fixture rewrites physical outstanding ownership')
    original=(ROOT/production['original']).read_text();candidate=(ROOT/production['candidate']).read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):
        need(block in candidate,'Focused producer original RTL assertion block changed')
    need(re.findall(r'\(\*(.*?)\*\)',original,re.S)==re.findall(r'\(\*(.*?)\*\)',candidate,re.S),
         'Focused producer synthesis attributes changed')
    synth=re.sub(r'`ifndef SYNTHESIS.*?`endif','',candidate,flags=re.S)
    need(not re.search(r'\b(?:address_owner_|cell_owner_)',synth),
         'Focused producer verification-only owner escaped synthesis guard')
    need('logic [12:0] prepared_successor_tile;'in synth and 'logic [10:0] prepared_successor_cell;'in synth,
         'Focused producer 13/11 source payload width changed')
    packaging=load(area/'packaging.json')
    need(packaging['schema']=='v126-producer-single-module-packaging-v1' and
         packaging['production_sha256']==sha(ROOT/PRODUCER_CANDIDATE) and packaging['split_byte_offsets']==[] and
         packaging['fragments']==[dict(filename=Path(PRODUCER_CANDIDATE).name,
              bytes=len((ROOT/PRODUCER_CANDIDATE).read_bytes()),sha256=sha(ROOT/PRODUCER_CANDIDATE))],
         'Focused producer full-module packaging changed')
    extraction=verification['scalar_extraction'];target=ROOT/extraction['target']
    need(extraction['source']==PRODUCER_CANDIDATE and extraction['source_sha256']==sha(ROOT/PRODUCER_CANDIDATE) and
         sha(target)==extraction['target_sha256'], 'Focused producer scalar extraction source/target drifted')
    need(target.read_text()==extraction['wrapper']+'\n'.join(extraction['fragments'])+extraction['tail'],
         'Focused producer scalar wrapper/fragments changed')
    for fragment in extraction['fragments']:
        need(candidate.count(fragment)==1,'Focused producer scalar fragment absent or ambiguous')
    need(len(extraction['call_fragments'])==4,'Focused producer scalar writer-call inventory changed')
    for fragment in extraction['call_fragments']:
        need(candidate.count(fragment)==target.read_text().count(fragment)>0,
             'Focused producer scalar writer call differs from production')
    runner_path=ROOT/'scripts/cu66-v126/integration/focused-runner-derivation.json'
    need(receipt['source_sha256'].get(str(runner_path.relative_to(ROOT)))==sha(runner_path),
         'Focused producer runner derivation not source-bound')
    runner=load(runner_path)
    for meta in runner['sources']:
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        need(sha(before)==meta['original_sha256'] and sha(after)==meta['candidate_sha256'],
             'Focused producer runner derivation source drifted')
        text=before.read_text()
        for edit in meta['edits']:
            need(text.count(edit['before'])==edit['count'],'Focused runner forward edit ambiguous')
            text=text.replace(edit['before'],edit['after'])
        need(text==after.read_text(),'Focused runner forward reconstruction failed')
        for edit in reversed(meta['edits']):
            need(text.count(edit['after'])==edit['count'],'Focused runner reverse edit ambiguous')
            text=text.replace(edit['after'],edit['before'])
        need(text==before.read_text(),'Focused runner reverse reconstruction failed')
    return dict(production_payload_bits=24,reversible_derivations=1+len(verification['adapters'])+len(runner['sources']),
                unchanged_files=len(verification['unchanged']),scalar_fragments=len(extraction['fragments']),
                new_fixture_inputs=len(verification['new_verification_inputs']),added_synthesis_attributes=0)


def verify_focused(path, receipt):
    """Independently bind exact scalar, retained generic, real-stage and caller records."""
    need(receipt['schema']=='v126-producer-existing-edge-successor-focused-v1', 'Focused producer schema changed')
    need(receipt['all_old_require_checks_retained'] is True and receipt['added_source_payload_bits']==24 and
         receipt['old_require_checks_removed']==receipt['added_public_cycles']==receipt['old_private_value_contract_changes']==
         receipt['candidate_private_comparison_edits']==receipt['new_payload_or_owner_forces']==0 and
         receipt['prepared_fixture_priming_edges_are_natural_cycles'] is False,
         'Focused producer old-oracle/cycle/fixture contract changed')
    derivation=verify_producer_sources(receipt)
    for field,seeds in [('scalar_runs',{126501,126502}),('generic_runs',{126501,126502}),('caller_runs',{126601,126602})]:
        need(len(receipt[field])==2 and {r['seed']for r in receipt[field]}==seeds,
             'Focused producer seed inventory changed: '+field)
    def raw_one(rows,kind,expected):
        selected=[r for r in rows if r.get('type')==kind]
        need(selected==[expected] and selected[0]['status']=='TEST_PASS','Focused raw terminal mismatch: '+kind)
    def monitor(value):
        events=value['events']
        need(len(events)==14 and all(isinstance(n,int)and n>=0 for n in events) and
             sum(events)==value['monitored_clocks']==value['current_cache_checks'],
             'Focused producer event/clock/current-cache ledger changed')
        need(value['address_captures']==events[0]+events[2]+events[3] and
             value['cell_consumes']==events[2]+events[3] and value['rom_samples']>=events[1]+events[7],
             'Focused producer capture/consume/speculative-ROM ledger changed')
        need(all(value[k]>0 for k in ('address_captures','rom_samples','cell_consumes','held_owned_edges',
                                      'earliest_mode2','earliest_skip','accepted_starts','blocked_raw_starts')) and
             value['max_lookup_age']>=1 and value['added_public_cycles']==value['new_payload_or_owner_forces']==0,
             'Focused producer first/held/blocked-start/accepted-start coverage changed')
    checked=[]
    for run in receipt['scalar_runs']:
        log=path.parent/('scalar-'+str(run['seed'])+'.log');rows=[json.loads(line)for line in log.read_text().splitlines()]
        v=run['verdict'];raw_one(rows,'v126_successor_scalar_verdict',v)
        cases=4*(1<<13)+65536;cancels=4*8*5*7;clocks=1+12*cases+9*cancels+2*(4*8*7)
        need(len(rows)==1 and v['seed']==run['seed'] and v['exhaustive_full13_cases']==32768 and
             v['random_cases']==65536 and v['cases']==cases==98304 and v['clock_edges']==clocks==1190177 and
             v['hold_edges']==3*cases==294912 and v['cancel_cases']==cancels==1120,
             'Focused full13/all-plane/scalar hold/cancel dimensions changed')
        need(all(v[k]>0 for k in ('successor13_wrap_cases','plus2_wrap_cases','plane3_cases',
                                  'y_cell11_truncation_cases','canceled_rom_value_changes')) and
             v['new_payload_or_owner_forces']==0 and v['prepared_scalar_domain_is_natural_packets'] is False,
             'Focused scalar truncation/wrap/canceled-ROM/domain coverage changed')
        checked.append(dict(kind='scalar',seed=run['seed'],raw_log_sha256=sha(log),verdict=v))
    for run in receipt['generic_runs']:
        log=path.parent/('generic-'+str(run['seed'])+'.log');rows=[json.loads(line)for line in log.read_text().splitlines()]
        base,owner,lanes,campaign,m=run['baseline'],run['owner'],run['lanes'],run['campaign'],run['monitor']
        need(rows==[base,owner,lanes,campaign,m] and base['status']=='TEST_PASS',
             'Focused generic raw dictionaries differ from receipt')
        for kind,value in [('v119_producer_owner',owner),('v124_owner_lanes_verdict',lanes),
                           ('v126_successor_campaign',campaign),('v126_successor_generic_monitor',m)]:raw_one(rows,kind,value)
        need(base['prepared_counter_cases']==2048 and base['cache_beats']>10000 and base['public_comparisons']>50000 and
             owner['cases']==9216 and owner['random_cases']==250000,
             'Focused inherited readiness/cache/full32 nonce/owner coverage changed')
        need(lanes['wire_cases']==466944 and lanes['random_fullwidth_cases']==65536 and lanes['state_cases']==8192 and
             lanes['mode_mask']==lanes['bank_ready_mask']==lanes['guard_mask']==15 and lanes['emit_mask']==3 and
             lanes['invalid_ready_true']>0 and lanes['unready_ready_true']>0,
             'Focused inherited fullwidth owner-lane/invalid-context coverage changed')
        need(lanes['clock_cases']==1152 and lanes['error67_cases']==192 and lanes['cancel_cases']==864 and
             lanes['wrap_cases']==16 and lanes['held_edges']==336 and lanes['response_contexts']==224 and
             lanes['added_public_cycles']==lanes['error_cycle_delta']==lanes['pair_skipped_edges']==lanes['old_checks_removed']==0 and
             lanes['prepared_domain_fixtures_are_natural_packets'] is False,
             'Focused inherited clocked error/response/cancel/physical-debt oracles changed')
        expected=dict(contexts=534,actual_clock_edges=3664,primer_clock_edges=1428,nonprimer_clock_edges=2236,
                      earliest_cases=24,walk_skip_advances=555,held_child_edges=21,nonterminal_advances=96,
                      cancel_cases=288,bad_owner_cases=48,stage_overlap_cases=72,unowned_bad_bound_cases=9,
                      empty_plane_cases=3,accepted_start_cases=3)
        need(all(campaign[k]==value for k,value in expected.items()) and
             campaign['actual_clock_edges']==campaign['primer_clock_edges']+campaign['nonprimer_clock_edges'] and
             campaign['new_payload_or_owner_forces']==0 and campaign['prepared_domain_is_natural_packets'] is False,
             'Focused actual predecessor/campaign/priority/domain dimensions changed')
        monitor(m)
        need(m['monitored_clocks']==275334 and m['monitored_clocks']-campaign['actual_clock_edges']==271670,
             'Focused retained-instrumented plus new-campaign clock ledger changed')
        primer_path=path.parent/(str(run['seed'])+'-producer-primer.jsonl.gz')
        primers=[json.loads(line)for line in payload(primer_path).decode().splitlines()]
        need(len(primers)==run['primer_trace_edges']==1428,'Focused real producer primer trace edge count changed')
        phase_counts=collections.Counter()
        for i,row in enumerate(primers):
            phase=row['phase'];phase_counts[phase]+=1
            need(phase in (0,1,2) and row['type']=='prepared_producer_primer' and row['edge']==i+1 and
                 row['equal'] is True and (row['before_state'],row['after_state'])=={0:(3,4),1:(9,10),2:(10,11)}[phase] and
                 row['tile']==0 and row['address']==1,
                 'Focused producer raw trace lacks actual PREP/request/earliest-response predecessor')
        need(phase_counts=={0:510,1:486,2:432} and {r['plane']for r in primers}=={0,1,2},
             'Focused raw producer primer phase/plane coverage changed')
        checked.append(dict(kind='generic',seed=run['seed'],raw_log_sha256=sha(log),terminal_records_exact=5,
                            campaign=campaign,monitor=m,primer_trace_sha256=sha(primer_path),primer_phase_counts=dict(phase_counts),
                            retained_cache_driver_clock_edges=base['edges'],
                            retained_instrumented_owner_clock_edges=271670))
    for run in receipt['caller_runs']:
        log=path.parent/('caller-'+str(run['seed'])+'.log');rows=[json.loads(line)for line in log.read_text().splitlines()]
        v,m=run['verdict'],run['monitor'];raw_one(rows,'verdict',v);raw_one(rows,'v126_successor_caller_monitor',m)
        need(rows[-2:]==[v,m] and v['seed']==run['seed'],'Focused actual-controller raw terminal/monitor order changed')
        cases=[r for r in rows if r.get('type')=='case']
        need(v['vectors']==11 and v['cases']==run['case_rows']==len(cases)==22 and v['configurations']==2 and
             v['directed_checks']>=12 and v['dense_comparisons']>0 and v['directed_dense_comparisons']>0 and
             all(r['status']=='PASS'and not r['pending_drain']and r['requests']==r['acks']for r in cases),
             'Focused actual-controller dense/mapped/accepted-memory/drain oracle changed')
        monitor(m)
        checked.append(dict(kind='caller',seed=run['seed'],raw_log_sha256=sha(log),case_rows=len(cases),verdict=v,monitor=m))
    return dict(derivation=derivation,runs=checked,
                scalar_scope='Exact production scalar/task/ROM/call extraction with old-field fixture loads; not original controller reachability.',
                generic_clock_scope='275334 instrumented owner/campaign clocks; original legacy cache Driver counters remain separate.',
                prepared_scope='1428 real PREP/MAP_REQ/MAP_WAIT priming edges within explicit prepared contexts, not natural packet cycles.')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--integration', type=Path, default=INTEGRATION)
    ap.add_argument('--output', type=Path, default=ROOT/'experiments/python-gamebub-v126/audit/full-independent.json')
    args = ap.parse_args()
    index_path = args.integration.resolve()
    index = load(index_path)
    need(index['schema'] == 'v126-producer-functional-composition-v1' and
         index['status'] == 'PASS_V126_PRODUCER_FULL_FUNCTIONAL', 'Integration functional gate is not PASS')
    need(index['all_original_oracles_retained'] is True and index['exact_B_public_cycles'] is True and
         index['assertions_disabled_or_downgraded'] is False, 'Integration contract changed')
    need(sha(HANDOFF) == 'a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987', 'Frozen V125 integration index changed')
    need(index['declared_public_cycle_delta'] == 0, 'Public cycle delta changed')
    handoff = load(HANDOFF)
    need(len(handoff['source_origins']) == 18, 'V125 handoff source map is not 18 files')
    for alias, meta in handoff['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V125 Source B source drift: ' + alias)
    need(len(index['source_origins']) == 18 and set(index['source_origins']) == set(handoff['source_origins']),
         'V126 composition does not map all Source B files')
    changed = []
    for alias, meta in index['source_origins'].items():
        need(sha(ROOT / meta['path']) == meta['sha256'], 'V126 mapped source drift: ' + alias)
        if alias == PRODUCER_ALIAS:
            need(meta['path'] == PRODUCER_CANDIDATE and meta['sha256'] != handoff['source_origins'][alias]['sha256'],
                 'V126 producer candidate identity mismatch')
            changed.append(alias)
        else:
            need(meta == handoff['source_origins'][alias], 'Unexpected non-producer source change: ' + alias)
    need(changed == [PRODUCER_ALIAS], 'V126 changed more than producer source')
    expected_order=[PRODUCER_CANDIDATE if p==handoff['source_origins'][PRODUCER_ALIAS]['path'] else p for p in handoff['rtl_source_order']]
    need(index['rtl_source_order']==expected_order, 'V126 RTL/include source order differs from V125')

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
            _, order_path, order_baseline = resolve_baseline(handoff['stages'][BASELINE_SELECTORS[name]])
            baseline_producer = handoff['source_origins'][PRODUCER_ALIAS]['path']
            expected_stage_order = [PRODUCER_CANDIDATE if p == baseline_producer else p
                                    for p in order_baseline['rtl_source_order']]
            need(receipt['rtl_source_order'][:18] == index['rtl_source_order'],
                 name + ' core18 RTL/include source order differs from integration')
            need(receipt['rtl_source_order'] == expected_stage_order,
                 name + ' complete RTL/include source order differs from frozen V125 stage')
            closure[name]['source_origin_count'] = n
            closure[name]['changed_aliases'] = delta
        stage_receipts[name] = receipt
    focused_receipt = stage_receipts['focused']
    need(focused_receipt['source_sha256'].get(PRODUCER_CANDIDATE) ==
         index['source_origins'][PRODUCER_ALIAS]['sha256'],
         'Focused proof is not bound to the selected producer source')
    need(focused_receipt['source_sha256'].get(handoff['source_origins'][PRODUCER_ALIAS]['path']) ==
         handoff['source_origins'][PRODUCER_ALIAS]['sha256'],
         'Focused proof baseline producer hash differs from V125')

    focused_checked = verify_focused(stage_paths['focused'][1], focused_receipt)
    _, tile_path, tile = resolve_baseline(handoff['stages']['focused'])
    verify_closure(tile_path, tile, 'inherited V125 tile')
    inherited_tile_checked = verify_inherited_tile(tile_path, tile)
    owner_index_path=ROOT/'experiments/python-gamebub-v124/integration/results.json'
    need(sha(owner_index_path)=='9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f', 'Frozen V124 owner index changed')
    _, owner_path, owner = resolve_baseline(load(owner_index_path)['stages']['focused'])
    verify_closure(owner_path, owner, 'inherited V124 owner')
    inherited_owner_checked = verify_inherited_owner(owner_path, owner)
    rank_index_path=ROOT/'experiments/python-gamebub-v123/integration/results.json'
    need(sha(rank_index_path)=='0a665162168f4aaa9bff29546263d57b61abbef50bb65fefc2606de919f15d00', 'Frozen V123 rank index changed')
    _, rank_path, rank = resolve_baseline(load(rank_index_path)['stages']['focused'])
    verify_closure(rank_path, rank, 'inherited V123 rank')
    inherited_rank_checked = verify_inherited_rank(rank_path, rank)
    bounds_index_path=ROOT/'experiments/python-gamebub-v122/integration/results.json'
    need(sha(bounds_index_path)=='c6c12f453375ed1d096960d2325c98e7ef17562229893360785a9455f4bce5a4', 'Frozen V122 bounds index changed')
    _, bounds_path, bounds = resolve_baseline(load(bounds_index_path)['stages']['focused'])
    verify_closure(bounds_path, bounds, 'inherited V122 bounds')
    inherited_bounds_checked = verify_inherited_bounds(bounds_path, bounds)
    queue_index_path=ROOT/'experiments/python-gamebub-v121/integration/results.json'
    need(sha(queue_index_path)=='bafb9950bbf740f0b3182f4d7f5f19875e1fbfa65b85d3c193282ceec748b689', 'Frozen V121 queue index changed')
    _, queue_path, queue = resolve_baseline(load(queue_index_path)['stages']['focused'])
    queue_counts=verify_closure(queue_path, queue, 'inherited V121 queue')
    baseline_receipts = {}
    for name, key in BASELINE_SELECTORS.items():
        _, path, raw = resolve_baseline(handoff['stages'][key])
        src_count, art_count = verify_closure(path, raw, 'V125 Source B ' + name)
        baseline_receipts[name] = (path, raw)
        closure['V125_' + name] = {'sources': src_count, 'artifacts': art_count}

    spatial = compare_spatial(stage_paths['spatial'][1], stage_receipts['spatial'],
                              *baseline_receipts['spatial'])
    peer = compare_peer(stage_paths['peer'][1], stage_receipts['peer'], *baseline_receipts['peer'])
    parent = compare_parent(stage_paths['parent'][1], stage_receipts['parent'], *baseline_receipts['parent'])
    result = {
        'schema': 'v126-full-independent-functional-audit-v1',
        'status': 'PASS_INDEPENDENT_V126_FULL_FUNCTIONAL_AUDIT',
        'integration_index': str(index_path.relative_to(ROOT)),
        'integration_index_sha256': sha(index_path),
        'source_B_count': 18,
        'source_B_hashes_match_handoff': True,
        'v126_source_map_count': 18,
        'v126_changed_aliases': changed,
        'stage_source_artifact_closure': closure,
        'focused_independent_raw_terminal_checks': focused_checked,
        'inherited_V122_bounds_raw_terminal_checks': inherited_bounds_checked,
        'inherited_V123_rank_raw_terminal_checks': inherited_rank_checked,
        'inherited_V125_tile_raw_terminal_checks': inherited_tile_checked,
        'inherited_V124_owner_raw_terminal_checks': inherited_owner_checked,
        'inherited_V121_queue_source_artifact_closure': dict(sources=queue_counts[0],artifacts=queue_counts[1],receipt=str(queue_path.relative_to(ROOT)),sha256=sha(queue_path)),
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
        print('V126_FUNCTIONAL_AUDIT_FAIL:', exc, file=sys.stderr)
        raise SystemExit(1)
