"""Exact causal CP02/SR coefficient traces from real AR03 packets; no timing claim."""
import hashlib
from pathlib import Path
import struct
import sys
import zlib
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
for name in ('python-game-local-refresh-study','python-game-feedback-study'):
    sys.path.insert(0,str(HERE.parent/name))
import local_codec as codec
import transport
cp=codec.gm.word_coeff

class Bits:
    """Byte-at-a-time refill; at most64bit reservoir, no future block scan."""
    def __init__(self,data):
        self.data=memoryview(data);self.position=0;self.offset=0;self.value=0;self.bits=0;self.peak_bits=0
    def get(self,n):
        if type(n) is not int or not 0<=n<=32 or self.position+n>len(self.data)*8:raise ValueError('truncated bit read')
        while self.bits<n:
            if self.offset==len(self.data):raise ValueError('truncated bit read')
            self.value=(self.value<<8)|self.data[self.offset];self.offset+=1;self.bits+=8;self.peak_bits=max(self.peak_bits,self.bits)
            assert self.bits<=64
        self.bits-=n;out=self.value>>self.bits;self.value&=(1<<self.bits)-1;self.position+=n;return out
    def rice(self,k,escape):
        q=0
        while q<15:
            if self.get(1):return (q<<k)|self.get(k)
            q+=1
        value=self.get(escape)
        if value>>k<15:raise ValueError('noncanonical Rice escape')
        return value
    def finish(self):
        n=len(self.data)*8-self.position
        if n>=8 or self.get(n):raise ValueError('extra/nonzero padding')

def unmap(v):return v//2 if v%2==0 else -(v+1)//2

def iter_cp02(packet,blocks,blocks_w):
    """Yields one coefficient block plus exact stream cursor trace; exhaust to validate."""
    if type(blocks) is not int or not 1<=blocks<=cp.MAX_BLOCKS or type(blocks_w) is not int or not 1<=blocks_w<=256 or blocks%blocks_w:raise ValueError('CP02 geometry')
    if not isinstance(packet,(bytes,bytearray,memoryview)) or not cp.PAYLOAD_OVERHEAD<=len(packet)<=128*blocks+cp.PAYLOAD_OVERHEAD:raise ValueError('CP02 bound')
    view=memoryview(packet);magic,version,mode,count,width,reserved,ndc,nac=cp.COEFF.unpack_from(view)
    if (magic,version,count,width,reserved)!=(b'CP02',1,blocks,blocks_w,0) or mode not in (0,1) or len(view)!=cp.PAYLOAD_OVERHEAD+ndc+nac:raise ValueError('CP02 header/length')
    if zlib.crc32(view[:-4])!=struct.unpack_from('<I',view,len(view)-4)[0]:raise ValueError('CP02 CRC')
    dcbase=cp.COEFF.size;acbase=dcbase+ndc
    if mode==0:
        if ndc!=128*blocks or nac:raise ValueError('CP02 RAW length')
        for i in range(blocks):
            start=dcbase+128*i;block=np.frombuffer(view[start:start+128],dtype='<i2').copy().reshape(8,8)
            if np.any(np.abs(block.astype(np.int32))>cp.MAX_COEFF):raise ValueError('CP02 RAW coefficient range')
            yield block,dict(block=i,storage='raw',raw_range=[start,start+128],dc_bits=None,ac_bits=None,dc_read_range=None,ac_read_range=None,reservoir_peak_bits=0)
        return
    if ndc<1 or view[dcbase]>13 or nac<3 or any(v>11 for v in view[acbase:acbase+3]):raise ValueError('CP02 Rice parameters')
    kd=int(view[dcbase]);ks=tuple(view[acbase:acbase+3]);dc=Bits(view[dcbase+1:acbase]);ac=Bits(view[acbase+3:-4]);previous=0
    for i in range(blocks):
        d0,a0=dc.position,ac.position;dr0,ar0=dc.offset,ac.offset
        if i%blocks_w==0:previous=0
        value=previous+unmap(dc.rice(kd,14))
        if not -cp.MAX_COEFF<=value<=cp.MAX_COEFF:raise ValueError('CP02 DC range')
        previous=value;zig=np.zeros(64,np.int16);zig[0]=value;pos=1
        while pos<64:
            tag=ac.get(2)
            if tag==0:break
            if tag==1:
                if pos+16>64:raise ValueError('CP02 ZRL overrun')
                pos+=16;continue
            target=pos+((tag&1)<<3)+ac.get(3)
            if target>=64:raise ValueError('CP02 AC run overrun')
            band=0 if target<=5 else 1 if target<=20 else 2
            value=unmap(ac.rice(ks[band],12)+1)
            if value==0 or not -cp.MAX_COEFF<=value<=cp.MAX_COEFF:raise ValueError('CP02 AC coefficient range')
            zig[target]=value;pos=target+1
        block=np.empty(64,np.int16);block[cp.frozen.ZIGZAG]=zig
        yield block.reshape(8,8),dict(block=i,storage='rice',dc_bits=[d0,dc.position],ac_bits=[a0,ac.position],
            dc_bit_base=8*(dcbase+1),ac_bit_base=8*(acbase+3),
            dc_read_range=[dcbase+1+dr0,dcbase+1+dc.offset],ac_read_range=[acbase+3+ar0,acbase+3+ac.offset],
            raw_range=None,reservoir_peak_bits=max(dc.peak_bits,ac.peak_bits))
    dc.finish();ac.finish()

