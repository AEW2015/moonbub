"""Bounded capability/reset agreement for the experimental CP23 profile.

Synchronous Python state machine. Persistent epoch storage and transport-drain
signals are model inputs, not durable storage, cryptographic rekey or DMA proof.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib.util
import json
import struct
import sys
import zlib

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('recovery24_joint', HERE.parent / 'python-game-hd22-joint-study/model.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

HELLO, HELLO_REPLY, OFFER, READY, COMMIT, COMMITTED, GO, GO_ACK, BUSY = range(1, 10)
HEADER = struct.Struct('<4sBBIQQ16s')
CONTROL_BYTES = HEADER.size + 4
MAX_EPOCH = 0xfffffffe
MAX_NONCE = 0xffffffffffffffff
PROFILE = dict(pair='CP23', ack='JA23', hud='HC22/HA22/HD22', version=1,
               coded=[720, 480], active=[720, 405], complete_cap=49152,
               refresh='independent AR03 key and nonreferenced full HUD')
PROFILE_TAG = hashlib.sha256(json.dumps(PROFILE, sort_keys=True, separators=(',', ':')).encode()).digest()[:16]


def positive_nonce(value):
    if type(value) is not int or not 0 < value <= MAX_NONCE:
        raise ValueError('bounded boot nonce')


def encode(kind, epoch, host_nonce, target_nonce, profile=PROFILE_TAG):
    if type(kind) is not int or kind not in range(HELLO, BUSY + 1):
        raise ValueError('RS24 message kind')
    if type(epoch) is not int or not 0 <= epoch <= MAX_EPOCH:
        raise ValueError('RS24 epoch')
    positive_nonce(host_nonce)
    if type(target_nonce) is not int or not 0 <= target_nonce <= MAX_NONCE:
        raise ValueError('bounded target boot nonce')
    if target_nonce != 0:
        positive_nonce(target_nonce)
    if type(profile) is not bytes or len(profile) != 16:
        raise ValueError('RS24 profile tag')
    if kind == HELLO:
        if epoch or target_nonce:
            raise ValueError('RS24 HELLO fields')
    elif not target_nonce or (kind != HELLO_REPLY and not epoch):
        raise ValueError('RS24 bound message fields')
    body = HEADER.pack(b'RS24', 1, kind, epoch, host_nonce, target_nonce, profile)
    return body + struct.pack('<I', zlib.crc32(body))


def parse(data):
    if type(data) is not bytes or len(data) != CONTROL_BYTES:
        raise ValueError('RS24 exact bounded length')
    if zlib.crc32(data[:-4]) != struct.unpack('<I', data[-4:])[0]:
        raise ValueError('RS24 CRC')
    magic, version, kind, epoch, host, target, profile = HEADER.unpack_from(data)
    if (magic, version) != (b'RS24', 1) or encode(kind, epoch, host, target, profile) != data:
        raise ValueError('RS24 grammar')
    return dict(kind=kind, epoch=epoch, host=host, target=target, profile=profile)


def identity(message):
    return tuple(message[k] for k in ('epoch', 'host', 'target', 'profile'))


@dataclass
class EpochLedger:
    last: int = 0

    def __post_init__(self):
        if type(self.last) is not int or not 0 <= self.last <= MAX_EPOCH:
            raise ValueError('epoch ledger')

    def reserve(self, peer_epoch):
        if type(peer_epoch) is not int or not 0 <= peer_epoch <= MAX_EPOCH:
            raise ValueError('peer epoch ledger')
        value = max(self.last, peer_epoch) + 1
        if value > MAX_EPOCH:
            raise ValueError('epoch exhausted; no wrap')
        self.last = value
        return value


class Host:
    def __init__(self, boot_nonce, ledger=None, max_retries=4):
        positive_nonce(boot_nonce)
        if type(max_retries) is not int or not 0 <= max_retries <= 8:
            raise ValueError('bounded retry count')
        self.nonce = boot_nonce
        self.ledger = EpochLedger() if ledger is None else ledger
        self.max_retries = max_retries
        self.phase = 'STOPPED'
        self.outstanding = self.proposal = self.sender = None
        self.retries = 0
        self.transport_drained = False

    def start(self):
        if not self.drained():
            raise ValueError('host transport/private/source owners must explicitly drain')
        self.phase, self.proposal = 'HELLO', None
        self.outstanding = encode(HELLO, 0, self.nonce, 0)
        self.retries = 0
        return self.outstanding

    def drained(self):
        return self.transport_drained and (self.sender is None or (
            self.sender.active_candidate is None and self.sender.base.readers == 0))

    def retry(self):
        if self.outstanding is None or self.phase in ('RUNNING', 'STOPPED', 'SAFE_STOP'):
            raise ValueError('no outstanding control')
        if self.retries >= self.max_retries:
            self.phase = 'SAFE_STOP'
            raise ValueError('bounded retry exhausted; remain data-blocked')
        self.retries += 1
        return self.outstanding

    def accept(self, data):
        x = parse(data)
        if x['host'] != self.nonce or x['profile'] != PROFILE_TAG:
            raise ValueError('host boot/profile binding')
        if self.phase == 'HELLO' and x['kind'] == HELLO_REPLY:
            epoch = self.ledger.reserve(x['epoch'])
            self.proposal = (epoch, self.nonce, x['target'], PROFILE_TAG)
            self.outstanding = encode(OFFER, *self.proposal)
            self.phase, self.retries = 'OFFER', 0
        else:
            if self.proposal is None or identity(x) != self.proposal:
                raise ValueError('host outstanding identity')
            if x['kind'] == BUSY and self.phase == 'OFFER':
                return self.retry()
            if self.phase == 'OFFER' and x['kind'] == READY:
                if not self.drained():
                    raise ValueError('host late owner before COMMIT')
                self.outstanding = encode(COMMIT, *self.proposal)
                self.phase, self.retries = 'COMMIT', 0
            elif self.phase == 'COMMIT' and x['kind'] == COMMITTED:
                if not self.drained():
                    raise ValueError('host late owner before reset')
                self.sender = m.JointSender(epoch=x['epoch'])
                self.outstanding = encode(GO, *self.proposal)
                self.phase, self.retries = 'GO', 0
            elif self.phase == 'GO' and x['kind'] == GO_ACK:
                self.phase, self.outstanding = 'RUNNING', None
            else:
                raise ValueError('host unexpected control phase/kind')
        return self.outstanding

    def build(self, rgb, frame_id, **kwargs):
        if self.phase != 'RUNNING' or self.sender is None:
            raise ValueError('host data blocked pending reset agreement')
        if self.sender.base.last_issued == -1:
            kwargs['force_key'] = True
        return self.sender.build(rgb, frame_id, **kwargs)

    def commit(self, candidate):
        if self.phase != 'RUNNING':
            raise ValueError('host data blocked')
        return self.sender.commit(candidate)

    def acknowledge_data(self, ack):
        if self.phase != 'RUNNING':
            raise ValueError('host data ACK blocked')
        return self.sender.ack(ack)


class Target:
    def __init__(self, boot_nonce, ledger=None):
        positive_nonce(boot_nonce)
        self.nonce = boot_nonce
        self.ledger = EpochLedger() if ledger is None else ledger
        self.phase = 'STOPPED'
        self.proposal = self.receiver = None
        self.transport_drained = False

    def drained(self):
        return self.transport_drained and (self.receiver is None or (
            self.receiver.active_candidate is None and self.receiver.base.readers == 0
            and not any(self.receiver.hud.readers)))

    def accept(self, data):
        x = parse(data)
        if x['profile'] != PROFILE_TAG:
            raise ValueError('target capability/profile mismatch')
        if x['kind'] == HELLO:
            return encode(HELLO_REPLY, self.ledger.last, x['host'], self.nonce)
        if x['target'] != self.nonce:
            raise ValueError('target boot nonce mismatch')
        request = identity(x)
        if x['kind'] == OFFER:
            if request == self.proposal:
                return encode(READY, *request)
            if x['epoch'] <= self.ledger.last or (self.proposal is not None and x['epoch'] <= self.proposal[0]):
                raise ValueError('target stale proposal')
            if not self.drained():
                # Block further data until explicitly retried with drained owners.
                self.phase = 'QUIESCING'
                return encode(BUSY, *request)
            self.proposal, self.phase = request, 'READY'
            return encode(READY, *request)
        if request != self.proposal:
            raise ValueError('target proposal identity')
        if x['kind'] == COMMIT:
            if self.phase in ('COMMITTED', 'RUNNING'):
                return encode(COMMITTED, *request)
            if self.phase != 'READY' or not self.drained():
                raise ValueError('target commit requires reserved drained state')
            self.receiver = m.JointReceiver(epoch=x['epoch'])
            self.ledger.last = x['epoch']
            self.phase = 'COMMITTED'
            return encode(COMMITTED, *request)
        if x['kind'] == GO:
            if self.phase not in ('COMMITTED', 'RUNNING'):
                raise ValueError('target GO phase')
            self.phase = 'RUNNING'
            return encode(GO_ACK, *request)
        raise ValueError('target unexpected control kind')

    def prepare_data(self, packet):
        if self.phase != 'RUNNING' or self.receiver is None:
            raise ValueError('target data blocked pending reset agreement')
        base, hud = m.compose.unbind(packet)
        meta, hm = m.C.identity(base), m.hc.parse(hud)
        if self.receiver.last_frame == -1 and (not meta['key'] or hm['refslot'] != m.hc.NO_REF):
            raise ValueError('new epoch requires independent video and full HUD')
        return self.receiver.prepare(packet)


def exchange(host, target, *, drop_once=None, drop_all=None):
    """Finite in-memory delivery campaign, counting lost controls too."""
    request = host.start()
    trace = []
    dropped = False
    for _ in range(64):
        for direction, data in (('forward', request),):
            msg = parse(data)
            lose = msg['kind'] == drop_all or (not dropped and msg['kind'] == drop_once)
            trace.append(dict(direction=direction, kind=msg['kind'], bytes=data.hex(), delivered=not lose))
            if lose:
                dropped = True
                break
        if lose:
            try:
                request = host.retry()
            except ValueError:
                return trace, False
            continue
        reply = target.accept(request)
        msg = parse(reply)
        lose = msg['kind'] == drop_all or (not dropped and msg['kind'] == drop_once)
        trace.append(dict(direction='reverse', kind=msg['kind'], bytes=reply.hex(), delivered=not lose))
        if lose:
            dropped = True
            try:
                request = host.retry()
            except ValueError:
                return trace, False
            continue
        request = host.accept(reply)
        if request is None:
            return trace, True
    raise AssertionError('finite delivery campaign exceeded bound')
