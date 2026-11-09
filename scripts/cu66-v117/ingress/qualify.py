#!/usr/bin/env python3
"""Root-dispatched exact descriptor-extent focus and real-caller qualification."""
import argparse,datetime,gzip,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v117-ingress';V=S/'verification';A=R/'experiments/python-gamebub-v117/ingress'
POLICY=R/'experiments/python-gamebub-v117/study-policy.json'
NATIVE=R/'experiments/python-gamebub-v117/read-study/native/20261109T113046956485Z/receipt.json'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def verify():
 q=load(S/'edit-recipes.json')
 for e in q['production']+q['adapters']:
  p,c=R/e['original'],R/e['candidate'];assert sha(p)==e['original_sha256']and sha(c)==e['candidate_sha256'];t=p.read_text()
  for x in e['edits']:assert t.count(x['before'])==1;t=t.replace(x['before'],x['after'],1)
  assert t==c.read_text()
  for x in reversed(e['edits']):assert t.count(x['after'])==1;t=t.replace(x['after'],x['before'],1)
  assert t==p.read_text()
 for e in q['production']:
  for b in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(R/e['original']).read_text(),re.S):assert b in(R/e['candidate']).read_text()
 for group in ('unchanged_verification','unchanged_caller_verification'):
  for old,h in q[group].items():assert sha(R/old)==h and(V/Path(old).name).read_bytes()==(R/old).read_bytes()
 assert q['declared_public_cycle_delta']==0
 assert ('-'+'Wno-fatal')not in Path(__file__).read_text()
 actual=load(NATIVE);assert actual['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'and actual['result']['timing']['WNS_ns']==-1.925 and actual['start_mode']=='rtl'
 return q,actual

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');ap.add_argument('--suite',choices=('ingress','caller','all'),default='all');args=ap.parse_args();manifest,native=verify()
 if not args.run:print('V117_INGRESS_PREPARED_NOT_RUN',manifest['production'][0]['candidate_sha256']);return
 assert args.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v117-ingress-'+stamp);build.mkdir();mapped='/build/'+build.name
 vectors=R/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz';prod=[R/x['path']for x in native['source_contract']['source_origins'].values()]
 for x in native['source_contract']['source_origins'].values():assert sha(R/x['path'])==x['sha256']
 original=[R/e['original']for e in manifest['production']+manifest['adapters']]
 for group in ('unchanged_verification','unchanged_caller_verification'):original +=[R/n for n in manifest[group]]
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+original+prod+[vectors,POLICY,NATIVE,NATIVE.parent/'reports/route-setup-paths.rpt',R/'docs/cu66-v117/ingress.md']))
 result=dict(schema='v117-routed-descriptor-extents-focus-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,cflags=CFLAGS,root_grant=args.root_grant,suite=args.suite,source_sha256={rel(p):sha(p)for p in files},commands=[],ingress_runs=[],caller_runs=[],memory_samples=[],production=manifest['production'],assertions_disabled_or_downgraded=False,original_assertions_retained=True,old_exact_checker_modified=False,declared_public_cycle_delta=0,pair_skipped_edges=0,actual_routed_cause=dict(path=rel(NATIVE),sha256=sha(NATIVE)),study_policy=dict(path=rel(POLICY),sha256=sha(POLICY)),scope='Frozen final ingress vs selected descriptor extents with unchanged current parser/context; original all-public ingress pair and actual caller pair. Independent full32 prepared descriptor/request/frontier and reset-owner tests; no route/parent/hardware claim.')
 began=time.monotonic()
 def persist():write(out/'receipt.json',result)
 def command(argv,name,cap,rtl=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v117-ingress-'+stamp.lower()+'-'+str(len(result['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);result['commands'].append(row)
  if rtl:result['actual_RTL_run']=True
  persist();start=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());result['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-start)
  persist();assert row['exit_code']==0 and'resource_stop'not in row,name
 try:
  for p in files:
   t=out/'sources'/p.relative_to(R);t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,t)
  for p in prod:shutil.copyfile(p,build/p.name)
  shutil.copyfile(S/'br88_packet_ingress_sync_v91h.sv',build/'br88_packet_ingress_sync_v91h.sv')
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  shutil.copyfile(V/'br88_pipeline_pair.sv',build/'br88_pipeline_v91h.sv')
  actual=out/'compile-sources';actual.mkdir()
  for p in build.iterdir():
   if p.is_file():shutil.copyfile(p,actual/p.name)
  result['compile_sources_sha256']={p.name:sha(p)for p in actual.iterdir()if p.is_file()}
  cases=[json.loads(x)for x in gzip.decompress(vectors.read_bytes()).splitlines()]
  expanded=''.join(' '.join(map(str,(c['id'],c['blocks'],c['packet_hex'],c['dense_hex'],c['packed_hex'])))+'\n'for c in cases);(build/'packet-vectors.txt').write_text(expanded);(out/'packet-vectors.txt').write_text(expanded)
  result['expanded_input_sha256']=sha(build/'packet-vectors.txt');command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020'in(out/'version.log').read_text()
  def compile(top,names):
   command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',CFLAGS,'--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',900)
   assert '%Warning-'not in(out/(top+'-compile.log')).read_text();result[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
  if args.suite in ('ingress','all'):
   compile('ingress_probe',['ingress_probe.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_context.sv','br88_rice_elastic.sv','tb_extents.cpp'])
   for seed in (117701,117702):
    name=f'ingress-{seed}.log';command([mapped+'/ingress_probe-obj/Vingress_probe',str(seed),mapped+'/packet-vectors.txt'],name,600,rtl=True)
    rows=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')];old=next(x for x in rows if x.get('type')=='ingress_verdict');v=rows[-1]
    assert old['status']=='TEST_PASS'and old['corpus_profiles']==160 and old['initial_cancel_retries']==54 and old['initial_successful_packets']==218
    assert old['refined_cancel_checks']==30 and old['refined_length_checks']==11 and old['cancel_retries']==84 and old['successful_packets']==259
    assert old['new_descriptor_cancel_checks']==old['new_context_cancel_checks']==old['word_tuple_cancel_checks']==6 and old['malformed_checks']==4
    assert old['public_cycle_pair_checks']==old['clock_edges']and old['requests']==old['responses']+old['canceled_read_owners']
    assert v['status']=='TEST_PASS'and v['type']=='v117_ingress_extent_verdict'and v['initial_cases']==6272 and v['ready_cases']==21860 and v['cancellation_cases']==v['prepared_retries']==56 and v['pair_skipped_edges']==0
    result['ingress_runs'].append(dict(seed=seed,inherited=old,extent=v));persist()
  if args.suite in ('caller','all'):
   compile('br88_pipeline_v91h',['br88_rice_elastic.sv','br88_context.sv','br88_packet_ingress.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_packet_ingress_v91h_reference.sv','br88_packet_ingress_v91h.sv','packed_scratch_reference.sv','packed_scratch_v91g2.sv','br88_pipeline_reference.sv','br88_pipeline_candidate.sv','br88_pipeline_v91h.sv','tb_pipeline.cpp'])
   for seed in (117801,117802):
    name=f'caller-{seed}.log';command([mapped+'/br88_pipeline_v91h-obj/Vbr88_pipeline_v91h',mapped+'/packet-vectors.txt',str(seed),mapped+f'/caller-{seed}.jsonl'],name,600,rtl=True)
    rows=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')];v=rows[-1]
    assert v['status']=='TEST_PASS'and v['packets']==len(cases)and v['configurations']==2 and v['case_rows']==2*len(cases)and v['directed_checks']>=50 and v['sync_staging_checks']>0 and v['caller_prepare_checks']==18
    result['caller_runs'].append(v);persist()
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS'
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  for p in build.glob('*.jsonl*'):
   if p.is_file():(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  result['wall_seconds']=time.monotonic()-began;result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};persist();write(A/'results.json',dict(status=result['status'],actual_RTL_run=result['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V117_INGRESS',result['status'],out,flush=True)
if __name__=='__main__':main()
