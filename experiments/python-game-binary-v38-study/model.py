"""AB38 adaptive binary arithmetic coding of bounded coefficient Rice events.

New Python research syntax. One17x8 probability product/bit,16-bit interval,
shift-only adaptation and four independent streams. No FPGA timing inference.
"""
import struct,zlib
import numpy as np
HEADER=struct.Struct('<4sBBIHH4I3I');STREAM=struct.Struct('<BBI')
BANDS=((1,6),(6,21),(21,64))
ZIGZAG=np.array(sorted(range(64),key=lambda n:(n//8+n%8,n//8 if(n//8+n%8)%2 else -(n//8))))

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def mapped(a):return np.where(a>=0,a*2,-a*2-1)

class BinaryEncoder:
    def __init__(self):
        self.low=0;self.high=65535;self.pending=0;self.bits=[];self.p=[128]*88
        self.decisions=0;self.renorm=0;self.maximum_renorm=0
    def emit(self,bit):
        self.bits.append(bit);self.bits.extend([1-bit]*self.pending);self.pending=0
    def bit(self,bit,context):
        probability=self.p[context];width=self.high-self.low+1
        split=max(self.low,min(self.high-1,self.low+((width*probability)>>8)-1))
        if bit:self.low=split+1;probability-=max(1,probability>>5)
        else:self.high=split;probability+=max(1,(256-probability)>>5)
        self.p[context]=min(255,max(1,probability));steps=0
        while True:
            if self.high<32768:self.emit(0)
            elif self.low>=32768:self.emit(1);self.low-=32768;self.high-=32768
            elif self.low>=16384 and self.high<49152:self.pending+=1;self.low-=16384;self.high-=16384
            else:break
            self.low*=2;self.high=self.high*2+1;steps+=1
        self.decisions+=1;self.renorm+=steps;self.maximum_renorm=max(self.maximum_renorm,steps)
    def rice(self,value,k,escape,kind):
        value=int(value)
        if not 0<=value<(1<<escape):raise ValueError('Rice bounded value')
        quotient=value>>k;base=kind*48
        for i in range(min(quotient,15)):self.bit(0,base+i)
        if quotient<15:
            self.bit(1,base+quotient);value&=(1<<k)-1;count=k
        else:count=escape
        for i in range(count-1,-1,-1):self.bit((value>>i)&1,base+16+min(i,23))
    def finish(self):
        self.pending+=1;self.emit(int(self.low>=16384));self.bits.extend([0]*16)
        length=len(self.bits);bits=self.bits+[0]*((-length)%8)
        data=bytes(sum(bits[i+j]<<(7-j) for j in range(8)) for i in range(0,len(bits),8))
        return data,length

def best_k(values,maximum,escape):
    values=np.asarray(values,np.int64)
    return min(range(maximum+1),key=lambda k:int(np.where((values>>k)<15,(values>>k)+1+k,15+escape).sum()))

def encode(coefficients,blocks_w):
    a=np.asarray(coefficients)
    if(a.dtype!=np.int16 or a.ndim!=3 or a.shape[1:]!=(8,8) or not 1<=len(a)<=65536 or
       type(blocks_w)is not int or not 1<=blocks_w<=256 or len(a)%blocks_w or np.any(a<-2048) or np.any(a>2048)):
        raise ValueError('bounded int16 block geometry/domain')
    zig=a.reshape(-1,64)[:,ZIGZAG].astype(np.int32);dc=zig[:,0].copy()
    dc[1:]-=zig[:-1,0];dc[::blocks_w]=zig[::blocks_w,0];dc=mapped(dc);kd=best_k(dc,13,14)
    coder=BinaryEncoder()
    for value in dc:coder.rice(value,kd,14,0)
    body,nbits=coder.finish();streams=[STREAM.pack(kd,255,nbits)+body]
    work=[dict(binary_decisions=coder.decisions,probability_products=coder.decisions,renorm_steps=coder.renorm,max_renorm_per_bit=coder.maximum_renorm)]
    counts=[]
    for lo,hi in BANDS:
        seq=zig[:,lo:hi].reshape(-1);indices=np.flatnonzero(seq);counts.append(len(indices))
        runs=np.diff(np.r_[-1,indices])-1;levels=mapped(seq[indices])-1
        kr,kv=best_k(runs,19,24),best_k(levels,11,12);coder=BinaryEncoder()
        for run,level in zip(runs,levels,strict=True):coder.rice(run,kr,24,0);coder.rice(level,kv,12,1)
        body,nbits=coder.finish();streams.append(STREAM.pack(kr,kv,nbits)+body)
        work.append(dict(binary_decisions=coder.decisions,probability_products=coder.decisions,renorm_steps=coder.renorm,max_renorm_per_bit=coder.maximum_renorm))
    flags=0;lengths=list(map(len,streams))
    if sum(lengths)>=128*len(a):flags=1;streams=[a.astype('<i2').tobytes()];lengths=[128*len(a),0,0,0];counts=[0,0,0]
    packet=seal(HEADER.pack(b'AB38',1,flags,len(a),blocks_w,0,*lengths,*counts)+b''.join(streams))
    return packet,dict(streams=work,raw_fallback=bool(flags),probability_state_bytes=352,
                       interval_bits=16,probability_bits=8,multiply_operand_bits=[17,8],
                       probability_products=sum(w['probability_products'] for w in work),renorm_steps=sum(w['renorm_steps'] for w in work),
                       max_renorm_per_bit=max(w['max_renorm_per_bit'] for w in work),parameters='minimum uncoded Rice cost, not arithmetic-optimal search')
