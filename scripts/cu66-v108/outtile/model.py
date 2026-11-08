#!/usr/bin/env python3
"""Finite independent all-word visibility invariant; no RTL or vendor process."""
import hashlib
import itertools
import json
import random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v108-outtile'
AREA=ROOT/'experiments/python-gamebub-v108/outtile'
MASK=(1<<64)-1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def visible(payload,written):return [x if written>>i&1 else 0 for i,x in enumerate(payload)]
def step(old,payload,written,state,k,group,rst,abort,valid,bad,zero,rng):
    # Arbitrary residual symbols make this independent of the unchanged Q14 math.
    plus=[rng.getrandbits(24) for _ in range(8)]
    minus=[rng.getrandbits(24) for _ in range(8)]
    dc=rng.getrandbits(24)
    literal=old[:]
    clear=rst or abort or (state==0 and valid and (bad or zero))
    if rst or abort:literal=[0]*64
    elif state==0 and valid and (bad or zero):literal=[0]*64
    elif state==8:literal=[dc]*64
    elif state==4 and k==7:
        for lane in range(8):
            literal[(lane%4)*8+group*2+lane//4]=plus[lane]
            literal[(7-lane%4)*8+group*2+lane//4]=minus[lane]
    replacement=set();next_payload=payload[:]
    for word in range(64):
        row,col=divmod(word,8)
        lane=(row if row<4 else 7-row)+4*(col%2)
        if state==8:next_payload[word]=dc;replacement.add(word)
        elif state==4 and k==7 and group==col//2:
            next_payload[word]=(plus if row<4 else minus)[lane];replacement.add(word)
    next_written=written
    if clear:next_written=0
    elif state==8:next_written=MASK
    elif state==4 and k==7:
        for lane in range(8):
            next_written|=1<<((lane%4)*8+group*2+lane//4)
            next_written|=1<<((7-lane%4)*8+group*2+lane//4)
    assert literal==visible(next_payload,next_written)
    for word in range(64):
        if (next_written>>word&1) and not(written>>word&1):assert word in replacement
    if rst or abort:assert next_written==0 and not any(literal)
    return literal,next_payload,next_written,int((rst or abort) and bool(replacement)),len(replacement)
def verify_recipe():
    r=json.loads((SRC/'edit-recipe.json').read_text());p=ROOT/r['original_path'];assert sha(p)==r['original_sha256'];s=p.read_text()
    for e in r['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'],1)
    assert s==(SRC/'cu66_idct8x8.sv').read_text() and sha(SRC/'cu66_idct8x8.sv')==r['candidate_sha256']
    for e in reversed(r['edits']):assert s.count(e['after'])==1;s=s.replace(e['after'],e['before'],1)
    assert s==p.read_text();return r
def main():
    recipe=verify_recipe();runs=[]
    # Full control grid includes all16 encodings, all group/k bits and every kill/clear combination.
    for seed in (108301,108302,108303,108304):
        rng=random.Random(seed);grid=sequence=collisions=writes=poisons=0
        for state,k,group,rst,abort,valid,bad,zero in itertools.product(range(16),range(8),range(4),range(2),range(2),range(2),range(2),range(2)):
            payload=[rng.getrandbits(24) for _ in range(64)];written=rng.getrandbits(64);old=visible(payload,written)
            _,_,_,c,w=step(old,payload,written,state,k,group,rst,abort,valid,bad,zero,rng)
            grid+=1;collisions+=c;writes+=w
        payload=[rng.getrandbits(24) for _ in range(64)];written=0;old=[0]*64
        for _ in range(10000):
            for word in range(64):
                if not(written>>word&1):payload[word]=rng.getrandbits(24);poisons+=1
            assert old==visible(payload,written)
            state=rng.randrange(16);k=rng.randrange(8);group=rng.randrange(4)
            old,payload,written,c,w=step(old,payload,written,state,k,group,rng.randrange(101)==0,rng.randrange(19)==0,rng.randrange(2),rng.randrange(2),rng.randrange(2),rng)
            sequence+=1;collisions+=c;writes+=w
        runs.append(dict(seed=seed,complete_control_grid_edges=grid,arbitrary_sequence_edges=sequence,kill_payload_write_collisions=collisions,private_word_writes=writes,arbitrary_hidden_word_replacements=poisons))
    AREA.mkdir(parents=True,exist_ok=True)
    r=dict(schema='v108-outtile-zero-visibility-finite-model-v1',status='PASS_PREPARATION_MODEL_NOT_RTL',actual_RTL_run=False,formal_tool_run=False,native_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in [SRC/'cu66_idct8x8.sv',SRC/'edit-recipe.json',Path(__file__).resolve(),Path(__file__).parent/'prepare.py']},candidate_sha256=recipe['candidate_sha256'],runs=runs,limits=['Finite arbitrary-word/control invariant model, not actual HDL simulation or formal-tool proof.','All public words compare even invalid/partially updated; masks never expose a previously hidden word without a same-edge complete replacement.','Whole original IDCT/golden/control/hold/reset/malformed qualification and native timing remain separate.'])
    (AREA/'preparation.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(r['status'],sum(x['complete_control_grid_edges']+x['arbitrary_sequence_edges'] for x in runs))
if __name__=='__main__':main()
