#!/usr/bin/env python3
"""Independent audit of v32 Python codec results and standards accounting.

The schema-specific audit is intentionally completed against retained v32
results and replay once both artifacts exist. These arithmetic and bounded
object helpers are independent of the producer implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ROOT / 'experiments/python-game-controller-v32-study'
V30_STUDY = ROOT / 'experiments/python-game-controller-v30-study'
V30_AUDIT_PATH = ROOT / 'experiments/python-game-audit-v30-study/audit.py'
CAP, HUD_WORDS, BINDING_BYTES = 49_152, 21_120, 60
SCENES = ('mass-effect-2600', 'mass-effect-7200')
POLICIES = ('band_control', 'shrink_strict', 'shrink_budget')


def _load_v30_audit():
    spec = importlib.util.spec_from_file_location('v30_audit_for_v32', V30_AUDIT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load independent v30 packet parser')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V30 = _load_v30_audit()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def finite_nonnegative(value) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(value) and value >= 0)


def integer_metric(metric: dict) -> tuple[int, int, float]:
    sse, samples = metric.get('active_squared_error'), metric.get('active_channel_samples')
    if type(sse) is not int or type(samples) is not int or sse < 0 or samples <= 0:
        raise ValueError('invalid integer active RGB SSE/sample metric')
    mse = sse / samples
    if metric.get('active_mse') != mse:
        raise ValueError('active MSE does not reconcile with integer totals')
    return sse, samples, mse


def complete_body_bytes(base_bytes: int, hud_bytes: int,
                        binding_bytes: int = BINDING_BYTES) -> int:
    values = (base_bytes, hud_bytes, binding_bytes)
    if any(type(v) is not int or v < 0 for v in values):
        raise ValueError('component byte counts must be nonnegative integers')
    return sum(values)


def under_cap(size: int, cap: int = CAP) -> bool:
    if type(size) is not int or type(cap) is not int or size < 0 or cap <= 0:
        raise ValueError('invalid packet size/cap')
    return size <= cap


def strict_or_budget_guard(candidate_sse: int, shadow_sse: int, policy: str) -> bool:
    """Use integer RGB-SSE comparison for the strict or one-percent quality gate."""
    if policy not in ('shrink_strict', 'shrink_budget'):
        raise ValueError('unknown shrink policy')
    if type(candidate_sse) is not int or type(shadow_sse) is not int or min(candidate_sse, shadow_sse) < 0:
        raise ValueError('quality guard requires nonnegative integer SSE')
    allowance = 1 if policy == 'shrink_budget' else 0
    return 100 * candidate_sse <= (100 + allowance) * shadow_sse


def read_object(desc: dict, folder: Path, *, max_raw_bytes=2_000_000) -> bytes:
    """Read a content-addressed zlib object with bounded decode and hash checks."""
    path = Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('unsafe object path')
    declared_dir = desc.get('directory')
    base = (ROOT / declared_dir).resolve() if declared_dir else folder.resolve()
    if declared_dir and (base != (ROOT / declared_dir).resolve() or ROOT not in base.parents):
        raise ValueError('object root outside repository')
    stored = (base / path).read_bytes()
    if 'stored_bytes' in desc and len(stored) != desc['stored_bytes']:
        raise ValueError('stored length mismatch')
    if sha(stored) != desc['stored_sha256']:
        raise ValueError('stored SHA-256 mismatch')
    raw_len = desc['raw_bytes']
    if type(raw_len) is not int or not 0 <= raw_len <= max_raw_bytes:
        raise ValueError('raw object exceeds audit bound')
    dec = zlib.decompressobj()
    raw = dec.decompress(stored, raw_len + 1)
    if (len(raw) != raw_len or not dec.eof or dec.unused_data or dec.unconsumed_tail
            or sha(raw) != desc['raw_sha256']):
        raise ValueError('bounded object decode/hash mismatch')
    return raw


def standard_operating_points(standard: dict, scene: str, hud_bytes_by_id: dict,
                             target_mse: float) -> dict:
    """Recompute sampled standards points with this run's exact HUD and binding."""
    if standard.get('schema') != 'gamebub-standard-compare-v24':
        raise ValueError('unexpected standard comparison schema')
    if not finite_nonnegative(target_mse) or not hud_bytes_by_id:
        raise ValueError('invalid custom quality threshold/current HUD bytes')
    candidates = []
    for case in standard.get('cases', []):
        if case.get('scene') != scene:
            continue
        rows = case.get('rows', [])
        if [row.get('id') for row in rows] != list(range(48)):
            raise ValueError('standard source frame IDs incomplete')
        total = sse = samples = maximum = 0
        for row in rows:
            fid = row['id']
            if fid not in hud_bytes_by_id:
                raise ValueError('current HUD bytes missing standard frame')
            raw = row.get('coded_access_unit_bytes')
            if type(raw) is not int or raw < 0:
                raise ValueError('invalid sampled native access-unit size')
            metric = row['hybrid']['metric']
            row_sse, row_samples, _ = integer_metric(metric)
            complete = complete_body_bytes(raw, hud_bytes_by_id[fid])
            total += complete
            sse += row_sse
            samples += row_samples
            maximum = max(maximum, complete)
        mean_mse = sse / samples
        candidates.append(dict(codec=case['codec'], profile=case['profile'], frames=48,
                               complete_bytes=total, max_complete_bytes=maximum,
                               active_squared_error=sse, active_channel_samples=samples,
                               active_mse=mean_mse,
                               same_current_HUD_and_60B_binding=True,
                               at_least_custom_quality=mean_mse <= target_mse,
                               cap_fits=maximum <= CAP))
    if not candidates:
        raise ValueError(f'no sampled native comparison cases for {scene}')
    eligible = [point for point in candidates
                if point['at_least_custom_quality'] and point['cap_fits']]
    selected = {}
    for codec in sorted({point['codec'] for point in eligible}):
        selected[codec] = min((point for point in eligible if point['codec'] == codec),
                              key=lambda point: point['complete_bytes'])
    return dict(sampled_operating_points=sorted(candidates,
                                                key=lambda point: (point['codec'], point['profile'])),
                selected_same_current_HUD={codec: selected[codec] for codec in sorted(selected)},
                qualifying_fit_exists=bool(eligible))


