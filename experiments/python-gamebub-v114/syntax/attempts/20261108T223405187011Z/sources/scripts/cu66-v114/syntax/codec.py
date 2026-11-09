"""Experimental SR14 packed-block chunks; independent BR88 contexts, no pixel codec."""
import importlib.util
from pathlib import Path
import struct
import zlib

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('strict_br88',ROOT/'experiments/python-gamebub-v88/entropy/codec.py')
strict=importlib.util.module_from_spec(spec);spec.loader.exec_module(strict)
ORDER=sorted(range(64),key=lambda i:(i//8+i%8,(i//8)if(i//8+i%8)%2 else -(i//8)))
HEADER=struct.Struct('>4sBBHI')
ENTRY=struct.Struct('>IIII')


class Bits:
    def __init__(self):self.data=bytearray();self.size=0
    def bit(self,b):
        if self.size%8==0:self.data.append(0)
        self.data[-1]|=b<<(7-self.size%8);self.size+=1
    def rice(self,value,k,escape):
        if not 0<=value<1<<escape:raise ValueError('Rice domain')
        q=value>>k
        for _ in range(min(q,15)):self.bit(0)
        if q<15:self.bit(1);value&=(1<<k)-1
        for n in range((k if q<15 else escape)-1,-1,-1):self.bit(value>>n&1)


def mapped(v):return -2*v-1 if v<0 else 2*v


def best(values,maximum,escape):
    return min(range(maximum+1),key=lambda k:sum((v>>k)+1+k if v>>k<15 else 15+escape for v in values))


def encode_br88(values):
    if not values or len(values)%64 or len(values)//64>5400 or any(not -2048<=v<=2048 for v in values):raise ValueError('coefficient geometry/range')
    blocks=len(values)//64;dc=[mapped(values[b*64])for b in range(blocks)];kd=best(dc,13,14)
    bits=Bits()
    for v in dc:bits.rice(v,kd,14)
    streams=[bytes([kd,255])+struct.pack('<I',bits.size)+bits.data];counts=[]
    for lo,hi in ((1,6),(6,21),(21,64)):
        runs=[];levels=[];previous=-1
        for b in range(blocks):
            for i in range(lo,hi):
                v=values[b*64+ORDER[i]]
                if v:
                    pos=b*(hi-lo)+i-lo;runs.append(pos-previous-1);levels.append(mapped(v)-1);previous=pos
        kr,kv=best(runs,19,24),best(levels,11,12);bits=Bits()
        for r,v in zip(runs,levels):bits.rice(r,kr,24);bits.rice(v,kv,12)
        streams.append(bytes([kr,kv])+struct.pack('<I',bits.size)+bits.data);counts.append(len(runs))
    raw=sum(map(len,streams))>=128*blocks
    lengths=[128*blocks,0,0,0]if raw else list(map(len,streams))
    body=b'BR88'+bytes([1,int(raw)])+struct.pack('<IHH',blocks,1,0)+struct.pack('<4I',*lengths)+struct.pack('<3I',*([0]*3 if raw else counts))
    body+=struct.pack('<'+'h'*len(values),*values)if raw else b''.join(streams)
    return body+struct.pack('<I',zlib.crc32(body))


def pack(values,plane,chunk_blocks):
    if plane not in (0,1,2)or chunk_blocks not in (32,64,128,256):raise ValueError('profile')
    blocks=len(values)//64
    if not values or len(values)%64 or blocks>5400:raise ValueError('geometry')
    pieces=[encode_br88(values[start*64:min(start+chunk_blocks,blocks)*64])for start in range(0,blocks,chunk_blocks)]
    at=HEADER.size+len(pieces)*ENTRY.size;table=bytearray();first=0
    for payload in pieces:
        n=int.from_bytes(payload[6:10],'little');table.extend(ENTRY.pack(first,n,at,len(payload)));at+=len(payload);first+=n
    body=HEADER.pack(b'SR14',1,plane,len(pieces),blocks)+table+b''.join(pieces)
    return body+struct.pack('>I',zlib.crc32(body))


def unpack(packet):
    if not HEADER.size+ENTRY.size+46+4<=len(packet)<=1048576:raise ValueError('container bound')
    if zlib.crc32(packet[:-4])!=int.from_bytes(packet[-4:],'big'):raise ValueError('container CRC')
    magic,version,plane,count,blocks=HEADER.unpack_from(packet)
    if magic!=b'SR14'or version!=1 or plane>2 or not 1<=count<=512 or not 1<=blocks<=5400:raise ValueError('container profile')
    end=HEADER.size+count*ENTRY.size
    if end>len(packet)-4:raise ValueError('directory bound')
    values=[];first=0;at=end;entries=[]
    for i in range(count):
        start,n,offset,length=ENTRY.unpack_from(packet,HEADER.size+i*ENTRY.size)
        if start!=first or not 1<=n<=256 or first+n>blocks or offset!=at or not 46<=length<=46+128*n or offset+length>len(packet)-4:raise ValueError('directory ownership/range')
        payload=packet[offset:offset+length];decoded=strict.decode(payload,n)
        values.extend(decoded);entries.append((start,n,payload));first+=n;at+=length
    if first!=blocks or at!=len(packet)-4:raise ValueError('directory closure')
    return plane,values,entries
