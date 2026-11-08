"""Exact EC26 length planning and bounded source-error-guarded GM27 selection.

Counter executes all parameter minimization, run generation, and byte padding;
no strings, CRCs, or serialized coefficients are allocated by the counter.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('entropy29_runtime28',HERE.parent/'python-game-runtime-v28-study/model.py')
m=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=m;_spec.loader.exec_module(m)
ec=m.ec


def _best(values,maximum,escape):
    values=np.asarray(values,np.int64)
    if np.any(values<0) or np.any(values>=1<<escape):raise ValueError('Rice domain')
    costs=[int(np.where((values>>k)<15,(values>>k)+1+k,15+escape).sum()) for k in range(maximum+1)]
    k=int(np.argmin(costs));return k,costs[k]


def plan_coefficients(coefficients,blocks_w,*,layout=0):
    a=ec.f._check(coefficients,blocks_w)
    if type(layout) is not int or layout not in (0,1):raise ValueError('EC26 layout')
    zig=a.reshape(-1,64)[:,ec.f.frozen.ZIGZAG].astype(np.int32)
    dc=zig[:,0].copy();dc[1:]-=zig[:-1,0];dc[::blocks_w]=zig[::blocks_w,0]
    kd,dc_bits=_best(ec.f._mapped(dc),13,14)
    lengths=[1+(dc_bits+7)//8];counts=[];parameters=[[kd]];bits=[dc_bits]
    for lo,hi in ec.BANDS:
        band=zig[:,lo:hi];seq=(band if layout==0 else band.T).reshape(-1)
        indices=np.flatnonzero(seq);runs=np.diff(np.r_[-1,indices])-1
        levels=ec.f._mapped(seq[indices])-1
        kr,rb=_best(runs,19,24);kv,vb=_best(levels,11,12)
        lengths.append(2+(rb+vb+7)//8);counts.append(int(len(indices)));parameters.append([kr,kv]);bits.append(rb+vb)
    raw=sum(lengths)>=a.size*2
    payload=a.size*2 if raw else sum(lengths)
    return dict(bytes=ec.COEFF.size+4+payload,raw=raw,layout=layout,stream_lengths=lengths,
                parameters=parameters,nonzero_band_counts=counts,stream_bits=bits,
                coefficient_values=int(a.size),rice_parameter_trials=14+3*(20+12),serialized_packets=0)


def count_coefficients(coefficients,blocks_w,*,layout=0):
    return plan_coefficients(coefficients,blocks_w,layout=layout)['bytes']


def _plane_plan(coeff,bw,module):
    legacy=module.legacy_plan(coeff,bw);entropy=plan_coefficients(coeff,bw)
    actual=entropy['bytes']+1
    return dict(bytes=min(legacy['bytes'],actual),mode='EC26' if actual<legacy['bytes'] else legacy['kind'],legacy=legacy,ec26=entropy)


def _construct(coeff,bw,plan,module):
    if plan['mode']=='EC26':return b'\x03'+module.ec.encode_coefficients(coeff,bw,layout=0),1,0,0
    data,cp,sp=module.build_legacy(coeff,bw,plan['legacy']);return data,0,cp,sp


def encode_with(module,prepared,scale_map,rdo_lambda=1):
    started=time.perf_counter_ns();p=prepared
    if not isinstance(p,module.Prepared) or p.owner is not module._PREPARED_OWNER:raise ValueError('owned GM27 preparation')
    if type(rdo_lambda) not in (int,float) or not np.isfinite(rdo_lambda) or not 0<=rdo_lambda<=1000000:raise ValueError('RDO lambda')
    q=module.roi.check_map(scale_map,p.width,p.height)
    original=module.base._quantize(p.raw_coefficients,q,p.width,p.height)
    pruned,rdo=module.counter.rdo_skip(p,original,q,rdo_lambda)
    # Reproduce v28 choice first: legacy lengths decide original-vs-pruned.
    incumbent=[];legacy_trials=[]
    for plane,candidate in enumerate(pruned):
        bw=((p.width if plane==0 else p.width//2)+7)//8
        cp=module.legacy_plan(candidate,bw);trials=[cp]
        if not np.array_equal(candidate,original[plane]):
            op=module.legacy_plan(original[plane],bw);trials.append(op)
            if op['bytes']<cp['bytes']:candidate=original[plane]
        incumbent.append(candidate);legacy_trials.append(trials)
    baseline=module.gm.reconstruct(tuple(incumbent),p.prediction,q,p.width,p.height)
    baseline_sse=[int(np.square(s.astype(np.int64)-v).sum()) for s,v in zip(p.source,baseline)]
    coefficients=[];details=[];payloads=[];ec_calls=cp_calls=sp_calls=0
    for plane,basecoeff in enumerate(incumbent):
        bw=((p.width if plane==0 else p.width//2)+7)//8
        candidates=[('incumbent',basecoeff)]
        for label,candidate in (('original',original[plane]),('pruned',pruned[plane])):
            if not any(np.array_equal(candidate,v) for _,v in candidates):candidates.append((label,candidate))
        records=[];eligible=[]
        for label,candidate in candidates:
            plan=_plane_plan(candidate,bw,module)
            if label=='incumbent':sse=baseline_sse[plane]
            else:
                trial=list(incumbent);trial[plane]=candidate
                rebuilt=module.gm.reconstruct(tuple(trial),p.prediction,q,p.width,p.height)
                sse=int(np.square(p.source[plane].astype(np.int64)-rebuilt[plane]).sum())
            record=dict(label=label,bytes=plan['bytes'],source_yuv_sse=sse,quality_eligible=sse<=baseline_sse[plane],plan=plan)
            records.append(record)
            if record['quality_eligible']:eligible.append((plan['bytes'],len(records)-1,candidate,plan))
        _,selected_index,candidate,plan=min(eligible,key=lambda v:(v[0],v[1]))
        data,ec_count,cp_count,sp_count=_construct(candidate,bw,plan,module)
        assert len(data)==plan['bytes']
        ec_calls+=ec_count;cp_calls+=cp_count;sp_calls+=sp_count
        coefficients.append(candidate);payloads.append(data)
        records[selected_index]['selected']=True
        details.append(dict(selected_label=records[selected_index]['label'],selected_mode=plan['mode'],selected_bytes=len(data),
                            baseline_bytes=records[0]['bytes'],baseline_source_yuv_sse=baseline_sse[plane],
                            candidate_plans=records,incumbent_legacy_trials=legacy_trials[plane]))
    rebuilt=module.gm.reconstruct(tuple(coefficients),p.prediction,q,p.width,p.height)
    outtag=module.C.reference_tag(rebuilt);qmap=module.roi.pack_map(q)
    body=module.HEADER.pack(module.MAGIC,module.VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,module.base.LIMIT,
                            p.reference_tag,outtag,len(qmap),len(p.vector_bytes),*(len(v) for v in payloads))+qmap+p.vector_bytes+b''.join(payloads)
    packet=body+struct.pack('<I',zlib.crc32(body));tap=module.decoder_tap_counts(p)
    work=dict(packet_bytes=len(packet),planes=details,rdo=rdo,search=p.work['search'],
              encode_prepared_wall_ms=(time.perf_counter_ns()-started)/1e6,analysis_paid_separately=True,
              ec26_size_counter_calls=sum(len(v['candidate_plans']) for v in details),
              legacy_size_counter_calls=sum(sum(x['size_counter_calls'] for x in d['incumbent_legacy_trials'])+
                  sum(r['plan']['legacy']['size_counter_calls'] for r in d['candidate_plans']) for d in details),
              actual_cp02_encode_calls=cp_calls,actual_sp01_construct_calls=sp_calls,ec26_construct_calls=ec_calls,
              decoder_reference_sample_reads=tap['reference_sample_fetches'],tap_work=tap,
              selected_alternative_planes=sum(v['selected_label']!='incumbent' for v in details),
              source_yuv_sse_guard=True,reference_tag=p.reference_tag.hex(),reconstructed_tag=outtag.hex())
    return packet,rebuilt,work


def encode_prepared(prepared,scale_map,rdo_lambda=1):
    return encode_with(m,prepared,scale_map,rdo_lambda)
