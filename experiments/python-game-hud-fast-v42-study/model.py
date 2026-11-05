"""Exact HUD32/33 planning and NumPy bit packing; no frozen-global mutation.

Every recipe, Huffman tree, Rice-k and channel scheme remains paid. Only chosen
patch/channel streams are materialized; no source-symbol format strings exist.
Plans are per-call owned temporaries, not externally reusable caches.
"""
import struct,time
import numpy as np
import helpers as h
STREAM=h.hud32.STREAM;CHANNEL=h.hud33.CHANNEL

def _pack_codes(values,lengths):
    a=np.asarray(values,np.uint16).reshape(-1);codes=h.hud32._codes(lengths)
    if not len(a)or len(a)>h.h.MAX_WORDS or int(a.max())>252 or any(int(v)not in codes for v in np.unique(a)):
        raise ValueError('symbol count/domain')
    if len(codes)==1:return b'',0
    code_lut=np.zeros(253,np.uint32);length_lut=np.zeros(253,np.uint8)
    for symbol,(code,length)in codes.items():code_lut[symbol]=code;length_lut[symbol]=length
    widths=length_lut[a];positions=np.arange(16,dtype=np.int32)[None,:]
    shifts=np.maximum(widths.astype(np.int32)[:,None]-1-positions,0).astype(np.uint32)
    bits=((code_lut[a,None]>>shifts)&1)[positions<widths[:,None]].astype(np.uint8)
    return np.packbits(bits,bitorder='big').tobytes(),len(bits)

