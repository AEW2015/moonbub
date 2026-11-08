#!/usr/bin/env python3
"""Exhaust all quant-cell inputs in two exact candidate helpers and retained RTL."""
import datetime,gzip,hashlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v106-math'
AREA=ROOT/'experiments/python-gamebub-v106/math'
BASELINE='eececf35da97c9b14230d464ecde7576cb7840db'
CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def python_proof(helpers):
    text=helpers['lut'];banks={};constants=0
    for match in re.finditer(r"6'd(\d+):begin(.*?)end",text,re.S):
        bank=int(match[1]);bits={int(b):int(v,16) for b,v in re.findall(r"lut(\d+)=64'h([0-9a-f]{16});",match[2])}
        assert set(bits)==set(range(11)) and bank not in banks
        banks[bank]=bits;constants+=len(bits)
    assert set(banks)==set(range(64)) and constants==704
    rows=wrap=paired=0;max_full=0
    for p in range(4):
        for tile in range(8192):
            row,column=divmod(tile,90)
            full=(row//2)*45+column//2;max_full=max(max_full,full)
            expected=(full if p==0 else tile)&2047
            # Explicit 13-bit intermediate model, separate from the LUT generator.
            row13=tile//90;column13=tile%90
            narrow=((((row13>>1)*45+(column13>>1))&8191)&2047) if p==0 else tile&2047
            bank,offset=tile>>7,(tile>>1)&63
            lut=sum(((banks[bank][b]>>offset)&1)<<b for b in range(11)) if p==0 else tile&2047
            assert narrow==lut==expected,(p,tile,narrow,lut,expected)
            rows+=1;wrap+=(p==0 and full>=2048)
            if p==0 and tile%2==0:
                row2,col2=divmod(tile+1,90)
                assert full==(row2//2)*45+col2//2;paired+=1
    assert rows==32768 and paired==4096 and max_full==2069 and wrap>0
    return dict(status='PASS',input_cases=rows,planes=4,tiles_per_plane=8192,LUT_constants_reconstructed=constants,
        Y_pairs_checked=paired,Y_return_wrap_inputs=wrap,largest_untruncated_Y_value=max_full,
        oracle='Independent Cartesian row/column integer geometry; all LUT constants decoded from helper text; all13bit inputs including invalid plane/tile positions.')


def main():
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out=AREA/'attempts'/stamp;out.mkdir(parents=True,exist_ok=False)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-math-'+stamp);build.mkdir(exist_ok=False)
    recipe_paths=[ROOT/n for n in json.loads((FPGA/'recipes.json').read_text())['recipes']]
    recipes=[json.loads(p.read_text()) for p in recipe_paths]
    originals=sorted(set(ROOT/r['original_path'] for r in recipes))
    files=[*sorted(p for p in FPGA.rglob('*') if p.is_file()),*originals,Path(__file__).resolve()]
    report=dict(schema='v106-math-combinational-exhaustive-v1',status='FAIL',baseline_revision=BASELINE,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,
        strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Two-state pure combinational helper equivalence over every input; full-module/canonical/native timing measured separately.',
            'LUT table constants count is a logical construction count, not measured mapped LUT count.',
            'No hardware FPS, complete decode latency or timing-closure qualification.'])
    def command(argv,name,timeout):
        entry=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());report['commands'].append(entry);began=time.monotonic()
        with (out/name).open('w') as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
        entry.update(exit_code=r.returncode,wall_seconds=time.monotonic()-began)
        if r.returncode:raise RuntimeError('failed '+name)
    try:
        report['resource_gate']=resources();helpers=json.loads((FPGA/'helpers.json').read_text())
        report['python_proof']=python_proof(helpers)
        production=[]
        for recipe in recipes:
            src=ROOT/recipe['original_path'];dest=ROOT/recipe['candidate_path']
            assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(src.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(src)
            assert sha(src)==recipe['original_sha256'] and sha(dest)==recipe['candidate_sha256']
            before=src.read_text();after=before
            for edit in recipe['edits']:
                assert after.count(edit['before'])==edit['expected_occurrences']==1
                assert edit['before']==helpers['original'] and edit['after']==helpers[recipe['variant']]
                after=after.replace(edit['before'],edit['after'],1)
            assert after==dest.read_text()
            normalized=dest.read_text().replace(helpers[recipe['variant']],helpers['original'],1)
            assert normalized==before
            production.append(dict(variant=recipe['variant'],path=recipe['candidate_path'],sha256=sha(dest),
                recipe_path=str(recipe_paths[recipes.index(recipe)].relative_to(ROOT)),recipe_sha256=sha(recipe_paths[recipes.index(recipe)])))
        probe=(FPGA/'math_probe.sv').read_text()
        for variant in ('original','narrow','lut'):
            assert helpers[variant].replace(' quant_cell(',' '+variant+'_quant_cell(',1) in probe
        report['six_complete_production_bodies_unchanged_outside_exact_helper']=True
        for p in files:
            target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','math_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',copy(FPGA/'math_probe.sv'),copy(FPGA/'tb_math.cpp')],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vmath_probe'],'binary.log',30)
        report['binary_sha256']=(out/'binary.log').read_text().split()[0]
        trace=out/'trace.tsv'
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','30s',mapped+'/Vmath_probe',str(trace)],'simulation.jsonl',30)
        verdict=json.loads((out/'simulation.jsonl').read_text());assert verdict['status']=='TEST_PASS' and verdict['cases']==32768
        count=0;seen=set()
        for line in trace.read_text().splitlines():
            p,tile,original,narrow,lut=map(int,line.split());assert (p,tile) not in seen;seen.add((p,tile))
            row,column=divmod(tile,90);expected=(((row//2)*45+column//2) if p==0 else tile)&2047
            assert original==narrow==lut==expected;count+=1
        assert count==32768 and seen==set((p,t) for p in range(4) for t in range(8192))
        report.update(actual_RTL_run=True,terminal_verdict=verdict,trace_replay=dict(status='PASS',rows=count,
            oracle='All32768 actual RTL input/output rows checked against independent Cartesian integer geometry.'),
            production=production,frozen_after_focused_PASS=True)
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
        report['status']='PASS'
    except BaseException as error:report.update(error_class=type(error).__name__,error=str(error));raise
    finally:
        trace=out/'trace.tsv'
        if trace.exists():
            report['raw_trace_sha256']=sha(trace)
            with trace.open('rb') as src,(out/'trace.tsv.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        report['wall_seconds']=time.monotonic()-started
        report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report);write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_MATH',report['status'],out,flush=True)
if __name__=='__main__':main()
