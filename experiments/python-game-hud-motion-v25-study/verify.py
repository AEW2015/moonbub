#!/usr/bin/env python3
"""Independent scalar word reconstruction and actual retained-sequence replay."""
from pathlib import Path
import hashlib
import json
import struct
import zlib
import numpy as np
import benchmark as b
import model as m
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def scalar_decode(packet, reference=None):
    header = struct.Struct('<4sBBHHI16s16s')
    assert type(packet) is bytes and 50 <= len(packet) <= 42290
    magic, version, mode, w, h, nbytes, reftag, currenttag = header.unpack_from(packet)
    assert magic == b'HD25' and version == 1 and mode in range(10)
    assert 0 < w <= 720 and 0 < h <= 480 and w*h <= 21120
    assert len(packet) == 50+nbytes and nbytes <= 42240
    assert zlib.crc32(packet[:-4]) == struct.unpack('<I', packet[-4:])[0]
    n = w*h
    def tag(words):
        return hashlib.sha256(struct.pack('<HH', w, h)+struct.pack('<'+'H'*n, *words)).digest()[:16]
    payload = packet[46:-4]
    independent = mode in (0, 6, 7, 9)
    if independent:
        assert reftag == bytes(16)
        base = None
    else:
        assert reference is not None and reference.shape == (h, w)
        base = [int(v) for v in reference.flat]
        assert tag(base) == reftag

    def rle(data):
        result, pos = [], 0
        while pos < len(data):
            token = data[pos]; pos += 1
            if token < 128:
                length = token+1; assert pos+length <= len(data)
                result.extend(data[pos:pos+length]); pos += length
            elif token < 192:
                result.extend([0]*((token & 63)+1))
            else:
                assert pos < len(data) and data[pos] != 0
                result.extend([data[pos]]*((token & 63)+1)); pos += 1
            assert len(result) <= n
        assert len(result) == n
        return result

    def planes(data):
        assert len(data) >= 8
        nl, nh = struct.unpack_from('<II', data)
        assert len(data) == 8+nl+nh
        lo, hi = rle(data[8:8+nl]), rle(data[8+nl:])
        return [a | (bb << 8) for a, bb in zip(lo, hi)]

    def spans(data):
        assert len(data) >= 2
        count = struct.unpack_from('<H', data)[0]
        assert count <= n and count <= (len(data)-2)//8
        out, pos, last_y, last_end = [0]*n, 2, -1, -1
        for _ in range(count):
            assert pos+6 <= len(data)
            y, x, length = struct.unpack_from('<HHH', data, pos); pos += 6
            assert y < h and 0 < length <= w and x+length <= w and y >= last_y
            assert y != last_y or x-last_end >= 3
            assert pos+2*length <= len(data)
            values = struct.unpack_from('<'+'H'*length, data, pos); pos += 2*length
            assert values[0] and values[-1]
            gap = 0
            for i, value in enumerate(values):
                gap = gap+1 if value == 0 else 0; assert gap < 3
                out[y*w+x+i] = value
            last_y, last_end = y, x+length
        assert pos == len(data)
        return out

    def rice(data, prediction, left=False):
        assert len(data) >= 15
        kr, kg, kb, br, bg, bb = struct.unpack_from('<BBBIII', data)
        counts, ks = (br, bg, bb), (kr, kg, kb)
        assert all(k <= 5 for k in ks) and all(n <= size <= 127*n for size in counts)
        assert len(data) == 15+sum((size+7)//8 for size in counts)
        out, offset = [0]*n, 15
        for k, size, shift, maximum in zip(ks, counts, (11, 5, 0), (31, 63, 31)):
            length = (size+7)//8; stream = data[offset:offset+length]; offset += length
            assert not size % 8 or stream[-1] & ((1 << (8-size%8))-1) == 0
            bitpos, previous = 0, 0
            for index in range(n):
                quotient = 0
                while True:
                    assert bitpos < size
                    bit = (stream[bitpos//8] >> (7-bitpos%8)) & 1; bitpos += 1
                    if bit: break
                    quotient += 1; assert (quotient << k) <= 2*maximum
                remainder = 0
                for _ in range(k):
                    assert bitpos < size
                    remainder = (remainder << 1) | ((stream[bitpos//8] >> (7-bitpos%8)) & 1); bitpos += 1
                zig = (quotient << k) | remainder; assert zig <= 2*maximum
                delta = zig//2 if zig%2 == 0 else -(zig//2)-1
                pred = (0 if index%w == 0 else previous) if left else (prediction[index] >> shift) & maximum
                value = pred+delta; assert 0 <= value <= maximum
                out[index] |= value << shift
                previous = value
            assert bitpos == size
        return out

    def predict(dx, dy):
        assert -4 <= dx <= 4 and -4 <= dy <= 4
        return [base[min(h-1, max(0, y+dy))*w+min(w-1, max(0, x+dx))] for y in range(h) for x in range(w)]

    def residual(data, prediction):
        assert data and data[0] in (0, 1, 2)
        if data[0] == 2: return rice(data[1:], prediction)
        xor = spans(data[1:]) if data[0] == 0 else planes(data[1:])
        return [a ^ bb for a, bb in zip(prediction, xor)]

    if mode == 0:
        assert nbytes == 2*n
        words = list(struct.unpack('<'+'H'*n, payload))
    elif mode == 1:
        assert not nbytes; words = base.copy()
    elif mode in (2, 3):
        xor = spans(payload) if mode == 2 else planes(payload)
        words = [a ^ bb for a, bb in zip(base, xor)]
    elif mode in (6, 7):
        words = planes(payload)
        if mode == 7:
            for y in range(h):
                for x in range(1, w): words[y*w+x] ^= words[y*w+x-1]
    elif mode == 8: words = rice(payload, base)
    elif mode == 9: words = rice(payload, None, left=True)
    elif mode == 4:
        assert len(payload) >= 3
        dx, dy = struct.unpack_from('<bb', payload)
        words = residual(payload[2:], predict(dx, dy))
    else:
        assert len(payload) >= 10
        tw, th, radius, field, count = struct.unpack_from('<BBBBH', payload)
        assert (tw, th, radius) == (16, 8, 4) and field in (0, 1)
        expected = ((w+15)//16)*((h+7)//8); assert count == expected
        length = struct.unpack_from('<I', payload, 6)[0]
        assert 0 < length <= 4*count and 10+length < len(payload)
        data, vectors = payload[10:10+length], []
        if field == 0:
            assert length == 2*count
            vectors = [struct.unpack_from('<bb', data, 2*i) for i in range(count)]
        else:
            assert length%4 == 0
            for i in range(0, length, 4):
                repeat, dx, dy = struct.unpack_from('<Hbb', data, i)
                assert repeat and len(vectors)+repeat <= count
                assert not vectors or vectors[-1] != (dx, dy)
                vectors.extend([(dx, dy)]*repeat)
            assert len(vectors) == count
        pred, index = [0]*n, 0
        for y in range(0, h, 8):
            for x in range(0, w, 16):
                dx, dy = vectors[index]; index += 1
                assert -4 <= dx <= 4 and -4 <= dy <= 4
                for yy in range(y, min(y+8, h)):
                    for xx in range(x, min(x+16, w)):
                        pred[yy*w+xx] = base[min(h-1,max(0,yy+dy))*w+min(w-1,max(0,xx+dx))]
        words = residual(payload[10+length:], pred)
    assert tag(words) == currenttag
    return np.asarray(words, np.uint16).reshape(h, w)


def main():
    data = b.load(HERE/'results.json')
    for path, digest in data['source_sha256'].items(): assert b.sha(ROOT/path) == digest, path
    old = b.load(b.OLD/'results.json')
    words = decisions = 0
    for source_case, case in zip(old['cases'], data['cases']):
        assert source_case['name'] == case['name']
        confirmed = None
        rebuilt, _ = b.run_case(source_case, export=False)
        for key, value in case['summary'].items():
            if 'encode_ms' not in key: assert rebuilt['summary'][key] == value, (case['name'], key)
        for source, row in zip(source_case['rows'], case['rows']):
            current = b.arrays(source)
            for i, (array, detail) in enumerate(zip(current, row['patches'])):
                ref = None if confirmed is None else confirmed[i]
                packet = m.encode(array, ref)
                assert hashlib.sha256(packet).hexdigest() == detail['packet_sha256']
                np.testing.assert_array_equal(scalar_decode(packet, ref), array)
                assert len(packet) == detail['hd25_bytes'] <= detail['no_motion_bytes'] <= detail['hd22_bytes']
                words += array.size; decisions += 1
            assert row['new_hud_bytes'] == 83+sum(p['selected_bytes'] for p in row['patches'])
            assert row['new_hud_bytes'] <= row['no_motion_hud_bytes'] <= row['old_hud_bytes']
            confirmed = current
    negatives = 0
    for vector in data['goldens']:
        cur = np.frombuffer(b.raw(vector['current'], HERE), dtype='<u2').reshape(vector['shape'])
        ref = None if vector['reference'] is None else np.frombuffer(b.raw(vector['reference'], HERE), dtype='<u2').reshape(vector['shape'])
        packet = b.raw(vector['packet'], HERE)
        np.testing.assert_array_equal(scalar_decode(packet, ref), cur)
        try: scalar_decode(packet[:-1]+bytes([packet[-1]^1]), ref)
        except AssertionError: negatives += 1
        else: raise AssertionError('badCRC accepted')
    controls = 0
    for case in data['controls']:
        for row in case['rows']:
            cur = np.frombuffer(b.raw(row['current'], HERE), dtype='<u2').reshape(row['shape'])
            ref = None if row['reference'] is None else np.frombuffer(b.raw(row['reference'], HERE), dtype='<u2').reshape(row['shape'])
            np.testing.assert_array_equal(scalar_decode(b.raw(row['packet'], HERE), ref), cur)
            controls += 1
    assert (decisions, words, controls) == (528, 2787840, 24)
    print(json.dumps(dict(replayed_patch_candidates=decisions, independent_scalar_words=words,
                          extra_synthetic_controls=controls, golden_vectors=len(data['goldens']),
                          crc_negative_rejections=negatives, physical_30fps_proven=False), indent=2))


if __name__ == '__main__': main()
