"""Exact CP02 byte counts and v25-equivalent isolated-block RDO, host Python.

The oracle is python-token-entropy-study/token_coeff.py, not another CP02
implementation. No bitstrings, byte payloads, CRCs, or packets are built here.
"""
from pathlib import Path
import importlib.util
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('rdo_counter_v26_frozen_base', HERE.parent / 'python-game-base-motion-v25-study/model.py')
base = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = base
_spec.loader.exec_module(base)
oracle = base.gm.token_coeff
OVERHEAD = base.gm.word_coeff.PAYLOAD_OVERHEAD
MAX_BLOCKS = 65536
ZIGZAG = base.ft.ZIGZAG


def _check(coefficients, blocks_w=1):
    # Check shape/type/count before range checks or any widened working arrays.
    a = np.asarray(coefficients)
    if (a.dtype != np.int16 or a.ndim != 3 or a.shape[1:] != (8, 8)
            or not 1 <= len(a) <= MAX_BLOCKS):
        raise ValueError('bounded int16 coefficient blocks required')
    if type(blocks_w) is not int or not 1 <= blocks_w <= 256 or len(a) % blocks_w:
        raise ValueError('integral coefficient rows required')
    if a.min() < -2048 or a.max() > 2048:
        raise ValueError('coefficient wire domain')
    return a


def _mapped(a):
    a = a.astype(np.int32)
    return np.where(a >= 0, a * 2, -a * 2 - 1)


def _rice_lengths(values, k, escape):
    q = values >> k
    return np.where(q < 15, q + 1 + k, 15 + escape)


# Small fixed tables, independent of caller input; uint8 holds max 29 bits.
_AC_LENGTHS = np.stack([_rice_lengths(np.arange(4096), k, 12) for k in range(12)]).astype(np.uint8)
_DC_MIN_LENGTH = np.min(np.stack([_rice_lengths(np.arange(8193), k, 14) for k in range(14)]), axis=0)


