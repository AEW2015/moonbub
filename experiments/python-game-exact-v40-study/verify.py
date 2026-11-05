#!/usr/bin/env python3
"""Independent exact-output mode alternatives and whole-packet byte guard.

No new encoder/helper is imported. Every proposed candidate is decoded from a
fork of the SAME committed reference. Full8x8 YUV equality, not equal scalar
error, determines eligibility; actual serialized lengths determine publication.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('exact40_frozen_signal39_verifier',HERE.parent/'python-game-signal-v39-study/verify.py')
signal=importlib.util.module_from_spec(spec);sys.modules[spec.name]=signal;spec.loader.exec_module(signal)
rank,spatial,f,m=signal.rank,signal.spatial,signal.f,signal.m

def load(path):return json.loads(Path(path).read_text())
def raw(desc):return f.frozen.raw(desc,HERE)

def candidate_wins(control_bytes,candidate_bytes):
    if type(control_bytes)is not int or not 1<=control_bytes<=49152:
        raise ValueError('fitting integer control size')
    if type(candidate_bytes)is not int or candidate_bytes<=0:
        raise ValueError('positive integer candidate size')
    return candidate_bytes<=49152 and candidate_bytes<control_bytes

def exact_pixels(candidates,target):
    candidates=np.asarray(candidates);target=np.asarray(target)
    if candidates.shape!=(4,8,8) or target.shape!=(8,8):raise ValueError('four full8x8 block candidates')
    return np.all(candidates==target,axis=(1,2))

def fork(receiver):
    branch=rank.Receiver()
    branch.ref,branch.rid,branch.hud,branch.last=receiver.ref,receiver.rid,receiver.hud,receiver.last
    return branch

def array(desc,shape,dtype):
    if desc['shape']!=list(shape) or desc['dtype']!=np.dtype(dtype).str:raise ValueError('exact array metadata')
    data=raw(desc)
    if len(data)!=int(np.prod(shape))*np.dtype(dtype).itemsize:raise ValueError('exact array bytes')
    return np.frombuffer(data,dtype=dtype).reshape(shape).copy()

def verify_plane(source,temporal,control,tables,safe,modes,coefficients,costs):
    height,width=source.shape;bh,bw=height//8,width//8;mask=safe.reshape(-1)
    current=np.empty_like(source);indices=[];proposals=[];evaluated=0
    assert np.all(costs[mask]==0)
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx;y,x=by*8,bx*8
                if safe[by,bx]:
                    assert modes[index]==0 and not np.any(coefficients[index])
                    current[y:y+8,x:x+8]=128
                    np.testing.assert_array_equal(control[y:y+8,x:x+8],128)
                    continue
                prediction=np.stack([spatial.predict_block(temporal,current,by,bx,mode) for mode in range(4)])
                canonical,rank_bits=signal.predictor_menu(prediction)
                original=source[y:y+8,x:x+8].astype(np.int64)
                quant=m.ft.round_quantize(m.ft.forward(original-prediction),tables[index]).astype(np.int16)
                assert not np.any(np.abs(quant.astype(np.int32))>m.ft.MAX_COEFF)
                pixels=np.clip(m.ft.inverse(quant.astype(np.int64)*tables[index])+prediction,0,255).astype(np.int16)
                target=pixels[0];np.testing.assert_array_equal(target,control[y:y+8,x:x+8])
                equal=exact_pixels(pixels,target);eligible=equal&canonical.astype(bool)
                assert eligible[0]
                errors=np.square(original-pixels).sum(axis=(1,2))
                np.testing.assert_array_equal(costs[index,:,0],errors)
                np.testing.assert_array_equal(costs[index,:,2],rank_bits)
                np.testing.assert_array_equal(costs[index,:,3],canonical)
                np.testing.assert_array_equal(costs[index,:,4],equal.astype(np.int64))
                np.testing.assert_array_equal(costs[index,:,5],eligible.astype(np.int64))
                scores=costs[index,:,1]+rank_bits;scores[~eligible]=np.iinfo(np.int64).max
                selected=int(np.argmin(scores));assert modes[index]==selected
                np.testing.assert_array_equal(coefficients[index],quant[selected])
                np.testing.assert_array_equal(pixels[selected],target)
                current[y:y+8,x:x+8]=pixels[selected]
                indices.append(index);proposals.append(quant);evaluated+=4
    joined=np.concatenate(proposals);bits=signal.fine_bits(joined).reshape(-1,4)
    np.testing.assert_array_equal(costs[np.array(indices),:,1],bits)
    for index in sorted({0,len(joined)//2,len(joined)-1}):assert signal.scalar_fine_bits(joined[index])==bits.reshape(-1)[index]
    np.testing.assert_array_equal(current,control)
    return current,evaluated

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-exact-v40'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..'not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    old_rank=load(HERE.parent/'python-game-mode-rank-v39-study/results.json')
    old_spatial=load(HERE.parent/'python-game-spatial-v38-study/results.json');inputs=load(f.n.V24/'results.json')['inputs']
    fixtures={}
    for item in old_spatial['synthetic_inputs']:
        packed=spatial.array(item['source'],(518400,),'u1')
        source=(packed[:345600].reshape(480,720).astype(np.int16),packed[345600:432000].reshape(240,360).astype(np.int16),packed[432000:].reshape(240,360).astype(np.int16))
        fixtures[item['scene']]=(source,spatial.array(item['original'],(480,720),'<u2'))
    keys=[(c['scene'],c['kind']) for c in data['cases']]
    assert len(keys)==len(set(keys))==5 and set(keys)=={(c['scene'],'main') for c in inputs}|{(scene,'synthetic') for scene in fixtures}
    selected_frames=control_goldens=candidate_blocks=accepted=rank_trials=0
    for case in data['cases']:
        count=12 if case['kind']=='main' else 1
        assert [r['id'] for r in case['rows']]==list(range(count)) and all(type(r['id'])is int for r in case['rows'])
        golden=next(c for c in old_rank['cases'] if c['scene']==case['scene'] and c['kind']==case['kind'] and c['policy']=='mode0control')
        live=rank.Receiver();old_live=rank.Receiver();checks=[]
        for row in case['rows']:
            fid=row['id'];key=fid%24==0;rid=m.NO_REF if key else fid-1
            assert row['key']==key and row['reference_id']==rid and row['source_id']==dict(scene=case['scene'],kind=case['kind'],id=fid)
            if case['kind']=='main':
                src=next(c for c in inputs if c['scene']==case['scene'])['rows'][fid]
                source=f.n.source(src);original=f.n.original(src)
                assert row['source_sha256']==src['common_yuv420_u8_sha256']
            else:source,original=fixtures[case['scene']]
            assert row['source_sha256']==hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in source)).hexdigest()
            temporal=tuple(np.full_like(p,128) for p in source) if key else live.ref
            incoming=bytes(16) if key else m.C.reference_tag(live.ref)
            assert row['reference_tag']==incoming.hex()
            before=(live.ref,live.hud,live.rid,live.last)
            control_wire=raw(row['control']['packet']);candidate_wire=raw(row['candidate']['packet']);selected_wire=raw(row['packet'])
            historical=f.frozen.raw(golden['rows'][fid]['packet'],HERE.parent/'python-game-mode-rank-v39-study')
            assert control_wire==historical and row['old_control_packet_exact']is True;control_goldens+=1
            # Each proposed stream starts at the same committed state. Neither
            # branch can become the next frame's reference through this path.
            control_rx=fork(live);candidate_rx=fork(live)
            control_pixels,control_hud,control_meta=control_rx.receive(control_wire)
            candidate_pixels,candidate_hud,candidate_meta=candidate_rx.receive(candidate_wire)
            assert (live.ref is before[0] and live.hud is before[1] and (live.rid,live.last)==before[2:])
            if not key:assert m.C.reference_tag(live.ref)==incoming
            for a,b in zip(control_pixels,candidate_pixels,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(control_hud,candidate_hud,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            assert control_meta['output_tag']==candidate_meta['output_tag']
            for meta in (control_meta,candidate_meta):
                assert (meta['key'],meta['frame_id'],meta['reference_id'],meta['reference_tag'])==(key,fid,rid,incoming)
                np.testing.assert_array_equal(meta['qmap'],m.roi.declared_map(720,480,f.n.ROIS,8,16))
            use_candidate=candidate_wins(len(control_wire),len(candidate_wire))
            wanted_kind='candidate' if use_candidate else 'control'
            assert row['selected_kind']==wanted_kind
            assert selected_wire==(candidate_wire if use_candidate else control_wire)
            assert (row['control_bytes'],row['candidate_bytes'],row['complete_bytes'])==(len(control_wire),len(candidate_wire),len(selected_wire))
            assert len(selected_wire)<=len(control_wire)<=49152
            work=row['work'];assert work['selection']==wanted_kind and work['strict_complete_byte_guard']is True and work['whole_mode0_reference_equal']is True
            assert (work['control_bytes'],work['candidate_bytes'],work['selected_bytes'])==(len(control_wire),len(candidate_wire),len(selected_wire))
            assert math.isfinite(work['encode_pair_ms']) and work['encode_pair_ms']>0
            eligible_nonzero=candidate_nonzero=0
            for role,variant,pixels,meta,rank_work in (
                ('control',row['control'],control_pixels,control_meta,work['control_work']['rank']),
                ('candidate',row['candidate'],candidate_pixels,candidate_meta,work['candidate_rank_work'])):
                intermediate=raw(variant['SP38_packet']);imeta=spatial.parse(intermediate)
                assert imeta['plane_payloads']==meta['plane_payloads'] and imeta['hud']==meta['hud']
                np.testing.assert_array_equal(imeta['qmap'],meta['qmap'])
                assert imeta['reference_tag']==incoming and imeta['output_tag']==meta['output_tag']
                assert rank_work['input_complete_bytes']==len(intermediate) and rank_work['output_complete_bytes']==len(raw(variant['packet']))
                assert rank_work['coefficient_payloads_unchanged']is True and rank_work['old_encode_already_paid']is True
                assert math.isfinite(rank_work['transcode_ms']) and rank_work['transcode_ms']>0
                entropy_records=spatial.verify_coeff_entropy(imeta)
                for plane,(src_plane,base,target,safe,modes,coeff,trial,rank_detail,oldpayload,selected_payload,entropy_record) in enumerate(zip(
                    source,temporal,control_pixels,f.safe_blocks(),meta['modes'],meta['coefficients'],variant['rank_trials'],rank_work['planes'],
                    imeta['mode_payloads'],meta['mode_payloads'],entropy_records,strict=True)):
                    np.testing.assert_array_equal(imeta['modes'][plane],modes)
                    np.testing.assert_array_equal(imeta['coefficients'][plane],coeff)
                    np.testing.assert_array_equal(array(variant['mode_arrays'][plane],(safe.size,),'u1'),modes)
                    columns=4 if role=='control' else 6
                    costs=array(variant['candidate_cost_arrays'][plane],(safe.size,4,columns),'<i8')
                    tables=m.roi.block_tables(meta['qmap'],720,480,plane)
                    if role=='control':
                        recovered,evaluated=signal.verify_plane(src_plane,base,tables,safe,modes,coeff,costs,0,True)
                        assert not np.any(modes)
                        detail=work['control_work']['planes'][plane]
                        assert detail['evaluated_block_candidates']==evaluated
                    else:
                        recovered,evaluated=verify_plane(src_plane,base,target,tables,safe,modes,coeff,costs)
                        eligibility=array(variant['eligibility_arrays'][plane],(safe.size,4),'u1')
                        np.testing.assert_array_equal(eligibility,costs[:,:,5])
                        detail=work['candidate_planes'][plane]
                        ep=int(costs[:,1:,5].sum());npick=int(np.count_nonzero(modes))
                        assert detail['eligible_nonzero_modes']==ep and detail['selected_nonzero_modes']==npick
                        assert detail['all_candidate_blocks']==evaluated
                        eligible_nonzero+=ep;candidate_nonzero+=npick
                    np.testing.assert_array_equal(recovered,pixels[plane]);np.testing.assert_array_equal(recovered,target)
                    candidate_blocks+=evaluated
                    assert detail['plane']==plane and detail['visible_blocks']==int((~safe).sum()) and detail['hidden_blocks']==int(safe.sum())
                    assert detail['mode_counts']==[int(np.count_nonzero(modes[~safe.reshape(-1)]==mode)) for mode in range(4)]
                    assert detail['SP38_mode_bytes']==len(oldpayload) and detail['coefficient_bytes']==entropy_record['selected']
                    assert detail['implicit_selected']is entropy_record['implicit'] and detail['fullgrid_payload_bytes']==entropy_record['full'] and detail['compact_payload_bytes']==entropy_record['compact']
                    trial_payload=raw(trial['rank_packet'])
                    menus,ranks,independent=rank.verify_trial(trial_payload,base,pixels[plane],safe,modes)
                    np.testing.assert_array_equal(array(trial['menus'],(safe.size,),'u1'),menus)
                    np.testing.assert_array_equal(array(trial['ranks'],(safe.size,),'u1'),ranks)
                    np.testing.assert_array_equal(meta['ranks'][plane],ranks)
                    rank.check_plane_work(rank_detail,independent,oldpayload,trial_payload,selected_payload,plane)
                    rank_trials+=1
            assert work['eligible_nonzero_modes']==eligible_nonzero and work['candidate_nonzero_modes']==candidate_nonzero
            assert work['control_work']['policy']=='mode0control' and work['control_work']['lambda_value']==0
            assert work['control_work']['encode_ms']+work['candidate_rank_work']['transcode_ms']<=work['encode_pair_ms']
            selected,patches,selected_meta=live.receive(selected_wire)
            expected,expected_hud,_=old_live.receive(historical)
            for a,b,c,d in zip(selected,control_pixels,candidate_pixels,expected,strict=True):
                np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,c);np.testing.assert_array_equal(a,d)
            for a,b in zip(patches,expected_hud,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            assert m.C.reference_tag(live.ref)==m.C.reference_tag(old_live.ref)
            assert live.rid==old_live.rid==fid and live.last==old_live.last==fid
            expected_patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in f.n.RECTS)
            for a,b in zip(patches,expected_patches,strict=True):np.testing.assert_array_equal(a['words'],b)
            quality,display=f.metric(selected,original,patches)
            assert quality==row['hybrid']==golden['rows'][fid]['hybrid']
            assert display==row['display_sha256']==golden['rows'][fid]['display_sha256']
            assert m.C.reference_tag(selected).hex()==row['normalized_tag']==golden['rows'][fid]['normalized_tag']
            assert math.isfinite(row['receiver_ms']) and row['receiver_ms']>0
            accepted+=use_candidate;selected_frames+=1;checks.append(row)
        s=case['summary'];control_total=sum(r['control_bytes'] for r in checks);candidate_total=sum(r['candidate_bytes'] for r in checks);selected_total=sum(r['complete_bytes'] for r in checks)
        assert s['frames']==count and (s['control_complete_bytes'],s['candidate_complete_bytes'],s['complete_bytes'])==(control_total,candidate_total,selected_total)
        assert s['saved_bytes']==control_total-selected_total and math.isclose(s['percent_saved'],100*(control_total-selected_total)/control_total,abs_tol=1e-12)
        assert s['selected_candidates']==sum(r['selected_kind']=='candidate' for r in checks)
        assert s['candidate_larger_frames']==sum(r['candidate_bytes']>r['control_bytes'] for r in checks)
        assert s['candidate_tie_frames']==sum(r['candidate_bytes']==r['control_bytes'] for r in checks)
        assert s['maximum_complete_bytes']==max(r['complete_bytes'] for r in checks) and s['maximum_control_bytes']==max(r['control_bytes'] for r in checks)
        assert s['eligible_nonzero_modes']==sum(r['work']['eligible_nonzero_modes'] for r in checks) and s['candidate_nonzero_modes']==sum(r['work']['candidate_nonzero_modes'] for r in checks)
        assert s['active_mse']==sum(r['hybrid']['active_squared_error'] for r in checks)/sum(r['hybrid']['active_channel_samples'] for r in checks)
        assert math.isclose(s['mean_paid_pair_ms'],sum(r['work']['encode_pair_ms'] for r in checks)/count,abs_tol=1e-10)
    assert selected_frames==control_goldens==27 and rank_trials==162
    print(json.dumps(dict(selected_exact_reference_frames=selected_frames,exact_frozen_control_packets=control_goldens,
        independently_recomputed_candidate_blocks=candidate_blocks,actual_rank_trial_planes=rank_trials,
        accepted_candidates=accepted,full_YUV_block_and_future_reference_equality=True,strict_actual_packet_byte_guard=True,
        source_pins=len(data['source_sha256']),new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
