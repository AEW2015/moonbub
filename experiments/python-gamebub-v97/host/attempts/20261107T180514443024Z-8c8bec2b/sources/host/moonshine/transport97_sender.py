"""Opt-in V97 PC preparation primitives; no live Sunshine/ESP32 integration.

An exact setup ACK is required before encoding/packetization. The queue retains
one latest prepared frame. Existing MSV1 sender/runtime behavior is unchanged.
"""
from dataclasses import dataclass
import hashlib
import time

from . import protocol97 as wire
from .encoding import encode, validate_jpeg


@dataclass(frozen=True)
class PreparedFrame:
    epoch: int
    frame_id: int
    capture_us: int
    payload: bytes
    datagrams: tuple[bytes, ...]
    timings_ns: dict

    @property
    def application_bytes(self):
        return sum(map(len, self.datagrams))

    @property
    def ipv4_udp_bytes(self):
        return self.application_bytes + 28 * len(self.datagrams)

    @property
    def payload_sha256(self):
        return hashlib.sha256(self.payload).hexdigest()


class LatestPrepared:
    """One unsent frame. An already taken in-flight frame is caller-owned.

    New epochs require an explicit clear, preventing silent old-session reuse.
    This synchronous policy object is not a thread-safe transport worker.
    """
    def __init__(self):
        self.pending = None
        self.last_identity = None
        self.replaced = 0

    def offer(self, frame):
        if self.last_identity is not None:
            epoch, fid = self.last_identity
            if frame.epoch != epoch or not wire.newer(frame.frame_id, fid):
                raise ValueError('stale frame or explicit session reset required')
        if self.pending is not None:
            self.replaced += 1
        self.pending = frame
        self.last_identity = frame.epoch, frame.frame_id

    def take(self):
        frame = self.pending
        self.pending = None
        return frame

    def clear(self):
        self.pending = self.last_identity = None


class Sender:
    def __init__(self, session, config=wire.SinkConfig()):
        self.host = wire.HostSession(session, config)
        self.config = config

    def setup_request(self):
        return self.host.request()

    def acknowledge(self, packet):
        self.host.accept_ack(packet)

    def _ready(self, frame_id, capture_us):
        if not self.host.acknowledged:
            raise ValueError('setup ACK required before host preparation')
        if not 0 <= frame_id <= 0xffffffff or not 0 <= capture_us <= 0xffffffffffffffff:
            raise ValueError('frame identity bounds')

    def prepare(self, image, frame_id, capture_us, quality=65, max_application_bytes=None):
        self._ready(frame_id, capture_us)
        if self.host.session.profile != wire.JPEG:
            raise ValueError('image preparation is JPEG-only')
        began = time.perf_counter_ns()
        payload = encode(image, quality=quality, subsampling='420')
        encoded = time.perf_counter_ns()
        result = self._packetize(payload, frame_id, capture_us, encoded, max_application_bytes)
        result.timings_ns.update(jpeg_encode_validate=encoded - began,
                                 complete_host_prepare=time.perf_counter_ns() - began)
        return result

    def prepare_bytes(self, payload, frame_id, capture_us, max_application_bytes=None):
        self._ready(frame_id, capture_us)
        began = time.perf_counter_ns()
        if self.host.session.profile == wire.JPEG:
            validate_jpeg(payload, expected=(720, 480), subsampling='420')
        elif self.config.opaque_profile != self.host.session.profile:
            raise ValueError('opaque research sink not explicitly configured')
        validated = time.perf_counter_ns()
        result = self._packetize(payload, frame_id, capture_us, validated, max_application_bytes)
        result.timings_ns.update(input_validate=validated - began,
                                 complete_host_prepare=time.perf_counter_ns() - began)
        return result

    def _packetize(self, payload, frame_id, capture_us, began, max_application_bytes):
        # Protocol generator charges CRC32, exact first-fragment metadata and
        # datagram allocation/copies. PC may retain complete frames; ESP may not.
        packets = tuple(self.host.packets(payload, frame_id, capture_us))
        if max_application_bytes is not None and sum(map(len, packets)) > max_application_bytes:
            raise ValueError('complete application-byte budget exceeded')
        return PreparedFrame(self.host.session.epoch, frame_id, capture_us,
                             bytes(payload), packets,
                             dict(crc_packetize=time.perf_counter_ns() - began))
