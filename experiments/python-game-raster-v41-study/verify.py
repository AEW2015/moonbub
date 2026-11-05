#!/usr/bin/env python3
"""Independent RR41 global-raster residual-edge predictor and decoder.

The decoder only reads previously reconstructed global-raster top/left edges.
The separately implemented host-oracle audit may inspect a full mode0 target,
but never supplies that image to Receiver or to its reconstruction function.
No new raster encoder/helper is imported.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,struct,sys,zlib
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('raster41_frozen_exact40_verifier',HERE.parent/'python-game-exact-v40-study/verify.py')
exact=importlib.util.module_from_spec(spec);sys.modules[spec.name]=exact;spec.loader.exec_module(exact)
signal,rank,spatial,f,m=exact.signal,exact.rank,exact.spatial,exact.f,exact.m
OUTER,INNER=rank.OUTER,rank.INNER
PROFILE=hashlib.sha256(b'RR41:global-raster-residualEdges-v1:clippedPred:DCavailable:hiddenImmediate:distinctRanks:AB38availabilityCtx44:'+
    json.dumps(f.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def load(path):return json.loads(Path(path).read_text())
def raw(desc):return f.frozen.raw(desc,HERE)

def array(desc,shape,dtype):
    if desc['shape']!=list(shape) or desc['dtype']!=np.dtype(dtype).str:raise ValueError('exact array descriptor')
    data=raw(desc)
    if len(data)!=int(np.prod(shape))*np.dtype(dtype).itemsize:raise ValueError('exact array bytes')
    return np.frombuffer(data,dtype=dtype).reshape(shape).copy()

def fork(receiver):
    result=Receiver();result.ref,result.rid,result.hud,result.last=receiver.ref,receiver.rid,receiver.hud,receiver.last
    return result

def predict_block(temporal,current,by,bx,mode):
    if type(mode)is not int or not 0<=mode<=3:raise ValueError('raster prediction mode')
    y,x=by*8,bx*8;top_available=by>0;left_available=bx>0
    top=(current[y-1,x:x+8].astype(np.int64)-temporal[y-1,x:x+8]) if top_available else np.zeros(8,np.int64)
    left=(current[y:y+8,x-1].astype(np.int64)-temporal[y:y+8,x-1]) if left_available else np.zeros(8,np.int64)
    if mode==0:correction=0
    elif mode==1:correction=top[None,:]
    elif mode==2:correction=left[:,None]
    else:
        denominator=8*(top_available+left_available)
        correction=0 if denominator==0 else (int(top.sum()+left.sum())+denominator//2)//denominator
    return np.clip(temporal[y:y+8,x:x+8].astype(np.int64)+correction,0,255).astype(np.int16)

def unique_predictors(temporal,current,by,bx):
    representatives=[];predictions=[]
    for mode in range(4):
        value=predict_block(temporal,current,by,bx,mode)
        if not any(np.array_equal(value,previous) for previous in predictions):
            representatives.append(mode);predictions.append(value)
    return representatives,predictions

class RankReader(rank.RankReader):
    def rank(self,count,by,bx):
        if type(count)is not int or not 1<=count<=4:raise ValueError('derived raster predictor menu size')
        if count==1:return 0
        base=(2*int(by>0)+int(bx>0))*12+(count-2)*3
        for step in range(count-1):
            context=base+step
            if not 0<=context<=44:raise ValueError('bounded availability context')
            before=self.reader.pos;bit=self.reader.decode(context)
            self.maximum_renorm=max(self.maximum_renorm,self.reader.pos-before)
            self.decisions+=1;self.contexts.add(context)
            if not bit:return step
        return count-1

def reconstruct_plane(temporal,coefficients,component,tables,safe):
    height,width=temporal.shape;bh,bw=height//8,width//8;mask=safe.reshape(-1)
    if coefficients.shape!=(bh*bw,8,8) or np.any(coefficients[mask]):raise ValueError('bounded hidden-zero coefficient plane')
    if not component or component[0]>3:raise ValueError('raster mode component dispatch')
    if component[0]==3:reader=RankReader(component);fallback=None
    else:
        reader=None;fallback=np.zeros(len(mask),np.uint8)
        fallback[~mask]=spatial.unpack_modes(component,int((~mask).sum()))
    current=np.empty_like(temporal);modes=np.zeros(len(mask),np.uint8);ranks=np.zeros(len(mask),np.uint8)
    menus=np.zeros(len(mask),np.uint8);events=0
    for by in range(bh):
        for bx in range(bw):
            index=by*bw+bx;y,x=by*8,bx*8
            if safe[by,bx]:current[y:y+8,x:x+8]=128;continue
            representatives,predictions=unique_predictors(temporal,current,by,bx);count=len(representatives)
            if reader is not None:
                chosen=reader.rank(count,by,bx);mode=rank.canonical_mode(representatives,chosen)
            else:
                mode=int(fallback[index])
                if mode not in representatives:raise ValueError('first canonical global-raster predictor')
                chosen=representatives.index(mode)
            menus[index]=count;ranks[index]=chosen;modes[index]=mode;events+=min(chosen+1,count-1)
            residual=m.ft.inverse(coefficients[index].astype(np.int64)*tables[index])
            current[y:y+8,x:x+8]=np.clip(residual+predictions[chosen],0,255).astype(np.int16)
    work=reader.finish() if reader is not None else None
    if work is not None:assert work['binary_decisions']==events
    return current,modes,ranks,dict(menu_counts=[int(np.count_nonzero(menus==n)) for n in range(1,5)],
        truncated_unary_decisions=events,arithmetic=work)

def parse(packet):
    """Validate new envelope, then share frozen identical coefficient grammar."""
    if type(packet)is not bytes or not OUTER.size+INNER.size+12<=len(packet)<=49152:raise ValueError('bounded immutable RR41')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('RR41 CRC')
    outer=list(OUTER.unpack_from(packet))
    if outer[0]!=b'RR41' or outer[8]!=PROFILE:raise ValueError('RR41 profile')
    nb,nh=outer[11:13]
    if nb<INNER.size+4 or nh<=0 or len(packet)!=OUTER.size+nb+nh+4:raise ValueError('RR41 exact lengths')
    inner=packet[OUTER.size:OUTER.size+nb];hud=packet[OUTER.size+nb:-4]
    if zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('GR41 CRC')
    fields=list(INNER.unpack_from(inner))
    if fields[0]!=b'GR41':raise ValueError('GR41 magic')
    # Only tags/magic are adapted for shared fixed syntax validation. Original
    # CRCs were checked first; no malformed checksum is repaired or ignored.
    fields[0]=b'TR39';converted_inner=seal(INNER.pack(*fields)+inner[INNER.size:-4])
    outer[0]=b'RP39';outer[8]=rank.PROFILE
    converted=seal(OUTER.pack(*outer)+converted_inner+hud)
    return rank.parse(converted)

class Receiver:
    def __init__(self):self.ref=None;self.rid=m.NO_REF;self.hud=None;self.last=-1
    def receive(self,packet):
        meta=parse(packet);key=meta['key']
        if meta['frame_id']<=self.last:raise ValueError('RR41 monotonic publication')
        if key:temporal=tuple(np.full(shape,128,np.int16) for shape in ((480,720),(240,360),(240,360)))
        else:
            if self.ref is None or self.rid!=meta['reference_id'] or m.C.reference_tag(self.ref)!=meta['reference_tag']:raise ValueError('RR41 actual committed reference')
            temporal=self.ref
        pixels=[];modes=[];ranks=[];work=[]
        for plane,(base,coeff,component,safe) in enumerate(zip(temporal,meta['coefficients'],meta['mode_payloads'],f.safe_blocks(),strict=True)):
            value,mode,rank_values,record=reconstruct_plane(base,coeff,component,m.roi.block_tables(meta['qmap'],720,480,plane),safe)
            pixels.append(value);modes.append(mode);ranks.append(rank_values);work.append(record)
        pixels=tuple(pixels)
        if m.C.reference_tag(pixels)!=meta['output_tag']:raise ValueError('RR41 committed output binding')
        patches,_=f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,expected_reference_id=None if key else self.rid)
        meta.update(modes=tuple(modes),ranks=tuple(ranks),rank_work=work)
        self.ref,self.rid,self.hud,self.last=pixels,meta['frame_id'],patches,meta['frame_id']
        return pixels,patches,meta

def verify_host_oracle(source,temporal,control,tables,safe,modes,coefficients,costs):
    height,width=source.shape;bh,bw=height//8,width//8;mask=safe.reshape(-1)
    current=np.full_like(source,-777);indices=[];proposals=[];evaluated=frontiers=0
    menus=np.zeros(len(mask),np.uint8);rank_options=np.zeros((len(mask),4),np.int64)
    assert np.all(costs[mask]==0)
    for by in range(bh):
        for bx in range(bw):
            index=by*bw+bx;y,x=by*8,bx*8;frontiers+=1
            # Explicit prefix equality establishes that a precomputed host
            # target does not leak future pixels into the decoder's context.
            if by>0:np.testing.assert_array_equal(current[y-1,x:x+8],control[y-1,x:x+8])
            if bx>0:np.testing.assert_array_equal(current[y:y+8,x-1],control[y:y+8,x-1])
            if safe[by,bx]:
                assert modes[index]==0 and not np.any(coefficients[index])
                np.testing.assert_array_equal(control[y:y+8,x:x+8],128)
                current[y:y+8,x:x+8]=128;continue
            causal=np.stack([predict_block(temporal,current,by,bx,mode) for mode in range(4)])
            host=np.stack([predict_block(temporal,control,by,bx,mode) for mode in range(4)])
            np.testing.assert_array_equal(causal,host)
            canonical,rank_bits=signal.predictor_menu(causal)
            unique=[causal[mode] for mode in range(4) if canonical[mode]]
            menus[index]=len(unique)
            rank_options[index]=[next(i for i,value in enumerate(unique) if np.array_equal(causal[mode],value)) for mode in range(4)]
            original=source[y:y+8,x:x+8].astype(np.int64)
            quant=m.ft.round_quantize(m.ft.forward(original-causal),tables[index]).astype(np.int16)
            assert not np.any(np.abs(quant.astype(np.int32))>m.ft.MAX_COEFF)
            pixels=np.clip(m.ft.inverse(quant.astype(np.int64)*tables[index])+causal,0,255).astype(np.int16)
            target=pixels[0];np.testing.assert_array_equal(target,control[y:y+8,x:x+8])
            equal=np.all(pixels==target,axis=(1,2));eligible=equal&canonical.astype(bool)
            errors=np.square(original-pixels).sum(axis=(1,2))
            for column,expected in ((0,errors),(2,rank_bits),(3,canonical),(4,equal.astype(np.int64)),(5,eligible.astype(np.int64))):
                np.testing.assert_array_equal(costs[index,:,column],expected)
            scores=costs[index,:,1]+rank_bits;scores[~eligible]=np.iinfo(np.int64).max
            chosen=int(np.argmin(scores));assert modes[index]==chosen and eligible[0]
            np.testing.assert_array_equal(coefficients[index],quant[chosen]);np.testing.assert_array_equal(pixels[chosen],target)
            current[y:y+8,x:x+8]=pixels[chosen]
            indices.append(index);proposals.append(quant);evaluated+=4
    joined=np.concatenate(proposals);bits=signal.fine_bits(joined).reshape(-1,4)
    np.testing.assert_array_equal(costs[np.array(indices),:,1],bits)
    for index in sorted({0,len(joined)//2,len(joined)-1}):assert signal.scalar_fine_bits(joined[index])==bits.reshape(-1)[index]
    np.testing.assert_array_equal(current,control)
    return current,evaluated,frontiers,menus,rank_options

def verify_trial(payload,temporal,committed,safe,expected_modes):
    bh,bw=safe.shape;mask=safe.reshape(-1);menus=np.zeros(mask.size,np.uint8);ranks=np.zeros_like(menus)
    reader=RankReader(payload)
    for by in range(bh):
        for bx in range(bw):
            index=by*bw+bx
            if safe[by,bx]:continue
            representatives,_=unique_predictors(temporal,committed,by,bx)
            value=reader.rank(len(representatives),by,bx)
            assert rank.canonical_mode(representatives,value)==expected_modes[index]
            menus[index]=len(representatives);ranks[index]=value
    work=reader.finish();work.update(menu_counts=[int(np.count_nonzero(menus==n)) for n in range(1,5)],
        rank_counts=[int(np.count_nonzero((ranks==r)&~mask)) for r in range(4)])
    return menus,ranks,work

def check_plane_work(record,independent,coeff_record,mode_payload,old_modes,candidate,coefficient_payload,plane):
    assert record['plane']==plane and record['old_mode_bytes']==len(old_modes)
    assert record['rank_payload_bytes']==len(candidate) and record['selected_mode_bytes']==len(mode_payload)
    chosen=len(candidate)<len(old_modes);assert record['rank_selected']is chosen
    assert mode_payload==(candidate if chosen else old_modes)
    assert record['arithmetic_bits']==independent['arithmetic_bits']
    for key in ('binary_decisions','probability_products','renorm_steps','max_renorm_per_bit'):
        assert record[key]==independent[key]
    assert record['context_ids']==independent['contexts_used']
    assert record['menu_counts']==independent['menu_counts'] and record['rank_counts']==independent['rank_counts']
    assert record['logical_probability_state_bytes']==88 and record['interval_bits']==16 and record['probability_bits']==8
    assert record['multiply_operand_bits']==[17,8]
    assert record['coefficient_bytes']==len(coefficient_payload)==coeff_record['selected']
    assert record['implicit_selected']is coeff_record['implicit']
    assert record['fullgrid_payload_bytes']==coeff_record['full'] and record['compact_payload_bytes']==coeff_record['compact']

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-raster-v41'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    assert data['profile']['profile_tag']==PROFILE.hex() and data['profile']['complete_memory_fit_proven']is False
    assert data['profile']['logical_top_edge_int16_bytes']==2880 and data['profile']['logical_left_edge_int16_bytes']==48
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..'not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    old_rank=load(HERE.parent/'python-game-mode-rank-v39-study/results.json')
    old_spatial=load(HERE.parent/'python-game-spatial-v38-study/results.json');inputs=load(f.n.V24/'results.json')['inputs']
    fixtures={}
    for item in old_spatial['synthetic_inputs']:
        packed=spatial.array(item['source'],(518400,),'u1')
        planes=(packed[:345600].reshape(480,720).astype(np.int16),packed[345600:432000].reshape(240,360).astype(np.int16),packed[432000:].reshape(240,360).astype(np.int16))
        fixtures[item['scene']]=(planes,spatial.array(item['original'],(480,720),'<u2'))
    keys=[(c['scene'],c['kind']) for c in data['cases']]
    assert len(keys)==len(set(keys))==5 and set(keys)=={(c['scene'],'main') for c in inputs}|{(scene,'synthetic') for scene in fixtures}
    frames=frontiers=proposed_blocks=trial_planes=accepted=old_content_matches=0
    for case in data['cases']:
        count=12 if case['kind']=='main' else 1
        assert [r['id'] for r in case['rows']]==list(range(count)) and all(type(r['id'])is int for r in case['rows'])
        golden=next(c for c in old_rank['cases'] if c['scene']==case['scene'] and c['kind']==case['kind'] and c['policy']=='mode0control')
        live=Receiver();old_live=rank.Receiver();checks=[]
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
            control_wire=raw(row['control']['packet']);candidate_wire=raw(row['candidate']['packet']);selected_wire=raw(row['packet'])
            before=(live.ref,live.hud,live.rid,live.last)
            cb,pb=fork(live),fork(live)
            control,ch,cm=cb.receive(control_wire);candidate,ph,pm=pb.receive(candidate_wire)
            assert live.ref is before[0] and live.hud is before[1] and (live.rid,live.last)==before[2:]
            if not key:assert m.C.reference_tag(live.ref)==incoming
            for a,b in zip(control,candidate,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(ch,ph,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            for meta in (cm,pm):
                assert (meta['key'],meta['frame_id'],meta['reference_id'],meta['reference_tag'])==(key,fid,rid,incoming)
                np.testing.assert_array_equal(meta['qmap'],m.roi.declared_map(720,480,f.n.ROIS,8,16))
            assert cm['output_tag']==pm['output_tag']
            historical=f.frozen.raw(golden['rows'][fid]['packet'],HERE.parent/'python-game-mode-rank-v39-study')
            gm=rank.parse(historical);old_pixels,old_hud,_=old_live.receive(historical)
            assert control_wire[:4]==b'RR41' and historical[:4]==b'RP39'
            assert cm['plane_payloads']==gm['plane_payloads'] and cm['qmap_bytes']==gm['qmap_bytes'] and cm['hud']==gm['hud']
            assert cm['reference_tag']==gm['reference_tag'] and cm['output_tag']==gm['output_tag']
            assert row['old_mode0_content_exact']is True;old_content_matches+=1
            for a,b in zip(control,old_pixels,strict=True):np.testing.assert_array_equal(a,b)
            # The host's full-image proposal is independently reproduced from
            # a strictly causal sentinel prefix, including all hidden blocks.
            eligible_count=selected_nonzero=0
            for plane,(src_plane,base,target,safe,modes,coeff) in enumerate(zip(source,temporal,control,f.safe_blocks(),pm['modes'],pm['coefficients'],strict=True)):
                costs=array(row['candidate_cost_arrays'][plane],(safe.size,4,6),'<i8')
                value,nproposed,nfrontiers,menus,options=verify_host_oracle(src_plane,base,target,m.roi.block_tables(pm['qmap'],720,480,plane),safe,modes,coeff,costs)
                np.testing.assert_array_equal(value,candidate[plane]);proposed_blocks+=nproposed;frontiers+=nfrontiers
                np.testing.assert_array_equal(array(row['eligibility_arrays'][plane],(safe.size,4),'u1'),costs[:,:,5])
                np.testing.assert_array_equal(array(row['menus'][plane],(safe.size,),'u1'),menus)
                stored_options=array(row['rank_options'][plane],(safe.size,4),'<i8')
                np.testing.assert_array_equal(stored_options[~safe.reshape(-1)],options[~safe.reshape(-1)])
                eligible_count+=int(costs[:,1:,5].sum());selected_nonzero+=int(np.count_nonzero(modes))
            for role,variant,pixels,meta in (('control',row['control'],control,cm),('candidate',row['candidate'],candidate,pm)):
                entropy_records=spatial.verify_coeff_entropy(meta)
                for plane,(base,committed,safe,modes,trial,record,coeff_record) in enumerate(zip(temporal,pixels,f.safe_blocks(),meta['modes'],variant['rank_trials'],variant['plane_work'],entropy_records,strict=True)):
                    np.testing.assert_array_equal(array(variant['mode_arrays'][plane],(safe.size,),'u1'),modes)
                    if role=='control':assert not np.any(modes)
                    payload=raw(trial['rank_packet']);menus,ranks,independent=verify_trial(payload,base,committed,safe,modes)
                    np.testing.assert_array_equal(array(trial['menus'],(safe.size,),'u1'),menus)
                    np.testing.assert_array_equal(array(trial['ranks'],(safe.size,),'u1'),ranks)
                    np.testing.assert_array_equal(meta['ranks'][plane],ranks)
                    assert meta['rank_work'][plane]['menu_counts']==independent['menu_counts']
                    assert meta['rank_work'][plane]['truncated_unary_decisions']==independent['binary_decisions']
                    old_mode_payload=spatial.canonical_modes(modes[~safe.reshape(-1)])
                    check_plane_work(record,independent,coeff_record,meta['mode_payloads'][plane],old_mode_payload,payload,meta['plane_payloads'][plane],plane)
                    trial_planes+=1
            use_candidate=exact.candidate_wins(len(control_wire),len(candidate_wire));kind='candidate' if use_candidate else 'control'
            assert row['selected_kind']==kind and selected_wire==(candidate_wire if use_candidate else control_wire)
            assert (row['control_bytes'],row['candidate_bytes'],row['complete_bytes'])==(len(control_wire),len(candidate_wire),len(selected_wire))
            work=row['work'];assert work['selection']==kind
            assert (work['control_bytes'],work['candidate_bytes'],work['selected_bytes'])==(len(control_wire),len(candidate_wire),len(selected_wire))
            assert work['host_precomputed_mode0_target']is True and work['exact_full_block_eligibility']is True and work['global_raster_context']is True
            assert work['eligible_nonzero_modes']==eligible_count and work['candidate_nonzero_modes']==selected_nonzero
            assert work['logical_top_edge_int16_bytes']==2880 and work['logical_left_edge_int16_bytes']==48 and work['complete_FPGA_memory_fit_proven']is False
            assert work['source_candidate_forward_mode0_reused']is True
            assert math.isfinite(work['encode_pair_ms']) and work['encode_pair_ms']>0
            selected,patches,sm=live.receive(selected_wire)
            for a,b,c,d in zip(selected,control,candidate,old_pixels,strict=True):
                np.testing.assert_array_equal(a,b);np.testing.assert_array_equal(a,c);np.testing.assert_array_equal(a,d)
            for a,b in zip(patches,old_hud,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            assert live.rid==old_live.rid==fid and live.last==old_live.last==fid
            assert m.C.reference_tag(live.ref)==m.C.reference_tag(old_live.ref)
            expected_patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in f.n.RECTS)
            for a,b in zip(patches,expected_patches,strict=True):np.testing.assert_array_equal(a['words'],b)
            quality,display=f.metric(selected,original,patches)
            assert quality==row['hybrid']==golden['rows'][fid]['hybrid'] and display==row['display_sha256']==golden['rows'][fid]['display_sha256']
            assert m.C.reference_tag(selected).hex()==row['normalized_tag']==golden['rows'][fid]['normalized_tag']
            assert math.isfinite(row['receiver_ms']) and row['receiver_ms']>0
            accepted+=use_candidate;frames+=1;checks.append(row)
        s=case['summary'];ctrl=sum(r['control_bytes'] for r in checks);cand=sum(r['candidate_bytes'] for r in checks);chosen=sum(r['complete_bytes'] for r in checks)
        assert s['frames']==count and (s['control_complete_bytes'],s['candidate_complete_bytes'],s['complete_bytes'])==(ctrl,cand,chosen)
        assert s['saved_bytes']==ctrl-chosen and math.isclose(s['percent_saved'],100*(ctrl-chosen)/ctrl,abs_tol=1e-12)
        assert s['selected_candidates']==sum(r['selected_kind']=='candidate' for r in checks)
        assert s['candidate_larger_frames']==sum(r['candidate_bytes']>r['control_bytes'] for r in checks) and s['candidate_tie_frames']==sum(r['candidate_bytes']==r['control_bytes'] for r in checks)
        assert s['maximum_complete_bytes']==max(r['complete_bytes'] for r in checks) and s['maximum_control_bytes']==max(r['control_bytes'] for r in checks)
        assert s['eligible_nonzero_modes']==sum(r['work']['eligible_nonzero_modes'] for r in checks) and s['candidate_nonzero_modes']==sum(r['work']['candidate_nonzero_modes'] for r in checks)
        assert s['active_mse']==sum(r['hybrid']['active_squared_error'] for r in checks)/sum(r['hybrid']['active_channel_samples'] for r in checks)
        assert math.isclose(s['mean_paid_pair_ms'],sum(r['work']['encode_pair_ms'] for r in checks)/count,abs_tol=1e-10)
    assert frames==old_content_matches==27 and frontiers==218700 and trial_planes==162
    print(json.dumps(dict(exact_selected_frames=frames,old_mode0_content_matches=old_content_matches,
        independently_recomputed_candidate_blocks=proposed_blocks,host_causal_frontiers_checked=frontiers,
        actual_rank_trial_planes=trial_planes,accepted_candidates=accepted,full_future_reference_equality=True,
        source_pins=len(data['source_sha256']),new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
