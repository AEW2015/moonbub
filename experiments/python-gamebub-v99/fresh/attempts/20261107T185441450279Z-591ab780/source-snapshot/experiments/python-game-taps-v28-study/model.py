"""Tap-aware, pixel-exact GM27 prediction and receive adapter.

This module imports frozen GM27 grammar/Q14 arithmetic without modifying it.
Reference gathers use 1, 2, or 4 taps according to fractional motion axes.
Clamped duplicate coordinates are still counted and fetched independently.
"""
from pathlib import Path
import importlib.util
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('taps28_frozen_unified27', HERE.parent / 'python-game-unified-v27-study/model.py')
frozen = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = frozen
_spec.loader.exec_module(frozen)


def _validated(reference, vectors, block_size):
    ref = frozen._planes(reference)
    h, w = ref[0].shape
    mw, mh = frozen._grid(w, h, block_size)
    return ref, frozen.old._validate_vectors(vectors, mw, mh)


def _predict(ref, vectors, block_size):
    if not np.any(vectors):
        # Copy is intentional: the output never aliases a mutable reference.
        return tuple(image.copy() for image in ref)
    result = []
    for plane, image in enumerate(ref):
        ph, pw = image.shape
        bs, den = (block_size, 2) if plane == 0 else (block_size // 2, 4)
        # Broadcast per-axis output coordinates; avoid the old pair of int64
        # full-plane mgrid arrays and full-plane two-component vector array.
        qx = np.repeat(np.repeat(vectors[..., 0], bs, axis=0), bs, axis=1)[:ph, :pw]
        qy = np.repeat(np.repeat(vectors[..., 1], bs, axis=0), bs, axis=1)[:ph, :pw]
        ix, fx = np.divmod(qx, den)
        iy, fy = np.divmod(qy, den)
        x0 = np.clip(np.arange(pw, dtype=np.int32)[None, :] + ix, 0, pw-1)
        y0 = np.clip(np.arange(ph, dtype=np.int32)[:, None] + iy, 0, ph-1)
        mx, my = fx != 0, fy != 0
        total = image[y0, x0].astype(np.int32)
        if not np.any(mx) and not np.any(my):
            result.append(total.astype(np.int16))
            continue
        total *= (den-fx)*(den-fy)
        if np.any(mx):
            # Clamp the original coordinate+1, not the already-clamped x0+1.
            # Negative coordinates at the left edge must remain clamped.
            x1 = np.clip(np.arange(pw, dtype=np.int32)[None, :] + ix + 1, 0, pw-1)
            total[mx] += fx[mx]*(den-fy[mx])*image[y0[mx], x1[mx]]
        if np.any(my):
            y1 = np.clip(np.arange(ph, dtype=np.int32)[:, None] + iy + 1, 0, ph-1)
            total[my] += (den-fx[my])*fy[my]*image[y1[my], x0[my]]
        both = mx & my
        if np.any(both):
            total[both] += fx[both]*fy[both]*image[y1[both], x1[both]]
        result.append(((total + den*den//2)//(den*den)).astype(np.int16))
    return tuple(result)


def predict(reference, vectors, block_size=16):
    """Same bounds/floor/clamp/single rounding as frozen GM26 prediction."""
    ref, a = _validated(reference, vectors, block_size)
    return _predict(ref, a, block_size)


def predict_with_info(reference, vectors, block_size=16):
    """Return planes and exact logical gather counts, including edge duplicates.

    Counts are weighted by actual partial-edge block sizes, not padded grids.
    Validation reads, map reads and output writes are separate from ref gathers.
    Named arrays describe NumPy storage, not an FPGA line-buffer architecture.
    """
    ref, a = _validated(reference, vectors, block_size)
    output = _predict(ref, a, block_size)
    details = []
    for plane, image in enumerate(ref):
        ph, pw = image.shape
        bs, den = (block_size, 2) if plane == 0 else (block_size//2, 4)
        heights = np.minimum(bs, ph-np.arange(a.shape[0])*bs)
        widths = np.minimum(bs, pw-np.arange(a.shape[1])*bs)
        pixels = heights[:, None]*widths[None, :]
        fractional = a % den != 0
        taps = (1+fractional[..., 0].astype(np.int64))*(1+fractional[..., 1])
        counts = {str(n): int(pixels[taps == n].sum()) for n in (1, 2, 4)}
        details.append(dict(plane=plane, samples=image.size, denominator=den,
                            pixels_by_taps=counts, reference_sample_fetches=int((pixels*taps).sum())))
    n = sum(p.size for p in ref)
    return output, dict(reference_sample_fetches=sum(d['reference_sample_fetches'] for d in details),
                        frozen_reference_sample_fetches=4*n, plane_work=details,
                        clamped_duplicate_taps_deduplicated=False,
                        prediction_array_bytes=sum(p.nbytes for p in output),
                        validated_reference_array_bytes=sum(p.nbytes for p in ref),
                        validated_vector_array_bytes=a.nbytes,
                        whole_map_zero_shortcut=not bool(np.any(a)),
                        named_plane_arrays=dict(qx='int32[padded_h,padded_w] then cropped view',
                            qy='int32[padded_h,padded_w] then cropped view',
                            ix_iy_fx_fy='four int32[ph,pw]', x0_y0='two int32[ph,pw]',
                            x1_y1='up to two int32[ph,pw]', mx_my_both='three bool[ph,pw]',
                            total='int32[ph,pw]', output='int16[ph,pw]'),
                        array_scope='Named retained expression arrays; excludes ufunc/indexing temporaries and allocator overhead. Full Python planes, not fitted FPGA RAM.')


def decode(packet, reference=None, *, expected_epoch=None, expected_reference_id=None):
    """Frozen GM27 syntax, exact prediction, frozen Q14 reconstruction/tags."""
    meta = frozen.parse(packet, expected_epoch=expected_epoch)
    w, h = meta['width'], meta['height']
    if meta['key']:
        prediction = tuple(np.full(shape, 128, np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
    else:
        if expected_reference_id is None or expected_reference_id != meta['reference_id']:
            raise ValueError('GM27 exact reference ID required')
        ref = frozen._planes(reference, (w, h))
        if frozen.C.reference_tag(ref) != meta['reference_tag']:
            raise ValueError('GM27 exact reconstructed reference tag')
        prediction = predict(ref, meta['vectors'], meta['block_size'])
    rebuilt = frozen.gm.reconstruct(meta['coefficients'], prediction, meta['scale_map'], w, h)
    if frozen.C.reference_tag(rebuilt) != meta['reconstructed_tag']:
        raise ValueError('GM27 reconstructed output tag')
    return rebuilt, meta
