"""Measured native codec controls using the frozen GM01 sample-plane contract.

run returns RGB frames in source PTS order plus a JSON-serializable evidence dict.
Native CPU call times are reference measurements, never target hardware evidence.
"""
from fractions import Fraction
import base64
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import time

import av
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-codec-study'))
import game_codec as gm

ALIASES = {'hevc': 'libx265', 'libx265': 'libx265',
           'av1': 'libsvtav1', 'libsvtav1': 'libsvtav1',
           'jpeg': 'mjpeg', 'mjpeg': 'mjpeg'}


def options(codec, parameter):
    """Pinned, explicitly low-delay native encoder settings."""
    name = ALIASES.get(codec)
    if name == 'libx265':
        return {'preset': 'ultrafast', 'tune': 'zerolatency', 'crf': str(parameter),
                'x265-params': 'log-level=error:pools=none:frame-threads=1:wpp=0:'
                'bframes=0:rc-lookahead=0:keyint=30:min-keyint=30:scenecut=0:repeat-headers=1'}
    if name == 'libsvtav1':
        return {'preset': '8', 'crf': str(parameter),
                'svtav1-params': 'pred-struct=1:lookahead=0:enable-tf=0:scd=0:lp=1:tune=1'}
    if name == 'mjpeg':
        return {}
    raise ValueError('codec must be hevc/libx265, av1/libsvtav1 or jpeg/mjpeg')


def frame_from_planes(planes, pts, time_base, pixel_format='yuv420p'):
    h, w = planes[0].shape
    frame = av.VideoFrame(w, h, pixel_format)
    frame.pts, frame.time_base, frame.color_range = pts, time_base, 2
    for destination, source in zip(frame.planes, planes):
        buffer = np.zeros((destination.height, destination.line_size), np.uint8)
        buffer[:source.shape[0], :source.shape[1]] = source
        destination.update(buffer.tobytes())
    return frame


def planes_from_frame(frame):
    if frame.format.name not in ('yuv420p', 'yuvj420p'):
        raise AssertionError('native decoder changed sample format: ' + frame.format.name)
    return tuple(np.frombuffer(p, np.uint8).reshape(p.height, p.line_size)[:, :p.width].copy()
                 for p in frame.planes)


