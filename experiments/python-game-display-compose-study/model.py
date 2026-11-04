"""Offline base/display-cache composition and necessary transport bounds.

CB21 is a bounded fixture container, not implemented endpoint negotiation.
Decoders remain separate; this module does not supply atomic joint publication.
"""
from pathlib import Path
import hashlib
import importlib.util
import math
import struct
import sys
import zlib

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


cache = load('compose21_cache', HERE.parent / 'python-game-hud-cache-study/model.py')
codec = cache.legacy.codec
HEADER = struct.Struct('<4sBIIII16s16s')
MAX_COMPONENT = 49152
FRAME_CAP = 49152
OVERHEAD = HEADER.size + 4


def digest(data):
    return hashlib.sha256(data).digest()[:16]


def strip_patches(packet):
    """Return a valid patch-free AR03 with identical inner bytes and YUV tags."""
    meta = codec.identity(packet, decode=True)
    values = list(codec.HEADER.unpack_from(packet))
    values[-2:] = [0, 0]
    result = codec.seal(codec.HEADER.pack(*values) + meta['inner'])
    stripped = codec.identity(result, decode=True)
    for name in ('epoch', 'frame_id', 'inner', 'reference_bank', 'reference_id',
                 'reference_tag', 'destination_bank', 'stored_tag'):
        if stripped[name] != meta[name]:
            raise AssertionError('stripping altered reference semantics')
    return result


def bind(base, hud):
    """Create a bounded offline pair fixture; report cap admission separately."""
    b, h = codec.identity(base), cache.parse(hud)
    if b['patch_count'] or (b['epoch'], b['frame_id']) != (h['epoch'], h['frame']):
        raise ValueError('base/cache pair identity')
    header = HEADER.pack(b'CB21', 1, b['epoch'], b['frame_id'], len(base), len(hud),
                         digest(base), digest(hud))
    return cache.seal(header + base + hud)


def unbind(packet, *, enforce_frame_cap=True):
    if type(packet) is not bytes or not OVERHEAD <= len(packet) <= 2 * MAX_COMPONENT + OVERHEAD:
        raise ValueError('bounded CB21 fixture length')
    if enforce_frame_cap and len(packet) > FRAME_CAP:
        raise ValueError('complete CB21 fixture exceeds development cap')
    if zlib.crc32(packet[:-4]) != struct.unpack('<I', packet[-4:])[0]:
        raise ValueError('CB21 CRC')
    magic, version, epoch, frame, nb, nh, bh, hh = HEADER.unpack_from(packet)
    if (magic, version) != (b'CB21', 1) or not 0 < nb <= MAX_COMPONENT or not 0 < nh <= MAX_COMPONENT:
        raise ValueError('CB21 header')
    if len(packet) != OVERHEAD + nb + nh:
        raise ValueError('CB21 exact length')
    base, hud = packet[HEADER.size:HEADER.size + nb], packet[HEADER.size + nb:-4]
    if (digest(base), digest(hud)) != (bh, hh):
        raise ValueError('CB21 content binding')
    b, h = codec.identity(base), cache.parse(hud)
    if b['patch_count'] or (epoch, frame) != (b['epoch'], b['frame_id']) or (epoch, frame) != (h['epoch'], h['frame']):
        raise ValueError('CB21 component identity')
    return base, hud


def transport_counts(body_bytes, hud_ack_bytes=0):
    """Necessary byte counts for a prospective single-frame GF03 carriage.

    One PC18 return per data fragment; two forward and three reverse FG19
    controls; one AF03 and, for CB21, one HA21. No RF/retry/QC18/input/audio.
    This accounting does not implement GF03/FG19 support for CB21.
    """
    if type(body_bytes) is not int or body_bytes <= 0 or type(hud_ack_bytes) is not int or hud_ack_bytes < 0:
        raise ValueError('positive body and nonnegative ACK bytes')
    fragments = math.ceil(body_bytes / 1008)
    return dict(body_bytes=body_bytes, fragments=fragments,
                data_forward_bytes=body_bytes + fragments * (31 + 16 + 28),
                frame_forward_control_bytes=2 * (36 + 28),
                frame_reverse_control_bytes=3 * (36 + 28),
                packet_credit_reverse_bytes=fragments * (29 + 28),
                reference_ack_reverse_bytes=43 + 28,
                hud_ack_reverse_bytes=(hud_ack_bytes + 28) if hud_ack_bytes else 0)


def necessary_network_bound(counts, link_mbps, feedback_delay_ms):
    """Optimistic stop/wait bound; independent symmetric virtual directions.

    Permits complete overlap between the two virtual directions, taking their
    maximum serialization time plus a supplied minimum propagation delay.
    Ignores CPU, grant RTT multiplicity, DMA/QSPI, display, contention and retries.
    Passing cannot prove a feasible frame rate. This is an optimistic planning
    bound under stated delay assumptions, not a discrete-event simulation.
    """
    if not math.isfinite(link_mbps) or link_mbps <= 0 or not math.isfinite(feedback_delay_ms) or feedback_delay_ms < 0:
        raise ValueError('finite positive link rate and nonnegative delay')
    forward = counts['data_forward_bytes'] + counts['frame_forward_control_bytes']
    reverse = sum(counts[k] for k in ('frame_reverse_control_bytes', 'packet_credit_reverse_bytes',
                                     'reference_ack_reverse_bytes', 'hud_ack_reverse_bytes'))
    forward_ms = 8 * forward / (link_mbps * 1000)
    reverse_ms = 8 * reverse / (link_mbps * 1000)
    service_ms = max(forward_ms, reverse_ms) + feedback_delay_ms
    return dict(link_mbps=link_mbps, feedback_delay_ms=feedback_delay_ms,
                forward_serialization_ms=forward_ms, reverse_serialization_ms=reverse_ms,
                network_only_stop_wait_ms=service_ms,
                optimistic_network_only_fps_ceiling=1000 / service_ms,
                necessary_30fps_condition=service_ms <= 1000 / 30)
