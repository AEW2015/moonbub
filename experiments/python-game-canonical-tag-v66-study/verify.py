#!/usr/bin/env python3
"""Independent canonical-only wire/state/hash-demand proof.

CS66 preserves old tag bytes; CU66 preserves exact pixels with a distinct,
validated uint8 representation. Neither SHA128 profile authenticates traffic or
provides ECC. Hash-round counts are hypothetical serial-core arithmetic.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,math,statistics,struct,sys,zlib
from contextlib import contextmanager
from unittest.mock import patch
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v);return v
oldproof=module('canonical66_frozen43_independent',HERE.parent/'python-game-direct-rx-v43-study/verify.py')
f,m=oldproof.f,oldproof.m;OUTER=f.HEADER;INNER=struct.Struct('<4sBBIIIHHBB16sIIIII')
FOLDERS=(('python-game-binary-v38-study',24),('python-game-binary-full-v39-study',96),('python-game-binary-qual-v40-study',457))
def bound(name,path,helper):
    prior=sys.modules.get('helpers')
    try:sys.modules['helpers']=helper;return module(name,path)
    finally:
        if prior is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=prior
helper=module('canonical66_subject_helpers',HERE/'helpers.py')
subject=bound('canonical66_subject_receiver',HERE/'receiver.py',helper)
raw,digest=oldproof.raw,oldproof.digest
RECTS=f.f.n.RECTS
PROFILES={name:hashlib.sha256(prefix+json.dumps(RECTS,separators=(',',':')).encode()).digest()[:16]for name,prefix in(
    ('CS66',b'CS66:canonical-only-cached-ref-sha128-i16-v1:'),('CU66',b'CU66:canonical-only-cached-ref-sha128-u8-v1:'))}

def tag(planes,profile):
    shapes=((480,720),(240,360),(240,360))
    if profile not in PROFILES or type(planes)not in(tuple,list)or len(planes)!=3:raise ValueError('fixed profile/plane domain')
    for p,shape in zip(planes,shapes,strict=True):
        if not isinstance(p,np.ndarray)or p.shape!=shape or p.dtype.kind not in('i','u')or np.any(p<0)or np.any(p>255):raise ValueError('canonical integer samples0..255 before cast')
    h=hashlib.sha256(struct.pack('<HH',720,480))
    for p in planes:h.update(p.astype('<i2'if profile=='CS66'else'u1').tobytes())
    return h.digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def expected_wire(old,profile,reference,normalized):
    outer=list(OUTER.unpack_from(old));nb=outer[11];inside=old[OUTER.size:OUTER.size+nb];fields=list(m.HEADER.unpack_from(inside));oldtag=fields[11]
    assert fields[0]==b'GS38'and outer[0]==b'CS38'
    del fields[11];fields[0]=b'GS66'if profile=='CS66'else b'GU66'
    rt=bytes(16)if reference is None else tag(reference,profile);ot=tag(normalized,profile)
    if profile=='CS66':assert rt==outer[9]and ot==outer[10]
    fields[10]=rt;newinner=seal(INNER.pack(*fields)+inside[m.HEADER.size:-4]);outer[0]=profile.encode();outer[8]=PROFILES[profile];outer[9]=rt;outer[10]=ot;outer[11]=len(newinner)
    result=seal(OUTER.pack(*outer)+newinner+old[OUTER.size+nb:-4]);assert len(result)==len(old)-16
    return result,oldtag

def equal_meta(actual,expected,profile):
    for key in('key','frame_id','reference_id','block_size'):assert actual[key]==expected[key],key
    for key in('qmap','vectors'):np.testing.assert_array_equal(actual[key],expected[key])
    oldproof.equal_planes(actual['coefficients'],expected['coefficients']);assert actual['hud']==expected['hud']
    assert actual['profile']==profile and 'base_tag'not in actual

@contextmanager
def counted():
    actual=subject.canonical_tag;legacy=subject.h.m.C.reference_tag;calls=[];oldcalls=[]
    def canonical(planes,profile):calls.append((planes,profile));return actual(planes,profile)
    def old(planes):oldcalls.append(planes);return legacy(planes)
    with patch.object(subject,'canonical_tag',canonical),patch.object(subject.h.m.C,'reference_tag',old):yield calls,oldcalls

def snapshot(rx):
    return dict(ref=None if rx.ref is None else tuple(p.copy()for p in rx.ref),rid=rx.rid,last=rx.last,
        hud=None if rx.hud is None else tuple(dict(rect=p['rect'],words=p['words'].copy())for p in rx.hud),cached_tag=rx.cached_tag,profile=rx.profile)
def unchanged(rx,state):
    assert(rx.rid,rx.last,rx.cached_tag,rx.profile)==(state['rid'],state['last'],state['cached_tag'],state['profile'])
    if state['ref']is None:assert rx.ref is None
    else:oldproof.equal_planes(rx.ref,state['ref'])
    if state['hud']is None:assert rx.hud is None
    else:oldproof.equal_hud(rx.hud,state['hud'])
def reject(rx,packet,calls=None):
    state=snapshot(rx)
    with counted()as(actual,legacy):
        try:rx.receive(packet)
        except ValueError:pass
        else:raise AssertionError('bad packet accepted')
    unchanged(rx,state)
    if calls is not None:assert len(actual)==calls
    return len(actual),len(legacy)

def rebuild(packet,*,outer_changes=None,inner_changes=None,hud=None):
    outer=list(OUTER.unpack_from(packet));inside=packet[OUTER.size:OUTER.size+outer[11]];fields=list(INNER.unpack_from(inside))
    if inner_changes:
        for index,value in inner_changes.items():fields[index]=value
    newinner=seal(INNER.pack(*fields)+inside[INNER.size:-4]);overlay=packet[OUTER.size+outer[11]:-4]if hud is None else hud
    outer[11]=len(newinner);outer[12]=len(overlay)
    if outer_changes:
        for index,value in outer_changes.items():outer[index]=value
    return seal(OUTER.pack(*outer)+newinner+overlay)

def corrupt_late_HUD(packet):
    outer=OUTER.unpack_from(packet);hud=packet[OUTER.size+outer[11]:-4];proto=f.f.hud.p
    fields=list(proto.HUD.unpack_from(hud));fields[9]=b'H'*16
    wrong=seal(proto.HUD.pack(*fields)+hud[proto.HUD.size:-4]);f.f.hud._meta(wrong)
    return rebuild(packet,hud=wrong)

def demand(sample_bytes,calls):
    size=4+518400*sample_bytes;blocks=(size+9+63)//64
    return dict(sample_bytes=sample_bytes,calls=calls,preimage_bytes_per_tag=size,padded_SHA256_blocks_per_tag=blocks,
        rounds_per_block=64,assumed_rounds_per_cycle=1,total_round_cycles=blocks*64*calls,assumed_clock_hz=100000000,
        assumed_serial_ms=blocks*64*calls/100000,physical_timing_or_RTL_fit_proven=False)

PATHS=('CS38','CS66','CU66')
def paired_timings(row):
    assert set(row['receive_ms'])==set(PATHS)
    for name,values in row['receive_ms'].items():
        assert len(values)==3 and all(type(v)in(int,float)and math.isfinite(v)and v>0 for v in values)
        assert math.isclose(row['median_receive_ms'][name],statistics.median(values),rel_tol=1e-12,abs_tol=1e-12)
    assert row['receive_order']==[list(PATHS[(row['id']+i)%3:]+PATHS[:(row['id']+i)%3])for i in range(3)]
    assert math.isfinite(row['offline_old_preflight_ms'])and row['offline_old_preflight_ms']>0

def check_summary(summary,rows):
    means={name:statistics.mean(row['median_receive_ms'][name]for row in rows)for name in PATHS}
    assert summary['frames']==len(rows)
    assert summary['old_complete_bytes']==sum(row['old_complete_bytes']for row in rows)
    assert summary['bytes_removed_per_profile']==16*len(rows)
    assert summary['old_full_tag_calls']==sum(2 if row['key']else 3 for row in rows)
    for name,value in means.items():assert math.isclose(summary['mean_median_receive_ms'][name],value,rel_tol=1e-12,abs_tol=1e-12)
    for name in PATHS[1:]:
        assert summary['complete_bytes'][name]==sum(row['profiles'][name]['complete_bytes']for row in rows)
        assert summary['observed_new_canonical_hash_calls'][name]==len(rows)
        assert math.isclose(summary['receive_ratio_to_CS38'][name],means[name]/means['CS38'],rel_tol=1e-12,abs_tol=1e-12)

def main():
    data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-canonical-tag-v66'
    for name in('physical_30fps_proven','new_RTL_implemented','current_JPEG_firmware_supports_new_profiles','protocol_negotiation_implemented'):assert data[name]is False
    pins=data['source_sha256']
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    for name in('helpers.py','protocol.py','receiver.py','benchmark.py','test_model.py'):
        assert (HERE/name).relative_to(ROOT).as_posix()in pins
    for name,domain in(('CS66','geometry+planar little-endian int16'),('CU66','geometry+planar validated uint8')):
        spec=data['profiles'][name]
        assert spec==dict(outer=name,inner='GS66'if name=='CS66'else'GU66',profile_tag=PROFILES[name].hex(),domain=domain,
            inner_header_bytes=60,canonical_digest='SHA256[:16]',outer_digest_bits=128,pre_normalization_output_tag_in_wire=False,verified_reference_tag_cached=True)
    assert data['hash_demand_assumptions']==dict(CS38_key=demand(2,2),CS38_P=demand(2,3),CS66_key_or_P=demand(2,1),CU66_key_or_P=demand(1,1))
    records={(c['source_folder'],c['scene']):c for c in data['cases']};assert len(records)==8
    oldreceiver=oldproof.direct_module();frames=keys=chains=arithmetic=0;unique=set();actualcalls={name:0 for name in PATHS[1:]};legacycalls={name:0 for name in PATHS[1:]}
    dispatch=[0]*7
    for foldername,total in FOLDERS:
        folder=HERE.parent/foldername;source=json.loads((folder/'results.json').read_text());count=0
        assert (folder/'results.json').relative_to(ROOT).as_posix()in pins
        for case in source['cases']:
            record=records[(foldername,case['scene'])];assert len(record['rows'])==len(case['rows'])
            oldrx=oldreceiver.Receiver();states={name:subject.Receiver(name)for name in PATHS[1:]};chains+=1
            for original,row in zip(case['rows'],record['rows'],strict=True):
                old=raw(original['packet'],folder);unique.add(digest(old));reference=oldrx.ref
                assert row['id']==original['id']and row['source_packet']==original['packet']and row['source_packet_sha256']==digest(old)
                assert row['old_complete_bytes']==len(old)<=49152
                paired_timings(row)
                with oldproof.no_reencode():expected=oldrx.receive(old)
                normalized,patches,meta,nplanes=expected;assert row['key']==meta['key']
                assert row['old_reference_tag']==meta['reference_tag'].hex()and row['old_output_tag']==meta['output_tag'].hex()
                assert row['old_base_tag_evidence']==meta['base_tag'].hex()
                assert tag(normalized,'CS66').hex()==original['normalized_tag']
                display=f.f.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(normalized)),tuple(p['words']for p in patches))
                assert f.f.n.digest(display)==original['display_sha256']==row['display_sha256']
                assert set(row['profiles'])==set(PATHS[1:])
                for name,rx in states.items():
                    recordprofile=row['profiles'][name];wire,pretag=expected_wire(old,name,None if meta['key']else reference,normalized)
                    assert raw(recordprofile['packet'],HERE)==wire
                    assert recordprofile['complete_bytes']==len(wire)==len(old)-16 and recordprofile['removed_bytes']==16
                    assert recordprofile['old_tag_evidence']==dict(old_base_tag=pretag.hex(),old_reference_tag=meta['reference_tag'].hex(),old_output_tag=meta['output_tag'].hex())
                    with oldproof.no_reencode(),counted()as(calls,oldcalls):actual=rx.receive(wire)
                    assert len(calls)==1 and calls[0][0]is actual[0]and calls[0][1]==name
                    assert len(oldcalls)==(1 if name=='CS66'else 0)
                    actualcalls[name]+=len(calls);legacycalls[name]+=len(oldcalls)
                    oldproof.equal_planes(actual[0],normalized);oldproof.equal_hud(actual[1],patches);equal_meta(actual[2],meta,name)
                    assert actual[3]==nplanes and actual[2]['dispatch']==meta['dispatch']and actual[2]['plane_payloads']==meta['plane_payloads']
                    assert rx.ref is actual[0]and rx.hud is actual[1]and rx.rid==rx.last==row['id']
                    assert rx.cached_tag==tag(normalized,name)==actual[2]['output_tag']
                    rt=bytes(16)if meta['key']else tag(reference,name)
                    assert actual[2]['reference_tag']==rt
                    assert recordprofile['reference_tag']==rt.hex()and recordprofile['output_tag']==recordprofile['cached_tag']==rx.cached_tag.hex()
                    for array in(*actual[0],*actual[2]['coefficients'],actual[2]['qmap'],actual[2]['vectors'],*(p['words']for p in actual[1])):assert not array.flags.writeable
                    assert recordprofile['normalized_i16_sha256']==digest(b''.join(p.astype('<i2').tobytes()for p in normalized))
                    assert recordprofile['coefficients_i16_sha256']==digest(b''.join(p.astype('<i2').tobytes()for p in meta['coefficients']))
                    assert recordprofile['qmap_sha256']==digest(meta['qmap'].tobytes())and recordprofile['vectors_sha256']==digest(meta['vectors'].tobytes())and recordprofile['hud_sha256']==digest(meta['hud'])
                    work=recordprofile['decode_work']
                    for key in('entropy_plan_calls','entropy_construct_calls','synthetic_reencoded_packets','reference_rehash_calls','pre_norm_hash_calls'):assert work[key]==0
                    for key in('output_reconstructions','normalization_passes','canonical_hash_calls'):assert work[key]==1
                    assert work['binary_plane_decode_calls']==nplanes and work['dispatch_counts']==[meta['dispatch'].count(i)for i in range(7)]
                    assert work['coefficient_array_bytes']==work['normalized_array_bytes']==1036800 and work['owned_HUD_array_bytes']==42240
                    assert work['outer_tag_checked']is work['HUD_validated_before_publication']is True and work['negotiated_profile']==name
                    assert 0<work['receive_ms']<=row['receive_ms'][name][-1]
                    spy=recordprofile['hash_spy'];assert spy['canonical_tag_calls']==1 and spy['actual_preimage_bytes']==4+518400*(2 if name=='CS66'else 1)
                    assert spy['profile_domain']==data['profiles'][name]['domain']and 'excluded'in spy['scope']
                    assert 0<recordprofile['offline_conversion_ms']and math.isfinite(recordprofile['offline_conversion_ms'])
                keys+=int(meta['key']);arithmetic+=nplanes
                for d in meta['dispatch']:dispatch[d]+=1
                frames+=1;count+=1
            check_summary(record['summary'],record['rows'])
        assert count==total
        print(json.dumps(dict(campaign=foldername,exact_causal_frames=count,profiles=2)),flush=True)
    assert frames==577;rows=[r for c in data['cases']for r in c['rows']];check_summary(data['summary'],rows)
    oldproof.assert_no_new_encoder()
    for modulevalue in list(sys.modules.values()):
        path=getattr(modulevalue,'__file__',None)
        assert path is None or Path(path).resolve()not in{HERE/'model.py',HERE/'benchmark.py'}
    print(json.dumps(dict(old_causal_presentations=frames,new_profile_receives=frames*2,unique_old_packets=len(unique),reference_chains=chains,key_frames=keys,P_frames=frames-keys,
        source_pins=len(pins),bytes_removed_each_profile=16*frames,actual_canonical_hash_calls=actualcalls,actual_legacy_i16_hash_calls=legacycalls,
        old_direct_full_video_tag_calls=2*keys+3*(frames-keys),arithmetic_planes=arithmetic,dispatch_counts=dispatch,
        complete_coefficients_qmap_vectors_YUV_HUD_display_and_future_reference_exact=True,no_entropy_reencode=True,
        CS66_old_tag_bytes_preserved=True,CU66_validated_distinct_uint8_domain=True,cached_reference_tag_bound_before_atomic_publish=True,
        input_canonical_arrays_still_int16=True,physical_30fps_proven=False,RTL_or_ECC_or_authentication_proven=False)),flush=True)
if __name__=='__main__':main()
