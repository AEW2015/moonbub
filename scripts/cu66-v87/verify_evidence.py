#!/usr/bin/env python3
"""Bind selected V87 native, conditional timing and functional-layout evidence."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v87'


def local(name):
    p=(ROOT/name).resolve()
    p.relative_to(ROOT)
    return p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--verify-summary',action='store_true')
    args=parser.parse_args()
    bindings={}
    def read(name):
        p=local(name);bindings[str(p.relative_to(ROOT))]=sha(p)
        return json.loads(p.read_text())
    def pinned(pins):
        for name,digest in pins.items():
            p=local(name);assert sha(p)==digest,('pin mismatch',name)
            bindings[name]=digest
    prefix='experiments/python-gamebub-v87/'
    q=read(prefix+'quantizers/results.json')
    qr=read(q['selected_report']);assert q==dict(qr,selected_report=q['selected_report'])
    assert q['status']=='PASS_ACTUAL_PACKETS_NATIVE_PARITY' and (q['sources'],q['received_packets'])==(457,914)
    assert len(q['receiver_exit_codes'])==2 and set(q['receiver_exit_codes'].values())=={0}
    assert all(c.get('observed_exit_code',0)==0 for c in q['commands'])
    pinned(q['source_sha256'])
    for relative,digest in q['artifacts_sha256'].items():
        target=local(str(Path(q['selected_report']).parent/relative))
        assert sha(target)==digest;bindings[str(target.relative_to(ROOT))]=digest
    qa=read(prefix+'quantizer-audit.json')
    assert qa['status']=='PASS' and qa['rows_checked']==914 and qa['retained_fixtures_checked']==12
    assert qa['schema']=='cu66-v87-quantizer-independent-audit-v2' and qa['independently_reconstructed_packets']==914
    assert qa['campaign']==q['selected_report'],'quantizer audit targets a different campaign'
    tests=read(prefix+'quantizers/tests.json');tr=read(tests['selected_report'])
    assert tests==dict(tr,selected_report=tests['selected_report'])
    assert tests['status']=='PASS_CROSS_LANGUAGE_QUANTIZER_AND_NATIVE_RECOVERY' and tests['checks_count']==len(tests['checks'])==37
    assert tests['parser_exit_code']==0 and tests['source_after_run_sha256']==tests['source_sha256']
    assert all(c['observed_exit_code']==0 for c in tests['commands'])
    pinned(tests['source_sha256'])
    alias=read(prefix+'alias/results.json');ar=read(alias['selected_report'])
    assert alias==dict(ar,selected_report=alias['selected_report'])
    assert alias['status']=='PASS_FUNCTIONAL_TILE_ALIAS_AND_LEASE_REPLAY'
    assert (alias['native_sources'],alias['scenario_source_replays'])==(457,914) and len(alias['checks'])==61
    pinned(alias['source_sha256'])
    ap=local(str(Path(alias['selected_report']).with_name('frames.jsonl')))
    assert sha(ap)==alias['rows_sha256'];bindings[str(ap.relative_to(ROOT))]=sha(ap)
    aa=read(prefix+'memory/alias-audit.json')
    assert aa['status']=='PASS_NATIVE_ROWS_AND_SYMBOLIC_ALIAS_ORACLE'
    assert (aa['native_scenario_rows'],aa['symbolic_accepted_frames'])==(914,1024)
    assert aa['selected_report_sha256']==sha(local(alias['selected_report']))
    assert aa['report_sha256']==sha(AREA/'alias/results.json')
    pinned(aa['source_sha256']);pinned(aa['verified_subject_source_pins'])
    memory=read(prefix+'memory/results.json');ma=read(prefix+'memory-independent-audit.json')
    assert memory['status']=='PASS_NECESSARY_TRAFFIC_ACCOUNTING' and memory['native_sources']==457
    assert ma['status']=='PASS' and (ma['source_rows'],ma['scenario_rows'])==(457,1828)
    pinned(memory['source_sha256'])
    mp=AREA/'memory/frames.jsonl';assert sha(mp)==memory['frames_sha256']==ma['generated_frames_sha256']
    bindings[str(mp.relative_to(ROOT))]=sha(mp)
    manifest=read(prefix+'memory/artifact-manifest.json');pinned(manifest['files_sha256'])
    coupled=read(prefix+'coupled/verification.json')
    assert coupled['status']=='PASS_RETAINED_ROWS_AND_FROZEN_ZERO_CONTROL'
    assert (coupled['native_sources'],coupled['schedules'],coupled['frozen_zero_front_exact_matches'])==(457,2742,457)
    pinned(coupled['artifact_sha256']);pinned(coupled['source_sha256'])
    component=read(prefix+'coupled/artifact-manifest.json');pinned(component['files_sha256'])
    probe=read(prefix+'coupled/memory-probe.json')
    assert probe['status']=='PASS_FOUR_CONDITIONAL_WITNESS_REPLAYS' and (probe['unique_sources'],probe['schedules'])==(1,4)
    pinned(probe['source_sha256'])
    assert sha(local(probe['selected_attempt']))==probe['selected_attempt_sha256']
    for row in probe['rows']:
        assert sha(local(row['witness']))==row['witness_sha256']
        assert row['independent_audit']['finish_cycles']==row['finish_cycles']
    synthetic=read(prefix+'coupled/synthetic-tests.json')
    assert synthetic['status']=='PASS' and len(synthetic['checks'])==7
    pinned(synthetic['source_sha256'])
    wa=read(prefix+'memory/final-coupled-audit.json')
    wb=read(prefix+'memory/final-coupled-bindings.json')
    assert wa['status']==wb['status']=='PASS' and len(wa['witnesses'])==len(wb['bindings'])==5
    assert wb['audit_sha256']==sha(AREA/'memory/final-coupled-audit.json')
    for witness,binding in zip(wa['witnesses'],wb['bindings'],strict=True):
        assert witness['path']==binding['witness']
        p=local(witness['path']);assert sha(p)==witness['sha256']==binding['witness_sha256']
        assert witness['audit']['timeline_sha256']==binding['timeline_sha256']
        assert witness['audit']['finish_cycles']==binding['finish_cycles']
        rows=local(binding['rows_path']).read_text().splitlines()
        selected=[line for line in rows if (lambda row:(row['cohort'],row['fid'],row['configuration'])==
                    (binding['cohort'],binding['fid'],binding['configuration']))(json.loads(line))]
        assert len(selected)==1 and hashlib.sha256(selected[0].encode()).hexdigest()==binding['row_line_sha256']
    report=dict(schema='cu66-v87-combined-evidence-v1',status='PASS_SELECTED_NATIVE_COUPLED_AND_LAYOUT_EVIDENCE',
                evidence_sha256=bindings,verifier_sha256=sha(Path(__file__)),native_sources=457,
                native_CS87_packets=914,quantizer_checks=37,independently_audited_alias_replays=914,
                alias_symbolic_updates=1024,alias_retained_checks=61,conditional_coupled_schedules=2742,
                frozen_zero_front_exact_matches=457,independent_full_witnesses=5,
                separate_memory_sensitivity_schedules=4,separate_memory_sensitivity_unique_sources=1,
                coupled_summaries=coupled['summaries'],two_lane_paired_comparison=coupled['two_lane_paired_comparison'],
                quantizer_summaries=q['summaries'],memory_summaries=memory['summaries'],
                physical_30fps_proven=False,validated_full_under10ms_proven=False,esp32_simulated=False,
                scope=['Same 457-source walkthrough family in four reset histories; configurations/replays are not new content sources.',
                       'CS87 actual native packets prove reconstruction parity; coupled timing retains fixed CS86, not CS87/all-visible timings.',
                       'Conditional model omits qualified HUD semantics, physical ports/controller/display/ESP32 and uses assumed primitive/stage costs.',
                       'Alias layout is functional Python; its dense comparator differs from frozen residency traffic and is not a timing improvement.'])
    dest=AREA/'summary.json'
    if args.verify_summary:
        assert json.loads(dest.read_text())==report,'retained summary differs'
    else:
        assert not dest.exists(),'summary already exists; use --verify-summary'
        dest.write_text(json.dumps(report,indent=2)+'\n')
    print('V87_COMBINED_EVIDENCE_PASS native_packets=914 coupled_schedules=2742 alias_replays=914')


if __name__=='__main__':main()
