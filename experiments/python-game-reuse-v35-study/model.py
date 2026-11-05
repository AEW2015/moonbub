"""Exact HM34 encoder reusing validated, already-paid GM27 map bytes.

No imports are patched. Every cache is independently decoded and checked for
both field equality and the frozen GM27 encoder's canonical mode/tie choice.
Only the winning HM34 candidate is serialized; all three sizes are computed.
"""
from pathlib import Path
import importlib.util
import sys
import struct
import time
import numpy as np

HERE = Path(__file__).resolve().parent

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj

old = load('reuse35_frozen_hm34', HERE.parent/'python-game-hierarchy-v34-study/model.py')
decoder = old.decoder
unpack, HEADER, CRC = decoder.unpack, decoder.HEADER, decoder.CRC


def _rice_plan(values, maximum_k, escape_bits):
    """Exact bit costs, including every parameter trial; stable smallest k."""
    a = np.asarray(values, dtype=np.int64)
    costs = [int(np.where((a >> k) >= 7, 7+escape_bits, (a >> k)+1+k).sum())
             for k in range(maximum_k+1)]
    k = min(range(len(costs)), key=costs.__getitem__)
    return k, costs[k]


def _canonical_plan(a):
    """GM27 costs without encoding alternative Rice streams or map bytes."""
    flat = a.reshape(-1, 2)
    n, mw = len(flat), a.shape[1]
    if np.all(flat == flat[0]):
        return dict(mode=0, candidates=1, rice_axis_trials=0, rice_value_trials=0)
    run_count = 1+int(np.count_nonzero(np.any(flat[1:] != flat[:-1], axis=1)))
    values, counts = np.unique(flat, axis=0, return_counts=True)
    default = values[np.argmax(counts)]
    costs = [1+2*n, 1+4*run_count, 3+4*(n-int(counts.max())), 1+(12*n+7)//8]
    rice_ks = {}
    wide = flat.astype(np.int64).reshape(a.shape)
    left = np.zeros_like(wide)
    left[:, 1:] = wide[:, :-1]
    top = np.zeros_like(wide)
    top[1:] = wide[:-1]
    right = np.zeros_like(wide)
    right[1:, :-1] = wide[:-1, 1:]
    right[1:, -1] = wide[:-1, -1]
    median = left+top+right-np.minimum(np.minimum(left, top), right)-np.maximum(np.maximum(left, top), right)
    for mode, prediction in ((5, left), (6, median)):
        delta = wide-prediction
        zig = np.where(delta >= 0, 2*delta, -2*delta-1).reshape(-1, 2)
        plans = [_rice_plan(zig[:, axis], 6, 7) for axis in (0, 1)]
        rice_ks[mode] = [p[0] for p in plans]
        costs.append(3+(sum(p[1] for p in plans)+7)//8)
    mode = 1+min(range(6), key=costs.__getitem__)
    return dict(mode=mode, costs=costs, default=default, rice_ks=rice_ks,
                candidates=6, rice_axis_trials=28, rice_value_trials=28*n)


def _validated_cache(data, field, label):
    # The syntax parser does not call pack_vectors or require minimum encoding.
    decoded = decoder.unpack_gm27(data, field.shape[1], field.shape[0])
    if not np.array_equal(decoded, field):
        raise ValueError(label+' cache field mismatch')
    plan = _canonical_plan(field)
    mode = data[0]
    if mode != plan['mode']:
        raise ValueError(label+' noncanonical GM27 cache mode')
    if mode == 2 and len(data) != plan['costs'][1]:
        raise ValueError(label+' noncanonical GM27 cache runs')
    if mode == 3 and data[1:3] != plan['default'].tobytes():
        raise ValueError(label+' noncanonical GM27 cache default')
    if mode in (5, 6) and list(data[1:3]) != plan['rice_ks'][mode]:
        raise ValueError(label+' noncanonical GM27 cache Rice parameters')
    return data, plan


def pack(parent, child, width, height, *, parent_bytes=None, child_bytes=None, return_info=False):
    """Produce byte-identical frozen HM34 packets with optional GM27 caches.

    Caches must be immutable bytes, valid syntax, equal to their arrays, and
    canonical under the frozen GM27 stable ties. Nonminimal-valid caches raise
    ValueError. Omitted caches use the frozen encoder, including partial reuse.
    """
    started = time.perf_counter_ns()
    pshape, cshape = decoder.geometry(width, height)
    p, c = np.asarray(parent), np.asarray(child)
    for a, shape in ((p, pshape), (c, cshape)):
        if a.dtype != np.int8 or a.shape != shape+(2,) or np.any(np.abs(a.astype(np.int16)) > 18):
            raise ValueError('HM34 bounded int8 vector field')
    setup_end = time.perf_counter_ns()
    plans = []
    calls = 0
    caches = 0
    gmwork = []
    maps = []
    for data, field, label in ((parent_bytes, p, 'parent'), (child_bytes, c, 'child')):
        if data is None:
            data, work = old.frozen.pack_vectors(field, return_work=True)
            gmwork.append(work)
            calls += 1
        else:
            data, plan = _validated_cache(data, field, label)
            plans.append(plan)
            caches += 1
        maps.append(data)
    parent_bytes, flat_bytes = maps
    validated_end = time.perf_counter_ns()
    seed = np.repeat(np.repeat(p, 2, axis=0), 2, axis=1)[:cshape[0], :cshape[1]]
    delta = c.astype(np.int16)-seed.astype(np.int16)
    indices = np.flatnonzero(np.any(delta != 0, axis=2).reshape(-1))
    values = delta.reshape(-1, 2)[indices].astype(np.int64)
    axes = [np.where(values[:, axis] >= 0, 2*values[:, axis], -2*values[:, axis]-1) for axis in (0, 1)]
    axis_plans = [_rice_plan(axis, 6, 7) for axis in axes]
    ks = [plan[0] for plan in axis_plans]
    axis_bits = sum(plan[1] for plan in axis_plans)
    gaps = np.diff(np.concatenate((np.array([-1]), indices)))-1
    escape_bits = max(1, (cshape[0]*cshape[1]-1).bit_length())
    kg, gap_bits = _rice_plan(gaps, min(10, escape_bits), escape_bits)
    changed = np.any(delta != 0, axis=2)
    masks = np.zeros(pshape, np.uint8)
    for local in range(4):
        sub = changed[local//2::2, local%2::2]
        masks[:sub.shape[0], :sub.shape[1]] |= sub.astype(np.uint8) << local
    mask_bits = masks.size+4*int(np.count_nonzero(masks))+axis_bits
    base = HEADER.size+CRC.size
    sizes = [base+len(flat_bytes), base+len(parent_bytes)+5+(gap_bits+axis_bits+7)//8,
             base+len(parent_bytes)+2+(mask_bits+7)//8]
    selected = min(range(3), key=sizes.__getitem__)
    planned_end = time.perf_counter_ns()
    if selected == 0:
        packet = old._seal(0, width, height, b'', flat_bytes)
        emitted_bits = 0
    else:
        bits = old.Bits()
        if selected == 1:
            for i, gap in enumerate(gaps):
                old._rice(bits, int(gap), kg, escape_bits)
                for axis in (0, 1):
                    old._rice(bits, int(axes[axis][i]), ks[axis], 7)
            payload = struct.pack('<HBBB', len(indices), kg, *ks)+bits.finish()
        else:
            for py in range(pshape[0]):
                for px in range(pshape[1]):
                    mask = int(masks[py, px])
                    bits.put(bool(mask), 1)
                    if mask:
                        bits.put(mask, 4)
                        for local in range(4):
                            if mask & (1 << local):
                                y, x = 2*py+local//2, 2*px+local%2
                                for axis in (0, 1):
                                    old._rice(bits, old._zig(int(delta[y, x, axis])), ks[axis], 7)
            payload = bytes(ks)+bits.finish()
        emitted_bits = len(bits.bits)
        packet = old._seal(selected, width, height, parent_bytes, payload)
    ended = time.perf_counter_ns()
    assert len(packet) == sizes[selected]
    info = dict(selected_mode=selected, selected_mode_name=decoder.MODE_NAMES[selected],
                candidates=[dict(mode=mode, name=decoder.MODE_NAMES[mode], bytes=size) for mode, size in enumerate(sizes)],
                parent_gm27_bytes=len(parent_bytes), flat_child_gm27_bytes=len(flat_bytes),
                refinement_vectors=len(indices), child_vectors=cshape[0]*cshape[1],
                component_bytes=len(packet), sparse_rice_parameters=[kg]+ks,
                header_bytes=HEADER.size, crc_bytes=CRC.size, stable_tie_order=list(decoder.MODE_NAMES),
                work=dict(cache_maps_validated=caches, frozen_pack_vectors_calls=calls,
                          cached_gm27_candidates_costed=sum(p['candidates'] for p in plans),
                          cached_gm27_rice_axis_cost_trials=sum(p['rice_axis_trials'] for p in plans),
                          cached_gm27_rice_value_cost_trials=sum(p['rice_value_trials'] for p in plans),
                          uncached_gm27_work=gmwork, hm34_candidates_costed=3,
                          hm34_candidates_serialized=1, hm34_crc_calls=1,
                          hm34_rice_parameter_cost_trials=14+min(10, escape_bits)+1,
                          hm34_rice_value_cost_trials=14*len(indices)+(min(10, escape_bits)+1)*len(gaps),
                          hm34_winner_bits_emitted=emitted_bits),
                timings_ms=dict(setup=(setup_end-started)/1e6, cache_validation_and_uncached_maps=(validated_end-setup_end)/1e6,
                                hm34_planning=(planned_end-validated_end)/1e6, winner_serialization_crc=(ended-planned_end)/1e6,
                                total=(ended-started)/1e6))
    return (packet, info) if return_info else packet