def decode_cp02(packet,blocks,blocks_w):
    rows=list(iter_cp02(packet,blocks,blocks_w))
    return np.stack([r[0] for r in rows]),[r[1] for r in rows]

def cp02_info(packet):
    f=cp.COEFF.unpack_from(packet);ndc,nac=f[-2:]
    return dict(mode=int(f[2]),blocks=int(f[3]),blocks_w=int(f[4]),header_range=[0,cp.COEFF.size],
        dc_range=[cp.COEFF.size,cp.COEFF.size+ndc],ac_range=[cp.COEFF.size+ndc,len(packet)-4],
        crc_range=[len(packet)-4,len(packet)],dc_parameter_bytes=1 if f[2] else 0,ac_parameter_bytes=3 if f[2] else 0)

def plane_trace(packet,n,blocks_w,is_sr=False):
    """Return coefficients and per-output-block records. No apportioning by size."""
    if not is_sr:
        coeff,records=decode_cp02(packet,n,blocks_w)
        return coeff,records,dict(storage='CP02',cp02_packets=1,header_bytes=cp.COEFF.size,crc_bytes=4,cp02=cp02_info(packet))
    sr=codec.sr
    if len(packet)<sr.PLANE.size:raise ValueError('SP01 short')
    magic,mode,count,nmap,ndc,nfull=sr.PLANE.unpack_from(packet)
    if magic!=sr.PLANE_MAGIC or count!=n or mode not in (0,1):raise ValueError('SP01 identity')
    if mode==0:
        if nmap or ndc or len(packet)!=sr.PLANE.size+nfull:raise ValueError('SP01 dense lengths')
        coeff,records=decode_cp02(memoryview(packet)[sr.PLANE.size:],n,blocks_w)
        for r in records:r['cp02_base']=sr.PLANE.size
        return coeff,records,dict(storage='SRdense',cp02_packets=1,header_bytes=sr.PLANE.size+cp.COEFF.size,crc_bytes=4,cp02_base=sr.PLANE.size,cp02=cp02_info(packet[sr.PLANE.size:]))
    if nmap!=(n+3)//4 or ndc>n or len(packet)!=sr.PLANE.size+nmap+2*ndc+nfull:raise ValueError('SP01 split lengths')
    raw=memoryview(packet)[sr.PLANE.size:sr.PLANE.size+nmap]
    def get_mode(i):return (raw[i//4]>>(6-2*(i%4)))&3
    if any(get_mode(i)>2 for i in range(n)) or any(get_mode(i) for i in range(n,nmap*4)):raise ValueError('SP01 modes/padding')
    full_count=sum(get_mode(i)==2 for i in range(n))
    if sum(get_mode(i)==1 for i in range(n))!=ndc or bool(nfull)!=bool(full_count):raise ValueError('SP01 counts')
    dcbase=sr.PLANE.size+nmap;fullbase=dcbase+2*ndc;full=iter_cp02(memoryview(packet)[fullbase:],full_count,1) if nfull else iter(())
    coeff=[];records=[];di=0;mode_byte=0
    for i in range(n):
        if i%4==0:mode_byte=int(raw[i//4])
        mode=(mode_byte>>(6-2*(i%4)))&3
        r=dict(block=i,storage=('zero','dc','full')[mode],mode_bits=[2*i,2*i+2],mode_bit_base=sr.PLANE.size*8,
               mode_read_range=[sr.PLANE.size+i//4,sr.PLANE.size+i//4+1] if i%4==0 else [sr.PLANE.size+i//4+1,sr.PLANE.size+i//4+1],dc_value_range=None)
        if mode==0:block=np.zeros((8,8),np.int16)
        elif mode==1:
            value=struct.unpack_from('<h',packet,dcbase+2*di)[0]
            if not value or abs(value)>cp.MAX_COEFF:raise ValueError('SP01 DC value')
            block=np.zeros((8,8),np.int16);block[0,0]=value;r['dc_value_range']=[dcbase+2*di,dcbase+2*di+2];di+=1
        else:
            block,child=next(full)
            if not np.any(block.reshape(64)[1:]):raise ValueError('SP01 full without AC')
            r['compact_cp02']=child;r['compact_cp02_base']=fullbase
        coeff.append(block);records.append(r)
    try:next(full)
    except StopIteration:pass
    else:raise ValueError('SP01 extra compact blocks')
    return np.stack(coeff),records,dict(storage='SRsplit',cp02_packets=int(bool(nfull)),header_bytes=sr.PLANE.size,crc_bytes=4*int(bool(nfull)),mode_bytes=nmap,mode_preflight_range=[sr.PLANE.size,sr.PLANE.size+nmap],dc_value_bytes=2*ndc,cp02_base=fullbase if nfull else None,cp02=cp02_info(packet[fullbase:]) if nfull else None)

def parse_packet(packet):
    """JSON-safe exact selected-entropy cursors; full input/preflight/output retained."""
    meta=codec.identity(packet,decode=False);inner=meta['inner'];fields=codec.gm.HEADER.unpack_from(inner)
    width,height=meta['width'],meta['height'];pos=codec.gm.HEADER.size+fields[12];planes=[]
    # Frozen full parser is the coefficient oracle, separate from causal walkers.
    oracle=codec.identity(packet,decode=True)['parsed']['coefficients']
    for plane,size in enumerate(fields[13:16]):
        pw,ph=(width,height) if plane==0 else (width//2,height//2);bw=(pw+7)//8;bh=(ph+7)//8
        payload=inner[pos:pos+size];coeff,records,info=plane_trace(payload,bw*bh,bw,meta['inner_codec']=='SR01')
        np.testing.assert_array_equal(coeff,oracle[plane])
        stripes=[]
        for row in range(bh):
            group=records[row*bw:(row+1)*bw];a=coeff[row*bw:(row+1)*bw].reshape(bw,64)
            full=np.any(a[:,1:]!=0,axis=1);dc=(~full)&(a[:,0]!=0)
            stripes.append(dict(y=row*8,rows=min(8,ph-row*8),block_start=row*bw,block_count=bw,
                zero=int((~full&~dc).sum()),dc=int(dc.sum()),general=int(full.sum()),blocks=group))
        planes.append(dict(plane=plane,width=pw,height=ph,blocks_w=bw,blocks_h=bh,
            packet_payload_offset=codec.HEADER.size+pos,payload_bytes=size,coefficients_sha256=hashlib.sha256(coeff.astype('<i2').tobytes()).hexdigest(),
            selected_entropy=info,stripes=stripes));pos+=size
    return dict(schema='ar03-exact-entropy-trace-v1',frame_id=meta['frame_id'],epoch=meta['epoch'],width=width,height=height,
        key=meta['key'],promoted=meta['promoted'],reference_bank=meta['reference_bank'],reference_id=meta['reference_id'],
        packet_bytes=len(packet),packet_sha256=hashlib.sha256(packet).hexdigest(),inner_codec=meta['inner_codec'],
        planes=planes,selected_ui_pixels=sum(x['rect'][2]*x['rect'][3] for x in codec.identity(packet,decode=True)['patches']),
        scope='Exact token walkers compare full coefficients with frozen decoder; input packet, output arrays, preflight/oracle and JSON traces retained outside bounded entropy reservoirs. No native/FPGA timing or fully streaming decoder proof.')
