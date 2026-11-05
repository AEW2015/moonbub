"""577 explicitprofile conversions and balanced whole-receive host comparisons."""
import json,platform,statistics,time
from unittest.mock import patch
import numpy as np
import helpers as h
r=h.bound('canonical66_owned_receiver',h.HERE/'receiver.py',h)
w=h.bound('canonical66_owned_protocol',h.HERE/'protocol.py',h)
PATHS=('CS38','CS66','CU66')

def fork(rx,name):
    copy=h.oldrx.Receiver()if name=='CS38'else r.Receiver(name)
    copy.ref,copy.rid,copy.hud,copy.last=rx.ref,rx.rid,rx.hud,rx.last
    if name!='CS38':copy._cached_tag=rx.cached_tag
    return copy

def equal(out,expected,profile):
    for a,b in zip(out[0],expected[0],strict=True):np.testing.assert_array_equal(a,b)
    for a,b in zip(out[1],expected[1],strict=True):
        assert a['rect']==b['rect'];np.testing.assert_array_equal(a['words'],b['words'])
    for name in('key','frame_id','reference_id','block_size'):
        assert out[2][name]==expected[2][name]
    for name in('qmap','vectors'):np.testing.assert_array_equal(out[2][name],expected[2][name])
    for a,b in zip(out[2]['coefficients'],expected[2]['coefficients'],strict=True):np.testing.assert_array_equal(a,b)
    assert out[2]['hud']==expected[2]['hud']and out[3]==expected[3]
    if profile=='CS66':
        assert out[2]['reference_tag']==expected[2]['reference_tag'];assert out[2]['output_tag']==expected[2]['output_tag']

def summary(rows):
    means={name:statistics.mean(row['median_receive_ms'][name]for row in rows)for name in PATHS}
    return dict(frames=len(rows),old_complete_bytes=sum(row['old_complete_bytes']for row in rows),
        complete_bytes={name:sum(row['profiles'][name]['complete_bytes']for row in rows)for name in PATHS[1:]},
        bytes_removed_per_profile=16*len(rows),mean_median_receive_ms=means,
        receive_ratio_to_CS38={name:means[name]/means['CS38']for name in PATHS[1:]},
        observed_new_canonical_hash_calls={name:sum(row['profiles'][name]['hash_spy']['canonical_tag_calls']for row in rows)for name in PATHS[1:]},
        old_full_tag_calls=sum(2 if row['key']else 3 for row in rows))

