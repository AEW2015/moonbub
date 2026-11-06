#!/usr/bin/env python3
"""Bind V88 actual-wire and addressed-memory evidence without merging scopes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v88'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-summary',action='store_true');args=parser.parse_args()
    bindings={}
    def path(name):
        p=(ROOT/name).resolve();p.relative_to(ROOT);return p
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def read(name):
        p=path(name);bindings[str(p.relative_to(ROOT))]=sha(p);return json.loads(p.read_text())
    def pins(items):
        for name,digest in items.items():
            p=path(name);assert sha(p)==digest,('pin mismatch',name);bindings[str(p.relative_to(ROOT))]=digest
    def selected(name):
        d=read(name);s=read(d['selected_report']);assert d==dict(s,selected_report=d['selected_report']);return d
    def artifacts(report):
        folder=path(report['selected_report']).parent
        for name,digest in report.get('artifacts_sha256',{}).items():
            p=folder/name;assert sha(p)==digest;bindings[str(p.relative_to(ROOT))]=digest
    prefix='experiments/python-gamebub-v88/'
    entropy=selected(prefix+'entropy/index.json')
    assert entropy['status']=='PASS_NATIVE_AND_INDEPENDENT_PYTHON_CHUNK_PARITY'
    assert (entropy['native_sources'],entropy['chunks'],entropy['coefficient_values'])==(457,1371,86444480)
    assert entropy['native_exit_code']==0 and entropy['old_feedback_decisions']==entropy['BR88_bit_reads']==37656819
    pins(entropy['source_sha256']);artifacts(entropy)
    em=read(prefix+'entropy/artifact-manifest.json');pins(em['files_sha256'])
    et=selected(prefix+'entropy/tests.json')
    assert et['status']=='PASS_CROSS_LANGUAGE_BOUNDED_RICE_GRAMMAR' and et['checks_count']==len(et['checks'])==35
    assert et['compile_exit_code']==et['native_exit_code']==0;pins(et['source_sha256']);artifacts(et)
    ea=read(prefix+'entropy-audit.json');assert ea['status']=='PASS' and ea['observed_exit_code']==0
    assert ea['counts']['native_sources']==457 and ea['counts']['chunks']==1371
    wire=selected(prefix+'wire/results.json')
    assert wire['status']=='PASS_FULL_NATIVE_MIXED_CODEC_PARITY' and (wire['native_sources'],wire['received_packets'])==(457,2285)
    assert len(wire['receiver_exit_codes'])==5 and set(wire['receiver_exit_codes'].values())=={0}
    pins(wire['source_sha256']);artifacts(wire)
    wa=read(prefix+'wire-audit.json');assert wa['status']=='PASS' and wa['observed_exit_code']==0
    assert wa['attempt_report']==wire['selected_report'] and wa['counts']==dict(sources=457,candidates=3656,selected_packets=2285,fixtures=35)
    pa=read(prefix+'packet-audit.json');assert pa['status']=='PASS_ALL_CANDIDATE_AND_SELECTED_PACKET_HASHES'
    assert (pa['native_sources'],pa['independently_reconstructed_candidates'],pa['independently_verified_selected_packets'],pa['retained_fixtures'])==(457,3656,2285,35)
    assert wire['selected_report'] in pa['source_sha256'];pins(pa['source_sha256'])
    wt=selected(prefix+'wire/tests.json')
    assert wt['status']=='PASS_NATIVE_CS88_PROTOCOL_RECOVERY' and wt['checks_count']==len(wt['checks'])==20
    assert all(check['observed_exit_code']==0 for check in wt['checks']);pins(wt['source_sha256'])
    alias=selected(prefix+'alias/results.json')
    assert alias['status']=='PASS_ADDRESSED_ALIAS_AND_NATIVE_PARITY' and alias['native_sources']==457
    pins(alias['source_sha256'])
    p=path(alias['selected_report']).with_name('frames.jsonl');assert sha(p)==alias['frames_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    for trace in alias['selected_traces']:
        p=path(trace['path']);assert sha(p)==trace['sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    am=read(prefix+'alias/artifact-manifest.json');pins(am['files_sha256'])
    at=read(prefix+'alias/tests.json');assert at['status'].startswith('PASS') and at['checks_count']==len(at['checks'])
    pins(at['source_sha256'])
    probe=selected(prefix+'alias/probe.json');assert probe['status']=='PASS_SELECTED_CAUSAL_ALIAS_REPLAY'
    assert probe['schedules']==len(probe['rows']) and probe['unique_sources']==len({(r['cohort'],r['fid']) for r in probe['rows']})
    assert probe['schedules']>=8 and probe['unique_sources']>=3;pins(probe['source_sha256'])
    for row in probe['rows']:
        p=path(row['witness']);assert sha(p)==row['witness_sha256'];bindings[str(p.relative_to(ROOT))]=sha(p)
    aa=read(prefix+'alias-audit.json');assert aa['status']=='PASS' and aa['observed_exit_code']==0
    ap=read(prefix+'alias-probe-audit.json')
    assert ap['status']=='PASS_INDEPENDENT_ALIAS_DAG_AND_CONSUMER_AUDIT' and (ap['unique_sources'],ap['schedules'])==(4,10)
    pins(ap['source_sha256'])
    report=dict(schema='cu66-v88-combined-evidence-v1',status='PASS_NATIVE_CODEC_AND_ADDRESSED_ALIAS_EVIDENCE',
                source_walkthrough_frames=457,native_CS88_packets=2285,independently_reconstructed_candidates=3656,
                independent_exact_fixtures=35,BR88_grammar_checks=35,native_protocol_checks=20,
                entropy_chunks=1371,entropy_coefficient_values=86444480,
                wire_summaries=wire['summaries'],addressed_alias_summaries=alias['summaries'],
                conditional_alias_probe_sources=probe['unique_sources'],conditional_alias_probe_schedules=probe['schedules'],
                conditional_alias_probe_rows=probe['rows'],alias_checks=at['checks_count'],
                evidence_sha256=bindings,verifier_sha256=sha(Path(__file__)),
                physical_30fps_proven=False,validated_full_under10ms_proven=False,esp32_simulated=False,
                scope=['One 457-source walkthrough family in four reset histories; encodings and probes do not add distinct gameplay coverage.',
                       'CS88 native pixels/bytes prove encoding correctness. Feedback removal does not make plain Rice parsing free or prove calibrated latency.',
                       'Alias causal probes retain fixed CS86 frontend work; do not assign those timings to BR88 or combine independent savings.',
                       'Addressed YUV base gather follows decoder publication; continuous LCD, RGB565/HUD composition, refresh and physical fit remain unqualified.'])
    dest=AREA/'summary.json'
    if args.verify_summary:assert json.loads(dest.read_text())==report,'summary differs'
    else:
        assert not dest.exists(),'use --verify-summary for retained results';dest.write_text(json.dumps(report,indent=2)+'\n')
    print('V88_EVIDENCE_PASS sources=457 packets=2285 candidates=3656')


if __name__=='__main__':main()
