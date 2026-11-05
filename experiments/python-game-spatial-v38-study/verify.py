#!/usr/bin/env python3
"""Independent SP38 tile-local spatial predictor and causal decoder.

No spatial encoder/helper is imported. Mode syntax, neighbor corrections, tile
order, hidden immediate publication and reconstruction are independently
implemented. Frozen entropy/quantization/Q14 arithmetic and source access are
shared primitives, not the new predictor or decoder.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,struct,sys,zlib
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('spatial38_independent_frozen37',HERE.parent/'python-game-implicit-v37-study/verify.py')
old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
f,m=old.f,old.m
OUTER=f.HEADER
INNER=struct.Struct('<4sBBHIIHH16s16s7I')
PROFILE=hashlib.sha256(b'SP38:tile2x2-residualEdges-v1:clippedPred:DCavailable:zeroTemporal:Q14:hiddenImmediate:'+
    json.dumps(f.n.RECTS,separators=(',',':')).encode()).digest()[:16]
CAP=49152

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def load(path):return json.loads(Path(path).read_text())
def raw(desc):return f.frozen.raw(desc,HERE)

def canonical_modes(modes):
    """Own syntax oracle: dense first on complete-length ties, then RLE."""
    a=np.asarray(modes)
    if a.ndim!=1 or not a.size or a.dtype.kind not in 'iu' or np.any(a<0) or np.any(a>3):raise ValueError('bounded mode vector')
    data=bytearray(1+(len(a)+3)//4)
    for i,value in enumerate(a):data[1+i//4]|=int(value)<<(6-2*(i%4))
    dense=bytes(data);runs=bytearray(b'\x01');start=0
    for end in range(1,len(a)+1):
        if end==len(a) or a[end]!=a[start]:
            runs.extend(struct.pack('<BH',int(a[start]),end-start));start=end
    choices=[dense,bytes(runs)]
    if not np.any(a):choices.append(b'\x02')
    return min(choices,key=len)

def unpack_modes(data,count):
    if type(data)is not bytes or type(count)is not int or not 0<count<=8100 or not data:
        raise ValueError('mode packet and expected visible count')
    if data[0]==0:
        if len(data)!=1+(count+3)//4:raise ValueError('dense exact mode length')
        pad=(-2*count)%8
        if pad and data[-1]&((1<<pad)-1):raise ValueError('dense mode zero padding')
        out=np.array([(data[1+i//4]>>(6-2*(i%4)))&3 for i in range(count)],np.uint8)
    elif data[0]==1:
        if len(data)<4 or (len(data)-1)%3:raise ValueError('RLE mode triples')
        values=[]
        for pos in range(1,len(data),3):
            value,run=struct.unpack_from('<BH',data,pos)
            if value>3 or not run or len(values)+run>count:raise ValueError('RLE mode domain/count')
            values.extend([value]*run)
        if len(values)!=count:raise ValueError('RLE exact expanded modes')
        out=np.array(values,np.uint8)
    elif data==b'\x02':out=np.zeros(count,np.uint8)
    else:raise ValueError('mode dispatch')
    if canonical_modes(out)!=data:raise ValueError('canonical complete-length mode representation')
    return out

def predict_block(temporal,current,by,bx,mode):
    """8x8 prediction; by/bx are block coordinates, not pixel coordinates.

    Tile-edge context is unavailable. Available residual edges are reconstructed
    current samples minus temporal samples at those same edge positions. Mode3
    averages AVAILABLE edges only, floor((sum+denominator//2)/denominator).
    """
    if type(mode)is not int or not 0<=mode<=3:raise ValueError('spatial prediction mode')
    y,x=8*by,8*bx
    has_top=bool(by&1);has_left=bool(bx&1)
    top=(current[y-1,x:x+8].astype(np.int64)-temporal[y-1,x:x+8]) if has_top else np.zeros(8,np.int64)
    left=(current[y:y+8,x-1].astype(np.int64)-temporal[y:y+8,x-1]) if has_left else np.zeros(8,np.int64)
    if mode==0:correction=0
    elif mode==1:correction=top[None,:]
    elif mode==2:correction=left[:,None]
    else:
        denominator=8*(has_top+has_left)
        correction=0 if not denominator else (int(top.sum()+left.sum())+denominator//2)//denominator
    return np.clip(temporal[y:y+8,x:x+8].astype(np.int64)+correction,0,255).astype(np.int16)

def reconstruct_plane(temporal,coefficients,modes,tables,safe):
    height,width=temporal.shape;bh,bw=height//8,width//8
    if coefficients.shape!=(bh*bw,8,8) or modes.shape!=(bh*bw,) or safe.shape!=(bh,bw):raise ValueError('fixed block arrays')
    if np.any(modes[safe.reshape(-1)]) or np.any(coefficients[safe.reshape(-1)]):raise ValueError('hidden mode0/coefficient0')
    current=np.empty((height,width),np.int16)
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx;y,x=by*8,bx*8
                if safe[by,bx]:
                    # This is normative BEFORE any later tile-local read.
                    current[y:y+8,x:x+8]=128
                    continue
                prediction=predict_block(temporal,current,by,bx,int(modes[index]))
                residual=m.ft.inverse(coefficients[index].astype(np.int64)*tables[index])
                current[y:y+8,x:x+8]=np.clip(residual+prediction,0,255).astype(np.int16)
    return current

def parse(packet):
    if type(packet)is not bytes or not OUTER.size+INNER.size+12<=len(packet)<=CAP:raise ValueError('bounded immutable SP38')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('SP38 CRC')
    magic,version,flags,epoch,fid,rid,w,h,profile,rt,ot,nb,nh=OUTER.unpack_from(packet)
    if (magic,version,epoch,w,h,profile)!=(b'SP38',1,25,720,480,PROFILE) or flags not in (0,1):raise ValueError('SP38 exact profile')
    key=bool(flags)
    if fid>=m.NO_REF or ot==bytes(16):raise ValueError('SP38 frame/output identity')
    if key:
        if rid!=m.NO_REF or rt!=bytes(16):raise ValueError('SP38 independent key')
    elif rid>=fid or rt==bytes(16):raise ValueError('SP38 past committed reference')
    if nb<INNER.size+4 or nh<=0 or len(packet)!=OUTER.size+nb+nh+4:raise ValueError('SP38 exact body lengths')
    inner=packet[OUTER.size:OUTER.size+nb];overlay=packet[OUTER.size+nb:-4]
    if zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('TS38 CRC')
    fields=INNER.unpack_from(inner)
    im,iv,ik,ie,iff,ir,iw,ih,irt,iot,*sizes=fields
    if (im,iv,ik,ie,iff,ir,iw,ih,irt,iot)!=(b'TS38',1,flags,epoch,fid,rid,w,h,rt,ot):raise ValueError('TS38 bound identity')
    if any(n<=0 for n in sizes) or INNER.size+sum(sizes)+4!=len(inner):raise ValueError('TS38 exact component lengths')
    hm=f.hud._meta(overlay)
    if (hm['epoch'],hm['frame_id'],hm['reference_id'],hm['width'],hm['height'],tuple(hm['rectangles']))!=(25,fid,rid,w,h,f.n.RECTS):raise ValueError('SP38 exact opaque HUD')
    nq,*lengths=sizes;pos=INNER.size
    qmap=m.roi.unpack_map(inner[pos:pos+nq],45,30);pos+=nq
    mode_payloads=[];modes=[]
    for length,safe in zip(lengths[:3],f.safe_blocks(),strict=True):
        data=inner[pos:pos+length];pos+=length;mask=safe.reshape(-1)
        visible=unpack_modes(data,int((~mask).sum()));all_modes=np.zeros(len(mask),np.uint8);all_modes[~mask]=visible
        modes.append(all_modes);mode_payloads.append(data)
    coefficients=[];plane_payloads=[]
    for plane,(length,safe) in enumerate(zip(lengths[3:],f.safe_blocks(),strict=True)):
        data=inner[pos:pos+length];pos+=length;mask=safe.reshape(-1);bw=(720 if plane==0 else 360)//8
        if data[0]==4:
            visible=m.base._decode_plane(data[1:],int((~mask).sum()),1)
            coeff=np.zeros((len(mask),8,8),np.int16);coeff[~mask]=visible
        elif data[0]in (0,1,2,3):coeff=m.base._decode_plane(data,len(mask),bw)
        else:raise ValueError('TS38 coefficient dispatch')
        if np.any(coeff[mask]):raise ValueError('TS38 hidden coefficients must be zero')
        coefficients.append(coeff);plane_payloads.append(data)
    if pos!=len(inner)-4:raise ValueError('TS38 component ending')
    return dict(key=key,frame_id=fid,reference_id=rid,reference_tag=rt,output_tag=ot,
        qmap=qmap,modes=tuple(modes),coefficients=tuple(coefficients),mode_payloads=mode_payloads,
        plane_payloads=plane_payloads,hud=overlay,inner_bytes=len(inner))

class Receiver:
    def __init__(self):self.ref=None;self.rid=m.NO_REF;self.hud=None;self.last=-1
    def receive(self,packet):
        meta=parse(packet);key=meta['key']
        if meta['frame_id']<=self.last:raise ValueError('SP38 monotonic publication')
        if key:temporal=tuple(np.full(s,128,np.int16) for s in ((480,720),(240,360),(240,360)))
        else:
            if self.ref is None or self.rid!=meta['reference_id'] or m.C.reference_tag(self.ref)!=meta['reference_tag']:raise ValueError('SP38 actual committed reference')
            temporal=self.ref
        pixels=tuple(reconstruct_plane(base,coeff,modes,m.roi.block_tables(meta['qmap'],720,480,plane),safe)
            for plane,(base,coeff,modes,safe) in enumerate(zip(temporal,meta['coefficients'],meta['modes'],f.safe_blocks(),strict=True)))
        if m.C.reference_tag(pixels)!=meta['output_tag']:raise ValueError('SP38 committed output binding')
        patches,_=f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,expected_reference_id=None if key else self.rid)
        self.ref,self.rid,self.hud,self.last=pixels,meta['frame_id'],patches,meta['frame_id']
        return pixels,patches,meta

def array(desc,shape,dtype):
    if desc['shape']!=list(shape) or desc['dtype']!=np.dtype(dtype).str:raise ValueError('exact array descriptor')
    data=raw(desc)
    if len(data)!=int(np.prod(shape))*np.dtype(dtype).itemsize:raise ValueError('exact array bytes')
    return np.frombuffer(data,dtype=dtype).reshape(shape).copy()

def verify_candidates(source,temporal,tables,safe,modes,coeff,costs,policy):
    """Recompute all proposed distortion/quantization, batch-check exact CP02 sizes.

    Archived byte costs are used provisionally for ordered decisions, then every
    cost is independently checked with the frozen exact counter after the plane.
    No unchecked size can survive the final verification. Representative actual
    CP02 serializations additionally qualify the counter without a million CRCs.
    """
    height,width=source.shape;bh,bw=height//8,width//8
    current=np.empty_like(source);eligible=[];proposals=[];candidate_count=0
    menu=(0,) if policy=='mode0control' else (0,1,2,3)
    flat_safe=safe.reshape(-1)
    assert np.all(costs[flat_safe]==0)
    if policy=='mode0control':assert np.all(costs[~flat_safe,1:]==-1)
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx;y,x=by*8,bx*8
                if safe[by,bx]:
                    assert modes[index]==0 and not np.any(coeff[index])
                    current[y:y+8,x:x+8]=128;continue
                prediction=np.stack([predict_block(temporal,current,by,bx,mode) for mode in menu])
                original=source[y:y+8,x:x+8].astype(np.int64)
                transformed=m.ft.forward(original-prediction)
                quant=m.ft.round_quantize(transformed,tables[index]).astype(np.int16)
                assert not np.any(np.abs(quant.astype(np.int32))>m.ft.MAX_COEFF)
                pixels=np.clip(m.ft.inverse(quant.astype(np.int64)*tables[index])+prediction,0,255).astype(np.int16)
                errors=np.square(original-pixels).sum(axis=(1,2))
                np.testing.assert_array_equal(costs[index,list(menu),0],errors)
                sizes=costs[index,list(menu),1]
                scores=errors+8*(sizes-m.counter.OVERHEAD)
                chosen=int(np.argmin(scores));assert modes[index]==menu[chosen]
                np.testing.assert_array_equal(coeff[index],quant[chosen])
                current[y:y+8,x:x+8]=pixels[chosen]
                eligible.append(index);proposals.append(quant);candidate_count+=len(menu)
    joined=np.concatenate(proposals)
    exact_sizes=m.counter.isolated_packet_bytes(joined).reshape(-1,len(menu))
    np.testing.assert_array_equal(costs[np.array(eligible)][:,list(menu),1],exact_sizes)
    for index in sorted({0,len(joined)//2,len(joined)-1}):
        actual=m.gm.token_coeff.encode_coefficients(joined[index:index+1],1)
        assert len(actual)==exact_sizes.reshape(-1)[index]
    return current,candidate_count

def verify_coeff_entropy(meta):
    entropy=f.frozen.shared.entropy;records=[]
    for plane,(coeff,safe,payload) in enumerate(zip(meta['coefficients'],f.safe_blocks(),meta['plane_payloads'],strict=True)):
        bw=(720 if plane==0 else 360)//8
        full_plan=entropy._plane_plan(coeff,bw,m)
        full,*_=entropy._construct(coeff,bw,full_plan,m)
        visible=coeff[~safe.reshape(-1)];compact_plan=entropy._plane_plan(visible,1,m)
        compact,*_=entropy._construct(visible,1,compact_plan,m);compact=b'\x04'+compact
        expected=compact if len(compact)<len(full) else full
        assert payload==expected
        records.append(dict(full=len(full),compact=len(compact),selected=len(payload),implicit=len(compact)<len(full)))
    return records

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-spatial-v38'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    assert data['profile']['profile_tag']==PROFILE.hex() and data['profile']['lambda_value']==1
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..' not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    inputs=load(f.n.V24/'results.json')['inputs'];decoded_frames=nonzero_modes=candidate_count=0
    synthetic={}
    for fixture in data['synthetic_inputs']:
        packed=array(fixture['source'],(518400,),'u1')
        source=(packed[:345600].reshape(480,720).astype(np.int16),packed[345600:432000].reshape(240,360).astype(np.int16),packed[432000:].reshape(240,360).astype(np.int16))
        original=array(fixture['original'],(480,720),'<u2')
        expected=m.C.corpus.rgb565(m.ft.planes_to_rgb(source))
        for x,y,w,h in f.n.RECTS:expected[y:y+h,x:x+w]=np.uint16(0x4a49)
        np.testing.assert_array_equal(original,expected)
        assert fixture['scene']not in synthetic
        synthetic[fixture['scene']]=(source,original,raw(fixture['hud_packet']))
    assert set(synthetic)=={'flat','directional_tiles','low_amplitude_noise'}
    expected_cases={(c['scene'],'main',p) for c in inputs for p in ('mode0control','spatial')}
    expected_cases|={(scene,'synthetic',p) for scene in synthetic for p in ('mode0control','spatial')}
    keys=[(c['scene'],c['kind'],c['policy']) for c in data['cases']]
    assert len(keys)==len(set(keys))==10 and set(keys)==expected_cases
    for case in data['cases']:
        rx=Receiver();count=12 if case['kind']=='main' else 1
        assert [r['id'] for r in case['rows']]==list(range(count)) and all(type(r['id'])is int for r in case['rows'])
        inp=next((c for c in inputs if c['scene']==case['scene']),None)
        checks=[]
        for row in case['rows']:
            fid=row['id'];key=fid%24==0;rid=m.NO_REF if key else fid-1
            if case['kind']=='main':
                src=inp['rows'][fid];source=f.n.source(src);original=f.n.original(src)
                assert row['source_sha256']==src['common_yuv420_u8_sha256']
            else:source,original,_=synthetic[case['scene']]
            assert row['source_id']==dict(scene=case['scene'],id=fid,kind=case['kind'])
            assert row['source_sha256']==hashlib.sha256(b''.join(p.astype('u1').tobytes() for p in source)).hexdigest()
            packet=raw(row['packet']);meta=parse(packet)
            assert (meta['frame_id'],meta['reference_id'],meta['key'])==(fid,rid,key)
            assert row['key']==key and row['reference_id']==rid and row['reference_tag']==meta['reference_tag'].hex()
            temporal=tuple(np.full_like(p,128) for p in source) if key else rx.ref
            assert meta['reference_tag']==(bytes(16) if key else m.C.reference_tag(temporal))
            assert meta['hud']==raw(row['hud_packet'])
            if case['kind']=='synthetic':assert meta['hud']==synthetic[case['scene']][2]
            np.testing.assert_array_equal(meta['qmap'],m.roi.declared_map(720,480,f.n.ROIS,8,16))
            reconstructed=[];plane_mode_counts=[];plane_records=[]
            for plane,(base,src_plane,safe,modes,coeff) in enumerate(zip(temporal,source,f.safe_blocks(),meta['modes'],meta['coefficients'],strict=True)):
                np.testing.assert_array_equal(array(row['mode_arrays'][plane],(safe.size,),'u1'),modes)
                costs=array(row['candidate_cost_arrays'][plane],(safe.size,4,2),'<i8')
                actual,proposed=verify_candidates(src_plane,base,m.roi.block_tables(meta['qmap'],720,480,plane),safe,modes,coeff,costs,case['policy'])
                reconstructed.append(actual);candidate_count+=proposed
                plane_mode_counts.append([int(np.count_nonzero(modes[~safe.reshape(-1)]==v)) for v in range(4)])
                plane_records.append(proposed)
            entropy_records=verify_coeff_entropy(meta)
            pixels,patches,_=rx.receive(packet)
            for a,b in zip(pixels,reconstructed,strict=True):np.testing.assert_array_equal(a,b)
            expected_patches=tuple(original[y:y+h,x:x+w] for x,y,w,h in f.n.RECTS)
            for a,b in zip(patches,expected_patches,strict=True):np.testing.assert_array_equal(a['words'],b)
            assert len(packet)==row['complete_bytes']<=CAP and row['cap_fit']is True
            assert m.C.reference_tag(pixels).hex()==row['normalized_tag']
            quality,tag=f.metric(pixels,original,patches)
            assert quality==row['hybrid'] and tag==row['display_sha256']
            nonzero=sum(int(np.count_nonzero(v)) for v in meta['modes']);nonzero_modes+=nonzero
            if case['policy']=='mode0control':assert not nonzero
            work=row['work'];assert work['policy']==case['policy'] and work['RDO_pruning']is False
            assert math.isfinite(work['encode_ms']) and work['encode_ms']>0
            assert work['outer_bytes']==80 and work['inner_header_bytes']==84 and work['cap_fit']is True
            assert work['frame_complete_bytes']==len(packet)
            assert work['fullgrid_coefficient_arrays_bytes']==1036800
            assert work['mode_bytes']==sum(map(len,meta['mode_payloads'])) and work['coefficient_bytes']==sum(map(len,meta['plane_payloads']))
            assert meta['inner_bytes']==84+work['qmap_bytes']+work['mode_bytes']+work['coefficient_bytes']
            assert len(packet)==80+meta['inner_bytes']+len(meta['hud'])
            for plane,(detail,safe,record) in enumerate(zip(work['planes'],f.safe_blocks(),entropy_records,strict=True)):
                assert detail['plane']==plane and detail['mode_bytes']==len(meta['mode_payloads'][plane])
                assert detail['coefficient_bytes']==record['selected'] and detail['implicit_selected']is record['implicit']
                assert detail['fullgrid_payload_bytes']==record['full'] and detail['compact_payload_bytes']==record['compact']
                assert detail['visible_blocks']==int((~safe).sum()) and detail['hidden_blocks']==int(safe.sum())
                assert detail['mode_counts']==plane_mode_counts[plane] and detail['evaluated_block_candidates']==plane_records[plane]
            decoded_frames+=1
            checks.append(dict(bytes=len(packet),quality=quality,mode_counts=plane_mode_counts,work=work))
        summary=case['summary'];assert summary['frames']==count
        assert summary['complete_bytes']==sum(c['bytes'] for c in checks) and summary['maximum_complete_bytes']==max(c['bytes'] for c in checks)
        assert summary['mode_bytes']==sum(c['work']['mode_bytes'] for c in checks)
        assert summary['coefficient_bytes']==sum(c['work']['coefficient_bytes'] for c in checks)
        assert summary['active_mse']==sum(c['quality']['active_squared_error'] for c in checks)/sum(c['quality']['active_channel_samples'] for c in checks)
        assert summary['peak_frame_mse']==max(c['quality']['active_mse'] for c in checks)
        assert summary['all_frames_cap_fit']is True
        assert math.isclose(summary['mean_encode_ms'],sum(c['work']['encode_ms'] for c in checks)/count,abs_tol=1e-9)
        assert math.isclose(summary['nominal_Mbps_at30'],summary['complete_bytes']*240/count/1e6,abs_tol=1e-12)
        assert summary['mode_counts']==[sum(p[mode] for c in checks for p in c['mode_counts']) for mode in range(4)]
    assert decoded_frames==54
    print(json.dumps(dict(independent_spatial_decodes=decoded_frames,nonzero_spatial_modes=nonzero_modes,
        independently_recomputed_candidate_blocks=candidate_count,exact_mode_and_coefficient_payloads=True,
        source_pins=len(data['source_sha256']),new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
