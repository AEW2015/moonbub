"""Actual full-reference exactness and strict packet choice over27 fixtures."""
import json,platform,time
import numpy as np
import helpers as h
model=h.module('exact40_benchmark_model',h.HERE/'model.py')
decoder=h.module('exact40_frozen_RP39_decoder',h.HERE.parent/'python-game-mode-rank-v39-study/verify.py')

def array_blob(a):return dict(**h.blob(a.tobytes()),shape=list(a.shape),dtype=a.dtype.str)
def trials(items):return [dict(rank_packet=h.blob(t['rank_packet']),menus=array_blob(t['menus']),ranks=array_blob(t['ranks']))for t in items]
def fork(rx):
    other=decoder.Receiver();other.ref,other.rid,other.hud,other.last=rx.ref,rx.rid,rx.hud,rx.last;return other
def summary(rows):
    old=sum(r['control_bytes']for r in rows);candidate=sum(r['candidate_bytes']for r in rows);selected=sum(r['complete_bytes']for r in rows)
    return dict(frames=len(rows),control_complete_bytes=old,candidate_complete_bytes=candidate,complete_bytes=selected,
        saved_bytes=old-selected,percent_saved=100*(old-selected)/old,selected_candidates=sum(r['selected_kind']=='candidate'for r in rows),
        candidate_larger_frames=sum(r['candidate_bytes']>r['control_bytes']for r in rows),candidate_tie_frames=sum(r['candidate_bytes']==r['control_bytes']for r in rows),
        maximum_complete_bytes=max(r['complete_bytes']for r in rows),maximum_control_bytes=max(r['control_bytes']for r in rows),
        eligible_nonzero_modes=sum(r['work']['eligible_nonzero_modes']for r in rows),candidate_nonzero_modes=sum(r['work']['candidate_nonzero_modes']for r in rows),
        active_mse=sum(r['hybrid']['active_squared_error']for r in rows)/sum(r['hybrid']['active_channel_samples']for r in rows),
        mean_paid_pair_ms=sum(r['work']['encode_pair_ms']for r in rows)/len(rows))

def frame(source,original,hud,fid,rx,golden,identity):
    reference=None if fid%24==0 else rx.ref;rid=h.m.NO_REF if reference is None else rx.rid
    q=h.m.roi.declared_map(720,480,h.n.ROIS,8,16)
    result=model.encode_pair(source,reference,q,hud,frame_id=fid,reference_id=rid)
    control=result['control'];candidate=result['candidate'];control_wire=control['packet'];candidate_wire=candidate['packet'];wire=result['packet']
    assert control_wire==h.raw(golden['packet'],h.HERE.parent/'python-game-mode-rank-v39-study'),'mode0 reference golden'
    control_rx,candidate_rx=fork(rx),fork(rx)
    control_pixels,control_hud,control_meta=control_rx.receive(control_wire)
    candidate_pixels,candidate_hud,candidate_meta=candidate_rx.receive(candidate_wire)
    start=time.perf_counter_ns();pixels,parts,meta=rx.receive(wire);receive_ms=(time.perf_counter_ns()-start)/1e6
    for values in zip(pixels,control_pixels,candidate_pixels,result['planes'],strict=True):
        for value in values[1:]:np.testing.assert_array_equal(value,values[0])
    for a,b,c in zip(parts,control_hud,candidate_hud,strict=True):
        np.testing.assert_array_equal(a['words'],b['words']);np.testing.assert_array_equal(a['words'],c['words'])
    display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words']for p in parts))
    quality=h.n.metric(original,display);displaytag=h.n.digest(display)
    assert quality==golden['hybrid']and displaytag==golden['display_sha256']
    control_desc=dict(packet=h.blob(control_wire),SP38_packet=h.blob(control['SP38_packet']),rank_trials=trials(control['rank_trials']),
        mode_arrays=[array_blob(a)for a in control['mode_arrays']],candidate_cost_arrays=[array_blob(a)for a in control['cost_arrays']])
    candidate_desc=dict(packet=h.blob(candidate_wire),SP38_packet=h.blob(candidate['SP38_packet']),rank_trials=trials(candidate['rank_trials']),
        mode_arrays=[array_blob(a)for a in candidate['modes']],candidate_cost_arrays=[array_blob(a)for a in candidate['costs']],eligibility_arrays=[array_blob(a)for a in candidate['eligibility']])
    return dict(id=fid,key=reference is None,reference_id=rid,source_sha256=h.digest(b''.join(v.astype('u1').tobytes()for v in source)),source_id=identity,
        packet=h.blob(wire),control=control_desc,candidate=candidate_desc,selected_kind=result['work']['selection'],
        control_bytes=len(control_wire),candidate_bytes=len(candidate_wire),complete_bytes=len(wire),
        reference_tag=(bytes(16)if reference is None else h.m.C.reference_tag(reference)).hex(),normalized_tag=h.m.C.reference_tag(pixels).hex(),
        display_sha256=displaytag,hybrid=quality,work=result['work'],receiver_ms=receive_ms,old_control_packet_exact=True)

