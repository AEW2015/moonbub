#!/usr/bin/env python3
"""Retain actual prior native key/delta candidate requests for controller replay."""
import gzip
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
AREA = Path(__file__).resolve().parent
ATTEMPT = ROOT / 'fpga/experiments/cu66-v91l-rows/comparison-attempts/20261106T231139409747Z-2dd7b637'
REPORT_SHA = '73286b38fb62dc667213d143005a4315a9cf661c96b19677e02310dccf261704'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def native_address(pos):
    if pos >= 518400:
        return pos
    plane = 0 if pos < 345600 else 1 if pos < 432000 else 2
    base = (0, 345600, 432000)[plane]
    width = (720, 360, 360)[plane]
    tile, index = divmod(pos - base, 64)
    y = (tile // (width // 8)) * 8 + index // 8
    x = (tile % (width // 8)) * 8 + index % 8
    return base + y * width + x


def main():
    report_path = ATTEMPT / 'results.json'
    assert sha(report_path.read_bytes()) == REPORT_SHA
    report = json.loads(report_path.read_text())
    assert report['status'] == 'PASS_EXACT_X16_PRICED_TILE_ROW_WRITES'
    mode = next(m for m in report['modes'] if m['name'] == 'rows')
    bus_info = mode['compressed_artifacts']['bus-rows.bin']
    actual_info = mode['compressed_artifacts']['actual-rows.tsv']
    bus_path = ATTEMPT / bus_info['path']
    actual_path = ATTEMPT / actual_info['path']
    assert sha(bus_path.read_bytes()) == bus_info['gzip_sha256']
    assert sha(actual_path.read_bytes()) == actual_info['gzip_sha256']
    actual_raw = gzip.decompress(actual_path.read_bytes())
    assert sha(actual_raw) == actual_info['raw_sha256']
    banks = {}
    for line in actual_raw.decode().splitlines():
        name, profile, data = line.split('\t')
        if profile == '0' and name.startswith('accepted_'):
            banks[name.removeprefix('accepted_')] = bytes.fromhex(data)
    chosen = {r['fid']: r for r in mode['live_rows'] if r['profile'] == 0}
    assert set(chosen) == {0, 1}
    counts = {fid: 0 for fid in chosen}
    frame_bytes = {fid: bytearray(560640) for fid in chosen}
    frame_seen = {fid: bytearray(560640) for fid in chosen}
    raw_digest = hashlib.sha256()
    requests = bytearray()
    fid_order = []
    with gzip.open(bus_path, 'rb') as source:
        while True:
            block = source.read(32 * 32768)
            if not block:
                break
            assert len(block) % 32 == 0
            raw_digest.update(block)
            for kind, profile, bank, size, fid, epoch, token, addr, value, cycle in struct.iter_unpack('<BBBBIIIIQI', block):
                if kind != 0 or profile != 0:
                    continue
                row = chosen[fid]
                assert bank == row['accepted_bank'] and bank < 3 and size == 8
                assert epoch == row['epoch'] and addr % 8 == 0 and addr + 8 <= 560640
                assert addr == native_address(counts[fid] * 8)
                data = value.to_bytes(8, 'little')
                expected = banks[row['pipeline_id']]
                assert len(expected) == 560640 and expected[addr:addr + 8] == data
                assert not any(frame_seen[fid][addr:addr + 8])
                frame_seen[fid][addr:addr + 8] = bytes([1]) * 8
                frame_bytes[fid][addr:addr + 8] = data
                packed = (epoch << 118) | (token << 86) | (bank << 84) | (addr << 64) | value
                requests.extend(f'{packed:040x}\n'.encode())
                counts[fid] += 1
                if not fid_order or fid_order[-1] != fid:
                    fid_order.append(fid)
    assert raw_digest.hexdigest() == bus_info['raw_sha256']
    assert fid_order == [0, 1] and counts == {0: 70080, 1: 70080}
    frames = []
    for fid, row in sorted(chosen.items()):
        assert all(frame_seen[fid])
        expected = banks[row['pipeline_id']]
        assert frame_bytes[fid] == expected
        frames.append(dict(id=row['id'], fid=fid, epoch=row['epoch'], bank=row['accepted_bank'],
                           requests=counts[fid], bytes=560640, first_row=fid * 70080,
                           accepted_bank_sha256=sha(expected), canonical_sha256=sha(expected[:518400]),
                           semantic_hud_sha256=sha(expected[518400:]),
                           packet_root=row['root'], packet_seal=row['seal']))
    packed_path = AREA / 'vectors/native-rows.hex.gz'
    packed_path.write_bytes(gzip.compress(bytes(requests), mtime=0, compresslevel=9))
    assert gzip.decompress(packed_path.read_bytes()) == requests
    result = dict(schema='cu66-v91l-sdram-native-traffic-v1', status='PASS_SOURCE_BACKED_NATIVE_TRAFFIC',
                  scope='Actual earlier live RTL row request payload/address replay for standalone controller tests. Does not connect current reconstruction/hash/publication RTL to the controller.',
                  source_report=str(report_path.relative_to(ROOT)), source_report_sha256=REPORT_SHA,
                  source_bus_gzip_sha256=bus_info['gzip_sha256'], source_bus_raw_sha256=bus_info['raw_sha256'],
                  source_actual_banks_gzip_sha256=actual_info['gzip_sha256'], source_actual_banks_raw_sha256=actual_info['raw_sha256'],
                  generator_sha256=sha(Path(__file__).read_bytes()),
                  fixture=dict(path=str(packed_path.relative_to(ROOT)), gzip_sha256=sha(packed_path.read_bytes()),
                               raw_sha256=sha(bytes(requests)), raw_bytes=len(requests), rows=140160,
                               format='160-bit hex: data[63:0], byteaddr[83:64], logicalbank[85:84], token[117:86], epoch[149:118], upper10zero'),
                  physical_mapping='word_address=(logical_bank<<22)|(byte_address>>1); four LE16 writes per row',
                  frames=frames, current_live_codec_join=False, hardware_30fps_proven=False)
    (AREA / 'traffic-results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('NATIVE_TRAFFIC_PASS', counts, ';', len(requests), 'raw hex bytes')


if __name__ == '__main__':
    main()
