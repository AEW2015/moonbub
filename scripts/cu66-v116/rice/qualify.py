#!/usr/bin/env python3
"""Root-dispatched strict standalone Rice and real-context ingress qualification."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v116-rice'
V=S/'verification'
A=R/'experiments/python-gamebub-v116/rice'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def verify():
 sys.dont_write_bytecode=True
 spec=importlib.util.spec_from_file_location('v116_rice_emit',Path(__file__).with_name('emit.py'))
 emitter=importlib.util.module_from_spec(spec);spec.loader.exec_module(emitter)
 # Reuse its exact reversible checks without invoking argument parsing.
 recipe=json.loads((S/'edit-recipe.json').read_text())
 p=R/recipe['original'];c=R/recipe['candidate']
 assert sha(p)==emitter.PIN==recipe['original_sha256']
 assert sha(c)==recipe['candidate_sha256']
 assert emitter.transform(p.read_text(),emitter.EDITS)==c.read_text()
 text=c.read_text()
 for e in reversed(recipe['edits']):
  assert text.count(e['after'])==e['occurrences'];text=text.replace(e['after'],e['before'],e['occurrences'])
 assert text==p.read_text()
 for e in json.loads((V/'adapters.json').read_text())['adapters']:
  src=R/e['source'];dst=R/e['path'];assert sha(src)==e['source_sha256']and sha(dst)==e['sha256']
  assert emitter.transform(src.read_text(),[(x['before'],x['after'],x['occurrences'])for x in e['edits']])==dst.read_text()
 # Preserve every old check body. Only prepared-state initialization changes.
 old=R/'fpga/experiments/cu66-v115-ingress/verification'
 assert (old/'historical_rice.cpp').read_bytes()==(V/'historical_rice.cpp').read_bytes()
 def check_body(t,start,end):return t[t.index(start):t.index(end,t.index(start))]
 assert check_body((old/'tb_rice.cpp').read_text(),'static void verify(', 'static void rice_pre(')==check_body((V/'tb_rice.cpp').read_text(),'static void verify(', 'static void rice_pre(')
 import re
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',p.read_text(),re.S):assert block in c.read_text()
 assert c.read_text().count('successful_payload<=')==1
 assert c.read_text().count('output_zero<=1;')==3
 assert ('-'+'Wno-fatal') not in Path(__file__).read_text()
 return recipe

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
 f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--suite',choices=('parser','ingress','all'),default='all');args=ap.parse_args();recipe=verify()
 if not args.run:
  print('V116_RICE_PREPARED_NOT_RUN',recipe['candidate_sha256']);return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=A/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v116-rice-'+stamp);build.mkdir();mapped='/build/'+build.name
 vectors=R/'experiments/python-gamebub-v91/rtl-vectors/cases.jsonl.gz'
 packet_vectors=R/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
 context=R/'fpga/experiments/cu66-v113-geometry/br88_context.sv'
 ingress=R/'fpga/experiments/cu66-v115-final-ingress/br88_packet_ingress_sync_v91h.sv'
 adapters=json.loads((V/'adapters.json').read_text())['adapters']
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+[R/e['source']for e in adapters]+[R/recipe['original'],vectors,packet_vectors,context,ingress]))
 result=dict(schema='v116-rice-unreset-successful-payload-exact-cycle-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,cflags=CFLAGS,suite=args.suite,source_sha256={rel(p):sha(p)for p in files},commands=[],parser_runs=[],ingress_runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,original_assertions_retained=True,old_exact_checker_modified=False,old_historical_body_modified=False,production=[recipe],declared_public_cycle_delta=0,contract='All original public outputs compared every edge including invalid, reset, error, start, and holds. Private payload only successful suffix writes; logical zero view reproduces all old clear edges.',scope='Focused parser and production real-context ingress simulation only; no timing, formal, full-parent, hardware, or achieved-clock claim.')
 began=time.monotonic()
 def receipt():write(out/'receipt.json',result)
 def command(argv,name,cap,rtl_run=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v116-rice-'+stamp.lower()+'-'+str(len(result['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);result['commands'].append(row)
  if rtl_run:result['actual_RTL_run']=True
  receipt() # Persist the true execution flag before launch, including failures.
  start=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());result['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-start)
  receipt();assert row['exit_code']==0 and'resource_stop'not in row,name
 def compile(top,names):
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',CFLAGS,'--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',900)
  assert '%Warning-'not in(out/(top+'-compile.log')).read_text()
  result[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
 try:
  for p in files:
   snapshot=out/'sources'/p.relative_to(R);snapshot.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snapshot)
  for p in [context,ingress,R/recipe['candidate']]+[p for p in V.iterdir()if p.is_file()]:shutil.copyfile(p,build/p.name)
  cases=requests=0
  with gzip.open(vectors,'rt')as source,(build/'rice-vectors.txt').open('w')as target:
   for line in source:
    c=json.loads(line);target.write(f"{c['id']} {c['bit_size']} {c['data_hex']or'-'} {len(c['requests'])}\n")
    for req in c['requests']:target.write(' '.join(map(str,req))+'\n')
    cases+=1;requests+=len(c['requests'])
  packets=[json.loads(line)for line in gzip.decompress(packet_vectors.read_bytes()).splitlines()]
  (build/'packet-vectors.txt').write_text(''.join(' '.join(map(str,(c['id'],c['blocks'],c['packet_hex'],c['dense_hex'],c['packed_hex'])))+'\n'for c in packets))
  expanded=out/'expanded-inputs';expanded.mkdir()
  for n in ('rice-vectors.txt','packet-vectors.txt'):shutil.copyfile(build/n,expanded/n)
  result['expanded_input_sha256']={n:sha(build/n)for n in ('rice-vectors.txt','packet-vectors.txt')};receipt()
  command(['verilator','--version'],'version.log',30)
  assert 'Verilator 5.020' in (out/'version.log').read_text()
  if args.suite in ('parser','all'):
   compile('rice_probe',['rice_original.sv','rice_candidate.sv','rice_probe.sv','tb_rice.cpp'])
   for seed in (116301,116302):
    name=f'parser-{seed}.log';command([mapped+'/rice_probe-obj/Vrice_probe',str(seed),mapped+f'/parser-{seed}.jsonl',mapped+'/rice-vectors.txt'],name,600,rtl_run=True)
    lines=[json.loads(line)for line in(out/name).read_text().splitlines()];v=lines[-1];historical=next(x for x in lines if x.get('type')=='verdict')
    assert v['status']=='TEST_PASS'and v['parameter_cases']==6096 and v['prepared_clocks']>100000 and v['view_directed_checks']>=600
    assert historical['status']=='TEST_PASS'and historical['cases']==cases==1520 and historical['requests_per_configuration']==requests==173061 and historical['configurations']==8 and historical['directed_checks']==104
    result['parser_runs'].append(dict(seed=seed,verdict=v,historical=historical));receipt()
  if args.suite in ('ingress','all'):
   compile('ingress_probe',['ingress_probe.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_context_reference.sv','br88_context.sv','rice_original.sv','br88_rice_elastic.sv','tb_ingress.cpp'])
   for seed in (116401,116402):
    name=f'ingress-{seed}.log';command([mapped+'/ingress_probe-obj/Vingress_probe',str(seed),mapped+'/packet-vectors.txt'],name,600,rtl_run=True);v=json.loads((out/name).read_text().splitlines()[-1])
    assert v['status']=='TEST_PASS'and v['corpus_profiles']==160 and v['initial_cancel_retries']==54 and v['initial_successful_packets']==218
    assert v['refined_cancel_checks']==30 and v['refined_length_checks']==11 and v['cancel_retries']==84 and v['successful_packets']==259
    assert v['new_descriptor_cancel_checks']==v['new_context_cancel_checks']==v['word_tuple_cancel_checks']==6 and v['malformed_checks']==4
    assert v['public_cycle_pair_checks']==v['clock_edges']and v['requests']==v['responses']+v['canceled_read_owners'];result['ingress_runs'].append(v);receipt()
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS'
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  for src in build.glob('parser-*.jsonl'):(out/(src.name+'.gz')).write_bytes(gzip.compress(src.read_bytes(),mtime=0))
  result['wall_seconds']=time.monotonic()-began
  result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
  receipt();write(A/'results.json',dict(status=result['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
  print('V116_RICE',result['status'],out,flush=True)
if __name__=='__main__':main()
