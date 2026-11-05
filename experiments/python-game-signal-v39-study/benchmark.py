"""Own-reference fine-bit signal policies; every actual RP39 frame retained."""
import json,platform,time
import numpy as np
import helpers as h
model=h.module('signal39_benchmark_model',h.HERE/'model.py')
decoder=h.module('signal39_frozen_RP39_decoder',h.HERE.parent/'python-game-mode-rank-v39-study/verify.py')
POLICIES=('mode0control','lambda1','lambda4','lambda16')

def array_blob(a):return dict(**h.blob(a.tobytes()),shape=list(a.shape),dtype=a.dtype.str)
def summary(rows):
    sse=sum(r['hybrid']['active_squared_error']for r in rows);samples=sum(r['hybrid']['active_channel_samples']for r in rows)
    return dict(frames=len(rows),complete_bytes=sum(r['complete_bytes']for r in rows),maximum_complete_bytes=max(r['complete_bytes']for r in rows),
        mode_bytes=sum(r['mode_bytes']for r in rows),coefficient_bytes=sum(r['work']['coefficient_bytes']for r in rows),
        active_mse=sse/samples,peak_frame_mse=max(r['hybrid']['active_mse']for r in rows),
        mean_encode_ms=sum(r['work']['encode_ms']for r in rows)/len(rows),all_frames_cap_fit=all(r['complete_bytes']<=49152 for r in rows),
        mode_counts=[sum(p['mode_counts'][mode]for r in rows for p in r['work']['planes'])for mode in range(4)],
        nominal_Mbps_at30=sum(r['complete_bytes']for r in rows)*240/len(rows)/1e6)

def frame(source,original,hud,policy,fid,state,source_id,old_control):
    if fid%24==0:state.update(ref=None,rid=h.m.NO_REF)
    key=state['ref']is None;reftag=bytes(16)if key else h.m.C.reference_tag(state['ref'])
    q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    packet,pixels,work,modes,costs,sp38,rank_trials=model.encode_planes(source,state['ref'],q,hud,policy=policy,frame_id=fid,reference_id=state['rid'])
    start=time.perf_counter_ns();decoded,parts,meta=state['rx'].receive(packet);receiver_ms=(time.perf_counter_ns()-start)/1e6
    for a,b in zip(decoded,pixels,strict=True):np.testing.assert_array_equal(a,b)
    for actual,expected in zip(meta['modes'],modes,strict=True):np.testing.assert_array_equal(actual,expected)
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(decoded)),tuple(v['words']for v in parts))
    quality=h.n.metric(original,display)
    row=dict(id=fid,key=key,reference_id=state['rid'],source_sha256=h.digest(b''.join(v.astype('u1').tobytes()for v in source)),source_id=source_id,
        packet=h.blob(packet),SP38_packet=h.blob(sp38),hud_packet=h.blob(hud),complete_bytes=len(packet),mode_bytes=sum(len(v)for v in meta['mode_payloads']),
        reference_tag=reftag.hex(),normalized_tag=h.m.C.reference_tag(decoded).hex(),display_sha256=h.n.digest(display),hybrid=quality,work=work,
        mode_arrays=[array_blob(a)for a in modes],candidate_cost_arrays=[array_blob(a)for a in costs],receiver_ms=receiver_ms,
        rank_trials=[dict(rank_packet=h.blob(t['rank_packet']),menus=array_blob(t['menus']),ranks=array_blob(t['ranks']))for t in rank_trials])
    if policy=='mode0control':
        assert packet==h.raw(old_control['packet'],h.HERE.parent/'python-game-mode-rank-v39-study'),'fixedcontrolgoldenpacket'
        row['old_control_packet_exact']=True
    if len(packet)>49152:raise ValueError('completeRP39cap')
    state.update(ref=decoded,rid=fid)
    return row

