#!/usr/bin/env python3
"""Bounded real-byte selective patches; no hardware or sustained FPS claim."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import PIL
import av
import selector as s

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

metrics=load('selective_metrics',HERE.parent/'python-game-roi-study/benchmark.py')
flat=load('selective_flat',HERE.parent/'python-game-hud-study/flat_probe.py')
rate=load('selective_rate',HERE.parent/'python-game-rate-study/controller.py')
INDICES=(0,2,4,6,8,10,12,14)
POLICIES={'broad':s.Config(rectangles=s.BROAD),'compact':s.Config(rectangles=s.COMPACT),
          'compact_observed35ms':s.Config(rectangles=s.COMPACT,work_budget_ms=35)}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sha(data):return hashlib.sha256(data).hexdigest()
def now():return time.perf_counter_ns()
def ms(start):return (now()-start)/1e6

def mask(rects):
    out=np.zeros((480,720),bool)
    for x,y,w,h in rects:out[y:y+h,x:x+w]=True
    return out

def wire(size):return {'forward_bytes':size+59*math.ceil(size/1024),'reverse_bytes':52}

def decision_row(d,base,source,base_rgb,base_cost,outer_selector,active,synthetic,receiver=None):
    row={'accepted':d.accepted,'format':d.format,'reason':d.reason,'base_bytes':len(base),
         'bytes':None if d.packet is None else len(d.packet),'base_packet_sha256':sha(base),
         'packet_sha256':None if d.packet is None else sha(d.packet),'requested_pixels':d.requested_pixels,
         'selected_pixels':d.selected_pixels,'selected_requested_fraction':d.selected_pixels/d.requested_pixels,
         'selected_common_broad_fraction':d.selected_pixels/47360,'attempts':list(d.attempts),'selected':list(d.selected),
         'deadline_hit':d.deadline_hit,'unattempted_rectangles':d.unattempted_rectangles,
         'base_prepare_ms':base_cost,'selector_ms':outer_selector,'selector_internal_ms':d.service_ms,
         'prepare_ms':base_cost+outer_selector,'observed_total_internal_ms':d.observed_total_ms,
         'base_validation_ms':d.base_validation_ms,'assembly_ms':d.assembly_ms,
         'wrapper_bytes_built':d.wrapper_bytes_built,'attempt_encode_ms':sum(a['encode_ms'] for a in d.attempts),
         'attempt_validate_ms':sum(a['validate_ms'] for a in d.attempts)}
    if not d.accepted:
        assert len(base)>49152 and not d.attempts;return row
    assert len(d.packet)<=49152
    if d.format=='GM01':assert d.packet==base
    rx=receiver or s.Decoder();began=now();actual,info=rx.receive(d.packet);receive_ms=ms(began)
    assert info['base_rgb_sha256']==sha(base_rgb.tobytes())
    source_words=s.hud.corpus.rgb565(source);actual_words=s.hud.corpus.rgb565(actual)
    selected=mask([p['rect'] for p in d.selected])
    selected_errors=int(np.count_nonzero(source_words[selected]!=actual_words[selected]));assert selected_errors==0
    unchanged_errors=int(np.count_nonzero(s.hud.corpus.rgb565(base_rgb)[~selected]!=actual_words[~selected]));assert unchanged_errors==0
    row.update(receive_ms=receive_ms,full_service_ms=row['prepare_ms']+receive_ms,
               selected_rgb565_mismatches=selected_errors,unselected_base_rgb565_mismatches=unchanged_errors,
               base_rgb_sha256=info['base_rgb_sha256'],display_rgb565_sha256=sha(actual_words.astype('<u2').tobytes()),
               metrics=metrics.metric(source,actual,s.BROAD,active,synthetic),
               anchor_id=rx.base.anchor_id,**wire(len(d.packet)))
    return row

def summary(scenes):
    result={}
    for label,prefix in (('combat','mass-effect-combat'),('second_clip','mass-effect-2600'),('synthetic_noisy','seeded-HUD'),('flat_best_case','flat-')):
        sources=[v for v in scenes if v['name'].startswith(prefix)];out={}
        for policy in POLICIES:
            rows=[v['policies'][policy] for v in sources];accepted=[r for r in rows if r['accepted']]
            entry={'sources':len(rows),'accepted':len(accepted),'base_rejected':len(rows)-len(accepted),
                   'GH01':sum(r['format']=='GH01' for r in accepted),'GM01':sum(r['format']=='GM01' for r in accepted),
                   'deadline_fallbacks':sum(r['deadline_hit'] for r in rows),
                   'attempts':sum(len(r['attempts']) for r in rows),'rejected_attempts':sum(not a['selected_in_output'] for r in rows for a in r['attempts']),
                   'prepare_mean_ms':float(np.mean([r['prepare_ms'] for r in rows])),
                   'full_service_mean_ms':None if not accepted else float(np.mean([r['full_service_ms'] for r in accepted]))}
            if accepted:
                entry.update(mean_bytes=float(np.mean([r['bytes'] for r in accepted])),max_bytes=max(r['bytes'] for r in accepted),
                    mean_selected_pixels=float(np.mean([r['selected_pixels'] for r in accepted])),
                    mean_selected_requested_fraction=float(np.mean([r['selected_requested_fraction'] for r in accepted])),
                    mean_selected_common_broad_fraction=float(np.mean([r['selected_common_broad_fraction'] for r in accepted])),
                    full_service_p95_ms=float(np.percentile([r['full_service_ms'] for r in accepted],95)),
                    mode_histogram={str(mode):sum(p['mode']==mode for r in accepted for p in r['selected']) for mode in (0,1,2,4,8)},
                    base_common_roi_mse=float(np.mean([v['control']['metrics']['roi']['mse'] for v in sources])),
                    selected_common_roi_mse=float(np.mean([r['metrics']['roi']['mse'] for r in accepted])))
            out[policy]=entry
        result[label]=out
    return result

def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[HERE/'selector.py',HERE/'benchmark.py',HERE/'test_selector.py',Path(s.hud.__file__),Path(s.hud.gm.__file__),
             Path(s.hud.gm.roi.__file__),Path(s.hud.gm.ft.__file__),Path(s.hud.gm.mt.__file__),Path(s.hud.gm.token_coeff.__file__),
             Path(s.hud.gm.word_coeff.__file__),Path(s.hud.gm.word_coeff.frozen_codec.__file__),Path(s.hud.corpus.__file__),
             Path(metrics.__file__),Path(flat.__file__),Path(rate.__file__)]
    hashes={str(p):digest(p) for p in sources};inputs=[];scenes=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=s.hud.corpus.load_video(media/f'{clip}.mp4',max_frames=16,start_seconds=4)
        for i in INDICES:inputs.append((f'{clip}-frame{i}',frames[i],manifest,i,tuple(manifest['active_rects'][i]),False))
    fixtures=[*metrics.synthetic_fixtures(),('flat-monochrome',flat.fixture(False)),('flat-colored',flat.fixture(True))]
    for name,rgb in fixtures:
        manifest={'source':'synthetic:'+name,'synthetic':True,'frame_sha256':[sha(rgb.tobytes())],
                  'scope':'Seeded noisy HUD' if name.startswith('seeded') else 'Deliberately flat low-color 1-bit glyph best case, not game evidence'}
        inputs.append((name,rgb,manifest,0,(0,0,720,480),True))
    for name,rgb,manifest,index,active,synthetic in inputs:
        enc=s.hud.gm.Encoder();began=now()
        mapped=s.hud.gm.roi.declared_map(720,480,s.BROAD,8,16);base=enc.prepare(rgb,0,scale_map=mapped);base_ms=ms(began)
        began=now();base_rgb,base_info=s.hud.gm.Receiver().receive(base);base_receive_ms=ms(began)
        assert sha(base_rgb.tobytes())==enc.expected_hash(0)
        control={'bytes':len(base),'over_cap':len(base)>49152,'packet_sha256':sha(base),
                 'prepare_ms':base_ms,'receive_ms':base_receive_ms,'full_service_ms':base_ms+base_receive_ms,
                 'metrics':metrics.metric(rgb,base_rgb,s.BROAD,active,synthetic),'base_rgb_sha256':sha(base_rgb.tobytes())}
        policies={}
        for label,cfg in POLICIES.items():
            began=now();d=s.select_frame(base,rgb,cfg,spent_before_ms=base_ms);outer=ms(began)
            policies[label]=decision_row(d,base,rgb,base_rgb,base_ms,outer,active,synthetic)
        scenes.append({'name':name,'manifest':manifest,'source_index':index,'input_sha256':manifest['frame_sha256'][index],
                       'synthetic':synthetic,'control':control,'policies':policies})
        print(name,{k:(v['format'],v['bytes'],v['selected_pixels'],len(v['attempts'])) for k,v in policies.items()},flush=True)
    # A functional causal mixed-format sequence, not paced simulation. A fixed
    # every-third-frame policy disables patches before current data is examined.
    frames,manifest=s.hud.corpus.load_video(media/'mass-effect-combat.mp4',max_frames=12,start_seconds=4)
    controller=rate.Controller();rx=s.Decoder();plain=s.hud.gm.Receiver();sequence=[]
    for i,rgb in enumerate(frames):
        began=now();base_decision=controller.prepare(rgb,i);base_ms=ms(began)
        if not base_decision.accepted:
            sequence.append({'frame_id':i,'base_rejected':True,'base_attempts':base_decision.attempts});continue
        base=base_decision.packet;pure,_=plain.receive(base)
        cfg=s.Config(rectangles=s.COMPACT,max_attempts=0 if i%3==1 else 4)
        began=now();d=s.select_frame(base,rgb,cfg,spent_before_ms=base_ms);outer=ms(began)
        row=decision_row(d,base,rgb,pure,base_ms,outer,tuple(manifest['active_rects'][i]),False,rx)
        assert d.accepted and row['base_rgb_sha256']==controller.encoder.expected_hash(i)
        for a,b in zip(rx.base._anchor,plain._anchor):np.testing.assert_array_equal(a,b)
        controller.encoder.ack(i,epoch=1)
        sequence.append({'frame_id':i,'source_sha256':manifest['frame_sha256'][i],
                         'max_attempts':cfg.max_attempts,'base_controller_attempts':base_decision.attempts,**row})
    assert hashes=={str(p):digest(p) for p in sources},'source changed during benchmark'
    result={'evidence':'Actual bounded selective HP01/GH01 packets plus unchanged GM01 fallback; Python functional/timing evidence, no hardware or sustained FPS claim',
            'source_sha256':hashes,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'source_inputs':len(scenes),'records':len(scenes)*len(POLICIES),'scenes':scenes,'summary':summary(scenes),
            'policies':{label:{'rectangles':cfg.rectangles,'max_attempts':cfg.max_attempts,'frame_cap':cfg.frame_cap,'work_budget_ms':cfg.work_budget_ms} for label,cfg in POLICIES.items()},
            'temporal':{'manifest':manifest,'scope':'12 sequential native frames, acknowledged after decode. Predeclared i%3==1 max_attempts=0 exercises byte-identical GM01 fallback; all others max4. Same GM YUV anchor, no pacing, losses, reordering or transport.',
                        'frames':sequence,'GH01':sum(r.get('format')=='GH01' for r in sequence),'GM01':sum(r.get('format')=='GM01' for r in sequence)},
            'policy_scope':'Current same-frame RGB and actual base/patch lengths only; no future frames or quality oracle. Up to4 declared nonoverlap priorities, not verified real HUD locations. Compact area21120 is smaller than common broad47360; both coverage denominators and common broad metrics retained.',
            'timing_scope':'Uncontrolled host Python wall time. Same GM key and preparation measured once per source and charged to each independent policy. Full service charges base map/prepare + complete selector (base validation, all encoded/rejected patches, validation, assembly) + stateful decode/overlay. Capture/scaling/metrics/oracle/source decode excluded. 35ms is observed prepare-work fallback only, not a hard deadline or complete-frame deadline; work is never refunded.',
            'transport_accounting':'Accounting only: accepted forward=packet+59*ceil(packet/1024), reverse52 bytes/frame. No transmission or inference of actual throughput/FPS.',
            'deploy_scope':'Mixed GM01/GH01 experiment only. Existing GF01/MSV1/JPEG peers do not negotiate these formats. No ESP32/FPGA integration or hardware benchmark.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result['summary'],indent=2));print('temporal',result['temporal']['GH01'],result['temporal']['GM01'],flush=True)

if __name__=='__main__':main()
