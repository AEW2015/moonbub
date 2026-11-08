"""HX32: exact HUD component-Huffman residuals, old HU25 byte fallback.

Host-only encoder/reassembly model. Canonical Huffman tables have <=253 symbols
and <=16-bit codes. Motion fields are reused from a paid retained HU25 baseline.
"""
from pathlib import Path
import hashlib,heapq,importlib.util,struct,sys,time,zlib
import numpy as np
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('hud32_frozen_cp27',HERE.parent/'python-game-runtime-v28-study/protocol.py')
p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
h=p.hud_codec
STREAM=struct.Struct('<HI');MAX_CODE=16

def _lengths(values):
    symbols,counts=np.unique(values,return_counts=True)
    heap=[];uid=0
    for s,n in zip(symbols,counts):heap.append((int(n),uid,int(s)));uid+=1
    heapq.heapify(heap)
    if len(heap)==1:return {heap[0][2]:1}
    while len(heap)>1:
        a,b=heapq.heappop(heap),heapq.heappop(heap);heapq.heappush(heap,(a[0]+b[0],uid,(a[2],b[2])));uid+=1
    result={}
    def walk(node,depth):
        if isinstance(node,int):result[node]=depth
        else:walk(node[0],depth+1);walk(node[1],depth+1)
    walk(heap[0][2],0)
    if max(result.values())>MAX_CODE:raise ValueError('bounded Huffman code depth')
    return result

def _codes(lengths):
    if not lengths or any(type(s) is not int or not 0<=s<=252 or type(n) is not int or not 1<=n<=MAX_CODE for s,n in lengths.items()):raise ValueError('Huffman table domain')
    if len(lengths)==1:
        if next(iter(lengths.values()))!=1:raise ValueError('constant Huffman code')
        return {next(iter(lengths)): (0,1)}
    code=0;prior=0;result={}
    for symbol,length in sorted(lengths.items(),key=lambda v:(v[1],v[0])):
        code<<=length-prior
        if code>=1<<length:raise ValueError('oversubscribed Huffman table')
        result[symbol]=(code,length);code+=1;prior=length
    if code!=1<<prior:raise ValueError('incomplete Huffman table')
    return result

def _huff_encode(values):
    a=np.asarray(values,np.uint16).reshape(-1)
    if not 0<len(a)<=h.MAX_WORDS or int(a.max())>252:raise ValueError('symbol count/domain')
    lengths=_lengths(a);codes=_codes(lengths)
    bits='' if len(codes)==1 else ''.join(format(codes[int(v)][0],f'0{codes[int(v)][1]}b') for v in a)
    nb=(len(bits)+7)//8;stream=(int(bits,2)<<(nb*8-len(bits))).to_bytes(nb,'big') if bits else b''
    table=bytes(v for s,n in sorted(lengths.items()) for v in (s,n))
    return STREAM.pack(len(codes),len(bits))+table+stream,dict(symbols=len(codes),maximum_code_bits=max(lengths.values()),coded_bits=len(bits),values=len(a))

