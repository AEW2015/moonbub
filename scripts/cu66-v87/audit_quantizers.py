#!/usr/bin/env python3
"""Independently audit Q87 packets against frozen V86 components and native sources."""
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'experiments/python-gamebub-v87/quantizers/attempts/20261106T142631412759Z-5847ed8e'
RESULT = RUN / 'results.json'
ROWS = RUN / 'frames.jsonl'
V86 = ROOT / 'experiments/python-gamebub-v86/wire-attempts/20261106T135235884295Z-2a73a26a'
OUT = ROOT / 'experiments/python-gamebub-v87/quantizer-audit.json'
RESIDUAL = ROOT / 'experiments/python-gamebub-v85/residual/data.py'
CONTROL = ROOT / 'experiments/python-gamebub-v86/controls/data.py'
NATIVE = ROOT / 'experiments/python-gamebub-v82/native/data.py'
C2_PATH = ROOT / 'experiments/python-gamebub-v82/execution/attempt-20261106T052617072164Z-c382bb87/g16-frames.jsonl'
V86_BUILDER = ROOT / 'scripts/cu66-v86/verify_evidence.py'


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(path.read_bytes())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def stats(values):
    return {'min': min(values), 'median': statistics.median(values),
            'max': max(values), 'total': sum(values)}


