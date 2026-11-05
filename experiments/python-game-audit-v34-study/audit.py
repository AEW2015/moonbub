#!/usr/bin/env python3
"""Independent provenance, causal accounting, selection and standards audit."""
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
CONTROLLER = ROOT / 'experiments/python-game-controller-v34-study'
HUD = ROOT / 'experiments/python-game-hud-runs-v33-study'
HIERARCHY = ROOT / 'experiments/python-game-hierarchy-v34-study'
SELECTIVE = ROOT / 'experiments/python-game-selective-v34-study'
OPAQUE = ROOT / 'experiments/python-game-opaque-v34-study'
STANDARD = ROOT / 'experiments/python-game-standard-v24-study/results.json'
CAP, BINDING, FRAMES = 49152, 60, 48
SCENES = ('mass-effect-2600', 'mass-effect-7200')
POLICIES = ('control', 'hierarchy_full', 'hierarchy_select25')


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot import audit helper {path}')
    out = importlib.util.module_from_spec(spec)
    sys.modules[name] = out
    spec.loader.exec_module(out)
    return out


h = module('audit_controller_v34_helpers', CONTROLLER / 'helpers.py')
chooser = module('audit_controller_v34_selector', CONTROLLER / 'controller.py')
v32audit = module('audit_v32_standard_helpers', ROOT / 'experiments/python-game-audit-v32-study/audit.py')
opaque_helpers = module('audit_opaque_v34_helpers', OPAQUE / 'helpers.py')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path, schema: str) -> dict:
    data = json.loads(path.read_text())
    if data.get('schema') != schema:
        raise ValueError(f'{path}: unexpected schema')
    return data


def verify_pins(data: dict, label: str) -> int:
    pins = data.get('source_sha256')
    if not isinstance(pins, dict) or not pins:
        raise ValueError(f'{label}: source pins missing')
    for rel, expected in pins.items():
        path = Path(rel)
        if path.is_absolute() or '..' in path.parts or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f'{label}: invalid pin path/hash')
        if sha(ROOT / path) != expected:
            raise ValueError(f'{label}: source hash mismatch: {rel}')
    return len(pins)


def metric_sse(metric: dict) -> tuple[int, int, float]:
    sse, samples = metric.get('active_squared_error'), metric.get('active_channel_samples')
    if type(sse) is not int or type(samples) is not int or sse < 0 or samples <= 0:
        raise ValueError('invalid integer active RGB totals')
    mse = sse / samples
    if metric.get('active_mse') != mse:
        raise ValueError('active MSE does not reconcile')
    return sse, samples, mse


