"""Actual global-raster controls/candidates and causal selected-byte guard."""
import json,platform,time
import numpy as np
import helpers as h
model=h.module('raster41_benchmark_model',h.HERE/'model.py')
decoder=h.module('raster41_independent_receiver',h.HERE/'verify.py')
old_decoder=h.module('raster41_frozen_RP39_receiver',h.HERE.parent/'python-game-mode-rank-v39-study/verify.py')

def array_blob(a):return dict(**h.blob(a.tobytes()),shape=list(a.shape),dtype=a.dtype.str)
def trials(items):return [dict(rank_packet=h.blob(t['rank_packet']),menus=array_blob(t['menus']),ranks=array_blob(t['ranks']))for t in items]
def fork(rx):
    other=decoder.Receiver();other.ref,other.rid,other.hud,other.last=rx.ref,rx.rid,rx.hud,rx.last;return other
def content(packet):
    outer=model.OUTER.unpack_from(packet);inner=packet[model.OUTER.size:model.OUTER.size+outer[11]];fields=model.INNER.unpack_from(inner)
    q=inner[model.INNER.size:model.INNER.size+fields[10]];pos=model.INNER.size+fields[10]+sum(fields[11:14]);coeff=[]
    for length in fields[14:17]:coeff.append(inner[pos:pos+length]);pos+=length
    assert pos==len(inner)-4
    return q,coeff,packet[model.OUTER.size+outer[11]:-4],outer[9],outer[10]
def summary(rows):
    old=sum(r['control_bytes']for r in rows);candidate=sum(r['candidate_bytes']for r in rows);selected=sum(r['complete_bytes']for r in rows)
    return dict(frames=len(rows),control_complete_bytes=old,candidate_complete_bytes=candidate,complete_bytes=selected,saved_bytes=old-selected,
        percent_saved=100*(old-selected)/old,selected_candidates=sum(r['selected_kind']=='candidate'for r in rows),
        candidate_larger_frames=sum(r['candidate_bytes']>r['control_bytes']for r in rows),candidate_tie_frames=sum(r['candidate_bytes']==r['control_bytes']for r in rows),
        maximum_complete_bytes=max(r['complete_bytes']for r in rows),maximum_control_bytes=max(r['control_bytes']for r in rows),
        eligible_nonzero_modes=sum(r['work']['eligible_nonzero_modes']for r in rows),candidate_nonzero_modes=sum(r['work']['candidate_nonzero_modes']for r in rows),
        active_mse=sum(r['hybrid']['active_squared_error']for r in rows)/sum(r['hybrid']['active_channel_samples']for r in rows),
        mean_paid_pair_ms=sum(r['work']['encode_pair_ms']for r in rows)/len(rows))

def frame(source,original,hud,fid,state,golden,identity):
    reference=None if fid%24==0 else state['ref'];rid=h.m.NO_REF if reference is None else state['rid']
    q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    result=model.encode_pair(source,reference,q,hud,frame_id=fid,reference_id=rid)
    control=result['control'];candidate=result['candidate'];cw=control['packet'];pw=candidate['packet'];wire=result['packet'];target=result['planes']
    oldpacket=h.raw(golden['packet'],h.HERE.parent/'python-game-mode-rank-v39-study')
    assert content(cw)==content(oldpacket),'mode0 coefficient/qmap/HUD/reference semantics'
    oldpixels,oldhud,_=state['old_rx'].receive(oldpacket)
    for a,b in zip(target,oldpixels,strict=True):np.testing.assert_array_equal(a,b)
    crx,prx=fork(state['rx']),fork(state['rx'])
    cp,ch,cm=crx.receive(cw);pp,ph,pm=prx.receive(pw)
    start=time.perf_counter_ns();pixels,parts,meta=state['rx'].receive(wire);receive_ms=(time.perf_counter_ns()-start)/1e6
    for values in zip(target,cp,pp,pixels,strict=True):
        for value in values[1:]:np.testing.assert_array_equal(value,values[0])
    for a,b,c,d in zip(parts,ch,ph,oldhud,strict=True):
        for other in(b,c,d):np.testing.assert_array_equal(a['words'],other['words'])
    # Encoder provenance is independent of the evolving verifier: future
    # encoder reference and metrics use OWNED mode0 oracle, while actual
    # decoder equivalence is asserted above on every selected/trial packet.
    patches=tuple(original[y:y+hh,x:x+w]for x,y,w,hh in h.n.RECTS)
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(target)),patches);quality=h.n.metric(original,display);tag=h.n.digest(display)
    assert quality==golden['hybrid']and tag==golden['display_sha256']
    def variant(v):return dict(packet=h.blob(v['packet']),rank_trials=trials(v['rank_trials']),mode_arrays=[array_blob(a)for a in v['mode_arrays']],plane_work=v['plane_work'])
    row=dict(id=fid,key=reference is None,reference_id=rid,source_sha256=h.digest(b''.join(v.astype('u1').tobytes()for v in source)),source_id=identity,
        packet=h.blob(wire),control=variant(control),candidate=variant(candidate),selected_kind=result['work']['selection'],
        control_bytes=len(cw),candidate_bytes=len(pw),complete_bytes=len(wire),reference_tag=(bytes(16)if reference is None else h.m.C.reference_tag(reference)).hex(),
        normalized_tag=h.m.C.reference_tag(target).hex(),display_sha256=tag,hybrid=quality,work=result['work'],receiver_ms=receive_ms,
        old_mode0_content_exact=True,candidate_cost_arrays=[array_blob(p['costs'])for p in result['proposals']],
        eligibility_arrays=[array_blob(p['eligibility'])for p in result['proposals']],
        menus=[array_blob(p['menus'])for p in result['proposals']],rank_options=[array_blob(p['rank_options'])for p in result['proposals']])
    state.update(ref=target,rid=fid);return row

