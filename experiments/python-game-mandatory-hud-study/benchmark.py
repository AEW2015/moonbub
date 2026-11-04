#!/usr/bin/env python3
"""Mandatory-HUD byte policy, actual AR03 decode/ACK, portable golden objects."""
from pathlib import Path
import hashlib,importlib.util,json,os,time,zlib,platform
import av,PIL
import numpy as np
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];C=model.codec
_spec=importlib.util.spec_from_file_location('mandatory_native_source',HERE.parent/'python-game-service-study/benchmark.py')
source=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(source)
VECTORS={0,1,8,24,25}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def pins():
    paths={ROOT/p for p in json.loads((HERE.parent/'python-game-candidate-commit-study/results.json').read_text())['source_sha256']}
    paths|={HERE/n for n in ('model.py','benchmark.py','verify.py','test_model.py')}
    paths|={Path(source.__file__),HERE.parent/'python-game-candidate-commit-study/results.json'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def blob(b,suffix='bin'):
    directory=HERE/'objects';directory.mkdir(exist_ok=True)
    data=zlib.compress(b,9);name=sha_bytes(data)+'.'+suffix+'.zlib';p=directory/name
    if not p.exists():p.write_bytes(data)
    assert p.read_bytes()==data
    return dict(path='objects/'+name,encoding='zlib',raw_bytes=len(b),raw_sha256=sha_bytes(b),stored_sha256=sha_bytes(data))
def array(a):
    a=np.ascontiguousarray(a)
    return dict(dtype=a.dtype.str,shape=list(a.shape),blob=blob(a.tobytes(),'array'))
def banks(rx,objects=False):
    return {str(k):None if b is None else dict(id=b.frame_id,tag=b.tag.hex(),**(dict(planes=[array(p.astype('<i2')) for p in b.planes]) if objects else {})) for k,b in rx.banks.items()}
def active_mse(a,b):
    aa=C.corpus.expand565(a).astype(np.float64);bb=C.corpus.expand565(b).astype(np.float64)
    return float(np.mean((aa[37:442]-bb[37:442])**2))
def brief(case):
    rows=case['rows'];accepted=[r for r in rows if r['accepted']]
    return dict(scene=case['scene'],policy=case['policy'],input_frames=len(rows),commits=len(accepted),whole_frame_rejections=len(rows)-len(accepted),
        full_ui_frames=sum(not r['omitted_rectangles'] for r in accepted),partial_ui_frames=sum(bool(r['omitted_rectangles']) for r in accepted),
        selected_ui_words=sum(r['selected_words'] for r in accepted),selected_word_errors=sum(r['selected_word_errors'] for r in accepted),
        profiles={str(k):sum(str(r.get('selected_profile'))==str(k) for r in accepted) for k in sorted({str(r.get('selected_profile')) for r in accepted})},
        maximum_packet_bytes=max((r['packet_bytes'] for r in accepted),default=0),total_packet_bytes=sum(r['packet_bytes'] for r in accepted),
        losing_builds=sum(sum(not a['accepted'] for a in r['attempts']) for r in rows),
        paid_build_ms=sum(sum(a['build_ms'] for a in r['attempts']) for r in rows),paid_discard_ms=sum(sum(a['discard_ms'] for a in r['attempts']) for r in rows),
        paid_patch_prepare_ms=sum(r.get('patch_prepare_ms',0) for r in rows),
        mean_active_rgb565_mse=None if not accepted else sum(r['active_rgb565_mse'] for r in accepted)/len(accepted),
        maximum_build_attempts=max((len(r['attempts']) for r in rows),default=0))
def run_case(scene,policy,frames,manifest):
    p=model.Policy() if policy=='mandatory' else None
    e=p.encoder if p else C.Encoder(mode='gm',patch_builder=model.ui.PatchSelector(rectangles=model.RECTANGLES));rx=C.Receiver()
    rows=[];vectors=[]
    for i,native in enumerate(frames):
        (rgb,_),box_ms=model.measured(lambda:C.corpus._letterbox(native,720,480));prior=model.state(e);readers_before=e.readers
        key=i in (0,24);promote=i in (8,16,32,40) and not key
        kw=dict(force_key=key,promote=promote)
        before_banks=banks(rx,objects=i in VECTORS)
        if p:
            prepared,outer_ms=model.measured(lambda:p.prepare(rgb,i,**kw));c=prepared.candidate;info=prepared.info
        else:
            mapped,map_ms=model.measured(lambda:C.gm.roi.declared_map(720,480,model.BASE_REGIONS,8,16))
            c,elapsed=model.measured(lambda:e.build(rgb,i,scale_map=mapped,**kw));ci=C.plain_info(c)
            info=dict(reason='baseline_complete' if c.accepted else 'baseline_over_cap',patch_prepare_ms=0.,
                selected_profile=[8,16],attempts=[dict(index=0,roi_scale=8,background_scale=16,map_ms=map_ms,build_ms=elapsed,
                candidate_build_internal_ms=c.service_ms,inner_bytes=ci['inner_bytes'],attempted_complete_bytes=ci['bytes'],
                built_packet_bytes=ci['bytes'],accepted=c.accepted,candidate_accepted=c.accepted,
                analyze_calls=ci['analyze_calls'],forward_calls=ci['forward_calls'],discard_ms=0.)]);outer_ms=map_ms+elapsed
        row=dict(id=i,input_sha256=model.digest(rgb),box_ms=box_ms,policy_outer_ms=outer_ms,reason=info['reason'],attempts=info['attempts'],
            readers_before=readers_before,readers_after_builds=e.readers,patch_prepare_ms=info.get('patch_prepare_ms',0),mandatory_patch_bytes=info.get('mandatory_patch_bytes'),reserved_inner_bytes=info.get('reserved_inner_bytes'),
            selected_profile=info.get('selected_profile'),state_before=prior,state_after_builds=model.state(e),accepted=c is not None and c.accepted)
        assert model.state(e)==prior
        if not row['accepted']:
            if c is not None:
                _,elapsed=model.measured(lambda:e.discard(c));row['attempts'][-1]['discard_ms']+=elapsed
            assert model.state(e)==prior and not e.readers and not e.active_candidate
            row.update(state_after=prior,readers_after=0);rows.append(row);continue
        decision,commit_ms=model.measured(lambda:e.commit(c));packet=decision.packet;meta=C.identity(packet,decode=True)
        task,begin_ms=model.measured(lambda:rx.begin(packet));planes=task.planes
        (out,decode_info,ack),complete_ms=model.measured(lambda:rx.complete(task));_,ack_ms=model.measured(lambda:e.ack(ack))
        selected=[list(v['rect']) for v in decode_info['patches']];omitted=[list(rect) for rect in model.RECTANGLES if list(rect) not in selected]
        original=C.corpus.rgb565(rgb);display=C.corpus.rgb565(out);errors=0
        for x,y,w,h in selected:errors+=int(np.count_nonzero(original[y:y+h,x:x+w]!=display[y:y+h,x:x+w]))
        assert errors==0 and len(packet)<=49152
        if p:assert not omitted and decode_info['selected_pixels']==21120
        assert not e.readers and not rx.readers and not e.pending and e.active_candidate is None and rx.active is None
        row.update(packet_bytes=len(packet),inner_bytes=meta['inner_bytes'],patch_bytes=meta['patch_bytes'],packet_sha256=sha_bytes(packet),
            key=meta['key'],promoted=meta['promoted'],reference_bank=meta['reference_bank'],reference_id=meta['reference_id'],
            reference_tag=meta['reference_tag'].hex(),destination_bank=meta['destination_bank'],stored_tag=meta['stored_tag'].hex(),
            selected_rectangles=selected,omitted_rectangles=omitted,selected_words=decode_info['selected_pixels'],selected_word_errors=errors,
            rgb_sha256=model.digest(out),base_rgb_sha256=decode_info['base_rgb_sha256'],active_rgb565_mse=active_mse(original,display),
            commit_ms=commit_ms,decode_begin_ms=begin_ms,decode_complete_ms=complete_ms,ack_apply_ms=ack_ms,
            state_after=model.state(e),readers_after=e.readers,receiver_readers_after=rx.readers)
        if i in VECTORS:
            vectors.append(dict(id=i,key=meta['key'],promoted=meta['promoted'],packet=blob(packet,'ar03'),ack=blob(ack,'af03'),source=array(rgb),
                pre_banks=before_banks,post_banks=banks(rx),decoded_yuv=[array(a.astype('<i2')) for a in planes],display_rgb565=array(display.astype('<u2')),
                rgb_sha256=row['rgb_sha256'],selected_words=row['selected_words'],selected_word_errors=0,
                selected_rectangles=selected,omitted_rectangles=omitted))
        rows.append(row)
    return dict(scene=scene,policy=policy,manifest=manifest,rows=rows,vectors=vectors,final_state=model.state(e),
        scope='Actual sequential build/commit/receive/AF03 ACK with no scheduled wire/deadline model; history-dependent losses/costs are not FPS.')
def main():
    before=pins();started=time.perf_counter();media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')));cases=[]
    for scene in ('mass-effect-2600','mass-effect-7200'):
        frames,manifest=source.native(media/(scene+'.mp4'),n=48,start=4);assert manifest['unique_frame_count']==48
        for policy in ('baseline','mandatory'):
            case=run_case(scene,policy,frames,manifest);cases.append(case);print(json.dumps(brief(case)),flush=True)
    assert before==pins(),'sources changed during run'
    comparisons=[]
    for scene in ('mass-effect-2600','mass-effect-7200'):
        a,b=[c for c in cases if c['scene']==scene];aa={r['id']:r for r in a['rows'] if r['accepted']};bb={r['id']:r for r in b['rows'] if r['accepted']};common=sorted(aa.keys()&bb.keys())
        same_refs=[i for i in common if all(aa[i][k]==bb[i][k] for k in ('key','promoted','reference_bank','reference_id','reference_tag'))]
        comparisons.append(dict(scene=scene,common_accepted_ids=common,same_reference_ids=same_refs,
            baseline_matched_rgb565_mse=sum(aa[i]['active_rgb565_mse'] for i in common)/len(common),mandatory_matched_rgb565_mse=sum(bb[i]['active_rgb565_mse'] for i in common)/len(common),
            same_reference_baseline_mse=sum(aa[i]['active_rgb565_mse'] for i in same_refs)/len(same_refs),same_reference_mandatory_mse=sum(bb[i]['active_rgb565_mse'] for i in same_refs)/len(same_refs),
            limitation='Same source IDs; adapting keys/promotions changes future prediction history. MSE is declared matched-source quality, not pure compression gain or lossless base image.'))
    result=dict(schema='gamebub-mandatory-hud-v1',source_sha256=before,cases=cases,summary=[brief(c) for c in cases],comparisons=comparisons,
        counts=dict(cases=4,source_acquisitions=96,frame_decisions=192,golden_vectors=sum(len(c['vectors']) for c in cases)),python_wall_seconds=time.perf_counter()-started,versions=dict(python=platform.python_version(),numpy=np.__version__,pyav=av.__version__,pillow=PIL.__version__),
        scope=['720x480coded/720x405active; complete49152Bcap; all accepted mandatory frames protect four originalRGB565 HUD rectangles.',
            'Patch bytes prepared/reserved before causal fixed-order ROI8BG16/ROI8BG32/ROI16BG32/uniform32 base adaptation. All actual losing builds/map/discards and UI work paid; no future-frame/quality-oracle selection.',
            'Actual AR03/AF03 payload syntax unchanged. Reference identity/source leases committed only after candidate acceptance. Source quantization changes background quality and future history.',
            'Sequential Python component proof, not wire/gateway/ESP32/RF/DSP/BRAM/resource/timing/30fps proof. Offline acquisition excluded; BOX measured per policy/frame; postdecode quality/oracle/export excluded from adaptation cost.',
            'Existing precompressed29.88fps regression windows, not fresh heldout/live gameplay. Golden fixtures retain precondition banks for isolated replay, not a complete transmitted stream.'])
    (HERE/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
