"""Transport-neutral HC70/HR70 framing codec; endpoint policy is out of scope."""
from dataclasses import dataclass
import struct
import zlib


HEADER = struct.Struct('<4sBBHIQIII')
CRC = struct.Struct('<I')
MAGIC_REQUEST = b'HC70'
MAGIC_RESPONSE = b'HR70'
VERSION = 1
MAX_PAYLOAD = 49152
MAX_GENERATION = (1 << 64) - 1
MAX_U32 = (1 << 32) - 1

PREPARE = 1
STATUS = 2
READ_CANDIDATE = 3
ACK_EXTERNAL_WRITE_DRAIN = 4
COMMIT = 5
ABORT = 6
RESET = 7
RESET_QUIESCENT = 1
OPCODES = frozenset(range(PREPARE, RESET + 1))


class ProtocolError(ValueError):
    """Malformed or unsupported ABI frame."""


@dataclass(frozen=True)
class Message:
    magic: bytes
    opcode: int
    generation: int
    frame_id: int
    reference_id: int
    argument: int = 0
    payload: bytes = b''
    version: int = VERSION
    reserved: int = 0


def _validate(message, *, check_payload=True):
    if message.magic not in (MAGIC_REQUEST, MAGIC_RESPONSE):
        raise ProtocolError('unknown message magic')
    if message.version != VERSION:
        raise ProtocolError('unsupported ABI version')
    if message.opcode not in OPCODES:
        raise ProtocolError('unknown opcode')
    if message.reserved != 0:
        raise ProtocolError('reserved field must be zero')
    if not 0 <= message.generation <= MAX_GENERATION:
        raise ProtocolError('generation outside u64 range')
    if not 0 <= message.frame_id <= MAX_U32:
        raise ProtocolError('frame ID outside u32 range')
    if not 0 <= message.reference_id <= MAX_U32:
        raise ProtocolError('reference ID outside u32 range')
    if not 0 <= message.argument <= MAX_U32:
        raise ProtocolError('argument outside u32 range')
    if not isinstance(message.payload, bytes):
        raise ProtocolError('payload must be immutable bytes')
    if len(message.payload) > MAX_PAYLOAD:
        raise ProtocolError('payload exceeds 49152-byte limit')
    if check_payload and message.magic == MAGIC_REQUEST:
        if message.opcode == READ_CANDIDATE and len(message.payload) != 8:
            raise ProtocolError('READ_CANDIDATE request payload must be offset:u32,count:u32')
        if message.opcode == ACK_EXTERNAL_WRITE_DRAIN and len(message.payload) != 20:
            raise ProtocolError('ACK_EXTERNAL_WRITE_DRAIN payload must be word_count:u32,tag:16 bytes')
        if message.opcode in (COMMIT, ABORT, STATUS, RESET) and message.payload:
            raise ProtocolError('command request must have an empty payload')
        if message.opcode == RESET and message.argument != RESET_QUIESCENT:
            raise ProtocolError('RESET requires argument=1 (caller asserts quiescence)')


def encode(message):
    """Encode one complete message and CRC32(header || payload) trailer."""
    _validate(message)
    payload = message.payload
    header = HEADER.pack(message.magic, message.version, message.opcode,
                         message.reserved, len(payload), message.generation,
                         message.frame_id, message.reference_id, message.argument)
    return header + payload + CRC.pack(zlib.crc32(header + payload) & MAX_U32)


def decode(data):
    """Decode exactly one complete frame; trailing bytes are rejected."""
    view = memoryview(data)
    if len(view) < HEADER.size:
        raise ProtocolError('truncated header')
    fields = HEADER.unpack(view[:HEADER.size])
    magic, version, opcode, reserved, length, generation, frame_id, reference_id, argument = fields
    # Validate fixed fields and declared size before accepting or copying payload.
    probe = Message(magic, opcode, generation, frame_id, reference_id,
                    argument, b'', version, reserved)
    _validate(probe, check_payload=False)
    if length > MAX_PAYLOAD:
        raise ProtocolError('payload exceeds 49152-byte limit')
    total = HEADER.size + length + CRC.size
    if len(view) < total:
        raise ProtocolError('truncated payload or CRC trailer')
    if len(view) != total:
        raise ProtocolError('trailing bytes after frame')
    payload = bytes(view[HEADER.size:HEADER.size + length])
    expected_crc, = CRC.unpack(view[HEADER.size + length:total])
    if (zlib.crc32(view[:HEADER.size + length]) & MAX_U32) != expected_crc:
        raise ProtocolError('header+payload CRC32 mismatch')
    result = Message(magic, opcode, generation, frame_id, reference_id,
                     argument, payload, version, reserved)
    _validate(result)
    return result


class StreamDecoder:
    """Incremental parser; feed returns all complete messages in arrival order."""

    def __init__(self):
        self._buffer = bytearray()

    def feed(self, fragment):
        if not isinstance(fragment, (bytes, bytearray, memoryview)):
            raise TypeError('fragment must be bytes-like')
        self._buffer.extend(fragment)
        messages = []
        try:
            while len(self._buffer) >= HEADER.size:
                fields = HEADER.unpack(self._buffer[:HEADER.size])
                magic, version, opcode, reserved, length, generation, frame_id, reference_id, argument = fields
                probe = Message(magic, opcode, generation, frame_id, reference_id,
                                argument, b'', version, reserved)
                _validate(probe, check_payload=False)
                if length > MAX_PAYLOAD:
                    raise ProtocolError('payload exceeds 49152-byte limit')
                total = HEADER.size + length + CRC.size
                if len(self._buffer) < total:
                    break
                messages.append(decode(self._buffer[:total]))
                del self._buffer[:total]
        except ProtocolError:
            self._buffer.clear()
            raise
        return messages

    def finish(self):
        """Signal EOF; reject any partial frame rather than silently dropping it."""
        if self._buffer:
            self._buffer.clear()
            raise ProtocolError('truncated stream at EOF')

    @property
    def buffered_bytes(self):
        return len(self._buffer)
