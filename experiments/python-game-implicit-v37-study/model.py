"""CS37: fixed-HUD implicit omitted8x8 coefficient blocks, real serialized bytes.

This research transcoder starts from already encoded CN36 skip; it is NOT a
direct sender or an inverse-transform bypass. A new inner dispatch4 entropy-
codes only nonhidden blocks in raster order. Plain dispatch0..3 remains a
per-plane fallback with no added byte, and wins complete-payload ties.
"""
import hashlib,json,struct,zlib,time
import numpy as np
import helpers as h

HEADER=h.cn.HEADER
PROFILE=hashlib.sha256(b'CS37:implicit-hidden-raster-v1:'+json.dumps(h.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))

def transcode(packet):
    start=time.perf_counter_ns();outer=h.cn.parse(packet)
    if not outer['skip']:raise ValueError('CN36 skip input required')
    inner=outer['inner'];meta=h.m.parse(inner,expected_epoch=25)
    if any(np.any(c[mask]) for c,mask in zip(meta['coefficients'],h.cn.HIDDEN,strict=True)):
        raise ValueError('hidden coefficients must already be zero')
    pos=h.m.HEADER.size+meta['qmap_bytes']+meta['vector_bytes'];payloads=[];work=[]
    for plane,(c,mask,size) in enumerate(zip(meta['coefficients'],h.cn.HIDDEN,meta['plane_lengths'],strict=True)):
        original=inner[pos:pos+size];pos+=size
        visible=c[~mask]
        plan=h.entropy._plane_plan(visible,1,h.m)
        encoded,*_=h.entropy._construct(visible,1,plan,h.m)
        compact=b'\x04'+encoded
        sparse=len(compact)<len(original)
        payloads.append(compact if sparse else original)
        work.append(dict(plane=plane,full_blocks=len(c),hidden_blocks=int(mask.sum()),visible_blocks=len(visible),
                         old_bytes=len(original),compact_bytes=len(compact),selected_bytes=len(payloads[-1]),implicit_selected=sparse))
    fields=list(h.m.HEADER.unpack_from(inner));fields[0]=b'GS37';fields[14:17]=map(len,payloads)
    maps=inner[h.m.HEADER.size:h.m.HEADER.size+meta['qmap_bytes']+meta['vector_bytes']]
    newinner=seal(h.m.HEADER.pack(*fields)+maps+b''.join(payloads))
    outerfields=list(HEADER.unpack_from(packet));outerfields[0]=b'CS37';outerfields[8]=PROFILE;outerfields[11]=len(newinner)
    result=seal(HEADER.pack(*outerfields)+newinner+outer['hud'])
    assert len(result)<=len(packet)<=49152
    return result,dict(planes=work,transcode_ms=(time.perf_counter_ns()-start)/1e6,
                       input_complete_bytes=len(packet),output_complete_bytes=len(result),
                       old_encode_already_paid=True,hidden_bitmap_bytes=0,new_outer_bytes=80)
