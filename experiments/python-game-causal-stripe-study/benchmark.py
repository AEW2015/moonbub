#!/usr/bin/env python3
"""Exact sparse-inverse proof and conditional actual-stripe service campaign."""
from dataclasses import replace
from pathlib import Path
import hashlib,json,time
import numpy as np
import model
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
TRACE=HERE.parent/'python-game-ar03-trace-study'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.astype('<i2').tobytes()).hexdigest()
def make_frames():
    d=json.loads((TRACE/'results.json').read_text());frames=[]
    for cohort in d['cohorts']:
        for row in cohort['rows']:
            packet=model.fixture.raw(row['ar03']);trace=json.loads(model.fixture.raw(row['trace']));meta=model.trace.codec.identity(packet,decode=True);parsed=meta['parsed'];w,h=meta['width'],meta['height']
            if not meta['key']:
                bank=row['pre_banks'][str(meta['reference_bank'])];assert (bank['id'],bank['tag'])==(meta['reference_id'],meta['reference_tag'].hex())
            prediction=[np.full((ph,pw),128,np.int16) for pw,ph in ((w,h),(w//2,h//2),(w//2,h//2))] if meta['key'] else [model.fixture.array(x) for x in row['pre_banks'][str(meta['reference_bank'])]['planes']]
            all_stats=[];stripes=[];planes=[];plane_proofs=[]
            for pi,(coeff,pred,pinfo) in enumerate(zip(parsed['coefficients'],prediction,trace['planes'])):
                a=coeff.astype(np.int64)*model.trace.codec.gm.roi.block_tables(parsed['scale_map'],w,h,pi)
                residual,stats=model.inverse(a);reference=model.ft.inverse(a);np.testing.assert_array_equal(residual,reference)
                pw,ph=pinfo['width'],pinfo['height'];bw,bh=pinfo['blocks_w'],pinfo['blocks_h']
                stitched=residual.reshape(bh,bw,8,8).transpose(0,2,1,3).reshape(bh*8,bw*8)[:ph,:pw]
                got=np.clip(pred+stitched,0,255).astype(np.int16);packed=got.astype(np.uint8);np.testing.assert_array_equal(packed.astype(np.int16),got);expected=model.fixture.array(row['decoded_yuv'][pi]);np.testing.assert_array_equal(got,expected);planes.append(got)
                plane_proofs.append(dict(plane=pi,blocks=len(coeff),residual_samples=int(residual.size),reconstructed_samples=int(got.size),
                    residual_sha256=digest(residual),frozen_residual_sha256=digest(reference),yuv_sha256=digest(got),frozen_yuv_sha256=digest(expected),packed_yuv8_sha256=hashlib.sha256(packed.tobytes()).hexdigest(),packed_bytes=int(packed.nbytes),unpacked_int16_tag_bytes=int(got.nbytes),
                    max_dequantized_abs=int(np.abs(a).max(initial=0)),max_second_multiply_input_abs=stats['max_second_multiply_input_abs'],
                    rounding_bias_abs_upper=stats['rounding_bias_abs_upper'],observed_accumulator_signed_bits=stats['observed_accumulator_signed_bits'],
                    max_first_accumulator_abs=stats['max_first_accumulator_abs'],max_second_accumulator_abs=stats['max_second_accumulator_abs']))
                for s in pinfo['stripes']:
                    lo=s['block_start'];hi=lo+s['block_count'];sub=coeff[lo:hi].reshape(hi-lo,64);general=np.any(sub[:,1:]!=0,axis=1);dc=(~general)&(sub[:,0]!=0)
                    work=dict(blocks=hi-lo,zero=int((~general&~dc).sum()),dc=int(dc.sum()),general=int(general.sum()),
                        **{k:stats[k][lo:hi] for k in ('first_mac','second_mac','nonzero_coeff','intermediate_nnz')})
                    stripes.append(dict(plane=pi,y=s['y'],rows=s['rows'],samples=pw*s['rows'],blocks=s['block_count'],
                        refill_bytes=sum(model.selected_reads(b) for b in s['blocks']),logical_bits=sum(model.logical_bits(b) for b in s['blocks']),work=work))
                all_stats.append(stats)
            canonical_tag=model.trace.codec.reference_tag(planes)
            packed_roundtrip_tag=model.trace.codec.reference_tag([p.astype(np.uint8).astype(np.int16) for p in planes]);assert packed_roundtrip_tag==canonical_tag
            if meta['destination_bank']!=model.trace.codec.NO_BANK:assert canonical_tag==meta['stored_tag']
            base=model.ft.planes_to_rgb(planes);assert hashlib.sha256(base.tobytes()).hexdigest()==row['base_rgb888_sha256']
            display=model.trace.codec._ui().apply_patches(base,meta['patches']) if meta['patches'] else base
            words=model.trace.codec.corpus.rgb565(display);expected=model.fixture.array(row['display_rgb565']);np.testing.assert_array_equal(words,expected)
            selected=0;original=model.trace.codec.corpus.rgb565(model.fixture.array(row['source_rgb888']))
            for patch in meta['patches']:
                x,y,pw,ph=patch['rect'];np.testing.assert_array_equal(words[y:y+ph,x:x+pw],original[y:y+ph,x:x+pw]);selected+=pw*ph
            assert all(s['max_dequantized_abs']<2**31 and s['max_second_multiply_input_abs']<2**31 and s['rounding_bias_abs_upper']<2**39 for s in all_stats)
            blocks=sum(s['blocks'] for s in all_stats);general=sum(s['general'] for s in all_stats);dc=sum(s['dc'] for s in all_stats);zero=sum(s['zero'] for s in all_stats)
            first=sum(sum(s['first_mac']) for s in all_stats);second=sum(sum(s['second_mac']) for s in all_stats);dequant=sum(sum(s['nonzero_coeff']) for s in all_stats)
            frame=dict(cohort=cohort['name'],id=row['id'],width=w,height=h,key=meta['key'],published=meta['destination_bank']!=model.trace.codec.NO_BANK,
                inner_codec=meta['inner_codec'],packet_bytes=len(packet),packet_sha256=sha(TRACE/row['ar03']['path']),source_rgb_sha256=row['source_rgb888']['blob']['raw_sha256'],
                samples=sum(p.size for p in planes),blocks=blocks,zero=zero,dc=dc,general=general,
                dense_mac_operations=1024*blocks,existing_bypass_general_mac_operations=1024*general,sparse_mac_operations=first+second,dc_constant_multiplies=2*dc,
                dequant_multiplies=dequant,dense_dequant_multiplies=64*blocks,
                exact_residual_samples=sum(p['residual_samples'] for p in plane_proofs),exact_reconstructed_samples=sum(p['reconstructed_samples'] for p in plane_proofs),
                selected_ui_pixels=selected,selected_ui_word_errors=0,canonical_int16_tag_hex=canonical_tag.hex(),packed_roundtrip_tag_hex=packed_roundtrip_tag.hex(),display_rgb565_sha256=hashlib.sha256(words.astype('<u2').tobytes()).hexdigest(),
                plane_proofs=plane_proofs,stripes=stripes)
            frames.append(frame)
    return frames

def pins():
    d=json.loads((TRACE/'results.json').read_text());paths={ROOT/p for p in d['source_sha256']}
    paths|={p for p in (TRACE/'objects').iterdir() if p.is_file()}
    paths|={TRACE/'results.json',TRACE/'stripe-demand.json',HERE/'model.py',HERE/'benchmark.py',HERE/'verify.py',HERE/'test_model.py'}
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def main():
    before=pins();started=time.perf_counter();frames=make_frames();cases=[];base=model.Budget()
    profiles=[('dense_all4_diagnostic',replace(base,sparse=False,bypass=False)),('existing_bypass4',replace(base,sparse=False)),('sparse1',replace(base,wide_lanes=1)),('sparse2',replace(base,wide_lanes=2)),('sparse4',base),
        ('sparse8',replace(base,wide_lanes=8)),('sparse4_onebuffer',replace(base,stripe_buffers=1)),('sparse4_mem80',replace(base,effective_sdram_MBps=80)),
        ('sparse4_yuv8',replace(base,bytes_per_sample=1)),('sparse4_yuv8_mem240',replace(base,bytes_per_sample=1,effective_sdram_MBps=240))]
    for label,budget in profiles:
        rows=[]
        for frame in frames:
            schedule=model.schedule(frame,budget);uniform=model.schedule(frame,budget,True)
            rows.append(dict(cohort=frame['cohort'],id=frame['id'],schedule=schedule,
                uniform_frame_done_ms=uniform['frame_done_ms'],uniform_entropy_backpressure_ms=uniform['entropy_backpressure_ms'],
                actual_peak_stripe_refill_bytes=max(s['refill_bytes'] for s in frame['stripes']),
                uniform_peak_stripe_refill_bytes=max(s['refill_bytes'] for s in uniform['stripes'])))
        native=[r['schedule'] for r in rows if r['cohort'].startswith('native')]
        summary=dict(profile=label,native_decisions=len(native),native_frame_done_ms_min=min(r['frame_done_ms'] for r in native),native_frame_done_ms_max=max(r['frame_done_ms'] for r in native),
            native_mean_ms=sum(r['frame_done_ms'] for r in native)/len(native),native_budget_misses=sum(r['missed_frame_budget'] for r in native),
            max_local_coefficient_stripe_bytes=max(r['local_coefficient_stripe_bytes'] for r in native),max_entropy_backpressure_ms=max(r['entropy_backpressure_ms'] for r in native))
        print(json.dumps(summary),flush=True);cases.append(dict(profile=label,budget=replace(budget).__dict__,summary=summary,rows=rows))
    assert before==pins()
    out=dict(schema='gamebub-actual-stripe-service-v1',source_sha256=before,frames=frames,cases=cases,
        legal_width_bounds=model.legal_width_bounds(),counts=dict(packets=len(frames),native_decisions=12,unique_native_acquisitions=6,flat_controls=4,blocks=sum(f['blocks'] for f in frames),
            exact_residual_samples=sum(f['exact_residual_samples'] for f in frames),exact_reconstructed_samples=sum(f['exact_reconstructed_samples'] for f in frames),
            exact_selected_ui_words=sum(f['selected_ui_pixels'] for f in frames),profiles=len(profiles)),python_wall_seconds=time.perf_counter()-started,
        arithmetic_scope='All actual dequantized AR03 blocks compare bit-exact with frozen two-pass Q14 inverse. Zero/DC shortcut and zero-product skipping preserve both rounding boundaries. All reconstructed YUV and display RGB565 compare with retained fixture vectors; selected UI remains display-only.',
        timing_scope='Declared conditional service model, not measured native or RTL cycles. Two dependent passes, nonzero discovery/index scans, dequant, round/control overhead and 64 output stores paid. One serial prediction/inverse/write consumer overlaps bounded coefficient-stripe entropy prefetch. No fused optimistic future-memory reservation.',
        memory_scope='Complete compressed input staged externally thenloadedinto separatelycounted49152byte localcache;external→cachecopyandlocalcache entropy reads charged. Four complete packet preflight/CRC planning passes are an explicit assumption, not a derived parser traversal count. Reference/reconstruction/tag/color traffic uses declared2-byte canonical or1-byte physicalYUV storage; packedYUV8roundtrip isexact andcanonicalSHA256taghashstill2bytes/sample;compacttags payexpansionworkwithoutinventingasecondSDRAMread. Bilinearchroma/colorconstantMACs/control/RGB565packservice,RGB565 display/UI writesandlinebufferspaid. 800x480x60 RGB565 scanout is average bandwidth reservation only; physical480x800 scan order, line deadlines/scaler/rotation/controller timing not proved.',
        multiplier_scope='wide_lanes are hypothetical exact32x16 product/40bit accumulation slots. Count2 18x18 primitives perwide lane as planning assumption; split-sign/recombine/add/round/index/routing logic andFmax not fitted. Legal coefficient2048*quantizer255 bound fits32bit multiplyinput/40bit accumulators; no DSP/RAM mapping or area proof.',
        bounded_scope='At most4 configurable coefficient stripes and one reconstruction stripe, plus two<=64bit entropy reservoirs,960B inverse/index scratch,512B basis/quantizerROM,colorlinebuffers,512BUIpalettewhenneededand a separatelycounted49152bytecompressedlocalcache. Control metadata and parser implementation state remain unmodeled. Python trace, fullcoefficient/output/oracle arrays and external reference/display banks are excluded from local-buffer bound. Nativecohorts reuse6 acquisitions across12 decisions;4flatcontrols notgameplayFPS. No jointgateway/ESP ISA/RF, hardware orphysical30fps proof.')
    (HERE/'results.json').write_text(json.dumps(out,separators=(',',':'),allow_nan=False)+'\n')
if __name__=='__main__':main()
