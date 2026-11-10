"""MSV1 test video datagrams. All multibyte wire fields are big endian."""
from dataclasses import dataclass
import struct
import zlib

VIDEO = struct.Struct("!4sBBHIHHIIHHIQ")
FEEDBACK = struct.Struct("!4sBBHIIIIQ")
MAX_FRAME = 256 * 1024
MAX_PAYLOAD = 1024
SOF, EOF = 1, 2


@dataclass(frozen=True)
class Packet:
    frame_id: int
    width: int
    height: int
    frame_len: int
    offset: int
    crc32: int
    capture_us: int
    flags: int
    payload: bytes


def parse_packet(data: bytes) -> Packet:
    if len(data) < VIDEO.size:
        raise ValueError("short MSV1 header")
    magic, version, codec, flags, fid, w, h, total, offset, size, reserved, crc, stamp = VIDEO.unpack_from(data)
    if magic != b"MSV1" or version != 1 or codec != 1 or reserved or flags & ~3:
        raise ValueError("unsupported MSV1 format")
    if (w, h) != (720, 480):
        raise ValueError("unsupported canvas")
    if not 0 < total <= MAX_FRAME or not 0 < size <= MAX_PAYLOAD:
        raise ValueError("invalid payload bounds")
    if len(data) != VIDEO.size + size or offset + size > total:
        raise ValueError("invalid datagram length or frame offset")
    if bool(flags & SOF) != (offset == 0) or bool(flags & EOF) != (offset + size == total):
        raise ValueError("invalid frame boundary flags")
    return Packet(fid, w, h, total, offset, crc, stamp, flags, data[VIDEO.size:])


def packets(jpeg: bytes, frame_id: int, capture_us: int, payload_size: int = MAX_PAYLOAD):
    if not 0 < len(jpeg) <= MAX_FRAME or not 0 < payload_size <= MAX_PAYLOAD:
        raise ValueError("frame/chunk exceeds protocol limit")
    crc = zlib.crc32(jpeg)
    for offset in range(0, len(jpeg), payload_size):
        payload = jpeg[offset:offset + payload_size]
        flags = (SOF if offset == 0 else 0) | (EOF if offset + len(payload) == len(jpeg) else 0)
        yield VIDEO.pack(b"MSV1", 1, 1, flags, frame_id & 0xffffffff, 720, 480,
                         len(jpeg), offset, len(payload), 0, crc, capture_us) + payload


@dataclass(frozen=True)
class Feedback:
    status: int
    buttons: int
    frame_id: int
    free_bytes: int
    received_frames: int
    dropped_frames: int
    capture_us: int


def parse_feedback(data: bytes) -> Feedback:
    if len(data) != FEEDBACK.size:
        raise ValueError("invalid MSF1 feedback length")
    magic, version, status, buttons, fid, free, received, dropped, stamp = FEEDBACK.unpack(data)
    if magic != b"MSF1" or version != 1 or status > 3:
        raise ValueError("unsupported feedback")
    return Feedback(status, buttons, fid, free, received, dropped, stamp)


class Reassembler:
    """Bounded one-frame reference sink. Lost/reordered chunks discard a frame.

    This is a host test oracle, not a requirement to buffer full JPEGs on ESP32.
    A new SOF supersedes an incomplete frame; no queue of stale frames exists.
    """
    def __init__(self):
        self.active = None
        self.data = bytearray()
        self.dropped = 0
        self.last_frame_id = None

    def reset(self, clear_history=True):
        self.active = None
        self.data.clear()
        if clear_history:
            self.last_frame_id = None

    def accept(self, datagram: bytes):
        try:
            p = parse_packet(datagram)
            if p.flags & SOF:
                if self.last_frame_id is not None:
                    delta = (p.frame_id - self.last_frame_id) & 0xffffffff
                    if not 0 < delta < 0x80000000:
                        raise ValueError("duplicate or stale frame ID")
                if self.active is not None:
                    self.dropped += 1
                self.reset(False)
                self.active = p
                self.last_frame_id = p.frame_id
            a = self.active
            if a is None or (p.frame_id, p.frame_len, p.crc32, p.capture_us) != (a.frame_id, a.frame_len, a.crc32, a.capture_us):
                raise ValueError("no matching frame start")
            if p.offset != len(self.data):
                raise ValueError("missing, duplicate, or reordered packet")
            self.data.extend(p.payload)
            if p.flags & EOF:
                result = bytes(self.data)
                if zlib.crc32(result) != p.crc32:
                    raise ValueError("frame CRC mismatch")
                self.reset(False)
                return p, result
            return None
        except ValueError:
            self.dropped += 1
            self.reset(False)
            raise