def main():
    before=h.pins();spatial_folder=h.HERE.parent/'python-game-spatial-v38-study';prior=h.load(spatial_folder/'results.json')
    old_rank=h.load(h.HERE.parent/'python-game-mode-rank-v39-study/results.json');inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    for inp in inputs:
        hc=next(c for c in huds if c['scene']==inp['scene']);oldcase=next(c for c in old_rank['cases']if c['scene']==inp['scene']and c['policy']=='mode0control')
        states={p:dict(ref=None,rid=h.m.NO_REF,rx=decoder.Receiver())for p in POLICIES};rows={p:[]for p in POLICIES}
        for src,hu,golden in zip(inp['rows'][:12],hc['rows'][:12],oldcase['rows'],strict=True):
            source=h.n.source(src);original=h.n.original(src);hud=h.raw(hu['packet'],h.HUD)
            rotation=src['id']%4;order=POLICIES[rotation:]+POLICIES[:rotation]
            for policy in order:
                rows[policy].append(frame(source,original,hud,policy,src['id'],states[policy],dict(scene=inp['scene'],id=src['id'],kind='main'),golden))
            print(json.dumps(dict(scene=inp['scene'],frame=src['id'])),flush=True)
        for policy in POLICIES:
            case=dict(scene=inp['scene'],kind='main',policy=policy,lambda_value=0 if policy=='mode0control'else int(policy[6:]),rows=rows[policy],summary=summary(rows[policy]));cases.append(case)
            print(json.dumps({k:v for k,v in case.items()if k!='rows'}),flush=True)
    for synth in prior['synthetic_inputs']:
        flat=np.frombuffer(h.raw(synth['source'],spatial_folder),np.uint8)
        source=(flat[:345600].reshape(480,720).astype(np.int16),flat[345600:432000].reshape(240,360).astype(np.int16),flat[432000:].reshape(240,360).astype(np.int16))
        original=np.frombuffer(h.raw(synth['original'],spatial_folder),'<u2').reshape(480,720).copy();hud=h.raw(synth['hud_packet'],spatial_folder)
        golden=next(c for c in old_rank['cases']if c['scene']==synth['scene']and c['policy']=='mode0control')['rows'][0]
        for policy in POLICIES:
            row=frame(source,original,hud,policy,0,dict(ref=None,rid=h.m.NO_REF,rx=decoder.Receiver()),dict(scene=synth['scene'],id=0,kind='synthetic'),golden)
            case=dict(scene=synth['scene'],kind='synthetic',policy=policy,lambda_value=0 if policy=='mode0control'else int(policy[6:]),rows=[row],summary=summary([row]));cases.append(case)
            print(json.dumps({k:v for k,v in case.items()if k!='rows'}),flush=True)
    assert h.pins()==before
    result=dict(schema='gamebub-signal-v39',source_sha256=before,cases=cases,
        physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        profile=dict(wire='unchangedRP39/TR39',policies=list(POLICIES),lambdas=[0,1,4,16],coefficient_parameter_bits=32,raw_coefficient_bits=1024,
            cost_tensor_fields=['sourceYUVSSE','unroundedCoefficientBits','rawTruncatedUnaryRankDecisions','canonicalFirstPredictor'],
            cost_tensor_dtype='<i8',opaque_geometry='frozenSP38',residual_RDO_pruning=False),
        scope=['Actual108RP39frames, independentownacceptedcausalhistoriesforall4policies, same2reused12framegameprefixes+3synthetics.',
               'All4modecandidateQ14/quant/inverse/proxycostsarepaidandarchivedforALLpoliciesincludingforcedmode0researchcontrol. Aliasesareexcludedfromargmin; lowestcanonicalmodewinsties.',
               'ScoreSSE+lambda*(unroundedDC/ACminRicebits+32parameters cappedRAW1024 +rawtruncatedrankdecisioncount). ThisisNOTactualadaptivearithmetic/full-plane/modefallbackcost.',
               'ProofsenderconstructsSP38thenpaidfrozenRP39transcodeandchecksoutput. Allintermediatesactualpacketsretained;encodeclockincludesbothpathsplusduplicateproofreconstruction.',
               'Fixtures/source/HUDreadsorgeneration,archiveIO,quality/hash/assertions,independentreceiver,network/displayexcluded. Singleclockperframe,nospeedor30fpsclaim.',
               '27mode0controlpacketsbyteidenticalpriorRP39controls. Newcandidatepolicieschangechoices/references/quality; alltradeoffsreported,noglobalqualityguardorforcedcompressionwin.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
