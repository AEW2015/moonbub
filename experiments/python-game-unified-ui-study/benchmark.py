#!/usr/bin/env python3
"""Paired cached/uncached unified UI plugin; no hidden base/wire/FPS claim."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import ui_plugin as ui

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus

BYTE_BUDGET=32768


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def ms(start):return (time.perf_counter_ns()-start)/1e6
def stats(values):
    return dict(n=len(values),mean=float(np.mean(values)),p50=float(np.percentile(values,50)),
                p95=float(np.percentile(values,95)),max=max(values)) if values else None


def dependencies():
    return sorted(set([HERE/name for name in ('ui_plugin.py','benchmark.py','test_unified_ui.py','verify.py')]
        + [Path(ui.frozen_cache.__file__),Path(ui.hybrid.__file__),Path(ui.row.__file__),Path(ui.hp.__file__),
           Path(ui.gm.__file__),Path(ui.gm.roi.__file__),Path(ui.gm.ft.__file__),Path(ui.gm.mt.__file__),
           Path(ui.gm.token_coeff.__file__),Path(ui.gm.word_coeff.__file__),
           Path(ui.gm.word_coeff.frozen_codec.__file__),Path(corpus.__file__)]))


def synthetic(name,n=12):
    yy,xx=np.indices((480,720));frames=[];rng=np.random.default_rng(1515)
    for i in range(n):
        rgb=np.stack(((xx//4+i*7)%256,(yy//3+i*5)%256,(xx//7+yy//9+i*3)%256),axis=-1).astype(np.uint8)
        for x,y,w,h in ui.COMPACT:
            if name=='moving-background-static-ui':
                rgb[y:y+h,x:x+w]=[24,40,56]
                rgb[y+4:y+8,x+6:x+w-6]=[240,244,248]
                rgb[y+12:y+16,x+6:x+w-6:3]=[160,180,200]
            else:
                rgb[y:y+h,x:x+w]=rng.integers(0,256,(h,w,3),dtype=np.uint8)
        frames.append(rgb)
    return frames,dict(source='synthetic:'+name,synthetic=True,frame_count=n,
                       frame_sha256=[digest(f) for f in frames],target_width=720,target_height=480,
                       active_rects=[(0,0,720,480)]*n)


def run_case(name,cohort,frames,manifest,index):
    selectors={'uncached':ui.PatchSelector(max_entries=0),'cached':ui.PatchSelector(max_entries=4)}
    base=np.full((480,720,3),[80,90,100],np.uint8)
    base_words=corpus.rgb565(base)
    rows=[];previous_source=None
    for i,rgb in enumerate(frames):
        source_hash=digest(rgb);assert source_hash==manifest['frame_sha256'][i]
        decisions={};selector_ms={};section_ms={};receive_ms={};sections={};outputs={}
        order=('uncached','cached') if (i+index)%2==0 else ('cached','uncached')
        for label in order:
            began=time.perf_counter_ns();d=selectors[label].select(rgb,BYTE_BUDGET);selector_ms[label]=ms(began)
            decisions[label]=d
            began=time.perf_counter_ns();sections[label]=ui.pack_patches(d.patches);section_ms[label]=ms(began)
            began=time.perf_counter_ns()
            validated=ui.parse_patches(sections[label],len(d.patches),720,480)
            outputs[label]=ui.apply_patches(base,validated);receive_ms[label]=ms(began)
        a,b=decisions['uncached'],decisions['cached']
        assert a.patches==b.patches and sections['uncached']==sections['cached']
        np.testing.assert_array_equal(outputs['uncached'],outputs['cached'])
        np.testing.assert_array_equal(base,np.full((480,720,3),[80,90,100],np.uint8))
        selected=[tuple(p['rect']) for p in b.details['selected']]
        outside=np.ones((480,720),bool);errors=0
        words=corpus.rgb565(outputs['cached']);original=corpus.rgb565(rgb)
        for x,y,w,h in selected:
            errors+=int(np.count_nonzero(words[y:y+h,x:x+w]!=original[y:y+h,x:x+w]))
            outside[y:y+h,x:x+w]=False
        unselected_errors=int(np.count_nonzero(words[outside]!=base_words[outside]))
        assert errors==unselected_errors==0
        rows.append(dict(id=i,input_sha256=source_hash,source_changed=previous_source is not None and source_hash!=previous_source,
                         byte_budget=BYTE_BUDGET,framed_ui_bytes=len(sections['cached']),selected_rectangles=selected,
                         selected_pixels=b.selected_pixels,selected_word_mismatches=errors,
                         unselected_base_word_mismatches=unselected_errors,
                         uncached_section_sha256=hashlib.sha256(sections['uncached']).hexdigest(),
                         cached_section_sha256=hashlib.sha256(sections['cached']).hexdigest(),
                         uncached_display_sha256=digest(outputs['uncached']),cached_display_sha256=digest(outputs['cached']),
                         selector_wall_ms=selector_ms,section_assembly_wall_ms=section_ms,ui_receive_wall_ms=receive_ms,
                         uncached=a.details,cached=b.details))
        previous_source=source_hash
    summary=dict(rows=len(rows),unique_source_hashes=len({r['input_sha256'] for r in rows}),
                 patch_attempts=sum(len(r['cached']['attempts']) for r in rows),
                 patch_hits=sum(a['candidate_details']['cache_hit'] for r in rows for a in r['cached']['attempts']),
                 hits_on_changed_whole_source=sum(a['candidate_details']['cache_hit'] for r in rows if r['source_changed'] for a in r['cached']['attempts']),
                 current_candidates_cached=sum(a['candidate_details']['current_candidate_count'] for r in rows for a in r['cached']['attempts']),
                 current_candidates_uncached=sum(a['candidate_details']['current_candidate_count'] for r in rows for a in r['uncached']['attempts']),
                 selected_pixels_mean=float(np.mean([r['selected_pixels'] for r in rows])),
                 framed_ui_bytes_mean=float(np.mean([r['framed_ui_bytes'] for r in rows])),
                 max_persistent_cache_bytes=max(r['cached']['persistent_cache_bytes'] for r in rows),
                 max_cache_entries=max(r['cached']['cache_entries'] for r in rows),
                 selector_wall_ms={label:stats([r['selector_wall_ms'][label] for r in rows]) for label in ('uncached','cached')},
                 ui_receive_wall_ms={label:stats([r['ui_receive_wall_ms'][label] for r in rows]) for label in ('uncached','cached')})
    return dict(source=name,cohort=cohort,manifest=manifest,rows=rows,summary=summary)


def main():
    paths=dependencies();pins={str(p):sha(p) for p in paths};cases=[];started=time.perf_counter()
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    sources=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        sources.append((clip+'-temporal','native_temporal',frames,manifest))
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=8,start_seconds=4)
        sources.append((clip+'-heldout','native_heldout',frames,manifest))
    for name in ('moving-background-static-ui','changing-noise-ui'):
        frames,manifest=synthetic(name);sources.append((name,'synthetic',frames,manifest))
    for index,(name,cohort,frames,manifest) in enumerate(sources):
        case=run_case(name,cohort,frames,manifest,index);cases.append(case)
        print(json.dumps(dict(source=name,summary=case['summary'])),flush=True)
    assert pins=={str(p):sha(p) for p in paths},'executed source changed'
    result=dict(evidence='Standalone unified exactUI plugin pairedcachecomparison; no completeAR02body or finiteFPS claim',
                source_sha256=pins,cases=cases,paired_ids=sum(len(c['rows']) for c in cases),case_count=len(cases),
                total_python_wall_seconds=time.perf_counter()-started,
                versions=dict(python=platform.python_version(),**{x:importlib.metadata.version(x) for x in ('numpy','Pillow','av')}),
                budget_scope='Declared32768UI-sectionbytes includes4lengthprefixes per admittedpatch. No basecodecbody/envelope/AF02/GF02orwirebytesare included.',
                timing_scope='PairedalternatingAB/BAselectincludeswordconversion,currentcachecompare/copy,actualcandidateencodes,per-patchvalidationandadmission. Sectionpackandfullparse/applyseparatelytimed. Sourcecapture/BOXload,baseRGBgeneration,hash/errorchecksoutside clocks. Hostloaduncontrolled.',
                quality_scope='EveryselectedwordexactoriginalRGB565; unselectedwords equal declaredbaseRGB565. Any nonemptyoverlayquantizeswholebasedisplaytoRGB565; no YUVreference or state altered.',
                memory_scope='FourpersistentUIword/payloadentriesonly; cachebytesexcludePythonmetadata,old/newtransientoverlap,decodedpatchwords,source/base/outputarraysandothercodecworkspaces. NotpeakmemoryorFPGAfit.',
                source_scope='Two relatedprecompressed25/29.88fps native clips plus labeledsyntheticcontrols. Allcoded720x480/nativeactive720x405; no live30distinctcapture or hardware rate proof.',
                integration_scope='Plugininterface supports newAR02core, butthisfilebenchmarks UI-selection/sectionparse only. Core/finite measurements elsewhere mustpaybase/wrapper/reference/transport/display costs.')
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
