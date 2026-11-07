#!/usr/bin/env python3
"""Compare actual V102/V104 reconstruction modules under clocked interface stimulus."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'fpga/experiments/cu66-v102-predicate/cu66_reconstruct_stream_v91k.sv'
FPGA = ROOT / 'fpga/experiments/cu66-v104-control'
AREA = ROOT / 'experiments/python-gamebub-v104/control'
CONTAINER = 'gamebub-cu66-v69-build'
BASELINE = '1d0a702a758787522723ac52ff44a1bf220c39d1'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    began = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True, exist_ok=False)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v104-control-' + stamp)
    build.mkdir(exist_ok=False)
    files = [SRC, *[FPGA/n for n in ('cu66_reconstruct_stream_v91k.sv', 'control_original.sv',
        'control_candidate.sv', 'control_probe.sv', 'tb_control.cpp', 'ports.json', 'adapter.json', 'change.json')],
        ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv', Path(__file__).resolve()]
    report = dict(schema='v104-control-focused-clocked-rtl-v1', status='FAIL', baseline_revision=BASELINE,
        candidate=dict(path=str((FPGA/'cu66_reconstruct_stream_v91k.sv').relative_to(ROOT)),
                       sha256=sha(FPGA/'cu66_reconstruct_stream_v91k.sv')),
        backend='Verilator 5.020 behavioral; explicitly configured existing backend',
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files}, commands=[],
        actual_RTL_run=False, strict_warnings=True, assertions_disabled_or_downgraded=False,
        limits=['Clocked module interface comparison and reachable geometry assertions; not formal or arbitrary internal-state equivalence.',
                'No native fit/timing, whole decoder/HUD/C2, hardware FPS or validated complete latency qualification.'])
    def command(argv, name, timeout):
        entry=dict(argv=argv,log=name,timeout_seconds=timeout,resource_gate=resources())
        report['commands'].append(entry)
        started=time.monotonic()
        with (out/name).open('w') as log:
            result=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+30)
        entry.update(exit_code=result.returncode,wall_seconds=time.monotonic()-started)
        if result.returncode:raise RuntimeError('command failed '+name)
    try:
        report['resource_gate']=resources()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)
        adapter=json.loads((FPGA/'adapter.json').read_text())
        for variant,production in [('original',SRC),('candidate',FPGA/'cu66_reconstruct_stream_v91k.sv')]:
            text=(FPGA/('control_'+variant+'.sv')).read_text()
            normalized=text.replace('module control_'+variant+' (','module cu66_reconstruct_stream_v91k (',1)
            normalized=normalized.replace(adapter['extra_ports'],');',1)
            normalized=normalized.replace(adapter['assignments'][variant],'',1)
            assert normalized==production.read_text(),'verification adapter body changed'
        report['verification_adapters_preserve_complete_production_body']=True
        report['production_port_count']=json.loads((FPGA/'ports.json').read_text())['production_port_count']
        for source in files:
            target=out/'sources'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT))
        mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2',
            '--assert','-Wall','--language','1800-2017','--top-module','control_probe','--Mdir',mapped,
            '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',
            *[copy(FPGA/n) for n in ('control_original.sv','control_candidate.sv','control_probe.sv')],
            copy(ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv'),copy(FPGA/'tb_control.cpp')],
            'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text(),'strict warning policy'
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vcontrol_probe'],'binary.log',30)
        report['binary']=dict(path=mapped+'/Vcontrol_probe',sha256=(out/'binary.log').read_text().split()[0])
        trace=out/'trace.jsonl'
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','120s',mapped+'/Vcontrol_probe',str(trace)],'simulation.jsonl',120)
        rows=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()]
        assert len(rows)==1 and rows[0]['status']=='TEST_PASS'
        verdict=rows[0]
        assert verdict['full_frames']==2 and verdict['directed_checks']==51
        assert verdict['clock_edges']>1000000 and verdict['half_cycle_public_comparisons']==3*verdict['clock_edges']
        report.update(terminal_verdict=verdict,clock_edges=verdict['clock_edges'],actual_RTL_run=True)
        # Independent integer-coordinate replay of every retained advance/hold/control row.
        raw=trace.read_bytes();raw_sha=hashlib.sha256(raw).hexdigest()
        packed=out/'trace.jsonl.gz'
        with packed.open('wb') as stream:
            with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as zipped:zipped.write(raw)
        trace.unlink()
        prev=None;n=0;advance=0;kills=0
        for line in raw.splitlines():
            r=json.loads(line);p,t=r['plane'],r['tile']
            assert p<=2 and 0<=t<(5400 if p==0 else 1350)
            expected=(t//90//2)*45+(t%90)//2 if p==0 else t
            assert r['cell']==r['lookup']==expected
            assert r['column']==(t%90 if p==0 else 0)
            assert r['odd']==((t//90)%2 if p==0 else 0)
            if prev:
                assert r['clock']>prev['clock']
                if r['reset'] or r['cancel'] or r['start']:
                    assert (p,t,expected)==(0,0,0);kills+=1
                elif r['advance']:
                    pp,pt=prev['plane'],prev['tile'];limit=5400 if pp==0 else 1350
                    expected_pt=(pp,pt+1) if pt+1<limit else (min(pp+1,2),0)
                    assert (p,t)==expected_pt,('coordinate progression',prev,r)
                    advance+=1
                else:assert (p,t)==(prev['plane'],prev['tile'])
            prev=r;n+=1
        assert n>16000 and advance>=16200 and kills>=100
        report['trace_replay']=dict(status='PASS',rows=n,coordinate_advances=advance,control_pulses=kills,
            oracle='Independent plane/row/column integer geometry and retained advance order; actual-interface fullmodule two-state trace.',
            path=packed.name,sha256=sha(packed),raw_sha256=raw_sha)
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files},'sources changed'
        report['status']='PASS'
    except BaseException as error:
        report.update(error_class=type(error).__name__,error=str(error));raise
    finally:
        if (out/'trace.jsonl').exists():
            raw=(out/'trace.jsonl').read_bytes()
            with (out/'partial-trace.jsonl.gz').open('wb') as stream:
                with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as zipped:zipped.write(raw)
            (out/'trace.jsonl').unlink()
        report['wall_seconds']=time.monotonic()-began
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report)
        write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V104_CONTROL',report['status'],out,flush=True)


if __name__=='__main__':
    main()
