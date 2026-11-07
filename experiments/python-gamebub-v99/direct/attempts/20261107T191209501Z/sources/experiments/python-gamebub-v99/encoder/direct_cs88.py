"""Fresh q16 RGB -> actual frozen V91-subset CS88; no AB38 bridge encoding.

Only a successful independent native ACK and exact control packet comparison
publish the sender's next reference/root/QM87 state. Control material is used
after packet readiness strictly as a verification oracle, never as encoder data.
"""
from pathlib import Path
import hashlib
import importlib.util
import struct
import sys
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


fresh = load('v99_direct_fresh_primitives', HERE / 'fresh_cu66.py')
cs88 = load('v99_direct_frozen_cs88', ROOT / 'scripts/cu66-v99/run_cs88.py')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def synthetic_rgb(frame_id):
    """Deterministic fresh cross-key control; not a captured gameplay source."""
    if type(frame_id) is not int or not 0 <= frame_id < 32:
        raise ValueError('synthetic cross-key control frame0..31')
    rgb = np.full((480, 720, 3), 80, np.uint8)
    x = 210 + frame_id * 3
    rgb[180:228, x:x+48] = (30 + frame_id * 3, 180, 220 - frame_id * 2)
    for bit in range(5):
        rgb[52:60, 24+bit*12:32+bit*12] = (240, 20, 80) if frame_id & (1 << bit) else (20, 210, 30)
    return rgb


class TimedDenseEncoder:
    def __init__(self, encoder):
        self.encoder = encoder
        self.elapsed_ms = 0.0
        self.calls = 0

    def encode(self, coefficients):
        start = time.perf_counter_ns()
        result = self.encoder.encode(coefficients)
        self.elapsed_ms += (time.perf_counter_ns() - start) / 1e6
        self.calls += 1
        return result


