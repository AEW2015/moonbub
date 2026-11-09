#!/usr/bin/env python3
"""Read selected actual RTL transcripts; report conditional cycle conversions only."""
import csv
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v115'
BASE = ROOT / 'experiments/python-gamebub-v114/optimized'
ORACLE = ROOT / 'experiments/python-gamebub-v113/spatial/results.json'
BASE_NATIVE = BASE / 'native/20261108T235739184089Z/receipt.json'
BASE_NATIVE_SHA = '521daae4a0f1ddc8c119a116c71eaee523cc3bf7c8295fe9b7a9e5ba5c7de1b1'
ORACLE_SHA = '70b3e484cb35e24d02913ae463ac91205d444b2b96d7008cc3b614db594cf445'
SEEDS = (107601, 107602)
SAMPLES = 518400
BUDGET = 1250000


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def load(path):
    return json.loads(path.read_text())


def pin(path, pins, wanted=None):
    actual = sha(path)
    require(wanted is None or wanted == actual, f'hash mismatch: {rel(path)}')
    pins[rel(path)] = actual
    return actual


def selected(path, wanted_status, pins):
    q = load(path)
    require(q['status'] == wanted_status and q['actual_RTL_run'] is True,
            f'not selected actual PASS: {rel(path)}')
    receipt = ROOT / q['selected_receipt']
    require(load(receipt) == {k: v for k, v in q.items() if k != 'selected_receipt'},
            f'summary/receipt mismatch: {rel(path)}')
    pin(path, pins)
    pin(receipt, pins)
    require(q['seeds'] == list(SEEDS), 'seed set changed')
    for group in ('runs', 'transport_runs'):
        require(len(q[group]) == 2 and {r['seed'] for r in q[group]} == set(SEEDS), group)
        for run in q[group]:
            require(run['canonical_exact'] is True, 'canonical comparison absent')
            artifact = run['artifacts']['canonical_actual']
            pin(receipt.parent/artifact['path'], pins, artifact['sha256'])
    return q, receipt


def transcript(q, receipt, kind, seed, pins):
    name = f'{"candidate" if kind == "component" else "transport"}-{seed}-simulation.jsonl'
    path = receipt.parent/name
    pin(path, pins, q['artifact_sha256'][name])
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    tag = 'verdict' if kind == 'component' else 'transport_verdict'
    verdicts = [r for r in lines if r.get('type') == tag]
    group = 'runs' if kind == 'component' else 'transport_runs'
    retained = next(r for r in q[group] if r['seed'] == seed)
    require(len(verdicts) == 1 and verdicts[0]['status'] == 'TEST_PASS', name)
    require(verdicts[0] == retained['verdict'], f'verdict mismatch: {name}')
    cases, fences = {}, {}
    if kind == 'component':
        require(verdicts[0]['cases'] == 22 and verdicts[0]['directed_checks'] == 21, name)
        for row in lines:
            if row.get('type') == 'case' and row['error'] == 0:
                key = (row['id'], row['memory_profile'])
                require(key not in cases, f'duplicate normal case: {name} {key}')
                cases[key] = row
    else:
        require(verdicts[0]['successful_case_profiles'] == 12 and
                verdicts[0]['abort_reset_retries'] == 2, name)
        # Two successful retry cases appear later without custom_transport reports.
        # Pair only each actual report with its immediately preceding normal case.
        for i, fence in enumerate(lines):
            if fence.get('type') != 'custom_transport':
                continue
            row = lines[i-1] if i else {}
            key = (fence['id'], fence['profile'])
            require(row.get('type') == 'case' and row['error'] == 0 and
                    key == (row['id'], row['memory_profile']), f'unpaired transport case: {name}')
            require(key not in cases and fence['status'] == 'PASS', name)
            require(fence['decoder_done_cycle'] == row['done_cycle'] and
                    fence['canonical_samples'] == SAMPLES and
                    row['last_input'] < fence['ingress_commit_cycle'] <= row['done_cycle'], name)
            cases[key], fences[key] = row, fence
        require(list(fences.values()) == retained['fences'], f'fence ledger mismatch: {name}')
    require(len(cases) == 12 and all(r['status'] == 'PASS' for r in cases.values()), name)
    return cases, fences


