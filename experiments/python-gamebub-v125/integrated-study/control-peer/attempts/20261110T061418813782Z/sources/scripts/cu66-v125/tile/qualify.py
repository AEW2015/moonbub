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
SRC = ROOT / 'fpga/experiments/cu66-v125-tile'
V=SRC/'verification'
AREA = ROOT / 'experiments/python-gamebub-v125/tile'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    temp = p.with_name(p.name + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')
    temp.replace(p)



def verify():
    """Read-only reconstruction; never invoke a preparer after proof freeze."""
    import collections,re
    runner_path=ROOT/'scripts/cu66-v125/integration/focused-runner-derivation.json'
    runner=json.loads(runner_path.read_text())
    assert runner['schema']=='v125-focused-runner-derivation-v1'
    assert sha(ROOT/runner['caller_runner_provenance']['path'])==runner['caller_runner_provenance']['sha256']
    recipe=json.loads((SRC/'edit-recipe.json').read_text())
    v=json.loads((SRC/'verification-recipe.json').read_text())
    def reversible(meta):
        before=ROOT/meta['original'];after=ROOT/meta['candidate']
        assert sha(before)==meta['original_sha256'] and sha(after)==meta['candidate_sha256']
        text=before.read_text()
        for e in meta['edits']:
            assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
        assert text==after.read_text()
        for e in reversed(meta['edits']):
            assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
        assert text==before.read_text()
    for meta in runner['sources']:
        reversible(meta)
    reversible(recipe)
    for e in v['adapters']:reversible(e)
    for e in v['unchanged']:assert sha(ROOT/e['original'])==sha(ROOT/e['candidate'])==e['sha256']
    assert len(v['new_verification_inputs'])==5
    for e in v['new_verification_inputs']:assert sha(ROOT/e['path'])==e['sha256']
    checks=lambda s:collections.Counter(re.findall(r'require\(.*?\);',s,re.S))
    for e in v['adapters']:
        if e['original'].endswith('.cpp'):assert not checks((ROOT/e['original']).read_text())-checks((ROOT/e['candidate']).read_text())
    assert recipe['added_source_payload_bits']==3 and recipe['added_public_cycles']==recipe['added_synthesis_attributes']==recipe['old_assertions_removed']==recipe['old_private_value_contract_changes']==0
    assert v['old_require_checks_removed']==v['new_predicate_or_owner_forces']==0 and v['prepared_key_priming_is_natural_traffic'] is False
    original=(ROOT/recipe['original']).read_text();candidate=(ROOT/recipe['candidate']).read_text()
    assert re.findall(r'\(\*(.*?)\*\)',original,re.S)==re.findall(r'\(\*(.*?)\*\)',candidate,re.S)
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):assert block in candidate
    e=v['scalar_extraction'];assert sha(ROOT/e['source'])==e['source_sha256'] and sha(ROOT/e['target'])==e['target_sha256']
    assert (ROOT/e['target']).read_text()==e['wrapper']+'\n'.join(e['fragments'])+e['tail']
    for part in e['fragments']:assert candidate.count(part)==1
    assert len(e['terminal_call_fragments'])==2
    for part in e['terminal_call_fragments']:assert candidate.count(part)==1 and (ROOT/e['target']).read_text().count(part)==1
    for helper in V.glob('*'):
        if helper.suffix not in ('.cpp','.hpp'):continue
        text=helper.read_text()
        for name in ['prepared_tile_hidden','prepared_tile_terminal','prepared_group_terminal','tile_pred_owner_valid','tile_pred_owner_epoch','tile_pred_owner_plane','tile_pred_owner_tile','group_pred_owner_valid','group_pred_owner_epoch','group_pred_owner_plane','group_pred_owner_tile','group_pred_owner_end']:
            assert not re.search(r'(?:QNEW|TM)\('+name+r'\)\s*=(?!=)',text)
            assert 'QBOTH('+name+',' not in text
    p=json.loads((SRC/'packaging.json').read_text());data=(ROOT/recipe['candidate']).read_bytes()
    assert p['schema']=='v125-lossless-admission-packaging-v1' and p['production_sha256']==sha(ROOT/recipe['candidate']) and len(p['fragments'])==3
    cuts=[0]+p['split_byte_offsets']+[len(data)]
    for i,f in enumerate(p['fragments']):assert f['bytes']==cuts[i+1]-cuts[i] and hashlib.sha256(data[cuts[i]:cuts[i+1]]).hexdigest()==f['sha256']
    for name in ('tb_scalar.cpp','tb_tile.cpp','tb_caller.cpp'):assert (V/name).is_file(),name
    return recipe


def one(rows,kind):
    selected=[r for r in rows if r.get('type')==kind]
    assert len(selected)==1 and selected[0]['status']=='TEST_PASS',kind
    return selected[0]


