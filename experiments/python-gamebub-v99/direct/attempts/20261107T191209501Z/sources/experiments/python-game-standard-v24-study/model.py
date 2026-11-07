"""Native low-delay HEVC/AV1 comparison with frozen Gamebub color arithmetic.

This module supplies host CPU reference codecs, not a Gamebub standards decoder.
"""
from fractions import Fraction
from pathlib import Path
import hashlib
import importlib.util
import math
import sys
import time
import av
import numpy as np

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


joint = load_module('standard24_frozen_joint', HERE.parent / 'python-game-hd22-joint-study/model.py')
C = joint.C
TB = Fraction(1, 30)
KEY_INTERVAL = 24
CAP = 49152
RECTANGLES = joint.hc.RECTANGLES


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def options(name, parameter):
    if type(parameter) is not int or not 0 <= parameter <= 63:
        raise ValueError('bounded integer quality parameter')
    if name == 'libx265':
        if parameter > 51:
            raise ValueError('x265 quality domain')
        return dict(preset='ultrafast', tune='zerolatency', crf=str(parameter),
                    **{'x265-params': 'log-level=error:pools=none:frame-threads=1:wpp=0:ref=1:bframes=0:rc-lookahead=0:keyint=24:min-keyint=24:scenecut=0:repeat-headers=1:range=full'})
    if name == 'libsvtav1':
        return dict(preset='8', crf=str(parameter),
                    **{'svtav1-params': 'pred-struct=1:lookahead=0:enable-tf=0:scd=0:lp=1:tune=1'})
    raise ValueError('explicit HEVC/AV1 encoder required')


