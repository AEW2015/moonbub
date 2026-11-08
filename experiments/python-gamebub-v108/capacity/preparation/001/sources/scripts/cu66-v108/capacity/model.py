#!/usr/bin/env python3
"""Finite independent arithmetic, register alignment and header schedule models."""
import hashlib
import json
import random
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT/'fpga/experiments/cu66-v108-capacity'
AREA = ROOT/'experiments/python-gamebub-v108/capacity'
MASK = (1 << 32)-1
UNITS = (1 << 28)-1


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def aligned_count(n):
    return ((n*4+15)&MASK)&0xfffffff0


def bounds(prefix):
    a = (2+(prefix >> 4))&UNITS
    return (((16384-a)&UNITS) << 3, ((~a)&UNITS) << 3, a > 16384)


def literal_bad(b, raw, prefix):
    if raw:
        planned = (32+128*b)&MASK
    else:
        planned = (32+(((2*b+15)&MASK)&0xfffffff0)+prefix)&MASK
    return planned > 262144


def bound_bad(b, raw, value):
    upper, lower, wrap = value
    return b > 2047 if raw else b > upper or (wrap and b <= lower)


class Pipe:
    """Exact nonblocking-assignment positions; output oracle uses literal prefix."""
    def __init__(self, rng):
        self.s = dict(p12=rng.getrandbits(32), a3=rng.getrandbits(32),
            p1=rng.getrandbits(32), a2=rng.getrandbits(28),
            u3=rng.getrandbits(28), l3=rng.getrandbits(28), w3=bool(rng.getrandbits(1)),
            valid=0, live=False, cache=bounds(rng.getrandbits(28) << 4))
        self.pending = deque()
        self.t = self.commits = self.flush_commit_collisions = self.flushes = 0
        self.max_pending = 0

    def step(self, prefix12, count3, capture=False, flush=False):
        old = self.s
        expected = None
        if old['valid']&8:
            due, owner = self.pending.popleft()
            assert due == self.t
            expected = bounds(owner)
        if flush:
            self.pending.clear()
            self.flushes += 1
            self.flush_commit_collisions += bool(old['valid']&8)
        elif capture:
            self.pending.append((self.t+4, (prefix12+aligned_count(count3))&MASK))
        s = dict(p12=prefix12, a3=aligned_count(count3),
            p1=(old['p12']+old['a3'])&MASK,
            a2=((old['p1'] >> 4)+2)&UNITS,
            u3=(16384-old['a2'])&UNITS, l3=(~old['a2'])&UNITS,
            w3=old['a2'] > 16384,
            valid=0 if flush else ((old['valid'] << 1)|int(capture))&15,
            live=False if flush else old['live'] or bool(old['valid']&8), cache=old['cache'])
        if old['valid']&8:
            s['cache'] = (old['u3'] << 3, old['l3'] << 3, old['w3'])
            assert s['cache'] == expected
            self.commits += 1
        self.s = s
        self.max_pending = max(self.max_pending, len(self.pending))
        assert len(self.pending) <= 4
        self.t += 1
        return expected is not None


def header(pipe, state, counts, rng, abort_index=None):
    pipe.step(rng.getrandbits(32), rng.getrandbits(32), flush=True)
    packet = [rng.randrange(256) for _ in range(46)]
    for i, n in enumerate(counts):
        packet[30+4*i:34+4*i] = n.to_bytes(4, 'little')
    fetched = [rng.randrange(256) for _ in range(46)]
    captured = committed = None
    edge = 0
    for index in range(46):
        for wait in (False, True):
            old_a, old_p12 = state['a'][:], state['p12']
            next_p12 = (old_a[0]+old_a[1])&MASK
            next_p123 = (old_p12+old_a[2])&MASK
            n3 = (packet[index] << 24)|(fetched[40] << 16)|(fetched[39] << 8)|fetched[38]
            flush = bool(wait and index == abort_index)
            take = wait and index == 41 and not flush
            if take:
                assert n3 == counts[2]
                assert old_p12 == (aligned_count(counts[0])+aligned_count(counts[1]))&MASK
                captured = edge
            if pipe.step(old_p12, n3, take, flush):
                committed = edge
            if flush:
                assert not pipe.s['live']
                return dict(aborted=True, edges=edge+1)
            if wait:
                if index in (33, 37, 41):
                    slot = (index-33)//4
                    state['a'][slot] = aligned_count(counts[slot])
                fetched[index] = packet[index]
            state.update(p12=next_p12, p123=next_p123)
            edge += 1
    # HEADER follows46REQ/WAIT pairs; it is not moved by the cache.
    pipe.step(state['p12'], rng.getrandbits(32))
    prefix = sum(aligned_count(n) for n in counts)&MASK
    assert pipe.s['live'] and pipe.s['cache'] == bounds(prefix)
    assert captured == 83 and committed == 87 and edge == 92
    held = 0
    for _ in range(17):
        old = pipe.s['cache']
        pipe.step(rng.getrandbits(32), rng.getrandbits(32))
        b = rng.randrange(1 << 17)
        assert pipe.s['cache'] == old
        assert bound_bad(b, False, pipe.s['cache']) == literal_bad(b, False, prefix)
        held += 1
    return dict(aborted=False, edges=93, capture=83, commit=87, header=92, held=held)


