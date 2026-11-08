#!/usr/bin/env python3
"""Bounded strict actual Count context and extracted exact geometry stage proof."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v113-geometry';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v113/geometry'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 e=json.loads((SRC/'edit-recipe.json').read_text());p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256'] and sha(q)==e['candidate_sha256'];s=p.read_text()
 for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
 assert s==q.read_text()
 for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
 assert s==p.read_text();assert p.read_text().split('`ifndef SYNTHESIS',1)[1] in q.read_text()
 for x in json.loads((V/'adapters.json').read_text())['adapters']:
  p=ROOT/x['source'];q=ROOT/x['path'];assert sha(p)==x['source_sha256'] and sha(q)==x['sha256'];s=p.read_text()
  for a,b in x['edits']:assert s.count(a)==1;s=s.replace(a,b,1)
  assert s==q.read_text()
 # Complete inherited checker byte-for-byte; no assertion or check relaxation.
 p=ROOT/'fpga/experiments/cu66-v110-count-domain/verification/inherited_context.cpp';assert p.read_bytes()==(V/p.name).read_bytes()
 # Exact field/function/stage extraction; top interface and unrelated scalar paths are excluded.
 s=(SRC/'br88_context.sv').read_text();probe=(V/'geometry_stage_probe.sv').read_text();stage=s[s.index('    // At E request acceptance'):s.index('    always_comb begin\n        case (band)')];assert stage in probe
 functions=s[s.index('    // Exact full32-bit'):s.index('    // At E request acceptance')];assert functions in probe
 assert e['added_public_cycles']==0 and e['PREVALIDATED_EVENT_COUNT_scope_unchanged'];return e

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();recipe=verify()
 if not a.run:print('V113_GEOMETRY_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v113-geometry-'+stamp);build.mkdir();mapped='/build/'+build.name
 parser=ROOT/'fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv';vectors=ROOT/'experiments/python-gamebub-v91b/context-vectors/contexts.jsonl.gz'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+[ROOT/recipe['original'],parser,vectors]))
 r=dict(schema='v113-private-geometry-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},commands=[],context_runs=[],stage_runs=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,public_latency_delta_cycles=0,scope='Whole actual original Count/candidate context default generic unconditional all public invalid/debug/counters exact. Existing specialized owner domain unchanged. Full32 extracted actual two-stage geometry and independent integer scalar oracle; bounded campaigns, not formal all-history equivalence. No native timing or hardware qualification.')
 began=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v113-geometry-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];entry=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(entry);t=time.monotonic();stop=None
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while p.poll()is None:
    elapsed=time.monotonic()-t
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if memory()['available_bytes']<4*1024**3:stop='HOST_MEMORY_GATE'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=p.wait(timeout=20)
  entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-t);write(out/'progress.json',r);assert code==0 and not stop,(name,code,stop)
 def compile(top,names):
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',600)
  assert '%Warning-'not in(out/(top+'-compile.log')).read_text();r[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  shutil.copyfile(parser,build/parser.name)
  contexts=[json.loads(x)for x in gzip.decompress(vectors.read_bytes()).splitlines()]
  with(build/'context-vectors.txt').open('w')as f:
   for c in contexts:
    expected=c['expected'];f.write(' '.join(map(str,(c['id'],c['blocks'],c['band'],c['k0'],c['k1'],c['event_count'],c['bit_size'],c['data_hex']or'-',c.get('expected_error',0),len(expected))))+'\n')
    for coef in expected:f.write(' '.join(map(str,coef))+'\n')
  command(['verilator','--version'],'version.log',30)
  compile('context_probe',['context_original.sv','context_candidate.sv','context_probe.sv','br88_rice_elastic.sv','tb_count_domain.cpp'])
  for seed in (113401,113402):
   name=f'context-{seed}.log';command([mapped+'/context_probe-obj/Vcontext_probe',mapped+'/context-vectors.txt',str(seed),mapped+f'/geometry-{seed}.tsv'],name,240);rows=[json.loads(x)for x in(out/name).read_text().splitlines()];v=rows[-1]
   assert rows[0]['type']=='edge_verdict' and rows[0]['minimum_success_request_response_gap']==3
   assert rows[1]['type']=='domain_start_verdict' and rows[1]['cases']==8064
   assert rows[2]['type']=='geometry_verdict' and rows[2]['cases']==4260918
   assert v['status']=='TEST_PASS' and v['cases']==55 and v['configurations']==8 and v['directed_checks']==172 and v['outputs_per_configuration']==84265
   trace=build/f'geometry-{seed}.tsv';assert sha(trace)=='8254dd9da380dfbffb8446fc8d699e536314572f90c84ba9ef98c5e24353c33d';r['context_runs'].append(dict(edge=rows[0],domain=rows[1],geometry=rows[2],inherited=v,geometry_raw_sha256=sha(trace)))
  compile('geometry_stage_probe',['geometry_stage_probe.sv','tb_geometry_stage.cpp'])
  for seed in (113501,113502):
   name=f'stage-{seed}.log';command([mapped+'/geometry_stage_probe-obj/Vgeometry_stage_probe',str(seed)],name,180);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['stage_cases']==157184 and v['random_full32']==131072;r['stage_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('*.tsv'):
   with p.open('rb')as source,(out/(p.name+'.gz')).open('wb')as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0)as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-began;r['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('V113_GEOMETRY_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