def quantizer_values(qmap):
    if len(qmap) != 338:
        raise ValueError('frozen qmap length')
    values = [(qmap[i // 4] >> (6 - 2 * (i % 4))) & 3 for i in range(1352)]
    if any(v == 3 for v in values[:1350]) or values[1350:] != [0, 0]:
        raise ValueError('frozen qmap encoding')
    return values[:1350]


def needed_mask(operations):
    if len(operations) != 8100 or any(v not in (0, 1, 2) for v in operations):
        raise ValueError('operation coverage')
    need = [False] * 1350
    for tile, op in enumerate(operations):
        if op != 2:
            continue
        if tile < 5400:
            row, col = divmod(tile, 90)
            cell = (row // 2) * 45 + col // 2
        else:
            cell = (tile - 5400) % 1350
        need[cell] = True
    return need


def packed(values):
    body = bytearray((len(values) + 3) // 4)
    for i, v in enumerate(values):
        if v not in (0, 1, 2):
            raise ValueError('quantizer value')
        body[i // 4] |= v << (6 - 2 * (i % 4))
    return bytes(body)


def rle(values):
    body = bytearray()
    i = 0
    while i < len(values):
        end = i + 1
        while end < len(values) and values[end] == values[i] and end - i < 64:
            end += 1
        body.append(values[i] * 64 + end - i - 1)
        i = end
    return bytes(body)


def method_candidates(values, needed, previous):
    active = [v for v, n in zip(values, needed) if n]
    candidates = [(0, packed(values)), (2, rle(values)), (4, packed(active)), (5, rle(active))]
    if len(set(values)) == 1:
        candidates.append((1, bytes([values[0]])))
    if active and len(set(active)) == 1:
        candidates.append((3, bytes([active[0]])))
    if previous is not None and all(not n or v == old for n, v, old in zip(needed, values, previous)):
        candidates.append((6, b''))
    return candidates


def make_qblock(method, body, needed):
    head = struct.pack('>4sBBHHH', b'QM87', 1, method, 1350, len(body), sum(needed))
    content = head + body
    return content + struct.pack('>I', zlib.crc32(content))


def decoded_map(method, values, needed, previous):
    if method == 6:
        if previous is None:
            raise ValueError('inherit without accepted map')
        return list(previous)
    if method < 3:
        return list(values)
    result, j = [0] * 1350, 0
    for i, use in enumerate(needed):
        if use:
            result[i] = values[j]
            j += 1
    if j != sum(needed):
        raise ValueError('required-only decode count')
    return result


def main():
    result = json.loads(RESULT.read_text())
    rows = lines(ROWS)
    old_rows = lines(V86 / 'frames.jsonl')
    old = {(r['configuration'], r['cohort'], r['fid']): r for r in old_rows}
    errors = []

    def require(ok, msg):
        if not ok:
            errors.append(msg)

    require(result.get('status') == 'PASS_ACTUAL_PACKETS_NATIVE_PARITY', 'campaign status')
    require(result.get('sources') == 457 and result.get('received_packets') == 914, 'source/packet counts')
    configs = [c.get('name') for c in result.get('configurations', [])]
    require(configs == ['copy_group_cap65536', 'all_visible_cap65536'], 'two selected configurations')
    require(len(rows) == 914, 'row count')
    require(set(result.get('receiver_exit_codes', {}).values()) == {0} and len(result.get('receiver_exit_codes', {})) == 2, 'receiver exit codes')

    for name, digest in result.get('source_sha256', {}).items():
        p = ROOT / name
        require(p.is_file() and sha(p) == digest, f'source pin: {name}')

    residual = load('q87_audit_residual', RESIDUAL)
    controls = load('q87_audit_controls', CONTROL)
    native = load('q87_audit_native', NATIVE)
    builder = load('q87_independent_v86_builder', V86_BUILDER)
    c2 = {(r['cohort'], r['fid']): r for r in lines(C2_PATH)}
    qualified = {(r['configuration'], r['cohort'], r['fid']): r for r in lines(V86 / 'frames.jsonl')}
    source_keys = set()
    seen = set()
    per_config = {}
    previous_maps = {}
    reconstructed = {}

    for frame, control_frame, original in zip(residual.iter_frames(), controls.iter_frames(), native.iter_frames(), strict=True):
        ident = (frame['cohort'], frame['fid'])
        source_keys.add(ident)
        require((frame['cohort'], frame['fid'], frame['ordinal'], frame['key']) ==
                (control_frame['cohort'], control_frame['fid'], control_frame['ordinal'], control_frame['key']),
                f'V86 residual/control identity {ident}')
        require((frame['cohort'], frame['fid'], frame['ordinal'], frame['key']) ==
                (original['cohort'], original['fid'], original['ordinal'], original['key']),
                f'V82 native identity {ident}')
        require(frame['qmap'] == control_frame['qmap'] and frame['hud'] == control_frame['hud'], f'V86 paired payload {ident}')
        require(frame['zero_mask'] == control_frame['zero_mask'] == ''.join(str(x) for x in original['zero_coeff_mask']), f'zero-mask join {ident}')
        control = c2[ident]
        for name in configs:
            kind = 'all_visible' if name.startswith('all_visible') else 'copy_group'
            source = control_frame if kind == 'all_visible' else frame
            key = (name, frame['cohort'])
            previous = None if frame['key'] else previous_maps.get(key)
            operations = [1 if hidden else 0 if kind != 'all_visible' and not frame['key'] and zero == '1' else 2
                          for hidden, zero in zip(original['hidden_mask'], frame['zero_mask'], strict=True)]
            needed = needed_mask(operations)
            values = quantizer_values(frame['qmap'])
            candidates = method_candidates(values, needed, previous)
            best_method, best_body = min(candidates, key=lambda item: (len(item[1]), item[0]))
            block = make_qblock(best_method, best_body, needed)
            scales = decoded_map(best_method, values, needed, previous)

            # Rebuild the frozen V86 packet with the independent V86 evidence builder,
            # then replace only its quantizer component for the CS87 profile.
            cap = 65536
            oldpacket, oldcounts, oldmethod, oldops = builder.reconstruct_packet(
                source, cap, kind, original['hidden_mask'], control)
            old_conf = f'{kind}_cap65536'
            old_row = qualified.get((old_conf, *ident))
            require(old_row is not None, f'missing independently selected V86 packet {ident}/{kind}')
            require(old_row is not None and sha_bytes(oldpacket) == old_row['packet_sha256'], f'independent V86 packet hash {ident}/{kind}')
            require(old_row is not None and len(oldpacket) == old_row['wire_bytes'], f'independent V86 packet length {ident}/{kind}')
            header = bytearray(oldpacket[:128])
            header[:4] = b'CS87'
            mode_bytes = struct.unpack_from('>I', header, 36)[0]
            struct.pack_into('>I', header, 40, len(block))
            qstart = 128 + mode_bytes
            packet_content = bytes(header) + oldpacket[128:qstart] + block + oldpacket[qstart + 338:-4]
            packet = packet_content + struct.pack('>I', zlib.crc32(packet_content))
            reconstructed[name, *ident] = packet
            require(oldmethod <= 3 and len(oldops) == 8100, f'independent builder shape {ident}/{kind}')

            row = next((r for r in rows if (r['configuration'], r['cohort'], r['fid']) == (name, *ident)), None)
            require(row is not None, f'missing Q87 row {(name, *ident)}')
            if row is None:
                continue
            row_key = (row['configuration'], row['cohort'], row['fid'])
            require(row_key not in seen, f'duplicate row {row_key}')
            seen.add(row_key)
            require(row['ordinal'] == frame['ordinal'] and row['key'] == frame['key'], f'ordinal/key mismatch {row_key}')
            require(row['q_method'] == best_method, f'method not independently shortest/tie-selected {row_key}')
            require(row['q_block_bytes'] == len(block) and row['qmap_sha256'] == sha_bytes(block), f'Q87 block mismatch {row_key}')
            require(row['needed_cells'] == sum(needed), f'needed count mismatch {row_key}')
            require(row['CS86_wire_bytes'] == len(oldpacket), f'CS86 byte count mismatch {row_key}')
            require(row['wire_bytes'] == len(packet) and row['packet_sha256'] == sha_bytes(packet), f'independent Q87 packet mismatch {row_key}')
            require(row['original_packet_bytes'] == frame['packet_bytes'], f'original packet byte source {row_key}')
            require(row['wire_bytes'] == row['CS86_wire_bytes'] - 338 + len(block), f'wire arithmetic {row_key}')
            require(row['decoded']['fid'] == frame['fid'] and row['decoded']['generation'] == frame['ordinal'] + 1, f'decoded identity {row_key}')
            require(row['decoded']['wire_bytes'] == len(packet), f'decoded wire length {row_key}')
            prior = old.get((old_conf, *ident))
            require(prior is not None, f'missing frozen V86 receiver control {row_key}')
            if prior:
                for field in ('canonical_sha256', 'hud_sha256', 'display_sha256', 'coefficient_sha256', 'root', 'seal'):
                    require(row['decoded'].get(field) == prior['decoded'].get(field), f'decoded {field} changed {row_key}')
                require(row['decoded']['fid'] == prior['decoded']['fid'] and row['decoded']['generation'] == prior['decoded']['generation'], f'V86 decoded fid/generation {row_key}')
                require(row['CS86_wire_bytes'] == prior['wire_bytes'] and row['original_packet_bytes'] == prior['original_packet_bytes'], f'V86 binding {row_key}')
            comp = row['components']
            require(sum(comp.values()) == row['wire_bytes'] and comp.get('qmap') == len(block), f'component sum {row_key}')
            require(row['wire_bytes'] <= 49152, f'compatibility size {row_key}')
            c = per_config.setdefault(name, {'rows': [], 'methods': {str(m): 0 for m in range(7)}})
            c['rows'].append(row)
            c['methods'][str(row['q_method'])] += 1
            previous_maps[key] = scales

    require(len(source_keys) == 457, 'frozen source identity count')
    require(seen == {(c, *identity) for c in configs for identity in source_keys}, 'output rows do not join exactly to 457 identities/config')
    summaries = {s['configuration']: s for s in result.get('summaries', [])}
    require(set(summaries) == set(configs), 'summary configuration set')
    independent = {}
    for config in configs:
        rr = per_config.get(config, {}).get('rows', [])
        methods = per_config.get(config, {}).get('methods', {})
        summary = summaries.get(config, {})
        wire = [r['wire_bytes'] for r in rr]
        old_sizes = [r['CS86_wire_bytes'] for r in rr]
        q_sizes = [r['q_block_bytes'] for r in rr]
        saved_old = sum(r['CS86_wire_bytes'] - r['wire_bytes'] for r in rr)
        saved_orig = sum(r['original_packet_bytes'] - r['wire_bytes'] for r in rr)
        require(len(rr) == 457, f'{config} rows != 457')
        require(summary.get('sources') == len(rr), f'{config} summary source count')
        require(summary.get('wire_bytes') == stats(wire), f'{config} wire min/median/max/total')
        require(summary.get('CS86_wire_bytes') == stats(old_sizes), f'{config} V86 min/median/max/total')
        require(summary.get('q_block_bytes') == stats(q_sizes), f'{config} q-block min/median/max/total')
        require(summary.get('saved_vs_CS86') == saved_old, f'{config} V86 savings')
        require(summary.get('saved_vs_original') == saved_orig, f'{config} original savings')
        require(summary.get('method_counts') == methods, f'{config} method counts')
        require(summary.get('fits_49152') == sum(v <= 49152 for v in wire), f'{config} fit count')
        independent[config] = {'sources': len(rr), 'wire_bytes': stats(wire),
                               'CS86_wire_bytes': stats(old_sizes), 'q_block_bytes': stats(q_sizes),
                               'saved_vs_CS86': saved_old, 'saved_vs_original': saved_orig,
                               'method_counts': methods}

    fixtures = []
    fixture_rows = [r for r in rows if r['cohort'] in (0, 3) and r['ordinal'] in (0, 1, 2)]
    for row in fixture_rows:
        name = f"c{row['cohort']}-f{row['fid']}-{row['configuration']}.cs87"
        path = RUN / name
        require(path.is_file(), f'missing retained fixture {name}')
        if not path.is_file():
            continue
        packet = path.read_bytes()
        valid = (packet == reconstructed.get((row['configuration'], row['cohort'], row['fid']))
                 and sha_bytes(packet) == row['packet_sha256'] and len(packet) == row['wire_bytes']
                 and len(packet) >= 132 and zlib.crc32(packet[:-4]) == struct.unpack('>I', packet[-4:])[0])
        mode_bytes = struct.unpack_from('>I', packet, 36)[0]
        qbytes = struct.unpack_from('>I', packet, 40)[0]
        qstart = 128 + mode_bytes
        quant_block = packet[qstart:qstart + qbytes]
        valid = valid and len(quant_block) == qbytes == row['q_block_bytes']
        valid = valid and zlib.crc32(quant_block[:-4]) == struct.unpack('>I', quant_block[-4:])[0]
        valid = valid and quant_block[:4] == b'QM87' and quant_block[4] == 1 and quant_block[5] == row['q_method']
        valid = valid and struct.unpack_from('>HHH', quant_block, 6) == (1350, qbytes - 16, row['needed_cells'])
        require(valid, f'fixture independent bytes/SHA/CRC/layout mismatch {name}')
        fixtures.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path), 'bytes': len(packet), 'layout_crc_pass': bool(valid)})

    audit = {'schema': 'cu66-v87-quantizer-independent-audit-v2',
             'status': 'PASS' if not errors else 'FAIL', 'campaign': str(RESULT.relative_to(ROOT)),
             'frozen_v86_controls': str((V86 / 'results.json').relative_to(ROOT)),
             'source_pins_checked': len(result.get('source_sha256', {})),
             'rows_checked': len(rows), 'independently_reconstructed_packets': len(reconstructed),
             'configurations': independent, 'retained_fixtures_checked': len(fixtures),
             'fixtures': fixtures, 'errors': errors}
    OUT.write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps({'status': audit['status'], 'rows_checked': len(rows),
                      'independently_reconstructed_packets': len(reconstructed),
                      'fixtures_checked': len(fixtures), 'errors': errors[:20]}, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
