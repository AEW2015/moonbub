#!/usr/bin/env python3
"""Freeze the measured exact chroma cache/control comparison and next gates."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91k-cache'
BASELINE='a0a60502edc348c3e6340722671bf6477a2f01c0'
SHARED=['docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_CURRENT_SOURCE_BOTH_SEEDS_EXACT_CACHE_AND_CONTROL'
    runs=[];performance=[];pixels=dict(control=0,cache=0);read_totals=dict(control=0,cache=0)
    for item in audit['runs']:
        path=ROOT/item['attempt'];assert sha(path)==item['results_sha256']
        report=read(path);assert report['status']=='PASS_EXACT_REGISTERED_CHROMA_CACHE_COMPARISON'
        assert all(sha(ROOT/name)==value for name,value in report['source_sha256'].items())
        assert all(sha(ROOT/name)==value for name,value in report['inputs_sha256'].items())
        assert all(sha(path.parent/name)==value for name,value in report['artifacts_sha256'].items())
        assert all(command['exit_code']==0 for command in report['commands'])
        builds=[command['argv'] for command in report['commands'] if '--build' in command['argv']]
        assert len(builds)==2
        for argv in builds:
            assert '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='2'
            assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS')+1]
        assert '5.020' in (path.parent/'tool-version.log').read_text()
        assert '13.3.0' in (path.parent/'compiler-version.log').read_text()
        for diag in (False,True):
            values={}
            for label in ('control','cache'):
                filename=('edge-'+label if diag else 'simulation-'+label)+'.jsonl'
                rows=[json.loads(line) for line in (path.parent/filename).read_text().splitlines()]
                cases={(row['id'],row['memory_profile']):row for row in rows if row['type']=='case'}
                assert len(cases)==(2 if diag else 12)
                verdict=rows[-1]
                assert verdict==report['edge_verdicts' if diag else 'verdicts'][label]
                assert verdict['directed_checks']==(29 if label=='cache' else 8)
                pixels[label]+=verdict['pixels']
                for row in cases.values():
                    assert row['reads']==row['responses']==(518400 if label=='cache' else 3110400)
                    assert row['pixels']==345600 and row['publication'] is False
                    read_totals[label]+=row['reads']
                    if label=='cache':
                        assert row['lookups']==row['lookup_responses']==row['cache_hits']==345600
                        assert row['row_fills']==240 and row['final_row_tags']==[238,239]
                values[label]=cases
            assert set(values['control'])==set(values['cache'])
            for key,a in values['control'].items():
                b=values['cache'][key]
                assert a['rgb565_hash']==b['rgb565_hash'] and a['canonical_input_hash']==b['canonical_input_hash']
                assert a['cycles']>b['cycles']
                start_a=a['first_output']-a['first_read'];start_b=b['first_output']-b['first_read']
                if key[1]==0:
                    assert a['cycles']==10022400 and b['cycles']==2938320
                    assert start_a==28 and start_b==4328
                performance.append(dict(seed=report['seed'],id=key[0],memory_profile=key[1],diagnostic=diag,
                    control_cycles=a['cycles'],cache_cycles=b['cycles'],saved_cycles=a['cycles']-b['cycles'],
                    reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],
                    control_first_read_to_first_word=start_a,cache_first_read_to_first_word=start_b,
                    control_reads=a['reads'],cache_reads=b['reads']))
        assert report['row_trace']['rows']==2880 and report['edge_row_trace']['rows']==480
        runs.append(dict(seed=report['seed'],path=item['attempt'],sha256=item['results_sha256'],
            verdicts=report['verdicts'],edge_verdicts=report['edge_verdicts'],audit=item,
            row_trace=report['row_trace'],edge_row_trace=report['edge_row_trace']))
    assert {row['seed'] for row in runs}=={911601,911602} and len(runs)==2
    assert pixels==dict(control=9676800,cache=9676800)
    assert read_totals['control']==6*read_totals['cache']
    prior={}
    for name in ('experiments/python-gamebub-v91k/summary.json','experiments/python-gamebub-v91k/audit.json',
        'docs/cu66-v91k/README.md','docs/cu66-v91k/chroma-cache-plan.md',
        'fpga/experiments/cu66-v91k/rgb/canonical_rgb565_v91k.sv','fpga/experiments/cu66-v91k/rgb/tb_rgb.cpp',
        'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv'):
        raw=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest()==sha(ROOT/name)
        prior[name]=sha(ROOT/name)
    selected={row['path'] for row in runs};superseded=[]
    for path in sorted((ROOT/'fpga/experiments/cu66-v91k-cache/comparison-attempts').glob('*/results.json')):
        if str(path.relative_to(ROOT)) not in selected:
            r=read(path);superseded.append(dict(path=str(path.relative_to(ROOT)),sha256=sha(path),status=r['status'],
                note='Retained prior attempt; does not qualify the current-source final coverage. Original verdict is preserved.'))
    slow=[row['reduction_percent'] for row in performance if row['memory_profile']==1 and not row['diagnostic']]
    summary=dict(schema='cu66-v91k-chroma-cache-qualified-v1',status='PASS',baseline_revision=BASELINE,
        runs=runs,performance=performance,exact_rgb565_words_by_path=pixels,external_reads_by_path=read_totals,
        actual_native_content_frames=4,existing_synthetic_cases=2,additional_synthetic_edge_frames=1,
        logical_cache_payload_bytes=1440,cache_external_reads_per_frame=518400,control_external_reads_per_frame=3110400,
        external_read_reduction_factor=6,fast_cycle_reduction_percent=100*(10022400-2938320)/10022400,
        slow_observed_cycle_reduction_percent_min=min(slow),slow_observed_cycle_reduction_percent_max=max(slow),
        first_read_to_first_word_fast_cycles=dict(control=28,cache=4328),
        prior_evidence_unchanged=prior,superseded_attempts=superseded,
        audit_sha256=sha(AREA/'audit.json'),independent_verifier_sha256=sha(AREA/'verify_results.py'),
        python_model_sha256=sha(AREA/'model.py'),model_results_sha256=sha(AREA/'model-results.json'),
        service_caveat='FAST measures deterministic scheduling. SLOW uses matching seeded service rules but different RNG consumption/absolute stall traces; these are measured observations under those rules.',
        scope='Exact base RGB565 conversion only, from actual V91k candidate-memory replay plus a separate labeled synthetic edge diagnostic. No wire/quantizer change.',
        full_frame_publication_timestamp=None,hardware_distinct_30fps_proven=False,
        full_frame_decode_under10ms_proven=False,mapped_cache_fit_proven=False,monolithic_full_frame_rtl_proven=False,
        next_milestone='V91l canonical/HUD validation, hashes/seals and atomic publication. Compare bounded multi-byte memory reads and overlapped local lookup separately; V91m full finite-service join and V100–V110 physical qualification remain open.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest_path=AREA/'bundle-manifest.json';paths=[ROOT/name for name in SHARED]
    for directory in ('docs/cu66-v91k-cache','scripts/cu66-v91k-cache','experiments/python-gamebub-v91k-cache','fpga/experiments/cu66-v91k-cache'):
        paths.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest_path)
    manifest=dict(schema='cu66-v91k-chroma-cache-bundle-v1',baseline_revision=BASELINE,
        files_sha256={str(path.relative_to(ROOT)):sha(path) for path in sorted(set(paths))},
        prior_shared_plan_sha256={name:hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest() for name in SHARED})
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    print('CHROMA_CACHE_SUMMARY_PASS',pixels,'words;',len(manifest['files_sha256']),'files; FAST -70.68247% cycles, reads /6')


if __name__=='__main__':
    main()
