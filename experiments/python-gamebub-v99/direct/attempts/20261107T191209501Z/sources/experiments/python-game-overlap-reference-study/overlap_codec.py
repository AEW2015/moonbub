"""Bank-specific overlap policy with unchanged AR01/AF01 coding and feedback.

Copied prepare arithmetic is identical to frozen recent_codec except explicit
reference selection and bank-specific admission. No temporary bank substitution.
"""
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-recent-reference-study'))
import recent_codec as frozen
from recent_codec import (gm, ms, ZERO, pixels, reference_tag, NO_BANK, HEADER,
                          KEY, PROMOTE, seal, body_crc, Decision)


class Encoder(frozen.Encoder):
    def can_prepare(self, force_key=False, promote=False):
        if force_key or self.banks[0] is None:
            return not self.pending and not self._leases
        if any(r['key'] for r in self.pending.values()): return False
        if len(self.pending)>=self.window: return False
        if promote:
            return (not any(r['promoted'] for r in self.pending.values())
                    and not any(r['reference_bank']==1 for r in self.pending.values())
                    and self._writable(1))
        return True

    def acquire(self, slot):
        if any(r['key'] for r in self.pending.values()):
            raise ValueError('AR01 pending key writer')
        if slot==1 and any(r['promoted'] for r in self.pending.values()):
            raise ValueError('AR01 pending bank1 writer')
        return self._acquire(slot)

    def prepare(self, rgb, frame_id, *, scale_map=None, quant_scale=16, force_key=False, promote=False, reference_bank=None):
        start = time.perf_counter_ns()
        if type(force_key) is not bool or type(promote) is not bool:
            raise ValueError('AR01 key/promotion booleans')
        a = gm.ft._check_rgb(rgb); h, w = a.shape[:2]
        key = bool(force_key or self.banks[0] is None or self.banks[0].planes[0].shape != (h, w))
        promoted = bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued < frame_id < gm.NO_REF or not self.can_prepare(key, promoted):
            raise ValueError('AR01 credit/identity/promotion drain')
        if reference_bank is not None and (type(reference_bank) is not int or reference_bank not in (0, 1)):
            raise ValueError('AR01 explicit reference bank')
        if key and reference_bank is not None:
            raise ValueError('AR01 key has no source bank')
        refslot = NO_BANK if key else (reference_bank if reference_bank is not None else (1 if self.banks[1] is not None else 0))
        if not key and self.banks[refslot] is None:
            raise ValueError('AR01 explicit reference is not confirmed')
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
        info = dict(reference_choice_explicit=reference_bank is not None,
                    pending_before=len(self.pending),
                    pending_writers_before=sum(r['key'] or r['promoted'] for r in self.pending.values()),
                    bank0_readers_before=sum(l.slot==0 for l in self._leases),
                    bank1_readers_before=sum(l.slot==1 for l in self._leases),
                    pending_bank0_consumers=sum(r['reference_bank']==0 for r in self.pending.values()),
                    pending_bank1_consumers=sum(r['reference_bank']==1 for r in self.pending.values()),
                    bytes=len(packet), inner_bytes=len(candidate.packet), envelope_bytes=HEADER.size+4,
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

