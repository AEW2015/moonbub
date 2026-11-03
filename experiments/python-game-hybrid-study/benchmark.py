#!/usr/bin/env python3
"""Actual temporal GM01 controls with capped same-source HP01/HR01 selection."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time
import av
import numpy as np
import PIL
import hybrid_codec as h

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

rate=load('hybrid_rate',HERE.parent/'python-game-rate-study/controller.py')
fixtures=load('hybrid_fixtures',HERE.parent/'python-game-roi-study/benchmark.py')
flat=load('hybrid_flat',HERE.parent/'python-game-hud-study/flat_probe.py')
POLICIES={f'{region}_{policy}':h.Config(rectangles=rects,patch_policy=policy)
          for region,rects in (('broad',h.BROAD),('compact',h.COMPACT)) for policy in ('hp01','adaptive_row')}
INDICES=(0,2,4,6,8,10,12,14)

def now():return time.perf_counter_ns()
def ms(t):return (now()-t)/1e6
def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):return sha(p.read_bytes())

def roi(rects):
    result=np.zeros((480,720),bool)
    for x,y,w,hh in rects:result[y:y+hh,x:x+w]=True
    return result

BROAD_MASK=roi(h.BROAD)

def quality(original_words,display_words,active):
    a=h.hp.corpus.expand565(original_words).astype(np.int16)
    b=h.hp.corpus.expand565(display_words).astype(np.int16)
    delta=a.astype(np.int32)-b;error=np.mean(delta*delta,axis=2)
    mask=np.zeros((480,720),bool);x,y,w,hh=active;mask[y:y+hh,x:x+w]=True
    return {label:{'mse':float(np.mean(error[m])),'pixels':int(m.sum())}
            for label,m in (('active',mask),('common_broad_roi',mask&BROAD_MASK),('background',mask&~BROAD_MASK))}


def selected_record(d,base,source,control_rgb,base_ms,selector_ms,rx,active):
    rec={'accepted':d.accepted,'format':d.format,'reason':d.reason,'packet_bytes':None if d.packet is None else len(d.packet),
         'packet_sha256':None if d.packet is None else sha(d.packet),'base_packet_sha256':sha(base),'base_bytes':len(base),
         'identity':d.identity,'requested_pixels':d.requested_pixels,'selected_pixels':d.selected_pixels,
         'selected_requested_fraction':d.selected_pixels/d.requested_pixels,'selected_common_broad_fraction':d.selected_pixels/47360,
         'attempts':d.attempts,'selected':d.selected,'deadline_hit':d.deadline_hit,'unattempted_rectangles':d.unattempted_rectangles,
         'base_prepare_ms_reused':base_ms,'selector_ms':selector_ms,'selector_internal_ms':d.service_ms,
         'preflight_ms':d.preflight_ms,'assembly_ms':d.assembly_ms,'wrapper_bytes_built':d.wrapper_bytes_built,
         'candidate_encode_ms':sum(a['encode_ms'] for a in d.attempts),'candidate_validate_ms':sum(a['validate_ms'] for a in d.attempts),
         'charged_prepare_ms':base_ms+selector_ms,'observed_total_internal_ms':d.observed_total_ms}
    if not d.accepted:
        assert len(base)>49152 and not d.attempts;return rec
    assert len(d.packet)<=49152
    identity=h.base_identity(d.packet,epoch=rx.epoch);assert identity['frame_id']==d.identity['frame_id']
    if d.format=='GM01':assert d.packet==base
    started=now();actual,info=rx.receive(d.packet);receive_ms=ms(started)
    assert info['base_rgb_sha256']==sha(control_rgb.tobytes())
    source_words=h.hp.corpus.rgb565(source);words=h.hp.corpus.rgb565(actual);base_words=h.hp.corpus.rgb565(control_rgb)
    mask=roi([p['rect'] for p in d.selected])
    selected_errors=int(np.count_nonzero(source_words[mask]!=words[mask]));assert selected_errors==0
    unchanged_errors=int(np.count_nonzero(base_words[~mask]!=words[~mask]));assert unchanged_errors==0
    rec.update(receive_ms=receive_ms,full_service_ms=rec['charged_prepare_ms']+receive_ms,
               selected_rgb565_mismatches=selected_errors,unselected_base_rgb565_mismatches=unchanged_errors,
               quality=quality(source_words,words,active),display_rgb565_sha256=sha(words.astype('<u2').tobytes()),
               base_rgb_sha256=info['base_rgb_sha256'],anchor_id=rx.base.anchor_id,
               forward_accounting_bytes=len(d.packet)+59*((len(d.packet)+1023)//1024),reverse_accounting_bytes=52)
    return rec


def aggregate(records):
    summaries={}
    for cohort in ('temporal_real','heldout_real','synthetic_noisy','synthetic_flat'):
        sources=[r for r in records if r['cohort']==cohort];out={}
        for policy in POLICIES:
            rows=[r['policies'][policy] for r in sources if policy in r['policies']];accepted=[r for r in rows if r['accepted']]
            item={'sources':len(sources),'selector_decisions':len(rows),'admitted':len(accepted),'selector_base_rejects':len(rows)-len(accepted),
                  'controller_base_rejects':sum(r['controller_rejected'] for r in sources),
                  'GH01':0,'HG01':sum(r['format']=='HG01' for r in accepted),'GM01':sum(r['format']=='GM01' for r in accepted),
                  'attempted_rectangles':sum(len(r['attempts']) for r in rows),
                  'rejected_attempts':sum(not a['selected_in_output'] for r in rows for a in r['attempts'])}
            if accepted:
                item.update(mean_packet_bytes=float(np.mean([r['packet_bytes'] for r in accepted])),max_packet_bytes=max(r['packet_bytes'] for r in accepted),
                    mean_selected_pixels=float(np.mean([r['selected_pixels'] for r in accepted])),
                    mean_common_broad_coverage=float(np.mean([r['selected_common_broad_fraction'] for r in accepted])),
                    mean_requested_coverage=float(np.mean([r['selected_requested_fraction'] for r in accepted])),
                    mean_prepare_ms=float(np.mean([r['charged_prepare_ms'] for r in accepted])),
                    mean_receive_ms=float(np.mean([r['receive_ms'] for r in accepted])),
                    mean_full_service_ms=float(np.mean([r['full_service_ms'] for r in accepted])),
                    p95_full_service_ms=float(np.percentile([r['full_service_ms'] for r in accepted],95)),
                    mean_common_broad_roi_mse=float(np.mean([r['quality']['common_broad_roi']['mse'] for r in accepted])),
                    selected_format_histogram={fmt:sum(p['format']==fmt for r in accepted for p in r['selected']) for fmt in ('HP01','HR01')})
            out[policy]=item
        summaries[cohort]=out
    return summaries


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'hybrid_codec.py',HERE/'test_hybrid_codec.py',HERE/'benchmark.py',Path(h.row.__file__),Path(h.hp.__file__),
           Path(h.gm.__file__),Path(h.gm.roi.__file__),Path(h.gm.ft.__file__),Path(h.gm.mt.__file__),Path(h.gm.token_coeff.__file__),
           Path(h.gm.word_coeff.__file__),Path(h.gm.word_coeff.frozen_codec.__file__),Path(h.hp.corpus.__file__),Path(rate.__file__),Path(fixtures.__file__),Path(flat.__file__)]
    pins={str(p):digest(p) for p in paths};records=[]
    def evaluate(name,rgb,manifest,index,cohort,frame_id,encoder,plain,receivers,controller=None,force_key=False):
        began=now()
        if controller is not None:
            base_decision=controller.prepare(rgb,frame_id,force_key=force_key)
            base=base_decision.packet;attempts=base_decision.attempts
        else:
            scale=h.gm.roi.declared_map(720,480,h.BROAD,8,16);base=encoder.prepare(rgb,frame_id,scale_map=scale)
            attempts=None
        base_ms=ms(began)
        rec={'name':name,'cohort':cohort,'manifest':manifest,'source_index':index,'source_rgb_sha256':sha(rgb.tobytes()),
             'frame_id':frame_id,'controller_rejected':base is None,'base_controller_attempts':attempts,'policies':{}}
        if base is None:
            rec['base_rejection_ms']=base_ms;records.append(rec);return
        began=now();control_rgb,control_info=plain.receive(base);control_receive_ms=ms(began)
        original_words=h.hp.corpus.rgb565(rgb);base_words=h.hp.corpus.rgb565(control_rgb)
        active=tuple(manifest.get('active_rects',[(0,0,720,480)])[index])
        identity=h.base_identity(base) if len(base)<=49152 else h._preflight_base(base)
        rec['control']={'bytes':len(base),'over_cap':len(base)>49152,'packet_sha256':sha(base),'identity':identity,
                        'prepare_ms':base_ms,'receive_ms':control_receive_ms,'full_service_ms':base_ms+control_receive_ms,
                        'quality':quality(original_words,base_words,active),'base_rgb_sha256':sha(control_rgb.tobytes())}
        for label,cfg in POLICIES.items():
            began=now();decision=h.select_frame(base,rgb,cfg,spent_before_ms=base_ms);selector_ms=ms(began)
            rec['policies'][label]=selected_record(decision,base,rgb,control_rgb,base_ms,selector_ms,receivers[label],active)
            if decision.accepted:
                for a,b in zip(receivers[label].base._anchor,plain._anchor):np.testing.assert_array_equal(a,b)
        encoder.ack(frame_id,epoch=1)
        records.append(rec)
        print(name,{p:(r['format'],r['packet_bytes'],r['selected_pixels']) for p,r in rec['policies'].items()},flush=True)
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=h.hp.corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        controller=rate.Controller();plain=h.gm.Receiver();receivers={p:h.Decoder() for p in POLICIES}
        assert len(frames)==60
        for index,rgb in enumerate(frames):
            evaluate(f'{clip}-seq{index}',rgb,manifest,index,'temporal_real',index,controller.encoder,plain,receivers,controller,force_key=index in (0,30))
        frames,manifest=h.hp.corpus.load_video(media/(clip+'.mp4'),max_frames=16,start_seconds=4)
        for index in INDICES:
            evaluate(f'{clip}-heldout{index}',frames[index],manifest,index,'heldout_real',0,h.gm.Encoder(),h.gm.Receiver(),{p:h.Decoder() for p in POLICIES})
    synthetic=[(name,rgb,'synthetic_noisy') for name,rgb in fixtures.synthetic_fixtures()]
    synthetic.extend((('flat-monochrome',flat.fixture(False),'synthetic_flat'),('flat-colored',flat.fixture(True),'synthetic_flat')))
    for name,rgb,cohort in synthetic:
        manifest={'source':'synthetic:'+name,'synthetic':True,'active_rects':[(0,0,720,480)],'frame_sha256':[sha(rgb.tobytes())],
                  'scope':'Seeded noisy background/antialiased UI' if cohort=='synthetic_noisy' else 'Deliberately flat low-color 1-bit-glyph best case, not general game evidence'}
        evaluate(name,rgb,manifest,0,cohort,0,h.gm.Encoder(),h.gm.Receiver(),{p:h.Decoder() for p in POLICIES})
    assert pins=={str(p):digest(p) for p in paths},'executed source changed'
    result={'evidence':'Actual HG01 selective HP01/HR01 integration and byte-identical GM01 fallback contract; same-source temporal software decode, not finite link or hardware/FPS proof',
            'source_sha256':pins,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'source_inputs':len(records),'selector_decisions':sum(len(r['policies']) for r in records),'records':records,'summary':aggregate(records),
            'policies':{name:{'rectangles':cfg.rectangles,'patch_policy':cfg.patch_policy,'max_attempts':cfg.max_attempts,'frame_cap':cfg.frame_cap,'work_budget_ms':cfg.work_budget_ms} for name,cfg in POLICIES.items()},
            'temporal_scope':'Two60-frame native sequential clips from1s, acknowledged only after all4 independent matching-policy decoders finish. Forced keys at sequence0/30. Same immutable GM YUV anchor, no loss/reorder/pacing/queue test. Clips25/29.88fps and related precompressed content, not120distinct30fps game frames.',
            'heldout_scope':'Eight fixed indices0,2,...14 from4s eachclip, independent keys, outside the120-frame temporal windows. Synthetic noisy and flat cases separate.',
            'selection_scope':'Same current capture RGB and actual GM/patch sizes only. Up to4 declared nonoverlap rectangles; no future or quality oracle. Complete cap49152 includes HGheaderCRC22 and4-byteprefix/patch. No fittingpatch returns originalGMbytes; overcapbase explicitly rejects. Compact21120pixels is44.59percent of broad47360; both denominators reported.',
            'timing_scope':'Host Python wall, uncontrolled load and fixed order. Base preparation includes map/controller attempts and is actually measured once per source then charged to each profile. Selector includes cheap baseheader/map/CRC preflight, all HP/HR candidates even rejected, selectedpatchvalidation andassembly. Receive includes allpatchvalidation, one GMentropydecode, basehash, RGB565overlay. Source decode/scaling/metrics/oraclechecks/transport/display excluded. No hard deadline or FPS claim.',
            'quality_scope':'MSE uses originalRGB565 and displayedRGB565 expanded to RGB channels on active/commonbroad/background regions. Selected word mismatch0 is exact; unselected matchesGMbase. SourceRGB888 precision alreadyquantized. DeclaredrealROIs not verifiedHUD locations.',
            'transport_scope':'Forward=packet+59*ceil(packet/1024), reverse52 peracceptedframe, accountingonly. HG01notacceptedbyfrozenGF02/MSV1/JPEG peers untilparentexplicitlyintegrates andnegotiates profile.',
            'memory_scope':'Python fullarrays/packets; no targetBRAM/SRAM/SDRAM/ESP32service qualification.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result['summary'],indent=2),flush=True)

if __name__=='__main__':main()
