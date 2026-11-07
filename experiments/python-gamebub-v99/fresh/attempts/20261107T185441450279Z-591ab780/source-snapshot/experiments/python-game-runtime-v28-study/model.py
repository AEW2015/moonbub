"""GM27 host encoder with exact lazy legacy trials and unchanged wire/pixels.

Only winning fallback packets are serialized; size counters execute all legacy
decisions. The selected EC26 packet remains an actual construction. No frozen
module globals are modified.
"""
from pathlib import Path
import importlib.util
import struct
import sys
import time
import zlib
import numpy as np

HERE=Path(__file__).resolve().parent


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


base=load_module('runtime28_frozen27',HERE.parent/'python-game-unified-v27-study/model.py')
taps=load_module('runtime28_exact_taps',HERE.parent/'python-game-taps-v28-study/model.py')
C,gm,roi,ft,sr,ec=base.C,base.gm,base.roi,base.ft,base.sr,base.ec
Prepared,_PREPARED_OWNER=base.Prepared,base._PREPARED_OWNER
HEADER,MAGIC,VERSION,NO_REF=base.HEADER,base.MAGIC,base.VERSION,base.NO_REF
_id,parse_metadata,parse=base._id,base.parse_metadata,base.parse
analyze_planes,predict=base.analyze_planes,base.predict
decode=taps.decode
counter=base.counter