def main():
    AREA.mkdir(parents=True, exist_ok=True)
    recipe = json.loads((SRC/'edit-recipe.json').read_text())
    for name, e in recipe['production'].items():
        p = ROOT/e['original']
        assert sha(p) == e['original_sha256']
        text = p.read_text()
        for edit in e['edits']:
            assert text.count(edit['before']) == 1
            text = text.replace(edit['before'], edit['after'], 1)
        assert text == (SRC/name).read_text() and sha(SRC/name) == e['candidate_sha256']
        for edit in reversed(e['edits']):
            assert text.count(edit['after']) == 1
            text = text.replace(edit['after'], edit['before'], 1)
        assert text == p.read_text()
    rng = random.Random(108201)
    prefixes = sorted({0, 16, 0x3ffd0, 0x3ffe0, 0x3fff0, 0x40000,
        0xffffffe0, 0xfffffff0, 0xffffffd0, 0xfffc0000,
        *[rng.getrandbits(28) << 4 for _ in range(6)]})
    grid = 0
    for p in prefixes:
        value = bounds(p)
        for b in range(1 << 17):
            assert bound_bad(b, False, value) == literal_bad(b, False, p)
            grid += 1
    for b in range(1 << 17):
        assert bound_bad(b, True, bounds(0)) == literal_bad(b, True, 0)
    random_cases = 0
    for _ in range(300000):
        ns = [rng.getrandbits(32) for _ in range(3)]
        p = sum(aligned_count(n) for n in ns)&MASK
        b = rng.randrange(1 << 17)
        assert bound_bad(b, False, bounds(p)) == literal_bad(b, False, p)
        random_cases += 1
    pipelines = []
    for seed in (108201, 108202, 108203, 108204):
        r = random.Random(seed)
        pipe = Pipe(r)
        for _ in range(30000):
            pipe.step(r.getrandbits(28) << 4, r.getrandbits(32), r.randrange(4) != 0, r.randrange(97) == 0)
        for _ in range(5):
            pipe.step(r.getrandbits(32), r.getrandbits(32))
        assert not pipe.pending
        pipelines.append(dict(seed=seed, clocks=pipe.t, commits=pipe.commits,
            flushes=pipe.flushes, flush_commit_collisions=pipe.flush_commit_collisions,
            max_pending=pipe.max_pending))
    pipe = Pipe(rng)
    state = dict(a=[rng.getrandbits(28) << 4 for _ in range(3)], p12=rng.getrandbits(32), p123=rng.getrandbits(32))
    successful = abandoned = held = 0
    for _ in range(512):
        counts = [rng.getrandbits(32) for _ in range(3)]
        result = header(pipe, state, counts, rng)
        successful += 1
        held += result['held']
        for index in (33, 37, 41, 43):
            assert header(pipe, state, [rng.getrandbits(32) for _ in range(3)], rng, index)['aborted']
            abandoned += 1
            result = header(pipe, state, [rng.getrandbits(32) for _ in range(3)], rng)
            successful += 1
            held += result['held']
    assert pipe.flush_commit_collisions >= 512
    files = [SRC/n for n in recipe['production']]+[SRC/'edit-recipe.json', Path(__file__), Path(__file__).parent/'prepare.py']
    result = dict(schema='v108-capacity-control-model-preparation-v1', status='PASS_PREPARATION_MODEL_NOT_RTL',
        actual_RTL_run=False, native_run=False, formal_tool_run=False,
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in files},
        full_u17_block_grid_cases=grid, arbitrary_full_u32_count_triples=random_cases,
        raw_full_u17_cases=131072, pipelines=pipelines,
        header_schedule=dict(successful_prepared_headers=successful, abandoned_prepared_headers=abandoned,
            held_metadata_edges=held, last_word_capture_edge=83, bounds_commit_edge=87,
            earliest_header_edge=92, post_capture_edges=4, public_added_cycles=0,
            flush_commit_collisions=pipe.flush_commit_collisions),
        limits=['Finite integer/register/header schedule models only; no actual RTL, formal tool, area, timing or operating-clock result.',
            'Actual complete production capture/RAW and both-controller-mode/public/golden proofs remain mandatory before selection.',
            'Private unowned bound payload may change on a simultaneous flush/commit; validity clears immediately.'])
    (AREA/'preparation.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_sha256'}, indent=2))


if __name__ == '__main__':
    main()
