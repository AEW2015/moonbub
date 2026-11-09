#!/usr/bin/env python3
"""Root-dispatched combined range/phase-payload proposal with explicit private-transition oracles."""
import argparse,datetime,gzip,hashlib,json,re,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];S=R/'fpga/experiments/cu66-v120-control-proposal';V=S/'verification';A=R/'experiments/python-gamebub-v120/control-proposal'
BASE_SELECTOR=R/'experiments/python-gamebub-v120/range/results.json'
POLICY=R/'experiments/python-gamebub-v120/study-policy.json'
NATIVE=R/'experiments/python-gamebub-v119/integrated-study/native/20261109T171305710307Z/receipt.json'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def verify():
 q=load(S/'combined/edit-recipes.json')
 for e in q['production']+q['adapters']:
  p,c=R/e['original'],R/e['candidate'];assert sha(p)==e['original_sha256']and sha(c)==e['candidate_sha256'];t=p.read_text()
  for x in e['edits']:assert t.count(x['before'])==1;t=t.replace(x['before'],x['after'],1)
  assert t==c.read_text()
  for x in reversed(e['edits']):assert t.count(x['after'])==1;t=t.replace(x['after'],x['before'],1)
  assert t==p.read_text()
 for e in q['production']:
  for b in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(R/e['original']).read_text(),re.S):assert b in(R/e['candidate']).read_text()
 for group in ('unchanged_verification',):
  for old,h in q[group].items():assert sha(R/old)==h and(V/Path(old).name).read_bytes()==(R/old).read_bytes()
 assert q['declared_public_cycle_delta']==0
 assert q['candidate_private_comparison_edits']==1 and q['changed_private_fields']==['prepared_request_addr','prepared_request_in_bounds']
 assert q['candidate_all_private_equivalence_claim'] is False
 assert ('-'+'Wno-fatal')not in Path(__file__).read_text()
 actual=load(NATIVE);assert actual['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'and actual['result']['timing']['WNS_ns']==-2.105 and actual['start_mode']=='rtl'
 baseline=load(BASE_SELECTOR);assert baseline['status']=='PASS'and baseline['actual_RTL_run'] is True
 bp=R/baseline['path'];assert sha(bp)==baseline['sha256'];b=load(bp);assert b['status']=='PASS'and b['actual_RTL_run'] is True
 assert b['source_sha256'][q['production'][0]['original']]==q['production'][0]['original_sha256']
 assert b['old_exact_checker_modified'] is False and b['candidate_model_reused'] is False
 assert b['source_sha256'][q['combined_range_source']['path']]==q['combined_range_source']['sha256']
 for n,h in b['source_sha256'].items():assert sha(R/n)==h,n
 for n,h in b['artifact_sha256'].items():assert sha(bp.parent/n)==h,n
 return q,actual

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');ap.add_argument('--routed-cause',type=Path,default=NATIVE);ap.add_argument('--suite',choices=('ingress','caller','all'),default='all');args=ap.parse_args();manifest,native=verify();cause=args.routed_cause.resolve();cause.relative_to(R);cause_record=load(cause);assert cause_record['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and cause_record['clock_period_ns']==8.0
 if not args.run:print('V120_CONTROL_PREPARED_NOT_RUN',manifest['production'][0]['candidate_sha256']);return
 assert args.root_grant,'Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v120-control-'+stamp);build.mkdir();mapped='/build/'+build.name
 vectors=R/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz';prod=[R/x['path']for x in native['source_contract']['source_origins'].values()]
 for x in native['source_contract']['source_origins'].values():assert sha(R/x['path'])==x['sha256']
 original=[R/e['original']for e in manifest['production']+manifest['adapters']]
 for group in ('unchanged_verification',):original +=[R/n for n in manifest[group]]
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+original+prod+[vectors,POLICY,NATIVE,NATIVE.parent/'reports/route-setup-paths.rpt',R/'docs/cu66-v120/control-owner.md',cause,cause.parent/'reports/route-setup-paths.rpt',BASE_SELECTOR,R/load(BASE_SELECTOR)['path']]))
 result=dict(schema='v120-combined-range-phase-payload-focus-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,cflags=CFLAGS,root_grant=args.root_grant,suite=args.suite,source_sha256={rel(p):sha(p)for p in files},commands=[],ingress_runs=[],caller_runs=[],range_runs=[],memory_samples=[],production=manifest['production'],assertions_disabled_or_downgraded=False,original_assertions_retained=True,old_exact_checker_modified=True,candidate_private_comparison_edits=1,changed_private_fields=['prepared_request_addr','prepared_request_in_bounds'],all_private_equivalence_claim=False,original_public_pair_checks_unchanged=True,old_private_equality_retained_in_control_proof=True,declared_public_cycle_delta=0,pair_skipped_edges=0,actual_routed_cause=dict(path=rel(cause),sha256=sha(cause)),baseline_extent_proof=dict(selector=rel(BASE_SELECTOR),selector_sha256=sha(BASE_SELECTOR),receipt=load(BASE_SELECTOR)['path'],receipt_sha256=load(BASE_SELECTOR)['sha256']),study_policy=dict(path=rel(POLICY),sha256=sha(POLICY)),scope='Exact V119 public/state/error/cursor/descriptor/physical-debt and owned-request contract against range prefix plus phase-local preparation. ONE two-field unowned-private equality comparison is explicitly replaced by complete every-edge independent old/new writer transition scoreboards. The unchanged equality remains in the frozen A proof. All other old oracles retained. Each seed retains A65536/36/27/67 coverage plus48 real initial/request/response cancellations,32 real context-error packets and80 nonreset retries. No all-private equivalence, route/parent/hardware claim.', caller_reference_uses_current_V119_sources=True, fresh_candidate_model_required=True, candidate_model_reused=False)
 began=time.monotonic()
 def persist():write(out/'receipt.json',result)
 def command(argv,name,cap,rtl=False):
  active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(n.startswith('gamebub-v') for n in active)<2,active
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v120-control-'+stamp.lower()+'-'+str(len(result['commands']))
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
  shutil.copyfile(S/'combined/br88_packet_ingress_sync_v91h.sv',build/'br88_packet_ingress_sync_v91h.sv')
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
   compile('ingress_probe',['ingress_probe.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_context.sv','br88_rice_elastic.sv','tb_control.cpp'])
   for seed in (117901,117902):
    name=f'ingress-{seed}.log';command([mapped+'/ingress_probe-obj/Vingress_probe',str(seed),mapped+'/packet-vectors.txt'],name,600,rtl=True)
    rows=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')];old=next(x for x in rows if x.get('type')=='ingress_verdict');v=next(x for x in rows if x.get('type')=='v117_ingress_extent_verdict');bytecount=next(x for x in rows if x.get('type')=='v117_ingress_bytecount_verdict');range_row=next(x for x in rows if x.get('type')=='v120_raw_range_verdict');control_row=rows[-1]
    assert old['status']=='TEST_PASS'and old['corpus_profiles']==160 and old['initial_cancel_retries']==54 and old['initial_successful_packets']==218
    assert old['refined_cancel_checks']==30 and old['refined_length_checks']==11 and old['cancel_retries']==84 and old['successful_packets']==259
    assert old['new_descriptor_cancel_checks']==old['new_context_cancel_checks']==old['word_tuple_cancel_checks']==6 and old['malformed_checks']==4
    assert old['public_cycle_pair_checks']==old['clock_edges']and old['requests']==old['responses']+old['canceled_read_owners']
    assert v['status']=='TEST_PASS'and v['type']=='v117_ingress_extent_verdict'and v['initial_cases']==6272 and v['ready_cases']==21860 and v['cancellation_cases']==v['prepared_retries']==56 and v['pair_skipped_edges']==0
    assert bytecount['status']=='TEST_PASS'and bytecount['type']=='v117_ingress_bytecount_verdict'and bytecount['extra_ready_cases']==1920 and bytecount['zero_L_nonzero_remainder_cases']==168 and bytecount['max_u_cases']==320 and bytecount['high_expected_byte_cases']==960 and bytecount['pair_skipped_edges']==0
    assert range_row['status']=='TEST_PASS' and range_row['type']=='v120_raw_range_verdict'
    assert range_row['prepared_predicate_contexts']==65536 and range_row['predicate_accepts']==4097 and range_row['predicate_rejects']==61439 and range_row['predicate_edges']==65537
    assert range_row['natural_boundary_packets']==36 and range_row['natural_valid']==20 and range_row['natural_error5']==16 and range_row['natural_prepared_cancels']==27 and range_row['natural_retries']==67 and range_row['held_output_edges']==364
    assert range_row['crc_priority']==range_row['header_priority']==2 and range_row['requests']==range_row['responses']+range_row['canceled_read_owners'] and range_row['public_cycle_delta']==range_row['pair_skipped_edges']==0
    assert control_row['type']=='v120_phase_payload_verdict' and control_row['status']=='TEST_PASS'
    assert control_row['initial_call_cancels']==control_row['first_request_response_cancels']==24 and control_row['natural_context_error_cases']==32 and control_row['nonreset_retries']==80
    assert control_row['candidate_private_comparison_edits']==1 and control_row['changed_private_fields']==2 and control_row['public_cycle_delta']==control_row['pair_skipped_edges']==0
    assert control_row['prepared_unowned_full32_cases']==11424
    assert control_row['requests']==control_row['responses']+control_row['canceled_read_owners']
    assert all(control_row[k]>0 for k in ['writer_edges','unowned_speculation_edges','exact_owned_request_tuples','reset_speculation_edges','start_speculation_edges','abort_speculation_edges','bad_descriptor_speculation_edges','context_fault_speculation_edges','context_done_speculation_edges','held_replay_speculation_edges','independent_cache_captures','owned_cache_wait_checks','initial_header_calls','initial_descriptor_calls','initial_replay_calls','initial_raw_calls'])
    result['ingress_runs'].append(dict(seed=seed,inherited=old,extent=v,bytecount=bytecount));result['range_runs'].append(dict(seed=seed,**range_row));result.setdefault('control_runs',[]).append(dict(seed=seed,**control_row));persist()
  if args.suite in ('caller','all'):
   compile('br88_pipeline_v91h',['br88_rice_elastic.sv','br88_context.sv','br88_packet_ingress.sv','br88_packet_ingress_sync_v91h_reference.sv','br88_packet_ingress_sync_v91h.sv','br88_packet_ingress_v91h_reference.sv','br88_packet_ingress_v91h.sv','packed_scratch_reference.sv','packed_scratch_v91g2.sv','br88_pipeline_reference.sv','br88_pipeline_candidate.sv','br88_pipeline_v91h.sv','tb_pipeline.cpp'])
   for seed in (118001,118002):
    name=f'caller-{seed}.log';command([mapped+'/br88_pipeline_v91h-obj/Vbr88_pipeline_v91h',mapped+'/packet-vectors.txt',str(seed),mapped+f'/caller-{seed}.jsonl'],name,600,rtl=True)
    rows=[json.loads(x)for x in(out/name).read_text().splitlines()if x.startswith('{')];v=rows[-1]
    assert v['status']=='TEST_PASS'and v['packets']==len(cases)and v['configurations']==2 and v['case_rows']==2*len(cases)and v['directed_checks']>=50 and v['sync_staging_checks']>0 and v['caller_prepare_checks']==18
    result['caller_runs'].append(v);persist()
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS' if args.suite=='all' else 'PASS_PARTIAL_'+args.suite.upper()
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  for p in build.glob('*.jsonl*'):
   if p.is_file():(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  result['wall_seconds']=time.monotonic()-began;result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};persist();write(A/('results.json' if args.suite=='all' else 'results-'+args.suite+'.json'),dict(status=result['status'],actual_RTL_run=result['actual_RTL_run'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V120_CONTROL',result['status'],out,flush=True)
if __name__=='__main__':main()
