#!/usr/bin/env python3
"""Root-dispatched strict V116B generic scratch and real-caller exact paired proof."""
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v116b-control'
V=S/'verification'
A=R/'experiments/python-gamebub-v116/control-b'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
CFLAGS='-std=c++17 -O2 -Wall -Wextra -Werror'
NATIVE=R/'experiments/python-gamebub-v116/native-study/native/20261109T053733793837Z/receipt.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,q):p.write_text(json.dumps(q,sort_keys=True,indent=2)+'\n')
def rel(p):return str(p.relative_to(R))
def verify():
 q=json.loads((S/'edit-recipes.json').read_text())
 for e in q['recipes']+q['adapters']:
  src=R/e['original'];dst=R/e['candidate']
  assert sha(src)==e['original_sha256'] and sha(dst)==e['candidate_sha256']
  text=src.read_text()
  for x in e['edits']:
   assert text.count(x['before'])==1;text=text.replace(x['before'],x['after'],1)
  assert text==dst.read_text()
  for x in reversed(e['edits']):
   assert text.count(x['after'])==1;text=text.replace(x['after'],x['before'],1)
  assert text==src.read_text()
 import re
 for e in q['recipes']:
  for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(R/e['original']).read_text(),re.S):assert block in(R/e['candidate']).read_text()
 for name in ('tb_scratch.cpp','historical_hazards.cpp','tb_bank.cpp','tb_prepare.cpp'):
  assert(V/name).read_bytes()==(R/'fpga/experiments/cu66-v115-refined-scratch/verification'/name).read_bytes()
 assert ('-'+'Wno-fatal') not in Path(__file__).read_text()
 assert 'pair_enable=0' not in (V/'clock_adapter.hpp').read_text()
 return q

