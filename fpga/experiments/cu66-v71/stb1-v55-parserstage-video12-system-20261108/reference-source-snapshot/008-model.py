"""Exact fixedzero Prepared construction with frozen zero-map copy predictor.

No old analyzer call, no slow prediction first and no frozen-global mutation.
The owned Prepared contract, source validation, vector grammar and forward
transform remain identical. Only the zero-motion prediction implementation
changes from redundant four-tap arithmetic to the frozen exact copy path.
"""
import time
import numpy as np
import helpers as h

def analyze_planes(source,reference,*,epoch=25,frame_id=0,reference_id=h.m.NO_REF,
                   block_size=32,motion_mode='zero',penalty=0,motion_precision='half'):
    start=time.perf_counter_ns();old=h.m.base.old
    src=old._planes(source);height,width=src[0].shape
    if (width,height)!=(720,480):raise ValueError('fixed CN36 source geometry')
    if epoch!=25 or not old._id(epoch) or not old._id(frame_id):raise ValueError('fixed epoch/bounded frame')
    if type(block_size)is not int or block_size!=32:raise ValueError('fixed block32')
    if motion_mode!='zero' or motion_precision!='half' or type(penalty)is not int or penalty!=0:
        raise ValueError('explicit fixedzero halfpel policy')
    mw,mh=old._grid(width,height,block_size);key=reference is None
    if key:
        if type(reference_id)is not int or reference_id!=h.m.NO_REF:raise ValueError('key reference identity')
        prediction=tuple(np.full_like(p,128) for p in src);vector_bytes=b'';reftag=old.ZERO_TAG
        search=dict(candidate_vectors=0,sad_sample_operations=0,nonzero_vectors=0);search_ms=0.
        vector_work=dict(candidate_representations=0,candidates=[],rice_axis_trials=0,rice_delta_values=0,
                         rice_value_encode_trials=0,selected_mode=None,pack_wall_ms=0.)
    else:
        if not old._id(reference_id) or reference_id>=frame_id:raise ValueError('past reference identity')
        ref=old._planes(reference,(width,height));reftag=old.C.reference_tag(ref)
        began=time.perf_counter_ns()
        vectors,search=old.estimate_vectors(src,ref,block_size,'zero',0,'half')
        search_ms=(time.perf_counter_ns()-began)/1e6
        prediction=h.m.taps.predict(ref,vectors,block_size)
        vector_bytes,vector_work=old.pack_vectors(vectors,return_work=True)
    began=time.perf_counter_ns();raw=old._forward(src,prediction);transform_ms=(time.perf_counter_ns()-began)/1e6
    for p in prediction:p.setflags(write=False)
    retained=tuple(v.copy() for v in src)
    for v in retained:v.setflags(write=False)
    work=dict(key=key,motion_mode='zero',block_size=32,search=search,motion_map=vector_work,
              search_ms=search_ms,forward_plane_calls=3,transform_ms=transform_ms,
              prediction_array_bytes=sum(p.nbytes for p in prediction),raw_coefficient_array_bytes=sum(p.nbytes for p in raw),
              source_array_bytes=sum(p.nbytes for p in retained),retained_analysis_array_bytes=sum(p.nbytes for p in prediction+raw+retained),
              analysis_wall_ms=(time.perf_counter_ns()-start)/1e6,reference_tag=reftag.hex(),
              old_analyze_calls=0,old_four_tap_prediction_calls=0,zero_map_copy_prediction=not key)
    return h.m.Prepared(h.m._PREPARED_OWNER,25,frame_id,reference_id,width,height,key,32,'zero',reftag,
                        vector_bytes,prediction,raw,retained,work)
