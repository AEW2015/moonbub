#!/usr/bin/env python3
"""Independent finite two-state owner-equation comparison; not RTL proof."""
from __future__ import annotations
import hashlib, json, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PARENT_INDEX=ROOT/'experiments/python-gamebub-v123/integration/results.json'
PRODUCER_ALIAS='fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv'
CANDIDATE=ROOT/'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen_producer_pin():
    index=json.loads(PARENT_INDEX.read_text())
    meta=index['source_origins'][PRODUCER_ALIAS]
    current=ROOT/meta['path']
    if sha(current)!=meta['sha256']: raise ValueError('V123 frozen producer drift')
    return {'functional_alias':PRODUCER_ALIAS,'frozen_path':meta['path'],'sha256':meta['sha256'],
            'candidate_path':str(CANDIDATE.relative_to(ROOT)) if CANDIDATE.exists() else None,
            'candidate_sha256':sha(CANDIDATE) if CANDIDATE.exists() else None}


def scalar_owner(tile_mode, selector, active_epoch, expected_block, banks, fallback_epoch, fallback_block):
    if not tile_mode:
        return ('fallback',None) if (fallback_epoch==active_epoch and fallback_block==expected_block) else (None,None)
    epoch,block=banks[selector]
    return ('bank',selector) if epoch==active_epoch and block==expected_block else (None,None)


def spatial_owner(tile_mode, selector, active_epoch, expected_block, banks, fallback_epoch, fallback_block):
    if not tile_mode:
        return ('fallback',None) if (fallback_epoch==active_epoch and fallback_block==expected_block) else (None,None)
    matches=tuple((epoch==active_epoch and block==expected_block) for epoch,block in banks)
    return ('bank',selector) if matches[selector] else (None,None)


def gates(tile_mode, selector, owner, bank_ready, child_valid, state_dispatch, downstream_ready,
          reset, abort, refill_error, child_error, accepted_start):
    # Identity ownership is deliberately independent of ready/valid and bank availability.
    selected_ready=bank_ready[selector] if tile_mode else True
    ready=state_dispatch and downstream_ready and owner and not reset and not abort
    valid=state_dispatch and child_valid and owner and not reset and not abort
    # Top-level priority from the selected wrapper: reset/abort, accepted start,
    # refill error, child error, then normal DISPATCH bad-owner handling.
    if reset or abort: priority='reset_abort'
    elif accepted_start: priority='accepted_start'
    elif refill_error: priority='refill_error_67'
    elif child_error: priority='child_error'
    else: priority='normal_dispatch'
    error67=(priority=='refill_error_67' or
             (priority=='normal_dispatch' and state_dispatch and child_valid and not owner))
    return ready,valid,error67,priority,selected_ready


def check_pair(case):
    a=scalar_owner(**case); b=spatial_owner(**case)
    if a!=b: raise AssertionError({'case':case,'scalar':a,'spatial':b})
    return a