def _ms(start):
    return (time.perf_counter_ns() - start) / 1e6


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _jpeg_headers(data):
    """Read the emitted JPEG SOF/DQT/DRI markers, rather than infer from options."""
    found = []
    cursor = 0
    while cursor + 1 < len(data):
        if data[cursor:cursor + 2] == b'\xff\xd8':
            frame = {'sof_marker': None, 'sampling': [], 'quantization_tables': [],
                     'restart_interval': None}
            found.append(frame)
            cursor += 2
            continue
        if data[cursor] != 255:
            cursor += 1
            continue
        marker = data[cursor + 1]
        cursor += 2
        if marker in (0, 255, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if cursor + 2 > len(data):
            break
        length = int.from_bytes(data[cursor:cursor + 2], 'big')
        payload = data[cursor + 2:cursor + length]
        if length < 2 or len(payload) != length - 2:
            raise AssertionError('truncated JPEG marker')
        if marker == 0xC0:
            frame.update(sof_marker='SOF0 baseline sequential', precision=payload[0],
                         height=int.from_bytes(payload[1:3], 'big'),
                         width=int.from_bytes(payload[3:5], 'big'))
            frame['sampling'] = [{'id': payload[i], 'h': payload[i + 1] >> 4,
                                  'v': payload[i + 1] & 15, 'quant_table': payload[i + 2]}
                                 for i in range(6, 6 + payload[5] * 3, 3)]
        elif marker == 0xDB:
            i = 0
            while i < len(payload):
                precision, ident = payload[i] >> 4, payload[i] & 15
                size = 64 * (precision + 1)
                frame['quantization_tables'].append({'id': ident, 'precision_bits': 8 * (precision + 1),
                    'sha256': _digest(payload[i + 1:i + 1 + size])})
                i += 1 + size
        elif marker == 0xDD:
            frame['restart_interval'] = int.from_bytes(payload, 'big')
        cursor += length
    return found


def _inspect(stream, extradata, name, artifact_dir):
    import imageio_ffmpeg
    suffix, demux = {'libx265': ('hevc', 'hevc'), 'libsvtav1': ('obu', 'obu'),
                     'mjpeg': ('mjpeg', 'mjpeg')}[name]
    directory = Path(artifact_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stream_path = directory / ('stream.' + suffix)
    stream_path.write_bytes(stream)
    extra_path = directory / 'extradata.bin'
    extra_path.write_bytes(extradata)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    version = subprocess.run([ffmpeg, '-version'], capture_output=True, text=True, check=True).stdout
    command = [ffmpeg, '-hide_banner', '-loglevel', 'info', '-threads', '1', '-f', demux,
               '-i', str(stream_path), '-map', '0:v:0', '-c:v', 'copy',
               '-bsf:v', 'trace_headers', '-f', 'null', '-']
    if name == 'mjpeg':
        parsed = _jpeg_headers(stream)
        log = json.dumps({'parser': 'JPEG marker parser', 'frames': parsed}, indent=2) + '\n'
        inspection = {'method': 'JPEG SOF0/DQT/DRI marker parser', 'frames': parsed,
                      'temporal_references': 'JPEG SOF0 images have no inter-frame references'}
        returncode = 0
    else:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        log, returncode = result.stderr, result.returncode
        # Match exact syntax names, including repeated array entries. Distinct values
        # describe observed headers only; absence is never interpreted as a zero flag.
        fields = ('slice_type', 'sps_max_num_reorder_pics', 'sps_max_dec_pic_buffering_minus1',
                  'sample_adaptive_offset_enabled_flag', 'slice_sao_luma_flag',
                  'slice_sao_chroma_flag', 'strong_intra_smoothing_enabled_flag',
                  'pps_deblocking_filter_disabled_flag', 'slice_deblocking_filter_disabled_flag',
                  'deblocking_filter_control_present_flag', 'num_ref_idx_l0_default_active_minus1',
                  'num_ref_idx_l1_default_active_minus1', 'num_ref_idx_l0_active_minus1',
                  'num_ref_idx_l1_active_minus1', 'num_negative_pics', 'num_positive_pics',
                  'long_term_ref_pics_present_flag', 'used_by_curr_pic_s0_flag',
                  'used_by_curr_pic_s1_flag', 'num_short_term_ref_pic_sets',
                  'general_profile_idc', 'video_full_range_flag', 'frame_type', 'show_frame',
                  'show_existing_frame', 'ref_frame_idx', 'enable_cdef', 'enable_restoration',
                  'film_grain_params_present', 'enable_order_hint', 'reduced_still_picture_header',
                  'color_range', 'max_frame_width_minus_1', 'max_frame_height_minus_1',
                  'chroma_subsampling_x', 'chroma_subsampling_y', 'subsampling_x', 'subsampling_y',
                  'refresh_frame_flags', 'frame_refs_short_signaling', 'loop_filter_level',
                  'cdef_y_pri_strength', 'cdef_y_sec_strength', 'cdef_uv_pri_strength',
                  'cdef_uv_sec_strength', 'frame_restoration_type')
        observed = {}
        for field in fields:
            values = re.findall(r'\b' + field + r'(?:\[\d+\])*\s+[^\n=]*=\s*(-?\d+)\s*$', log, re.M)
            if values:
                observed[field] = {'values': sorted(set(map(int, values))), 'count': len(values)}
        inspection = {'method': 'FFmpeg trace_headers on retained emitted elementary stream',
                      'returncode': returncode, 'observed_syntax': observed,
                      'interpretation': 'Observed values only. Reference indices/filter availability do not prove maximum live references, filter execution or target memory.'}
    (directory / 'syntax.log').write_text(log)
    (directory / 'ffmpeg-version.txt').write_text(version)
    return {'stream_path': str(stream_path), 'extradata_path': str(extra_path),
            'syntax_log_path': str(directory / 'syntax.log'), 'ffmpeg_version': version,
            'inspection_command': command if name != 'mjpeg' else None,
            'inspection': inspection, 'inspection_returncode': returncode}


def run(frames, codec, parameter, fps=Fraction(30, 1), output_dir=None):
    """Encode/decode one sequence; JPEG parameter is qscale, HEVC/AV1 is CRF.

    output_dir retains exact elementary bytes, extradata, emitted-header inspection
    and FFmpeg version. Without it, bytes and syntax log are embedded in info.
    Only one encoder is created per call; callers must serialize calls themselves.
    """
    requested = options(codec, parameter)
    name = ALIASES[codec]
    if not len(frames):
        raise ValueError('nonempty RGB frame sequence required')
    fps = Fraction(fps)
    if fps <= 0:
        raise ValueError('fps must be positive')
    if isinstance(parameter, bool) or int(parameter) != parameter:
        raise ValueError('quality parameter must be an integer')
    if not (1 <= parameter <= 31 if name == 'mjpeg' else 0 <= parameter <= (51 if name == 'libx265' else 63)):
        raise ValueError('quality parameter outside encoder range')
    for rgb in frames:
        if not isinstance(rgb, np.ndarray) or rgb.shape != (480, 720, 3) or rgb.dtype != np.uint8:
            raise ValueError('each source must be 720x480 RGB uint8')
    tb = 1 / fps
    enc = av.CodecContext.create(name, 'w')
    enc.width, enc.height, enc.pix_fmt = 720, 480, 'yuvj420p' if name == 'mjpeg' else 'yuv420p'
    enc.time_base, enc.framerate, enc.thread_count = tb, fps, 1
    enc.gop_size, enc.max_b_frames, enc.color_range = 30, 0, 2
    enc.options = requested.copy()
    if name == 'mjpeg':
        enc.flags |= av.codec.context.Flags.qscale
        enc.global_quality = int(parameter) * 118  # FF_QP2LAMBDA in libavcodec/defs.h.
        enc.qmin = enc.qmax = int(parameter)
    started = time.perf_counter_ns()
    enc.open()
    encoder_open_ms = _ms(started)
    unconsumed = dict(enc.options)
    if unconsumed:
        raise AssertionError(('unconsumed encoder options', unconsumed))
    dec = av.CodecContext.create({'libx265': 'hevc', 'libsvtav1': 'libdav1d', 'mjpeg': 'mjpeg'}[name], 'r')
    dec.thread_count = 1
    dec.thread_type = 'SLICE'
    extra = enc.extradata or b''
    if extra:
        dec.extradata = extra
    started = time.perf_counter_ns()
    dec.open()
    decoder_open_ms = _ms(started)
    packets, calls, decode_calls, outputs, availability = [], [], [], {}, []
    chunks = []
    first_packet = None

    def accept(decoded, submitted_index, phase, decode_started_ns):
        conversion_ms = 0.0
        for frame in decoded:
            if frame.pts is None or frame.pts in outputs or not 0 <= frame.pts < len(frames):
                raise AssertionError(('missing/duplicate/out-of-range decoded PTS', frame.pts))
            if frame.pts > submitted_index:
                raise AssertionError('decoder output preceded source submission')
            tick = time.perf_counter_ns()
            outputs[frame.pts] = gm.ft.planes_to_rgb(planes_from_frame(frame))
            conversion_ms += _ms(tick)
            availability.append({'pts': frame.pts, 'after_input_index': submitted_index,
                                 'input_lag_frames': submitted_index - frame.pts, 'phase': phase,
                                 'sequence_processing_elapsed_ms': _ms(sequence_started_ns),
                                 'decode_call_start_to_rgb_ready_ms': _ms(decode_started_ns),
                                 'decoded_pixel_format': frame.format.name, 'decoded_color_range': frame.color_range})
        return conversion_ms

    def consume(batch, submitted_index, phase):
        nonlocal first_packet
        for packet in batch:
            if packet.pts is None or packet.dts is None or packet.pts > submitted_index:
                raise AssertionError(('unassociated/future packet PTS/DTS', packet.pts, packet.dts))
            data = bytes(packet)
            chunks.append(data)
            record = {'pts': packet.pts, 'dts': packet.dts, 'bytes': len(data),
                      'sha256': _digest(data), 'is_keyframe': packet.is_keyframe,
                      'after_input_index': submitted_index, 'input_lag_frames': submitted_index - packet.pts,
                      'sequence_processing_elapsed_ms': _ms(sequence_started_ns),
                      'phase': phase}
            packets.append(record)
            if first_packet is None:
                first_packet = dict(record)
            copied = av.Packet(data)
            copied.pts, copied.dts, copied.time_base = packet.pts, packet.dts, tb
            tick = time.perf_counter_ns()
            decoded = dec.decode(copied)
            decode_ms = _ms(tick)
            conversion_ms = accept(decoded, submitted_index, phase, tick)
            decode_calls.append({'packet_index': len(packets) - 1, 'packet_pts': packet.pts,
                                 'decode_call_ms': decode_ms, 'decode_ms': decode_ms, 'rgb_convert_ms': conversion_ms,
                                 'output_pts': [f.pts for f in decoded], 'after_input_index': submitted_index,
                                 'phase': phase})

    sequence_started_ns = time.perf_counter_ns()
    for index, rgb in enumerate(frames):
        started = time.perf_counter_ns()
        planes = gm.ft.rgb_to_planes(rgb)
        color_ms = _ms(started)
        started = time.perf_counter_ns()
        frame = frame_from_planes(planes, index, tb, enc.pix_fmt)
        plane_copy_ms = _ms(started)
        started = time.perf_counter_ns()
        batch = enc.encode(frame)
        encode_ms = _ms(started)
        calls.append({'id': index, 'rgb_to_planes_ms': color_ms, 'plane_copy_ms': plane_copy_ms,
                      'convert_ms': color_ms + plane_copy_ms, 'encode_call_ms': encode_ms,
                      'emitted_pts': [p.pts for p in batch], 'emitted_bytes': sum(p.size for p in batch)})
        consume(batch, index, 'input')
    started = time.perf_counter_ns()
    tail = enc.encode(None)
    encode_flush_ms = _ms(started)
    consume(tail, len(frames) - 1, 'encoder_flush')
    started = time.perf_counter_ns()
    decoded_tail = dec.decode(None)
    decode_flush_ms = _ms(started)
    decode_flush_convert_ms = accept(decoded_tail, len(frames) - 1, 'decoder_flush', started)
    sequence_processing_ms = _ms(sequence_started_ns)
    if sorted(outputs) != list(range(len(frames))):
        raise AssertionError(('incomplete decoded output', sorted(outputs)))
    stream = b''.join(chunks)
    info = {'encoder': name, 'parameter': parameter, 'parameter_kind': 'qscale' if name == 'mjpeg' else 'crf',
            'requested_options': requested, 'unconsumed_options': unconsumed,
            'requested_context': {'thread_count': 1, 'gop_size': 30, 'max_b_frames': 0, 'color_range': 2,
                                  'pixel_format': enc.pix_fmt, 'decoder_thread_count': 1, 'decoder_thread_type': 'SLICE',
                                  'jpeg_global_quality': int(parameter) * 118 if name == 'mjpeg' else None},
            'width': 720, 'height': 480, 'fps': str(fps), 'time_base': str(tb), 'input_frames': len(frames),
            'packets': packets, 'frame_calls': calls, 'decode_calls': decode_calls,
            'encoder_open_ms': encoder_open_ms, 'decoder_open_ms': decoder_open_ms,
            'encode_flush_ms': encode_flush_ms, 'decode_flush_ms': decode_flush_ms,
            'decode_flush_rgb_convert_ms': decode_flush_convert_ms,
            'packets_returned_only_at_flush': len(tail), 'decoded_frames_only_at_flush': len(decoded_tail),
            'first_packet': first_packet, 'first_decoded_output': availability[0] if availability else None,
            'first_packet_elapsed_ms': first_packet['sequence_processing_elapsed_ms'] if first_packet else None,
            'first_decoded_output_elapsed_ms': availability[0]['sequence_processing_elapsed_ms'] if availability else None,
            'sequence_processing_ms': sequence_processing_ms,
            'timing_fences': {
                'sequence_processing': 'Starts immediately before input0 RGB-to-plane conversion, after encoder/decoder open. Encode and decode are interleaved per emitted packet; ends after final decoder flush conversion. Includes Python bookkeeping, excludes artifact writes/header inspection. Preloaded unpaced software sequence, not capture-to-display latency.',
                'first_packet_elapsed_ms': 'Sequence processing start to first native encoded packet observed in Python, before that packet is decoded.',
                'first_decoded_output_elapsed_ms': 'Sequence processing start to first RGB output from the interleaved native decoder and canonical inverse.',
                'decode_call_start_to_rgb_ready_ms': 'Start of this packet decode call to canonical RGB output readiness, independent of encoder/open/previous packet costs.',
                'encode_call_ms': 'Only AVCodecContext.encode call; excludes color conversion and plane copying.',
                'decode_ms': 'Only AVCodecContext.decode call; excludes canonical inverse conversion.'},
            'output_availability': availability, 'output_pts': [item['pts'] for item in availability],
            'extradata_bytes': len(extra), 'elementary_stream_bytes': len(stream),
            'coded_bytes': len(stream) + len(extra), 'elementary_stream_sha256': _digest(stream),
            'extradata_sha256': _digest(extra),
            'versions': {'python': platform.python_version(), **{p: importlib.metadata.version(p) for p in ('numpy', 'av', 'imageio-ffmpeg')}},
            'codec_library_versions': {k: list(v) for k, v in av.library_versions.items()},
            'color_contract': 'GM01 frozen gm.ft.rgb_to_planes and gm.ft.planes_to_rgb for every codec; full-range 8-bit YUV420 samples, no swscale RGB conversion',
            'color_implementation_path': str(Path(gm.ft.__file__).resolve()),
            'color_implementation_sha256': _digest(Path(gm.ft.__file__).read_bytes()),
            'scope': 'Native CPU software call timing and emitted stream evidence only. Preloaded RGB; no capture/network/display, FPGA decoding, target memory, or hardware throughput proof. Codec reference policy differs from GM01.'}
    if output_dir is None:
        with tempfile.TemporaryDirectory(prefix='v98-standard-') as temp:
            artifacts = _inspect(stream, extra, name, temp)
            info['elementary_stream_base64'] = base64.b64encode(stream).decode('ascii')
            info['extradata_base64'] = base64.b64encode(extra).decode('ascii')
            info['syntax_log'] = Path(artifacts.pop('syntax_log_path')).read_text()
            artifacts.pop('stream_path')
            artifacts.pop('extradata_path')
            info.update(artifacts)
    else:
        info.update(_inspect(stream, extra, name, output_dir))
    return [outputs[i] for i in range(len(frames))], info
