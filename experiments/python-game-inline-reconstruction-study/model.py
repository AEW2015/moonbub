"""Inline compact reconstruction tagging; exact pixels, conditional service only."""
from dataclasses import asdict, dataclass, replace
import hashlib,hmac,importlib.util,math,struct,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);out=importlib.util.module_from_spec(spec);sys.modules[name]=out;spec.loader.exec_module(out);return out
v19=module('v20_frozen_stripe_model',HERE.parent/'python-game-causal-stripe-study/model.py')
trace=v19.trace;fixture=v19.fixture
STREAM=struct.Struct('<4sBHHII')
TILE=struct.Struct('<BHHBB')

class StripeTagger:
    """One compact raster stripe and one canonical int16 row; no source-plane read.

    Successful finish exposes a private tag. Only an explicitly eligible complete
    packet may expose publication_tag. Hashlib/Python metadata storage is excluded
    from the measured ndarray bound; hardware state is a separate planning input.
    """
    def __init__(self,width,height):
        if type(width)is not int or type(height)is not int or min(width,height)<2 or max(width,height)>4096 or width%2 or height%2:raise ValueError('bounded even geometry')
        self.width,self.height=width,height;self.shapes=((height,width),(height//2,width//2),(height//2,width//2))
        self.stripe=np.empty((min(8,height),width),np.uint8);self.row=np.empty(width,dtype='<i2')
        self.local_array_bytes=self.stripe.nbytes+self.row.nbytes
        self.sha=hashlib.sha256(struct.pack('<HH',width,height));self.canonical_bytes=4
        self.plane=self.y=self.x=0;self.tiles=self.stripes=self.rows=0;self.failed=False;self.sealed=False;self._tag=self._publication=None
    def fail(self,message):
        self.failed=True;self._tag=self._publication=None;self.sha=None;raise ValueError(message)
    def abort(self):
        self.failed=True;self._tag=self._publication=None;self.sha=None
    @property
    def tag(self):
        if self._tag is None:raise ValueError('private tag unavailable')
        return self._tag
    @property
    def publication_tag(self):
        if self._publication is None:raise ValueError('publication unavailable')
        return self._publication
    def push(self,plane,y,x,tile):
        if self.failed or self.sealed:self.fail('inactive tile stream')
        if any(type(n)is not int for n in (plane,y,x)) or (plane,y,x)!=(self.plane,self.y,self.x) or plane>=3:self.fail('tile order/identity')
        ph,pw=self.shapes[plane];rh,rw=min(8,ph-y),min(8,pw-x)
        if not isinstance(tile,np.ndarray) or tile.dtype!=np.uint8 or tile.shape!=(rh,rw):self.fail('compact cropped tile geometry')
        self.stripe[:rh,x:x+rw]=tile;self.tiles+=1;self.x+=rw
        if self.x==pw:
            for j in range(rh):
                self.row[:pw]=self.stripe[j,:pw]
                self.sha.update(memoryview(self.row[:pw]).cast('B'));self.canonical_bytes+=2*pw;self.rows+=1
            self.stripes+=1;self.x=0;self.y+=rh
            if self.y==ph:self.plane+=1;self.y=0
            return dict(plane=plane,y=y,rows=rh,width=pw,canonical_bytes=2*rh*pw)
        return None
    def finish(self,expected,*,packet_validated,allow_publication):
        if (self.failed or self.sealed or self.plane!=3 or self.x or self.y
                or type(packet_validated)is not bool or not packet_validated
                or type(allow_publication)is not bool or type(expected)is not bytes or len(expected)!=16):self.fail('incomplete/unvalidated finalization')
        actual=self.sha.digest()[:16]
        if not hmac.compare_digest(actual,expected):self.fail('canonical tag mismatch')
        self.sealed=True;self._tag=actual
        if allow_publication:self._publication=actual
        return actual

def reconstruct(row,cohort,*,packet_override=None,hook=None):
    """Inverse one actual coefficient stripe; tag each new tile before external write.

    Complete parsed packet/coefficient/fixture arrays and external prediction/output
    banks are Python oracles outside the tagger-local bound. No full reconstructed
    plane is ever traversed as tag input. The callback is a test fault/stall hook.
    """
    packet=fixture.raw(row['ar03']) if packet_override is None else packet_override
    meta=trace.codec.identity(packet,decode=True);w,h=meta['width'],meta['height'];parsed=meta['parsed']
    if not meta['key']:
        bank=row['pre_banks'][str(meta['reference_bank'])]
        if (bank['id'],bank['tag'])!=(meta['reference_id'],meta['reference_tag'].hex()):raise ValueError('fixture reference mismatch')
    prediction=[np.full((ph,pw),128,np.int16) for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2))] if meta['key'] else [fixture.array(x) for x in row['pre_banks'][str(meta['reference_bank'])]['planes']]
    expected_planes=[fixture.array(x) for x in row['decoded_yuv']]
    expected_tag=trace.codec.reference_tag(expected_planes)
    eligible=meta['destination_bank']!=trace.codec.NO_BANK
    if eligible and expected_tag!=meta['stored_tag']:raise ValueError('stored publication mismatch')
    tagger=StripeTagger(w,h);planes=[];records=[];payload=bytearray();residual_samples=blocks=0
    try:
        for pi,(coeff,pred) in enumerate(zip(parsed['coefficients'],prediction)):
            ph,pw=pred.shape;bw,bh=(pw+7)//8,(ph+7)//8
            out=np.full((ph,pw),256,np.int16)
            scales=trace.codec.gm.roi.block_scales(parsed['scale_map'],w,h,pi)
            tables={q:v19.ft.qtable(q,pi!=0) for q in trace.codec.gm.roi.SCALES}
            for by in range(bh):
                lo,hi=by*bw,(by+1)*bw
                dequant=np.stack([coeff[i].astype(np.int64)*tables[int(scales[i])] for i in range(lo,hi)])
                residual,stats=v19.inverse(dequant)
                np.testing.assert_array_equal(residual,v19.ft.inverse(dequant));blocks+=bw;residual_samples+=residual.size
                y=8*by;rh=min(8,ph-y)
                for bx in range(bw):
                    x=8*bx;rw=min(8,pw-x)
                    tile=np.clip(pred[y:y+rh,x:x+rw].astype(np.int64)+residual[bx,:rh,:rw],0,255).astype(np.uint8)
                    # At this instant the output bank still contains its sentinel.
                    assert np.all(out[y:y+rh,x:x+rw]==256)
                    if hook is not None:hook(tagger,pi,y,x,tile)
                    stripe=tagger.push(pi,y,x,tile)
                    payload.extend(TILE.pack(pi,y,x,rh,rw));payload.extend(tile.tobytes())
                    out[y:y+rh,x:x+rw]=tile
                    if stripe is not None:records.append(stripe)
                # The next coefficient stripe is not examined until this one has
                # supplied every tile to the tagger and external write sink.
            np.testing.assert_array_equal(out,expected_planes[pi]);planes.append(out)
        tag=tagger.finish(expected_tag,packet_validated=True,allow_publication=eligible)
        if eligible:assert tagger.publication_tag==meta['stored_tag']
        else:
            try:tagger.publication_tag
            except ValueError:pass
            else:raise AssertionError('ordinary P published')
        base=v19.ft.planes_to_rgb(planes);assert hashlib.sha256(base.tobytes()).hexdigest()==row['base_rgb888_sha256']
        display=trace.codec._ui().apply_patches(base,meta['patches']) if meta['patches'] else base
        words=trace.codec.corpus.rgb565(display);np.testing.assert_array_equal(words,fixture.array(row['display_rgb565']))
        original=trace.codec.corpus.rgb565(fixture.array(row['source_rgb888']));selected=0
        for patch in meta['patches']:
            x,y,pw,ph=patch['rect'];np.testing.assert_array_equal(words[y:y+ph,x:x+pw],original[y:y+ph,x:x+pw]);selected+=pw*ph
        stream=STREAM.pack(b'IT20',1,w,h,tagger.tiles,len(payload))+bytes(payload)
        proof=dict(cohort=cohort,id=row['id'],width=w,height=h,key=meta['key'],published=eligible,
            packet_sha256=hashlib.sha256(packet).hexdigest(),private_tag_hex=tag.hex(),canonical_fixture_tag_hex=expected_tag.hex(),
            publication_tag_hex=tagger.publication_tag.hex() if eligible else None,blocks=blocks,tiles=tagger.tiles,
            residual_samples=int(residual_samples),reconstructed_samples=sum(p.size for p in planes),canonical_bytes_hashed=tagger.canonical_bytes,
            tagger_local_ndarray_bytes=tagger.local_array_bytes,tagger_stripe_bytes=tagger.stripe.nbytes,canonical_row_bytes=tagger.row.nbytes,
            output_written_after_tag_push=True,selected_ui_words=selected,selected_ui_word_errors=0,
            yuv_sha256=[hashlib.sha256(p.astype('<i2').tobytes()).hexdigest() for p in planes],
            display_rgb565_sha256=hashlib.sha256(words.astype('<u2').tobytes()).hexdigest(),stripes=records,
            tile_stream_sha256=hashlib.sha256(stream).hexdigest())
        return proof,stream
    except BaseException:
        tagger.abort();raise