def main():
    before=h.pins();old=h.load(h.HERE.parent/'python-game-mode-rank-v39-study/results.json')
    inputs=h.load(h.n.V24/'results.json')['inputs'];huds=h.load(h.HUD/'results.json')['cases'];cases=[]
    for inp in inputs:
        hc=next(c for c in huds if c['scene']==inp['scene']);previous=next(c for c in old['cases']if c['scene']==inp['scene']and c['policy']=='mode0control');rx=decoder.Receiver();rows=[]
        for src,hu,golden in zip(inp['rows'][:12],hc['rows'][:12],previous['rows'],strict=True):
            rows.append(frame(h.n.source(src),h.n.original(src),h.raw(hu['packet'],h.HUD),src['id'],rx,golden,dict(scene=inp['scene'],kind='main',id=src['id'])))
            print(json.dumps(dict(scene=inp['scene'],frame=src['id'],selected=rows[-1]['selected_kind'],bytes=rows[-1]['complete_bytes'])),flush=True)
        case=dict(scene=inp['scene'],kind='main',rows=rows,summary=summary(rows));cases.append(case);print(json.dumps(case['summary']),flush=True)
    sourcefolder=h.HERE.parent/'python-game-spatial-v38-study';source=h.load(sourcefolder/'results.json')
    for inp in source['synthetic_inputs']:
        flat=np.frombuffer(h.raw(inp['source'],sourcefolder),np.uint8)
        planes=(flat[:345600].reshape(480,720).astype(np.int16),flat[345600:432000].reshape(240,360).astype(np.int16),flat[432000:].reshape(240,360).astype(np.int16))
        original=np.frombuffer(h.raw(inp['original'],sourcefolder),'<u2').reshape(480,720).copy();hud=h.raw(inp['hud_packet'],sourcefolder)
        golden=next(c for c in old['cases']if c['scene']==inp['scene']and c['policy']=='mode0control')['rows'][0]
        row=frame(planes,original,hud,0,decoder.Receiver(),golden,dict(scene=inp['scene'],kind='synthetic',id=0))
        case=dict(scene=inp['scene'],kind='synthetic',rows=[row],summary=summary([row]));cases.append(case);print(json.dumps(dict(scene=inp['scene'],summary=case['summary'])),flush=True)
    assert h.pins()==before
    result=dict(schema='gamebub-exact-v40',source_sha256=before,cases=cases,physical_30fps_proven=False,new_RTL_implemented=False,HEVC_AV1_superiority_proven=False,
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        profile=dict(wire='unchangedRP39/TR39',cost_tensor_fields=['sourceYUVSSE','fineCoefficientBits','rawRankDecisions','canonicalFirst','exactMode0Pixels','eligible'],
            cost_tensor_dtype='<i8',eligibility='canonicalFirst AND everyreconstructed8x8YUVsampleequalsmode0',guard='strictlyfewercompleteactualbytes;tiescontrol'),
        scope=['27selectedactualRP39frames,54actualcontrol/candidatetrialsplusallSP38intermediates/ranktrialstreams/costs/eligibilityarraysretained.',
               'Everycandidatefullblockequalstoitsmode0blockbeforeitcaninfluenceneighbors. Fullplaneandreferenceequalityholdsinductivelyandischeckedagainstactualserializedpacketdecodes.',
               'Actualcandidate/controldecodesareforkedfromcurrentselectedreceiverstate;onlyselectedpacketadvancestheactualreference. All27controlsbyte-matchfrozenRP39mode0goldens.',
               'Rateproxyonlychoosesamongexactoutputalternatives;wholeframeactualbyteguardkeepscontrolonloss/tie. NomereSSEguard,nosourcequalitytradeandnoreferencedrift.',
               'Paidpairclockincludesallcontroloracleandcandidateevaluations,bothSP38/RP39proofpaths,allranktrialsandproofassertions. Fixture/HUDloads,archives/hashes/metrics,independentdecoders/network/displayexcluded.',
               'Same2reused12frameprefixes+3synthetics,nomode0qualityimprovement/freshnativecomparison/heldoutcontent/optimizedsender/physical30fpsclaim.'])
    (h.HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
