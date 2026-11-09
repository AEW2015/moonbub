"""Independent strict BR88 bounded Rice reader; no encoder import."""
import struct
import zlib


class Reader:
    def __init__(self,data):self.data=data;self.at=0
    def take(self,n):
        if n<0 or self.at+n>len(self.data):raise ValueError('BR88 truncated byte fields')
        result=self.data[self.at:self.at+n];self.at+=n;return result
    def byte(self):return self.take(1)[0]
    def u16(self):return int.from_bytes(self.take(2),'little')
    def u32(self):return int.from_bytes(self.take(4),'little')
    def end(self):
        if self.at!=len(self.data):raise ValueError('BR88 trailing fields')


class Rice:
    def __init__(self,data,size):
        if len(data)!=(size+7)//8:raise ValueError('BR88 exact bit bytes')
        if size%8 and data[-1]&((1<<(8-size%8))-1):raise ValueError('BR88 padding')
        self.data=data;self.size=size;self.at=0
    def bit(self):
        if self.at>=self.size:raise ValueError('BR88 truncated coded bits')
        value=(self.data[self.at//8]>>(7-self.at%8))&1;self.at+=1;return value
    def value(self,k,escape):
        quotient=0
        while quotient<15:
            if self.bit():break
            quotient+=1
        width=escape if quotient==15 else k
        value=0
        for _ in range(width):value=(value<<1)|self.bit()
        return value if quotient==15 else (quotient<<k)|value
    def end(self):
        if self.at!=self.size:raise ValueError('BR88 unused coded bits')


def signed(value):return -(value//2)-1 if value&1 else value//2


def decode(packet,blocks,bw=1):
    if not 1<=blocks<=65536 or bw!=1 or not 46<=len(packet)<=46+128*blocks:raise ValueError('BR88 bounds')
    if zlib.crc32(packet[:-4])!=int.from_bytes(packet[-4:],'little'):raise ValueError('BR88 CRC')
    r=Reader(packet[:-4])
    if r.take(4)!=b'BR88' or r.byte()!=1:raise ValueError('BR88 profile')
    flags=r.byte()
    if flags>1 or r.u32()!=blocks or r.u16()!=1 or r.u16()!=0:raise ValueError('BR88 binding')
    lengths=[r.u32() for _ in range(4)];counts=[r.u32() for _ in range(3)]
    if sum(lengths)!=len(packet)-46:raise ValueError('BR88 lengths')
    result=[0]*(blocks*64)
    if flags:
        if lengths!=[128*blocks,0,0,0] or counts!=[0,0,0]:raise ValueError('BR88 raw fields')
        result=list(struct.unpack('<'+'h'*(blocks*64),r.take(128*blocks)))
        if any(not -2048<=v<=2048 for v in result):raise ValueError('BR88 raw range')
        r.end();return result
    streams=[]
    for length in lengths:
        if length<6:raise ValueError('BR88 stream header')
        q=Reader(r.take(length));k0,k1,size=q.byte(),q.byte(),q.u32();streams.append((k0,k1,Rice(q.take(length-6),size)));q.end()
    r.end()
    k0,k1,dc=streams[0]
    if k0>13 or k1!=255:raise ValueError('BR88 DC parameters')
    for b in range(blocks):
        value=signed(dc.value(k0,14))
        if not -2048<=value<=2048:raise ValueError('BR88 DC range')
        result[b*64]=value
    dc.end()
    order=sorted(range(64),key=lambda i:(i//8+i%8, (i//8) if (i//8+i%8)%2 else -(i//8)))
    limits=(1,6,21,64)
    for band,count in enumerate(counts):
        k0,k1,bits=streams[band+1];width=limits[band+1]-limits[band]
        if k0>19 or k1>11 or count>blocks*width:raise ValueError('BR88 AC parameters')
        position=-1
        for _ in range(count):
            position+=bits.value(k0,24)+1
            if position>=blocks*width:raise ValueError('BR88 run range')
            value=signed(bits.value(k1,12)+1)
            if value==0 or not -2048<=value<=2048:raise ValueError('BR88 level range')
            block,index=divmod(position,width);result[block*64+order[limits[band]+index]]=value
        bits.end()
    return result
