#!/usr/bin/env python3
"""Strict bounded V128 source-extracted padding proof; no run without Root grant."""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'fpga/experiments/cu66-v128-padding'
V=SRC/'verification'
AREA=ROOT/'experiments/python-gamebub-v128/padding'
BUILD=Path('/home/lori/gamebub-build/cu66-v69')
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
SEEDS=(128701,128702)
GIB=1024**3

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).resolve().relative_to(ROOT))
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def memory():
 m={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()}
 pressure=next(s for s in Path('/proc/pressure/memory').read_text().splitlines() if s.startswith('full '))
 return {'available_bytes':m['MemAvailable'],'psi_full_avg10':float(pressure.split('avg10=')[1].split()[0]),'combined_used_ratio':(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal'])}

def verify():
 rec=json.loads((SRC/'edit-recipe.json').read_text());orig=ROOT/rec['original']['path'];candidate=ROOT/rec['candidate']['path']
 assert sha(orig)==rec['original']['sha256'] and sha(candidate)==rec['candidate']['sha256']
 text=orig.read_text()
 for e in rec['edits']:assert text.count(e['old'])==1;text=text.replace(e['old'],e['new'])
 assert text==candidate.read_text()
 for e in reversed(rec['edits']):assert text.count(e['new'])==1;text=text.replace(e['new'],e['old'])
 assert text==orig.read_text()
 assert rec['source_payload_bits_added']==1 and rec['source_payload_reset_added'] is False
 assert rec['added_public_cycles']==rec['added_synthesis_attributes']==0 and rec['old_guarded_blocks_retained']==16
 assert all(block in candidate.read_text() for block in re.findall(r'`ifndef SYNTHESIS\n.*?`endif',orig.read_text(),re.S))
 pkg=json.loads((SRC/'packaging.json').read_text());assert pkg['production_sha256']==sha(candidate) and pkg['split_byte_offsets']==[] and len(pkg['fragments'])==1 and pkg['module_count']==3
 assert pkg['fragments'][0]=={'bytes':candidate.stat().st_size,'filename':candidate.name,'sha256':sha(candidate)}
 preparer=ROOT/'scripts/cu66-v128/padding/prepare_verification.py';spec=importlib.util.spec_from_file_location('v128_padding_extraction',preparer);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 modules,fragments=mod.build_files();assert all((V/name).read_text()==text for name,text in modules.items())
 vrec=json.loads((SRC/'verification-recipe.json').read_text());assert vrec['source_fragments']==fragments and vrec['private_new_payload_or_owner_forces']==0
 for key in ('preparer','original','candidate','target','bench'):assert sha(ROOT/vrec[key]['path'])==vrec[key]['sha256']
 assert vrec['kernel_modules']==[{'path':rel(V/name),'sha256':sha(V/name)} for name in modules]
 assert vrec['kernel_bundle_sha256']==hashlib.sha256(''.join(modules.values()).encode()).hexdigest()
 assert vrec['seeds']==list(SEEDS) and vrec['scoped_source_kernel'] and not vrec['full_admission_model'] and not vrec['actual_FSM_executed']
 cpp=(V/'tb_padding.cpp').read_text()
 for token in ('new_cache','new_owner_complete'):assert not re.search(r'\.'+token+r'\s*=(?!=)',cpp)
 return [orig,candidate,SRC/'edit-recipe.json',SRC/'source-map.json',SRC/'packaging.json',SRC/'verification-recipe.json',*[V/name for name in modules],V/'tb_padding.cpp',Path(__file__),ROOT/'scripts/cu66-v128/padding/prepare.py',preparer]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');a=ap.parse_args()
 inputs=verify()
 if not a.run:print('PASS_READONLY_PADDING_RECONSTRUCTION_NOT_RUN',len(inputs));return
 assert a.root_grant=='ROOT_V128_PADDING','Exact Root heavy-job grant required'
 assert memory()['available_bytes']>=8*GIB and memory()['psi_full_avg10']<1 and memory()['combined_used_ratio']<.85
 active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines();assert sum(bool(re.match(r'^gamebub-v\d+-',x)) for x in active)<2
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');attempt=AREA/'attempts'/stamp;attempt.mkdir(parents=True);build=BUILD/('v128-padding-'+stamp);build.mkdir();mapped=Path('/build')/build.name
 rec={'schema':'v128-owned-header-padding-focused-v1','status':'RUNNING','actual_RTL_run':False,'source_kernel':True,'actual_full_admission_FSM':False,'seeds':list(SEEDS),'declared_public_cycle_delta':0,'source_payload_bits_added':1,'original_guards_retained':True,'new_payload_or_owner_forces':0,'commands':[],'runs':[],'source_sha256':{rel(p):sha(p) for p in inputs},'image_id':IMAGE,'resource_policy':{'cpus':2,'memory_bytes':8*GIB,'memory_swap_bytes':8*GIB,'compile_jobs':1,'pids':2048,'max_heavy_jobs':2},'strict_warnings':True,'hardware_contact':False,'memory_samples':[]}
 for p in inputs:
  target=attempt/'sources'/rel(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 write(attempt/'receipt.json',rec)
 started=time.monotonic();print('V128_PADDING_STARTED',rel(attempt),flush=True)
 def command(tail,tag,timeout,cwd=None):
  m=memory();assert m['available_bytes']>=8*GIB and m['psi_full_avg10']<1 and m['combined_used_ratio']<.85
  name='gamebub-v128-padding-'+stamp.lower()+'-'+tag
  cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={attempt},dst={attempt},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',str(cwd or mapped),IMAGE,'timeout','--kill-after=5s',str(timeout)+'s']+list(map(str,tail))
  record={'argv':cmd,'timeout_seconds':timeout,'resource_before':m};rec['commands'].append(record);write(attempt/'receipt.json',rec)
  t=time.monotonic();last=-15;high=0;reason=None
  with (attempt/(tag+'.log')).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    age=time.monotonic()-t
    if age-last>=15:
     sample={'command':tag,'elapsed_seconds':age,**memory()};rec['memory_samples'].append(sample);last=age;high=high+1 if sample['psi_full_avg10']>=5 else 0
     if sample['available_bytes']<4*GIB or high>=2 or sample['combined_used_ratio']>=.90:reason='HOST_MEMORY_PRESSURE'
    if age>timeout+30:reason='HOST_TIMEOUT'
    if reason:subprocess.run(['docker','stop','--time','10',name],capture_output=True,timeout=20);break
    time.sleep(1)
   code=proc.wait(timeout=30)
  record.update(exit_code=code,wall_seconds=time.monotonic()-t,stop_reason=reason);write(attempt/'receipt.json',rec)
  assert code==0 and reason is None,(tag,code,reason)
  return (attempt/(tag+'.log')).read_text(errors='replace')
 try:
  version=command(['verilator','--version'],'version',30);assert 'Verilator 5.020' in version;rec['backend']='standalone Verilator 5.020'
  kernels=[attempt/'sources'/rel(V/name) for name in ('padding_original_kernel.sv','padding_candidate_kernel.sv','padding_probe.sv')];cpp=attempt/'sources'/rel(V/'tb_padding.cpp')
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--language','1800-2017','--top-module','padding_probe','--Mdir',mapped/'obj','-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror',*kernels,cpp],'compile',300)
  binary=build/'obj/Vpadding_probe';assert binary.is_file();rec['binary_sha256']=sha(binary);rec['simulation_started']=True
  for seed in SEEDS:
   sub=build/str(seed);sub.mkdir();rec['actual_RTL_run']=True
   stdout=command([mapped/'obj/Vpadding_probe',seed],f'seed-{seed}',300,mapped/str(seed));rows=[json.loads(s) for s in stdout.splitlines() if s.startswith('{')]
   assert len(rows)==1 and rows[0]['type']=='v128_padding_clock_verdict';v=rows[0]
   assert v['status']=='TEST_PASS' and v['seed']==seed
   exact={'exhaustive_single_byte_cases':3072,'random_header_cases':4096,'cancel_prefix_cases':84,'incomplete_prefix_checks':12,'nonwriter_hold_checks':558,'nonpadding_writer_hold_checks':6,'last_byte_forwarding_cases':2,'unowned_canceled_payload_changes':84,'completed_headers':7268,'public_cycle_delta':0,'new_payload_or_owner_forces':0}
   assert all(v[k]==val for k,val in exact.items()),(seed,v)
   assert v['equality_evaluations']==3*v['clock_edges']==v['view_checks'] and v['payload_captures']>12*v['completed_headers']
   assert v['source_kernel'] is True and v['actual_full_admission_FSM'] is False and all(v['error_classes'][e]>0 for e in (0,4,5,6,7,8))
   trace=sub/'padding-cases.jsonl';trace_rows=[json.loads(s) for s in trace.read_text().splitlines()];assert len(trace_rows)==7268 and all(row['case']==i+1 for i,row in enumerate(trace_rows))
   gz=attempt/f'seed-{seed}-cases.jsonl.gz';gz.write_bytes(gzip.compress(trace.read_bytes(),mtime=0))
   rec['runs'].append({'seed':seed,'verdict':v,'trace_rows':len(trace_rows),'raw_trace_sha256':sha(trace),'retained_trace':gz.name});write(attempt/'receipt.json',rec)
  rec['status']='PASS'
 except Exception as e:
  rec['status']='FAIL';rec['error']=str(e)
 rec['wall_seconds']=time.monotonic()-started
 rec['source_snapshot_unchanged']=all(sha(ROOT/p)==h and sha(attempt/'sources'/p)==h for p,h in rec['source_sha256'].items())
 if not rec['source_snapshot_unchanged']:rec['status']='FAIL';rec['error']='Source or snapshot changed'
 rec['artifacts_sha256']={str(p.relative_to(attempt)):sha(p) for p in sorted(attempt.rglob('*')) if p.is_file() and p.name!='receipt.json'}
 write(attempt/'receipt.json',rec)
 if rec['status']=='PASS':
  AREA.mkdir(exist_ok=True);write(AREA/'results.json',{'schema':rec['schema'],'status':'PASS','actual_RTL_run':True,'path':rel(attempt/'receipt.json'),'sha256':sha(attempt/'receipt.json'),'source_kernel':True,'actual_full_admission_FSM':False})
 print('V128_PADDING_FINISHED',rec['status'],rel(attempt/'receipt.json'),sha(attempt/'receipt.json'),flush=True)
 if rec['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
