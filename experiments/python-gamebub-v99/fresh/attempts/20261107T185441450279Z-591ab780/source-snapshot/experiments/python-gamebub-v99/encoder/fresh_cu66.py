"""Fresh RGB -> actual CU66/GU66, using the unchanged frozen transform chain.

No retained packet, decoded fixture or historical GM01 output is an input.
The receiver is the existing v66 implementation; native parity is separate.
"""
from pathlib import Path
import contextlib
import gzip
import hashlib
import importlib.util
import json
import struct
import sys
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPERIMENTS = ROOT / 'experiments'
CAP = 49152
_DEPENDENCIES = None


def digest(data):
    return hashlib.sha256(data).hexdigest()


@contextlib.contextmanager
def aliases(**values):
    previous = {name: sys.modules.get(name) for name in values}
    try:
        sys.modules.update(values)
        yield
    finally:
        for name, old in previous.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


def module(name, path):
    spec = importlib.util.spec_from_file_location('v99_fresh_' + name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = value
    spec.loader.exec_module(value)
    return value


def dependencies():
    global _DEPENDENCIES
    if _DEPENDENCIES is not None:
        return _DEPENDENCIES
    # These dependency loaders use explicit frozen names. The few historical
    # bare imports are scoped while loading and restored before returning.
    helper = module('analysis_helper', EXPERIMENTS / 'python-game-analysis-v37-study/helpers.py')
    with aliases(helpers=helper):
        analysis = module('analysis', EXPERIMENTS / 'python-game-analysis-v37-study/model.py')
    canonical_helper = module('canonical_helper', EXPERIMENTS / 'python-game-canonical-tag-v66-study/helpers.py')
    with aliases(helpers=canonical_helper):
        wire = module('wire', EXPERIMENTS / 'python-game-canonical-tag-v66-study/protocol.py')
        receiver = module('receiver', EXPERIMENTS / 'python-game-canonical-tag-v66-study/receiver.py')
    arithmetic = module('arithmetic', EXPERIMENTS / 'python-game-binary-v38-study/model.py')
    baseline = module('hud_baseline', EXPERIMENTS / 'python-game-hud-runs-v33-study/baseline.py')
    with aliases(baseline=baseline):
        hud_decoder = module('hud_decoder', EXPERIMENTS / 'python-game-hud-runs-v33-study/decoder.py')
        with aliases(decoder=hud_decoder):
            hud33 = module('hud33', EXPERIMENTS / 'python-game-hud-runs-v33-study/model.py')
    _DEPENDENCIES = dict(h=helper, analysis=analysis, wire=wire, receiver=receiver,
                         arithmetic=arithmetic, hud32=baseline.old, hud33=hud33)
    return _DEPENDENCIES


def source_pins():
    dependencies()
    paths = {Path(__file__).resolve()}
    for value in tuple(sys.modules.values()):
        path = getattr(value, '__file__', None)
        if path:
            path = Path(path).resolve()
            if path.suffix == '.py' and EXPERIMENTS in path.parents:
                paths.add(path)
    return {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in sorted(paths)}


def seal(body):
    return body + struct.pack('<I', zlib.crc32(body))


def _rgb(rgb):
    if not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.shape != (480, 720, 3):
        raise ValueError('fresh fixed 720x480 RGB uint8 required')
    return rgb


def validate_native_packet(packet):
    """Apply v66 parsing plus the unchanged native receiver capability subset."""
    deps = dependencies()
    meta = deps['receiver'].parse(packet, 'CU66')
    if meta['block_size'] not in (16, 32) or any(v not in (5, 6) for v in meta['dispatch']):
        raise ValueError('native capability block16/32 arithmetic5/6 only')
    if np.any(meta['vectors']):
        raise ValueError('native capability zero-motion only')
    outer = deps['wire'].OUTER.unpack_from(packet)
    inner = packet[deps['wire'].OUTER.size:deps['wire'].OUTER.size + outer[11]]
    fields = deps['wire'].INNER.unpack_from(inner)
    nq, nv = fields[11:13]
    motion = inner[deps['wire'].INNER.size + nq:deps['wire'].INNER.size + nq + nv]
    if motion != (b'' if meta['key'] else b'\0\0\0'):
        raise ValueError('native capability canonical zero motion map only')
    return meta


def hud_bytes(patches):
    """Exact native hud_tag preimage, including geometry and rectangles."""
    out = bytearray(struct.pack('<HHB', 720, 480, len(patches)))
    for patch in patches:
        out.extend(struct.pack('<4H', *patch['rect']))
        out.extend(np.ascontiguousarray(patch['words'], dtype='<u2').tobytes())
    return bytes(out)


def _encode_hud(rgb, reference, frame_id, reference_id, deps):
    h, hud32, hud33 = deps['h'], deps['hud32'], deps['hud33']
    protocol = hud32.p
    selected = protocol.ui.PatchSelector(rectangles=tuple(h.n.RECTS)).select(rgb, 98304)
    hu25, _ = protocol.encode_hud(selected.patches, reference=reference, epoch=25,
                                frame_id=frame_id, reference_id=reference_id,
                                motion=False, width=720, height=480)
    hx32, _ = hud32.encode_hud(hu25, reference, expected_reference_id=None if reference is None else reference_id)
    hx33, _ = hud33.encode_hud(hu25, hx32, reference,
                             expected_reference_id=None if reference is None else reference_id)
    patches, _ = hud33.decode_hud(hx33, reference, expected_epoch=25,
                                 expected_reference_id=None if reference is None else reference_id)
    original = h.m.C.corpus.rgb565(rgb)
    for patch, rect in zip(patches, h.n.RECTS, strict=True):
        x, y, w, height = rect
        if tuple(patch['rect']) != tuple(rect) or not np.array_equal(patch['words'], original[y:y+height, x:x+w]):
            raise AssertionError('fresh HUD exact source RGB565 invariant')
    return hx33, patches


def encode_candidate(rgb, reference=None, hud_reference=None, *, frame_id=0,
                     reference_id=0xffffffff, quant_scale=16, motion_mode='zero'):
    """Construct one complete candidate, including overcap diagnostic bytes.

    The expected output is computed directly from the fresh forward transform
    and quantized coefficients before the independent v66 packet parse.
    """
    rgb = _rgb(rgb)
    if type(quant_scale) is not int or quant_scale not in (8, 16, 32):
        raise ValueError('CU66 qmap supports only scales8/16/32')
    if motion_mode != 'zero':
        raise ValueError('native capability zero-motion only')
    if (reference is None) != (hud_reference is None):
        raise ValueError('base and HUD references advance together')
    deps = dependencies()
    h, analysis, wire, arithmetic = (deps[n] for n in ('h', 'analysis', 'wire', 'arithmetic'))
    started = time.perf_counter_ns()
    source_sha = digest(rgb.tobytes())
    source = tuple(h.m.ft.rgb_to_planes(rgb))
    prepared = analysis.analyze_planes(source, reference, epoch=25, frame_id=frame_id,
                                      reference_id=reference_id, motion_mode='zero')
    qmap = np.full((30, 45), quant_scale, np.uint8)
    coefficients = tuple(c.copy() for c in h.m.base._quantize(prepared.raw_coefficients, qmap, 720, 480))
    payloads, plane_work = [], []
    for axis, (coeff, safe) in enumerate(zip(coefficients, h.canonical.HIDDEN, strict=True)):
        coeff[safe] = 0
        full, _ = arithmetic.encode(coeff, 90 if axis == 0 else 45)
        compact, _ = arithmetic.encode(coeff[~safe], 1)
        payload = (b'\x06' + compact) if len(compact) < len(full) else (b'\x05' + full)
        payloads.append(payload)
        plane_work.append(dict(dispatch=payload[0], full_bytes=len(full)+1,
                               compact_bytes=len(compact)+1, selected_bytes=len(payload)))
    rebuilt = h.m.gm.reconstruct(coefficients, prepared.prediction, qmap, 720, 480)
    normalized = h.canonical.normalize(rebuilt)
    hud, patches = _encode_hud(rgb, hud_reference, frame_id, reference_id, deps)
    packed_q = h.m.roi.pack_map(qmap)
    canonical_reference_tag = bytes(16) if reference is None else wire.tag_u8(reference)
    canonical_output_tag = wire.tag_u8(normalized)
    # Real historical CS38 envelope, freshly constructed, is retained as bridge
    # evidence. Only CU66 is submitted to a receiver. The bounded offline v66
    # adapter is checked byte-for-byte when its old-CS38 cap permits it.
    cs38_inner = seal(h.m.HEADER.pack(b'GS38', h.m.VERSION, int(prepared.key), 25,
        frame_id, reference_id, 720, 480, 32, h.m.base.LIMIT, prepared.reference_tag,
        h.m.C.reference_tag(rebuilt), len(packed_q), len(prepared.vector_bytes),
        *(len(p) for p in payloads)) + packed_q + prepared.vector_bytes + b''.join(payloads))
    cs38 = seal(wire.OUTER.pack(b'CS38', 1, 2|int(prepared.key), 25, frame_id,
        reference_id, 720, 480, deps['receiver'].h.oldrx.PROFILE, prepared.reference_tag,
        h.m.C.reference_tag(normalized), len(cs38_inner), len(hud)) + cs38_inner + hud)
    inner = seal(wire.INNER.pack(b'GU66', h.m.VERSION, int(prepared.key), 25,
        frame_id, reference_id, 720, 480, 32, h.m.base.LIMIT, canonical_reference_tag,
        len(packed_q), len(prepared.vector_bytes), *(len(p) for p in payloads)) +
        packed_q + prepared.vector_bytes + b''.join(payloads))
    packet = seal(wire.OUTER.pack(b'CU66', 1, 2|int(prepared.key), 25, frame_id,
        reference_id, 720, 480, wire.PROFILES['CU66']['profile'], canonical_reference_tag,
        canonical_output_tag, len(inner), len(hud)) + inner + hud)
    converted_checked = len(cs38) <= CAP
    if converted_checked:
        converted, _ = wire.convert(cs38, 'CU66', reference=reference, normalized=normalized)
        if converted != packet:
            raise AssertionError('fresh CS38 -> CU66 exact adapter bytes')
    encode_ms = (time.perf_counter_ns() - started) / 1e6
    canonical = b''.join(np.ascontiguousarray(p, dtype=np.uint8).tobytes() for p in normalized)
    hud_raw = hud_bytes(patches)
    display = h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(normalized))
    display = h.n.overlay(display, tuple(p['words'] for p in patches))
    display = np.ascontiguousarray(display, dtype='<u2')
    expected = dict(canonical_sha256=digest(canonical), hud_sha256=digest(hud_raw),
                    rgb565_sha256=digest(display.tobytes()), canonical_tag=canonical_output_tag.hex())
    if digest(rgb.tobytes()) != source_sha:
        raise AssertionError('fresh RGB input modified')
    return dict(frame_id=frame_id, reference_id=reference_id, key=prepared.key,
                quant_scale=quant_scale, packet=packet, cs38_packet=cs38,
                packet_sha256=digest(packet), bytes=len(packet), cap_fit=len(packet)<=CAP,
                source_rgb_sha256=source_sha, expected=expected,
                canonical_bytes=canonical, hud_bytes=hud_raw, rgb565_bytes=display.tobytes(),
                normalized_planes=normalized, hud_patches=patches, rgb565=display,
                rtl_components=dict(coefficients=coefficients, qmap=qmap, packed_qmap=packed_q,
                    hud_envelope=hud, block_size=32, reference_id=reference_id, key=prepared.key,
                    operations=np.concatenate([np.where(safe, 1,
                        np.where(np.all(c == 0, axis=(1, 2)) & (not prepared.key), 0, 2))
                        for c, safe in zip(coefficients, h.canonical.HIDDEN, strict=True)]).astype(np.uint8)),
                planes=plane_work, adapter_exact_checked=converted_checked, encode_ms=encode_ms)


