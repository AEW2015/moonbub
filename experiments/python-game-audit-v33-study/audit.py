#!/usr/bin/env python3
"""Independent accounting and provenance check for retained v33 experiments."""
from __future__ import annotations
import hashlib
import importlib.util
import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GLOBAL = ROOT / 'experiments/python-game-global-v33-study'
HUD = ROOT / 'experiments/python-game-hud-runs-v33-study'
SHARED = ROOT / 'experiments/python-game-shared-v33-study'
SPLIT = ROOT / 'experiments/python-game-split-v33-study'
STANDARD = ROOT / 'experiments/python-game-standard-v24-study/results.json'
CAP, BINDING, FRAMES = 49152, 60, 48
SCENES = ('mass-effect-2600', 'mass-effect-7200')
POLICIES = ('band_control', 'global_cross', 'global_grid')

spec = importlib.util.spec_from_file_location(
    'audit_v32_helpers_for_v33', ROOT / 'experiments/python-game-audit-v32-study/audit.py')
v32 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v32)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pins(data: dict, label: str) -> int:
    pins = data.get('source_sha256')
    if not isinstance(pins, dict) or not pins:
        raise ValueError(f'{label}: missing source pins')
    for rel, expected in pins.items():
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f'{label}: unsafe source pin')
        if sha(ROOT / p) != expected:
            raise ValueError(f'{label}: source pin mismatch {rel}')
    return len(pins)


def load(path: Path, schema: str) -> dict:
    data = json.loads(path.read_text())
    if data.get('schema') != schema:
        raise ValueError(f'{path}: unexpected schema')
    return data


