#!/usr/bin/env python3
"""Freeze qualified V91k canonical and base RGB565 replay evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91k'
BASELINE='914fe698ba61ac0b266dd45c722fca2b86d995a7'
SHARED=['docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md']
PRIMARY=('actual_001','actual_006','actual_043','actual_031')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_INDEPENDENT_GOLDENS_AND_BOTH_RTL_SEEDS'
    assert audit['goldens']['status']=='PASS_INDEPENDENT_SOURCE_RECONSTRUCTION_AND_RGB565'
    assert audit['goldens']['cases']==6
    assert all(sha(ROOT/name)==value for name,value in audit['source_sha256'].items())
    attempts=[];fences=[];complete_bytes=0;all_bytes=0;words=0
    for item in audit['integration']['attempts']:
        path=ROOT/item['path'];assert sha(path)==item['sha256']
        report=read(path)
        assert report['status']=='PASS_CANONICAL_AND_BASE_RGB565_RTL_REPLAY'
        assert all(sha(ROOT/name)==value for name,value in report['source_sha256'].items())
        assert all(sha(AREA/'vectors'/name)==value for name,value in report['vectors_sha256'].items())
        builds=[command for command in report['commands'] if '--build' in command['argv']]
        assert len(builds)==2 and all(command['exit_code']==0 for command in report['commands'])
        for command in builds:
            argv=command['argv']
            assert '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='2'
            assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS')+1]
        assert '5.020' in (path.parent/'tool-version.log').read_text()
        assert '13.3.0' in (path.parent/'compiler-version.log').read_text()
        assert report['verdict']['directed_checks']==21
        assert report['rgb_verdict']['directed_checks']==8
        assert report['rgb_verdict']['pixels']==4147200
        sim=[json.loads(line) for line in (path.parent/'simulation.jsonl').read_text().splitlines()]
        rgb=[json.loads(line) for line in (path.parent/'rgb.jsonl').read_text().splitlines()]
        cases={(row['id'],row['memory_profile']):row for row in sim if row['type']=='case'}
        colors={(row['id'],row['memory_profile']):row for row in rgb if row['type']=='case'}
        assert len(cases)==22 and len(colors)==12
        accepted={key:row for key,row in cases.items() if row['error']==0}
        assert set(accepted)==set(colors)
        assert sum(row['canonical']['samples'] for row in accepted.values())==6220800
        complete_bytes+=sum(row['canonical']['samples'] for row in accepted.values())
        all_bytes+=report['verdict']['canonical_comparisons'];words+=report['rgb_verdict']['pixels']
        for key,row in accepted.items():
            col=colors[key]
            assert row['done_cycle']>0 and not row['full_frame_publication'] and not row['pending_drain']
            assert row['canonical']['reference_requests']==row['canonical']['reference_acks']
            assert row['canonical']['ref_pending']==0 and row['canonical']['samples']==518400
            assert col['reads']==col['responses']==3110400 and col['pixels']==345600
            if key[1]==0:assert col['cycles']==10022400
            fences.append(dict(seed=report['seed'],id=key[0],memory_profile=key[1],
                native_content=key[0] in PRIMARY,canonical_start_to_done_cycles=row['cycles'],
                last_outer_byte_to_canonical_done_cycles=row['done_cycle']-row['last_input'],
                cache_preload_cycles=row['cache_cycles'],canonical_reference_requests=row['canonical']['reference_requests'],
                base_rgb565_replay_cycles=col['cycles'],rgb_byte_reads=col['reads'],
                sequential_canonical_plus_rgb_replay_cycles=row['cycles']+col['cycles']))
        attempts.append(dict(path=item['path'],sha256=item['sha256'],seed=report['seed'],
            verdict=report['verdict'],rgb_verdict=report['rgb_verdict'],audit=item,
            canonical_trace=report['canonical_trace'],canonical_actual=report['canonical_actual']))
    assert {item['seed'] for item in attempts}=={911501,911502} and len(attempts)==2
    prior={}
    for name in ('experiments/python-gamebub-v91j/summary.json','experiments/python-gamebub-v91j/audit.json',
                 'docs/cu66-v91j/README.md','fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv',
                 'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv'):
        original=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
        assert hashlib.sha256(original).hexdigest()==sha(ROOT/name)
        prior[name]=sha(ROOT/name)
    smoke_reports=[]
    for path in sorted((ROOT/'fpga/experiments/cu66-v91k/rgb/smoke-attempts').glob('*/results.json')):
        r=read(path)
        if r['status']=='PASS_SIGNED_CHROMA_CLIPPING_RGB_AND_RECOVERY' and all(
                sha(ROOT/name)==value for name,value in r['source_sha256'].items()):
            assert all(sha(path.parent/'sources'/name)==value for name,value in r['source_sha256'].items())
            assert all(sha(path.parent/name)==value for name,value in r['artifacts_sha256'].items())
            assert all(command['exit_code']==0 for command in r['commands'])
            build_commands=[command['argv'] for command in r['commands'] if '--build' in command['argv']]
            assert len(build_commands)==1
            argv=build_commands[0]
            assert '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='2'
            assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS')+1]
            observed=[json.loads(line) for line in (path.parent/'simulation.jsonl').read_text().splitlines()]
            assert observed[-1]==r['verdict'] and r['verdict']['status']=='TEST_PASS'
            assert r['verdict']['pixels']==1382400 and r['verdict']['directed_checks']==8
            assert {row['id'] for row in observed if row['type']=='case'}=={
                'neutral','negative_chroma','signed_green','positive_clip'}
            smoke_reports.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),verdict=r['verdict']))
    assert smoke_reports and smoke_reports[-1]['verdict']['cases']==4
    summary=dict(schema='cu66-v91k-canonical-rgb-qualified-v1',status='PASS',baseline_revision=BASELINE,
        attempts=attempts,signed_chroma_clipping_smoke=smoke_reports[-1],service_fences=fences,
        actual_native_content_frames=4,synthetic_content_cases=2,
        total_complete_canonical_byte_comparisons=complete_bytes,
        total_canonical_byte_comparisons_including_failed_prefixes=all_bytes,
        total_base_rgb565_word_comparisons=words,
        prior_evidence_and_math_unchanged=prior,audit_sha256=sha(AREA/'audit.json'),
        independent_verifier_sha256=sha(AREA/'verify_results.py'),python_model_sha256=sha(AREA/'model.py'),
        model_results_sha256=sha(AREA/'model-results.json'),
        logical_payload_bytes=dict(coefficient_banks=256,reconstruction_tiles=320,packet_staging=98304,
                                   canonical_candidate=518400,accepted_reference=518400,retained_rgb565_if_used=691200),
        proposed_chroma_cache=dict(status='PLANNED_NOT_MEASURED',logical_bytes=1440,
            baseline_external_byte_reads_per_frame=3110400,target_external_byte_reads_per_frame=518400,
            reduction_factor=6,contract='Exact horizontal-then-vertical rounding and edge replication; valid tags only after acknowledged fill; cancel retains pending physical read owner.'),
        worst_tested_native_canonical_cycles=max(row['canonical_start_to_done_cycles'] for row in fences if row['native_content']),
        worst_tested_native_rgb_replay_cycles=max(row['base_rgb565_replay_cycles'] for row in fences if row['native_content']),
        scope='BR88 actual frame -> canonical reconstruction; separate RTL RGB565 replay from actual committed candidate memory, no HUD/hash validation/publication.',
        timing_caveat='Sequential sums are candidate-memory replay service, not monolithic shared-bus/transport/scanout or complete validated latency. No achieved frequency is inferred.',
        full_frame_publication_timestamp=None,full_frame_decode_under10ms_proven=False,
        hardware_distinct_30fps_proven=False,monolithic_full_frame_rtl_proven=False,mapped_memory_fit_proven=False,
        next_milestone='V91l HUD/content validation, canonical hashes/seals and atomic publication. Qualify bounded chroma-row-cache control comparison before 30-Hz full finite-service V91m.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest_path=AREA/'bundle-manifest.json';paths=[ROOT/name for name in SHARED]
    for directory in ('docs/cu66-v91k','scripts/cu66-v91k','experiments/python-gamebub-v91k','fpga/experiments/cu66-v91k'):
        paths.extend(path for path in (ROOT/directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts and path!=manifest_path)
    manifest=dict(schema='cu66-v91k-bundle-manifest-v1',baseline_revision=BASELINE,
        files_sha256={str(path.relative_to(ROOT)):sha(path) for path in sorted(set(paths))},
        prior_shared_plan_sha256={name:hashlib.sha256(subprocess.check_output(
            ['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('V91K_SUMMARY_PASS',complete_bytes,'complete canonical bytes;',words,'RGB words;',len(manifest['files_sha256']),'bundle files; next V91l')


if __name__=='__main__':
    main()
