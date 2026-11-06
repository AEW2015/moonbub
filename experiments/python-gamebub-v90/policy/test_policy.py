#!/usr/bin/env python3
"""Plane-layout and negotiated-budget contracts for the resource policy."""
from array import array
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent


def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def main():
    data=load('v90_policy_test_data',AREA/'data.py');model=load('v90_policy_test_model',AREA/'model.py');checks=[]
    words=array('I')
    for plane,count in enumerate(data.PLANE_TILES):
        words.extend([plane*1000+row*100+field for _ in range(count)for row in range(5)for field in range(12)])
    if sys.byteorder!='little':words.byteswap()
    payload=words.tobytes();totals=data.plane_totals(payload)
    for plane,count in enumerate(data.PLANE_TILES):
        for row in range(5):
            actual=totals[plane]['shared']if row==0 else totals[plane]['contexts'][row-1]
            assert actual=={field:count*(plane*1000+row*100+i)for i,field in enumerate(data.FIELDS)}
    checks.append(dict(name='packed_plane_row_field_totals_independent_pattern',status='PASS'))
    ab=bytes([0x35])*len(payload);br=bytes([0xca])*len(payload)
    for mask in range(8):
        mixed=data.blend(ab,br,mask);offset=0
        for axis,count in enumerate(data.PLANE_TILES):
            part=mixed[offset*240:(offset+count)*240];assert part==bytes([0xca if mask&(1<<axis) else 0x35])*len(part)
            offset+=count
        checks.append(dict(name='whole_plane_mask_'+str(mask),status='PASS'))
    for bad in (-1,8,True):
        try:data.blend(ab,br,bad)
        except ValueError:pass
        else:raise AssertionError('invalid mask accepted')
        checks.append(dict(name='invalid_mask_'+str(bad),status='PASS_REJECT'))
    for masks in ((),(1,1),(9,)):
        try:next(data.iter_masks(masks))
        except ValueError:pass
        else:raise AssertionError('invalid mask list accepted')
        checks.append(dict(name='invalid_mask_list_'+str(masks),status='PASS_REJECT'))
    selected=model.select([dict(mask=0,wire_bytes=49152,resource_score_cycles=100),dict(mask=7,wire_bytes=49153,resource_score_cycles=1)])
    assert selected['mask']==0
    checks.append(dict(name='absolute_packet_cap_overrides_score',status='PASS'))
    try:model.select([dict(mask=0,wire_bytes=49153,resource_score_cycles=0)])
    except ValueError:pass
    else:raise AssertionError('missing feasible fallback accepted')
    checks.append(dict(name='no_feasible_candidate_rejected',status='PASS_REJECT'))
    selected=model.select([dict(mask=7,wire_bytes=100,resource_score_cycles=5),dict(mask=1,wire_bytes=100,resource_score_cycles=5)])
    assert selected['mask']==1
    checks.append(dict(name='deterministic_equal_score_equal_byte_tie',status='PASS'))
    output=dict(schema='cu66-v90-policy-contract-tests-v1',status='PASS_PLANE_LAYOUT_AND_ABSOLUTE_CAP_CONTRACTS',checks_count=len(checks),checks=checks,
                source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [Path(__file__).resolve(),AREA/'data.py',AREA/'model.py']},
                scope='Synthetic field/plane and negotiated-cap contracts; no runtime/decode-deadline proof.')
    (AREA/'tests.json').write_text(json.dumps(output,indent=2)+'\n');print(output['status'],len(checks))


if __name__=='__main__':main()
