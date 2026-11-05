#!/usr/bin/env python3
"""Independent RP39 dynamic distinct-predictor rank decoder.

No v39 encoder/helper is imported. Frozen SP38 predictor/quant/entropy primitives
are shared, while stable clipped-predictor deduplication, conditional unary rank
events, syntax validation and causal reconstruction are implemented here.
"""
from pathlib import Path
import hashlib,importlib.util,json,math,struct,sys,zlib
import numpy as np

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value

spatial=module('rank39_frozen_spatial38_decoder',HERE.parent/'python-game-spatial-v38-study/verify.py')
arithmetic=module('rank39_frozen_AB38_reader',HERE.parent/'python-game-binary-v38-study/decoder.py')
f,m=spatial.f,spatial.m
OUTER,INNER=spatial.OUTER,spatial.INNER
PROFILE=hashlib.sha256(b'RP39:distinct-clipped-prediction-rank-v1:tilemajor:truncated-unary:AB38ctx44:'+
    json.dumps(f.n.RECTS,separators=(',',':')).encode()).digest()[:16]
OLD=HERE.parent/'python-game-spatial-v38-study'

def seal(body):return body+struct.pack('<I',zlib.crc32(body))
def load(path):return json.loads(Path(path).read_text())
def raw(desc,folder=HERE):return f.frozen.raw(desc,folder)

def unique_predictors(temporal,current,by,bx):
    representatives=[];predictions=[]
    for mode in range(4):
        prediction=spatial.predict_block(temporal,current,by,bx,mode)
        if not any(np.array_equal(prediction,old) for old in predictions):
            representatives.append(mode);predictions.append(prediction)
    assert 1<=len(representatives)<=4 and representatives[0]==0
    return representatives,predictions

def canonical_mode(representatives,rank):
    if type(rank)is not int or not 0<=rank<len(representatives):raise ValueError('rank inside derived predictor menu')
    return representatives[rank]

class RankReader:
    def __init__(self,payload):
        if type(payload)is not bytes or len(payload)<8 or payload[0]!=3:raise ValueError('rank arithmetic mode syntax')
        self.bits=struct.unpack_from('<I',payload,1)[0]
        self.reader=arithmetic.ArithmeticReader(payload[5:],self.bits)
        self.decisions=0;self.maximum_renorm=0;self.contexts=set()
    def rank(self,count,by,bx):
        if type(count)is not int or not 1<=count<=4:raise ValueError('derived menu cardinality')
        if count==1:return 0
        base=((by&1)*2+(bx&1))*12+(count-2)*3
        for step in range(count-1):
            context=base+step
            if not 0<=context<=44:raise ValueError('bounded rank context')
            before=self.reader.pos;bit=self.reader.decode(context)
            self.maximum_renorm=max(self.maximum_renorm,self.reader.pos-before)
            self.decisions+=1;self.contexts.add(context)
            if not bit:return step
        return count-1
    def finish(self):
        self.reader.finish()
        assert self.bits>=18 and self.reader.pos==self.bits and self.maximum_renorm<=16
        return dict(binary_decisions=self.decisions,probability_products=self.decisions,
            renorm_steps=self.bits-18,max_renorm_per_bit=self.maximum_renorm,
            arithmetic_bits=self.bits,contexts_used=sorted(self.contexts))

def reconstruct_plane(temporal,coefficients,component,tables,safe):
    height,width=temporal.shape;bh,bw=height//8,width//8;mask=safe.reshape(-1)
    if coefficients.shape!=(bh*bw,8,8) or np.any(coefficients[mask]):raise ValueError('bounded hidden-zero block array')
    if not component or component[0]>3:raise ValueError('rank/fallback mode dispatch')
    if component[0]==3:reader=RankReader(component);fallback=None
    else:
        reader=None;fallback=np.zeros(len(mask),np.uint8)
        fallback[~mask]=spatial.unpack_modes(component,int((~mask).sum()))
    current=np.empty_like(temporal);modes=np.zeros(len(mask),np.uint8);ranks=np.zeros(len(mask),np.uint8)
    menu_counts=[0,0,0,0];events=0
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx;y,x=by*8,bx*8
                if safe[by,bx]:current[y:y+8,x:x+8]=128;continue
                representatives,predictions=unique_predictors(temporal,current,by,bx)
                count=len(representatives);menu_counts[count-1]+=1
                if reader is not None:
                    rank=reader.rank(count,by,bx);mode=canonical_mode(representatives,rank)
                else:
                    mode=int(fallback[index])
                    if mode not in representatives:raise ValueError('fallback selected mode must be first stable duplicate')
                    rank=representatives.index(mode)
                events+=min(rank+1,count-1)
                modes[index]=mode;ranks[index]=rank
                residual=m.ft.inverse(coefficients[index].astype(np.int64)*tables[index])
                current[y:y+8,x:x+8]=np.clip(residual+predictions[rank],0,255).astype(np.int16)
    work=reader.finish() if reader is not None else None
    if work is not None:assert work['binary_decisions']==events
    return current,modes,ranks,dict(menu_counts=menu_counts,implicit_singleton_blocks=menu_counts[0],
        truncated_unary_decisions=events,arithmetic=work)

