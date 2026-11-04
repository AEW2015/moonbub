"""Isolated GM26 adapter: identical serialization and exact batched RDO counter.

Copied encode functions from this study's frozen model; _rdo_skip binds only in
this adapter. No dependency globals are modified.
"""
from pathlib import Path
import importlib.util,sys,struct,time,zlib
import numpy as np
HERE=Path(__file__).resolve().parent

def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
base=_load('fractional26_frozen_predictor',HERE/'model.py')
counter=_load('fractional26_exact_counter',HERE.parent/'python-game-rdo-counter-v26-study/model.py')
C,gm,ft,roi,sr=base.C,base.gm,base.ft,base.roi,base.sr
Prepared,_PREPARED_OWNER=base.Prepared,base._PREPARED_OWNER
MAGIC,HEADER,NO_REF,ZERO_TAG,MAX_PACKET,LIMIT=base.MAGIC,base.HEADER,base.NO_REF,base.ZERO_TAG,base.MAX_PACKET,base.LIMIT
_quantize,_encode_plane=base._quantize,base._encode_plane
_rdo_skip=counter.rdo_skip
analyze_planes,parse,decode=base.analyze_planes,base.parse,base.decode
predict,estimate_vectors=base.predict,base.estimate_vectors
pack_vectors,unpack_vectors=base.pack_vectors,base.unpack_vectors
_id=base._id

def encode_prepared(prepared, scale_map, rdo_lambda=0):
    """Pay a new quantization/entropy/reconstruction for one declared map.

    Search/forward work is in prepared.work and must be paid once by the caller,
    not added once per candidate or silently excluded from whole-source service.
    """
    start = time.perf_counter_ns()
    p = prepared
    if not isinstance(p, Prepared) or p.owner is not _PREPARED_OWNER:
        raise ValueError('GM26 prepared analysis owner')
    if (type(rdo_lambda) not in (int, float) or not np.isfinite(rdo_lambda)
            or not 0 <= rdo_lambda <= 1_000_000):
        raise ValueError('bounded nonnegative RDO lambda')
    w, h = p.width, p.height
    mapped = roi.check_map(scale_map, w, h)
    began = time.perf_counter_ns()
    coefficients = _quantize(p.raw_coefficients, mapped, w, h)
    quantize_ms = (time.perf_counter_ns() - began) / 1e6
    began = time.perf_counter_ns()
    original_coefficients = coefficients
    coefficients, rdo = _rdo_skip(p, coefficients, mapped, rdo_lambda)
    rdo_ms = (time.perf_counter_ns() - began) / 1e6
    began = time.perf_counter_ns()
    payloads, details = [], []
    for plane, coeff in enumerate(coefficients):
        pw = w if plane == 0 else w // 2
        payload, info = _encode_plane(coeff, (pw + 7) // 8)
        if not np.array_equal(coeff, original_coefficients[plane]):
            original_payload, original_info = _encode_plane(original_coefficients[plane], (pw + 7) // 8)
            info['rdo_original_payload_bytes'] = len(original_payload)
            info['rdo_pruned_payload_bytes'] = len(payload)
            info['rdo_actual_plane_candidates'] = 2
            if len(original_payload) < len(payload):
                coeff = original_coefficients[plane]
                payload = original_payload
                info.update(original_info)
                info['rdo_reverted'] = True
                coefficients = tuple(coeff if j == plane else c for j, c in enumerate(coefficients))
        payloads.append(payload); details.append(info)
    entropy_ms = (time.perf_counter_ns() - began) / 1e6
    rebuilt = gm.reconstruct(coefficients, p.prediction, mapped, w, h)
    rdo['proposed_zeroed_blocks'] = rdo['zeroed_blocks']
    rdo['proposed_source_sse_increase'] = rdo['source_sse_increase']
    del rdo['source_sse_increase']
    rdo['zeroed_blocks'] = sum(int(np.count_nonzero(np.any(a != 0, axis=(1, 2))
                                                  & ~np.any(b != 0, axis=(1, 2))))
                             for a, b in zip(original_coefficients, coefficients))
    outtag = C.reference_tag(rebuilt)
    qmap = roi.pack_map(mapped)
    header = HEADER.pack(MAGIC, 2, int(p.key), p.epoch, p.frame_id, p.reference_id, w, h,
                         p.block_size, LIMIT, p.reference_tag, outtag, len(qmap), len(p.vector_bytes), *(len(v) for v in payloads))
    body = header + qmap + p.vector_bytes + b''.join(payloads)
    packet = body + struct.pack('<I', zlib.crc32(body))
    work = dict(key=p.key, block_size=p.block_size, motion_mode=p.motion_mode, packet_bytes=len(packet),
                header_bytes=HEADER.size + 4, qmap_bytes=len(qmap), vector_bytes=len(p.vector_bytes),
                coefficient_bytes=sum(len(v) for v in payloads), search=p.work['search'], search_ms=0.,
                forward_plane_calls=0, transform_ms=0., quantize_ms=quantize_ms, entropy_ms=entropy_ms,
                rdo=rdo, rdo_ms=rdo_ms,
                planes=details, reconstructed_yuv_array_bytes=sum(p.nbytes for p in rebuilt),
                prediction_array_bytes=sum(v.nbytes for v in p.prediction),
                decoder_reference_sample_reads=0 if p.key else 4*sum(v.size for v in p.prediction),
                encode_prepared_wall_ms=(time.perf_counter_ns() - start) / 1e6,
                analysis_paid_separately=True,
                reference_tag=p.reference_tag.hex(), reconstructed_tag=outtag.hex())
    return packet, rebuilt, work


def encode_planes(source, reference, scale_map, *, epoch=1, frame_id=0, reference_id=NO_REF,
                  block_size=16, motion_mode='block', penalty=0, rdo_lambda=0, motion_precision='half'):
    started = time.perf_counter_ns()
    prepared = analyze_planes(source, reference, epoch=epoch, frame_id=frame_id, reference_id=reference_id,
                              block_size=block_size, motion_mode=motion_mode, penalty=penalty, motion_precision=motion_precision)
    packet, rebuilt, work = encode_prepared(prepared, scale_map, rdo_lambda=rdo_lambda)
    work.update(analysis=prepared.work, analysis_paid_separately=False, forward_plane_calls=3,
                search_ms=prepared.work['search_ms'], transform_ms=prepared.work['transform_ms'],
                encoder_wall_ms=(time.perf_counter_ns() - started) / 1e6)
    return packet, rebuilt, work


