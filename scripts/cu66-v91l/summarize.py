#!/usr/bin/env python3
"""Freeze partial V91l integrity/publication proof and aligned-read follow-up."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l'
BASELINE='1e974dcaab4b86646b0480f8987d3469316c06b3'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md','docs/literature-review-2026-11-06/README.md']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    subprocess.run([sys.executable,str(ROOT/'scripts/cu66-v91k-lines/summarize.py')],check=True,cwd=ROOT)
    audit=read(AREA/'audit.json');assert audit['status']=='PASS_BOTH_SEEDS'
    assert all(sha(ROOT/name)==value for name,value in audit['source_sha256'].items())
    lines=read(ROOT/'experiments/python-gamebub-v91k-lines/summary.json');assert lines['status']=='PASS'
    runs=[];fences=[];totals=dict(canonical_bytes=0,hud_bytes=0,sha_jobs=0,message_bytes=0,sha_blocks=0,validated_commits=0)
    for item in audit['results']:
        path=ROOT/item['attempt']/'results.json';assert sha(path)==item['results_sha256']
        report=read(path);assert report['status']=='PASS_C2_AND_ATOMIC_PUBLICATION_WITH_SOFTWARE_HUD'
        assert all(sha(ROOT/name)==value for name,value in report['source_sha256'].items())
        assert all(sha(path.parent/'vectors'/name)==value for name,value in report['vectors_sha256'].items())
        assert all(sha(path.parent/name)==value for name,value in report['artifacts_sha256'].items())
        assert all(cmd['exit_code']==0 for cmd in report['commands'])
        builds=[cmd['argv'] for cmd in report['commands'] if '--build' in cmd['argv']];assert len(builds)==1
        argv=builds[0];assert '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='2'
        assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS')+1]
        assert '5.020' in (path.parent/'tool-version.log').read_text() and '13.3.0' in (path.parent/'compiler-version.log').read_text()
        assert report['verdict']['directed_checks']==54 and report['verdict']['cases']==14
        rows=[json.loads(line) for line in (path.parent/'simulation.jsonl').read_text().splitlines()]
        cases=[row for row in rows if row['type']=='case'];assert len(cases)==14
        for row in cases:
            assert row['status']=='PASS' and row['canonical_bytes']==518400 and row['hud_bytes']==42240
            assert row['write_requests']==row['write_acks']==560640
            assert row['hash_jobs']==1025 and row['hash_message_bytes']==628815 and row['hash_blocks']==10298
            assert row['commit_cycle']>row['last_pixel_cycle'] and row['commit_cycle']>row['last_hud_cycle']
            if row['profile']==0:assert row['cycles']==1290445
            totals['canonical_bytes']+=row['canonical_bytes'];totals['hud_bytes']+=row['hud_bytes']
            totals['sha_jobs']+=row['hash_jobs'];totals['message_bytes']+=row['hash_message_bytes']
            totals['sha_blocks']+=row['hash_blocks'];totals['validated_commits']+=1
            fences.append(dict(seed=report['seed'],id=row['id'],role=row['role'],profile=row['profile'],
                rtl_start_to_commit_cycles=row['cycles'],last_pixel_to_commit=row['commit_cycle']-row['last_pixel_cycle'],
                last_hud_to_commit=row['commit_cycle']-row['last_hud_cycle'],commit_cycle=row['commit_cycle']))
        assert item['independently_checked_rtl_digest_jobs']==14350
        runs.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),seed=report['seed'],verdict=report['verdict'],
            audit=item,hash_trace=report['hash_trace']))
    assert {r['seed'] for r in runs}=={911801,911802} and len(runs)==2
    assert totals['validated_commits']==28 and totals['sha_jobs']==28700
    prior={}
    for name in ('fpga/experiments/cu66-v69/hash/cu66_sha256_bytes.sv','fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv',
        'experiments/cu66-native-v69/hud.hpp','experiments/cu66-native-v69/bytes.hpp','experiments/cu66-native-v69/generated_constants.hpp',
        'experiments/python-gamebub-v91k/summary.json','experiments/python-gamebub-v91k-cache/summary.json'):
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest()==sha(ROOT/name)
        prior[name]=sha(ROOT/name)
    report=dict(schema='cu66-v91l-partition-qualified-v1',status='PASS_HETEROGENEOUS_PARTITION',complete_v91l_full_rtl_proven=False,
        baseline_revision=BASELINE,runs=runs,totals=totals,service_fences=fences,actual_primary_frames=4,historical_bootstrap_frames=3,
        c2_node_logical_bytes=32768,candidate_bank_bytes=560640,three_candidate_reference_front_banks_bytes=1681920,
        full_rtl_hud_decoder=False,full_rtl_hud_overlay=False,
        timing_scope='RTL C2/HUD/seal hash + finite candidate write service + validated commit; excludes native C++ HUD semantic decode, fixture I/O and original packet CRC parsing before begin. Safe presentation has a separate vblank/scanout fence.',
        audit_sha256=sha(AREA/'audit.json'),independent_verifier_sha256=sha(AREA/'verify_results.py'),
        model_results_sha256=sha(AREA/'model-results.json'),prior_sources_unchanged=prior,
        aligned_read_summary_sha256=sha(ROOT/'experiments/python-gamebub-v91k-lines/summary.json'),
        hardware_distinct_30fps_proven=False,full_frame_decode_under10ms_proven=False,physical_bank_fit_proven=False,
        monolithic_full_frame_rtl_proven=False,
        next='Complete V91l live canonical/write-ACK join and actual HUD decode/overlay boundary; price intended CPU endpoint if heterogeneous. Then V91m finite transport/memory/display workload; V100–V110 physical closure and sustained hardware goals.')
    (AREA/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    manifest_path=AREA/'bundle-manifest.json';paths=[ROOT/name for name in SHARED]
    for stem in ('cu66-v91l','cu66-v91k-lines'):
        for directory in ('docs/'+stem,'scripts/'+stem,'fpga/experiments/'+stem):
            paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for directory in ('experiments/python-gamebub-v91l','experiments/python-gamebub-v91k-lines'):
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest_path)
    manifest=dict(schema='cu66-v91l-and-aligned-lines-bundle-v1',baseline_revision=BASELINE,
        files_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths))},
        prior_shared_plan_sha256={name:hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('V91L_PARTITION_SUMMARY_PASS',totals,';',len(manifest['files_sha256']),'files; full-RTL milestone still partial')
if __name__=='__main__':main()