def scalar_check(rows):
    s=one(rows,'v125_tile_scalar_verdict')
    values=set(range(8192))
    for bit in range(13,32):
        n=1<<bit;values.update([n-1,n,n+1,n+633,n+1350,n+5400])
    values.update([0xfffffff0,0xfffffff1,0xfffffffe,0xffffffff])
    boundary=4*len(values)*7;cases=boundary+65536
    assert s['boundary_cases']==boundary and s['random_full32_cases']==65536 and s['cases']==cases
    assert s['terminal_transition_cases']==8 and s['clock_edges']==1+19*cases+16 and s['hold_edges']==2*cases and s['cancel_cases']==7*cases
    assert all(s[f]>0 for f in ('highbit_cases','plane3_cases','uint32_plus16_wrap_cases','hidden_true','terminal_true','group_true'))
    assert s['new_predicate_or_owner_forces']==0 and s['extracted_domain_is_natural_packets'] is False
    return s


def generic_check(rows,primer_path):
    verdict=one(rows,'verdict');owner=one(rows,'v119_mode_bound');boundary=one(rows,'v116_chunk_boundaries')
    match=one(rows,'v120_header_match_verdict');bounds=one(rows,'v122_bounds_verdict')
    ledger=one(rows,'v125_retained_mode_ledger');tile=one(rows,'v125_tile_verdict')
    assert owner['cases']==540 and boundary['cases']==25344 and boundary['cancellation_cases']==294
    assert verdict['prepared_edges']==348673 and verdict['header_prepared_edges']==738933 and verdict['scale_prepared_edges']==40585
    assert ledger['semantic_cases']==158228 and ledger['original_clock_edges']==158230 and ledger['primer_clock_edges']>0
    assert ledger['total_clock_edges']==ledger['original_clock_edges']+ledger['primer_clock_edges']==verdict['mode_prepared_edges']
    assert match['prepared_full35_cases']==67664 and match['random_full35']==65536 and match['owned_consumes']==4096
    assert all(match[k]>0 for k in ('high32_alias_rejections','true_cases','false_cases','canceled_captures','fixture_priming_edges'))
    assert match['idle_hold_edges']==135328 and match['natural_packets']==match['natural_nonreset_retries']==36
    assert match['old_require_checks_removed']==match['added_natural_public_cycles']==0 and match['prepared_predicate_contexts_are_natural_packets'] is False
    assert bounds['random_full32_cases']==16384 and bounds['cancellation_cases']==56
    assert all(bounds[k]>0 for k in ('full64_high32_cases','uint32_wrap_cases','fixture_priming_edges'))
    assert bounds['added_natural_public_cycles']==bounds['old_require_checks_removed']==0 and bounds['prepared_domain_fixtures_are_natural_packets'] is False
    campaign=one(rows,'v125_tile_campaign')
    expected=dict(contexts=411,semantic_clock_edges=852,primer_clock_edges=411,total_clock_edges=1263,
                  cancel_cases=189,first_followup_consumes=19,malformed_contexts=3,speculative_mode_checks=2)
    assert all(campaign[k]==v for k,v in expected.items()) and campaign['prepared_domain_fixtures_are_natural_packets'] is False
    for key in ('natural_writers','prepared_writers','first_consume_counts','overwritten_before_consume'):
        assert len(tile[key])==9 and all(isinstance(n,int)and n>=0 for n in tile[key])
    assert all(a+b>0 for a,b in zip(tile['natural_writers'],tile['prepared_writers']))
    assert all(tile['first_consume_counts'][i]>0 for i in range(7)) and tile['overwritten_before_consume'][7]>0
    assert tile['first_consume_counts'][7:]==[0,0]
    assert len(tile['cancel_counts'])==8 and all(n>0 for n in tile['cancel_counts'][1:])
    assert len(tile['cancel_state_counts'])==33 and all(len(row)==8 and all(n>0 for n in row[1:])for row in tile['cancel_state_counts'])
    assert tile['total_primer_clock_edges']==ledger['primer_clock_edges']+411
    assert tile['prepared_monitored_clock_edges']==158228+tile['total_primer_clock_edges']+852
    assert tile['monitored_clock_edges']==tile['natural_clock_edges']+tile['prepared_monitored_clock_edges']
    assert all(tile[k]>0 for k in ('natural_clock_edges','hold_edges','consume_edges','natural_start_edges'))
    assert tile['new_predicate_or_owner_forces']==tile['old_require_checks_removed']==tile['added_natural_public_cycles']==0
    assert tile['prepared_domain_fixtures_are_natural_packets'] is False
    modes=[r for r in rows if 'type'not in r and r.get('final_mode_entries')==8100]
    assert len(modes)==1 and modes[0]['cases']==158228 and modes[0]['clock_edges']==ledger['total_clock_edges']
    primers=[json.loads(line)for line in primer_path.read_text().splitlines()]
    assert len(primers)==tile['total_primer_clock_edges']
    assert all(r['type']=='prepared_key_primer'and r['edge']==i+1 and r['real_writer_state']==8 and r['next_state']==10 and r['equal'] is True for i,r in enumerate(primers))
    assert {0,6,10,11}=={r['target_state']for r in primers}
    return dict(terminal_verdict=verdict,owned_mode_bound=owner,boundary=boundary,header_match=match,
                bounds=bounds,mode_ledger=ledger,tile_campaign=campaign,tile=tile,raw_mode_verdict=modes[0])


