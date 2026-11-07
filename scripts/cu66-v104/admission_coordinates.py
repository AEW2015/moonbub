#!/usr/bin/env python3
"""Model bounded admission coordinate recurrence; no actual RTL or reachability proof."""
from dataclasses import dataclass, replace
import hashlib
import json
import subprocess
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'fpga/experiments/cu66-v102-memory/cs88_admission_v91i2a.sv'
AREA=ROOT/'experiments/python-gamebub-v104'
OUTPUT=AREA/'admission-coordinate-model.json'
DOC=ROOT/'docs/cu66-v104/admission-coordinate-model.md'
BASELINE='1d0a702a758787522723ac52ff44a1bf220c39d1'


@dataclass(frozen=True)
class Coordinates:
    plane:int
    tile:int
    column:int
    odd_row:int
    pair_base:int
    cell:int


def limit(plane):
    assert plane in (0,1,2)
    return 5400 if plane==0 else 1350


def oracle(plane,tile):
    # Published function's full unsigned arithmetic, evaluated without narrowing.
    assert 0<=tile<2**32 and 0<=plane<4
    quotient,remainder=divmod(tile,90)
    return (quotient//2)*45+remainder//2 if plane==0 else tile


def canonical(plane,tile):
    assert 0<=tile<=limit(plane)
    if plane==0:
        row,column=divmod(tile,90)
        return Coordinates(plane,tile,column,row%2,(row//2)*45,oracle(plane,tile))
    return Coordinates(plane,tile,0,0,0,tile)


def advance(state,delta):
    assert 0<=delta<=16 and state.tile+delta<=limit(state.plane)
    tile=(state.tile+delta)&0x1fff
    if state.plane==0:
        column_sum=state.column+delta
        assert column_sum<=105  # At most one 90-column wrap for delta<=16.
        crossed=column_sum>=90
        raw_column=column_sum-(90 if crossed else 0)
        raw_base=state.pair_base+(45 if crossed and state.odd_row else 0)
        assert 0<=raw_column<90 and 0<=raw_base<=1350
        column=raw_column&0x7f
        base=raw_base&0x7ff
        parity=(state.odd_row^int(crossed))&1
        cell=(base+(column>>1))&0x7ff
        return Coordinates(state.plane,tile,column,parity,base,cell)
    return Coordinates(state.plane,tile,0,0,0,tile&0x7ff)


def check_state(state):
    expected=canonical(state.plane,state.tile)
    assert state==expected,(state,expected)
    assert state.cell==oracle(state.plane,state.tile)
    assert state.column<2**7 and state.odd_row<2 and state.pair_base<2**11
    assert state.cell<2**11 and state.tile<2**13
    if state.tile<limit(state.plane):assert state.cell<1350
    else:assert state.cell==1350  # An end sentinel is never a residual-cell mark.


def hidden(plane,tile):
    if not 0<=tile<limit(plane):return False
    if plane!=0:
        y,x=divmod(tile,45)
        return y==23 and 11<=x<30
    y,x=divmod(tile,90)
    return (3<=x<22 and (7<=y<9 or 11<=y<13)) or (21<=x<61 and 45<=y<48) or (21<=x<51 and 49<=y<51)


@dataclass(frozen=True)
class OwnerState:
    coordinate:Coordinates
    valid:bool
    owner:int


def invalidate(state):
    # Matches the planning obligation: reset/start/abort invalidate derived
    # ownership; admission's existing tile/plane are not assumed to reset.
    return replace(state,valid=False)


def header_entry(owner):
    return OwnerState(canonical(0,0),True,owner)


def mark_allowed(state,owner):
    return state.valid and state.owner==owner and state.coordinate.tile<limit(state.coordinate.plane)


def run():
    assert SOURCE.read_bytes()==subprocess.check_output(['git','show',BASELINE+':'+str(SOURCE.relative_to(ROOT))],cwd=ROOT), 'published admission source changed'
    began=time.monotonic();input_hash=hashlib.sha256();result_hash=hashlib.sha256()
    counts=dict(bounded_transition_cases=0,holds=0,row_wraps=0,end_sentinel_results=0,
                sentinel_hold_cases=0,canonical_group_end_cases=0,hidden_boundary_crossings=0,
                trajectory_steps=0,trajectory_plane_transitions=0,owner_event_sequences=0,
                owner_assertions=0,rejected_sentinel_marks=0)
    maxima=dict(column_sum=0,column=0,pair_base=0,cell=0,tile=0)
    per_plane={str(p):0 for p in (0,1,2)}
    for plane in (0,1,2):
        end=limit(plane)
        for tile in range(end+1):
            state=canonical(plane,tile);check_state(state)
            for delta in range(min(16,end-tile)+1):
                assert time.monotonic()-began<20,'finite Python watchdog'
                updated=advance(state,delta);check_state(updated)
                counts['bounded_transition_cases']+=1;per_plane[str(plane)]+=1
                counts['holds']+=delta==0
                counts['row_wraps']+=plane==0 and state.column+delta>=90
                counts['end_sentinel_results']+=updated.tile==end
                counts['sentinel_hold_cases']+=tile==end
                counts['canonical_group_end_cases']+=delta==min(16,end-tile)
                for offset in range(1,delta+1):
                    counts['hidden_boundary_crossings']+=hidden(plane,tile+offset-1)!=hidden(plane,tile+offset)
                maxima['column_sum']=max(maxima['column_sum'],state.column+delta if plane==0 else 0)
                for key in ['column','pair_base','cell','tile']:maxima[key]=max(maxima[key],getattr(updated,key))
                input_hash.update(bytes((plane,delta))+tile.to_bytes(2,'big'))
                result_hash.update(bytes((updated.column,updated.odd_row))+updated.pair_base.to_bytes(2,'big')+updated.cell.to_bytes(2,'big')+updated.tile.to_bytes(2,'big'))
    # Feed recurrence output into the next step, rather than reinitializing
    # from the oracle, across held and variable-size group trajectories.
    for pattern in [(1,), (16,), (0,1,15,0,16,2,7,3)]:
        state=canonical(0,0);iteration=0
        while True:
            end=limit(state.plane)
            if state.tile==end:
                assert not mark_allowed(OwnerState(state,True,42),42);counts['rejected_sentinel_marks']+=1
                if state.plane==2:break
                state=canonical(state.plane+1,0);counts['trajectory_plane_transitions']+=1
            delta=min(pattern[iteration%len(pattern)],limit(state.plane)-state.tile)
            state=advance(state,delta);check_state(state)
            counts['trajectory_steps']+=1;iteration+=1
            assert iteration<20000,'trajectory watchdog'
    # These are hypothetical owner-validity rules, not execution of the
    # admission FSM. Retain stale coordinates and queued old-owner marks on
    # invalidation, then demonstrate that explicit validity/owner gating drops
    # them until a qualified new header establishes fresh geometry.
    for plane in (0,1,2):
        for tile in [0,1,16,89,90,limit(plane)-1,limit(plane)]:
            if tile>limit(plane):continue
            for event in ['reset','start','abort','failed_header']:
                old=OwnerState(canonical(plane,tile),True,17)
                if tile==limit(plane):
                    assert not mark_allowed(old,17);counts['owner_assertions']+=1
                invalid=invalidate(old)
                assert invalid.coordinate==old.coordinate
                assert not mark_allowed(invalid,17)
                assert not mark_allowed(invalid,18)
                fresh=header_entry(18)
                assert not mark_allowed(fresh,17)
                assert mark_allowed(fresh,18)
                assert fresh.coordinate==canonical(0,0)
                counts['owner_assertions']+=6;counts['owner_event_sequences']+=1
                input_hash.update(f'{plane}/{tile}/{event}'.encode())
                result_hash.update(b'old_invalid/new_header/stale_drop/new_allow')
    return dict(schema='v104-admission-coordinate-model-v1',status='PASS',baseline_revision=BASELINE,
        source=dict(path=str(SOURCE.relative_to(ROOT)),sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest()),
        script=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
        input_sha256=input_hash.hexdigest(),result_sha256=result_hash.hexdigest(),counts=counts,
        transitions_per_plane=per_plane,observed_maxima=maxima,
        finite_widths=dict(tile=13,Y_column_and_sum=7,Y_row_parity=1,Y_pair_base=11,cell=11,delta=5),
        domain='Planes0–2; Y tile0..5400 and chroma0..1350 include end-onlysentinels; delta0..16 not past plane end.',
        limits=['Conditional coordinate arithmetic model only; current admission tile state/function contract remains32 bits.',
                'No actual admission RTL, protocol reachability, invalid-packet equivalence or machine-checked formal proof.',
                'Owner invalidation/header-entry/stale-drop are proposed model rules, not verified existing hardware behavior.',
                'No native mapping/timing, full decoder/HUD/C2, hardware FPS or validated complete latency claim.'],
        watchdog_seconds=20)


def main():
    result=run();OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    c=result['counts'];m=result['observed_maxima']
    text=f'''# V104 admission-coordinate recurrence model

**PASS: Python coordinate arithmetic only.** This model prepares an isolated
future admission recurrence experiment; it changes no admission RTL, measured
V104 source, source width, parser state or native timing contract.

The published admission `cell_index` accepts a full unsigned 32-bit tile. The
model exhausts a **conditional bounded domain**: planes 0–2, valid Y/chroma tiles
plus their end sentinels, and every delta 0–16 that does not pass plane end.
It compares a finite-width cached-coordinate update with the original full-width
integer quotient/remainder formula. This is not a proof that arbitrary real
admission histories stay in that bounded domain.

| Modeled evidence | Count |
| --- | ---: |
| One-step tile/delta transitions | {c['bounded_transition_cases']:,} |
| Holds | {c['holds']:,} |
| Y row crossings | {c['row_wraps']:,} |
| End-sentinel results | {c['end_sentinel_results']:,} |
| Chained trajectory steps | {c['trajectory_steps']:,} |
| Proposed owner-event sequences | {c['owner_event_sequences']:,} |
| Owner-rule assertions | {c['owner_assertions']:,} |

For Y, cache column `tile%90`, row parity and `45*floor(tile/180)`. Adding a
bounded delta crosses at most one 90-column row: wrap column if needed, toggle
parity, and increment pair base by 45 only when the old row was odd. Cell is
pair base plus half-column. Chroma cell is tile. Observed maxima are column sum
{m['column_sum']}, column {m['column']}, pair base {m['pair_base']}, cell {m['cell']}
and tile {m['tile']}; all declared 7/1/11/13-bit arithmetic bounds hold.

The tile5400 Y and tile1350 chroma sentinels have cell1350. They are **not**
residual cells and must never mark `active_cell`. The model checks sentinel
holds/mark rejection, all group-size deltas, every row/plane end, hidden-region
crossings and multi-step held/variable-group trajectories. The sentinel-to-next-
plane transition resets geometry; it is distinct from advancing past the end.

The owner model deliberately retains stale tile/plane coordinates on reset,
start, abort or failed entry, but invalidates their ownership. A qualified new
header establishes plane0/tile0 under a fresh opaque owner; queued old-owner
marks remain rejected. These are proposed safety rules, **not actual admission
FSM execution or a proof of its reachability**. Future RTL must establish the
entry invariant, cover every real assignment/group jump and error path, enforce
write drain before active-cell scan, and preserve epoch/reset/abort priorities.
Current 32-bit admission semantics cannot be narrowed merely from this model.

```sh
python3 scripts/cu66-v104/admission_coordinates.py
```

The receipt stores source/script/input/result hashes and a finite20-second
watchdog. It writes no large expanded trace. No RTL simulation, formal proof,
placed/routed improvement, full decoder integration, hardware30fps or complete
validated under10ms decoding follows from this conditional arithmetic result.
'''
    DOC.write_text(text)
    print('V104_ADMISSION_COORDINATE_MODEL',result['status'],c['bounded_transition_cases'],'transitions')


if __name__=='__main__':
    main()
