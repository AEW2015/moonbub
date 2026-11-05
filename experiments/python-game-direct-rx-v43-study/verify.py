#!/usr/bin/env python3
"""Independent retained-CS38 replay against the frozen re-encoding adapter.

This driver imports the new RECEIVER, never a new encoder.  Its oracle deliberately
retains the old proof adapter, and that adapter runs outside the no-encode guard.
Full coefficient arrays remain allowed; no target-memory or FPGA-cycle claim.
"""
from pathlib import Path
import contextlib,hashlib,importlib.util,json,math,statistics,struct,sys,zlib
from unittest.mock import patch
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=HERE.parent/'python-game-binary-v38-study'
CAMPAIGNS=(('python-game-binary-v38-study',24),('python-game-binary-full-v39-study',96),('python-game-binary-qual-v40-study',457))

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value

def bootstrap():
    """Bind each frozen module to its own helper at import, then restore alias."""
    prior=sys.modules.get('helpers')
    try:
        helpers=module('rx43_oracle_helpers',OLD/'helpers.py');sys.modules['helpers']=helpers
        adapter=module('rx43_oracle_adapter',OLD/'frame_verify.py')
    finally:
        if prior is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=prior
    return helpers,adapter
h,adapter=bootstrap();f=h.f;m=f.m

def direct_module():
    prior=sys.modules.get('helpers')
    try:
        if (HERE/'helpers.py').exists():sys.modules['helpers']=module('rx43_direct_helpers',HERE/'helpers.py')
        return module('rx43_direct_receiver',HERE/'receiver.py')
    finally:
        if prior is None:sys.modules.pop('helpers',None)
        else:sys.modules['helpers']=prior

def raw(desc,folder):return h.raw(desc,folder)
def digest(data):return hashlib.sha256(data).hexdigest()

def assert_no_new_encoder():
    forbidden={HERE/'model.py',OLD/'model.py'}
    for value in list(sys.modules.values()):
        path=getattr(value,'__file__',None)
        assert path is None or Path(path).resolve() not in forbidden,'new coefficient encoder imported'

@contextlib.contextmanager
def no_reencode():
    """Actual call failures, rather than trusted self-reported zero counters."""
    targets={id(v):v for v in list(sys.modules.values()) if hasattr(v,'_plane_plan') and hasattr(v,'_construct')}
    # Frozen imports may replace module-name entries while old adapters retain
    # earlier module objects. Bind that retained oracle object explicitly too.
    retained=f.f.frozen.shared.entropy;targets[id(retained)]=retained
    assert targets,'no frozen entropy targets loaded'
    with contextlib.ExitStack() as stack:
        for entropy in targets.values():
            for name in ('_plane_plan','_construct'):
                stack.enter_context(patch.object(entropy,name,side_effect=AssertionError('entropy re-encode forbidden')))
        yield

def equal_planes(left,right):
    assert len(left)==len(right)==3
    for a,b in zip(left,right,strict=True):np.testing.assert_array_equal(a,b)

def equal_hud(left,right):
    assert len(left)==len(right)==4
    for a,b in zip(left,right,strict=True):
        assert tuple(a['rect'])==tuple(b['rect']);np.testing.assert_array_equal(a['words'],b['words'])

def equal_meta(actual,expected):
    for name in ('key','frame_id','reference_id','reference_tag','output_tag','base_tag','block_size'):
        assert actual[name]==expected[name],name
    for name in ('qmap','vectors'):np.testing.assert_array_equal(actual[name],expected[name])
    equal_planes(actual['coefficients'],expected['coefficients'])
    assert actual['hud']==expected['hud']

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def outer_edit(packet,index,value):
    fields=list(adapter.HEADER.unpack_from(packet));fields[index]=value
    return seal(adapter.HEADER.pack(*fields)+packet[adapter.HEADER.size:-4])

def snapshot(rx):
    return dict(rid=rx.rid,last=rx.last,ref=None if rx.ref is None else tuple(a.copy() for a in rx.ref),
                hud=None if rx.hud is None else tuple({'rect':tuple(p['rect']),'words':p['words'].copy()} for p in rx.hud))

