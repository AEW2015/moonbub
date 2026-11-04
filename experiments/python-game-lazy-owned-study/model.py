"""Owned immutable capture snapshots and lazily produced retry analysis.

The source copy and ownership checks are actual host Python work. This is a
synchronous API contract, not a native concurrent capture fence or ESP32 cache.
"""
from dataclasses import dataclass, field
from pathlib import Path
import importlib.util
import struct
import sys
import time
import numpy as np

HERE = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


m = load('owned24_joint23', HERE.parent / 'python-game-hd22-joint-study/model.py')
shared = load('owned24_shared23', HERE.parent / 'python-game-shared-analysis-study/model.py')
C = m.C
gm, sr, fast_codec, corpus = C.gm, C.sr, C.fast_codec, C.corpus
NO_BANK, ZERO, KEY, PROMOTE = C.NO_BANK, C.ZERO, C.KEY, C.PROMOTE
HEADER, MAX_PATCHES = C.HEADER, C.MAX_PATCHES
Candidate, reference_tag, pixels, seal, body_crc = C.Candidate, C.reference_tag, C.pixels, C.seal, C.body_crc
_freeze, _ui, _sr_candidate, ms = C._freeze, C._ui, C._sr_candidate, C.ms
LIMIT = 0xffffffff


@dataclass(frozen=True, eq=False)
class CaptureLease:
    owner: object = field(repr=False)
    epoch: int
    slot: int
    generation: int
    token: int
    array: np.ndarray = field(repr=False)


class CapturePool:
    """Two bounded snapshot slots; their arrays are backed by immutable bytes."""
    def __init__(self, *, epoch=1, slots=2, max_readers=8):
        if type(epoch) is not int or not 1 <= epoch < LIMIT or slots != 2:
            raise ValueError('bounded capture epoch and exactly two slots')
        if type(max_readers) is not int or not 1 <= max_readers <= 8:
            raise ValueError('one to eight capture descriptors')
        self.epoch, self.max_readers = epoch, max_readers
        self._owner = object()
        self._slots = [None, None]
        self._generations = [0, 0]
        self._leases = {}
        self._next_token = 0
        self.copied_bytes = self.copies = self.peak_pixel_bytes = self.peak_slots = 0

    @property
    def active_readers(self): return len(self._leases)

    @property
    def pixel_bytes(self): return sum(0 if row is None else len(row['bytes']) for row in self._slots)

    def _can_issue(self):
        if len(self._leases) >= self.max_readers or self._next_token >= LIMIT:
            raise ValueError('capture descriptor/token exhausted')

    def _issue(self, slot):
        self._can_issue()
        self._next_token += 1
        row = self._slots[slot]
        lease = CaptureLease(self._owner, self.epoch, slot, row['generation'], self._next_token, row['array'])
        self._leases[lease.token] = lease
        return lease

    def capture(self, rgb, *, slot=None):
        a = gm.ft._check_rgb(rgb)
        self._can_issue()
        if slot is None:
            slot = next((i for i, row in enumerate(self._slots) if row is None), None)
        if type(slot) is not int or slot not in (0, 1) or self._slots[slot] is not None:
            raise ValueError('capture slot busy or absent')
        if self._generations[slot] >= LIMIT:
            raise ValueError('capture generation exhausted; drain and reset')
        # One actual snapshot copy. The resulting ndarray cannot enable writes,
        # even through its base ndarray, because the ultimate owner is bytes.
        payload = a.tobytes(order='C')
        view = np.frombuffer(payload, dtype=np.uint8).reshape(a.shape)
        generation = self._generations[slot] + 1
        self._slots[slot] = dict(bytes=payload, array=view, generation=generation)
        self._generations[slot] = generation
        self.copied_bytes += len(payload)
        self.copies += 1
        self.peak_pixel_bytes = max(self.peak_pixel_bytes, self.pixel_bytes)
        self.peak_slots = max(self.peak_slots, sum(row is not None for row in self._slots))
        return self._issue(slot)

    def validate(self, lease, array=None):
        if not isinstance(lease, CaptureLease) or lease.owner is not self._owner or self._leases.get(lease.token) is not lease:
            raise ValueError('foreign/stale capture descriptor')
        row = self._slots[lease.slot]
        if (lease.epoch != self.epoch or row is None or row['generation'] != lease.generation
                or row['array'] is not lease.array or (array is not None and array is not lease.array)):
            raise ValueError('capture generation/view changed')
        if lease.array.flags.writeable:
            raise ValueError('capture snapshot must remain immutable')
        return lease.array

    def acquire(self, lease):
        self.validate(lease)
        return self._issue(lease.slot)

    def release(self, lease):
        self.validate(lease)
        self._leases.pop(lease.token)
        if not any(other.slot == lease.slot for other in self._leases.values()):
            self._slots[lease.slot] = None

    def replace(self, slot, rgb):
        """Writer API refuses a leased slot; an empty slot gets a fresh generation."""
        return self.capture(rgb, slot=slot)

    def reset(self, epoch):
        if type(epoch) is not int or not self.epoch < epoch < LIMIT or self._leases:
            raise ValueError('capture reset needs later epoch and drained readers')
        self.__init__(epoch=epoch, max_readers=self.max_readers)


