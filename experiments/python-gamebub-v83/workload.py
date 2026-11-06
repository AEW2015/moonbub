"""Causal COPY/CONST/residual execution workload for the V83 Python study.

This models prospective scheduling, not RTL timing. Inverse costs, memory service
intervals and resource ports are explicit caller assumptions. Native pixels and
V82 commitment jobs supply semantics; no inverse arithmetic is executed here.
"""
from __future__ import annotations
from collections import Counter


def build(frame, elided, plan, *, inverse_cycles=256, read_gap=18,
          write_gap=16, group_slots=1, granularity=16, hud_blocks=2640,
          reconstruct_cycles=64):
    """Return jobs, exact priced operation counts, and the complete-task id.

    A fixed ring of group buffers admits group i only after group i-N releases.
    Each release waits for physical stores, map writes and its leaf digest write.
    The default service costs are V82 bridge intervals, conservatively charged to
    completion of every BL8 (including the final command). There is no LCD model.
    """
    for name, value in [('inverse_cycles', inverse_cycles), ('read_gap', read_gap),
                        ('write_gap', write_gap), ('group_slots', group_slots),
                        ('granularity', granularity), ('hud_blocks', hud_blocks),
                        ('reconstruct_cycles', reconstruct_cycles)]:
        if type(value) is not int or value < (0 if name in ('inverse_cycles', 'hud_blocks', 'reconstruct_cycles') else 1):
            raise ValueError('invalid ' + name)
    geometry = tuple(frame.get('geometry', plan['frame']['geometry']))
    count = sum(geometry[2:])
    hidden, copy = bytes(frame['hidden_mask']), bytes(frame['copy_ref_mask'])
    if len(elided) != count or len(hidden) != count or len(copy) != count:
        raise ValueError('tile coverage')
    if any(v not in (0, 1, False, True) for v in elided) or any(v not in (0, 1) for v in hidden + copy):
        raise ValueError('nonboolean tile mode')
    key = bool(frame['key'])
    if key and (any(elided) or any(copy)):
        raise ValueError('COPY/store elision on key')
    if any(c and h for c, h in zip(copy, hidden)):
        raise ValueError('COPY on hidden tile')
    groups = []
    offset = 0
    for plane, tiles in enumerate(geometry[2:]):
        for start in range(0, tiles, granularity):
            groups.append(list(range(offset + start, offset + min(start + granularity, tiles))))
        offset += tiles
    L = plan['memory']['padded_leaves']
    if L != 1 << (len(groups) - 1).bit_length():
        raise ValueError('granularity/tree shape disagreement')
    recomputed = {g['leaf']: g for g in plan['recomputed_groups']}
    if any(groups[i] != g['tile_indices'] for i, g in recomputed.items()):
        raise ValueError('granularity/leaf tile disagreement')
    hash_jobs = plan['jobs']
    leaf_by_index = {j['node'] - L: j for j in hash_jobs if j['kind'] == 'leaf'}
    if set(leaf_by_index) != set(recomputed):
        raise ValueError('leaf job coverage')
    if not hash_jobs or hash_jobs[-1]['kind'] != 'seal':
        raise ValueError('missing final seal')
    jobs, totals = [], Counter()

    def add(kind, resource=None, duration=0, deps=(), **fields):
        ident = len(jobs)
        deps = sorted(set(deps))
        if any(type(d) is not int or d < 0 or d >= ident for d in deps):
            raise ValueError('noncausal dependency')
        job = dict(id=ident, deps=deps, resource=resource,
                   duration=duration, kind=kind, **fields)
        jobs.append(job)
        if 'BL8' in fields:
            totals[kind + '_BL8'] += fields['BL8']
        if 'words32' in fields:
            totals[resource + '_words32'] += fields['words32']
        if 'entries' in fields:
            totals[resource + '_entries'] += fields['entries']
        return ident

    # Every cloned 32B digest uses one bounded temporary buffer: read then write,
    # then reuse the temporary. The two tree ports are independent, but this
    # deliberately conservative clone implementation does not overlap copies.
    clone_done = add('epoch_start')
    clone_nodes = 0 if key else 2 * L - 1
    for node in range(1, clone_nodes + 1):
        rd = add('tree_clone_read', 'tree_r', 8, [clone_done], words32=8, node=node)
        clone_done = add('tree_clone_write', 'tree_w', 8, [rd], words32=8, node=node)
    totals['tree_clone_nodes'] = clone_nodes
    digest_done = {}
    starts, releases, stores, map_updates = [], [], [], []
    modes = Counter()

    def finish_hash(hj, payload_deps=(), group=None, extra_deps=()):
        deps = [clone_done, *payload_deps, *extra_deps,
                *(digest_done[d] for d in hj['deps'])]
        words = (8 if hj['kind'] == 'seal' else
                 (16 if hj['kind'] == 'internal' else 0) + (0 if key else 8))
        if words:
            read = add('hash_metadata_read', 'tree_r', words, deps,
                       words32=words, node=hj['node'], group=group)
            deps = [read]
        hashed = add('hash_' + hj['kind'], 'hash', hj['cycles'], deps,
                     hash_id=hj['id'], node=hj['node'], group=group,
                     compression_blocks=hj['blocks'])
        totals['hash_cycles'] += hj['cycles']
        totals['hash_compression_blocks'] += hj['blocks']
        if hj['kind'] != 'seal':
            hashed = add('hash_digest_write', 'tree_w', 8, [hashed],
                         words32=8, node=hj['node'], group=group)
        digest_done[hj['id']] = hashed
        return hashed

    for gi, tile_indices in enumerate(groups):
        start_deps = [releases[gi - group_slots]] if gi >= group_slots else []
        started = add('group_start', deps=start_deps, group=gi)
        starts.append(started)
        payloads, group_stores, group_maps = [], [], []
        dirty = gi in recomputed
        for tile in tile_indices:
            map_rd = add('map_lookup', 'map_r', 1, [started], entries=1, tile=tile, group=gi)
            deps = [map_rd]
            if not key and not hidden[tile] and (not copy[tile] or not elided[tile] or dirty):
                ref = add('reference_read', 'memory', 4 * read_gap, deps,
                          BL8=4, tile=tile, group=gi)
                deps = [ref]
            mode = 'CONST128' if hidden[tile] else 'COPY_REF' if copy[tile] else 'RESIDUAL'
            modes[mode] += 1
            if mode == 'RESIDUAL':
                inverse = add('inverse', 'inverse', inverse_cycles, [map_rd], tile=tile, group=gi)
                payload = add('reconstruct', 'reconstruct', reconstruct_cycles,
                              [inverse, *deps], tile=tile, group=gi)
                totals['inverse_tiles'] += 1
                totals['reconstruct_tiles'] += 1
            elif mode == 'CONST128':
                payload = add('const_generate', duration=1, deps=deps, tile=tile, group=gi)
            else:
                # A resident COPY in a clean group need not be materialized;
                # otherwise deps already include its actual reference read.
                payload = add('copy_ready', deps=deps, tile=tile, group=gi)
            payloads.append(payload)
            done = payload
            if not elided[tile]:
                invalid = add('map_invalidate', 'map_w', 1, [map_rd], entries=1, tile=tile, group=gi)
                done = add('canonical_write', 'memory', 4 * write_gap,
                           [payload, invalid], BL8=4, tile=tile, group=gi)
                group_stores.append(done)
                stores.append(done)
            updated = add('map_shadow_entry', 'map_w', 1, [done], entries=1, tile=tile, group=gi)
            group_maps.append(updated)
            map_updates.append(updated)
        # Leaf hashes consume payloads only once all group tiles are ready.
        # Hash input buffering is bounded by group_slots * granularity *64B.
        leaf_done = finish_hash(leaf_by_index[gi], payloads, gi) if dirty else None
        release = add('group_release', deps=[*group_stores, *group_maps,
                                             *([] if leaf_done is None else [leaf_done])], group=gi)
        releases.append(release)

    # Empty leaves and internal nodes may run while later groups are produced.
    # Recomputed-equal nodes retain dependencies via V82's propagated frontier.
    for hj in hash_jobs:
        if hj['kind'] not in ('leaf', 'seal'):
            finish_hash(hj)

    # HUD readback follows its corresponding physical writes, not an oracle
    # arrival at time zero. Eight BL8 chunks permit bounded-memory arbitration.
    hud_reads = []
    for offset in range(0, hud_blocks, 8):
        n = min(8, hud_blocks - offset)
        written = add('HUD_write', 'memory', n * write_gap, BL8=n, block=offset)
        readback = add('HUD_read', 'memory', n * read_gap, [written], BL8=n, block=offset)
        hud_reads.append(readback)
    hud_done = add('HUD_readback_complete', deps=hud_reads)
    seal = finish_hash(hash_jobs[-1], extra_deps=[hud_done])
    complete = add('candidate_complete', deps=[seal, *stores, *map_updates, *releases, hud_done])
    counts = dict(totals)
    counts.update(mode_tiles=dict(modes), groups=len(groups),
                  recomputed_groups=len(recomputed), group_starts=starts,
                  group_releases=releases, complete=complete,
                  group_payload_buffer_bytes=group_slots * granularity * 64,
                  clone_temporary_bytes=32,
                  hash_jobs=len(hash_jobs), task_count=len(jobs),
                  physical_store_tiles=count - sum(elided), resident_store_elisions=sum(elided))
    return dict(jobs=jobs, counts=counts, complete=complete,
                groups=[dict(start=a, release=b) for a, b in zip(starts, releases)],
                assumptions=dict(inverse_cycles_per_visible_residual_tile=inverse_cycles,
                                 reconstruct_cycles_per_visible_residual_tile=reconstruct_cycles,
                                 read_service_cycles_per_BL8=read_gap,
                                 write_service_cycles_per_BL8=write_gap,
                                 group_slots=group_slots, granularity=granularity,
                                 metadata_ports='Independent 1x32-bit read and 1x32-bit write per clock; separate map ports.',
                                 clone='Serial per-digest read then write using a 32-byte temporary.',
                                 HUD='8-BL8 chunks; readback after corresponding write; semantic HUD hash cost omitted.',
                                 producer='Entropy/ingress and mode classification available at epoch start; residual inverse and reconstruction costs are hypothetical. Inverse can overlap reference fetch; reconstruction waits for both.',
                                 CONST='One cycle per CONST generator task with no shared resource; bounded by admitted groups.',
                                 memory='One shared nonpreemptive memory server; per-tile four-BL8 reference/store jobs.',
                                 commitment='SHA cycles from frozen V82 compact-message model; digest comparisons/control cost zero beyond priced metadata.',
                                 performance_is_physical=False))
