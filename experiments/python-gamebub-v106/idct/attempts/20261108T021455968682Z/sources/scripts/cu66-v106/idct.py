#!/usr/bin/env python3
"""Independently model two-pass Q14 tiles and compare complete clocked IDCT modules."""
import argparse,datetime,gzip,hashlib,json,random,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v106-idct';AREA=ROOT/'experiments/python-gamebub-v106/idct';SRC=ROOT/'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv';FIXTURE=ROOT/'fpga/experiments/cu66-v69/inverse/tiles.hex';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db';CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources
HALF=((5793,5793,5793,5793),(8035,6811,4551,1598),(7568,3135,-3135,-7568),(6811,-1598,-8035,-4551),(5793,-5793,-5793,5793),(4551,-8035,1598,6811),(3135,-7568,7568,-3135),(1598,-4551,6811,-8035))
BASIS=[tuple(row)+tuple(((-1 if k%2 else 1)*row[p]) for p in (3,2,1,0)) for k,row in enumerate(HALF)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def signed(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def unpack(h,bits):
    word=int(h,16);return [signed((word>>(bits*i))&((1<<bits)-1),bits) for i in range(64)]
def packed(v,bits):return ''.join(f'{x&((1<<bits)-1):0{bits//4}x}' for x in v[::-1])
def inverse(tile):
    if any(x < -522240 or x>522240 for x in tile):return [0]*64,1
    middle=[0]*64;output=[0]*64
    for row in range(8):
        for p in range(8):middle[8*row+p]=(sum(tile[8*row+k]*BASIS[k][p] for k in range(8))+8192)>>14
    for p in range(8):
        for column in range(8):output[8*p+column]=(sum(middle[8*k+column]*BASIS[k][p] for k in range(8))+8192)>>14
    assert all(-(1<<23)<=x<(1<<23) for x in middle+output)
    return output,0

def model():
    AREA.mkdir(parents=True,exist_ok=True);lines=[];old=0
    for line in FIXTURE.read_text().splitlines():
        ident,data,golden,error=line.split();tile=unpack(data,20);expected,bad=inverse(tile)
        assert expected==unpack(golden,24) and bad==int(error),ident;lines.append(line);old+=1
    assert old==3471;rng=random.Random(1061001)
    extras=[]
    for _ in range(512):extras.append([rng.randint(-522240,522240) for _ in range(64)])
    for _ in range(64):extras.append([rng.randint(-522240,522240)]+[0]*63)
    for index in range(64):
        for value in (-524288,-522241,522241,524287):
            tile=[0]*64;tile[index]=value;extras.append(tile)
    for tile in extras:
        golden,bad=inverse(tile);lines.append(f'{len(lines)+1} {packed(tile,20)} {packed(golden,24)} {bad}')
    data=('\n'.join(lines)+'\n').encode();path=AREA/'vectors.hex.gz'
    with path.open('wb') as stream:
        with gzip.GzipFile(filename='',mode='wb',fileobj=stream,mtime=0) as z:z.write(data)
    r=dict(schema='v106-idct-independent-integer-model-v1',status='PASS',original_tiles=old,extra_tiles=len(extras),tiles=len(lines),
        original_fixture_sha256=sha(FIXTURE),vectors=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),raw_sha256=hashlib.sha256(data).hexdigest()),
        arbitrary_AC_tiles=512,additional_DC_tiles=64,additional_invalid_domain_tiles=256,
        oracle='Independent dense two-pass integer Q14 matrix using full8-position basis, separate round(+8192)>>14 aftereachpass; no NumPy or productionRTL/helper import.')
    write(AREA/'model.json',r);return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model-only',action='store_true');args=ap.parse_args();m=model()
    if args.model_only:print('V106_IDCT_MODEL PASS',m['tiles']);return
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-idct-'+stamp);build.mkdir()
    files=[SRC,FIXTURE,ROOT/'fpga/experiments/cu66-v69/inverse/fixtures.json',ROOT/'fpga/experiments/cu66-v69/inverse/tb_idct.sv',*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve(),AREA/'model.json',AREA/'vectors.hex.gz']
    r=dict(schema='v106-idct-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,model=m,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Actual complete-module reachable-state clocked comparison and independentinteger gold; not formal arbitraryinternal-state/four-state proof.',
            'No native DSPmapping/timing, hardware FPS or complete validated frame latency qualification.'])
    def command(argv,name,timeout):
        e=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());r['commands'].append(e);began=time.monotonic()
        with (out/name).open('w') as f:result=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+15)
        e.update(exit_code=result.returncode,wall_seconds=time.monotonic()-began)
        if result.returncode:raise RuntimeError('failed '+name)
    try:
        r['resource_gate']=resources();recipe=json.loads((FPGA/'edit-recipe.json').read_text());text=SRC.read_text()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)==recipe['original_sha256']
        for e in recipe['edits']:
            assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
        assert text==(FPGA/'cu66_idct8x8.sv').read_text() and sha(FPGA/'cu66_idct8x8.sv')==recipe['candidate_sha256']
        a=json.loads((FPGA/'adapter.json').read_text())
        for name,path in [('original',SRC),('candidate',FPGA/'cu66_idct8x8.sv')]:
            s=(FPGA/('idct_'+name+'.sv')).read_text().replace('module idct_'+name+' (','module cu66_idct8x8 (',1)
            assert s.replace(a['extra_ports'],'\n);',1).replace(a['assignments'],'',1)==path.read_text()
        r['complete_production_bodies_preserved_by_adapters']=True
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        vectors=out/'vectors.hex';vectors.write_bytes(gzip.decompress((AREA/'vectors.hex.gz').read_bytes()));copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','idct_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('idct_original.sv','idct_candidate.sv','idct_probe.sv','tb_idct.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text();command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vidct_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0]
        r['runs']=[]
        for seed in (106401,106402):
            trace=out/f'trace-{seed}.jsonl';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','120s',mapped+'/Vidct_probe',str(vectors),str(seed),str(trace)],f'seed-{seed}.jsonl',120)
            verdict=json.loads((out/f'seed-{seed}.jsonl').read_text());assert verdict['status']=='TEST_PASS' and verdict['tiles']==4303 and verdict['directed_abort_reset_cases']==30 and verdict['abort_state_mask']==1023 and verdict['states']==1023
            products=[0]*8;rows=mul=0
            for line in trace.open():
                v=json.loads(line)
                if v['kill']:products=[0]*8
                elif v['mul']:products=[a*b for a,b in zip(v['samples'],v['basis'])];mul+=1
                assert v['products']==products;rows+=1
            assert rows==verdict['clock_edges'] and mul==verdict['multiply_edges']
            r['runs'].append(dict(seed=seed,verdict=verdict,trace_replay=dict(status='PASS',rows=rows,multiply_edges=mul,raw_sha256=sha(trace))))
        r.update(actual_RTL_run=True,candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),frozen_after_focused_PASS=True)
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r['status']='PASS'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        (out/'vectors.hex').unlink(missing_ok=True)
        for trace in out.glob('trace-*.jsonl'):
            with trace.open('rb') as src,trace.with_suffix('.jsonl.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_IDCT',r['status'],out,flush=True)
if __name__=='__main__':main()
