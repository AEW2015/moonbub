#!/usr/bin/env python3
"""Run a fresh strict paired scratch and source-extracted count-factor proof."""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT/'fpga/experiments/cu66-v129-scratch'
V = SRC/'verification'
AREA = ROOT/'experiments/python-gamebub-v129/scratch-factor'
BASE = ROOT/'scripts/cu66-v128/raw/qualify.py'
GATE = ROOT/'scripts/cu66-v128/integration/resource_gate.py'
IMAGE = 'sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB = 1024**3


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def save(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--root-grant')
    args = ap.parse_args()
    for name in ('prepare.py', 'prepare_verification.py'):
        subprocess.run([sys.executable, str(Path(__file__).with_name(name))], cwd=ROOT,
                       check=True, stdout=subprocess.DEVNULL)
    spec=importlib.util.spec_from_file_location('v128_checker',BASE)
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    wait=runpy.run_path(str(GATE))['wait_ready']
    inputs = [SRC/'packed_scratch_v91g2.sv',SRC/'edit-recipe.json',
        ROOT/'fpga/experiments/cu66-v128-raw/packed_scratch_v91g2.sv',
        ROOT/'fpga/experiments/cu66-v128-raw/verification/raw_probe.sv',
        ROOT/'fpga/experiments/cu66-v128-raw/verification/v128_raw_scalar_probe.sv',
        ROOT/'fpga/experiments/cu66-v128-raw/verification/tb_raw.cpp',
        Path(__file__).resolve(),Path(__file__).with_name('prepare.py'),
        Path(__file__).with_name('prepare_verification.py'),Path(__file__).with_name('tb_count.cpp'),
        BASE,GATE,*sorted(V.glob('*'))]
    assert len(set(inputs))==len(inputs) and all(p.is_file() for p in inputs)
    if not args.run:
        print('V129_SCRATCH_FOCUSED_PREPARED_NOT_RUN');return
    assert args.root_grant=='ROOT_V129_SCRATCH', 'Exact Root heavy dispatch grant required'
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v129-scratch-focused-'+stamp);build.mkdir()
    mapped='/build/'+build.name
    result=dict(schema='v129-scratch-count-factor-focused-v1',status='RUNNING',actual_RTL_run=False,
        image_id=IMAGE,source_sha256={rel(p):sha(p)for p in inputs},commands=[],wire_runs=[],clock_runs=[],
        count_runs=[],memory_samples=[],launch_gate_waits=[],strict_warnings=True,
        assertions_disabled_or_downgraded=False,all_original_assertions_retained=True,
        declared_public_cycle_delta=0,prepared_state_forces=0,new_result_or_owner_forces=0,
        paired_baseline_is_actual_v128=True,source_extracted_count_probe=True,
        count_probe_is_natural_packets=False,hardware_contact=False,
        full_parent_or_routed_timing_qualified=False,build_external=str(build))
    begun=time.monotonic()

    def command(argv, name, cap, actual=False):
        waits=[];before=wait(checker.memory,waits);result['launch_gate_waits'].append(dict(command=name,samples=waits))
        assert before['available_bytes']>=8*GIB and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
        container='gamebub-v129-scratch-'+stamp.lower()+'-'+str(len(result['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g',
             '--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0',
             '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,
             'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record=dict(argv=cmd,timeout_seconds=cap,resource_before=before,launch_gate_wait_samples=waits)
        result['commands'].append(record)
        if actual:result['actual_RTL_run']=True
        save(out/'receipt.json',result);start=time.monotonic()
        with (out/name).open('w') as log:
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
            while process.poll() is None:
                sample=dict(elapsed_seconds=time.monotonic()-start,**checker.memory())
                result['memory_samples'].append(sample)
                high=high+1 if sample['psi_full_avg10']>=5 else 0
                if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
                    subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15)
                    record['resource_stop']=sample;break
                time.sleep(2)
            record.update(exit_code=process.wait(timeout=20),wall_seconds=time.monotonic()-start)
        save(out/'receipt.json',result)
        assert record['exit_code']==0 and 'resource_stop' not in record,name

    try:
        for p in inputs:
            dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
        compiled=[V/'v128_scratch_baseline.sv',SRC/'packed_scratch_v91g2.sv',
                  V/'v128_raw_scalar_probe.sv',V/'raw_probe.sv',V/'tb_raw.cpp',
                  V/'count_factor_probe.sv',Path(__file__).with_name('tb_count.cpp')]
        assert len({p.name for p in compiled})==len(compiled)
        for p in compiled:shutil.copyfile(p,build/p.name)
        result['compile_inputs_sha256']={p.name:sha(build/p.name)for p in compiled}
        command(['verilator','--version'],'version.log',30)
        assert 'Verilator 5.020' in (out/'version.log').read_text()
        common=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw',
                '--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017']
        cppflags='-std=c++17 -O2 -Wall -Wextra -Werror'
        pair=['v128_scratch_baseline.sv','packed_scratch_v91g2.sv','v128_raw_scalar_probe.sv','raw_probe.sv','tb_raw.cpp']
        command(common+['--top-module','raw_probe','--Mdir',mapped+'/obj_pair','-CFLAGS',cppflags,
                       *[mapped+'/'+x for x in pair]],'pair-compile.log',900)
        assert '%Warning-' not in (out/'pair-compile.log').read_text()
        for suite,seeds,validator in [('wire',(128501,128502),checker.check_wire),
                                      ('clock',(128601,128602),checker.check_clock)]:
            for seed in seeds:
                name=f'{suite}-{seed}.jsonl'
                command([mapped+'/obj_pair/Vraw_probe',suite,str(seed)],name,900,True)
                rows=[json.loads(x)for x in(out/name).read_text().splitlines()]
                result[suite+'_runs'].append(validator(rows,seed))
        command(common+['--top-module','count_factor_probe','--Mdir',mapped+'/obj_count',
                       '-CFLAGS',cppflags,mapped+'/count_factor_probe.sv',mapped+'/tb_count.cpp'],
                       'count-compile.log',900)
        assert '%Warning-' not in (out/'count-compile.log').read_text()
        for seed in (129301,129302):
            name=f'count-{seed}.jsonl';command([mapped+'/obj_count/Vcount_factor_probe',str(seed)],name,900,True)
            rows=[json.loads(x)for x in(out/name).read_text().splitlines()];assert len(rows)==1
            v=rows[0];assert v['type']=='v129_count_factor_verdict' and v['status']=='TEST_PASS' and v['seed']==seed
            assert v['records']==30224 and v['phase_checks']==241792 and v['DUT_clocks']==0
            assert v['equal']>0 and v['unequal']>0 and v['high_bit_differences']>0
            result['count_runs'].append(v)
        assert result['source_sha256']=={rel(p):sha(p)for p in inputs}
        assert all(sha(out/'sources'/p.relative_to(ROOT))==result['source_sha256'][rel(p)]for p in inputs)
        assert result['compile_inputs_sha256']=={p.name:sha(build/p.name)for p in compiled}
        result.update(compiled_input_snapshots_unchanged=True,retained_source_snapshots_unchanged=True,status='PASS')
    except BaseException as error:
        result.update(status='FAIL',error=repr(error));raise
    finally:
        result['wall_seconds']=time.monotonic()-begun
        result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))
                                   if p.is_file()and p.name!='receipt.json'}
        save(out/'receipt.json',result)
        save(AREA/'results.json',dict(path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json'),
                                     status=result['status'],actual_RTL_run=result['actual_RTL_run']))
        print('V129_SCRATCH_FOCUSED',result['status'],rel(out),flush=True)


if __name__ == '__main__':
    main()
