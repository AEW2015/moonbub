#!/usr/bin/env python3
"""Finite two-state algebra model for V125 admission tile predicates.

This compares full-width original equations with owned registered predicate
successors. It is an independent Python model, not RTL, synthesis, or timing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[2]
MASK32 = 0xFFFF_FFFF
HIDDEN_PLANE0 = (
    (633, 651), (723, 741), (993, 1011), (1083, 1101),
    (4071, 4110), (4161, 4200), (4251, 4290), (4431, 4460),
    (4521, 4550),
)
HIDDEN_OTHER_PLANES = ((1046, 1064),)


def u32(value: int) -> int:
    return value & MASK32


def tile_count(plane: int) -> int:
    assert 0 <= plane < 4
    return 5400 if plane == 0 else 1350


def hidden(plane: int, tile: int) -> bool:
    assert 0 <= plane < 4 and 0 <= tile <= MASK32
    ranges = HIDDEN_PLANE0 if plane == 0 else HIDDEN_OTHER_PLANES
    return any(lo <= tile <= hi for lo, hi in ranges)


def terminal(plane: int, tile: int) -> bool:
    """Original exact equality; deliberately not >=."""
    return tile == tile_count(plane)


def group_terminal(tile: int, group_end: int) -> bool:
    """Original exact equality; deliberately not >=."""
    return tile == group_end


def next_group_end(plane: int, tile: int) -> int:
    """Literal uint32 `(tile+16)<count ? tile+16 : count` successor."""
    plus16 = u32(tile + 16)
    count = tile_count(plane)
    return plus16 if plus16 < count else count


class PredicateState:
    """Three predicate payloads plus verification-only owner keys/validity."""
    def __init__(self, plane: int, tile: int, group_end: int | None,
                 epoch: int = 0, group_owned: bool = True):
        self.plane = plane
        self.tile = tile
        self.group_end = group_end
        self.epoch = epoch
        self.group_end_known = group_end is not None
        self.group_owned = group_owned and self.group_end_known
        self.prepared_tile_hidden = hidden(plane, tile)
        self.prepared_tile_terminal = terminal(plane, tile)
        self.prepared_group_terminal = (
            group_terminal(tile, group_end) if self.group_owned else False
        )
        self.owner_hidden = self.tile_key()
        self.owner_terminal = self.tile_key()
        self.owner_group = self.group_key() if self.group_owned else None
        self.check_owned()

    def tile_key(self):
        return (self.epoch, self.plane, self.tile)

    def group_key(self):
        return (self.epoch, self.plane, self.tile, self.group_end)

    def check_owned(self):
        if self.owner_hidden is not None:
            assert self.owner_hidden == self.tile_key()
            assert self.prepared_tile_hidden == hidden(self.plane, self.tile)
        if self.owner_terminal is not None:
            assert self.owner_terminal == self.tile_key()
            assert self.prepared_tile_terminal == terminal(self.plane, self.tile)
        if self.owner_group is not None:
            assert self.group_owned and self.owner_group == self.group_key()
            assert self.prepared_group_terminal == group_terminal(self.tile, self.group_end)

    def require_tile_owners(self):
        assert self.owner_hidden == self.tile_key()
        assert self.owner_terminal == self.tile_key()
        self.check_owned()

    def require_group_owner(self):
        assert self.owner_group == self.group_key()
        self.check_owned()

    def refresh_tile_predicates(self):
        self.prepared_tile_hidden = hidden(self.plane, self.tile)
        self.prepared_tile_terminal = terminal(self.plane, self.tile)
        self.owner_hidden = self.tile_key()
        self.owner_terminal = self.tile_key()
        # Key/plane-only writers do not prepare the group terminal. Its owner
        # key is invalidated until a MODE_BIT tag commit snapshots all keys.
        self.owner_group = None
        self.group_owned = False
        self.check_owned()

    def refresh_group_predicate(self):
        assert self.group_owned and self.group_end is not None
        self.prepared_group_terminal = group_terminal(self.tile, self.group_end)
        self.owner_group = self.group_key()
        self.check_owned()

    def header_check_success(self):
        # New parse epoch: tile=0, plane=0. group_end is not written here and
        # the group predicate is unowned until MODE_BIT commits a tag.
        self.epoch += 1
        self.plane, self.tile = 0, 0
        self.group_end_known = False
        self.group_owned = False
        self.owner_group = None
        self.refresh_tile_predicates()
        return 'header_success'

    def group_begin(self):
        self.require_tile_owners()
        self.group_end = next_group_end(self.plane, self.tile)
        self.group_end_known = True
        self.group_owned = False
        self.owner_group = None
        return 'group_begin'

    def key_tile(self):
        self.require_tile_owners()
        if self.prepared_tile_terminal:
            old_plane = self.plane
            self.tile = 0
            if old_plane != 2:
                self.plane = (old_plane + 1) & 0x3
            self.group_owned = False
            self.owner_group = None
            self.refresh_tile_predicates()
            return 'key_terminal'
        # Hidden is consumed by the canonical mode-write/coordinate branch;
        # the tile counter itself advances identically for visible/hidden.
        _ = self.prepared_tile_hidden
        self.tile = u32(self.tile + 1)
        self.refresh_tile_predicates()
        return 'key_step'

    def mode_bit_mixed_consume(self):
        self.require_tile_owners()
        self.require_group_owner()
        self.tile = u32(self.tile + 1)
        self.refresh_all_predicates()
        return 'mode_bit_step'

    def refresh_all_predicates(self):
        assert self.group_end_known and self.group_end is not None
        self.prepared_tile_hidden = hidden(self.plane, self.tile)
        self.prepared_tile_terminal = terminal(self.plane, self.tile)
        self.owner_hidden = self.tile_key()
        self.owner_terminal = self.tile_key()
        self.group_owned = True
        self.refresh_group_predicate()

    def mode_bit_tag_commit(self, tag: int, group_visible: int):
        self.require_tile_owners()
        assert self.group_end_known and self.group_end is not None
        assert 0 <= tag < 4
        if group_visible == 0 and tag == 3:
            self.tile = self.group_end
            self.refresh_all_predicates()
            return 'mode_bit_hidden_only_jump_prime'
        # A committed ordinary tag atomically owns the current (p,t,g) tuple.
        self.refresh_all_predicates()
        return 'mode_bit_tag_commit_current'

    def group_tile(self, tag: int, mixed_ones: int = 0, group_visible: int = 1):
        assert 0 <= tag < 4
        self.require_tile_owners()
        self.require_group_owner()
        # Original terminal equality has priority over mixed-count error and
        # over hidden/tag stepping.
        if self.prepared_group_terminal:
            if tag == 2 and (mixed_ones == 0 or mixed_ones == group_visible):
                return 'group_terminal_error8'
            return 'group_terminal'
        if self.prepared_tile_hidden or tag == 0:
            self.tile = u32(self.tile + 1)
            self.refresh_all_predicates()
            return 'group_hidden_or_zero_step'
        if tag == 1:
            self.tile = u32(self.tile + 1)
            self.refresh_all_predicates()
            return 'group_one_step'
        # Tags 2/3 enter mixed-bit parsing without tile advance.
        return 'group_enter_mixed_bit'

    def group_next(self):
        self.require_tile_owners()
        if not self.prepared_tile_terminal:
            return 'group_next_hold_nonterminal'
        old_plane = self.plane
        if old_plane == 2:
            return 'group_next_finish_plane2_hold'
        self.plane = (old_plane + 1) & 0x3
        self.tile = 0
        self.group_end_known = False
        self.group_owned = False
        self.owner_group = None
        self.refresh_tile_predicates()
        return 'group_next_advance_plane'

    def hold(self):
        before = self.snapshot()
        self.check_owned()
        assert self.snapshot() == before
        return 'hold'

    def cancel(self, kind: str):
        assert kind in ('reset', 'start', 'abort')
        # Payload registers are not reset by this verification policy. Owner
        # keys/epoch are verification-only and invalidate stale private data.
        self.epoch += 1
        self.owner_hidden = self.owner_terminal = self.owner_group = None
        self.group_end_known = False
        self.group_owned = False
        self.check_owned()
        return kind + '_cancel'

    def snapshot(self):
        return (self.plane, self.tile, self.group_end, self.epoch,
                self.prepared_tile_hidden, self.prepared_tile_terminal,
                self.prepared_group_terminal, self.owner_hidden,
                self.owner_terminal, self.owner_group, self.group_owned,
                self.group_end_known)


def boundary_tiles():
    values = {0, 1, 632, 633, 651, 652, 722, 723, 741, 742,
              992, 993, 1011, 1012, 1082, 1083, 1101, 1102,
              4070, 4071, 4110, 4111, 4160, 4161, 4200, 4201,
              4250, 4251, 4290, 4291, 4430, 4431, 4460, 4461,
              4520, 4521, 4550, 4551, 1045, 1046, 1064, 1065,
              0x7FFF_FFFF, 0x8000_0000, 0xFFFF_FFEF, 0xFFFF_FFF0,
              0xFFFF_FFF1, 0xFFFF_FFFE, 0xFFFF_FFFF}
    for count in (1350, 5400):
        values.update((count - 1, count, count + 1, count + 2))
    return sorted(v for v in values if 0 <= v <= MASK32)


def make_contexts():
    values = boundary_tiles()
    rng = random.Random(0x12571_1E)
    for _ in range(2048):
        values.append(rng.getrandbits(32))
    contexts = []
    for plane in range(4):
        count = tile_count(plane)
        for tile in values:
            groups = {tile, u32(tile - 1), u32(tile + 1), count,
                      u32(tile + 16), next_group_end(plane, tile), MASK32,
                      0x8000_0000}
            for group_end in groups:
                contexts.append((plane, tile, group_end))
    return contexts


def check_pure_domain(contexts):
    counts = {'contexts': 0, 'hidden_true': 0, 'tile_terminal_true': 0,
              'group_terminal_true': 0, 'strict_vs_ge_tile_witnesses': 0,
              'strict_vs_ge_group_witnesses': 0, 'wrap_tile_plus1': 0,
              'wrap_tile_plus16_group_end': 0}
    for plane, tile, group_end in contexts:
        state = PredicateState(plane, tile, group_end)
        assert state.prepared_tile_hidden == hidden(plane, tile)
        assert state.prepared_tile_terminal == (tile == (5400 if plane == 0 else 1350))
        assert state.prepared_group_terminal == (tile == group_end)
        counts['contexts'] += 1
        counts['hidden_true'] += int(hidden(plane, tile))
        counts['tile_terminal_true'] += int(terminal(plane, tile))
        counts['group_terminal_true'] += int(group_terminal(tile, group_end))
        counts['strict_vs_ge_tile_witnesses'] += int(tile > tile_count(plane) and not terminal(plane, tile))
        counts['strict_vs_ge_group_witnesses'] += int(tile > group_end and not group_terminal(tile, group_end))
        counts['wrap_tile_plus1'] += int(tile == MASK32 and u32(tile + 1) == 0)
        plus16 = u32(tile + 16)
        if tile >= MASK32 - 15 and plus16 < tile_count(plane):
            assert next_group_end(plane, tile) == plus16
            counts['wrap_tile_plus16_group_end'] += 1
    assert counts['strict_vs_ge_tile_witnesses'] > 0
    assert counts['strict_vs_ge_group_witnesses'] > 0
    assert counts['wrap_tile_plus1'] > 0 and counts['wrap_tile_plus16_group_end'] > 0
    return counts


def run_successor_cases(contexts):
    names = ('HEADER_CHECK_success', 'KEY_TILE_nonterminal', 'KEY_TILE_terminal',
        'MODE_BIT_mixed_consume', 'MODE_BIT_tag_commit_current',
        'MODE_BIT_hidden_only_jump_prime', 'MODE_BIT_hold',
        'GROUP_BEGIN_write', 'GROUP_BEGIN_invalidates_group_owner', 'GROUP_TILE_hidden_step',
        'GROUP_TILE_tag0_step', 'GROUP_TILE_tag1_step',
        'GROUP_TILE_tag2_or3_mixed_hold', 'GROUP_TILE_terminal',
        'GROUP_TILE_terminal_error8_priority', 'group_owner_wrong_plane_rejected',
        'GROUP_NEXT_nonterminal_hold',
        'GROUP_NEXT_terminal_plane_advance', 'GROUP_NEXT_plane2_terminal_hold',
        'hold', 'reset_cancel', 'start_cancel', 'abort_cancel')
    counts = {name: 0 for name in names}
    for plane, tile, group_end in contexts:
        m = PredicateState(plane, tile, group_end)
        assert m.header_check_success() == 'header_success'
        m.require_tile_owners(); assert m.owner_group is None
        counts['HEADER_CHECK_success'] += 1
        for key_tile, label in ((tile_count(plane), 'terminal'),
                                (tile if tile != tile_count(plane) else u32(tile + 1), 'nonterminal')):
            m = PredicateState(plane, key_tile, None, group_owned=False)
            branch = m.key_tile(); expected = 'key_terminal' if label == 'terminal' else 'key_step'
            assert branch == expected
            expected_plane = plane if label=='nonterminal' or plane==2 else ((plane+1)&3)
            expected_tile = u32(key_tile+1) if label=='nonterminal' else 0
            assert (m.plane,m.tile)==(expected_plane,expected_tile)
            m.require_tile_owners(); counts['KEY_TILE_'+label] += 1
        m = PredicateState(plane, tile, group_end)
        assert m.mode_bit_tag_commit(2,group_visible=2)=='mode_bit_tag_commit_current'
        m.require_group_owner(); counts['MODE_BIT_tag_commit_current'] += 1
        before=(m.plane,m.tile,m.group_end)
        assert m.mode_bit_mixed_consume() == 'mode_bit_step'; m.check_owned()
        assert (m.plane,m.tile,m.group_end)==(before[0],u32(before[1]+1),before[2])
        counts['MODE_BIT_mixed_consume'] += 1
        m = PredicateState(plane, tile, group_end)
        before=(m.plane,m.tile,m.group_end)
        assert m.mode_bit_tag_commit(3,group_visible=0)=='mode_bit_hidden_only_jump_prime'
        m.require_group_owner(); assert m.tile==group_end
        assert (m.plane,m.tile,m.group_end)==(before[0],before[2],before[2])
        counts['MODE_BIT_hidden_only_jump_prime'] += 1
        m = PredicateState(plane, tile, group_end); before=m.snapshot()
        assert m.hold()=='hold' and m.snapshot()==before
        counts['MODE_BIT_hold'] += 1
        m = PredicateState(plane, tile, None, group_owned=False)
        assert m.group_begin()=='group_begin'; assert m.owner_group is None
        assert m.group_end == next_group_end(plane,tile); counts['GROUP_BEGIN_write'] += 1
        counts['GROUP_BEGIN_invalidates_group_owner'] += 1
        assert m.mode_bit_tag_commit(0,group_visible=1)=='mode_bit_tag_commit_current'
        m.require_group_owner()
        nonterminal_group = group_end if tile != group_end else u32(group_end + 1)
        for tag in (0,1,2,3):
            m = PredicateState(plane, tile, nonterminal_group)
            outcome=m.group_tile(tag,mixed_ones=1,group_visible=2)
            if hidden(plane,tile) or tag==0:
                assert outcome=='group_hidden_or_zero_step'
                if hidden(plane,tile): counts['GROUP_TILE_hidden_step']+=1
                if tag==0: counts['GROUP_TILE_tag0_step']+=1
            elif tag==1:
                assert outcome=='group_one_step'
                counts['GROUP_TILE_tag1_step']+=1
            else:
                assert outcome=='group_enter_mixed_bit'
                counts['GROUP_TILE_tag2_or3_mixed_hold']+=1
            if outcome in ('group_hidden_or_zero_step','group_one_step'):
                assert m.tile==u32(tile+1)
            else:
                assert m.tile==tile
            m.check_owned()
        m=PredicateState(plane,tile,tile); before=m.snapshot()
        outcome=m.group_tile(2,mixed_ones=0,group_visible=3)
        assert outcome=='group_terminal_error8' and m.snapshot()==before
        counts['GROUP_TILE_terminal_error8_priority']+=1
        m=PredicateState(plane,tile,group_end); right_owner=m.owner_group
        m.owner_group=(m.epoch,(plane+1)&3,tile,group_end)
        try:
            m.require_group_owner()
        except AssertionError:
            pass
        else:
            raise AssertionError('wrong-plane group predicate owner was accepted')
        m.owner_group=right_owner; m.require_group_owner()
        counts['group_owner_wrong_plane_rejected']+=1
        m=PredicateState(plane,tile,tile)
        assert m.group_tile(0)=='group_terminal'; counts['GROUP_TILE_terminal']+=1
        m=PredicateState(plane,tile_count(plane),None,group_owned=False)
        outcome=m.group_next()
        if plane==2:
            assert outcome=='group_next_finish_plane2_hold'; counts['GROUP_NEXT_plane2_terminal_hold']+=1
            assert (m.plane,m.tile)==(plane,tile_count(plane))
        else:
            assert outcome=='group_next_advance_plane'; counts['GROUP_NEXT_terminal_plane_advance']+=1
            assert (m.plane,m.tile)==((plane+1)&3,0)
        nonterm=tile if tile != tile_count(plane) else u32(tile+1)
        m=PredicateState(plane,nonterm,None,group_owned=False)
        assert m.group_next()=='group_next_hold_nonterminal'; counts['GROUP_NEXT_nonterminal_hold']+=1
        for kind in ('reset','start','abort'):
            m=PredicateState(plane,tile,group_end)
            payload=(m.prepared_tile_hidden,m.prepared_tile_terminal,m.prepared_group_terminal)
            assert m.cancel(kind)==kind+'_cancel'
            assert m.owner_hidden is None and m.owner_terminal is None and m.owner_group is None
            assert (m.prepared_tile_hidden,m.prepared_tile_terminal,m.prepared_group_terminal)==payload
            counts[kind+'_cancel']+=1
        counts['hold']+=1
    return counts


def run(output: pathlib.Path):
    contexts = make_contexts()
    pure = check_pure_domain(contexts)
    transitions = run_successor_cases(contexts)
    source = ROOT/'fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv'
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_sha == '54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf'
    result = {
        'schema':'v125-independent-tile-predicate-successor-model-v1',
        'status':'PASS_FINITE_ALGEBRAIC_MODEL',
        'model_type':'independent standard-library two-state finite model',
        'source':{'path':str(source.relative_to(ROOT)),'sha256':source_sha},
        'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        'domain':{'planes':4,'plane_width_bits':2,'tile_width_bits':32,'group_end_width_bits':32,
                  'hidden_plane0_inclusive_ranges':[list(x) for x in HIDDEN_PLANE0],
                  'hidden_planes1_2_3_inclusive_ranges':[list(x) for x in HIDDEN_OTHER_PLANES],
                  'tile_count_plane0':5400,'tile_count_planes1_2_3':1350,
                  'tile_and_group_arithmetic':'explicit modulo-2^32; terminal and group end use exact equality'},
        'counts':{'context_count':len(contexts),'pure_domain':pure,'successor_transitions':transitions},
        'verification_policy':'Owner keys (epoch,plane,tile) and (epoch,plane,tile,group_end) are verification-only and include full plane coherence even though group equality is plane-independent. Epoch is an abstract fresh-parse identity token, not a claim that RTL has or increments an epoch register. Reset/start/abort invalidate owners without clearing modeled predicate payload. GROUP_BEGIN writes group_end and invalidates group-terminal ownership; the completed MODE_BIT tag edge snapshots all three current predicates, or (p,g,g) for hidden-only jump. Mixed-bit and GROUP_TILE increments snapshot successor (p,t+1,g). Key/plane-only successors prepare hidden and tile-terminal predicates and invalidate group ownership. Algebra-only contexts are not claims about RTL reachability.',
        'scope':'Checks equations and successor ownership only. No RTL, four-state/X, synthesis, route, timing, latency, FPS, firmware, or hardware qualification.'
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'contexts':len(contexts),'pure':pure,'transitions':transitions,'script_sha256':result['script_sha256'],'output':str(output.relative_to(ROOT))},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=pathlib.Path,default=ROOT/'experiments/python-gamebub-v125/python-model/tile-model.json')
    args=p.parse_args(); run(args.output)

if __name__=='__main__': main()
