#!/usr/bin/env python3
"""Probe cycle-exact dequantization register mapping with an independent oracle."""
import ast
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v104-dsp'
AREA=ROOT/'experiments/python-gamebub-v104/dsp'
SOURCE=ROOT/'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv'
HOST_QUANT=ROOT/'experiments/python-transform-study/fixed_codec.py'
ROM=ROOT/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh'
CONTAINER='gamebub-cu66-v69-build'
BASELINE='1d0a702a758787522723ac52ff44a1bf220c39d1'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,o):p.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n')


def quant_tables():
    def literal(n):
        if isinstance(n,ast.Constant):return n.value
        if isinstance(n,ast.List):return [literal(x) for x in n.elts]
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Mult):return literal(n.left)*literal(n.right)
        raise ValueError('unsupported host-table AST')
    tables={}
    for n in ast.parse(HOST_QUANT.read_text()).body:
        if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('QY','QC'):
            tables[n.targets[0].id]=[x for row in literal(n.value.args[0]) for x in row]
    assert set(tables)=={'QY','QC'} and all(len(t)==64 for t in tables.values())
    return tables


def replay(path,verdict):
    tables=quant_tables();state=0;group=0;scale=0;chroma=0;oid=0;error=0;coeff=[0]*64;out=0;edges=0
    counts=dict(accepted_inputs=0,held_output_edges=0,reset_edges=0,abort_edges=0,directed_interruptions=0)
    for line in gzip.open(path,'rt'):
        r=json.loads(line);assert r['edge']==edges+1
        if state==0 and not r['rst'] and not r['abort'] and r['in_valid']:counts['accepted_inputs']+=1
        if state==2 and not r['rst'] and not r['abort'] and not r['out_ready']:counts['held_output_edges']+=1
        counts['reset_edges']+=int(r['rst']);counts['abort_edges']+=int(r['abort'])
        counts['directed_interruptions']+=int(r['tag'] in ('interrupt_group','hold_interrupt'))
        if r['rst'] or r['abort']:
            state=group=scale=chroma=oid=error=out=0;coeff=[0]*64
        elif state==0 and r['in_valid']:
            packed=int(r['coeff_hex'],16)
            coeff=[(lambda v:v-65536 if v>=32768 else v)((packed>>(16*n))&65535) for n in range(64)]
            scale=r['scale'];chroma=r['chroma'];oid=r['in_id'];group=0
            error=int(scale==3 or any(v< -2048 or v>2048 for v in coeff))
            if error or not any(coeff):out=0;state=2
            else:state=1
        elif state==1:
            for n in range(group*8,group*8+8):
                base=tables['QC' if chroma else 'QY'][n]
                q=min(255,(base+1)//2 if scale==0 else base if scale==1 else base*2)
                product=coeff[n]*q
                out=(out&~(0xfffff<<(20*n)))|((product&0xfffff)<<(20*n))
            if group==7:state=2
            else:group+=1
        elif state==2 and r['out_ready']:state=0
        assert r['in_ready']==int(state==0 and not r['rst'] and not r['abort'])
        assert r['out_valid']==int(state==2 and not r['rst'] and not r['abort'])
        assert r['out_id']==oid and r['out_error']==error
        assert int(r['out_hex'],16)==out,('public partial output',r['edge'])
        edges+=1
    assert edges==verdict['clock_edges']
    assert all(counts[k]==verdict[k] for k in counts)
    assert verdict['public_samples']==edges*3-1
    assert verdict['packed_element_comparisons']==verdict['public_samples']*64
    assert verdict['legal_value_transactions']==2*3*4097
    return dict(status='PASS',rows=edges,oracle='Independent Python state machine + frozen host quant tables; public packed partial outputs checked at every recorded rising edge.',**counts)


def main():
    start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True,exist_ok=False)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v104-dsp-'+stamp);build.mkdir(exist_ok=False)
    files=[SOURCE,ROM,HOST_QUANT,Path(__file__).resolve(),*[FPGA/n for n in ('cu66_dequant.sv','dequant_original.sv','dequant_candidate.sv','dequant_probe.sv','tb_dequant.cpp','oracle_quant.hpp','ports.json','change.json')]]
    report=dict(schema='v104-dsp-clocked-focus-v1',status='FAIL',baseline_revision=BASELINE,
        candidate=dict(path=str((FPGA/'cu66_dequant.sv').relative_to(ROOT)),sha256=sha(FPGA/'cu66_dequant.sv')),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],runs=[],
        backend='Verilator 5.020 behavioral historical backend; GCC13.3 strict checker',strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Two-state clocked component proof, not formal or mapped-netlist equivalence.','Register inference, achieved clock, full decoder latency and hardware FPS are separate native/full-system gates.'])
    def command(argv,logname,timeout):
        rec=dict(argv=argv,log=logname,timeout_seconds=timeout,exit_code=None,resource_gate=resources());report['commands'].append(rec)
        began=time.monotonic()
        with (out/logname).open('w') as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+20)
        rec.update(exit_code=r.returncode,wall_seconds=time.monotonic()-began)
        if r.returncode:raise RuntimeError('command failed '+logname)
    try:
        report['resource_gate']=resources()
        assert subprocess.check_output(['git','show',BASELINE+':'+str(SOURCE.relative_to(ROOT))],cwd=ROOT)==SOURCE.read_bytes()
        for variant,production in [('original',SOURCE),('candidate',FPGA/'cu66_dequant.sv')]:
            assert (FPGA/('dequant_'+variant+'.sv')).read_text().replace('module dequant_'+variant+' (','module cu66_dequant (',1)==production.read_text()
        assert SOURCE.read_text().split(');',1)[0]==(FPGA/'cu66_dequant.sv').read_text().split(');',1)[0]
        tables=quant_tables();header='// Independent frozen host quantizer tables; not read from the RTL ROM.\n#pragma once\n'
        for key in ('QY','QC'):header+='static constexpr unsigned '+key+'[64]={'+','.join(map(str,tables[key]))+'};\n'
        assert (FPGA/'oracle_quant.hpp').read_text()==header
        report['verification_adapters_preserve_complete_production_body']=True
        report['production_port_count']=json.loads((FPGA/'ports.json').read_text())['production_port_count']
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','dequant_probe','--Mdir',mapped,
            '-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-I'+str(out/'sources/fpga/experiments/cu66-v104-dsp'),
            '-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('dequant_original.sv','dequant_candidate.sv','dequant_probe.sv','tb_dequant.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vdequant_probe'],'binary.log',30)
        report['binary']=dict(path=mapped+'/Vdequant_probe',sha256=(out/'binary.log').read_text().split()[0])
        for seed in (104401,104402):
            trace=out/('trace-'+str(seed)+'.jsonl')
            command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','120s',mapped+'/Vdequant_probe',str(seed),str(trace)],'simulation-'+str(seed)+'.jsonl',120)
            verdict=json.loads((out/('simulation-'+str(seed)+'.jsonl')).read_text());assert verdict['status']=='TEST_PASS' and verdict['seed']==seed
            raw_sha=sha(trace);packed=trace.with_suffix('.jsonl.gz')
            with trace.open('rb') as source,packed.open('wb') as dest:
                with gzip.GzipFile(fileobj=dest,mode='wb',filename='',mtime=0) as zipped:shutil.copyfileobj(source,zipped)
            assert hashlib.sha256(gzip.decompress(packed.read_bytes())).hexdigest()==raw_sha;trace.unlink()
            report['runs'].append(dict(seed=seed,verdict=verdict,trace=dict(path=packed.name,sha256=sha(packed),raw_sha256=raw_sha),trace_replay=replay(packed,verdict)))
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
        report.update(status='PASS',actual_RTL_run=True,clock_edges=sum(r['verdict']['clock_edges'] for r in report['runs']),public_samples=sum(r['verdict']['public_samples'] for r in report['runs']),packed_element_comparisons=sum(r['verdict']['packed_element_comparisons'] for r in report['runs']))
    except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        for trace in out.glob('*.jsonl'):
            if trace.name.startswith('trace-'):
                with trace.open('rb') as source,gzip.GzipFile(filename=str(trace.with_suffix('.jsonl.gz')),mode='wb',mtime=0) as dest:shutil.copyfileobj(source,dest)
                trace.unlink()
        report['wall_seconds']=time.monotonic()-start
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report);write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V104_DSP',report['status'],out,flush=True)


if __name__=='__main__':main()
