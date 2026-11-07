#!/usr/bin/env python3
"""Bounded fresh key/P V91j-compatible input and integer residual goldens.

Exports verification data only. Does not build or run RTL. The third case is a
late inner-CRC failure, with the completed Y/U prefix retained in the golden.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tiles(plane):
    h, w = plane.shape
    return plane.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)


def semantic_cases(source):
    selected = [r for r in source if r['quant_scale'] == 16 and r['clip_id'] == 'mass-effect-legendary-combat-20s-q16']
    if not selected:
        raise ValueError('completed source must contain new-user mass-effect-legendary-combat-20s q16')
    chain = selected[0]['chain']
    sequence = [r for r in selected if r['chain'] == chain]
    assert sequence[0]['key'] and not sequence[1]['key']
    assert sequence[1]['reference_id'] == sequence[0]['frame_id']
    assert all(r['fits_49152'] for r in sequence[:2])
    return sequence[:2]


def read_components(row):
    path = Path(row['fresh_components']['path'])
    assert sha(path) == row['fresh_components']['sha256']
    with np.load(path, allow_pickle=False) as value:
        result = {name: value[name].copy() for name in value.files}
    assert hashlib.sha256(b''.join(result['plane_' + a].tobytes() for a in 'yuv')).hexdigest() == row['decoded']['canonical_sha256']
    assert hashlib.sha256(b''.join(result['coefficients_' + a].astype('<i2').tobytes() for a in 'yuv')).hexdigest() == row['decoded']['coefficient_sha256']
    return result


def packet_coefficients(packet, reader):
    """Independently decode actual new BR88 payload bytes, no historical data."""
    assert zlib.crc32(packet[:-4]) == int.from_bytes(packet[-4:], 'big')
    at = 128 + int.from_bytes(packet[36:40], 'big') + int.from_bytes(packet[40:44], 'big')
    end = at + int.from_bytes(packet[48:52], 'big')
    result = []
    for _ in range(3):
        chunks, = struct.unpack_from('>I', packet, at)
        assert chunks in (0, 1)
        at += 4
        if chunks:
            blocks, length = struct.unpack_from('>II', packet, at)
            at += 8
            decoded = reader.decode(packet[at:at + length], blocks, 1)
            result.append(np.asarray(decoded, dtype='<i2').reshape(-1, 8, 8))
            at += length
        else:
            result.append(np.empty((0, 8, 8), dtype='<i2'))
    assert at == end
    return result


def mutate_third_inner_crc(packet):
    at = 128 + int.from_bytes(packet[36:40], 'big') + int.from_bytes(packet[40:44], 'big')
    spans = []
    for axis in range(3):
        count, = struct.unpack_from('>I', packet, at)
        at += 4
        assert count == 1, 'bounded key has one nonempty BR88 chunk per plane'
        blocks, length = struct.unpack_from('>II', packet, at)
        at += 8
        assert blocks == (5144 if axis == 0 else 1331)
        assert packet[at:at + 4] == b'BR88'
        spans.append((at, length))
        at += length
    mutated = bytearray(packet[:-4])
    start, length = spans[2]
    mutated[start + length - 1] ^= 1
    return bytes(mutated) + struct.pack('>I', zlib.crc32(mutated))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cs88-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new immutable artifact directory')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report_path = args.cs88_report.resolve()
    report = json.loads(report_path.read_text())
    assert report['status'] == 'PASS_FRESH_NATIVE_CS88_PARITY' and report['profile'] == 'v91-group3'
    parent = report_path.parent
    frames_path = parent / 'frames.jsonl'
    source = [json.loads(line) for line in frames_path.read_text().splitlines()]
    selected = semantic_cases(source)
    qcodec_path = ROOT / 'scripts/cu66-v87/quantizer_codec.py'
    model_path = ROOT / 'experiments/python-gamebub-v91j/model.py'
    reader_path = ROOT / 'experiments/python-gamebub-v88/entropy/codec.py'
    qcodec = load('v99_rtl_qcodec', qcodec_path)
    model = load('v99_rtl_inverse_model', model_path)
    reader = load('v99_rtl_br88_reader', reader_path)
    dct, quantizers = model.tables()
    dct = np.asarray(dct, dtype=np.int64)
    quantizers = np.asarray(quantizers, dtype=np.int64)
    paths = [Path(__file__).resolve(), qcodec_path, model_path, model.CONSTANTS, reader_path,
             ROOT / 'fpga/experiments/cu66-v91j/tb_pipeline.cpp',
             ROOT / 'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv',
             ROOT / 'experiments/python-gamebub-v88/wire/receiver.cpp']
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for path in paths:
        dest = out / 'sources' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    receipt = dict(schema='v99-fresh-v91j-rtl-facing-goldens-v1', status='FAIL', argv=sys.argv,
                   source_sha256=pins, cs88_report=dict(path=str(report_path), sha256=sha(report_path)),
                   frames_jsonl_sha256=sha(frames_path), selected=[], max_cases=3, max_source_frames=2,
                   actual_RTL_run=False, terminal_RTL_verdict=None,
                   scope='Bounded new-user q16 key/P portable input; independent signed integer dequant/Q14-IDCT residual computation, checked against fresh normalized native-verified planes.',
                   exclusions=['No new RTL compile/simulation.', 'No complete RGB565/HUD/C2/shared-service RTL publication proof.',
                               'No FPGA Hz, physical timing, memory mapping, or active transport capability assignment.'])
    case_rows, transform_rows, current_cache, previous_planes = [], [], None, None
    material = []
    try:
        for ordinal, row in enumerate(selected):
            packet_path = parent / row['packet_path']
            packet = packet_path.read_bytes()
            assert sha(packet_path) == row['packet_sha256'] and len(packet) <= 49152
            assert packet[:8] == b'CS88\x01' + bytes([int(row['key']), 16, 0 if row['key'] else 3])
            value = read_components(row)
            actual_coefficients = packet_coefficients(packet, reader)
            operations = value['operations'].tolist()
            mode_bytes = int.from_bytes(packet[36:40], 'big')
            qbytes = int.from_bytes(packet[40:44], 'big')
            qblock = packet[128 + mode_bytes:128 + mode_bytes + qbytes]
            assert qblock[5] in (2, 6)
            prior_cache = current_cache
            current_cache = qcodec.decode(qblock, operations, None if row['key'] else prior_cache)
            ident = f'fresh_q16_{"key" if row["key"] else "P"}'
            dense_hex = []
            offset = 0
            plane_golds = []
            inverse_planes = []
            for axis, name in enumerate('yuv'):
                c = value['coefficients_' + name].reshape(-1, 8, 8).astype(np.int64)
                plane = value['plane_' + name]
                count = len(c)
                op = np.asarray(operations[offset:offset + count])
                active = np.flatnonzero(op == 2)
                cells = (active // 90 // 2) * 45 + active % 90 // 2 if axis == 0 else active
                scales = np.asarray(current_cache, dtype=np.int64)[cells]
                coefficients = c[active]
                assert np.array_equal(coefficients, actual_coefficients[axis]), 'fresh dense coefficients equal independently decoded actual BR88 bytes'
                dequant = coefficients * quantizers[int(axis != 0), scales]
                middle = (np.matmul(dequant, dct) + 8192) // 16384
                residual = (np.matmul(dct.T, middle) + 8192) // 16384
                assert np.all(dequant >= -(1 << 19)) and np.all(dequant < (1 << 19))
                assert np.all(residual >= -(1 << 23)) and np.all(residual < (1 << 23))
                prediction = np.full_like(tiles(plane), 128, dtype=np.int64) if row['key'] else tiles(previous_planes[axis]).astype(np.int64)
                reconstructed = prediction.copy()
                reconstructed[op == 1] = 128
                reconstructed[active] = np.clip(prediction[active] + residual, 0, 255)
                assert np.array_equal(reconstructed.astype('u1'), tiles(plane)), 'independent residual-to-normalized native golden parity'
                inverse_planes.append(dict(axis=axis, active_tiles=len(active),
                                           coefficient_sha256=hashlib.sha256(coefficients.astype('<i2').tobytes()).hexdigest(),
                                           dequant_signed32le_sha256=hashlib.sha256(dequant.astype('<i4').tobytes()).hexdigest(),
                                           residual_signed32le_sha256=hashlib.sha256(residual.astype('<i4').tobytes()).hexdigest(),
                                           normalized_plane_sha256=hashlib.sha256(plane.tobytes()).hexdigest()))
                dense_hex.append(coefficients.astype('<i2').tobytes().hex() or '-')
                for block, tile in enumerate(active):
                    line = (f'{ident}\t{axis}\t{block}\t{tile}\t{cells[block]}\t{scales[block]}\t'
                            f'{coefficients[block].astype("<i2").tobytes().hex()}\t'
                            f'{dequant[block].astype("<i4").tobytes().hex()}\t'
                            f'{residual[block].astype("<i4").tobytes().hex()}\n')
                    transform_rows.append(line)
                    plane_golds.append((axis, line))
                offset += count
            predecessor = selected[ordinal - 1] if ordinal else None
            columns = [ident, '0', packet.hex(), str(int(not row['key'])),
                       str(predecessor['frame_id'] if predecessor else 0), str(predecessor['generation'] if predecessor else 0),
                       str(int(not row['key'])), str(predecessor['frame_id'] if predecessor else 0),
                       str(predecessor['generation'] if predecessor else 0),
                       bytes(prior_cache).hex() if prior_cache is not None else '-', bytes(current_cache).hex(),
                       bytes(operations).hex(), *dense_hex]
            assert len(columns) == 15
            case_rows.append('\t'.join(columns) + '\n')
            material.append((packet, columns, plane_golds))
            receipt['selected'].append(dict(id=ident, chain=row['chain'], clip_id=row['clip_id'], frame_id=row['frame_id'],
                                            packet_sha256=row['packet_sha256'], fresh_components=row['fresh_components'],
                                            active_tiles=sum(op == 2 for op in operations), verified_normalized_pixels=518400,
                                            inverse_planes=inverse_planes))
            previous_planes = [value['plane_' + a] for a in 'yuv']
        packet, columns, plane_golds = material[0]
        bad = mutate_third_inner_crc(packet)
        assert zlib.crc32(bad[:-4]) == int.from_bytes(bad[-4:], 'big')
        columns = columns.copy()
        columns[0], columns[1], columns[2], columns[14] = 'fresh_q16_late_inner_crc', '147', bad.hex(), '-'
        case_rows.append('\t'.join(columns) + '\n')
        for axis, line in plane_golds:
            if axis < 2:
                transform_rows.append(line.replace('fresh_q16_key\t', 'fresh_q16_late_inner_crc\t', 1))
        for name, lines in [('cases.tsv', case_rows), ('transform_tiles.tsv', transform_rows)]:
            raw = ''.join(lines).encode('ascii')
            packed = gzip.compress(raw, compresslevel=9, mtime=0)
            path = out / (name + '.gz')
            path.write_bytes(packed)
            assert gzip.decompress(packed) == raw
            receipt.setdefault('vectors', {})[name] = dict(path=path.name, records=len(lines), bytes=len(raw),
                                                          sha256=hashlib.sha256(raw).hexdigest(), gzip_sha256=sha(path))
        assert pins == {str(p.relative_to(ROOT)): sha(p) for p in paths}
        assert len(case_rows) == 3
        receipt.update(status='PASS_BOUNDED_FRESH_RTL_FACING_GOLDENS', verification='518400 normalized pixels per fresh frame exactly match fresh components already independently accepted by frozen native CS88; all active dequant signed20/residual signed24 bounds checked',
                       testbench_contract='Existing V91j 15-column case grammar and 9-column transform grammar; key/P/late-inner-CRC fixture shapes available. Generated input is unexecuted RTL stimulus.')
    except BaseException as error:
        receipt['failure'] = repr(error)
        raise
    finally:
        receipt['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file()}
        (out / 'results.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('V99_RTL_FACING_GOLDENS', out / 'results.json', receipt['status'])


if __name__ == '__main__':
    main()
