"""Fresh-RGB GM01 controls; this historical syntax is not current CU66."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import struct
import sys
import tempfile
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_source = HERE.parent / 'python-game-codec-study/game_codec.py'
_spec = importlib.util.spec_from_file_location('v98_control_gm01', _source)
gm = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = gm
_spec.loader.exec_module(gm)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _profile(parameter):
    if type(parameter) is int and parameter in (8, 16, 32):
        return parameter, 'zero'
    if parameter in ('global8', 'global16', 'global32'):
        return int(parameter[6:]), 'global'
    raise ValueError('GM01 parameter must be 8, 16, 32 or global8/global16/global32')


def _pins():
    modules = (gm, gm.ft, gm.roi, gm.mt, gm.token_coeff, gm.word_coeff,
               gm.roi.cc, gm.roi.cc.frozen)
    paths = {Path(m.__file__).resolve() for m in modules}
    paths.update((Path(__file__).resolve(), HERE.parent / 'python-game-standard-study/common_color.py'))
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)}


def run(frames, parameter, fps=30, output_dir=None):
    """Return ``(decoded_RGB_list, JSON_info)`` using every fresh source frame.

    Full GM01 packets, including nested CP02 and outer CRCs, are retained in a
    concatenated stream with byte offsets. No admission cap or adaptive policy
    is enabled. Every successful receive gets an immediate in-process ACK.
    """
    scale, motion = _profile(parameter)
    if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not math.isfinite(fps) or fps <= 0:
        raise ValueError('positive finite fps required')
    frames = list(frames)
    if not frames:
        raise ValueError('at least one RGB frame required')
    shape = gm.ft._check_rgb(frames[0]).shape
    for frame in frames:
        if gm.ft._check_rgb(frame).shape != shape:
            raise ValueError('fixed RGB geometry required')
    pins = _pins()
    h, w = shape[:2]
    mw, mh = gm.roi.geometry(w, h)
    scale_map = np.full((mh, mw), scale, np.uint8)
    directory = Path(output_dir) if output_dir is not None else Path(tempfile.mkdtemp(prefix='v98-gm01-'))
    directory.mkdir(parents=True, exist_ok=True)
    profile = f'gm01_{motion}_scale{scale}'
    stream_path = directory / (profile + '.gm01')
    enc, dec = gm.Encoder(epoch=1, window=1), gm.Receiver(epoch=1)
    outputs, packets, encode_calls, decode_calls, checks = [], [], [], [], []
    stream_hash = hashlib.sha256()
    offset = 0
    reference_samples = h * w * 3 // 2
    with stream_path.open('wb') as stream:
        for i, rgb in enumerate(frames):
            source_sha = digest(rgb.tobytes())
            start = time.perf_counter_ns()
            prepared = enc.analyze(rgb, i, force_key=i % 30 == 0, mode=motion)
            candidate = enc.encode_candidate(prepared, scale_map)
            packet = enc.commit(candidate)
            encode_ms = (time.perf_counter_ns() - start) / 1e6
            encode_calls.append(dict(id=i, input_pts=i, emitted_pts=[i], packets=1,
                                     elapsed_ms=encode_ms, encode_call_ms=encode_ms,
                                     analyze_ms=prepared.analyze_ms,
                                     candidate_ms=candidate.candidate_ms))
            # Sender-side reconstruction from its own candidate, independent of
            # packet parse/receive. Keep this verification outside encode timing.
            start = time.perf_counter_ns()
            expected_planes = gm.reconstruct(candidate.coefficients, prepared.prediction,
                                             candidate.scale_map, w, h)
            expected_sha = digest(gm.ft.planes_to_rgb(expected_planes).tobytes())
            check_ms = (time.perf_counter_ns() - start) / 1e6
            start = time.perf_counter_ns()
            actual, meta = dec.receive(packet)
            decode_ms = (time.perf_counter_ns() - start) / 1e6
            actual_sha = digest(actual.tobytes())
            if expected_sha != actual_sha:
                raise AssertionError(('GM01 sender/receiver reconstruction mismatch', i))
            if not enc.ack(i, epoch=1) or enc.pending:
                raise AssertionError('GM01 immediate ACK did not drain credit')
            if (enc.anchor_id, dec.anchor_id) != (i // 30 * 30,) * 2:
                raise AssertionError('GM01 unexpected anchor change')
            if digest(rgb.tobytes()) != source_sha:
                raise AssertionError('GM01 modified source RGB')
            crc = struct.unpack('<I', packet[-4:])[0]
            if crc != zlib.crc32(packet[:-4]):
                raise AssertionError('GM01 outer CRC mismatch')
            stream.write(packet)
            stream_hash.update(packet)
            headers = gm.HEADER.unpack_from(packet)
            packets.append(dict(id=i, pts=i, dts=i, bytes=len(packet), is_key=prepared.key,
                                key=prepared.key, reference_id=meta['reference_id'],
                                sha256=digest(packet), source_rgb_sha256=source_sha,
                                decoded_rgb_sha256=actual_sha, expected_rgb_sha256=expected_sha,
                                offset=offset, stream_path=str(stream_path.resolve()),
                                outer_header_bytes=gm.HEADER.size, outer_crc32_bytes=4,
                                outer_crc32=f'{crc:08x}', map_bytes=meta['map_bytes'],
                                nested_plane_bytes=list(headers[-3:]), dx=meta['dx'], dy=meta['dy']))
            decode_calls.append(dict(id=i, packet_pts=i, emitted_pts=[i], output_pts=[i],
                                     elapsed_ms=decode_ms, decode_ms=decode_ms))
            checks.append(dict(id=i, sender_reconstruction_ms=check_ms, expected_hash_matches=True))
            outputs.append(actual)
            offset += len(packet)
    info = dict(profile=profile, parameter=parameter, codec='GM01',
                implementation='older Python GM01 actual fresh-RGB encoder/decoder control',
                current_cu66_equivalent=False, fps=fps, width=w, height=h,
                key_interval=30, key_ids=[p['id'] for p in packets if p['is_key']],
                key_packet_bytes=[p['bytes'] for p in packets if p['is_key']],
                motion_mode=motion, quant_scale=scale, byte_cap=None, dropped_frames=0,
                adaptive_quantization=False, reference_policy='immutable reconstructed key; P never advances reference',
                feedback_policy='immediate in-process ACK after successful receive; no serialized ACK bytes',
                packets=packets, input_calls=encode_calls, frame_calls=encode_calls, encode_calls=encode_calls,
                decode_calls=decode_calls, verification_calls=checks, packets_only_at_flush=0,
                extradata_bytes=0, total_bytes=offset,
                stream=dict(path=str(stream_path.resolve()), bytes=offset, sha256=stream_hash.hexdigest(),
                            framing='concatenated complete GM01 packets; packet offsets and lengths in records'),
                timing_scope='measured Python wall time; encode analyze+candidate+commit; decode receive; '
                             'excludes verification hashes/reconstruction, file IO and ACK; no FPGA cycle or FPS inference',
                reference_memory=dict(logical_yuv420_u8_bytes_per_endpoint=reference_samples,
                                      logical_sender_plus_receiver_bytes=2 * reference_samples,
                                      measured_encoder_numpy_reference_bytes=enc.retained_reference_bytes(),
                                      measured_decoder_numpy_reference_bytes=sum(p.nbytes for p in dec._anchor),
                                      numpy_sample_dtype='int16', peak_pending_credits=enc.peak_pending,
                                      scope='retained immutable key only; excludes source/output/candidate/coefficient arrays, '
                                            'packet storage and Python allocator overhead; no physical RAM proof'),
                color_contract='same fixed_codec.rgb_to_planes / planes_to_rgb used by '
                               'python-game-standard-study/common_color.py via b.gm.ft; full-range integer YUV420',
                source_sha256=pins)
    if pins != _pins():
        raise AssertionError('GM01 source changed during run')
    (directory / (profile + '.json')).write_text(json.dumps(info, indent=2, allow_nan=False) + '\n')
    return outputs, info
