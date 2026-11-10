#!/usr/bin/env python3
"""Strict bounded admission proof. Default verifies recipes; --run needs Root grant."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'fpga/experiments/cu66-v126-producer'
V=SRC/'verification'
AREA = ROOT / 'experiments/python-gamebub-v126/producer'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    temp = p.with_name(p.name + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    temp.replace(p)




def verify():
    """Read-only validation; never regenerate source or fixtures after freeze."""
    import collections,re
    recipe=json.loads((SRC/'edit-recipe.json').read_text())
    vr=json.loads((SRC/'verification-recipe.json').read_text())
    runner=json.loads((ROOT/'scripts/cu66-v126/integration/focused-runner-derivation.json').read_text())
    def reversible(meta):
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        assert sha(before)==meta['original_sha256']and sha(after)==meta['candidate_sha256']
        text=before.read_text()
        for e in meta['edits']:
            assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
        assert text==after.read_text()
        for e in reversed(meta['edits']):
            assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
        assert text==before.read_text()
    reversible(recipe)
    for e in runner['sources']:reversible(e)
    assert recipe['added_source_payload_bits']==24 and recipe['unchanged_other_origins']==17
    assert recipe['added_public_cycles']==recipe['added_synthesis_attributes']==recipe['old_assertions_removed']==recipe['old_private_value_contract_changes']==0
    original=(ROOT/recipe['original']).read_text();candidate=(ROOT/recipe['candidate']).read_text()
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):assert block in candidate
    assert re.findall(r'\(\*(.*?)\*\)',original,re.S)==re.findall(r'\(\*(.*?)\*\)',candidate,re.S)
    checks=lambda text:collections.Counter(re.findall(r'(?:need|require_owner)\(.*?\);',text,re.S))
    assert vr['schema']=='v126-producer-verification-derivation-v1'
    assert vr['old_require_checks_removed']==vr['new_payload_or_owner_forces']==0 and vr['prepared_priming_is_natural_traffic'] is False
    for meta in vr['adapters']:
        reversible(meta)
        if Path(meta['original']).suffix in ('.cpp','.hpp'):
            assert not checks((ROOT/meta['original']).read_text())-checks((ROOT/meta['candidate']).read_text())
    for meta in vr['unchanged']:assert sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256']
    assert len(vr['new_verification_inputs'])==4
    for meta in vr['new_verification_inputs']:assert sha(ROOT/meta['path'])==meta['sha256']
    extraction=vr['scalar_extraction'];target=ROOT/extraction['target']
    assert extraction['source']==recipe['candidate']and extraction['source_sha256']==sha(ROOT/recipe['candidate'])and sha(target)==extraction['target_sha256']
    assert target.read_text()==extraction['wrapper']+'\n'.join(extraction['fragments'])+extraction['tail']
    for fragment in extraction['fragments']:assert candidate.count(fragment)==1
    for fragment in extraction['call_fragments']:assert candidate.count(fragment)==target.read_text().count(fragment)>0
    for source in V.iterdir():
        if source.suffix not in ('.cpp','.hpp'):continue
        text=source.read_text()
        for name in ['prepared_successor_tile','prepared_successor_cell','address_owner_valid','address_owner_frame','address_owner_plane','address_owner_tile','cell_owner_valid','cell_owner_frame','cell_owner_child_epoch','cell_owner_plane','cell_owner_tile','cell_owner_address']:
            assert not re.search(r'(?:NEW|SP)\('+name+r'\)\s*=(?!=)',text)
            assert 'BOTH('+name+','not in text
    packaging=json.loads((SRC/'packaging.json').read_text())
    assert packaging['schema']=='v126-producer-single-module-packaging-v1'and packaging['split_byte_offsets']==[]
    assert packaging['production_sha256']==sha(ROOT/recipe['candidate'])and packaging['fragments']==[dict(filename=Path(recipe['candidate']).name,bytes=len((ROOT/recipe['candidate']).read_bytes()),sha256=sha(ROOT/recipe['candidate']))]
    return recipe


def one(rows,kind):
    selected=[r for r in rows if r.get('type')==kind]
    assert len(selected)==1 and selected[0]['status']=='TEST_PASS',kind
    return selected[0]


def scalar_check(rows):
    value=one(rows,'v126_successor_scalar_verdict')
    cases=(1<<13)*4+65536;cancel_cases=4*8*5*7
    clocks=1+12*cases+9*cancel_cases+2*(4*8*7)
    assert value['exhaustive_full13_cases']==32768 and value['random_cases']==65536 and value['cases']==cases==98304
    assert value['clock_edges']==clocks==1190177 and value['hold_edges']==3*cases==294912 and value['cancel_cases']==cancel_cases==1120
    assert all(value[k]>0 for k in ('successor13_wrap_cases','plus2_wrap_cases','plane3_cases','y_cell11_truncation_cases','canceled_rom_value_changes'))
    assert value['new_payload_or_owner_forces']==0 and value['prepared_scalar_domain_is_natural_packets']is False
    return value


def monitor_check(value):
    events=value['events']
    assert len(events)==14 and all(isinstance(n,int)and n>=0 for n in events)
    assert sum(events)==value['monitored_clocks']==value['current_cache_checks']
    assert value['address_captures']==events[0]+events[2]+events[3]
    assert value['cell_consumes']==events[2]+events[3] and value['rom_samples']>=events[1]+events[7]
    assert all(value[k]>0 for k in ('address_captures','rom_samples','cell_consumes','held_owned_edges','earliest_mode2','earliest_skip','accepted_starts','blocked_raw_starts'))
    assert value['max_lookup_age']>=1 and value['added_public_cycles']==value['new_payload_or_owner_forces']==0


def generic_check(rows,primer_path):
    base=rows[0];owner=one(rows,'v119_producer_owner');lanes=one(rows,'v124_owner_lanes_verdict')
    campaign=one(rows,'v126_successor_campaign');monitor=one(rows,'v126_successor_generic_monitor')
    assert rows==[base,owner,lanes,campaign,monitor] and base['status']=='TEST_PASS'
    assert base['prepared_counter_cases']==2048 and base['cache_beats']>10000 and base['public_comparisons']>50000
    assert owner['cases']==9216 and owner['random_cases']==250000
    assert lanes['wire_cases']==466944 and lanes['random_fullwidth_cases']==65536 and lanes['state_cases']==8192
    assert lanes['mode_mask']==lanes['bank_ready_mask']==lanes['guard_mask']==15 and lanes['emit_mask']==3
    assert lanes['invalid_ready_true']>0 and lanes['unready_ready_true']>0
    assert lanes['clock_cases']==1152 and lanes['error67_cases']==192 and lanes['cancel_cases']==864 and lanes['wrap_cases']==16 and lanes['held_edges']==336 and lanes['response_contexts']==224
    assert lanes['added_public_cycles']==lanes['error_cycle_delta']==lanes['pair_skipped_edges']==lanes['old_checks_removed']==0 and lanes['prepared_domain_fixtures_are_natural_packets'] is False
    expected=dict(contexts=534,actual_clock_edges=3664,primer_clock_edges=1428,nonprimer_clock_edges=2236,
                  earliest_cases=24,walk_skip_advances=555,held_child_edges=21,nonterminal_advances=96,
                  cancel_cases=288,bad_owner_cases=48,stage_overlap_cases=72,unowned_bad_bound_cases=9,
                  empty_plane_cases=3,accepted_start_cases=3)
    assert all(campaign[k]==v for k,v in expected.items())
    assert campaign['new_payload_or_owner_forces']==0 and campaign['prepared_domain_is_natural_packets'] is False
    monitor_check(monitor)
    assert monitor['monitored_clocks']==275333 and monitor['monitored_clocks']-campaign['actual_clock_edges']==271669
    primers=[json.loads(line)for line in primer_path.read_text().splitlines()]
    assert len(primers)==1428
    phases={0:0,1:0,2:0}
    for i,row in enumerate(primers):
        phase=row['phase'];assert phase in phases;phases[phase]+=1
        assert row['type']=='prepared_producer_primer'and row['edge']==i+1 and row['equal'] is True
        assert (row['before_state'],row['after_state'])=={0:(3,4),1:(9,10),2:(10,11)}[phase]
        assert row['tile']==0 and row['address']==1
    assert phases=={0:510,1:486,2:432}and {r['plane']for r in primers}=={0,1,2}
    return dict(baseline=base,owner=owner,lanes=lanes,campaign=campaign,monitor=monitor,primer_trace_edges=len(primers))


def caller_check(rows):
    v=one(rows,'verdict');monitor=one(rows,'v126_successor_caller_monitor');cases=[r for r in rows if r.get('type')=='case']
    assert rows[-2:]==[v,monitor]
    assert v['vectors']==11 and v['cases']==22 and v['configurations']==2 and v['directed_checks']>=12
    assert v['dense_comparisons']>0 and v['directed_dense_comparisons']>0
    assert len(cases)==22 and all(r['status']=='PASS'and not r['pending_drain']and r['requests']==r['acks']for r in cases)
    monitor_check(monitor)
    return dict(verdict=v,monitor=monitor,case_rows=len(cases))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args()
    recipe=verify()
    if not args.run:print('V126_PRODUCER_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
    assert args.root_grant=='ROOT_V126_PRODUCER','Exact Root heavy execution grant required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v126-producer-'+stamp);build.mkdir()
    baseline=ROOT/'experiments/python-gamebub-v125/integration/results.json';assert sha(baseline)=='a06d14b48b89e672aa74c7675d21365cbf64e831f9327f4678e7ec7aee15e987'
    origins=json.loads(baseline.read_text())['source_origins']
    for meta in origins.values():assert sha(ROOT/meta['path'])==meta['sha256']
    excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh'}
    children=[ROOT/m['path']for a,m in origins.items()if Path(a).name not in excluded];assert len(children)==9
    vectors=ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv'
    packaging=ROOT/'fpga/experiments/cu66-v125-tile/packaging.json';policy=ROOT/'experiments/python-gamebub-v126/study-policy.json'
    vr=json.loads((SRC/'verification-recipe.json').read_text())
    originals=[ROOT/e['original']for e in vr['adapters']+vr['unchanged']]
    files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+children+originals+[ROOT/recipe['original'],Path(__file__).resolve(),ROOT/'scripts/cu66-v126/producer/prepare.py',ROOT/'scripts/cu66-v126/producer/prepare_verification.py',ROOT/'scripts/cu66-v126/integration/focused-runner-derivation.json',ROOT/'scripts/cu66-v125/tile/qualify.py',ROOT/'scripts/cu66-v124/owner/qualify.py',ROOT/'docs/cu66-v126/producer-design.md',ROOT/'docs/cu66-v126/verification-plan.md',baseline,vectors,packaging,policy]))
    assert all(p.is_file()for p in files)
    report=dict(schema='v126-producer-existing-edge-successor-focused-v1',status='RUNNING',actual_RTL_run=False,root_grant=args.root_grant,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],generic_runs=[],scalar_runs=[],caller_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,all_old_require_checks_retained=True,old_require_checks_removed=0,added_public_cycles=0,added_source_payload_bits=24,old_private_value_contract_changes=0,candidate_private_comparison_edits=0,new_payload_or_owner_forces=0,prepared_fixture_priming_edges_are_natural_cycles=False,candidate=dict(path=recipe['candidate'],sha256=recipe['candidate_sha256']),source_origins_baseline=origins,study_policy=dict(path=str(policy.relative_to(ROOT)),sha256=sha(policy)),backend='Verilator 5.020',image=IMAGE,build_external=str(build),limits=['Finite simulation is not formal proof, routed timing closure, CDC or hardware qualification.','Extracted full13 scalar and prepared-key domains are separate from reachable controller packets.'])
    started=time.monotonic()
    def persist():write(out/'receipt.json',report)
    def command(argv, name, cap, simulation=False):
        gate = memory()
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined'] < .85, gate
        container = 'gamebub-v126-producer-' + stamp.lower() + '-' + str(len(report['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container, '--memory', '8g', '--memory-swap', '8g', '--cpus', '2',
               '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0', '--mount', f'type=bind,src={build},dst=/work',
               '-w', '/work', IMAGE, 'timeout', '--kill-after=5s', str(cap)+'s', *argv]
        entry = dict(argv=cmd, resource_before=gate, timeout_seconds=cap, simulation=simulation)
        report['commands'].append(entry)
        if simulation:
            report['actual_RTL_run'] = True  # Persist BEFORE executing any simulation.
        persist()
        began = time.monotonic()
        process = None
        reason = None
        high_psi = 0
        with (out / name).open('w') as log, (out / (name+'.resources.jsonl')).open('w') as samples:
            try:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                while process.poll() is None:
                    sample = memory()
                    samples.write(json.dumps(sample, sort_keys=True)+'\n')
                    samples.flush()
                    high_psi = high_psi+1 if sample['psi_full_avg10'] >= 5 else 0
                    if sample['available_bytes'] < 4*GIB or sample['combined'] >= .9 or high_psi >= 2:
                        reason = 'RESOURCE_STOP'
                        raise RuntimeError(reason)
                    if time.monotonic()-began > cap+15:
                        reason = 'HOST_WATCHDOG'
                        raise RuntimeError(reason)
                    time.sleep(1)
                entry['exit_code'] = process.wait(timeout=10)
                assert entry['exit_code'] == 0, (name, entry['exit_code'])
            finally:
                if process is not None and process.poll() is None:
                    stopped = subprocess.run(['docker', 'stop', '--time', '3', container], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=12)
                    (out / (name+'.stop.log')).write_bytes(stopped.stdout)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=10)
                entry.update(wall_seconds=time.monotonic()-began, stop_reason=reason, resource_after=memory())
                persist()

    try:
        for p in files:
            target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        for p in V.iterdir():
            if p.suffix in ('.sv','.cpp','.hpp'):shutil.copyfile(p,build/p.name)
        for p in children:shutil.copyfile(p,build/p.name)
        data=next(p for p in children if p.name=='cs88_admission_v91i2a.sv').read_bytes();pack=json.loads(packaging.read_text());assert hashlib.sha256(data).hexdigest()==pack['production_sha256'];cuts=[0]+pack['split_byte_offsets']+[len(data)]
        for i,fragment in enumerate(pack['fragments']):
            p=build/fragment['filename'];p.write_bytes(data[cuts[i]:cuts[i+1]]);assert sha(p)==fragment['sha256']
        assert b''.join((build/f['filename']).read_bytes()for f in pack['fragments'])==data
        shutil.copyfile(vectors,build/'cases.tsv');report['lossless_admission_packaging']=pack
        report['compiled_source_sha256']={p.name:sha(p)for p in build.iterdir()if p.is_file()}
        command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020'in(out/'version.log').read_text()
        common=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I/work','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror']
        builds=[('producer_scalar_probe',['producer_scalar_probe.sv','tb_successor_scalar.cpp']),('ready_probe',[p.name for p in children]+[f['filename']for f in pack['fragments'][1:]]+['ready_original.sv','ready_candidate.sv','ready_probe.sv','tb_successor.cpp'])]
        report['binary_sha256']={}
        for top,names in builds:
            name=top+'-compile.log';command(common+['--top-module',top,'--Mdir','/work/'+top+'-obj',*['/work/'+n for n in names]],name,900)
            assert '%Warning-'not in(out/name).read_text();report['binary_sha256'][top]=sha(build/(top+'-obj')/('V'+top));persist()
        for seed in (126501,126502):
            name=f'scalar-{seed}.log';command(['/work/producer_scalar_probe-obj/Vproducer_scalar_probe',str(seed)],name,600,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];report['scalar_runs'].append(dict(seed=seed,verdict=scalar_check(rows)));persist()
        for seed in (126501,126502):
            name=f'generic-{seed}.log';command(['/work/ready_probe-obj/Vready_probe','generic',str(seed),'/work/cases.tsv',f'/work/{seed}-trace.csv'],name,900,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];result=generic_check(rows,build/'producer-primer.jsonl');result['seed']=seed;report['generic_runs'].append(result)
            (build/'producer-primer.jsonl').rename(build/(str(seed)+'-producer-primer.jsonl'));persist()
        for seed in (126601,126602):
            name=f'caller-{seed}.log';command(['/work/ready_probe-obj/Vready_probe','caller',str(seed),'/work/cases.tsv',f'/work/{seed}-trace.csv'],name,900,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];report['caller_runs'].append(dict(seed=seed,**caller_check(rows)));persist()
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p)for p in files},'sources changed during run'
        assert all(sha(out/'sources'/p.relative_to(ROOT))==sha(p)for p in files),'snapshot mismatch'
        report.update(status='PASS',frozen_after_focused_PASS=True)
    except BaseException as exc:
        report.update(status='FAIL',error_class=type(exc).__name__,error=str(exc));raise
    finally:
        for p in sorted([*build.glob('*.jsonl'),*build.glob('*.csv')]):
            with p.open('rb')as source,(out/(p.name+'.gz')).open('wb')as dest:
                with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0)as zipped:shutil.copyfileobj(source,zipped)
        report['wall_seconds']=time.monotonic()-started
        report['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
        report['artifacts_sha256']=report['artifact_sha256'];persist()
        write(AREA/'results.json',dict(status=report['status'],actual_RTL_run=report['actual_RTL_run'],path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')))
        print('V126_PRODUCER_FOCUSED',report['status'],out,flush=True)

if __name__=='__main__':main()
