#!/usr/bin/env python3
"""Bind V90 policy, exact conditional oracle, native histories and review prep."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v90'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-summary',action='store_true');args=parser.parse_args();bindings={}
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
    def artifacts(report):
        folder=local(report['selected_report']).parent
        for name,digest in report.get('artifacts_sha256',{}).items():
            p=folder/name;assert sha(p)==digest;bindings[str(p.relative_to(ROOT))]=digest
    prefix='experiments/python-gamebub-v90/'
    policy=selected(prefix+'policy/results.json')
    assert policy['status']=='PASS_ACTUAL_WORK_RESOURCE_SCORE_SELECTION' and (policy['native_sources'],policy['candidate_records'],policy['selected_packets'])==(457,3656,914)
    assert policy['cap_bytes']==49152;pins(policy['source_sha256']);artifacts(policy)
    pm=read(prefix+'policy/artifact-manifest.json');pins(pm['files_sha256'])
    pv=read(prefix+'policy/verification.json')
    assert pv['status']=='PASS_SAVED_SCORE_SELECTION_AND_NATIVE_ENDPOINT_COUNTS' and (pv['native_sources'],pv['candidate_records'],pv['selected_records'],pv['endpoint_observation_records'])==(457,3656,914,914)
    pins(pv['source_sha256'])
    pt=read(prefix+'policy/tests.json');assert pt['status']=='PASS_PLANE_LAYOUT_AND_ABSOLUTE_CAP_CONTRACTS' and pt['checks_count']==18;pins(pt['source_sha256'])
    pa=read(prefix+'policy-audit.json');assert pa['status']=='PASS_INDEPENDENT_POLICY_ACCOUNTING'
    assert pa['parent_report_sha256']==sha(AREA/'policy/results.json')
    assert pa['candidate_records']==3656 and pa['selected_packets']==914 and pa['candidate_packet_digests_and_sizes_match_v88']
    exact=selected(prefix+'exact/results.json')
    assert exact['status']=='PASS_EXHAUSTIVE_SELECTED_CAUSAL_TIMING' and (exact['unique_sources'],exact['schedules'])==(4,64)
    assert len(exact['unchanged_V89_control_matches'])==32;pins(exact['source_sha256']);artifacts(exact)
    em=read(prefix+'exact/artifact-manifest.json');pins(em['files_sha256'])
    ev=read(prefix+'exact/verification.json')
    assert ev['status']=='PASS_ALL_MASK_WORK_ORACLES_AND_RETAINED_DAGS'
    assert (ev['unique_sources'],ev['schedules'],ev['actual_masks_observed'],ev['unchanged_V89_matches'],ev['unchanged_V89_unique_cases'],ev['independent_retained_witnesses'])==(4,64,32,32,22,16)
    pins(ev['source_sha256'])
    choices=read(prefix+'exact/oracle-selections.json');assert len(choices['choices'])==8
    assert sha(local(choices['source_report']))==choices['source_report_sha256'] and sha(local(choices['verification_report']))==choices['verification_report_sha256']
    comparison=read(prefix+'policy/exact-comparison.json')
    assert comparison['status']=='PASS_EXHAUSTIVE_COMPARISON_NOT_A_DEADLINE_PROOF' and comparison['exact_candidate_rows']==64 and comparison['source_cost_pairs']==8
    pins(comparison['source_sha256'])
    native=selected(prefix+'native/results.json')
    assert native['status']=='PASS_NATIVE_SELECTIONS_AND_EXACT_REPLAY'
    assert (native['native_sources'],native['new_packet_calls'],native['exact_replay_calls'],native['oracle_override_calls'])==(457,1828,1828,8)
    assert len(native['receiver_exit_codes'])==4 and set(native['receiver_exit_codes'].values())=={0}
    pins(native['source_sha256']);artifacts(native)
    na=read(prefix+'native-audit.json');assert na['status']=='PASS_NATIVE_SELECTION_DECODE_REPLAY_AUDIT'
    assert (na['native_rows'],na['distinct_sources'],na['new_packet_calls'],na['exact_replay_calls'],na['oracle_override_rows'])==(1828,457,1828,1828,8)
    assert na['all_selected_packets_within_49152_bytes'] and 'display_sha256' in na['groundtruth_fields']
    review=read('docs/cu66-v90/literature-review-source-log.json')
    assert review['status']=='PREPARATION_NOT_COMPLETED_LITERATURE_REVIEW' and len(review['sources'])==9
    for name in ('literature-review-prep.md','literature-review-matrix.csv'):
        p=ROOT/'docs/cu66-v90'/name;bindings[str(p.relative_to(ROOT))]=sha(p)
    report=dict(schema='cu66-v90-combined-evidence-v1',status='PASS_POLICY_ORACLE_NATIVE_AND_REVIEW_PREPARATION',
                native_sources=457,candidate_records=3656,proxy_selections=914,exact_sources=4,exact_unique_schedules=64,
                previous_policy_row_matches=32,previous_unique_case_matches=22,independent_retained_DAGs=16,policy_contract_checks=18,
                native_new_packet_calls=1828,native_exact_replay_calls=1828,native_oracle_override_calls=8,
                policy_summaries=policy['summaries'],exact_oracles=exact['exact_oracles'],exact_summary=exact['summary_by_cost'],
                proxy_exact_comparison=comparison['summaries'],necessary_floor_false_passes=comparison['all64_necessary_floor_pass_actual_not'],
                review_seed_sources=9,literature_review_completed=False,evidence_sha256=bindings,verifier_sha256=sha(Path(__file__)),
                physical_30fps_proven=False,validated_full_under10ms_proven=False,esp32_simulated=False,
                scope=['Existing CS88 bytes/quantized picture unchanged; actual candidate counters under absolute49152-byte admission.',
                       'Proxy serialization score ranks candidates and is not completion latency; formula frozen before exact results.',
                       'Exact oracle covers four selected sources with assumed costs, not full457 or live encoder timing.',
                       'Native oracle override histories use proxy fallback outside those four sources; replays do not add content coverage.',
                       'Primary literature seeds were screened for preparation, not a completed review or transferred hardware benchmark.'])
    dest=AREA/'summary.json'
    if args.verify_summary:assert json.loads(dest.read_text())==report,'summary differs'
    else:
        assert not dest.exists(),'use --verify-summary for retained results';dest.write_text(json.dumps(report,indent=2)+'\n')
    print('V90_EVIDENCE_PASS sources=457 candidates=3656 exact_schedules=64 native_new=1828')


if __name__=='__main__':main()
