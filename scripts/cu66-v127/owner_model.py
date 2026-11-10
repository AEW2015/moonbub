#!/usr/bin/env python3
"""Finite algebra model for the V127 selected-owner lane proposal (stdlib only)."""
from __future__ import annotations
import hashlib, itertools, json, pathlib, random, re
ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v126-producer/cs88_coefficients_v91k.sv'
SCRATCH=ROOT/'fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv'
OUT=ROOT/'experiments/python-gamebub-v127/python-model/owner-model.json'
MASK32=(1<<32)-1; MASK16=(1<<16)-1

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def old_owner(tilemode, emitbank, b0e,b0b,b1e,b1b,raw_e,raw_b,cur_e,expected_b):
    e,b=(b1e,b1b) if tilemode and emitbank else (b0e,b0b) if tilemode else (raw_e,raw_b)
    return e==cur_e and b==expected_b

def lane_owner(e,b,cur_e,expected_b): return e==cur_e and b==expected_b

def new_owner(tilemode,emitbank,b0e,b0b,b1e,b1b,raw_e,raw_b,cur_e,expected_b):
    lane0=lane_owner(b0e,b0b,cur_e,expected_b)
    lane1=lane_owner(b1e,b1b,cur_e,expected_b)
    raw=lane_owner(raw_e,raw_b,cur_e,expected_b)
    return (lane1 if emitbank else lane0) if tilemode else raw

def assert_case(args, counts, label):
    a=old_owner(*args); b=new_owner(*args)
    counts['cases']+=1
    if a != b: raise AssertionError(f'{label}: old={a} new={b} args={args}')

def main():
    src=SRC.read_text(); scratch=SCRATCH.read_text()
    # Bind the model to the actual frozen expressions and selected scratch mux.
    assert 'assign child_owner_match=dbg_tile_mode ? tile_owner_match[dbg_emit_bank] :' in src
    assert '(child_out_epoch==current_child_epoch && out_block==expected_block);' in src
    assert 'dense_epoch=tile_mode ? bank_epoch[emit_bank] : active_epoch;' in scratch
    assert 'dense_block=tile_mode ? bank_block[emit_bank] : output_block;' in scratch
    counts={'cases':0,'truth_table_cases':0,'boundary_cases':0,'random_cases':0,'context_cases':0}
    # Exhaustive Boolean lane/mode/selector combinations. raw_mode, ready, valid
    # are surrounding context only and do not redefine ownership.
    for tilemode,emitbank,l0,l1,lr,rawmode,ready,valid in itertools.product(range(2),repeat=8):
        cur_e,cur_b=0x81234567,0x91a7
        # Lane bits encode each compare result. Make equal tags for true lanes,
        # and change one full-width tag bit for false lanes.
        tags=[]
        for lane,want in enumerate((l0,l1,lr)):
            tags.append((cur_e if want else cur_e^(1<<(lane+3)),cur_b))
        (e0,b0),(e1,b1),(er,br)=tags
        args=(tilemode,emitbank,e0,b0,e1,b1,er,br,cur_e,cur_b)
        assert_case(args,counts,'Boolean lane truth table')
        counts['truth_table_cases']+=1; counts['context_cases']+=1
    # Explicitly prove ready/valid/raw mode are not part of owner equality;
    # exercise selected match/mismatch for each context combination.
    for ctx in itertools.product(range(2),repeat=4):
        rawmode,ready,valid,tilemode=ctx
        for bank in range(2):
            cur_e,cur_b=0xfedcba98,0xfffe
            b0=(cur_e,cur_b);b1=(cur_e^0x10000,cur_b^1);raw=(cur_e,cur_b)
            args=(tilemode,bank,*b0,*b1,*raw,cur_e,cur_b)
            assert_case(args,counts,'context orthogonality')
            counts['context_cases']+=1
    vals32=[0,1,2,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    vals16=[0,1,2,0x7fff,0x8000,0xfffe,0xffff]
    # Full-width cross product of boundaries: equality, high-bit mismatch,
    # equality at max/wrap values, duplicate/opposite bank, foreign coherent raw.
    for ce,eb in itertools.product(vals32,vals16):
      for pe,pb in itertools.product(vals32,vals16):
       for rmode,bank,tilemode in itertools.product(range(2),repeat=3):
        b0=(ce,eb); b1=(pe,pb); raw=(pe,pb)
        args=(tilemode,bank,*b0,*b1,*raw,ce,eb)
        assert_case(args,counts,'full-width boundary')
        counts['boundary_cases']+=1
    # Seeded complete-width independent vectors; include malformed ownership
    # relationships without assuming readiness implies owner match.
    rng=random.Random(0x1270A11)
    for _ in range(50000):
        cur_e=rng.getrandbits(32); cur_b=rng.getrandbits(16)
        tags=[]
        for __ in range(3):
            if rng.randrange(4)==0: tags.append((cur_e,cur_b))
            else: tags.append((rng.getrandbits(32),rng.getrandbits(16)))
        (e0,b0),(e1,b1),(er,br)=tags
        args=(rng.randrange(2),rng.randrange(2),e0,b0,e1,b1,er,br,cur_e,cur_b)
        assert_case(args,counts,'deterministic random')
        counts['random_cases']+=1
    # Directed mismatch cases: selected bank vs opposite bank, and parent
    # expected identity differs from a coherent selected child (ready/valid set).
    directed=[]
    cur_e,cur_b=0x12345678,0x4567
    directed.append((1,0,cur_e,cur_b,cur_e^0x80000000,cur_b^1,cur_e^1,cur_b^2,cur_e,cur_b))
    directed.append((1,1,cur_e^1,cur_b^2,cur_e,cur_b,cur_e^1,cur_b^2,cur_e,cur_b))
    directed.append((0,1,cur_e^1,cur_b^2,cur_e,cur_b,cur_e,cur_b,cur_e^1,cur_b))
    for x in directed: assert_case(x,counts,'opposite bank / foreign parent')
    counts['directed_owner_cases']=len(directed)
    output={'schema':'v127-owner-selection-algebra-v1','status':'PASS','model_scope':'Pure Boolean algebra and finite tag-value checks; no sequential RTL execution, formal equivalence, synthesis, timing, FPS, or hardware claim. ready/valid/rawmode are enumerated as context and do not imply ownership.','source_bindings':{'producer_path':str(SRC.relative_to(ROOT)),'producer_sha256':sha(SRC),'scratch_path':str(SCRATCH.relative_to(ROOT)),'scratch_sha256':sha(SCRATCH)},'script_sha256':sha(pathlib.Path(__file__)),'reference':'V126 selected expression: tile_mode ? tile_owner_match[emit_bank] : (child_out_epoch==current_child_epoch && out_block==expected_block). Proposed equivalent computes three full32/full16 comparisons then selects the tile bank or raw active_epoch/output_block lane.','counts':counts,'limitations':['All values are full-width; finite boundary and seeded random sampling do not exhaust 2^32×2^16 tag pairs.','No production RTL or source is changed.','No claim that the three comparison lanes remain physically separate after synthesis or improve routed timing.','Readiness and child validity are orthogonal context flags, not ownership evidence.']}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n'); print(json.dumps({'status':'PASS','counts':counts,'script_sha256':output['script_sha256'],'producer_sha256':output['source_bindings']['producer_sha256'],'scratch_sha256':output['source_bindings']['scratch_sha256'],'output':str(OUT.relative_to(ROOT))},indent=2))
if __name__=='__main__': main()