def audit() -> dict:
    g = load(GLOBAL / 'results.json', 'gamebub-global-v33')
    h = load(HUD / 'results.json', 'gamebub-run-HUD-v33')
    s = load(SHARED / 'results.json', 'gamebub-shared-v33')
    split = load(SPLIT / 'results.json', 'gamebub-split-v33')
    pins = {'global': check_pins(g, 'global'), 'hud': check_pins(h, 'HUD'),
            'shared': check_pins(s, 'shared'), 'split': check_pins(split, 'split')}
    if g.get('physical_30fps_proven') is not False or g.get('unchanged_GM27_wire') is not True:
        raise ValueError('global v33 scope/wire flags mismatch')
    if s.get('physical_30fps_proven') is not False or s.get('unchanged_GM27_wire') is not True:
        raise ValueError('shared v33 scope/wire flags mismatch')
    if split.get('physical_30fps_proven') is not False or split.get('unchanged_GM27_wire') is not True or split.get('causal_campaign') is not False:
        raise ValueError('split probe scope/wire flags mismatch')
    cases = {(c['scene'], c['policy']): c for c in g['cases']}
    if len(cases) != 6 or set(cases) != {(scene, policy) for scene in SCENES for policy in POLICIES}:
        raise ValueError('exact six global-motion cohorts missing')
    hud_cases = {c['scene']: c for c in h['cases']}
    if set(hud_cases) != set(SCENES):
        raise ValueError('exact two HUD scenes missing')
    hud_by_scene = {}
    for scene, case in hud_cases.items():
        if [r['id'] for r in case['rows']] != list(range(FRAMES)):
            raise ValueError(f'{scene}: HUD IDs incomplete or reordered')
        sizes = {r['id']: r['bytes'] for r in case['rows']}
        if any(type(v) is not int or v <= 0 or v > CAP for v in sizes.values()):
            raise ValueError(f'{scene}: invalid accepted HUD bytes')
        if sum(sizes.values()) != case['summary']['new_hud_bytes']:
            raise ValueError(f'{scene}: HUD total mismatch')
        hud_by_scene[scene] = sizes

    rows_out, standard_out = {}, {}
    comparisons = {}
    for scene in SCENES:
        hrows = hud_cases[scene]['rows']
        current_sizes = hud_by_scene[scene]
        standard_out[scene] = {}
        for policy in POLICIES:
            case = cases[(scene, policy)]
            rows = case['rows']
            if [r['id'] for r in rows] != list(range(FRAMES)):
                raise ValueError(f'{scene}/{policy}: IDs incomplete or reordered')
            custom_base = custom_new = sse = samples = max_new = 0
            search_ops = search_fetches = decoder_reads = 0
            analysis_ms = encode_ms = quality_ms = bind_ms = 0.0
            for fid, (row, hudrow) in enumerate(zip(rows, hrows, strict=True)):
                key = fid % 24 == 0
                expected_ref = 0xffffffff if key else fid - 1
                if row['key'] is not key or row['reference_id'] != expected_ref:
                    raise ValueError(f'{scene}/{policy}/{fid}: incorrect own-history reference ID')
                if row['hud_bytes'] != hudrow['hu25_bytes']:
                    raise ValueError(f'{scene}/{policy}/{fid}: archived global packet is not the retained HU25 wire packet')
                if row['binding_bytes'] != BINDING or row['body_bytes'] != row['base_bytes'] + row['hud_bytes'] + BINDING:
                    raise ValueError(f'{scene}/{policy}/{fid}: component byte sum mismatch')
                if row['body_bytes'] > CAP:
                    raise ValueError(f'{scene}/{policy}/{fid}: packet cap exceeded')
                metric = row['hybrid']
                _, n_samples, _ = v32.integer_metric(metric)
                sse += metric['active_squared_error']; samples += n_samples
                custom_base += row['base_bytes']
                complete = row['base_bytes'] + current_sizes[fid] + BINDING
                custom_new += complete; max_new = max(max_new, complete)
                selected = [a for a in row['attempts'] if a['selected']]
                if len(selected) != 1:
                    raise ValueError(f'{scene}/{policy}/{fid}: selected-attempt cardinality')
                decoder_reads += selected[0]['work']['decoder_reference_sample_reads']
                for a in row['analyses'].values():
                    analysis_ms += a['analysis_wall_ms']
                    sea = a.get('search', {})
                    search_ops += sea.get('sad_sample_operations', 0)
                    search_fetches += sea.get('reference_sample_fetches', 0)
                for a in row['attempts']:
                    encode_ms += a['encode_ms']; quality_ms += a['quality_ms']; bind_ms += a['bind_ms']
            mse = sse / samples
            if not math.isclose(mse, case['summary']['active_mse'], rel_tol=1e-13):
                raise ValueError(f'{scene}/{policy}: summary MSE mismatch')
            if custom_base + sum(current_sizes.values()) + FRAMES * BINDING != custom_new:
                raise ValueError('prospective common-HUD byte sum mismatch')
            if not math.isclose(analysis_ms + encode_ms, sum(r['paid_base_encode_ms'] for r in rows),
                                rel_tol=1e-10, abs_tol=1e-5):
                raise ValueError(f'{scene}/{policy}: paid analysis+encode subtotal mismatch')
            if not math.isclose(analysis_ms + encode_ms + quality_ms + bind_ms,
                                sum(r['base_policy_service_ms'] for r in rows), rel_tol=1e-10, abs_tol=1e-5):
                raise ValueError(f'{scene}/{policy}: paid service subtotal mismatch')
            rows_out[f'{scene}/{policy}'] = dict(
                frames=FRAMES, own_accepted_reference_chain=True,
                v32_hud_wire_complete_bytes=case['summary']['complete_bytes'],
                prospective_new_hud_complete_bytes=custom_new,
                prospective_new_hud_max_frame_bytes=max_new, cap_fits=max_new <= CAP,
                active_squared_error=sse, active_channel_samples=samples, active_mse=mse,
                sad_sample_operations=search_ops, search_reference_fetches=search_fetches,
                selected_decoder_reference_sample_reads=decoder_reads,
                paid_work_ms=dict(analysis=analysis_ms, attempted_encode=encode_ms,
                                  quality_scoring=quality_ms, binding_checks=bind_ms,
                                  source_row_sum=analysis_ms + encode_ms + quality_ms + bind_ms),
                shadow_reference_semantics='shadow is the v30 strict selector evaluated on this cohort own accepted-reference history')
            control = cases[(scene, 'band_control')]['summary']
            summary = case['summary']
            comparisons[f'{scene}/{policy}'] = dict(
                complete_byte_delta_vs_control=summary['complete_bytes'] - control['complete_bytes'],
                complete_byte_percent_vs_control=100 * (summary['complete_bytes'] / control['complete_bytes'] - 1),
                active_mse_delta_vs_control=summary['active_mse'] - control['active_mse'],
                active_mse_percent_vs_control=100 * (summary['active_mse'] / control['active_mse'] - 1),
                paid_policy_ms_delta_vs_control=summary['mean_base_policy_service_ms'] - control['mean_base_policy_service_ms'],
                sad_sample_ops_delta_vs_control=summary['sad_sample_operations'] - control['sad_sample_operations'],
                search_reference_fetches_delta_vs_control=summary['search_reference_fetches'] - control['search_reference_fetches'],
                selected_decoder_reads_delta_vs_control=decoder_reads - sum(
                    a['work']['decoder_reference_sample_reads'] for r in cases[(scene, 'band_control')]['rows']
                    for a in r['attempts'] if a['selected']))
            standard_out[scene][policy] = v32.standard_operating_points(
                json.loads(STANDARD.read_text()), scene, current_sizes, mse)

    global_summary = dict(accepted_frames=sum(len(c['rows']) for c in cases.values()),
                          exact_control_packet_ack_pixel_rows=96,
                          actual_candidate_attempts=sum(len(r['attempts']) for c in cases.values() for r in c['rows']),
                          source_pins=pins['global'], same_current_HUD_and_60B=True)
    for case in cases.values():
        if case['policy'] == 'band_control' and case['summary']['complete_bytes'] != sum(r['body_bytes'] for r in case['rows']):
            raise ValueError('global control byte summary mismatch')
    shared = dict(s['summary'])
    if not shared.get('exact_packet_plane_and_output_parity'):
        raise ValueError('shared v33 exact parity flag missing')
    pin_digests = {}
    flat_pins = {}
    for name, data, folder in (('global', g, GLOBAL), ('hud', h, HUD), ('shared', s, SHARED), ('split', split, SPLIT)):
        for rel, digest in data['source_sha256'].items():
            if rel in flat_pins and flat_pins[rel] != digest:
                raise ValueError(f'conflicting source pins for {rel}')
            flat_pins[rel] = digest
        pin_digests[name] = dict(result_sha256=sha(folder / 'results.json'),
                                 source_pin_set_sha256=hashlib.sha256(json.dumps(
                                     data['source_sha256'], sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                                 source_pin_count=pins[name])
    direct_inputs = [
        'experiments/python-game-global-v33-study/results.json',
        'experiments/python-game-hud-runs-v33-study/results.json',
        'experiments/python-game-shared-v33-study/results.json',
        'experiments/python-game-split-v33-study/results.json',
        'experiments/python-game-split-v33-study/benchmark.py',
        'experiments/python-game-split-v33-study/helpers.py',
        'experiments/python-game-split-v33-study/model.py',
        'experiments/python-game-split-v33-study/verify.py',
        'experiments/python-game-split-v33-study/test_model.py',
        'experiments/python-game-split-v33-study/README.md',
        'experiments/python-game-split-v33-study/benchmark.log',
        'experiments/python-game-split-v33-study/verify.log',
        'experiments/python-game-standard-v24-study/results.json',
        'experiments/python-game-audit-v32-study/audit.py',
        'experiments/python-game-audit-v33-study/audit.py',
        'experiments/python-game-audit-v33-study/baseline.json',
        'experiments/python-game-audit-v33-study/test_baseline.py',
    ]
    for rel in direct_inputs:
        flat_pins[rel] = sha(ROOT / rel)
    split_rows = split['rows']
    expected_keys = {(scene, fid) for scene in SCENES for fid in range(12)}
    indexed = {(r['scene'], r['id']): r for r in split_rows}
    if len(split_rows) != 24 or len(indexed) != 24 or set(indexed) != expected_keys:
        raise ValueError('split probe must contain exactly two scenes × ordered IDs 0..11')
    control_bytes = control_sse = selected_bytes = selected_sse = raw_band_bytes = raw_band_sse = qualified = raw_regressions = 0
    selected_splits = []
    for scene in SCENES:
        previous = None
        for fid in range(12):
            row = indexed[(scene, fid)]
            if row['reference_id'] != (0xffffffff if fid == 0 else fid - 1):
                raise ValueError('split probe reference differs from fixed accepted v32 history')
            if row['key'] is not (fid == 0):
                raise ValueError('split probe key cadence mismatch')
            ctrl, out = row['accepted_v32_hybrid'], row['selected_hybrid']
            v32.integer_metric(ctrl); v32.integer_metric(out)
            if (row['control_baseline']['kind'] != 'v32_control'
                    or row['control_baseline']['complete_bytes'] != row['accepted_v32_complete_bytes']
                    or row['control_baseline']['hybrid'] != ctrl):
                raise ValueError('split accepted-control baseline bytes/kind mismatch')
            if row['accepted_v32_complete_bytes'] > CAP or row['selected_complete_bytes'] > CAP:
                raise ValueError('split packet exceeds complete cap')
            control_bytes += row['accepted_v32_complete_bytes']; control_sse += ctrl['active_squared_error']
            selected_bytes += row['selected_complete_bytes']; selected_sse += out['active_squared_error']
            if row['selected_kind'] == 'v32_control':
                if row['selected_complete_bytes'] != row['accepted_v32_complete_bytes'] or out != ctrl:
                    raise ValueError('split fallback is not the actual accepted v32 control')
            elif row['selected_kind'] == 'split16_band':
                trial = next((t for t in row['trials'] if t['kind'] == 'split16_band'), None)
                if trial is None or not trial['qualified'] or not trial['qualifies_against_v32_selected']:
                    raise ValueError('selected split trial failed actual-control admission')
                if (trial['complete_bytes'] != row['selected_complete_bytes']
                        or trial['hybrid'] != out or trial['complete_bytes'] >= row['accepted_v32_complete_bytes']
                        or out['active_squared_error'] > ctrl['active_squared_error']):
                    raise ValueError('selected split packet fails strict byte/RGB guard')
                selected_splits.append([scene, fid])
            else:
                raise ValueError('unknown split selection kind')
            raw = next(t for t in row['trials'] if t['kind'] == 'split16_band')
            for trial in row['trials']:
                qualifies_control = (trial['complete_bytes'] <= CAP
                                     and trial['complete_bytes'] < row['accepted_v32_complete_bytes']
                                     and trial['hybrid']['active_squared_error'] <= ctrl['active_squared_error'])
                if (trial['qualifies_against_v32_selected'] is not qualifies_control
                        or trial['qualified'] is not qualifies_control):
                    raise ValueError('split trial controller-guard flag mismatch')
                qualified += bool(qualifies_control)
            qualifies_control = raw['qualifies_against_v32_selected']
            raw_band_bytes += raw['complete_bytes']; raw_band_sse += raw['hybrid']['active_squared_error']
            raw_regressions += raw['hybrid']['active_squared_error'] > ctrl['active_squared_error']
            if (row['selected_kind'] == 'split16_band') is not qualifies_control:
                raise ValueError('guarded split choice does not match the sole admissible trial')
            previous = row['reference_tag']
    split_summary = split['summary']
    for key, actual in (('baseline_complete_bytes', control_bytes), ('baseline_source_rgb_sse', control_sse),
                        ('selected_complete_bytes', selected_bytes), ('selected_source_rgb_sse', selected_sse),
                        ('raw16_band_complete_bytes', raw_band_bytes), ('raw16_band_source_rgb_sse', raw_band_sse),
                        ('qualified_against_v32_selected_trials', qualified)):
        if split_summary[key] != actual:
            raise ValueError(f'split summary mismatch: {key}')
    if selected_splits != [['mass-effect-7200', 5], ['mass-effect-7200', 7],
                           ['mass-effect-7200', 8], ['mass-effect-7200', 10], ['mass-effect-7200', 11]]:
        raise ValueError('split selected-frame set differs from retained result')
    split_report = dict(source_frames=24, ordered_two_scene_matrix=True, causal_campaign=False,
                        baseline_complete_bytes=control_bytes, selected_complete_bytes=selected_bytes,
                        complete_byte_saving=control_bytes-selected_bytes,
                        baseline_active_rgb_sse=control_sse, selected_active_rgb_sse=selected_sse,
                        active_rgb_sse_saving=control_sse-selected_sse,
                        raw_split16_band_complete_bytes=raw_band_bytes,
                        raw_split16_band_complete_byte_delta_vs_control=raw_band_bytes-control_bytes,
                        raw_split16_band_active_rgb_sse=raw_band_sse,
                        raw_split16_frames_with_rgb_regression=raw_regressions,
                        raw_split16_strict_guard_qualifications=qualified,
                        selected_split_frames=selected_splits,
                        no_causal_or_cross_study_combined_gain_claim=True)
    return dict(schema='gamebub-python-game-audit-v33', source_pins=pin_digests,
                source_sha256=dict(sorted(flat_pins.items())),
                global_motion=global_summary, cohorts=rows_out,
                comparison_to_control=comparisons,
                same_current_HUD_standard_operating_points=standard_out,
                split_fixed_reference=split_report,
                shared_work_reuse=shared,
                hud_runs={scene: case['summary'] for scene, case in hud_cases.items()},
                claim_boundary='Two reused 48-frame windows and prospective common-HUD accounting; no integrated HX33 plus custom/HEVC/AV1 endpoint, native codec run, hardware fit, or physical 30fps proof.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='require byte-identical current audit.json')
    args = parser.parse_args()
    result = audit()
    encoded = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
    output = HERE / 'audit.json'
    if args.check:
        if not output.is_file() or output.read_bytes() != encoded:
            raise SystemExit('audit.json missing or stale; rerun without --check')
    else:
        output.write_bytes(encoded)
    print(json.dumps({k: result[k] for k in ('global_motion', 'source_pins')}))
