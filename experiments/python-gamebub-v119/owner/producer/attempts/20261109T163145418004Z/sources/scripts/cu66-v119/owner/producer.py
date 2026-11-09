#!/usr/bin/env python3
"""Strict complete existing-edge ready pair and unchanged independent oracle; --run opts in."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v119-owner';AREA=ROOT/'experiments/python-gamebub-v119/owner/producer';IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
V=SRC/'producer-verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 import re,collections
 recipe=json.loads((SRC/'recipes/producer.json').read_text());old=ROOT/recipe['original'];new=ROOT/recipe['candidate'];assert sha(old)==recipe['original_sha256']and sha(new)==recipe['candidate_sha256'];text=old.read_text()
 for e in recipe['edits']:assert text.count(e['before'])==1;text=text.replace(e['before'],e['after'],1)
 text=text.replace('endmodule\n',recipe['appended_assertions']+'endmodule\n');assert text==new.read_text()
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',old.read_text(),re.S):assert block in text
 for label,source in [('original',old),('candidate',new)]:
  assert source.read_text().replace('module cs88_coefficients_v91k #','module ready_'+label+' #',1)==(V/('ready_'+label+'.sv')).read_text()
 q=json.loads((V/'lineage.json').read_text());assert sha(ROOT/q['old_bench'])==q['old_bench_sha256'];oldbench=(ROOT/q['old_bench']).read_text();newbench=(V/'tb_ready.cpp').read_text();assert oldbench.replace(q['fixture_before'],q['fixture_after'],1)==newbench
 checks=lambda x:collections.Counter(re.findall(r'need\(.*?\);',x,re.S));assert not checks(oldbench)-checks(newbench)
 assert sha(ROOT/q['unchanged_probe']['old'])==sha(ROOT/q['unchanged_probe']['new'])==q['unchanged_probe']['sha256']
 return recipe,[recipe]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args();recipe,entries=verify()
 if not args.run:print('V119_OWNER_PRODUCER_PREPARED_NOT_RUN');return
 assert args.root_grant,'Root grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v119-owner-producer-'+stamp);build.mkdir();mapped='/build/'+build.name
 cardpath=ROOT/'experiments/python-gamebub-v118/integrated-study/native/20261109T151432649740Z/receipt.json';card=json.loads(cardpath.read_text())
 for metadata in card['source_contract']['source_origins'].values():assert sha(ROOT/metadata['path'])==metadata['sha256']
 excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh'}
 children=[ROOT/m['path'] for a,m in card['source_contract']['source_origins'].items()if Path(a).name not in excluded]
 children=[ROOT/'fpga/experiments/cu66-v118-scratch/packed_scratch_v91g2.sv' if p.name=='packed_scratch_v91g2.sv' else p for p in children];assert len(children)==9
 packpath=ROOT/'fpga/experiments/cu66-v116-admission/packaging.json'
 files=sorted(set([p for p in V.iterdir()if p.is_file()]+children+[ROOT/recipe['original'],ROOT/recipe['candidate'],SRC/'recipes/producer.json',ROOT/'fpga/experiments/cu66-v110-ready/verification/tb_ready.cpp',ROOT/'fpga/experiments/cu66-v110-ready/verification/ready_probe.sv',Path(__file__).resolve(),cardpath,packpath]))
 r=dict(schema='v119-owner-producer-existing-edge-operands-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in [recipe]],replacements=[dict(original=e['original'],candidate=e['candidate']) for e in [recipe]],commands=[],runs=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Current V110 producer baseline vs exact nonce/redundant-write cuts with frozen V118 children. Whole original public/private/cache oracles plus independent entropy/nonce reason matrix and full32 random RTL wire checks. Declared prepared predicate contexts; no natural physical frame or native timing claim.')
 started=time.monotonic()
 def command(argv,name,cap,rtl=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v119-owner-producer-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
  e=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(e);began=time.monotonic();stop=None;last=-5;pressure_breaches=0
  if rtl:r['actual_RTL_run']=True
  write(out/'receipt.json',r)
  with (out/name).open('w') as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll() is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed
     pressure_breaches=pressure_breaches+1 if sample['psi_full_avg10']>=5 else 0
     if sample['available_bytes']<4*1024**3 or pressure_breaches>=2 or sample['combined_used_ratio']>=.9:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  e.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  for p in children:shutil.copyfile(p,build/p.name)
  admission=next(p for p in children if p.name=='cs88_admission_v91i2a.sv');pack=json.loads(packpath.read_text());data=admission.read_bytes();assert sha(admission)==pack['production_sha256'];offsets=[0]+pack['split_byte_offsets']+[len(data)];fragments=[]
  for j,m in enumerate(pack['fragments']):
   p=build/m['filename'];p.write_bytes(data[offsets[j]:offsets[j+1]]);assert sha(p)==m['sha256'];fragments.append(p)
  assert b''.join(p.read_bytes()for p in fragments)==data;r['lossless_admission_packaging']=pack
  compiled=[mapped+'/'+p.name for p in children]+[mapped+'/'+p.name for p in fragments[1:]]
  command(['verilator','--version'],'version.log',30)
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror','--top-module','ready_probe','--Mdir',mapped+'/ready-obj',*compiled,*[mapped+'/'+n for n in ('ready_original.sv','ready_candidate.sv','ready_probe.sv','tb_owner.cpp')]],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'ready-obj/Vready_probe')
  for seed in (119101,119102):
   name=f'owner-{seed}.log';command([mapped+'/ready-obj/Vready_probe',str(seed),mapped+f'/{seed}-trace.csv'],name,300,rtl=True)
   rows=[json.loads(line)for line in(out/name).read_text().splitlines()];assert len(rows)==2 and all(x['status']=='TEST_PASS'for x in rows);base,owner=rows;assert base['prepared_counter_cases']==2048 and base['cache_beats']>10000 and base['public_comparisons']>50000;assert owner['type']=='v119_producer_owner'and owner['cases']==9216 and owner['random_cases']==250000
   r['runs'].append(dict(seed=seed,baseline=base,owner=owner))
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('*-trace.csv'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('V119_OWNER_PRODUCER_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
