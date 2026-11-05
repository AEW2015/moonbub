#!/usr/bin/env python3
"""Independent finer coefficient-bit/rank-cost selector qualification.

No new signal encoder/helper is imported. Frozen RP39 receives actual packets.
The unrounded isolated-coefficient proxy is independently derived here and
qualified with a separate scalar Rice/syntax oracle. It is deliberately not a
claim about full-plane or arithmetic-coded marginal rate.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,sys
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('signal39_frozen_rank39_decoder',HERE.parent/'python-game-mode-rank-v39-study/verify.py')
rank=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rank;spec.loader.exec_module(rank)
spatial,f,m=rank.spatial,rank.f,rank.m

def load(path):return json.loads(Path(path).read_text())
def raw(desc):return f.frozen.raw(desc,HERE)

def mapped(value):return 2*value if value>=0 else -2*value-1
def scalar_rice(value,k,escape):
    quotient=value>>k
    return quotient+1+k if quotient<15 else 15+escape

def scalar_fine_bits(block):
    zig=np.asarray(block).reshape(-1)[m.ft.ZIGZAG]
    dc=min(scalar_rice(mapped(int(zig[0])),k,14) for k in range(14))
    positions=[i for i in range(1,64) if zig[i]]
    syntax=5*len(positions)+2*(not positions or positions[-1]!=63)
    previous=0
    for position in positions:syntax+=2*((position-previous-1)//16);previous=position
    ac=syntax
    for lo,hi in ((1,6),(6,21),(21,64)):
        levels=[mapped(int(zig[position]))-1 for position in range(lo,hi) if zig[position]]
        ac+=min(sum(scalar_rice(value,k,12) for value in levels) for k in range(12))
    return min(1024,32+dc+ac)

def fine_bits(coefficients):
    """Unrounded32 parameter bits + separate DC/AC Rice/syntax, raw1024 cap."""
    a=np.asarray(coefficients)
    if a.dtype!=np.int16 or a.ndim!=3 or a.shape[1:]!=(8,8) or not 1<=len(a)<=65536 or np.any(a<-2048) or np.any(a>2048):
        raise ValueError('bounded coefficient arrays')
    output=np.empty(len(a),np.int64)
    for start in range(0,len(a),1024):
        zig=a[start:start+1024].reshape(-1,64)[:,m.ft.ZIGZAG].astype(np.int64)
        dc=np.where(zig[:,0]>=0,2*zig[:,0],-2*zig[:,0]-1)
        dc_bits=np.full(len(zig),1000,np.int64)
        for k in range(14):
            quotient=dc>>k;dc_bits=np.minimum(dc_bits,np.where(quotient<15,quotient+1+k,15+14))
        values=zig[:,1:];nonzero=values!=0;positions=np.arange(1,64)
        last=np.maximum.accumulate(np.where(nonzero,positions,0),axis=1)
        previous=np.column_stack((np.zeros(len(zig),np.int64),last[:,:-1]))
        runs=positions-previous-1
        ac_bits=5*nonzero.sum(axis=1)+2*np.where(nonzero,runs//16,0).sum(axis=1)+2*(last[:,-1]!=63)
        levels=np.where(values>=0,2*values,-2*values-1)-1;levels[~nonzero]=0
        for lo,hi in ((0,5),(5,20),(20,63)):
            best=np.full(len(zig),1000000,np.int64)
            for k in range(12):
                quotient=levels[:,lo:hi]>>k
                sizes=np.where(quotient<15,quotient+1+k,15+12)
                best=np.minimum(best,(sizes*nonzero[:,lo:hi]).sum(axis=1))
            ac_bits+=best
        output[start:start+len(zig)]=np.minimum(1024,32+dc_bits+ac_bits)
    return output

def predictor_menu(predictions):
    """Return stable canonical flags and each original mode's canonical rank."""
    unique=[];canonical=[];ranks=[]
    for prediction in predictions:
        found=next((i for i,previous in enumerate(unique) if np.array_equal(prediction,previous)),None)
        canonical.append(found is None)
        if found is None:found=len(unique);unique.append(prediction)
        ranks.append(found)
    count=len(unique)
    bits=np.array([0 if count==1 else min(value+1,count-1) for value in ranks],np.int64)
    return np.array(canonical,np.int64),bits