def replay_stream(data,expected,*,eligible):
    if type(data)is not bytes or len(data)<STREAM.size:raise ValueError('IT20 short')
    magic,version,w,h,count,length=STREAM.unpack_from(data)
    if magic!=b'IT20' or version!=1 or len(data)!=STREAM.size+length:raise ValueError('IT20 header/length')
    t=StripeTagger(w,h);pos=STREAM.size
    try:
        for _ in range(count):
            if pos+TILE.size>len(data):raise ValueError('IT20 tile prefix')
            p,y,x,rh,rw=TILE.unpack_from(data,pos);pos+=TILE.size;n=rh*rw
            if pos+n>len(data):raise ValueError('IT20 tile data')
            a=np.frombuffer(data[pos:pos+n],np.uint8).reshape(rh,rw);pos+=n;t.push(p,y,x,a)
        if pos!=len(data):raise ValueError('IT20 trailing data')
        return t.finish(expected,packet_validated=True,allow_publication=eligible),t
    except BaseException:t.abort();raise

@dataclass(frozen=True)
class InlineBudget:
    hash_MBps:float=100
    copy_cycles_per_sample:float=1
    expand_cycles_per_sample:float=1
    hash_state_planning_bytes:int=128
    control_state_planning_bytes:int=64
    def validate(self):
        if any(not math.isfinite(x) or x<=0 for x in (self.hash_MBps,self.copy_cycles_per_sample,self.expand_cycles_per_sample)):raise ValueError('positive service')
        if any(type(x)is not int or x<0 for x in (self.hash_state_planning_bytes,self.control_state_planning_bytes)):raise ValueError('planning state')