def isolated_packet_bytes(coefficients):
    """Return N exact sizes, each encoded as its own one-block CP02 packet.

    Input is the frozen encoder's bounded int16[N,8,8] domain. Work is chunked
    to 1024 independent blocks, so the band/k temporary stays below 1 MiB.
    """
    a = _check(coefficients)
    out = np.empty(len(a), np.int64)
    positions = np.arange(1, 64)
    for start in range(0, len(a), 1024):
        zig = a[start:start + 1024].reshape(-1, 64)[:, ZIGZAG]
        ac = zig[:, 1:]
        nz = ac != 0
        last = np.maximum.accumulate(np.where(nz, positions, 0), axis=1)
        prev = np.empty_like(last)
        prev[:, 0] = 0
        prev[:, 1:] = last[:, :-1]
        run = positions - prev - 1
        syntax = (5 * nz.sum(axis=1) + 2 * np.where(nz, run // 16, 0).sum(axis=1)
                  + 2 * (last[:, -1] != 63))
        mapped = _mapped(ac) - 1
        mapped[~nz] = 0
        bits = syntax
        for lo, hi in ((0, 5), (5, 20), (20, 63)):
            costs = (_AC_LENGTHS[:, mapped[:, lo:hi]] * nz[:, lo:hi]).sum(axis=2)
            bits = bits + costs.min(axis=0)
        dc_bits = _DC_MIN_LENGTH[_mapped(zig[:, 0])]
        compressed = 4 + (dc_bits + 7) // 8 + (bits + 7) // 8
        out[start:start + len(zig)] = OVERHEAD + np.minimum(compressed, 128)
    return out


def count_packets(coefficients, blocks_w):
    """Return exact bytes for one general CP02 packet with row-reset DC."""
    a = _check(coefficients, blocks_w)
    zig = a.reshape(-1, 64)[:, ZIGZAG].astype(np.int32)
    dc = zig[:, 0]
    delta = dc.copy()
    delta[1:] -= dc[:-1]
    delta[::blocks_w] = dc[::blocks_w]
    values = _mapped(delta)
    dc_bits = min(int(_rice_lengths(values, k, 14).sum()) for k in range(14))
    block, pos = np.nonzero(zig[:, 1:])
    pos = pos + 1
    mapped = _mapped(zig[block, pos]) - 1
    # Separate blocks reset the preceding AC position to zero.
    prev = np.r_[0, pos[:-1]]
    if len(pos):
        prev[np.r_[True, block[1:] != block[:-1]]] = 0
    ac_bits = 5 * len(pos) + 2 * int(((pos - prev - 1) // 16).sum())
    ac_bits += 2 * (len(a) - int(np.count_nonzero(pos == 63)))
    for lo, hi in ((1, 5), (6, 20), (21, 63)):
        v = mapped[(pos >= lo) & (pos <= hi)]
        ac_bits += min(int(_rice_lengths(v, k, 12).sum()) for k in range(12))
    compressed = 4 + (dc_bits + 7) // 8 + (ac_bits + 7) // 8
    return OVERHEAD + min(compressed, len(a) * 128)


def rdo_skip(p, coefficients, mapped, rdo_lambda):
    """v25 choices and old scalar accounting, with batched size-only probes.

    cp02_probe_* records actual constructions (zero); cp02_logical_probe_*
    records exactly the v25 probe count/length. Counter calls are per plane.
    """
    stats = dict(lambda_value=float(rdo_lambda), distortion='clipped-source-YUV-SSE',
                 bit_proxy='isolated-CP02-body-or-DC16', checked_blocks=0,
                 zeroed_blocks=0, protected_blocks=0, cp02_probe_calls=0,
                 cp02_probe_bytes=0, cp02_logical_probe_calls=0,
                 cp02_logical_probe_bytes=0, cp02_size_counter_calls=0,
                 cp02_size_counter_blocks=0, predicted_bit_saving=0,
                 source_sse_increase=0, baseline_inverse_plane_calls=0)
    if not rdo_lambda or p.key:
        return coefficients, stats
    baseline = base.gm.reconstruct(coefficients, p.prediction, mapped, p.width, p.height)
    stats['baseline_inverse_plane_calls'] = 3
    result = []
    for plane, coeff in enumerate(coefficients):
        protected = base.roi.block_scales(mapped, p.width, p.height, plane) == 8
        if plane:
            priority = mapped == 8
            halo = priority.copy()
            halo[:, 1:] |= priority[:, :-1]
            halo[1:, :] |= priority[:-1, :]
            halo[1:, 1:] |= priority[:-1, :-1]
            protected = halo.reshape(-1)
        stats['protected_blocks'] += int(protected.sum())
        eligible = np.flatnonzero(np.any(coeff != 0, axis=(1, 2)) & ~protected)
        delta = (base._block_sse(p.source[plane] - p.prediction[plane])
                 - base._block_sse(p.source[plane] - baseline[plane]))
        _, dc, _ = base.sr.classifications(coeff)
        bits = np.full(len(eligible), 16, np.int64)
        full = ~dc[eligible]
        if full.any():
            sizes = isolated_packet_bytes(coeff[eligible[full]])
            bits[full] = np.maximum(1, 8 * (sizes - OVERHEAD))
            stats['cp02_size_counter_calls'] += 1
            stats['cp02_size_counter_blocks'] += len(sizes)
            stats['cp02_logical_probe_calls'] += len(sizes)
            stats['cp02_logical_probe_bytes'] += int(sizes.sum())
        picked = delta[eligible] <= rdo_lambda * bits
        indices = eligible[picked]
        selected = coeff.copy()
        selected[indices] = 0
        result.append(selected)
        stats['checked_blocks'] += len(eligible)
        stats['zeroed_blocks'] += len(indices)
        stats['predicted_bit_saving'] += int(bits[picked].sum())
        stats['source_sse_increase'] += int(delta[indices].sum())
    return tuple(result), stats