def array(desc,shape,dtype):
    if desc['shape']!=list(shape) or desc['dtype']!=np.dtype(dtype).str:raise ValueError('exact array metadata')
    data=raw(desc)
    if len(data)!=int(np.prod(shape))*np.dtype(dtype).itemsize:raise ValueError('exact array bytes')
    return np.frombuffer(data,dtype=dtype).reshape(shape).copy()

def verify_plane(source,temporal,tables,safe,modes,coefficients,costs,weight,control):
    height,width=source.shape;bh,bw=height//8,width//8
    current=np.empty_like(source);mask=safe.reshape(-1)
    assert np.all(costs[mask]==0)
    indices=[];proposals=[];evaluated=0
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx;y,x=by*8,bx*8
                if safe[by,bx]:
                    assert modes[index]==0 and not np.any(coefficients[index])
                    current[y:y+8,x:x+8]=128;continue
                prediction=np.stack([spatial.predict_block(temporal,current,by,bx,mode) for mode in range(4)])
                canonical,rank_bits=predictor_menu(prediction)
                np.testing.assert_array_equal(costs[index,:,2],rank_bits)
                np.testing.assert_array_equal(costs[index,:,3],canonical)
                original=source[y:y+8,x:x+8].astype(np.int64)
                transformed=m.ft.forward(original-prediction)
                quant=m.ft.round_quantize(transformed,tables[index]).astype(np.int16)
                assert not np.any(np.abs(quant.astype(np.int32))>m.ft.MAX_COEFF)
                pixels=np.clip(m.ft.inverse(quant.astype(np.int64)*tables[index])+prediction,0,255).astype(np.int16)
                errors=np.square(original-pixels).sum(axis=(1,2))
                np.testing.assert_array_equal(costs[index,:,0],errors)
                scores=errors+weight*(costs[index,:,1]+rank_bits)
                scores[canonical==0]=np.iinfo(np.int64).max
                selected=0 if control else int(np.argmin(scores))
                assert modes[index]==selected and canonical[selected]
                np.testing.assert_array_equal(coefficients[index],quant[selected])
                current[y:y+8,x:x+8]=pixels[selected]
                indices.append(index);proposals.append(quant);evaluated+=4
    joined=np.concatenate(proposals);expected_bits=fine_bits(joined).reshape(-1,4)
    np.testing.assert_array_equal(costs[np.array(indices),:,1],expected_bits)
    for index in sorted({0,len(joined)//2,len(joined)-1}):assert scalar_fine_bits(joined[index])==expected_bits.reshape(-1)[index]
    return current,evaluated

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-signal-v39'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..'not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    old_spatial=load(HERE.parent/'python-game-spatial-v38-study/results.json')
    old_rank=load(HERE.parent/'python-game-mode-rank-v39-study/results.json')
    inputs=load(f.n.V24/'results.json')['inputs'];policies=('mode0control','lambda1','lambda4','lambda16')
    assert data['profile']['policies']==list(policies) and data['profile']['lambdas']==[0,1,4,16]
    assert data['profile']['coefficient_parameter_bits']==32 and data['profile']['raw_coefficient_bits']==1024
    fixtures={}
    for item in old_spatial['synthetic_inputs']:
        packed=spatial.array(item['source'],(518400,),'u1')
        source=(packed[:345600].reshape(480,720).astype(np.int16),packed[345600:432000].reshape(240,360).astype(np.int16),packed[432000:].reshape(240,360).astype(np.int16))
        fixtures[item['scene']]=(source,spatial.array(item['original'],(480,720),'<u2'))
    keys=[(c['scene'],c['kind'],c['policy']) for c in data['cases']]
    expected={(c['scene'],'main',p) for c in inputs for p in policies}|{(name,'synthetic',p) for name in fixtures for p in policies}
    assert len(keys)==len(set(keys))==20 and set(keys)==expected
    decoded_frames=candidate_blocks=exact_controls=rank_trials=0;directional={}
    for case in data['cases']:
        control=case['policy']=='mode0control';weight=0 if control else int(case['policy'][6:])
        assert case['lambda_value']==weight
        count=12 if case['kind']=='main' else 1
        assert [r['id'] for r in case['rows']]==list(range(count)) and all(type(r['id'])is int for r in case['rows'])
        golden=next(c for c in old_rank['cases'] if c['scene']==case['scene'] and c['kind']==case['kind'] and c['policy']=='mode0control')
        rx=rank.Receiver();checks=[]
        for row in case['rows']:
            fid=row['id'];key=fid%24==0;rid=m.NO_REF if key else fid-1
            assert row['key']==key and row['reference_id']==rid
            assert row['source_id']==dict(scene=case['scene'],id=fid,kind=case['kind'])
            if case['kind']=='main':
                src=next(c for c in inputs if c['scene']==case['scene'])['rows'][fid]
                source=f.n.source(src);original=f.n.original(src)
                assert row['source_sha256']==src['common_yuv420_u8_sha256']
            else:source,original=fixtures[case['scene']]
            assert row['source_sha256']==hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in source)).hexdigest()
            packet=raw(row['packet']);intermediate=raw(row['SP38_packet']);imeta=spatial.parse(intermediate)
            meta=rank.parse(packet);temporal=tuple(np.full_like(p,128) for p in source) if key else rx.ref
            assert (meta['key'],meta['frame_id'],meta['reference_id'])==(key,fid,rid)
            assert meta['reference_tag']==(bytes(16) if key else m.C.reference_tag(temporal))
            assert row['reference_tag']==meta['reference_tag'].hex()==imeta['reference_tag'].hex()
            assert meta['output_tag']==imeta['output_tag']
            assert meta['hud']==imeta['hud']==raw(row['hud_packet'])
            assert meta['plane_payloads']==imeta['plane_payloads']
            np.testing.assert_array_equal(meta['qmap'],imeta['qmap'])
            np.testing.assert_array_equal(meta['qmap'],m.roi.declared_map(720,480,f.n.ROIS,8,16))
            pixels,patches,decoded=rx.receive(packet)
            reconstructed=[];mode_counts=[];evaluated=[]
            for plane,(src_plane,base,safe,modes,coeff) in enumerate(zip(source,temporal,f.safe_blocks(),decoded['modes'],decoded['coefficients'],strict=True)):
                np.testing.assert_array_equal(array(row['mode_arrays'][plane],(safe.size,),'u1'),modes)
                np.testing.assert_array_equal(imeta['modes'][plane],modes)
                np.testing.assert_array_equal(imeta['coefficients'][plane],coeff)
                costs=array(row['candidate_cost_arrays'][plane],(safe.size,4,4),'<i8')
                recovered,proposed=verify_plane(src_plane,base,m.roi.block_tables(meta['qmap'],720,480,plane),safe,modes,coeff,costs,weight,control)
                reconstructed.append(recovered);candidate_blocks+=proposed;evaluated.append(proposed)
                mode_counts.append([int(np.count_nonzero(modes[~safe.reshape(-1)]==mode)) for mode in range(4)])
                if case['scene']=='directional_tiles' and plane==0:
                    directional[case['policy']]=(costs[1].copy(),int(modes[1]))
            for a,b in zip(reconstructed,pixels,strict=True):np.testing.assert_array_equal(a,b)
            expected_patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in f.n.RECTS)
            for a,b in zip(patches,expected_patches,strict=True):np.testing.assert_array_equal(a['words'],b)
            quality,display=f.metric(pixels,original,patches)
            assert quality==row['hybrid'] and display==row['display_sha256']
            assert m.C.reference_tag(pixels).hex()==row['normalized_tag']
            assert len(packet)==row['complete_bytes']<=len(intermediate)<=49152
            entropy_records=spatial.verify_coeff_entropy(imeta)
            work=row['work'];assert work['policy']==case['policy'] and work['lambda_value']==weight
            assert math.isfinite(work['encode_ms']) and work['encode_ms']>0
            assert work['cap_fit']is True and work['research_oracle_evaluates_all4_modes_even_control']is True
            assert work['SP38_complete_bytes']==len(intermediate) and work['RP39_complete_bytes']==len(packet)
            assert work['SP38_mode_bytes']==sum(map(len,imeta['mode_payloads']))
            assert work['coefficient_bytes']==sum(map(len,imeta['plane_payloads']))
            assert row['mode_bytes']==sum(map(len,decoded['mode_payloads']))
            rankwork=work['rank'];assert rankwork['old_encode_already_paid']is True and rankwork['coefficient_payloads_unchanged']is True
            assert rankwork['input_complete_bytes']==len(intermediate) and rankwork['output_complete_bytes']==len(packet)
            assert 0<rankwork['transcode_ms']<=work['encode_ms']
            assert len(row['rank_trials'])==len(work['planes'])==3
            for plane,(trial,record,safe,base,committed,modes,oldpayload,selected,detail,entropy_record) in enumerate(zip(
                    row['rank_trials'],rankwork['planes'],f.safe_blocks(),temporal,pixels,imeta['modes'],imeta['mode_payloads'],
                    decoded['mode_payloads'],work['planes'],entropy_records,strict=True)):
                candidate=raw(trial['rank_packet']);menus,ranks,independent=rank.verify_trial(candidate,base,committed,safe,modes)
                np.testing.assert_array_equal(array(trial['menus'],(safe.size,),'u1'),menus)
                np.testing.assert_array_equal(array(trial['ranks'],(safe.size,),'u1'),ranks)
                np.testing.assert_array_equal(decoded['ranks'][plane],ranks)
                rank.check_plane_work(record,independent,oldpayload,candidate,selected,plane)
                assert detail['plane']==plane and detail['visible_blocks']==int((~safe).sum()) and detail['hidden_blocks']==int(safe.sum())
                assert detail['evaluated_block_candidates']==evaluated[plane] and detail['mode_counts']==mode_counts[plane]
                assert detail['SP38_mode_bytes']==len(oldpayload) and detail['coefficient_bytes']==entropy_record['selected']
                assert detail['implicit_selected']is entropy_record['implicit']
                assert detail['fullgrid_payload_bytes']==entropy_record['full'] and detail['compact_payload_bytes']==entropy_record['compact']
                rank_trials+=1
            assert len(intermediate)-len(packet)==work['SP38_mode_bytes']-row['mode_bytes']
            if control:
                assert packet==f.frozen.raw(golden['rows'][fid]['packet'],HERE.parent/'python-game-mode-rank-v39-study')
                assert row['old_control_packet_exact']is True;exact_controls+=1
            assert math.isfinite(row['receiver_ms']) and row['receiver_ms']>0
            checks.append(row);decoded_frames+=1
        summary=case['summary'];assert summary['frames']==count
        assert summary['complete_bytes']==sum(r['complete_bytes'] for r in checks) and summary['maximum_complete_bytes']==max(r['complete_bytes'] for r in checks)
        assert summary['mode_bytes']==sum(r['mode_bytes'] for r in checks) and summary['coefficient_bytes']==sum(r['work']['coefficient_bytes'] for r in checks)
        assert summary['active_mse']==sum(r['hybrid']['active_squared_error'] for r in checks)/sum(r['hybrid']['active_channel_samples'] for r in checks)
        assert summary['peak_frame_mse']==max(r['hybrid']['active_mse'] for r in checks) and summary['all_frames_cap_fit']is True
        assert math.isclose(summary['mean_encode_ms'],sum(r['work']['encode_ms'] for r in checks)/count,abs_tol=1e-10)
        assert summary['mode_counts']==[sum(p['mode_counts'][mode] for r in checks for p in r['work']['planes']) for mode in range(4)]
        assert math.isclose(summary['nominal_Mbps_at30'],summary['complete_bytes']*240/count/1e6,abs_tol=1e-12)
    assert decoded_frames==108 and exact_controls==27 and rank_trials==324
    assert set(directional)==set(policies)
    for policy,(costs,mode) in directional.items():
        np.testing.assert_array_equal(costs[:,0],0)
        assert costs[0,1]==41 and costs[2,1]==35 and costs[0,2]==costs[2,2]==1
        assert mode==(0 if policy=='mode0control' else 2)
    print(json.dumps(dict(actual_RP39_frames=decoded_frames,exact_frozen_control_packets=exact_controls,
        independently_recomputed_candidate_blocks=candidate_blocks,actual_rank_trial_planes=rank_trials,
        unrounded_scalar_vector_proxy_qualified=True,directional_byte_tie_distinguished=True,
        source_pins=len(data['source_sha256']),new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
