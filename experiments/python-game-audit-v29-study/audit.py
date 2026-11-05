#!/usr/bin/env python3
"""Independent bounded audit of retained v29 controller results."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STUDY = ROOT / 'experiments/python-game-controller-v29-study'
V28_STUDY = ROOT / 'experiments/python-game-runtime-v28-study'
V28_AUDIT_PATH = ROOT / 'experiments/python-game-audit-v28-study/audit.py'
CAP, HUD_WORDS = 49_152, 21_120
POLICIES = ('mixed_lazy', 'adaptive_lazy', 'mixed_ec', 'adaptive_ec')
SCENES = ('mass-effect-2600', 'mass-effect-7200')
CP27 = struct.Struct('<4sBBIIBBII16s16s')
GM27 = struct.Struct('<4sBBIIIHHBB16s16sIIIII')
HU25 = struct.Struct('<4sBBIIIHH16s16s4I4B16H')
NO_REF = 0xFFFFFFFF


def _load_v28_audit():
    spec = importlib.util.spec_from_file_location('v28_audit_for_v29', V28_AUDIT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V28 = _load_v28_audit()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_object(desc: dict, folder: Path, *, max_raw=1_000_000) -> bytes:
    """Read one bounded zlib object, checking path, size, both hashes and EOF."""
    path = Path(desc['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('unsafe object path')
    directory = desc.get('directory')
    base = (ROOT / directory).resolve() if directory else Path(folder).resolve()
    if ROOT not in base.parents:
        raise ValueError('object directory outside repository')
    target = base / path
    if not target.is_file() or target.resolve().parent != base.resolve() and base.resolve() not in target.resolve().parents:
        raise ValueError('object path escapes declared directory')
    packed = target.read_bytes()
    if len(packed) > max_raw + 65536 or sha(packed) != desc['stored_sha256']:
        raise ValueError('stored object size or digest mismatch')
    raw_len = desc['raw_bytes']
    if type(raw_len) is not int or not 0 < raw_len <= max_raw:
        raise ValueError('raw object outside audit bound')
    dec = zlib.decompressobj()
    raw = dec.decompress(packed, raw_len + 1)
    if (len(raw) != raw_len or not dec.eof or dec.unused_data or dec.unconsumed_tail
            or sha(raw) != desc['raw_sha256']):
        raise ValueError('bounded object decode or raw digest mismatch')
    return raw


def parse_pair(packet: bytes, *, enforce_cap=True) -> dict:
    """Independently reconcile CP27 framing and use frozen parser for nested formats."""
    if len(packet) < CP27.size + 4 or (enforce_cap and len(packet) > CAP):
        raise ValueError('complete CP27 cap/length')
    if zlib.crc32(packet[:-4]) != struct.unpack_from('<I', packet, len(packet)-4)[0]:
        raise ValueError('CP27 CRC')
    magic, ver, flags, epoch, frame, src, dst, nb, nh, base_hash, hud_hash = CP27.unpack_from(packet)
    if magic != b'CP27' or ver != 1 or flags not in (0, 2, 3):
        raise ValueError('CP27 profile')
    if len(packet) != CP27.size + nb + nh + 4:
        raise ValueError('CP27 declared component lengths')
    base = packet[CP27.size:CP27.size+nb]
    hud = packet[CP27.size+nb:-4]
    if hashlib.sha256(base).digest()[:16] != base_hash or hashlib.sha256(hud).digest()[:16] != hud_hash:
        raise ValueError('CP27 component digest')
    bm = V28.parse_gm27(base)
    hm = V28.parse_hu25(hud)
    if (bm['epoch'], bm['frame'], hm['epoch'], hm['frame']) != (epoch, frame, epoch, frame):
        raise ValueError('nested frame identity')
    if bm['key'] != (flags == 3) or (bm['key'] and (src, dst) != (255, 0)):
        raise ValueError('CP27 base/bank semantics')
    if not bm['key'] and (src not in (0, 1) or dst != 1-src):
        raise ValueError('CP27 P bank semantics')
    if hm['patch_words'] != HUD_WORDS:
        raise ValueError('accepted HUD area is not exact')
    return dict(bytes=len(packet), pair_tag=hashlib.sha256(packet).digest()[:16],
                epoch=epoch, frame=frame, base=base, hud=hud, base_meta=bm, hud_meta=hm,
                source=src, destination=dst, flags=flags)


def metric_totals(rows: list[dict]) -> tuple[int, int, float, int]:
    sse = samples = hud_errors = 0
    for row in rows:
        metric = row['hybrid']
        e, n = metric.get('active_squared_error'), metric.get('active_channel_samples')
        if type(e) is not int or type(n) is not int or e < 0 or n <= 0:
            raise ValueError('invalid integer SSE/sample metric')
        if metric.get('active_mse') != e / n:
            raise ValueError('per-frame MSE does not reconcile')
        sse += e; samples += n
        hud_errors += metric.get('hud_word_errors', 0)
    return sse, samples, sse / samples, hud_errors


def summarize_rows(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError('empty frame rows')
    lengths = [int(row['body_bytes']) for row in rows]
    sse, samples, mse, hud_errors = metric_totals(rows)
    attempts = [a for row in rows for a in row['attempts']]
    analyses = [a for row in rows for a in row['analyses'].values()]
    return dict(
        frames=len(rows), complete_bytes=sum(lengths),
        coded_body_Mbps_at30=sum(lengths) * 240 / len(rows) / 1_000_000,
        base_bytes=sum(int(r['base_bytes']) for r in rows),
        hud_bytes=sum(int(r['hud_bytes']) for r in rows),
        binding_bytes=60 * len(rows), maximum_complete_bytes=max(lengths),
        cap_fit_frames=sum(n <= CAP for n in lengths),
        active_squared_error=sse, active_channel_samples=samples, active_mse=mse,
        active_psnr_db=10 * math.log10(65025 / mse), hud_word_errors=hud_errors,
        exact_hud_words=len(rows) * HUD_WORDS,
        paid_candidate_encodes=len(attempts),
        mean_paid_base_encode_ms=sum(float(r['paid_base_encode_ms']) for r in rows) / len(rows),
        mean_base_policy_service_ms=sum(float(r['base_policy_service_ms']) for r in rows) / len(rows),
        mean_receiver_ms=sum(float(r['receive_ms']) for r in rows) / len(rows),
        sad_sample_operations=sum(int(a['search']['sad_sample_operations']) for a in analyses),
        search_reference_fetches=sum(int(a['search'].get('reference_sample_fetches', 0)) for a in analyses),
        quiet_blocks=sum(int(a['search'].get('quiet_blocks', 0)) for a in analyses),
        active_blocks=sum(int(a['search'].get('active_blocks', 0)) for a in analyses),
        selected_alternative_planes=sum(int(a['work'].get('selected_alternative_planes', 0)) for a in attempts if a['selected']),
        ec26_size_counter_calls=sum(int(a['work'].get('ec26_size_counter_calls', 0)) for a in attempts),
        coarse_fallback_frames=[r['id'] for r in rows if r['selected_background'] == 32])


def _verify_pins(pins: dict) -> int:
    if not isinstance(pins, dict) or not pins:
        raise ValueError('source hash pins missing')
    for rel, expected in sorted(pins.items()):
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or len(expected) != 64:
            raise ValueError('unsafe source pin')
        target = ROOT / path
        if not target.is_file() or sha(target.read_bytes()) != expected:
            raise ValueError(f'source hash mismatch: {rel}')
    return len(pins)


def source_inventory(result_pins: dict) -> dict:
    """Bind package inputs and audit implementation without a self-hash cycle."""
    paths = set(result_pins)
    paths.update({
        'experiments/python-game-controller-v29-study/benchmark.py',
        'experiments/python-game-controller-v29-study/controller.py',
        'experiments/python-game-controller-v29-study/results.json',
        'experiments/python-game-controller-v29-study/verify.py',
        'experiments/python-game-controller-v29-study/replay.json',
        'experiments/python-game-controller-v29-study/verify.log',
        'experiments/python-game-audit-v28-study/audit.py',
        'experiments/python-game-audit-v29-study/audit.py',
        'experiments/python-game-audit-v29-study/test_audit.py',
        'experiments/python-game-audit-v29-study/AUDIT-CHECKLIST.md',
        'experiments/python-game-audit-v29-study/README.md',
        'experiments/python-game-audit-v29-study/tests.log',
        'experiments/python-game-runtime-v28-study/results.json',
        'experiments/python-game-adaptive-v29-study/model.py',
        'experiments/python-game-entropy-v29-study/model.py',
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
    if data.get('schema') != 'gamebub-controller-v29':
        raise ValueError('unexpected v29 controller schema')
    if data.get('physical_30fps_proven') is not False or data.get('unchanged_GM27_wire') is not True:
        raise ValueError('scope/profile claims are missing or inconsistent')
    geometry = data.get('geometry', {})
    if geometry != dict(coded=[720, 480], active=[720, 405], exact_hud_words=HUD_WORDS, complete_cap=CAP):
        raise ValueError('geometry/cap/HUD contract mismatch')
    pin_count = _verify_pins(data['source_sha256'])
    cases = {}
    accepted_count = attempted_count = 0
    accepted_max = 0
    reference_links = 0
    source_keys = {}
    for case in data['cases']:
        scene, policy = case['scene'], case['policy']
        if scene not in SCENES or policy not in POLICIES or (scene, policy) in cases:
            raise ValueError('unexpected or duplicate policy case')
        rows = case['rows']
        if [r['id'] for r in rows] != list(range(48)):
            raise ValueError(f'{scene}/{policy}: frame IDs incomplete or reordered')
        prev_tag = None
        for fid, row in enumerate(rows):
            key = fid % 24 == 0
            expected_ref = NO_REF if key else fid - 1
            if row['key'] is not key or row['reference_id'] != expected_ref:
                raise ValueError(f'{scene}/{policy}/{fid}: key/reference ID discontinuity')
            if row['binding_bytes'] != 60 or row['body_bytes'] > CAP:
                raise ValueError(f'{scene}/{policy}/{fid}: complete-pair cap or binding')
            pair = read_object(row['packet'], STUDY)
            parsed = parse_pair(pair)
            if len(pair) != row['body_bytes'] or len(pair) != row['packet']['raw_bytes']:
                raise ValueError('accepted complete byte count mismatch')
            if parsed['base_meta']['bytes'] != row['base_bytes'] or parsed['hud_meta']['bytes'] != row['hud_bytes']:
                raise ValueError('accepted component byte counts mismatch')
            if parsed['base_meta']['reference_id'] != expected_ref or parsed['hud_meta']['reference_id'] != expected_ref:
                raise ValueError('accepted base/HUD reference IDs mismatch')
            ref_tag = row['reference_tag']
            if parsed['base_meta']['reference_tag'].hex() != ref_tag:
                raise ValueError('row reference tag differs from packet')
            if key:
                if ref_tag != bytes(16).hex():
                    raise ValueError('key references must be zero')
            else:
                if prev_tag is None or ref_tag != prev_tag:
                    raise ValueError(f'{scene}/{policy}/{fid}: policy reference not previous accepted output')
                reference_links += 1
            if parsed['base_meta']['reconstructed_tag'].hex() != row['reconstructed_tag']:
                raise ValueError('accepted output tag differs from nested GM27 tag')
            if parsed['hud_meta']['patch_words'] != HUD_WORDS:
                raise ValueError('accepted HUD words/frame mismatch')
            if row['hud_packet']:
                declared_hud = read_object(row['hud_packet'], STUDY)
                if declared_hud != parsed['hud']:
                    raise ValueError('accepted HU packet differs from retained HUD source')
            ack = read_object(row['ack'], STUDY)
            ack_meta = V28.parse_ja27(ack, parsed)
            am = row['ack_meta']
            if (len(ack) != 65 or ack_meta['frame'] != fid or ack_meta['epoch'] != 25
                    or am.get('frame_id') != fid or am.get('epoch') != 25
                    or am.get('source_slot') != parsed['source'] or am.get('destination_slot') != parsed['destination']
                    or am.get('pair_tag') != parsed['pair_tag'].hex()
                    or am.get('base_tag') != parsed['base_meta']['reconstructed_tag'].hex()
                    or am.get('hud_tag') != parsed['hud_meta']['out_tag'].hex()):
                raise ValueError('accepted ACK identity or size mismatch')
            # Full verifier's replay rows independently bind decoded image/reference hashes.
            prev_tag = row['reconstructed_tag']
            accepted_count += 1
            accepted_max = max(accepted_max, len(pair))
            source_keys.setdefault((scene, fid), row['source_common_yuv_sha256'])
            if source_keys[(scene, fid)] != row['source_common_yuv_sha256']:
                raise ValueError(f'{scene}/{fid}: policy source pairing mismatch')
            if not row['attempts']:
                raise ValueError('accepted row omitted attempted candidates')
            zero_sse = next((a['hybrid']['active_squared_error'] for a in row['attempts'] if a['kind'] == 'zero'), None)
            if zero_sse is None:
                raise ValueError('candidate group has no zero-motion quality baseline')
            selected = [a for a in row['attempts'] if a.get('selected')]
            if len(selected) != 1 or selected[0]['complete_bytes'] != len(pair):
                raise ValueError('accepted packet is not the uniquely selected attempt')
            expected_choice = None
            backgrounds = list(dict.fromkeys(a['background'] for a in row['attempts']))
            if backgrounds != sorted(set(backgrounds)):
                raise ValueError('candidate background groups are not in causal fallback order')
            for bg in backgrounds:
                group = [a for a in row['attempts'] if a['background'] == bg]
                if not group or group[0]['kind'] != 'zero' or len({a['kind'] for a in group}) != len(group):
                    raise ValueError('candidate group does not start with a unique zero baseline')
                group_zero = group[0]['hybrid']['active_squared_error']
                eligible = []
                for a in group:
                    valid = len(read_object(a['packet'], STUDY)) <= CAP and a['hybrid']['active_squared_error'] <= group_zero
                    if a['quality_eligible'] is not (a['hybrid']['active_squared_error'] <= group_zero):
                        raise ValueError('candidate quality flag does not match same-group baseline')
                    if a['cap_fit'] is not (a['complete_bytes'] <= CAP):
                        raise ValueError('candidate cap flag does not match complete bytes')
                    if valid:
                        eligible.append(a)
                if eligible:
                    expected_choice = min(eligible, key=lambda a: a['complete_bytes'])
                    break
            if expected_choice is None or selected[0] is not expected_choice:
                raise ValueError('selected candidate does not follow cap/quality/minimum-size rule')
            if (row['selected_kind'] != selected[0]['kind']
                    or row['selected_background'] != selected[0]['background']):
                raise ValueError('accepted selection metadata differs from selected candidate')
            for attempt in row['attempts']:
                candidate = read_object(attempt['packet'], STUDY)
                cp = parse_pair(candidate, enforce_cap=False)
                if len(candidate) != attempt['complete_bytes'] or attempt['cap_fit'] != (len(candidate) <= CAP):
                    raise ValueError('attempt complete bytes/cap flag mismatch')
                if cp['base_meta']['reference_id'] != expected_ref or cp['base_meta']['reference_tag'].hex() != ref_tag:
                    raise ValueError('attempt uses wrong own accepted reference')
                if cp['hud_meta']['patch_words'] != HUD_WORDS:
                    raise ValueError('attempt HUD word count mismatch')
                if attempt['base_bytes'] != cp['base_meta']['bytes']:
                    raise ValueError('attempt base size mismatch')
                base_obj = read_object(attempt['base_packet'], STUDY)
                if base_obj != cp['base']:
                    raise ValueError('attempt base-only object differs from complete packet')
                attempted_count += 1
            if selected[0]['hybrid'] != row['hybrid'] or selected[0]['reconstructed_tag'] != row['reconstructed_tag']:
                raise ValueError('accepted row metrics/tag differ from selected attempt')
            if read_object(selected[0]['packet'], STUDY) != pair:
                raise ValueError('selected candidate bytes differ from accepted complete packet')
            paid = sum(float(a['encode_ms']) for a in row['attempts']) + sum(float(a['analysis_wall_ms']) for a in row['analyses'].values())
            service = paid + sum(float(a['quality_ms']) + float(a['bind_ms']) for a in row['attempts'])
            timing_values = [row['receive_ms'], row['ack_ms'], row['paid_base_encode_ms'], row['base_policy_service_ms']]
            timing_values += [a['analysis_wall_ms'] for a in row['analyses'].values()]
            timing_values += [a[k] for a in row['attempts'] for k in ('encode_ms', 'quality_ms', 'bind_ms')]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
                   for v in timing_values):
                raise ValueError('nonfinite or negative paid timing')
            if not math.isclose(paid, row['paid_base_encode_ms'], rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError('paid work omits a candidate or analysis')
            if not math.isclose(service, row['base_policy_service_ms'], rel_tol=1e-10, abs_tol=1e-7):
                raise ValueError('base policy service does not include all attempts')
        expected = summarize_rows(rows)
        if set(case['summary']) != set(expected):
            raise ValueError(f'{scene}/{policy}: summary field set mismatch')
        for name, value in expected.items():
            actual = case['summary'][name]
            if isinstance(value, float):
                if not math.isclose(float(actual), value, rel_tol=1e-10, abs_tol=1e-7):
                    raise ValueError(f'{scene}/{policy}: summary mismatch for {name}')
            elif actual != value:
                raise ValueError(f'{scene}/{policy}: summary mismatch for {name}')
        cases[(scene, policy)] = case
    if set(cases) != {(s, p) for s in SCENES for p in POLICIES}:
        raise ValueError('v29 campaign case matrix incomplete')
    baseline = json.loads((V28_STUDY / 'results.json').read_text())
    v28_cases = {(c['scene'], c['policy']): c for c in baseline['cases']}
    parity_rows = 0
    ec_negative_control_rows = 0
    for scene in SCENES:
        new = cases[(scene, 'mixed_lazy')]['rows']
        old = v28_cases[(scene, 'sample4_refine2')]['rows']
        for nr, orow in zip(new, old):
            if (nr['id'] != orow['id'] or nr['source_common_yuv_sha256'] != orow['source_common_yuv_sha256']
                    or read_object(nr['packet'], STUDY) != read_object(orow['packet'], V28_STUDY)
                    or read_object(nr['ack'], STUDY) != read_object(orow['ack'], V28_STUDY)
                    or nr['hybrid'] != orow['hybrid']):
                raise ValueError(f'{scene}/{nr["id"]}: mixed_lazy v28 parity mismatch')
            parity_rows += 1
        for ec_policy, plain_policy in (('mixed_ec', 'mixed_lazy'), ('adaptive_ec', 'adaptive_lazy')):
            ec_rows = cases[(scene, ec_policy)]['rows']
            plain_rows = cases[(scene, plain_policy)]['rows']
            for erow, prow in zip(ec_rows, plain_rows):
                if (erow['id'] != prow['id']
                        or read_object(erow['packet'], STUDY) != read_object(prow['packet'], STUDY)
                        or read_object(erow['ack'], STUDY) != read_object(prow['ack'], STUDY)
                        or erow['hybrid'] != prow['hybrid']):
                    raise ValueError(f'{scene}/{erow["id"]}: EC negative control changed accepted output')
                ec_negative_control_rows += 1
    replay_path = STUDY / 'replay.json'
    replay = None
    if replay_path.exists():
        replay = json.loads(replay_path.read_text())
        verify_replay(replay, cases)
    elif require_replay:
        raise ValueError('full decoded-chain replay.json is required')
    return dict(schema='gamebub-v29-independent-audit', source_sha256=source_inventory(data['source_sha256']),
                source_pins_verified=pin_count,
                cases=len(cases), accepted_frames=accepted_count, attempted_candidates=attempted_count,
                maximum_complete_bytes=accepted_max, exact_hud_words=accepted_count * HUD_WORDS,
                accepted_reference_links=reference_links, v28_parity_rows=parity_rows,
                ec_negative_control_rows=ec_negative_control_rows,
                decoded_replay_verified=replay is not None,
                physical_30fps_proven=False,
                claim_boundary='Python host measurements and nominal 30-ID/s byte projections only; no native or physical 30-fps proof.')


def verify_replay(replay: dict, cases: dict) -> None:
    """Check full verifier summary hashes against accepted packet tags and IDs."""
    if replay.get('schema') != 'gamebub-v29-replay':
        raise ValueError('unexpected decoded replay schema')
    if replay.get('results_sha256') != sha((STUDY / 'results.json').read_bytes()):
        raise ValueError('decoded replay is stale for current results')
    verifier = STUDY / 'verify.py'
    if not verifier.is_file() or replay.get('verifier_sha256') != sha(verifier.read_bytes()):
        raise ValueError('decoded replay verifier pin mismatch')
    _verify_replay_chains(replay, cases)
    if replay.get('accepted_pairs') != 384 or replay.get('exact_hud_words') != 384 * HUD_WORDS:
        raise ValueError('decoded replay totals do not cover complete campaign')
    if (replay.get('candidate_attempts') != 752 or replay.get('baseline_v28_exact_pairs') != 96
            or replay.get('adaptive_p_frames') != 184 or replay.get('entropy_candidate_planes') != 1128):
        raise ValueError('decoded replay candidate/parity totals mismatch')
    if replay.get('physical_30fps_proven') is not False:
        raise ValueError('decoded replay overclaims physical frame rate')


def _verify_replay_chains(replay: dict, cases: dict) -> None:
    chains = replay.get('chains')
    if not isinstance(chains, list):
        raise ValueError('replay.json missing decoded chains')
    indexed = {(x['scene'], x['policy']): x for x in chains}
    if len(indexed) != len(chains) or set(indexed) != set(cases):
        raise ValueError('decoded replay chains do not cover exact policy cases')
    for (scene, policy), case in cases.items():
        replay_rows = indexed[(scene, policy)].get('rows')
        if not isinstance(replay_rows, list) or len(replay_rows) != len(case['rows']):
            raise ValueError(f'{scene}/{policy}: decoded replay row count mismatch')
        previous_tag = None
        for row, check in zip(case['rows'], replay_rows):
            if check.get('id') != row['id']:
                raise ValueError(f'{scene}/{policy}: decoded replay IDs reordered')
            if (check.get('hybrid_rgb565_sha256') != row['hybrid_rgb565_sha256']
                    or check.get('decoded_tag') != row['reconstructed_tag']
                    or check.get('reference_tag') != row['reference_tag']):
                raise ValueError(f'{scene}/{policy}/{row["id"]}: decoded replay binding mismatch')
            if row['key']:
                if check.get('reference_tag') != bytes(16).hex():
                    raise ValueError(f'{scene}/{policy}/{row["id"]}: key reference tag nonzero')
            elif check.get('reference_tag') != previous_tag:
                raise ValueError(f'{scene}/{policy}/{row["id"]}: replay uses another accepted reference')
            previous_tag = check['decoded_tag']


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