def caller_check(rows):
    verdict=one(rows,'verdict');cases=[r for r in rows if r.get('type')=='case']
    assert verdict['vectors']==11 and verdict['cases']==22 and verdict['configurations']==2 and verdict['directed_checks']>=12
    assert verdict['dense_comparisons']>0 and verdict['directed_dense_comparisons']>0
    assert len(cases)==22 and all(r['status']=='PASS' and not r['pending_drain'] and r['requests']==r['acks'] for r in cases)
    return dict(verdict=verdict,case_rows=len(cases))

def memory():
    raw = Path('/proc/meminfo').read_text()
    mem = {x.split(':')[0]:int(x.split()[1])*1024 for x in raw.splitlines()}
    pressure = Path('/proc/pressure/memory').read_text()
    full = next(x for x in pressure.splitlines() if x.startswith('full '))
    # Combined host memory+swap utilization; swap is not added to containers.
    combined = (mem['MemTotal'] - mem['MemAvailable'] + mem['SwapTotal'] - mem['SwapFree']) / (mem['MemTotal'] + mem['SwapTotal'])
    return dict(monotonic=time.monotonic(), available_bytes=mem['MemAvailable'], psi_full_avg10=float(full.split('avg10=')[1].split()[0]),
                combined=combined, meminfo=raw, memory_pressure=pressure)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod



