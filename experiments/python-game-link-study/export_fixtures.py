#!/usr/bin/env python3
"""Export versioned GM01/GF01 functional golden vectors; no network or hardware."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import struct
import sys

import numpy as np
import chunks
from harness import codec,decode_complete

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    rng=np.random.default_rng(8088)
    small=rng.integers(0,256,(64,80,3),dtype=np.uint8)
    yield 'small-key',small,False,False
    a=small.copy();a[8:24,16:40]=np.array((210,30,90),np.uint8)
    yield 'small-patch',a,False,False
    yield 'small-pan',np.roll(small,2,axis=1),False,False
    yy,xx=np.mgrid[:18,:34]
    edge=np.stack(((xx*7+yy*11)%256,(xx*5+yy*3)%256,(xx*11+yy*7)%256),axis=2).astype(np.uint8)
    yield 'edge-key',edge,True,False
    yield 'edge-patch',255-edge,False,False
    yy,xx=np.mgrid[:480,:720]
    full=np.stack(((xx//3+yy//2)%256,(xx//5+yy//3+21)%256,(yy//4+xx//4+85)%256),axis=2).astype(np.uint8)
    full[48:112,16:208]=np.array((15,18,25),np.uint8)
    full[60:68,28:188]=np.array((220,45,60),np.uint8)
    full[84:92,28:148]=np.array((230,235,240),np.uint8)
    yield 'canvas-key',full,True,False
    a=full.copy();a[200:224,300:324]=np.array((45,210,80),np.uint8)
    yield 'canvas-patch',a,False,False
    yield 'epoch-reset',np.full((16,32,3),81,np.uint8),True,True


def map_for(rgb):
    h,w=rgb.shape[:2];mw,mh=codec.roi.geometry(w,h)
    m=np.full((mh,mw),16,np.uint8)
    if (w,h)==(720,480):
        return codec.roi.declared_map(w,h,((16,48,192,80),(160,352,400,80)),8,16)
    m[:min(2,mh),:min(2,mw)]=8
    return m


def main():
    paths=[HERE/'export_fixtures.py',HERE/'chunks.py',HERE/'harness.py',Path(codec.__file__),
           Path(codec.roi.__file__),Path(codec.mt.__file__),Path(codec.ft.__file__),
           Path(codec.token_coeff.__file__),Path(codec.word_coeff.__file__),Path(codec.word_coeff.frozen_codec.__file__),Path(corpus.__file__)]
    hashes={str(p):digest(p) for p in paths}
    out=HERE/'fixtures';out.mkdir(exist_ok=True)
    enc=codec.Encoder();rx=codec.Receiver();ingress=chunks.Reassembler()
    epoch=1;frame=0;now=0;cases=[];files={};datagram_count=0;total_forward_calls=0
    def save(name,data):
        p=out/name;p.write_bytes(data)
        files[name]={'bytes':len(data),'sha256':digest(p)}
        return name
    for name,rgb,force_key,reset in sources():
        if reset:
            epoch=2;frame=0;ingress.reset(epoch);enc=codec.Encoder(epoch);rx=codec.Receiver(epoch)
        m=map_for(rgb);before_forward=enc.forward_calls
        packet=enc.prepare(rgb,frame,scale_map=m,force_key=force_key)
        total_forward_calls+=enc.forward_calls-before_forward
        parsed=codec.parse(packet,epoch)
        wire=chunks.datagrams(packet,epoch,frame)
        before=rx.last_frame_id;complete=None
        # Reverse every complete frame's chunks; insert one duplicate before
        # the final missing chunk. Complete decode is still a separate action.
        order=list(reversed(wire))
        for i,datagram in enumerate(order):
            now+=1;complete=ingress.feed(datagram,now)
            if i==0 and complete is None:
                now+=1;assert ingress.feed(datagram,now) is None
            assert rx.last_frame_id==before
        assert complete is not None
        actual,info=decode_complete(complete,ingress,rx)
        expected=hashlib.sha256(actual.tobytes()).hexdigest()
        assert enc.expected_hash(frame)==expected
        assert enc.ack(frame,epoch=epoch)
        assert enc.anchor_id==rx.anchor_id and ingress.payload_bytes()==0
        datagram_count+=len(wire)
        coeff_files=[]
        for i,c in enumerate(parsed['coefficients']):
            coeff_files.append(save(f'{name}.plane{i}.i16le',c.astype('<i2').tobytes()))
        cases.append({'name':name,'epoch':epoch,'frame_id':frame,'anchor_id':rx.anchor_id,'key':info['key'],
                      'width':rgb.shape[1],'height':rgb.shape[0],'source_sha256':hashlib.sha256(rgb.tobytes()).hexdigest(),
                      'decoded_rgb_sha256':expected,'packet_bytes':len(packet),'map_bytes':parsed['map_bytes'],
                      'datagrams':len(wire),'chunk_header_bytes':chunks.HEADER.size,
                      'udp_payload_bytes':sum(len(p) for p in wire),
                      'ipv4_udp_bytes':sum(len(p)+28 for p in wire),
                      'source':save(f'{name}.rgb888',rgb.tobytes()),
                      'packet':save(f'{name}.gm01',packet),
                      'packed_datagrams':save(f'{name}.gf01',b''.join(struct.pack('!H',len(p))+p for p in wire)),
                      'map':save(f'{name}.scale8',m.tobytes()),'map_shape':list(m.shape),
                      'rgb565':save(f'{name}.rgb565le',corpus.rgb565(actual).astype('<u2').tobytes()),
                      'coefficients':coeff_files,
                      'coefficient_shapes':[list(c.shape) for c in parsed['coefficients']]})
        frame+=1
    assert hashes=={str(p):digest(p) for p in paths},'source changed'
    result={'evidence':'Generated functional GM01vectors and in-process reordered/duplicateGF01 replays; no socket/hardware/throughput proof',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),**{n:importlib.metadata.version(n) for n in ('numpy','Pillow','av')}},
            'format':'GM01 actual codec; GF01 experimental27byte chunk header,1024payload,2slots×49152bytes; not MSV1/JPEG compatible',
            'frame_cap':49152,'cases':cases,'files':files,'total_datagrams':datagram_count,
            'peak_slot_payload_bytes':ingress.peak_payload_bytes,'peak_slots':ingress.peak_slots,
            'all_resources_drained':not ingress.pending,'total_forward_plane_calls':total_forward_calls,
            'data_layout':'SourceRGB888rowmajor; RGB565littleendianrowmajor; scale8actualscalevalues8/16/32rowmajor; signed16LEcoefficients(block_raster,8,8). GF01fixture hasu16BE datagramlength prefixes not sent onwire.',
            'scope':'Immediate decode ACK after complete parse. Reverse chunks and duplicate exercised; measured memory covers logicalretainedpayload only, not transientcopies/decoder/workspaces/ESP32orFPGAallocation.'}
    (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'golden_frames':len(cases),'datagrams':datagram_count,'fixture_files':len(files),
                      'fixture_bytes':sum(f['bytes'] for f in files.values()),'max_packet_bytes':max(c['packet_bytes'] for c in cases),
                      'peak_slot_payload_bytes':ingress.peak_payload_bytes,'all_resources_drained':not ingress.pending},indent=2))


if __name__=='__main__':main()
