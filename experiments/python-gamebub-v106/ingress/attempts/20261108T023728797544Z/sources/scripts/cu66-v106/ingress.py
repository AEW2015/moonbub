#!/usr/bin/env python3
"""Compare the actual full sync ingress in complete old/new production pipelines."""
import argparse,datetime,gzip,hashlib,json,random,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];FPGA=ROOT/'fpga/experiments/cu66-v106-ingress';AREA=ROOT/'experiments/python-gamebub-v106/ingress';BASELINE='eececf35da97c9b14230d464ecde7576cb7840db';CONTAINER='gamebub-cu66-v69-build'
SRC=ROOT/'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv';FIXTURE=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
DEPS=[ROOT/('fpga/experiments/'+p) for p in ('cu66-v106-suffix/br88_rice_elastic.sv','cu66-v106-context/br88_context.sv','cu66-v91d/br88_packet_ingress.sv','cu66-v91g2/packed_scratch_v91g2.sv')]
sys.path.insert(0,str(ROOT/'scripts/cu66-v100'))
from run_rtl import resources

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def model():
 mask=(1<<32)-1;rows=wraps=0;rng=random.Random(106410)
 points=[0,1,7,8,15,16,17,31,32,33,0x7fffffff,0x80000000,0xffffffe0,0xfffffff0,mask]
 pairs=[(a,b) for a in points for b in points]+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(100000)]
 for size,replay in pairs:
  remaining=(size-replay)&mask
  for cap in (16,32):
   bits=min(remaining,cap)
   assert (((replay+bits)&mask)==size)==(remaining==bits)
   assert ((remaining-bits)&mask)==((size-((replay+bits)&mask))&mask)
   for cancel,initialize,accept in ((1,1,1),(0,1,1),(0,0,1),(0,0,0)):
    actual=0 if cancel else size if initialize else (remaining-bits)&mask if accept else remaining
    expected=0 if cancel else (size-0)&mask if initialize else (size-((replay+bits)&mask))&mask if accept else (size-replay)&mask
    assert actual==expected
   rows+=1;wraps+=int(replay>size)
 return dict(schema='v106-ingress-mod32-model-v1',status='PASS',rows=rows,wrapped_subtractions=wraps,full32_induction={'reset_abort_replacement_start':'cache=0; replay=0; inactive except replacement may enter RECEIVE','context_start':'replay_next=0; cache_next=sizes[band]','accepted_word':'cache_next=cache-bits mod2^32; replay_next=replay+bits mod2^32','hold':'both hold; size[band] is unchanged throughout live context','last':'(replay+bits==size) iff (size-replay==bits) in Z/(2^32)'},scope='Algebra is universal modulo32; numeric rows are sampled evidence, not exhaustive 2^64 input enumeration. Inactive private ctx_bits/ctx_last deliberately unqualified.')
