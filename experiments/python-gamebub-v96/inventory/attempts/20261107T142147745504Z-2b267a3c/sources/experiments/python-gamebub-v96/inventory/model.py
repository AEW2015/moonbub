"""Addressed exact V96 research records; deliberately not a deployed CU66 wire.

No aliases: every descriptor writes one 64-byte destination tile. Dictionaries
contain positions in one accepted frame, never candidate bytes.
"""
import collections
import hashlib
import json
import struct

COUNTS = (5400, 1350, 1350)
BASES = (0, 345600, 432000)
STARTS = (0, 5400, 6750)
WIDTHS = (720, 360, 360)
BANK_STRIDE = 1 << 23
CONST = bytes([128]) * 64
FALLBACK, COPY_REF, CONST128, CROSSCOPY = range(4)
OPS = ('FALLBACK', 'COPY_REF', 'CONST128', 'CROSSCOPY')
PROFILES = {'control': 0, 'cross64': 64, 'cross256': 256}
MAGIC = b'V96RS01\0'
RECORD = struct.Struct('<BBHHBBIIII')
NONE = 0xffffffff


def require(value, message):
    if not value:
        raise ValueError(message)


def physical_byte(logical):
    """Independent Python spelling of the frozen tiled row bridge function."""
    if logical >= 518400:
        return logical
    plane = 0 if logical < 345600 else 1 if logical < 432000 else 2
    y, x = divmod(logical - BASES[plane], WIDTHS[plane])
    return BASES[plane] + ((y // 8) * (WIDTHS[plane] // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8


def address(plane, tile, bank):
    require(0 <= plane < 3 and 0 <= tile < COUNTS[plane] and 0 <= bank < 3, 'address bound')
    relative = tile * 64
    return relative, bank * BANK_STRIDE + BASES[plane] + relative


def raster_digest(tiles):
    h = hashlib.sha256()
    for plane, (start, count, width) in enumerate(zip(STARTS, COUNTS, WIDTHS)):
        across = width // 8
        for row in range(count // across):
            for y in range(8):
                h.update(b''.join(tiles[start + row * across + x][y*8:y*8+8] for x in range(across)))
    return h.hexdigest()


def dictionaries(tiles, slots):
    """FIFO of distinct byte strings, first position kept until FIFO eviction.

    Ascending scan is exactly 8100 tiles / 518400 byte comparisons-input. A
    duplicate does not refresh FIFO order. A rebuild occurs only on acceptance.
    Host exact-byte hashing is an implementation convenience, not RTL service.
    """
    require(slots in (0, 64, 256), 'dictionary size')
    out = []
    for start, count in zip(STARTS, COUNTS):
        entries = collections.OrderedDict()
        if slots:
            for pos in range(count):
                tile = tiles[start + pos]
                if tile not in entries:
                    if len(entries) == slots:
                        entries.popitem(last=False)
                    entries[tile] = pos
        out.append(dict(entries))
    return out


def header(frame, profile, dst_bank, src_bank):
    return dict(schema='v96-addressed-research-stream-1', profile=profile,
                cohort=frame['cohort'], ordinal=frame['ordinal'], fid=frame['fid'],
                refid=frame['refid'], key=frame['key'], accepted_fid=frame.get('previous_fid'),
                epoch=frame['cohort']+1, destination_generation=frame['ordinal']+1,
                accepted_generation=None if src_bank is None else frame['ordinal'],
                canonical_sha256=frame['canonical_sha256'], tile_count=8100,
                plane_counts=list(COUNTS), plane_bases=list(BASES), bank_stride_bytes=BANK_STRIDE,
                destination_bank=dst_bank, source_bank=src_bank,
                dictionary_slots_per_plane=PROFILES[profile], dictionary_scan_budget_tiles=list(COUNTS),
                dictionary_policy='accepted-frame-only; ascending FIFO distinct bytes; no duplicate refresh',
                descriptor_format='<BBHHBBIIII', descriptor_bytes=RECORD.size,
                fields=['op','plane','dst_tile_local','src_tile_local_or_65535','dst_bank','src_bank_or_255',
                        'dst_plane_physical_byte','dst_global_physical_byte','src_plane_physical_byte_or_ffffffff','src_global_physical_byte_or_ffffffff'],
                operations=list(OPS), fallback_payload_bytes=64, tile_bytes=64,
                source_sentinel=NONE, no_sameframe_dependencies=True,
                qualification='Research descriptors and frozen canonical fallback bytes; no entropy coding or compression claim')


def encode(frame, accepted, profile, dst_bank, src_bank, index=None):
    require(profile in PROFILES, 'profile')
    require(accepted is not None or src_bank is None, 'initial source bank')
    index = dictionaries(accepted['tiles'], PROFILES[profile]) if index is None and accepted else index
    h = header(frame, profile, dst_bank, src_bank)
    meta = json.dumps(h, sort_keys=True, separators=(',', ':')).encode()
    body = bytearray()
    stats = dict(ops={name: 0 for name in OPS}, search_queries=0, search_hits=0,
                 exact_tile_comparison_budget_bytes=0, candidate_slots_inspected_upper_bound=0)
    for plane, (start, count) in enumerate(zip(STARTS, COUNTS)):
        for pos in range(count):
            tile = start + pos
            payload = frame['tiles'][tile]
            op, source = FALLBACK, None
            if frame['hidden_mask'][tile]:
                require(payload == CONST, 'hidden value')
                op = CONST128
            elif frame['copy_ref_mask'][tile]:
                require(not frame['key'] and accepted and accepted['tiles'][tile] == payload, 'invalid COPY_REF')
                op, source = COPY_REF, pos
            elif not frame['key'] and accepted and PROFILES[profile]:
                stats['search_queries'] += 1
                stats['exact_tile_comparison_budget_bytes'] += 64*PROFILES[profile]
                stats['candidate_slots_inspected_upper_bound'] += PROFILES[profile]
                candidate = index[plane].get(payload)
                if candidate is not None and candidate != pos:
                    require(accepted['tiles'][start+candidate] == payload, 'dictionary payload')
                    op, source = CROSSCOPY, candidate
                    stats['search_hits'] += 1
            dst_rel, dst_global = address(plane, pos, dst_bank)
            src_rel, src_global = (NONE, NONE) if source is None else address(plane, source, src_bank)
            body.extend(RECORD.pack(op, plane, pos, 65535 if source is None else source,
                                    dst_bank, 255 if source is None else src_bank,
                                    dst_rel, dst_global, src_rel, src_global))
            if op == FALLBACK:
                body.extend(payload)
            stats['ops'][OPS[op]] += 1
    stream = MAGIC + struct.pack('<II', len(meta), 8100) + meta + body
    stats.update(stream_bytes=len(stream), header_bytes=16+len(meta),
                 descriptor_bytes=8100*RECORD.size, fallback_bytes=stats['ops']['FALLBACK']*64)
    require(stats['stream_bytes'] == stats['header_bytes']+stats['descriptor_bytes']+stats['fallback_bytes'], 'byte accounting')
    copies = stats['ops']['COPY_REF'] + stats['ops']['CROSSCOPY']
    # Named fence excludes host encoder search, fallback precompute and scanout.
    # Includes each materialized tile write and each COPY/CROSSCOPY source read.
    stats['materialization_fence'] = dict(name='canonical_candidate_tiles_drained_before_publication',
        source_read_bytes=copies*64, destination_write_bytes=8100*64,
        source_read_words16=copies*32, destination_write_words16=8100*32,
        copy_source_read_bytes=copies*64, copy_destination_write_bytes=copies*64,
        const_generated_bytes=stats['ops']['CONST128']*64)
    return stream, stats


def parse(stream):
    require(stream[:8] == MAGIC and len(stream) >= 16, 'research magic')
    length, count = struct.unpack_from('<II', stream, 8)
    require(1 <= length <= 8192 and count == 8100, 'header bounds')
    require(len(stream) >= 16+length, 'truncated header')
    h = json.loads(stream[16:16+length])
    require(h['schema'] == 'v96-addressed-research-stream-1' and h['descriptor_format'] == RECORD.format, 'header grammar')
    require(h['profile'] in PROFILES and h['plane_counts'] == list(COUNTS) and h['plane_bases'] == list(BASES) and h['bank_stride_bytes'] == BANK_STRIDE, 'geometry grammar')
    require(h['tile_count'] == 8100 and h['descriptor_bytes'] == RECORD.size and h['tile_bytes'] == 64 and h['operations'] == list(OPS) and h['fallback_payload_bytes'] == 64 and h['source_sentinel'] == NONE, 'tile grammar')
    require(type(h['epoch']) is int and 0 < h['epoch'] < 2**32 and type(h['destination_generation']) is int and 0 < h['destination_generation'] < 2**64, 'generation grammar')
    require(h['accepted_generation'] is None if h['source_bank'] is None else type(h['accepted_generation']) is int and 0 < h['accepted_generation'] < 2**64, 'accepted generation grammar')
    cursor = 16+length
    records = []
    for plane, tile_count in enumerate(COUNTS):
        for pos in range(tile_count):
            require(cursor+RECORD.size <= len(stream), 'truncated descriptor')
            rec = RECORD.unpack_from(stream, cursor)
            cursor += RECORD.size
            op, axis, dst, src, db, sb, dr, dg, sr, sg = rec
            require(op in range(4) and (axis,dst,db) == (plane,pos,h['destination_bank']), 'descriptor order/op')
            require((dr,dg) == address(plane,pos,db), 'destination address')
            if op in (COPY_REF,CROSSCOPY):
                require(not h['key'] and h['source_bank'] is not None and sb == h['source_bank'] and sb != db, 'source ownership')
                require((sr,sg) == address(plane,src,sb), 'source address')
                require((src == dst) == (op == COPY_REF), 'copy position')
            else:
                require((src,sb,sr,sg) == (65535,255,NONE,NONE), 'source sentinel')
            payload = None
            if op == FALLBACK:
                require(cursor+64 <= len(stream), 'truncated fallback')
                payload = stream[cursor:cursor+64]
                cursor += 64
            records.append((rec,payload))
    require(cursor == len(stream), 'extra bytes')
    return h, records


def materialize(stream, accepted):
    h, records = parse(stream)
    if accepted is not None:
        require(h['accepted_fid'] == accepted['fid'], 'accepted identity')
        if not h['key']:
            require(h['refid'] == accepted['fid'], 'reference identity')
    else:
        require(h['key'] and h['source_bank'] is None, 'initial key required')
    tiles = []
    for rec, payload in records:
        op, plane, dst, src = rec[:4]
        if op in (COPY_REF,CROSSCOPY):
            require(accepted is not None, 'source missing')
            payload = accepted['tiles'][STARTS[plane]+src]
        elif op == CONST128:
            payload = CONST
        tiles.append(payload)
    require(raster_digest(tiles) == h['canonical_sha256'], 'canonical SHA mismatch')
    return h, tiles