class DirectSender:
    """One causal q16 clip context, backed by persistent independent native IPC.

    ``send`` takes fresh RGB and a frame identity. All historical/control data
    is restricted to the verification block after the actual packet is ready.
    A failure raises and aborts this context; no rejected reference is published.
    """
    def __init__(self, dense_encoder, native_receiver, *, clip_id):
        self.deps = fresh.dependencies()
        self.h = self.deps['h']
        self.encoder = dense_encoder
        self.receiver = native_receiver
        self.clip_id = clip_id
        self.maps = cs88.load('v99_direct_maps', 'scripts/cu66-v86/prototype_maps.py')
        self.qcodec = cs88.load('v99_direct_qcodec', 'scripts/cu66-v87/quantizer_codec.py')
        self.commitment = cs88.load('v99_direct_commitment', 'scripts/cu66-v82/prototype_commitment.py')
        self.hidden = [int(x) for mask in self.h.canonical.HIDDEN for x in mask]
        self.maps.profile(self.hidden)
        self.qmap = np.full((30, 45), 16, np.uint8)
        self.packed_qmap = self.h.m.roi.pack_map(self.qmap)
        self.ref = self.hud_ref = None
        self.reference_id = 0xffffffff
        self.root = bytes(32)
        self.previous_qmap = None
        self.generation = 0
        self.next_id = 0

    def send(self, rgb, frame_id, *, expected_source_sha256, packet_path,
             control_row=None, control_packet_path=None):
        rgb = fresh._rgb(rgb)
        if type(frame_id) is not int or frame_id != self.next_id:
            raise ValueError('direct sender consumes sequential fresh frame IDs')
        # Immutable input/source verification lies outside packet-construction
        # timing. No control packet or coefficient material has been read here.
        source_sha = digest(rgb.tobytes())
        if source_sha != expected_source_sha256:
            raise ValueError('fresh source RGB SHA256 mismatch')
        reference_sha = None if self.ref is None else digest(b''.join(np.asarray(a, dtype='u1').tobytes() for a in self.ref))
        key = frame_id % 30 == 0
        reference_id = 0xffffffff if key else self.reference_id
        if not key and self.ref is None:
            raise ValueError('direct P requires native-ACKed reference')
        generation = self.generation + 1
        phases = {}
        started = phase = time.perf_counter_ns()
        source = tuple(self.h.m.ft.rgb_to_planes(rgb))
        phases['rgb_to_planes_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        prediction = tuple(np.full_like(a, 128) for a in source) if key else self.ref
        raw = self.h.m.base.old._forward(source, prediction)
        coefficients = tuple(c.copy() for c in self.h.m.base._quantize(raw, self.qmap, 720, 480))
        for c, mask in zip(coefficients, self.h.canonical.HIDDEN, strict=True):
            c[mask] = 0
        dense = np.concatenate([c.reshape(-1, 64) for c in coefficients])
        operations = np.where(np.asarray(self.hidden, dtype=bool), 1,
            np.where(np.all(dense == 0, axis=1) & (not key), 0, 2)).tolist()
        phases['forward_quant_hidden_operations_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        rebuilt = self.h.m.gm.reconstruct(coefficients, prediction, self.qmap, 720, 480)
        normalized = self.h.canonical.normalize(rebuilt)
        phases['sender_reconstruction_normalization_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        hud, patches = fresh._encode_hud(rgb, None if key else self.hud_ref, frame_id, reference_id, self.deps)
        hud_words = b''.join(np.ascontiguousarray(p['words'], dtype='<u2').tobytes() for p in patches)
        hud_sha = digest(hud_words)
        phases['fresh_HUD_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        scales = self.qcodec.unpacked(self.packed_qmap, 1350)
        qblock = self.qcodec.encode(scales, operations, None if key else self.previous_qmap)
        if qblock[5] != 6:
            qbody = self.qcodec.runs(scales)
            qcontent = self.qcodec.HEAD.pack(b'QM87', 1, 2, 1350, len(qbody), sum(self.qcodec.needed_cells(operations))) + qbody
            qblock = qcontent + struct.pack('>I', zlib.crc32(qcontent))
        if qblock[5] not in (2, 6) or (key and qblock[5] != 2):
            raise ValueError('fixed V91 QM87 run2/inherit6 subset')
        next_qmap = self.qcodec.decode(qblock, operations, None if key else self.previous_qmap)
        phases['QM87_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        tree = self.commitment.CommitmentTree(granularity=16)
        cframe = dict(fid=frame_id, refid=reference_id, key=key, generation=generation,
                      tiles=cs88.tile_bytes(normalized), hidden_mask=self.hidden, hud_sha256=hud_sha)
        control = tree.full(cframe, previous_root=self.root)
        phases['C2_tree_seal_ms'] = (time.perf_counter_ns() - phase) / 1e6
        phase = time.perf_counter_ns()
        timed_encoder = TimedDenseEncoder(self.encoder)
        identity = dict(key=key, frame_id=frame_id, reference_id=reference_id)
        value = dict(coefficients=[c.reshape(-1, 64) for c in coefficients], planes=normalized,
                     hidden=self.hidden, block_size=32, hud=hud)
        packet, counts, work, chunks, _ = cs88.compose(identity, value, operations, qblock, control,
            timed_encoder, self.maps, generation, 'v91-group3')
        phases['BR88_encode_IPC_ms'] = timed_encoder.elapsed_ms
        phases['mode_packet_assembly_ms'] = (time.perf_counter_ns() - phase) / 1e6 - timed_encoder.elapsed_ms
        packet_ready_ms = (time.perf_counter_ns() - started) / 1e6
        # Packet is now complete. All verification and artifact writes below
        # are outside the measured RGB->packet-ready interval.
        packet_path = Path(packet_path)
        packet_path.write_bytes(packet)
        if len(packet) > 49152:
            raise ValueError('direct complete CS88 cap49152 exceeded; context aborted')
        if packet[7] != (0 if key else 3):
            raise AssertionError('direct fixed key0/Pgroup3 mode')
        packet_sha = digest(packet)
        expected = dict(canonical_sha256=digest(b''.join(np.asarray(a, dtype='u1').tobytes() for a in normalized)),
                        coefficient_sha256=digest(dense.astype('<i2').tobytes()), hud_sha256=hud_sha,
                        root=control['root'].hex(), seal=control['seal'].hex())
        display = self.h.m.C.corpus.rgb565(self.h.m.ft.planes_to_rgb(normalized))
        display = self.h.n.overlay(display, tuple(p['words'] for p in patches))
        expected['display_sha256'] = digest(np.ascontiguousarray(display, dtype='<u2').tobytes())
        if digest(rgb.tobytes()) != source_sha:
            raise AssertionError('direct sender modified fresh input RGB')
        if self.ref is not None and reference_sha != digest(b''.join(np.asarray(a, dtype='u1').tobytes() for a in self.ref)):
            raise AssertionError('direct sender mutated accepted reference')
        if control_row is not None:
            if (control_row['clip_id'], control_row['quant_scale'], control_row['frame_id']) != (self.clip_id, 16, frame_id):
                raise ValueError('authoritative q16 control identity mismatch')
            if control_row['source_rgb_sha256'] != source_sha:
                raise ValueError('authoritative control/fresh source RGB binding mismatch')
            authoritative = Path(control_packet_path).read_bytes()
            if packet_sha != control_row['packet_sha256'] or packet != authoritative:
                raise AssertionError('fresh direct actual CS88 != authoritative packet bytes')
        tick = time.perf_counter_ns()
        decoded = self.receiver.receive(0, packet)
        native_ack_roundtrip_ms = (time.perf_counter_ns() - tick) / 1e6
        if not decoded.get('accepted') or decoded.get('replayed'):
            raise AssertionError(('native direct rejection', decoded))
        for field, golden in expected.items():
            if decoded[field] != golden or (control_row is not None and decoded[field] != control_row['decoded'][field]):
                raise AssertionError(('direct native/control exact output mismatch', frame_id, field))
        if decoded['fid'] != frame_id or decoded['generation'] != generation or decoded['wire_bytes'] != len(packet):
            raise AssertionError('direct native identity/byte accounting mismatch')
        # This is the only reference/root/quantizer publication point.
        for a in normalized:
            a.setflags(write=False)
        self.ref, self.hud_ref, self.reference_id = normalized, patches, frame_id
        self.root, self.previous_qmap, self.generation = control['root'], next_qmap, generation
        self.next_id += 1
        return dict(clip_id=self.clip_id, quant_scale=16, frame_id=frame_id, reference_id=reference_id,
                    key=key, generation=generation, accepted=True, ack_verified=True,
                    source_rgb_sha256=source_sha, accepted_reference_canonical_sha256=None if key else reference_sha,
                    packet_path=str(packet_path), packet_sha256=packet_sha, packet_bytes=len(packet),
                    actual_packet_equal_control=True if control_row is not None else None,
                    control_packet_path=str(Path(control_packet_path).resolve()) if control_packet_path is not None else None,
                    control_packet_sha256=control_row['packet_sha256'] if control_row is not None else None,
                    packet_ready_ms=packet_ready_ms, phases=phases,
                    native_ack_roundtrip_ms=native_ack_roundtrip_ms, native_decoded=decoded,
                    expected=expected, components=counts, BR88_work=work,
                    map_method=packet[7], qmap_method=qblock[5], BR88_chunks=len(chunks),
                    timing_scope='fresh prevalidated RGB -> complete CS88 packet; verification/IO/ACK excluded; BR88 includes frozen helper self-decode and IPC')
