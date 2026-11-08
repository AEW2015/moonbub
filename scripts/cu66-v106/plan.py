#!/usr/bin/env python3
"""Prove full32-bit modular scratch prefix identities and clocked production comparison."""
import argparse,datetime,gzip,hashlib,itertools,json,random,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
FPGA=ROOT/'fpga/experiments/cu66-v106-plan';AREA=ROOT/'experiments/python-gamebub-v106/plan'
SRC=ROOT/'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db'
CONTAINER='gamebub-cu66-v69-build';MASK=2**32-1
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def aligned(x):return ((x&MASK)+15)&0xfffffff0
def csa3(a,b,c):return ((a^b^c)+(((a&b)|(a&c)|(b&c))<<1))&MASK
def csa4(a,b,c,d):return csa3(a^b^c,(((a&b)|(a&c)|(b&c))<<1)&MASK,d)
def csa5(a,b,c,d,e):
    s=a^b^c;carry=(((a&b)|(a&c)|(b&c))<<1)&MASK
    return csa3(s^d^e,(((s&d)|(s&e)|(d&e))<<1)&MASK,carry)
def prefixes(blocks,raw,c1,c2,c3):
    terms=[32,aligned(blocks*2),aligned(c1*4),aligned(c2*4),aligned(c3*4)]
    a,b,c,d,e=terms;p1=(a+b)&MASK;p2=(p1+c)&MASK;p3=(p2+d)&MASK
    used=(32+blocks*128)&MASK if raw else (p3+e)&MASK
    assert csa3(a,b,c)==p2 and csa4(a,b,c,d)==p3
    assert csa5(a,b,c,d,e)==((p3+e)&MASK)
    return p1,p2,p3,used

def cases():
    edges=(0,1,2,3,4,15,16,17,0x3ffffffc,0x3fffffff,0x40000000,0x7fffffff,0x80000000,0xfffffffc,0xfffffffe,0xffffffff)
    for b in (0,1,7,8,9,8191,8192,8193,65535,65536,131071):
        for c in itertools.product(edges,repeat=3):
            for raw in range(2):yield (b,raw,*c)
    patterns=((0,0,0),(1,2,3),(0x3fffffff,0x3fffffff,0x3fffffff),(0xffffffff,0x80000000,0x40000000))
    for b in range(131072):yield b,b&1,*patterns[b%4]
    rng=random.Random(1067001)
    for _ in range(65536):yield rng.getrandbits(17),rng.getrandbits(1),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32)
    for _ in range(4096):
        b=rng.randrange(1,8193);yield b,0,rng.randrange(b*5+1),rng.randrange(b*15+1),rng.randrange(b*43+1)

