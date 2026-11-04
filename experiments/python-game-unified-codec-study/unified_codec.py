"""AR02/AF02: GM/SR residual choice, two ACKed banks and exact display patches.

One prediction/forward transform feeds all actual inner candidates. Exact SR
dense CP02 bytes are shared with GM; split syntax and all losing/pruning work
are paid. Patches are display-only and never enter reference reconstruction.
"""
from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import sys
import time
from types import MappingProxyType
import numpy as np

HERE=Path(__file__).resolve().parent
for name in ('python-game-overlap-reference-study','python-game-skip-residual-study',
             'python-game-unified-ui-study'):
    sys.path.insert(0,str(HERE.parent/name))
import overlap_codec
import recent_codec as old
import skip_codec as sr
gm=old.gm
fast_codec=sr.fast_codec
corpus=fast_codec.hybrid.hp.corpus
NO_BANK,ZERO,KEY,PROMOTE,ACK,NACK=old.NO_BANK,old.ZERO,old.KEY,old.PROMOTE,old.ACK,old.NACK
Bank,Lease,Banks=old.Bank,old.Lease,old.Banks
reference_tag,pixels,body_crc,seal=old.reference_tag,old.pixels,old.body_crc,old.seal
HEADER=struct.Struct('<4sBBIIBBI16s16sIBI')
FEEDBACK=old.FEEDBACK
MAX_PATCHES=4


def ms(start):return (time.perf_counter_ns()-start)/1e6
def _ui():
    import ui_plugin
    return ui_plugin


def split_patches(blob,count):
    if type(count) is not int or not 0<=count<=MAX_PATCHES:raise ValueError('AR02 patch count')
    result=[];pos=0
    for _ in range(count):
        if pos+4>len(blob):raise ValueError('AR02 patch prefix')
        size=struct.unpack_from('<I',blob,pos)[0];pos+=4
        if size==0 or pos+size>len(blob):raise ValueError('AR02 patch length')
        result.append(blob[pos:pos+size]);pos+=size
    if pos!=len(blob):raise ValueError('AR02 patch section exact length')
    return tuple(result)


