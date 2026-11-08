"""AR01: bounded two-bank acknowledged reconstructed-reference experiment.

Bank0 is an immutable key. Bank1 may hold an explicitly promoted P reconstruction.
Promotions conservatively drain all sender transactions and physical read leases.
This is a new research dialect, not installed GM01 or a hardware timing claim.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import sys
import time
from types import MappingProxyType
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'python-game-codec-study'))
import game_codec as gm

NO_BANK = 255
ZERO = b'\0'*16
KEY, PROMOTE = 1, 2
ACK, NACK = 1, 2
HEADER = struct.Struct('<4sBBIIBBI16s16sI')
FEEDBACK = struct.Struct('<4sBBIIIBI16s')


def ms(start): return (time.perf_counter_ns()-start)/1e6
def body_crc(packet): return zlib.crc32(packet[:-4])
def seal(body): return body+struct.pack('<I', zlib.crc32(body))
def pixels(planes): return sum(p.size for p in planes)


def reference_tag(planes):
    h, w = planes[0].shape
    digest = hashlib.sha256(struct.pack('<HH', w, h))
    for p in planes:
        digest.update(np.asarray(p, dtype='<i2').tobytes())
    return digest.digest()[:16]


@dataclass(frozen=True, eq=False)
class Bank:
    frame_id: int
    tag: bytes
    planes: tuple


@dataclass(frozen=True, eq=False)
class Lease:
    owner: object
    slot: int
    bank: Bank


@dataclass(frozen=True)
class Decision:
    packet: bytes | None
    frame_id: int
    key: bool
    promoted: bool
    reference_bank: int
    reference_id: int | None
    reference_tag: bytes
    destination_bank: int
    service_ms: float
    info: dict

    @property
    def accepted(self): return self.packet is not None


@dataclass(frozen=True, eq=False)
class Decode:
    owner: object
    meta: dict
    planes: tuple
    rgb: np.ndarray
    lease: Lease | None
    info: dict


class Banks:
    def __init__(self, epoch=1, max_readers=3):
        if type(epoch) is not int or not 0 <= epoch < gm.NO_REF:
            raise ValueError('AR01 epoch')
        if type(max_readers) is not int or not 1 <= max_readers <= 8:
            raise ValueError('AR01 bounded readers')
        self.epoch = epoch
        self.banks = {0: None, 1: None}
        self._owner = object()
        self._leases = set()
        self.max_readers = max_readers
        self.reference_read_bytes = self.reconstruction_write_bytes = 0
        self.reference_read_array_bytes = self.reconstruction_write_array_bytes = 0
        self.tag_read_bytes = 0
        self.peak_retained_banks = self.peak_retained_array_bytes = 0

    def _writable(self, slot): return not any(l.slot == slot for l in self._leases)

    def _acquire(self, slot):
        bank = self.banks.get(slot)
        if bank is None or len(self._leases) >= self.max_readers:
            raise ValueError('AR01 missing reference or reader capacity')
        lease = Lease(self._owner, slot, bank)
        self._leases.add(lease)
        return lease

    def release(self, lease):
        if not isinstance(lease, Lease) or lease.owner is not self._owner or lease not in self._leases:
            raise ValueError('AR01 foreign/released lease')
        self._leases.remove(lease)

    def _observe(self):
        current = [b for b in self.banks.values() if b is not None]
        self.peak_retained_banks = max(self.peak_retained_banks, len(current))
        self.peak_retained_array_bytes = max(self.peak_retained_array_bytes,
                                             sum(p.nbytes for b in current for p in b.planes))

    def retained_bytes(self):
        return sum(p.nbytes for b in self.banks.values() if b is not None for p in b.planes)

    @property
    def readers(self): return len(self._leases)


def identity(packet, epoch=None, frame_cap=49152, *, decode=False):
    """Validate envelope/base preflight; coefficient entropy is optional.

    Lightweight routing is not a decode-success certificate. Receiver.begin pays
    full frozen coefficient parsing before any reference publication.
    """
    if type(packet) is not bytes or len(packet) > frame_cap or len(packet) < HEADER.size+4:
        raise ValueError('AR01 complete cap/type/length')
    magic, version, flags, session, frame, refbank, dest, refid, reftag, newtag, size = HEADER.unpack_from(packet)
    if (magic != b'AR01' or version != 1 or flags not in (0, KEY, PROMOTE)
            or session == gm.NO_REF or (epoch is not None and session != epoch)
            or frame == gm.NO_REF or size < gm.HEADER.size+4
            or len(packet) != HEADER.size+size+4 or body_crc(packet) != struct.unpack('<I', packet[-4:])[0]):
        raise ValueError('AR01 envelope identity/CRC')
    key, promoted = flags == KEY, flags == PROMOTE
    if key:
        valid = refbank == NO_BANK and refid == gm.NO_REF and reftag == ZERO and dest == 0 and newtag != ZERO
    else:
        valid = refbank in (0, 1) and refid < frame and reftag != ZERO
        valid &= (dest == 1 and newtag != ZERO) if promoted else (dest == NO_BANK and newtag == ZERO)
    if not valid: raise ValueError('AR01 reference/publication profile')
    inner = packet[HEADER.size:-4]
    if len(inner) < gm.HEADER.size+4: raise ValueError('AR01 short GM base')
    im, iv, ik, ie, iframe, iref, w, h, dx, dy, mw, mh, nm, ny, ncb, ncr = gm.HEADER.unpack_from(inner)
    if (im != gm.MAGIC or iv != 1 or ik not in (0,1) or ie != session
            or iframe != frame or bool(ik) != key or iref != refid
            or (mw,mh) != gm.roi.geometry(w,h) or dx or dy
            or nm != (mw*mh+3)//4 or len(inner) != gm.HEADER.size+nm+ny+ncb+ncr+4
            or body_crc(inner) != struct.unpack('<I', inner[-4:])[0]):
        raise ValueError('AR01 inner identity mismatch')
    for size, (pw,ph) in zip((ny,ncb,ncr), ((w,h),(w//2,h//2),(w//2,h//2))):
        blocks = ((pw+7)//8)*((ph+7)//8)
        if not gm.word_coeff.PAYLOAD_OVERHEAD <= size <= 128*blocks+gm.word_coeff.PAYLOAD_OVERHEAD:
            raise ValueError('AR01 inner plane bound')
    gm.roi.unpack_map(inner[gm.HEADER.size:gm.HEADER.size+nm],mw,mh)
    parsed = gm.parse(inner, session) if decode else None
    return dict(epoch=session, frame_id=frame, key=key, promoted=promoted,
                reference_bank=refbank, reference_id=refid, reference_tag=reftag,
                destination_bank=dest, stored_tag=newtag, inner=inner,
                parsed=parsed, width=w, height=h, body_crc=body_crc(packet), packet_bytes=len(packet))


def feedback(meta, status=ACK):
    if status not in (ACK, NACK): raise ValueError('AF01 feedback status')
    stored = status == ACK and meta['destination_bank'] != NO_BANK
    body = FEEDBACK.pack(b'AF01', 1, status, meta['epoch'], meta['frame_id'], meta['body_crc'],
                         meta['destination_bank'] if stored else NO_BANK,
                         meta['frame_id'] if stored else gm.NO_REF, meta['stored_tag'] if stored else ZERO)
    return seal(body)


def parse_feedback(data):
    if type(data) is not bytes or len(data) != FEEDBACK.size+4 or body_crc(data) != struct.unpack('<I', data[-4:])[0]:
        raise ValueError('AF01 length/CRC')
    magic, version, status, epoch, frame, crc, slot, stored_id, tag = FEEDBACK.unpack_from(data)
    if magic != b'AF01' or version != 1 or status not in (ACK, NACK) or epoch == gm.NO_REF or frame == gm.NO_REF:
        raise ValueError('AF01 profile')
    return dict(status=status, epoch=epoch, frame_id=frame, body_crc=crc,
                stored_bank=slot, stored_id=stored_id, stored_tag=tag)


class Encoder(Banks):
    def __init__(self, epoch=1, window=3, frame_cap=49152):
        if type(window) is not int or not 1 <= window <= 8:
            raise ValueError('AR01 transaction window')
        if type(frame_cap) is not int or not HEADER.size+gm.HEADER.size+8 <= frame_cap <= 49152:
            raise ValueError('AR01 frame cap')
        super().__init__(epoch, max_readers=window)
        self.window, self.frame_cap = window, frame_cap
        self.pending = {}
        self.last_issued = -1
        self.peak_pending = 0
        self._generation = 0
        self.forward_calls = 0
        self.last_info = None

    def can_prepare(self, force_key=False, promote=False):
        if any(r['key'] or r['promoted'] for r in self.pending.values()): return False
        if force_key or self.banks[0] is None or promote:
            return not self.pending and not self._leases
        return len(self.pending) < self.window

    def acquire(self, slot):
        if any(r['key'] or r['promoted'] for r in self.pending.values()):
            raise ValueError('AR01 pending writer reservation')
        return self._acquire(slot)

    def prepare(self, rgb, frame_id, *, scale_map=None, quant_scale=16, force_key=False, promote=False):
        start = time.perf_counter_ns()
        if type(force_key) is not bool or type(promote) is not bool:
            raise ValueError('AR01 key/promotion booleans')
        a = gm.ft._check_rgb(rgb); h, w = a.shape[:2]
        key = bool(force_key or self.banks[0] is None or self.banks[0].planes[0].shape != (h, w))
        promoted = bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued < frame_id < gm.NO_REF or not self.can_prepare(key, promoted):
            raise ValueError('AR01 credit/identity/promotion drain')
        refslot = NO_BANK if key else (1 if self.banks[1] is not None else 0)
        ref = None if key else self.banks[refslot]
        if ref is not None and ref.planes[0].shape != (h, w): raise ValueError('AR01 reference geometry')
        local = gm.Encoder(self.epoch, self.window)
        if ref is not None: local.anchor_id, local._anchor = ref.frame_id, ref.planes
        began = time.perf_counter_ns()
        prepared = local.analyze(a, frame_id, force_key=key, mode='zero')
        analyze_ms = ms(began)
        if scale_map is None:
            if type(quant_scale) is not int or quant_scale not in gm.roi.SCALES: raise ValueError('AR01 scale')
            mw, mh = gm.roi.geometry(w, h); scale_map = np.full((mh, mw), quant_scale, np.uint8)
        began = time.perf_counter_ns()
        candidate = local.encode_candidate(prepared, scale_map)
        candidate_ms = ms(began)
        self.forward_calls += 3
        reconstruction_ms = tag_ms = 0.0; planes = None; tag = ZERO
        # Promotion reconstruction is mandatory paid sender work, not the oracle.
        if key or promoted:
            began = time.perf_counter_ns()
            planes = gm.reconstruct(candidate.coefficients, prepared.prediction, candidate.scale_map, w, h)
            reconstruction_ms = ms(began)
            began = time.perf_counter_ns(); tag = reference_tag(planes); tag_ms = ms(began)
        dest = 0 if key else (1 if promoted else NO_BANK)
        body = HEADER.pack(b'AR01', 1, KEY if key else PROMOTE if promoted else 0,
                           self.epoch, frame_id, refslot, dest,
                           gm.NO_REF if ref is None else ref.frame_id,
                           ZERO if ref is None else ref.tag, tag, len(candidate.packet))+candidate.packet
        packet = seal(body)
        fit = len(packet) <= self.frame_cap
        info = dict(bytes=len(packet), inner_bytes=len(candidate.packet), envelope_bytes=HEADER.size+4,
                    analyze_ms=analyze_ms, candidate_ms=candidate_ms,
                    reconstruction_ms=reconstruction_ms, reference_tag_ms=tag_ms,
                    forward_calls=3, cap_fit=fit, promotion_reconstruction_paid=bool(key or promoted),
                    reference_read_bytes=0 if ref is None else pixels(ref.planes),
                    reconstruction_write_bytes=0 if planes is None else pixels(planes),
                    reference_read_array_bytes=0 if ref is None else sum(p.nbytes for p in ref.planes),
                    reconstruction_write_array_bytes=0 if planes is None else sum(p.nbytes for p in planes),
                    tag_read_bytes=0 if planes is None else 4+2*pixels(planes),
                    retained_banks_before=sum(b is not None for b in self.banks.values()),
                    reference_array_bytes_before=self.retained_bytes())
        self.reference_read_bytes += info['reference_read_bytes']
        self.reconstruction_write_bytes += info['reconstruction_write_bytes']
        self.reference_read_array_bytes += info['reference_read_array_bytes']
        self.reconstruction_write_array_bytes += info['reconstruction_write_array_bytes']
        self.tag_read_bytes += info['tag_read_bytes']
        if fit:
            row = dict(key=key, promoted=promoted, packet=packet, planes=planes,
                       reference_bank=refslot, reference_id=None if ref is None else ref.frame_id,
                       reference_tag=ZERO if ref is None else ref.tag,
                       reference=None if (key or promoted) else ref,
                       destination_bank=dest, stored_tag=tag, body_crc=body_crc(packet))
            self.pending[frame_id] = row
            if key: self.banks = {0: None, 1: None}
            elif promoted: self.banks[1] = None  # reserved/uncertain until exact publication ACK
            self.last_issued = frame_id; self._generation += 1
            self.peak_pending = max(self.peak_pending, len(self.pending))
        self._observe(); self.last_info = info
        return Decision(packet if fit else None, frame_id, key, promoted, refslot,
                        None if ref is None else ref.frame_id, ZERO if ref is None else ref.tag,
                        dest, ms(start), info)

    def expected_hash(self, frame_id):
        row = self.pending[frame_id]
        if row['planes'] is not None: planes = row['planes']
        else:
            meta = identity(row['packet'], self.epoch, self.frame_cap, decode=True)
            p = meta['parsed']; ref = row['reference']
            planes = gm.reconstruct(p['coefficients'], tuple(gm.mt.predict(ref.planes, p['dx'], p['dy'])),
                                    p['scale_map'], p['width'], p['height'])
        return hashlib.sha256(gm.ft.planes_to_rgb(planes).tobytes()).hexdigest()

    def ack(self, data):
        ack = parse_feedback(data)
        if ack['epoch'] != self.epoch: raise ValueError('AF01 wrong session')
        frame = ack['frame_id']; row = self.pending.get(frame)
        if row is None: return False
        if ack['body_crc'] != row['body_crc']: raise ValueError('AF01 wrong outer content')
        stored = row['destination_bank'] != NO_BANK and ack['status'] == ACK
        expected = (row['destination_bank'], frame, row['stored_tag']) if stored else (NO_BANK, gm.NO_REF, ZERO)
        if (ack['stored_bank'], ack['stored_id'], ack['stored_tag']) != expected:
            raise ValueError('AF01 wrong reference publication')
        if ack['status'] == NACK: return self.expire(frame)
        if stored:
            if not self._writable(row['destination_bank']): raise ValueError('AR01 ACK while destination read-owned')
            if row['key']: self.banks = {0: None, 1: None}
            self.banks[row['destination_bank']] = Bank(frame, row['stored_tag'], row['planes'])
        self.pending.pop(frame); self._generation += 1; self._observe()
        return True

    def expire(self, frame_id):
        row = self.pending.pop(frame_id, None)
        if row is None: return False
        if row['key']: self.banks = {0: None, 1: None}
        elif row['promoted']: self.banks[1] = None
        self._generation += 1
        return True


class Receiver(Banks):
    def __init__(self, epoch=1, frame_cap=49152, max_readers=3):
        if type(frame_cap) is not int or not HEADER.size+gm.HEADER.size+8 <= frame_cap <= 49152:
            raise ValueError('AR01 receiver frame cap')
        super().__init__(epoch, max_readers)
        self.frame_cap = frame_cap
        self.last_frame_id = -1
        self.active = None

    def acquire(self, slot):
        if self.active is not None:
            dest = self.active.meta['destination_bank']
            if self.active.meta['key'] or slot == dest: raise ValueError('AR01 reserved writer')
        return self._acquire(slot)

    def begin(self, packet):
        if self.active is not None: raise ValueError('AR01 serialized decoder already active')
        meta = identity(packet, self.epoch, self.frame_cap, decode=True); p = meta['parsed']
        frame, w, h = meta['frame_id'], p['width'], p['height']
        if frame <= self.last_frame_id: raise ValueError('AR01 replay/regression')
        dest = meta['destination_bank']
        if meta['key']:
            if self._leases: raise ValueError('AR01 key overwrites read-owned bank')
        elif dest != NO_BANK and not self._writable(dest):
            raise ValueError('AR01 destination read-owned')
        lease = None
        try:
            if meta['key']:
                prediction = tuple(np.full(shape, 128, np.int16) for shape in ((h,w),(h//2,w//2),(h//2,w//2)))
            else:
                bank = self.banks[meta['reference_bank']]
                if (bank is None or bank.frame_id != meta['reference_id'] or bank.tag != meta['reference_tag']
                        or bank.planes[0].shape != (h, w)):
                    raise ValueError('AR01 missing exact reconstructed reference')
                lease = self._acquire(meta['reference_bank'])
                prediction = tuple(gm.mt.predict(bank.planes, p['dx'], p['dy']))
                self.reference_read_bytes += pixels(bank.planes)
                self.reference_read_array_bytes += sum(p.nbytes for p in bank.planes)
            planes = gm.reconstruct(p['coefficients'], prediction, p['scale_map'], w, h)
            self.reconstruction_write_bytes += pixels(planes)
            self.reconstruction_write_array_bytes += sum(p.nbytes for p in planes)
            if dest != NO_BANK:
                self.tag_read_bytes += 4+2*pixels(planes)
                if reference_tag(planes) != meta['stored_tag']:
                    raise ValueError('AR01 published reconstruction tag mismatch')
            rgb = gm.ft.planes_to_rgb(planes)
            rgb.setflags(write=False)
            info = dict(frame_id=frame, key=meta['key'], promoted=meta['promoted'],
                        reference_bank=meta['reference_bank'], reference_id=None if meta['key'] else meta['reference_id'],
                        destination_bank=dest, reference_read_bytes=0 if lease is None else pixels(lease.bank.planes),
                        reconstruction_write_bytes=pixels(planes), packet_bytes=len(packet),
                        reference_read_array_bytes=0 if lease is None else sum(p.nbytes for p in lease.bank.planes),
                        reconstruction_write_array_bytes=sum(p.nbytes for p in planes),
                        tag_read_bytes=0 if dest == NO_BANK else 4+2*pixels(planes),
                        scope='AR01 software two-bank/reference/read-lease proof, not target memory timing')
            published_meta = MappingProxyType({k:v for k,v in meta.items() if k not in ('parsed','inner')})
            task = Decode(self._owner, published_meta, planes, rgb, lease, MappingProxyType(info))
            self.active = task
            return task
        except BaseException:
            if lease is not None: self.release(lease)
            raise

    def complete(self, task):
        if not isinstance(task, Decode) or task.owner is not self._owner or task is not self.active:
            raise ValueError('AR01 foreign/stale decode completion')
        meta = task.meta
        if task.lease is not None: self.release(task.lease)
        if meta['key']: self.banks = {0: None, 1: None}
        dest = meta['destination_bank']
        if dest != NO_BANK:
            self.banks[dest] = Bank(meta['frame_id'], meta['stored_tag'], task.planes)
        self.last_frame_id = meta['frame_id']; self.active = None
        self._observe()
        info = dict(task.info, retained_banks=sum(b is not None for b in self.banks.values()),
                    retained_reference_array_bytes=self.retained_bytes())
        return task.rgb, info, feedback(meta)

    def abort(self, task):
        if task is not self.active or task.owner is not self._owner:
            raise ValueError('AR01 foreign/stale decode abort')
        if task.lease is not None: self.release(task.lease)
        self.active = None

    def receive(self, packet): return self.complete(self.begin(packet))
