"""Bounded source-error-gated small-AC deletion/shrink candidates, exact rate choice.

Stable GM27 wire, full geometry, no new decoder approximation. All trial inverse
transforms, size counters, and packet constructions execute inside encode_with.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('shrink32_entropy29',HERE.parent/'python-game-entropy-v29-study/model.py')
e=importlib.util.module_from_spec(spec);sys.modules[spec.name]=e;spec.loader.exec_module(e)
m=e.m
POLICIES=('shrink_strict','shrink_budget')


def protected_blocks(module,q,w,h,plane):
    protected=module.roi.block_scales(q,w,h,plane)==8
    if plane:
        priority=q==8;halo=priority.copy();halo[:,1:]|=priority[:,:-1];halo[1:,:]|=priority[:-1,:];halo[1:,1:]|=priority[:-1,:-1]
        protected=halo.reshape(-1)
    return protected


def reconstruct_plane(module,coeff,prediction,q,w,h,plane):
    ph,pw=prediction.shape;bh,bw=(ph+7)//8,(pw+7)//8
    residual=module.ft.inverse(coeff.astype(np.int64)*module.roi.block_tables(q,w,h,plane))
    pixels=residual.reshape(bh,bw,8,8).transpose(0,2,1,3).reshape(bh*8,bw*8)[:ph,:pw]
    return np.clip(prediction+pixels,0,255).astype(np.int16)


def candidates(module,p,q,coeff,plane,baseline,policy):
    if policy not in POLICIES:raise ValueError('declared shrink policy')
    protected=protected_blocks(module,q,p.width,p.height,plane)
    sse=module.base.old._block_sse(p.source[plane].astype(np.int64)-baseline)
    allowance=np.zeros_like(sse) if policy=='shrink_strict' else np.minimum(sse//100,64)
    menu=[('incumbent',coeff)];trials=[]
    # The declared menu is fixed before corpus evaluation. Four full-plane
    # proposals are gated independently by each block's actual clipped SSE.
    for label,cutoff,threshold in (('zero_small1',6,1),('zero_small2',6,2),('shrink_high1',21,0),('shrink_ac1',6,0)):
        trial=coeff.copy();flat=trial.reshape(-1,64);positions=module.ft.ZIGZAG[cutoff:]
        values=flat[:,positions].copy()
        if threshold:
            values[np.abs(values)<=threshold]=0
        else:
            values=values-np.sign(values).astype(np.int16)
        flat[:,positions]=values
        out=reconstruct_plane(module,trial,p.prediction[plane],q,p.width,p.height,plane)
        trial_sse=module.base.old._block_sse(p.source[plane].astype(np.int64)-out)
        changed=np.any(trial!=coeff,axis=(1,2));eligible=~protected & changed & (trial_sse<=sse+allowance)
        selected=coeff.copy();selected[eligible]=trial[eligible]
        trials.append(dict(label=label,cutoff=cutoff,threshold=threshold,attempted_changed_blocks=int(changed.sum()),eligible_blocks=int(eligible.sum()),
                           eligible_sse_increase=int((trial_sse[eligible]-sse[eligible]).sum())))
        if not any(np.array_equal(selected,c) for _,c in menu):menu.append((label,selected))
    return menu,dict(protected_blocks=int(protected.sum()),total_blocks=len(coeff),candidate_inverse_plane_calls=4,
                     trials=trials,allowed_extra_source_yuv_sse=int(allowance[~protected].sum()),
                     baseline_source_yuv_sse=int(sse.sum()))


def encode_with(module,prepared,scale_map,rdo_lambda=1,policy='shrink_strict'):
    started=time.perf_counter_ns();p=prepared
    if policy not in POLICIES:raise ValueError('declared shrink policy')
    if not isinstance(p,module.Prepared) or p.owner is not module._PREPARED_OWNER:raise ValueError('owned GM27 preparation')
    if type(rdo_lambda) not in (int,float) or not np.isfinite(rdo_lambda) or not 0<=rdo_lambda<=1000000:raise ValueError('RDO lambda')
    q=module.roi.check_map(scale_map,p.width,p.height)
    original=module.base._quantize(p.raw_coefficients,q,p.width,p.height)
    pruned,rdo=module.counter.rdo_skip(p,original,q,rdo_lambda)
    incumbent=[];legacy_trials=[]
    for plane,coeff in enumerate(pruned):
        bw=((p.width if plane==0 else p.width//2)+7)//8
        plan=module.legacy_plan(coeff,bw);trials=[plan]
        if not np.array_equal(coeff,original[plane]):
            op=module.legacy_plan(original[plane],bw);trials.append(op)
            if op['bytes']<plan['bytes']:coeff=original[plane]
        incumbent.append(coeff);legacy_trials.append(trials)
    baseline=module.gm.reconstruct(tuple(incumbent),p.prediction,q,p.width,p.height)
    output=[];payloads=[];details=[];ec_calls=cp_calls=sp_calls=0
    for plane,coeff in enumerate(incumbent):
        bw=((p.width if plane==0 else p.width//2)+7)//8
        menu,stats=candidates(module,p,q,coeff,plane,baseline[plane],policy)
        plans=[e._plane_plan(c,bw,module) for _,c in menu]
        selected=min(range(len(menu)),key=lambda i:plans[i]['bytes'])
        label,chosen=menu[selected];plan=plans[selected]
        data,ec_count,cp_count,sp_count=e._construct(chosen,bw,plan,module)
        assert len(data)==plan['bytes']<=plans[0]['bytes']
        assert np.array_equal(chosen[:,0,0],coeff[:,0,0])
        protected=protected_blocks(module,q,p.width,p.height,plane)
        assert np.array_equal(chosen[protected],coeff[protected])
        rebuilt=reconstruct_plane(module,chosen,p.prediction[plane],q,p.width,p.height,plane)
        source_sse=int(np.square(p.source[plane].astype(np.int64)-rebuilt).sum())
        assert source_sse<=stats['baseline_source_yuv_sse']+stats['allowed_extra_source_yuv_sse']
        stats.update(selected_label=label,selected_bytes=len(data),baseline_bytes=plans[0]['bytes'],
                     selected_source_yuv_sse=source_sse,changed_blocks=int(np.count_nonzero(np.any(chosen!=coeff,axis=(1,2)))),
                     removed_coefficients=int(np.count_nonzero(coeff)-np.count_nonzero(chosen)),
                     changed_coefficients=int(np.count_nonzero(chosen!=coeff)),
                     candidate_plans=[dict(label=v[0],bytes=pl['bytes'],plan=pl) for v,pl in zip(menu,plans)],
                     incumbent_legacy_trials=legacy_trials[plane])
        details.append(stats);output.append(chosen);payloads.append(data)
        ec_calls+=ec_count;cp_calls+=cp_count;sp_calls+=sp_count
    rebuilt=module.gm.reconstruct(tuple(output),p.prediction,q,p.width,p.height)
    outtag=module.C.reference_tag(rebuilt);qmap=module.roi.pack_map(q)
    body=module.HEADER.pack(module.MAGIC,module.VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,module.base.LIMIT,
                            p.reference_tag,outtag,len(qmap),len(p.vector_bytes),*(len(v) for v in payloads))+qmap+p.vector_bytes+b''.join(payloads)
    packet=body+struct.pack('<I',zlib.crc32(body));tap=module.decoder_tap_counts(p)
    work=dict(packet_bytes=len(packet),policy=policy,planes=details,rdo=rdo,search=p.work['search'],
              encode_prepared_wall_ms=(time.perf_counter_ns()-started)/1e6,analysis_paid_separately=True,
              ec26_size_counter_calls=sum(len(x['candidate_plans']) for x in details),
              actual_cp02_encode_calls=cp_calls,actual_sp01_construct_calls=sp_calls,ec26_construct_calls=ec_calls,
              decoder_reference_sample_reads=tap['reference_sample_fetches'],tap_work=tap,
              selected_alternative_planes=sum(v['selected_label']!='incumbent' for v in details),
              changed_blocks=sum(v['changed_blocks'] for v in details),protected_blocks=sum(v['protected_blocks'] for v in details),
              removed_coefficients=sum(v['removed_coefficients'] for v in details),
              changed_coefficients=sum(v['changed_coefficients'] for v in details),
              reference_tag=p.reference_tag.hex(),reconstructed_tag=outtag.hex())
    return packet,rebuilt,work


def encode_prepared(p,q,rdo_lambda=1,policy='shrink_strict'):
    return encode_with(m,p,q,rdo_lambda,policy)