def _inner(packet,epoch,decode):
    if type(packet) is not bytes or len(packet)<gm.HEADER.size+4:raise ValueError('AR02 inner type/length')
    values=gm.HEADER.unpack_from(packet)
    magic,version,flags,session,frame,ref,w,h,dx,dy,mw,mh,nmap,*lengths=values
    is_sr=magic==sr.MAGIC
    if magic not in (gm.MAGIC,sr.MAGIC) or version!=1 or session!=epoch or session==gm.NO_REF:
        raise ValueError('AR02 inner dispatch/session')
    if (flags not in ((0,1,2,4) if is_sr else (0,1)) or frame==gm.NO_REF or dx or dy
            or (mw,mh)!=gm.roi.geometry(w,h) or nmap!=(mw*mh+3)//4
            or bool(flags&1)!=(ref==gm.NO_REF) or (not flags&1 and ref>=frame)
            or len(packet)!=gm.HEADER.size+nmap+sum(lengths)+4
            or body_crc(packet)!=struct.unpack('<I',packet[-4:])[0]):
        raise ValueError('AR02 inner identity/profile/CRC')
    gm.roi.unpack_map(packet[gm.HEADER.size:gm.HEADER.size+nmap],mw,mh)
    for i,size in enumerate(lengths):
        pw,ph=(w,h) if i==0 else (w//2,h//2);n=((pw+7)//8)*((ph+7)//8)
        lower=sr.PLANE.size if is_sr else gm.word_coeff.PAYLOAD_OVERHEAD
        upper=(sr.PLANE.size+(n+3)//4+2*n+128*n+gm.word_coeff.PAYLOAD_OVERHEAD
               if is_sr else 128*n+gm.word_coeff.PAYLOAD_OVERHEAD)
        if not lower<=size<=upper:raise ValueError('AR02 inner plane bound')
    parsed=(sr.parse(packet,epoch) if is_sr else gm.parse(packet,epoch)) if decode else None
    return dict(codec=magic.decode(),key=bool(flags&1),frame_id=frame,reference_id=ref,
                width=w,height=h,parsed=parsed,level=0 if not is_sr else sr.LEVELS[flags>>1])


def identity(packet,epoch=None,frame_cap=49152,*,decode=False):
    if type(packet) is not bytes or not HEADER.size+gm.HEADER.size+8<=len(packet)<=frame_cap:
        raise ValueError('AR02 complete cap/type/length')
    magic,version,flags,session,frame,refbank,dest,refid,reftag,newtag,ninner,count,npatch=HEADER.unpack_from(packet)
    if (magic!=b'AR02' or version!=2 or flags not in (0,KEY,PROMOTE) or session==gm.NO_REF
            or (epoch is not None and session!=epoch) or frame==gm.NO_REF
            or ninner<gm.HEADER.size+4 or count>MAX_PATCHES
            or len(packet)!=HEADER.size+ninner+npatch+4
            or body_crc(packet)!=struct.unpack('<I',packet[-4:])[0]):
        raise ValueError('AR02 outer identity/length/CRC')
    key,promoted=flags==KEY,flags==PROMOTE
    if key:
        valid=refbank==NO_BANK and refid==gm.NO_REF and reftag==ZERO and dest==0 and newtag!=ZERO
    else:
        valid=refbank in (0,1) and refid<frame and reftag!=ZERO
        valid &= (dest==1 and newtag!=ZERO) if promoted else (dest==NO_BANK and newtag==ZERO)
    if not valid:raise ValueError('AR02 reference/publication profile')
    inner=packet[HEADER.size:HEADER.size+ninner];p=_inner(inner,session,decode)
    if (p['frame_id'],p['reference_id'],p['key'])!=(frame,refid,key):raise ValueError('AR02 outer/inner identity')
    blob=packet[HEADER.size+ninner:-4];patch_packets=split_patches(blob,count)
    patches=_ui().validate_patches(patch_packets,p['width'],p['height']) if decode and count else ()
    return dict(epoch=session,frame_id=frame,key=key,promoted=promoted,reference_bank=refbank,
                reference_id=refid,reference_tag=reftag,destination_bank=dest,stored_tag=newtag,
                inner=inner,inner_codec=p['codec'],inner_bytes=ninner,parsed=p['parsed'],level=p['level'],
                patch_packets=patch_packets,patches=patches,patch_count=count,patch_bytes=npatch,
                width=p['width'],height=p['height'],body_crc=body_crc(packet),packet_bytes=len(packet))


def feedback(meta,status=ACK):
    if status not in (ACK,NACK):raise ValueError('AF02 status')
    stored=status==ACK and meta['destination_bank']!=NO_BANK
    return seal(FEEDBACK.pack(b'AF02',2,status,meta['epoch'],meta['frame_id'],meta['body_crc'],
               meta['destination_bank'] if stored else NO_BANK,meta['frame_id'] if stored else gm.NO_REF,
               meta['stored_tag'] if stored else ZERO))


def parse_feedback(data):
    if type(data) is not bytes or len(data)!=FEEDBACK.size+4 or body_crc(data)!=struct.unpack('<I',data[-4:])[0]:
        raise ValueError('AF02 length/CRC')
    magic,version,status,epoch,frame,crc,slot,stored_id,tag=FEEDBACK.unpack_from(data)
    if magic!=b'AF02' or version!=2 or status not in (ACK,NACK) or epoch==gm.NO_REF or frame==gm.NO_REF:
        raise ValueError('AF02 profile')
    return dict(status=status,epoch=epoch,frame_id=frame,body_crc=crc,stored_bank=slot,stored_id=stored_id,stored_tag=tag)


def _dense_payloads(packet):
    f=gm.HEADER.unpack_from(packet);pos=gm.HEADER.size+f[12];out=[]
    for n in f[13:16]:out.append(packet[pos:pos+n]);pos+=n
    return out


def _plane(coeff,blocks_w,dense=None):
    shared=dense is not None
    if dense is None:dense=gm.token_coeff.encode_coefficients(coeff,blocks_w)
    n=len(coeff);d=sr.PLANE.pack(sr.PLANE_MAGIC,0,n,0,0,len(dense))+dense
    modes,dc,full=sr.classifications(coeff)
    mapped=sr.pack_modes(modes);dcdata=coeff[dc,0,0].astype('<i2').tobytes()
    full_data=gm.token_coeff.encode_coefficients(coeff[full],1) if np.any(full) else b''
    s=sr.PLANE.pack(sr.PLANE_MAGIC,1,n,len(mapped),int(dc.sum()),len(full_data))+mapped+dcdata+full_data
    selected=s if len(s)<len(d) else d
    return selected,dict(mode='split' if selected is s else 'dense',dense_bytes=len(d),split_bytes=len(s),
        selected_bytes=len(selected),shared_gm_dense_payload=shared,actual_candidates=2,
        zero_blocks=int((modes==0).sum()),dc_blocks=int(dc.sum()),full_blocks=int(full.sum()))


def _sr_candidate(prepared,gm_candidate,limit):
    started=time.perf_counter_ns();p=prepared;m=gm_candidate.scale_map
    actual_limit=limit if not p.key else 0
    coefficients=[];payloads=[];details=[];pruning=[]
    dense=_dense_payloads(gm_candidate.packet)
    for i,original in enumerate(gm_candidate.coefficients):
        if actual_limit:c,stats=sr.prune(original,m,p.width,p.height,i,actual_limit)
        else:c=original;stats=dict(eligible=0,protected=0,zeroed=0,dc_only=0,max_reconstructed_yuv_delta=0,checked_blocks=0)
        c.setflags(write=False);coefficients.append(c);pruning.append(stats)
        pw=p.width if i==0 else p.width//2
        same=np.array_equal(c,original)
        payload,info=_plane(c,(pw+7)//8,dense[i] if same else None)
        payloads.append(payload);details.append(info)
    mw,mh=gm.roi.geometry(p.width,p.height);mapped=gm.roi.pack_map(m)
    flags=int(p.key)|(sr.LEVELS.index(actual_limit)<<1)
    body=sr.HEADER.pack(sr.MAGIC,1,flags,p.epoch,p.frame_id,p.reference_id,p.width,p.height,0,0,mw,mh,
                        len(mapped),*(len(x) for x in payloads))+mapped+b''.join(payloads)
    return seal(body),tuple(coefficients),tuple(details),tuple(pruning),actual_limit,ms(started)


@dataclass(frozen=True)
class Decision:
    packet:bytes|None
    frame_id:int
    key:bool
    promoted:bool
    reference_bank:int
    reference_id:int|None
    reference_tag:bytes
    destination_bank:int
    service_ms:float
    info:dict
    @property
    def accepted(self):return self.packet is not None


class Encoder(overlap_codec.Encoder):
    def __init__(self,epoch=1,window=3,frame_cap=49152,*,mode='exact',patch_builder=None):
        if mode not in ('gm','exact','prune2','prune4'):raise ValueError('AR02 coding mode')
        if type(frame_cap) is not int or not HEADER.size+gm.HEADER.size+8<=frame_cap<=49152:raise ValueError('AR02 cap')
        super().__init__(epoch,window,frame_cap)
        self.mode,self.patch_builder=mode,patch_builder
        self.analysis_count=0

    def prepare(self,rgb,frame_id,*,scale_map=None,quant_scale=16,force_key=False,promote=False,reference_bank=None):
        started=time.perf_counter_ns();a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
        if type(force_key) is not bool or type(promote) is not bool:raise ValueError('AR02 booleans')
        key=bool(force_key or self.banks[0] is None or self.banks[0].planes[0].shape!=(h,w));promoted=bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued<frame_id<gm.NO_REF or not self.can_prepare(key,promoted):
            raise ValueError('AR02 credit/identity/bank drain')
        if reference_bank is not None and (type(reference_bank) is not int or reference_bank not in (0,1)):
            raise ValueError('AR02 explicit reference')
        if key and reference_bank is not None:raise ValueError('AR02 key source')
        refslot=NO_BANK if key else reference_bank if reference_bank is not None else 1 if self.banks[1] is not None else 0
        ref=None if key else self.banks[refslot]
        if not key and (ref is None or ref.planes[0].shape!=(h,w)):raise ValueError('AR02 unconfirmed reference')
        local=gm.Encoder(self.epoch,self.window)
        if ref is not None:local.anchor_id,local._anchor=ref.frame_id,ref.planes
        began=time.perf_counter_ns();p=local.analyze(a,frame_id,force_key=key,mode='zero');analyze_ms=ms(began)
        self.analysis_count+=1;self.forward_calls+=3
        if scale_map is None:
            if type(quant_scale) is not int or quant_scale not in gm.roi.SCALES:raise ValueError('AR02 quant scale')
            mw,mh=gm.roi.geometry(w,h);scale_map=np.full((mh,mw),quant_scale,np.uint8)
        began=time.perf_counter_ns();gm_candidate=local.encode_candidate(p,scale_map);gm_ms=ms(began)
        inner=gm_candidate.packet;coefficients=gm_candidate.coefficients;codec='GM01';level=0
        attempts=[dict(codec='GM01',bytes=len(inner),service_ms=gm_ms,selected=True)]
        sr_details=();pruning=();sr_ms=0.
        if self.mode!='gm':
            limit=0 if self.mode=='exact' else int(self.mode[-1])
            alternative,c,details,pruning,lev,sr_ms=_sr_candidate(p,gm_candidate,limit)
            chosen=len(alternative)<len(inner)
            attempts[0]['selected']=not chosen
            attempts.append(dict(codec='SR01',bytes=len(alternative),service_ms=sr_ms,selected=chosen,
                                 level=lev,planes=details))
            if chosen:inner,coefficients,codec,level=alternative,c,'SR01',lev
            sr_details=details
        reconstruction_ms=tag_ms=0.;planes=None;tag=ZERO
        if key or promoted:
            began=time.perf_counter_ns();planes=fast_codec.reconstruct(coefficients,p.prediction,gm_candidate.scale_map,w,h);reconstruction_ms=ms(began)
            began=time.perf_counter_ns();tag=reference_tag(planes);tag_ms=ms(began)
        patches=();patch_info={};ui_ms=ui_validation_ms=0.;selected=[]
        base_bytes=HEADER.size+len(inner)+4
        if self.patch_builder is not None and base_bytes<=self.frame_cap:
            began=time.perf_counter_ns();selection=self.patch_builder.select(a,self.frame_cap-base_bytes);ui_ms=ms(began)
            patches=tuple(selection.patches);patch_info=selection.details
            if len(patches)>MAX_PATCHES:raise ValueError('AR02 patch callback count')
        began=time.perf_counter_ns()
        if patches:
            decoded=_ui().validate_patches(patches,w,h)
            for patch in decoded:
                x,y,rw,rh=patch['rect']
                if not np.array_equal(corpus.rgb565(a[y:y+rh,x:x+rw]),patch['words']):
                    raise ValueError('AR02 UI callback changed original RGB565 words')
                selected.append({k:v for k,v in patch.items() if k!='words'})
        ui_validation_ms=ms(began)
        blob=b''.join(struct.pack('<I',len(data))+data for data in patches)
        dest=0 if key else 1 if promoted else NO_BANK
        body=HEADER.pack(b'AR02',2,KEY if key else PROMOTE if promoted else 0,self.epoch,frame_id,refslot,dest,
            gm.NO_REF if ref is None else ref.frame_id,ZERO if ref is None else ref.tag,tag,len(inner),len(patches),len(blob))+inner+blob
        packet=seal(body);fit=len(packet)<=self.frame_cap
        info=dict(reference_choice_explicit=reference_bank is not None,pending_before=len(self.pending),
            pending_writers_before=sum(r['key'] or r['promoted'] for r in self.pending.values()),
            bank0_readers_before=sum(l.slot==0 for l in self._leases),bank1_readers_before=sum(l.slot==1 for l in self._leases),
            pending_bank0_consumers=sum(r['reference_bank']==0 for r in self.pending.values()),
            pending_bank1_consumers=sum(r['reference_bank']==1 for r in self.pending.values()),
            bytes=len(packet),inner_bytes=len(inner),envelope_bytes=HEADER.size+4,inner_codec=codec,level=level,
            analyze_ms=analyze_ms,candidate_ms=gm_ms+sr_ms,reconstruction_ms=reconstruction_ms,reference_tag_ms=tag_ms,
            analyze_calls=1,forward_calls=3,inner_attempts=attempts,pruning=pruning,sr_planes=sr_details,
            cap_fit=fit,promotion_reconstruction_paid=bool(key or promoted),
            reference_read_bytes=0 if ref is None else pixels(ref.planes),
            reconstruction_write_bytes=0 if planes is None else pixels(planes),
            reference_read_array_bytes=0 if ref is None else sum(x.nbytes for x in ref.planes),
            reconstruction_write_array_bytes=0 if planes is None else sum(x.nbytes for x in planes),
            tag_read_bytes=0 if planes is None else 4+2*pixels(planes),
            retained_banks_before=sum(b is not None for b in self.banks.values()),reference_array_bytes_before=self.retained_bytes(),
            ui_service_ms=ui_ms,ui_validation_ms=ui_validation_ms,patch_count=len(patches),patch_bytes=len(blob),
            selected=selected,selected_pixels=sum(x['rect'][2]*x['rect'][3] for x in selected),ui=patch_info,
            minimum_complete_inner_bytes=min(x['bytes'] for x in attempts))
        for name in ('reference_read_bytes','reconstruction_write_bytes','reference_read_array_bytes','reconstruction_write_array_bytes','tag_read_bytes'):
            setattr(self,name,getattr(self,name)+info[name])
        if fit:
            self.pending[frame_id]=dict(key=key,promoted=promoted,packet=packet,planes=planes,
                reference_bank=refslot,reference_id=None if ref is None else ref.frame_id,reference_tag=ZERO if ref is None else ref.tag,
                reference=None if key or promoted else ref,destination_bank=dest,stored_tag=tag,body_crc=body_crc(packet))
            if key:self.banks={0:None,1:None}
            elif promoted:self.banks[1]=None
            self.last_issued=frame_id;self._generation+=1;self.peak_pending=max(self.peak_pending,len(self.pending))
        self._observe();self.last_info=info
        return Decision(packet if fit else None,frame_id,key,promoted,refslot,None if ref is None else ref.frame_id,
                        ZERO if ref is None else ref.tag,dest,ms(started),info)

    def _expected(self,frame_id):
        row=self.pending[frame_id];meta=identity(row['packet'],self.epoch,self.frame_cap,decode=True)
        if row['planes'] is not None:planes=row['planes']
        else:
            p=meta['parsed'];ref=row['reference']
            planes=fast_codec.reconstruct(p['coefficients'],tuple(gm.mt.predict(ref.planes,0,0)),p['scale_map'],p['width'],p['height'])
        base=gm.ft.planes_to_rgb(planes)
        display=_ui().apply_patches(base,meta['patches']) if meta['patches'] else base
        return base,display

    def expected_hash(self,frame_id):return hashlib.sha256(self._expected(frame_id)[1].tobytes()).hexdigest()
    def expected_base_hash(self,frame_id):return hashlib.sha256(self._expected(frame_id)[0].tobytes()).hexdigest()

    def ack(self,data):
        ack=parse_feedback(data)
        if ack['epoch']!=self.epoch:raise ValueError('AF02 wrong session')
        frame=ack['frame_id'];row=self.pending.get(frame)
        if row is None:return False
        if ack['body_crc']!=row['body_crc']:raise ValueError('AF02 wrong outer content')
        stored=row['destination_bank']!=NO_BANK and ack['status']==ACK
        expected=(row['destination_bank'],frame,row['stored_tag']) if stored else (NO_BANK,gm.NO_REF,ZERO)
        if (ack['stored_bank'],ack['stored_id'],ack['stored_tag'])!=expected:raise ValueError('AF02 wrong publication')
        if ack['status']==NACK:return self.expire(frame)
        if stored:
            if not self._writable(row['destination_bank']):raise ValueError('AR02 read-owned ACK destination')
            if row['key']:self.banks={0:None,1:None}
            self.banks[row['destination_bank']]=Bank(frame,row['stored_tag'],row['planes'])
        self.pending.pop(frame);self._generation+=1;self._observe();return True


@dataclass(frozen=True,eq=False)
class Decode:
    owner:object
    meta:dict
    planes:tuple
    rgb:np.ndarray
    lease:Lease|None
    info:dict


class Receiver(old.Receiver):
    def __init__(self,epoch=1,frame_cap=49152,max_readers=3):
        if type(frame_cap) is not int or not HEADER.size+gm.HEADER.size+8<=frame_cap<=49152:
            raise ValueError('AR02 receive cap')
        super().__init__(epoch,frame_cap,max_readers)

    def begin(self,packet):
        if self.active is not None:raise ValueError('AR02 serialized decoder already active')
        meta=identity(packet,self.epoch,self.frame_cap,decode=True);p=meta['parsed']
        frame,w,h=meta['frame_id'],p['width'],p['height'];dest=meta['destination_bank']
        if frame<=self.last_frame_id:raise ValueError('AR02 replay')
        if meta['key']:
            if self._leases:raise ValueError('AR02 key read-owned')
        elif dest!=NO_BANK and not self._writable(dest):raise ValueError('AR02 destination read-owned')
        lease=None
        try:
            if meta['key']:prediction=tuple(np.full(s,128,np.int16) for s in ((h,w),(h//2,w//2),(h//2,w//2)))
            else:
                bank=self.banks[meta['reference_bank']]
                if bank is None or (bank.frame_id,bank.tag)!=(meta['reference_id'],meta['reference_tag']) or bank.planes[0].shape!=(h,w):
                    raise ValueError('AR02 missing exact reference')
                lease=self._acquire(meta['reference_bank']);prediction=tuple(gm.mt.predict(bank.planes,0,0))
                self.reference_read_bytes+=pixels(bank.planes);self.reference_read_array_bytes+=sum(x.nbytes for x in bank.planes)
            planes=fast_codec.reconstruct(p['coefficients'],prediction,p['scale_map'],w,h)
            self.reconstruction_write_bytes+=pixels(planes);self.reconstruction_write_array_bytes+=sum(x.nbytes for x in planes)
            if dest!=NO_BANK:
                self.tag_read_bytes+=4+2*pixels(planes)
                if reference_tag(planes)!=meta['stored_tag']:raise ValueError('AR02 reconstructed publication tag')
            base=gm.ft.planes_to_rgb(planes);base_hash=hashlib.sha256(base.tobytes()).hexdigest()
            rgb=_ui().apply_patches(base,meta['patches']) if meta['patches'] else base
            rgb.setflags(write=False)
            patches=[{k:v for k,v in x.items() if k!='words'} for x in meta['patches']]
            info=dict(frame_id=frame,key=meta['key'],promoted=meta['promoted'],reference_bank=meta['reference_bank'],
                reference_id=None if meta['key'] else meta['reference_id'],destination_bank=dest,
                reference_read_bytes=0 if lease is None else pixels(lease.bank.planes),reconstruction_write_bytes=pixels(planes),
                reference_read_array_bytes=0 if lease is None else sum(x.nbytes for x in lease.bank.planes),
                reconstruction_write_array_bytes=sum(x.nbytes for x in planes),tag_read_bytes=0 if dest==NO_BANK else 4+2*pixels(planes),
                packet_bytes=len(packet),inner_codec=meta['inner_codec'],level=meta['level'],base_rgb_sha256=base_hash,
                patches=patches,selected_pixels=sum(x['rect'][2]*x['rect'][3] for x in patches))
            published=MappingProxyType({k:v for k,v in meta.items() if k not in ('inner','parsed','patches','patch_packets')})
            task=Decode(self._owner,published,planes,rgb,lease,MappingProxyType(info));self.active=task;return task
        except BaseException:
            if lease is not None:self.release(lease)
            raise

    def complete(self,task):
        if not isinstance(task,Decode) or task.owner is not self._owner or task is not self.active:raise ValueError('AR02 stale decode completion')
        meta=task.meta
        if task.lease is not None:self.release(task.lease)
        if meta['key']:self.banks={0:None,1:None}
        dest=meta['destination_bank']
        if dest!=NO_BANK:self.banks[dest]=Bank(meta['frame_id'],meta['stored_tag'],task.planes)
        self.last_frame_id=meta['frame_id'];self.active=None;self._observe()
        info=dict(task.info,retained_banks=sum(x is not None for x in self.banks.values()),retained_reference_array_bytes=self.retained_bytes())
        return task.rgb,info,feedback(meta)

    def receive(self,packet):return self.complete(self.begin(packet))
