"""V23 bounded immutable-source analysis reuse for AR03 candidate retries.

The build body is a local adaptation of frozen candidate_codec.Encoder.build.
Only prediction/forward analysis is reused; every actual map, entropy candidate,
reconstruction, publication tag and outer packet remains paid and byte-identical.
No global module or function is patched. This is a host Python experiment.
"""
from pathlib import Path
import copy
import hashlib
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'python-game-candidate-commit-study'))
import candidate_codec as C

gm, sr, fast_codec, corpus = C.gm, C.sr, C.fast_codec, C.corpus
NO_BANK, ZERO, KEY, PROMOTE = C.NO_BANK, C.ZERO, C.KEY, C.PROMOTE
HEADER, MAX_PATCHES = C.HEADER, C.MAX_PATCHES
Candidate, reference_tag, pixels, seal, body_crc = C.Candidate, C.reference_tag, C.pixels, C.seal, C.body_crc
_freeze, _ui, _sr_candidate, ms = C._freeze, C._ui, C._sr_candidate, C.ms


def _hash_source(a):
    # A bounded transient canonical byte copy is paid on every guard. No source
    # pixel snapshot is retained in addition to the caller's borrowed ndarray.
    return hashlib.sha256(a.tobytes(order='C')).digest()


def _semantics(encoder):
    return (encoder.epoch, encoder.frame_cap, encoder.window, encoder.mode,
            id(encoder.patch_builder), encoder.last_issued, encoder._generation,
            encoder._geometry,
            tuple((slot, None if bank is None else (id(bank), bank.frame_id, bank.tag))
                  for slot, bank in sorted(encoder.banks.items())),
            tuple((fid, id(row)) for fid, row in sorted(encoder.pending.items())))


