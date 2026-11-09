#!/usr/bin/env python3
"""Actual V115 canonical -> finite tagged ACK -> unchanged C2/HUD publication partition."""
import argparse
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

R=Path(__file__).resolve().parents[3]
S=R/'fpga/experiments/cu66-v115-live-parent'
A=R/'experiments/python-gamebub-v115/live-parent'
IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
SELECT=R/'experiments/python-gamebub-v115/spatial/results.json'
SELECT_SHA='52697a476f23ec0c44c17fc80026daeb63755d5481f2c360c8af9b4f557fc907'
RAW_SHA='fb381cd142dfb9c4712bf8dacb280b45555859591af264bde244fa8f4ccff573'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def rel(p):return str(p.relative_to(R))
def write(p,q):p.write_text(json.dumps(q,indent=2,sort_keys=True)+'\n')
def verify():
 assert sha(SELECT)==SELECT_SHA
 q=load(SELECT);raw=R/q['selected_receipt'];assert sha(raw)==RAW_SHA and load(raw)=={k:v for k,v in q.items()if k!='selected_receipt'}
 assert q['status']=='PASS_V115_SPATIAL_CANONICAL'and q['actual_RTL_run']
 for origin in q['source_origins'].values():assert sha(R/origin['path'])==origin['sha256']
 d=load(S/'derivation.json');assert sha(R/d['base']['path'])==d['base']['sha256']and sha(R/d['live_extensions']['path'])==d['live_extensions']['sha256']
 assert sha(R/d['derived']['path'])==d['derived']['sha256']
 text=(R/d['derived']['path']).read_text();assert text.endswith(d['main']);text=text[:-len(d['main'])]
 for e in reversed(d['edits']):assert text.count(e['after'])==e['occurrences'];text=text.replace(e['after'],e['before'],e['occurrences'])
 original=(R/d['base']['path']).read_text().split('int main(')[0];assert text==original and hashlib.sha256(text.encode()).hexdigest()==d['base']['prefix_sha256']
 w=d['wrapper'];assert sha(R/w['original'])==w['original_sha256']and sha(R/w['copy'])==w['sha256'];text=(R/w['copy']).read_text()
 for e in reversed(w['edits']):assert text.count(e['after'])==1;text=text.replace(e['after'],e['before'],1)
 assert text==(R/w['original']).read_text()
 return q,d