def main():
    before=h.pins();old=h.load(h.HERE.parent/'python-game-mode-rank-v39-study/results.json');inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    def state():return dict(ref=None,rid=h.m.NO_REF,rx=decoder.Receiver(),old_rx=old_decoder.Receiver())
    for inp in inputs:
        hc=next(c for c in huds if c['scene']==inp['scene']);gold=next(c for c in old['cases']if c['scene']==inp['scene']and c['policy']=='mode0control');st=state();rows=[]
        for src,hu,golden in zip(inp['rows'][:12],hc['rows'][:12],gold['rows'],strict=True):
            rows.append(frame(h.n.source(src),h.n.original(src),h.raw(hu['packet'],h.HUD),src['id'],st,golden,dict(scene=inp['scene'],kind='main',id=src['id'])))
            print(json.dumps(dict(scene=inp['scene'],frame=src['id'],selected=rows[-1]['selected_kind'],bytes=rows[-1]['complete_bytes'])),flush=True)
        case=dict(scene=inp['scene'],kind='main',rows=rows,summary=summary(rows));cases.append(case);print(json.dumps(case['summary']),flush=True)
    sourcefolder=h.HERE.parent/'python-game-spatial-v38-study';source=h.load(sourcefolder/'results.json')
    for inp in source['synthetic_inputs']:
        flat=np.frombuffer(h.raw(inp['source'],sourcefolder),np.uint8)
        planes=(flat[:345600].reshape(480,720).astype(np.int16),flat[345600:432000].reshape(240,360).astype(np.int16),flat[432000:].reshape(240,360).astype(np.int16))
        original=np.frombuffer(h.raw(inp['original'],sourcefolder),'<u2').reshape(480,720).copy();hud=h.raw(inp['hud_packet'],sourcefolder)
        golden=next(c for c in old['cases']if c['scene']==inp['scene']and c['policy']=='mode0control')['rows'][0]
        row=frame(planes,original,hud,0,state(),golden,dict(scene=inp['scene'],kind='synthetic',id=0))
        case=dict(scene=inp['scene'],kind='synthetic',rows=[row],summary=summary([row]));cases.append(case);print(json.dumps(dict(scene=inp['scene'],summary=case['summary'])),flush=True)
    assert h.pins()==before
    result=dict(schema='gamebub-raster-v41',source_sha256=before,cases=cases,physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        profile=dict(magic='RR41',inner_magic='GR41',profile_tag=model.PROFILE.hex(),outer_format=model.OUTER.format,inner_format=model.INNER.format,
            predictor_order='GLOBALblockraster;topiffby>0,leftiffbx>0',rank_context='availabilityposition*12+(N-2)*3+decision<=44',
            cost_tensor_fields=['sourceYUVSSE','fineCoefficientBits','rawRankDecisions','canonicalFirst','exactMode0Pixels','eligible'],
            logical_top_edge_int16_bytes=2880,logical_left_edge_int16_bytes=48,complete_memory_fit_proven=False),
        scope=['NewGLOBALspatialprofileRR41/GR41. Actual27selectedframesand54control/candidatetrialsplusranklosers/costs/eligibilityretained.',
               'HOSTcomputeswholemode0canonicaltargetonce, thenvectorizesallcandidatepredictorsfromcausalNEIGHBORpositionsinthatknownimage. Everyeligibleoutputblockmustexactlyequalthattarget.',
               'DECODERmustglobalrasterdecodefromalreadyreconstructedprefixonly; nooracle/futurepixelread. Independentdecodercomparescausalfrontierandhostoraclepredictionsateveryblock.',
               'Bothactualnewprofilecontrols/candidatesdecodedfromforkedselectedstate;selecteddecoderadvancesonlyselectedpacket. Encoderfuturestateandmetricsderiveownedmode0oracleandassertdecoderidentity.',
               'OldRP39mode0 coefficientpayload/qmap/HUD/referencebytesandfullYUV/RGBqualityunchanged; wiremagic/profiledifferent, nocross-profilebytegoldenclaim.',
               'Wholeactualpacketguardstrictsmallertiescontrol. Paidsourcepairclocksincludeoracleforward/inverse,allcandidateproposals,allentropy/ranktrialsandbothwrappers;fixtures/archive/metrics/independentreceivers/network/displayexcluded.',
               'Logicalresidualedgecache2880Btop+48BleftdoesNOTincludecompleteframebuffers/coeffpayload/rank/DSP/scratch/transportorproveFPGAfit. Same27reusedinputs,nofreshHEVCAV1orhardware30fpsproof.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