def frame_from_planes(planes, pts):
    if type(pts) is not int or pts < 0 or len(planes) != 3:
        raise ValueError('three planes and nonnegative PTS')
    h, w = planes[0].shape
    if w % 2 or h % 2 or w < 2 or h < 2 or w * h > 720 * 480:
        raise ValueError('bounded even 420 geometry')
    if [p.shape for p in planes] != [(h, w), (h // 2, w // 2), (h // 2, w // 2)]:
        raise ValueError('420 plane shapes')
    for p in planes:
        if not isinstance(p, np.ndarray) or p.dtype.kind not in 'ui' or np.any(p < 0) or np.any(p > 255):
            raise ValueError('8-bit sample domain')
    frame = av.VideoFrame(w, h, 'yuv420p')
    frame.pts = pts
    frame.time_base = TB
    frame.color_range = 2
    if pts % KEY_INTERVAL == 0:
        frame.pict_type = av.video.frame.PictureType.I
    for target, source in zip(frame.planes, planes):
        buf = np.zeros((target.height, target.line_size), np.uint8)
        buf[:source.shape[0], :source.shape[1]] = source
        target.update(buf.tobytes())
    return frame


def planes_from_frame(frame):
    if frame.format.name not in ('yuv420p', 'yuvj420p'):
        raise ValueError('only decoded eight-bit planar420 is accepted')
    return tuple(np.frombuffer(p, np.uint8).reshape(p.height, p.line_size)[:, :p.width].copy()
                 for p in frame.planes)


def metric(source, display):
    if source.shape != (480, 720) or display.shape != source.shape or source.dtype != np.uint16 or display.dtype != np.uint16:
        raise ValueError('fixed full RGB565 canvases required')
    a = C.corpus.expand565(source).astype(np.int32)
    b = C.corpus.expand565(display).astype(np.int32)
    error = (a - b).astype(np.int64) ** 2
    total = int(error[37:442].sum())
    count = 405 * 720 * 3
    hud_errors = sum(int(np.count_nonzero(source[y:y+h, x:x+w] != display[y:y+h, x:x+w])) for x, y, w, h in RECTANGLES)
    hud_sse = sum(int(error[y:y+h, x:x+w].sum()) for x, y, w, h in RECTANGLES)
    mse = total / count
    return dict(active_squared_error=total, active_channel_samples=count,
                active_mse=mse, active_psnr_db=None if not mse else 10 * math.log10(65025 / mse),
                hud_word_errors=hud_errors, hud_squared_channel_error=hud_sse,
                hud_channel_samples=21120 * 3)


def overlay(display, patches):
    out = display.copy()
    if len(patches) != 4:
        raise ValueError('four exact HUD regions required')
    for rect, words in zip(RECTANGLES, patches):
        x, y, w, h = rect
        if words.shape != (h, w) or words.dtype != np.uint16:
            raise ValueError('fixed HUD patch')
        out[y:y+h, x:x+w] = words
    return out


def accounting(base_bytes, hud_bytes=0, *, binding=False):
    if type(base_bytes) is not int or base_bytes < 0 or type(hud_bytes) is not int or hud_bytes < 0:
        raise ValueError('nonnegative byte counts')
    body = base_bytes + hud_bytes + (57 if binding else 0)
    fragments = math.ceil(body / 1008)
    return dict(body_bytes=body, under_complete_cap=body <= CAP,
                forward_data_ip_udp_bytes=body + fragments * 75,
                frame_forward_control_bytes=128,
                reverse_model_bytes=fragments * 57 + 192 + 134 + 28,
                fragments=fragments)


def make_encoder(name, parameter, width, height):
    enc = av.CodecContext.create(name, 'w')
    enc.width, enc.height = width, height
    enc.pix_fmt = 'yuv420p'
    enc.time_base = TB
    enc.framerate = Fraction(30, 1)
    enc.thread_count = 1
    enc.gop_size = KEY_INTERVAL
    enc.max_b_frames = 0
    enc.color_range = 2
    requested = options(name, parameter)
    enc.options = requested.copy()
    started = time.perf_counter_ns()
    enc.open()
    open_ms = (time.perf_counter_ns() - started) / 1e6
    if enc.options:
        raise ValueError('unconsumed options: ' + repr(enc.options))
    return enc, requested, open_ms


def encode(planes, name, parameter):
    if not planes:
        raise ValueError('nonempty source sequence')
    h, w = planes[0][0].shape
    enc, requested, open_ms = make_encoder(name, parameter, w, h)
    packets, calls = [], []
    for index, source in enumerate(planes):
        start = time.perf_counter_ns()
        frame = frame_from_planes(source, index)
        frame_ms = (time.perf_counter_ns() - start) / 1e6
        start = time.perf_counter_ns()
        emitted = enc.encode(frame)
        encode_ms = (time.perf_counter_ns() - start) / 1e6
        for p in emitted:
            packets.append(dict(pts=p.pts, dts=p.dts, is_key=bool(p.is_keyframe), data=bytes(p)))
        calls.append(dict(id=index, plane_frame_wrap_ms=frame_ms, encode_ms=encode_ms,
                          emitted_pts=[p.pts for p in emitted], emitted_bytes=sum(p.size for p in emitted)))
    start = time.perf_counter_ns()
    tail = enc.encode(None)
    flush_ms = (time.perf_counter_ns() - start) / 1e6
    for p in tail:
        packets.append(dict(pts=p.pts, dts=p.dts, is_key=bool(p.is_keyframe), data=bytes(p)))
    extras = bytes(enc.extradata or b'')
    return packets, extras, dict(encoder=name, parameter=parameter, requested_options=requested,
                                 unconsumed_options=dict(enc.options), encoder_open_ms=open_ms,
                                 encoder_flush_ms=flush_ms, packets_only_at_flush=len(tail),
                                 frame_calls=calls, width=w, height=h,
                                 requested_gop=KEY_INTERVAL, requested_time_base=str(TB),
                                 library_versions={k: list(v) for k, v in av.library_versions.items()})


def decode(packets, extras, name):
    decoder = av.CodecContext.create('hevc' if name == 'libx265' else 'libdav1d', 'r')
    decoder.thread_count = 1
    if extras:
        decoder.extradata = extras
    outputs, calls = {}, []
    for p in packets:
        packet = av.Packet(p['data'])
        packet.pts, packet.dts, packet.time_base = p['pts'], p['dts'], TB
        start = time.perf_counter_ns()
        frames = decoder.decode(packet)
        decode_ms = (time.perf_counter_ns() - start) / 1e6
        converted_ms = 0.0
        for f in frames:
            start = time.perf_counter_ns()
            words = C.corpus.rgb565(C.gm.ft.planes_to_rgb(planes_from_frame(f)))
            converted_ms += (time.perf_counter_ns() - start) / 1e6
            if f.pts in outputs:
                raise ValueError('duplicate native decoded ID')
            outputs[f.pts] = words
        calls.append(dict(packet_pts=p['pts'], decode_ms=decode_ms,
                          frozen_display_convert_ms=converted_ms, output_pts=[f.pts for f in frames],
                          decoded_color_ranges=[int(f.color_range) for f in frames]))
    start = time.perf_counter_ns()
    tail = decoder.decode(None)
    flush_ms = (time.perf_counter_ns() - start) / 1e6
    for f in tail:
        if f.pts in outputs:
            raise ValueError('duplicate native flushed ID')
        outputs[f.pts] = C.corpus.rgb565(C.gm.ft.planes_to_rgb(planes_from_frame(f)))
    return outputs, dict(decoder='hevc' if name == 'libx265' else 'libdav1d', decode_calls=calls,
                         decoder_flush_ms=flush_ms, frames_only_at_decode_flush=len(tail))
