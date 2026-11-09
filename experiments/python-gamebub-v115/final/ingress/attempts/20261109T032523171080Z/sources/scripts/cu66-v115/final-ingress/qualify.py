#!/usr/bin/env python3
"""Fresh strict parser and refined ingress exact-public-cycle RTL qualification."""
import argparse,datetime,gzip,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v115-final-ingress';V=S/'verification';OLD=R/'fpga/experiments/cu66-v115-ingress';A=R/'experiments/python-gamebub-v115/final/ingress'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def verify():
 q=load(S/'edit-recipe.json');p=R/q['original'];c=R/q['candidate'];assert sha(p)==q['original_sha256']and sha(c)==q['candidate_sha256'];text=p.read_text()
 for e in q['edits']:assert text.count(e['before'])==e['occurrences'];text=text.replace(e['before'],e['after'],e['occurrences'])
 assert text==c.read_text()
 for e in reversed(q['edits']):assert text.count(e['after'])==e['occurrences'];text=text.replace(e['after'],e['before'],e['occurrences'])
 assert text==p.read_text()
 for b in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',p.read_text(),re.S):assert b in c.read_text()
 adapters=load(V/'adapters.json');ref=adapters['reference_module'];assert sha(R/ref['original'])==ref['original_sha256']and sha(R/ref['copy'])==ref['copy_sha256']
 assert (R/ref['copy']).read_text()==(R/ref['original']).read_text().replace('module br88_packet_ingress_sync_v91h #(','module br88_packet_ingress_sync_v91h_reference #(',1)
 for key in ('wrapper','bench'):
  e=adapters[key];assert sha(R/e['original'])==e['original_sha256']and sha(R/e['candidate'])==e['candidate_sha256'];text=(R/e['original']).read_text()
  for x in e['edits']:assert text.count(x['before'])==1;text=text.replace(x['before'],x['after'],1)
  assert text==(R/e['candidate']).read_text()
  for x in reversed(e['edits']):assert text.count(x['after'])==1;text=text.replace(x['after'],x['before'],1)
  assert text==(R/e['original']).read_text()
 # Exact unchanged parser production and its established reversible wrappers.
 assert sha(OLD/'br88_rice_elastic.sv')=='37c8f5bb79621117c0e9e05096b6edead446540b026b7240819bac39838660a3'
 old=load(OLD/'verification/adapters.json')
 for e in old['adapters']:
  if Path(e['path']).name not in ('rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp','historical_rice.cpp'):continue
  assert sha(R/e['source'])==e['source_sha256']and sha(R/e['path'])==e['sha256'];text=(R/e['source']).read_text()
  for x in e['edits']:assert text.count(x['before'])==1;text=text.replace(x['before'],x['after'],1)
  assert text==(R/e['path']).read_text()
  for x in reversed(e['edits']):assert text.count(x['after'])==1;text=text.replace(x['after'],x['before'],1)
  assert text==(R/e['source']).read_text()
 return q

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('FINAL_INGRESS_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-final-ingress-'+stamp);build.mkdir();mapped='/build/'+build.name
 parser_names=['rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp','historical_rice.cpp'];parser_files=[OLD/'verification'/n for n in parser_names]
 rice_vectors=R/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz';packet_vectors=R/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz';context=R/'fpga/experiments/cu66-v113-geometry/br88_context.sv'
 oldadapt=load(OLD/'verification/adapters.json');oldparents=[R/e['source']for e in oldadapt['adapters']if Path(e['path']).name in parser_names]
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+parser_files+oldparents+[OLD/'br88_rice_elastic.sv',OLD/'verification/adapters.json',R/recipe['original'],rice_vectors,packet_vectors,context,R/'fpga/experiments/cu66-v115-refined-ingress/verification/ingress_probe.sv',R/'fpga/experiments/cu66-v115-refined-ingress/verification/tb_ingress.cpp']))
 result=dict(schema='v115-final-ingress-zero-public-cycle-header-sum-focus-v1',status='FAIL',actual_RTL_run=False,backend='Verilator',image_id=IMAGE,source_sha256={rel(p):sha(p)for p in files},commands=[],parser_runs=[],ingress_runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,original_assertions_retained=True,parser_unchanged=True,production=[recipe],declared_public_cycle_delta=0,old_exact_checker_modified=False,contract='Unchanged full32 next-address formula captured on existing real request edge; existing WAIT computes bounds, no public bubble. Frozen93 reference versus actual final body compared on every original output edge.',scope='Actual source-bound standalone RTL focus, all original parser/value/owner checks plus direct public-cycle pair. No native timing, full parent or hardware claim.')
 began=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v115-final-ingress-'+stamp.lower()+'-'+str(len(result['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];row=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);result['commands'].append(row);start=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());result['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-start)
  assert row['exit_code']==0 and'resource_stop'not in row,name
 def compile(top,names):
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror','--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',600)
  assert '%Warning-'not in(out/(top+'-compile.log')).read_text();result[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
 try:
  for p in files:
   snapshot=out/'sources'/p.relative_to(R);snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snapshot)
  for p in parser_files+[context,OLD/'br88_rice_elastic.sv',R/recipe['candidate']]+[p for p in V.iterdir()if p.is_file()]:shutil.copyfile(p,build/p.name)
  cases=requests=0
  with gzip.open(rice_vectors,'rt')as source,(build/'rice-vectors.txt').open('w')as target:
   for line in source:
    c=json.loads(line);target.write(f"{c['id']} {c['bit_size']} {c['data_hex']or'-'} {len(c['requests'])}\n")
    for request in c['requests']:target.write(' '.join(map(str,request))+'\n')
    cases+=1;requests+=len(c['requests'])
  packets=[json.loads(line)for line in gzip.decompress(packet_vectors.read_bytes()).splitlines()];(build/'packet-vectors.txt').write_text(''.join(' '.join(map(str,(c['id'],c['blocks'],c['packet_hex'],c['dense_hex'],c['packed_hex'])))+'\n'for c in packets))
  result['expanded_input_sha256']={n:sha(build/n)for n in ('rice-vectors.txt','packet-vectors.txt')}
  command(['verilator','--version'],'version.log',30)
  compile('rice_probe',['rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp'])
  for seed in (116101,116102):
   result['actual_RTL_run']=True;name=f'parser-{seed}.log';command([mapped+'/rice_probe-obj/Vrice_probe',str(seed),mapped+f'/parser-{seed}.jsonl',mapped+'/rice-vectors.txt'],name,300)
   lines=[json.loads(line)for line in(out/name).read_text().splitlines()];v=lines[-1];historical=next(x for x in lines if x.get('type')=='verdict')
   assert v['status']=='TEST_PASS'and v['parameter_cases']==6096 and v['prepared_clocks']>100000
   assert historical['status']=='TEST_PASS'and historical['cases']==cases==1520 and historical['requests_per_configuration']==requests==173061 and historical['configurations']==8 and historical['directed_checks']==104
   result['parser_runs'].append(dict(seed=seed,verdict=v,historical=historical))
  compile('ingress_probe',['ingress_probe.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_context.sv','br88_rice_elastic.sv','tb_ingress.cpp'])
  for seed in (116201,116202):
   name=f'ingress-{seed}.log';command([mapped+'/ingress_probe-obj/Vingress_probe',str(seed),mapped+'/packet-vectors.txt'],name,300);v=json.loads((out/name).read_text().splitlines()[-1])
   assert v['status']=='TEST_PASS'and v['corpus_profiles']==160 and v['initial_cancel_retries']==54 and v['initial_successful_packets']==218
   assert v['refined_cancel_checks']==30 and v['refined_length_checks']==11 and v['cancel_retries']==84 and v['successful_packets']==259
   assert v['new_descriptor_cancel_checks']==v['new_context_cancel_checks']==v['word_tuple_cancel_checks']==6 and v['malformed_checks']==4
   assert v['public_cycle_pair_checks']==v['clock_edges']and v['requests']==v['responses']+v['canceled_read_owners'];result['ingress_runs'].append(v)
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS'
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  for src in build.glob('parser-*.jsonl'):(out/(src.name+'.gz')).write_bytes(gzip.compress(src.read_bytes(),mtime=0))
  result['wall_seconds']=time.monotonic()-began;result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'receipt.json',result);write(A/'results.json',dict(status=result['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V115_FINAL_INGRESS',result['status'],out,flush=True)
if __name__=='__main__':main()
