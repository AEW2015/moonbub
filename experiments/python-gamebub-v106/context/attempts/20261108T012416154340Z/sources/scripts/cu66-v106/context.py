#!/usr/bin/env python3
"""Full32 byte-identity proof and strict clocked full-production context comparison."""
import argparse,datetime,gzip,hashlib,json,random,re,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v106-context';AREA=ROOT/'experiments/python-gamebub-v106/context'
SRC=ROOT/'fpga/experiments/cu66-v91b/br88_context.sv';PARSER=ROOT/'fpga/experiments/cu66-v91/br88_rice_elastic.sv'
FIXTURE=ROOT/'experiments/python-gamebub-v91b/context-vectors/contexts.jsonl.gz';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db';CONTAINER='gamebub-cu66-v69-build'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def tables():
    h=json.loads((FPGA/'helpers.json').read_text());data={}
    for key,body in re.findall(r"4'd(\d+):begin(.*?)endcase",h['helpers'],re.S):
        b,i=divmod(int(key),4);values={int(v):int(pair,16) for v,pair in re.findall(r"8'd(\d+):return 22'h([0-9a-f]{6});",body)}
        assert b in (1,2,3) and set(values)==set(range(256)) and (b,i) not in data
        divisor=(5,15,43)[b-1]
        for v,pair in values.items():
            q,r=divmod(v<<(8*i),divisor);assert pair==((q&65535)<<6)|r
        data[b,i]=[values[v] for v in range(256)]
    assert len(data)==12
    zz=list(map(int,re.findall(r"6'd(\d+)",h['ZIGZAG'])))
    assert len(zz)==64 and sorted(zz)==list(range(64))
    correction={}
    for b,body in re.findall(r"2'd(\d+):begin(.*?)endcase",h['helpers'],re.S):
        b=int(b);values={int(v):(int(q)<<6)|zz[int(index)] for v,q,index in re.findall(r"8'd(\d+):return \{2'd(\d+),ZIGZAG\[6'd(\d+)\]\};",body)}
        if not values:continue
        assert b in (1,2,3) and set(values)==set(range(256))
        d=(5,15,43)[b-1];offset=(1,6,21)[b-1]
        for total,pair in values.items():assert pair==(((total//d)&3)<<6)|zz[offset+total%d]
        correction[b]=[values[v] for v in range(256)]
    assert len(correction)==3
    return data,zz,correction

def inputs():
    for b,d in ((1,5),(2,15),(3,43)):
        for n in range(65536*d+1):yield b,n,0,'valid'
        for n in (0,1,4,5,14,15,42,43,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff):yield b,n,(~n)&0xffffffff,'edge'
    for b,d in ((1,5),(2,15),(3,43)):
        for target in (d-1,d,2*d-1,2*d,3*d-1,3*d,4*(d-1)):
            remaining=target;n=0
            for i in range(4):
                residue=min(remaining,d-1);remaining-=residue
                v=next(v for v in range(256) if (v<<(8*i))%d==residue);n|=v<<(8*i)
            assert remaining==0
            yield b,n,0,'edge'
    rng=1068001
    for i in range(131072):
        rng^=(rng<<13)&0xffffffffffffffff;rng^=rng>>7;rng^=(rng<<17)&0xffffffffffffffff;n=rng&0xffffffff
        rng^=(rng<<13)&0xffffffffffffffff;rng^=rng>>7;rng^=(rng<<17)&0xffffffffffffffff;e=rng&0xffffffff
        yield i%3+1,n,e,'random'
    for b in range(256):
        if b==0 or b>3:
            for n in (0,1,0x80000000,0xffffffff):yield b,n,(~n)&0xffffffff,'default'

def model():
    AREA.mkdir(parents=True,exist_ok=True);t,zz,corrections=tables();digest=hashlib.sha256();counts=dict(valid=0,edge=0,random=0,default=0);maximum_rem=0;rows=0
    for b,n,e,kind in inputs():
        if b in (1,2,3):
            d=(5,15,43)[b-1];offset=(1,6,21)[b-1]
            w0=t[b,0][n&255];w1=t[b,1][(n>>8)&255];w2=t[b,2][(n>>16)&255];w3=t[b,3][n>>24]
            total=(w0&63)+(w1&63)+(w2&63)+(w3&63);maximum_rem=max(maximum_rem,total)
            correction=corrections[b][total]>>6
            assert correction==total//d and total<=4*(d-1)
            rem=total-correction*d;q=((w0>>6)+(w1>>6)+(w2>>6)+(w3>>6)+correction)&65535
            assert (q,rem)==((n//d)&65535,n%d)
            geometry=(q<<6)|(corrections[b][total]&63)
            assert geometry==(((n//d)&65535)<<6)|zz[offset+n%d]
        else:geometry=(e&65535)<<6
        digest.update(f'{b}\t{n}\t{e}\t{geometry}\t{geometry}\n'.encode());rows+=1;counts[kind]+=1
    assert rows==4260918 and counts==dict(valid=4128771,edge=63,random=131072,default=1012)
    r=dict(schema='v106-context-full32-byte-identity-model-v1',status='PASS',rows=rows,coverage=counts,
        byte_constants_checked=3072,correction_index_constants_checked=768,theoretical_remainder_sum_bound=168,max_remainder_sum=maximum_rem,all_band_values_covered=256,
        raw_geometry_trace_sha256=digest.hexdigest(),random_seed=1068001,
        algebra='For n=sum(256^i*byte_i), write each term=d*q_i+r_i. Then floor(n/d)=sum(q_i)+floor(sum(r_i)/d), n mod d=sum(r_i) mod d. Reducing each q_i modulo65536 preserves the final quotient modulo65536. Each r_i<d gives sum(r_i)<=4*(d-1)<=168 and correction<=3.',
        scope='Universal algebra plus exhaustive byte constants/all valid positions and large deterministic full32 tests; not exhaustive over all2^32 positions or unknown logic values.')
    write(AREA/'model.json',r);return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model-only',action='store_true');args=ap.parse_args();m=model()
    if args.model_only:print('V106_CONTEXT_MODEL PASS',m['rows']);return
    started=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True)
    build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-context-'+stamp);build.mkdir()
    files=[SRC,PARSER,FIXTURE,*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve(),ROOT/'fpga/experiments/cu66-v91b/tb_context.cpp',AREA/'model.json']
    r=dict(schema='v106-context-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,model=m,
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Universal byte identity and deterministic binary tests, not formal arbitrary-state/four-state equivalence.',
            'Complete-module clocked interface comparison; fullpipeline and native timing are separate gates.'])
    def command(argv,name,timeout):
        e=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());r['commands'].append(e);began=time.monotonic()
        with (out/name).open('w') as log:result=subprocess.run(argv,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+15)
        e.update(exit_code=result.returncode,wall_seconds=time.monotonic()-began)
        if result.returncode:raise RuntimeError('failed '+name)
    try:
        r['resource_gate']=resources();recipe=json.loads((FPGA/'edit-recipe.json').read_text());text=SRC.read_text()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)==recipe['original_sha256']
        for e in recipe['edits']:
            assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
        assert text==(FPGA/'br88_context.sv').read_text() and sha(FPGA/'br88_context.sv')==recipe['candidate_sha256']
        a=json.loads((FPGA/'adapter.json').read_text());h=json.loads((FPGA/'helpers.json').read_text())
        for variant,production in [('original',SRC),('candidate',FPGA/'br88_context.sv')]:
            text=(FPGA/('context_'+variant+'.sv')).read_text().replace('module context_'+variant+' (','module br88_context (',1)
            assert text.replace(a['extra_ports'],'\n);',1).replace(a['assignments'],'',1)==production.read_text()
        probe=(FPGA/'context_probe.sv').read_text();assert h['helpers'] in probe and h['original_geometry'] in probe
        r['complete_production_bodies_preserved_by_adapters']=True
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        fixtures=[json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()]
        vectors=out/'vectors.txt'
        with vectors.open('w') as f:
            for c in fixtures:
                expected=c['expected'];f.write(' '.join(map(str,(c['id'],c['blocks'],c['band'],c['k0'],c['k1'],c['event_count'],c['bit_size'],c['data_hex'] or '-',c.get('expected_error',0),len(expected))))+'\n')
                for coef in expected:f.write(' '.join(map(str,coef))+'\n')
        r['fixtures']=dict(cases=len(fixtures),outputs_per_configuration=sum(len(c['expected']) for c in fixtures),sha256=sha(FIXTURE),text_sha256=sha(vectors))
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','context_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('context_original.sv','context_candidate.sv','context_probe.sv')],copy(PARSER),copy(FPGA/'tb_context.cpp')],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vcontext_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0]
        trace=out/'geometry.tsv';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s',mapped+'/Vcontext_probe',str(vectors),'1068001',str(trace)],'simulation.jsonl',300)
        rows=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()]
        geom=rows[0];verdict=rows[-1];assert geom['type']=='geometry_verdict' and geom['status']=='TEST_PASS' and geom['cases']==m['rows'] and geom['valid_domain_cases']==4128771 and geom['random_full32_cases']==131072
        assert verdict['type']=='verdict' and verdict['status']=='TEST_PASS' and verdict['cases']==55 and verdict['configurations']==8 and verdict['outputs_per_configuration']==84265
        assert len([v for v in rows if v['type']=='case'])==55*8
        # Python independently replays every actual geometry row, not only the terminal count.
        _,zz,_=tables();digest=hashlib.sha256();count=0
        with trace.open('rb') as f:
            for line in f:
                b,n,e,old,new=map(int,line.split());d=(5,15,43)[b-1] if b in (1,2,3) else 1;offset=(1,6,21)[b-1] if b in (1,2,3) else 0
                expected=(((n//d)&65535)<<6)|zz[offset+n%d] if b in (1,2,3) else (e&65535)<<6
                assert old==new==expected;digest.update(line);count+=1
        assert count==m['rows'] and digest.hexdigest()==m['raw_geometry_trace_sha256']
        r.update(actual_RTL_run=True,geometry_verdict=geom,terminal_verdict=verdict,trace_replay=dict(status='PASS',rows=count,raw_sha256=digest.hexdigest()),
            candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),frozen_after_focused_PASS=True)
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r['status']='PASS'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        (out/'vectors.txt').unlink(missing_ok=True);trace=out/'geometry.tsv'
        if trace.exists():
            r['raw_trace_sha256']=sha(trace)
            with trace.open('rb') as src,(out/'geometry.tsv.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_CONTEXT',r['status'],out,flush=True)
if __name__=='__main__':main()