def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()}
 f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');ap.add_argument('--suite',choices=('generic','caller','all'),default='all');args=ap.parse_args();manifest=verify()
 if not args.run:print('V116B_CONTROL_PREPARED_NOT_RUN',json.dumps({Path(e['candidate']).name:e['candidate_sha256']for e in manifest['recipes']}));return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 out=A/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v116b-control-'+stamp);build.mkdir();mapped='/build/'+build.name
 vectors=R/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
 source_contract=json.loads(NATIVE.read_text())['source_contract']
 for e in source_contract['source_origins'].values():assert sha(R/e['path'])==e['sha256']
 production_sources=[R/e['path']for e in source_contract['source_origins'].values()]
 files=sorted(set([p for p in S.rglob('*')if p.is_file()]+list(Path(__file__).parent.glob('*.py'))+[R/e['original']for e in manifest['recipes']+manifest['adapters']]+production_sources+[NATIVE,vectors]))
 result=dict(schema='v116b-generic-foreign-abort-real-caller-exact-pair-v1',status='FAIL',actual_RTL_run=False,backend='Verilator 5.020',image_id=IMAGE,cflags=CFLAGS,suite=args.suite,source_sha256={rel(p):sha(p)for p in files},commands=[],generic_runs=[],caller_runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,original_assertions_retained=True,declared_public_cycle_delta=0,pair_skipped_edges=0,production=manifest['recipes'],scope='Current V115 scratch vs factored generic selected target; old/current selected real caller exact output/counter/raw/memory comparison. No timing or full-parent claim.')
 began=time.monotonic()
 def receipt():write(out/'receipt.json',result)
 def command(argv,name,cap,rtl_run=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v116b-control-'+stamp.lower()+'-'+str(len(result['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,timeout_seconds=cap,resource_before=gate);result['commands'].append(row)
  if rtl_run:result['actual_RTL_run']=True
  receipt();start=time.monotonic();high=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=name,elapsed_seconds=time.monotonic()-start,**memory());result['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-start)
  receipt();assert row['exit_code']==0 and'resource_stop'not in row,name
 try:
  for p in files:
   snap=out/'sources'/p.relative_to(R);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
  for p in production_sources:shutil.copyfile(p,build/p.name)
  for p in (S/'packed_scratch_v91g2.sv',S/'br88_pipeline_v91h.sv'):shutil.copyfile(p,build/p.name)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  # Top wrapper keeps the original class/header name and original port contract.
  shutil.copyfile(V/'br88_pipeline_pair.sv',build/'br88_pipeline_v91h.sv')
  import gzip
  packets=[json.loads(line)for line in gzip.decompress(vectors.read_bytes()).splitlines()]
  expanded=''.join(' '.join(map(str,(c['id'],c['blocks'],c['packet_hex'],c['dense_hex'],c['packed_hex'])))+'\n'for c in packets)
  (build/'packet-vectors.txt').write_text(expanded);(out/'packet-vectors.txt').write_text(expanded)
  result['expanded_input_sha256']=sha(build/'packet-vectors.txt')
  command(['verilator','--version'],'version.log',30);assert 'Verilator 5.020' in(out/'version.log').read_text()
  def compile(top,names):
   command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS',CFLAGS,'--top-module',top,'--Mdir',mapped+'/'+top+'-obj',*[mapped+'/'+n for n in names]],top+'-compile.log',900)
   assert '%Warning-'not in(out/(top+'-compile.log')).read_text()
   result[top+'_binary_sha256']=sha(build/(top+'-obj')/('V'+top))
  if args.suite in ('generic','all'):
   compile('scratch_probe',['observed_original.sv','observed_candidate.sv','scratch_probe.sv','tb_control.cpp'])
   for seed in (116801,116802):
    name=f'generic-{seed}.log';command([mapped+'/scratch_probe-obj/Vscratch_probe',str(seed),mapped+f'/generic-{seed}.jsonl'],name,300,rtl_run=True)
    entries=[json.loads(line)for line in(out/name).read_text().splitlines()if line.startswith('{')];v=entries[-1]
    old=next(x for x in entries if x.get('type')=='v115_scratch_prepare_verdict')
    slot=next(x for x in entries if x.get('type')=='refined_scratch_slot_verdict')
    assert old['status']=='TEST_PASS'and old['full_transactions']==72 and old['corrupt_response_cases']==128 and old['read_owner_cases']==4
    assert old['pending_cancel_cases']==12 and old['stale_pending_abort_checks']==12 and old['complete_retry_transactions']==24 and old['dc_line_boundary_transactions']==48
    assert old['paired_candidate_extra_edges']==3*old['paired_accepted_descriptors'] and old['poisoned_tuples']==old['paired_accepted_descriptors']
    assert slot['status']=='TEST_PASS'and slot['natural_pending_kills']==8 and slot['same_object_full_retries']==8 and slot['private_storage_event_fixtures']==9 and slot['outer_priority_guard_fixtures']==5 and slot['ready_bank_hold_edges']==2
    assert v['status']=='TEST_PASS'and v['prepared_abort_cases']==90 and v['foreign_abort_cases']==36 and v['current_or_reset_cases']==54 and v['unsolicited_response_error_cases']==24 and v['pair_skipped_edges']==0 and v['physical_pending_abort_cases']==4
    result['generic_runs'].append(dict(seed=seed,verdict=v,inherited_prepare=old,inherited_slot=slot));receipt()
  if args.suite in ('caller','all'):
   compile('br88_pipeline_v91h',['br88_rice_elastic.sv','br88_context.sv','br88_packet_ingress.sv','br88_packet_ingress_sync_v91h.sv','br88_packet_ingress_v91h.sv','packed_scratch_reference.sv','packed_scratch_v91g2.sv','br88_pipeline_reference.sv','br88_pipeline_candidate.sv','br88_pipeline_v91h.sv','tb_pipeline.cpp'])
   for seed in (116901,116902):
    name=f'caller-{seed}.log';command([mapped+'/br88_pipeline_v91h-obj/Vbr88_pipeline_v91h',mapped+'/packet-vectors.txt',str(seed),mapped+f'/caller-{seed}.jsonl'],name,600,rtl_run=True)
    entries=[json.loads(line)for line in(out/name).read_text().splitlines()if line.startswith('{')];v=entries[-1]
    assert v['status']=='TEST_PASS'and v['packets']==len(packets) and v['configurations']==2 and v['case_rows']==2*len(packets) and v['directed_checks']>=50 and v['sync_staging_checks']>0 and v['caller_prepare_checks']==18
    result['caller_runs'].append(v);receipt()
  assert result['source_sha256']=={rel(p):sha(p)for p in files};result['status']='PASS'
 except BaseException as exc:result['error']=repr(exc);raise
 finally:
  import gzip
  for src in build.glob('*.jsonl*'):
   if src.is_file():(out/(src.name+'.gz')).write_bytes(gzip.compress(src.read_bytes(),mtime=0))
  result['wall_seconds']=time.monotonic()-began
  result['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'}
  receipt();write(A/'results.json',dict(status=result['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')))
  print('V116B_CONTROL',result['status'],out,flush=True)
if __name__=='__main__':main()