def latency(row):
    require(row['canonical']['samples'] == SAMPLES and row['full_frame_publication'] is False,
            'scope or sample count changed')
    first, done, pixel = row['first_input'], row['done_cycle'], row['canonical']['last_pixel_cycle']
    require(0 < first <= pixel <= done and not row['pending_drain'], 'incomplete successful case')
    return done-first+1, pixel-first+1


def summary(rows):
    result = {}
    for kind in ('component', 'transport'):
        result[kind] = {}
        for profile in (0, 1):
            selected_rows = [r for r in rows if r['kind'] == kind and r['profile'] == profile]
            counts = [r['candidate_first_decoder_byte_to_done_cycles'] for r in selected_rows]
            changes = [r['change_first_decoder_byte_to_done_cycles'] for r in selected_rows]
            require(len(counts) == 12, 'missing matched successful profiles')
            result[kind][str(profile)] = dict(
                cases=len(counts), minimum_cycles=min(counts), median_cycles=statistics.median(counts),
                maximum_cycles=max(counts), minimum_change_cycles=min(changes),
                median_change_cycles=statistics.median(changes), maximum_change_cycles=max(changes),
                conditional_minimum_ms_at125MHz=min(counts)/125000,
                conditional_maximum_ms_at125MHz=max(counts)/125000,
                conditional_strict_under10ms_at125MHz_case_count=sum(n < BUDGET for n in counts),
                conditional_worst_case_30fps_service_slack_cycles_at125MHz=125000000/30-max(counts),
                minimum_identity={k: v for k, v in min(selected_rows, key=lambda r: r['candidate_first_decoder_byte_to_done_cycles']).items() if k in ('seed', 'case', 'profile')},
                maximum_identity={k: v for k, v in max(selected_rows, key=lambda r: r['candidate_first_decoder_byte_to_done_cycles']).items() if k in ('seed', 'case', 'profile')})
    return result


