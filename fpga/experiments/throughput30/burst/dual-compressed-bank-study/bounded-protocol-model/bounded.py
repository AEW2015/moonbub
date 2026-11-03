"""Stop-and-wait replay wrapper for the experimental tagged bank model.

This executable specification is single-threaded; it is not production code.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tagged-protocol-model'))
from model import Ack, Model, Token  # noqa: E402


MAX_DATA_PAYLOAD = 1024
MAX_WIRE_UINT = (1 << 64) - 1
MAX_OPCODE_BYTES = 16
_ALLOWED_FIELDS = {'token', 'frame_id', 'length', 'crc', 'offset', 'payload'}
_INTEGER_FIELDS = {'frame_id', 'length', 'crc', 'offset'}


class BoundedProtocol:
    """One-entry idempotency cache with a bounded DATA payload.

    Invalid envelope/field values and oversized payloads return an error ACK
    without executing the core, changing the replay cache, or consuming seq.
    """

    def __init__(self, epoch, capacity=49152):
        if type(epoch) is not int or not 0 <= epoch <= MAX_WIRE_UINT:
            raise ValueError('epoch must fit an unsigned 64-bit wire field')
        self.core = Model(epoch, capacity)
        self.next_seq = 0
        self.last = None

    def reset(self, epoch):
        if type(epoch) is not int or not 0 <= epoch <= MAX_WIRE_UINT:
            raise ValueError('epoch must fit an unsigned 64-bit wire field')
        self.core.reset(epoch)
        self.next_seq = 0
        self.last = None

    @staticmethod
    def _valid_token(token):
        return (token is None or
                (type(token) is Token and
                 type(token.epoch) is int and 0 <= token.epoch <= MAX_WIRE_UINT and
                 type(token.bank) is int and token.bank in (0, 1) and
                 type(token.generation) is int and 0 <= token.generation <= MAX_WIRE_UINT))

    @classmethod
    def _validate(cls, epoch, op, kwargs):
        if (type(epoch) is not int or not 0 <= epoch <= MAX_WIRE_UINT or
                type(op) is not str or not op.isascii() or
                len(op.encode('ascii')) > MAX_OPCODE_BYTES):
            return 'INVALID_REQUEST'
        if any(type(key) is not str or key not in _ALLOWED_FIELDS for key in kwargs):
            return 'INVALID_REQUEST'
        for key, value in kwargs.items():
            if key == 'token':
                if not cls._valid_token(value):
                    return 'INVALID_REQUEST'
            elif key == 'payload':
                if type(value) is not bytes:
                    return 'INVALID_REQUEST'
                if len(value) > MAX_DATA_PAYLOAD:
                    return 'REQUEST_TOO_LARGE'
            elif key in _INTEGER_FIELDS:
                field_max = 0xffffffff if key == 'crc' else MAX_WIRE_UINT
                if (value is not None and
                        (type(value) is not int or value < 0 or value > field_max)):
                    return 'INVALID_REQUEST'
            else:
                return 'INVALID_REQUEST'
        return None

    def request(self, epoch, seq, op, **kwargs):
        if type(seq) is not int or not 0 <= seq <= MAX_WIRE_UINT:
            raise ValueError('sequence must fit an unsigned 64-bit wire field')
        invalid = self._validate(epoch, op, kwargs)
        if invalid is not None:
            return Ack(seq, invalid)
        if epoch != self.core.epoch:
            return Ack(seq, 'STALE_EPOCH')

        body = (op, tuple(sorted(kwargs.items())))
        if self.last is not None and seq == self.next_seq - 1:
            prior_body, prior_ack = self.last
            return prior_ack if body == prior_body else Ack(seq, 'REQUEST_ID_CONFLICT')
        if seq != self.next_seq:
            return Ack(seq, 'OUT_OF_ORDER')
        ack = self.core.request(epoch, seq, op, **kwargs)
        self.last = (body, ack)
        self.next_seq += 1
        # Only the most recent operation is eligible for replay. The wrapper
        # rejects older IDs before consulting the underlying model.
        self.core.history.clear()
        return ack
