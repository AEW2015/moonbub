#!/usr/bin/env python3
"""Causal sampled motion gate with fully coded controls at720x480."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import av
import numpy as np
import PIL
import motion_gate as g
r=g.r
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'python-codec-study'))
import corpus
spec=importlib.util.spec_from_file_location('rate_motion_quality',HERE.parent/'python-game-roi-study/benchmark.py')
quality=importlib.util.module_from_spec(spec);sys.modules[spec.name]=quality;spec.loader.exec_module(quality)
RECTS=((16,48,192,80),(160,352,400,80))
PROFILES={'gm_zero':('gm_zero',),'bm_block':('bm_block',),'actual_rate':('gm_zero','bm_block'),'gated_rate':None}
INDICES=(0,2,4,6,8,10,12,14)


def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):return sha(p.read_bytes())
def anchor_hash(planes):return None if planes is None else sha(b''.join(a.astype('<i2').tobytes() for a in planes))


def synthetic():
    rng=np.random.default_rng(1212);hh,ww=480,720
    texture=np.repeat(np.repeat(rng.integers(30,226,(30,45,3),dtype=np.uint8)//16*16,16,0),16,1)
    yy,xx=np.mgrid[:hh,:ww]
    moving=[]
    for i in range(8):
        shift=2*(i%3);dx=np.where(xx<ww//2,shift,-shift)
        moving.append(texture[yy,np.clip(xx+dx,0,ww-1)])
    return [('synthetic-static128',[np.full((hh,ww,3),128,np.uint8) for _ in range(4)]),
            ('synthetic-opposite-translation',moving),
            ('synthetic-noise-cut',[np.full((hh,ww,3),128,np.uint8),rng.integers(0,256,(hh,ww,3),dtype=np.uint8),
                rng.integers(0,256,(hh,ww,3),dtype=np.uint8),np.full((hh,ww,3),220,np.uint8),
                rng.integers(0,256,(hh,ww,3),dtype=np.uint8),np.full((hh,ww,3),128,np.uint8)])]


def run_scene(name,frames,manifest,indices,cohort,key_ids):
    byprofile={}
    for profile,modes in PROFILES.items():
        enc=g.Encoder() if profile=='gated_rate' else r.Encoder(modes=modes);rx=r.Decoder();rows=[]
        for source_index in indices:
            rgb=frames[source_index];assert rgb.shape==(480,720,3)
            frame=source_index;ref_hash=anchor_hash(enc._anchor)
            began=time.perf_counter_ns();scale=r.gm.roi.declared_map(720,480,RECTS,8,16)
            d=enc.prepare(rgb,frame,scale_map=scale,force_key=frame in key_ids)
            prepare_ms=(time.perf_counter_ns()-began)/1e6
            row={'frame_id':frame,'source_index':source_index,'source_rgb_sha256':sha(rgb.tobytes()),
                 'accepted':d.accepted,'selected_mode':d.selected_mode,'key':d.key,'reference_id':d.reference_id,
                 'canonical_reference_yuv_sha256':ref_hash,'attempts':d.attempts,'common_stages':d.common_stages,
                 'preview_ms':d.preview_ms,'commit_ms':d.commit_ms,'internal_service_ms':d.service_ms,'prepare_ms':prepare_ms,
                 'pending_after_prepare':len(enc.pending),'read_pins_after_prepare':enc.read_pins,
                 'minimum_candidate_bytes':min(a['bytes'] for a in d.attempts),
                 'packet_bytes':None if d.packet is None else len(d.packet),
                 'gate':enc.last_gate.copy() if profile=='gated_rate' else None,
                 'gate_included_in_prepare_timer':profile=='gated_rate'}
            if d.accepted:
                began=time.perf_counter_ns();actual,info=rx.receive(d.packet);receive_ms=(time.perf_counter_ns()-began)/1e6
                expected=enc.expected_hash(frame);assert sha(actual.tobytes())==expected
                assert enc.ack(frame,epoch=1,frame_crc=info['body_tag'])
                for a,b in zip(enc._anchor,rx._anchor):np.testing.assert_array_equal(a,b)
                row.update(packet_sha256=sha(d.packet),decoded_rgb_sha256=expected,receive_ms=receive_ms,
                    full_service_ms=prepare_ms+receive_ms,codec=info['codec'],inner_bytes=info['inner_bytes'],
                    outer_header_crc_bytes=r.HEADER.size+4,body_tag=info['body_tag'],anchor_id=rx.anchor_id,
                    vector_bytes=info['vector_bytes'],zero_residual=info['zero_residual'],
                    metrics=quality.metric(rgb,actual,RECTS,tuple(manifest['active_rects'][source_index]),False),
                    forward_size_accounting=len(d.packet)+59*math.ceil(len(d.packet)/1024),reverse_size_accounting=52)
            else:
                assert not enc.pending
                assert all(a['bytes']>49152 for a in d.attempts)
                assert anchor_hash(enc._anchor)==ref_hash
            row['pending_after_feedback']=len(enc.pending);rows.append(row)
        assert not enc.pending;byprofile[profile]=rows
    # Independent controls and selector must really encode identical candidates
    # against the same committed key, not just report matching source IDs.
    comparisons=[]
    for i,index in enumerate(indices):
        gm=byprofile['gm_zero'][i];bm=byprofile['bm_block'][i];selected=byprofile['actual_rate'][i]
        assert gm['canonical_reference_yuv_sha256']==bm['canonical_reference_yuv_sha256']==selected['canonical_reference_yuv_sha256']
        assert gm['key']==bm['key']==selected['key'] and gm['reference_id']==bm['reference_id']==selected['reference_id']
        for control,mode in ((gm,'gm_zero'),(bm,'bm_block')):
            candidate=next(a for a in selected['attempts'] if a['mode']==mode)
            assert control['attempts'][0]['packet_sha256']==candidate['packet_sha256']
            assert control['attempts'][0]['bytes']==candidate['bytes']
        assert selected['minimum_candidate_bytes']==min(gm['minimum_candidate_bytes'],bm['minimum_candidate_bytes'])
        entry={'frame_id':index,'same_canonical_reference':True,'candidate_packets_match_controls':True,
               'gm_bytes':gm['minimum_candidate_bytes'],'bm_bytes':bm['minimum_candidate_bytes'],
               'selected_bytes':selected['packet_bytes'],'accepted':selected['accepted']}
        if selected['accepted']:
            entry.update(active_mse=selected['metrics']['active']['mse'],
                         gm_active_mse=None if not gm['accepted'] else gm['metrics']['active']['mse'],
                         bm_active_mse=None if not bm['accepted'] else bm['metrics']['active']['mse'])
        gated=byprofile['gated_rate'][i]
        assert gated['canonical_reference_yuv_sha256']==gm['canonical_reference_yuv_sha256']
        assert gated['key']==gm['key'] and gated['reference_id']==gm['reference_id']
        for candidate in gated['attempts']:
            control=gm if candidate['mode']=='gm_zero' else bm
            assert candidate['packet_sha256']==control['attempts'][0]['packet_sha256']
        assert len(gated['attempts'])==(2 if gated['gate']['allow_block'] else 1)
        entry.update(gate_allowed_block=gated['gate']['allow_block'], gated_bytes=gated['packet_bytes'],
                     gate_candidates_match_controls=True, gated_prepare_ms=gated['prepare_ms'],
                     gated_active_mse=gated.get('metrics',{}).get('active',{}).get('mse'))
        comparisons.append(entry)
    scene={'name':name,'cohort':cohort,'manifest':manifest,'indices':indices,'key_ids':key_ids,'profiles':byprofile,'comparisons':comparisons}
    scene['summary']=summarize(scene);return scene


def summarize(scene):
    result={}
    for profile,rows in scene['profiles'].items():
        accepted=[row for row in rows if row['accepted']]
        out={'source_ids':len(rows),'admitted':len(accepted),'cap_rejections':len(rows)-len(accepted),
             'attempted_candidates':sum(len(row['attempts']) for row in rows),
             'selected_modes':{mode:sum(row['selected_mode']==mode for row in accepted) for mode in ('gm_zero','bm_block')},
             'mean_prepare_ms_all':float(np.mean([row['prepare_ms'] for row in rows])),
             'p95_prepare_ms_all':float(np.percentile([row['prepare_ms'] for row in rows],95)),
             'rejected_prepare_sum_ms':sum(row['prepare_ms'] for row in rows if not row['accepted']),
             'mean_minimum_candidate_bytes_all':float(np.mean([row['minimum_candidate_bytes'] for row in rows]))}
        if accepted:
            out.update(mean_packet_bytes=float(np.mean([row['packet_bytes'] for row in accepted])),max_packet_bytes=max(row['packet_bytes'] for row in accepted),
                mean_receive_ms=float(np.mean([row['receive_ms'] for row in accepted])),
                mean_full_service_ms=float(np.mean([row['full_service_ms'] for row in accepted])),
                vector_bytes_mean=float(np.mean([row['vector_bytes'] for row in accepted])),
                forward_mbps_if30=sum(row['forward_size_accounting'] for row in accepted)/len(accepted)*8*30/1e6,
                zero_residual_frames=sum(row['zero_residual'] for row in accepted))
            regions={}
            for region in ('active','roi','background'):
                pixels=sum(row['metrics'][region]['pixels'] for row in accepted)
                mse=sum(row['metrics'][region]['pixels']*row['metrics'][region]['mse'] for row in accepted)/pixels
                regions[region]={'mse':mse,'psnr':None if mse==0 else 10*math.log10(65025/mse),'pixels':pixels}
            out['regions']=regions
        if profile=='gated_rate':
            out.update(gate_allows=sum(row['gate']['allow_block'] for row in rows),
                       gate_comparisons=sum(row['gate']['comparisons'] for row in rows),
                       gate_ms_sum=sum(row['gate']['gate_ms'] for row in rows),
                       gate_mean_ms=float(np.mean([row['gate']['gate_ms'] for row in rows])),
                       full_block_searches=sum(a['mode']=='bm_block' and not row['key'] for row in rows for a in row['attempts']))
        result[profile]=out
    return result


def main():
    media=Path(os.environ.get('GAMEBUB_MEDIA_DIR',str(HERE.parents[3]/'media')))
    paths=[HERE/'motion_gate.py',HERE/'test_motion_gate.py',HERE/'benchmark.py',Path(r.__file__),Path(r.bm.__file__),Path(r.gm.__file__),
           Path(r.gm.ft.__file__),Path(r.gm.roi.__file__),Path(r.gm.mt.__file__),Path(r.gm.token_coeff.__file__),
           Path(r.gm.word_coeff.__file__),Path(r.gm.word_coeff.frozen_codec.__file__),Path(corpus.__file__),Path(quality.__file__)]
    pins={str(p):digest(p) for p in paths};scenes=[];start=time.perf_counter()
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=60,start_seconds=1)
        assert len(frames)==60
        scene=run_scene(clip,frames,manifest,tuple(range(60)),'temporal_real',(0,30));scenes.append(scene)
        print(clip,json.dumps(scene['summary']),flush=True)
    for clip in ('mass-effect-combat','mass-effect-2600'):
        frames,manifest=corpus.load_video(media/(clip+'.mp4'),max_frames=16,start_seconds=4)
        scene=run_scene(clip+'-heldout',frames,manifest,INDICES,'heldout_real',(0,));scenes.append(scene)
        print(scene['name'],json.dumps(scene['summary']),flush=True)
    for name,frames in synthetic():
        manifest={'source':'synthetic:'+name,'synthetic':True,'seed':1212,'frame_sha256':[sha(a.tobytes()) for a in frames],
                  'active_rects':[(0,0,720,480)]*len(frames),'scope':'Full720x480 artificial fixture, not realgame evidence'}
        scene=run_scene(name,frames,manifest,tuple(range(len(frames))),'synthetic',(0,));scenes.append(scene)
        print(name,json.dumps(scene['summary']),flush=True)
    assert pins=={str(p):digest(p) for p in paths},'source changed during gate benchmark'
    result={'evidence':'Actual causal four-corner motion screen before optional RM01 GM/BM rate choice, same ACKed key, all gate and candidate work charged; no hardware/FPS proof',
            'source_sha256':pins,'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'pyav':av.__version__},
            'scenes':scenes,'source_ids':sum(len(s['indices']) for s in scenes),'decisions':sum(len(rows) for s in scenes for rows in s['profiles'].values()),
            'wall_seconds':time.perf_counter()-start,
            'policy':{'profiles':PROFILES,'rectangles':RECTS,'frame_cap':49152,'selection':'gated arm: source/ACKkey four-corner luma screen enablesoptionalBM; actualattemptminimumbytes with declaredorderties; controlsGM/BM/dual'
                      ,'gate_config':g.Config().__dict__,
                      'default_modes':['gm_zero'],'optional_motion_modes':['gm_zero','bm_block'],'gm_global':'optional unit-tested mode, omitted in paired benchmark because v11 real controls chose zero; not silently estimated free',
                      'key_reference':'single reconstructed ACKed immutable key; only selected candidate consumes credit; no shadow encoders',
                      'feedback':'immediate matching outerepoch/frame/body-tag ACK after full decode/oraclecheck; no paced transport or benchmark faults',
                      'future_frames':0,'quality_oracle_for_selection':False},
            'timing_scope':'All actual screen,map,sourceconversion,search,prediction,transform,quantization,entropy,envelope/hash andcommit work charged. Fourcorner gate resamples currentluma separatelyanddoesnotshare laterfullsourceconversion; botharepaid. Sourceconversion/map shared once per preview. Keys have identical128prediction; key transform,entropy and one actualreconstruction shared and chargedonce, with count/stages explicit. Every losingP search/transform/entropy stillruns. Receive independently parses/reconstructs. Source decode/scale, quality, expectedP oracle,comparisonverification,transport/display excluded. Hostload uncontrolled,fixedprofileorder.',
            'comparison_scope':'All controls use sameRM01envelope overhead30B and same720x480source/map/keyIDs. Every coded ratecandidate andgatedcandidate musthash-identicallymatch its independent single-modecontrol againstsamecanonicalkey. Gatecanmissusefulmotion; byteoptimalitynotclaimedforunsearchedBM. Lowerbytesselection isnot rate-distortionoptimization; actual regionalerror retained.',
            'resolution_scope':'PRIMARY720x480target30fpspreserved. No reducedresolution/fpscases. Two60native windows from1s; heldoutcausalindices0,2,...14 from4s eachclip; static/opposite-motion/noise-cut fixtures all720x480. Relatedprecompressed25/29.88fpscontent isnotnative30distinctframe capture.',
            'ownership_scope':'At most2P credits/readpinslogical. Newkeyrequiresdrain. WrongACKsession/tag or expiredkey cannotinstall. No physicalDMA/CDC/read-drain implementation; Pythoncandidate/prediction/coeff/source/referencecopies extra.',
            'format_scope':'RM01 new experimental mixedGM01/BM01profile; envelopeouterCRC binds innercodec,epoch/frame/reference/canvas. Not GF02/GA01 adapter, firmware, standardHEVC/AV1orHDL integration.',
            'transport_scope':'Forward packet+59per1024Bchunk and reverse52B are accountingonly;30fpsfield isbyte-rate arithmetic, no schedule/executed network.'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')

if __name__=='__main__':main()