def verify_source_pins(pins: dict) -> int:
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source_sha256 pins missing')
    for rel, expected in sorted(pins.items()):
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError('unsafe source pin')
        target = ROOT / path
        if not target.is_file() or sha(target.read_bytes()) != expected:
            raise ValueError(f'source hash mismatch: {rel}')
    return len(pins)


def _choose_v30_shadow(group: list[dict]) -> dict | None:
    """Recompute the v30 strict winner from legacy and band attempts."""
    legacy = [a for a in group if not a['kind'].endswith(('_band', '_shrink'))]
    baseline = min((a for a in legacy if a['cap_fit'] and a['quality_eligible']),
                   key=lambda a: a['complete_bytes'], default=None)
    if baseline is None:
        return None
    eligible = [baseline]
    for candidate in (a for a in group if a['kind'].endswith('_band')):
        expected = V30.band_guard_passes(candidate['hybrid']['active_squared_error'],
                                         baseline['hybrid']['active_squared_error'], 'band_strict')
        if candidate['quality_eligible'] is not expected:
            raise ValueError('v30 strict band quality eligibility mismatch')
        if candidate['cap_fit'] and expected:
            eligible.append(candidate)
    return min(eligible, key=lambda a: a['complete_bytes'])


def expected_reference_tag(frame_id: int, previous_tag: str | None) -> str:
    if type(frame_id) is not int or frame_id < 0:
        raise ValueError('invalid frame ID for reference chain')
    if frame_id % 24 == 0:
        return bytes(16).hex()
    if not isinstance(previous_tag, str) or len(previous_tag) != 32:
        raise ValueError('P frame is missing its own cohort accepted predecessor tag')
    try:
        bytes.fromhex(previous_tag)
    except ValueError as exc:
        raise ValueError('invalid previous decoded reference tag') from exc
    return previous_tag


