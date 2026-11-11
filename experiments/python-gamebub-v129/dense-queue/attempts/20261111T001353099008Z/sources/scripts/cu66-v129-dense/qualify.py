#!/usr/bin/env python3
"""Strict standalone dense-boundary RTL test with two targeted negative controls."""
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

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'fpga/experiments/cu66-v129-dense-queue'
AREA=ROOT/'experiments/python-gamebub-v129/dense-queue'
BASE=ROOT/'scripts/cu66-v128/raw/qualify.py'
GATE=ROOT/'scripts/cu66-v128/integration/resource_gate.py'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
GIB=1024**3


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return str(Path(path).resolve().relative_to(ROOT))
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args()
    rtl=SRC/'v129_dense_owned_queue.sv';tb=SRC/'tb_dense.cpp';readme=SRC/'README.md'
    inputs=[rtl,tb,readme,Path(__file__).resolve(),BASE,GATE]
    text=rtl.read_text()
    mutations=[('truncate_child_epoch','in_child_epoch!=owner_child',
                'in_child_epoch[30:0]!=owner_child[30:0]','control mismatch'),
               ('unsafe_full_accept',"occupancy<2'd2","occupancy<=2'd2",'ready/valid mismatch')]
    for _,old,new,_ in mutations:assert text.count(old)==1 and old!=new
    assert all(p.is_file()for p in inputs)
    if not args.run:
        print('V129_DENSE_STANDALONE_PREPARED_NOT_RUN');return
    assert args.root_grant=='ROOT_V129_DENSE', 'Exact Root heavy dispatch grant required'
    spec=importlib.util.spec_from_file_location('v128_memory_checker',BASE)
    checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    wait=runpy.run_path(str(GATE))['wait_ready']
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v129-dense-focused-'+stamp);build.mkdir()
    mapped='/build/'+build.name
    result=dict(schema='v129-dense-owned-queue-standalone-focused-v1',status='RUNNING',actual_RTL_run=False,
        image_id=IMAGE,source_sha256={rel(p):sha(p)for p in inputs},commands=[],runs=[],negative_controls=[],
        memory_samples=[],launch_gate_waits=[],strict_warnings=True,assertions_disabled_or_downgraded=False,
        standalone_unit=True,integrated_producer=False,hardware_contact=False,
        FPGA_timing_qualified=False,physical_memory_ACKs_modeled=False,
        comparison_contract='Cycle-exact standalone scoreboard; latency changes versus original producer require a separate integrated contract.',
        same_edge_bad_offer_good_head='A previously valid good head can retire while an offered bad tuple is faulted and invalidated.',
        build_external=str(build))
    started=time.monotonic()

    def command(argv,name,cap,actual=False,expected_exit=0):
        waits=[];before=wait(checker.memory,waits);result['launch_gate_waits'].append(dict(command=name,samples=waits))
        assert before['available_bytes']>=8*GIB and before['psi_full_avg10']<1 and before['combined_used_ratio']<.85,before
        container='gamebub-v129-dense-'+stamp.lower()+'-'+str(len(result['commands']))
        cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g',
             '--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0',
             '--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,
             'timeout','--kill-after=5s',str(cap)+'s',*argv]
        record=dict(argv=cmd,timeout_seconds=cap,resource_before=before,launch_gate_wait_samples=waits,
                    expected_exit=expected_exit);result['commands'].append(record)
        if actual:result['actual_RTL_run']=True
        save(out/'receipt.json',result);start=time.monotonic()
        with(out/name).open('w')as log:
            process=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
            while process.poll() is None:
                sample=dict(elapsed_seconds=time.monotonic()-start,**checker.memory());result['memory_samples'].append(sample)
                high=high+1 if sample['psi_full_avg10']>=5 else 0
                if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
                    subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15)
                    record['resource_stop']=sample;break
                time.sleep(2)
            record.update(exit_code=process.wait(timeout=20),wall_seconds=time.monotonic()-start)
        save(out/'receipt.json',result)
        assert record['exit_code']==expected_exit and 'resource_stop'not in record,name

    try:
        for p in inputs:
            dst=out/'sources'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
        for label,old,new,expected_message in [('good',None,None,None),*mutations]:
            folder=build/label;folder.mkdir();rtl_text=text if old is None else text.replace(old,new,1)
            (folder/rtl.name).write_text(rtl_text);shutil.copyfile(tb,folder/tb.name)
            built_source=sha(folder/rtl.name);built_tb=sha(folder/tb.name)
            if label=='good':assert built_source==sha(rtl)
            else:assert built_source!=sha(rtl)
            if label=='good':
                command(['verilator','--version'],'version.log',30)
                assert 'Verilator 5.020'in(out/'version.log').read_text()
            prefix=mapped+'/'+label
            command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw',
                     '--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017',
                     '--top-module','v129_dense_owned_queue','--Mdir',prefix+'/obj',
                     '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',prefix+'/'+rtl.name,prefix+'/'+tb.name],
                     label+'-compile.log',900)
            assert '%Warning-' not in(out/(label+'-compile.log')).read_text()
            assert sha(folder/rtl.name)==built_source and sha(folder/tb.name)==built_tb
            for seed in ((129501,129502)if label=='good' else (129501,)):
                log=f'{label}-{seed}.log';command([prefix+'/obj/Vv129_dense_owned_queue',str(seed)],log,900,True,
                                                    expected_exit=0 if label=='good' else 1)
                raw=(out/log).read_text()
                if label=='good':
                    rows=[json.loads(x)for x in raw.splitlines()];assert len(rows)==1;v=rows[0]
                    assert v['type']=='v129_dense_queue_verdict'and v['status']=='TEST_PASS'and v['seed']==seed
                    for k in ('pushes','pops','simultaneous','full_recovery_bubbles','bad_while_full','bad_accepted',
                              'good_pop_on_fault_edge','held_stalls','kill_flushes','finish_fenced','finishes','arm_fenced','block_wraps'):
                        assert v[k]>0,k
                    assert v['clocks']>=60000;result['runs'].append(v)
                else:
                    assert 'V129_DENSE_FAIL' in raw and expected_message in raw
                    result['negative_controls'].append(dict(name=label,old=old,new=new,
                        mutant_source_sha256=built_source,detected=True,expected_message=expected_message,log=log))
        assert result['source_sha256']=={rel(p):sha(p)for p in inputs}
        assert all(sha(out/'sources'/p.relative_to(ROOT))==result['source_sha256'][rel(p)]for p in inputs)
        result.update(retained_source_snapshots_unchanged=True,status='PASS')
    except BaseException as error:
        result.update(status='FAIL',error=repr(error));raise
    finally:
        result['wall_seconds']=time.monotonic()-started
        result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))
                                   if p.is_file()and p.name!='receipt.json'}
        save(out/'receipt.json',result)
        save(AREA/'results.json',dict(path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json'),
                                     status=result['status'],actual_RTL_run=result['actual_RTL_run']))
        print('V129_DENSE_STANDALONE',result['status'],rel(out),flush=True)


if __name__=='__main__':main()
