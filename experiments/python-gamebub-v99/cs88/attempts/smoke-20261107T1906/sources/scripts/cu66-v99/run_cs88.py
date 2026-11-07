#!/usr/bin/env python3
"""Compose actual all-BR88 CS88 from fresh accepted CU66 components.

The unchanged CS88 native receiver independently reconstructs and checks every
new packet. The diagnostic receiver admits 2 MiB; 49152-byte eligibility is
reported separately for complete causal chains, never simulated by dropping a
packet and advancing its reference or QM87 cache.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import time
import uuid
import zlib

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v99/cs88'
CONTAINER = 'gamebub-cu66-v69-build'
CAP = 49152
RESEARCH_CAP = 2 * 1024 * 1024
PREFIX = struct.Struct('>4sBBBBIIQHHHHIIIII')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def run_command(command, out, report, name):
    result = subprocess.run(command, capture_output=True)
    (out / (name + '.log')).write_bytes(result.stdout + result.stderr)
    report['commands'].append(dict(argv=command, exit_code=result.returncode))
    if result.returncode:
        raise RuntimeError(f'{name} failed; retained {out / (name + ".log")}')
    return result.stdout


def prepare_binaries(out, report, container):
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    report['compiler_version'] = run_command(
        ['docker', 'exec', container, 'g++', '--version'], out, report, 'compiler-version').decode()
    identity = json.loads(run_command(['docker', 'inspect', container], out, report, 'container-inspect'))[0]
    report['container'] = dict(name=container, id=identity['Id'], image_id=identity['Image'])
    paths = {}
    for name, source in [('encode_dense', AREA / 'encode_dense.cpp'),
                         ('receiver', ROOT / 'experiments/python-gamebub-v88/wire/receiver.cpp')]:
        binary = f'/build/v99-cs88-{name}-{stamp}-{uuid.uuid4().hex[:8]}'
        run_command(['docker', 'exec', container, 'g++', '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                     str(source), '-o', binary], out, report, 'compile-' + name)
        # Retain binaries outside Git; hash a stream from that immutable path.
        digest = run_command(['docker', 'exec', container, 'sha256sum', binary], out, report, 'hash-' + name)
        paths[name] = binary
        report.setdefault('binaries', {})[name] = dict(path=binary, sha256=digest.decode().split()[0])
    return paths


def components(record):
    if isinstance(record.get('rtl_components'), dict):
        value = record['rtl_components']
        return dict(coefficients=[np.asarray(a).reshape(-1, 64) for a in value['coefficients']],
                    planes=[np.asarray(a) for a in value['normalized_planes']],
                    qmap=bytes(value['packed_qmap']), hud=bytes(value['hud_envelope']),
                    operations=np.asarray(value['operations']).reshape(-1).tolist(),
                    block_size=int(value['block_size']))
    path = Path(record['rtl_components_path'])
    with np.load(path, allow_pickle=False) as value:
        return dict(coefficients=[value['coefficients_' + axis].copy().reshape(-1, 64) for axis in 'yuv'],
                    planes=[value['plane_' + axis].copy() for axis in 'yuv'],
                    qmap=value['qmap'].astype('u1').tobytes(), hud=value['hud'].astype('u1').tobytes(),
                    operations=value['operations'].astype('u1').tolist(), block_size=int(value['block_size']))


def tile_bytes(planes):
    result = []
    for axis, plane in enumerate(planes):
        height, width = (240, 360) if axis else (480, 720)
        a = np.asarray(plane)
        if a.shape != (height, width) or np.any(a < 0) or np.any(a > 255):
            raise ValueError('normalized plane shape/range')
        tiles = a.astype('u1').reshape(height // 8, 8, width // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
        result.extend(tile.tobytes() for tile in tiles)
    return result


class Native:
    def __init__(self, command, stderr):
        self.log = stderr.open('wb')
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.log)

    def receive(self, cohort, packet):
        self.process.stdin.write(struct.pack('>II', cohort, len(packet)) + packet)
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError(f'native receiver ended: {self.process.poll()}')
        return json.loads(line)

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            code = self.process.wait()
        else:
            code = self.process.returncode
        self.log.close()
        if code:
            raise RuntimeError(f'native process exit {code}')

    def abort(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.log.close()


class DenseEncoder(Native):
    def encode(self, coefficients):
        a = np.asarray(coefficients).reshape(-1, 64)
        if not 1 <= len(a) <= 5400 or np.any(a < -2048) or np.any(a > 2048):
            raise ValueError('fresh coefficient geometry/range')
        self.process.stdin.write(struct.pack('<I', len(a)) + a.astype('<i2').tobytes())
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError('dense encoder ended')
        metrics = json.loads(line)
        head = self.process.stdout.read(4)
        if len(head) != 4:
            raise RuntimeError('dense encoder truncated length')
        length, = struct.unpack('<I', head)
        if not 46 <= length <= 46 + 128 * len(a):
            raise ValueError('actual BR88 length bound')
        packet = self.process.stdout.read(length)
        if len(packet) != length or metrics['bytes'] != length:
            raise RuntimeError('dense encoder truncated packet')
        return packet, metrics


def compose(record, value, operations, qblock, control, encoder, maps, generation):
    key = bool(record['key'])
    method, mode = maps.encode_body(operations, value['hidden'], key=key)
    assert maps.decode_body(method, mode, value['hidden'], key=key) == operations
    residual = bytearray()
    metrics, chunks = [], []
    offset = 0
    for axis, coefficients in enumerate(value['coefficients']):
        total = (5400, 1350, 1350)[axis]
        needed = np.array(operations[offset:offset + total]) == 2
        selected = coefficients[needed]
        residual.extend(struct.pack('>I', int(bool(len(selected)))))
        if len(selected):
            payload, work = encoder.encode(selected)
            residual.extend(struct.pack('>II', len(selected), len(payload)))
            chunk_at = len(residual)
            residual.extend(payload)
            chunks.append(dict(axis=axis, payload_offset=chunk_at, payload_bytes=len(payload), coefficients=selected))
            metrics.append(dict(axis=axis, **work))
        offset += total
    header = PREFIX.pack(b'CS88', 1, int(key), 16, method, int(record['frame_id']), int(record['reference_id']), generation,
                         720, 480, value['block_size'], 0, 65536, len(mode), len(qblock), len(value['hud']), len(residual))
    header += control['root'] + control['seal'] + bytes(12)
    content = header + mode + qblock + bytes(residual) + value['hud']
    packet = content + struct.pack('>I', zlib.crc32(content))
    if not 132 <= len(packet) <= RESEARCH_CAP:
        raise ValueError('CS88 research packet bound')
    counts = dict(header=128, mode_body=len(mode), qmap=len(qblock), chunk_directory=12 + 8 * len(chunks),
                  BR88_payloads=sum(c['payload_bytes'] for c in chunks), HUD=len(value['hud']), outer_CRC=4)
    assert sum(counts.values()) == len(packet)
    return packet, counts, metrics, chunks, 128 + len(mode) + len(qblock)


def corrupt_last_residual(packet, chunks, residual_at, encoder):
    # Keep the complete framing, all coefficient grammar checks and both CRCs
    # valid. Only a late reconstructed tile changes; the original C2 root/seal
    # must catch it after reconstruction and before publication.
    chunk = chunks[-1]
    coefficients = chunk['coefficients'].copy()
    old = int(coefficients[-1, 0])
    coefficients[-1, 0] = old + 32 if old <= 2016 else old - 32
    payload, _ = encoder.encode(coefficients)
    at = residual_at + chunk['payload_offset']
    content = bytearray(packet[:at] + payload + packet[at + chunk['payload_bytes']:-4])
    struct.pack_into('>I', content, at - 4, len(payload))
    data_bytes = int.from_bytes(packet[48:52], 'big') + len(payload) - chunk['payload_bytes']
    struct.pack_into('>I', content, 48, data_bytes)
    return bytes(content) + struct.pack('>I', zlib.crc32(content))


def convert_records(records, output_dir, *, container=CONTAINER, input_manifests=()):
    """Convert fresh accepted records (in memory or NPZ-backed), verify native.

    Returns the report dictionary and writes an immutable attempt directory.
    Distinct (clip_id,quant_scale) groups each get fresh decoder/QM87/C2 state.
    Rejected CU66 input records are recorded as skipped and never composed.
    """
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = dict(schema='fresh-current-cu66-to-actual-cs88-v99', status='FAIL',
                  started_utc=dt.datetime.now(dt.timezone.utc).isoformat(), argv=sys.argv,
                  python=sys.version, platform=platform.platform(), commands=[],
                  physical_packet_cap=CAP, native_research_packet_cap=RESEARCH_CAP,
                  policy='all_BR88; QM87; C2 content tree granularity16; exact semantic native HUD',
                  chain_policy='diagnostic native 2MiB chain advances every accepted fresh CU66 input, including CS88 oversize; entire chain physically eligible only if every CS88 packet fits49152',
                  physical_30fps_proven=False, validated_under10ms_proven=False,
                  inputs=[dict(path=str(Path(p).resolve()), sha256=sha(p)) for p in input_manifests])
    sources = [Path(__file__).resolve(), AREA / 'encode_dense.cpp', ROOT / 'experiments/python-gamebub-v88/wire/receiver.cpp',
               ROOT / 'experiments/python-gamebub-v88/entropy/codec.hpp', ROOT / 'experiments/python-gamebub-v85/residual/encode.hpp',
               ROOT / 'scripts/cu66-v86/prototype_maps.py', ROOT / 'scripts/cu66-v87/quantizer_codec.py',
               ROOT / 'scripts/cu66-v82/prototype_commitment.py']
    sources += sorted((ROOT / 'experiments/cu66-native-v69').glob('*.hpp'))
    report['source_sha256'] = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        dest = out / 'sources' / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    write_json(out / 'receipt.json', report)
    started = time.monotonic()
    encoder = receiver = None
    rows, tests = [], []
    try:
        binaries = prepare_binaries(out, report, container)
        mask = run_command(['docker', 'exec', container, binaries['encode_dense'], '--mask'], out, report, 'fixed-mask')
        assert len(mask) == 8100 and hashlib.sha256(mask).hexdigest() == 'e08b9861ae9a170c913c6425a5773ff42042a0abfe2fef8cd756cb505a8a8fa5'
        maps = load('v99_cs88_maps', 'scripts/cu66-v86/prototype_maps.py')
        qcodec = load('v99_cs88_qcodec', 'scripts/cu66-v87/quantizer_codec.py')
        commitment = load('v99_cs88_commitment', 'scripts/cu66-v82/prototype_commitment.py')
        encoder_command = ['docker', 'exec', '-i', container, binaries['encode_dense']]
        report['commands'].append(dict(argv=encoder_command))
        encoder = DenseEncoder(encoder_command, out / 'encoder.stderr')
        groups = {}
        for record in records:
            groups.setdefault((str(record.get('clip_id', 'clip')), int(record.get('quant_scale', 0))), []).append(record)
        summaries = []
        with (out / 'frames.jsonl').open('w') as frames, (out / 'skipped.jsonl').open('w') as skipped:
            for chain_index, ((clip, quant), sequence) in enumerate(groups.items()):
                name = f'chain{chain_index:02d}'
                chain_out = out / name
                chain_out.mkdir()
                command = ['docker', 'exec', '-i', container, binaries['receiver']]
                report['commands'].append(dict(argv=command, chain=name))
                receiver = Native(command, chain_out / 'receiver.stderr')
                previous_root = bytes(32)
                previous_qmap = None
                previous_fid = None
                generation = 0
                chain_rows = []
                for record in sequence:
                    if not record.get('accepted', True):
                        skipped.write(json.dumps(dict(clip_id=clip, quant_scale=quant, frame_id=record['frame_id'],
                                                      reason='fresh CU66 rejected; no CS88 state transition')) + '\n')
                        continue
                    value = components(record)
                    value['hidden'] = list(mask)
                    assert [len(a) for a in value['coefficients']] == [5400, 1350, 1350]
                    dense = np.concatenate(value['coefficients'])
                    assert np.issubdtype(dense.dtype, np.integer) and np.all(dense >= -2048) and np.all(dense <= 2048)
                    assert not np.any(dense[np.frombuffer(mask, dtype='u1').astype(bool)]), 'hidden coefficients must already be zero'
                    key = bool(record['key'])
                    operations = [1 if hidden else 0 if not key and not np.any(c) else 2
                                  for hidden, c in zip(mask, dense, strict=True)]
                    assert operations == value['operations'], 'fresh operation semantics'
                    if key:
                        assert record['reference_id'] == 0xffffffff
                    else:
                        assert record['reference_id'] == previous_fid, 'actual accepted fresh reference'
                    expected = record['expected']
                    canonical = b''.join(np.asarray(a, dtype='u1').tobytes() for a in value['planes'])
                    assert hashlib.sha256(canonical).hexdigest() == expected['canonical_sha256']
                    scales = qcodec.unpacked(value['qmap'], 1350)
                    qblock = qcodec.encode(scales, operations, None if key else previous_qmap)
                    next_qmap = qcodec.decode(qblock, operations, None if key else previous_qmap)
                    generation += 1
                    tree = commitment.CommitmentTree(granularity=16)
                    cframe = dict(fid=int(record['frame_id']), refid=int(record['reference_id']), key=key,
                                  generation=generation, tiles=tile_bytes(value['planes']), hidden_mask=mask,
                                  hud_sha256=expected['hud_sha256'])
                    control = tree.full(cframe, previous_root=previous_root)
                    packet, counts, work, chunks, residual_at = compose(record, value, operations, qblock, control, encoder, maps, generation)
                    # The first P frame with data exercises late canonical corruption
                    # against existing accepted state, followed by the exact good packet.
                    if not tests and not key and chunks:
                        corrupt = corrupt_last_residual(packet, chunks, residual_at, encoder)
                        rejected = receiver.receive(0, corrupt)
                        assert not rejected['accepted'] and rejected['error'] == 'CS88 reconstructed content root', rejected
                        assert rejected['retained_fid'] == previous_fid, rejected
                        badpath = chain_out / f"f{record['frame_id']:06d}-late-coefficient-valid-crc.cs88"
                        badpath.write_bytes(corrupt)
                        tests.append(dict(name='late_canonical_coefficient_valid_inner_outer_CRC', status='PASS_REJECT_UNCHANGED',
                                          decoded=rejected, corruption_sha256=sha(badpath)))
                    decoded = receiver.receive(0, packet)
                    assert decoded['accepted'] and not decoded['replayed'], decoded
                    coefficient_sha = hashlib.sha256(dense.astype('<i2').tobytes()).hexdigest()
                    for field, golden in [('canonical_sha256', expected['canonical_sha256']), ('hud_sha256', expected['hud_sha256']),
                                          ('display_sha256', expected['rgb565_sha256']), ('coefficient_sha256', coefficient_sha),
                                          ('root', control['root'].hex()), ('seal', control['seal'].hex())]:
                        assert decoded[field] == golden, (clip, quant, record['frame_id'], field, decoded[field], golden)
                    assert decoded['fid'] == record['frame_id'] and decoded['generation'] == generation and decoded['wire_bytes'] == len(packet)
                    packet_path = chain_out / f"f{record['frame_id']:06d}.cs88"
                    packet_path.write_bytes(packet)
                    row = dict(chain=name, clip_id=clip, quant_scale=quant, frame_id=int(record['frame_id']), reference_id=int(record['reference_id']),
                               key=key, generation=generation, wire_bytes=len(packet), fits_49152=len(packet) <= CAP,
                               CU66_wire_bytes=record.get('bytes'), source_rgb_sha256=record.get('source_rgb_sha256'),
                               packet_path=str(packet_path.relative_to(out)), packet_sha256=hashlib.sha256(packet).hexdigest(),
                               components=counts, BR88_work=work, remaining_adaptive_decisions=0, decoded=decoded,
                               qmap_sha256=hashlib.sha256(qblock).hexdigest(), operations_sha256=hashlib.sha256(bytes(operations)).hexdigest())
                    if record.get('rtl_components_path'):
                        row['fresh_components'] = dict(path=record['rtl_components_path'], sha256=sha(record['rtl_components_path']))
                    frames.write(json.dumps(row, separators=(',', ':')) + '\n')
                    rows.append(row)
                    chain_rows.append(row)
                    previous_root, previous_qmap, previous_fid = control['root'], next_qmap, record['frame_id']
                    if len(rows) == 1 or len(rows) % 50 == 0:
                        print('V99_CS88_PROGRESS', len(rows), flush=True)
                receiver.close()
                receiver = None
                sizes = [r['wire_bytes'] for r in chain_rows]
                summaries.append(dict(chain=name, clip_id=clip, quant_scale=quant, accepted_frames=len(sizes),
                                      total_bytes=sum(sizes), max_bytes=max(sizes, default=0), fits_49152=sum(s <= CAP for s in sizes),
                                      oversize_49152=sum(s > CAP for s in sizes),
                                      entire_sequence_49152_eligible=bool(sizes) and all(s <= CAP for s in sizes)))
        encoder.close()
        encoder = None
        assert report['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in sources}, 'executed sources changed'
        report.update(status='PASS_FRESH_NATIVE_CS88_PARITY', received_packets=len(rows), chains=summaries, adversarial=tests,
                      all_sequences_49152_eligible=bool(rows) and all(r['fits_49152'] for r in rows),
                      fit_packets_49152=sum(r['fits_49152'] for r in rows), oversize_packets_49152=sum(not r['fits_49152'] for r in rows),
                      total_wire_bytes=sum(r['wire_bytes'] for r in rows),
                      scope=['New BR88 encoded directly from fresh post-hiddenzero quantized coefficients; no historical quantized packet data used.',
                             'Unchanged native CS88 receiver checks full coefficient/canonical/semantic HUD/RGB565/C2 root/seal parity.',
                             'All diagnostic native accepted frames advance diagnostic reference/root/QM87 state; no 49152-byte bounded acceptance claim for oversized chains.',
                             'No FPGA, calibrated timing, SRAM mapping, production transport, or physical30fps claim.'])
    except BaseException as error:
        report['failure'] = repr(error)
        raise
    finally:
        if receiver:
            receiver.abort()
        if encoder:
            encoder.abort()
        report['wall_seconds'] = time.monotonic() - started
        report['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'results.json'}
        write_json(out / 'results.json', report)
        print('V99_CS88_REPORT', out / 'results.json', report['status'], flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', action='append', type=Path, required=True, help='fresh encoder records.json; repeat for clips/scales')
    parser.add_argument('--output', type=Path, required=True, help='new immutable attempt directory')
    parser.add_argument('--container', default=CONTAINER)
    args = parser.parse_args()
    records = []
    for path in args.records:
        data = json.loads(path.read_text())
        source = data if isinstance(data, list) else data['records']
        records.extend(source)
    report = convert_records(records, args.output, container=args.container, input_manifests=args.records)
    return 0 if report['status'] == 'PASS_FRESH_NATIVE_CS88_PARITY' else 1


if __name__ == '__main__':
    raise SystemExit(main())