def verify_packet_parity(current: dict, baseline: dict,
                         current_folder: Path, baseline_folder: Path) -> None:
    """Require exact retained full-pair and ACK bytes plus decoded evidence parity."""
    if (read_object(current['packet'], current_folder) != read_object(baseline['packet'], baseline_folder)
            or read_object(current['ack'], current_folder) != read_object(baseline['ack'], baseline_folder)
            or current.get('hybrid') != baseline.get('hybrid')
            or current.get('hybrid_rgb565_sha256') != baseline.get('hybrid_rgb565_sha256')):
        raise ValueError('strict-control full packet/ACK/output parity mismatch')


def _select_from_shadow(shadow: dict, shrink_attempts: list[dict], policy: str) -> dict:
    """Reapply byte-saving and actual same-history RGB quality gates."""
    eligible = [shadow]
    for attempt in shrink_attempts:
        passed = strict_or_budget_guard(attempt['hybrid']['active_squared_error'],
                                        shadow['hybrid']['active_squared_error'], policy)
        if attempt.get('quality_eligible') is not passed:
            raise ValueError('shrink quality eligibility differs from integer shadow guard')
        if attempt['complete_bytes'] >= shadow['complete_bytes']:
            if attempt.get('selected'):
                raise ValueError('selected shrink did not save bytes against v30 shadow')
            continue
        if attempt['cap_fit'] and passed:
            eligible.append(attempt)
    return min(eligible, key=lambda a: a['complete_bytes'])