def encode_sequence(frames, quant_scale=16, output_dir=None, *, clip_id='clip', key_interval=30):
    """Encode every fresh input and ACK only exact successful v66 receives.

    Overcap candidates are retained, counted, and never submitted/ACKed. A
    rejection clears both references so the next input attempts a fresh key.
    Disk ledger contains accepted packets only, plus a complete records.json.
    """
    if type(key_interval) is not int or key_interval != 30:
        raise ValueError('fixed study key interval30')
    frames = list(frames)
    if not frames:
        raise ValueError('at least one fresh RGB frame required')
    for frame in frames:
        _rgb(frame)
    deps = dependencies()
    receiver = deps['receiver'].Receiver('CU66')
    records, outputs, ledger = [], [], []
    reference = hud_reference = None
    reference_id = 0xffffffff
    directory = Path(output_dir).resolve() if output_dir is not None else None
    if directory:
        directory.mkdir(parents=True, exist_ok=True)
    for fid, rgb in enumerate(frames):
        key = fid % key_interval == 0 or reference is None
        row = encode_candidate(rgb, None if key else reference, None if key else hud_reference,
                               frame_id=fid, reference_id=0xffffffff if key else reference_id,
                               quant_scale=quant_scale)
        row.update(clip_id=clip_id, accepted=False, ack_verified=False,
                   rejection_reason=None if row['cap_fit'] else 'complete CU66 cap exceeded')
        if row['cap_fit']:
            validate_native_packet(row['packet'])
            start = time.perf_counter_ns()
            got, got_hud, meta, _ = receiver.receive(row['packet'])
            row['decode_ms'] = (time.perf_counter_ns()-start)/1e6
            if any(not np.array_equal(a, b) for a, b in zip(got, row['normalized_planes'], strict=True)):
                raise AssertionError('fresh sender reconstruction != v66 receiver')
            if hud_bytes(got_hud) != row['hud_bytes'] or meta['output_tag'].hex() != row['expected']['canonical_tag']:
                raise AssertionError('fresh sender HUD/canonical tag != v66 receiver')
            reference, hud_reference, reference_id = got, got_hud, fid
            row.update(accepted=True, ack_verified=True)
            outputs.append(row['rgb565'])
        else:
            reference = hud_reference = None
            reference_id = 0xffffffff
            outputs.append(None)
        if directory:
            prefix = f'{fid:06d}'
            packet_path = directory / (prefix + ('.cu66' if row['accepted'] else '.oversized-cu66'))
            packet_path.write_bytes(row['packet'])
            row['packet_path'] = str(packet_path)
            for kind in ('canonical', 'hud', 'rgb565'):
                path = directory / f'{prefix}.{kind}.bin.gz'
                path.write_bytes(gzip.compress(row[kind + '_bytes'], compresslevel=9, mtime=0))
                row[kind + '_path'] = str(path)
                row[kind + '_compression'] = 'gzip-mtime0'
            components_path = directory / f'{prefix}.rtl-components.npz'
            components = row['rtl_components']
            np.savez_compressed(components_path,
                coefficients_y=components['coefficients'][0].reshape(-1, 64),
                coefficients_u=components['coefficients'][1].reshape(-1, 64),
                coefficients_v=components['coefficients'][2].reshape(-1, 64),
                plane_y=row['normalized_planes'][0].astype(np.uint8),
                plane_u=row['normalized_planes'][1].astype(np.uint8),
                plane_v=row['normalized_planes'][2].astype(np.uint8),
                qmap=np.frombuffer(components['packed_qmap'], np.uint8),
                hud=np.frombuffer(components['hud_envelope'], np.uint8),
                operations=components['operations'], key=np.array(row['key']),
                frame_id=np.array(fid, np.uint32), reference_id=np.array(row['reference_id'], np.uint32),
                block_size=np.array(32, np.uint8))
            row['rtl_components_path'] = str(components_path)
            disk_row = {k: v for k, v in row.items() if k not in {
                'packet', 'cs38_packet', 'canonical_bytes', 'hud_bytes', 'rgb565_bytes',
                'normalized_planes', 'hud_patches', 'rgb565', 'rtl_components'}}
            if row['accepted']:
                ledger.append(disk_row)
        records.append(row)
    report = dict(schema='fresh-rgb-current-cu66-v99', clip_id=clip_id,
                  quant_scale=quant_scale, records=records, outputs_rgb565=outputs,
                  input_frames=len(frames), accepted_frames=sum(r['accepted'] for r in records),
                  rejected_frames=sum(not r['accepted'] for r in records),
                  dropped_frames=0, cap_bytes=CAP, epoch=25, key_interval=30,
                  reference_policy='previous exactly ACKed normalized frame; reset to key after rejection',
                  hud_policy='exact fresh source RGB565 fixed rectangles; HU25/HX32/HX33 minimum; motion=False',
                  quant_policy='uniform scale8/16/32; no RDO or adaptive fallback',
                  color_contract='unchanged fixed_codec.rgb_to_planes and planes_to_rgb',
                  input_color_code_sha256=digest(Path(deps['h'].m.ft.__file__).read_bytes()),
                  golden_compression='gzip-mtime0',
                  source_sha256=source_pins(), ledger_path=None)
    if directory:
        ledger_path = directory / 'ledger.jsonl'
        ledger_path.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in ledger))
        report['ledger_path'] = str(ledger_path)
        disk_report = {k:v for k,v in report.items() if k not in ('records', 'outputs_rgb565')}
        disk_report['records'] = [{k:v for k,v in row.items() if k not in {
            'packet', 'cs38_packet', 'canonical_bytes', 'hud_bytes', 'rgb565_bytes',
            'normalized_planes', 'hud_patches', 'rgb565', 'rtl_components'}} for row in records]
        (directory / 'records.json').write_text(json.dumps(disk_report, indent=2)+'\n')
    return report
