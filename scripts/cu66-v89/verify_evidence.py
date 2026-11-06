#!/usr/bin/env python3
"""Bind actual Rice observations, selected joined DAGs and separate constants."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v89'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-summary',action='store_true');args=parser.parse_args()
    bindings={}
    def local(name):
        p=(ROOT/name).resolve();p.relative_to(ROOT);return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(name):
        p=local(name);bindings[str(p.relative_to(ROOT))]=sha(p);return json.loads(p.read_text())
    def pins(values):
        for name,digest in values.items():
            p=local(name);assert sha(p)==digest,('pin mismatch',name);bindings[str(p.relative_to(ROOT))]=digest
    def selected(name):
        d=read(name);s=read(d['selected_report']);assert d==dict(s,selected_report=d['selected_report']);return d
    prefix='experiments/python-gamebub-v89/'
    obs=read(prefix+'observations/index.json');assert obs['record_count']==obs['native_sources']==457
    pins(obs['source_sha256'])
    p=AREA/'observations'/obs['data']['path'];assert sha(p)==obs['data']['gzip_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    om=read(prefix+'observations/artifact-manifest.json');pins(om['files_sha256'])
    ov=read(prefix+'observations/verification.json')
    assert ov['status']=='PASS_ACTUAL_BR_AND_ALL_MIXED_POLICY_TOTALS'
    assert (ov['native_sources'],ov['chunks'],ov['mixed_policy_records'],ov['public_interface_records'])==(457,1371,2285,16)
    pins(ov['source_sha256'])
    p=AREA/'observations/mixed-totals.jsonl';assert sha(p)==ov['mixed_totals_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    ot=read(prefix+'observations/tests.json')
    assert ot['status']=='PASS_NATIVE_LOOKAHEAD_RAW_AND_PRIMITIVE_COUNTS' and ot['checks_count']==18
    assert all(c['observed_exit_code']==0 for c in ot['commands']);pins(ot['source_sha256'])
    joint=selected(prefix+'joint/results.json');assert joint['status']=='PASS_SELECTED_ACTUAL_JOINT_SCHEDULES'
    assert (joint['unique_sources'],joint['schedules'],len(joint['frozen_CS86_control_matches']))==(4,64,10)
    pins(joint['source_sha256'])
    for name,digest in joint['artifacts_sha256'].items():
        p=local(joint['selected_report']).parent/name;assert sha(p)==digest;bindings[str(p.relative_to(ROOT))]=digest
    jm=read(prefix+'joint/artifact-manifest.json');pins(jm['files_sha256'])
    jv=read(prefix+'joint/verification.json')
    assert jv['status']=='PASS_ACTUAL_WORK_ROWS_AND_RETAINED_DAGS'
    assert (jv['unique_sources'],jv['schedules'],jv['actual_mixed_observations'],jv['frozen_CS86_control_matches'],jv['independent_retained_witnesses'])==(4,64,16,10,15)
    pins(jv['evidence_sha256'])
    jt=read(prefix+'joint/tests.json');assert jt['status']=='PASS' and len(jt['checks'])==6;pins(jt['source_sha256'])
    ja=read(prefix+'joint/joint-audit.json');assert ja['status']=='PASS' and (ja['rows'],ja['sources'])==(64,4)
    assert ja['selected_report']==joint['selected_report']
    constants=selected(prefix+'constants/results.json')
    assert constants['status']=='PASS_FIXED_PROFILE_CONSTANT_AND_NATIVE_CONTENT' and constants['native_sources']==457
    pins(constants['source_sha256'])
    p=local(constants['selected_report']).with_name('frames.jsonl');assert sha(p)==constants['frames_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    for item in constants['selected_traces']:
        p=local(item['path']);assert sha(p)==item['sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    ct=read(prefix+'constants/tests.json')
    assert ct['status']=='PASS_PROFILE_SENTINEL_AND_LEASE_CONTRACT' and ct['checks_count']==len(ct['checks'])==20 and ct['symbolic_updates']==1024
    pins(ct['source_sha256'])
    ca=read(prefix+'constants/constants-audit.json');assert ca['status']=='PASS' and ca['rows']==457
    assert ca['selected_report']==constants['selected_report']
    report=dict(schema='cu66-v89-combined-evidence-v1',status='PASS_ACTUAL_OBSERVATIONS_JOINED_SCHEDULES_AND_FIXED_CONSTANTS',
                native_observation_sources=457,native_BR88_chunks=1371,native_coefficient_values=86444480,
                mixed_policy_observation_records=2285,attribution_tests=18,selected_joint_sources=4,selected_joint_schedules=64,
                unchanged_frozen_control_matches=10,independent_retained_DAGs=15,joint_synthetic_tests=6,
                constant_native_sources=457,constant_contract_checks=20,constant_symbolic_updates=1024,
                joint_summaries=joint['summaries'],paired_policy_checks=ja['paired_vs_AB38'],constant_summaries=constants['summaries'],
                actual_observation_totals=obs['totals'],evidence_sha256=bindings,verifier_sha256=sha(Path(__file__)),
                physical_30fps_proven=False,validated_full_under10ms_proven=False,esp32_simulated=False,
                scope=['Existing CS88 bytes and quantized picture unchanged. Observations are actual decoder primitive counts, not clocks.',
                       'Joined conditional timing covers four selected sources with hypothetical parser/stage/service costs, not all457 or physical hardware.',
                       'Constant sentinel traffic is a separate fixed-profile experiment and is not included in joined timing.',
                       'One walkthrough family in four reset histories. Multiple policies/replays do not add distinct gameplay coverage.',
                       'HUD semantics, physical ports/controller, continuous display and ESP32 transport remain unqualified.'])
    dest=AREA/'summary.json'
    if args.verify_summary:assert json.loads(dest.read_text())==report,'summary differs'
    else:
        assert not dest.exists(),'use --verify-summary for retained results';dest.write_text(json.dumps(report,indent=2)+'\n')
    print('V89_EVIDENCE_PASS observation_sources=457 mixed_records=2285 joint_schedules=64')


if __name__=='__main__':main()
