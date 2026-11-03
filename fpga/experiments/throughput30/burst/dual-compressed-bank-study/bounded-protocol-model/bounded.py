"""Stop-and-wait replay wrapper for the experimental tagged bank model.

This executable specification is single-threaded; it is not production code.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tagged-protocol-model'))
from model import Ack, Model  # noqa: E402


class BoundedProtocol:
    def __init__(self, epoch, capacity=49152):
        self.core = Model(epoch, capacity)
        self.next_seq = 0
        self.last = None

    def reset(self, epoch):
        self.core.reset(epoch)
        self.next_seq = 0
        self.last = None

    def request(self, epoch, seq, op, **kwargs):
        if epoch != self.core.epoch:
            return Ack(seq, 'STALE_EPOCH')
        if type(seq) is not int or seq < 0:
            raise ValueError('sequence must be a nonnegative integer')
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
