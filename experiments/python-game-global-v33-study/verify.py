"""Independent retained packet/causal/metric/choice/paid-work replay for v33."""
from pathlib import Path
import json
import math
import numpy as np
import benchmark as b
from controller import select_tier,complete_cases,SCENES
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
m,p,n=b.m,b.p,b.n
def quiet_mask(source,reference):
    costs=np.zeros((15,23),np.int64);counts=np.zeros_like(costs)
    for plane,(s,r) in enumerate(zip(source,reference)):
        bs,weight=(32,1) if plane==0 else (16,2)
        for y in range(0,s.shape[0],4):
            for x in range(0,s.shape[1],4):
                costs[y//bs,x//bs]+=weight*abs(int(s[y,x])-int(r[y,x]));counts[y//bs,x//bs]+=weight
    return costs<=2*counts

def main():
    data=json.loads((HERE/'results.json').read_text());assert data['schema']=='gamebub-global-v33'
    complete_cases(data['cases'])
    for path,h in data['source_sha256'].items():
        q=Path(path);assert not q.is_absolute() and '..' not in q.parts;assert b.sha(ROOT/q)==h,path
    inputs=b.b.load(n.V24/'results.json')['inputs'];prior=b.b.load(HERE.parent/'python-game-controller-v32-study/results.json')['cases']
    pairs=trials=words=controls=search_frames=0
    for case in data['cases']:
        inp=next(v for v in inputs if v['scene']==case['scene'])
        old=next(v for v in prior if v['scene']==case['scene'] and v['policy']=='band_control')
        assert [r['id'] for r in inp['rows']]==list(range(48))
        rx=p.Receiver(epoch=25);ref=None;refid=m.NO_REF;slot=0
        for row,src,oldrow in zip(case['rows'],inp['rows'],old['rows'],strict=True):
            fid=row['id'];key=fid%24==0
            if key:ref=None;refid=m.NO_REF;slot=0
            tag=m.base.ZERO_TAG.hex() if key else m.C.reference_tag(ref).hex()
            assert row['key']==key and row['reference_id']==refid and row['reference_tag']==tag
            assert row['source_common_yuv_sha256']==src['common_yuv420_u8_sha256']
            assert row['source_slot']==(p.NO_SLOT if key else slot) and row['destination_slot']==(0 if key else 1-slot)
            source,original=n.source(src),n.original(src);quiet=None;vectors=None
            if not key:
                quiet=quiet_mask(source,ref);search=row['analyses']['half32']['search']
                assert search['quiet_blocks']==int(quiet.sum()) and search['active_blocks']==int((~quiet).sum())
                if case['policy']!='band_control':
                    vectors,work=b.camera.estimate(source,ref,32,case['policy'],n.ROIS)
                    assert work==search
                    assert work['candidate_vectors']==len(work['score_calls'])
                    assert work['sad_sample_operations']==sum(c['samples'] for c in work['score_calls'])
                    assert work['reference_sample_fetches']==sum(c['reference_gathers'] for c in work['score_calls'])
                    assert not np.any(vectors[quiet])
                    if case['policy']=='global_grid':assert not np.any(vectors%4)
                    search_frames+=1
            kinds=['zero'] if key else ['zero','half32'];winner=None
            backgrounds=sorted({a['background'] for a in row['attempts']})
            assert backgrounds in ([16],[16,32])
            for bg in backgrounds:
                group=[a for a in row['attempts'] if a['background']==bg]
                assert [a['kind'] for a in group]==kinds+[k+'_band' for k in kinds]
                before=[(a['cap_fit'],a['quality_eligible']) for a in group]
                chosen,shadow=select_tier(group)
                assert before==[(a['cap_fit'],a['quality_eligible']) for a in group]
                if chosen is not None:
                    assert winner is None;winner=chosen
                    assert bg==backgrounds[-1] and row['baseline_kind']==shadow['kind']
                    assert row['baseline_complete_bytes']==shadow['complete_bytes']
                    assert row['baseline_source_sse']==shadow['hybrid']['active_squared_error']
            assert winner is not None and [a for a in row['attempts'] if a['selected']]==[winner]
            for attempt in row['attempts']:
                base,pair=b.raw(attempt['base_packet']),b.raw(attempt['packet'])
                assert len(base)==attempt['base_bytes'] and len(pair)==attempt['complete_bytes']==len(base)+row['hud_bytes']+60
                decoded,meta=m.decode(base,ref,expected_epoch=25,expected_reference_id=None if key else refid)
                assert meta['reference_tag'].hex()==tag and meta['reconstructed_tag'].hex()==attempt['reconstructed_tag']
                np.testing.assert_array_equal(meta['scale_map'],m.roi.declared_map(720,480,n.ROIS,8,attempt['background']))
                if attempt['kind'].startswith('zero'):assert not np.any(meta['vectors'])
                elif vectors is not None:np.testing.assert_array_equal(meta['vectors'],vectors)
                elif quiet is not None:assert not np.any(meta['vectors'][quiet])
                hybrid=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),tuple(original[y:y+h,x:x+w] for x,y,w,h in n.RECTS))
                assert n.metric(original,hybrid)==attempt['hybrid'] and n.digest(hybrid)==attempt['hybrid_rgb565_sha256']
                reads=0 if key else m.taps.predict_with_info(ref,meta['vectors'],32)[1]['reference_sample_fetches']
                assert attempt['work']['decoder_reference_sample_reads']==reads
                trials+=1
            pair=b.raw(row['packet']);decoded,patches,ack=rx.receive(pair);p.validate_ack(ack,pair)
            assert ack==b.raw(row['ack']) and pair==b.raw(winner['packet'])
            assert row['body_bytes']==len(pair)<=49152 and row['base_bytes']==winner['base_bytes']
            assert row['hybrid']==winner['hybrid'] and row['selected_kind']==winner['kind'] and row['selected_background']==winner['background']
            for patch,(x,y,w,h) in zip(patches,n.RECTS,strict=True):np.testing.assert_array_equal(patch['words'],original[y:y+h,x:x+w])
            hybrid=n.overlay(m.C.corpus.rgb565(m.ft.planes_to_rgb(decoded)),tuple(v['words'] for v in patches))
            assert n.metric(original,hybrid)==row['hybrid'] and n.digest(hybrid)==row['hybrid_rgb565_sha256']
            paid=sum(v['analysis_wall_ms'] for v in row['analyses'].values())+sum(v['encode_ms'] for v in row['attempts'])
            service=paid+sum(v['quality_ms']+v['bind_ms'] for v in row['attempts'])
            assert math.isclose(paid,row['paid_base_encode_ms'],abs_tol=1e-9)
            assert math.isclose(service,row['base_policy_service_ms'],abs_tol=1e-9)
            if case['policy']=='band_control':
                folder=HERE.parent/'python-game-controller-v32-study'
                assert pair==b.raw(oldrow['packet'],folder) and ack==b.raw(oldrow['ack'],folder) and row['hybrid']==oldrow['hybrid'];controls+=1
            words+=21120;pairs+=1;ref,refid,slot=decoded,fid,row['destination_slot']
        assert b.summarize(case['rows'])==case['summary']
    assert pairs==288 and words==6082560 and controls==96 and search_frames==184
    print(json.dumps(dict(accepted_frames=pairs,candidate_attempts=trials,exact_hud_words=words,exact_v32_controls=controls,
                         causal_fast_search_frames=search_frames,source_pins=len(data['source_sha256']),
                         physical_30fps_proven=False,GM27_wire_unchanged=True)))
if __name__=='__main__':main()
