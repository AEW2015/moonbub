#!/usr/bin/env python3
"""Independent bounded audit of retained v30 controller results."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ROOT / 'experiments/python-game-controller-v30-study'
V29_STUDY = ROOT / 'experiments/python-game-controller-v29-study'
V29_AUDIT_PATH = ROOT / 'experiments/python-game-audit-v29-study/audit.py'
BASELINE_STUDY = ROOT / 'experiments/python-game-controller-v29-study'
CAP, HUD_WORDS = 49_152, 21_120
SCENES = ('mass-effect-2600', 'mass-effect-7200')
POLICIES = ('adaptive_control', 'band_strict', 'band_budget')
NO_REF = 0xFFFFFFFF


def _load_v29_audit():
    spec = importlib.util.spec_from_file_location('v29_audit_for_v30', V29_AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V29 = _load_v29_audit()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_object(desc: dict, folder: Path) -> bytes:
    return V29.read_object(desc, folder)


def integer_metric(row: dict) -> tuple[int, int]:
    metric = row['hybrid']
    sse, samples = metric.get('active_squared_error'), metric.get('active_channel_samples')
    if type(sse) is not int or type(samples) is not int or sse < 0 or samples <= 0:
        raise ValueError('invalid integer active RGB SSE/sample metric')
    if metric.get('active_mse') != sse / samples:
        raise ValueError('active MSE does not reconcile with integer totals')
    return sse, samples


def finite_nonnegative(value) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0)


def band_guard_passes(candidate_sse: int, shadow_sse: int, policy: str) -> bool:
    """Compare actual RGB SSE to the same-history incumbent with exact integer math."""
    if policy not in ('band_strict', 'band_budget'):
        raise ValueError('band guard requires a declared modified policy')
    if type(candidate_sse) is not int or type(shadow_sse) is not int or min(candidate_sse, shadow_sse) < 0:
        raise ValueError('band guard requires nonnegative integer SSE')
    allowance = 1 if policy == 'band_budget' else 0
    return 100 * candidate_sse <= (100 + allowance) * shadow_sse


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError('empty rows')
    total = sum(int(r['body_bytes']) for r in rows)
    sse = samples = hud_errors = 0
    for r in rows:
        e, n = integer_metric(r)
        sse += e
        samples += n
        err = r['hybrid'].get('hud_word_errors')
        if type(err) is not int or err < 0:
            raise ValueError('invalid HUD word error count')
        hud_errors += err
    attempts = [a for r in rows for a in r['attempts']]
    analyses = [a for r in rows for a in r['analyses'].values()]
    return dict(frames=len(rows), complete_bytes=total,
                coded_body_Mbps_at30=total * 240 / len(rows) / 1_000_000,
                base_bytes=sum(int(r['base_bytes']) for r in rows),
                hud_bytes=sum(int(r['hud_bytes']) for r in rows),
                binding_bytes=60 * len(rows),
                maximum_complete_bytes=max(int(r['body_bytes']) for r in rows),
                cap_fit_frames=sum(int(r['body_bytes']) <= CAP for r in rows),
                active_squared_error=sse, active_channel_samples=samples, active_mse=sse / samples,
                active_psnr_db=10 * math.log10(65025 / (sse / samples)),
                hud_word_errors=hud_errors, exact_hud_words=len(rows) * HUD_WORDS,
                paid_candidate_encodes=len(attempts),
                mean_paid_base_encode_ms=sum(float(r['paid_base_encode_ms']) for r in rows) / len(rows),
                mean_base_policy_service_ms=sum(float(r['base_policy_service_ms']) for r in rows) / len(rows),
                mean_receiver_ms=sum(float(r['receive_ms']) for r in rows) / len(rows),
                sad_sample_operations=sum(int(a['search']['sad_sample_operations']) for a in analyses),
                search_reference_fetches=sum(int(a['search'].get('reference_sample_fetches', 0)) for a in analyses),
                quiet_blocks=sum(int(a['search'].get('quiet_blocks', 0)) for a in analyses),
                active_blocks=sum(int(a['search'].get('active_blocks', 0)) for a in analyses),
                selected_alternative_planes=sum(int(a['work'].get('selected_alternative_planes', 0))
                                                for a in attempts if a['selected']),
                selected_band_frames=sum(str(r['selected_kind']).endswith('_band') for r in rows),
                selected_changed_blocks=sum(int(a['work'].get('changed_blocks', 0))
                                            for a in attempts if a['selected']),
                selected_removed_coefficients=sum(int(a['work'].get('removed_coefficients', 0))
                                                  for a in attempts if a['selected']),
                same_history_shadow_complete_bytes=sum(int(r['baseline_complete_bytes']) for r in rows),
                same_history_shadow_sse=sum(int(r['baseline_source_sse']) for r in rows),
                ec26_size_counter_calls=sum(int(a['work'].get('ec26_size_counter_calls', 0)) for a in attempts),
                coarse_fallback_frames=[r['id'] for r in rows if r['selected_background'] == 32])


def verify_pins(pins: dict) -> int:
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source_sha256 pins missing')
    for rel, expected in sorted(pins.items()):
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or len(expected) != 64:
            raise ValueError('unsafe source pin')
        target = ROOT / path
        if not target.is_file() or sha(target.read_bytes()) != expected:
            raise ValueError(f'source hash mismatch: {rel}')
    return len(pins)


def source_inventory(pins: dict) -> dict:
    paths = set(pins)
    paths.update({
        'experiments/python-game-controller-v30-study/benchmark.py',
        'experiments/python-game-controller-v30-study/controller.py',
        'experiments/python-game-controller-v30-study/results.json',
        'experiments/python-game-controller-v30-study/replay.json',
        'experiments/python-game-controller-v30-study/verify.py',
        'experiments/python-game-controller-v30-study/verify.log',
        'experiments/python-game-controller-v30-study/run.log',
        'experiments/python-game-controller-v30-study/tests.log',
        'experiments/python-game-controller-v29-study/results.json',
        'experiments/python-game-audit-v29-study/audit.py',
        'experiments/python-game-audit-v30-study/audit.py',
        'experiments/python-game-audit-v30-study/test_audit.py',
        'experiments/python-game-audit-v30-study/README.md',
        'experiments/python-game-audit-v30-study/tests.log',
    })
    out = {}
    for rel in sorted(paths):
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or rel.endswith('/audit.json'):
            raise ValueError('unsafe audit inventory path')
        target = ROOT / path
        if not target.is_file():
            raise ValueError(f'missing audit inventory input: {rel}')
        out[rel] = sha(target.read_bytes())
    return out


def audit(data: dict | None = None, *, require_replay=True) -> dict:
    data = data or json.loads((STUDY / 'results.json').read_text())
    if data.get('schema') != 'gamebub-controller-v30':
        raise ValueError('unexpected v30 controller schema')
    if data.get('physical_30fps_proven') is not False or data.get('unchanged_GM27_wire') is not True:
        raise ValueError('scope or wire profile claim mismatch')
    if data.get('geometry') != dict(coded=[720, 480], active=[720, 405],
                                    exact_hud_words=HUD_WORDS, complete_cap=CAP):
        raise ValueError('geometry, HUD, or complete cap mismatch')
    pin_count = verify_pins(data['source_sha256'])
    cases = {}
    accepted = attempted = reference_links = baseline_parity = 0
    max_bytes = 0
    paired_sources = {}
    for case in data['cases']:
        scene, policy = case['scene'], case['policy']
        if scene not in SCENES or policy not in POLICIES or (scene, policy) in cases:
            raise ValueError('unexpected/duplicate policy case')
        rows = case['rows']
        if [r.get('id') for r in rows] != list(range(48)):
            raise ValueError(f'{scene}/{policy}: rows missing or reordered')
        previous_tag = None
        for fid, row in enumerate(rows):
            key = (fid % 24 == 0)
            ref_id = NO_REF if key else fid - 1
            if row.get('key') is not key or row.get('reference_id') != ref_id:
                raise ValueError(f'{scene}/{policy}/{fid}: key/reference discontinuity')
            pair = read_object(row['packet'], STUDY)
            parsed = V29.parse_pair(pair)
            if len(pair) != row['body_bytes'] or len(pair) > CAP or row['binding_bytes'] != 60:
                raise ValueError('accepted complete byte/cap/binding mismatch')
            if parsed['base_meta']['bytes'] != row['base_bytes'] or parsed['hud_meta']['bytes'] != row['hud_bytes']:
                raise ValueError('accepted base/HUD declared byte mismatch')
            if parsed['base_meta']['reference_id'] != ref_id or parsed['hud_meta']['reference_id'] != ref_id:
                raise ValueError('accepted component reference IDs mismatch')
            if parsed['base_meta']['reference_tag'].hex() != row['reference_tag']:
                raise ValueError('accepted reference tag differs from GM27')
            if key:
                if row['reference_tag'] != bytes(16).hex():
                    raise ValueError('key reference tag must be zero')
            else:
                if row['reference_tag'] != previous_tag:
                    raise ValueError('policy did not reference its previous accepted output')
                reference_links += 1
            if parsed['base_meta']['reconstructed_tag'].hex() != row['reconstructed_tag']:
                raise ValueError('decoded tag mismatch')
            if parsed['hud_meta']['patch_words'] != HUD_WORDS:
                raise ValueError('accepted HUD patch coverage mismatch')
            hud = read_object(row['hud_packet'], STUDY)
            if hud != parsed['hud']:
                raise ValueError('accepted packet HUD differs from retained HUD object')
            ack = read_object(row['ack'], STUDY)
            ack_meta = V29.V28.parse_ja27(ack, parsed)
            am = row['ack_meta']
            if (len(ack) != 65 or ack_meta['frame'] != fid or ack_meta['epoch'] != 25
                    or am.get('frame_id') != fid or am.get('epoch') != 25
                    or am.get('source_slot') != parsed['source'] or am.get('destination_slot') != parsed['destination']
                    or am.get('pair_tag') != parsed['pair_tag'].hex()
                    or am.get('base_tag') != parsed['base_meta']['reconstructed_tag'].hex()
                    or am.get('hud_tag') != parsed['hud_meta']['out_tag'].hex()):
                raise ValueError('accepted ACK fails identity, tag, or size binding')
            if row.get('source_slot') != parsed['source'] or row.get('destination_slot') != parsed['destination']:
                raise ValueError('row slot binding mismatch')
            src_key = (scene, fid)
            paired_sources.setdefault(src_key, row['source_common_yuv_sha256'])
            if paired_sources[src_key] != row['source_common_yuv_sha256']:
                raise ValueError('policy source pairing mismatch')
            if not row['attempts']:
                raise ValueError('no candidate attempts retained')
            attempt_candidates = []
            for a in row['attempts']:
                candidate = read_object(a['packet'], STUDY)
                cp = V29.parse_pair(candidate, enforce_cap=False)
                if len(candidate) != a['complete_bytes'] or a.get('cap_fit') is not (len(candidate) <= CAP):
                    raise ValueError('candidate complete bytes/cap mismatch')
                if cp['base_meta']['reference_id'] != ref_id or cp['base_meta']['reference_tag'].hex() != row['reference_tag']:
                    raise ValueError('candidate uses wrong accepted history')
                if cp['base_meta']['reconstructed_tag'].hex() != a['reconstructed_tag']:
                    raise ValueError('candidate output tag differs from nested GM27')
                if cp['hud'] != hud or cp['hud_meta']['patch_words'] != HUD_WORDS:
                    raise ValueError('candidate changes HUD packet or coverage')
                base = read_object(a['base_packet'], STUDY)
                if base != cp['base'] or len(base) != a['base_bytes']:
                    raise ValueError('candidate base object differs from complete packet')
                integer_metric(a)
                for t in ('encode_ms', 'offline_debug_decode_ms', 'quality_ms', 'bind_ms'):
                    if not finite_nonnegative(a.get(t)):
                        raise ValueError('invalid candidate timing')
                attempt_candidates.append((a, cp, candidate))
                attempted += 1
            expected_kinds = ['zero'] if key else ['zero', 'half32']
            expected_by_bg = {}
            backgrounds = []
            for a, _, _ in attempt_candidates:
                bg = a['background']
                if bg not in backgrounds:
                    backgrounds.append(bg)
            if backgrounds not in ([16], [16, 32]):
                raise ValueError('invalid causal background fallback sequence')
            for bg in backgrounds:
                group = [a for a, _, _ in attempt_candidates if a['background'] == bg]
                kinds = expected_kinds + ([] if policy == 'adaptive_control' else [k + '_band' for k in expected_kinds])
                if [a['kind'] for a in group] != kinds:
                    raise ValueError('candidate family/order incomplete within attempted tier')
                zero = group[0]['hybrid']['active_squared_error']
                for a in group:
                    same_source_sse = a['hybrid']['active_squared_error']
                    if a['kind'].endswith('_band'):
                        continue
                    if a.get('quality_eligible') is not (same_source_sse <= zero):
                        raise ValueError('legacy candidate same-tier quality gate mismatch')
                legacy = [a for a in group if not a['kind'].endswith('_band')]
                incumbent = [a for a in legacy if a['cap_fit'] and a['quality_eligible']]
                baseline = min(incumbent, key=lambda a: a['complete_bytes']) if incumbent else None
                for a in group:
                    if a['kind'].endswith('_band'):
                        permitted = baseline is not None and band_guard_passes(
                            a['hybrid']['active_squared_error'], baseline['hybrid']['active_squared_error'], policy)
                        if a.get('quality_eligible') is not permitted:
                            raise ValueError('band candidate fails strict/budget same-history RGB guard')
                if baseline is None:
                    expected_by_bg[bg] = None
                    continue
                eligible = [baseline] + [a for a in group if a['kind'].endswith('_band') and a['cap_fit'] and a['quality_eligible']]
                expected_by_bg[bg] = (min(eligible, key=lambda a: a['complete_bytes']), baseline)
                if bg != backgrounds[-1]:
                    raise ValueError('fallback tier attempted after a fitting earlier shadow tier')
                break
            expected = next((v for v in expected_by_bg.values() if v is not None), None)
            if expected is None:
                raise ValueError('no fitting incumbent tier')
            chosen, shadow = expected
            selected = [a for a in row['attempts'] if a.get('selected')]
            if len(selected) != 1 or selected[0] != chosen:
                raise ValueError('selected candidate differs from independent tier/size decision')
            if (row['selected_kind'] != chosen['kind'] or row['selected_background'] != chosen['background']
                    or row['baseline_kind'] != shadow['kind']
                    or row['baseline_complete_bytes'] != shadow['complete_bytes']
                    or row['baseline_source_sse'] != shadow['hybrid']['active_squared_error']):
                raise ValueError('row selection or same-history shadow metadata mismatch')
            if chosen['hybrid'] != row['hybrid'] or chosen['reconstructed_tag'] != row['reconstructed_tag']:
                raise ValueError('accepted metrics/tag differ from chosen candidate')
            if read_object(chosen['packet'], STUDY) != pair:
                raise ValueError('accepted packet differs from selected candidate')
            e, n = integer_metric(row)
            if row['hybrid_rgb565_sha256'] != chosen['hybrid_rgb565_sha256']:
                raise ValueError('accepted RGB565 hash differs from chosen candidate')
            paid = sum(float(a['analysis_wall_ms']) for a in row['analyses'].values()) + sum(float(a['encode_ms']) for a in row['attempts'])
            service = paid + sum(float(a['quality_ms']) + float(a['bind_ms']) for a in row['attempts'])
            if any(not finite_nonnegative(v) for v in (row['receive_ms'], row['ack_ms'], row['paid_base_encode_ms'], row['base_policy_service_ms'])):
                raise ValueError('invalid frame timing')
            if any(not finite_nonnegative(a['analysis_wall_ms']) for a in row['analyses'].values()):
                raise ValueError('invalid analysis timing')
            if not math.isclose(paid, row['paid_base_encode_ms'], rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError('paid work omits analyses or a losing candidate encode')
            if not math.isclose(service, row['base_policy_service_ms'], rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError('service time omits candidate quality/binding work')
            previous_tag = row['reconstructed_tag']
            accepted += 1
            max_bytes = max(max_bytes, len(pair))
        expected_summary = summarize(rows)
        if set(case['summary']) != set(expected_summary):
            raise ValueError('summary field set mismatch')
        for name, value in expected_summary.items():
            actual = case['summary'][name]
            if isinstance(value, float):
                if not math.isclose(float(actual), value, rel_tol=1e-10, abs_tol=1e-7):
                    raise ValueError(f'{scene}/{policy}: summary mismatch {name}')
            elif actual != value:
                raise ValueError(f'{scene}/{policy}: summary mismatch {name}')
        cases[(scene, policy)] = case
    if set(cases) != {(s, p) for s in SCENES for p in POLICIES}:
        raise ValueError('incomplete scene/policy matrix')
    v29_data = json.loads((V29_STUDY / 'results.json').read_text())
    v29_cases = {(c['scene'], c['policy']): c for c in v29_data['cases']}
    for scene in SCENES:
        for row, old in zip(cases[(scene, 'adaptive_control')]['rows'], v29_cases[(scene, 'adaptive_lazy')]['rows']):
            if (row['id'] != old['id'] or row['source_common_yuv_sha256'] != old['source_common_yuv_sha256']
                    or read_object(row['packet'], STUDY) != read_object(old['packet'], V29_STUDY)
                    or read_object(row['ack'], STUDY) != read_object(old['ack'], V29_STUDY)
                    or row['hybrid'] != old['hybrid']):
                raise ValueError('adaptive_control does not exactly match v29 adaptive_lazy')
            baseline_parity += 1
    replay_path = STUDY / 'replay.json'
    replay = None
    if replay_path.is_file():
        replay = json.loads(replay_path.read_text())
        verify_replay(replay, cases)
    elif require_replay:
        raise ValueError('deep decode verifier replay is required')
    return dict(schema='gamebub-v30-independent-audit', source_sha256=source_inventory(data['source_sha256']),
                source_pins_verified=pin_count, cases=len(cases), accepted_frames=accepted,
                attempted_candidates=attempted, maximum_complete_bytes=max_bytes,
                exact_hud_words=accepted * HUD_WORDS, accepted_reference_links=reference_links,
                adaptive_v29_exact_parity_rows=baseline_parity, decoded_replay_verified=replay is not None,
                physical_30fps_proven=False,
                claim_boundary='Python host measurements and nominal 30-ID/s byte projections only; no native or physical 30-fps proof.')


def verify_replay(replay: dict, cases: dict) -> None:
    # Exact v30 replay layout is checked here and can only be satisfied by the
    # sibling verifier's retained decode evidence, not a controller import.
    if replay.get('schema') != 'gamebub-v30-replay':
        raise ValueError('unexpected deep replay schema')
    if replay.get('results_sha256') != sha((STUDY / 'results.json').read_bytes()):
        raise ValueError('replay is stale against results.json')
    verifier = STUDY / 'verify.py'
    if not verifier.is_file() or replay.get('verifier_sha256') != sha(verifier.read_bytes()):
        raise ValueError('replay verifier hash mismatch')
    if replay.get('accepted_pairs') != 288 or replay.get('candidate_attempts') != 940:
        raise ValueError('deep replay coverage totals mismatch')
    if replay.get('exact_hud_words') != 288 * HUD_WORDS or replay.get('physical_30fps_proven') is not False:
        raise ValueError('deep replay HUD or scope claim mismatch')
    verify_replay_chains(replay, cases)
    if (type(replay.get('band_candidate_planes')) is not int or replay['band_candidate_planes'] <= 0
            or type(replay.get('band_block_checks')) is not int or replay['band_block_checks'] <= 0):
        raise ValueError('deep replay omitted band plane/block validation counts')
    if replay.get('band_dc_roi_perblock_and_rgb_guards_replayed') is not True:
        raise ValueError('deep verifier did not replay DC/ROI/per-block/RGB band guards')
    if replay.get('all_source_pixels_decoded_references_metrics_and_work_replayed') is not True:
        raise ValueError('deep verifier did not replay source pixels, own references, metrics, and work')


def verify_replay_chains(replay: dict, cases: dict) -> None:
    chains = replay.get('chains')
    if not isinstance(chains, list):
        raise ValueError('deep replay chains missing')
    indexed = {(v['scene'], v['policy']): v for v in chains}
    if len(indexed) != len(chains) or set(indexed) != set(cases):
        raise ValueError('deep replay chains do not match policy cases')
    for key, case in cases.items():
        rows = indexed[key].get('rows')
        if not isinstance(rows, list) or len(rows) != 48:
            raise ValueError(f'{key}: deep replay row count mismatch')
        prev = None
        for original, check in zip(case['rows'], rows):
            if check.get('id') != original['id']:
                raise ValueError('deep replay ID ordering mismatch')
            if (check.get('decoded_tag') != original['reconstructed_tag']
                    or check.get('reference_tag') != original['reference_tag']
                    or check.get('hybrid_rgb565_sha256') != original['hybrid_rgb565_sha256']):
                raise ValueError('deep replay accepted decode/hash binding mismatch')
            if original['key']:
                if check['reference_tag'] != bytes(16).hex():
                    raise ValueError('deep replay key reference tag nonzero')
            elif check['reference_tag'] != prev:
                raise ValueError('deep replay does not use policy own prior decode')
            prev = check['decoded_tag']
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = audit()
    target = HERE / 'audit.json'
    encoded = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.check:
        if not target.exists() or target.read_text() != encoded:
            raise SystemExit('audit.json differs from deterministic audit output')
        print('PASS audit.json byte-identical')
    else:
        target.write_text(encoded)
        print('PASS wrote audit.json')


if __name__ == '__main__':
    main()