def _huff_plan(values):
    a=np.asarray(values,np.uint16).reshape(-1).copy()
    if not 0<len(a)<=h.h.MAX_WORDS or int(a.max())>252:raise ValueError('symbol count/domain')
    lengths=h.hud32._lengths(a);h.hud32._codes(lengths)
    counts=np.bincount(a,minlength=253)
    bits=0 if len(lengths)==1 else sum(int(counts[s])*n for s,n in lengths.items())
    stats=dict(symbols=len(lengths),maximum_code_bits=max(lengths.values()),coded_bits=bits,values=len(a))
    return dict(values=a,lengths=lengths,bits=bits,bytes=STREAM.size+2*len(lengths)+(bits+7)//8,stats=stats)

def _huff_emit(plan,work=None):
    bits,nbits=_pack_codes(plan['values'],plan['lengths'])
    if nbits!=plan['bits']:raise ValueError('owned Huffman plan mismatch')
    table=bytes(v for s,n in sorted(plan['lengths'].items())for v in(s,n))
    result=STREAM.pack(len(plan['lengths']),nbits)+table+bits
    if len(result)!=plan['bytes']:raise ValueError('Huffman planned length')
    if work is not None:work['huffman_materializations']+=1
    return result

def huff_encode(values):
    plan=_huff_plan(values);return _huff_emit(plan),plan['stats']

def _rice_plan(values):
    a=np.asarray(values,np.int64)
    if a.ndim!=1 or len(a)>h.h.MAX_WORDS+1 or np.any(a<0)or np.any(a>h.h.MAX_WORDS)or int(a.sum())>h.h.MAX_WORDS:
        raise ValueError('bounded nonnegative run sequence')
    a=a.copy()
    if not len(a):return dict(values=a,k=0,bits=0,bytes=0,k_costs=[0]*15)
    sizes=[int((a>>k).sum())+len(a)*(k+1)for k in range(15)];k=min(range(15),key=lambda k:sizes[k])
    return dict(values=a,k=k,bits=sizes[k],bytes=(sizes[k]+7)//8,k_costs=sizes)

def _rice_emit(plan,work=None):
    a=plan['values'];k=plan['k'];bits=np.zeros(plan['bits'],np.uint8)
    if len(a):
        quotient=a>>k;lengths=quotient+1+k;starts=np.r_[0,np.cumsum(lengths[:-1])];delimiters=starts+quotient
        bits[delimiters]=1
        if k:
            suffix=delimiters[:,None]+1+np.arange(k)[None,:]
            bits[suffix]=((a[:,None]>>np.arange(k-1,-1,-1)[None,:])&1).astype(np.uint8)
        if int(lengths.sum())!=plan['bits']:raise ValueError('owned Rice plan mismatch')
    if work is not None:work['rice_materializations']+=1
    return np.packbits(bits,bitorder='big').tobytes()

def rice_encode(values):
    plan=_rice_plan(values);return plan['k'],plan['bits'],_rice_emit(plan)

def _channel_plan(values,work):
    a=np.asarray(values,np.uint16).reshape(-1);options=[];trials=[]
    if not 0<len(a)<=h.h.MAX_WORDS or int(a.max())>252:raise ValueError('mapped channel count/domain')
    for scheme in(0,1,2):
        if scheme==0:symbols=a;runs=np.empty(0,np.int64)
        elif scheme==1:
            nz=np.flatnonzero(a);symbols=a[nz];runs=np.diff(np.r_[-1,nz,len(a)])-1
        else:
            starts=np.r_[0,np.flatnonzero(a[1:]!=a[:-1])+1];symbols=a[starts];runs=np.diff(np.r_[starts,len(a)])-1
        try:
            hp=_huff_plan(symbols)if len(symbols)else None
            if hp is not None:work['huffman_plans']+=1
        except ValueError as error:
            if str(error)!='bounded Huffman code depth':raise
            trials.append(dict(scheme=scheme,rejected='code-depth'));continue
        rp=_rice_plan(runs);work['rice_k_trials']+=15 if len(runs)else 0
        stats=dict(scheme=scheme,k=rp['k'],events=len(symbols),runs=len(runs),rice_bits=rp['bits'],
            bytes=CHANNEL.size+(hp['bytes']if hp else 0)+rp['bytes'],huffman=hp['stats']if hp else dict(symbols=0,maximum_code_bits=0,coded_bits=0,values=0),
            rice_k_trials=15 if len(runs)else 0)
        options.append(dict(huff=hp,rice=rp,stats=stats));trials.append(stats)
    if not options:raise ValueError('no bounded channel candidate')
    return min(options,key=lambda p:p['stats']['bytes']),trials

def _channel_emit(plan,work):
    stats=plan['stats'];stream=_huff_emit(plan['huff'],work)if plan['huff']else b'';runs=_rice_emit(plan['rice'],work)
    data=CHANNEL.pack(stats['scheme'],stats['k'],stats['events'],len(stream),stats['rice_bits'])+stream+runs
    if len(data)!=stats['bytes']:raise ValueError('planned channel length')
    return data

def channel_encode(values):
    work=_work();plan,trials=_channel_plan(values,work);return _channel_emit(plan,work),dict(selected=plan['stats'],trials=trials)

def _work():return dict(huffman_plans=0,huffman_materializations=0,rice_k_trials=0,rice_materializations=0,patch_materializations=0)

def _recipes(reference,old_kind,old_payload,a):
    recipes=[(0,None,b'')]
    if reference is not None:
        recipes.extend([(1,reference,b''),(9,reference,b'')])
        if old_kind==2:
            old_mode=h.h.HEADER.unpack_from(old_payload)[2];data=old_payload[h.h.HEADER.size:-4]
            if old_mode in(h.h.GLOBAL,h.h.TILED):
                mode=2 if old_mode==h.h.GLOBAL else 3
                prediction,length=h.hud32._motion_reference(reference,mode,data,a.shape[1],a.shape[0])
                recipes.extend([(mode,prediction,data[:length]),(mode|8,prediction,data[:length])])
    return recipes

def _mapped_channels(current,prediction,mode):
    current=h.h._array(current);components=h.h._components(current)
    pred=h.h._components(prediction)if prediction is not None else None
    mapped=[]
    for axis in range(3):
        values=components[axis].astype(np.int32)
        if mode&7==0:delta=values.copy();delta[:,1:]-=values[:,:-1]
        else:delta=values-pred[axis].astype(np.int32)
        if mode&8:before=delta.copy();delta[:,1:]-=before[:,:-1]
        mapped.append(np.where(delta>=0,2*delta,-2*delta-1))
    return mapped

def _patch_plan(current,prediction,mode,prefix,version,work):
    plans=[];stats=[]
    for values in _mapped_channels(current,prediction,mode):
        if version==32:
            plan=_huff_plan(values);work['huffman_plans']+=1;plans.append(plan);stats.append(plan['stats'])
        else:
            plan,trials=_channel_plan(values,work);plans.append(plan);stats.append(dict(selected=plan['stats'],trials=trials))
    payload_bytes=len(prefix)+sum(p['bytes']if version==32 else p['stats']['bytes']for p in plans)
    return dict(mode=mode,prefix=prefix,channels=plans,channel_stats=stats,payload_bytes=payload_bytes,
                packet_bytes=h.h.FIXED_BYTES+payload_bytes,version=version)

def _patch_emit(current,reference,plan,work):
    pieces=[_huff_emit(p,work)if plan['version']==32 else _channel_emit(p,work)for p in plan['channels']]
    payload=plan['prefix']+b''.join(pieces);magic=b'HS32'if plan['version']==32 else b'HS33'
    packet=h.p.seal(h.h.HEADER.pack(magic,1,plan['mode'],current.shape[1],current.shape[0],len(payload),
        h.h.ZERO if plan['mode']==0 else h.h._tag(reference),h.h._tag(current))+payload)
    if len(packet)!=plan['packet_bytes']:raise ValueError('planned patch length')
    work['patch_materializations']+=1;return packet

def encode_hud32(baseline,reference=None,*,expected_reference_id=None):
    start=time.perf_counter_ns();current,meta=h.p.decode_hud(baseline,reference,expected_reference_id=expected_reference_id)
    if meta['reference_id']==h.p.NO_REF:reference=None
    by_rect={p['rect']:p['words']for p in reference or()};payloads=[];types=[];details=[];work=_work()
    for patch,kind,old_payload in zip(current,meta['types'],meta['payloads'],strict=True):
        a=patch['words'];ref=by_rect.get(patch['rect']);candidates=[dict(kind=kind,payload=old_payload,plan=None,bytes=len(old_payload))];trials=[]
        for mode,pred,prefix in _recipes(ref,kind,old_payload,a):
            try:plan=_patch_plan(a,pred,mode,prefix,32,work)
            except ValueError as error:
                if str(error)!='bounded Huffman code depth':raise
                trials.append(dict(mode=mode,rejected='code-depth'));continue
            fits=plan['packet_bytes']<=h.h.MAX_PACKET
            trials.append(dict(mode=mode,bytes=plan['packet_bytes'],bounded_fit=fits,channels=plan['channel_stats']))
            if fits:candidates.append(dict(kind=3,payload=None,plan=plan,bytes=plan['packet_bytes']))
        chosen=min(candidates,key=lambda p:p['bytes']);payload=chosen['payload']if chosen['plan']is None else _patch_emit(a,ref,chosen['plan'],work)
        payloads.append(payload);types.append(chosen['kind']);details.append(dict(rect=patch['rect'],baseline_bytes=len(old_payload),baseline_kind=kind,
            selected_bytes=len(payload),selected_kind=chosen['kind'],selected_mode=None if chosen['plan']is None else chosen['plan']['mode'],trials=trials))
    fields=list(h.p.HUD.unpack_from(baseline));fields[0]=b'HX32';fields[10:14]=[len(v)for v in payloads]+[0]*(4-len(payloads));fields[14:18]=types+[0]*(4-len(types))
    candidate=h.p.seal(h.p.HUD.pack(*fields)+b''.join(payloads));packet=candidate if len(candidate)<len(baseline)else baseline
    wall=(time.perf_counter_ns()-start)/1e6
    return packet,dict(baseline_bytes=len(baseline),packet_bytes=len(packet),selected_new=packet[:4]==b'HX32',patches=details,
        encode_extra_wall_ms=wall,encode_ms=wall,work=work,baseline_motion_search_reused=True,baseline_encode_cost_included=False,
        maximum_code_bits=16,maximum_table_entries_per_channel=253,receiver_reference_hud_words=sum(p['words'].size for p in current),
        proposed_ESP32_role='opaque bounded transport, no Huffman decode',source_words=sum(p['words'].size for p in current),
        baseline_decode_validation_paid=True,cache_used=False,hu25_generation_externally_paid=True)

def encode_hud33(baseline,baseline32,reference=None,*,expected_reference_id=None):
    start=time.perf_counter_ns();current,meta=h.p.decode_hud(baseline,reference,expected_reference_id=expected_reference_id)
    prior,prior_meta=h.hud32.decode_hud(baseline32,reference,expected_reference_id=expected_reference_id)
    if len(baseline32)>len(baseline)or meta['reconstructed_tag']!=prior_meta['reconstructed_tag']or any(meta[k]!=prior_meta[k]for k in('epoch','frame_id','reference_id','reference_tag','rectangles')):
        raise ValueError('v32 baseline binding')
    for a,b in zip(current,prior,strict=True):
        if not np.array_equal(a['words'],b['words']):raise ValueError('v32 baseline exact words')
    if meta['reference_id']==h.p.NO_REF:reference=None
    by_rect={p['rect']:p['words']for p in reference or()};payloads=[];types=[];details=[];work=_work()
    for patch,old_kind,old_payload,kind,prior_payload in zip(current,meta['types'],meta['payloads'],prior_meta['types'],prior_meta['payloads'],strict=True):
        a=patch['words'];ref=by_rect.get(patch['rect']);options=[dict(kind=kind,payload=prior_payload,plan=None,bytes=len(prior_payload))];trials=[]
        for mode,pred,prefix in _recipes(ref,old_kind,old_payload,a):
            try:plan=_patch_plan(a,pred,mode,prefix,33,work)
            except ValueError as error:
                if str(error)!='no bounded channel candidate':raise
                trials.append(dict(mode=mode,bounded_fit=False,rejected='all-channel-Huffman-depth',channels=[]));continue
            fits=plan['packet_bytes']<=h.h.MAX_PACKET
            trials.append(dict(mode=mode,bytes=plan['packet_bytes'],bounded_fit=fits,channels=plan['channel_stats']))
            if fits:options.append(dict(kind=4,payload=None,plan=plan,bytes=plan['packet_bytes']))
        chosen=min(options,key=lambda p:p['bytes']);payload=chosen['payload']if chosen['plan']is None else _patch_emit(a,ref,chosen['plan'],work)
        payloads.append(payload);types.append(chosen['kind']);details.append(dict(rect=patch['rect'],hu25_bytes=len(old_payload),v32_bytes=len(prior_payload),
            selected_bytes=len(payload),selected_kind=chosen['kind'],selected_mode=None if chosen['plan']is None else chosen['plan']['mode'],
            selected_channels=None if chosen['plan']is None else chosen['plan']['channel_stats'],trials=trials))
    fields=list(h.p.HUD.unpack_from(baseline));fields[0]=b'HX33';fields[10:14]=[len(v)for v in payloads]+[0]*(4-len(payloads));fields[14:18]=types+[0]*(4-len(types))
    candidate=h.p.seal(h.p.HUD.pack(*fields)+b''.join(payloads));packet=candidate if len(candidate)<len(baseline32)else baseline32
    wall=(time.perf_counter_ns()-start)/1e6
    return packet,dict(hu25_bytes=len(baseline),v32_bytes=len(baseline32),packet_bytes=len(packet),selected_new=packet[:4]==b'HX33',patches=details,
        encode_extra_wall_ms=wall,encode_ms=wall,work=work,hu25_generation_included=False,v32_generation_included=False,
        baseline_motion_search_reused=True,all_run_huffman_rice_trials_included=True,
        baseline_HU25_and_HX32_decode_validation_paid=True,cache_used=False,hu25_generation_externally_paid=True)
