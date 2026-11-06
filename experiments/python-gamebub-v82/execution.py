"""COPY-aware execution accounting; no elapsed FPGA time is simulated here."""
from __future__ import annotations
import math

TILES = 8100
HUD_BLOCKS = 2640
FULL_SHA_BLOCKS = (518400 + 4 + 9 + 63) // 64


def service_floor(reads, writes):
    """Conditional frozen bridge floor, omitting the last successor interval."""
    if reads + writes == 0:
        return 0
    return reads * 18 + writes * 16 - (18 if reads else 16)


def hash_compute_bounds(jobs, lanes):
    """Necessary work/dependency bounds for the assumed non-pipelined engines."""
    finish = {}
    for job in jobs:
        finish[job['id']] = job['cycles'] + max((finish[d] for d in job['deps']), default=0)
    return max(math.ceil(sum(j['cycles'] for j in jobs) / lanes), max(finish.values(), default=0))


def metadata_accounting(plan, key, stores):
    """Price the software plan's full shadow copy, comparisons and digest I/O.

    Assumptions: two digest trees, 32-bit tree words; separate 3-bit map entries.
    External-tree BL8 accounting uses aligned 32-byte digest objects. It omits
    row misses, refresh and masks (masks remain on chip in that scenario).
    """
    nodes = 2 * plan['memory']['padded_leaves'] - 1
    clone_nodes = 0 if key else nodes
    reads = clone_nodes * 8
    writes = clone_nodes * 8
    for job in plan['jobs']:
        if job['kind'] == 'seal':
            reads += 8
        else:
            reads += (16 if job['kind'] == 'internal' else 0)
            reads += 0 if key else 8  # old digest comparison
            writes += 8
    assert reads % 4 == writes % 4 == 0
    return dict(tree_clone_nodes=clone_nodes, tree_read_words32=reads,
                tree_write_words32=writes, map_read_entries=TILES,
                map_write_entries=TILES + stores,
                onchip_tree_port_floor_cycles=max(reads, writes),
                onchip_separate_map_port_floor_cycles=max(TILES, TILES + stores),
                external_tree_BL8_reads=reads // 4,
                external_tree_BL8_writes=writes // 4,
                assumptions='One shared 32-bit tree read and write per clock; separate map read/write port. External case keeps maps on chip. No fit or schedule proof.')


def account(frame, elided, plan):
    key = bool(frame['key'])
    hidden = frame['hidden_mask']
    copy = frame['copy_ref_mask']
    assert len(elided) == len(hidden) == len(copy) == TILES
    assert all(not c or (not key and not h) for c, h in zip(copy, hidden))
    dirty_tiles = {i for group in plan['recomputed_groups'] for i in group['tile_indices']}
    decoded_ref = set()
    copied_ref = set()
    hash_only_ref = set()
    for i in range(TILES):
        if key or hidden[i]:
            continue
        if not copy[i]:
            decoded_ref.add(i)
        elif not elided[i]:
            copied_ref.add(i)
        elif i in dirty_tiles:
            hash_only_ref.add(i)
    assert not (decoded_ref & copied_ref or decoded_ref & hash_only_ref or copied_ref & hash_only_ref)
    ref_tiles = len(decoded_ref | copied_ref | hash_only_ref)
    stores = TILES - sum(elided)
    metadata = metadata_accounting(plan, key, stores)
    reads = ref_tiles * 4 + HUD_BLOCKS
    writes = stores * 4 + HUD_BLOCKS
    external_reads = reads + metadata['external_tree_BL8_reads']
    external_writes = writes + metadata['external_tree_BL8_writes']
    eager_ref = 0 if key else TILES * 4
    visible_ref = 0 if key else (TILES - sum(hidden)) * 4
    return dict(
        cohort=frame['cohort'], fid=frame['fid'], generation=frame['generation'], key=key,
        granularity=plan['granularity'] if 'granularity' in plan else None,
        copy_tiles=sum(copy), const_tiles=sum(hidden), resident_store_elisions=sum(elided),
        physical_store_tiles=stores,
        decode_reference_tiles=len(decoded_ref), materialize_copy_reference_tiles=len(copied_ref),
        mixed_leaf_hash_only_reference_tiles=len(hash_only_ref), reference_read_tiles=ref_tiles,
        logical_BL8=dict(reference_reads=ref_tiles * 4, canonical_writes=stores * 4,
                         HUD_reads=HUD_BLOCKS, HUD_writes=HUD_BLOCKS, total=reads + writes),
        controls=dict(
            v81_full_store_eager_reads=eager_ref + HUD_BLOCKS,
            v81_full_store_writes=TILES * 4 + HUD_BLOCKS,
            resident_full_SHA_eager_reads=eager_ref + HUD_BLOCKS,
            resident_full_SHA_writes=writes,
            copy_aware_full_SHA_reads=visible_ref + HUD_BLOCKS,
            copy_aware_full_SHA_writes=writes,
            flat_canonical_SHA_compression_blocks=FULL_SHA_BLOCKS),
        hash_compression_blocks=plan['compression_blocks'],
        hash_isolated_list_schedule_cycles={str(k): v for k, v in plan['lane_cycles'].items()},
        hash_necessary_compute_bound_cycles={str(n): hash_compute_bounds(plan['jobs'], n) for n in (1, 2, 4)},
        metadata=metadata,
        group_payload_buffer_bytes=max((g['count'] * 64 for g in plan['recomputed_groups']), default=0),
        memory=plan['memory'],
        conditional_data_service_floor_cycles=service_floor(reads, writes),
        external_tree_scenario=dict(
            reads=external_reads, writes=external_writes,
            total_BL8=external_reads + external_writes,
            conditional_service_floor_cycles=service_floor(external_reads, external_writes)),
        costs_not_priced=['LCD scanout', 'row changes/refresh', 'ESP32 ingress/packet decode',
                          'entropy/dequant/inverse/reconstruction', 'hash input arrival and ports',
                          'target clock/fit/CDC', 'CPU HUD/control and commit scheduling'])
