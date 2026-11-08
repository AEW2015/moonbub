#!/usr/bin/env python3
"""V113 new-latency content contract and actual V97 custom-packet chain (Verilator)."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v113/spatial';HARNESS=ROOT/'fpga/experiments/cu66-v113-harness'
NATIVE=ROOT/'experiments/python-gamebub-v112/native/20261108T195804890929Z/receipt.json'
BASELINE=ROOT/'experiments/python-gamebub-v112/canonical/results.json'
BENCH=ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
FORWARD=ROOT/'fpga/experiments/cu66-v97-forward/v97_forward.sv'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
OVERRIDES={
 'br88_context.sv':ROOT/'fpga/experiments/cu66-v113-geometry/br88_context.sv',
 'packed_scratch_v91g2.sv':ROOT/'fpga/experiments/cu66-v113-scratch/packed_scratch_v91g2.sv',
 'cu66_inverse_stream_v91j.sv':ROOT/'fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,j):Path(p).write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def derive():
 s=BENCH.read_text();edits=[
  ('#include <deque>','#include <deque>\n#include <functional>'),
  ('    Vcs88_pipeline_v91k d;std::mt19937 rng;', '    std::function<void()> before_edge,after_edge;\n    Vcs88_pipeline_v91k d;std::mt19937 rng;'),
  ('        d.eval();const bool cancel=d.reset||d.abort_packet;', '        d.eval();if(before_edge)before_edge();const bool cancel=d.reset||d.abort_packet;'),
  ('        d.clk=1;d.eval();++cycle;', '        d.clk=1;d.eval();++cycle;if(after_edge)after_edge();'),
  ('int main(int argc,char **argv){','int frozen_bench_main(int argc,char **argv){')]
 for a,b in edits:assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b,1)
 (HARNESS/'bench_transport_base.hpp').write_text(s)
 write(HARNESS/'derivation.json',dict(schema='v113-oracle-preserving-two-clock-hook-derivation-v1',original=rel(BENCH),original_sha256=sha(BENCH),derived=rel(HARNESS/'bench_transport_base.hpp'),derived_sha256=sha(HARNESS/'bench_transport_base.hpp'),edits=[dict(before=a,after=b)for a,b in edits],all_original_need_checks_retained=True,old_exact_checker_modified=False))
 rev=s
 for a,b in reversed(edits):assert rev.count(b)==1;rev=rev.replace(b,a,1)
 assert rev==BENCH.read_text()
def prepare(require_proofs):
 derive();native=load(NATIVE);control=native['source_contract'];base=load(BASELINE)
 assert base['status']=='PASS_EXACT_V112_CANONICAL' and base['actual_RTL_run']
 baseline_receipt=ROOT/base['selected_receipt'];assert load(baseline_receipt)=={k:v for k,v in base.items()if k!='selected_receipt'}
 assert base['source_sha256'][rel(BENCH)]==sha(BENCH)
 aliases=control['source_order']['rtl_read_order_aliases']+[a for a in control['source_origins']if a.endswith('.svh')]
 assert len(aliases)==18 and len(set(aliases))==18
 sources=[];origins={};replacements=[]
 for a in aliases:
  m=control['source_origins'][a];old=ROOT/m['path'];assert sha(old)==m['sha256'];p=OVERRIDES.get(old.name,old);sources.append(p);origins[a]=dict(path=rel(p),sha256=sha(p))
  if p!=old:replacements.append(dict(alias=a,original=m['path'],original_sha256=m['sha256'],candidate=rel(p),candidate_sha256=sha(p)))
 assert len(replacements)==3 and not any('v111-header' in rel(p)for p in sources)
 proofs=[ROOT/'experiments/python-gamebub-v113/geometry/results.json',ROOT/'experiments/python-gamebub-v113/scratch/results.json',ROOT/'experiments/python-gamebub-v113/inverse/selected.json']
 if require_proofs:
  for p in proofs:
   q=load(p);assert q['status']=='PASS',p
   selected=ROOT/q.get('selected_report',q.get('path',''));assert selected.is_file(),p
   if 'selected_report_sha256'in q:assert sha(selected)==q['selected_report_sha256']
   if 'sha256'in q:assert sha(selected)==q['sha256']
   target=next(x for x in OVERRIDES.values()if x.parent.name.split('cu66-v113-')[1] in str(p))
   inner=load(selected);assert inner['source_sha256'][rel(target)]==sha(target),target
 packaging=ROOT/'fpga/experiments/cu66-v112-control/packaging.json'
 files=set(sources+[BENCH,FORWARD,HARNESS/'transport.cpp',HARNESS/'bench_transport_base.hpp',HARNESS/'derivation.json',packaging,Path(__file__).resolve(),NATIVE,BASELINE,baseline_receipt])
 files.update(p for p in proofs if p.is_file())
 for p in proofs:
  if p.is_file():
   q=load(p);candidate=q.get('selected_report',q.get('path'))
   if candidate:files.add(ROOT/candidate)
 for m in base['inputs'].values():files.add(ROOT/m['source'])
 return base,baseline_receipt,sources,origins,replacements,packaging,sorted(files)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--reuse-canonical',type=Path,help='Explicit prior V113 raw receipt with both unchanged full-component proofs');a=ap.parse_args()
 base,baseline_receipt,sources,origins,replacements,packaging,files=prepare(a.run)
 if not a.run:print('V113_SPATIAL_PREPARED_NOT_RUN',json.dumps(replacements));return
 prior=None;prior_path=None;prior_out=None
 if a.reuse_canonical:
  prior_path=a.reuse_canonical.resolve();prior=load(prior_path);prior_out=prior_path.parent
  assert prior_path.is_relative_to(AREA.resolve()) and prior_path.name=='receipt.json'
  assert prior['actual_RTL_run'] and prior['seeds']==[107601,107602] and len(prior['runs'])==2
  assert prior['newly_executed_candidate_case_profiles']==44 and prior['newly_executed_candidate_directed_checks']==42
  assert prior['source_origins']==origins and prior['rtl_source_order']==[rel(p)for p in sources]
  assert prior['source_sha256'][rel(BENCH)]==sha(BENCH)
  for n,h in prior['artifact_sha256'].items():assert sha(prior_out/n)==h,n
  for row in prior['runs']:
   assert row['canonical_exact'] and row['verdict']['status']=='TEST_PASS' and row['verdict']['cases']==22 and row['verdict']['directed_checks']==21
   for m in row['artifacts'].values():assert sha(prior_out/m['path'])==m['sha256'] and hashlib.sha256(gzip.decompress((prior_out/m['path']).read_bytes())).hexdigest()==m['raw_sha256']
  files.append(prior_path);files=sorted(set(files))
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v113-spatial-'+stamp);build.mkdir();mapped='/build/'+build.name
 r=dict(schema='v113-spatial-canonical-and-custom-transport-v1',status='FAIL',actual_RTL_run=False,backend='Verilator',image_id=IMAGE,transport_rtl_source_order=[rel(FORWARD)],seeds=[107601,107602],baseline_reference=dict(path=rel(baseline_receipt),sha256=sha(baseline_receipt)),baseline_reused_actual_RTL=True,baseline_recompiled_or_rerun=False,source_sha256={rel(p):sha(p)for p in files},source_origins=origins,rtl_source_order=[rel(p)for p in sources],inputs=base['inputs'],replacements=replacements,commands=[],runs=[],transport_runs=[],memory_samples=[],newly_executed_candidate_case_profiles=0,newly_executed_candidate_directed_checks=0,full_frame_publication=False,hardware_contact=False,strict_warnings=True,assertions_disabled_or_downgraded=False,old_exact_checker_modified=False,public_cycle_equivalence_claim=False,contract='IV113.1 plus existing accepted external value/owner/drain oracle; V97 ingress commit distinct from decoder drained validated tentative candidate',limits=['Actual retained custom packet/parallel DMA source adapter; no QSPI, ESP32 CPU, native Sunshine, C2 seal or publication claim.','Canonical oracle and all original held/error/counter/physical-drain checks retained; candidate event cycles intentionally differ.','New local inverse owners do not implement full PCTL1 supervisor/session/physical ledger ownership.'])
 started=time.monotonic()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v113-spatial-'+stamp.lower()+'-'+str(len(r['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  record=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(record);began=time.monotonic()
  with(out/name).open('w')as log:
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
   while p.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-began,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);record['resource_stop']=sample;break
    time.sleep(2)
   record.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-began)
  assert record['exit_code']==0 and 'resource_stop'not in record,name
 def pack(p):
  q=out/(p.name+'.gz');q.write_bytes(gzip.compress(p.read_bytes(),mtime=0));return dict(path=q.name,sha256=sha(q),raw_sha256=sha(p))
 try:
  for p in files:
   q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  snap=lambda p:str(out/'sources'/p.relative_to(ROOT))
  for name,m in base['inputs'].items():
   p=ROOT/m['source'];assert sha(p)==m['sha256'];data=gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes();(build/name).write_bytes(data);assert sha(build/name)==m['expanded_sha256']
  packaging_data=load(packaging);admission=next(p for p in sources if p.name=='cs88_admission_v91i2a.sv');data=admission.read_bytes();assert sha(admission)==packaging_data['production_sha256'];offsets=[0]+packaging_data['split_byte_offsets']+[len(data)];fragments=[]
  for i,m in enumerate(packaging_data['fragments']):
   p=build/m['filename'];p.write_bytes(data[offsets[i]:offsets[i+1]]);assert sha(p)==m['sha256'];fragments.append(p)
  assert b''.join(p.read_bytes()for p in fragments)==data;r['lossless_compile_packaging']=packaging_data
  compiled=[mapped+'/'+fragments[0].name if p==admission else snap(p)for p in sources if p.suffix=='.sv']+[mapped+'/'+p.name for p in fragments[1:]]
  if prior is None:
   command(['verilator','--version'],'version.log',30)
   command(['verilator','--cc','--exe','--build','-j','1','--output-split','10000','--output-split-cfuncs','1000','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -DELASTIC=1',*compiled,snap(BENCH)],'compile.log',900)
   assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vcs88_pipeline_v91k')
   for reference in base['runs']:
    seed=reference['seed'];prefix='candidate-'+str(seed);command([mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
    lines=[json.loads(l)for l in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];verdict=[j for j in lines if j.get('type')=='verdict'];assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS'and verdict[0]['cases']==22 and verdict[0]['directed_checks']==21
    path=build/(prefix+'-canonical.tsv');old=reference['artifacts']['canonical_actual'];assert sha(path)==old['raw_sha256'],'canonical accepted pixel bytes differ'
    row=dict(seed=seed,verdict=verdict[0],canonical_exact=True,exact_stdout_events_cycles_and_canonical=False,artifacts=dict(events=pack(build/(prefix+'-events.jsonl')),canonical_actual=pack(path)),case_latency_metrics=[dict(id=x['id'],memory_profile=x['memory_profile'],cycles=x['cycles'],first_input=x['first_input'],last_input=x['last_input'],first_coef=x['first_coef'],last_coef=x['last_coef'],done_cycle=x['done_cycle'],last_residual=x['last_residual'])for x in lines if x.get('type')=='case'])
    r['runs'].append(row);r['actual_RTL_run']=True;r['newly_executed_candidate_case_profiles']+=22;r['newly_executed_candidate_directed_checks']+=21
  else:
   # Reuse the exact previously compiled component and independently checked
   # canonical streams. Adapter/tool-header edits do not alter that component.
   r['full_component_reuse']=dict(parent_receipt=rel(prior_path),parent_receipt_sha256=sha(prior_path),scope='Both full seeds and unchanged 18-source component; only transport adapter/tool compilation is newly executed here',new_full_component_case_profiles_in_this_attempt=0)
   compile_command=next(c['argv']for c in prior['commands']if '--Mdir'in c['argv'] and 'cs88_pipeline_v91k'in c['argv'])
   mount=next(x for x in compile_command if x.startswith('type=bind,src=/home/lori/gamebub-build/cu66-v69/'))
   old_build=Path(mount.split(',src=',1)[1].split(',dst=',1)[0]);old_obj=old_build/'obj';new_obj=build/'obj';new_obj.mkdir()
   assert sha(old_obj/'Vcs88_pipeline_v91k')==prior['binary_sha256']
   copied=list(old_obj.glob('*.h'))+[old_obj/n for n in ('Vcs88_pipeline_v91k__ALL.a','Vcs88_pipeline_v91k','verilated.o','verilated_dpi.o','verilated_threads.o')]
   r['full_component_reuse']['compiled_model_sha256']={str(p):sha(p)for p in copied}
   for p in copied:shutil.copyfile(p,new_obj/p.name)
   r['binary_sha256']=prior['binary_sha256'];r['runs']=prior['runs'];r['actual_RTL_run']=True
   r['newly_executed_candidate_case_profiles']=44;r['newly_executed_candidate_directed_checks']=42
   r['newly_executed_count_scope']='V113 campaign: 44 profiles and 42 directed checks freshly executed in the explicitly pinned parent attempt; no full component re-run in this adapter-only retry'
   for row in prior['runs']:
    seed=row['seed'];shutil.copyfile(prior_out/f'candidate-{seed}-simulation.jsonl',out/f'candidate-{seed}-simulation.jsonl')
    for m in row['artifacts'].values():shutil.copyfile(prior_out/m['path'],out/m['path'])
   for n in ('compile.log','version.log'):shutil.copyfile(prior_out/n,out/n)
  # Actual V97 model is compiled independently; no component hierarchy renaming.
  for p in [HARNESS/'transport.cpp',HARNESS/'bench_transport_base.hpp']:shutil.copyfile(p,build/p.name)
  command(['verilator','--cc','--build','-j','1','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','v97_forward','--Mdir',mapped+'/forward-obj',snap(FORWARD)],'transport-model-compile.log',300)
  assert '%Warning-'not in(out/'transport-model-compile.log').read_text()
  command(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-DELASTIC=1','-DVM_SC=0','-DVM_TRACE=0','-DVM_COVERAGE=0','-DVM_TRACE_FST=0','-DVM_TRACE_VCD=0','-I'+mapped+'/obj','-I'+mapped+'/forward-obj','-isystem','/usr/share/verilator/include','-isystem','/usr/share/verilator/include/vltstd',mapped+'/transport.cpp',mapped+'/obj/Vcs88_pipeline_v91k__ALL.a',mapped+'/forward-obj/Vv97_forward__ALL.a',mapped+'/obj/verilated.o',mapped+'/obj/verilated_dpi.o',mapped+'/obj/verilated_threads.o','-pthread','-latomic','-o',mapped+'/custom_transport'],'transport-adapter-compile.log',300)
  r['transport_binary_sha256']=sha(build/'custom_transport')
  for reference in base['runs']:
   seed=reference['seed'];prefix='transport-'+str(seed);command([mapped+'/custom_transport',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
   lines=[json.loads(l)for l in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];v=[j for j in lines if j.get('type')=='transport_verdict'];assert len(v)==1 and v[0]['status']=='TEST_PASS'and v[0]['successful_case_profiles']==12 and v[0]['abort_reset_retries']==2
   path=build/(prefix+'-canonical.tsv');assert sha(path)==reference['artifacts']['canonical_actual']['raw_sha256'],'transport canonical accepted pixel bytes differ'
   r['transport_runs'].append(dict(seed=seed,verdict=v[0],canonical_exact=True,artifacts=dict(events=pack(build/(prefix+'-events.jsonl')),canonical_actual=pack(path)),fences=[x for x in lines if x.get('type')=='custom_transport']))
  assert r['source_sha256']=={rel(p):sha(p)for p in files};r['status']='PASS_V113_SPATIAL_CANONICAL';r['custom_transport_status']='PASS_ACTUAL_V97_TO_CUSTOM_DECODER_CANONICAL'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  # Preserve failed prefixes as well as final receipts; never replace an attempt.
  for p in build.glob('*'):
   if p.is_file()and p.name.endswith(('-events.jsonl','-canonical.tsv'))and not(out/(p.name+'.gz')).exists():pack(p)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'receipt.json',r);write(AREA/'results.json',dict(r,selected_receipt=rel(out/'receipt.json')));print('V113_SPATIAL',r['status'],out,flush=True)
if __name__=='__main__':main()