def verify_sources():
 recipe=json.loads((FPGA/'edit-recipe.json').read_text());s=SRC.read_text();assert sha(SRC)==recipe['original_sha256']
 for edit in recipe['edits']:assert s.count(edit['before'])==edit['expected_occurrences']==1;s=s.replace(edit['before'],edit['after'],1)
 assert s==(FPGA/SRC.name).read_text() and sha(FPGA/SRC.name)==recipe['candidate_sha256']
 for name,p in [('original',SRC),('candidate',FPGA/SRC.name)]:
  assert (FPGA/('ingress_'+name+'.sv')).read_text().replace('module ingress_'+name+' #(','module br88_packet_ingress_sync_v91h #(',1)==p.read_text()
  assert (FPGA/('packet_'+name+'.sv')).read_text().replace('module packet_'+name+' #(','module br88_packet_ingress_v91h #(',1).replace('ingress_'+name+' #(','br88_packet_ingress_sync_v91h #(',1)==(ROOT/'fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv').read_text()
  assert (FPGA/('pipeline_'+name+'.sv')).read_text().replace('module pipeline_'+name+' #','module br88_pipeline_v91h #',1).replace('packet_'+name+' #','br88_packet_ingress_v91h #',1)==(ROOT/'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv').read_text()
 h=(ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp').read_text().replace('Vbr88_pipeline_v91h','Vingress_probe').replace('int main(int argc,char** argv)','int historical_pipeline_main(int argc,char** argv)').replace('        d.clk=1;d.eval();','        ingress_pre(d);d.clk=1;d.eval();ingress_post(d);',1)
 assert h==(FPGA/'historical_pipeline.cpp').read_text()
 return recipe

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--model-only',action='store_true');args=parser.parse_args();AREA.mkdir(exist_ok=True);write(AREA/'model.json',model());recipe=verify_sources()
 if args.model_only:print('PASS_INGRESS_MODEL_AND_RECIPES');return
 start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v106-ingress-'+stamp);build.mkdir();mapped='/build/'+build.name
 files=[SRC,*DEPS,FIXTURE,ROOT/'fpga/experiments/cu66-v91h/tb_pipeline.cpp',ROOT/'fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv',ROOT/'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv',*sorted(p for p in FPGA.iterdir() if p.is_file()),Path(__file__).resolve(),AREA/'model.json']
 r=dict(schema='v106-ingress-clocked-production-comparison-v1',status='FAIL',baseline_revision=BASELINE,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},commands=[],runs=[],actual_RTL_run=False,strict_warnings=True,assertions_disabled_or_downgraded=False,candidate=dict(path=recipe['candidate_path'],sha256=recipe['candidate_sha256'],recipe_sha256=sha(FPGA/'edit-recipe.json')),limits=['Prepared full32 cache-consistent child/controller states are verification-only and not packet-reachability or formal arbitrary-state proof.','Full protocol bench covers real packets, cancellation, malformed streams, stalls, old/new complete pipelines and every synchronous ingress public output.','Independent replay/cache/counter and child Rice reservoir/loaded/consumed/counter oracle runs every clock. Trace is all prepared clocks and sampled historical checkpoints.','Private ctx_bits/ctx_last may differ outside CONTEXT_RUN; both child in_valid and stage_word_valid are then false; unchanged child in_ready has no in_bits/in_last dependency.','Two-state simulation, not four-state, native mapping, board FPS or validated latency proof.'])
 def command(argv,name,timeout):
  e=dict(argv=argv,timeout_seconds=timeout,resource_gate=resources());r['commands'].append(e);began=time.monotonic()
  with (out/name).open('w') as f:result=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout+15)
  e.update(exit_code=result.returncode,wall_seconds=time.monotonic()-began)
  if result.returncode:raise RuntimeError('failed '+name)
 try:
  r['resource_gate']=resources();r['complete_production_bodies_preserved_by_module_rename_and_type_substitution']=True;r['historical_bench_only_renames_and_pre_post_hooks']=True
  for p in files:
   d=out/'sources'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
  cases=[json.loads(line) for line in gzip.decompress(FIXTURE.read_bytes()).splitlines()];vectors=out/'vectors.txt';vectors.write_text(''.join(' '.join(map(str,(v['id'],v['blocks'],v['packet_hex'],v['dense_hex'],v['packed_hex'])))+'\n' for v in cases));r['fixtures']=dict(cases=len(cases),sha256=sha(FIXTURE),text_sha256=sha(vectors));copy=lambda p:str(out/'sources'/p.relative_to(ROOT))
  sv=[FPGA/(n+'.sv') for n in ('ingress_original','ingress_candidate','packet_original','packet_candidate','pipeline_original','pipeline_candidate','ingress_probe')]
  command(['docker','exec',CONTAINER,'verilator','--version'],'verilator.log',30)
  command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','300s','verilator','--cc','--exe','--build','-j','2','--assert','-Wall','-Wno-DECLFILENAME','--public-flat-rw','--language','1800-2017','--top-module','ingress_probe','--Mdir',mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*[copy(p) for p in sv],*[copy(p) for p in DEPS],copy(FPGA/'tb_ingress.cpp')],'compile.log',300)
  assert '%Warning-' not in (out/'compile.log').read_text();command(['docker','exec',CONTAINER,'sha256sum',mapped+'/Vingress_probe'],'binary.log',30);r['binary_sha256']=(out/'binary.log').read_text().split()[0]
  for seed in (106401,106402):
   trace=out/('seed-'+str(seed)+'.jsonl');log='seed-'+str(seed)+'.log';command(['docker','exec',CONTAINER,'timeout','--kill-after=5s','180s',mapped+'/Vingress_probe',str(seed),str(trace),str(vectors)],log,180)
   records=[json.loads(line) for line in (out/log).read_text().splitlines()];v=records[-1];hist=next(x for x in records if x['type']=='verdict');assert v['type']=='ingress_verdict' and v['status']=='TEST_PASS' and v['prepared_cases']==5760 and v['prepared_updates']>0 and v['prepared_initializations']>0 and hist['status']=='TEST_PASS' and hist['packets']==len(cases) and hist['configurations']==2
   v['historical_verdict']=hist;r['runs'].append(v)
  r.update(status='PASS_ACTUAL_INGRESS_CACHE_EQUIVALENCE',actual_RTL_run=True,total_clock_edges=sum(v['prepared_edges']+v['historical_edges'] for v in r['runs']),frozen_after_focused_PASS=True)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files}
 except BaseException as e:r.update(error_class=type(e).__name__,error=str(e));raise
 finally:
  (out/'vectors.txt').unlink(missing_ok=True)
  for trace in sorted(out.glob('*.jsonl')):
   with trace.open('rb') as src,(out/(trace.name+'.gz')).open('wb') as dst:
    with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0) as z:shutil.copyfileobj(src,z)
   trace.unlink()
  r['wall_seconds']=time.monotonic()-start;r['artifacts_sha256']={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()};write(out/'receipt.json',r);write(AREA/'probe-results.json',dict(schema='v106-ingress-probe-selection-v1',status=r['status'],selected_receipt=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('V106_INGRESS',r['status'],out,flush=True)
if __name__=='__main__':main()
