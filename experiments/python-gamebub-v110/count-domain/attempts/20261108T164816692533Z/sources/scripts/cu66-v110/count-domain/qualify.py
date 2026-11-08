#!/usr/bin/env python3
"""Bounded actual whole-context generic/conditional specialization and whole-ingress qualification."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v110-count-domain';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v110/count-domain';IMAGE='gamebub-cu66-v69-tools:20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):p.write_text(json.dumps(j,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 recipe=json.loads((SRC/'edit-recipe.json').read_text())
 for e in recipe['production'].values():
  old=ROOT/e['original'];new=ROOT/e['candidate'];assert sha(old)==e['original_sha256'] and sha(new)==e['candidate_sha256'];t=old.read_text()
  for x in e['edits']:assert t.count(x['before'])==1;t=t.replace(x['before'],x['after'],1)
  assert t==new.read_text()
  for x in reversed(e['edits']):assert t.count(x['after'])==1;t=t.replace(x['after'],x['before'],1)
  assert t==old.read_text()
  # Every original assertion remains, and the context's complete original assertion tail is byte-exact.
  if old.name=='br88_context.sv':assert old.read_text().split('`ifndef SYNTHESIS',1)[1] in new.read_text()
 a=json.loads((V/'adapters.json').read_text())
 for x in a['adapters']:
  old=ROOT/x['source'];new=ROOT/x['path'];assert sha(old)==x['source_sha256'] and sha(new)==x['sha256'];t=old.read_text()
  for before,after in x['renames']:assert t.count(before)==1;t=t.replace(before,after,1)
  assert t==new.read_text()
 p=ROOT/a['context_probe_original'];assert sha(p)==a['context_probe_original_sha256'];t=p.read_text()
 for before,after in a['context_probe_edits']:assert t.count(before)==1;t=t.replace(before,after,1)
 assert t==(V/'context_probe.sv').read_text()
 p=ROOT/a['context_fixture_original'];assert sha(p)==a['context_fixture_original_sha256'];assert p.read_text().replace('int main(','int inherited_context_main(',1)==(V/'inherited_context.cpp').read_text()
 for n,h in a['whole_ingress_fixture_originals'].items():
  p=ROOT/n;assert sha(p)==h;t=p.read_text()
  for before,after in a['whole_ingress_fixture_edits'][p.name]:assert t.count(before)==1;t=t.replace(before,after,1)
  assert t==(V/p.name).read_text()
 analysis=ROOT/'experiments/python-gamebub-v110/context-validation-analysis.json';p=json.loads((AREA/'preparation.json').read_text());assert sha(analysis)==p['arithmetic_analysis']['sha256']
 return recipe

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('COUNT_DOMAIN_PREPARED_NOT_RUN');return
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v110-count-domain-'+stamp);build.mkdir();mapped='/build/'+build.name
 parser=ROOT/'fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv';cvectors=ROOT/'experiments/python-gamebub-v91b/context-vectors/contexts.jsonl.gz';ivectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
 extra=[ROOT/'fpga/experiments/cu66-v106-context'/n for n in ['tb_context.cpp','context_probe.sv','adapter.json','ports.json']]+[ROOT/'experiments/python-gamebub-v106/context/model.json',ROOT/'experiments/python-gamebub-v106/context/results.json',ROOT/'experiments/python-gamebub-v110/context-validation-analysis.json']
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+[ROOT/e['original']for e in recipe['production'].values()]+[p for p in Path(__file__).parent.glob('*.py')]+[AREA/'preparation.json',parser,cvectors,ivectors]+extra))
 r=dict(schema='v110-count-domain-focused-qualification-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},production=[dict(path=e['candidate'],sha256=e['candidate_sha256'])for e in recipe['production'].values()],replacements=[dict(original=e['original'],candidate=e['candidate'])for e in recipe['production'].values()],commands=[],context_runs=[],capture_runs=[],whole_ingress_runs=[],negative_owner_contract_rejections=[],memory_samples=[],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,scope='Actual selected context old/new defaultFalse unconditional all public/invalid/counters/private geometry, plus enabled specialization under explicit consumed-start ACcount<=unsigned64 blocks*factor precondition; DC and invalid-band/config checks retained. Whole actual REQUEST ingress old/new every public/invalid/debug/counter/memory signal exact without precondition, candidate caller assertion exercised. No full canonical/native/clock/hardware qualification.',specialized_precondition='On consumed start: band0 or band>3 or event_count<=unsigned64(blocks)*(band1?5:band2?15:43). Captured per owner; reset/abort always compared. Only AC count-invalid owner excluded from enabled-context equivalence; generic remains unconditional.',all_private_state_exact_claim=False)
 started=time.monotonic()
 def command(argv,name,cap,negative=False):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate
  container='gamebub-v110-count-domain-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];entry=dict(argv=cmd,resource_before=gate,timeout_seconds=cap);r['commands'].append(entry);began=time.monotonic();stop=None;last=-5;pressure=0
  with (out/name).open('w')as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while proc.poll()is None:
    elapsed=time.monotonic()-began
    if elapsed-last>=5:
     sample=dict(command=name,elapsed_seconds=elapsed,**memory());r['memory_samples'].append(sample);last=elapsed;pressure=pressure+1 if sample['psi_full_avg10']>=5 else 0
     if sample['available_bytes']<4*1024**3 or pressure>=2:stop='HOST_MEMORY_GATE'
    if elapsed>cap+20:stop='HOST_TIMEOUT'
    if stop:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);break
    time.sleep(.5)
   code=proc.wait(timeout=20)
  entry.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);write(out/'progress.json',r)
  if negative:
   t=(out/name).read_text();assert code==134 and not stop and 'stale staging response'in t and 'EXPECTED_ASSERTION_ARMED'in t and '"capture_enable":false'in t,name;entry['status']='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'
  else:assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():shutil.copyfile(p,build/p.name)
  shutil.copyfile(parser,build/'br88_rice_elastic.sv');shutil.copyfile(SRC/'br88_context.sv',build/'br88_context.sv')
  contexts=[json.loads(x)for x in gzip.decompress(cvectors.read_bytes()).splitlines()]
  with(build/'context-vectors.txt').open('w')as f:
   for c in contexts:
    expected=c['expected'];f.write(' '.join(map(str,(c['id'],c['blocks'],c['band'],c['k0'],c['k1'],c['event_count'],c['bit_size'],c['data_hex']or'-',c.get('expected_error',0),len(expected))))+'\n')
    for coef in expected:f.write(' '.join(map(str,coef))+'\n')
  packets=[json.loads(x)for x in gzip.decompress(ivectors.read_bytes()).splitlines()];(build/'packet-vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n'for x in packets))
  command(['verilator','--version'],'version.log',30)
  flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror']
  command([*flags,'--top-module','context_probe','--Mdir',mapped+'/context-obj',*[mapped+'/'+n for n in ['context_original.sv','context_candidate.sv','context_probe.sv','br88_rice_elastic.sv','tb_count_domain.cpp']]],'context-compile.log',600);assert '%Warning-'not in(out/'context-compile.log').read_text()
  r['context_binary_sha256']=sha(build/'context-obj/Vcontext_probe')
  for seed in [111401,111402]:
   name=f'context-{seed}.log';command([mapped+'/context-obj/Vcontext_probe',mapped+'/context-vectors.txt',str(seed),mapped+f'/geometry-{seed}.tsv'],name,240);rows=[json.loads(x)for x in(out/name).read_text().splitlines()];domain=rows[0];geom=rows[1];v=rows[-1]
   assert domain['status']=='TEST_PASS' and domain['cases']==8064 and domain['enabled_cases']>0 and domain['excluded_AC_count_cases']>0
   assert geom['status']=='TEST_PASS' and geom['cases']==4260918 and v['status']=='TEST_PASS' and v['cases']==55 and v['configurations']==8 and v['directed_checks']==172 and v['outputs_per_configuration']==84265
   trace=build/f'geometry-{seed}.tsv';assert sha(trace)=='8254dd9da380dfbffb8446fc8d699e536314572f90c84ba9ef98c5e24353c33d';r['context_runs'].append(dict(domain=domain,geometry=geom,inherited=v,geometry_raw_sha256=sha(trace)))
  command([*flags,'--public-flat-rw','--top-module','ingress_capture_probe','--Mdir',mapped+'/ingress-obj',*[mapped+'/'+n for n in ['ingress_original.sv','ingress_candidate.sv','ingress_capture_probe.sv','br88_context_reference.sv','br88_context.sv','br88_rice_elastic.sv','tb_fetch.cpp']]],'ingress-compile.log',600);assert '%Warning-'not in(out/'ingress-compile.log').read_text();r['ingress_binary_sha256']=sha(build/'ingress-obj/Vingress_capture_probe')
  for seed in [111401,111402]:
   name=f'capture-{seed}.log';command([mapped+'/ingress-obj/Vingress_capture_probe',str(seed),mapped+f'/capture-{seed}.csv'],name,120);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['positive_prepared_cases']==1728 and v['actual_raw_packets']==8 and v['high32_metadata_owners']==128 and v['capture_edge_abort_restarts']==3 and v['held_metadata_edges']==2312;r['capture_runs'].append(v)
  for mode in [1,2]:
   for index in [33,37,41]:
    name=f'negative-{mode}-{index}.log';command([mapped+'/ingress-obj/Vingress_capture_probe','111401',mapped+'/negative.csv',str(mode),str(index)],name,30,True);r['negative_owner_contract_rejections'].append(dict(mode=mode,index=index,status='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'))
  for seed in [111401,111402]:
   name=f'whole-{seed}.log';command([mapped+'/ingress-obj/Vingress_capture_probe',str(seed),mapped+'/unused.csv',mapped+'/packet-vectors.txt'],name,240);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['packets']==76 and v['cancel_retries']==36 and v['prepared_actual_requests']==8 and v['boundary_mask']==15 and all(v['purpose_responses']);r['whole_ingress_runs'].append(v)
  assert r['source_sha256']=={str(p.relative_to(ROOT)):sha(p)for p in files};r.update(status='PASS',actual_RTL_run=True,frozen_after_focused_PASS=True)
 except BaseException as e:r['error']=repr(e);raise
 finally:
  for p in list(build.glob('*.csv'))+list(build.glob('geometry-*.tsv')):
   with p.open('rb')as source,(out/(p.name+'.gz')).open('wb')as dest:
    with gzip.GzipFile(filename='',fileobj=dest,mode='wb',mtime=0)as z:shutil.copyfileobj(source,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('COUNT_DOMAIN_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
