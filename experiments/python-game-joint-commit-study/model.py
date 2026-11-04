"""V22 synchronous whole-pair admission and atomic logical publication.

This is a laboratory Python transaction model, not native protocol support,
memory-order/CDC evidence, a physical DMA fence, or a presentation-rate proof.
Arrays in retained banks are shared read-only; only bookkeeping is forked.
"""
from dataclasses import dataclass
from pathlib import Path
import copy
import hashlib
import importlib.util
import math
import struct
import sys
import time
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


compose = load('joint22_compose', HERE.parent / 'python-game-display-compose-study/model.py')
hc = compose.cache
C = compose.codec
PROFILES = hc.legacy.PROFILES
RECTANGLES = hc.RECTANGLES
BASE_REGIONS = hc.legacy.BASE_REGIONS
FRAME_CAP = 49152
ACK_HEADER = struct.Struct('<4sBII16sHH')
ACK_BYTES = ACK_HEADER.size + C.FEEDBACK.size + 4 + hc.ACK.size + 4 + 4
MAX_LEASES = 8


def pair_digest(packet):
    return hashlib.sha256(packet).digest()[:16]


def pack_ack(packet, base_ack, hud_ack):
    base, hud = compose.unbind(packet)
    bm, hm = C.identity(base), hc.parse(hud)
    ba, ha = C.parse_feedback(base_ack), hc.parse_ack(hud_ack)
    if (ba['epoch'], ba['frame_id'], ha['epoch'], ha['frame']) != (bm['epoch'], bm['frame_id'], hm['epoch'], hm['frame']):
        raise ValueError('JA22 component identity')
    header = ACK_HEADER.pack(b'JA22', 1, bm['epoch'], bm['frame_id'], pair_digest(packet), len(base_ack), len(hud_ack))
    return hc.seal(header + base_ack + hud_ack)


def parse_ack(data):
    if type(data) is not bytes or len(data) != ACK_BYTES:
        raise ValueError('JA22 fixed length')
    if zlib.crc32(data[:-4]) != struct.unpack('<I', data[-4:])[0]:
        raise ValueError('JA22 CRC')
    magic, version, epoch, frame, digest, nb, nh = ACK_HEADER.unpack_from(data)
    if (magic, version, nb, nh) != (b'JA22', 1, C.FEEDBACK.size + 4, hc.ACK.size + 4):
        raise ValueError('JA22 profile')
    hc.check_id(epoch, epoch=True)
    hc.check_id(frame)
    ba = data[ACK_HEADER.size:ACK_HEADER.size + nb]
    ha = data[ACK_HEADER.size + nb:-4]
    b, h = C.parse_feedback(ba), hc.parse_ack(ha)
    if (b['epoch'], b['frame_id'], h['epoch'], h['frame']) != (epoch, frame, epoch, frame):
        raise ValueError('JA22 component identities')
    return dict(epoch=epoch, frame=frame, pair_digest=digest, base_ack=ba, hud_ack=ha)


