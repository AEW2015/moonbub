#!/usr/bin/env python3
"""Strict paired V116/V129 parser qualification with finite resource gates."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V = HERE/'verification'
AREA = ROOT/'experiments/python-gamebub-v129/parser'
BUILD = Path('/home/lori/gamebub-build/cu66-v69')
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
VECTORS = ROOT/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz'
SEEDS = (129301,129302)
GIB = 1024**3
GATE_SHA = '4f9f5bdadf6337d253c3412b668a3579dc646d060208a3ead1570bfebdd18bed'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def write(path, obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def memory():
    m = {v.split(':')[0]:int(v.split()[1])*1024 for v in Path('/proc/meminfo').read_text().splitlines()}
    pressure = next(v for v in Path('/proc/pressure/memory').read_text().splitlines() if v.startswith('full '))
    return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(pressure.split('avg10=')[1].split()[0]),
                combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',action='store_true')
    ap.add_argument('--root-grant')
    args = ap.parse_args()
    for script in ('prepare.py','prepare_verification.py'):
        subprocess.run(['python3',str(HERE/script)],check=True,cwd=ROOT,stdout=subprocess.DEVNULL)
    recipe = json.loads((HERE/'edit-recipe.json').read_text())
    adapter = json.loads((V/'adapters.json').read_text())
    model = json.loads((HERE/'model-results.json').read_text())
    assert model['status']=='PASS_MODEL_ONLY' and model['candidate_sha256']==recipe['candidate']['sha256']
    assert sha(ROOT/'scripts/cu66-v128/integration/resource_gate.py')==GATE_SHA
    sources = sorted(set([HERE/'prepare.py',HERE/'prepare_verification.py',HERE/'model.py',HERE/'model-results.json',
                          HERE/'edit-recipe.json',HERE/'br88_rice_elastic.sv',Path(__file__).resolve(),VECTORS,
                          ROOT/'scripts/cu66-v128/integration/resource_gate.py',
                          ROOT/recipe['original']['path']]+list(V.glob('*'))+
                         [ROOT/'fpga/experiments/cu66-v116-rice/verification'/n for n in
                          ('rice_probe.sv','tb_rice.cpp','historical_rice.cpp','view_directed.cpp')]))
    assert all(p.is_file() for p in sources)
    if not args.run:
        print(json.dumps(dict(status='V129_PARSER_PREPARED_NOT_RUN',input_count=len(sources),
                              candidate=recipe['candidate'],seeds=SEEDS),sort_keys=True))
        return
    assert args.root_grant == 'ROOT_V129_PARSER'
    freeze=AREA/'freeze.json'
    frozen=json.loads(freeze.read_text())
    assert frozen['status']=='FROZEN_BEFORE_FOCUSED_RTL' and frozen['source_sha256']=={rel(p):sha(p) for p in sources}
    assert frozen['candidate_sha256']==recipe['candidate']['sha256'] and frozen['seeds']==list(SEEDS)
    sources=sorted(set(sources+[freeze]))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA/'attempts'/stamp
    out.mkdir(parents=True)
    build = BUILD/('v129-parser-'+stamp)
    build.mkdir()
    mapped = '/build/'+build.name
    original_hashes = {rel(p):sha(p) for p in sources}
    result = dict(schema='v129-rice-response-focused-v1',status='FAIL',actual_RTL_run=False,
                  candidate=recipe['candidate'],baseline=recipe['original'],image_id=IMAGE,
                  source_sha256=original_hashes,declared_public_cycle_delta=0,new_state_bits=0,
                  pre_run_freeze=dict(path=rel(freeze),sha256=sha(freeze)),
                  assertions_disabled_or_downgraded=False,original_assertions_retained=True,
                  full32_predicate_model=model,adapter=adapter,seeds=list(SEEDS),commands=[],runs=[],
                  memory_samples=[],launch_gate_waits=[],hardware_contact=False,
                  resource_policy=dict(cpus=2,memory_bytes=8*GIB,memory_swap_bytes=8*GIB,
                                       pids_limit=2048,compiler_jobs=1,max_heavy_jobs=1),
                  scope='Paired actual V116/V129 parser plus historical real-interface corpus and explicitly prepared private states. No full parent, native route, board, or FPGA speed claim.')
    started=time.monotonic()
    def receipt():
        write(out/'receipt.json',result)
    def command(argv,name,cap,rtl=False):
        waiting=[]
        gate_script=ROOT/'scripts/cu66-v128/integration/resource_gate.py'
        spec=importlib.util.spec_from_file_location('v128_ready_gate',gate_script)
        gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
        latest=gate.wait_ready(memory,waiting)
        result['launch_gate_waits'].append(dict(command=name,samples=waiting))
        assert latest['available_bytes']>=8*GIB and latest['psi_full_avg10']<1 and latest['combined_used_ratio']<.85, latest
        container='gamebub-v129-parser-'+stamp.lower()+'-'+str(len(result['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g',
             '--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0',
             '--mount',f'type=bind,src={out},dst={out},readonly',
             '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,
             'timeout','--kill-after=5s',str(cap)+'s',*argv]
        row=dict(argv=cmd,resource_before=latest,launch_gate_wait_samples=waiting,timeout_seconds=cap)
        result['commands'].append(row)
        if rtl: result['actual_RTL_run']=True
        receipt();begin=time.monotonic();high=0
        with (out/name).open('w') as log:
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            while proc.poll() is None:
                sample=dict(command=name,elapsed_seconds=time.monotonic()-begin,**memory())
                result['memory_samples'].append(sample)
                high=high+1 if sample['psi_full_avg10']>=5 else 0
                if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
                    row['resource_stop']=sample
                    subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15)
                    break
                time.sleep(2)
            row.update(exit_code=proc.wait(timeout=20),wall_seconds=time.monotonic()-begin)
        receipt()
        assert row['exit_code']==0 and 'resource_stop' not in row,name
    try:
        for source in sources:
            target=out/'sources'/source.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
        gate=ROOT/'scripts/cu66-v128/integration/resource_gate.py'
        result['readiness_helper']=dict(path=rel(gate),sha256=sha(gate))
        expanded=build/'rice-vectors.txt'; cases=requests=0
        with gzip.open(VECTORS,'rt') as source,expanded.open('w') as target:
            for line in source:
                c=json.loads(line)
                target.write(f"{c['id']} {c['bit_size']} {c['data_hex'] or '-'} {len(c['requests'])}\n")
                for req in c['requests']:target.write(' '.join(map(str,req))+'\n')
                cases+=1;requests+=len(c['requests'])
        shutil.copyfile(expanded,out/'rice-vectors.txt')
        result['expanded_vector_sha256']=sha(expanded)
        command(['verilator','--version'],'version.log',30)
        assert 'Verilator 5.020' in (out/'version.log').read_text()
        snap=out/'sources'/V.relative_to(ROOT)
        names=['rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp']
        command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw',
                 '--output-split','10000','--output-split-cfuncs','500','--language','1800-2017',
                 '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror', '--top-module','rice_probe',
                 '--Mdir',mapped+'/obj',*[str(snap/n) for n in names]],'compile.log',900)
        assert '%Warning-' not in (out/'compile.log').read_text()
        binary=build/'obj/Vrice_probe';result['model_binary_sha256']=sha(binary)
        for seed in SEEDS:
            command([mapped+'/obj/Vrice_probe',str(seed),mapped+f'/trace-{seed}.jsonl',mapped+'/rice-vectors.txt'],
                    f'parser-{seed}.log',600,rtl=True)
            lines=[json.loads(line) for line in (out/f'parser-{seed}.log').read_text().splitlines()]
            verdict=lines[-1];historic=next(x for x in lines if x.get('type')=='verdict')
            assert verdict['status']=='TEST_PASS' and verdict['seed']==seed
            assert verdict['parameter_cases']==6096 and verdict['prepared_clocks']>100000 and verdict['view_directed_checks']>=600
            assert historic['status']=='TEST_PASS' and historic['cases']==cases==1520
            assert historic['requests_per_configuration']==requests==173061 and historic['configurations']==8 and historic['directed_checks']==104
            result['runs'].append(dict(seed=seed,verdict=verdict,historical=historic))
            receipt()
        assert sha(gate)==result['readiness_helper']['sha256']
        assert sha(expanded)==sha(out/'rice-vectors.txt')==result['expanded_vector_sha256']
        assert sha(binary)==result['model_binary_sha256']
        assert all(sha(ROOT/p)==h and sha(out/'sources'/p)==h for p,h in original_hashes.items())
        result['compiled_input_snapshots_unchanged']=True
        result['source_snapshots_unchanged']=True
        result['status']='PASS'
    except BaseException as exc:
        result['error']=repr(exc)
        raise
    finally:
        for p in build.glob('trace-*.jsonl'):
            (out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
        result['wall_seconds']=time.monotonic()-started
        result['artifact_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*'))
                                   if p.is_file() and p.name!='receipt.json'}
        receipt()
        if result['status']=='PASS':
            write(AREA/'results.json',dict(status='PASS',actual_RTL_run=True,path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
        print('V129_PARSER',result['status'],rel(out),flush=True)


if __name__ == '__main__':
    main()
