#!/usr/bin/env python3
"""Strict bounded three-lane owner-selection proof. Default verifies recipes; --run needs Root grant."""
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
SRC = ROOT / 'fpga/experiments/cu66-v127-owner'
V=SRC/'verification'
AREA = ROOT / 'experiments/python-gamebub-v127/owner'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    temp = p.with_name(p.name + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    temp.replace(p)




def verify():
    """Read-only recipe closure; no preparation, source writes, builds or simulation."""
    import collections,re
    spec=importlib.util.spec_from_file_location('v127_owner_contract',ROOT/'scripts/cu66-v127/integration/contract.py')
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);production=c.verify_owner()
    vr=json.loads((SRC/'verification-recipe.json').read_text());runner=json.loads((ROOT/'scripts/cu66-v127/integration/focused-runner-derivation.json').read_text())
    def reversible(meta):
        before,after=ROOT/meta['original'],ROOT/meta['candidate']
        assert sha(before)==meta['original_sha256']and sha(after)==meta['candidate_sha256']
        text=before.read_text()
        for edit in meta['edits']:
            assert text.count(edit['before'])==1;text=text.replace(edit['before'],edit['after'],1)
        assert text==after.read_text()
        for edit in reversed(meta['edits']):
            assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
        assert text==before.read_text()
    for meta in runner['sources']+vr['adapters']:reversible(meta)
    assert vr['schema']=='v127-owner-selection-verification-derivation-v1'
    assert vr['old_require_checks_removed']==vr['new_payload_or_owner_forces']==vr['added_public_cycles']==0
    checks=lambda text:collections.Counter(re.findall(r'(?:need|require_owner|factor_need)\(.*?\);',text,re.S))
    assert len(vr['adapters'])==9 and len(vr['unchanged'])==4 and len(vr['new_verification_inputs'])==3
    for meta in vr['adapters']:
        if Path(meta['original']).suffix in ('.cpp','.hpp'):
            assert not checks((ROOT/meta['original']).read_text())-checks((ROOT/meta['candidate']).read_text())
    for meta in vr['unchanged']:assert sha(ROOT/meta['original'])==sha(ROOT/meta['candidate'])==meta['sha256']
    for meta in vr['new_verification_inputs']:assert sha(ROOT/meta['path'])==meta['sha256']
    e=vr['scalar_extraction'];candidate=(ROOT/e['source']).read_text();target=ROOT/e['target']
    assert sha(ROOT/e['source'])==e['source_sha256']and sha(target)==e['target_sha256']
    base_path=ROOT/e['baseline_stage_recipe'];assert sha(base_path)==e['baseline_stage_recipe_sha256']
    base=json.loads(base_path.read_text())['scalar_extraction'];old=ROOT/base['target'];assert sha(old)==base['target_sha256']
    expected=old.read_text().replace('module producer_scalar_probe (\n','module producer_scalar_probe (\n'+e['wrapper_ports'],1)
    expected=expected.replace('endmodule',e['wrapper_tail']+'endmodule',1);assert target.read_text()==expected
    assert e['bindings']=={'current_child_epoch':'owner_expected_epoch'}
    for fragment in e['fragments']:
        assert candidate.count(fragment)==1
        bound=fragment
        for before,after in e['bindings'].items():bound=re.sub(r'\b'+re.escape(before)+r'\b',after,bound)
        assert target.read_text().count(bound)==1
    assert sha(ROOT/e['mode_source'])==e['mode_source_sha256']and (ROOT/e['mode_source']).read_text().count(e['mode_fragment'])==1 and target.read_text().count(e['mode_fragment'])==1
    old_expression=e['original_owner_expression']
    for before,after in e['bindings'].items():old_expression=re.sub(r'\b'+re.escape(before)+r'\b',after,old_expression)
    assert target.read_text().count(old_expression)==1
    prior_source=(ROOT/base['source']).read_text()
    for fragment in base['fragments']+base['call_fragments']:assert candidate.count(fragment)==prior_source.count(fragment)>0
    for meta in vr['new_verification_inputs']:
        source=(ROOT/meta['path']).read_text()
        for name in ('prepared_successor_tile','prepared_successor_cell','address_owner_valid','address_owner_frame','address_owner_plane','address_owner_tile','cell_owner_valid','cell_owner_frame','cell_owner_child_epoch','cell_owner_plane','cell_owner_tile','cell_owner_address','scalar_owner_match','tile_owner_match','child_owner_match'):
            assert not re.search(r'(?:NEW|SP)\('+name+r'\)\s*=(?!=)',source)and 'BOTH('+name+','not in source
        assert 'BS(outstanding,'not in source
    primary=next(r for r in production['sources']if r['alias']==c.PRODUCER_ALIAS)
    return dict(production,candidate=primary['candidate'],candidate_sha256=primary['candidate_sha256'],original=primary['original'])


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
    assert monitor['monitored_clocks']==275334 and monitor['monitored_clocks']-campaign['actual_clock_edges']==271670
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