def main():
    selected_path = AREA/'spatial/results.json'
    if not selected_path.exists():
        print('PREREQUISITES_NOT_READY: selected V115 spatial PASS is absent; no ledger written.')
        return
    pins = {}
    candidate, candidate_receipt = selected(selected_path, 'PASS_V115_SPATIAL_CANONICAL', pins)
    baseline_path = BASE/'spatial/results.json'
    baseline, baseline_receipt = selected(baseline_path, 'PASS_V114_OPTIMIZED_SPATIAL_CANONICAL', pins)
    oracle, _ = selected(ORACLE, 'PASS_V113_SPATIAL_CANONICAL', pins)
    pin(ORACLE, pins, ORACLE_SHA)
    native = load(BASE_NATIVE)
    pin(BASE_NATIVE, pins, BASE_NATIVE_SHA)
    origins = native['source_contract']['source_origins']
    require(len(origins) == 18, 'baseline origin contract')
    require(native['source_contract']['proof_pins'][rel(baseline_path)] == sha(baseline_path),
            'B125 native receipt does not bind selected baseline')
    for origin in origins.values():
        require(baseline['source_sha256'][origin['path']] == origin['sha256'], 'baseline body differs from B125')
    require(candidate['candidate_model_reused'] is False and candidate['canonical_reused_actual_RTL'] is False,
            'candidate must have fresh full proof')
    rows = []
    for seed in SEEDS:
        for group in ('runs', 'transport_runs'):
            new_run = next(r for r in candidate[group] if r['seed'] == seed)
            old_run = next(r for r in baseline[group] if r['seed'] == seed)
            ref_run = next(r for r in oracle[group] if r['seed'] == seed)
            require(len({r['artifacts']['canonical_actual']['raw_sha256'] for r in (new_run, old_run, ref_run)}) == 1,
                    'canonical artifact differs from frozen V113 oracle')
        for kind in ('component', 'transport'):
            current, current_fences = transcript(candidate, candidate_receipt, kind, seed, pins)
            before, before_fences = transcript(baseline, baseline_receipt, kind, seed, pins)
            require(current.keys() == before.keys(), 'baseline/candidate successful corpus differs')
            for key, row in current.items():
                old = before[key]
                after_done, after_pixel = latency(row)
                old_done, old_pixel = latency(old)
                result = dict(kind=kind, seed=seed, case=key[0], profile=key[1],
                              baseline_case_cycles=old['cycles'], candidate_case_cycles=row['cycles'],
                              change_case_cycles=row['cycles']-old['cycles'],
                              baseline_first_decoder_byte_to_done_cycles=old_done,
                              candidate_first_decoder_byte_to_done_cycles=after_done,
                              change_first_decoder_byte_to_done_cycles=after_done-old_done,
                              baseline_first_decoder_byte_to_last_pixel_cycles=old_pixel,
                              candidate_first_decoder_byte_to_last_pixel_cycles=after_pixel,
                              conditional_done_ms_at100MHz=after_done/100000,
                              conditional_done_ms_at125MHz=after_done/125000,
                              conditional_strict_under10ms_at125MHz=after_done < BUDGET,
                              conditional_10ms_cycle_margin_at125MHz=BUDGET-after_done,
                              baseline_transport_start_to_report_cycles=None,
                              candidate_transport_start_to_report_cycles=None,
                              change_transport_start_to_report_cycles=None,
                              candidate_ingress_commit_to_decoder_done_cycles=None)
                if kind == 'transport':
                    a, b = current_fences[key], before_fences[key]
                    result.update(baseline_transport_start_to_report_cycles=b['elapsed_cycles'],
                                  candidate_transport_start_to_report_cycles=a['elapsed_cycles'],
                                  change_transport_start_to_report_cycles=a['elapsed_cycles']-b['elapsed_cycles'],
                                  candidate_ingress_commit_to_decoder_done_cycles=a['decoder_done_cycle']-a['ingress_commit_cycle'])
                rows.append(result)
    report = dict(schema='v115-actual-component-transport-cycle-comparison-v1',
                  status='MEASURED_RTL_CYCLES_CONDITIONAL_CLOCK_CONVERSIONS_ONLY',
                  qualification=dict(path=rel(selected_path), sha256=sha(selected_path)),
                  baseline=dict(path=rel(baseline_path), sha256=sha(baseline_path), native_receipt=rel(BASE_NATIVE), native_receipt_sha256=BASE_NATIVE_SHA),
                  canonical_oracle=dict(path=rel(ORACLE), sha256=ORACLE_SHA),
                  source_sha256={rel(Path(__file__).resolve()):sha(Path(__file__))},
                  selected_input_sha256=pins, successful_component_case_profiles=24,
                  successful_transport_case_profiles=24, rows=rows, profiles=summary(rows),
                  candidate_contract=candidate['contract'], baseline_contract=baseline['contract'],
                  assumed_conversion_clocks_Hz=[100000000, 125000000],
                  strict_under10ms_at125MHz_requires_fewer_than_cycles=BUDGET,
                  conditional_30fps_service_budget_cycles_at125MHz=125000000/30,
                  achieved_clock_validated_by_this_ledger=False, hardware_30fps=False,
                  complete_validated_decode_under10ms=False, full_frame_publication=False,
                  limits=[
                      'Actual component/transport bench cycles; not host capture/encode, network, ESP32/QSPI firmware, scanout or end-to-end latency.',
                      'First byte is the first accepted decoder byte. Transport begins earlier: elapsed_cycles includes command, finite-FIFO prefill and report time; it is not first transport-byte latency.',
                      'Decoder done and last canonical pixel are provisional component fences. Complete C2/HUD seals, PCTL1 parent publication and display ownership are not qualified.',
                      'Transport normal 12 cases are paired with their own reports; two abort/reset retry cases per seed are functional evidence and excluded from latency distributions.',
                      'Failed frames and their provisional prefixes are excluded. Successful full canonical sample arrays match frozen V113, which remains the oracle.',
                      'V114 B125 is the source identity of the baseline, not an achieved 125-MHz clock. Its retained optimized proofs are not rerun here.',
                      'Profile0 is deterministic fast service. Profile1 retains seeded policy, but pipeline changes shift random draw times; deltas are actual observations, not isolated combinational savings.',
                      'Extra preparation edges trade cycle count for shorter timing cones; their overlapping/stalled whole-case cost must be measured, not assumed to equal the sum of local bubbles.',
                      '100/125-MHz conversions and 30-fps service budgets are arithmetic assumptions; no achieved clock, full-parent decode, sustained hardware FPS or validated under-10-ms result is claimed.'])
    AREA.mkdir(parents=True, exist_ok=True)
    (AREA/'performance.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    with (AREA/'performance.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report['profiles'], sort_keys=True))


if __name__ == '__main__':
    main()
