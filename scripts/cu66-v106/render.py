#!/usr/bin/env python3
"""Deterministically render V106 handoff documents from final audited evidence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'
DOCS = ROOT / 'docs/cu66-v106'
STAGES = ('synth', 'place', 'route')
RESOURCE_KEYS = ('total_LUT', 'LUTRAM', 'FF', 'RAMB36', 'RAMB18', 'DSP')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def obj(path):
    return json.loads(path.read_text())


def bound(pin):
    path = ROOT / pin['path']
    assert sha(path) == pin['sha256'], ('pinned input drift', pin['path'])
    return obj(path)


def link(path, label=None):
    return '[' + (label or path) + '](../../' + path + ')'


def signed(value):
    return f'{value:+,}'


def stage_row(name, stage, value):
    r, t = value['resources'], value['timing']
    return (f"| {name} | {stage} | {r['total_LUT']:,} | {r['LUTRAM']:,} | {r['FF']:,} | "
            f"{r['RAMB36']} / {r['RAMB18']} | {r['DSP']} | {t['WNS_ns']:+.3f} |")


def focused_evidence(summary, source):
    # These fixed evidence entrypoints are independently bound by the source
    # audit; additional summary.focused pins may be added without changing prose.
    bindings = source.get('input_sha256', source.get('input_hashes', {}))
    def read(name):
        path = AREA / name
        rel = str(path.relative_to(ROOT))
        assert rel in bindings and sha(path) == bindings[rel], ('focused input not audit-bound', rel)
        return obj(path)
    math, plan, context = [read(n + '/results.json') for n in ('math', 'plan', 'context')]
    assert math['status'] == plan['status'] == context['status'] == 'PASS'
    storage_pin = read('locality/probe-results.json')
    rice_pin = read('rice/probe-results.json')
    storage = bound(dict(path=storage_pin['selected_receipt'], sha256=storage_pin['sha256']))
    rice = bound(dict(path=rice_pin['selected_receipt'], sha256=rice_pin['sha256']))
    assert storage['status'] == 'PASS_ACTUAL_INVERSE_STORAGE_EQUIVALENCE'
    assert rice['status'] == 'PASS_ACTUAL_RICE_CACHE_EQUIVALENCE'
    # Check any explicitly supplied summary pins too, including root-added
    # follow-up fields, while tolerating explanatory scalar/dictionary fields.
    for value in summary.get('focused', {}).values():
        if isinstance(value, dict) and {'path', 'sha256'} <= value.keys():
            bound(value)
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, dict) and {'path', 'sha256'} <= nested.keys():
                    bound(nested)
    extras = {}
    if 'prefix' in source.get('candidate_sources', {}):
        pref = read('prefix/probe-results.json')
        extras['prefix'] = bound(dict(path=pref['selected_receipt'], sha256=pref['sha256']))
        assert extras['prefix']['status'] == 'PASS_ACTUAL_PREFIX_EQUIVALENCE'
    if 'telemetry' in source.get('candidate_sources', {}):
        extras['telemetry'] = read('telemetry/results.json')
        assert extras['telemetry']['status'] == 'PASS'
    if 'suffix' in source.get('candidate_sources', {}):
        selected_suffix = read('suffix/probe-results.json')
        extras['suffix'] = bound(dict(path=selected_suffix['selected_receipt'], sha256=selected_suffix['sha256']))
        assert extras['suffix']['status'] == 'PASS_ACTUAL_SUFFIX_EQUIVALENCE'
    if 'idct' in source.get('candidate_sources', {}):
        extras['idct'] = read('idct/trace-audit.json')
        assert extras['idct']['status'] == 'PASS'
    if 'producer_cache' in source.get('candidate_sources', {}):
        extras['producer_cache'] = read('producer-cache/results.json')
        assert extras['producer_cache']['status'] == 'PASS_MODEL_AND_EXACT_SOURCE_RECIPES'
        assert extras['producer_cache']['actual_RTL_run'] is False
    if 'ingress' in source.get('candidate_sources', {}):
        selected_ingress = read('ingress/probe-results.json')
        extras['ingress'] = bound(dict(path=selected_ingress['selected_receipt'], sha256=selected_ingress['sha256']))
        assert extras['ingress']['status'] == 'PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE'
    if 'suffix24' in source.get('candidate_sources', {}):
        extras['suffix24'] = read('suffix24/results.json')
        assert extras['suffix24']['status'] == 'PASS_EXACT_PROJECTION_AND_RECIPES' and extras['suffix24']['actual_RTL_run'] is False
    for component, directory in [('scratch', 'scratch'), ('idct_area', 'idct-area')]:
        if component in source.get('candidate_sources', {}):
            extras[component] = read(directory + '/results.json')
            assert extras[component]['status'] == 'PASS' and extras[component]['actual_RTL_run']
    if 'idct_area' in extras:
        unit = read('idct-area/unit-synthesis-comparison.json')
        assert unit['status'] == 'UNIT_SYNTHESIS_EVIDENCE_COMPLETE' and unit['all_settings_matched']
        receipt = bound(unit['selected_receipt'])
        assert receipt['status'] == 'SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN' and receipt['observed_exit_code'] == 0
        for variant in unit['variants'].values():
            for path, digest in variant['reports'].items():
                assert path in bindings and sha(ROOT / path) == digest == bindings[path]
        extras['idct_area_unit'] = unit
    return math, storage, plan, context, rice, extras


def source_tables(summary, source):
    variants = sorted({lane['variant'] for lane in summary['paired_regression']['lanes']})
    mapping_rows = []
    pins = source.get('input_sha256', source.get('input_hashes', {}))
    for name in variants:
        p = AREA / 'regression' / name / 'canonical' / 'results.json'
        rel = str(p.relative_to(ROOT))
        assert rel in pins and sha(p) == pins[rel], ('lane input not audited', rel)
        lane = obj(p)
        assert lane['status'] == 'PASS' and lane['exact_same_seed_transcripts_events_cycles']
        mapping = dict(lane['baseline_overrides'])
        mapping.update({row['original']: row['path'] for row in lane['candidates']})
        for original, replacement in sorted(mapping.items()):
            digest = lane['source_sha256'][replacement]
            assert sha(ROOT / replacement) == digest
            mapping_rows.append(f'| {name} | `{original}` | {link(replacement)} | `{digest}` |')
    recipes = []
    for path, digest in sorted(pins.items()):
        name = Path(path).name
        if (path.startswith('fpga/experiments/cu66-v106-') and
                (name in ('edit-proof.json', 'edit-recipe.json') or name.endswith('.recipe.json'))):
            assert sha(ROOT / path) == digest, ('recipe drift', path)
            recipes.append((path, digest))
    assert recipes, 'No audit-bound source recipes'
    recipe_rows = [f'| {link(path)} | `{digest}` |' for path, digest in sorted(set(recipes))]
    return '\n'.join(mapping_rows), '\n'.join(recipe_rows)


def render(summary, selection):
    assert summary['status'] == 'PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN'
    audits = {Path(pin['path']).name: bound(pin) for pin in summary['audits']}
    source, native = audits['source-audit.json'], audits['native-audit.json']
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert selection['baseline_revision'] == summary['baseline_revision'] == source['baseline_revision'] == native['baseline_revision']
    assert bound(summary['next_study_selection']) == selection
    assert bound(selection['native_audit']) == native
    assert not native.get('pending_variants')
    physical_pin = summary.get('physical_locality')
    if physical_pin:
        physical = bound(physical_pin)
        assert physical['status'] == 'PASS_EVIDENCE' and bound(physical['native_audit']) == native
    postroute_section = ''
    diagnostic = summary.get('postroute_diagnostic')
    if diagnostic:
        diagnostic_audit = bound(diagnostic['audit'])
        diagnostic_receipt = bound(diagnostic['receipt'])
        assert diagnostic_audit['status'] == 'RETAINED_DIAGNOSTIC_AUDITED'
        assert diagnostic_audit['before'] == diagnostic['before'] and diagnostic_audit['after'] == diagnostic['after']
        assert not diagnostic['selected_or_promoted'] and not diagnostic_audit['selected_or_promoted']
        assert diagnostic_receipt['status'] == 'DIAGNOSTIC_FINISHED_REVIEW_REQUIRED' and diagnostic_receipt['observed_exit_code'] == 0
        before, after = diagnostic['before']['timing'], diagnostic['after']['timing']
        postroute_section = (f"A separate, **unselected post-route diagnostic** reopened the original closure route and ran AggressiveExplore once: WNS changed from {before['WNS_ns']:+.3f} to {after['WNS_ns']:+.3f} ns ({after['WNS_ns'] - before['WNS_ns']:+.3f} ns), with {after['setup_failing_endpoints']:,} setup endpoints still failing. It is outside the six Default-flow source trials and does not replace the selected source or meet 100 MHz. [Diagnostic details](postroute-probe.md) and the [portable report audit](../../experiments/python-gamebub-v106/postroute/report-audit.json) retain its separate strategy, reports and scope.")
    math, storage, plan, context, rice, extra_focused = focused_evidence(summary, source)
    mapping_rows, recipe_rows = source_tables(summary, source)
    paired = summary['paired_regression']
    lane_modes = {(r['variant'], r['mode']) for r in paired['lanes']}
    variants = sorted({v for v, _ in lane_modes})
    assert all((name, mode) in lane_modes for name in variants for mode in ('fresh', 'canonical'))
    qualification = summary['qualification']
    met = qualification['component_100MHz_internal_timing_target_met']
    wns = selection['timing']['WNS_ns']
    assert not met or wns >= 0
    for key in ('hardware_30fps_validated', 'complete_FPGA_decode_under10ms_validated', 'hardware_test_performed'):
        assert not qualification[key], ('unexpected hardware claim; update renderer deliberately', key)
    target = ('The selected component meets the fixed **100 MHz internal OOC timing target** in its recorded route; '
              'parent/board and product qualification remain open.' if met else
              f'The fixed **100 MHz internal OOC timing target remains unmet**: selected routed setup WNS is **{wns:+.3f} ns**.')
    control = summary['native']['control']['stages']['route']
    selected = selection['selected_variant']
    selection_line = (f'The selected next-study source is **{selected}**, with routed WNS **{wns:+.3f} ns**, '
                      f"a **{selection['setup_WNS_change_from_V105_ns']:+.3f} ns** change from the selected V105 geometry control.")
    rows = [stage_row('V105 geometry control', stage, summary['native']['control']['stages'][stage])
            for stage in STAGES if stage in summary['native']['control']['stages']]
    attempts = sorted(summary['native']['variants'], key=lambda x: (x['variant'], x['receipt']['path']))
    for attempt in attempts:
        bound(attempt['receipt'])
        for stage in STAGES:
            if stage in attempt['stages'] and 'resources' in attempt['stages'][stage]:
                rows.append(stage_row(attempt['variant'], stage, attempt['stages'][stage]))
    failures = []
    for attempt in attempts:
        if 'route' not in attempt['stages']:
            receipt = bound(attempt['receipt'])
            exit_code = receipt['observed_exit_code']
            cause = 'watchdog timeout' if exit_code == 124 else 'tool/build failure'
            synth = attempt['stages'].get('synth')
            synthesis = (f" Synthesis WNS {synth['timing']['WNS_ns']:+.3f} ns is an estimate only." if synth else '')
            failures.append(f"**{attempt['variant']}: {cause}**, exit {exit_code}, {receipt['wall_seconds']:.3f} s; no placement/routing result was retained.{synthesis} The attempt remains in the [native audit](../../experiments/python-gamebub-v106/native-audit.json), without routed target qualification.")
    failure_section = '\n\n'.join(failures)
    native_rows, ram_rows = [], []
    deferred = set(summary['native']['deferred_native_variants'])
    measured = {a['variant'] for a in attempts}
    for name in sorted(set(variants) | measured):
        functional = 'fresh + canonical, paired PASS' if name in variants else '**Excluded/rejected trial; required paired PASS absent**'
        records = [a for a in attempts if a['variant'] == name]
        if records:
            outcome = '<br>'.join(a['status'] + ('; **no completed route**' if 'route' not in a.get('stages', {}) else '') for a in records)
            receipt = '<br>'.join(link(a['receipt']['path'], Path(a['receipt']['path']).parent.name) for a in records)
        else:
            assert name in deferred, ('native outcome neither measured nor deferred', name)
            outcome, receipt = '**Unmeasured: native run deferred**', '—'
        native_rows.append(f'| {name} | {functional} | {outcome} | {receipt} |')
    for name, attempt in sorted(native['measured_variants'].items()):
        stage = attempt.get('stages', {}).get('route')
        if not stage:
            continue
        assert 'distributed_RAM' in stage, ('missing native distributed-memory ledger', name)
        coeff = [r for r in stage['distributed_RAM']
                 if 'coefficients_reg' in r['instance'] or 'coefficient_banks' in r['instance']]
        counts = Counter(r['primitive'] for r in coeff)
        description = ', '.join(f'{primitive} × {count:,}' for primitive, count in sorted(counts.items())) or '0 named coefficient RAM objects'
        transform = next((r for r in stage['hierarchy'] if r['instance'] == 'transform'), None)
        ram_rows.append(f"| {name} | {description} | {transform['LUTRAM']:,} | {transform['FF']:,} |" if transform else
                        f'| {name} | {description} | unavailable | unavailable |')
    delta_rows = [f"| {key} | {control['resources'][key]:,} | {selection['resources'][key]:,} | {signed(selection['resource_delta_from_V105'][key])} |"
                  for key in RESOURCE_KEYS]
    all_delta_rows = []
    for attempt in attempts:
        route = attempt['stages'].get('route', {})
        if 'resources' not in route:
            continue
        delta = [signed(route['resources'][k] - control['resources'][k]) for k in RESOURCE_KEYS]
        all_delta_rows.append('| ' + attempt['variant'] + ' | ' + ' | '.join(delta) +
                              f" | {route['timing']['WNS_ns'] - control['timing']['WNS_ns']:+.3f} |")
    composition = bound(summary['composition'])
    assert composition['both_orders_identical'] and composition['status'] == 'PASS'
    math_cases = math['terminal_verdict']['cases']
    plan_v = next(v for v in plan['terminal_verdicts'] if v.get('type') == 'plan_verdict')
    hazards = next(v for v in plan['terminal_verdicts'] if v.get('type') == 'scratch_hazards_verdict')
    context_v = context['terminal_verdict']
    rice_edges = rice['total_clock_edges']
    full_rice = rice['runs'][0]['historical_verdict']
    storage_edges = storage['total_clock_edges']
    focused_rows = [
        f'| Coordinate helpers | {math_cases:,} inputs: all four binary planes × 8,192 tile values; narrow and LUT helpers retain original truncation/invalid-domain behavior. | [Math results](math-results.md) |',
        f'| Coefficient storage | {storage_edges:,} whole-module edges; both 64-word banks checked each edge; 48 historical boundary cases and 15 directed checks per seed, plus prepared states and same-edge write/failure cases. | [Storage results](locality-results.md) |',
        f"| Scratch PLAN | {plan['model']['rows']:,} exact modular prefix rows, all {plan['model']['all17bit_block_values_exercised']:,} 17-bit block values, {plan_v['clocked_begin_cases']:,} clocked begin cases; {hazards['directed_checks']} accepted-write hazard checks over {hazards['edges']} edges. | [PLAN results](plan-results.md) |",
        f"| Context divmod | {context['geometry_verdict']['cases']:,} actual full32 geometry cases, including {context['geometry_verdict']['random_full32_cases']:,} random full32 cases; {context_v['cases']} real-interface fixtures × {context_v['configurations']} configurations, {context_v['directed_checks']} directed checks. | [Context results](context-results.md) |",
        f"| Rice caches | {rice_edges:,} whole-module edges; complete {full_rice['cases']:,}-vector corpus × {full_rice['configurations']} configurations, {full_rice['requests_per_configuration']:,} golden requests/configuration and {full_rice['directed_checks']} directed checks per seed; full32 cache identities and per-clock arithmetic/counter/reservoir oracle. | [Rice results](rice-results.md) |",
    ]
    if 'prefix' in extra_focused:
        pref = extra_focused['prefix']
        focused_rows.append(f"| Balanced Rice prefix | {pref['total_clock_edges']:,} whole-module edges; each seed exhausts 524,288 pattern/window cases and 8,320 availability corners, plus the complete generic Rice suite; late window clamp follows a balanced first-one tree. | [PREFIX results](prefix-results.md) |")
    if 'telemetry' in extra_focused:
        telemetry = extra_focused['telemetry']['terminal_verdict']
        focused_rows.append(f"| Telemetry | {telemetry['counter_words']} counter words × {telemetry['carry_positions']} carry positions; {telemetry['prepared_cases']:,} prepared cases/{telemetry['prepared_edges']:,} prepared edges, plus {telemetry['historical_edges']:,} historical pipeline edges. | [Telemetry results](telemetry-results.md) |")
    if 'suffix' in extra_focused:
        suffix = extra_focused['suffix']
        focused_rows.append(f"| Selected SUFFIX | {suffix['total_clock_edges']:,} whole-module edges; 12,480 additional suffix-domain cases/seed plus the full generic corpus. Only unconsumed suffix/decoded private values outside SUFFIX may differ; public/common checks remain unconditional. | [SUFFIX results](suffix-results.md) |")
    if 'idct' in extra_focused:
        idct = extra_focused['idct']
        focused_rows.append(f"| IDCT operands | {idct['total_clock_edges']:,} edges/{idct['total_multiply_edges']:,} multiply edges, {idct['independent_integer_gold_tiles']:,} independent integer-golden tiles, with directed reset/abort coverage across all ten states. | [IDCT results](idct-results.md) |")
    if 'producer_cache' in extra_focused:
        cache = extra_focused['producer_cache']
        focused_rows.append(f"| Producer cell cache | {cache['transition_model_rows']:,} Python transition rows/{cache['helper_domain_cases']:,} helper inputs and exact source recipes. This is model-only component evidence; live cache assertions are checked separately in required paired pipeline lanes. | [Producer cache results](producer-cache-results.md) |")
    if 'ingress' in extra_focused:
        ingress = extra_focused['ingress']
        focused_rows.append(f"| Live ingress replay cache | {ingress['total_clock_edges']:,} whole-pipeline clock edges, 5,760 prepared full32 boundary/mode/guard cases per seed; all 47 ingress public outputs and independent replay/cache/counter and child Rice reservoir oracles. Inactive private bits/last alone are unqualified and unconsumed. | [Ingress results](ingress-results.md) |")
    if 'scratch' in extra_focused:
        runs = extra_focused['scratch']['runs']
        focused_rows.append(f"| Scratch word predecode | {sum(r['verdict']['clock_edges'] + r['historical_verdict']['edges'] for r in runs):,} whole-module clocks including {sum(r['historical_verdict']['edges'] for r in runs):,} historical hazard clocks; all sixteen byte offsets/four banks, independent cache-word/head oracles, corrupt responses and accepted-write hazard suite. | [Scratch results](scratch-results.md) |")
    if 'idct_area' in extra_focused:
        runs = extra_focused['idct_area']['runs']
        focused_rows.append(f"| IDCT area repair | {sum(r['verdict']['clock_edges'] for r in runs):,} whole-module clocks/{sum(r['verdict']['multiply_edges'] for r in runs):,} multiply edges, 4,303 independent integer-golden tiles and all ten abort states. The failed earlier area candidate remains retained separately. | [IDCT area results](idct-area-results.md) |")
    if 'suffix24' in extra_focused:
        projection = extra_focused['suffix24']
        focused_rows.append(f"| Private SUFFIX projection | {projection['exhaustive_boundary_pattern_cases'] + projection['full_width_random_cases']:,} model checks and an exact two-edit low24 projection recipe; model/source-only standalone evidence, with strict paired production RTL qualification required separately. No unused-signal warning is waived. | [Projection model](../../experiments/python-gamebub-v106/suffix24/results.json) |")
    unit_section = ''
    if 'idct_area_unit' in extra_focused:
        unit = extra_focused['idct_area_unit']
        unit_rows = []
        for name in ('original', 'prefetch', 'shared'):
            v = unit['variants'][name]
            unit_rows.append(f"| {name} | {v['synthesis_slice_LUTs']:,} | {v['synthesis_slice_registers']:,} | {v['synthesis_DSPs']} | {v['synthesis_estimated_worst_slack_ns']:+.3f} |")
        unit_section = '\n## Matched isolated IDCT synthesis screen\n\n' + ('The independently pinned [unit comparison](../../experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json) uses the same part, 10 ns clock, tool/settings and rebuilt original/first-prefetch/shared-selector sources. These are **unit synthesis** values, distinct from complete-top hierarchy or routed metrics.\n\n| IDCT unit | Slice LUTs | Registers | DSPs | Estimated setup slack (ns) |\n| --- | ---: | ---: | ---: | ---: |\n' + '\n'.join(unit_rows) + f"\n\nThe shared selector changes unit LUTs by {unit['shared_minus_original_LUTs']:+,} versus original and {unit['shared_minus_prefetch_LUTs']:+,} versus the first prefetch. This supports the area-repair preflight; it does not establish whole-top fit, placed/routed timing, parent input arrival or hardware latency/FPS. The failed fifth full-top placement remains retained separately.\n")
    measured_commands = []
    for name in dict.fromkeys(a['variant'] for a in sorted(attempts, key=lambda a: a['receipt']['path'])):
        builders = {
            'lut': 'scripts/cu66-v106/build.py',
            'lut-storage-plan': 'scripts/cu66-v106/followup/build.py',
            'closure': 'scripts/cu66-v106/followup/build.py',
            'closure-prefix-telemetry': 'scripts/cu66-v106/final/build.py',
            'guarded-suffix-idct-cache': 'scripts/cu66-v106/pipeline/build.py',
            'local-guards-scratch-area': 'scripts/cu66-v106/locality_final/build.py',
        }
        builder = builders[name]
        measured_commands.append(f'python3 {builder} --variant {name} --run')
    native_commands = '\n'.join(measured_commands)
    extra_focused_commands = '\n'.join(f'python3 scripts/cu66-v106/{name}.py' for name in ('prefix', 'telemetry', 'suffix', 'idct', 'ingress', 'scratch', 'idct_area') if name in extra_focused)
    if 'suffix24' in extra_focused:
        extra_focused_commands += '\npython3 scripts/cu66-v106/suffix24.py --verify'
    if 'producer_cache' in extra_focused:
        extra_focused_commands += '\npython3 scripts/cu66-v106/producer_cache.py --verify'
    if 'idct_area_unit' in extra_focused:
        extra_focused_commands += '\npython3 scripts/cu66-v106/idct_area_unit.py --run\npython3 scripts/cu66-v106/idct_area_analyze.py'
    functional_rows = []
    for lane in sorted(paired['lanes'], key=lambda r: (r['variant'], r['mode'])):
        bound(lane)
        functional_rows.append(f"| {lane['variant']} | {lane['mode']} | {lane['case_profile_runs']} | {lane['directed_checks']} | {link(lane['path'], 'PASS receipt')} |")
    readme = f'''# V106: fixed-clock decoder timing work

{target}

{selection_line} This is experimental component source selection from one implementation run per measured variant. It preserves **{summary['resolution'][0]}×{summary['resolution'][1]}**, the **{summary['packet_cap_bytes']:,}-byte CS88 cap**, the codec profile and the tested public cycle schedule. No compression, image-quality or network-bitrate improvement is measured here.

{postroute_section}

{failure_section}

## Changes and focused proofs

The selected map retains inherited V105 admission/reconstruction changes. V106 studies exact coordinate helpers and explicitly banked coefficient registers, then uses actual failing paths to add cycle-preserving fixes: parallel modular scratch-layout prefixes, full32 context divide/remainder tables with bounded correction, cached Rice remaining-bit counts, balanced prefix rank, selected-SUFFIX extraction, guarded telemetry and IDCT operand/producer-address caches where selected. No validation, backpressure, owner/cancellation, error priority or clock requirement is removed.

| Experiment | Retained evidence | Details |
| --- | --- | --- |
''' + '\n'.join(focused_rows) + f'''

These focused scopes differ. Exhaustive finite helper domains and exact algebra establish the stated arithmetic identities; prepared-state probes do not establish complete packet reachability. Historical/interface suites and paired integration provide additional behavioral evidence. The selected-SUFFIX specialization allows only its unused private suffix/decoded values to differ outside SUFFIX; all public outputs are checked every edge. The producer-address cache has a model-only standalone proof and live assertions in full paired pipeline lanes. The Rice C++ oracle checks every edge; historical Rice trace checkpoints are sampled every 256 edges plus reset/start, while prepared traces log every edge. The offline Rice checker verifies the recorded checkpoints and exact modular algebra, not omitted transitions. None is a four-state, complete formal or mapped-netlist equivalence proof.

The storage and helper recipes compose to identical bytes in both orders, verified by the {link(summary['composition']['path'], 'composition proof')}. The PLAN/context/Rice/PREFIX/telemetry/SUFFIX/IDCT/producer-cache source recipes retain complete production bodies outside their exact edits. Source hashes, retained original bodies, strict compiler commands, finite watchdogs and attempt outcomes are checked by the {link('experiments/python-gamebub-v106/source-audit.json', 'independent source/functional audit')}.

## Paired integration

**{len(paired['lanes'])} lanes pass {paired['total_case_profile_runs']:,} case/profile runs and {paired['total_directed_checks']:,} directed checks** at seeds 106401/106402. The initial six variants and {len(variants) - 6} adaptive follow-up/final/locality variants each run fresh and canonical workloads. Baseline/candidate transcripts, events and cycle counters match exactly; canonical bytes match where applicable. Counts include both implementations, seeds, profiles and expected rejects; they are not unique displayed frames or hardware FPS.

Fresh lanes cover admission, coefficients and inverse-transform behavior; canonical lanes also cover reconstruction. The complete per-lane receipts are listed in the [native and functional comparison](vendor-comparison.md).

## Selected source and integration

Apply `source_overrides` from the {link('experiments/python-gamebub-v106/selection.json', 'selected-source manifest')} to the frozen source list, compiling exactly one production file per module. The native decoder closure is 17 files targeting `xc7a100tcsg324-1`. The fresh-only producer override is retained for behavioral reproduction and filtered from the native canonical closure. Keep focused wrappers, prepared-state controls and duplicate module adapters in verification source sets only.

The [comparison and source-map tables](vendor-comparison.md) list every variant, recipe and replacement SHA-256. {link('experiments/python-gamebub-v106/summary.json', 'Summary JSON')}, {link('experiments/python-gamebub-v106/native-audit.json', 'native audit')}, {link('experiments/python-gamebub-v106/path-analysis.json', 'actual setup cones')} and {link('experiments/python-gamebub-v106/methodology-resolution.json', 'methodology findings')} retain qualification and reproducibility details. The [physical-locality analysis](physical-locality.md) quantifies the retained top-50 fanout list, control-set totals and threshold-specific congestion observations. Audit `PASS_EVIDENCE` verifies retained records; it is not a timing or hardware pass.

## Reproduce

The existing `gamebub-cu66-v69-build` container supplies Verilator 5.020 and GCC with this repository and its external `/build` mount. Runs use assertions, strict warnings, two compilation jobs and finite timeouts. The shared resource gate uses available RAM and memory pressure; swap alone is not a stop condition. Do not overlap more than two heavy jobs.

```sh
python3 scripts/cu66-v106/math.py
python3 scripts/cu66-v106/locality.py
python3 scripts/cu66-v106/plan.py
python3 scripts/cu66-v106/context.py
python3 scripts/cu66-v106/rice.py
{extra_focused_commands}
python3 scripts/cu66-v106/compose.py
python3 scripts/cu66-v106/run_matrix.py
python3 scripts/cu66-v106/followup/run_matrix.py
python3 scripts/cu66-v106/final/run_matrix.py
python3 scripts/cu66-v106/locality_final/run_matrix.py
python3 scripts/cu66-v106/audit_sources.py
```

For interrupted follow-up/final/locality matrices, resume without replacing hash-current PASS receipts:

```sh
python3 scripts/cu66-v106/continue_matrix.py --runner followup final
python3 scripts/cu66-v106/locality_final/continue_matrix.py --runner locality_final
```

The resume helper verifies existing PASS source/receipt hashes, waits for a stable resource gate and retries only retained host-gate denials, with bounded retries. Compile, simulation, assertion and transcript-mismatch failures stop for investigation; a retained failed or gated attempt is not a functional PASS.

The initial, follow-up, final and locality runners stay frozen independently. The rejected fifth pipeline trial retains its failed fresh compile and explicitly unrun canonical lane; it is excluded from the 24 required PASS lanes and must not be reproduced as a successful pair. Its native placement failure remains a required retained implementation attempt. The {link('scripts/cu66-v106/campaign.py', 'adaptive campaign policy')} records the measured native set and why native controls were deferred; original declarations of potential trials are not claims that every trial was measured. Reproduce only the actual required implementation-attempt campaign below (failed placement remains a retained failure), using the existing legitimate Artix-enabled Vivado 2026.1 installation and license. Each native job retains two CPUs, two tool threads, an 8 GiB limit, a 1,800-second watchdog, the 10 ns comparison clock and Default directives.

```sh
{native_commands}
python3 scripts/cu66-v106/audit_native.py
python3 scripts/cu66-v106/analyze_paths.py
python3 scripts/cu66-v106/methodology.py --write-external
python3 scripts/cu66-v106/physical_locality.py
python3 scripts/cu66-v106/audit_postroute.py
python3 scripts/cu66-v106/summarize.py
python3 scripts/cu66-v106/render.py
python3 scripts/cu66-v106/render.py --check
python3 scripts/cu66-v106/bundle_manifest.py --verify
```

## Qualification still required

The comparison clock is fixed at **100 MHz**; no relaxed clock, false path, waiver or validation deletion supplies a pass. Setup/hold/pulse-width and legality must be assessed from the actual route, together with the retained methodology/DRC/CDC findings. Even an internal OOC timing pass does not supply missing parent clock-source/boundary, I/O or full-system constraints. Single-route measurements do not establish timing robustness across implementation seeds. The [remaining timing plan](remaining-timing-plan.md) pins the earlier closure cones and concrete next experiments; the actual final routed report must govern their priority.

Hardware remains on another system. Parent/board timing, whole-device external-memory service and arbitration, transport/clock-domain integration, complete custom-path integration, **sustained hardware 30 fps** and **validated complete FPGA decoding below 10 ms** remain open. No achieved-Fmax or hardware test is claimed.
'''
    vendor = f'''# V106 measured implementation and source comparison

{target}

{selection_line} Selection requires paired functional parity, completed legal routing and target resource fit, clocked/constrained internal endpoints, no loops, nonnegative hold/pulse slack and zero hold/pulse failures; among eligible routes it prefers setup WNS, then LUT/DSP counts. Negative setup WNS remains a failure of the fixed 10 ns target. One route per measured variant is an experimental comparison, not robustness or achieved-Fmax evidence.

{postroute_section}

{failure_section}

{unit_section}
## Measured stages

All native attempts use Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, the retained 17-file canonical decoder closure, a 10 ns clock loaded before synthesis, Default directives and two threads. Native containers retain two CPUs, 8 GiB and a 1,800-second timeout. Synthesis, placement and routing values are separate stages; compare like stages. Failed placement attempts retain synthesis evidence only and supply no routed WNS, physical-locality result or target pass.

| Variant | Stage | LUTs | LUTRAMs | FFs | RAMB36 / RAMB18 | DSPs | WNS (ns) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
''' + '\n'.join(rows) + f'''

The V105 control is the published selected **geometry** route. The final selected route's same-stage resource deltas are:

| Resource | V105 route | Selected V106 route | Delta |
| --- | ---: | ---: | ---: |
''' + '\n'.join(delta_rows) + f'''

All measured routed variants relative to that same V105 route:

| Variant | Δ LUT | Δ LUTRAM | Δ FF | Δ RAMB36 | Δ RAMB18 | Δ DSP | Δ WNS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
''' + '\n'.join(all_delta_rows) + f'''

## Actual campaign versus deferred controls

{summary['native']['campaign_redirection']['reason']} The {link('scripts/cu66-v106/campaign.py', 'campaign policy')} records its actual routed and synthesis evidence pins. Deferred variants retain functional verification; native resources/timing remain **unmeasured**, without interpolated values or inferred wins. This adaptive set is not an exhaustive factorial comparison.

| Variant | Functional status | Native outcome | Receipt |
| --- | --- | --- | --- |
''' + '\n'.join(native_rows) + '''

## Coefficient memory objects and storage tradeoffs

The retained distributed-RAM ledger includes both macro objects and their physical/logical subcell records. For example, 1,024 `RAM32X1D` objects plus 2,048 `RAMD32` SP/DP rows represent 1,024 parent memories, not 3,072 independent memories or LUTRAM sites. Use the utilization report's LUTRAM count for site accounting; do not add parent and subcell counts. The following table reports the actual named coefficient objects separately from full transform-hierarchy resources:

| Routed variant | Named coefficient objects by primitive | Transform LUTRAMs | Transform FFs |
| --- | --- | ---: | ---: |
''' + '\n'.join(ram_rows) + f'''

Static generated coefficient words can eliminate the tiny two-deep distributed memories while increasing FF use. Shared guards, CE/control-set fanout and other logic still require actual route evaluation. Full-component deltas include every composed edit and synthesis optimization; they are not isolated per-feature area costs. Mode-table BRAM inference is a separately qualified inherited building block and is not assumed present unless the measured variant's source map and RAM ledger contain it.

The {link('experiments/python-gamebub-v106/native-audit.json', 'native audit')} retains primitive RAM/DSP settings, high-fanout, control-set, complexity, congestion, capacity, timing, DRC, methodology and routing-legality evidence, including every terminal failure/stop if present. The {link('experiments/python-gamebub-v106/path-analysis.json', 'setup-path analysis')} records actual source/destination, logic/route delay and logic depth. The [quantitative physical-locality report](physical-locality.md) separates top-50 net samples, finite versus nonfinite slack, control-set/packing metrics and congestion-window thresholds. Report counts and observed settings do not by themselves establish mapped-netlist collision semantics or hardware service latency.

## Per-lane functional evidence

| Variant | Mode | Case/profile runs | Directed checks | Evidence |
| --- | --- | ---: | ---: | --- |
''' + '\n'.join(functional_rows) + f'''

Counts include both implementations, both seeds and scheduled profiles/expected rejects; they are not frame counts. Golden data and cycle-exact equivalence have distinct scopes from routed frequency or complete-system service.

## Exact edit recipes

| Recipe | SHA-256 |
| --- | --- |
''' + recipe_rows + f'''

The {link(summary['composition']['path'], 'composition proof')} records exact both-order LUT-helper/storage composition. Other component recipes target distinct source modules. Module interfaces remain unchanged. Full recipe data includes each original/candidate hash and uniquely anchored exact replacement; use the machine manifests rather than copying snippets from prose.

## All variant source maps

Each row below is a replacement layered over the retained frozen source list. Inherited baseline replacements are included. Fresh-only producer mappings appear for reproducibility but are outside the filtered 17-file native canonical closure. Each replacement hash is verified against its audited paired-lane receipt when rendering.

| Variant | Original source key | Replacement | SHA-256 |
| --- | --- | --- | --- |
''' + mapping_rows + f'''

For integration, use only the selected override set in {link('experiments/python-gamebub-v106/selection.json', 'selection.json')} and compile one production definition per module. Verification adapters are not integration sources. Parent clock/I/O/CDC constraints, actual external-memory arbitration, full-system integration, hardware 30 fps and complete under-10-ms decoding remain open; none follows from these OOC tables.
'''
    # Normalize generated prose only; retained source/report bytes are immutable.
    return {name: '\n'.join(line.rstrip() for line in value.splitlines()) + '\n'
            for name, value in {'README.md': readme, 'vendor-comparison.md': vendor}.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify existing rendered bytes without writing')
    args = parser.parse_args()
    summary, selection = [obj(AREA / name) for name in ('summary.json', 'selection.json')]
    documents = render(summary, selection)
    for name, text in documents.items():
        path = DOCS / name
        if args.check:
            assert path.read_text() == text, ('rendered document drift', name)
        else:
            path.write_text(text)
    print('V106_DOCS_CHECKED' if args.check else 'V106_DOCS_RENDERED')


if __name__ == '__main__':
    main()