def owner_scalar_check(rows):
    assert len(rows)==2
    inherited=scalar_check(rows[:-1]);v=one(rows,'v127_owner_factor_scalar_verdict')
    assert rows==[inherited,v]
    assert v['boundary_cases']==24576 and v['random_cases']==65536 and v['cases']==v['clock_edges']==90112 and v['eval_checks']==270336
    assert v['mode_mask']==15 and v['emit_mask']==3
    assert all(v[k]>0 for k in ('true_cases','false_cases','scalar_only_match_cases','bank_only_match_cases'))
    assert v['true_cases']+v['false_cases']==v['cases'] and v['new_predicate_forces']==0 and v['extracted_scalar_domain_is_natural_packets']is False
    return dict(verdict=inherited,owner_factor=v)


def owner_generic_check(rows,primer_path):
    assert len(rows)==6
    inherited=generic_check(rows[:-1],primer_path);v=one(rows,'v127_owner_factor_verdict');assert rows[-1]==v
    expected=dict(wire_cases=425984,random_cases=32768,clock_cases=1152,cancel_cases=864,error67_cases=192,wrap_cases=16,inherited_monitored_clock_edges=275334,additional_clock_edges=2308,reset_primer_edges=1156,mode_mask=15,emit_mask=3,bank_ready_mask=15,guard_mask=15)
    assert all(v[k]==n for k,n in expected.items())
    assert v['additional_clock_edges']==v['clock_cases']+v['reset_primer_edges']
    assert all(v[k]>0 for k in ('all_cycle_identity_evals','scalar_true','scalar_false','invalid_selected_match','unready_selected_match'))
    assert v['added_public_cycles']==v['pair_skipped_edges']==v['old_checks_removed']==v['new_predicate_forces']==0 and v['prepared_fixtures_are_natural_packets']is False
    return dict(inherited,owner_factor=v)


def owner_caller_check(rows):
    inherited=caller_check(rows[:-1]);v=one(rows,'v127_owner_factor_caller_verdict');assert rows[-1]==v
    assert v['clock_edges']>0 and v['eval_checks']>v['clock_edges'] and v['scalar_true']>0 and v['scalar_false']>0
    assert 0<v['mode_mask']<=15 and 0<v['emit_mask']<=3
    assert v['added_public_cycles']==v['pair_skipped_edges']==v['new_predicate_forces']==0 and v['natural_actual_controller']is True
    return dict(inherited,owner_factor=v)


