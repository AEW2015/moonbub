#!/usr/bin/env python3
"""Strict actual ingress and exact-cycle parser qualification; Root slot required."""
import argparse,datetime,gzip,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v115-ingress';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v115/ingress';IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def write(p,j):Path(p).write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=load(SRC/'edit-recipe.json')
 for e in recipe['production']:
  p=ROOT/e['original'];q=ROOT/e['candidate'];assert sha(p)==e['original_sha256']and sha(q)==e['candidate_sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==x['occurrences'];s=s.replace(x['before'],x['after'])
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==x['occurrences'];s=s.replace(x['after'],x['before'])
  assert s==p.read_text()
  blocks=re.findall(r'`ifndef SYNTHESIS(.*?)`endif',p.read_text(),re.S);assert blocks
  for block in blocks:assert block in q.read_text(),'original assertion text missing'
 a=load(V/'adapters.json')
 for e in a['adapters']:
  p=ROOT/e['source'];q=ROOT/e['path'];assert sha(p)==e['source_sha256'] and sha(q)==e['sha256'];s=p.read_text()
  for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
  assert s==q.read_text()
  for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
  assert s==p.read_text()
 assert sha(ROOT/a['wrapper_source'])==a['wrapper_source_sha256']and sha(V/'ingress_probe.sv')==a['wrapper_sha256'];return recipe

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args();recipe=verify()
 if not a.run:print('V115_INGRESS_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-ingress-'+stamp);build.mkdir();mapped='/build/'+build.name
 rice_vectors=ROOT/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz';packet_vectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz';context=ROOT/'fpga/experiments/cu66-v113-geometry/br88_context.sv'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()and'__pycache__'not in p.parts]+list(Path(__file__).parent.glob('*.py'))+[ROOT/e['original']for e in recipe['production']]+[rice_vectors,packet_vectors,context,ROOT/'fpga/experiments/cu66-v110-prefix/verification/tb_rice.cpp',ROOT/'fpga/experiments/cu66-v110-prefix/verification/rice_probe.sv',ROOT/'fpga/experiments/cu66-v110-prefix/verification/historical_rice.cpp']))
 r=dict(schema='v115-ingress-descriptor-parser-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={rel(p):sha(p)for p in files},commands=[],parser_runs=[],ingress_runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,original_assertions_retained=True,production=recipe['production'],contract=recipe['contract'],scope='Parser all original public/private stored values exact cycles with original independent scalar/golden checks retained; one complete prepared tuple adapter. Ingress is new latency-changing admitted-event dense-golden/address-owner/counter checker, not old cycle equivalence. No physical hardware/timing/full-parent claim.')
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v115-ingress-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);t=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-t,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed_seconds']>cap+20:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);e['resource_stop']=sample;break
    time.sleep(2)
   e.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-t)
  assert e['exit_code']==0 and'resource_stop'not in e,(name,e)
 def compile(top,names):
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',600)
  assert '%Warning-'not in(out/(top+'-compile.log')).read_text();r[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for n in ['br88_packet_ingress_sync_v91h.sv','br88_rice_elastic.sv']:shutil.copyfile(SRC/n,build/n)
  shutil.copyfile(context,build/context.name)
  cases=requests=0
  with gzip.open(rice_vectors,'rt')as src,(build/'rice-vectors.txt').open('w')as dst:
   for line in src:
    c=json.loads(line);dst.write(f"{c['id']} {c['bit_size']} {c['data_hex']or'-'} {len(c['requests'])}\n")
    for req in c['requests']:dst.write(' '.join(map(str,req))+'\n')
    cases+=1;requests+=len(c['requests'])
  packets=[json.loads(s)for s in gzip.decompress(packet_vectors.read_bytes()).splitlines()];(build/'packet-vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n'for x in packets))
  r['expanded_input_sha256']={n:sha(build/n)for n in ['rice-vectors.txt','packet-vectors.txt']}
  command(['verilator','--version'],'version.log',30)
  compile('rice_probe',['rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp'])
  for seed in [115201,115202]:
   name=f'parser-{seed}.log';command([mapped+'/rice_probe-obj/Vrice_probe',str(seed),mapped+f'/parser-{seed}.jsonl',mapped+'/rice-vectors.txt'],name,300);rows=[json.loads(s)for s in(out/name).read_text().splitlines()];v=rows[-1];h=next(x for x in rows if x.get('type')=='verdict');assert v['status']=='TEST_PASS'and v['parameter_cases']==6096 and v['prepared_clocks']>100000 and h['status']=='TEST_PASS'and h['cases']==cases and h['requests_per_configuration']==requests and h['configurations']==8 and h['directed_checks']>90;r['parser_runs'].append(dict(seed=seed,verdict=v,historical=h))
  compile('ingress_probe',['ingress_probe.sv','br88_packet_ingress_sync_v91h.sv','br88_context.sv','br88_rice_elastic.sv','tb_ingress.cpp'])
  for seed in [115301,115302]:
   name=f'ingress-{seed}.log';command([mapped+'/ingress_probe-obj/Vingress_probe',str(seed),mapped+'/packet-vectors.txt'],name,300);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS'and v['corpus_profiles']==160 and v['cancel_retries']==54 and v['malformed_checks']==4 and v['new_descriptor_cancel_checks']==v['new_context_cancel_checks']==v['word_tuple_cancel_checks']==6;r['ingress_runs'].append(v)
  assert r['source_sha256']=={rel(p):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('parser-*.jsonl'):
   with p.open('rb')as src,(out/(p.name+'.gz')).open('wb')as dst:
    with gzip.GzipFile(filename='',fileobj=dst,mode='wb',mtime=0)as z:shutil.copyfileobj(src,z)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V115_INGRESS',r['status'],out,flush=True)
if __name__=='__main__':main()
