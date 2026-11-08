#!/usr/bin/env python3
"""Model full record-position identity and compare complete clocked packed scratch modules."""
import argparse,datetime,gzip,hashlib,json,random,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v106-scratch';AREA=ROOT/'experiments/python-gamebub-v106/scratch';SRC=ROOT/'fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db';CONTAINER='gamebub-cu66-v69-build';PLAN_SHA='c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48'
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def ranks():
    order=[]
    for diagonal in range(15):
        rows=range(8) if diagonal&1 else range(7,-1,-1)
        order.extend(row*8+diagonal-row for row in rows if 0<=diagonal-row<8)
    assert len(set(order))==64
    return [order.index(i) for i in range(64)]
RANKS=ranks()
def old_position(word):return (word>>19)*64+RANKS[(word>>13)&63]
def model():
    AREA.mkdir(parents=True,exist_ok=True);rng=random.Random(1061101);digest=hashlib.sha256();geometry=offsets=randoms=0
    for upper in range(1<<19):
        word=(upper<<13)|(rng.getrandbits(13));block=upper>>6;raster=upper&63
        original=old_position(word);cached=(block<<6)|RANKS[raster]
        assert original==cached and original<1<<19;digest.update(cached.to_bytes(3,'little'));geometry+=1
    for _ in range(16384):
        data=rng.getrandbits(128);raw=data.to_bytes(16,'little')
        for offset in range(16):
            word=(data>>(8*offset))&0xffffffff
            byteword=int.from_bytes(raw[offset:offset+4].ljust(4,b'\0'),'little')
            assert word==byteword and old_position(word)==((word>>19)<<6)|RANKS[(word>>13)&63]
            digest.update(word.to_bytes(4,'little'));offsets+=1
    for _ in range(262144):
        word=rng.getrandbits(32);address=rng.getrandbits(32)
        assert old_position(word)==((word>>19)<<6)|RANKS[(word>>13)&63]
        assert (address&15)==address%16;randoms+=1
    for band in range(4):
        for raster in range(64):
            rank=RANKS[raster];old=(1<=rank<6 if band==1 else 6<=rank<21 if band==2 else rank>=21 if band==3 else raster==0)
            new=(1<=rank<6 if band==1 else 6<=rank<21 if band==2 else rank>=21 if band==3 else rank==0)
            assert old==new
    r=dict(schema='v106-scratch-independent-position-model-v1',status='PASS',all19bit_upper_record_values=geometry,all16_offset_line_probes=offsets,random_full32_word_address_pairs=randoms,band_rank_pairs=256,model_digest_sha256=digest.hexdigest(),seed=1061101,
        algebra='For every32-bit word, block=word[31:19] in[0,8191], rank=zigzag(word[18:13]) in[0,63]; block*64+rank is exactly the19-bit concatenation, with no carry or truncation. Lower13bits never participate. Fixed-offset logical shifts of128-bit lines zero-fill bytes16..18 at offsets13..15.',
        scope='Exhaustive upper19-bit record geometry and all band/raster combinations, independent finite random full32 records/addresses and128-bit lines; not exhaustive over all128-bit cache lines or arbitrary internal states.')
    write(AREA/'model.json',r);return r

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model-only',action='store_true');args=ap.parse_args();m=model()
    if args.model_only:print('V106_SCRATCH_MODEL PASS',m['all19bit_upper_record_values']);return
    start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-scratch-'+stamp);build.mkdir()
    files=[SRC,ROOT/'fpga/experiments/cu66-v106-plan/edit-recipe.json',ROOT/'experiments/python-gamebub-v106/plan/results.json',ROOT/'fpga/experiments/cu66-v91g2/tb_scratch_hazards.cpp',*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve(),AREA/'model.json']
    r=dict(schema='v106-scratch-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,baseline_plan_sha256=PLAN_SHA,model=m,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Complete production reachable clocked comparison plus independent record/position/dense-value oracle; not formal arbitrary state/four-state equivalence.',
            'Native timing and integrated complete encoded-packet pipeline qualification are separate checks. New memory-response input-to-cache capture logic requires real parent input-delay qualification.'])
    def command(argv,name,cap):
        entry=dict(argv=argv,timeout_seconds=cap,resource_gate=resources());r['commands'].append(entry);began=time.monotonic()
        with (out/name).open('w') as f:p=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=cap+15)
        entry.update(exit_code=p.returncode,wall_seconds=time.monotonic()-began)
        if p.returncode:raise RuntimeError('failed '+name)
    try:
        r['resource_gate']=resources();recipe=json.loads((FPGA/'edit-recipe.json').read_text());text=SRC.read_text();plan=json.loads((ROOT/'experiments/python-gamebub-v106/plan/results.json').read_text());assert plan['status']=='PASS' and plan['candidate']['sha256']==sha(SRC)==PLAN_SHA==recipe['original_sha256']
        for e in recipe['edits']:
            assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
        assert text==(FPGA/'packed_scratch_v91g2.sv').read_text() and sha(FPGA/'packed_scratch_v91g2.sv')==recipe['candidate_sha256']
        a=json.loads((FPGA/'adapter.json').read_text())
        for n,path in [('original',SRC),('candidate',FPGA/'packed_scratch_v91g2.sv')]:
            t=(FPGA/('scratch_'+n+'.sv')).read_text().replace('module scratch_'+n+' (','module packed_scratch_v91g2 (',1)
            assert t.replace(a['extra_ports'],'\n);',1).replace(a['assignments'][n],'',1)==path.read_text()
        historical=(ROOT/'fpga/experiments/cu66-v91g2/tb_scratch_hazards.cpp').read_text().replace('Vpacked_scratch_v91g2','Vscratch_probe').replace('int main(int argc,char** argv)','int historical_hazards_main(int argc,char** argv)').replace('d.eval();','d.eval();need(!d.mismatch,"historical whole scratch mismatch");')
        assert historical==(FPGA/'historical_hazards.cpp').read_text();r['complete_production_bodies_preserved_by_adapters']=True
        for p in files:
            dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--language','1800-2017','--top-module','scratch_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(FPGA/n) for n in ('scratch_original.sv','scratch_candidate.sv','scratch_probe.sv','tb_scratch.cpp')]],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text();command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vscratch_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0];r['runs']=[]
        for seed in (106401,106402):
            trace=out/f'trace-{seed}.jsonl';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','120s',mapped+'/Vscratch_probe',str(seed),str(trace)],f'seed-{seed}.jsonl',120)
            verdicts=[json.loads(line) for line in (out/f'seed-{seed}.jsonl').read_text().splitlines()];assert len(verdicts)==2 and all(v['status']=='TEST_PASS' for v in verdicts)
            historical,v=verdicts;assert historical['directed_checks']==9 and v['full_transactions']==72 and v['corrupt_response_cases']==128 and v['read_owner_cases']==4 and v['bank_mask']==15 and v['offset_mask']==65535
            cache=reads=heads=0;digest=hashlib.sha256()
            for line in trace.open('rb'):
                digest.update(line);row=json.loads(line)
                if row['kind']=='cache':
                    for bank in range(4):
                        if row['valid']&(1<<bank):
                            data=sum(row['data'][bank*4+j]<<(32*j) for j in range(4))
                            for offset in range(16):assert row['positions'][bank*16+offset]==old_position((data>>(8*offset))&0xffffffff)
                    cache+=1
                else:
                    assert row['kind']=='read' and row['position']==old_position(row['word']);reads+=1
                    if row['cursor']:assert row['head_position']==old_position(row['head_word']);heads+=1
            assert cache==v['cache_events'] and reads==v['live_reads'] and heads==v['head_compares']
            r['runs'].append(dict(seed=seed,verdict=v,historical_verdict=historical,trace_replay=dict(status='PASS',cache_events=cache,live_reads=reads,head_compares=heads,raw_sha256=digest.hexdigest())))
        r.update(actual_RTL_run=True,candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),frozen_after_focused_PASS=True)
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r['status']='PASS'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        for trace in out.glob('trace-*.jsonl'):
            with trace.open('rb') as src,trace.with_suffix('.jsonl.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        r['wall_seconds']=time.monotonic()-start;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_SCRATCH',r['status'],out,flush=True)
if __name__=='__main__':main()