def unchanged(rx,before):
    assert rx.rid==before['rid'] and rx.last==before['last']
    if before['ref'] is None:assert rx.ref is None
    else:equal_planes(rx.ref,before['ref'])
    if before['hud'] is None:assert rx.hud is None
    else:equal_hud(rx.hud,before['hud'])

def assert_rejected_atomically(rx,packet):
    before=snapshot(rx)
    try:
        with no_reencode():rx.receive(packet)
    except ValueError:
        unchanged(rx,before);return
    raise AssertionError('malformed/replayed packet accepted')

def original_parts(packet):
    outer=list(adapter.HEADER.unpack_from(packet));inner=packet[adapter.HEADER.size:adapter.HEADER.size+outer[11]]
    fields=list(m.HEADER.unpack_from(inner));pos=m.HEADER.size+fields[12]+fields[13]
    maps=inner[m.HEADER.size:pos];payloads=[]
    for size in fields[14:17]:payloads.append(inner[pos:pos+size]);pos+=size
    assert pos==len(inner)-4
    return outer,fields,maps,payloads,packet[adapter.HEADER.size+outer[11]:-4]

def paired_timings(row):
    samples=row['paired_timing_ms'];assert set(samples)=={'adapter','direct'}
    for name,values in samples.items():
        assert len(values)==3 and all(type(v)in(int,float)and math.isfinite(v)and v>0 for v in values)
        assert math.isclose(row['paired_median_ms'][name],statistics.median(values),rel_tol=1e-12,abs_tol=1e-12)
    expected=[['adapter','direct']if(row['id']+rep)%2==0 else['direct','adapter']for rep in range(3)]
    assert row['paired_order']==expected
    return row['paired_median_ms']

def check_timing_summary(summary,rows):
    means={name:statistics.mean(r['paired_median_ms'][name]for r in rows)for name in('adapter','direct')}
    for name,value in means.items():assert math.isclose(summary['mean_paired_median_ms'][name],value,rel_tol=1e-12,abs_tol=1e-12)
    ratio=means['direct']/means['adapter']
    assert math.isclose(summary['direct_to_adapter_ratio'],ratio,rel_tol=1e-12,abs_tol=1e-12)
    if 'receive_time_reduction_percent'in summary:assert math.isclose(summary['receive_time_reduction_percent'],100*(1-ratio),rel_tol=1e-12,abs_tol=1e-12)
    if 'frames'in summary:assert summary['frames']==len(rows)
    if 'complete_bytes'in summary:assert summary['complete_bytes']==sum(r['complete_bytes']for r in rows)
    if 'dispatch_counts'in summary:assert summary['dispatch_counts']==[sum(r['decode_work']['dispatch_counts'][i]for r in rows)for i in range(7)]
    if 'arithmetic_planes'in summary:assert summary['arithmetic_planes']==sum(r['binary_planes']for r in rows)
    return means

