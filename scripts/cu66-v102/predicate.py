#!/usr/bin/env python3
"""Run a bounded exhaustive actual-RTL V102 predicate comparison and Python replay."""
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
SRC = ROOT / 'fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv'
FPGA = ROOT / 'fpga/experiments/cu66-v102-predicate'
AREA = ROOT / 'experiments/python-gamebub-v102/predicate'
CONTAINER = 'gamebub-cu66-v69-build'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def main():
    began = time.monotonic()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True, exist_ok=False)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v102-predicate-' + stamp)
    build.mkdir(exist_ok=False)
    files = [SRC, FPGA / 'cu66_reconstruct_stream_v91k.sv', FPGA / 'reconstruct_original.sv',
        FPGA / 'reconstruct_candidate.sv', FPGA / 'predicate_probe.sv', FPGA / 'tb_predicate.cpp',
        FPGA / 'ports.json', ROOT / 'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv',
        Path(__file__).resolve()]
    report = {'schema':'v102-predicate-focused-rtl-v1', 'status':'FAIL',
        'baseline_revision':'6b36a3228804953c50c10db61f620cad5412ecce',
        'candidate':{'path':str((FPGA/'cu66_reconstruct_stream_v91k.sv').relative_to(ROOT)),
                     'sha256':sha(FPGA/'cu66_reconstruct_stream_v91k.sv')},
        'backend':'Verilator 5.020 behavioral; explicitly configured existing backend',
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in files}, 'commands':[],
        'clock_edges':0,'limits':['Exhaustive combinational function domain only; no sequential protocol coverage.',
        'No native synthesis/placement/routing, formal proof or achieved hardware speed claim.']}
    def command(argv, logname, timeout):
        entry={'argv':argv,'log':logname,'timeout_seconds':timeout,'resource_gate':resources()}
        report['commands'].append(entry)
        start=time.monotonic()
        with (out/logname).open('w') as log:
            result=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+30)
        entry.update(exit_code=result.returncode,wall_seconds=time.monotonic()-start)
        if result.returncode:raise RuntimeError('command failed '+logname)
    try:
        report['resource_gate']=resources()
        original_blob=subprocess.check_output(['git','show',report['baseline_revision']+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)
        assert hashlib.sha256(original_blob).hexdigest()==sha(SRC)
        for variant,production in [('original',SRC),('candidate',FPGA/'cu66_reconstruct_stream_v91k.sv')]:
            text=(FPGA/('reconstruct_'+variant+'.sv')).read_text()
            text=text.replace('module reconstruct_'+variant+' (','module cu66_reconstruct_stream_v91k (',1)
            text=text.replace(',\n    input logic [1:0] probe_plane,\n    input logic [12:0] probe_tile,\n    output logic probe_hidden\n);',');',1)
            text=text.replace('    assign probe_hidden=safe_hidden(probe_plane,probe_tile);\n','',1)
            assert text==production.read_text(),'verification adapter changed design body'
        report['verification_adapters_preserve_complete_production_body']=True
        report['production_port_count']=json.loads((FPGA/'ports.json').read_text())['production_port_count']
        for source in files:
            dest=out/'sources'/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT))
        cbuild='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2',
            '--assert','-Wall','--language','1800-2017','--top-module','predicate_probe','--Mdir',cbuild,
            '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',
            *[copy(FPGA/name) for name in ['reconstruct_original.sv','reconstruct_candidate.sv','predicate_probe.sv']],
            copy(ROOT/'fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv'),copy(FPGA/'tb_predicate.cpp')],
            'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text(),'strict warning policy'
        command(['docker','exec',CONTAINER,'sha256sum',cbuild+'/Vpredicate_probe'],'binary.log',30)
        report['binary']={'path':cbuild+'/Vpredicate_probe','sha256':(out/'binary.log').read_text().split()[0]}
        trace=out/'trace.jsonl'
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','60s',cbuild+'/Vpredicate_probe',str(trace)],'simulation.jsonl',60)
        rows=[json.loads(x) for x in (out/'simulation.jsonl').read_text().splitlines()]
        assert len(rows)==1 and rows[0]['status']=='TEST_PASS' and rows[0]['cases']==32768 and rows[0]['clock_edges']==0
        report['terminal_verdict']=rows[0]
        # Independent discrete geometry model: Cartesian rectangles, not the candidate interval expression.
        ytiles=set()
        for xa,xb,ya,yb in [(3,22,7,9),(3,22,11,13),(21,61,45,48),(21,51,49,51)]:
            ytiles.update(y*90+x for y in range(ya,yb) for x in range(xa,xb))
        ctiles={23*45+x for x in range(11,30)}
        counts=[0,0,0,0];count=0;raw_sha=sha(trace);packed=out/'trace.jsonl.gz'
        with trace.open('rb') as src,packed.open('wb') as dst:
            with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as zipped:
                for line in src:
                    r=json.loads(line);p,t=count//8192,count%8192
                    assert r['plane']==p and r['tile']==t,'missing/duplicate/reordered input'
                    expected=int(t in (ytiles if p==0 else ctiles))
                    assert r['original']==r['candidate']==r['expected']==expected,(p,t)
                    counts[p]+=expected;count+=1;zipped.write(line)
        assert count==32768 and counts==[256,19,19,19]
        assert hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()==raw_sha
        trace.unlink()
        report['trace_replay']={'status':'PASS','rows':count,'true_counts':counts,
            'oracle':'independent Cartesian rectangle tile sets; complete 4-plane x8192-tile domain',
            'path':packed.name,'sha256':sha(packed),'raw_sha256':raw_sha}
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files},'source changed'
        report.update(status='PASS',actual_RTL_run=True,cases=32768,strict_warnings=True,
                      assertions_disabled_or_downgraded=False)
    except BaseException as error:
        report.update(error_class=type(error).__name__,error=str(error));raise
    finally:
        report['wall_seconds']=time.monotonic()-began
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report)
        write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V102_PREDICATE',report['status'],out,flush=True)

if __name__=='__main__':main()
