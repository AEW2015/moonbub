#!/usr/bin/env python3
"""Summarize exact x16-priced line gathering; bundle is frozen by V91l summary."""
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91k-lines'
BASELINE='1e974dcaab4b86646b0480f8987d3469316c06b3'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_CURRENT_SOURCE_BOTH_SEEDS_EXACT_ALIGNED_LINES_AND_CONTROL'
    runs=[];performance=[];words=dict(control=0,lines=0)
    for item in audit['attempts']:
        path=ROOT/item['attempt'];assert sha(path)==item['results_sha256']
        report=read(path);assert report['status']=='PASS_EXACT_X16_PRICED_ALIGNED_LINES'
        assert all(sha(ROOT/name)==value for name,value in report['source_sha256'].items())
        assert all(sha(ROOT/name)==value for name,value in report['inputs_sha256'].items())
        assert all(sha(path.parent/name)==value for name,value in report['artifacts_sha256'].items())
        assert all(cmd['exit_code']==0 for cmd in report['commands'])
        builds=[cmd['argv'] for cmd in report['commands'] if '--build' in cmd['argv']];assert len(builds)==2
        for argv in builds:
            assert '--assert' in argv and '-Wall' in argv and argv[argv.index('-j')+1]=='2'
            assert '-Wall -Wextra -Werror' in argv[argv.index('-CFLAGS')+1]
        assert '5.020' in (path.parent/'tool-version.log').read_text() and '13.3.0' in (path.parent/'compiler-version.log').read_text()
        for diagnostic in (False,True):
            cases={}
            for label in ('control','lines'):
                name=('edge-'+label if diagnostic else 'simulation-'+label)+'.jsonl'
                rows=[json.loads(line) for line in (path.parent/name).read_text().splitlines()]
                cases[label]={(r['id'],r['memory_profile']):r for r in rows if r['type']=='case'}
                assert len(cases[label])==(2 if diagnostic else 12)
                verdict=rows[-1];assert verdict==report['edge_verdicts' if diagnostic else 'verdicts'][label]
                assert verdict['directed_checks']==(33 if label=='lines' else 29)
                words[label]+=verdict['pixels']
            assert set(cases['control'])==set(cases['lines'])
            for key,a in cases['control'].items():
                b=cases['lines'][key];assert a['rgb565_hash']==b['rgb565_hash'] and a['canonical_input_hash']==b['canonical_input_hash']
                assert a['reads']==b['reads']==b['responses']==518400
                assert b['physical_reads']==b['physical_responses']==32400 and b['physical_x16_beats']==259200
                assert b['line_hits']==486000 and b['line_misses']==32400 and b['byte_response_hash']==b['read_schedule_hash']
                assert b['cycles']<a['cycles']
                if key[1]==0:
                    assert a['cycles']==2938320 and b['cycles']==2743921
                    assert a['first_output']-a['first_read']==4328 and b['first_output']-b['first_read']==3797
                performance.append(dict(seed=report['seed'],id=key[0],profile=key[1],diagnostic=diagnostic,
                    control_cycles=a['cycles'],line_cycles=b['cycles'],saved_cycles=a['cycles']-b['cycles'],
                    reduction_percent=100*(a['cycles']-b['cycles'])/a['cycles'],
                    control_first_byte_to_first_word=a['first_output']-a['first_read'],
                    line_first_byte_to_first_word=b['first_output']-b['first_read']))
        runs.append(dict(seed=report['seed'],path=item['attempt'],sha256=item['results_sha256'],
            verdicts=report['verdicts'],edge_verdicts=report['edge_verdicts'],audit=item))
    assert {r['seed'] for r in runs}=={911701,911702} and len(runs)==2
    assert words==dict(control=9676800,lines=9676800)
    prior={}
    for name in ('experiments/python-gamebub-v91k-cache/summary.json','experiments/python-gamebub-v91k-cache/audit.json',
                 'fpga/experiments/cu66-v91k-cache/canonical_rgb565_cached.sv','fpga/experiments/cu66-v91k-cache/tb_cache.cpp'):
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)).hexdigest()==sha(ROOT/name)
        prior[name]=sha(ROOT/name)
    slow=[r['reduction_percent'] for r in performance if r['profile']==1 and not r['diagnostic']]
    report=dict(schema='cu66-v91k-x16-line-gather-qualified-v1',status='PASS',baseline_revision=BASELINE,runs=runs,
        performance=performance,exact_rgb565_words_by_path=words,
        physical_reads_per_frame=32400,byte_requests_per_frame=518400,priced_x16_beats_per_frame=259200,
        line_payload_bytes_per_frame=518400,line_slot_logical_bytes=48,byte_cache_logical_bytes=1440,
        fast_cycle_reduction_percent=100*(2938320-2743921)/2938320,
        slow_observed_cycle_reduction_percent_min=min(slow),slow_observed_cycle_reduction_percent_max=max(slow),
        prior_evidence_unchanged=prior,audit_sha256=sha(AREA/'audit.json'),independent_verifier_sha256=sha(AREA/'verify_results.py'),
        service_scope='128-bit gathered responses cost eight x16 payload beats plus response/stall overhead; no command-accurate SDRAM/refresh/scanout model. SLOW rules match but absolute stall traces differ.',
        full_frame_decode_under10ms_proven=False,hardware_distinct_30fps_proven=False,mapped_memory_fit_proven=False,
        monolithic_full_frame_rtl_proven=False,next='Join actual memory-controller and shared service, then test local lookup overlap; preserve pending physical/inner-byte ownership.')
    (AREA/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('LINES_SUMMARY_PASS',words,'words; external reads /16, x16 beats /2; FAST cycles',report['fast_cycle_reduction_percent'])
if __name__=='__main__':main()