def audit() -> dict:
    controller = load(CONTROLLER / 'results.json', 'gamebub-controller-v34')
    hierarchy = load(HIERARCHY / 'results.json', 'gamebub-hierarchy-v34')
    selective = load(SELECTIVE / 'results.json', 'gamebub-selective-v34')
    hud = load(HUD / 'results.json', 'gamebub-run-HUD-v33')
    pin_counts = dict(controller=verify_pins(controller, 'controller v34'),
                      hierarchy=verify_pins(hierarchy, 'hierarchy v34'),
                      selective=verify_pins(selective, 'selective v34'),
                      hud=verify_pins(hud, 'HUD v33'))
    if (controller.get('physical_30fps_proven') is not False
            or controller.get('new_RTL_implemented') is not False
            or controller.get('geometry') != dict(coded=[720, 480], active=[720, 405],
                maximum_HUD_words=21120, cap=CAP)):
        raise ValueError('controller geometry/scope flags mismatch')
    indexed = {(case['scene'], case['policy']): case for case in controller['cases']}
    expected = {(scene, policy) for scene in SCENES for policy in POLICIES}
    if len(indexed) != 6 or set(indexed) != expected:
        raise ValueError('controller must contain exactly six cohorts')
    hud_cases = {case['scene']: case for case in hud['cases']}
    if set(hud_cases) != set(SCENES):
        raise ValueError('HX33 common sidecar lacks one of the two scenes')
    hud_rows = {}
    for scene, case in hud_cases.items():
        if [row['id'] for row in case['rows']] != list(range(FRAMES)):
            raise ValueError('HX33 frame order incomplete')
        hud_rows[scene] = case['rows']

    inputs = h.load(h.n.V24 / 'results.json')['inputs']
    source_cases = {case['scene']: case for case in inputs}
    if set(source_cases) != set(SCENES):
        raise ValueError('expected source scenes missing')
    old_selector = h.select30
    cohort_reports, comparisons, standard_points = {}, {}, {}
    total_rows = total_candidates = exact_control_rows = 0
    for scene in SCENES:
        standard_points[scene] = {}
        old_input = source_cases[scene]['rows']
        hr = hud_rows[scene]
        if [r['id'] for r in old_input] != list(range(FRAMES)):
            raise ValueError('source IDs incomplete or reordered')
        hud_bytes_by_id = {r['id']: r['bytes'] for r in hr}
        for policy in POLICIES:
            case = indexed[(scene, policy)]
            rows = case['rows']
            if [r['id'] for r in rows] != list(range(FRAMES)):
                raise ValueError(f'{scene}/{policy}: IDs incomplete or reordered')
            rx = h.p.Receiver(epoch=25)
            ref, refid, slot, previous_tag = None, h.m.NO_REF, 0, None
            sums = dict(body=0, base=0, hud=0, binding=0, sse=0, samples=0, maximum=0,
                        analysis_ms=0.0, encode_group_ms=0.0, component_ms=0.0,
                        selection_ms=0.0, wrap_ms=0.0, quality_ms=0.0, bind_ms=0.0,
                        receive_ms=0.0, ack_ms=0.0, candidates=0, group_calls=0,
                        selected_child=0, selected_gm34=0, decoder_reads=0,
                        shadow_bytes=0, shadow_sse=0)
            accepted_ids = []
            for fid, (row, srcrow, hudrow) in enumerate(zip(rows, old_input, hr, strict=True)):
                key = fid % 24 == 0
                expected_ref = h.m.NO_REF if key else fid - 1
                if row['key'] is not key or row['reference_id'] != expected_ref:
                    raise ValueError(f'{scene}/{policy}/{fid}: accepted reference ID mismatch')
                if row['reference_tag'] != (bytes(16).hex() if key else previous_tag):
                    raise ValueError(f'{scene}/{policy}/{fid}: not the cohort-local accepted reference')
                if row['source_sha256'] != srcrow['common_yuv420_u8_sha256']:
                    raise ValueError('source lineage mismatch')
                hud_bytes = h.raw(hudrow['packet'], HUD)
                if h.raw(row['hud_packet'], HUD) != hud_bytes or len(hud_bytes) != row['hud_bytes']:
                    raise ValueError(f'{scene}/{policy}/{fid}: HX33 shared sidecar mismatch')
                if row['binding_bytes'] != BINDING:
                    raise ValueError('CP34 binding byte count mismatch')
                pair = h.raw(row['packet'])
                base_packet = h.raw(row['base_packet'])
                ack = h.raw(row['ack'])
                pm = h.p.parse_pair(pair)
                bm = pm['base_meta']
                if (pm['base'] != base_packet or pm['hud'] != hud_bytes
                        or len(pair) != row['body_bytes']
                        or len(base_packet) != row['base_bytes']
                        or len(pair) != len(base_packet) + len(hud_bytes) + BINDING
                        or len(pair) > CAP):
                    raise ValueError('accepted complete bytes, components or cap mismatch')
                if (pm['frame_id'] != fid or pm['key'] is not key
                        or pm['source_slot'] != row['source_slot']
                        or pm['destination_slot'] != row['destination_slot']
                        or bm['reference_id'] != expected_ref
                        or bm['reference_tag'].hex() != row['reference_tag']
                        or bm['reconstructed_tag'].hex() != row['reconstructed_tag']):
                    raise ValueError('accepted CP34 identity/tag/reference mismatch')
                ackmeta = h.p.validate_ack(ack, pair)
                if ackmeta['frame_id'] != fid or ackmeta['base_tag'] != row['reconstructed_tag']:
                    raise ValueError('JA34 does not bind accepted output/frame')
                out_planes, hud_patches, ack_replay = rx.receive(pair)
                if ack_replay != ack:
                    raise ValueError('replayed JA34 differs from retained ACK')
                source, original = h.n.source(srcrow), h.n.original(srcrow)
                hybrid = h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(out_planes)),
                                     tuple(patch['words'] for patch in hud_patches))
                metric = h.n.metric(original, hybrid)
                if metric != row['hybrid'] or h.n.digest(hybrid) != row['hybrid_sha256']:
                    raise ValueError('accepted source RGB/SSE evidence mismatch')
                sse, samples, _ = metric_sse(metric)

                attempts = row['attempts']
                if not attempts:
                    raise ValueError('accepted row has no paid candidates')
                by_bg = sorted({a['background'] for a in attempts})
                if by_bg not in ([16], [16, 32]):
                    raise ValueError('invalid scale-map fallback sequence')
                expected_selected = None
                expected_shadow = None
                groups_found = []
                for bg in by_bg:
                    controls = [a for a in attempts if a['background'] == bg
                                and not a['kind'].startswith('child')]
                    children = [a for a in attempts if a['background'] == bg
                                and a['kind'].startswith('child')]
                    if [a['kind'] for a in controls] != ['zero', 'half32', 'zero_band', 'half32_band'] and not key:
                        raise ValueError('control candidate group/order incomplete')
                    if key and [a['kind'] for a in controls] != ['zero', 'zero_band']:
                        raise ValueError('key control candidate group/order incomplete')
                    for a in attempts:
                        if a['background'] != bg:
                            continue
                        if a['complete_bytes'] != a['base_bytes'] + row['hud_bytes'] + BINDING:
                            raise ValueError('attempt packet component sum mismatch')
                        if a['cap_fit'] is not (a['complete_bytes'] <= CAP):
                            raise ValueError('candidate cap flag mismatch')
                        m = a['hybrid']
                        metric_sse(m)
                        raw_pair = h.raw(a['packet'])
                        raw_base = h.raw(a['base_packet'])
                        parsed = h.p.parse_pair(raw_pair)
                        if (len(raw_pair) != a['complete_bytes'] or parsed['base'] != raw_base
                                or parsed['hud'] != hud_bytes or len(raw_base) != a['base_bytes']
                                or parsed['base_meta']['reference_id'] != expected_ref
                                or parsed['base_meta']['reference_tag'].hex() != row['reference_tag']):
                            raise ValueError('attempt packet/reference binding mismatch')
                        if a['wire_magic'] != raw_base[:4].decode():
                            raise ValueError('attempt wire profile label mismatch')
                    # Run the original v30 selector on actual current-history controls.
                    tier_winner, tier_baseline = old_selector.select_tier(controls, 'band_strict')
                    if tier_winner is None:
                        winner = chooser.choose(None, children)
                        if winner is not None:
                            raise ValueError('child selected without a fitting same-history shadow')
                        continue
                    winner = chooser.choose(tier_winner, children)
                    if winner is None:
                        continue
                    if expected_selected is not None:
                        raise ValueError('campaign continued after a fitting selection tier')
                    expected_selected, expected_shadow = winner, tier_winner
                    groups_found.append(bg)
                if expected_selected is None:
                    raise ValueError('no selected fitting candidate')
                chosen = [a for a in attempts if a.get('selected') is True]
                if len(chosen) != 1 or chosen[0]['kind'] != expected_selected['kind'] or chosen[0]['complete_bytes'] != expected_selected['complete_bytes']:
                    raise ValueError(f'{scene}/{policy}/{fid}: actual selection {[(a["kind"],a["background"],a["complete_bytes"]) for a in chosen]} differs from expected {(expected_selected["kind"], expected_selected["background"], expected_selected["complete_bytes"])}')
                shadow = expected_shadow
                if (row['shadow_kind'] != shadow['kind']
                        or row['shadow_complete_bytes'] != shadow['complete_bytes']
                        or row['shadow_source_sse'] != shadow['hybrid']['active_squared_error']):
                    raise ValueError('same-history shadow metadata mismatch')
                winner = chosen[0]
                if (winner['hybrid'] != row['hybrid'] or winner['wire_magic'] != row['wire_magic']
                        or winner['selected'] is not True):
                    raise ValueError('accepted row is not selected candidate')

                # Reconcile each independently charged host-work bucket.
                analysis_ms = sum(v['wall_ms'] for v in row['analyses'].values())
                group_ms = sum(v['wall_ms'] for v in row['encode_groups'])
                wrap_ms = sum(a['wrap_ms'] for a in attempts)
                quality_ms = sum(a['quality_ms'] for a in attempts)
                bind_ms = sum(a['bind_ms'] for a in attempts)
                paid = analysis_ms + group_ms + row['component_ms'] + row['selection_ms'] + wrap_ms + quality_ms + bind_ms
                if not math.isclose(paid, row['paid_policy_ms'], rel_tol=1e-10, abs_tol=1e-5):
                    raise ValueError('paid work omitted/recounted a shared group or actual candidate trial')
                sums['body'] += len(pair); sums['base'] += len(base_packet); sums['hud'] += len(hud_bytes)
                sums['binding'] += BINDING; sums['sse'] += sse; sums['samples'] += samples
                sums['maximum'] = max(sums['maximum'], len(pair)); sums['analysis_ms'] += analysis_ms
                sums['encode_group_ms'] += group_ms; sums['component_ms'] += row['component_ms']
                sums['selection_ms'] += row['selection_ms']; sums['wrap_ms'] += wrap_ms
                sums['quality_ms'] += quality_ms; sums['bind_ms'] += bind_ms
                sums['receive_ms'] += row['receive_ms']; sums['ack_ms'] += row['ack_ms']
                sums['candidates'] += len(attempts); sums['group_calls'] += len(row['encode_groups'])
                sums['selected_child'] += winner['kind'].startswith('child')
                sums['selected_gm34'] += winner['wire_magic'] == 'GM34'
                sums['decoder_reads'] += winner['work']['decoder_reference_sample_reads']
                sums['shadow_bytes'] += shadow['complete_bytes']; sums['shadow_sse'] += shadow['hybrid']['active_squared_error']
                accepted_ids.append(fid)
                previous_tag = row['reconstructed_tag']
                ref, refid, slot = out_planes, fid, row['destination_slot']
                total_candidates += len(attempts)
                if policy == 'control':
                    ref_v33 = h.load(ROOT / 'experiments/python-game-global-v33-study/results.json')['cases']
                    v33case = next(c for c in ref_v33 if c['scene'] == scene and c['policy'] == 'band_control')
                    # CP34 changes the envelope; the base stream and pixels remain the exact v33 control.
                    if (base_packet != h.raw(v33case['rows'][fid]['base_packet'], ROOT / 'experiments/python-game-global-v33-study')
                            or metric != v33case['rows'][fid]['hybrid']):
                        raise ValueError('control base/pixel parity against frozen v33 control failed')
                    exact_control_rows += 1

            summary = case['summary']
            mse = sums['sse'] / sums['samples']
            for name, actual in (('frames', len(rows)), ('complete_bytes', sums['body']),
                                 ('base_bytes', sums['base']), ('hud_bytes', sums['hud']),
                                 ('binding_bytes', sums['binding']), ('active_squared_error', sums['sse']),
                                 ('active_channel_samples', sums['samples']),
                                 ('maximum_complete_bytes', sums['maximum']),
                                 ('actual_candidate_frames', sums['candidates']),
                                 ('shared_pair_calls', sums['group_calls']),
                                 ('selected_child_frames', sums['selected_child']),
                                 ('selected_GM34_frames', sums['selected_gm34']),
                                 ('control_shadow_bytes', sums['shadow_bytes']),
                                 ('control_shadow_sse', sums['shadow_sse']),
                                 ('selected_decoder_reference_reads', sums['decoder_reads'])):
                if summary[name] != actual:
                    raise ValueError(f'{scene}/{policy}: summary mismatch at {name}')
            if not math.isclose(summary['active_mse'], mse, rel_tol=1e-13):
                raise ValueError(f'{scene}/{policy}: summary MSE mismatch')
            for name, value in (('mean_analysis_ms', sums['analysis_ms']),
                                ('mean_shared_encode_ms', sums['encode_group_ms']),
                                ('mean_HM34_pack_verify_ms', sums['component_ms']),
                                ('mean_paid_policy_ms', sum(r['paid_policy_ms'] for r in rows)),
                                ('mean_receiver_ms', sums['receive_ms'])):
                divisor = FRAMES if name.startswith('mean_') else 1
                if not math.isclose(summary[name], value / divisor, rel_tol=1e-10, abs_tol=1e-5):
                    raise ValueError(f'{scene}/{policy}: paid work summary mismatch at {name}')
            if summary['nominal_Mbps_at30'] != sums['body'] * 5 / 1_000_000:
                raise ValueError(f'{scene}/{policy}: nominal rate arithmetic mismatch')
            if sums['maximum'] > CAP:
                raise ValueError('accepted stream exceeds complete cap')
            cohort_reports[f'{scene}/{policy}'] = dict(
                frames=FRAMES, own_accepted_reference_history=True, complete_bytes=sums['body'],
                base_bytes=sums['base'], shared_HX33_bytes=sums['hud'], binding_bytes=sums['binding'],
                maximum_complete_bytes=sums['maximum'], cap_fits=True,
                active_squared_error=sums['sse'], active_channel_samples=sums['samples'], active_mse=mse,
                same_history_shadow_bytes=sums['shadow_bytes'], same_history_shadow_sse=sums['shadow_sse'],
                same_history_shadow_mean_mse=sums['shadow_sse'] / sums['samples'],
                paid_work_ms={k: sums[k] for k in ('analysis_ms','encode_group_ms','component_ms',
                    'selection_ms','wrap_ms','quality_ms','bind_ms')},
                paid_mean_ms=summary['mean_paid_policy_ms'], candidates=sums['candidates'],
                selected_GM34_frames=sums['selected_gm34'], selected_child_frames=sums['selected_child'],
                selected_decoder_reference_sample_reads=sums['decoder_reads'])
            standard_points[scene][policy] = v32audit.standard_operating_points(
                json.loads(STANDARD.read_text()), scene, hud_bytes_by_id, mse)
            if policy == 'control':
                ctrl_summary = summary
            else:
                comparisons[f'{scene}/{policy}'] = dict(
                    complete_byte_delta_vs_v34_control=summary['complete_bytes']-ctrl_summary['complete_bytes'],
                    active_mse_delta_vs_v34_control=summary['active_mse']-ctrl_summary['active_mse'],
                    same_history_shadow_bytes_delta_vs_control=sums['shadow_bytes']-ctrl_summary['complete_bytes'],
                    same_history_shadow_sse_delta_vs_control=sums['shadow_sse']-ctrl_summary['active_squared_error'],
                    note='policy shadow is re-encoded on this policy own causal accepted-reference history')
            total_rows += len(rows)

    def component_summary(data, label):
        if data.get('causal_campaign') is not False or data.get('physical_30fps_proven') is not False:
            raise ValueError(f'{label}: fixed-reference scope flags missing')
        sm = data['summary']
        if label == 'hierarchy':
            if sm['source_frames'] != 24 or sm['raw_band16_old_motion_bytes'] - sm['raw_band16_hm34_motion_bytes'] != sm['raw_band16_motion_bytes_saved']:
                raise ValueError('hierarchy component framing/motion byte summary mismatch')
        else:
            if sm['frames'] != 24 or set(sm) & {'causal_campaign'}:
                raise ValueError('selective fixed-reference source count mismatch')
        return dict(source_frames=sm.get('source_frames', sm.get('frames')), causal_campaign=False,
                    summary=sm, scope='fixed-reference component probe; selected outputs do not update next reference')

    fixed = dict(hierarchy=component_summary(hierarchy, 'hierarchy'),
                 selective=component_summary(selective, 'selective'))
    opaque = load(OPAQUE / 'results.json', 'gamebub-opaque-v34')
    opaque_pin_count = verify_pins(opaque, 'opaque v34')
    for rel, expected_hash in opaque.get('producer_sha256', {}).items():
        if sha(ROOT / rel) != expected_hash:
            raise ValueError(f'opaque producer source hash mismatch: {rel}')
    for filename, expected_hash in opaque['offline_evidence_sha256'].items():
        if sha(OPAQUE / filename) != expected_hash:
            raise ValueError(f'opaque offline evidence hash mismatch: {filename}')
    if (opaque.get('causal_campaign') is not True or opaque.get('decoder_format_changed') is not False
            or opaque.get('physical_30fps_proven') is not False
            or opaque.get('preserve_first_chroma_row_column') is not True):
        raise ValueError('opaque masking scope/safe chroma contract mismatch')
    opaque_cases = {case['scene']: case for case in opaque['cases']}
    if set(opaque_cases) != set(SCENES) or any(c['policy'] != 'opaque_masked' for c in opaque_cases.values()):
        raise ValueError('opaque custom case matrix invalid')
    opaque_rows_report = {}
    for scene in SCENES:
        case, srcs, hr = opaque_cases[scene], source_cases[scene]['rows'], hud_rows[scene]
        if [r['id'] for r in case['rows']] != list(range(FRAMES)):
            raise ValueError('opaque custom IDs incomplete or reordered')
        rx = h.p.Receiver(epoch=25)
        ref, refid, slot, prevtag = None, h.m.NO_REF, 0, None
        byte_total = sse_total = sample_total = max_frame = full_changed = row_candidate_count = 0
        policy_ms = 0.0
        for fid, (row, srcrow, hu) in enumerate(zip(case['rows'], srcs, hr, strict=True)):
            key = fid % 24 == 0
            if row['key'] is not key or row['reference_id'] != (h.m.NO_REF if key else fid-1):
                raise ValueError('opaque custom reference chain ID mismatch')
            if row['reference_tag'] != (bytes(16).hex() if key else prevtag):
                raise ValueError('opaque custom accepted-reference tag mismatch')
            original_yuv, masked_yuv, original_rgb, patches = opaque_helpers.source(srcrow)
            masked_hash = opaque_helpers.digest(b''.join(v.astype('u1').tobytes() for v in masked_yuv))
            if (row['source_sha256'] != srcrow['common_yuv420_u8_sha256']
                    or row['masked_source_sha256'] != masked_hash
                    or row['visible_precodec_equal'] is not True):
                raise ValueError('safe opaque source-mask lineage/equivalence mismatch')
            full = opaque_helpers.requested_full_mask_audit(original_yuv, patches)
            if (row['requested_full_mask_audit'] != full or full['visible_precodec_equal'] is not False
                    or full['changed_visible_rgb565_words'] <= 0):
                raise ValueError('requested full-plane mask negative evidence mismatch')
            full_changed += full['changed_visible_rgb565_words']
            hud_bytes = opaque_helpers.raw(hu['packet'], HUD)
            pair = opaque_helpers.raw(row['packet'], OPAQUE)
            base_packet = opaque_helpers.raw(row['base_packet'], OPAQUE)
            ack = opaque_helpers.raw(row['ack'], OPAQUE)
            pm = h.p.parse_pair(pair)
            if (pm['base'] != base_packet or pm['hud'] != hud_bytes or len(hud_bytes) != row['hud_bytes']
                    or row['binding_bytes'] != BINDING or len(pair) != row['body_bytes']
                    or len(base_packet) != row['base_bytes'] or len(pair) != len(base_packet)+len(hud_bytes)+BINDING
                    or len(pair)>CAP):
                raise ValueError(f'opaque CP34/HX33 byte accounting/cap mismatch {scene}/{fid}')
            if (pm['frame_id'] != fid or pm['base_meta']['reference_id'] != row['reference_id']
                    or pm['base_meta']['reference_tag'].hex() != row['reference_tag']
                    or pm['source_slot'] != row['source_slot'] or pm['destination_slot'] != row['destination_slot']):
                raise ValueError('opaque accepted component identity/reference mismatch')
            ack_checked = h.p.validate_ack(ack, pair)
            pixels, hud_patches, decoded_ack = rx.receive(pair)
            if decoded_ack != ack or ack_checked['frame_id'] != fid:
                raise ValueError('opaque JA34 mismatch')
            display = h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),
                                  tuple(p['words'] for p in hud_patches))
            metric = h.n.metric(original_rgb, display)
            if metric != row['hybrid'] or h.n.digest(display) != row['hybrid_sha256']:
                raise ValueError('opaque accepted metric is not measured against original source RGB')
            sse, samples, _ = metric_sse(metric)
            attempts = row['attempts']
            backgrounds = sorted({a['background'] for a in attempts})
            if backgrounds not in ([16], [16, 32]):
                raise ValueError('opaque invalid scale map fallback')
            expected = None
            for bg in backgrounds:
                group = [a for a in attempts if a['background'] == bg]
                winner, _ = h.select30.select_tier(group, 'band_strict')
                if winner is not None:
                    if expected is not None:
                        raise ValueError('opaque selection continued past fitting strict tier')
                    expected = winner
                for a in group:
                    raw_pair = opaque_helpers.raw(a['packet'], OPAQUE)
                    raw_base = opaque_helpers.raw(a['base_packet'], OPAQUE)
                    parsed = h.p.parse_pair(raw_pair)
                    if (len(raw_pair) != a['complete_bytes']
                            or a['complete_bytes'] != a['base_bytes'] + row['hud_bytes'] + BINDING
                            or parsed['base'] != raw_base or parsed['hud'] != hud_bytes
                            or a['cap_fit'] is not (a['complete_bytes'] <= CAP)):
                        raise ValueError('opaque candidate actual bytes/cap/HX33 binding mismatch')
                    metric_sse(a['hybrid'])
                    row_candidate_count += 1
            selected = [a for a in attempts if a.get('selected') is True]
            if expected is None or len(selected) != 1 or selected[0]['kind'] != expected['kind'] or selected[0]['complete_bytes'] != expected['complete_bytes']:
                raise ValueError('opaque selected candidate does not match strict selection')
            paid = (sum(a['wall_ms'] for a in row['analyses'].values())
                    +sum(g['wall_ms'] for g in row['encode_groups'])
                    +sum(a['quality_ms']+a['bind_ms'] for a in attempts))
            if not math.isclose(paid, row['paid_policy_ms'], rel_tol=1e-10, abs_tol=1e-5):
                raise ValueError('opaque paid work subtotals mismatch')
            control_row = indexed[(scene, 'control')]['rows'][fid]
            if (row['original_control_bytes'] != control_row['body_bytes']
                    or row['original_control_hybrid'] != control_row['hybrid']):
                raise ValueError('opaque corrected baseline is not actual CP34/HX33 controller control')
            byte_total += len(pair); sse_total += sse; sample_total += samples
            max_frame = max(max_frame, len(pair)); policy_ms += paid
            prevtag = pm['base_meta']['reconstructed_tag'].hex()
            ref, refid, slot = pixels, fid, row['destination_slot']
        sm = case['summary']
        if (byte_total != sm['complete_bytes'] or sse_total != sm['active_squared_error']
                or sample_total != sm['active_channel_samples'] or max_frame != sm['maximum_complete_bytes']
                or max_frame > CAP or sm['cap_violations'] != 0
                or not math.isclose(sse_total/sample_total, sm['active_mse'], rel_tol=1e-13)):
            raise ValueError('opaque custom aggregate accounting mismatch')
        original_baseline = case['baseline_summary']
        if (original_baseline['complete_bytes'] != sum(r['body_bytes'] for r in indexed[(scene,'control')]['rows'])
                or original_baseline['active_squared_error'] != sum(r['hybrid']['active_squared_error'] for r in indexed[(scene,'control')]['rows'])):
            raise ValueError('opaque corrected control baseline aggregate mismatch')
        opaque_rows_report[scene] = dict(frames=FRAMES, complete_bytes=byte_total,
            active_squared_error=sse_total, active_channel_samples=sample_total, active_mse=sse_total/sample_total,
            max_complete_bytes=max_frame, cap_fits=True, visible_safe_mask_frames=FRAMES,
            full_mask_visible_negative_frames=sum(r['requested_full_mask_audit']['changed_visible_rgb565_words']>0 for r in case['rows']),
            full_mask_changed_visible_rgb565_words=full_changed,
            actual_candidate_packets=row_candidate_count, mean_paid_policy_ms=policy_ms/FRAMES,
            corrected_CP34_HX33_control_bytes=original_baseline['complete_bytes'],
            corrected_control_source_sse=original_baseline['active_squared_error'],
            historical_HU25_bytes_not_used_for_savings=True)

    native_cases = opaque.get('native_cases', [])
    native_index = {(c['scene'],c['encoder'],c['processed'],c['parameter']):c for c in native_cases}
    if len(native_cases) != 12 or len(native_index) != 12:
        raise ValueError('expected twelve distinct actual native same-processed cases')
    native_report = {}
    for item in native_cases:
        if item.get('supported') is not True or [r['id'] for r in item['rows']] != list(range(FRAMES)):
            raise ValueError('native case unsupported or frame order incomplete')
        ext = opaque_helpers.raw(item['extradata'], OPAQUE)
        sum_bytes = sum_sse = sum_samples = 0
        maximum = 0
        for fid, row in enumerate(item['rows']):
            if (row['pts'] != fid or row['dts'] != fid or row['key'] is not (fid%24==0)
                    or row['hud_packet'] != hud_rows[item['scene']][fid]['packet']):
                raise ValueError('native PTS/DTS/key/common-HX33 alignment mismatch')
            au = opaque_helpers.raw(row['access_unit'], OPAQUE)
            charged_ext = len(ext) if fid == 0 else 0
            if (len(au) != row['access_unit_bytes'] or row['extradata_bytes_charged'] != charged_ext
                    or row['hud_bytes'] != len(opaque_helpers.raw(row['hud_packet'], HUD))
                    or row['binding_bytes'] != BINDING or row['body_bytes'] != len(au)+row['hud_bytes']+BINDING+charged_ext):
                raise ValueError('native AU + once-only extradata + HX33 + binding sum mismatch')
            sse, samples, _ = metric_sse(row['hybrid'])
            sum_bytes += row['body_bytes']; sum_sse += sse; sum_samples += samples
            maximum=max(maximum,row['body_bytes'])
        sm=item['summary']
        if (sm['complete_bytes'] != sum_bytes or sm['active_squared_error'] != sum_sse
                or sm['active_channel_samples'] != sum_samples or sm['maximum_complete_bytes'] != maximum
                or sm['cap_violations'] != sum(r['body_bytes']>CAP for r in item['rows'])
                or not math.isclose(sm['active_mse'],sum_sse/sum_samples,rel_tol=1e-13)):
            raise ValueError('native aggregate accounting mismatch')
    for scene in SCENES:
        target = opaque_cases[scene]['summary']['active_mse']
        for codec in ('libx265','libsvtav1'):
            eligible=[]
            for (sc,enc,processed,q),item in native_index.items():
                if sc==scene and enc==codec and processed=='masked':
                    sm=item['summary']
                    if sm['active_mse']<=target and sm['cap_violations']==0:
                        eligible.append(item)
            if not eligible:
                raise ValueError(f'{scene}/{codec}: no same-masked-input native quality/cap point')
            selected=min(eligible,key=lambda c:c['summary']['complete_bytes'])
            native_report[f'{scene}/{codec}'] = dict(processed='masked', parameter=selected['parameter'],
                complete_bytes=selected['summary']['complete_bytes'], active_mse=selected['summary']['active_mse'],
                max_frame_bytes=selected['summary']['maximum_complete_bytes'],
                same_processed_masked_input=True, same_HX33_and_60B=True,
                meets_custom_MSE_and_cap=True)
    offcoeff=json.loads((OPAQUE/'offline_coefficients.json').read_text())
    offmask=json.loads((OPAQUE/'offline_mask_cost.json').read_text())
    if (offcoeff.get('schema')!='gamebub-opaque-offline-coefficients-v34'
            or len(offcoeff.get('cases',[]))!=2 or len(offmask.get('mask_only_ms_samples',[]))!=96):
        raise ValueError('opaque offline coefficient/mask evidence missing')
    coefficient_report = {}
    for item in offcoeff['cases']:
        if [r['id'] for r in item['rows']] != list(range(FRAMES)):
            raise ValueError('offline coefficient IDs incomplete')
        totals = {label:dict(zero=0,dc=0,general=0,cycles=0) for label in ('masked','control')}
        for row in item['rows']:
            for label in ('masked','control'):
                rec=row[label]
                if rec['zero']+rec['dc']+rec['general'] != 8100:
                    raise ValueError('offline coefficient block classification is not exhaustive')
                for field in ('zero','dc','general'):
                    totals[label][field]+=rec[field]
                totals[label]['cycles']+=rec['two_bank_inverse_component_cycles']
        if any(totals[label][key]!=item['summary'][label][key] for label in ('masked','control') for key in ('zero','dc','general')):
            raise ValueError('offline coefficient aggregate mismatch')
        coefficient_report[item['scene']] = totals
    offline_summary=dict(offline_coefficients_sha256=sha(OPAQUE/'offline_coefficients.json'),
        offline_mask_cost_sha256=sha(OPAQUE/'offline_mask_cost.json'),
        mask_only_mean_ms=offmask['mean_mask_only_ms'],
        logical_uint8_source_bytes=offmask['logical_uint8_source_bytes'],
        actual_int16_source_bytes=offmask['actual_int16_source_bytes'],
        constant_stores_per_frame=offmask['constant_stores_per_frame'],
        conditional_two_bank_inverse_coefficients=coefficient_report,
        assumed_clock_MHz=offcoeff['clock_MHz_assumed_unclosed'],
        conditional_inverse_model_only=True,physical_fpga_claim=False,
        coefficients_total_frames=96,blocks_per_frame=8100)
    direct = [
        'experiments/python-game-controller-v34-study/results.json',
        'experiments/python-game-controller-v34-study/helpers.py',
        'experiments/python-game-controller-v34-study/controller.py',
        'experiments/python-game-controller-v34-study/model.py',
        'experiments/python-game-controller-v34-study/protocol.py',
        'experiments/python-game-controller-v34-study/verify.py',
        'experiments/python-game-controller-v34-study/test_model.py',
        'experiments/python-game-controller-v34-study/benchmark.py',
        'experiments/python-game-hierarchy-v34-study/results.json',
        'experiments/python-game-selective-v34-study/results.json',
        'experiments/python-game-hud-runs-v33-study/results.json',
        'experiments/python-game-opaque-v34-study/results.json',
        'experiments/python-game-opaque-v34-study/helpers.py',
        'experiments/python-game-opaque-v34-study/model.py',
        'experiments/python-game-opaque-v34-study/benchmark.py',
        'experiments/python-game-opaque-v34-study/verify.py',
        'experiments/python-game-opaque-v34-study/test_model.py',
        'experiments/python-game-opaque-v34-study/README.md',
        'experiments/python-game-opaque-v34-study/offline_coefficients.json',
        'experiments/python-game-opaque-v34-study/offline_mask_cost.json',
        'experiments/python-game-opaque-v34-study/verify.py',
        'experiments/python-game-standard-v24-study/results.json',
        'experiments/python-game-audit-v34-study/audit.py',
        'experiments/python-game-audit-v34-study/baseline.json',
        'experiments/python-game-audit-v34-study/test_baseline.py',
        'experiments/python-game-audit-v32-study/audit.py',
    ]
    flat = {}
    for data in (controller, hierarchy, selective, hud, opaque):
        for rel, digest in data['source_sha256'].items():
            if rel in flat and flat[rel] != digest:
                raise ValueError(f'conflicting flat source pin: {rel}')
            flat[rel] = digest
    for rel in direct:
        flat[rel] = sha(ROOT / rel)
    for rel, digest in opaque.get('producer_sha256', {}).items():
        if rel in flat and flat[rel] != digest:
            raise ValueError(f'opaque producer pin conflicts: {rel}')
        flat[rel] = digest
    pin_report = {}
    for name, data, folder, count in (('controller',controller,CONTROLLER,pin_counts['controller']),
                                      ('hierarchy',hierarchy,HIERARCHY,pin_counts['hierarchy']),
                                      ('selective',selective,SELECTIVE,pin_counts['selective']),
                                      ('hud',hud,HUD,pin_counts['hud'])):
        pin_report[name] = dict(results_sha256=sha(folder/'results.json'),
            source_pin_set_sha256=hashlib.sha256(json.dumps(data['source_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            source_pin_count=count)
    pin_report['opaque'] = dict(results_sha256=sha(OPAQUE/'results.json'),
        source_pin_set_sha256=hashlib.sha256(json.dumps(opaque['source_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        source_pin_count=opaque_pin_count, producer_pin_count=len(opaque['producer_sha256']))
    return dict(schema='gamebub-python-game-audit-v34', source_sha256=dict(sorted(flat.items())),
                source_pin_sets=pin_report, cohort_rows=total_rows, accepted_control_parity_rows=exact_control_rows,
                cohorts=cohort_reports, comparison_to_control=comparisons,
                same_HX33_and_60B_standards=standard_points, fixed_reference_components=fixed,
                opaque_masking=opaque_rows_report, opaque_same_processed_native_points=native_report,
                opaque_offline_evidence=offline_summary,
                claim_boundary='Causal v34 custom stream is actual CP34/HX33 host-model output; HEVC/AV1 points are prospective same-HX33 budgets. Hierarchy/selective component evidence uses fixed prior references and is not a causal or additive gain. Opaque safe masking metrics are measured against original RGB; native points use same-processed masked input and identical HX33+60B accounting. Offline inverse projections assume an unclosed 100MHz clock. No native service, hardware fit, or physical 30fps claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='require byte-identical audit.json without writing')
    options = parser.parse_args()
    report = audit()
    encoded = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
    output = HERE / 'audit.json'
    if options.check:
        if not output.is_file() or output.read_bytes() != encoded:
            raise SystemExit('audit.json missing or stale; regenerate without --check')
    else:
        output.write_bytes(encoded)
    print(json.dumps(dict(cohort_rows=report['cohort_rows'], accepted_control_parity_rows=report['accepted_control_parity_rows'],
                          cohort_count=len(report['cohorts']), flat_source_pins=len(report['source_sha256']),
                          fixed_reference_components=sorted(report['fixed_reference_components']))))