def parse(packet):
    if type(packet)is not bytes or not OUTER.size+INNER.size+12<=len(packet)<=49152:raise ValueError('bounded immutable RP39')
    if zlib.crc32(packet[:-4])!=struct.unpack('<I',packet[-4:])[0]:raise ValueError('RP39 CRC')
    magic,version,flags,epoch,fid,rid,w,h,profile,rt,ot,nb,nh=OUTER.unpack_from(packet)
    if (magic,version,epoch,w,h,profile)!=(b'RP39',1,25,720,480,PROFILE) or flags not in (0,1):raise ValueError('RP39 exact profile')
    key=bool(flags)
    if fid>=m.NO_REF or ot==bytes(16):raise ValueError('RP39 frame/output identity')
    if key:
        if rid!=m.NO_REF or rt!=bytes(16):raise ValueError('RP39 independent key')
    elif rid>=fid or rt==bytes(16):raise ValueError('RP39 past reference')
    if nb<INNER.size+4 or nh<=0 or len(packet)!=OUTER.size+nb+nh+4:raise ValueError('RP39 exact component lengths')
    inner=packet[OUTER.size:OUTER.size+nb];overlay=packet[OUTER.size+nb:-4]
    if zlib.crc32(inner[:-4])!=struct.unpack('<I',inner[-4:])[0]:raise ValueError('TR39 CRC')
    im,iv,ik,ie,iff,ir,iw,ih,irt,iot,*sizes=INNER.unpack_from(inner)
    if (im,iv,ik,ie,iff,ir,iw,ih,irt,iot)!=(b'TR39',1,flags,epoch,fid,rid,w,h,rt,ot):raise ValueError('TR39 bound identity')
    if any(n<=0 for n in sizes) or INNER.size+sum(sizes)+4!=len(inner):raise ValueError('TR39 exact lengths')
    hm=f.hud._meta(overlay)
    if (hm['epoch'],hm['frame_id'],hm['reference_id'],hm['width'],hm['height'],tuple(hm['rectangles']))!=(25,fid,rid,w,h,f.n.RECTS):raise ValueError('RP39 exact HUD')
    nq,*lengths=sizes;pos=INNER.size
    qmap=m.roi.unpack_map(inner[pos:pos+nq],45,30);qmap_bytes=inner[pos:pos+nq];pos+=nq
    mode_payloads=[]
    for length,safe in zip(lengths[:3],f.safe_blocks(),strict=True):
        data=inner[pos:pos+length];pos+=length
        if not data or data[0]>3:raise ValueError('RP39 mode dispatch')
        if data[0]<3:spatial.unpack_modes(data,int((~safe).sum()))
        else:RankReader(data)
        mode_payloads.append(data)
    coefficients=[];plane_payloads=[]
    for plane,(length,safe) in enumerate(zip(lengths[3:],f.safe_blocks(),strict=True)):
        data=inner[pos:pos+length];pos+=length;mask=safe.reshape(-1);bw=(720 if plane==0 else 360)//8
        if data[0]==4:
            visible=m.base._decode_plane(data[1:],int((~mask).sum()),1)
            coeff=np.zeros((len(mask),8,8),np.int16);coeff[~mask]=visible
        elif data[0]in (0,1,2,3):coeff=m.base._decode_plane(data,len(mask),bw)
        else:raise ValueError('TR39 coefficient dispatch')
        if np.any(coeff[mask]):raise ValueError('TR39 hidden coefficient0')
        coefficients.append(coeff);plane_payloads.append(data)
    if pos!=len(inner)-4:raise ValueError('TR39 ending')
    return dict(key=key,frame_id=fid,reference_id=rid,reference_tag=rt,output_tag=ot,qmap=qmap,qmap_bytes=qmap_bytes,
        mode_payloads=mode_payloads,coefficients=tuple(coefficients),plane_payloads=plane_payloads,hud=overlay,inner_bytes=len(inner))

