"""Independent HS33 bit parser: no call to encoder or its Huffman/Rice helpers."""
import struct,zlib
import numpy as np
# Frozen baseline parsing/prediction is shared, never candidate construction.
from baseline import old,p,h
CHANNEL=struct.Struct('<BBIII')

def _huffman(data,count,maximum):
    if len(data)<6:raise ValueError('short Huffman header')
    ns,nb=struct.unpack_from('<HI',data)
    if not 1<=ns<=min(count,maximum+1) or nb>16*count or len(data)!=6+2*ns+(nb+7)//8:raise ValueError('Huffman bounds')
    pairs=[(data[6+2*i],data[7+2*i]) for i in range(ns)]
    if [s for s,n in pairs]!=sorted({s for s,n in pairs}) or any(s>maximum or not 1<=n<=16 for s,n in pairs):raise ValueError('Huffman symbols/lengths')
    bits=data[6+2*ns:]
    if nb%8 and bits[-1]&((1<<(8-nb%8))-1):raise ValueError('Huffman padding')
    if ns==1:
        if pairs[0][1]!=1 or nb:raise ValueError('Huffman constant syntax')
        return np.full(count,pairs[0][0],np.int32)
    table={};code=prior=0
    for symbol,length in sorted(pairs,key=lambda v:(v[1],v[0])):
        code<<=length-prior
        if code>=1<<length:raise ValueError('Huffman oversubscribed')
        table[(length,code)]=symbol;code+=1;prior=length
    if code!=1<<prior or nb<count:raise ValueError('Huffman incomplete/coverage')
    out=np.empty(count,np.int32);pos=0
    for i in range(count):
        code=0
        for length in range(1,17):
            if pos>=nb:raise ValueError('Huffman truncated')
            code=code*2+((bits[pos//8]>>(7-pos%8))&1);pos+=1
            if (length,code) in table:out[i]=table[(length,code)];break
        else:raise ValueError('Huffman unknown code')
    if pos!=nb:raise ValueError('Huffman trailing bits')
    return out

def decode_channel(data,pos,count,maximum):
    if not 0<count<=h.MAX_WORDS or pos+CHANNEL.size>len(data):raise ValueError('channel bounds')
    scheme,k,events,size,nb=CHANNEL.unpack_from(data,pos);pos+=CHANNEL.size
    if scheme not in (0,1,2) or k>14 or events>count or size>6+506+2*count or nb>16*count+1 or pos+size+(nb+7)//8>len(data):raise ValueError('channel framing')
    if events:
        symbols=_huffman(data[pos:pos+size],events,maximum)
    else:
        if scheme!=1 or size:raise ValueError('empty symbol stream')
        symbols=np.empty(0,np.int32)
    pos+=size;bits=data[pos:pos+(nb+7)//8];pos+=(nb+7)//8
    if nb%8 and bits[-1]&((1<<(8-nb%8))-1):raise ValueError('Rice padding')
    if scheme==0:
        if k or nb or events!=count:raise ValueError('plain channel syntax')
        return symbols,pos
    bit=0;output=[]
    def rice(remaining):
        nonlocal bit
        quotient=0
        while True:
            if bit>=nb:raise ValueError('Rice truncated unary')
            value=(bits[bit//8]>>(7-bit%8))&1;bit+=1
            if value:break
            quotient+=1
            if quotient>(remaining>>k):raise ValueError('Rice unary bound')
        value=quotient<<k
        for index in range(k):
            if bit>=nb:raise ValueError('Rice truncated remainder')
            value|=((bits[bit//8]>>(7-bit%8))&1)<<(k-1-index);bit+=1
        if value>remaining:raise ValueError('Rice expansion bound')
        return value
    if scheme==1:
        if np.any(symbols==0):raise ValueError('zero in nonzero symbol stream')
        for s in symbols:
            gap=rice(count-len(output));output.extend([0]*gap)
            if len(output)>=count:raise ValueError('nonzero expansion overflow')
            output.append(int(s))
        gap=rice(count-len(output));output.extend([0]*gap)
    else:
        if not events or np.any(symbols[1:]==symbols[:-1]):raise ValueError('repeat event order')
        for s in symbols:
            if len(output)>=count:raise ValueError('repeat expansion overflow')
            length=rice(count-len(output)-1)+1;output.extend([int(s)]*length)
    if bit!=nb or len(output)!=count:raise ValueError('run coverage/trailing bits')
    return np.asarray(output,np.int32),pos

def decode_patch(packet,reference):
    if type(packet) is not bytes or not h.FIXED_BYTES<=len(packet)<=h.MAX_PACKET:raise ValueError('HS33 bounded packet')
    magic,ver,mode,w,hh,size,ref,tag=h.HEADER.unpack_from(packet);h.old._geometry(w,hh)
    if magic!=b'HS33' or ver!=1 or mode not in (0,1,2,3,9,10,11) or len(packet)!=h.FIXED_BYTES+size or zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('HS33 framing/CRC')
    data=packet[h.HEADER.size:-4];plain=mode&7
    if plain==0:
        if ref!=h.ZERO:raise ValueError('intra reference')
        prediction=None;pos=0
    else:
        if reference is None:raise ValueError('missing exact reference')
        reference=h._array(reference)
        if reference.shape!=(hh,w) or h._tag(reference)!=ref:raise ValueError('exact patch reference')
        prediction,pos=old._motion_reference(reference,plain,data,w,hh)
    channels=[]
    for channel,maximum in enumerate((31,63,31)):
        mapped,pos=decode_channel(data,pos,w*hh,4*maximum if mode&8 else 2*maximum)
        delta=np.where(mapped&1,-(mapped//2)-1,mapped//2).reshape(hh,w)
        if mode&8:delta=np.cumsum(delta,axis=1)
        result=np.cumsum(delta,axis=1) if plain==0 else h._components(prediction)[channel].astype(np.int32)+delta
        if np.any(result<0) or np.any(result>maximum):raise ValueError('reconstructed range')
        channels.append(result.astype(np.uint16))
    if pos!=len(data):raise ValueError('HS33 trailing bytes')
    output=(channels[0]<<11)|(channels[1]<<5)|channels[2]
    if h._tag(output)!=tag:raise ValueError('HS33 output tag')
    return output

def _meta(packet):
    if packet[:4] in (b'HU25',b'HX32'):return old._meta(packet)
    p._checked(packet,p.HUD.size+4,p.CAP,'HX33');fields=list(p.HUD.unpack_from(packet))
    if fields[0]!=b'HX33' or fields[1]!=1:raise ValueError('HX33 profile')
    kinds=tuple(fields[14:18])
    if any(k not in (1,2,3,4) for k in kinds[:fields[2]]):raise ValueError('HX33 kinds')
    fields[0]=b'HU25';fields[14:18]=[2 if k in (3,4) else k for k in kinds]
    meta=p._parse_hud(p.seal(p.HUD.pack(*fields)+packet[p.HUD.size:-4]));meta['types']=kinds[:fields[2]];return meta

def decode_hud(packet,reference=None,*,expected_epoch=None,expected_reference_id=None):
    if packet[:4] in (b'HU25',b'HX32'):return old.decode_hud(packet,reference,expected_epoch=expected_epoch,expected_reference_id=expected_reference_id)
    meta=_meta(packet);w,hh=meta['width'],meta['height']
    if expected_epoch is not None and meta['epoch']!=expected_epoch:raise ValueError('HX33 epoch')
    if meta['reference_id']==p.NO_REF:ref=()
    else:
        if reference is None or expected_reference_id!=meta['reference_id']:raise ValueError('HX33 exact reference ID')
        ref=p._validated_hud(reference,w,hh)
        if p.hud_tag(ref,w,hh)!=meta['reference_tag']:raise ValueError('HX33 exact reference tag')
    by_rect={v['rect']:v['words'] for v in ref};result=[]
    for rect,kind,data in zip(meta['rectangles'],meta['types'],meta['payloads']):
        if kind==1:
            item=p.ui.validate_patches((data,),w,hh)[0]
            if tuple(item['rect'])!=rect:raise ValueError('full rectangle')
            words=item['words']
        elif kind==2:words=h.decode(data,by_rect.get(rect))
        elif kind==3:words=old._decode_patch(data,by_rect.get(rect))
        else:words=decode_patch(data,by_rect.get(rect))
        if words.shape!=(rect[3],rect[2]):raise ValueError('patch geometry')
        result.append(dict(rect=rect,words=words))
    output=p._validated_hud(result,w,hh)
    if p.hud_tag(output,w,hh)!=meta['reconstructed_tag']:raise ValueError('HX33 output tag')
    return output,meta
