#!/usr/bin/env python3
"""Independent CS37 decoder; never imports v37 encoder or its hidden masks.

Dispatch4 is expanded using frozen v36 independent scalar-support masks;
frozen legacy entropy, motion/quant maps and arithmetic remain shared.
"""
from pathlib import Path
import importlib.util,sys,hashlib,json,struct,zlib
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('cs37_verify_frozen36',HERE.parent/'python-game-canonical-v36-study/verify.py')
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)
m=f.m;HEADER=f.HEADER
PROFILE=hashlib.sha256(b'CS37:implicit-hidden-raster-v1:'+json.dumps(f.n.RECTS,separators=(',',':')).encode()).digest()[:16]

def seal(body):return body+struct.pack('<I',zlib.crc32(body))

def parse(packet):
    if type(packet)is not bytes or not HEADER.size+8<=len(packet)<=49152:raise ValueError('bounded immutable CS37')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('CS37 CRC')
    fields=list(HEADER.unpack_from(packet))
    magic,version,flags,epoch,fid,rid,w,h,profile,rt,ot,nb,nh=fields
    if (magic,version,epoch,w,h,profile)!=(b'CS37',1,25,720,480,PROFILE) or flags not in (2,3):raise ValueError('CS37 exact profile')
    if ot==bytes(16) or fid>=m.NO_REF:raise ValueError('CS37 output identity')
    key=bool(flags&1)
    if key:
        if rid!=m.NO_REF or rt!=bytes(16):raise ValueError('CS37 independent key')
    elif rid>=fid or rt==bytes(16):raise ValueError('CS37 P identity')
    if min(nb,nh)<=0 or len(packet)!=HEADER.size+nb+nh+4:raise ValueError('CS37 exact lengths')
    inner,overlay=packet[HEADER.size:HEADER.size+nb],packet[HEADER.size+nb:-4]
    if len(inner)<m.HEADER.size+7 or zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('GS37 CRC/length')
    ib=list(m.HEADER.unpack_from(inner))
    if ib[0]!=b'GS37':raise ValueError('GS37 magic')
    # Envelope validation only; frozen decoder never sees dispatch4 syntax.
    ib[0]=b'GM27';synthetic=seal(m.HEADER.pack(*ib)+inner[m.HEADER.size:-4])
    bm=m.parse_metadata(synthetic,expected_epoch=25);hm=f.hud._meta(overlay)
    if (bm['key'],bm['frame_id'],bm['reference_id'],bm['width'],bm['height'],bm['reference_tag'])!=(key,fid,rid,w,h,rt):raise ValueError('CS37 base binding')
    if (hm['epoch'],hm['frame_id'],hm['reference_id'],hm['width'],hm['height'],tuple(hm['rectangles']))!=(25,fid,rid,w,h,f.n.RECTS):raise ValueError('CS37 exact HUD')
    pos=m.HEADER.size;nq,nv=bm['qmap_bytes'],bm['vector_bytes']
    q=m.roi.unpack_map(inner[pos:pos+nq],(w+15)//16,(h+15)//16);pos+=nq
    mw,mh=m.base._grid(w,h,bm['block_size'])
    vectors=np.zeros((mh,mw,2),np.int8) if key else m.base.unpack_vectors(inner[pos:pos+nv],mw,mh);pos+=nv
    coefficients=[];dispatch=[];plane_payloads=[]
    for plane,(size,safe) in enumerate(zip(bm['plane_lengths'],f.safe_blocks(),strict=True)):
        payload=inner[pos:pos+size];pos+=size;mask=safe.reshape(-1);n=len(mask)
        bw=((w if plane==0 else w//2)+7)//8
        if payload[0]==4:
            visible=m.base._decode_plane(payload[1:],int((~mask).sum()),1)
            c=np.zeros((n,8,8),np.int16);c[~mask]=visible
        elif payload[0]in (0,1,2,3):c=m.base._decode_plane(payload,n,bw)
        else:raise ValueError('GS37 plane dispatch')
        if np.any(c[mask]):raise ValueError('GS37 hidden values must be absent or zero')
        coefficients.append(c);dispatch.append(payload[0]);plane_payloads.append(payload)
    assert pos==len(inner)-4
    return dict(key=key,frame_id=fid,reference_id=rid,reference_tag=rt,output_tag=ot,base_tag=bm['reconstructed_tag'],
                qmap=q,vectors=vectors,block_size=bm['block_size'],coefficients=tuple(coefficients),hud=overlay,dispatch=dispatch,plane_payloads=plane_payloads)

class Receiver:
    def __init__(self):self.ref=None;self.rid=m.NO_REF;self.hud=None;self.last=-1
    def receive(self,packet):
        meta=parse(packet);key=meta['key']
        if meta['frame_id']<=self.last:raise ValueError('CS37 monotonic frame')
        if key:prediction=tuple(np.full(s,128,np.int16) for s in ((480,720),(240,360),(240,360)))
        else:
            if self.ref is None or self.rid!=meta['reference_id'] or m.C.reference_tag(self.ref)!=meta['reference_tag']:raise ValueError('CS37 actual committed reference')
            prediction=m.predict(self.ref,meta['vectors'],meta['block_size'])
        out=m.gm.reconstruct(meta['coefficients'],prediction,meta['qmap'],720,480)
        if m.C.reference_tag(out)!=meta['base_tag']:raise ValueError('GS37 reconstruction binding')
        normalized=f.normalize(out)
        if m.C.reference_tag(normalized)!=meta['output_tag']:raise ValueError('CS37 normalized binding')
        patches,_=f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,expected_reference_id=None if key else self.rid)
        self.ref,self.rid,self.hud,self.last=normalized,meta['frame_id'],patches,meta['frame_id']
        return normalized,patches,meta

def main():
    data=f.frozen.load(HERE/'results.json')
    for path,tag in data['source_sha256'].items():assert f.frozen.sha(ROOT/path)==tag,path
    oldfolder=HERE.parent/'python-game-canonical-v36-study';old=f.frozen.load(oldfolder/'results.json')
    count=selected=0
    for case in data['cases']:
        source=old['motion_probe'] if case['kind']=='fractional_motion' else next(c for c in old['cases'] if c['scene']==case['scene'])
        rx,baseline=Receiver(),f.Receiver()
        assert [r['id'] for r in case['rows']]==list(range(6 if case['kind']=='fractional_motion' else 48))
        for row,prior in zip(case['rows'],source['rows'],strict=True):
            packet=f.frozen.raw(row['packet'],HERE);original=f.frozen.raw(prior['skip']['packet'],oldfolder)
            actual,patches,meta=rx.receive(packet);expected,oldhud,oldmeta=baseline.receive(original)
            assert len(packet)==row['complete_bytes']<=len(original)==row['old_complete_bytes']
            for a,b in zip(actual,expected,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(patches,oldhud,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            oldparsed=m.parse(oldmeta['base']);oldcoeff=oldparsed['coefficients']
            for a,b in zip(meta['coefficients'],oldcoeff,strict=True):np.testing.assert_array_equal(a,b)
            # Recompute all compact alternatives using frozen entropy primitives,
            # not the new transcoder. Independently verify exact fallback/ties.
            oldpos=m.HEADER.size+oldparsed['qmap_bytes']+oldparsed['vector_bytes']
            entropy=f.frozen.shared.entropy
            for size,coeff,safe,payload,work in zip(oldparsed['plane_lengths'],oldcoeff,f.safe_blocks(),meta['plane_payloads'],row['work']['planes'],strict=True):
                previous=oldmeta['base'][oldpos:oldpos+size];oldpos+=size
                visible=coeff[~safe.reshape(-1)]
                plan=entropy._plane_plan(visible,1,m)
                encoded,*_=entropy._construct(visible,1,plan,m)
                compact=b'\x04'+encoded;winner=compact if len(compact)<len(previous) else previous
                assert payload==winner
                assert (work['old_bytes'],work['compact_bytes'],work['selected_bytes'])==(len(previous),len(compact),len(payload))
                assert work['implicit_selected']==(payload[0]==4)
            assert oldpos==len(oldmeta['base'])-4
            assert m.C.reference_tag(actual).hex()==prior['skip']['normalized_tag']==row['normalized_tag']
            display=f.n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(actual)),tuple(p['words'] for p in patches))
            assert f.n.digest(display)==prior['skip']['display_sha256']==row['display_sha256']
            count+=1;selected+=meta['dispatch'].count(4)
        assert sum(r['complete_bytes'] for r in case['rows'])==case['summary']['complete_bytes']
        assert sum(r['old_complete_bytes'] for r in case['rows'])==case['summary']['old_complete_bytes']
    assert count==102
    print(json.dumps(dict(exact_frames=count,implicit_plane_payloads=selected,independent_compact_alternatives=count*3,new_encoder_imported=False,new_RTL_implemented=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
