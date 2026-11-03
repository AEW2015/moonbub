#!/usr/bin/env python3
"""Verify v10 frozen software evidence without rerunning timed campaigns."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parent.parent


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel):return json.loads((ROOT/rel).read_text())

def resolve(path):
    marker='/moonbub-30fps-study/'
    return ROOT/path.split(marker,1)[1] if marker in path else Path(path)


def main():
    snapshot=load('docs/prototype-v10-provenance.json')
    for rel,expected in snapshot['file_sha256'].items():
        assert sha(ROOT/rel)==expected,('snapshot',rel)
    bindings=0
    for rel in snapshot['run_artifacts']:
        data=load(rel)
        for path,expected in data.get('source_sha256',{}).items():
            assert sha(resolve(path))==expected,('executed source',rel,path)
            bindings+=1
    tests=0
    for rel,count in snapshot['test_counts'].items():
        log=(ROOT/rel/'tests.log').read_text();m=re.search(r'^Ran (\d+) tests? in ',log,re.M)
        assert m and int(m[1])==count and log.rstrip().endswith('OK'),rel
        tests+=count
    checks={}
    for folder,script in (('python-game-selective-study','verify.py'),('python-game-row-study','verify.py'),
                          ('python-game-service-study','check_stored_results.py'),('python-game-standard-study','verify.py')):
        p=subprocess.run([sys.executable,str(ROOT/'experiments'/folder/script)],check=True,capture_output=True,text=True)
        checks[folder]='passed'
    audit=load('experiments/python-game-audit-v10-study/audit.json')
    assert audit['source_pins_match_before_and_after']
    assert audit['external_media_hash_guard_match_before_and_after']
    assert not audit['inputs_missing'] and not audit['evidence_gaps']
    for row in audit['source_pins_before']['rows']:
        assert row['matches'] and sha(resolve(row['path']))==row['expected'],row['path']
    assert len(audit['source_pins_before']['rows'])==31
    assert audit['row_rle']['all_candidate_bytes_choose_minimum']
    assert audit['row_rle']['all_rederived_means_and_fit_counts_match_stored']
    assert audit['service']['all_model_cpu_queues_drained']
    accounting=audit['accounting']
    assert accounting['standard_campaign_decoded_rows']==1080
    assert accounting['common_color_new_native_codec_outputs']==720
    assert accounting['common_color_reused_gm_rows_not_new_decodes']==360
    assert accounting['total_unique_codec_output_rows_across_campaigns']==1800
    assert accounting['separate_color_floor_conversion_rows']==240
    common=load('experiments/python-game-standard-study/common-color-results.json')
    pairs=[]
    for clip,profiles in (('mass-effect-combat',('libx265_q36','libsvtav1_q48')),
                          ('mass-effect-2600',('libx265_q28','libsvtav1_q38'))):
        base=next(c for c in common['cases'] if c['source']==clip and c['profile']=='gm_roi8bg16')['summary']
        for profile in profiles:
            s=next(c for c in common['cases'] if c['source']==clip and c['profile']==profile)['summary']
            assert s['pooled']['active']['psnr']>base['pooled']['active']['psnr']
            assert s['pooled']['roi']['psnr']>base['pooled']['roi']['psnr']
            ratio=base['coded_bytes']/s['coded_bytes'];assert 10<ratio<24
            pairs.append({'source':clip,'profile':profile,'gm_to_native_coded_byte_ratio':ratio})
    missing=[]
    for path,expected in snapshot['input_sha256'].items():
        if Path(path).exists():assert sha(Path(path))==expected,('external input',path)
        else:missing.append(path)
    print(json.dumps({'snapshot_files':len(snapshot['file_sha256']),'executed_source_bindings':bindings,
        'passing_tests':tests,'stored_evidence_helpers':checks,'independent_unique_source_pins':31,
        'selective_decisions':60,'temporal_mixed_format_frames':12,'row_wrapper_decodes':80,
        'service_cases':8,'service_hash_checked_decodes':333,'common_color_operating_point_comparisons':pairs,
        'actual_codec_outputs_across_standard_campaigns':1800,'reused_gm_rows_not_double_counted':360,
        'separate_color_conversion_probe_outputs':240,'missing_external_inputs':missing,
        'scope':'Frozen software evidence checks; no live network, target decoder or30fps hardware qualification'},indent=2))


if __name__=='__main__':main()
