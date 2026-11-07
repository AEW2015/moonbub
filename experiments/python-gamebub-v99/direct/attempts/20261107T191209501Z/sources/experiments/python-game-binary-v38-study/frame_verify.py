"""Independent CS38 syntax-to-frozen-CS37 adapter and causal receive proof.

No AB38 encoder import. This Python adapter decodes new payloads then re-encodes
frozen entropy for validation/reconstruction. Its cost is NOT a native decoder
architecture or FPGA throughput result; full arrays and packets are staged.
"""
import hashlib,json,struct,zlib
import numpy as np
import helpers as h
decoder=h.module('binary38_frame_arithmetic_decoder',h.HERE/'decoder.py')

HEADER=h.f.HEADER
PROFILE=hashlib.sha256(b'CS38:adaptive-binary-coefficients-v1:'+json.dumps(h.f.f.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))

def convert(packet):
    if type(packet)is not bytes or not HEADER.size+8<=len(packet)<=49152:raise ValueError('CS38 bounded packet')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('CS38 CRC')
    outer=list(HEADER.unpack_from(packet));magic,version,flags,epoch,fid,rid,w,hh,profile,rt,ot,nb,nh=outer
    if(magic,version,epoch,w,hh,profile)!=(b'CS38',1,25,720,480,PROFILE) or flags not in(2,3):raise ValueError('CS38 fixed profile')
    if min(nb,nh)<=0 or len(packet)!=HEADER.size+nb+nh+4:raise ValueError('CS38 exact lengths')
    inner=packet[HEADER.size:HEADER.size+nb];hud=packet[HEADER.size+nb:-4];m=h.f.m
    if len(inner)<m.HEADER.size+7 or zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('GS38 CRC')
    fields=list(m.HEADER.unpack_from(inner))
    if fields[0]!=b'GS38':raise ValueError('GS38 magic')
    fields[0]=b'GM27';synthetic=seal(m.HEADER.pack(*fields)+inner[m.HEADER.size:-4])
    meta=m.parse_metadata(synthetic,expected_epoch=25)
    maps=inner[m.HEADER.size:m.HEADER.size+meta['qmap_bytes']+meta['vector_bytes']]
    pos=m.HEADER.size+len(maps);payloads=[];newplanes=0
    for axis,(size,safe) in enumerate(zip(meta['plane_lengths'],h.f.f.safe_blocks(),strict=True)):
        data=inner[pos:pos+size];pos+=size;mask=safe.reshape(-1);bw=90 if axis==0 else 45
        if data[0]in(5,6):
            compact=data[0]==6;count=int((~mask).sum()) if compact else len(mask)
            coeff=decoder.decode(data[1:],count,1 if compact else bw)
            if not compact and np.any(coeff[mask]):raise ValueError('GS38 hidden residuals')
            entropy=h.f.f.frozen.shared.entropy;plan=entropy._plane_plan(coeff,1 if compact else bw,m)
            encoded,*_=entropy._construct(coeff,1 if compact else bw,plan,m)
            data=(b'\x04'+encoded) if compact else encoded;newplanes+=1
        elif data[0]not in(0,1,2,3,4):raise ValueError('GS38 dispatch')
        payloads.append(data)
    fields[0]=b'GS37';fields[14:17]=map(len,payloads)
    converted=seal(m.HEADER.pack(*fields)+maps+b''.join(payloads))
    outer[0]=b'CS37';outer[8]=h.f.PROFILE;outer[11]=len(converted)
    result=seal(HEADER.pack(*outer)+converted+hud)
    h.f.parse(result)
    return result,newplanes

class Receiver:
    def __init__(self):self.frozen=h.f.Receiver()
    def receive(self,packet):
        converted,count=convert(packet);pixels,hud,meta=self.frozen.receive(converted)
        return pixels,hud,meta,count