class SharedEncoder(C.Encoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shared_context = None
        self.last_shared_info = None

    @property
    def last_source_info(self):
        return self.last_shared_info

    def can_prepare(self, force_key=False, promote=False):
        ctx = getattr(self, '_shared_context', None)
        if ctx is None or ctx['lease'] is None:
            return super().can_prepare(force_key, promote)
        # The context's read hold is our own preparation, not an independent
        # reader preventing a source==promotion-destination operation. Build
        # and commit still enforce all external readers and candidate ownership.
        probe = copy.copy(self)
        probe._leases = self._leases - {ctx['lease']}
        return C.Encoder.can_prepare(probe, force_key, promote)

    def begin_source(self, rgb, frame_id, *, force_key=False, promote=False, reference_bank=None):
        started = time.perf_counter_ns()
        if self._shared_context is not None or self.active_candidate is not None or self._building:
            raise ValueError('unresolved shared analysis/candidate')
        a = gm.ft._check_rgb(rgb)
        h, w = a.shape[:2]
        if type(force_key) is not bool or type(promote) is not bool:
            raise ValueError('AR03 booleans')
        if (self._geometry is not None and self._geometry != (h, w)) or any(
                b is not None and b.planes[0].shape != (h, w) for b in self.banks.values()):
            raise ValueError('shared fixed geometry')
        key = bool(force_key or not any(b is not None for b in self.banks.values()))
        promoted = bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued < frame_id < gm.NO_REF or not self.can_prepare(key, promoted):
            raise ValueError('shared credit/identity/bank drain')
        if reference_bank is not None and (type(reference_bank) is not int or reference_bank not in (0, 1)):
            raise ValueError('shared explicit reference')
        if key and reference_bank is not None:
            raise ValueError('shared key source')
        slot = NO_BANK if key else reference_bank if reference_bank is not None else max(
            (s for s, bank in self.banks.items() if bank is not None), key=lambda s: self.banks[s].frame_id)
        ref = None if key else self.banks[slot]
        if not key and (ref is None or ref.planes[0].shape != (h, w)):
            raise ValueError('shared unconfirmed reference')
        if ref is not None and len(self._leases) + 2 > self.max_readers:
            raise ValueError('shared context and candidate require two reader descriptors')
        lease = None
        try:
            if ref is not None:
                lease = self.acquire(slot)
            hash_started = time.perf_counter_ns()
            source_hash = _hash_source(a)
            hash_ms = ms(hash_started)
            local = gm.Encoder(self.epoch, self.window)
            if ref is not None:
                local.anchor_id, local._anchor = ref.frame_id, ref.planes
            analysis_started = time.perf_counter_ns()
            prepared = local.analyze(a, frame_id, force_key=key, mode='zero')
            analysis_ms = ms(analysis_started)
            self.analysis_count += 1
            self.forward_calls += 3
            reference_bytes = 0 if ref is None else pixels(ref.planes)
            reference_array_bytes = 0 if ref is None else sum(p.nbytes for p in ref.planes)
            self.reference_read_bytes += reference_bytes
            self.reference_read_array_bytes += reference_array_bytes
            pred_bytes = sum(p.nbytes for p in prepared.prediction)
            transform_bytes = sum(p.nbytes for p in prepared.raw_coefficients)
            info = dict(frame_id=frame_id, actual_analyze_calls=1, actual_forward_calls=3,
                        cached_attempts=0, eliminated_analysis_calls=0,
                        source_prepare_ms=ms(started), forward_analysis_ms=analysis_ms,
                        source_guard_calls=1, source_guard_bytes=int(a.nbytes),
                        source_guard_ms=hash_ms, borrowed_source_array_bytes=int(a.nbytes),
                        retained_source_copy_bytes=0, retained_prediction_array_bytes=pred_bytes,
                        retained_transform_array_bytes=transform_bytes,
                        retained_analysis_array_bytes=pred_bytes + transform_bytes,
                        source_reference_read_bytes=reference_bytes,
                        source_reference_array_read_bytes=reference_array_bytes,
                        additional_context_reader_descriptors=int(ref is not None),
                        dedicated_context_lease=lease is not None, context_lease_released=False,
                        scope='named retained host arrays only; not peak heap, ESP32 SRAM, bus traffic or target timing')
            self._shared_context = dict(source=a, source_hash=source_hash, frame=frame_id,
                                        key=key, promoted=promoted, slot=slot, reference=ref,
                                        semantics=_semantics(self), local=local, prepared=prepared,
                                        lease=lease, info=info)
            self.last_shared_info = info
            return dict(info)
        except BaseException:
            if lease is not None and lease in self._leases:
                self.release(lease)
            raise

    def _reuse_analysis(self, a, frame_id, key, promoted, slot, ref):
        ctx = self._shared_context
        if ctx is None or _semantics(self) != ctx['semantics']:
            raise ValueError('stale shared source state/configuration')
        if (a is not ctx['source'] or frame_id != ctx['frame'] or key != ctx['key']
                or promoted != ctx['promoted'] or slot != ctx['slot'] or ref is not ctx['reference']):
            raise ValueError('different shared source/frame/reference')
        if ctx['lease'] is not None and ctx['lease'] not in self._leases:
            raise ValueError('lost shared source ownership')
        started = time.perf_counter_ns()
        current_hash = _hash_source(a)
        elapsed = ms(started)
        info = ctx['info']
        info['source_guard_calls'] += 1
        info['source_guard_bytes'] += int(a.nbytes)
        info['source_guard_ms'] += elapsed
        if current_hash != ctx['source_hash']:
            raise ValueError('shared source input mutated')
        info['cached_attempts'] += 1
        info['eliminated_analysis_calls'] = max(0, info['cached_attempts'] - 1)
        return ctx['local'], ctx['prepared']

    def end_source(self):
        ctx = self._shared_context
        if ctx is None:
            raise ValueError('no shared source context')
        lease = ctx['lease']
        if lease is not None and lease in self._leases:
            self.release(lease)
        ctx['info']['context_lease_released'] = lease is not None
        self.last_shared_info = dict(ctx['info'])
        self._shared_context = None
        return dict(self.last_shared_info)

    def commit(self, candidate):
        if self._shared_context is not None:
            raise ValueError('end shared source before candidate commit')
        return super().commit(candidate)

    def build(self,rgb,frame_id,*,scale_map=None,quant_scale=16,force_key=False,promote=False,reference_bank=None):
        if self._shared_context is None:
            return super().build(rgb,frame_id,scale_map=scale_map,quant_scale=quant_scale,
                                 force_key=force_key,promote=promote,reference_bank=reference_bank)
        started=time.perf_counter_ns();a=gm.ft._check_rgb(rgb);h,w=a.shape[:2]
        if type(force_key) is not bool or type(promote) is not bool:raise ValueError('AR03 booleans')
        if (self._geometry is not None and self._geometry!=(h,w)) or any(b is not None and b.planes[0].shape!=(h,w) for b in self.banks.values()):
            raise ValueError('AR03 fixed geometry; use a fresh epoch for size changes')
        key=bool(force_key or not any(b is not None for b in self.banks.values()));promoted=bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued<frame_id<gm.NO_REF or not self.can_prepare(key,promoted):
            raise ValueError('AR03 credit/identity/bank drain')
        if reference_bank is not None and (type(reference_bank) is not int or reference_bank not in (0,1)):
            raise ValueError('AR03 explicit reference')
        if key and reference_bank is not None:raise ValueError('AR03 key source')
        refslot=NO_BANK if key else reference_bank if reference_bank is not None else max(
            (slot for slot,bank in self.banks.items() if bank is not None),key=lambda slot:self.banks[slot].frame_id)
        ref=None if key else self.banks[refslot]
        if not key and (ref is None or ref.planes[0].shape!=(h,w)):raise ValueError('AR03 unconfirmed reference')
        lease=None
        self._building=True
        try:
            if ref is not None:lease=self.acquire(refslot)
            lookup_started=time.perf_counter_ns()
            local,p=self._reuse_analysis(a,frame_id,key,promoted,refslot,ref)
            shared_lookup_ms=ms(lookup_started);analyze_ms=0.
            if scale_map is None:
                if type(quant_scale) is not int or quant_scale not in gm.roi.SCALES:raise ValueError('AR03 quant scale')
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
                if len(patches)>MAX_PATCHES:raise ValueError('AR03 patch callback count')
            began=time.perf_counter_ns()
            if patches:
                decoded=_ui().validate_patches(patches,w,h)
                for patch in decoded:
                    x,y,rw,rh=patch['rect']
                    if not np.array_equal(corpus.rgb565(a[y:y+rh,x:x+rw]),patch['words']):
                        raise ValueError('AR03 UI callback changed original RGB565 words')
                    selected.append({k:v for k,v in patch.items() if k!='words'})
            ui_validation_ms=ms(began)
            blob=b''.join(struct.pack('<I',len(data))+data for data in patches)
            dest=0 if key else 1 if promoted else NO_BANK
            body=HEADER.pack(b'AR03',3,KEY if key else PROMOTE if promoted else 0,self.epoch,frame_id,refslot,dest,
                gm.NO_REF if ref is None else ref.frame_id,ZERO if ref is None else ref.tag,tag,len(inner),len(patches),len(blob))+inner+blob
            packet=seal(body);fit=len(packet)<=self.frame_cap
            info=dict(candidate_source_lease_held=lease is not None,reference_choice_explicit=reference_bank is not None,pending_before=len(self.pending),
                pending_writers_before=sum(r['key'] or r['promoted'] for r in self.pending.values()),
                bank0_readers_before=sum(l.slot==0 for l in self._leases),bank1_readers_before=sum(l.slot==1 for l in self._leases),
                pending_bank0_consumers=sum(r['reference_bank']==0 for r in self.pending.values()),
                pending_bank1_consumers=sum(r['reference_bank']==1 for r in self.pending.values()),
                bytes=len(packet),inner_bytes=len(inner),envelope_bytes=HEADER.size+4,inner_codec=codec,level=level,
                analyze_ms=analyze_ms,candidate_ms=gm_ms+sr_ms,reconstruction_ms=reconstruction_ms,reference_tag_ms=tag_ms,
                analyze_calls=0,forward_calls=0,shared_analysis_reused=True,shared_lookup_ms=shared_lookup_ms,inner_attempts=attempts,pruning=pruning,sr_planes=sr_details,
                cap_fit=fit,promotion_reconstruction_paid=bool(key or promoted),
                reference_read_bytes=0,
                reconstruction_write_bytes=0 if planes is None else pixels(planes),
                reference_read_array_bytes=0,
                reconstruction_write_array_bytes=0 if planes is None else sum(x.nbytes for x in planes),
                tag_read_bytes=0 if planes is None else 4+2*pixels(planes),
                retained_banks_before=sum(b is not None for b in self.banks.values()),reference_array_bytes_before=self.retained_bytes(),
                ui_service_ms=ui_ms,ui_validation_ms=ui_validation_ms,patch_count=len(patches),patch_bytes=len(blob),
                selected=selected,selected_pixels=sum(x['rect'][2]*x['rect'][3] for x in selected),ui=patch_info,
                minimum_complete_inner_bytes=min(x['bytes'] for x in attempts))
            for name in ('reference_read_bytes','reconstruction_write_bytes','reference_read_array_bytes','reconstruction_write_array_bytes','tag_read_bytes'):
                setattr(self,name,getattr(self,name)+info[name])
            if not fit and lease is not None:
                self.release(lease);lease=None
            frozen_info=_freeze(info)
            candidate=Candidate(self._owner,packet if fit else None,frame_id,key,promoted,refslot,
                None if ref is None else ref.frame_id,ZERO if ref is None else ref.tag,dest,ms(started),frozen_info,lease)
            row=None if not fit else dict(key=key,promoted=promoted,packet=packet,planes=planes,
                reference_bank=refslot,reference_id=None if ref is None else ref.frame_id,reference_tag=ZERO if ref is None else ref.tag,
                reference=None if key or promoted else ref,destination_bank=dest,stored_tag=tag,body_crc=body_crc(packet))
            self._candidate=candidate
            self._candidate_record=dict(candidate=candidate,packet=packet if fit else None,row=row,geometry=(h,w),
                source=ref,lease=lease,epoch=self.epoch,cap=self.frame_cap,info=frozen_info,
                identity=(frame_id,key,promoted,refslot,None if ref is None else ref.frame_id,ZERO if ref is None else ref.tag,dest),
                field_types=(int,bool,bool,int,type(None) if ref is None else int,bytes,int),service_ms=candidate.service_ms,config=(self.epoch,self.frame_cap,self.window,self.mode))
            self.build_count+=1;self.last_info=info
            return candidate

        except BaseException:
            if lease is not None and lease in self._leases:self.release(lease)
            raise
        finally:
            self._building=False