class Receiver:
    def __init__(self):self.ref=None;self.rid=m.NO_REF;self.hud=None;self.last=-1
    def receive(self,packet):
        meta=parse(packet);key=meta['key']
        if meta['frame_id']<=self.last:raise ValueError('RP39 monotonic publication')
        if key:temporal=tuple(np.full(s,128,np.int16) for s in ((480,720),(240,360),(240,360)))
        else:
            if self.ref is None or self.rid!=meta['reference_id'] or m.C.reference_tag(self.ref)!=meta['reference_tag']:raise ValueError('RP39 actual committed reference')
            temporal=self.ref
        pixels=[];modes=[];ranks=[];work=[]
        for plane,(base,coeff,component,safe) in enumerate(zip(temporal,meta['coefficients'],meta['mode_payloads'],f.safe_blocks(),strict=True)):
            out,mode,rank,record=reconstruct_plane(base,coeff,component,m.roi.block_tables(meta['qmap'],720,480,plane),safe)
            pixels.append(out);modes.append(mode);ranks.append(rank);work.append(record)
        pixels=tuple(pixels)
        if m.C.reference_tag(pixels)!=meta['output_tag']:raise ValueError('RP39 committed output binding')
        patches,_=f.hud.decode_hud(meta['hud'],None if key else self.hud,expected_epoch=25,expected_reference_id=None if key else self.rid)
        meta.update(modes=tuple(modes),ranks=tuple(ranks),rank_work=work)
        self.ref,self.rid,self.hud,self.last=pixels,meta['frame_id'],patches,meta['frame_id']
        return pixels,patches,meta

def array(desc,count):
    if desc['shape']!=[count] or desc['dtype']!='|u1':raise ValueError('bounded full-block u8 rank array')
    value=raw(desc)
    if len(value)!=count:raise ValueError('exact rank array length')
    return np.frombuffer(value,np.uint8).copy()

def verify_trial(payload,temporal,committed,safe,expected_modes):
    """Decode every proposed stream against independently decoded old context.

    The old full plane is available here, but the frozen predictor only reads
    earlier neighbors inside each tile. Thus no future pixel can influence a
    derived menu. Selected RP39 packets are separately decoded from empty state.
    """
    height,width=temporal.shape;bh,bw=height//8,width//8;mask=safe.reshape(-1)
    menus=np.zeros(len(mask),np.uint8);ranks=np.zeros(len(mask),np.uint8)
    reader=RankReader(payload)
    for ty in range(0,bh,2):
        for tx in range(0,bw,2):
            for dy,dx in ((0,0),(0,1),(1,0),(1,1)):
                by,bx=ty+dy,tx+dx
                if by>=bh or bx>=bw:continue
                index=by*bw+bx
                if safe[by,bx]:continue
                representatives,_=unique_predictors(temporal,committed,by,bx)
                rank=reader.rank(len(representatives),by,bx)
                assert canonical_mode(representatives,rank)==expected_modes[index]
                menus[index]=len(representatives);ranks[index]=rank
    work=reader.finish()
    work.update(menu_counts=[int(np.count_nonzero(menus==n)) for n in range(1,5)],
        rank_counts=[int(np.count_nonzero((ranks==r)&~mask)) for r in range(4)],
        visible_blocks=int((~mask).sum()))
    return menus,ranks,work

def check_plane_work(work,independent,oldpayload,candidate,selected,plane):
    assert work['plane']==plane
    assert work['visible_blocks']==independent['visible_blocks']
    assert work['menu_counts']==independent['menu_counts'] and work['rank_counts']==independent['rank_counts']
    assert work['rank_payload_bytes']==len(candidate) and work['arithmetic_bit_count']==independent['arithmetic_bits']
    for key in ('binary_decisions','probability_products','renorm_steps','max_renorm_per_bit'):
        assert work[key]==independent[key]
    assert work['context_ids']==independent['contexts_used'] and work['active_contexts']==len(independent['contexts_used'])
    assert work['logical_probability_state_bytes']==88 and work['interval_bits']==16 and work['probability_bits']==8
    assert work['multiply_operand_bits']==[17,8] and work['maximum_decisions_per_rank']==3
    assert work['hidden_bitmap_bytes']==0 and work['rank_header_bytes']==5 and work['termination_guard_bits']==18
    assert (work['old_mode_bytes'],work['selected_mode_bytes'])==(len(oldpayload),len(selected))
    rank_selected=len(candidate)<len(oldpayload)
    assert work['rank_selected']is rank_selected
    assert selected==(candidate if rank_selected else oldpayload)

