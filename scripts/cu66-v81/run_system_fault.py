#!/usr/bin/env python3
"""Actual mode-3 decoder/SDRAM/display rejection, external abort, and recovery."""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import tarfile
import time
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v81/system'
NATIVE=ROOT/'experiments/cu66-native-v69'
CONTAINER='gamebub-cu66-v69-build'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields(line):
    return {key:int(value) for key,value in re.findall(r'(\w+)=(\d+)',line)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args()
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'faults'/f'attempt-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True,exist_ok=False)
    commands=[]
    report=dict(schema='cu81-actual-system-fault-v1',status='FAIL_FUNCTIONAL',prefetch_mode=3,scope='Actual integrated mode-3 decoder, controller, SDRAM model, native HUD endpoint and continuous LCD raster; normal external abort input, no DUT force or canonical seeding.',observer_unit_only=False,hardware_fault_injection=False,commands=commands)
    started=time.monotonic();held_lock=None

    def run(argv,name,timeout):
        entry=dict(argv=argv,log=str((out/name).relative_to(ROOT)),exit_code=None,timed_out=False,timeout_seconds=timeout)
        commands.append(entry);begin=time.monotonic()
        try:
            with (out/name).open('w') as stream:
                result=subprocess.run(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            entry['exit_code']=result.returncode
        except subprocess.TimeoutExpired:
            entry['timed_out']=True
        finally:
            entry.update(wall_seconds=time.monotonic()-begin,sha256=sha(out/name))
            (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        if entry['exit_code']!=0 or entry['timed_out']:
            raise RuntimeError(f'{name}: exit={entry["exit_code"]} timed_out={entry["timed_out"]}; retained log')
        return (out/name).read_text()

    try:
        spec_path=AREA/'sources.json';spec=json.loads(spec_path.read_text())
        files=[ROOT/path for path in spec['rtl_sources']]+[spec_path,AREA/'tb_system.cpp',AREA/'tb_system_fault.cpp',AREA/'monitor.hpp',Path(__file__).resolve(),NATIVE/'index.tsv',*NATIVE.glob('*.hpp'),ROOT/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',ROOT/'fpga/experiments/cu66-v70/memory/cu70_memory_map.svh',ROOT/'fpga/experiments/cu66-v70/memory/memory_map.hpp',ROOT/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh']
        files += [NATIVE/line.split('\t')[2] for line in (NATIVE/'index.tsv').read_text().splitlines()]
        files=sorted(set(files));pins={str(path.relative_to(ROOT)):sha(path) for path in files}
        report['source_sha256']=pins
        (out/'source-manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
        with tarfile.open(out/'sources.tar.gz','w:gz') as archive:
            for path in files:
                if 'cu66-v81' in path.parts:
                    archive.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
        report['source_snapshot']=dict(path=str((out/'sources.tar.gz').relative_to(ROOT)),sha256=sha(out/'sources.tar.gz'),scope='Mutable V81 RTL/source list/observer/main bench/fault bench/fault runner; complete frozen pool pinned by SHA-256.')
        assert pins=={path:sha(ROOT/path) for path in pins},'sources changed during snapshot'
        mdir='/build/v81-system-fault-prefetch3-tac2';binary=mdir+'/Vcu81_system_sim'
        build_record=AREA/'build-fault-prefetch3-tac2.json'
        if not args.skip_build:
            assert not build_record.exists(),'immutable fault build identity exists; use --skip-build or explicitly archive it'
            lock=AREA/'.build-fault-prefetch3-tac2.lock'
            with lock.open('x') as stream:stream.write(str(out.relative_to(ROOT))+'\n')
            held_lock=lock
            run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','1',*spec['verilator_options'],'-DSIMULATION','-GTAC_NS=2.0','-GPREFETCH_ENABLE=3','--top-module',spec['top'],'--Mdir',mdir,'-CFLAGS','-O2 -std=c++17',*['-I'+str(ROOT/path) for path in spec['include_dirs']],*[str(ROOT/path) for path in spec['rtl_sources']],str(AREA/'tb_system_fault.cpp')],'build.log',1200)
            binary_sha=run(['docker','exec',CONTAINER,'sha256sum',binary],'binary.log',30).split()[0]
            assert pins=={path:sha(ROOT/path) for path in pins},'source changed during build'
            with build_record.open('x') as stream:
                json.dump(dict(source_sha256=pins,binary=binary,binary_sha256=binary_sha,prefetch_mode=3,tac_ns=2,source_snapshot=report['source_snapshot'],commands=list(commands)),stream,indent=2);stream.write('\n')
        build=json.loads(build_record.read_text())
        assert build['source_sha256']==pins and build['binary']==binary and build['prefetch_mode']==3,'fault build identity differs'
        assert run(['docker','exec',CONTAINER,'sha256sum',binary],'binary-check.log',30).split()[0]==build['binary_sha256'],'fault executable changed'
        report['build_provenance']=build
        log=run(['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=10s','1800s',binary,str(NATIVE/'index.tsv')],'run.log',1830)
        rows=[dict(kind=re.search(r'kind=(\w+)',line)[1],**fields(line)) for line in log.splitlines() if line.startswith('SYSTEM_FAULT_PASS ')]
        terminal=re.findall(r'^SYSTEM_FAULT_CAMPAIGN_PASS (.+)$',log,re.M)
        assert len(terminal)==1 and 'FAIL' not in log and len(rows)==2,'fault campaign terminal/case proof missing'
        summary=fields(terminal[0]);releases=[fields(line) for line in log.splitlines() if line.startswith('SYSTEM_FAULT_ENDPOINT_RELEASE ')]
        accepts=[fields(line) for line in log.splitlines() if line.startswith('SYSTEM_FAULT_ABORT_ACCEPT ')]
        assert summary['rejected']==summary['accepted']==summary['aborted_endpoint_releases']==2 and summary['attempts']==summary['admitted']==summary['endpoint_releases']==4
        assert summary['no_per_source_reset']==1 and summary['prefetch_mode']==3 and summary['underruns']==summary['black_lines']==summary['observer_unit_only']==0
        assert summary['recovery_complete_rasters']>0 and summary['recovery_commit_calls']>=2
        assert len(releases)==2 and all(row['successful_commit']==0 for row in releases)
        assert [row['aborted_endpoint_releases'] for row in releases]==[1,2]
        assert rows[0]['kind']=='bad_crc' and rows[0]['physical_write_words']==rows[0]['actual_prefetch_read_accepts']==0 and rows[0]['error']>0
        partial=rows[1]
        assert partial['kind']=='partial_write_read_accept_abort' and partial['physical_write_words']>0 and partial['canonical_write_words_observed']>=64
        assert partial['epoch_done_events']==partial['epoch_aborted_events']==1 and partial['abort_cycle']<=partial['epoch_done_cycle']==partial['epoch_aborted_cycle']<=releases[1]['cycle']
        assert partial['actual_prefetch_read_accepts']>0 and partial['read_accept_coincident_abort']==1 and partial['processor_abort_calls']>0
        assert len(accepts)==1 and accepts[0]['client']==3 and accepts[0]['write']==0 and accepts[0]['canonical_words_before_abort']>=64 and accepts[0]['cycle']==partial['abort_cycle']
        assert all(all(row[key]==1 for key in ('wrapper_and_prefetch_drained','raw_bridge_and_controller_idle_observed','accepted_reference_unchanged','accepted_HUD_unchanged','old_front_full_raster')) for row in rows)
        assert pins=={path:sha(ROOT/path) for path in pins},'sources changed during fault campaign'
        report.update(status='PASS_ACTUAL_REJECT_ABORT_RETAIN_AND_RECOVER',cases=rows,summary=summary,endpoint_releases=releases,coincident_accepts=accepts,pending_lookup_at_abort=bool(partial['pending_lookup_at_abort']),limitations=['Two directed actual-system rejection/abort cases, not exhaustive fault coverage.','Native HUD CPU/hash/control executes at zero simulated time.','No live ESP32/Wi-Fi/QSPI, physical timing/CDC/fit, or fatal scanout/cache recovery proof.'])
    except Exception as error:
        report['failure']=str(error);raise
    finally:
        if held_lock is not None:held_lock.unlink()
        report['wall_seconds']=time.monotonic()-started
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(status=report['status'],results_path=str(out/'results.json'),wall_seconds=report['wall_seconds'])),flush=True)


if __name__=='__main__':main()
