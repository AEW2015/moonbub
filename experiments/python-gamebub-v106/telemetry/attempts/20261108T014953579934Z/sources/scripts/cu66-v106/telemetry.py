#!/usr/bin/env python3
"""Clocked full-production telemetry comparison and independent52word counter oracle."""
import datetime,gzip,hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v106-telemetry';AREA=ROOT/'experiments/python-gamebub-v106/telemetry';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db';CONTAINER='gamebub-cu66-v69-build'
SRC=ROOT/'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv';FIXTURE=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
DEPS=[ROOT/('fpga/experiments/'+p) for p in ('cu66-v91/br88_rice_elastic.sv','cu66-v91b/br88_context.sv','cu66-v91d/br88_packet_ingress.sv','cu66-v91g2/packed_scratch_v91g2.sv','cu66-v91h/br88_packet_ingress_v91h.sv','cu66-v91h/br88_packet_ingress_sync_v91h.sv')]
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def main():
    start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-telemetry-'+stamp);build.mkdir()
    files=[SRC,*DEPS,FIXTURE,ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp',*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve()]
    r=dict(schema='v106-telemetry-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,
        limits=['Prepared child/controller/counter states test the actual production modules but are not packet-reachability or formal arbitrary-state proof.',
            'Historical packet streams supplement prepared states; comparison/oracle runs on every edge while historical retained trace is sampled every256edges plus resets/starts/aborts.',
            'No native mapping/timing, hardware FPS or complete validated latency qualification.'])
    def command(argv,name,timeout):
        e=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());r['commands'].append(e);began=time.monotonic()
        with (out/name).open('w') as f:result=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+15)
        e.update(exit_code=result.returncode,wall_seconds=time.monotonic()-began)
        if result.returncode:raise RuntimeError('failed '+name)
    try:
        r['resource_gate']=resources();recipe=json.loads((FPGA/'edit-recipe.json').read_text());text=SRC.read_text()
        assert hashlib.sha256(subprocess.check_output(['git','show',BASELINE+':'+str(SRC.relative_to(ROOT))],cwd=ROOT)).hexdigest()==sha(SRC)==recipe['original_sha256']
        for edit in recipe['edits']:
            assert text.count(edit['before'])==edit['expected_occurrences']==1;text=text.replace(edit['before'],edit['after'],1)
        assert text==(FPGA/'br88_pipeline_v91h.sv').read_text() and sha(FPGA/'br88_pipeline_v91h.sv')==recipe['candidate_sha256']
        for name,path in [('original',SRC),('candidate',FPGA/'br88_pipeline_v91h.sv')]:
            assert (FPGA/('telemetry_'+name+'.sv')).read_text().replace('module telemetry_'+name+' #','module br88_pipeline_v91h #',1)==path.read_text()
        historical=(ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp').read_text().replace('Vbr88_pipeline_v91h','Vtelemetry_probe').replace('int main(int argc,char** argv)','int historical_pipeline_main(int argc,char** argv)').replace('        d.clk=1;d.eval();','        telemetry_pre(d);d.clk=1;d.eval();telemetry_post(d);',1)
        assert historical==(FPGA/'historical_pipeline.cpp').read_text()
        r['complete_production_bodies_preserved_by_module_rename']=True;r['historical_bench_only_renames_and_pre_post_hooks']=True
        for p in files:
            d=out/'sources'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
        cases=[json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()];vectors=out/'vectors.txt'
        vectors.write_text(''.join(' '.join(map(str,(v['id'],v['blocks'],v['packet_hex'],v['dense_hex'],v['packed_hex'])))+'\n' for v in cases));r['fixtures']=dict(cases=len(cases),sha256=sha(FIXTURE),text_sha256=sha(vectors))
        copy=lambda p:str(out/'sources'/p.relative_to(ROOT));mapped='/build/'+build.name
        command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30);command(['docker','exec',CONTAINER,'g++','--version'],'compiler.log',30)
        command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','telemetry_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DSYNC_STAGING=1',*[copy(FPGA/n) for n in ('telemetry_original.sv','telemetry_candidate.sv','telemetry_probe.sv')],*[copy(p) for p in DEPS],copy(FPGA/'tb_telemetry.cpp')],'compile.log',300)
        assert '%Warning-' not in (out/'compile.log').read_text()
        command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vtelemetry_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0]
        trace=out/'trace.jsonl';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','180s',mapped+'/Vtelemetry_probe','1069001',str(trace),str(vectors)],'simulation.jsonl',180)
        records=[json.loads(line) for line in (out/'simulation.jsonl').read_text().splitlines()];verdict=records[-1]
        assert verdict['type']=='telemetry_verdict' and verdict['status']=='TEST_PASS' and verdict['prepared_cases']==53248 and verdict['prepared_edges']==106497 and verdict['counter_words']==52 and verdict['carry_positions']==64 and verdict['guard_running_combinations']==16
        historical_verdict=next(x for x in records if x['type']=='verdict');assert historical_verdict['status']=='TEST_PASS' and historical_verdict['packets']==len(cases) and historical_verdict['configurations']==2
        # Independent replay of every prepared-clock value; historical snapshots remain sampled evidence.
        current=[0]*52;clocks=preparations=historical_rows=0;historical=False;coverage=set();rawsha=hashlib.sha256()
        for line in trace.open('rb'):
            rawsha.update(line);event=json.loads(line)
            if 'model_start' in event:historical=True;continue
            if 'prepare' in event:
                assert len(event['counts'])==52;current=event['counts'];preparations+=1;coverage.add((event['kind'],event['word'],event['carry'],event['action']));continue
            if historical:historical_rows+=1;continue
            if event['guards']:current=[0]*52
            elif event['running']:
                for i in (event['emitter'],4+event['packet'],20+event['scratch']):current[i]=(current[i]+1)&((1<<64)-1)
            assert event['counts']==current;clocks+=1
        assert clocks==106497 and preparations==53248 and len(coverage)==53248 and historical_rows==verdict['historical_trace_rows']
        r.update(actual_RTL_run=True,terminal_verdict=verdict,historical_verdict=historical_verdict,trace_replay=dict(status='PASS',prepared_clocks=clocks,prepared_cases=preparations,historical_checkpoints=historical_rows,raw_sha256=rawsha.hexdigest()),
            candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),frozen_after_focused_PASS=True)
        assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r['status']='PASS'
    except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
    finally:
        (out/'vectors.txt').unlink(missing_ok=True);trace=out/'trace.jsonl'
        if trace.exists():
            r['raw_trace_sha256']=sha(trace)
            with trace.open('rb') as src,(out/'trace.jsonl.gz').open('wb') as dst:
                with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
            trace.unlink()
        r['wall_seconds']=time.monotonic()-start;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT))))
        print('V106_TELEMETRY',r['status'],out,flush=True)
if __name__=='__main__':main()