def _validate_attempts(row: dict, policy: str, key: bool, refid: int,
                       reference_tag: str, hud: bytes) -> tuple[dict, dict]:
    attempts = row.get('attempts')
    if not isinstance(attempts, list) or not attempts:
        raise ValueError('no candidate attempts retained')
    expected_base = ['zero'] if key else ['zero', 'half32']
    expected_kinds = expected_base + [f'{kind}_band' for kind in expected_base]
    if policy != 'band_control':
        expected_kinds += [f'{kind}_shrink' for kind in expected_base]
    backgrounds = []
    parsed_attempts = []
    for a in attempts:
        packet = read_object(a['packet'], STUDY)
        cp = V30.V29.parse_pair(packet, enforce_cap=False)
        base = read_object(a['base_packet'], STUDY)
        if (len(packet) != a.get('complete_bytes') or len(base) != a.get('base_bytes')
                or cp['base'] != base or cp['hud'] != hud):
            raise ValueError('attempt complete/base/HUD bytes differ from nested pair')
        if cp['hud_meta']['patch_words'] != HUD_WORDS:
            raise ValueError('attempt HUD coverage differs from exact 21,120 words')
        if cp['base_meta']['reference_id'] != refid or cp['base_meta']['reference_tag'].hex() != reference_tag:
            raise ValueError('attempt uses wrong cohort-local accepted reference')
        if cp['base_meta']['reconstructed_tag'].hex() != a.get('reconstructed_tag'):
            raise ValueError('attempt reconstructed tag differs from GM27')
        if a.get('cap_fit') is not under_cap(len(packet)):
            raise ValueError('attempt complete cap flag mismatch')
        integer_metric(a['hybrid'])
        if a['hybrid'].get('hud_word_errors') != 0:
            raise ValueError('exact HUD attempt has word errors')
        for field in ('encode_ms', 'offline_debug_decode_ms', 'quality_ms', 'bind_ms'):
            if not finite_nonnegative(a.get(field)):
                raise ValueError(f'invalid candidate timing: {field}')
        if a['background'] not in backgrounds:
            backgrounds.append(a['background'])
        parsed_attempts.append((a, cp, packet))
    if backgrounds not in ([16], [16, 32]):
        raise ValueError('invalid v32 background fallback sequence')
    selected_group = None
    expected_candidate = shadow = None
    for bg in backgrounds:
        group = [a for a, _, _ in parsed_attempts if a['background'] == bg]
        if [a['kind'] for a in group] != expected_kinds:
            raise ValueError('candidate family/order incomplete within background tier')
        legacy = [a for a in group if not a['kind'].endswith(('_band', '_shrink'))]
        zero_sse = legacy[0]['hybrid']['active_squared_error']
        for a in legacy:
            eligible = a['hybrid']['active_squared_error'] <= zero_sse
            if a.get('quality_eligible') is not eligible:
                raise ValueError('legacy candidate quality gate mismatch')
        group_shadow = _choose_v30_shadow(group)
        if group_shadow is None:
            if bg == backgrounds[-1]:
                raise ValueError('no fitting v30 shadow candidate')
            continue
        shadow = group_shadow
        shrink_attempts = [a for a in group if a['kind'].endswith('_shrink')]
        quality_percent = 1 if policy == 'shrink_budget' else 0
        if row.get('quality_budget_percent') != quality_percent:
            raise ValueError('row quality budget does not match cohort policy')
        expected_candidate = _select_from_shadow(shadow, shrink_attempts, policy)
        selected_group = bg
        break
    if expected_candidate is None or shadow is None:
        raise ValueError('no selectable v30 shadow tier')
    if selected_group != backgrounds[-1]:
        raise ValueError('fallback continued after a fitting shadow tier')
    selected = [a for a in attempts if a.get('selected') is True]
    if len(selected) != 1 or selected[0] is not expected_candidate:
        raise ValueError(f"selected candidate differs from independent shrink selection: actual={[(a['kind'], a['background'], a['complete_bytes']) for a in selected]}, expected={(expected_candidate['kind'], expected_candidate['background'], expected_candidate['complete_bytes'])}, baseline={(shadow['kind'], shadow['complete_bytes'])}")
    if (row.get('selected_kind') != expected_candidate['kind']
            or row.get('selected_background') != expected_candidate['background']
            or row.get('baseline_kind') != shadow['kind']
            or row.get('baseline_complete_bytes') != shadow['complete_bytes']
            or row.get('baseline_source_sse') != shadow['hybrid']['active_squared_error']):
        raise ValueError('accepted choice or v30 shadow metadata mismatch')
    return expected_candidate, shadow


def _walk_objects(value):
    if isinstance(value, dict):
        if all(k in value for k in ('path', 'raw_bytes', 'raw_sha256', 'stored_sha256')):
            yield value
        else:
            for child in value.values():
                yield from _walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_objects(child)


def _source_inventory(pins: dict) -> dict:
    paths = set(pins)
    paths.update({
        'experiments/python-game-controller-v32-study/benchmark.py',
        'experiments/python-game-controller-v32-study/controller.py',
        'experiments/python-game-controller-v32-study/verify.py',
        'experiments/python-game-controller-v32-study/results.json',
        'experiments/python-game-controller-v32-study/replay.json',
        'experiments/python-game-controller-v32-study/run.log',
        'experiments/python-game-controller-v32-study/tests.log',
        'experiments/python-game-controller-v30-study/results.json',
        'experiments/python-game-controller-v30-study/replay.json',
        'experiments/python-game-controller-v30-study/verify.py',
        'experiments/python-game-standard-v24-study/results.json',
        'experiments/python-game-hud-v32-study/results.json',
        'experiments/python-game-hud-v32-study/benchmark.py',
        'experiments/python-game-hud-v32-study/model.py',
        'experiments/python-game-hud-v32-study/verify.py',
        'experiments/python-game-hud-v32-study/run.log',
        'experiments/python-game-hud-v32-study/tests.log',
        'experiments/python-game-hud-v32-study/verify.log',
        'experiments/python-game-audit-v32-study/audit.py',
        'experiments/python-game-audit-v32-study/test_audit.py',
        'experiments/python-game-audit-v32-study/README.md',
        'experiments/python-game-audit-v32-study/AUDIT-CHECKLIST.md',
        'experiments/python-game-audit-v32-study/tests.log',
    })
    out = {}
    for rel in sorted(paths):
        p = Path(rel)
        if p.is_absolute() or '..' in p.parts or rel.endswith('/audit.json'):
            raise ValueError('unsafe audit inventory path')
        file = ROOT / p
        if not file.is_file():
            raise ValueError(f'missing audit inventory input: {rel}')
        out[rel] = sha(file.read_bytes())
    return out