def run_model():
    records=0; owner_matches=0; mismatch_cases=0; explicit={'duplicate_banks':0,'selected_mismatch_opposite_match':0,'selected_match_opposite_poison':0}
    boundaries=[0,1,2,0x7ffffffe,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    block_bounds=[0,1,2,0xfffd,0xfffe,0xffff]
    # Explicit boundary cross-product: both selectors, tile/fallback mode,
    # selected and opposite-bank exact/mismatch/duplicate ownership.
    for selector in (0,1):
      for tile_mode in (False,True):
       for epoch in boundaries:
        for block in block_bounds:
         for variant in range(7):
          e_other=epoch if variant in (0,1) else ((epoch+1)&0xffffffff)
          b_other=block if variant in (0,2) else ((block+1)&0xffff)
          selected=(epoch,block) if variant in (0,1,2,3) else (e_other,b_other)
          opposite=(e_other,b_other) if variant==4 else ((epoch,block) if variant in (5,6) else (epoch^0x80000000,block^0xffff))
          if variant==6: selected=(epoch,block); opposite=(epoch,block)
          banks=[None,None]; banks[selector]=selected; banks[1-selector]=opposite
          explicit['duplicate_banks']+=int(variant==6)
          explicit['selected_mismatch_opposite_match']+=int(variant==5)
          explicit['selected_match_opposite_poison']+=int(variant==0)
          case=dict(tile_mode=tile_mode,selector=selector,active_epoch=epoch,expected_block=block,
                    banks=tuple(banks),fallback_epoch=epoch,fallback_block=block)
          result=check_pair(case); records+=1; owner_matches+=int(result[0] is not None)
          mismatch_cases+=int(result[0] is None)
    # High-bit/equality-adjacent deterministic random cases across full widths.
    rng=random.Random(12420261109)
    random_count=100000
    for _ in range(random_count):
        epoch=rng.getrandbits(32); block=rng.getrandbits(16); selector=rng.randrange(2)
        banks=[]
        for b in range(2):
            mode=rng.randrange(6)
            e=epoch if mode in (0,1,2) else (epoch ^ (1 << rng.randrange(32)) if mode==3 else rng.getrandbits(32))
            bl=block if mode in (0,1,3) else ((block + (1 if mode==4 else 0xffff))&0xffff) if mode==4 else rng.getrandbits(16)
            banks.append((e,bl))
        case=dict(tile_mode=bool(rng.getrandbits(1)),selector=selector,active_epoch=epoch,
                  expected_block=block,banks=tuple(banks),fallback_epoch=epoch,
                  fallback_block=(block if rng.randrange(2) else (block+1)&0xffff))
        result=check_pair(case); records+=1; owner_matches+=int(result[0] is not None)
        mismatch_cases+=int(result[0] is None)
    # Gates test all boolean combinations for owner match and mismatch.
    gate_contexts=0
    for tile_mode in (False,True):
     for selector in (0,1):
      for owner_identity in (False,True):
       for downstream_ready in (False,True):
        for child_valid in (False,True):
         for dispatch in (False,True):
          for reset in (False,True):
           for abort in (False,True):
            for refill_error in (False,True):
             for child_error in (False,True):
              for accepted_start in (False,True):
               banks=((9,12),(9,12)) if owner_identity else ((9,13),(9,13))
               fallback_block=12 if owner_identity else 13
               ident=spatial_owner(tile_mode,selector,9,12,banks,9,fallback_block)
               out=gates(tile_mode,selector,ident[0] is not None,(False,False),child_valid,dispatch,downstream_ready,
                         reset,abort,refill_error,child_error,accepted_start)
               expected_priority=('reset_abort' if reset or abort else 'accepted_start' if accepted_start else
                                  'refill_error_67' if refill_error else 'child_error' if child_error else 'normal_dispatch')
               assert out[3]==expected_priority
               assert out[2]==(expected_priority=='refill_error_67' or
                   (expected_priority=='normal_dispatch' and dispatch and child_valid and ident[0] is None))
               assert out[0]==(dispatch and downstream_ready and ident[0] is not None and not reset and not abort)
               assert out[1]==(dispatch and child_valid and ident[0] is not None and not reset and not abort)
               gate_contexts+=1
    # Child-valid and bank-ready do not participate in identity: poison each independently.
    context_independence=0
    for br in ((False,False),(False,True),(True,False),(True,True)):
      for cv in (False,True):
       for selector in (0,1):
        banks=((0x87654321,0xfffe),(0x87654321,0xfffe))
        a=scalar_owner(True,selector,0x87654321,0xfffe,banks,0,0)
        # Exercise all readiness/valid settings in gates without changing owner identity.
        g=gates(True,selector,a[0] is not None,br,cv,True,True,False,False,False,False,False)
        assert a==('bank',selector) and g[2] is False
        context_independence+=1
    return {'identity_cases':records,'random_seed':12420261109,'random_cases':random_count,
            'owner_matches':owner_matches,'no_owner_cases':mismatch_cases,'explicit_patterns':explicit,'gate_contexts':gate_contexts,
            'ready_child_valid_bankready_independence_contexts':context_independence,
            'full32_epoch_width':32,'full16_block_width':16}


def main():
    pin=frozen_producer_pin(); counts=run_model()
    report={'schema':'v124-owner-equation-independent-model-v1','classification':'FINITE_TWO_STATE_ALGEBRAIC_MODEL_NOT_RTL_PROOF',
      'model_source_sha256':sha(Path(__file__).resolve()),'v123_producer':pin,
      'equations':{'selected_scalar':'tile_mode ? ((bank_epoch[selector]==active_epoch) && (bank_block[selector]==expected_block)) : ((fallback_epoch==active_epoch) && (fallback_block==expected_block))',
       'perbank_spatial':'tile_mode ? (((bank_epoch[0]==active_epoch)&&(bank_block[0]==expected_block)) OR (same for bank 1), selected strictly by selector) : the unchanged fallback scalar equation',
       'ready_valid_error67':'exact same computed owner_match enters ready/valid/error67 gates; reset/abort, accepted-start, refill-error, child-error precedence preserved'},
      'counts':counts,'scope':{'RTL_equivalence':False,'formal_proof':False,'timing':False,'throughput':False,'FPS':False},
      'coverage_notes':['both bank selectors','tile mode and non-tile fallback','full 32-bit epoch equality and high-bit mismatches','full 16-bit block equality/boundaries/wrap adjacency','opposite-bank poison, duplicate tags and mismatches','bank_ready and child_valid do not affect owner identity','ready/valid/error-67 boolean gate contexts preserve listed priority']}
    out=ROOT/'experiments/python-gamebub-v124/python-model/owner-model.json'
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'output':str(out.relative_to(ROOT)),**counts,'producer':pin},indent=2))
if __name__=='__main__': main()
