"""HX33/HS33 bounded component run coding; exact HU25/HX32 fallback.

The supplied HU25 and v32 packets are paid inherited fixtures. All work performed
here (including decoding both, all run/Huffman/Rice trials and sealing) is timed.
"""
from pathlib import Path
import struct,time
import numpy as np
HERE=Path(__file__).resolve().parent
from baseline import old,p,h
CHANNEL=struct.Struct('<BBIII');MAX_K=14

def _bits_blob(bits):
    n=(len(bits)+7)//8
    return (int(bits,2)<<(n*8-len(bits))).to_bytes(n,'big') if bits else b''

def _rice_encode(values):
    a=np.asarray(values,np.int64)
    if len(a)==0:return 0,0,b''
    sizes=[int(np.sum(a>>k))+len(a)*(k+1) for k in range(MAX_K+1)]
    k=min(range(MAX_K+1),key=lambda k:sizes[k])
    bits=''.join('0'*(int(x)>>k)+'1'+(format(int(x)&((1<<k)-1),f'0{k}b') if k else '') for x in a)
    assert len(bits)==sizes[k]
    return k,len(bits),_bits_blob(bits)

def _channel_encode(values):
    a=np.asarray(values,np.uint16).reshape(-1)
    candidates=[];trials=[]
    for scheme in (0,1,2):
        if scheme==0:symbols=a;runs=np.empty(0,np.int64)
        elif scheme==1:
            nz=np.flatnonzero(a);symbols=a[nz]
            runs=np.diff(np.r_[-1,nz,len(a)])-1
        else:
            starts=np.r_[0,np.flatnonzero(a[1:]!=a[:-1])+1]
            symbols=a[starts];runs=np.diff(np.r_[starts,len(a)])-1
        try:
            stream,stats=old._huff_encode(symbols) if len(symbols) else (b'',dict(symbols=0,maximum_code_bits=0,coded_bits=0,values=0))
        except ValueError as err:
            if str(err)!='bounded Huffman code depth':raise
            trials.append(dict(scheme=scheme,rejected='code-depth'));continue
        k,nbits,bits=_rice_encode(runs)
        payload=CHANNEL.pack(scheme,k,len(symbols),len(stream),nbits)+stream+bits
        stat=dict(scheme=scheme,k=k,events=len(symbols),runs=len(runs),rice_bits=nbits,bytes=len(payload),huffman=stats,
                  rice_k_trials=MAX_K+1 if len(runs) else 0)
        candidates.append((payload,stat));trials.append(stat)
    if not candidates:raise ValueError('no bounded channel candidate')
    payload,stat=min(candidates,key=lambda v:len(v[0]))
    return payload,dict(selected=stat,trials=trials)

def _encode_patch(current,prediction,mode,prefix=b''):
    parts=[];work=[];plain=mode&7
    components=h._components(current)
    pred=h._components(prediction) if prediction is not None else None
    for channel in range(3):
        values=components[channel].astype(np.int32)
        if plain==0:
            delta=values.copy();delta[:,1:]-=values[:,:-1]
        else:delta=values-pred[channel].astype(np.int32)
        if mode&8:before=delta.copy();delta[:,1:]-=before[:,:-1]
        mapped=np.where(delta>=0,2*delta,-2*delta-1)
        payload,stats=_channel_encode(mapped);parts.append(payload);work.append(stats)
    return prefix+b''.join(parts),work

def _pack_patch(current,reference,mode,payload):
    return p.seal(h.HEADER.pack(b'HS33',1,mode,current.shape[1],current.shape[0],len(payload),h.ZERO if mode==0 else h._tag(reference),h._tag(current))+payload)

def encode_hud(baseline,baseline32,reference=None,*,expected_reference_id=None):
    started=time.perf_counter_ns()
    current,meta=p.decode_hud(baseline,reference,expected_reference_id=expected_reference_id)
    prior,prior_meta=old.decode_hud(baseline32,reference,expected_reference_id=expected_reference_id)
    if len(baseline32)>len(baseline) or meta['reconstructed_tag']!=prior_meta['reconstructed_tag'] or any(meta[k]!=prior_meta[k] for k in ('epoch','frame_id','reference_id','reference_tag','rectangles')):raise ValueError('v32 baseline binding')
    for a,b in zip(current,prior):
        if not np.array_equal(a['words'],b['words']):raise ValueError('v32 baseline exact words')
    if meta['reference_id']==p.NO_REF:reference=None
    by_rect={v['rect']:v['words'] for v in reference or ()};payloads=[];types=[];details=[]
    for patch,old_kind,old_payload,prior_kind,prior_payload in zip(current,meta['types'],meta['payloads'],prior_meta['types'],prior_meta['payloads']):
        a=patch['words'];ref=by_rect.get(patch['rect']);candidates=[(prior_kind,prior_payload,None,None)];recipes=[(0,None,b'')]
        if ref is not None:
            recipes.extend([(1,ref,b''),(9,ref,b'')])
            if old_kind==2:
                old_mode=h.HEADER.unpack_from(old_payload)[2];data=old_payload[h.HEADER.size:-4]
                if old_mode in (h.GLOBAL,h.TILED):
                    mode=2 if old_mode==h.GLOBAL else 3;pred,n=old._motion_reference(ref,mode,data,a.shape[1],a.shape[0])
                    recipes.extend([(mode,pred,data[:n]),(mode|8,pred,data[:n])])
        trials=[]
        for mode,pred,prefix in recipes:
            try:payload,channels=_encode_patch(a,pred,mode,prefix)
            except ValueError as err:
                if str(err)!='no bounded channel candidate':raise
                trials.append(dict(mode=mode,bounded_fit=False,rejected='all-channel-Huffman-depth',channels=[]));continue
            packet=_pack_patch(a,ref,mode,payload);fits=len(packet)<=h.MAX_PACKET
            trials.append(dict(mode=mode,bytes=len(packet),bounded_fit=fits,channels=channels))
            if fits:candidates.append((4,packet,mode,channels))
        selected=min(candidates,key=lambda v:len(v[1]));types.append(selected[0]);payloads.append(selected[1])
        details.append(dict(rect=patch['rect'],hu25_bytes=len(old_payload),v32_bytes=len(prior_payload),selected_bytes=len(selected[1]),
                            selected_kind=selected[0],selected_mode=selected[2],selected_channels=selected[3],trials=trials))
    fields=list(p.HUD.unpack_from(baseline));fields[0]=b'HX33';fields[10:14]=[len(v) for v in payloads]+[0]*(4-len(payloads));fields[14:18]=types+[0]*(4-len(types))
    candidate=p.seal(p.HUD.pack(*fields)+b''.join(payloads));packet=candidate if len(candidate)<len(baseline32) else baseline32
    return packet,dict(hu25_bytes=len(baseline),v32_bytes=len(baseline32),packet_bytes=len(packet),selected_new=packet[:4]==b'HX33',patches=details,
                       encode_extra_wall_ms=(time.perf_counter_ns()-started)/1e6,hu25_generation_included=False,v32_generation_included=False,
                       baseline_motion_search_reused=True,all_run_huffman_rice_trials_included=True)

from decoder import decode_hud,decode_patch,decode_channel