def _verify_replay(replay: dict, data: dict, cases: dict, attempt_count: int) -> int:
    if replay.get('schema') != 'gamebub-v32-replay':
        raise ValueError('unexpected deep replay schema')
    if replay.get('results_sha256') != sha((STUDY / 'results.json').read_bytes()):
        raise ValueError('deep replay is stale against results.json')
    verify_path = STUDY / 'verify.py'
    if replay.get('verifier_sha256') != sha(verify_path.read_bytes()):
        raise ValueError('deep replay verifier hash mismatch')
    if (replay.get('accepted_pairs') != 288 or replay.get('candidate_attempts') != attempt_count
            or replay.get('exact_hud_words') != 288 * HUD_WORDS
            or replay.get('baseline_v30_exact_pairs') != 96
            or replay.get('physical_30fps_proven') is not False
            or replay.get('band_and_shrink_dc_roi_magnitude_perblock_rgb_guards_replayed') is not True
            or replay.get('all_source_pixels_decoded_references_metrics_and_work_replayed') is not True):
        raise ValueError('deep replay coverage, parity, or scope flags mismatch')
    chains = replay.get('chains')
    indexed = {(v['scene'], v['policy']): v for v in chains}
    if len(indexed) != len(chains) or set(indexed) != set(cases):
        raise ValueError('deep replay chains do not match all controller cases')
    for key, case in cases.items():
        rows = indexed[key].get('rows')
        if not isinstance(rows, list) or len(rows) != 48:
            raise ValueError(f'{key}: replay row count mismatch')
        previous = None
        for original, check in zip(case['rows'], rows):
            if check.get('id') != original['id']:
                raise ValueError('deep replay ID ordering mismatch')
            if (check.get('decoded_tag') != original['reconstructed_tag']
                    or check.get('reference_tag') != original['reference_tag']
                    or check.get('hybrid_rgb565_sha256') != original['hybrid_rgb565_sha256']):
                raise ValueError('deep replay decode/hash does not bind to accepted row')
            if original['key']:
                if check['reference_tag'] != bytes(16).hex():
                    raise ValueError('deep replay key reference tag must be zero')
            elif check['reference_tag'] != previous:
                raise ValueError('deep replay did not follow cohort-local prior reconstruction')
            previous = check['decoded_tag']
    return len(chains) * 48


