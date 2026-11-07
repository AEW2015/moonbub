"""Opt-in V97 transport study. Big endian, explicit setup ACK, no runtime advertising.

This module is independent of MSV1. Research profiles describe opaque transport
only; their decoder/reference reset semantics are deliberately not claimed.
"""
from dataclasses import dataclass, replace
import struct
import zlib

SETUP = struct.Struct('!4sBBHIIHHIHHIII')
FRAGMENT = struct.Struct('!IIHBB')
START = struct.Struct('!IIQ')
VERSION, REQUEST, ACK, DATA = 97, 1, 2, 3
SOF, EOF = 1, 2
JPEG, JPEG_CAP, RESEARCH_CAP = 1, 262144, 49152
CAP_JPEG, CAP_OPAQUE = 1, 2
RESEARCH = tuple(int.from_bytes(s, 'big') for s in (b'CS92', b'CS94', b'CS95', b'CS96'))


def newer(value, previous):
    return 0 < ((value - previous) & 0xffffffff) < 0x80000000


@dataclass(frozen=True)
class SinkConfig:
    # Separate receiver-only configuration; not inferred from sender caps.
    opaque_profile: int | None = None


@dataclass(frozen=True)
class Session:
    epoch: int
    profile: int = JPEG
    width: int = 720
    height: int = 480
    frame_cap: int = JPEG_CAP
    payload_size: int = 1400
    flags: int = 0
    sink_caps: int = CAP_JPEG
    core_generation: int = 1

    def validate(self, config=SinkConfig()):
        if not 0 < self.epoch <= 0xffffffff or not 0 < self.core_generation <= 0xffffffff:
            raise ValueError('epoch')
        if (self.width, self.height) != (720, 480) or self.payload_size not in (1024, 1400) or self.flags:
            raise ValueError('format')
        if self.profile == JPEG:
            if self.frame_cap != JPEG_CAP or self.sink_caps != CAP_JPEG:
                raise ValueError('capability')
        elif not (self.profile in RESEARCH and config.opaque_profile == self.profile
                  and self.frame_cap == RESEARCH_CAP and self.sink_caps == CAP_OPAQUE):
            raise ValueError('capability')
        return self

    def encode(self, kind=REQUEST):
        if kind not in (REQUEST, ACK):
            raise ValueError('kind')
        return SETUP.pack(b'MB97', VERSION, kind, SETUP.size, self.epoch, self.profile,
                          self.width, self.height, self.frame_cap, self.payload_size,
                          self.flags, self.sink_caps, self.core_generation, 0)


def parse_session(data, kind=REQUEST, config=SinkConfig()):
    if len(data) != SETUP.size:
        raise ValueError('setup_length')
    magic, version, actual_kind, length, epoch, profile, width, height, cap, payload, flags, caps, core, reserved = SETUP.unpack(data)
    if magic != b'MB97' or version != VERSION or actual_kind != kind or length != SETUP.size or reserved:
        raise ValueError('setup_header')
    return Session(epoch, profile, width, height, cap, payload, flags, caps, core).validate(config)


class HostSession:
    """Sender cannot packetize until an exact compatible ACK has arrived."""
    def __init__(self, session, config=SinkConfig()):
        self.session = session.validate(config)
        self.config = config
        self.acknowledged = False

    def request(self):
        return self.session.encode()

    def accept_ack(self, data):
        if parse_session(data, ACK, self.config) != self.session:
            raise ValueError('ack_mismatch')
        self.acknowledged = True

    def packets(self, payload, frame_id, capture_us):
        if not self.acknowledged:
            raise ValueError('setup_unacknowledged')
        if not 0 < len(payload) <= self.session.frame_cap:
            raise ValueError('frame_bounds')
        crc = zlib.crc32(payload)
        for index, offset in enumerate(range(0, len(payload), self.session.payload_size)):
            part = payload[offset:offset + self.session.payload_size]
            flags = (SOF if index == 0 else 0) | (EOF if offset + len(part) == len(payload) else 0)
            header = FRAGMENT.pack(self.session.epoch, frame_id & 0xffffffff, index, DATA, flags)
            if index == 0:
                header += START.pack(len(payload), crc, capture_us)
            yield header + part


@dataclass(frozen=True)
class Chunk:
    epoch: int
    frame_id: int
    index: int
    offset: int
    length: int
    crc: int
    capture_us: int
    payload: bytes
    crc_complete: bool


class Receiver:
    """Bounded metadata oracle. Caller streams bytes; CRC completion is not commit.

    A transfer error requires a downstream abort/drain. Session installation here
    models the wire parser only; the Rust Gateway enforces the DMA drain barrier.
    """
    def __init__(self, config=SinkConfig(), core_generation=1):
        self.config = config
        self.core_generation = core_generation
        self.session = None
        self.retired_epoch = None
        self.last_id = None
        self.abort()

    def abort(self):
        self.active = None
        self.offset = self.index = self.crc = 0

    def reset(self):
        if self.session:
            self.retired_epoch = self.session.epoch
        self.session = None
        self.last_id = None
        self.abort()

    def core_changed(self, generation):
        self.reset()
        self.core_generation = generation

    def setup(self, data):
        s = parse_session(data, REQUEST, self.config)
        if s.core_generation != self.core_generation:
            raise ValueError('core')
        if s == self.session:
            return s.encode(ACK)  # Exact retransmission preserves frame history.
        previous = self.session.epoch if self.session else self.retired_epoch
        if previous is not None and not newer(s.epoch, previous):
            raise ValueError('epoch')
        self.reset()
        self.session = s
        return s.encode(ACK)

    def accept(self, data):
        try:
            return self._accept(data)
        except (ValueError, struct.error):
            self.abort()
            raise ValueError('packet_rejected') from None

    def _accept(self, data):
        if self.session is None or len(data) < FRAGMENT.size:
            raise ValueError('session/header')
        epoch, fid, index, kind, flags = FRAGMENT.unpack_from(data)
        if epoch != self.session.epoch or kind != DATA or flags & ~3 or bool(flags & SOF) != (index == 0):
            raise ValueError('format/epoch')
        base = FRAGMENT.size
        if index == 0:
            if len(data) < base + START.size or (self.last_id is not None and not newer(fid, self.last_id)):
                raise ValueError('start/history')
            total, crc, capture = START.unpack_from(data, base)
            if not 0 < total <= self.session.frame_cap:
                raise ValueError('bounds')
            self.active = fid, total, crc, capture
            self.offset = self.index = self.crc = 0
            self.last_id = fid
            base += START.size
        if self.active is None:
            raise ValueError('missing_start')
        afid, total, crc, capture = self.active
        part = data[base:]
        if fid != afid or index != self.index or index * self.session.payload_size != self.offset:
            raise ValueError('sequence')
        if len(part) != min(self.session.payload_size, total - self.offset) or not part:
            raise ValueError('bounds')
        done = self.offset + len(part) == total
        if bool(flags & EOF) != done:
            raise ValueError('final')
        offset = self.offset
        self.crc = zlib.crc32(part, self.crc)
        self.offset += len(part)
        self.index += 1
        if done:
            if self.crc != crc:
                raise ValueError('crc')
            self.active = None
        return Chunk(epoch, fid, index, offset, total, crc, capture, part, done)
