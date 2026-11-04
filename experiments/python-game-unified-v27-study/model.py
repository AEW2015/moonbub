"""GM27 unified fractional motion, frozen RDO and block-major EC26 residuals.

The direct encoder pays all original/pruned legacy entropy alternatives before
trying EC26 on the frozen chosen coefficients. No GM26 serialization/reparse or
global mutation is used. Frozen imported modules retain their own ownership.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

old = _load('gm27_frozen_prediction26', HERE.parent / 'python-game-prediction-v26-study/model.py')
counter = _load('gm27_exact_rdo26', HERE.parent / 'python-game-rdo-counter-v26-study/model.py')
ec = _load('gm27_frozen_entropy26', HERE.parent / 'python-game-entropy-v26-study/model.py')
motion_decoder = _load('gm27_syntax_motion', HERE.parent / 'python-game-decoder-v27-study/model.py')
C, gm, roi, ft, sr = old.C, old.gm, old.roi, old.ft, old.sr
NO_REF, ZERO_TAG, MAX_PACKET, LIMIT, PRECISION = old.NO_REF, old.ZERO_TAG, old.MAX_PACKET, old.LIMIT, 2
MAGIC, VERSION, HEADER = b'GM27', 1, old.HEADER
Prepared, _PREPARED_OWNER = old.Prepared, old._PREPARED_OWNER
_id, _planes, _grid = old._id, old._planes, old._grid
predict, estimate_vectors = old.predict, old.estimate_vectors
pack_vectors, unpack_vectors_strict = old.pack_vectors, old.unpack_vectors
# GM27 owns a syntax-only receive grammar; the frozen GM26 canonicality oracle
# remains explicitly available for same-packet qualification.
unpack_vectors = motion_decoder.unpack_vectors
analyze_planes, _quantize = old.analyze_planes, old._quantize
_rdo_skip = counter.rdo_skip


def _legacy_plane(coeff, blocks_w):
    """Execute frozen legacy encoder and account every constructed alternative.

    Nonzero: direct CP02, SP01 dense wrapper, SP01 split wrapper; the latter
    also constructs a CP02 full-block subset when present. Zero uses shortcut.
    """
    payload, info = old._encode_plane(coeff, blocks_w)
    nonzero = bool(np.any(coeff))
    full = int(info.get('full_blocks', 0))
    trial = dict(selected_bytes=len(payload), selected_mode=info['mode'],
                 dense_bytes=info.get('dense_bytes'), structured_bytes=info.get('structured_bytes'),
                 representations=3 if nonzero else 1,
                 cp02_encode_calls=(1 + bool(full)) if nonzero else 0,
                 sp01_construct_calls=2 if nonzero else 0)
    return payload, info, [trial]


def _decode_plane(data, n, bw):
    if not data:
        raise ValueError('GM27 empty plane')
    if data[0] == 3:
        # GM27 admits only EC26 block-major or raw fallback, never layout1.
        if len(data) < 1 + ec.COEFF.size + 4 or ec.COEFF.unpack_from(data, 1)[2] not in (0, 1):
            raise ValueError('GM27 EC26 block-major profile')
        return ec.decode_coefficients(data[1:], n, bw)
    return old._decode_plane(data, n, bw)


def encode_prepared(prepared, scale_map, rdo_lambda=1):
    """Pay a new quantization/entropy/reconstruction for one declared map.

    Search/forward work is in prepared.work and must be paid once by the caller,
    not added once per candidate or silently excluded from whole-source service.
    """
    start = time.perf_counter_ns()
    p = prepared
    if not isinstance(p, Prepared) or p.owner is not _PREPARED_OWNER:
        raise ValueError('GM27 prepared analysis owner')
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
    # Phase one: freeze the exact legacy original/pruned plane decision.
    # EC26 never affects RDO coefficient selection in this experiment.
    legacy_payloads, details, selected_coefficients = [], [], []
    for plane, coeff in enumerate(coefficients):
        pw = w if plane == 0 else w // 2
        bw = (pw + 7) // 8
        payload, info, trials = _legacy_plane(coeff, bw)
        rdo_fields = dict(rdo_actual_plane_candidates=1)
        if not np.array_equal(coeff, original_coefficients[plane]):
            original_payload, original_info, original_trials = _legacy_plane(original_coefficients[plane], bw)
            trials += original_trials
            rdo_fields.update(rdo_original_payload_bytes=len(original_payload),
                              rdo_pruned_payload_bytes=len(payload), rdo_actual_plane_candidates=2)
            if len(original_payload) < len(payload):
                coeff, payload, info = original_coefficients[plane], original_payload, original_info
                rdo_fields['rdo_reverted'] = True
        info.update(rdo_fields)
        info['legacy_trials'] = trials
        info['legacy_plane_encode_calls'] = len(trials)
        info['legacy_actual_entropy_candidates'] = sum(t['representations'] for t in trials)
        info['legacy_cp02_encode_calls'] = sum(t['cp02_encode_calls'] for t in trials)
        info['legacy_sp01_construct_calls'] = sum(t['sp01_construct_calls'] for t in trials)
        legacy_payloads.append(payload)
        details.append(info)
        selected_coefficients.append(coeff)
    coefficients = tuple(selected_coefficients)
    # Phase two: construct exactly one new block-major EC26 candidate for each
    # already-selected coefficient plane and compare complete payload bytes.
    payloads = []
    for plane, (coeff, legacy, info) in enumerate(zip(coefficients, legacy_payloads, details)):
        pw = w if plane == 0 else w // 2
        began_ec = time.perf_counter_ns()
        candidate = b'\x03' + ec.encode_coefficients(coeff, (pw + 7) // 8, layout=0)
        info['ec26_encode_ms'] = (time.perf_counter_ns() - began_ec) / 1e6
        selected = candidate if len(candidate) < len(legacy) else legacy
        info.update(legacy_selected_mode=info['mode'], legacy_selected_bytes=len(legacy),
                    old_bytes=len(legacy), ec26_bytes=[len(candidate)], ec26_layout=0,
                    ec26_construct_calls=1, selected_bytes=len(selected),
                    selected_mode='EC26' if selected is candidate else 'frozen',
                    selected_layout=0 if selected is candidate else None,
                    blocks=len(coeff), nonzero_coefficients=int(np.count_nonzero(coeff)),
                    actual_entropy_candidates=info['legacy_actual_entropy_candidates'] + 1)
        if selected is candidate:
            info['mode'] = 'EC26'
        payloads.append(selected)
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
    header = HEADER.pack(MAGIC, 1, int(p.key), p.epoch, p.frame_id, p.reference_id, w, h,
                         p.block_size, LIMIT, p.reference_tag, outtag, len(qmap), len(p.vector_bytes), *(len(v) for v in payloads))
    body = header + qmap + p.vector_bytes + b''.join(payloads)
    packet = body + struct.pack('<I', zlib.crc32(body))
    work = dict(key=p.key, block_size=p.block_size, motion_mode=p.motion_mode, packet_bytes=len(packet),
                header_bytes=HEADER.size + 4, qmap_bytes=len(qmap), vector_bytes=len(p.vector_bytes),
                coefficient_bytes=sum(len(v) for v in payloads), legacy_coefficient_bytes=sum(map(len, legacy_payloads)),
                actual_entropy_candidates=sum(d['actual_entropy_candidates'] for d in details),
                legacy_cp02_encode_calls=sum(d['legacy_cp02_encode_calls'] for d in details),
                legacy_sp01_construct_calls=sum(d['legacy_sp01_construct_calls'] for d in details),
                ec26_construct_calls=3, ec26_encode_ms=sum(d['ec26_encode_ms'] for d in details),
                search=p.work['search'], search_ms=0.,
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
                  block_size=16, motion_mode='block', penalty=0, rdo_lambda=1, motion_precision='half'):
    started = time.perf_counter_ns()
    prepared = analyze_planes(source, reference, epoch=epoch, frame_id=frame_id, reference_id=reference_id,
                              block_size=block_size, motion_mode=motion_mode, penalty=penalty, motion_precision=motion_precision)
    packet, rebuilt, work = encode_prepared(prepared, scale_map, rdo_lambda=rdo_lambda)
    work.update(analysis=prepared.work, analysis_paid_separately=False, forward_plane_calls=3,
                search_ms=prepared.work['search_ms'], transform_ms=prepared.work['transform_ms'],
                encoder_wall_ms=(time.perf_counter_ns() - started) / 1e6)
    return packet, rebuilt, work


def parse_metadata(packet, *, expected_epoch=None):
    """Validate the immutable envelope without MV/quant-map/entropy decoding.

    Suitable for pair SHA/identity binding and ACK inspection, never sufficient
    for reconstructed bank publication. decode() performs all semantic checks.
    """
    if type(packet) is not bytes or not HEADER.size + 7 <= len(packet) <= MAX_PACKET:
        raise ValueError('GM27 bounded frame length')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('GM27 CRC')
    (magic, version, flags, epoch, frame, refid, w, h, bs, limit, reftag, outtag,
     nq, nv, ny, ncb, ncr) = HEADER.unpack_from(packet)
    roi.geometry(w, h)
    mw, mh = _grid(w, h, bs)
    key = bool(flags)
    if (magic, version) != (MAGIC, 1) or flags not in (0, 1) or limit != LIMIT or not _id(epoch) or not _id(frame):
        raise ValueError('GM27 profile/identity')
    if expected_epoch is not None and epoch != expected_epoch:
        raise ValueError('GM27 wrong epoch')
    if key:
        if refid != NO_REF or reftag != ZERO_TAG or nv:
            raise ValueError('GM27 independent key reference')
    elif not _id(refid) or refid >= frame or reftag == ZERO_TAG or not 1 <= nv <= 1 + 2 * mw * mh:
        raise ValueError('GM27 P reference/map')
    if outtag == ZERO_TAG or nq != (((w + 15) // 16) * ((h + 15) // 16) + 3) // 4:
        raise ValueError('GM27 output tag/quant-map length')
    lengths = (ny, ncb, ncr)
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w // 2, h // 2)
        n = ((pw + 7) // 8) * ((ph + 7) // 8)
        if not 1 <= size <= 132 * n + 256:
            raise ValueError('GM27 plane bound')
    if len(packet) != HEADER.size + nq + nv + sum(lengths) + 4:
        raise ValueError('GM27 exact frame length')
    return dict(epoch=epoch, frame_id=frame, reference_id=refid, key=key, width=w, height=h,
                block_size=bs, reference_tag=reftag, reconstructed_tag=outtag,
                qmap_bytes=nq, vector_bytes=nv, plane_lengths=lengths)


def parse(packet, *, expected_epoch=None):
    meta = parse_metadata(packet, expected_epoch=expected_epoch)
    w, h, bs = meta['width'], meta['height'], meta['block_size']
    key, nq, nv = meta['key'], meta['qmap_bytes'], meta['vector_bytes']
    lengths = meta['plane_lengths']
    mw, mh = _grid(w, h, bs)
    pos = HEADER.size
    mapped = roi.unpack_map(packet[pos:pos + nq], (w + 15) // 16, (h + 15) // 16); pos += nq
    vectors = np.zeros((mh, mw, 2), np.int8) if key else unpack_vectors(packet[pos:pos + nv], mw, mh)
    pos += nv
    coefficients = []
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w // 2, h // 2)
        n, bw = ((pw + 7) // 8) * ((ph + 7) // 8), (pw + 7) // 8
        coefficients.append(_decode_plane(packet[pos:pos + size], n, bw)); pos += size
    meta.update(vectors=vectors, scale_map=mapped, coefficients=tuple(coefficients))
    return meta


def decode(packet, reference=None, *, expected_epoch=None, expected_reference_id=None):
    meta = parse(packet, expected_epoch=expected_epoch)
    w, h = meta['width'], meta['height']
    if meta['key']:
        prediction = tuple(np.full(shape, 128, np.int16) for shape in ((h, w), (h // 2, w // 2), (h // 2, w // 2)))
    else:
        if expected_reference_id is None or expected_reference_id != meta['reference_id']:
            raise ValueError('GM27 exact reference ID required')
        ref = _planes(reference, (w, h))
        if C.reference_tag(ref) != meta['reference_tag']:
            raise ValueError('GM27 exact reconstructed reference tag')
        prediction = predict(ref, meta['vectors'], meta['block_size'])
    rebuilt = gm.reconstruct(meta['coefficients'], prediction, meta['scale_map'], w, h)
    if C.reference_tag(rebuilt) != meta['reconstructed_tag']:
        raise ValueError('GM27 reconstructed output tag')
    return rebuilt, meta
