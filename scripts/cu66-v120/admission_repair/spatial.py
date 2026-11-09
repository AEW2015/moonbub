#!/usr/bin/env python3
"""V120 spatial validation and owned domain controls with exact V119 scheduling and independent goldens."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,threading,collections
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
AREA=ROOT/'experiments/python-gamebub-v120/repair-study/spatial';HARNESS=ROOT/'fpga/experiments/cu66-v117-harness'
NATIVE=ROOT/'experiments/python-gamebub-v115/final/native/20261109T040313064127Z/receipt.json'
BASELINE=ROOT/'experiments/python-gamebub-v113/spatial/results.json'
B_CANONICAL=ROOT/'experiments/python-gamebub-v119/integrated-study/spatial/results.json'
BENCH=ROOT/'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
FULL_BENCH=HARNESS/'bench_command_api.cpp'
API_DERIVATION=HARNESS/'bench-api-derivation.json'
FORWARD=ROOT/'fpga/experiments/cu66-v97-forward/v97_forward.sv'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
OVERRIDES={
 'cs88_coefficients_v91k.sv':ROOT/'fpga/experiments/cu66-v119-owner/cs88_coefficients_v91k.sv',
 'br88_packet_ingress_sync_v91h.sv':ROOT/'fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv',
 'br88_rice_elastic.sv':ROOT/'fpga/experiments/cu66-v116-rice/br88_rice_elastic.sv',
 'cs88_admission_v91i2a.sv':ROOT/'fpga/experiments/cu66-v120-admission-match/cs88_admission_v91i2a.sv',
 'packed_scratch_v91g2.sv':ROOT/'fpga/experiments/cu66-v119-scratch/packed_scratch_v91g2.sv',
 'br88_pipeline_v91h.sv':ROOT/'fpga/experiments/cu66-v116b-control/br88_pipeline_v91h.sv',
 'cu66_coefficient_elastic.sv':ROOT/'fpga/experiments/cu66-v116b-domain/cu66_coefficient_elastic.sv',
 'cu66_inverse_stream_v91j.sv':ROOT/'fpga/experiments/cu66-v117-throughput/cu66_inverse_stream_v91j.sv',
 'cu66_reconstruct_stream_v91k.sv':ROOT/'fpga/experiments/cu66-v119-owner/cu66_reconstruct_stream_v91k.sv'}
FOCUSED={
 'experiments/python-gamebub-v119/owner/producer/results.json':['cs88_coefficients_v91k.sv'],
 'experiments/python-gamebub-v120/range/results.json':['br88_packet_ingress_sync_v91h.sv'],
 'experiments/python-gamebub-v116/rice/results.json':['br88_rice_elastic.sv'],
 'experiments/python-gamebub-v120/admission-match/results.json':['cs88_admission_v91i2a.sv'],
 'experiments/python-gamebub-v116/control-b/results.json':['br88_pipeline_v91h.sv'],
 'experiments/python-gamebub-v116/domain-b/results.json':['cu66_coefficient_elastic.sv'],
 'experiments/python-gamebub-v119/scratch/results.json':['packed_scratch_v91g2.sv'],
 'experiments/python-gamebub-v117/throughput/inverse/results.json':['cu66_inverse_stream_v91j.sv'],
 'experiments/python-gamebub-v119/owner/reconstruct/results.json':['cu66_reconstruct_stream_v91k.sv']}
PRIMARY_RUNNER=ROOT/'scripts/cu66-v114/spatial.py'
PRIMARY_RUNNER_SHA256='19dda677968bf539d7723777dedb7a59af02e1b6808bd1c5665e6302ac1b254e'
HARNESS_PINS={'bench_command_api.cpp': '1e741341d18fcde01cdd18ef752a9c88db0e8837ca10898cd015d723aceb4c90', 'bench-api-derivation.json': 'b197c0f301fca5503412a02eb7590195f7147a5b6985e3657386e5d16c565db8', 'bench_transport_base.hpp': '98c7cd7de9502a040f2de538da2ff7456192d06da622b50a3c2ef1e344ffed0f', 'derivation.json': '8d2a58c3e8ad429c21c86265e3bb15928ac6f431e7e26bda65b7f8551002ca82', 'transport.cpp': '266d9669092ca3893245b86a3281e321a7157819aaab406fbfef1e2c7f0bf5b2', 'admission_monitor.hpp': '7e45ba077fe1fcbf26e1a9235043ead0732fb2f00177529493ccfb26df17e1c3'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def write(p,j):Path(p).write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def derive():
 # Read/verify only: the primary runner and a concurrently running primary proof
 # own these files. Reconstruct both adaptations in memory and reverse them.
 assert sha(PRIMARY_RUNNER)==PRIMARY_RUNNER_SHA256
 for n,h in HARNESS_PINS.items():assert sha(HARNESS/n)==h,n
 original=BENCH.read_text();assert sha(BENCH)=='ec51ee82e4981d00a432aab633defd01e5fe638dbe999e4a41de2f2a5ad12384' and len(original.splitlines())==496
 def verify(meta,source,derived):
  assert sha(source)==meta['original_sha256'] and sha(derived)==meta['derived_sha256']
  text=source.read_text()
  for e in meta['edits']:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
  assert text==derived.read_text()
  for e in reversed(meta['edits']):assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
  assert text==source.read_text()
 verify(load(API_DERIVATION),BENCH,FULL_BENCH)
 verify(load(HARNESS/'derivation.json'),FULL_BENCH,HARNESS/'bench_transport_base.hpp')
 assert load(HARNESS/'derivation.json')['bench_api_derivation']['sha256']==sha(API_DERIVATION)
def prepare(require_proofs):
 derive();assert sha(NATIVE)=='0a71ca28ff7379da6bcdccf94d21bb1b0f8592fff27390734736d98d1a976995';native=load(NATIVE);control=native['source_contract'];base=load(BASELINE)
 assert base['status']=='PASS_V113_SPATIAL_CANONICAL' and base['actual_RTL_run']
 baseline_receipt=ROOT/base['selected_receipt'];assert load(baseline_receipt)=={k:v for k,v in base.items()if k!='selected_receipt'}
 assert base['source_sha256'][rel(BENCH)]==sha(BENCH)
 aliases=control['source_order']['rtl_read_order_aliases']+[a for a in control['source_origins']if a.endswith('.svh')]
 assert len(aliases)==18 and len(set(aliases))==18
 sources=[];origins={};replacements=[]
 for a in aliases:
  m=control['source_origins'][a];old=ROOT/m['path'];assert sha(old)==m['sha256'];p=OVERRIDES.get(old.name,old);sources.append(p);origins[a]=dict(path=rel(p),sha256=sha(p))
  if p!=old:replacements.append(dict(alias=a,original=m['path'],original_sha256=m['sha256'],candidate=rel(p),candidate_sha256=sha(p)))
 assert len(replacements)==9 and {Path(x['alias']).name for x in replacements}==set(OVERRIDES)
 assert not any('v111-header' in rel(p)for p in sources)
 proofs=[ROOT/name for name in FOCUSED]
 if require_proofs:
  for p in proofs:
   q=load(p);assert q['status']=='PASS',p
   selected=ROOT/q.get('selected_report',q.get('path',''));assert selected.is_file(),p
   if 'selected_report_sha256'in q:assert sha(selected)==q['selected_report_sha256']
   if 'sha256'in q:assert sha(selected)==q['sha256']
   inner=load(selected);assert inner['status']=='PASS' and inner.get('assertions_disabled_or_downgraded',False) is False
   assert inner.get('actual_RTL_run',inner.get('backend')=='Verilator') is True
   for name in FOCUSED[rel(p)]:assert inner['source_sha256'][rel(OVERRIDES[name])]==sha(OVERRIDES[name]),name
   commands=[c if isinstance(c,list) else c['argv'] for c in inner['commands']]
   compiles=[c for c in commands if 'verilator' in c and '--cc' in c]
   assert compiles and all('--assert' in c and '-Wall' in c and '-Wno-fatal' not in c for c in compiles)
   assert all('-CFLAGS' in c and '-Werror' in c[c.index('-CFLAGS')+1] for c in compiles)
   for n,h in inner['source_sha256'].items():assert sha(ROOT/n)==h,n
   artifacts=inner.get('artifact_sha256',inner.get('artifacts_sha256',{}));assert artifacts
   for n,h in artifacts.items():assert sha(selected.parent/n)==h,n
 packaging=ROOT/'fpga/experiments/cu66-v120-admission-match/packaging.json'
 files=set(sources+[BENCH,FULL_BENCH,API_DERIVATION,FORWARD,HARNESS/'transport.cpp',HARNESS/'admission_monitor.hpp',HARNESS/'bench_transport_base.hpp',HARNESS/'derivation.json',packaging,Path(__file__).resolve(),PRIMARY_RUNNER,NATIVE,BASELINE,baseline_receipt])
 b=load(B_CANONICAL);assert b['status']=='PASS_V119_FINAL_SPATIAL_CANONICAL'and b['actual_RTL_run'] is True
 bp=ROOT/b['selected_receipt'];assert load(bp)=={k:v for k,v in b.items()if k!='selected_receipt'}
 for n,h in b['source_sha256'].items():assert sha(ROOT/n)==h,n
 for n,h in b['artifact_sha256'].items():assert sha(bp.parent/n)==h,n
 files.update([B_CANONICAL,bp])
 for seed in (107601,107602):
  for prefix in ('candidate','transport'):files.add(bp.parent/f'{prefix}-{seed}-simulation.jsonl')
 files.update(p for p in proofs if p.is_file())
 for p in proofs:
  if p.is_file():
   q=load(p);candidate=q.get('selected_report',q.get('path'))
   if candidate:files.add(ROOT/candidate)
 for m in base['inputs'].values():files.add(ROOT/m['source'])
 return base,baseline_receipt,sources,origins,replacements,packaging,sorted(files)
def semantic_events(actual,baseline_gz,stdout,prefix):
 # Independent event comparison excludes time and interleaving only. Successful
 # cases must retain every transform/reference/canonical accepted event tuple.
 successful={(x['id'],x['memory_profile']) for x in stdout if x.get('type')=='case' and x['error']==0}
 assert successful,prefix
 def normalize(raw):
  answer=collections.Counter()
  for line in raw.splitlines():
   x=json.loads(line)
   if (x['id'],x['memory_profile']) not in successful:continue
   for key in ('cycle','first_cycle','last_cycle'):x.pop(key,None)
   answer[json.dumps(x,sort_keys=True,separators=(',',':'))]+=1
  return answer
 a=normalize(actual.read_text());b=normalize(gzip.decompress(baseline_gz.read_bytes()).decode())
 assert a==b,dict(prefix=prefix,extra=list((a-b).items())[:3],missing=list((b-a).items())[:3])
 assert sum(a.values())>1000
 return sum(a.values())
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--attempt-id');ap.add_argument('--pair-grant-file',type=Path);a=ap.parse_args()
 base,baseline_receipt,sources,origins,replacements,packaging,files=prepare(a.run)
 if not a.run:print('V120_SPATIAL_PREPARED_NOT_RUN',json.dumps(replacements));return
 stamp=a.attempt_id or datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 assert datetime.datetime.strptime(stamp,'%Y%m%dT%H%M%S%fZ').strftime('%Y%m%dT%H%M%S%fZ')==stamp
 out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v120-admission-repair-spatial-'+stamp);build.mkdir();mapped='/build/'+build.name
 r=dict(schema='v120-admission-repair-spatial-validation-owned-bounds-canonical-v1',variant='v120-admission-repair-study',primary_runner_reference=dict(path=rel(PRIMARY_RUNNER),sha256=PRIMARY_RUNNER_SHA256),shared_harness_read_only_verified=True,status='FAIL',actual_RTL_run=False,simulation_started=False,backend='Verilator',image_id=IMAGE,transport_rtl_source_order=[rel(FORWARD)],seeds=[107601,107602],baseline_reference=dict(path=rel(baseline_receipt),sha256=sha(baseline_receipt)),baseline_reused_actual_RTL=True,baseline_recompiled_or_rerun=False,bench_api_derivation=dict(path=rel(API_DERIVATION),sha256=sha(API_DERIVATION)),full_component_bench_compiled_byte_exact_original=False,all_original_functional_oracles_retained=True,source_sha256={rel(p):sha(p)for p in files},source_origins=origins,rtl_source_order=[rel(p)for p in sources],inputs=base['inputs'],replacements=replacements,commands=[],runs=[],transport_runs=[],memory_samples=[],newly_executed_candidate_case_profiles=0,newly_executed_candidate_directed_checks=0,candidate_model_reused=False,canonical_reused_actual_RTL=False,fresh_candidate_model_required=True,full_frame_publication=False,hardware_contact=False,strict_warnings=True,simulation_concurrency='Root exclusively grants two study heavy slots for two independent seeds; first container confirmed running before second launch. No concurrent source edits.',assertions_disabled_or_downgraded=False,old_exact_checker_modified=False,public_cycle_equivalence_claim=True,contract='V120 range prefix plus phase-local full35 admission packet-total equality payload; exact V119 public values/events/cycles, error priority, owners and physical debt. New focused prepared HEADER_CHECK fixtures prime one coherent real predecessor edge in both models; natural packets gain no public edges. All other selected bodies remain V119.',limits=['Actual retained custom packet/parallel DMA source adapter; no QSPI, ESP32 CPU, native Sunshine, C2 seal or publication claim.','Canonical oracle and all original held/error/counter/physical-drain checks retained; V120 public event cycles must match the frozen V119 control.','Registered local command ownership is bounded; complete production PCTL1/session/publication qualification remains separate.'])
 bcontrol=load(B_CANONICAL);broot=(ROOT/bcontrol['selected_receipt']).parent
 r['B_exact_control']=dict(selector=rel(B_CANONICAL),selector_sha256=sha(B_CANONICAL),receipt=rel(broot/'receipt.json'),receipt_sha256=sha(broot/'receipt.json'),scope='V120 targets exact V119 stdout, events and cycles plus independent V113 canonical goldens; all older checkers frozen.')
 started=time.monotonic();worker=threading.local()
 def command(argv,name,cap):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v120-admission-repair-spatial-'+stamp.lower()+'-'+name.split('.')[0]
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  record=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);r['commands'].append(record);began=time.monotonic()
  with(out/name).open('w')as log:
   if argv[0] in (mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/custom_transport'):r['actual_RTL_run']=True;r['simulation_started']=True
   write(out/'receipt.json',r)
   p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
   if getattr(worker,'started',None) is not None:
    for _ in range(30):
     state=subprocess.run(['docker','inspect','--format','{{.State.Running}}',container],capture_output=True,text=True,timeout=5)
     if state.returncode==0 and state.stdout.strip()=='true':record['container_running_confirmed']=True;worker.started.set();break
     if p.poll() is not None:break
     time.sleep(.1)
   while p.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-began,**memory());r['memory_samples'].append(sample);high=high+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);record['resource_stop']=sample;break
    time.sleep(2)
   record.update(exit_code=p.wait(timeout=20),wall_seconds=time.monotonic()-began)
  assert record['exit_code']==0 and 'resource_stop'not in record,name
 def seed_pair(fn):
  def wrapped(ref,event):worker.started=event;return fn(ref)
  def parallel_granted():
   if a.pair_grant_file is None:return False
   if not a.pair_grant_file.is_file():return False
   grant=load(a.pair_grant_file)
   assert grant['owner']=='Root' and grant['grantee']=='v120-admission-repair-spatial' and grant['max_study_heavy_jobs']==2
   assert grant['runner_sha256']==sha(Path(__file__))
   peer=ROOT/grant['completed_peer_receipt']['path'];assert sha(peer)==grant['completed_peer_receipt']['sha256'] and load(peer)['status']=='PASS'
   for name in r['rtl_source_order']:assert load(peer)['source_sha256'][name]==r['source_sha256'][name]
   r['parallel_slot_grant']=dict(path=str(a.pair_grant_file),sha256=sha(a.pair_grant_file),grant=grant)
   return True
  event=threading.Event()
  with ThreadPoolExecutor(max_workers=2)as pool:
   first=pool.submit(wrapped,base['runs'][0],event)
   while True:
    if first.done():
     result=first.result();return [result,fn(base['runs'][1])]
    if event.is_set() and parallel_granted():break
    time.sleep(.1)
   second=pool.submit(wrapped,base['runs'][1],threading.Event())
   return [first.result(),second.result()]
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
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--output-split','10000','--output-split-cfuncs','1000','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','cs88_pipeline_v91k','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror -DELASTIC=1',*compiled,snap(FULL_BENCH)],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'obj/Vcs88_pipeline_v91k')
  def canonical_seed(reference):
   seed=reference['seed'];prefix='candidate-'+str(seed);command([mapped+'/obj/Vcs88_pipeline_v91k',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
   lines=[json.loads(l)for l in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];verdict=[j for j in lines if j.get('type')=='verdict'];assert len(verdict)==1 and verdict[0]['status']=='TEST_PASS'and verdict[0]['cases']==22 and verdict[0]['directed_checks']==21
   # V120 requires exact V119 public scheduling; older checkers stay intact.
   r.setdefault('baseline_schedule_comparisons',[]).append(dict(prefix=prefix,stdout_exact=lines==[json.loads(l)for l in(broot/(prefix+'-simulation.jsonl')).read_text().splitlines()]));assert r['baseline_schedule_comparisons'][-1]['stdout_exact'],'V120 public stdout/cycles changed'
   bc=next(x for x in bcontrol['runs']if x['seed']==seed)
   semantic_events(build/(prefix+'-events.jsonl'),broot/bc['artifacts']['events']['path'],lines,prefix);assert sha(build/(prefix+'-events.jsonl'))==bc['artifacts']['events']['raw_sha256'],'V120 accepted-event bytes/cycles changed'
   path=build/(prefix+'-canonical.tsv');old=reference['artifacts']['canonical_actual'];assert sha(path)==old['raw_sha256'],'canonical accepted pixel bytes differ'
   row=dict(seed=seed,verdict=verdict[0],canonical_exact=True,exact_stdout_events_cycles_and_canonical=True,artifacts=dict(events=pack(build/(prefix+'-events.jsonl')),canonical_actual=pack(path)),case_latency_metrics=[dict(id=x['id'],memory_profile=x['memory_profile'],cycles=x['cycles'],first_input=x['first_input'],last_input=x['last_input'],first_coef=x['first_coef'],last_coef=x['last_coef'],done_cycle=x['done_cycle'],last_residual=x['last_residual'])for x in lines if x.get('type')=='case'])
   return row
  r['runs']=seed_pair(canonical_seed);r['actual_RTL_run']=True;r['newly_executed_candidate_case_profiles']=22*len(r['runs']);r['newly_executed_candidate_directed_checks']=21*len(r['runs'])
  # Actual V97 model is compiled independently; no component hierarchy renaming.
  for p in [HARNESS/'transport.cpp',HARNESS/'admission_monitor.hpp',HARNESS/'bench_transport_base.hpp']:shutil.copyfile(p,build/p.name)
  command(['verilator','--cc','--build','-j','1','--assert','-Wall','--public-flat-rw','--language','1800-2017','--top-module','v97_forward','--Mdir',mapped+'/forward-obj',snap(FORWARD)],'transport-model-compile.log',300)
  assert '%Warning-'not in(out/'transport-model-compile.log').read_text()
  command(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror','-DELASTIC=1','-DVM_SC=0','-DVM_TRACE=0','-DVM_COVERAGE=0','-DVM_TRACE_FST=0','-DVM_TRACE_VCD=0','-I'+mapped+'/obj','-I'+mapped+'/forward-obj','-isystem','/usr/share/verilator/include','-isystem','/usr/share/verilator/include/vltstd',mapped+'/transport.cpp',mapped+'/obj/Vcs88_pipeline_v91k__ALL.a',mapped+'/forward-obj/Vv97_forward__ALL.a',mapped+'/obj/verilated.o',mapped+'/obj/verilated_dpi.o',mapped+'/obj/verilated_threads.o','-pthread','-latomic','-o',mapped+'/custom_transport'],'transport-adapter-compile.log',300)
  r['transport_binary_sha256']=sha(build/'custom_transport')
  def transport_seed(reference):
   seed=reference['seed'];prefix='transport-'+str(seed);command([mapped+'/custom_transport',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv',str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-canonical.tsv'],prefix+'-simulation.jsonl',900)
   lines=[json.loads(l)for l in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];v=[j for j in lines if j.get('type')=='transport_verdict'];assert len(v)==1 and v[0]['status']=='TEST_PASS'and v[0]['successful_case_profiles']==12 and v[0]['abort_reset_retries']==2 and v[0]['public_command_accepts']==16 and v[0]['registered_child_deliveries']==16 and v[0]['poisoned_command_tuples']==16
   r.setdefault('baseline_schedule_comparisons',[]).append(dict(prefix=prefix,stdout_exact=lines==[json.loads(l)for l in(broot/(prefix+'-simulation.jsonl')).read_text().splitlines()]));assert r['baseline_schedule_comparisons'][-1]['stdout_exact'],'V120 public stdout/cycles changed'
   bc=next(x for x in bcontrol['transport_runs']if x['seed']==seed)
   semantic_events(build/(prefix+'-events.jsonl'),broot/bc['artifacts']['events']['path'],lines,prefix);assert sha(build/(prefix+'-events.jsonl'))==bc['artifacts']['events']['raw_sha256'],'V120 accepted-event bytes/cycles changed'
   path=build/(prefix+'-canonical.tsv');assert sha(path)==reference['artifacts']['canonical_actual']['raw_sha256'],'transport canonical accepted pixel bytes differ'
   return dict(seed=seed,verdict=v[0],canonical_exact=True,artifacts=dict(events=pack(build/(prefix+'-events.jsonl')),canonical_actual=pack(path)),fences=[x for x in lines if x.get('type')=='custom_transport'])
  r['transport_runs']=seed_pair(transport_seed)
  r.setdefault('canonical_qualified_case_profiles',r['newly_executed_candidate_case_profiles']);r.setdefault('canonical_qualified_directed_checks',r['newly_executed_candidate_directed_checks'])
  assert r['newly_executed_candidate_case_profiles']==44 and r['newly_executed_candidate_directed_checks']==42
  assert len(r['transport_runs'])==2 and not r['canonical_reused_actual_RTL']
  r['baseline_successful_event_semantics_exact']=True;r['B_all_stdout_records_events_and_cycles_exact']=True;r['V119_stdout_events_cycles_exact']=True
  assert r['source_sha256']=={rel(p):sha(p)for p in files};r['status']='PASS_V120_FINAL_SPATIAL_CANONICAL';r['custom_transport_status']='PASS_ACTUAL_V97_TO_CUSTOM_DECODER_CANONICAL'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  # Preserve failed prefixes as well as final receipts; never replace an attempt.
  for p in build.glob('*'):
   if p.is_file()and p.name.endswith(('-events.jsonl','-canonical.tsv'))and not(out/(p.name+'.gz')).exists():pack(p)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(r,selected_receipt=rel(out/'receipt.json')));print('V120_SPATIAL',r['status'],out,flush=True)
if __name__=='__main__':main()
