#!/usr/bin/env python3
"""Quantify retained V106 routed fanout/control/congestion reports after audit PASS."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'
DOC = ROOT / 'docs/cu66-v106/physical-locality.md'
LOAD_CATEGORIES = ('clock_enable', 'set_reset', 'data_other', 'clock')
LOAD_DESTINATIONS = ('slice', 'io', 'bram_dsp_other')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path):
    return dict(path=str(path.relative_to(ROOT)), sha256=sha(path))


def cells(line):
    return [part.strip() for part in line.strip().strip('|').split('|')]


def reported_number(token):
    number = float(token)
    return number if math.isfinite(number) else None


def fanout(text):
    assert '-max_nets 50' in text and '-timing -load_types' in text
    rows = []
    for line in text.splitlines():
        if not line.lstrip().startswith('|'):
            continue
        value = cells(line)
        if len(value) != 17 or not value[1].isdigit():
            continue
        loads = {category: {destination: int(value[5 + 3*i + j])
                            for j, destination in enumerate(LOAD_DESTINATIONS)}
                 for i, category in enumerate(LOAD_CATEGORIES)}
        number = int(value[1])
        assert sum(sum(group.values()) for group in loads.values()) == number
        slack = reported_number(value[3])
        delay = reported_number(value[4])
        rows.append(dict(net=value[0], fanout=number, driver=value[2],
                         worst_slack_ns=slack, reported_slack=value[3],
                         has_finite_reported_slack=slack is not None,
                         worst_delay_ns=delay, reported_delay=value[4], loads=loads))
    assert rows and len(rows) <= 50
    assert [r['fanout'] for r in rows] == sorted((r['fanout'] for r in rows), reverse=True)
    load_occurrences = {k: sum(sum(row['loads'][k].values()) for row in rows) for k in LOAD_CATEGORIES}
    finite = [row for row in rows if row['has_finite_reported_slack']]
    return dict(reported_rows=len(rows), requested_max_nets=50, largest=rows[0],
                listed_net_load_occurrences=load_occurrences,
                listed_net_fanout_sum=sum(row['fanout'] for row in rows),
                listed_nets_at_least_1000=sum(row['fanout'] >= 1000 for row in rows),
                listed_nets_at_least_500=sum(row['fanout'] >= 500 for row in rows),
                finite_slack_rows=len(finite), nonfinite_slack_rows=len(rows)-len(finite),
                most_negative_finite_listed_slack_ns=min((row['worst_slack_ns'] for row in finite), default=None),
                rows=rows,
                scope='At most the50 largest reported nets; load occurrences are not unique physical loads/cells, and this is not the global fanout distribution. Nonfinite slack is not finite timing margin.')


def control_sets(text):
    labels = {'Total control sets': 'total_control_sets',
              'Minimum number of control sets': 'minimum_control_sets',
              'Addition due to synthesis replication': 'addition_synthesis_replication',
              'Addition due to physical synthesis replication': 'addition_physical_replication',
              'Unused register locations in slices containing registers': 'unused_register_locations_in_used_slices'}
    out, histogram, distribution = {}, [], []
    for line in text.splitlines():
        if not line.lstrip().startswith('|'):
            continue
        row = cells(line)
        if len(row) == 2 and row[1].isdigit():
            if row[0] in labels:
                out.setdefault(labels[row[0]], int(row[1]))
            elif row[0].startswith('>='):
                histogram.append(dict(reported_interval=row[0], control_sets=int(row[1])))
        if len(row) == 5 and all(x in ('Yes', 'No') for x in row[:3]) and all(x.isdigit() for x in row[3:]):
            distribution.append(dict(clock_enable=row[0] == 'Yes', synchronous_set_reset=row[1] == 'Yes',
                                     asynchronous_set_reset=row[2] == 'Yes', registers=int(row[3]), reported_slices=int(row[4])))
    assert set(labels.values()) <= out.keys()
    assert sum(row['control_sets'] for row in histogram) == out['total_control_sets']
    out.update(histogram=histogram, flip_flop_distribution=distribution,
               register_count_in_distribution=sum(row['registers'] for row in distribution),
               scope='Reported control-set totals and unused register locations inside slices that contain registers; not whole-device free FF capacity. Slice counts from different distribution rows are not assumed disjoint.')
    return out


def congestion(text):
    sections = {'placer_final': dict(windows=[], no_windows_above_threshold=None),
                'initial_estimated_router': dict(windows=[], no_windows_above_threshold=None)}
    section, header = None, None
    for line in text.splitlines():
        if 'Placer Final Level Congestion Reporting' in line:
            section, header = 'placer_final', None
        elif 'Initial Estimated Router Congestion Reporting' in line:
            section, header = 'initial_estimated_router', None
        if section and line.strip().startswith('* No '):
            match = re.fullmatch(r'\* No (?:initial estimated )?congestion windows are found above level (\d+)', line.strip())
            assert match, ('unrecognized congestion statement', line)
            sections[section].update(no_windows_above_threshold=True, threshold_level=int(match[1]), literal_statement=line.strip())
        if not section or not line.lstrip().startswith('|'):
            continue
        row = cells(line)
        if row[0] == 'Direction':
            header = row
            continue
        if header and len(row) == len(header) and row[0] not in ('Direction', ''):
            sections[section]['windows'].append(dict(zip(header, row)))
    for name, result in sections.items():
        assert result['no_windows_above_threshold'] is not None or result['windows'], ('missing congestion result', name)
        if result['windows']:
            assert result['no_windows_above_threshold'] is not True
            result['no_windows_above_threshold'] = False
            result['reported_window_count'] = len(result['windows'])
        else:
            result['reported_window_count'] = 0
    return dict(sections=sections, scope='Literal placer-final and initial-estimated-router congestion-window reports. No windows above threshold5 does not mean no congestion globally, no lower-level congestion, or no routed delay penalty.')


def evidence():
    audit_path = AREA / 'native-audit.json'
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'PASS_EVIDENCE' and not audit.get('pending_variants'), 'Final native audit must PASS before generating this analysis'
    bindings = audit.get('input_hashes', audit.get('input_sha256', {}))
    assert bindings
    variants = []
    for name, attempt in sorted(audit['measured_variants'].items(), key=lambda item: item[1]['path']):
        receipt_path = ROOT / attempt['path']
        assert bindings[str(receipt_path.relative_to(ROOT))] == sha(receipt_path)
        receipt = json.loads(receipt_path.read_text())
        record = dict(variant=name, receipt=pin(receipt_path), native_status=attempt['status'],
                      component_route_finished=attempt.get('component_route_finished', False))
        if not record['component_route_finished']:
            record['scope'] = 'No completed route; no routed physical-locality metrics are asserted.'
            variants.append(record)
            continue
        reports = {}
        for label, filename in [('fanout', 'route-high-fanout.rpt'), ('control_sets', 'route-control-sets.rpt'), ('congestion', 'route-congestion.rpt')]:
            path = receipt_path.parent / 'reports' / filename
            digest = sha(path)
            assert digest == receipt['artifacts'][filename]['sha256'] == bindings[str(path.relative_to(ROOT))]
            assert path.stat().st_size == receipt['artifacts'][filename]['bytes']
            reports[label] = dict(**pin(path), artifact_bytes=path.stat().st_size)
        parsed_fanout = fanout((ROOT / reports['fanout']['path']).read_text())
        parsed_control = control_sets((ROOT / reports['control_sets']['path']).read_text())
        route = attempt['stages']['route']
        assert parsed_control['register_count_in_distribution'] == route['hierarchy'][0]['FF']
        record.update(reports=reports, fanout=parsed_fanout, control_sets=parsed_control,
                      congestion=congestion((ROOT / reports['congestion']['path']).read_text()),
                      route_wns_ns=route['timing']['WNS_ns'], resources=route['hierarchy'][0])
        variants.append(record)
    return dict(schema='v106-physical-locality-evidence-v1', status='PASS_EVIDENCE', native_audit=pin(audit_path),
                analyzer=pin(Path(__file__).resolve()), baseline_revision=audit['baseline_revision'], variants=variants,
                V105_comparison_performed=False,
                scope=['Actual routed V106 variants only; comparable V105 physical-locality reports are not available here.',
                       'Top50 high-fanout rows are a truncated net list, not a global distribution.',
                       'Reported nonfinite reset/input slack is not finite timing margin or a constrained boundary proof.',
                       'Control sets and unused register locations are observed placement/packing metrics, not independent causal feature costs.',
                       'No congestion windows above reported threshold5 does not establish globally congestion-free routing.',
                       'Composed variants change multiple features; differences are not isolated storage/CSA attribution.',
                       'No Fmax, hardware service/FPS/decode latency, parent boundary or full-system signoff claim.'])


def render(result):
    rows, sections = [], []
    first = next((r for r in result['variants'] if r['component_route_finished']), None)
    for variant in result['variants']:
        name = variant['variant']
        if not variant['component_route_finished']:
            rows.append(f"| {name} | no completed route | — | — | — | — | — |")
            continue
        f, c, g = variant['fanout'], variant['control_sets'], variant['congestion']['sections']
        largest = f['largest']
        congestion_summary = '; '.join(f"{key}: " + (f"none reported above level{value['threshold_level']}" if value['no_windows_above_threshold'] else f"{value['reported_window_count']} reported windows") for key, value in g.items())
        rows.append(f"| {name} | {f['reported_rows']} | {largest['fanout']:,} | {c['total_control_sets']:,} | {c['unused_register_locations_in_used_slices']:,} | {f['nonfinite_slack_rows']} | {congestion_summary} |")
        net_rows = []
        for net in f['rows'][:10]:
            loads = {key: sum(value.values()) for key, value in net['loads'].items()}
            slack = f"{net['worst_slack_ns']:+.3f}" if net['has_finite_reported_slack'] else f"nonfinite `{net['reported_slack']}`"
            delay = f"{net['worst_delay_ns']:.3f}" if net['worst_delay_ns'] is not None else f"nonfinite `{net['reported_delay']}`"
            net_rows.append(f"| `{net['net']}` | {net['fanout']:,} | {net['driver']} | {slack} | {delay} | {loads['clock_enable']:,} | {loads['set_reset']:,} | {loads['data_other']:,} | {loads['clock']:,} |")
        nonfinite = [row for row in f['rows'] if not row['has_finite_reported_slack']]
        nonfinite_text = ', '.join(f"`{row['net']}` ({row['driver']}, fanout{row['fanout']}, slack`{row['reported_slack']}`)" for row in nonfinite) or 'none in the retained list'
        report_links = ', '.join(f"[{label}](../../{row['path']}) (`{row['sha256']}`)" for label, row in variant['reports'].items())
        totals = ', '.join(f"{key} {value:,}" for key, value in f['listed_net_load_occurrences'].items())
        change = c['total_control_sets'] - first['control_sets']['total_control_sets']
        sections.append(f'''## {name}

Route WNS is {variant['route_wns_ns']:+.3f} ns. The largest retained net is `{largest['net']}`: {largest['fanout']:,} loads, of which {sum(largest['loads']['set_reset'].values()):,} are reported set/reset loads. The list has {f['listed_nets_at_least_1000']} nets with fanout≥1,000 and {f['listed_nets_at_least_500']} with fanout≥500; these counts refer only to the retained top50. Control sets change by {change:+,} relative to the first measured V106 route ({first['variant']}); this is a composed implementation comparison, not isolated storage/CSA causality.

| Net (largest ten retained) | Fanout | Driver | Worst reported slack (ns) | Worst reported delay (ns) | CE loads | Set/reset loads | Data/other loads | Clock loads |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
''' + '\n'.join(net_rows) + f'''

Across all {f['reported_rows']} listed nets, the load-occurrence totals are {totals}. A physical cell can load several nets, so these sums are not unique registers, cells or device-wide loads. Nonfinite-slack rows: {nonfinite_text}. In particular an OOC reset/input port with `inf` slack has no finite timing margin reported here; it is not an unconstrained-boundary timing pass.

Congestion observations: ''' + '; '.join(value.get('literal_statement', f"{key}: {value['reported_window_count']} windows, full rows retained in JSON") for key, value in g.items()) + f'''. This statement is threshold-specific and does not rule out congestion at level5 or below, transient routing congestion, or large net delays.

Pinned reports: {report_links}.
''')
    return '''# V106 routed physical locality

This analysis quantifies the actual retained high-fanout, control-set and congestion reports after the final native audit passes. It does not run vendor tools. The machine-readable [evidence ledger](../../experiments/python-gamebub-v106/physical-locality.json) binds the native audit, analyzer, receipts and each retained report hash/byte count.

Only V106 measured routes are compared. Comparable V105 physical-locality reports are absent, so no V105 fanout, control-set or congestion delta is inferred. The high-fanout command requests at most50 nets with timing and load types; its rows are a truncated list rather than a global distribution. Header load types comprise clock-enable, set/reset, data/other and clock loads, each split across Slice, IO and BRAM/DSP/OTHER columns.

| Variant | Retained nets | Largest fanout | Total control sets | Unused register locations in used slices | Nonfinite-slack rows | Congestion report observation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
''' + '\n'.join(rows) + '\n\n' + '\n'.join(sections) + '''
## Interpretation and reproduction

Large global cancellation/reset/control nets remain a measured locality burden even after tiny coefficient RAMs are removed. Changing storage, modular layout arithmetic or telemetry can also change control sets, FF counts and placement; these composed trials cannot assign every delta to one feature. Unused register locations reported inside slices with registers are a placement/packing metric, not the whole-device free FF count. Threshold-limited congestion estimates do not establish globally congestion-free routing.

```sh
python3 scripts/cu66-v106/audit_native.py
python3 scripts/cu66-v106/physical_locality.py
```

The analyzer requires `native-audit.json` to report `PASS_EVIDENCE`, then independently rechecks report hashes and byte counts against both the audit's bound inputs and the terminal receipt artifacts. `PASS_EVIDENCE` here verifies provenance and parsing, not timing closure. The fixed100MHz target, parent clock/I/O/CDC and methodology signoff, actual external-memory service, sustained hardware30fps and complete under10ms decoding remain separate gates. No achieved Fmax is derived.
'''


def main():
    result = evidence()
    document = render(result)
    (AREA / 'physical-locality.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    DOC.write_text(document)
    print('V106_PHYSICAL_LOCALITY', result['status'], 'variants', len(result['variants']))


if __name__ == '__main__':
    main()
