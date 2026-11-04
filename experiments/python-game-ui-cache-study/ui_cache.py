"""Bounded exact RGB565 UI payload reuse through the frozen hybrid selector."""
from collections import OrderedDict
import copy
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-hybrid-study'))
import hybrid_codec as hybrid


def ms(start):
    return (time.perf_counter_ns() - start) / 1e6


class PatchCache:
    """Up to four canvas/rectangle/policy entries; current words always compared."""
    def __init__(self, max_entries=4):
        if type(max_entries) is not int or not 0 <= max_entries <= 4:
            raise ValueError('at most four patch entries')
        self.max_entries = max_entries
        self._entries = OrderedDict()
        self.hits = self.misses = self.evictions = 0

    def persistent_bytes(self):
        return sum(e['words'].nbytes + len(e['packet']) for e in self._entries.values())

    def __call__(self, rgb, rect, policy):
        started = time.perf_counter_ns()
        a = hybrid.gm.ft._check_rgb(rgb)
        height, width = a.shape[:2]
        x, y, rw, rh = hybrid.hp._rect(rect, width, height)
        if policy not in ('hp01', 'adaptive_row'):
            raise ValueError('supported patch policy')
        key = (width, height, (x, y, rw, rh), policy)
        began = time.perf_counter_ns()
        words = hybrid.hp.corpus.rgb565(a[y:y+rh, x:x+rw])
        conversion_ms = ms(began)
        began = time.perf_counter_ns()
        entry = self._entries.get(key)
        hit = entry is not None and np.array_equal(entry['words'], words)
        compare_ms = ms(began)
        copy_ms = encoder_ms = 0.0
        evicted = False
        if hit:
            self.hits += 1
            self._entries.move_to_end(key)
            packet = entry['packet']
            # Historical work stays labeled historical. No old candidate cost
            # is reported as if this hit ran HP/HR search again.
            details = dict(current_candidate_count=0, current_attempts=[], current_encoder_details={},
                           reused_candidate_details=copy.deepcopy(entry['history']))
        else:
            self.misses += 1
            began = time.perf_counter_ns()
            packet, history = hybrid._encode_patch(a, rect, policy)
            encoder_ms = ms(began)
            current_attempts = ([dict(format='HP01', bytes=history['hp01_bytes'])]
                                + [dict(format='HR01', **r) for r in history['attempts']]
                                if policy == 'adaptive_row' else copy.deepcopy(history['attempts']))
            details = dict(current_candidate_count=len(current_attempts),
                           current_attempts=current_attempts,
                           current_encoder_details=history, reused_candidate_details=None)
            if self.max_entries:
                began = time.perf_counter_ns()
                saved = words.copy()
                saved.setflags(write=False)
                if key not in self._entries and len(self._entries) == self.max_entries:
                    self._entries.popitem(last=False)
                    self.evictions += 1
                    evicted = True
                self._entries[key] = dict(words=saved, packet=packet, history=copy.deepcopy(history))
                self._entries.move_to_end(key)
                copy_ms = ms(began)
        details.update(cache_hit=bool(hit), cache_key=key, conversion_ms=conversion_ms,
                       compare_ms=compare_ms, copy_ms=copy_ms, current_encoder_ms=encoder_ms,
                       current_total_ms=ms(started), persistent_cache_bytes=self.persistent_bytes(),
                       cache_entries=len(self._entries), evicted=evicted,
                       scope='Exact current RGB565 rectangle words; full HP01/HR01 bytes reused, normal selector validation/cap/assembly still run')
        return packet, details


def select(base, rgb, cache, config=None, **kwargs):
    return hybrid.select_frame(base, rgb, config, patch_encoder=cache, **kwargs)
