"""Exact runtime28 + strict band30 pair with one paid preparation/entropy path.

No persistent cache or global monkeypatch: the short-lived per-call plans and
coefficient arrays are private. Caller retains the ordinary Prepared ownership.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('shared33_band30', HERE.parent/'python-game-band-v30-study/model.py')
band = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = band
_spec.loader.exec_module(band)
entropy = band.e


def _packet(module, p, qmap, payloads, rebuilt):
    tag = module.C.reference_tag(rebuilt)
    body = module.HEADER.pack(module.MAGIC, module.VERSION, int(p.key), p.epoch,
        p.frame_id, p.reference_id, p.width, p.height, p.block_size, module.base.LIMIT,
        p.reference_tag, tag, len(qmap), len(p.vector_bytes), *(len(v) for v in payloads))
    body += qmap + p.vector_bytes + b''.join(payloads)
    return body + struct.pack('<I', zlib.crc32(body)), tag


def encode_pair(module, prepared, scale_map, rdo_lambda=1):
    """Return (runtime28 triple, strict-band30 triple), including all pair work."""
    start = time.perf_counter_ns()
    p = prepared
    if not isinstance(p, module.Prepared) or p.owner is not module._PREPARED_OWNER:
        raise ValueError('owned GM27 preparation')
    if type(rdo_lambda) not in (int, float) or not np.isfinite(rdo_lambda) or not 0 <= rdo_lambda <= 1000000:
        raise ValueError('RDO lambda')
    q = module.roi.check_map(scale_map, p.width, p.height)
    original = module.base._quantize(p.raw_coefficients, q, p.width, p.height)
    pruned, rdo = module.counter.rdo_skip(p, original, q, rdo_lambda)
    incumbent, trials, plans, reverted = [], [], [], []
    for plane, coeff in enumerate(pruned):
        bw = ((p.width if plane == 0 else p.width//2)+7)//8
        legacy = module.legacy_plan(coeff, bw)
        history = [legacy]
        revert = False
        if not np.array_equal(coeff, original[plane]):
            op = module.legacy_plan(original[plane], bw)
            history.append(op)
            if op['bytes'] < legacy['bytes']:
                coeff, legacy, revert = original[plane], op, True
        ec = entropy.plan_coefficients(coeff, bw)
        count = ec['bytes'] + 1
        # Incumbent wins representation ties, just as both frozen encoders do.
        plan = dict(bytes=min(legacy['bytes'], count),
                    mode='EC26' if count < legacy['bytes'] else legacy['kind'], legacy=legacy, ec26=ec)
        incumbent.append(coeff); trials.append(history); plans.append(plan); reverted.append(revert)
    baseline = module.gm.reconstruct(tuple(incumbent), p.prediction, q, p.width, p.height)
    payloads, inc_details, constructions = [], [], [0, 0, 0]
    for plane, (coeff, plan) in enumerate(zip(incumbent, plans)):
        bw = ((p.width if plane == 0 else p.width//2)+7)//8
        data, ec, cp, sp = entropy._construct(coeff, bw, plan, module)
        assert len(data) == plan['bytes']
        payloads.append(data)
        constructions = [a+b for a, b in zip(constructions, (ec, cp, sp))]
        inc_details.append(dict(selected_mode=plan['mode'], selected_bytes=len(data),
            legacy_selected_bytes=plan['legacy']['bytes'], legacy_trials=trials[plane],
            rdo_reverted=reverted[plane]))
    output, band_payloads, band_details = [], [], []
    selected_inverse = alternative_plans = reused_payloads = 0
    for plane, coeff in enumerate(incumbent):
        bw = ((p.width if plane == 0 else p.width//2)+7)//8
        menu, stats = band.candidates(module, p, q, coeff, plane, baseline[plane], 'band_strict')
        options = [plans[plane]] + [entropy._plane_plan(c, bw, module) for _, c in menu[1:]]
        alternative_plans += len(menu)-1
        selected = min(range(len(menu)), key=lambda i: options[i]['bytes'])
        label, chosen = menu[selected]
        plan = options[selected]
        if selected == 0:
            data, rebuilt = payloads[plane], baseline[plane]
            reused_payloads += 1
        else:
            data, ec, cp, sp = entropy._construct(chosen, bw, plan, module)
            constructions = [a+b for a, b in zip(constructions, (ec, cp, sp))]
            rebuilt = band.reconstruct_plane(module, chosen, p.prediction[plane], q, p.width, p.height, plane)
            rebuilt.setflags(write=False)
            selected_inverse += 1
        assert len(data) == plan['bytes'] <= options[0]['bytes']
        assert np.array_equal(chosen[:, 0, 0], coeff[:, 0, 0])
        protected = band.protected_blocks(module, q, p.width, p.height, plane)
        assert np.array_equal(chosen[protected], coeff[protected])
        source_sse = int(np.square(p.source[plane].astype(np.int64)-rebuilt).sum())
        assert source_sse <= stats['baseline_source_yuv_sse']
        stats.update(selected_label=label, selected_bytes=len(data), baseline_bytes=options[0]['bytes'],
            selected_source_yuv_sse=source_sse, changed_blocks=int(np.count_nonzero(np.any(chosen != coeff, axis=(1,2)))),
            removed_coefficients=int(np.count_nonzero(coeff)-np.count_nonzero(chosen)),
            candidate_plans=[dict(label=v[0], bytes=pl['bytes'], plan=pl) for v, pl in zip(menu, options)],
            incumbent_legacy_trials=trials[plane])
        output.append(rebuilt); band_payloads.append(data); band_details.append(stats)
    qmap = module.roi.pack_map(q)
    inc_packet, inc_tag = _packet(module, p, qmap, payloads, baseline)
    band_packet, band_tag = _packet(module, p, qmap, band_payloads, tuple(output))
    shared = dict(quantize_calls=1, rdo_calls=1, incumbent_legacy_plan_calls=sum(map(len, trials)),
        legacy_size_counter_calls=sum(p['size_counter_calls'] for trial in trials for p in trial)
            +sum(option['plan']['legacy']['size_counter_calls'] for detail in band_details for option in detail['candidate_plans'][1:]),
        alternative_legacy_plan_calls=alternative_plans, ec26_plan_calls=3+alternative_plans,
        incumbent_plane_packet_constructions=3, additional_plane_packet_constructions=3-reused_payloads,
        reused_incumbent_plane_payloads=reused_payloads,
        inverse_plane_calls=9+selected_inverse+int(rdo.get('baseline_inverse_plane_calls',0)),
        ec26_construct_calls=constructions[0], actual_cp02_encode_calls=constructions[1],
        actual_sp01_construct_calls=constructions[2], packet_constructions=2,
        persistent_cache_bytes=0,
        live_coefficient_array_bytes=sum(a.nbytes for a in original)+sum(a.nbytes for a in pruned),
        pair_wall_ms=(time.perf_counter_ns()-start)/1e6)
    tap = module.decoder_tap_counts(p)
    common = dict(analysis_paid_separately=True, search=p.work['search'], shared_pair=shared,
        decoder_reference_sample_reads=tap['reference_sample_fetches'], tap_work=tap,
        reference_tag=p.reference_tag.hex())
    inc_rdo = dict(rdo)
    inc_rdo['proposed_zeroed_blocks'] = inc_rdo['zeroed_blocks']
    inc_rdo['proposed_source_sse_increase'] = inc_rdo.pop('source_sse_increase')
    inc_rdo['zeroed_blocks'] = sum(int(np.count_nonzero(np.any(a != 0, axis=(1,2)) & ~np.any(b != 0, axis=(1,2))))
                                 for a, b in zip(original, incumbent))
    inc_work = dict(common, packet_bytes=len(inc_packet), planes=inc_details, rdo=inc_rdo,
                    reconstructed_tag=inc_tag.hex())
    band_work = dict(common, packet_bytes=len(band_packet), policy='band_strict', planes=band_details, rdo=rdo,
        reconstructed_tag=band_tag.hex(), selected_alternative_planes=sum(x['selected_label'] != 'incumbent' for x in band_details),
        changed_blocks=sum(x['changed_blocks'] for x in band_details),
        protected_blocks=sum(x['protected_blocks'] for x in band_details),
        removed_coefficients=sum(x['removed_coefficients'] for x in band_details))
    return (inc_packet, baseline, inc_work), (band_packet, tuple(output), band_work)
