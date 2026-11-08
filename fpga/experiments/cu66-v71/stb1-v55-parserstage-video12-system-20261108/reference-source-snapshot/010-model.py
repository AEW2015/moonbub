"""GM25 bounded integer block prediction with frozen Q14/ROI residuals.

Stateless Python frame component. References are exact reconstructed YUV, not
original captures. Selection, ACK ownership and presentation remain parent work.
"""
from pathlib import Path
from dataclasses import dataclass
import struct
import sys
import time
import zlib
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-candidate-commit-study'))
import candidate_codec as C

gm, ft, roi, sr = C.gm, C.gm.ft, C.gm.roi, C.sr
MAGIC = b'GM25'
HEADER = struct.Struct('<4sBBIIIHHBB16s16sIIIII')
NO_REF = 0xffffffff
ZERO_TAG = bytes(16)
MAX_PACKET = 2_000_000
LIMIT = 8
_PREPARED_OWNER = object()


def _id(value):
    return type(value) is int and 0 <= value < NO_REF


def _planes(planes, geometry=None):
    if not isinstance(planes, (tuple, list)) or len(planes) != 3:
        raise ValueError('three YUV420 planes required')
    a = tuple(np.asarray(p) for p in planes)
    h, w = a[0].shape if a[0].ndim == 2 else (0, 0)
    roi.geometry(w, h)
    if geometry is not None and (w, h) != geometry:
        raise ValueError('reference geometry')
    expected = ((h, w), (h // 2, w // 2), (h // 2, w // 2))
    if any(p.shape != s or p.dtype.kind not in 'ui' or np.any(p < 0) or np.any(p > 255)
           for p, s in zip(a, expected)):
        raise ValueError('bounded integer YUV420 samples')
    return tuple(p.astype(np.int16, copy=False) for p in a)


def _grid(w, h, block_size):
    if type(block_size) is not int or block_size not in (16, 32):
        raise ValueError('declared macroblock size16/32')
    return (w + block_size - 1) // block_size, (h + block_size - 1) // block_size


def predict(reference, vectors, block_size=16):
    """Reference[y+dy,x+dx], clamped; even luma vectors halve for chroma."""
    h, w = reference[0].shape
    mw, mh = _grid(w, h, block_size)
    a = np.asarray(vectors)
    if a.shape != (mh, mw, 2) or a.dtype.kind not in 'iu' or np.any(a % 2) or np.any(np.abs(a.astype(np.int32)) > LIMIT):
        raise ValueError('bounded even motion vectors')
    out = []
    for plane, ref in enumerate(reference):
        ph, pw = ref.shape
        bs = block_size if plane == 0 else block_size // 2
        yy, xx = np.mgrid[:ph, :pw]
        v = a[yy // bs, xx // bs].astype(np.int32)
        dx, dy = v[..., 0], v[..., 1]
        if plane:
            dx, dy = dx // 2, dy // 2
        out.append(ref[np.clip(yy + dy, 0, ph - 1), np.clip(xx + dx, 0, pw - 1)].astype(np.int16))
    return tuple(out)


def estimate_vectors(source, reference, block_size=16, mode='block', penalty=0):
    """Exhaustive bounded current-source SAD; all tested luma/chroma work paid.

    A small optional nonzero-vector penalty is host policy, never a decoder rule.
    Candidate ordering makes exact ties prefer zero and then short vectors.
    """
    if mode not in ('zero', 'global', 'block') or type(penalty) is not int or not 0 <= penalty <= 4096:
        raise ValueError('motion policy')
    h, w = source[0].shape
    mw, mh = _grid(w, h, block_size)
    if mode == 'zero':
        return np.zeros((mh, mw, 2), np.int8), dict(candidate_vectors=1, sad_sample_operations=0, nonzero_vectors=0)
    candidates = sorted(((dx, dy) for dy in range(-LIMIT, LIMIT + 1, 2)
                         for dx in range(-LIMIT, LIMIT + 1, 2)), key=lambda p: (abs(p[0]) + abs(p[1]), p[1], p[0]))
    best = np.full((mh, mw), 2**62, np.int64)
    chosen = np.zeros((mh, mw, 2), np.int8)
    global_best = None
    for dx, dy in candidates:
        costs = np.zeros((mh, mw), np.int64)
        for plane, (src, ref) in enumerate(zip(source, reference)):
            ph, pw = src.shape
            step = 1 if plane == 0 else 2
            bs = block_size // step
            y = np.clip(np.arange(ph) + dy // step, 0, ph - 1)
            x = np.clip(np.arange(pw) + dx // step, 0, pw - 1)
            error = np.abs(src.astype(np.int32) - ref[y[:, None], x].astype(np.int32))
            error = np.pad(error, ((0, mh * bs - ph), (0, mw * bs - pw)), constant_values=0)
            weight = 1 if plane == 0 else 2
            costs += weight * error.reshape(mh, bs, mw, bs).sum(axis=(1, 3), dtype=np.int64)
        if dx or dy:
            costs += penalty
        if mode == 'global':
            total = int(costs.sum())
            if global_best is None or total < global_best[0]:
                global_best = total, dx, dy
        else:
            improve = costs < best
            chosen[improve] = (dx, dy)
            best[improve] = costs[improve]
    if mode == 'global':
        chosen[:] = global_best[1:]
    return chosen, dict(candidate_vectors=len(candidates),
                         sad_sample_operations=len(candidates) * sum(p.size for p in source),
                         nonzero_vectors=int(np.count_nonzero(np.any(chosen != 0, axis=2))))


def pack_vectors(vectors):
    a = np.asarray(vectors)
    if (a.ndim < 2 or a.shape[-1] != 2 or a.size == 0 or a.dtype.kind not in 'iu'
            or np.any(a % 2) or np.any(np.abs(a.astype(np.int64)) > LIMIT)):
        raise ValueError('bounded even motion-map values')
    flat = a.astype(np.int8).reshape(-1, 2)
    if np.all(flat == flat[0]):
        return b'\x00' + flat[0].tobytes()
    dense = b'\x01' + flat.tobytes()
    run = bytearray(b'\x02')
    start = 0
    for end in range(1, len(flat) + 1):
        if end == len(flat) or not np.array_equal(flat[end], flat[start]):
            run.extend(struct.pack('<Hbb', end - start, int(flat[start, 0]), int(flat[start, 1])))
            start = end
    # Even -8..8 maps to two legal nibbles0..8, one byte/vector.
    packed = (((flat[:, 0].astype(np.int16) + 8) // 2) << 4) | ((flat[:, 1].astype(np.int16) + 8) // 2)
    nibble = b'\x03' + packed.astype(np.uint8).tobytes()
    values, counts = np.unique(packed, return_counts=True)
    default = int(values[np.argmax(counts)])
    indices = np.flatnonzero(packed != default)
    sparse = bytearray((4, default))
    for index in indices:
        sparse.extend(struct.pack('<HB', int(index), int(packed[index])))
    # Canonical minimum: old modes first on a byte-length tie.
    return min((dense, bytes(run), nibble, bytes(sparse)), key=len)


def unpack_vectors(data, mw, mh):
    n = mw * mh
    if type(data) is not bytes or not 1 <= len(data) <= 1 + 2 * n:
        raise ValueError('motion-map bounded length')
    mode = data[0]
    if mode == 0:
        if len(data) != 3:
            raise ValueError('global motion-map length')
        flat = np.tile(np.frombuffer(data[1:], np.int8), (n, 1))
    elif mode == 1:
        if len(data) != 1 + 2 * n:
            raise ValueError('dense motion-map length')
        flat = np.frombuffer(data[1:], np.int8).reshape(n, 2).copy()
    elif mode == 2:
        if (len(data) - 1) % 4:
            raise ValueError('RLE motion-map length')
        flat = np.empty((n, 2), np.int8)
        count = 0
        previous = None
        for offset in range(1, len(data), 4):
            run, dx, dy = struct.unpack_from('<Hbb', data, offset)
            if not run or count + run > n or previous == (dx, dy):
                raise ValueError('RLE motion-map coverage/canonicality')
            flat[count:count + run] = dx, dy
            count += run
            previous = dx, dy
        if count != n:
            raise ValueError('RLE incomplete motion map')
    elif mode in (3, 4):
        if mode == 3:
            if len(data) != n + 1:
                raise ValueError('nibble motion-map length')
            packed = np.frombuffer(data[1:], np.uint8)
        else:
            if len(data) < 2 or (len(data) - 2) % 3:
                raise ValueError('sparse motion-map length')
            packed = np.full(n, data[1], np.uint8)
            previous = -1
            for offset in range(2, len(data), 3):
                index, value = struct.unpack_from('<HB', data, offset)
                if index <= previous or index >= n or value == data[1]:
                    raise ValueError('sparse motion-map indices/default')
                packed[index] = value
                previous = index
        high, low = packed >> 4, packed & 15
        if np.any(high > 8) or np.any(low > 8):
            raise ValueError('nibble motion-vector code')
        flat = np.stack((high.astype(np.int16) * 2 - 8, low.astype(np.int16) * 2 - 8), axis=1).astype(np.int8)
    else:
        raise ValueError('motion-map mode')
    vectors = flat.reshape(mh, mw, 2)
    if np.any(flat.astype(np.int16) % 2) or np.any(np.abs(flat.astype(np.int16)) > LIMIT):
        raise ValueError('motion vector domain')
    if pack_vectors(vectors) != data:
        raise ValueError('nonminimal motion-map representation')
    return vectors


def _forward(source, prediction):
    out = []
    for plane, (src, pred) in enumerate(zip(source, prediction)):
        residual = src.astype(np.int64) - pred
        ph, pw = residual.shape
        residual = np.pad(residual, ((0, (-ph) % 8), (0, (-pw) % 8)), mode='edge')
        hh, ww = residual.shape
        blocks = residual.reshape(hh // 8, 8, ww // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        raw = ft.forward(blocks)
        raw.setflags(write=False)
        out.append(raw)
    return tuple(out)


def _quantize(raw_planes, mapped, w, h):
    out = []
    for plane, raw in enumerate(raw_planes):
        quantized = ft.round_quantize(raw, roi.block_tables(mapped, w, h, plane))
        if np.any(np.abs(quantized) > ft.MAX_COEFF):
            raise ValueError('coefficient wire domain')
        out.append(quantized.astype(np.int16))
    return tuple(out)


def _encode_plane(coeff, blocks_w):
    if not np.any(coeff):
        return b'\x02', dict(mode='zero', zero_blocks=len(coeff), dc_blocks=0, full_blocks=0)
    dense_payload = gm.token_coeff.encode_coefficients(coeff, blocks_w)
    dense = b'\x00' + dense_payload
    split, info = C._plane(coeff, blocks_w, dense=dense_payload)
    selected = b'\x01' + split if 1 + len(split) < len(dense) else dense
    modes, dc, full = sr.classifications(coeff)
    return selected, dict(mode='structured' if selected[0] else 'dense', zero_blocks=int((modes == 0).sum()),
                          dc_blocks=int(dc.sum()), full_blocks=int(full.sum()),
                          dense_bytes=len(dense), structured_bytes=len(split) + 1,
                          actual_entropy_candidates=2)


def _decode_plane(data, n, bw):
    if not data:
        raise ValueError('empty plane payload')
    if data[0] == 2:
        if len(data) != 1:
            raise ValueError('zero-plane exact length')
        return np.zeros((n, 8, 8), np.int16)
    if data[0] == 0:
        return gm.word_coeff.decode_coefficients(data[1:], n, bw)
    if data[0] == 1:
        return sr.decode_plane(data[1:], n, bw)
    raise ValueError('plane payload mode')


@dataclass(frozen=True, eq=False)
class Prepared:
    owner: object
    epoch: int
    frame_id: int
    reference_id: int
    width: int
    height: int
    key: bool
    block_size: int
    motion_mode: str
    reference_tag: bytes
    vector_bytes: bytes
    prediction: tuple
    raw_coefficients: tuple
    source: tuple
    work: dict


def analyze_planes(source, reference, *, epoch=1, frame_id=0, reference_id=NO_REF,
                   block_size=16, motion_mode='block', penalty=0):
    """One actual source/predictor/MV search and three forward transforms.

    This pure component has no bank/ACK owner. The parent must hold the exact
    immutable reference while any candidate/decode may read it. Returned arrays
    are read-only by trusted local API contract, not an adversarial boundary.
    """
    start = time.perf_counter_ns()
    src = _planes(source)
    h, w = src[0].shape
    mw, mh = _grid(w, h, block_size)
    if not _id(epoch) or not _id(frame_id):
        raise ValueError('bounded epoch/frame')
    if motion_mode not in ('zero', 'global', 'block') or type(penalty) is not int or not 0 <= penalty <= 4096:
        raise ValueError('motion policy')
    key = reference is None
    if key:
        if type(reference_id) is not int or reference_id != NO_REF:
            raise ValueError('key reference identity')
        prediction = tuple(np.full_like(p, 128) for p in src)
        vectors = np.zeros((mh, mw, 2), np.int8)
        vector_bytes = b''
        reftag = ZERO_TAG
        search = dict(candidate_vectors=0, sad_sample_operations=0, nonzero_vectors=0)
        search_ms = 0.
    else:
        if not _id(reference_id) or reference_id >= frame_id:
            raise ValueError('past reference identity')
        ref = _planes(reference, (w, h))
        reftag = C.reference_tag(ref)
        began = time.perf_counter_ns()
        vectors, search = estimate_vectors(src, ref, block_size, motion_mode, penalty)
        search_ms = (time.perf_counter_ns() - began) / 1e6
        prediction = predict(ref, vectors, block_size)
        vector_bytes = pack_vectors(vectors)
    began = time.perf_counter_ns()
    raw = _forward(src, prediction)
    transform_ms = (time.perf_counter_ns() - began) / 1e6
    for p in prediction:
        p.setflags(write=False)
    retained_source = tuple(v.copy() for v in src)
    for v in retained_source:
        v.setflags(write=False)
    work = dict(key=key, motion_mode=motion_mode, block_size=block_size, search=search,
                search_ms=search_ms, forward_plane_calls=3, transform_ms=transform_ms,
                prediction_array_bytes=sum(p.nbytes for p in prediction),
                raw_coefficient_array_bytes=sum(p.nbytes for p in raw),
                source_array_bytes=sum(p.nbytes for p in retained_source),
                retained_analysis_array_bytes=sum(p.nbytes for p in prediction + raw + retained_source),
                analysis_wall_ms=(time.perf_counter_ns() - start) / 1e6,
                reference_tag=reftag.hex())
    return Prepared(_PREPARED_OWNER, epoch, frame_id, reference_id, w, h, key, block_size,
                    motion_mode, reftag, vector_bytes, prediction, raw, retained_source, work)


def _block_sse(error):
    h, w = error.shape
    padded = np.pad(error.astype(np.int64) ** 2, ((0, (-h) % 8), (0, (-w) % 8)))
    hh, ww = padded.shape
    return padded.reshape(hh // 8, 8, ww // 8, 8).sum(axis=(1, 3)).reshape(-1)


def _rdo_skip(p, coefficients, mapped, rdo_lambda):
    """P-only actual source-SSE versus paid standalone-coefficient-bit proxy.

    CP02 block payload bytes are real constructions, but their marginal cost is
    a proxy: plane DC prediction and token packing context differ. The final
    full-plane original/pruned packets are also constructed and compared.
    """
    stats = dict(lambda_value=float(rdo_lambda), distortion='clipped-source-YUV-SSE',
                 bit_proxy='isolated-CP02-body-or-DC16', checked_blocks=0,
                 zeroed_blocks=0, protected_blocks=0, cp02_probe_calls=0,
                 cp02_probe_bytes=0, predicted_bit_saving=0, source_sse_increase=0,
                 baseline_inverse_plane_calls=0)
    if not rdo_lambda or p.key:
        return coefficients, stats
    baseline = gm.reconstruct(coefficients, p.prediction, mapped, p.width, p.height)
    stats['baseline_inverse_plane_calls'] = 3
    result = []
    for plane, coeff in enumerate(coefficients):
        protected = roi.block_scales(mapped, p.width, p.height, plane) == 8
        if plane:
            priority = mapped == 8
            halo = priority.copy()
            halo[:, 1:] |= priority[:, :-1]
            halo[1:, :] |= priority[:-1, :]
            halo[1:, 1:] |= priority[:-1, :-1]
            protected = halo.reshape(-1)
        stats['protected_blocks'] += int(protected.sum())
        nonzero = np.any(coeff != 0, axis=(1, 2))
        eligible = np.flatnonzero(nonzero & ~protected)
        delta = (_block_sse(p.source[plane] - p.prediction[plane])
                 - _block_sse(p.source[plane] - baseline[plane]))
        selected = coeff.copy()
        _, dc, _ = sr.classifications(coeff)
        for index in eligible:
            stats['checked_blocks'] += 1
            if dc[index]:
                bits = 16
            else:
                probe = gm.token_coeff.encode_coefficients(coeff[index:index + 1], 1)
                stats['cp02_probe_calls'] += 1
                stats['cp02_probe_bytes'] += len(probe)
                bits = max(1, 8 * (len(probe) - gm.word_coeff.PAYLOAD_OVERHEAD))
            if int(delta[index]) <= rdo_lambda * bits:
                selected[index] = 0
                stats['zeroed_blocks'] += 1
                stats['predicted_bit_saving'] += bits
                stats['source_sse_increase'] += int(delta[index])
        result.append(selected)
    return tuple(result), stats


def encode_prepared(prepared, scale_map, rdo_lambda=0):
    """Pay a new quantization/entropy/reconstruction for one declared map.

    Search/forward work is in prepared.work and must be paid once by the caller,
    not added once per candidate or silently excluded from whole-source service.
    """
    start = time.perf_counter_ns()
    p = prepared
    if not isinstance(p, Prepared) or p.owner is not _PREPARED_OWNER:
        raise ValueError('GM25 prepared analysis owner')
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
    header = HEADER.pack(MAGIC, 1, int(p.key), p.epoch, p.frame_id, p.reference_id, w, h,
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
                decoder_reference_sample_reads=0 if p.key else sum(v.size for v in p.prediction),
                encode_prepared_wall_ms=(time.perf_counter_ns() - start) / 1e6,
                analysis_paid_separately=True,
                reference_tag=p.reference_tag.hex(), reconstructed_tag=outtag.hex())
    return packet, rebuilt, work


def encode_planes(source, reference, scale_map, *, epoch=1, frame_id=0, reference_id=NO_REF,
                  block_size=16, motion_mode='block', penalty=0, rdo_lambda=0):
    started = time.perf_counter_ns()
    prepared = analyze_planes(source, reference, epoch=epoch, frame_id=frame_id, reference_id=reference_id,
                              block_size=block_size, motion_mode=motion_mode, penalty=penalty)
    packet, rebuilt, work = encode_prepared(prepared, scale_map, rdo_lambda=rdo_lambda)
    work.update(analysis=prepared.work, analysis_paid_separately=False, forward_plane_calls=3,
                search_ms=prepared.work['search_ms'], transform_ms=prepared.work['transform_ms'],
                encoder_wall_ms=(time.perf_counter_ns() - started) / 1e6)
    return packet, rebuilt, work


def parse(packet, *, expected_epoch=None):
    if type(packet) is not bytes or not HEADER.size + 7 <= len(packet) <= MAX_PACKET:
        raise ValueError('GM25 bounded frame length')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('GM25 CRC')
    (magic, version, flags, epoch, frame, refid, w, h, bs, limit, reftag, outtag,
     nq, nv, ny, ncb, ncr) = HEADER.unpack_from(packet)
    roi.geometry(w, h)
    mw, mh = _grid(w, h, bs)
    key = bool(flags)
    if (magic, version) != (MAGIC, 1) or flags not in (0, 1) or limit != LIMIT or not _id(epoch) or not _id(frame):
        raise ValueError('GM25 profile/identity')
    if expected_epoch is not None and epoch != expected_epoch:
        raise ValueError('GM25 wrong epoch')
    if key:
        if refid != NO_REF or reftag != ZERO_TAG or nv:
            raise ValueError('GM25 independent key reference')
    elif not _id(refid) or refid >= frame or reftag == ZERO_TAG or not 1 <= nv <= 1 + 2 * mw * mh:
        raise ValueError('GM25 P reference/map')
    if outtag == ZERO_TAG or nq != (((w + 15) // 16) * ((h + 15) // 16) + 3) // 4:
        raise ValueError('GM25 output tag/quant-map length')
    lengths = (ny, ncb, ncr)
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w // 2, h // 2)
        n = ((pw + 7) // 8) * ((ph + 7) // 8)
        if not 1 <= size <= 132 * n + 256:
            raise ValueError('GM25 plane bound')
    if len(packet) != HEADER.size + nq + nv + sum(lengths) + 4:
        raise ValueError('GM25 exact frame length')
    pos = HEADER.size
    mapped = roi.unpack_map(packet[pos:pos + nq], (w + 15) // 16, (h + 15) // 16); pos += nq
    vectors = np.zeros((mh, mw, 2), np.int8) if key else unpack_vectors(packet[pos:pos + nv], mw, mh)
    pos += nv
    coefficients = []
    for plane, size in enumerate(lengths):
        pw, ph = (w, h) if plane == 0 else (w // 2, h // 2)
        n, bw = ((pw + 7) // 8) * ((ph + 7) // 8), (pw + 7) // 8
        coefficients.append(_decode_plane(packet[pos:pos + size], n, bw)); pos += size
    return dict(epoch=epoch, frame_id=frame, reference_id=refid, key=key, width=w, height=h,
                block_size=bs, vectors=vectors, scale_map=mapped, coefficients=tuple(coefficients),
                reference_tag=reftag, reconstructed_tag=outtag)


def decode(packet, reference=None, *, expected_epoch=None, expected_reference_id=None):
    meta = parse(packet, expected_epoch=expected_epoch)
    w, h = meta['width'], meta['height']
    if meta['key']:
        prediction = tuple(np.full(shape, 128, np.int16) for shape in ((h, w), (h // 2, w // 2), (h // 2, w // 2)))
    else:
        if expected_reference_id is None or expected_reference_id != meta['reference_id']:
            raise ValueError('GM25 exact reference ID required')
        ref = _planes(reference, (w, h))
        if C.reference_tag(ref) != meta['reference_tag']:
            raise ValueError('GM25 exact reconstructed reference tag')
        prediction = predict(ref, meta['vectors'], meta['block_size'])
    rebuilt = gm.reconstruct(meta['coefficients'], prediction, meta['scale_map'], w, h)
    if C.reference_tag(rebuilt) != meta['reconstructed_tag']:
        raise ValueError('GM25 reconstructed output tag')
    return rebuilt, meta