def _time(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('finite nonnegative ' + name)
    return float(value)


def _profiles(value):
    if not isinstance(value, tuple) or not 1 <= len(value) <= 4 or any(
            not isinstance(p, tuple) or len(p) != 2 or any(type(x) is not int or x not in C.gm.roi.SCALES for x in p) for p in value):
        raise ValueError('one to four bounded legal profiles')
    return value


def _clone_base(base):
    out = copy.copy(base)
    out.banks = base.banks.copy()
    out._leases = set(base._leases)
    if hasattr(base, 'pending'):
        out.pending = base.pending.copy()
    return out


def _clone_hud(hud):
    out = copy.copy(hud)
    if isinstance(hud, hc.Receiver):
        out.banks = hud.banks.copy()
        out.readers = hud.readers.copy()
        out._leases = hud._leases.copy()
    return out


def _bank_identity(bank):
    return None if bank is None else [bank.frame_id, bank.tag.hex()]


def _hud_identity(bank):
    return None if bank is None else [bank['frame'], bank['generation'], bank['newtag'].hex()]


def _freeze_planes(planes):
    if planes is not None:
        for plane in planes:
            plane.setflags(write=False)


@dataclass(frozen=True, eq=False)
class Candidate:
    owner: object
    frame_id: int
    packet: bytes | None
    info: dict

    @property
    def accepted(self):
        return self.packet is not None


@dataclass(frozen=True, eq=False)
class ReceiveCandidate:
    owner: object
    frame_id: int
    packet: bytes
    display: np.ndarray
    planes: tuple
    info: dict


class JointSender:
    def __init__(self, epoch=1, frame_cap=FRAME_CAP, profiles=PROFILES):
        hc.check_id(epoch, epoch=True)
        if type(frame_cap) is not int or not 256 <= frame_cap <= FRAME_CAP:
            raise ValueError('joint complete cap')
        self.epoch, self.frame_cap, self.profiles = epoch, frame_cap, _profiles(profiles)
        self._state = (C.Encoder(epoch=epoch, window=1, frame_cap=FRAME_CAP, mode='gm'), hc.Sender(epoch))
        self.base.max_readers = 8
        self._owner = object()
        self._active = None
        self._record = None
        self._pending = None
        self._version = 0

    @property
    def base(self): return self._state[0]

    @property
    def hud(self): return self._state[1]

    @property
    def active_candidate(self): return self._active

    def snapshot(self):
        return dict(epoch=self.epoch, base_epoch=self.base.epoch, hud_epoch=self.hud.epoch,
                    version=self._version, last_issued=self.base.last_issued,
                    base_generation=self.base._generation, base_banks={str(k): _bank_identity(b) for k, b in self.base.banks.items()},
                    base_pending=sorted(self.base.pending), base_readers=self.base.readers,
                    hud_frame=self.hud.last_frame, hud_generation=self.hud.generation,
                    hud_confirmed=_hud_identity(self.hud.confirmed), hud_pending=self.hud.pending is not None,
                    pair_pending=None if self._pending is None else self._pending['frame'])

    def build(self, rgb, frame_id, *, force_key=False, promote=False, profiles=None, now_ms=0, deadline_ms=None):
        started = time.perf_counter_ns()
        now_ms = _time(now_ms, 'build time')
        deadline = None if deadline_ms is None else _time(deadline_ms, 'deadline')
        declared = _profiles(self.profiles if profiles is None else profiles)
        if self._active is not None or self._pending is not None or self.base.active_candidate is not None:
            raise ValueError('joint unresolved transaction')
        a = C.gm.ft._check_rgb(rgb)
        if a.shape != (480, 720, 3):
            raise ValueError('joint fixed canvas')
        hc.check_id(frame_id)
        if frame_id <= self.base.last_issued:
            raise ValueError('joint monotonic frame')
        before = self.snapshot()
        info = dict(frame_id=frame_id, attempts=[], selected_profile=None, hud_prepare_ms=0.,
                    binding_bytes=compose.OVERHEAD, complete_bytes=None, reason='deadline_before_build',
                    state_before=before, paid_service_ms=0.)
        hud_private = _clone_hud(self.hud)
        chosen = None
        pair = None
        try:
            if deadline is None or now_ms < deadline:
                t = time.perf_counter_ns()
                hud_packet, hud_info = hud_private.prepare(a, frame_id)
                info['hud_prepare_ms'] = (time.perf_counter_ns() - t) / 1e6
                info['hud'] = hud_info
                info['hud_bytes'] = len(hud_packet)
                info['reason'] = 'all_declared_maps_exceed_complete_cap'
                for index, (roi, bg) in enumerate(declared):
                    if deadline is not None and now_ms + (time.perf_counter_ns() - started) / 1e6 >= deadline:
                        info['reason'] = 'deadline_after_paid_work'
                        break
                    t = time.perf_counter_ns()
                    mapped = C.gm.roi.declared_map(720, 480, BASE_REGIONS, roi, bg)
                    map_ms = (time.perf_counter_ns() - t) / 1e6
                    t = time.perf_counter_ns()
                    candidate = self.base.build(a, frame_id, scale_map=mapped, force_key=force_key, promote=promote)
                    build_ms = (time.perf_counter_ns() - t) / 1e6
                    ci = C.plain_info(candidate)
                    complete = ci['bytes'] + len(hud_packet) + compose.OVERHEAD
                    fit = candidate.accepted and complete <= self.frame_cap
                    expired = deadline is not None and now_ms + (time.perf_counter_ns() - started) / 1e6 >= deadline
                    row = dict(index=index, roi_scale=roi, background_scale=bg, map_ms=map_ms, build_ms=build_ms,
                               base_bytes=ci['bytes'], complete_bytes=complete, base_accepted=candidate.accepted,
                               accepted=bool(fit and not expired), analyze_calls=ci['analyze_calls'],
                               forward_calls=ci['forward_calls'], discard_ms=0., deadline_expired=expired)
                    info['attempts'].append(row)
                    if fit and not expired:
                        chosen = candidate
                        pair = compose.bind(candidate.packet, hud_packet)
                        if len(pair) != complete:
                            raise AssertionError('complete pair budget')
                        info.update(selected_profile=[roi, bg], complete_bytes=len(pair), reason='whole_pair_admitted')
                        break
                    t = time.perf_counter_ns()
                    self.base.discard(candidate)
                    row['discard_ms'] = (time.perf_counter_ns() - t) / 1e6
                    if expired:
                        info['reason'] = 'deadline_after_paid_work'
                        break
            info['paid_service_ms'] = (time.perf_counter_ns() - started) / 1e6
            info['state_after_build'] = self.snapshot()
            result = Candidate(self._owner, frame_id, pair, info)
            if chosen is not None:
                _freeze_planes(self.base._candidate_record['row']['planes'])
                self._active = result
                self._record = dict(candidate=result, packet=pair, frame=frame_id, base_candidate=chosen,
                                    hud_private=hud_private, state=self._state, version=self._version,
                                    config=(self.epoch, self.frame_cap), deadline=deadline,
                                    semantics={k: v for k, v in before.items() if k != 'base_readers'})
            elif self.snapshot() != before:
                raise AssertionError('rejected pair changed semantic state/readers')
            return result
        except BaseException:
            if self.base.active_candidate is not None:
                self.base.discard(self.base.active_candidate)
            raise

    def _owned(self, candidate):
        r = self._record
        if (r is None or candidate is not self._active or candidate.owner is not self._owner
                or candidate.packet != r['packet'] or candidate.frame_id != r['frame']):
            raise ValueError('foreign/stale/mutated joint candidate')
        if self._state is not r['state'] or self._version != r['version'] or (self.epoch, self.frame_cap) != r['config']:
            raise ValueError('changed joint candidate state')
        if {k: v for k, v in self.snapshot().items() if k != 'base_readers'} != r['semantics']:
            raise ValueError('changed joint component semantics')
        return r

    def discard(self, candidate):
        if candidate is not self._active or self._record is None:
            raise ValueError('foreign/stale joint discard')
        self.base.discard(self._record['base_candidate'])
        self._active = self._record = None
        return True

    def commit(self, candidate, *, now_ms=0):
        r = self._owned(candidate)
        now_ms = _time(now_ms, 'commit time')
        if r['deadline'] is not None and now_ms >= r['deadline']:
            raise ValueError('joint candidate deadline')
        if len(r['packet']) > self.frame_cap or self._pending is not None:
            raise ValueError('joint complete cap/pending')
        # Every potentially failing action happens on a metadata fork. The live
        # base candidate/source lease stays owned until a single tuple swap.
        private_base = _clone_base(self.base)
        private_base.commit(r['base_candidate'])
        private_hud = r['hud_private']
        base_packet, hud_packet = compose.unbind(r['packet'])
        expected = pack_ack(r['packet'], C.feedback(C.identity(base_packet)), hc.ack_for(hc.parse(hud_packet)))
        pending = dict(frame=r['frame'], packet=r['packet'], expected_ack=expected)
        self._state = (private_base, private_hud)
        self._pending = pending
        self._version += 1
        self._active = self._record = None
        return pending['packet']

    def retry(self):
        if self._pending is None:
            raise ValueError('no unresolved pair')
        return self._pending['packet']

    def ack(self, data):
        parsed = parse_ack(data)
        if self._pending is None or data != self._pending['expected_ack']:
            raise ValueError('JA22 exact outstanding whole-pair ACK')
        private_base, private_hud = _clone_base(self.base), _clone_hud(self.hud)
        if not private_base.ack(parsed['base_ack']):
            raise ValueError('JA22 base no longer outstanding')
        private_hud.accept_ack(parsed['hud_ack'])
        self._state = (private_base, private_hud)
        self._pending = None
        self._version += 1
        return True

    def reset(self, epoch):
        hc.check_id(epoch, epoch=True)
        if epoch <= self.epoch or self._active is not None or self._pending is not None or self.base.readers:
            raise ValueError('joint reset requires later epoch and drained owners')
        self.__init__(epoch, self.frame_cap, self.profiles)


class JointReceiver:
    def __init__(self, epoch=1, frame_cap=FRAME_CAP):
        hc.check_id(epoch, epoch=True)
        if type(frame_cap) is not int or not 256 <= frame_cap <= FRAME_CAP:
            raise ValueError('joint receive complete cap')
        self.epoch, self.frame_cap = epoch, frame_cap
        self._state = (C.Receiver(epoch=epoch, max_readers=8), hc.Receiver(epoch), None)
        self._owner = object()
        self._active = self._record = None
        self._version = 0
        self._leases = {}
        self._next_lease = 0
        self.last_ack = self.last_pair = None

    @property
    def base(self): return self._state[0]

    @property
    def hud(self): return self._state[1]

    @property
    def display(self): return self._state[2]

    @property
    def last_frame(self): return self.base.last_frame_id

    @property
    def active_candidate(self): return self._active

    def snapshot(self):
        return dict(epoch=self.epoch, base_epoch=self.base.epoch, hud_epoch=self.hud.epoch,
                    version=self._version, last_frame=self.last_frame,
                    base_banks={str(k): _bank_identity(b) for k, b in self.base.banks.items()},
                    base_readers=self.base.readers, hud_banks=[_hud_identity(b) for b in self.hud.banks],
                    hud_frame=self.hud.last_frame, hud_generation=self.hud.last_generation,
                    hud_readers=list(self.hud.readers), reader_tokens=[list(x) for x in self._leases],
                    display_sha256=None if self.display is None else hashlib.sha256(self.display.tobytes()).hexdigest(),
                    last_ack_sha256=None if self.last_ack is None else hashlib.sha256(self.last_ack).hexdigest())

    def published_snapshot(self):
        return {k: v for k, v in self.snapshot().items()
                if k not in ('base_readers', 'hud_readers', 'reader_tokens')}

    def _acquire(self, kind, slot):
        if type(slot) is not int or slot not in (0, 1) or len(self._leases) >= MAX_LEASES or self._next_lease >= hc.INVALID:
            raise ValueError('bounded joint reader descriptor')
        component = self.base if kind == 'base' else self.hud
        lease = component.acquire(slot)
        self._next_lease += 1
        token = (self.epoch, kind, slot, self._next_lease)
        self._leases[token] = lease
        return token

    def acquire_base(self, slot): return self._acquire('base', slot)

    def acquire_hud(self, slot): return self._acquire('hud', slot)

    def release(self, token):
        if type(token) is not tuple or token not in self._leases:
            raise ValueError('foreign/released joint lease')
        component = self.base if token[1] == 'base' else self.hud
        component.release(self._leases[token])
        del self._leases[token]

    def prepare(self, packet, *, now_ms=0, deadline_ms=None):
        _time(now_ms, 'receive time')
        deadline = None if deadline_ms is None else _time(deadline_ms, 'deadline')
        if self._active is not None:
            raise ValueError('joint receive already active')
        if type(packet) is not bytes or len(packet) > self.frame_cap:
            raise ValueError('joint complete receive cap')
        base_packet, hud_packet = compose.unbind(packet)
        bm, hm = C.identity(base_packet), hc.parse(hud_packet)
        if bm['epoch'] != self.epoch or hm['epoch'] != self.epoch:
            raise ValueError('joint receive epoch')
        if (bm['width'], bm['height']) != (720, 480):
            raise ValueError('joint receive fixed canvas')
        if deadline is not None and now_ms >= deadline:
            raise ValueError('joint receive expired')
        reference_hold = None
        try:
            if not bm['key']:
                reference_hold = self.base.acquire(bm['reference_bank'])
            private_base, private_hud = _clone_base(self.base), _clone_hud(self.hud)
            if reference_hold is not None:
                private_base._leases.remove(reference_hold)
            began = time.perf_counter_ns()
            task = private_base.begin(base_packet)
            planes = task.planes
            rgb, base_info, base_ack = private_base.complete(task)
            base_ms = (time.perf_counter_ns() - began) / 1e6
            began = time.perf_counter_ns()
            hud_ack = private_hud.receive(hud_packet)
            hud_ms = (time.perf_counter_ns() - began) / 1e6
            display = C.corpus.rgb565(rgb)
            for (x, y, w, h), patch in zip(RECTANGLES, private_hud.display['patches']):
                display[y:y + h, x:x + w] = patch
            display.setflags(write=False)
            _freeze_planes(planes)
            result = ReceiveCandidate(self._owner, bm['frame_id'], packet, display, planes,
                                      dict(base_decode_ms=base_ms, hud_decode_ms=hud_ms,
                                           base_info=base_info, complete_bytes=len(packet),
                                           hud_words=hc.WORDS, destination_base=bm['destination_bank'],
                                           destination_hud=hm['dest']))
            self._active = result
            self._record = dict(candidate=result, state=self._state, version=self._version,
                                packet=packet, frame=bm['frame_id'], display=display, planes=planes,
                                private_base=private_base, private_hud=private_hud,
                                destination_base=bm['destination_bank'], destination_hud=hm['dest'],
                                reference_hold=reference_hold, writes_drained=False, deadline=deadline,
                                ack=pack_ack(packet, base_ack, hud_ack),
                                publication=self.published_snapshot())
            return result
        except BaseException:
            if reference_hold is not None:
                self.base.release(reference_hold)
            raise

    def _owned(self, candidate):
        r = self._record
        if (r is None or candidate is not self._active or candidate.owner is not self._owner
                or candidate.packet != r['packet'] or candidate.frame_id != r['frame']
                or candidate.display is not r['display'] or candidate.planes is not r['planes']
                or self._state is not r['state'] or self._version != r['version']):
            raise ValueError('foreign/stale/mutated joint receive candidate')
        if self.published_snapshot() != r['publication']:
            raise ValueError('changed joint published component semantics')
        return r

    def abort(self, candidate):
        if candidate is not self._active or self._record is None:
            raise ValueError('foreign/stale joint abort')
        hold = self._record['reference_hold']
        if hold is not None:
            self.base.release(hold)
        self._active = self._record = None
        return True

    def mark_writes_drained(self, candidate):
        r = self._owned(candidate)
        # An explicit injected model event; not inferred from decoder completion.
        r['writes_drained'] = True

    def present(self, candidate, *, vblank=True, now_ms=0):
        r = self._owned(candidate)
        now_ms = _time(now_ms, 'presentation time')
        if type(vblank) is not bool or not vblank or not r['writes_drained']:
            raise ValueError('joint publication requires write-drain event and vblank event')
        if r['deadline'] is not None and now_ms >= r['deadline']:
            raise ValueError('joint presentation deadline')
        dest = r['destination_base']
        hold = r['reference_hold']
        if dest != C.NO_BANK and any(l.slot == dest and l is not hold for l in self.base._leases):
            raise ValueError('joint base destination gained a reader')
        if self.hud.readers[r['destination_hud']]:
            raise ValueError('joint HUD destination gained a reader')
        private_base, private_hud = r['private_base'], r['private_hud']
        # Preserve late independent readers, and remove only this candidate's
        # private reference hold. Published arrays remain shared and immutable.
        private_base._leases = self.base._leases - ({hold} if hold is not None else set())
        private_hud._leases = self.hud._leases.copy()
        private_hud.readers = self.hud.readers.copy()
        private_hud._next_lease = self.hud._next_lease
        self._state = (private_base, private_hud, r['display'])
        self.last_pair, self.last_ack = r['packet'], r['ack']
        self._version += 1
        self._active = self._record = None
        return self.last_ack

    def retry_ack(self, packet):
        if type(packet) is not bytes or self.last_pair is None or packet != self.last_pair:
            raise ValueError('only exact last published pair may repeat its ACK')
        return self.last_ack

    def reset(self, epoch):
        hc.check_id(epoch, epoch=True)
        if (epoch <= self.epoch or self._active is not None or self._leases
                or self.base.readers or any(self.hud.readers)):
            raise ValueError('joint reset requires later epoch and drained readers')
        self.__init__(epoch, self.frame_cap)