class LazyEncoder(shared.SharedEncoder):
    """A cheap owned-source context; first build produces the actual analysis."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture_binding = None

    def bind_capture(self, pool, lease):
        if self._capture_binding is not None or self._shared_context is not None:
            raise ValueError('capture already bound')
        pool.validate(lease)
        self._capture_binding = (pool, lease)

    def unbind_capture(self):
        if self._shared_context is not None:
            raise ValueError('end analysis before capture unbind')
        self._capture_binding = None

    def begin_source(self, rgb, frame_id, *, force_key=False, promote=False, reference_bank=None):
        started = time.perf_counter_ns()
        if self._capture_binding is None:
            raise ValueError('lazy analysis requires an owned capture')
        if self._shared_context is not None or self.active_candidate is not None or self._building:
            raise ValueError('unresolved owned context/candidate')
        pool, capture = self._capture_binding
        a = gm.ft._check_rgb(rgb)
        pool.validate(capture, a)
        h, w = a.shape[:2]
        if type(force_key) is not bool or type(promote) is not bool:
            raise ValueError('AR03 booleans')
        if (self._geometry is not None and self._geometry != (h, w)) or any(
                bank is not None and bank.planes[0].shape != (h, w) for bank in self.banks.values()):
            raise ValueError('owned fixed geometry')
        key = bool(force_key or not any(bank is not None for bank in self.banks.values()))
        promoted = bool(promote and not key)
        if type(frame_id) is not int or not self.last_issued < frame_id < gm.NO_REF or not self.can_prepare(key, promoted):
            raise ValueError('owned credit/identity/bank drain')
        if reference_bank is not None and (type(reference_bank) is not int or reference_bank not in (0, 1)):
            raise ValueError('owned explicit reference')
        if key and reference_bank is not None:
            raise ValueError('owned key source')
        slot = NO_BANK if key else reference_bank if reference_bank is not None else max(
            (s for s, bank in self.banks.items() if bank is not None), key=lambda s: self.banks[s].frame_id)
        ref = None if key else self.banks[slot]
        if not key and (ref is None or ref.planes[0].shape != (h, w)):
            raise ValueError('owned missing reference')
        if ref is not None and len(self._leases) + 2 > self.max_readers:
            raise ValueError('owned context and candidate need two reader descriptors')
        hold = None if ref is None else self.acquire(slot)
        info = dict(frame_id=frame_id, actual_analyze_calls=0, actual_forward_calls=0,
                    cached_attempts=0, eliminated_analysis_calls=0,
                    context_open_ms=ms(started), source_prepare_ms=ms(started), forward_analysis_ms=0.,
                    source_guard_calls=0, source_guard_bytes=0, source_guard_ms=0.,
                    ownership_check_calls=1, borrowed_source_array_bytes=0,
                    owned_capture_array_bytes=int(a.nbytes), retained_source_copy_bytes=int(a.nbytes),
                    retained_prediction_array_bytes=0, retained_transform_array_bytes=0,
                    retained_analysis_array_bytes=0, source_reference_read_bytes=0,
                    source_reference_array_read_bytes=0, additional_context_reader_descriptors=int(ref is not None),
                    dedicated_context_lease=hold is not None, context_lease_released=False,
                    analysis_allocated_lazily=True,
                    scope='owned host snapshot and named arrays; not native concurrent capture or ESP32 storage')
        self._shared_context = dict(source=a, frame=frame_id, key=key, promoted=promoted, slot=slot,
                                    reference=ref, semantics=shared._semantics(self), lease=hold,
                                    local=None, prepared=None, capture= capture, pool=pool, info=info)
        self.last_shared_info = info
        return dict(info)

    def _reuse_analysis(self, a, frame_id, key, promoted, slot, ref):
        ctx = self._shared_context
        if ctx is None or shared._semantics(self) != ctx['semantics']:
            raise ValueError('stale owned source/configuration')
        if (a is not ctx['source'] or frame_id != ctx['frame'] or key != ctx['key']
                or promoted != ctx['promoted'] or slot != ctx['slot'] or ref is not ctx['reference']):
            raise ValueError('different owned source/frame/reference')
        if ctx['lease'] is not None and ctx['lease'] not in self._leases:
            raise ValueError('lost owned source hold')
        ctx['pool'].validate(ctx['capture'], a)
        info = ctx['info']
        info['ownership_check_calls'] += 1
        if ctx['prepared'] is None:
            local = gm.Encoder(self.epoch, self.window)
            if ref is not None:
                local.anchor_id, local._anchor = ref.frame_id, ref.planes
            started = time.perf_counter_ns()
            prepared = local.analyze(a, frame_id, force_key=key, mode='zero')
            elapsed = ms(started)
            self.analysis_count += 1
            self.forward_calls += 3
            ctx['local'], ctx['prepared'] = local, prepared
            reference_bytes = 0 if ref is None else pixels(ref.planes)
            reference_arrays = 0 if ref is None else sum(p.nbytes for p in ref.planes)
            self.reference_read_bytes += reference_bytes
            self.reference_read_array_bytes += reference_arrays
            prediction_bytes = sum(p.nbytes for p in prepared.prediction)
            transform_bytes = sum(p.nbytes for p in prepared.raw_coefficients)
            info.update(actual_analyze_calls=1, actual_forward_calls=3, forward_analysis_ms=elapsed,
                        source_prepare_ms=info['context_open_ms'] + elapsed,
                        retained_prediction_array_bytes=prediction_bytes,
                        retained_transform_array_bytes=transform_bytes,
                        retained_analysis_array_bytes=prediction_bytes + transform_bytes,
                        source_reference_read_bytes=reference_bytes,
                        source_reference_array_read_bytes=reference_arrays)
        info['cached_attempts'] += 1
        info['eliminated_analysis_calls'] = max(0, info['cached_attempts'] - 1)
        return ctx['local'], ctx['prepared']


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
            analyze_before=self.analysis_count
            lookup_started=time.perf_counter_ns()
            local,p=self._reuse_analysis(a,frame_id,key,promoted,refslot,ref)
            shared_lookup_ms=ms(lookup_started)
            actual_analysis_calls=self.analysis_count-analyze_before
            analyze_ms=self._shared_context['info']['forward_analysis_ms'] if actual_analysis_calls else 0.
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
                analyze_calls=actual_analysis_calls,forward_calls=3*actual_analysis_calls,shared_analysis_reused=not bool(actual_analysis_calls),shared_lookup_ms=shared_lookup_ms,inner_attempts=attempts,pruning=pruning,sr_planes=sr_details,
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


class OwnedJointSender(m.JointSender):
    def __init__(self, epoch=1, frame_cap=m.FRAME_CAP, profiles=m.PROFILES,
                 base_encoder_class=None, *, capture_pool=None):
        if base_encoder_class not in (None, LazyEncoder):
            raise ValueError('owned sender uses LazyEncoder')
        super().__init__(epoch, frame_cap, profiles, base_encoder_class=LazyEncoder)
        self.capture_pool = CapturePool() if capture_pool is None else capture_pool

    def build(self, rgb, frame_id, **kwargs):
        started = time.perf_counter_ns()
        # The private snapshot is taken BEFORE both HUD preparation and base
        # analysis. The parent only sees the same immutable capture view.
        now = m._time(kwargs.get('now_ms', 0), 'build time')
        deadline = kwargs.get('deadline_ms')
        if deadline is not None:
            deadline = m._time(deadline, 'deadline')
        if deadline is not None and now >= deadline:
            result = super().build(rgb, frame_id, **kwargs)
            result.info['capture'] = dict(copied_bytes=0, snapshot_copy_ms=0., released=True,
                                          active_readers_after=self.capture_pool.active_readers)
            return result
        a = C.gm.ft._check_rgb(rgb)
        if a.shape != (480, 720, 3):
            raise ValueError('owned joint fixed canvas')
        capture_started = time.perf_counter_ns()
        lease = self.capture_pool.capture(a)
        copy_ms = ms(capture_started)
        result = None
        encoder = self.base
        try:
            encoder.bind_capture(self.capture_pool, lease)
            call_kwargs = dict(kwargs)
            call_kwargs['now_ms'] = now + ms(started)
            result = super().build(lease.array, frame_id, **call_kwargs)
            result.info['joint_inner_service_ms'] = result.info['paid_service_ms']
            return result
        finally:
            try:
                if encoder._shared_context is not None:
                    encoder.end_source()
                encoder.unbind_capture()
            finally:
                self.capture_pool.release(lease)
            if result is not None:
                result.info['capture'] = dict(epoch=lease.epoch, slot=lease.slot, generation=lease.generation,
                                              token=lease.token, copied_bytes=int(a.nbytes), snapshot_copy_ms=copy_ms,
                                              peak_pool_pixel_bytes=self.capture_pool.peak_pixel_bytes,
                                              peak_pool_slots=self.capture_pool.peak_slots, released=True,
                                              active_readers_after=self.capture_pool.active_readers,
                                              retained_pool_pixel_bytes_after=self.capture_pool.pixel_bytes)
                result.info['paid_service_ms'] = ms(started)

    def reset(self, epoch):
        m.hc.check_id(epoch, epoch=True)
        if (epoch <= self.epoch or self._active is not None or self._pending is not None
                or self.base.readers or self.capture_pool.active_readers):
            raise ValueError('owned reset needs drained codec/capture owners')
        pool = self.capture_pool
        pool.reset(pool.epoch + 1)
        self.__init__(epoch, self.frame_cap, self.profiles, capture_pool=pool)
