#!/usr/bin/env python3
"""Actual HP01 versus adaptive row-run packets on identical declared UI crops."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import time
import numpy as np
import row_codec as rc

HERE=Path(__file__).resolve().parent
BROAD=((16,48,192,80),(160,352,400,80))
COMPACT=((22,54,160,24),(22,82,160,24),(168,360,320,24),(168,390,240,24))
CAP=49152


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


metrics=module('row_metrics',HERE.parent/'python-game-roi-study/benchmark.py')
flat=module('row_flat_fixtures',HERE.parent/'python-game-hud-study/flat_probe.py')


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def hash_bytes(x):return hashlib.sha256(x).hexdigest()
def elapsed(t):return (time.perf_counter_ns()-t)/1e6


def main():
    paths=[HERE/'row_codec.py',HERE/'benchmark.py',HERE/'test_row_codec.py',
           Path(rc.hp.__file__),Path(rc.hp.gm.__file__),Path(rc.hp.gm.ft.__file__),
           Path(rc.hp.gm.roi.__file__),Path(rc.hp.gm.mt.__file__),Path(rc.hp.gm.token_coeff.__file__),
           Path(rc.hp.gm.word_coeff.__file__),Path(rc.hp.gm.word_coeff.frozen_codec.__file__),
           Path(rc.hp.corpus.__file__),Path(metrics.__file__),Path(flat.__file__)]
    pins={str(p):sha(p) for p in paths}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    inputs=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=rc.hp.corpus.load_video(media/(clip+'.mp4'),max_frames=16,start_seconds=4)
        for i in (0,2,4,6,8,10,12,14):
            inputs.append((clip+'-frame'+str(i),frames[i],manifest,i,'real_precompressed'))
    for name,rgb in metrics.synthetic_fixtures():
        inputs.append((name,rgb,{'synthetic':True,'source':'synthetic:'+name},0,'synthetic_antialiased'))
    for colored in (False,True):
        inputs.append(('flat-colored' if colored else 'flat-monochrome',flat.fixture(colored),
                       {'synthetic':True,'source':'synthetic:flat-glyph-mask'},0,'synthetic_low_color'))
    cases=[]
    for name,rgb,manifest,index,kind in inputs:
        h,w=rgb.shape[:2];source_words=rc.hp.corpus.rgb565(rgb)
        enc=rc.hp.gm.Encoder();scale=rc.hp.gm.roi.declared_map(w,h,BROAD,8,16)
        t=time.perf_counter_ns();base=enc.prepare(rgb,0,scale_map=scale);base_ms=elapsed(t)
        expected=enc.expected_hash(0)
        control,info=rc.hp.gm.Receiver().receive(base)
        assert hash_bytes(control.tobytes())==expected
        profiles=[]
        for label,rectangles in (('broad',BROAD),('compact',COMPACT)):
            mask=metrics.roi_mask(w,h,rectangles)
            for method in ('hp01','adaptive_row'):
                t=time.perf_counter_ns();patches=[];details=[]
                for rect in rectangles:
                    if method=='hp01':
                        p=rc.hp.encode_patch(rgb,rect);detail={'chosen_format':'HP01','chosen_bytes':len(p)}
                    else:p,detail=rc.choose_patch(rgb,rect)
                    patches.append(p);details.append(detail)
                packet=rc.wrap(base,patches,w,h);search_ms=elapsed(t)
                receiver=rc.Receiver();t=time.perf_counter_ns();actual,meta=receiver.receive(packet);receive_ms=elapsed(t)
                words=rc.hp.corpus.rgb565(actual)
                mismatches=int(np.count_nonzero(words[mask]!=source_words[mask]));assert mismatches==0
                for a,b in zip(receiver.base._anchor,enc.pending[0]['planes']):np.testing.assert_array_equal(a,b)
                assert len(packet)==rc.FRAME.size+4+len(base)+sum(4+len(p) for p in patches)
                profiles.append({'region_set':label,'method':method,'rectangles':rectangles,'patches':details,
                    'packet_bytes':len(packet),'base_bytes':len(base),'patch_increment_bytes':len(packet)-len(base),
                    'packet_sha256':hash_bytes(packet),'display_rgb565_sha256':hash_bytes(words.astype('<u2').tobytes()),
                    'over_cap':len(packet)>CAP,'selected_region_pixels':int(mask.sum()),'rgb565_word_mismatches':mismatches,
                    'base_prepare_ms_reused':base_ms,'patch_search_and_wrapper_ms':search_ms,
                    'charged_prepare_sum_ms':base_ms+search_ms,'receive_ms':receive_ms,
                    'forward_ipv4_udp_bytes_accounting_only':len(packet)+59*((len(packet)+1023)//1024),
                    'installed_gf02_adapter_accepts_hg01':False})
        cases.append({'name':name,'source_kind':kind,'manifest':manifest,'source_index':index,
                      'rgb_sha256':hash_bytes(rgb.tobytes()),'base_packet_sha256':hash_bytes(base),
                      'profiles':profiles})
        print(name,[(r['region_set'],r['method'],r['packet_bytes'],r['over_cap']) for r in profiles],flush=True)
    summary={}
    for kind in ('real_precompressed','synthetic_antialiased','synthetic_low_color'):
        for region in ('broad','compact'):
            selected=[r for c in cases if c['source_kind']==kind for r in c['profiles'] if r['region_set']==region]
            out={}
            for method in ('hp01','adaptive_row'):
                rows=[r for r in selected if r['method']==method]
                out[method]={'frames':len(rows),'mean_packet_bytes':float(np.mean([r['packet_bytes'] for r in rows])),
                    'fit_frames':sum(not r['over_cap'] for r in rows),'hr01_patches':sum(p['chosen_format']=='HR01' for r in rows for p in r['patches']),
                    'mean_patch_search_ms':float(np.mean([r['patch_search_and_wrapper_ms'] for r in rows])),
                    'mean_charged_prepare_ms':float(np.mean([r['charged_prepare_sum_ms'] for r in rows])),
                    'mean_receive_ms':float(np.mean([r['receive_ms'] for r in rows]))}
            summary[kind+'/'+region]=out
    assert pins=={str(p):sha(p) for p in paths},'executed source changed'
    result={'scope':'Actual lossless RGB565 row-run/HP01 selection and HG01 wrapper. Offline keys, not live/native/RTL or30fps proof.',
        'source_sha256':pins,'versions':{'python':platform.python_version(),**{p:importlib.metadata.version(p) for p in ('numpy','Pillow','av')}},
        'cases':cases,'source_inputs':len(cases),'profile_records':sum(len(c['profiles']) for c in cases),'summary':summary,
        'cap':CAP,'policy':{'lookahead':0,'oracle_selection':False,'max_patch_candidates':4,'broad':BROAD,'compact':COMPACT},
        'timing_scope':'Base encode measured once perinput and reused across4profiles; chargedprepare sums that actualbase cost with each actualpatchsearch/wrap. Allrow/legacycandidate work included. No acquisition,transport, display ormetrics service. Hostload uncontrolled.',
        'format_scope':'HG01 new wrapper explicitlydispatchesHP01/HR01; frozenGH01 andGF02/GM01finite adapters do notaccept it. No patchtemporalcache. Displaypatches neveralterGM01YUVanchor.',
        'memory_scope':'Softwareboundedrows+up to256wordpalette; completepatch arrays/reference/framecopies allocatedonhost. No targetBRAM/DSP/SDRAMfit/bandwidthclaim.',
        'quality_scope':'Exact originalRGB565 words in allselectedcrops only; not losslessRGB888. Realrectangles aredeclared priorities, not recognizedorverifiedHUDs. Overcap frames decodedforalgorithmproof andcountedfailures, notadmitted.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
