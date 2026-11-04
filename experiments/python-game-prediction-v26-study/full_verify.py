#!/usr/bin/env python3
"""Replay CP2F, all losing GM26 candidates, SSE decisions, HUD/ACK and goldens."""
import json,time,importlib.util,sys
import numpy as np
import full_benchmark as f
spec=importlib.util.spec_from_file_location('fractional26_local_verify',f.HERE/'verify.py')
v=importlib.util.module_from_spec(spec);sys.modules[spec.name]=v;spec.loader.exec_module(v)

def main():
    result=f.b.n.load(f.HERE/'full_results.json');v.check_pins(result['source_sha256'])
    old=f.b.n.load(f.b.n.V24/'results.json');selected_count=attempt_count=half_count=0
    for case in result['cases']:
        inp=next(x for x in old['inputs'] if x['scene']==case['scene']);receiver=f.p.Receiver(epoch=25);ref=None;refid=f.m.NO_REF
        for row,source in zip(case['rows'],inp['rows']):
            if row['key']:ref=None;refid=f.m.NO_REF
            original=f.b.n.original(source);hud=f.b.n.raw(row['hud_packet'],f.b.ROOT/row['hud_packet']['directory'])
            selected=None
            for a in row['attempts']:
                packet=f.b.n.raw(a['base_packet'],f.HERE)
                decoded,meta=f.m.decode(packet,ref,expected_epoch=25,expected_reference_id=None if row['key'] else refid)
                bare=f.m.C.corpus.rgb565(f.m.ft.planes_to_rgb(decoded))
                hybrid=f.b.n.overlay(bare,tuple(original[y:y+h,x:x+w] for x,y,w,h in f.b.n.RECTS))
                assert f.b.n.metric(original,hybrid)==a['hybrid']
                pair=f.b.n.raw(a['packet'],f.HERE);assert len(pair)==a['complete_bytes']
                assert pair==f.pair_bytes(packet,hud,row['id'],row['source_slot'] if not row['key'] else 0,row['key'])
                if a['cap_fit']:f.p.parse_pair(pair)
                else:
                    try:f.p.parse_pair(pair)
                    except ValueError:pass
                    else:raise AssertionError('overcap accepted')
                zero=next(z for z in row['attempts'] if z['background']==a['background'] and z['kind']=='zero')
                assert a['quality_eligible']==(a['hybrid']['active_squared_error']<=zero['hybrid']['active_squared_error'])
                if a['selected']:selected=a
                attempt_count+=1
            assert selected is not None
            eligible=[a for a in row['attempts'] if a['background']==row['selected_background'] and a['cap_fit'] and a['quality_eligible']]
            assert selected is min(eligible,key=lambda a:a['complete_bytes'])
            assert selected['kind']==row['selected_kind']
            pair=f.b.n.raw(row['packet'],f.HERE);decoded,patches,ack=receiver.receive(pair)
            assert ack==f.b.n.raw(row['ack'],f.HERE);assert f.p.validate_ack(ack,pair)==row['ack_meta']
            for patch,(x,y,w,h) in zip(patches,f.b.n.RECTS):np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
            hybrid=f.b.n.overlay(f.m.C.corpus.rgb565(f.m.ft.planes_to_rgb(decoded)),tuple(p['words'] for p in patches))
            assert f.b.n.metric(original,hybrid)==row['hybrid'] and row['hybrid']['hud_word_errors']==0
            assert f.b.n.digest(hybrid)==row['hybrid_rgb565_sha256']
            if 'golden_hybrid_rgb565' in row:assert hybrid.astype('<u2').tobytes()==f.b.n.raw(row['golden_hybrid_rgb565'],f.HERE)
            ref=decoded;refid=row['id'];selected_count+=1;half_count+=row['selected_kind']=='half32'
        assert sum(r['body_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
        assert sum(r['hybrid']['active_squared_error'] for r in case['rows'])==case['summary']['active_squared_error']
        assert len(case['rows'])==48 and case['summary']['cap_fit_frames']==48
    print(json.dumps(dict(status='PASS',selected_packets=selected_count,actual_attempts=attempt_count,half32_selected=half_count,exact_hud_word_errors=0)))
if __name__=='__main__':main()
