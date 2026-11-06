#!/usr/bin/env python3
"""Independent operation-count and causal-edge checks for the V83 workload."""
from __future__ import annotations
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v83'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    workload = load('cu83_workload_test', AREA / 'workload.py')
    commitment = load('cu83_workload_commitment', ROOT / 'scripts/cu66-v82/prototype_commitment.py')
    residency = load('cu83_workload_residency', ROOT / 'fpga/experiments/cu66-v81/residency/model.py')
    native = load('cu83_workload_native', ROOT / 'experiments/python-gamebub-v82/native/data.py')
    costs = load('cu83_workload_costs', ROOT / 'experiments/python-gamebub-v82/execution.py')
    scheduler = load('cu83_workload_scheduler', AREA / 'scheduler.py')
    checks = []
    capacities = dict(memory=1, inverse=1, reconstruct=1, hash=4, tree_r=1, tree_w=1, map_r=1, map_w=1)

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def reject(name, fn):
        try:
            fn()
        except (ValueError, TypeError, KeyError, IndexError):
            checks.append(name)
        else:
            raise AssertionError('accepted invalid workload: ' + name)

    def verify(frame, elided, plan, *, geometry, granularity, slots, hud_blocks, timeline=False):
        w = workload.build(frame, elided, plan, granularity=granularity, group_slots=slots,
                           hud_blocks=hud_blocks, inverse_cycles=64, reconstruct_cycles=64)
        c, jobs = w['counts'], w['jobs']
        n = sum(geometry[2:]); key = frame['key']
        dirty = {t for g in plan['recomputed_groups'] for t in g['tile_indices']}
        ref = sum(not key and not frame['hidden_mask'][t] and
                  (not frame['copy_ref_mask'][t] or not elided[t] or t in dirty)
                  for t in range(n))
        stores = n - sum(elided)
        clone = 0 if key else 2 * plan['memory']['padded_leaves'] - 1
        rwords = clone * 8 + sum(8 if j['kind'] == 'seal' else
                                (16 if j['kind'] == 'internal' else 0) + (0 if key else 8)
                                for j in plan['jobs'])
        wwords = clone * 8 + sum(j['kind'] != 'seal' for j in plan['jobs']) * 8
        expected = dict(reference_read_BL8=ref * 4, canonical_write_BL8=stores * 4,
                        HUD_read_BL8=hud_blocks, HUD_write_BL8=hud_blocks,
                        tree_r_words32=rwords, tree_w_words32=wwords,
                        map_r_entries=n, map_w_entries=n + stores,
                        hash_compression_blocks=sum(j['blocks'] for j in plan['jobs']))
        check('independent-counts', all(c.get(k, 0) == v for k, v in expected.items()))
        check('mode-partition', sum(c['mode_tiles'].values()) == n)
        check('group-ring', all(jobs[g['start']]['deps'] ==
                               ([] if i < slots else [w['groups'][i - slots]['release']])
                               for i, g in enumerate(w['groups'])))
        lookup = {j['tile']: j for j in jobs if j['kind'] == 'map_lookup'}
        invalid = {j['tile']: j for j in jobs if j['kind'] == 'map_invalidate'}
        inverses = {j['tile']: j for j in jobs if j['kind'] == 'inverse'}
        reads = {j['tile']: j for j in jobs if j['kind'] == 'reference_read'}
        recon = {j['tile']: j for j in jobs if j['kind'] == 'reconstruct'}
        check('invalidate-before-store', all(invalid[j['tile']]['id'] in j['deps']
                                             for j in jobs if j['kind'] == 'canonical_write'))
        check('inverse-does-not-wait-reference', all(j['deps'] == [lookup[t]['id']]
                                                    for t, j in inverses.items()))
        check('reconstruction-waits-inverse-and-reference',
              all(inverses[t]['id'] in j['deps'] and
                  (t not in reads or reads[t]['id'] in j['deps']) for t, j in recon.items()))
        if timeline:
            result = scheduler.schedule(jobs, capacities,
                                        memory_windows=dict(period=10000, blocked=[(0, 2000)]),
                                        retain_timeline=True)
            timings = {r['id']: r for r in result['timeline']}
            check('all-edges-time-causal', all(timings[j['id']]['start'] >= timings[d]['finish']
                                              for j in jobs for d in j['deps']))
            check('completion-after-all-writes', all(timings[w['complete']]['finish'] >= timings[j['id']]['finish']
                                                    for j in jobs if j['kind'] in ('canonical_write', 'HUD_read', 'map_shadow_entry')))
            check('completion-after-every-task', timings[w['complete']]['finish'] == result['finish_cycles'])
            check('memory-work-accounting', result['resources']['memory']['work_cycles'] ==
                  (ref * 4 + hud_blocks) * 18 + (stores * 4 + hud_blocks) * 16)
            events = [(timings[g['start']]['start'], 1) for g in w['groups']]
            events += [(timings[g['release']]['finish'], -1) for g in w['groups']]
            # At equal time, a released slot is available to its next group.
            live = maximum = 0
            for _, delta in sorted(events):
                live += delta; maximum = max(maximum, live)
            check('bounded-group-buffer-lifetime', live == 0 and maximum <= slots)
        return w

    geometry = (40, 8, 5, 3, 2)
    hidden = bytes(int(i in (4, 7, 9)) for i in range(10))
    pixels = [bytes([128 if h else i + 1]) * 64 for i, h in enumerate(hidden)]
    tree = commitment.CommitmentTree(granularity=4, geometry=geometry)
    model = residency.Residency(10)
    first = None
    synthetic_stats = []
    for ordinal, changed in enumerate((None, 1, None, None, 2, None)):
        key = ordinal == 0
        old = list(pixels)
        if changed is not None:
            pixels[changed] = bytes([50 + ordinal]) * 64
        same = bytes(int(a == b) for a, b in zip(pixels, old)) if not key else bytes(10)
        copy = bytes(int(not key and not hidden[t] and same[t]) for t in range(10))
        frame = dict(fid=ordinal, refid=0xffffffff if key else ordinal - 1, key=key,
                     generation=ordinal + 1, geometry=geometry, tiles=list(pixels), hidden_mask=hidden,
                     copy_ref_mask=copy, same_mask=same, hud=b'unit-hud')
        candidate = 0 if model.reference is None else (model.reference + 1) % 3
        elided = [not key and bool(same[t]) and bool(model.masks[t] & (1 << candidate)) for t in range(10)]
        plan = tree.plan(frame, copy)
        for slots in (1, 4):
            w = verify(frame, elided, plan, geometry=geometry, granularity=4,
                       slots=slots, hud_blocks=11, timeline=True)
        synthetic_stats.append(dict(ordinal=ordinal, key=key,
                                    store_elisions=sum(elided), dirty_groups=len(plan['recomputed_groups'])))
        if first is None:
            first = frame, elided, plan
        model.begin(ordinal, str(ordinal), candidate, key, pixels, same)
        model.step(); model.commit(); model.present(); tree.commit(plan)
    check('synthetic-materializes-and-elides-COPY', any(s['store_elisions'] for s in synthetic_stats)
          and any(not s['key'] and not s['store_elisions'] for s in synthetic_stats))
    check('synthetic-mixed-and-clean-leaves', any(s['dirty_groups'] for s in synthetic_stats[1:])
          and any(not s['dirty_groups'] for s in synthetic_stats[1:]))
    frame, elided, plan = first
    reject('bad-mask-size', lambda: workload.build(frame, elided[:-1], plan, granularity=4))
    reject('bad-group-slots', lambda: workload.build(frame, elided, plan, granularity=4, group_slots=0))
    reject('bad-timing-bool', lambda: workload.build(frame, elided, plan, granularity=4, read_gap=True))
    reject('key-copy-rejected', lambda: workload.build(dict(frame, copy_ref_mask=bytes([1]) + bytes(9)), elided, plan, granularity=4))
    reject('key-elision-rejected', lambda: workload.build(frame, [True] + [False] * 9, plan, granularity=4))
    reject('bad-tree-granularity', lambda: workload.build(frame, elided, plan, granularity=16))

    tree = commitment.CommitmentTree(granularity=16)
    model = residency.Residency(8100)
    native_records = []
    for ordinal, original in enumerate(itertools.islice(native.iter_frames(), 8)):
        frame = dict(original, generation=original['ordinal'] + 1)
        candidate = 0 if model.reference is None else (model.reference + 1) % 3
        elided = [not frame['key'] and bool(frame['same_mask'][t]) and
                  bool(model.masks[t] & (1 << candidate)) for t in range(8100)]
        plan = tree.plan(frame, frame['copy_ref_mask'])
        w = verify(frame, elided, plan, geometry=commitment.GEOMETRY, granularity=16,
                   slots=4, hud_blocks=2640, timeline=ordinal < 2)
        cost = costs.account(frame, elided, plan)
        c = w['counts']; m = cost['metadata']
        check('native-v82-counter-parity',
              (c.get('reference_read_BL8', 0), c['canonical_write_BL8'], c['tree_r_words32'],
               c['tree_w_words32'], c['map_r_entries'], c['map_w_entries']) ==
              (cost['logical_BL8']['reference_reads'], cost['logical_BL8']['canonical_writes'],
               m['tree_read_words32'], m['tree_write_words32'], m['map_read_entries'], m['map_write_entries']))
        native_records.append(dict(cohort=frame['cohort'], fid=frame['fid'], key=frame['key'],
                                   canonical_sha256=frame['canonical_sha256'], tasks=len(w['jobs']),
                                   store_elisions=sum(elided)))
        model.begin(frame['fid'], frame['packet_sha256'], candidate, frame['key'], frame['tiles'], frame['same_mask'])
        model.step(); model.commit(); model.present(); tree.commit(plan)
    report = dict(schema='cu83-workload-tests-v1', status='PASS', checks=len(checks),
                  cases=checks, synthetic_sources=synthetic_stats, native_sources=native_records,
                  native_scope='First eight native records; root full-corpus campaign separately verifies all457.',
                  source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in (Path(__file__).resolve(), AREA / 'workload.py', AREA / 'scheduler.py',
                                           ROOT / 'scripts/cu66-v82/prototype_commitment.py',
                                           ROOT / 'experiments/python-gamebub-v82/execution.py')},
                  timing_is_physical=False)
    (AREA / 'workload-tests.json').write_text(json.dumps(report, indent=2) + '\n')
    print('V83_WORKLOAD_TESTS_PASS', len(checks), 'native8 synthetic6')


if __name__ == '__main__':
    main()