def decoder_tap_counts(prepared):
    if prepared.key:return dict(reference_sample_fetches=0,frozen_reference_sample_fetches=0)
    mw,mh=base._grid(prepared.width,prepared.height,prepared.block_size)
    vectors=base.unpack_vectors(prepared.vector_bytes,mw,mh).astype(np.int32)
    count=0
    for plane in range(3):
        ph,pw=(prepared.height,prepared.width) if plane==0 else (prepared.height//2,prepared.width//2)
        bs=prepared.block_size if plane==0 else prepared.block_size//2;den=2 if plane==0 else 4
        heights=np.minimum(bs,ph-np.arange(mh)*bs);widths=np.minimum(bs,pw-np.arange(mw)*bs)
        fractional=vectors%den!=0
        count+=int((heights[:,None]*widths[None,:]*(1+fractional[...,0].astype(np.int64))*(1+fractional[...,1])).sum())
    return dict(reference_sample_fetches=count,frozen_reference_sample_fetches=4*prepared.width*prepared.height*3//2)


def legacy_plan(coeff,bw):
    """Exact incumbent size and representation, no coefficient serialization."""
    counter._check(coeff,bw)
    if not np.any(coeff):
        return dict(bytes=1,kind='zero',logical_candidates=1,size_counter_calls=0,full_blocks=0,dc_blocks=0)
    dense=1+counter.count_packets(coeff,bw)
    modes,dc,full=sr.classifications(coeff)
    subset=counter.count_packets(coeff[full],1) if np.any(full) else 0
    split=1+sr.PLANE.size+(len(coeff)+3)//4+2*int(dc.sum())+subset
    return dict(bytes=min(dense,split),kind='split' if split<dense else 'dense',
                dense_bytes=dense,split_bytes=split,logical_candidates=3,size_counter_calls=1+int(np.any(full)),
                full_blocks=int(full.sum()),dc_blocks=int(dc.sum()))


def build_legacy(coeff,bw,plan):
    if plan['kind']=='zero':return b'\x02',0,0
    if plan['kind']=='dense':return b'\x00'+gm.token_coeff.encode_coefficients(coeff,bw),1,0
    modes,dc,full=sr.classifications(coeff)
    payload=gm.token_coeff.encode_coefficients(coeff[full],1) if np.any(full) else b''
    output=(b'\x01'+sr.PLANE.pack(sr.PLANE_MAGIC,1,len(coeff),(len(coeff)+3)//4,int(dc.sum()),len(payload))
            +sr.pack_modes(modes)+coeff[dc,0,0].astype('<i2').tobytes()+payload)
    return output,int(np.any(full)),1


def encode_prepared(prepared,scale_map,rdo_lambda=1):
    started=time.perf_counter_ns();p=prepared
    if not isinstance(p,Prepared) or p.owner is not _PREPARED_OWNER:raise ValueError('owned GM27 preparation')
    if type(rdo_lambda) not in (int,float) or not np.isfinite(rdo_lambda) or not 0<=rdo_lambda<=1000000:raise ValueError('RDO lambda')
    q=roi.check_map(scale_map,p.width,p.height)
    began=time.perf_counter_ns();original=base._quantize(p.raw_coefficients,q,p.width,p.height);quant_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();pruned,rdo=counter.rdo_skip(p,original,q,rdo_lambda);rdo_ms=(time.perf_counter_ns()-began)/1e6
    began=time.perf_counter_ns();coefficients=[];payloads=[];details=[]
    for plane,candidate in enumerate(pruned):
        bw=((p.width if plane==0 else p.width//2)+7)//8
        plan=legacy_plan(candidate,bw);trials=[plan];reverted=False
        if not np.array_equal(candidate,original[plane]):
            original_plan=legacy_plan(original[plane],bw);trials.append(original_plan)
            if original_plan['bytes']<plan['bytes']:candidate,plan,reverted=original[plane],original_plan,True
        # Every valid EC26 packet costs at least46Bheader+CRC,2BDC and6Bband
        # parameters, plus1Bdispatch. Incumbent wins all ties.
        if plan['bytes']<=55:
            ec_payload=None;ec_skipped=True
        else:
            ec_payload=b'\x03'+ec.encode_coefficients(candidate,bw,layout=0);ec_skipped=False
        cp_calls=sp_calls=0
        if ec_payload is not None and len(ec_payload)<plan['bytes']:
            selected=ec_payload;mode='EC26'
        else:selected,cp_calls,sp_calls=build_legacy(candidate,bw,plan);mode=plan['kind']
        assert len(selected)<=plan['bytes']
        payloads.append(selected);coefficients.append(candidate)
        details.append(dict(selected_mode=mode,selected_bytes=len(selected),legacy_selected_bytes=plan['bytes'],
                            legacy_trials=trials,rdo_reverted=reverted,size_counter_calls=sum(x['size_counter_calls'] for x in trials),
                            logical_legacy_candidates=sum(x['logical_candidates'] for x in trials),
                            actual_cp02_encode_calls=cp_calls,actual_sp01_construct_calls=sp_calls,
                            ec26_construct_calls=not ec_skipped,ec26_lower_bound_skipped=ec_skipped,
                            ec26_bytes=None if ec_payload is None else len(ec_payload)))
    entropy_ms=(time.perf_counter_ns()-began)/1e6;coefficients=tuple(coefficients)
    rebuilt=gm.reconstruct(coefficients,p.prediction,q,p.width,p.height)
    outtag=C.reference_tag(rebuilt);qmap=roi.pack_map(q)
    body=HEADER.pack(MAGIC,VERSION,int(p.key),p.epoch,p.frame_id,p.reference_id,p.width,p.height,p.block_size,base.LIMIT,
                     p.reference_tag,outtag,len(qmap),len(p.vector_bytes),*(len(v) for v in payloads))+qmap+p.vector_bytes+b''.join(payloads)
    packet=body+struct.pack('<I',zlib.crc32(body));tap_work=decoder_tap_counts(p)
    rdo['proposed_zeroed_blocks']=rdo['zeroed_blocks'];rdo['proposed_source_sse_increase']=rdo.pop('source_sse_increase')
    rdo['zeroed_blocks']=sum(int(np.count_nonzero(np.any(a!=0,axis=(1,2)) & ~np.any(b!=0,axis=(1,2)))) for a,b in zip(original,coefficients))
    work=dict(packet_bytes=len(packet),planes=details,rdo=rdo,quantize_ms=quant_ms,rdo_ms=rdo_ms,entropy_ms=entropy_ms,
              search=p.work['search'],search_ms=0.,forward_plane_calls=0,analysis_paid_separately=True,
              encode_prepared_wall_ms=(time.perf_counter_ns()-started)/1e6,
              legacy_size_counter_calls=sum(x['size_counter_calls'] for x in details),
              logical_legacy_candidates=sum(x['logical_legacy_candidates'] for x in details),
              actual_cp02_encode_calls=sum(x['actual_cp02_encode_calls'] for x in details),
              actual_sp01_construct_calls=sum(x['actual_sp01_construct_calls'] for x in details),
              ec26_construct_calls=sum(x['ec26_construct_calls'] for x in details),
              decoder_reference_sample_reads=tap_work['reference_sample_fetches'],tap_work=tap_work,
              reference_tag=p.reference_tag.hex(),reconstructed_tag=outtag.hex())
    return packet,rebuilt,work


def encode_planes(source,reference,scale_map,*,rdo_lambda=1,**kwargs):
    p=analyze_planes(source,reference,**kwargs);packet,out,work=encode_prepared(p,scale_map,rdo_lambda)
    work['analysis']=p.work;work['analysis_paid_separately']=False
    work['encoder_wall_ms']=p.work['analysis_wall_ms']+work['encode_prepared_wall_ms']
    return packet,out,work