def audit() -> dict:
    result_path, replay_path = STUDY / 'results.json', STUDY / 'replay.json'
    if not result_path.is_file() or not replay_path.is_file():
        raise ValueError('v32 results and deep replay must both be complete before audit')
    data = json.loads(result_path.read_text())
    if data.get('schema') != 'gamebub-controller-v32':
        raise ValueError('unexpected controller-v32 result schema')
    if data.get('geometry') != dict(coded=[720, 480], active=[720, 405],
                                    exact_hud_words=HUD_WORDS, complete_cap=CAP):
        raise ValueError('geometry, HUD, or complete cap mismatch')
    if data.get('physical_30fps_proven') is not False or data.get('unchanged_GM27_wire') is not True:
        raise ValueError('scope or wire-profile claim mismatch')
    pin_count = verify_source_pins(data.get('source_sha256'))
    cases, paired_sources, hud_by_scene = {}, {}, {}
    v30_data = json.loads((V30_STUDY / 'results.json').read_text())
    accepted = attempts_total = ref_links = control_parity = max_complete = 0
    object_seen = set()
    for desc in _walk_objects(data):
        key = (desc.get('directory'), desc['path'], desc['stored_sha256'])
        if key not in object_seen:
            read_object(desc, STUDY)
            object_seen.add(key)
    for case in data['cases']:
        scene, policy = case['scene'], case['policy']
        key_case = (scene, policy)
        if scene not in SCENES or policy not in POLICIES or key_case in cases:
            raise ValueError('unexpected or duplicate scene/policy case')
        rows = case['rows']
        if [row.get('id') for row in rows] != list(range(48)):
            raise ValueError(f'{scene}/{policy}: frame IDs missing or reordered')
        previous_tag = None
        for fid, row in enumerate(rows):
            key = fid % 24 == 0
            refid = 0xFFFFFFFF if key else fid - 1
            if row.get('key') is not key or row.get('reference_id') != refid:
                raise ValueError(f'{scene}/{policy}/{fid}: key/reference discontinuity')
            reference_tag = expected_reference_tag(fid, previous_tag)
            if row.get('reference_tag') != reference_tag:
                raise ValueError('cohort did not reference its own accepted predecessor')
            if not key:
                ref_links += 1
            pair = read_object(row['packet'], STUDY)
            parsed = V30.V29.parse_pair(pair)
            base = read_object(row['base_packet'], STUDY)
            hud = read_object(row['hud_packet'], STUDY)
            ack = read_object(row['ack'], STUDY)
            if (parsed['base'] != base or parsed['hud'] != hud
                    or parsed['base_meta']['reference_id'] != refid
                    or parsed['hud_meta']['reference_id'] != refid
                    or parsed['base_meta']['reference_tag'].hex() != reference_tag
                    or parsed['base_meta']['reconstructed_tag'].hex() != row['reconstructed_tag']):
                raise ValueError('accepted packet component/reference/tag mismatch')
            if parsed['hud_meta']['patch_words'] != HUD_WORDS or len(hud) != row['hud_bytes']:
                raise ValueError('accepted HU25 size or exact word coverage mismatch')
            if len(pair) != row['body_bytes'] or len(base) != row['base_bytes'] or row.get('binding_bytes') != BINDING_BYTES:
                raise ValueError('accepted body component accounting mismatch')
            if not under_cap(len(pair)):
                raise ValueError('accepted complete CP27 exceeds 49,152-byte cap')
            ack_meta = V30.V29.V28.parse_ja27(ack, parsed)
            am = row['ack_meta']
            if (row.get('source_slot') != parsed['source']
                    or row.get('destination_slot') != parsed['destination']
                    or am.get('source_slot') != parsed['source']
                    or am.get('destination_slot') != parsed['destination']):
                raise ValueError('accepted pair/ACK bank slot binding mismatch')
            if (len(ack) != 65 or ack_meta['frame'] != fid or ack_meta['epoch'] != 25
                    or am.get('frame_id') != fid or am.get('epoch') != 25
                    or am.get('pair_tag') != parsed['pair_tag'].hex()
                    or am.get('base_tag') != parsed['base_meta']['reconstructed_tag'].hex()
                    or am.get('hud_tag') != parsed['hud_meta']['out_tag'].hex()):
                raise ValueError('accepted ACK identity/tag/length mismatch')
            metric = row['hybrid']
            integer_metric(metric)
            if metric.get('hud_word_errors') != 0:
                raise ValueError('accepted exact HUD reports word errors')
            if row.get('hybrid_rgb565_sha256') != next(a['hybrid_rgb565_sha256'] for a in row['attempts'] if a['selected']):
                raise ValueError('accepted RGB565 digest differs from selected attempt')
            src_key = (scene, fid)
            paired_sources.setdefault(src_key, row['source_common_yuv_sha256'])
            if paired_sources[src_key] != row['source_common_yuv_sha256']:
                raise ValueError('source lineage differs across causal cohorts')
            hud_by_scene.setdefault(scene, {})[fid] = len(hud)
            chosen, shadow = _validate_attempts(row, policy, key, refid, reference_tag, hud)
            if (chosen['hybrid'] != metric or chosen['reconstructed_tag'] != row['reconstructed_tag']
                    or read_object(chosen['packet'], STUDY) != pair):
                raise ValueError('accepted result differs from selected complete candidate')
            if policy == 'band_control':
                baseline = next(c for c in v30_data['cases']
                                if c['scene'] == scene and c['policy'] == 'band_strict')
                old = baseline['rows'][fid]
                verify_packet_parity(row, old, STUDY, V30_STUDY)
                control_parity += 1
            analyses = row['analyses']
            expected_analyses = ['zero'] if key else ['zero', 'half32']
            if list(analyses) != expected_analyses:
                raise ValueError('analysis set differs from key/P frame profile')
            for name, analysis in analyses.items():
                if not finite_nonnegative(analysis.get('analysis_wall_ms')):
                    raise ValueError('invalid paid analysis timing')
            for field in ('receive_ms', 'ack_ms', 'paid_base_encode_ms', 'base_policy_service_ms'):
                if not finite_nonnegative(row.get(field)):
                    raise ValueError(f'invalid frame timing: {field}')
            paid = sum(a['analysis_wall_ms'] for a in analyses.values()) + sum(a['encode_ms'] for a in row['attempts'])
            service = paid + sum(a['quality_ms'] + a['bind_ms'] for a in row['attempts'])
            if (not math.isclose(paid, row['paid_base_encode_ms'], rel_tol=1e-10, abs_tol=1e-7)
                    or not math.isclose(service, row['base_policy_service_ms'], rel_tol=1e-10, abs_tol=1e-7)):
                raise ValueError('paid work omits an analysis, losing encode, quality, or bind cost')
            previous_tag = row['reconstructed_tag']
            accepted += 1
            attempts_total += len(row['attempts'])
            max_complete = max(max_complete, len(pair))
        summary = V30.summarize(rows)
        summary['selected_shrink_frames'] = sum(row['selected_kind'].endswith('_shrink') for row in rows)
        if set(case['summary']) != set(summary):
            raise ValueError('summary field set mismatch')
        for name, value in summary.items():
            actual = case['summary'][name]
            if isinstance(value, float):
                if not math.isclose(float(actual), value, rel_tol=1e-10, abs_tol=1e-7):
                    raise ValueError(f'{scene}/{policy}: summary mismatch {name}')
            elif actual != value:
                raise ValueError(f'{scene}/{policy}: summary mismatch {name}')
        cases[key_case] = case
    expected_keys = {(scene, policy) for scene in SCENES for policy in POLICIES}
    if set(cases) != expected_keys or accepted != 288 or attempts_total != 1504:
        raise ValueError('incomplete v32 cohort matrix or accepted/attempt count')
    if ref_links != 288 - 2 * 2 * 3 or control_parity != 96:
        raise ValueError('reference-link or v30 exact packet parity totals mismatch')
    for scene in SCENES:
        # HU25 packets are shared across policy paths; each report uses their actual bytes.
        if len(hud_by_scene[scene]) != 48:
            raise ValueError('incomplete current HUD byte map')
    hud_dir = ROOT / 'experiments/python-game-hud-v32-study'
    hud_data = json.loads((hud_dir / 'results.json').read_text())
    if hud_data.get('schema') != 'gamebub-huffman-HUD-v32':
        raise ValueError('unexpected current HUD v32 schema')
    hud_pin_count = verify_source_pins(hud_data.get('source_sha256'))
    hud_by_scene = {}
    for hud_case in hud_data.get('cases', []):
        scene = hud_case['scene']
        if scene not in SCENES or [r.get('id') for r in hud_case['rows']] != list(range(48)):
            raise ValueError('current HUD case has invalid scene or frame coverage')
        sizes = {}
        for row in hud_case['rows']:
            packet = read_object(row['packet'], hud_dir)
            if (len(packet) != row.get('bytes') or row.get('exact_hud_words') != HUD_WORDS
                    or len(packet) > CAP or row.get('reference_id') != (0xFFFFFFFF if row['key'] else row['id']-1)):
                raise ValueError('current HU32 object size/reference/exact-word mismatch')
            sizes[row['id']] = len(packet)
        if len(sizes) != 48 or scene in hud_by_scene:
            raise ValueError('duplicate or incomplete current HUD scene')
        hud_total = sum(sizes.values())
        if hud_total != hud_case['summary'].get('new_hud_bytes'):
            raise ValueError('HU32 rows do not reconcile with component summary bytes')
        hud_by_scene[scene] = sizes
    if set(hud_by_scene) != set(SCENES):
        raise ValueError('current HU32 comparison vector incomplete')
    standard = json.loads((ROOT / 'experiments/python-game-standard-v24-study/results.json').read_text())
    standard_reports, current_hud_custom = {}, {}
    for scene in SCENES:
        standard_reports[scene] = {}
        for policy in POLICIES:
            case = cases[(scene, policy)]
            rows = case['rows']
            source_sse = sum(row['hybrid']['active_squared_error'] for row in rows)
            samples = sum(row['hybrid']['active_channel_samples'] for row in rows)
            custom_total = 0
            custom_max = 0
            for row in rows:
                complete = complete_body_bytes(row['base_bytes'], hud_by_scene[scene][row['id']])
                custom_total += complete
                custom_max = max(custom_max, complete)
            if custom_max > CAP:
                raise ValueError(f'{scene}/{policy}: custom base plus HU32 plus 60B exceeds cap')
            current_hud_custom[policy] = current_hud_custom.get(policy, {})
            current_hud_custom[policy][scene] = dict(
                current_HU32_complete_bytes=custom_total,
                current_HU32_max_complete_bytes=custom_max,
                current_HU32_cap_fits=True,
                active_squared_error=source_sse,
                active_channel_samples=samples,
                active_mse=source_sse / samples,
                current_HU25_complete_bytes=case['summary']['complete_bytes'],
                exact_HUD_words=48 * HUD_WORDS,
                current_HU32_and_60B_binding=True,
                prospective_HX32_CP32_wire=False)
            standard_reports[scene][policy] = standard_operating_points(
                standard, scene, hud_by_scene[scene], source_sse / samples)
            standard_reports[scene][policy]['quality_and_cap_comparable_points_exist'] = bool(
                standard_reports[scene][policy]['selected_same_current_HUD'])
            standard_reports[scene][policy]['comparison_scope'] = (
                'sampled operating points add the same HU32 per-frame bytes and 60B binding; no HX32/CP32 endpoint is implemented')
    replay = json.loads(replay_path.read_text())
    replay_rows = _verify_replay(replay, data, cases, attempts_total)
    return dict(schema='gamebub-v32-independent-audit', source_sha256=_source_inventory(data['source_sha256']),
                source_pins_verified=pin_count, archived_objects_verified=len(object_seen),
                accepted_frames=accepted, attempted_candidates=attempts_total,
                maximum_complete_bytes=max_complete, exact_hud_words=accepted * HUD_WORDS,
                accepted_reference_links=ref_links, band_control_v30_strict_exact_parity_rows=control_parity,
                deep_replay_rows_verified=replay_rows, deep_replay_verified=True,
                current_HU32_custom_accounting=current_hud_custom,
                standards_same_current_HU32_and_60B_binding=standard_reports,
                current_HUD_source_pins_verified=hud_pin_count,
                physical_30fps_proven=False,
                claim_boundary='Python host measurements and nominal 30-ID/s byte projections only; HU32 accounting is prospective because no HX32/CP32 full receiver endpoint is implemented; no native or physical 30-fps proof.')


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
