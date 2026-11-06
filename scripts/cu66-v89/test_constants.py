#!/usr/bin/env python3
"""Fixed-profile sentinel, invalid descriptor and lease-publication contracts."""
import hashlib,importlib.util,json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v89/constants'


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def main():
    module=load('v89_constants_test_layout',AREA/'layout.py');trace=load('v89_constants_test_trace',AREA/'trace.py')
    checks=[]
    def reject(name,call):
        try:call()
        except (ValueError,AssertionError):checks.append(dict(name=name,status='PASS_REJECT'))
        else:raise AssertionError(name)
    state=module.ConstantSlots([0,1]);first=[bytes([7])*64,module.CONSTANT]
    reject('unpublished_constant_map_cannot_be_presented',state.present)
    reject('COPY_without_reference',lambda:state.begin(first,[1,0]))
    state.begin(first,[0,0]);assert state.candidate==[0,3]
    assert state.written==[(0,0)] and state.physical[0][1] is None
    state.commit(first);state.present()
    checks.append(dict(name='hidden_constant_has_no_pixel_store',status='PASS'))
    reject('visible_descriptor_3_is_INVALID',lambda:state.image([3,3]))
    reject('hidden_descriptor_must_be_CONST',lambda:state.image([0,0]))
    before=state.image(state.accepted)
    reject('hidden_wrong_pixels_rejected',lambda:state.begin([bytes([8])*64,bytes([9])*64],[0,0]))
    state.abort();assert state.image(state.accepted)==before and state.image(state.presented)==before
    reject('hidden_COPY_not_a_constant_operation',lambda:state.begin(first,[0,1]))
    state.abort();assert state.image(state.accepted)==before
    state.begin(first,[0,0],stop_after=1)
    reject('partial_candidate_not_published',lambda:state.commit(first))
    state.abort();assert state.image(state.presented)==before
    state.begin([bytes([8])*64,module.CONSTANT],[0,0])
    reject('invalid_content_aborts_only_provisional_data',lambda:state.commit(first))
    assert state.candidate is None and state.image(state.accepted)==before and state.image(state.presented)==before
    # Packed word value3 is valid at a fixed hidden position and invalid at a
    # visible position. The INVALID interpretation is not silently discarded.
    banks=[bytearray(b'\xff'*trace.MAP_STRIDE) for _ in range(3)]
    bad=[dict(kind='descriptor_candidate',direction='write',address=trace.MAP_BASE,BL8=0,tile=0,bit_offset=0,map=0,value=3)]
    reject('packed_visible_3_rejected',lambda:trace.validate_descriptors(bad,banks,[0,1]))
    good=[dict(kind='descriptor_candidate',direction='write',address=trace.MAP_BASE,BL8=0,tile=1,bit_offset=2,map=0,value=3)]
    trace.validate_descriptors(good,banks,[0,1]);checks.append(dict(name='packed_hidden_3_retains_constant_semantics',status='PASS'))
    reject('constant_has_no_physical_slot_address',lambda:trace.tile_address(3,1))
    # Immutable plaintext oracle; keep scanout old while accepted tiles advance.
    for seed in range(8):
        rng=random.Random(seed);s=module.ConstantSlots([0,1,0,1]);accepted=None;display=None
        for i in range(128):
            values=[];copies=[]
            for t in range(4):
                if t%2:values.append(module.CONSTANT);copies.append(0)
                elif accepted is not None and rng.random()<.5:values.append(accepted[t]);copies.append(1)
                else:values.append(bytes([rng.randrange(256)])*64);copies.append(0)
            if i%13==0:
                s.begin(values,copies,stop_after=rng.randrange(5));s.abort()
                assert s.image(s.accepted)==accepted and s.image(s.presented)==display
            s.begin(values,copies);assert s.image(s.candidate)==values
            assert s.image(s.accepted)==accepted and s.image(s.presented)==display
            s.commit(values);accepted=list(values)
            if i==0 or rng.random()<.2:s.present();display=list(accepted)
            assert s.image(s.accepted)==accepted and s.image(s.presented)==display
            assert all(s.physical[slot][t] is None for slot in range(3) for t in (1,3))
        checks.append(dict(name='immutable_lease_and_constant_oracle',seed=seed,accepted_updates=128,status='PASS'))
    sources=[Path(__file__).resolve(),AREA/'layout.py',AREA/'trace.py']
    report=dict(schema='cu66-v89-constant-contract-tests-v1',status='PASS_PROFILE_SENTINEL_AND_LEASE_CONTRACT',checks=checks,checks_count=len(checks),
                symbolic_updates=1024,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
                scope='Sequential fixed-profile state and packed descriptor contracts; no async hardware drain or generator timing proof.')
    (AREA/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(checks))


if __name__=='__main__':main()