def main():
    data=load(HERE/'results.json');assert data['schema']=='gamebub-mode-rank-v39'
    assert data['physical_30fps_proven']is False and data['new_RTL_implemented']is False and data['HEVC_AV1_superiority_proven']is False
    assert data['profile']['profile_tag']==PROFILE.hex() and data['profile']['old_full_mode_fallback_wins_ties']is True
    assert data['profile']['coefficients_unchanged']is True and data['profile']['probability_states']==88
    for name,tag in data['source_sha256'].items():
        path=Path(name);assert not path.is_absolute() and '..'not in path.parts
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==tag,path
    prior=load(OLD/'results.json');inputs=load(f.n.V24/'results.json')['inputs']
    oldcases={(c['scene'],c['kind'],c['policy']):c for c in prior['cases']}
    keys=[(c['scene'],c['kind'],c['policy']) for c in data['cases']]
    assert len(keys)==len(set(keys))==10 and set(keys)==set(oldcases)
    synthetic={c['scene']:spatial.array(c['original'],(480,720),'<u2') for c in prior['synthetic_inputs']}
    count=trials=selected_count=singletons=products=0
    for case in data['cases']:
        key=(case['scene'],case['kind'],case['policy']);oldcase=oldcases[key]
        assert [r['id'] for r in case['rows']]==list(range(len(oldcase['rows'])))
        rx=Receiver();oldrx=spatial.Receiver();checks=[]
        for row,oldrow in zip(case['rows'],oldcase['rows'],strict=True):
            fid=row['id'];is_key=fid%24==0;rid=m.NO_REF if is_key else fid-1
            assert type(fid)is int and row['key']==is_key and row['reference_id']==rid
            assert row['source_sha256']==oldrow['source_sha256']
            packet=raw(row['packet']);incoming=raw(row['old_packet'],OLD)
            assert incoming==raw(oldrow['packet'],OLD)
            oldmeta=spatial.parse(incoming);newmeta=parse(packet)
            assert (newmeta['key'],newmeta['frame_id'],newmeta['reference_id'])==(is_key,fid,rid)
            assert newmeta['reference_tag'].hex()==row['reference_tag']==oldrow['reference_tag']
            assert newmeta['output_tag']==oldmeta['output_tag']
            assert len(packet)==row['complete_bytes']<=row['old_complete_bytes']==len(incoming)<=49152
            temporal=tuple(np.full(s,128,np.int16) for s in ((480,720),(240,360),(240,360))) if is_key else rx.ref
            assert newmeta['reference_tag']==(bytes(16) if is_key else m.C.reference_tag(temporal))
            # Lossless wrapper change: coefficient payloads/HUD and qmap bytes
            # must be preserved, rather than only produce equal visible pixels.
            oldouter=OUTER.unpack_from(incoming);oldinner=incoming[OUTER.size:OUTER.size+oldouter[11]]
            oldfields=INNER.unpack_from(oldinner);oldq=oldinner[INNER.size:INNER.size+oldfields[10]]
            assert newmeta['qmap_bytes']==oldq and newmeta['hud']==oldmeta['hud']
            assert newmeta['plane_payloads']==oldmeta['plane_payloads']
            np.testing.assert_array_equal(newmeta['qmap'],oldmeta['qmap'])
            for a,b in zip(newmeta['coefficients'],oldmeta['coefficients'],strict=True):np.testing.assert_array_equal(a,b)
            pixels,patches,decoded=rx.receive(packet);expected,oldpatches,_=oldrx.receive(incoming)
            for a,b in zip(pixels,expected,strict=True):np.testing.assert_array_equal(a,b)
            for a,b in zip(patches,oldpatches,strict=True):np.testing.assert_array_equal(a['words'],b['words'])
            for a,b in zip(decoded['modes'],oldmeta['modes'],strict=True):np.testing.assert_array_equal(a,b)
            assert m.C.reference_tag(pixels).hex()==row['normalized_tag']==oldrow['normalized_tag']
            if case['kind']=='main':
                source=next(c for c in inputs if c['scene']==case['scene'])['rows'][fid]
                original=f.n.original(source);assert source['common_yuv420_u8_sha256']==row['source_sha256']
            else:original=synthetic[case['scene']]
            quality,display=f.metric(pixels,original,patches)
            assert quality==row['hybrid']==oldrow['hybrid'] and display==row['display_sha256']==oldrow['display_sha256']
            work=row['work'];assert work['input_complete_bytes']==len(incoming) and work['output_complete_bytes']==len(packet)
            assert work['old_encode_already_paid']is True and work['coefficient_payloads_unchanged']is True
            assert work['new_outer_bytes']==80 and work['new_inner_header_bytes']==84
            assert math.isfinite(work['transcode_ms']) and work['transcode_ms']>0
            assert len(row['trials'])==len(work['planes'])==3
            for plane,(trial,record,base,committed,safe,modes,selected,oldpayload) in enumerate(zip(
                    row['trials'],work['planes'],temporal,expected,f.safe_blocks(),oldmeta['modes'],
                    newmeta['mode_payloads'],oldmeta['mode_payloads'],strict=True)):
                candidate=raw(trial['rank_packet'])
                menus,ranks,independent=verify_trial(candidate,base,committed,safe,modes)
                np.testing.assert_array_equal(array(trial['menus'],safe.size),menus)
                np.testing.assert_array_equal(array(trial['ranks'],safe.size),ranks)
                np.testing.assert_array_equal(decoded['ranks'][plane],ranks)
                assert decoded['rank_work'][plane]['menu_counts']==independent['menu_counts']
                assert decoded['rank_work'][plane]['truncated_unary_decisions']==independent['binary_decisions']
                check_plane_work(record,independent,oldpayload,candidate,selected,plane)
                trials+=1;selected_count+=record['rank_selected'];singletons+=menus.tolist().count(1)
                products+=independent['probability_products']
            assert len(incoming)-len(packet)==sum(w['old_mode_bytes']-w['selected_mode_bytes'] for w in work['planes'])
            count+=1;checks.append(row)
        summary=case['summary'];planes=[p for r in checks for p in r['work']['planes']]
        oldbytes=sum(r['old_complete_bytes'] for r in checks);newbytes=sum(r['complete_bytes'] for r in checks)
        assert summary['frames']==len(checks) and summary['complete_bytes']==newbytes and summary['old_complete_bytes']==oldbytes
        assert summary['saved_bytes']==oldbytes-newbytes and math.isclose(summary['percent_saved'],100*(oldbytes-newbytes)/oldbytes,abs_tol=1e-12)
        assert summary['maximum_complete_bytes']==max(r['complete_bytes'] for r in checks)
        assert summary['old_mode_bytes']==sum(p['old_mode_bytes'] for p in planes)
        assert summary['selected_mode_bytes']==sum(p['selected_mode_bytes'] for p in planes)
        assert summary['rank_planes']==sum(p['rank_selected'] for p in planes)
        assert summary['trial_probability_products']==sum(p['probability_products'] for p in planes)
        assert summary['selected_probability_products']==sum(p['probability_products'] for p in planes if p['rank_selected'])
        assert summary['selected_arithmetic_bits']==sum(p['arithmetic_bit_count'] for p in planes if p['rank_selected'])
        assert summary['menu_counts']==[sum(p['menu_counts'][i] for p in planes) for i in range(4)]
        assert math.isclose(summary['mean_paid_transcode_ms'],sum(r['work']['transcode_ms'] for r in checks)/len(checks),abs_tol=1e-10)
        assert summary['active_mse']==sum(r['hybrid']['active_squared_error'] for r in checks)/sum(r['hybrid']['active_channel_samples'] for r in checks)
    assert count==54 and trials==162
    print(json.dumps(dict(exact_causal_frames=count,rank_trial_planes=trials,selected_rank_planes=selected_count,
        singleton_zero_decision_blocks=singletons,independent_probability_products=products,source_pins=len(data['source_sha256']),
        coefficient_payloads_unchanged=True,new_encoder_imported=False,physical_30fps_proven=False)))

if __name__=='__main__':main()
