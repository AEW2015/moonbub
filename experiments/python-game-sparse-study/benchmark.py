#!/usr/bin/env python3
"""Paired frozen versus zero/DC bypass decoder calls on identical720x480 bytes."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
import numpy as np
import fast_codec as f

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(a):return hashlib.sha256(a.tobytes()).hexdigest()
def elapsed(t):return (time.perf_counter_ns()-t)/1e6

def stats(values):
    return {'n':len(values),'mean':float(np.mean(values)),'p50':float(np.percentile(values,50)),
            'p95':float(np.percentile(values,95)),'max':max(values)}


def main():
    sources=[HERE/'fast_codec.py',HERE/'benchmark.py',HERE/'test_fast_codec.py',Path(f.gm.__file__),Path(corpus.__file__),
        Path(f.gm.roi.__file__),Path(f.gm.ft.__file__),Path(f.gm.mt.__file__),Path(f.gm.token_coeff.__file__),
        Path(f.gm.word_coeff.__file__),Path(f.gm.word_coeff.frozen_codec.__file__),Path(f.hybrid.__file__),
        Path(f.hybrid.row.__file__),Path(f.hybrid.hp.__file__)]
    pins={str(p):sha(p) for p in sources}
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')));cases=[]
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        enc=f.gm.Encoder();slow_gm=f.gm.Receiver();fast_gm=f.Receiver();slow_hg=f.hybrid.Decoder();fast_hg=f.HybridReceiver()
        m=f.gm.roi.declared_map(720,480,f.hybrid.BROAD,8,16);rows=[]
        for i,rgb in enumerate(frames):
            t=time.perf_counter_ns();base=enc.prepare(rgb,i,scale_map=m,force_key=(i%30==0));base_prepare_ms=elapsed(t)
            t=time.perf_counter_ns();selection=f.hybrid.select_frame(base,rgb,f.hybrid.Config());selection_ms=elapsed(t)
            assert selection.accepted
            outputs={};timings={}
            # Reverse paired order each input, and reverse first order in second clip.
            order=(('baseline',slow_gm),('fast',fast_gm)) if (i+(clip.endswith('2600')))%2==0 else (('fast',fast_gm),('baseline',slow_gm))
            for name,decoder in order:
                t=time.perf_counter_ns();actual,info=decoder.receive(base);timings['gm_'+name]=elapsed(t);outputs['gm_'+name]=(actual,info)
            order=(('baseline',slow_hg),('fast',fast_hg)) if (i+(clip.endswith('2600')))%2==0 else (('fast',fast_hg),('baseline',slow_hg))
            for name,decoder in order:
                t=time.perf_counter_ns();actual,info=decoder.receive(selection.packet);timings['hg_'+name]=elapsed(t);outputs['hg_'+name]=(actual,info)
            np.testing.assert_array_equal(outputs['gm_baseline'][0],outputs['gm_fast'][0])
            np.testing.assert_array_equal(outputs['hg_baseline'][0],outputs['hg_fast'][0])
            assert digest(outputs['gm_baseline'][0])==enc.expected_hash(i)
            for a,b in zip(slow_gm._anchor,fast_gm._anchor):np.testing.assert_array_equal(a,b)
            for a,b in zip(slow_hg.base._anchor,fast_hg.base._anchor):np.testing.assert_array_equal(a,b)
            words=corpus.rgb565(outputs['hg_fast'][0]);original=corpus.rgb565(rgb);errors=0
            for p in selection.selected:
                x,y,w,h=p['rect'];errors+=int(np.count_nonzero(words[y:y+h,x:x+w]!=original[y:y+h,x:x+w]))
            assert errors==0
            # Separate core reconstruction comparison: coefficient parse/preparation
            # is outside these two micro-timers, but included in full receiver above.
            parsed=f.gm.parse(base,1)
            if parsed['key']:prediction=tuple(np.full(shape,128,np.int16) for shape in ((480,720),(240,360),(240,360)))
            else:prediction=tuple(f.gm.mt.predict(enc._anchor,parsed['dx'],parsed['dy']))
            if i%2:
                t=time.perf_counter_ns();fast_planes,counts=f.reconstruct(parsed['coefficients'],prediction,m,720,480,return_stats=True);core_fast=elapsed(t)
                t=time.perf_counter_ns();baseline_planes=f.gm.reconstruct(parsed['coefficients'],prediction,m,720,480);core_baseline=elapsed(t)
            else:
                t=time.perf_counter_ns();baseline_planes=f.gm.reconstruct(parsed['coefficients'],prediction,m,720,480);core_baseline=elapsed(t)
                t=time.perf_counter_ns();fast_planes,counts=f.reconstruct(parsed['coefficients'],prediction,m,720,480,return_stats=True);core_fast=elapsed(t)
            for a,b in zip(fast_planes,baseline_planes):np.testing.assert_array_equal(a,b)
            rows.append({'id':i,'input_sha256':manifest['frame_sha256'][i],'key':parsed['key'],
                'gm_packet_bytes':len(base),'gm_packet_sha256':hashlib.sha256(base).hexdigest(),
                'hybrid_packet_bytes':len(selection.packet),'hybrid_packet_sha256':hashlib.sha256(selection.packet).hexdigest(),
                'baseline_gm_rgb_sha256':digest(outputs['gm_baseline'][0]),'fast_gm_rgb_sha256':digest(outputs['gm_fast'][0]),
                'baseline_hg_rgb_sha256':digest(outputs['hg_baseline'][0]),'fast_hg_rgb_sha256':digest(outputs['hg_fast'][0]),
                'baseline_reconstructed_yuv_sha256':[digest(a) for a in baseline_planes],
                'fast_reconstructed_yuv_sha256':[digest(a) for a in fast_planes],
                'all_pixels_and_yuv_exact':True,'selected_rgb565_mismatches':errors,'inverse_blocks':counts,
                'core_baseline_ms':core_baseline,'core_fast_ms':core_fast,'whole_receive_ms':timings,
                'base_prepare_ms':base_prepare_ms,'selection_ms':selection_ms,'map_construction_in_prepare_timer':False})
            enc.ack(i,epoch=1)
        summary={}
        for kind in ('key','p','all'):
            group=[r for r in rows if kind=='all' or r['key']==(kind=='key')]
            block={k:sum(p[k] for r in group for p in r['inverse_blocks']) for k in ('blocks','zero','dc_only','general_inverse','bypass_blocks')}
            summary[kind]={'frames':len(group),'block_counts':block,
                'core_baseline_ms':stats([r['core_baseline_ms'] for r in group]),'core_fast_ms':stats([r['core_fast_ms'] for r in group]),
                'receive_ms':{name:stats([r['whole_receive_ms'][name] for r in group]) for name in ('gm_baseline','gm_fast','hg_baseline','hg_fast')}}
        cases.append({'source':clip,'manifest':manifest,'rows':rows,'summary':summary})
        print(clip,{k:{'frames':v['frames'],'counts':v['block_counts'],'core_means':[v['core_baseline_ms']['mean'],v['core_fast_ms']['mean']],
            'gm_means':[v['receive_ms']['gm_baseline']['mean'],v['receive_ms']['gm_fast']['mean']],
            'hg_means':[v['receive_ms']['hg_baseline']['mean'],v['receive_ms']['hg_fast']['mean']]} for k,v in summary.items()},flush=True)
    assert pins=={str(p):sha(p) for p in sources}
    result={'evidence':'Bit-exactGM01/HG01zero/DCinversebypass+cachedquanttables, pairedsamebytes. Fullparse/decodepaid.',
        'source_sha256':pins,'versions':{'python':platform.python_version(),**{x:importlib.metadata.version(x) for x in ('numpy','Pillow','av')}},
        'cases':cases,'source_frames':120,'whole_decoder_calls':480,'core_reconstruction_calls':240,
        'scope':'Allcodedcanvases720x480atunchangedquantization. No newwireformat, rate reduction or targetdecoderthroughputclaim. Fastandbaselinepixel/YUVoutputsexact.',
        'timing_scope':'Per-packetwholeGM/HGreceiveincludesunchangedparse/CRC/entropy/prediction/color, newinversebypassandcachedtables. Verificationhash/arrays/metrics excluded. Coretimesexcludeparseandpredictionconstruction. Mapconstructionoutsidebasepreparetimers; prep/selectiononlycontext. Hostloaduncontrolled, alternatingAB/BAreceiverorder, nostatisticalrepeat/isolation.',
        'memory_scope':'Fullcoefficients/residual/outputarraysstillallocatedonhost. Bypass avoidsdensematrixwork, notproofBRAM/DSPfit or memorybandwidth. Pythoncachedtablesinitializedatimport; hotconstantsnotperframeconstruction.',
        'deployment_scope':'Wireformatcompatibleoracleonly; native/RTLimplementationsnotchanged. No finitefeedback/displayFPSmeasurement. Two relatedprecompressed25/29.88fpsclips, repeatedcontent, notnative30distinctcapture.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