def memory():
 m={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines()}
 f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '))
 return dict(available_bytes=m['MemAvailable'],PSI_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');args=ap.parse_args();selected,derivation=verify()
 if not args.run:print('V115_LIVE_PARENT_PREPARED_NOT_RUN',derivation['derived']['sha256']);return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'attempts'/stamp;out.mkdir(parents=True)
 build=Path('/home/lori/gamebub-build/cu66-v69')/('v115-live-parent-'+stamp);build.mkdir();mapped='/build/'+build.name
 endpoints=[R/('fpga/experiments/'+x)for x in ('cu66-v69/hash/cu66_sha256_bytes.sv','cu66-v69/banks/cu66_frame_bank_control.sv','cu66-v91l/cs88_validate_publish_v91l.sv','cu66-v91l-live/cu66_write_hash_join_v91l.sv')]+[S/'cs88_live_v91l.sv']
 sources=[R/x for x in selected['rtl_source_order']]
 inputs=[R/selected['inputs'][n]['source']for n in ('cases.tsv','transform_tiles.tsv','canonical_goldens.tsv')]+[R/'experiments/python-gamebub-v91l/vectors/validation.tsv.gz']
 support=[R/('experiments/cu66-native-v69/'+x)for x in ('hud.hpp','bytes.hpp','generated_constants.hpp')]
 files=sorted(set(sources+endpoints+inputs+support+[S/'tb_keyframe.cpp',S/'derivation.json',R/'scripts/cu66-v115/live-parent/prepare.py',Path(__file__).resolve(),SELECT,R/selected['selected_receipt'],R/derivation['base']['path'],R/derivation['live_extensions']['path'],R/derivation['wrapper']['original']]))
 receipt=dict(schema='v115-keyframe-live-parent-ACK-C2-HUD-publication-v1',status='FAIL',actual_RTL_run=False,simulation_started=False,backend='Verilator',image_id=IMAGE,source_sha256={rel(p):sha(p)for p in files},source_origins=selected['source_origins'],rtl_source_order=selected['rtl_source_order']+[rel(p)for p in endpoints],selected_component=dict(path=rel(SELECT),sha256=sha(SELECT),receipt=selected['selected_receipt'],receipt_sha256=RAW_SHA),source_derivation=dict(path=rel(S/'derivation.json'),sha256=sha(S/'derivation.json')),contract=derivation['contract'],scope=derivation['scope'],commands=[],runs=[],memory_samples=[],assertions_disabled_or_downgraded=False,hardware_contact=False,hardware_30fps=False,complete_validated_decode_under10ms=False,physical_SDRAM=False,ESP32_execution=False,full_RTL_HUD_decoder=False,abstract_publication=True,old_public_cycle_equivalence_claim=False)
 start=time.monotonic()
 def command(argv,log,cap):
  before=memory();assert before['available_bytes']>=8*1024**3 and before['PSI_full_avg10']<1 and before['combined_used_ratio']<.85,before
  container='gamebub-v115-live-parent-'+stamp.lower()+'-'+str(len(receipt['commands']))
  cmd=['docker','run','--rm','--init','--name',container,'--cpus','2','--memory','8g','--memory-swap','8g','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={out},dst={out},readonly','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  row=dict(argv=cmd,log=log,resource_before=before,timeout_seconds=cap);receipt['commands'].append(row);begin=time.monotonic();high=0
  with(out/log).open('w')as stream:
   child=subprocess.Popen(cmd,stdout=stream,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=dict(command=log,elapsed_seconds=time.monotonic()-begin,**memory());receipt['memory_samples'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or high>=2 or sample['combined_used_ratio']>=.9 or sample['elapsed_seconds']>cap+20:
     row['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',container],capture_output=True,timeout=15);break
    time.sleep(2)
   row.update(exit_code=child.wait(timeout=20),wall_seconds=time.monotonic()-begin)
  assert row['exit_code']==0 and'resource_stop'not in row,log
 try:
  for p in files:
   snap=out/'sources'/p.relative_to(R);snap.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,snap)
  expanded=[]
  for p in inputs:
   data=gzip.decompress(p.read_bytes())if p.suffix=='.gz'else p.read_bytes();dest=build/(p.stem if p.suffix=='.gz'else p.name);dest.write_bytes(data);expanded.append(mapped+'/'+dest.name)
   receipt.setdefault('expanded_input_sha256',{})[dest.name]=hashlib.sha256(data).hexdigest()
  # Losslessly split the same unchanged admission source for established compilation.
  packaging=selected['lossless_compile_packaging'];admission=R/selected['source_origins']['fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv']['path'];raw=admission.read_bytes();assert hashlib.sha256(raw).hexdigest()==packaging['production_sha256']
  cuts=[0]+packaging['split_byte_offsets']+[len(raw)]
  for i,f in enumerate(packaging['fragments']):
   data=raw[cuts[i]:cuts[i+1]];assert len(data)==f['bytes']and hashlib.sha256(data).hexdigest()==f['sha256'];(build/f['filename']).write_bytes(data)
  sv=[]
  for p in sources:
   if p.suffix=='.sv':sv.append(mapped+'/'+p.name if p==admission else str(out/'sources'/p.relative_to(R)))
  sv += [mapped+'/'+f['filename']for f in packaging['fragments'][1:]]+[str(out/'sources'/p.relative_to(R))for p in endpoints]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','1000','--language','1800-2017','--top-module','cs88_live_v91l','--Mdir',mapped+'/obj','-I'+str(out/'sources/fpga/experiments/cu66-v69/inverse'),'-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror -DELASTIC=1',*sv,str(out/'sources'/derivation['derived']['path'])],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();receipt['binary_sha256']=sha(build/'obj/Vcs88_live_v91l')
  # Independent vector data for full emitted canonical + accepted/HUD/cache bytes.
  canonical=next(l.split('\t')[2]for l in(build/'canonical_goldens.tsv').read_text().splitlines()if l.startswith('actual_001\t'))
  case=next(l.split('\t')for l in(build/'cases.tsv').read_text().splitlines()if l.startswith('actual_001\t'))
  validation=next(l.split('\t')for l in(build/'validation.tsv').read_text().splitlines()if l.startswith('c0_f0\t'))
  for seed,profile in [(115701,0),(115702,1)]:
   prefix=f'keyframe-{seed}';receipt['actual_RTL_run']=True;receipt['simulation_started']=True;command([mapped+'/obj/Vcs88_live_v91l',*expanded,str(seed),mapped+'/'+prefix+'-events.jsonl',mapped+'/'+prefix+'-actual.tsv',mapped+'/'+prefix+'-hashes.jsonl',str(profile)],prefix+'-simulation.jsonl',900)
   rows=[json.loads(line)for line in(out/(prefix+'-simulation.jsonl')).read_text().splitlines()];verdict=[r for r in rows if r.get('type')=='live_parent_verdict'];live=[r for r in rows if r.get('type')=='live_case']
   assert len(verdict)==len(live)==1 and verdict[0]['status']=='TEST_PASS'and live[0]['status']=='PASS';v=verdict[0]
   assert v['profile']==profile and v['keyframes']==1 and v['candidate_write_requests']==v['candidate_write_acks']==v['hash_deliveries']==560640 and v['hash_jobs']==1025
   assert v['elastic_accepted']==v['elastic_delivered']+v['elastic_discarded'] and v['elastic_discarded']<=1
   assert v['actual_C2_HUD_seal_validation']and v['abstract_publication']
   assert v['observed_wrong_ack_count']==1 and v['directed_checks']==2 and v['wrong_ack_owned_write_drained']and v['clean_retry_without_reset']
   assert live[0]['root']==validation[8]and live[0]['hud_sha256']==validation[7]and live[0]['seal']==validation[9]
   actual=[l.rstrip('\n').split('\t')for l in(build/(prefix+'-actual.tsv')).read_text().splitlines()];assert len(actual)==3
   expected={'actual_001':canonical,'accepted_actual_001':canonical+validation[5],'qcache_actual_001':case[10]}
   assert {r[0]for r in actual}==set(expected)
   for ident,p,data in actual:assert int(p)==profile and data==expected[ident]
   hashes=[json.loads(l)for l in(build/(prefix+'-hashes.jsonl')).read_text().splitlines()];assert len(hashes)==1025
   artifacts={}
   for suffix in ('events.jsonl','actual.tsv','hashes.jsonl'):
    src=build/(prefix+'-'+suffix);data=src.read_bytes();target=out/(src.name+'.gz');target.write_bytes(gzip.compress(data,mtime=0));artifacts[suffix]=dict(path=target.name,sha256=sha(target),raw_sha256=hashlib.sha256(data).hexdigest(),rows=len(data.splitlines()))
   receipt['runs'].append(dict(seed=seed,profile=profile,verdict=v,live_case=live[0],canonical_and_accepted_bytes_exact=True,actual_hash_job_records=1025,artifacts=artifacts))
  assert receipt['source_sha256']=={rel(p):sha(p)for p in files};receipt.update(status='PASS_V115_SELECTED_COMPONENT_ACK_C2_HUD_ABSTRACT_PUBLICATION',actual_RTL_run=True)
 except BaseException as e:receipt['error']=repr(e);raise
 finally:
  # Retain partial evidence on every failure; never promote compile/exit alone.
  for src in sorted(build.glob('keyframe-*')):
   if src.is_file()and src.suffix in ('.jsonl','.tsv'):
    target=out/(src.name+'.gz')
    if not target.exists():target.write_bytes(gzip.compress(src.read_bytes(),mtime=0))
  receipt['wall_seconds']=time.monotonic()-start;receipt['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'receipt.json',receipt);write(A/'results.json',dict(status=receipt['status'],path=rel(out/'receipt.json'),sha256=sha(out/'receipt.json')));print('V115_LIVE_PARENT',receipt['status'],out,flush=True)
if __name__=='__main__':main()
