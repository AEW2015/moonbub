"""Fixed coefficient-sampling gate for exact SR work in unchanged AR02.

The source/predictor/GM candidate is computed once. A sampled zero/DC fraction
can enable actual SR serialization; skipped SR bytes/quality are unknown.
"""
from dataclasses import dataclass
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-game-unified-codec-study'))
import unified_codec as frozen
from unified_codec import *
_ui=frozen._ui
_sr_candidate=frozen._sr_candidate


@dataclass(frozen=True)
class GateConfig:
    threshold:float=0.90
    sample_blocks_per_plane:int=64
    def __post_init__(self):
        if not np.isfinite(self.threshold) or not 0<=self.threshold<=1:
            raise ValueError('finite bounded sparse threshold')
        if type(self.sample_blocks_per_plane) is not int or not 1<=self.sample_blocks_per_plane<=64:
            raise ValueError('at most64 samples per plane')


def no_screen(mode):
    return dict(evaluated=False,allow_sr=mode=='exact',reason='baseline_'+mode,service_ms=0.,
                total_sampled_blocks=0,planes=[])


def screen(coefficients,config=GateConfig()):
    started=time.perf_counter_ns()
    if len(coefficients)!=3:raise ValueError('three coefficient planes')
    planes=[]
    for i,c in enumerate(coefficients):
        if c.dtype!=np.int16 or c.ndim!=3 or c.shape[1:]!=(8,8) or len(c)<1:
            raise ValueError('bounded quantized8x8plane')
        n=len(c);count=min(n,config.sample_blocks_per_plane)
        indices=np.linspace(0,n-1,count,dtype=np.int64)
        samples=c[indices].reshape(count,64)
        sparse=~np.any(samples[:,1:]!=0,axis=1)
        planes.append(dict(plane=i,blocks=n,sample_indices=indices.tolist(),sampled_blocks=count,
                           zero_or_dc_blocks=int(sparse.sum()),zero_or_dc_fraction=float(sparse.mean())))
    allowed=all(p['zero_or_dc_fraction']>=config.threshold for p in planes)
    return dict(evaluated=True,allow_sr=allowed,reason='sample_sparse' if allowed else 'sample_not_sparse',
                threshold=config.threshold,sample_blocks_per_plane=config.sample_blocks_per_plane,
                total_sampled_blocks=sum(p['sampled_blocks'] for p in planes),planes=planes,
                service_ms=(time.perf_counter_ns()-started)/1e6,
                scope='Current quantizedGMcoefficient samples only; uncodedSRrate/quality unknown')


class Encoder(frozen.Encoder):
    def __init__(self,epoch=1,window=3,frame_cap=49152,*,mode='gated',patch_builder=None,gate_config=GateConfig()):
        if mode not in ('gm','exact','gated'):raise ValueError('exact GM/exact/gated profiles only')
        if not isinstance(gate_config,GateConfig):raise ValueError('immutable gate configuration')
        super().__init__(epoch,window,frame_cap,mode='exact' if mode=='gated' else mode,patch_builder=patch_builder)
        self.mode=mode;self.gate_config=gate_config

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
        gate=screen(gm_candidate.coefficients,self.gate_config) if self.mode=='gated' else no_screen(self.mode)
        if self.mode!='gm' and (self.mode!='gated' or gate['allow_sr']):
            limit=0
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
            analyze_ms=analyze_ms,candidate_ms=gm_ms+sr_ms+gate['service_ms'],gate=gate,gate_ms=gate['service_ms'],reconstruction_ms=reconstruction_ms,reference_tag_ms=tag_ms,
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