def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args()
    recipe=verify()
    if not args.run:print('V125_TILE_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
    assert args.root_grant=='ROOT_V125_TILE','Exact Root heavy execution grant required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v125-tile-'+stamp);build.mkdir()
    baseline=ROOT/'experiments/python-gamebub-v124/integration/results.json';assert sha(baseline)=='9514c117b7a3769babb3cb4bc9b1c6b4bf355212203c710695696b7b63fcf33f'
    origins=json.loads(baseline.read_text())['source_origins']
    for meta in origins.values():assert sha(ROOT/meta['path'])==meta['sha256']
    excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh','cs88_admission_v91i2a.sv'}
    children=[ROOT/m['path']for a,m in origins.items()if Path(a).name not in excluded];assert len(children)==8
    vectors=ROOT/'experiments/python-gamebub-v91i/vectors/vectors.txt';caller_vectors=ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv'
    policy=ROOT/'experiments/python-gamebub-v125/study-policy.json'
    helpers=[ROOT/p for p in ['scripts/cu66-v107/tables.py','scripts/cu66-v100/run_rtl.py','scripts/cu66-v107/header/replay.py','scripts/cu66-v107/tables/mode_replay.py','experiments/python-gamebub-v91i/admission-model.py','experiments/cu66-native-v69/generated_constants.hpp']]
    vr=json.loads((SRC/'verification-recipe.json').read_text())
    originals=[ROOT/e['original']for e in vr['adapters']+vr['unchanged']]
    files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+children+originals+helpers+[ROOT/recipe['original'],Path(__file__).resolve(),ROOT/'scripts/cu66-v125/tile/prepare.py',ROOT/'scripts/cu66-v125/tile/prepare_verification.py',ROOT/'scripts/cu66-v125/integration/focused-runner-derivation.json',ROOT/'scripts/cu66-v122/bounds/qualify.py',ROOT/'scripts/cu66-v124/owner/qualify.py',ROOT/'docs/cu66-v125/tile-design.md',ROOT/'docs/cu66-v125/verification-plan.md',baseline,vectors,caller_vectors,policy]))
    assert all(p.is_file()for p in files)
    report=dict(schema='v125-tile-existing-edge-predicates-focused-v1',status='RUNNING',actual_RTL_run=False,root_grant=args.root_grant,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],generic_runs=[],scalar_runs=[],caller_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,all_old_require_checks_retained=True,old_require_checks_removed=0,added_public_cycles=0,added_source_payload_bits=3,old_private_value_contract_changes=0,candidate_private_comparison_edits=0,new_predicate_or_owner_forces=0,prepared_fixture_priming_edges_are_natural_cycles=False,candidate=dict(path=recipe['candidate'],sha256=recipe['candidate_sha256']),source_origins_baseline=origins,study_policy=dict(path=str(policy.relative_to(ROOT)),sha256=sha(policy)),backend='Verilator 5.020',image=IMAGE,build_external=str(build),limits=['Finite simulation is not formal proof, routed timing closure, CDC or hardware qualification.','Extracted scalar and prepared-key domains are separate from reachable controller packets.'])
    started=time.monotonic()
    def persist():write(out/'receipt.json',report)
    def command(argv, name, cap, simulation=False):
        gate = memory()
        assert gate['available_bytes'] >= 8*GIB and gate['psi_full_avg10'] < 1 and gate['combined'] < .85, gate
        container = 'gamebub-v125-tile-' + stamp.lower() + '-' + str(len(report['commands']))
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
        # Whole-source adapters are retained. The compile copy shares byte-identical helpers.
        for variant in ('admission_original','admission_candidate','controller_admission_original','controller_admission_candidate'):
            p=build/(variant+'.sv');text=p.read_text();a=text.index('module cu66_scale_tdp_v107 (');b=text.index('module cu66_mode_store_v107 (')
            for name,piece in [('cu66_scale_tdp_v107.sv',text[a:b]),('cu66_mode_store_v107.sv',text[b:])]:
                target=build/name
                if target.exists():assert target.read_text()==piece
                else:target.write_text(piece)
            p.write_text(text[:a]);assert p.read_text()+(build/'cu66_scale_tdp_v107.sv').read_text()+(build/'cu66_mode_store_v107.sv').read_text()==text
        shutil.copyfile(vectors,build/'vectors.txt');shutil.copyfile(caller_vectors,build/'cases.tsv')
        report['compiled_source_sha256']={p.name:sha(p)for p in build.iterdir()if p.is_file()}
        command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020' in(out/'version.log').read_text()
        common=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I/work','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror']
        builds=[('scalar_probe',['scalar_probe.sv','tb_scalar.cpp']),('admission_probe',['admission_original.sv','admission_candidate.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv','admission_probe.sv','tb_tile.cpp']),('ready_probe',[p.name for p in children]+['ready_original.sv','ready_candidate.sv','controller_admission_original.sv','controller_admission_candidate.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv','ready_probe.sv','tb_caller.cpp'])]
        report['binary_sha256']={}
        for top,names in builds:
            name=top+'-compile.log';command(common+['--top-module',top,'--Mdir','/work/'+top+'-obj',*['/work/'+n for n in names]],name,900)
            assert '%Warning-'not in(out/name).read_text();report['binary_sha256'][top]=sha(build/(top+'-obj')/('V'+top));persist()
        for seed in (125501,125502):
            name=f'scalar-{seed}.log';command(['/work/scalar_probe-obj/Vscalar_probe',str(seed)],name,600,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];report['scalar_runs'].append(dict(seed=seed,verdict=scalar_check(rows)));persist()
        snapshot=out/'sources';sys.path[:0]=[str(snapshot/'scripts/cu66-v100'),str(snapshot/'scripts/cu66-v107/header'),str(snapshot/'scripts/cu66-v107/tables')]
        replay=load_module(snapshot/'scripts/cu66-v107/tables.py','v125_frozen_independent_tables')
        for seed in (125501,125502):
            name=f'generic-{seed}.log';command(['/work/admission_probe-obj/Vadmission_probe','/work/vectors.txt',str(seed)],name,900,simulation=True)
            rows=[json.loads(line)for line in(out/name).read_text().splitlines()];result=generic_check(rows,build/'tile-primer.jsonl');result['seed']=seed
            result.update(coordinate=replay.replay(build/'trace.jsonl',snapshot/vectors.relative_to(ROOT)),quant=replay.quant_replay(build/'trace.jsonl',snapshot/vectors.relative_to(ROOT)),scale=replay.scale_replay(build/'scale-ports.csv'),mode=replay.mode_replay(build/'mode-ports.jsonl',seed))
            report['generic_runs'].append(result)
            for stem in ('trace.jsonl','scale-ports.csv','mode-ports.jsonl','match-natural-trace.jsonl','tile-primer.jsonl','tile-writers.jsonl'):
                p=build/stem
                if p.exists():p.rename(build/(str(seed)+'-'+stem))
            persist()
        for seed in (125601,125602):
            name=f'caller-{seed}.log';command(['/work/ready_probe-obj/Vready_probe','/work/cases.tsv',str(seed),f'/work/{seed}-trace.csv'],name,900,simulation=True)
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
        print('V125_TILE_FOCUSED',report['status'],out,flush=True)

if __name__=='__main__':main()
