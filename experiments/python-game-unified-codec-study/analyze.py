#!/usr/bin/env python3
"""Untimed retained cross-profile exactness and publication-tag analysis."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    path=HERE/'results.json';result=json.loads(path.read_text());scenes=[];count=stores=0
    for scene in result['scenes']:
        if scene['cohort'] not in ('native_temporal','native_heldout_temporal'):continue
        left,right=scene['profiles']['gm'],scene['profiles']['exact']
        assert len(left)==len(right)==scene['manifest']['frame_count']
        publications=[]
        for index,(a,b) in enumerate(zip(left,right)):
            assert a['id']==b['id']==index and a['input_sha256']==b['input_sha256']
            assert a['accepted'] and b['accepted']
            assert (a['reference_bank'],a['reference_id'],a['reference_tag'])==(b['reference_bank'],b['reference_id'],b['reference_tag'])
            assert a['decoded_rgb_sha256']==b['decoded_rgb_sha256'] and a['base_rgb_sha256']==b['base_rgb_sha256']
            assert a['max_yuv_delta_same_reference_gm']==b['max_yuv_delta_same_reference_gm']==0
            assert a['metrics']==b['metrics']
            assert b['packet_bytes']<=a['packet_bytes']
            if a['attempted_key'] or a['promoted']:
                # Every stored native frame has a following P consumer. The
                # source ID/bank/tag proves which canonical YUV publication was
                # subsequently selected, not a hash inferred from display RGB.
                assert index+1<len(left)
                next_a,next_b=left[index+1],right[index+1]
                bank=0 if a['attempted_key'] else 1
                assert (next_a['reference_bank'],next_a['reference_id'])==(bank,index)
                assert (next_b['reference_bank'],next_b['reference_id'])==(bank,index)
                assert next_a['reference_tag']==next_b['reference_tag']!='00'*16
                publications.append(dict(stored_id=index,bank=bank,consumer_id=index+1,canonical_yuv_tag=next_a['reference_tag']))
        count+=len(left);stores+=len(publications)
        scenes.append(dict(name=scene['name'],matched_ids=[r['id'] for r in left],source_hashes_identical=True,
            display_rgb_hashes_exact=True,base_rgb_hashes_exact=True,selected_reference_ids_and_tags_exact=True,
            all_source_quality_metrics_exact=True,stored_tag_observations=publications,
            gm_mean_bytes=sum(r['packet_bytes'] for r in left)/len(left),
            selected_exact_mean_bytes=sum(r['packet_bytes'] for r in right)/len(right),
            raw_gm_fallbacks=sum(r['inner_codec']=='GM01' for r in right)))
    assert count==300 and stores==45
    out=dict(results_sha256=sha(path),analysis_sha256=sha(Path(__file__)),source_ids=300,
        stored_canonical_yuv_tag_observations=45,scenes=scenes,
        scope='Retained native base-only GM/exact controls under identical fixed key/promotion histories. All300RGBhashesandpriorreferenceIDs/tagsagree; all45storedYUVtagsobservedasnextPsource. Supplemental unit checks actual cross-profile YUV arrays. UI/prune/finitehistory claims excluded.')
    target=HERE/'matched-exact.json'
    if args.check:
        assert json.loads(target.read_text())==out
        print('PASS:300nativeGM/exactsame-source/reference/RGB/quality rows;45canonicalYUVpublicationtagsobservedasnextP;GMfallbacknonregression')
    else:
        target.write_text(json.dumps(out,indent=2)+'\n')
        print('WROTE matched-exact.json for300nativeexactpairsand45observedYUVpublicationtags')


if __name__=='__main__':main()
