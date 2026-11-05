#!/usr/bin/env python3
"""Independent v35 source, causal, byte, guard, work and native-trace audit."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CTRL=ROOT/'experiments/python-game-controller-v35-study'
ALIGNED=ROOT/'experiments/python-game-aligned-v35-study'
REUSE=ROOT/'experiments/python-game-reuse-v35-study'
HUD=ROOT/'experiments/python-game-hud-runs-v33-study'
OLDCTRL=ROOT/'experiments/python-game-controller-v34-study'
STANDARD=ROOT/'experiments/python-game-standard-v24-study/results.json'
SCENES=('mass-effect-2600','mass-effect-7200');POLICIES=('control','guarded_core8')
FRAMES,CAP,BINDING=48,49152,60

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None:raise RuntimeError(f'cannot load {path}')
    out=importlib.util.module_from_spec(spec);sys.modules[name]=out;spec.loader.exec_module(out);return out

h=module('audit_guard35_helpers',CTRL/'helpers.py')
choose=module('audit_guard35_selector',CTRL/'controller.py').choose

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path,schema):
    data=json.loads(Path(path).read_text())
    if data.get('schema')!=schema:raise ValueError(f'{path}: unexpected schema')
    return data
def pins(data,label):
    values=data.get('source_sha256')
    if not isinstance(values,dict) or not values:raise ValueError(f'{label}: no source pins')
    for rel,digest in values.items():
        p=Path(rel)
        if p.is_absolute() or '..' in p.parts or len(digest)!=64 or sha(ROOT/p)!=digest:raise ValueError(f'{label}: bad source pin {rel}')
    return len(values)
def metric(m):
    e,n=m.get('active_squared_error'),m.get('active_channel_samples')
    if type(e)is not int or type(n)is not int or e<0 or n<=0 or m.get('active_mse')!=e/n:raise ValueError('integer RGB metric mismatch')
    return e,n,e/n

def audit():
    result=load(CTRL/'results.json','gamebub-controller-v35')
    aligned=load(ALIGNED/'results.json','gamebub-aligned-v35')
    reuse=load(REUSE/'results.json','gamebub-reuse-v35')
    hud=load(HUD/'results.json','gamebub-run-HUD-v33')
    pin_counts={name:pins(data,name) for name,data in (('controller',result),('aligned',aligned),('reuse',reuse),('HUD',hud))}
    if result.get('physical_30fps_proven') is not False or result.get('new_RTL_implemented') is not False:
        raise ValueError('controller proof boundary mismatch')
    indexed={(c['scene'],c['policy']):c for c in result['cases']}
    expected={(s,p) for s in SCENES for p in POLICIES}
    if len(indexed)!=4 or set(indexed)!=expected:raise ValueError('exact four causal cohorts required')
    acases={c['scene']:c for c in aligned['cases']};hcases={c['scene']:c for c in hud['cases']}
    if set(acases)!=set(SCENES) or set(hcases)!=set(SCENES):raise ValueError('missing aligned/HX33 scene')
    source_inputs=h.load(h.n.V24/'results.json')['inputs'];input_by_scene={c['scene']:c for c in source_inputs}
    v34=load(OLDCTRL/'results.json','gamebub-controller-v34');v34idx={(c['scene'],c['policy']):c for c in v34['cases']}
    report={};diffs={};mask_report={};native_report={};candidate_total=accepted_total=control_parity=0
    for scene in SCENES:
        srcrows=input_by_scene[scene]['rows'];hr=hcases[scene]['rows'];ar=acases[scene]['rows']
        if any([r['id'] for r in rows]!=list(range(FRAMES)) for rows in (srcrows,hr,ar)):raise ValueError('ordered source/HUD/aligned IDs required')
        if len(srcrows)!=FRAMES:raise ValueError('48 retained input frames required')
        aligned_masked=[]
        for row,src in zip(ar,srcrows,strict=True):
            if row['source_sha256']!=src['common_yuv420_u8_sha256'] or not row['visible_precodec_equal']:
                raise ValueError('aligned core8 source lineage/equivalence flag mismatch')
            source=h.n.source(src)
            made=h.mask.mask_source(source,h.n.RECTS,policy='core8')
            digest=h.digest(b''.join(a.astype('u1').tobytes() for a in made))
            if digest!=row['masked_source_sha256']:raise ValueError('aligned core8 source mask hash mismatch')
            aligned_masked.append(digest)
        hud_by_id={r['id']:r['bytes'] for r in hr}
        scene_report={}
        for policy in POLICIES:
            case=indexed[(scene,policy)];rows=case['rows']
            if [r['id'] for r in rows]!=list(range(FRAMES)):raise ValueError(f'{scene}/{policy}: IDs missing/reordered')
            rx=h.p.Receiver(epoch=25);ref=None;rid=h.m.NO_REF;slot=0;previous_tag=None
            sums=dict(body=0,base=0,hud=0,binding=0,sse=0,samples=0,max=0,mask_ms=0.,
                analysis_ms=0.,groups_ms=0.,selection_ms=0.,candidate_quality_ms=0.,candidate_bind_ms=0.,
                receive_ms=0., candidates=0,shadow_bytes=0,shadow_sse=0,masked=0,decoder_reads=0)
            for fid,(row,src,hu) in enumerate(zip(rows,srcrows,hr,strict=True)):
                key=fid%24==0;expected_rid=h.m.NO_REF if key else fid-1
                if key:ref=None;rid=h.m.NO_REF;slot=0
                if row['key'] is not key or row['reference_id']!=expected_rid or row['reference_tag']!=(bytes(16).hex() if key else previous_tag):
                    raise ValueError(f'{scene}/{policy}/{fid}: own-history ref/key/tag mismatch')
                if row['source_sha256']!=src['common_yuv420_u8_sha256'] or row['hud_packet']!=hu['packet']:
                    raise ValueError('source/HX33 descriptor identity mismatch')
                source=h.n.source(src);original=h.n.original(src)
                if policy=='guarded_core8':
                    mask_work={};masked=h.mask.mask_source(source,h.n.RECTS,policy='core8',work=mask_work)
                    digest=h.digest(b''.join(a.astype('u1').tobytes() for a in masked))
                    if digest!=row['masked_source_sha256'] or digest!=aligned_masked[fid]:raise ValueError('causal source differs from aligned/native source trace')
                    before=h.m.ft.planes_to_rgb(source);after=h.m.ft.planes_to_rgb(masked)
                    if mask_work!=row['mask_work']:raise ValueError('core8 mask store/work counts mismatch')
                    visible=np.ones((480,720),dtype=bool)
                    for x,y,w,hh in h.n.RECTS:visible[y:y+hh,x:x+w]=False
                    np.testing.assert_array_equal(before[visible],after[visible])
                    if not row['mask_used']:raise ValueError('guarded candidate was not selected')
                else:
                    if row['mask_used'] or row['masked_source_sha256'] is not None:raise ValueError('control unexpectedly masks source')
                    digest=None
                hudbytes=h.raw(hu['packet'],HUD)
                pair=h.raw(row['packet']);base=h.raw(row['base_packet']);ack=h.raw(row['ack'])
                pm=h.p.parse_pair(pair)
                if (pm['base']!=base or pm['hud']!=hudbytes or len(pair)!=row['body_bytes']
                        or len(base)!=row['base_bytes'] or len(hudbytes)!=row['hud_bytes']
                        or row['binding_bytes']!=BINDING or len(pair)!=len(base)+len(hudbytes)+BINDING
                        or len(pair)>CAP):raise ValueError('accepted CP34 component sum/cap mismatch')
                if (pm['frame_id']!=fid or pm['key'] is not key or pm['base_meta']['reference_id']!=expected_rid
                        or pm['base_meta']['reference_tag'].hex()!=row['reference_tag']):
                    raise ValueError('accepted packet identity/ref mismatch')
                ackmeta=h.p.validate_ack(ack,pair)
                if ackmeta['base_tag']!=pm['base_meta']['reconstructed_tag'].hex():raise ValueError('ACK does not bind base output tag')
                pixels,patches,decoded_ack=rx.receive(pair)
                if decoded_ack!=ack or ackmeta['frame_id']!=fid:raise ValueError('JA35/JA34 ACK mismatch')
                display=h.n.overlay(h.m.C.corpus.rgb565(h.m.ft.planes_to_rgb(pixels)),tuple(p['words'] for p in patches))
                q=h.n.metric(original,display);digest_rgb=h.n.digest(display)
                if q!=row['hybrid'] or digest_rgb!=row['hybrid_sha256']:raise ValueError('accepted original-source RGB metric mismatch')
                sse,samples,_=metric(q)
                attempts=row['attempts'];bgs=sorted({a['background'] for a in attempts})
                if bgs not in ([16],[16,32]):raise ValueError('invalid scale fallback sequence')
                selected=None;selected_shadow=None
                for bg in bgs:
                    controls=[a for a in attempts if a['background']==bg and not a['kind'].startswith('mask_')]
                    candidates=[a for a in attempts if a['background']==bg and a['kind'].startswith('mask_')]
                    order=['zero','half32','zero_band','half32_band'] if not key else ['zero','zero_band']
                    if [a['kind'] for a in controls]!=order:raise ValueError('orig-source strict-control candidate family/order incomplete')
                    expected_mask_order=[f'mask_{v}' for v in order]
                    if policy=='guarded_core8' and [a['kind'] for a in candidates]!=expected_mask_order:raise ValueError('core8 mask candidate family/order incomplete')
                    shadow,_baseline=h.select30.select_tier(controls,'band_strict')
                    winner=choose(shadow,candidates)
                    for a in controls+candidates:
                        if a['background']!=bg:continue
                        rawpair=h.raw(a['packet']);rawbase=h.raw(a['base_packet']);parsed=h.p.parse_pair(rawpair)
                        if (len(rawpair)!=a['complete_bytes'] or a['complete_bytes']!=a['base_bytes']+row['hud_bytes']+BINDING
                                or parsed['base']!=rawbase or parsed['hud']!=hudbytes
                                or a['cap_fit'] is not (a['complete_bytes']<=CAP)):
                            raise ValueError('candidate packet/binding/cap accounting mismatch')
                        metric(a['hybrid'])
                    if winner is not None:
                        if selected is not None:raise ValueError('candidate selection continued after fit')
                        selected,selected_shadow=winner,shadow
                actual=[a for a in attempts if a.get('selected') is True]
                if selected is None or len(actual)!=1 or actual[0]['kind']!=selected['kind'] or actual[0]['complete_bytes']!=selected['complete_bytes']:
                    raise ValueError('selected attempt differs from strict guarded decision')
                if (row['selected_kind']!=selected['kind'] or row['selected_background']!=selected['background']
                        or row['shadow_kind']!=selected_shadow['kind'] or row['shadow_complete_bytes']!=selected_shadow['complete_bytes']
                        or row['shadow_source_sse']!=selected_shadow['hybrid']['active_squared_error']):
                    raise ValueError('selected output or same-history strict shadow mismatch')
                if policy=='guarded_core8' and (not selected['qualified'] or selected['complete_bytes']>=selected_shadow['complete_bytes']
                        or selected['hybrid']['active_squared_error']>selected_shadow['hybrid']['active_squared_error']):
                    raise ValueError('core8 selection violated strict byte/RGB guard')
                if selected['hybrid']!=q or selected['hybrid_sha256']!=digest_rgb:raise ValueError('selected/accepted metric mismatch')
                paid=(row['mask_ms']+sum(v['wall_ms'] for v in row['analyses'].values())
                      +sum(v['wall_ms'] for v in row['encode_groups'])+row['selection_ms']
                      +sum(a['quality_ms']+a['bind_ms'] for a in attempts))
                if not math.isclose(paid,row['paid_policy_ms'],rel_tol=1e-10,abs_tol=1e-5):raise ValueError('paid work subtotal mismatch')
                sums['body']+=len(pair);sums['base']+=len(base);sums['hud']+=len(hudbytes);sums['binding']+=BINDING
                sums['sse']+=sse;sums['samples']+=samples;sums['max']=max(sums['max'],len(pair));sums['mask_ms']+=row['mask_ms']
                sums['analysis_ms']+=sum(v['wall_ms'] for v in row['analyses'].values());sums['groups_ms']+=sum(v['wall_ms'] for v in row['encode_groups'])
                sums['selection_ms']+=row['selection_ms'];sums['candidate_quality_ms']+=sum(a['quality_ms'] for a in attempts)
                sums['candidate_bind_ms']+=sum(a['bind_ms'] for a in attempts);sums['receive_ms']+=row['receive_ms']
                sums['candidates']+=len(attempts);sums['shadow_bytes']+=selected_shadow['complete_bytes'];sums['shadow_sse']+=selected_shadow['hybrid']['active_squared_error']
                sums['masked']+=row['mask_used'];sums['decoder_reads']+=selected['work']['decoder_reference_sample_reads']
                previous_tag=pm['base_meta']['reconstructed_tag'].hex();ref,rid,slot=pixels,fid,row['destination_slot']
                candidate_total+=len(attempts);accepted_total+=1
                if policy=='control':
                    oldrow=v34idx[(scene,'control')]['rows'][fid]
                    if pair!=h.raw(oldrow['packet'],OLDCTRL) or ack!=h.raw(oldrow['ack'],OLDCTRL) or q!=oldrow['hybrid']:
                        raise ValueError('v35 original control lacks exact v34 CP34/HX33/pixel parity')
                    control_parity+=1
            sm=case['summary'];mse=sums['sse']/sums['samples']
            checks={'frames':FRAMES,'complete_bytes':sums['body'],'base_bytes':sums['base'],'hud_bytes':sums['hud'],
                'binding_bytes':sums['binding'],'active_squared_error':sums['sse'],'active_channel_samples':sums['samples'],
                'maximum_complete_bytes':sums['max'],'actual_candidate_frames':sums['candidates'],
                'selected_masked_frames':sums['masked'],'source_same_history_shadow_bytes':sums['shadow_bytes'],
                'source_same_history_shadow_sse':sums['shadow_sse']}
            for k,v in checks.items():
                if sm[k]!=v:raise ValueError(f'{scene}/{policy} summary mismatch {k}')
            if not math.isclose(sm['active_mse'],mse,rel_tol=1e-13) or sums['max']>CAP:raise ValueError('MSE/cap aggregate mismatch')
            for k,v in (('mean_paid_policy_ms',sum(r['paid_policy_ms'] for r in rows)/FRAMES),
                        ('mean_mask_ms',sums['mask_ms']/FRAMES),('mean_receiver_ms',sums['receive_ms']/FRAMES)):
                if not math.isclose(sm[k],v,rel_tol=1e-10,abs_tol=1e-5):raise ValueError(f'{k} summary mismatch')
            scene_report[policy]=dict(frames=FRAMES,complete_bytes=sums['body'],base_bytes=sums['base'],
                same_HX33_bytes=sums['hud'],binding_bytes=sums['binding'],maximum_complete_bytes=sums['max'],cap_fits=True,
                active_squared_error=sums['sse'],active_channel_samples=sums['samples'],active_mse=mse,
                own_history_strict_shadow_bytes=sums['shadow_bytes'],own_history_strict_shadow_sse=sums['shadow_sse'],
                own_history_shadow_is_standalone_v34_control=(policy=='control'),
                candidates=sums['candidates'],selected_masked_frames=sums['masked'],
                mean_paid_policy_ms=sm['mean_paid_policy_ms'],paid_subtotals_ms=dict(mask=sums['mask_ms'],
                    analysis=sums['analysis_ms'],shared_encode_groups=sums['groups_ms'],selection=sums['selection_ms'],
                    candidate_quality=sums['candidate_quality_ms'],candidate_binding=sums['candidate_bind_ms']),
                selected_decoder_reference_reads=sums['decoder_reads'])
        ctrl=scene_report['control'];core=scene_report['guarded_core8']
        diffs[scene]=dict(complete_byte_saving=ctrl['complete_bytes']-core['complete_bytes'],
            complete_byte_saving_percent=100*(ctrl['complete_bytes']-core['complete_bytes'])/ctrl['complete_bytes'],
            active_mse_delta=core['active_mse']-ctrl['active_mse'],
            active_mse_percent_delta=100*(core['active_mse']/ctrl['active_mse']-1),
            strict_guarded_candidates_selected=core['selected_masked_frames'],
            quality_neutral_or_better=(core['active_mse']<=ctrl['active_mse']))
        mask_report[scene]=dict(all_source_mask_digests_equal_aligned=True,
            all_48_frames_select_core8=True,source_mask_policy='whole-transform core8; included in paid controller time')
        report[scene]=scene_report

    if accepted_total!=192 or candidate_total!=1128 or control_parity!=96:raise ValueError('overall accepted/candidate/control parity mismatch')

    # The native packets are encoded from the exact selected source trace, and
    # are cross-checked against the aligned-v35 masked native anchor, not v34 original input.
    native_index={}
    for item in result['native_cases']:
        key=(item['scene'],item['codec'],item['parameter'])
        if key in native_index or item['trace_policy']!='guarded_core8':raise ValueError('duplicate or wrong native trace policy')
        native_index[key]=item
    if len(native_index)!=4:raise ValueError('expected four same-trace native points')
    anchor_index={(c['scene'],c['encoder'],c['parameter']):c for c in aligned['native_cases'] if c['processed']=='masked'}
    native_summary={}
    for key,item in native_index.items():
        scene,codec,param=key;anchor=anchor_index.get(key)
        if anchor is None:raise ValueError('same-processed aligned native anchor missing')
        if [r['id'] for r in item['rows']]!=list(range(FRAMES)) or [r['id'] for r in anchor['rows']]!=list(range(FRAMES)):
            raise ValueError('native IDs incomplete')
        extra=h.raw(item['extradata'],CTRL);anchor_extra=h.raw(anchor['extradata'],ALIGNED)
        if extra!=anchor_extra:raise ValueError('native extradata differs from exact masked-input anchor')
        bsum=ssum=nsum=0;maximum=0;exact_au=True
        core_rows=indexed[(scene,'guarded_core8')]['rows']
        for fid,(r,a,cr) in enumerate(zip(item['rows'],anchor['rows'],core_rows,strict=True)):
            au=h.raw(r['access_unit'],CTRL);anchor_au=h.raw(a['access_unit'],ALIGNED)
            if (r['pts']!=fid or r['dts']!=fid or r['key'] is not (fid%24==0)
                    or r['source_sha256']!=cr['masked_source_sha256']):raise ValueError('native source trace/PTS/key mismatch')
            expected_ext=len(extra) if fid==0 else 0
            hudbytes=h.raw(r['hud_packet'],HUD)
            if (len(au)!=r['access_unit_bytes'] or r['extradata_bytes_charged']!=expected_ext
                    or r['hud_bytes']!=len(hudbytes) or r['binding_bytes']!=BINDING
                    or r['body_bytes']!=len(au)+len(hudbytes)+BINDING+expected_ext):raise ValueError('native actual AU/HX33/60B bytes mismatch')
            if au!=anchor_au or r['hybrid']!=a['hybrid']:exact_au=False
            e,n,_=metric(r['hybrid']);bsum+=r['body_bytes'];ssum+=e;nsum+=n;maximum=max(maximum,r['body_bytes'])
        sm=item['summary']
        if (sm['complete_bytes']!=bsum or sm['active_squared_error']!=ssum or sm['active_channel_samples']!=nsum
                or sm['maximum_complete_bytes']!=maximum or not sm['cap_fit'] or maximum>CAP
                or not math.isclose(sm['active_mse'],ssum/nsum,rel_tol=1e-13)):
            raise ValueError('native summary rate/MSE/cap mismatch')
        if not exact_au:raise ValueError('fresh native result differs from aligned exact masked-source anchor')
        target=indexed[(scene,'guarded_core8')]['summary']['active_mse']
        if sm['active_mse']>target:raise ValueError('native trace point fails core8 quality target')
        native_summary[f'{scene}/{codec}']=dict(processed='exact selected guarded_core8 trace',parameter=param,
            complete_bytes=bsum,active_squared_error=ssum,active_channel_samples=nsum,active_mse=ssum/nsum,
            maximum_complete_bytes=maximum,same_actual_HX33_and_60B=True,exact_AU_anchor_parity=True,
            meets_custom_quality_and_cap=True)

    reuse_sha=sha(OLDCTRL/'results.json')
    if reuse.get('input_controller_results_sha256')!=reuse_sha:raise ValueError('reuse study is pinned to different controller results')
    if len(reuse['rows'])!=184 or reuse['frame_variants']!=368:raise ValueError('HM34 reuse field/variant coverage mismatch')
    reuse_summary={}
    for row in reuse['summary']:
        key=f"{row['scene']}/{row['policy']}"
        if row['fields']!=46 or row['frame_variants']!=92:raise ValueError('HM34 reuse per-cohort coverage mismatch')
        reuse_summary[key]=dict(fields=row['fields'],frame_variants=row['frame_variants'],
            old_component_mean_ms=row['old']['mean_ms'],reused_component_mean_ms=row['new']['mean_ms'],
            component_speedup=row['sum_component_speedup'],prepaid_parent_child_analysis_ms=row['already_charged_parent_child_analysis_ms'],
            scope='component-only encoder timing; original-map generation/analysis is prepaid and remains in controller policy totals')

    # Baseline same-HX33 native budgets remain only reference points; v35's
    # actual native comparison above uses the exact selected core8 input trace.
    direct=['experiments/python-game-controller-v35-study/results.json',
        'experiments/python-game-controller-v35-study/helpers.py','experiments/python-game-controller-v35-study/controller.py',
        'experiments/python-game-controller-v35-study/benchmark.py','experiments/python-game-controller-v35-study/verify.py',
        'experiments/python-game-controller-v35-study/test_model.py','experiments/python-game-controller-v35-study/README.md',
        'experiments/python-game-aligned-v35-study/results.json','experiments/python-game-aligned-v35-study/model.py',
        'experiments/python-game-aligned-v35-study/benchmark.py','experiments/python-game-aligned-v35-study/verify.py',
        'experiments/python-game-reuse-v35-study/results.json','experiments/python-game-reuse-v35-study/benchmark.py',
        'experiments/python-game-reuse-v35-study/verify.py','experiments/python-game-reuse-v35-study/test_model.py',
        'experiments/python-game-hud-runs-v33-study/results.json','experiments/python-game-controller-v34-study/results.json',
        'experiments/python-game-standard-v24-study/results.json','experiments/python-game-audit-v34-study/audit.json',
        'experiments/python-game-audit-v35-study/audit.py','experiments/python-game-audit-v35-study/baseline.json',
        'experiments/python-game-audit-v35-study/test_baseline.py']
    flat={}
    for data in (result,aligned,reuse,hud):
        for rel,digest in data['source_sha256'].items():
            if rel in flat and flat[rel]!=digest:raise ValueError(f'conflicting pin for {rel}')
            flat[rel]=digest
    for rel in direct:flat[rel]=sha(ROOT/rel)
    pinsets={}
    for name,data,folder in (('controller',result,CTRL),('aligned',aligned,ALIGNED),('reuse',reuse,REUSE),('hud',hud,HUD)):
        pinsets[name]=dict(result_sha256=sha(folder/'results.json'),pin_count=len(data['source_sha256']),
            pin_set_sha256=hashlib.sha256(json.dumps(data['source_sha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest())
    return dict(schema='gamebub-python-game-audit-v35',source_sha256=dict(sorted(flat.items())),source_pin_sets=pinsets,
        cohorts=report,quality_comparison=diffs,core8_source_identity=mask_report,
        accepted_frames=accepted_total,actual_candidate_frames=candidate_total,exact_v34_control_CP34_parity_rows=control_parity,
        actual_same_processed_native_points=native_summary,HM34_reuse=reuse_summary,
        claim_boundary='Guarded source masks are paid in controller time. Local same-history guards do not ensure no aggregate quality loss after references diverge. Native points use the exact selected guarded-core8 source trace, actual same HX33+60B accounting, and exact aligned native-anchor parity. HM34 reuse timing excludes the prepaid motion-map generation. V34 same-HX33 standards points are historical references only; no native codec rerun is claimed here. No physical FPS or RTL claim.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');opts=parser.parse_args()
    out=audit();data=(json.dumps(out,indent=2,sort_keys=True)+'\n').encode();dest=HERE/'audit.json'
    if opts.check:
        if not dest.is_file() or dest.read_bytes()!=data:raise SystemExit('audit.json missing or stale; regenerate without --check')
    else:dest.write_bytes(data)
    print(json.dumps(dict(cohorts=len(out['cohorts']),accepted=out['accepted_frames'],candidates=out['actual_candidate_frames'],flat_source_pins=len(out['source_sha256']),native_points=len(out['actual_same_processed_native_points']))))