def main():
    before=h.pins();cases=[]
    for foldername in h.FOLDERS:
        folder=h.HERE.parent/foldername
        for source_case in h.load(folder/'results.json')['cases']:
            preflight=h.oldrx.Receiver();states={'CS38':h.oldrx.Receiver(),'CS66':r.Receiver('CS66'),'CU66':r.Receiver('CU66')};rows=[]
            for original in source_case['rows']:
                fid=original['id'];oldpacket=h.raw(original['packet'],folder);incoming=preflight.ref
                t=time.perf_counter_ns();expected=preflight.receive(oldpacket);preflight_ms=(time.perf_counter_ns()-t)/1e6
                converted={};evidence={};conversion_ms={}
                for name in PATHS[1:]:
                    t=time.perf_counter_ns();converted[name],evidence[name]=w.convert(oldpacket,name,reference=None if expected[2]['key']else incoming,normalized=expected[0]);conversion_ms[name]=(time.perf_counter_ns()-t)/1e6
                packets={'CS38':oldpacket,**converted};clocks={name:[]for name in PATHS};orders=[]
                for rep in range(3):
                    start=(fid+rep)%3;order=list(PATHS[start:]+PATHS[:start]);orders.append(order);probes={name:fork(states[name],name)for name in PATHS};outputs={}
                    for name in order:
                        began=time.perf_counter_ns();outputs[name]=probes[name].receive(packets[name]);clocks[name].append((time.perf_counter_ns()-began)/1e6)
                    for name in PATHS:equal(outputs[name],expected,name)
                    accepted=probes;lastoutputs=outputs
                profiles={}
                # Actual per-packet canonical-hash call probes, separate from clocks.
                for name in PATHS[1:]:
                    probe=fork(states[name],name)
                    with patch.object(r,'canonical_tag',wraps=r.canonical_tag)as spy:proof=probe.receive(converted[name])
                    assert spy.call_count==1;equal(proof,expected,name)
                    args=spy.call_args.args;assert args[1]==name
                    preimage_bytes=4+sum(p.size for p in args[0])*(2 if name=='CS66'else 1)
                    assert probe.cached_tag==proof[2]['output_tag']and isinstance(probe.cached_tag,bytes)
                    meta=lastoutputs[name][2]
                    profiles[name]=dict(packet=h.blob(converted[name]),complete_bytes=len(converted[name]),removed_bytes=len(oldpacket)-len(converted[name]),
                        old_tag_evidence=evidence[name],reference_tag=meta['reference_tag'].hex(),output_tag=meta['output_tag'].hex(),cached_tag=accepted[name].cached_tag.hex(),
                        normalized_i16_sha256=h.digest(b''.join(p.astype('<i2').tobytes()for p in proof[0])),
                        coefficients_i16_sha256=h.digest(b''.join(p.astype('<i2').tobytes()for p in meta['coefficients'])),
                        qmap_sha256=h.digest(meta['qmap'].tobytes()),vectors_sha256=h.digest(meta['vectors'].tobytes()),hud_sha256=h.digest(meta['hud']),
                        decode_work=meta['decode_work'],hash_spy=dict(canonical_tag_calls=spy.call_count,actual_preimage_bytes=preimage_bytes,
                            profile_domain=w.PROFILES[name]['domain'],scope='one additionalreceive onmatching incomingfork; excludedfromtimedcalls'),
                        offline_conversion_ms=conversion_ms[name])
                states=accepted
                assert h.m.C.reference_tag(expected[0]).hex()==original['normalized_tag']
                display=h.f.f.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(expected[0])),tuple(p['words']for p in expected[1]));assert h.f.f.n.digest(display)==original['display_sha256']
                row=dict(id=fid,key=expected[2]['key'],source_packet=original['packet'],source_packet_sha256=h.digest(oldpacket),old_complete_bytes=len(oldpacket),
                    old_reference_tag=expected[2]['reference_tag'].hex(),old_output_tag=expected[2]['output_tag'].hex(),old_base_tag_evidence=expected[2]['base_tag'].hex(),
                    display_sha256=original['display_sha256'],profiles=profiles,receive_ms=clocks,receive_order=orders,
                    median_receive_ms={name:statistics.median(values)for name,values in clocks.items()},offline_old_preflight_ms=preflight_ms)
                rows.append(row)
                if fid%20==0:print(json.dumps(dict(source=foldername,scene=source_case['scene'],frame=fid,medians=row['median_receive_ms'])),flush=True)
            cases.append(dict(source_folder=foldername,scene=source_case['scene'],rows=rows,summary=summary(rows)));print(json.dumps(cases[-1]['summary']),flush=True)
    flat=[row for c in cases for row in c['rows']];assert len(flat)==577;assert h.pins()==before
    result=dict(schema='gamebub-canonical-tag-v66',source_sha256=before,cases=cases,summary=summary(flat),
        profiles={name:dict(outer=spec['outer'].decode(),inner=spec['inner'].decode(),profile_tag=spec['profile'].hex(),domain=spec['domain'],inner_header_bytes=w.INNER.size,
            canonical_digest='SHA256[:16]',outer_digest_bits=128,pre_normalization_output_tag_in_wire=False,verified_reference_tag_cached=True)for name,spec in w.PROFILES.items()},
        hash_demand_assumptions=dict(CS38_key=w.hash_demand(2,2),CS38_P=w.hash_demand(2,3),CS66_key_or_P=w.hash_demand(2,1),CU66_key_or_P=w.hash_demand(1,1)),
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        physical_30fps_proven=False,new_RTL_implemented=False,current_JPEG_firmware_supports_new_profiles=False,protocol_negotiation_implemented=False,
        scope=['NewnegotiatedprofilesONLY; oldCS38compatibilityreference frozen. Actual577oldstored38/39/40presentations across8histories, not577uniquecaptures.',
            'CS66removesONLY16Binnerpre-normalizedtag andkeepsoldi16rt/ot. CU66addsexplicitvalidateduint8SHApreimagedomain andrecomputesbase reference/outputtags; no truncatingpixels.',
            'Eachreceiverisconfiguredforoneprofile; old/crossprofilesreject. Omittedpre-normalizedunderHUDpreimageisnotpartofnewprofile; canonicaloutputSHA128/CRCs/identity/maps/coeff/HUD retained.',
            'Publishedreference/ID andverifiedcachedtag commitonlyaftercanonicaltag+HUDvalidation. Cachedtagsassumeimmutablebank; noECC/general memoryfault/authenticationclaim.',
            'Threebalancedwhole-receive rounds perframe: orderrotation(frameid+repeat)%3. Stateforks/offlineoldpreflight/conversion/spyproof/metrics/archives outsideclocks identically.',
            'Hashroundmodelassumes64rounds/block andoneiterativeround/cycle, ignoresload/control/memory/overlap; noRTLfit/clock/FPSclaim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