def main():
    direct=direct_module();assert_no_new_encoder()
    data=json.loads((HERE/'results.json').read_text())
    assert data['schema']=='gamebub-direct-rx-v43'
    assert data['physical_30fps_proven'] is data['new_RTL_implemented'] is data['HEVC_AV1_superiority_proven'] is False
    assert data['scope']['repetitions']==3
    pins=data.get('source_sha256',data.get('source_pins_sha256'))
    assert pins is not None
    for path,want in pins.items():assert digest((ROOT/path).read_bytes())==want,path
    records={(Path(c['source_folder']).name,c['scene']):c for c in data['cases']}
    assert len(records)==8
    frames=arithmetic=visible=chains=0;packet_digests=set();dispatch_counts={str(i):0 for i in range(7)}
    for foldername,total in CAMPAIGNS:
        folder=HERE.parent/foldername;source=json.loads((folder/'results.json').read_text());caseframes=0
        for case in source['cases']:
            rx,oldrx=direct.Receiver(),adapter.Receiver();chains+=1
            record=records[(foldername,case['scene'])]
            assert len(record['rows'])==len(case['rows'])
            for row,timed in zip(case['rows'],record['rows'],strict=True):
                packet=raw(row['packet'],folder);packet_digests.add(digest(packet))
                assert timed['id']==row['id'] and timed['source_packet']==row['packet']
                assert timed['source_packet_sha256']==digest(packet)
                assert raw(timed['packet'],HERE)==packet
                assert timed['complete_bytes']==len(packet)
                assert timed['normalized_tag']==row['normalized_tag'] and timed['display_sha256']==row['display_sha256']
                paired_timings(timed)
                work=timed['decode_work']
                for key in('entropy_plan_calls','entropy_construct_calls','synthetic_reencoded_packets'):assert work[key]==0
                assert work['output_reconstructions']==work['normalization_passes']==1
                assert work['coefficient_array_bytes']==work['normalized_array_bytes']==1036800
                assert work['owned_HUD_array_bytes']==42240
                for key in('pre_norm_tag_checked','outer_tag_checked','HUD_validated_before_publication'):assert work[key] is True
                assert 0<work['receive_ms']<=timed['paired_timing_ms']['direct'][-1]
                # The only proof-adapter encode is confined to this independent oracle.
                converted,count=adapter.convert(packet);expected_meta=f.parse(converted)
                with no_reencode():
                    actual_meta=direct.parse(packet)
                    result=rx.receive(packet)
                actual,parts,meta=result[:3]
                assert len(result)==4 and result[3]==count==timed['binary_planes']
                assert timed['decode_work']['binary_plane_decode_calls']==count
                assert timed['decode_work']['dispatch_counts']==[actual_meta['dispatch'].count(i)for i in range(7)]
                _,ib,maps,payloads,overlay=original_parts(packet)
                assert list(actual_meta['dispatch'])==[v[0] for v in payloads]
                assert list(actual_meta['plane_payloads'])==payloads
                expected,oldparts,oldmeta=oldrx.frozen.receive(converted)
                oldcount=count
                equal_meta(actual_meta,expected_meta);equal_meta(meta,oldmeta)
                equal_planes(actual,expected);equal_hud(parts,oldparts)
                for array in(*actual,*meta['coefficients'],meta['qmap'],meta['vectors'],*(p['words']for p in parts)):assert not array.flags.writeable
                assert oldcount==count
                assert m.C.reference_tag(actual).hex()==row['normalized_tag']
                display=f.f.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(actual)),tuple(p['words'] for p in parts))
                assert f.f.n.digest(display)==row['display_sha256']
                assert rx.rid==oldrx.frozen.rid and rx.last==oldrx.frozen.last
                equal_planes(rx.ref,oldrx.frozen.ref);equal_hud(rx.hud,oldrx.frozen.hud)
                assert len(packet)==row['complete_bytes']<=49152
                arithmetic+=count;visible+=sum(int((~s).sum()) for s in f.f.safe_blocks())
                for d in actual_meta['dispatch']:dispatch_counts[str(d)]+=1
                frames+=1;caseframes+=1
            check_timing_summary(record['summary'],record['rows'])
        assert caseframes==total,(foldername,caseframes)
        print(json.dumps({'campaign':foldername,'exact_causal_frames':caseframes}),flush=True)
    assert frames==577
    if 'summary'in data:check_timing_summary(data['summary'],[r for c in data['cases']for r in c['rows']])
    assert_no_new_encoder()
    print(json.dumps(dict(exact_causal_frames=frames,unique_packet_digests=len(packet_digests),reference_chains=chains,independent_source_pins=len(pins),selected_arithmetic_planes=arithmetic,
        visible_coefficient_blocks=visible,dispatch_counts=dispatch_counts,whole_coefficients_qmap_vectors_YUV_HUD_and_reference_exact=True,
        entropy_reencode_disabled=True,new_encoder_imported=False,full_coefficient_arrays_retained=True,physical_30fps_proven=False)))
if __name__=='__main__':main()
