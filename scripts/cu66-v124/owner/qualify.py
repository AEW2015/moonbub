#!/usr/bin/env python3
"""Strict complete existing-edge ready pair and unchanged independent oracle; --run opts in."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time,sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v124-owner';AREA=ROOT/'experiments/python-gamebub-v124/owner';IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
V=SRC/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines() if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]),combined_used_ratio=(m['MemTotal']-m['MemAvailable']+m['SwapTotal']-m['SwapFree'])/(m['MemTotal']+m['SwapTotal']))
def verify():
 import re,collections,importlib.util
 oldrunner=ROOT/'scripts/cu66-v119/owner/producer.py'
 spec=importlib.util.spec_from_file_location('v119_owner_frozen_baseline',oldrunner);oldmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(oldmod);oldmod.verify()
 q=json.loads((SRC/'edit-recipes.json').read_text());recipe=q['production']
 def reversible(e):
  old=ROOT/e['original'];new=ROOT/e['candidate'];assert sha(old)==e['original_sha256'] and sha(new)==e['candidate_sha256'];text=old.read_text()
  for x in e['edits']:assert text.count(x['before'])==1;text=text.replace(x['before'],x['after'],1)
  assert text==new.read_text()
  for x in reversed(e['edits']):assert text.count(x['after'])==1;text=text.replace(x['after'],x['before'],1)
  assert text==old.read_text()
 reversible(recipe)
 for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',(ROOT/recipe['original']).read_text(),re.S):assert block in(ROOT/recipe['candidate']).read_text()
 for e in q['adapters']+q['fixture_adapters']:reversible(e)
 for e in q['unchanged']:assert sha(ROOT/e['original'])==sha(ROOT/e['candidate'])==e['sha256']
 checks=lambda x:collections.Counter(re.findall(r'(?:need|require_owner)\(.*?\);',x,re.S))
 for e in q['fixture_adapters']:assert not checks((ROOT/e['original']).read_text())-checks((ROOT/e['candidate']).read_text())
 candidate=(ROOT/recipe['candidate']).read_text();assert candidate.count('(* keep = "true" *)')==1 and '(* keep = "true" *) logic [1:0] tile_owner_match;' in candidate
 assert q['added_registers']==q['added_public_cycles']==q['old_assertions_removed']==q['old_require_checks_removed']==0
 assert q['synthesis_attribute']==dict(name='keep',value='true',exact_target='tile_owner_match[1:0]',bit_count=2,other_directives_added=False)
 packaging=json.loads((SRC/'packaging.json').read_text());production=ROOT/recipe['candidate']
 assert packaging['production_sha256']==sha(production) and packaging['fragments']==[dict(filename=production.name,bytes=len(production.read_bytes()),sha256=sha(production))]
 helper=(V/'tb_owner_lanes.cpp').read_text()
 for name in ['tile_owner_match','child_owner_match']:
  assert not re.search(r'NEW\('+name+r'\)\s*=(?!=)',helper) and 'BOTH('+name+',' not in helper
 return recipe,[recipe]

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');ap.add_argument('--root-grant');args=ap.parse_args();recipe,entries=verify()
 if not args.run:print('V124_OWNER_PREPARED_NOT_RUN');return
 assert args.root_grant=='ROOT_V124_OWNER','Exact Root heavy-slot grant required'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v124-owner-lanes-'+stamp);build.mkdir();mapped='/build/'+build.name
 cardpath=ROOT/'experiments/python-gamebub-v123/integration/results.json';card=json.loads(cardpath.read_text())
 for metadata in card['source_origins'].values():assert sha(ROOT/metadata['path'])==metadata['sha256']
 excluded={'cs88_pipeline_v91k.sv','cs88_coefficients_v91k.sv','cu66_inverse_stream_v91j.sv','cu66_reconstruct_stream_v91k.sv','cu66_dequant.sv','cu66_idct8x8.sv','cu66_reconstruct_tile.sv','cu66_coefficient_elastic.sv','cu66_quant_rom.svh'}
 children=[ROOT/m['path'] for a,m in card['source_origins'].items()if Path(a).name not in excluded]
 assert len(children)==9
 packpath=ROOT/'fpga/experiments/cu66-v122-bounds/packaging.json'
 vectors=ROOT/'experiments/python-gamebub-v91i2/vectors/cases.tsv';policy=ROOT/'experiments/python-gamebub-v124/study-policy.json'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+children+[ROOT/recipe['original'],ROOT/recipe['candidate'],ROOT/'scripts/cu66-v124/owner/prepare.py',ROOT/'scripts/cu66-v119/owner/producer.py',ROOT/'fpga/experiments/cu66-v119-owner/recipes/producer.json',*list((ROOT/'fpga/experiments/cu66-v119-owner/producer-verification').glob('*')),ROOT/'fpga/experiments/cu66-v91i2b/tb_pipeline.cpp',ROOT/'docs/cu66-v124/owner-design.md',Path(__file__).resolve(),cardpath,packpath,vectors,policy]))
 r=dict(schema='v124-owner-lanes-existing-edge-operands-focused-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256']) for e in [recipe]],replacements=[dict(original=e['original'],candidate=e['candidate']) for e in [recipe]],commands=[],runs=[],caller_runs=[],memory_samples=[],root_grant=args.root_grant,study_policy=dict(path=str(policy.relative_to(ROOT)),sha256=sha(policy)),source_origins=card['source_origins'],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Selected V123 producer vs spatial full32/full16 owner lanes. All original V119 cache/nonce checks retained plus raw-bank generic wire/clock/response contexts and actual V91i2b packet/controller pairs. Prepared domains explicitly labelled; no native timing/hardware claim.')
 started=time.monotonic()
 def command(argv,name,cap,rtl=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1 and gate['combined_used_ratio']<.85,gate
  container='gamebub-v124-owner-lanes-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv]
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
  shutil.copyfile(vectors,build/'cases.tsv')
  admission=next(p for p in children if p.name=='cs88_admission_v91i2a.sv');pack=json.loads(packpath.read_text());data=admission.read_bytes();assert sha(admission)==pack['production_sha256'];offsets=[0]+pack['split_byte_offsets']+[len(data)];fragments=[]
  for j,m in enumerate(pack['fragments']):
   p=build/m['filename'];p.write_bytes(data[offsets[j]:offsets[j+1]]);assert sha(p)==m['sha256'];fragments.append(p)
  assert b''.join(p.read_bytes()for p in fragments)==data;r['lossless_admission_packaging']=pack
  compiled=[mapped+'/'+p.name for p in children]+[mapped+'/'+p.name for p in fragments[1:]]
  command(['verilator','--version'],'version.log',30)
  assert 'Verilator 5.020' in(out/'version.log').read_text()
  command(['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--public-flat-rw','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-I'+mapped,'-CFLAGS','-std=c++17 -O2 -Wall -Wextra -Werror','--top-module','ready_probe','--Mdir',mapped+'/ready-obj',*compiled,*[mapped+'/'+n for n in ('ready_original.sv','ready_candidate.sv','ready_probe.sv','tb_owner_lanes.cpp')]],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();r['binary_sha256']=sha(build/'ready-obj/Vready_probe')
  r['compiled_source_sha256']={p.name:sha(p)for p in build.iterdir()if p.is_file()}
  for seed in (124101,124102):
   name=f'owner-{seed}.log';command([mapped+'/ready-obj/Vready_probe','generic',str(seed),mapped+'/cases.tsv',mapped+f'/{seed}-trace.csv'],name,600,rtl=True)
   rows=[json.loads(line)for line in(out/name).read_text().splitlines()];assert len(rows)==3 and all(x['status']=='TEST_PASS'for x in rows);base,owner,lanes=rows;
   assert lanes['type']=='v124_owner_lanes_verdict' and lanes['wire_cases']==466944 and lanes['random_fullwidth_cases']==65536 and lanes['state_cases']==8192
   assert lanes['mode_mask']==lanes['bank_ready_mask']==lanes['guard_mask']==15 and lanes['emit_mask']==3 and lanes['invalid_ready_true']>0 and lanes['unready_ready_true']>0
   assert lanes['clock_cases']==1152 and lanes['error67_cases']==192 and lanes['cancel_cases']==864 and lanes['wrap_cases']==16 and lanes['held_edges']==336 and lanes['response_contexts']==224
   assert lanes['added_public_cycles']==lanes['error_cycle_delta']==lanes['pair_skipped_edges']==lanes['old_checks_removed']==0 and lanes['prepared_domain_fixtures_are_natural_packets'] is False
   assert base['prepared_counter_cases']==2048 and base['cache_beats']>10000 and base['public_comparisons']>50000;assert owner['type']=='v119_producer_owner'and owner['cases']==9216 and owner['random_cases']==250000
   r['runs'].append(dict(seed=seed,baseline=base,owner=owner,lanes=lanes));write(out/'receipt.json',r)
  for seed in (124201,124202):
   name=f'caller-{seed}.log';command([mapped+'/ready-obj/Vready_probe','caller',str(seed),mapped+'/cases.tsv',mapped+f'/{seed}-trace.csv'],name,900,rtl=True)
   rows=[json.loads(line)for line in(out/name).read_text().splitlines()];verdict=rows[-1]
   assert verdict['type']=='verdict' and verdict['status']=='TEST_PASS' and verdict['vectors']==11 and verdict['cases']==22 and verdict['configurations']==2 and verdict['directed_checks']>=12
   assert verdict['dense_comparisons']>0 and verdict['directed_dense_comparisons']>0
   cases=[x for x in rows if x.get('type')=='case'];assert len(cases)==22 and all(x['status']=='PASS' and not x['pending_drain'] and x['requests']==x['acks'] for x in cases)
   r['caller_runs'].append(dict(seed=seed,verdict=verdict,case_rows=len(cases)));write(out/'receipt.json',r)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p) for p in files};r.update(status='PASS',frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in build.glob('*-trace.csv'):
   with p.open('rb') as source,(out/(p.name+'.gz')).open('wb') as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0) as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()and p.name!='receipt.json'};write(out/'receipt.json',r);write(AREA/'results.json',dict(status=r['status'],actual_RTL_run=r['actual_RTL_run'],path=str((out/'receipt.json').relative_to(ROOT)),sha256=sha(out/'receipt.json')));print('V124_OWNER_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