def model():
    AREA.mkdir(parents=True,exist_ok=True);path=AREA/'vectors.tsv.gz';rawsha=hashlib.sha256();rows=0;valid=0;wrapped=0
    # Per-bit truth table is a closed local proof of the carry-save identity.
    for a,b,c in itertools.product((0,1),repeat=3):
        assert a+b+c==(a^b^c)+2*((a&b)|(a&c)|(b&c))
    with path.open('wb') as dst:
        with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as stream:
            for inputs in cases():
                b,raw,c1,c2,c3=inputs;result=prefixes(*inputs)
                # Direct unbounded integer oracle, applying only original arithmetic wrap points.
                a=aligned(2*b);s1=(32+a)&MASK;s2=(s1+aligned(4*c1))&MASK;s3=(s2+aligned(4*c2))&MASK
                end=(32+128*b)&MASK if raw else (s3+aligned(4*c3))&MASK
                assert result==(s1,s2,s3,end)
                invalid=b==0 or b>8192 or c1>b*5 or c2>b*15 or c3>b*43 or (raw and (c1 or c2 or c3)) or end>262144
                valid+=not invalid;wrapped+=any(c>=2**30 for c in (c1,c2,c3))
                line=('\t'.join(map(str,(*inputs,*result)))+'\n').encode();stream.write(line);rawsha.update(line);rows+=1
    result=dict(schema='v106-plan-independent-modular-model-v1',status='PASS',rows=rows,valid_plan_inputs=valid,
        high_count_inputs=wrapped,all17bit_block_values_exercised=131072,seed=1067001,
        vectors=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),raw_sha256=rawsha.hexdigest()),
        algebra='For each bit a+b+c=(a XOR b XOR c)+2*majority(a,b,c); summing bit weights and discarding carry beyond bit31 proves modulo2^32 identity. Repeated compressor stages preserve the sum; each prefix is independent.',
        scope='Exact modulo32 identity, no input/state narrowing or guard assumptions; deterministic edge/full-block-domain/random vectors are not exhaustive over three32bit counts.')
    write(AREA/'model.json',result);return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model-only',action='store_true');args=ap.parse_args();m=model()
    if args.model_only:print('V106_PLAN_MODEL PASS',m['rows']);return
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-plan-'+stamp);build.mkdir()
    files=[SRC,*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v91g2/tb_scratch_hazards.cpp',AREA/'vectors.tsv.gz',AREA/'model.json']
    report=dict(schema='v106-plan-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,model=m,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Universal CSA algebra plus deterministic full32 modular test cases; not exhaustive over all3x32bit count tuples.',
            'Focused complete-module clocked equivalence; fullpipeline and native/routed timing are separate checks.'])
    def command(argv,name,timeout):
        item=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());report['commands'].append(item);began=time.monotonic()
        with (out/name).open('w') as log:r=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
        item.update(exit_code=r.returncode,wall_seconds=time.monotonic()-began)
        if r.returncode:raise RuntimeError('failed '+name)
    try:
        report['resource_gate']=resources();recipe=json.loads((FPGA/'edit-recipe.json').read_text());text=SRC.read_text()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)==recipe['original_sha256']
        for e in recipe['edits']:
            assert e['expected_occurrences']==text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
        assert text==(FPGA/'packed_scratch_v91g2.sv').read_text() and sha(FPGA/'packed_scratch_v91g2.sv')==recipe['candidate_sha256']
        adapter=json.loads((FPGA/'adapter.json').read_text())
        for variant,production in [('original',SRC),('candidate',FPGA/'packed_scratch_v91g2.sv')]:
            t=(FPGA/('plan_'+variant+'.sv')).read_text().replace('module plan_'+variant+' (','module packed_scratch_v91g2 (',1)
            assert t.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'],'',1)==production.read_text()
        report['complete_production_body_preserved_by_adapters']=True
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        vectors=out/'vectors.tsv';vectors.write_bytes(gzip.decompress((AREA/'vectors.tsv.gz').read_bytes()))
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
        command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','plan_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('plan_original.sv','plan_candidate.sv','plan_probe.sv','tb_plan.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vplan_probe'],'binary.log',30);report['binary_sha256']=(out/'binary.log').read_text().split()[0]
        trace=out/'trace.tsv';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','120s',mapped+'/Vplan_probe',str(vectors),str(trace)],'simulation.jsonl',120)
        rows=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()]
        assert len(rows)==2 and all(r['status']=='TEST_PASS' for r in rows)
        assert rows[0]['rows']==m['rows'] and rows[0]['clocked_begin_cases']==(m['rows']+31)//32 and rows[0]['priority_checks']==1
        assert rows[1]['directed_checks']==9
        rawsha=hashlib.sha256();n=0
        for line in trace.open('rb'):
            inputs=tuple(map(int,line.split()));assert tuple(inputs[5:])==prefixes(*inputs[:5]);rawsha.update(line);n+=1
        assert n==m['rows'] and rawsha.hexdigest()==m['vectors']['raw_sha256']
        report.update(actual_RTL_run=True,terminal_verdicts=rows,trace_replay=dict(status='PASS',rows=n,raw_sha256=rawsha.hexdigest()),
            candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),frozen_after_focused_PASS=True)
        assert report['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};report['status']='PASS'
    except BaseException as e:report.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        (out/'vectors.tsv').unlink(missing_ok=True);trace=out/'trace.tsv'
        if trace.exists():
            report['raw_trace_sha256']=sha(trace)
            with trace.open('rb') as src,(out/'trace.tsv.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        report['wall_seconds']=time.monotonic()-started;report['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',report);write(AREA/'results.json',dict(report,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_PLAN',report['status'],out,flush=True)
if __name__=='__main__':main()
