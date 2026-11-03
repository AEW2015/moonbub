"""@brief Experimental UDP5534 audio/control wire contract, independent of MSV1.

See MoonBub docs/av-wire-v1.md. Importing this module sends no network traffic.
CRC and session cookies provide correlation, not peer authentication.
"""

import struct
import zlib
from dataclasses import dataclass

HEADER = struct.Struct("!4sBBHQIIHHIQII")
INPUT = struct.Struct("!8I")
NONCE = struct.Struct("!Q")
RATE = 48293
FRAMES = 505
BLOCK = 512
PORT = 5534
LEASE_NS = 500_000_000
KEEP_NS = 100_000_000


def newer(current, previous):
    """@brief Compare wrapping32-bit sequence values; duplicates are not newer."""
    return previous is None or 0 < ((current - previous) & 0xFFFFFFFF) < 0x80000000


def validate_adpcm(block):
    """@brief Validate one independent stereo IMA WAV block before decoding."""
    if len(block) != BLOCK or block[2] > 88 or block[6] > 88 or block[3] or block[7]:
        raise ValueError("Expected512-byte stereo IMA WAV block with valid indices/reserved bytes")


@dataclass(frozen=True)
class Packet:
    """@brief Validated AV packet fields; payload bytes remain immutable."""

    magic: bytes
    kind: int
    session: int
    seq: int = 0
    flags: int = 0
    timestamp_us: int = 0
    payload: bytes = b""

    def encode(self):
        """@brief Serialize one schema-checked packet including whole-packet CRC."""
        _validate(self)
        samples = FRAMES if self.magic == b"MSA1" else 0
        raw = HEADER.pack(self.magic, 1, self.kind, HEADER.size, self.session,
                          self.seq, RATE, samples, len(self.payload), self.flags,
                          self.timestamp_us, 0, 0) + self.payload
        crc = zlib.crc32(raw) & 0xFFFFFFFF
        return raw[:40] + struct.pack("!I", crc) + raw[44:]


def _validate(packet):
    """@brief Reject unsupported packet classes, flags, payloads and integer bounds."""
    if (type(packet.session) is not int or not 0 < packet.session < 1 << 64
            or type(packet.seq) is not int or not 0 <= packet.seq < 1 << 32
            or type(packet.timestamp_us) is not int or not 0 <= packet.timestamp_us < 1 << 64
            or type(packet.payload) is not bytes):
        raise ValueError("Invalid AV integer or payload")
    key = packet.magic, packet.kind
    if key == (b"MSC1", 1):
        length, allowed = 0, 1
        if packet.seq != 0:
            raise ValueError("HELLO sequence must be0")
    elif key == (b"MSC1", 2):
        length, allowed = 8, 1
        if packet.seq != 1:
            raise ValueError("START sequence must be1")
    elif key in ((b"MSC1", 3), (b"MSC1", 4)):
        length, allowed = 0, 0
    elif key == (b"MSR1", 1):
        length, allowed = 8, 1
        if packet.seq != 0:
            raise ValueError("OFFER sequence must be0")
    elif key == (b"MSA1", 1):
        length, allowed = BLOCK, 0
        validate_adpcm(packet.payload)
    elif key == (b"MSI1", 1):
        length, allowed = INPUT.size, 0
        if len(packet.payload) == length:
            buttons, _, _, _, _, _, state, _ = INPUT.unpack(packet.payload)
            if buttons & ~0xFFF or state & ~7:
                raise ValueError("Unsupported input/status bits")
    else:
        raise ValueError("Unknown AV packet class")
    if type(packet.flags) is not int or packet.flags & ~allowed or packet.flags < 0:
        raise ValueError("Unsupported AV flags")
    if len(packet.payload) != length:
        raise ValueError("Invalid AV payload length")
    if length == 8 and NONCE.unpack(packet.payload)[0] == 0:
        raise ValueError("Zero nonce")


def decode(raw):
    """@brief Parse a complete datagram without permitting trailing or truncated bytes."""
    if not HEADER.size <= len(raw) <= HEADER.size + BLOCK:
        raise ValueError("Invalid AV datagram length")
    magic, version, kind, size, session, seq, rate, samples, length, flags, stamp, crc, reserved = HEADER.unpack_from(raw)
    if (version != 1 or size != HEADER.size or rate != RATE or reserved
            or len(raw) != size + length or samples != (FRAMES if magic == b"MSA1" else 0)):
        raise ValueError("Unsupported AV header")
    if zlib.crc32(raw[:40] + b"\0" * 4 + raw[44:]) & 0xFFFFFFFF != crc:
        raise ValueError("AV CRC mismatch")
    packet = Packet(magic, kind, session, seq, flags, stamp, bytes(raw[size:]))
    _validate(packet)
    return packet


class InputLease:
    """@brief Accept only independently ordered input for one pinned AV session."""

    def __init__(self, session, peer, dispatcher=None):
        """@brief Bind transport identity; optional dispatcher consumes12-bit masks."""
        self.session, self.peer, self.dispatcher = session, peer, dispatcher
        self.seq = self.last_ns = None
        self.status = None
        self.expired = False

    def accept(self, raw, peer, now_ns):
        """@brief Apply a newer ACTIVE MSI1, never renewing liveness on stale input."""
        packet = decode(raw)
        if (peer != self.peer or packet.magic != b"MSI1" or packet.session != self.session
                or not newer(packet.seq, self.seq)):
            return False
        values = INPUT.unpack(packet.payload)
        if not values[6] & 1:
            return False
        if self.last_ns is not None and now_ns < self.last_ns:
            raise ValueError("Monotonic clock moved backward")
        if self.dispatcher is not None:
            self.dispatcher.apply(values[0])
        self.seq, self.last_ns, self.status, self.expired = packet.seq, now_ns, values, False
        return True

    def expire(self, now_ns):
        """@brief Neutralize once after500ms without a strictly newer valid MSI1."""
        if self.last_ns is not None and now_ns - self.last_ns >= LEASE_NS and not self.expired:
            self.expired = True
            if self.dispatcher is not None:
                self.dispatcher.neutral()
            return True
        return False

    def close(self):
        """@brief Neutralize and detach the optional virtual controller."""
        if self.dispatcher is not None:
            self.dispatcher.close()