def _huff_decode(data,pos,count,maximum):
    if pos+STREAM.size>len(data):raise ValueError('short Huffman stream')
    ns,nbits=STREAM.unpack_from(data,pos);pos+=STREAM.size
    if not 1<=ns<=min(maximum+1,count) or nbits>count*MAX_CODE or pos+2*ns>len(data):raise ValueError('Huffman stream bounds')
    pairs=[(data[pos+2*i],data[pos+2*i+1]) for i in range(ns)];pos+=2*ns
    if any(s>maximum for s,_ in pairs) or [s for s,_ in pairs]!=sorted({s for s,_ in pairs}):raise ValueError('Huffman symbols/order')
    lengths=dict(pairs);codes=_codes(lengths)
    size=(nbits+7)//8
    if pos+size>len(data):raise ValueError('short Huffman bits')
    stream=data[pos:pos+size];pos+=size
    if nbits%8 and stream[-1]&((1<<(8-nbits%8))-1):raise ValueError('Huffman padding')
    if ns==1:
        if nbits:raise ValueError('constant stream has bits')
        return np.full(count,pairs[0][0],np.int32),pos
    if nbits<count:raise ValueError('short Huffman symbol coverage')
    decode={(n,c):s for s,(c,n) in codes.items()};out=np.empty(count,np.int32);bit=0;limit=max(lengths.values())
    for i in range(count):
        code=0
        for length in range(1,limit+1):
            if bit>=nbits:raise ValueError('truncated Huffman symbol')
            code=(code<<1)|((stream[bit//8]>>(7-bit%8))&1);bit+=1
            key=(length,code)
            if key in decode:out[i]=decode[key];break
        else:raise ValueError('unknown Huffman code')
    if bit!=nbits:raise ValueError('trailing Huffman bits')
    return out,pos

def _motion_reference(reference,mode,data,w,hh):
    """Parse the frozen HD25 motion prefix, retaining its bounded grammar."""
    if mode==1:return reference,0
    if mode==2:
        if len(data)<2:raise ValueError('short global prefix')
        dx,dy=struct.unpack_from('<bb',data)
        if abs(dx)>h.RADIUS or abs(dy)>h.RADIUS:raise ValueError('global bounds')
        return h.predict(reference,dx,dy),2
    if mode!=3:raise ValueError('prediction mode')
    if len(data)<h.TILE.size+4:raise ValueError('short tile prefix')
    tw,th,radius,field,n=h.TILE.unpack_from(data);count=((w+15)//16)*((hh+7)//8)
    size=struct.unpack_from('<I',data,h.TILE.size)[0];begin=h.TILE.size+4
    if (tw,th,radius)!=(16,8,4) or field not in (0,1) or n!=count or not 0<size<=4*count or begin+size>len(data):raise ValueError('tile prefix bounds')
    raw=data[begin:begin+size];vectors=[]
    if field==0:
        if size!=2*count:raise ValueError('raw tile vector size')
        vectors=[struct.unpack_from('<bb',raw,2*i) for i in range(count)]
    else:
        if size%h.RUN.size:raise ValueError('tile run bytes')
        for i in range(0,size,h.RUN.size):
            length,dx,dy=h.RUN.unpack_from(raw,i)
            if not length or len(vectors)+length>count or (vectors and vectors[-1]==(dx,dy)):raise ValueError('tile run coverage/order')
            vectors.extend([(dx,dy)]*length)
    if len(vectors)!=count or any(abs(dx)>4 or abs(dy)>4 for dx,dy in vectors):raise ValueError('tile vector bounds')
    pred=np.empty_like(reference);index=0
    for y in range(0,hh,8):
        for x in range(0,w,16):
            dx,dy=vectors[index];index+=1;yh=min(8,hh-y);xw=min(16,w-x)
            pred[y:y+yh,x:x+xw]=reference[np.ix_(np.clip(np.arange(y,y+yh)+dy,0,hh-1),np.clip(np.arange(x,x+xw)+dx,0,w-1))]
    return pred,begin+size

def _encode_patch(current,prediction,mode,prefix=b''):
    current=h._array(current);row_delta=bool(mode&8);plain=mode&7;parts=[];work=[]
    for channel,maximum in enumerate((31,63,31)):
        values=h._components(current)[channel].astype(np.int32)
        if plain==0:
            delta=values.copy();delta[:,1:]-=values[:,:-1]
        else:delta=values-h._components(prediction)[channel].astype(np.int32)
        if row_delta:before=delta.copy();delta[:,1:]-=before[:,:-1]
        mapped=np.where(delta>=0,2*delta,-2*delta-1)
        payload,stats=_huff_encode(mapped);parts.append(payload);work.append(stats)
    return prefix+b''.join(parts),work

def _pack_patch(current,reference,mode,payload):
    body=h.HEADER.pack(b'HS32',1,mode,current.shape[1],current.shape[0],len(payload),h.ZERO if mode==0 else h._tag(reference),h._tag(current))+payload
    return body+struct.pack('<I',zlib.crc32(body))

def _decode_patch(packet,reference):
    if type(packet) is not bytes or not h.FIXED_BYTES<=len(packet)<=h.MAX_PACKET:raise ValueError('HS32 bounded packet')
    magic,ver,mode,w,hh,size,ref,tag=h.HEADER.unpack_from(packet)
    h.old._geometry(w,hh)
    if magic!=b'HS32' or ver!=1 or mode not in (0,1,2,3,9,10,11) or len(packet)!=h.FIXED_BYTES+size or zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('HS32 framing/CRC')
    data=packet[h.HEADER.size:-4];plain=mode&7;row_delta=bool(mode&8)
    if plain==0:
        if ref!=h.ZERO:raise ValueError('intra HS32 reference')
        prediction=None;pos=0
    else:
        if reference is None:raise ValueError('HS32 missing reference')
        reference=h._array(reference)
        if reference.shape!=(hh,w) or h._tag(reference)!=ref:raise ValueError('HS32 exact reference')
        prediction,pos=_motion_reference(reference,plain,data,w,hh)
    channels=[]
    for channel,maximum in enumerate((31,63,31)):
        mapped,pos=_huff_decode(data,pos,w*hh,4*maximum if row_delta else 2*maximum)
        delta=np.where(mapped&1,-(mapped//2)-1,mapped//2).reshape(hh,w)
        if row_delta:delta=np.cumsum(delta,axis=1)
        if plain==0:result=np.cumsum(delta,axis=1)
        else:result=h._components(prediction)[channel].astype(np.int32)+delta
        if np.any(result<0) or np.any(result>maximum):raise ValueError('HS32 reconstructed range')
        channels.append(result.astype(np.uint16))
    if pos!=len(data):raise ValueError('HS32 trailing data')
    output=(channels[0]<<11)|(channels[1]<<5)|channels[2]
    if h._tag(output)!=tag:raise ValueError('HS32 output tag')
    return output

def _meta(packet):
    if packet[:4]==b'HU25':return p._parse_hud(packet)
    p._checked(packet,p.HUD.size+4,p.CAP,'HX32')
    fields=list(p.HUD.unpack_from(packet))
    if fields[0]!=b'HX32' or fields[1]!=1:raise ValueError('HX32 profile')
    original_types=tuple(fields[14:18]);fields[0]=b'HU25';fields[14:18]=[2 if v==3 else v for v in original_types]
    shadow=p.seal(p.HUD.pack(*fields)+packet[p.HUD.size:-4]);meta=p._parse_hud(shadow)
    meta['types']=original_types[:fields[2]];return meta

def decode_hud(packet,reference=None,*,expected_epoch=None,expected_reference_id=None):
    if packet[:4]==b'HU25':return p.decode_hud(packet,reference,expected_epoch=expected_epoch,expected_reference_id=expected_reference_id)
    meta=_meta(packet);w,hh=meta['width'],meta['height']
    if expected_epoch is not None and meta['epoch']!=expected_epoch:raise ValueError('HX32 epoch')
    if meta['reference_id']==p.NO_REF:ref=()
    else:
        if reference is None or expected_reference_id!=meta['reference_id']:raise ValueError('HX32 exact reference ID')
        ref=p._validated_hud(reference,w,hh)
        if p.hud_tag(ref,w,hh)!=meta['reference_tag']:raise ValueError('HX32 exact reference tag')
    by_rect={v['rect']:v['words'] for v in ref};result=[]
    for rect,kind,data in zip(meta['rectangles'],meta['types'],meta['payloads']):
        if kind==1:
            item=p.ui.validate_patches((data,),w,hh)[0]
            if tuple(item['rect'])!=rect:raise ValueError('full patch rectangle')
            words=item['words']
        elif kind==2:words=h.decode(data,by_rect.get(rect))
        elif kind==3:words=_decode_patch(data,by_rect.get(rect))
        else:raise ValueError('HX32 patch kind')
        if words.shape!=(rect[3],rect[2]):raise ValueError('HX32 patch geometry')
        result.append(dict(rect=rect,words=words))
    output=p._validated_hud(result,w,hh)
    if p.hud_tag(output,w,hh)!=meta['reconstructed_tag']:raise ValueError('HX32 reconstructed tag')
    return output,meta

def encode_hud(baseline,reference=None,*,expected_reference_id=None):
    started=time.perf_counter_ns();current,meta=p.decode_hud(baseline,reference,expected_reference_id=expected_reference_id)
    if meta['reference_id']==p.NO_REF:reference=None
    by_rect={v['rect']:v['words'] for v in reference or ()};payloads=[];types=[];details=[]
    for patch,old_kind,old_payload in zip(current,meta['types'],meta['payloads']):
        a=patch['words'];ref=by_rect.get(patch['rect']);candidates=[(old_kind,old_payload,None)];recipes=[(0,None,b'')]
        if ref is not None:
            recipes.extend([(1,ref,b''),(9,ref,b'')])
            if old_kind==2:
                values=h.HEADER.unpack_from(old_payload);old_mode=values[2];data=old_payload[h.HEADER.size:-4]
                if old_mode in (h.GLOBAL,h.TILED):
                    mode=2 if old_mode==h.GLOBAL else 3;pred,n=_motion_reference(ref,mode,data,a.shape[1],a.shape[0])
                    recipes.extend([(mode,pred,data[:n]),(mode|8,pred,data[:n])])
        trials=[]
        for mode,pred,prefix in recipes:
            try:
                payload,work=_encode_patch(a,pred,mode,prefix);packet=_pack_patch(a,ref,mode,payload)
            except ValueError as err:
                if str(err)!='bounded Huffman code depth':raise
                trials.append(dict(mode=mode,rejected='code-depth'));continue
            fits=len(packet)<=h.MAX_PACKET
            trials.append(dict(mode=mode,bytes=len(packet),bounded_fit=fits,channels=work))
            if fits:candidates.append((3,packet,mode))
        selected=min(candidates,key=lambda v:len(v[1]));payloads.append(selected[1]);types.append(selected[0])
        details.append(dict(rect=patch['rect'],baseline_bytes=len(old_payload),selected_bytes=len(selected[1]),selected_mode=selected[2],
                            baseline_kind=old_kind,selected_kind=selected[0],trials=trials))
    fields=list(p.HUD.unpack_from(baseline));fields[0]=b'HX32';fields[10:14]=[len(v) for v in payloads]+[0]*(4-len(payloads));fields[14:18]=types+[0]*(4-len(types))
    candidate=p.seal(p.HUD.pack(*fields)+b''.join(payloads));selected=candidate if len(candidate)<len(baseline) else baseline
    assert len(selected)<=len(baseline)<=p.CAP
    return selected,dict(baseline_bytes=len(baseline),packet_bytes=len(selected),selected_new=selected[:4]==b'HX32',patches=details,
        encode_extra_wall_ms=(time.perf_counter_ns()-started)/1e6,baseline_motion_search_reused=True,
        baseline_encode_cost_included=False,maximum_code_bits=MAX_CODE,maximum_table_entries_per_channel=253,
        receiver_reference_hud_words=sum(v['words'].size for v in current),proposed_ESP32_role='opaque bounded transport, no Huffman decode',
        source_words=sum(v['words'].size for v in current))
