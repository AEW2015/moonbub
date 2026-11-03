#!/usr/bin/env python3
"""Synchronous tagged bank ownership specification prototype, not RTL."""
from dataclasses import dataclass, field
import zlib

@dataclass(frozen=True)
class Token:
    epoch: int
    bank: int
    generation: int

@dataclass(frozen=True)
class Ack:
    request_id: int
    outcome: str
    token: Token | None = None
    count: int = 0

@dataclass
class Bank:
    generation: int = 0
    state: str = 'FREE'
    frame_id: int | None = None
    expected_length: int = 0
    expected_crc: int = 0
    data: bytearray = field(default_factory=bytearray)

class Model:
    def __init__(self, epoch: int, capacity: int = 49152):
        if epoch < 0 or capacity < 1:
            raise ValueError('invalid epoch or capacity')
        self.epoch, self.capacity = epoch, capacity
        self.banks = [Bank(), Bank()]
        self.history = {}

    def reset(self, new_epoch: int):
        # External authority must ensure epoch non-reuse across power loss.
        if new_epoch <= self.epoch:
            raise ValueError('epoch must increase')
        self.epoch = new_epoch
        self.banks = [Bank(), Bank()]
        self.history.clear()

    def request(self, epoch: int, request_id: int, op: str, *, token=None,
                frame_id=None, length=None, crc=None, offset=None, payload=b''):
        if epoch != self.epoch:
            return Ack(request_id, 'STALE_EPOCH', token)
        if not isinstance(request_id, int) or request_id < 0:
            raise ValueError('request ID must be a nonnegative integer')
        if not isinstance(payload, bytes):
            raise TypeError('payload must be bytes')
        body = (op, token, frame_id, length, crc, offset, payload)
        if request_id in self.history:
            prior_body, prior_ack = self.history[request_id]
            if body != prior_body:
                return Ack(request_id, 'REQUEST_ID_CONFLICT', token)
            return prior_ack
        ack = self._apply(request_id, op, token, frame_id, length, crc, offset, payload)
        self.history[request_id] = (body, ack)
        return ack

    def _apply(self, rid, op, token, frame_id, length, crc, offset, payload):
        if op == 'BEGIN':
            if token is not None or not isinstance(frame_id, int) or frame_id < 0 or not isinstance(length, int) or not 0 < length <= self.capacity or not isinstance(crc, int) or not 0 <= crc <= 0xffffffff:
                return Ack(rid, 'INVALID_BEGIN')
            for i, bank in enumerate(self.banks):
                if bank.state == 'FREE':
                    bank.generation += 1
                    bank.state, bank.frame_id = 'RECEIVING', frame_id
                    bank.expected_length, bank.expected_crc = length, crc
                    bank.data.clear()
                    return Ack(rid, 'BEGIN_OK', Token(self.epoch, i, bank.generation))
            return Ack(rid, 'BUSY')
        if not isinstance(token, Token) or token.epoch != self.epoch or token.bank not in (0, 1):
            return Ack(rid, 'STALE_TOKEN', token)
        bank = self.banks[token.bank]
        if token.generation != bank.generation or bank.state == 'FREE':
            return Ack(rid, 'STALE_TOKEN', token)
        if op == 'RELEASE':
            if bank.state != 'READY':
                return Ack(rid, 'WRONG_STATE', token, len(bank.data))
            bank.state = 'FREE'
            return Ack(rid, 'RELEASE_OK', token, len(bank.data))
        if bank.state != 'RECEIVING':
            return Ack(rid, 'WRONG_STATE', token, len(bank.data))
        if op == 'DATA':
            if not isinstance(offset, int) or offset != len(bank.data) or not payload or len(bank.data)+len(payload) > bank.expected_length:
                return Ack(rid, 'BAD_DATA', token, len(bank.data))
            bank.data.extend(payload)
            return Ack(rid, 'DATA_OK', token, len(bank.data))
        if op == 'ABORT':
            count = len(bank.data)
            bank.state = 'FREE'
            return Ack(rid, 'ABORT_OK', token, count)
        if op == 'COMMIT':
            if len(bank.data) != bank.expected_length or zlib.crc32(bank.data) != bank.expected_crc:
                bank.state = 'FREE'
                return Ack(rid, 'COMMIT_REJECTED', token, len(bank.data))
            bank.state = 'READY'
            return Ack(rid, 'COMMIT_OK', token, len(bank.data))
        return Ack(rid, 'UNKNOWN_OP', token, len(bank.data))
