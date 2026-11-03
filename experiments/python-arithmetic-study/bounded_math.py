"""Exact Q14 transform dispatch with checked intermediate-width bounds.

This is a Python arithmetic experiment, not generated HDL or a DSP schedule.
Full legal dequantized syntax falls back to int64. Decoder precision is never
silently reduced based on assumptions about host-generated coefficients.
"""
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'python-transform-study'))
import fixed_codec as frozen

Q32 = frozen.Q14.astype(np.int32)
Q32.setflags(write=False)
INT32_MAX = (1 << 31) - 1
MAX_DEQUANT = frozen.MAX_COEFF * 255


def stage_bounds(max_abs, direction):
    if type(max_abs) is not int or max_abs < 0 or direction not in ('forward', 'inverse'):
        raise ValueError('invalid arithmetic bound')
    axis = 1 if direction == 'forward' else 0
    l1 = int(np.abs(frozen.Q14).sum(axis=axis).max())
    first_acc = max_abs*l1 + 8192
    first_out = first_acc >> 14
    second_acc = first_out*l1 + 8192
    return {'max_abs_input': max_abs, 'matrix_l1': l1,
            'first_acc_abs_including_bias': first_acc,
            'first_rounded_abs': first_out,
            'second_acc_abs_including_bias': second_acc,
            'second_rounded_abs': second_acc >> 14,
            'int32_safe': max(first_acc, second_acc) <= INT32_MAX}


def _check(a, bound):
    a = np.asarray(a)
    if a.ndim != 3 or a.shape[1:] != (8, 8) or not len(a) or a.dtype.kind not in 'iu':
        raise ValueError('expected nonempty integer Nx8x8 blocks')
    # Convert extrema to Python ints before abs to avoid signed-min overflow.
    maximum = max(abs(int(a.min())), abs(int(a.max())))
    if maximum > bound:
        raise ValueError('input exceeds declared arithmetic domain')
    return a, maximum


def forward(blocks):
    a, maximum = _check(blocks, 255)
    assert stage_bounds(maximum, 'forward')['int32_safe']
    a = a.astype(np.int32)
    return (((((Q32 @ a + 8192) >> 14) @ Q32.T) + 8192) >> 14).astype(np.int64)


def inverse(coefficients):
    a, maximum = _check(coefficients, MAX_DEQUANT)
    if stage_bounds(maximum, 'inverse')['int32_safe']:
        a = a.astype(np.int32)
        return ((Q32.T @ ((a @ Q32 + 8192) >> 14) + 8192) >> 14).astype(np.int64)
    return frozen.inverse(a)


def signed_bits(max_abs):
    return int(max_abs).bit_length() + 1


def domain_report():
    values = {'residual_forward': stage_bounds(255, 'forward'),
              'full_syntax_inverse': stage_bounds(MAX_DEQUANT, 'inverse')}
    for row in values.values():
        for field in ('max_abs_input', 'first_acc_abs_including_bias',
                      'first_rounded_abs', 'second_acc_abs_including_bias', 'second_rounded_abs'):
            row[field + '_signed_bits'] = signed_bits(row[field])
    safe_limit = 0
    lo, hi = 0, MAX_DEQUANT
    while lo <= hi:
        middle = (lo + hi)//2
        if stage_bounds(middle, 'inverse')['int32_safe']:
            safe_limit, lo = middle, middle + 1
        else:
            hi = middle - 1
    return {'domains': values, 'inverse_int32_max_abs': safe_limit,
            'matrix_coefficient_signed_bits': signed_bits(int(np.abs(frozen.Q14).max())),
            'logical_multiply_mapping': 'Both passes fit a 25x18 signed multiplier for these declared domains; no schedule, DSP count, fit, timing or memory-service proof.',
            'accumulator_note': 'Bounds include rounding bias; actual reachable host key values usually use fewer bits than the full accepted coefficient syntax.'}


def residual_coefficients(source, prediction, scale):
    """Host residual transform; samples must be in the declared +/-255 domain."""
    result = []
    for i, (src, pred) in enumerate(zip(source, prediction)):
        residual = src.astype(np.int64) - pred
        h, w = residual.shape
        padded = np.pad(residual, ((0, (-h)%8), (0, (-w)%8)), mode='edge')
        ph, pw = padded.shape
        blocks = padded.reshape(ph//8, 8, pw//8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
        coeff = frozen.round_quantize(forward(blocks), frozen.qtable(scale, i != 0))
        if np.any(np.abs(coeff) > frozen.MAX_COEFF):
            raise ValueError('coefficient outside frozen wire domain')
        result.append(coeff.astype(np.int16))
    return result


def reconstruct(coefficients, prediction, scale):
    """Exact inverse with automatic int64 fallback for wider legal coefficients."""
    planes = []
    for i, (coeff, pred) in enumerate(zip(coefficients, prediction)):
        h, w = pred.shape
        ph, pw = ((h+7)//8)*8, ((w+7)//8)*8
        residual = inverse(coeff.astype(np.int64)*frozen.qtable(scale, i != 0))
        residual = residual.reshape(ph//8, pw//8, 8, 8).transpose(0, 2, 1, 3).reshape(ph, pw)[:h, :w]
        planes.append(np.clip(pred+residual, 0, 255).astype(np.int16))
    return planes