def memory():
    raw = Path('/proc/meminfo').read_text()
    mem = {x.split(':')[0]:int(x.split()[1])*1024 for x in raw.splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(x for x in pressure.splitlines() if x.startswith('full '))
    # Combined host memory+swap utilization; swap is not added to containers.
    combined = (mem['MemTotal'] - mem['MemAvailable'] + mem['SwapTotal'] - mem['SwapFree']) / (mem['MemTotal'] + mem['SwapTotal'])
    return dict(monotonic=time.monotonic(), available_bytes=mem['MemAvailable'], psi_full_avg10=float(full.split('avg10=')[1].split()[0]),
                combined=combined, meminfo=raw, memory_pressure=pressure)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args()
    recipe=verify()
    if not args.run:print('V127_OWNER_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
    assert args.root_grant=='ROOT_V127_OWNER','Exact Root heavy execution grant required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v127-owner-'+stamp);build.mkdir()
    baseline=ROOT/'experiments/python-gamebub-v126/integration/results.json';assert sha(baseline)=='7d534c343732bc50786bff874c9b6d536bceaa6298fc5e7f002d98b5216e732f'
    origins=json.loads(baseline.read_text())['source_origins']
    for meta in origins.values():assert sha(ROOT/meta['path'])==meta['sha256']
    excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh'}
    changes=json.loads((SRC/'source-map.json').read_text())['source_origins']
    children=[ROOT/changes.get(a,m)['path']for a,m in origins.items()if Path(a).name not in excluded];assert len(children)==9
    vectors=ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv'
    packaging=ROOT/'fpga/experiments/cu66-v125-tile/packaging.json';policy=ROOT/'experiments/python-gamebub-v127/study-policy.json'
    vr=json.loads((SRC/'verification-recipe.json').read_text())
    originals=[ROOT/e['original']for e in vr['adapters']+vr['unchanged']]+[ROOT/m['original']for m in recipe['sources']]
    originals += [ROOT/vr['scalar_extraction']['baseline_stage_recipe'],ROOT/'scripts/cu66-v127/integration/contract.py',ROOT/'scripts/cu66-v126/producer/qualify.py']
    files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+children+originals+[ROOT/recipe['original'],Path(__file__).resolve(),ROOT/'scripts/cu66-v127/owner/prepare.py',ROOT/'scripts/cu66-v127/owner/prepare_verification.py',ROOT/'scripts/cu66-v127/integration/focused-runner-derivation.json',ROOT/'scripts/cu66-v125/tile/qualify.py',ROOT/'scripts/cu66-v124/owner/qualify.py',ROOT/'docs/cu66-v127/owner-design.md',ROOT/'docs/cu66-v127/verification-plan.md',baseline,vectors,packaging,policy]))
    assert all(p.is_file()for p in files)
    report=dict(schema='v127-owner-selection-three-lane-focused-v1',status='RUNNING',actual_RTL_run=False,root_grant=args.root_grant,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],generic_runs=[],scalar_runs=[],caller_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,all_old_require_checks_retained=True,old_require_checks_removed=0,added_public_cycles=0,added_source_payload_bits=0,retained_V126_source_payload_bits=24,old_private_value_contract_changes=0,candidate_private_comparison_edits=1,new_payload_or_owner_forces=0,prepared_fixture_priming_edges_are_natural_cycles=False,candidate=dict(path=recipe['candidate'],sha256=recipe['candidate_sha256']),candidate_sources={a:dict(path=m['path'],sha256=m['sha256'])for a,m in changes.items()},source_origins_baseline=origins,study_policy=dict(path=str(policy.relative_to(ROOT)),sha256=sha(policy)),backend='Verilator 5.020',image=IMAGE,build_external=str(build),limits=['Finite simulation is not formal proof, routed timing closure, CDC or hardware qualification.','Extracted full13 scalar and prepared-key domains are separate from reachable controller packets.'])
    started=time.monotonic()
    def persist():write(out/'receipt.json',report)
    def command(argv, name, cap, simulation=False):
        gate = memory()
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined'] < .85, gate
        container = 'gamebub-v127-owner-' + stamp.lower() + '-' + str(len(report['commands']))
        cmd = ['docker', 'run', '--rm', '--init', '--name', container, '--memory', '8g', '--memory-swap', '8g', '--cpus', '2',
               '--pids-limit', '2048', '--network', 'none', '--ulimit', 'core=0', '--mount', f'type=bind,src={build},dst=/work',
               '-w', '/work', IMAGE, 'timeout', '--kill-after=5s', str(cap)+'s', *argv]
        entry = dict(argv=cmd, resource_before=gate, timeout_seconds=cap, simulation=simulation)
        report['commands'].append(entry)
        persist()
        began = time.monotonic()
        process = None
        reason = None
        high_psi = 0
        with (out / name).open('w') as log, (out / (name+'.resources.jsonl')).open('w') as samples:
            try:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
                if simulation:report['actual_RTL_run']=True;persist()
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
        builds=[('producer_scalar_probe',['producer_scalar_probe.sv','tb_owner_scalar.cpp']),('ready_probe',[p.name for p in children]+[f['filename']for f in pack['fragments'][1:]]+['ready_original.sv','ready_candidate.sv','ready_probe.sv','tb_owner_factor.cpp'])]
        report['binary_sha256']={}
        for top,names in builds:
            name=top+'-compile.log';command(common+['--top-module',top,'--Mdir','/work/'+top+'-obj',*['/work/'+n for n in names]],name,900)
            assert '%Warning-'not in(out/name).read_text();report['binary_sha256'][top]=sha(build/(top+'-obj')/('V'+top));persist()
        for seed in (127501,127502):
            name=f'scalar-{seed}.log';command(['/work/producer_scalar_probe-obj/Vproducer_scalar_probe',str(seed)],name,600,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];report['scalar_runs'].append(dict(seed=seed,**owner_scalar_check(rows)));persist()
        for seed in (127501,127502):
            name=f'generic-{seed}.log';command(['/work/ready_probe-obj/Vready_probe','generic',str(seed),'/work/cases.tsv',f'/work/{seed}-trace.csv'],name,900,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];result=owner_generic_check(rows,build/'producer-primer.jsonl');result['seed']=seed;report['generic_runs'].append(result)
            (build/'producer-primer.jsonl').rename(build/(str(seed)+'-producer-primer.jsonl'));persist()
        for seed in (127601,127602):
            name=f'caller-{seed}.log';command(['/work/ready_probe-obj/Vready_probe','caller',str(seed),'/work/cases.tsv',f'/work/{seed}-trace.csv'],name,900,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];report['caller_runs'].append(dict(seed=seed,**owner_caller_check(rows)));persist()
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
        print('V127_OWNER_FOCUSED',report['status'],out,flush=True)

if __name__=='__main__':main()
