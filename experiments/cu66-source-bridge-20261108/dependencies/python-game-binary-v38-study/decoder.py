"""Independent AB38 decoder; no encoder import or encoder bit-state helper."""
import struct,zlib
import numpy as np
FRAME=struct.Struct('<4sBBIHH4I3I')
ORDER=tuple(sorted(range(64),key=lambda n:(n//8+n%8,n//8 if(n//8+n%8)%2 else -(n//8))))

class ArithmeticReader:
    def __init__(self,data,bitcount):
        if bitcount<18 or len(data)!=(bitcount+7)//8:raise ValueError('arithmetic exact bit length')
        self.data=data;self.size=bitcount;self.pos=0
        if bitcount%8 and data[-1]&((1<<(8-bitcount%8))-1):raise ValueError('arithmetic padding')
        self.start=0;self.end=65535;self.code=0;self.probabilities=[128]*88
        for _ in range(16):self.code=self.code*2+self.raw()
    def raw(self):
        if self.pos>=self.size:raise ValueError('arithmetic truncation')
        value=(self.data[self.pos//8]>>(7-self.pos%8))&1;self.pos+=1;return value
    def decode(self,index):
        probability=self.probabilities[index];partition=((self.end-self.start+1)*probability)//256
        partition=max(1,min(self.end-self.start,partition));boundary=self.start+partition-1
        value=int(self.code>boundary)
        if value:self.start=boundary+1;probability=max(1,probability-max(1,probability//32))
        else:self.end=boundary;probability=min(255,probability+max(1,(256-probability)//32))
        self.probabilities[index]=probability
        while True:
            if self.end<32768:offset=0
            elif self.start>=32768:offset=32768
            elif self.start>=16384 and self.end<49152:offset=16384
            else:break
            self.start=(self.start-offset)*2;self.end=(self.end-offset)*2+1;self.code=(self.code-offset)*2+self.raw()
        if not self.start<=self.code<=self.end:raise ValueError('arithmetic interval')
        return value
    def rice(self,k,escape,level=False):
        base=48 if level else 0;quotient=0
        while quotient<15:
            if self.decode(base+quotient):break
            quotient+=1
        width=escape if quotient==15 else k;value=0
        for i in range(width-1,-1,-1):value=value*2+self.decode(base+16+min(i,23))
        return value if quotient==15 else (quotient<<k)|value
    def finish(self):
        if self.size-self.pos!=2 or self.raw() or self.raw():raise ValueError('arithmetic exact termination')

def signed(value):return value//2 if value%2==0 else -(value//2)-1

def decode(packet,blocks,blocks_w):
    if(type(blocks)is not int or not 1<=blocks<=65536 or type(blocks_w)is not int or
       not 1<=blocks_w<=256 or blocks%blocks_w):raise ValueError('bounded requested coefficient geometry')
    if type(packet)is not bytes or not FRAME.size+4<=len(packet)<=FRAME.size+4+128*blocks:raise ValueError('AB38 bounded packet')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('AB38 CRC')
    magic,version,flags,n,bw,reserved,*tail=FRAME.unpack_from(packet);lengths=tail[:4];counts=tail[4:]
    if(magic,version,n,bw,reserved)!=(b'AB38',1,blocks,blocks_w,0) or flags not in (0,1):raise ValueError('AB38 profile')
    if len(packet)!=FRAME.size+4+sum(lengths):raise ValueError('AB38 exact lengths')
    if flags:
        if lengths!=[128*blocks,0,0,0] or any(counts):raise ValueError('AB38 raw syntax')
        result=np.frombuffer(packet[FRAME.size:-4],'<i2').copy().reshape(blocks,8,8)
        if np.any(result<-2048) or np.any(result>2048):raise ValueError('AB38 raw coefficient range')
        return result
    streams=[];pos=FRAME.size
    for size in lengths:
        if size<9:raise ValueError('AB38 stream bound')
        chunk=packet[pos:pos+size];pos+=size;k0,k1,bits=struct.unpack_from('<BBI',chunk)
        streams.append((k0,k1,ArithmeticReader(chunk[6:],bits)))
    kd,reserved,reader=streams[0]
    if kd>13 or reserved!=255:raise ValueError('AB38 DC parameters')
    zig=np.zeros((blocks,64),np.int16);previous=0
    for block in range(blocks):
        if block%blocks_w==0:previous=0
        previous+=signed(reader.rice(kd,14))
        if not -2048<=previous<=2048:raise ValueError('AB38 DC bounds')
        zig[block,0]=previous
    reader.finish()
    for (lo,hi),count,(kr,kv,reader) in zip(((1,6),(6,21),(21,64)),counts,streams[1:],strict=True):
        if kr>19 or kv>11 or count>blocks*(hi-lo):raise ValueError('AB38 band parameters/count')
        seq=np.zeros(blocks*(hi-lo),np.int16);index=-1
        for _ in range(count):
            index+=reader.rice(kr,24)+1
            if index>=len(seq):raise ValueError('AB38 run bound')
            value=signed(reader.rice(kv,12,True)+1)
            if not value or not -2048<=value<=2048:raise ValueError('AB38 level domain')
            seq[index]=value
        reader.finish();zig[:,lo:hi]=seq.reshape(blocks,hi-lo)
    result=np.empty_like(zig);result[:,ORDER]=zig
    return result.reshape(blocks,8,8)