def schedule(frame,b=None,inline=InlineBudget()):
    """Conditional inline hash with explicit per-stripe backpressure and storage.

    The reconstruction/compact-write consumer is serial, as in v19. On published
    frames it retains each reconstruction stripe until the parallel hash path has
    copied/expanded/hashed it. This is conservative and does not assume free hash
    work or a second SDRAM port. Complete packet preflight/cache/scanout constraints
    remain the frozen v19 planning assumptions, not hardware measurements.
    """
    inline.validate();b=b or v19.Budget(bytes_per_sample=1);b.validate()
    if b.bytes_per_sample!=1:raise ValueError('inline profile requires compact YUV8')
    # Same hash/expansion service assumptions in both designs; only placement,
    # reread removal and explicit new copy/backpressure differ.
    b=replace(b,tag_hash_MBps=inline.hash_MBps,tag_expand_cycles_sample=inline.expand_cycles_per_sample)
    baseline=v19.schedule(frame,b)
    reserve=b.scanout_width*b.scanout_height*b.scanout_hz*2/1e6;rate=b.effective_sdram_MBps-reserve
    def transfer(n):return n/(rate*1000)+math.ceil(n/b.memory_burst_bytes)*b.memory_burst_overhead_ns/1e6
    start=baseline['staged_ms']+baseline['preflight_ms']+baseline['compressed_cache_load_ms']
    entropy_free=consumer_free=start;free=[start]*b.stripe_buffers
    hashing=frame['published'];hash_free=start+(4/(inline.hash_MBps*1000) if hashing else 0)
    canonical=baseline['tag_canonical_hashed_bytes']
    compression_bytes=64*math.ceil((canonical+9)/64) if hashing else 0
    padding_bytes=compression_bytes-canonical if hashing else 0
    padding_ms=padding_bytes/(inline.hash_MBps*1000)
    entries=[];wait=hash_stall=hash_busy=0
    for i,s in enumerate(frame['stripes']):
        slot=i%b.stripe_buffers;es=max(entropy_free,free[slot]);wait+=es-entropy_free
        ec=math.ceil(max(s['refill_bytes']/b.compressed_cache_bytes_cycle,s['logical_bits']/b.entropy_bits_cycle))+2*s['blocks']
        ee=es+ec/(b.clock_mhz*1000);entropy_free=ee;cs=max(consumer_free,ee)
        pred=0 if frame['key'] else s['samples'];pd=cs+transfer(pred)
        cycles=v19.block_cycles(s['work'],b);inv=pd+cycles['total']/(b.clock_mhz*1000)
        wd=inv+transfer(s['samples'])
        hs=max(hash_free,inv);service=0
        if hashing:
            service=s['samples']*(inline.copy_cycles_per_sample+inline.expand_cycles_per_sample)/(b.clock_mhz*1000)+2*s['samples']/(inline.hash_MBps*1000)
            hd=hs+service;hash_free=hd;hash_busy+=service
        else:hd=inv
        done=max(wd,hd);hash_stall+=done-wd;consumer_free=done;free[slot]=done
        entries.append(dict(index=i,plane=s['plane'],y=s['y'],samples=s['samples'],coefficient_slot=slot,entropy_start_ms=es,entropy_done_ms=ee,
            consumer_start_ms=cs,prediction_done_ms=pd,inverse_done_ms=inv,compact_write_done_ms=wd,hash_start_ms=hs if hashing else None,
            hash_service_ms=service,hash_done_ms=hd if hashing else None,done_ms=done))
    if hashing:
        hash_free+=padding_ms
        prior=consumer_free;consumer_free=max(consumer_free,hash_free);hash_stall+=consumer_free-prior
        entries[-1]['hash_done_ms']=hash_free;entries[-1]['hash_finalize_service_ms']=padding_ms;entries[-1]['done_ms']=consumer_free
    post_bytes=baseline['color_read_bytes']+baseline['display_write_bytes']+baseline['ui_display_only_write_bytes']
    color_post=transfer(post_bytes)+(frame['selected_ui_pixels']/b.ui_pixels_cycle+baseline['color_control_and_mac_cycles'])/(b.clock_mhz*1000)
    end=consumer_free+color_post
    tagger_arrays=10*frame['width'] if hashing else 0
    state=inline.hash_state_planning_bytes+inline.control_state_planning_bytes if hashing else 0
    return dict(config=asdict(b),inline_config=asdict(inline),published=hashing,baseline_serial_frame_ms=baseline['frame_done_ms']+padding_ms,frame_done_ms=end,
        frame_budget_ms=b.frame_budget_ms,missed_frame_budget=end>b.frame_budget_ms,
        reference_tag_ready_ms=hash_free if hashing else None,bank_publication_earliest_ms=consumer_free if hashing else None,rgb_display_ready_ms=end,
        tag_bank_reread_bytes=0,eliminated_physical_tag_bank_bytes=frame['samples'] if hashing else 0,
        eliminated_v19_tag_read_planning_bytes=baseline['tag_read_bytes'],canonical_bytes_hashed=baseline['tag_canonical_hashed_bytes'],
        sha256_compression_service_bytes=compression_bytes,sha256_padding_service_bytes=padding_bytes,sha256_finalize_service_ms=padding_ms,
        hash_service_ms=hash_busy+(4/(inline.hash_MBps*1000) if hashing else 0)+padding_ms,hash_backpressure_ms=hash_stall,
        entropy_backpressure_ms=wait,post_color_ms=color_post,baseline_local_buffer_bytes=baseline['local_buffer_total_bytes'],
        additional_tagger_ndarray_bytes=tagger_arrays,additional_hash_control_planning_bytes=state,
        local_planning_bytes=baseline['local_buffer_total_bytes']+tagger_arrays+state,stripes=entries)
