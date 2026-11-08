#!/usr/bin/env python3
"""Bounded strict actual old/new ingress qualification of V111 header preparation."""
import argparse,datetime,gzip,hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v111-header';V=SRC/'verification';AREA=ROOT/'experiments/python-gamebub-v111/header';IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def verify():
 e=json.loads((SRC/'edit-recipe.json').read_text());old=ROOT/e['original'];new=ROOT/e['candidate'];assert sha(old)==e['original_sha256'] and sha(new)==e['candidate_sha256'];s=old.read_text()
 for x in e['edits']:assert s.count(x['before'])==1;s=s.replace(x['before'],x['after'],1)
 assert s==new.read_text()
 for x in reversed(e['edits']):assert s.count(x['after'])==1;s=s.replace(x['after'],x['before'],1)
 assert s==old.read_text()
 for tail in old.read_text().split('`ifndef SYNTHESIS')[1:]:
  for line in tail.splitlines():
   if 'assert' in line:assert line in new.read_text()
 a=json.loads((V/'adapters.json').read_text())
 for x in a['adapters']:
  p=ROOT/x['source'];q=ROOT/x['path'];assert sha(p)==x['source_sha256'] and sha(q)==x['sha256'];s=p.read_text()
  for b,c in x['edits']:assert s.count(b)==1;s=s.replace(b,c,1)
  assert s==q.read_text()
 return e

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',action='store_true');args=ap.parse_args();recipe=verify()
 if not args.run:print('HEADER_PREPARED_NOT_RUN');return
 image=json.loads(subprocess.check_output(['docker','image','inspect',IMAGE],text=True))[0];assert image['Id']==IMAGE
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=AREA/'attempts'/stamp;out.mkdir(parents=True);build=Path('/home/lori/gamebub-build/cu66-v69')/('v111-header-'+stamp);build.mkdir();mapped='/build/'+build.name
 parser=ROOT/'fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv';context=ROOT/'fpga/experiments/cu66-v110-count-domain/br88_context.sv';vectors=ROOT/'experiments/python-gamebub-v91e/vectors/coefficients.jsonl.gz'
 files=sorted(set([p for p in SRC.rglob('*')if p.is_file()]+[ROOT/recipe['original'],parser,context,vectors,Path(__file__).resolve(),Path(__file__).with_name('prepare.py'),AREA/'preparation.json']))
 r=dict(schema='v111-header-focused-qualification-v1',status='FAIL',actual_RTL_run=False,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in files},replacements=[dict(original=recipe['original'],candidate=recipe['candidate'])],commands=[],capture_runs=[],whole_ingress_runs=[],header_runs=[],negative_owner_contract_rejections=[],memory_samples=[],seeds=[111501,111502],strict_warnings=True,warning_suppression=False,assertions_disabled_or_downgraded=False,added_public_cycles=0,all_private_state_exact_claim=False,hardware_contact=False,native_implementation=False,scope='Actual old Count ingress vs three-stage header candidate, same enabled Count context and prefix Rice; every original public invalid/error/counter/debug/memory signal exact. New private pipeline carries arbitrary data outside consumed HEADER. Existing packet/assertion/golden fixtures unchanged except explicit reversible module/entry binding. Synthetic arithmetic header fixtures have three preceding real stable preparation edges, without injecting candidate private registers.',tool_image=dict(content_id=image['Id'],created=image['Created']))
 started=time.monotonic()
 def command(argv,name,cap,negative=False):
  g=memory();assert g['available_bytes']>=8*1024**3 and g['psi_full_avg10']<1,g
  container='gamebub-v111-header-'+stamp.lower()+'-'+str(len(r['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','4g','--memory-swap','4g','--cpus','2','--pids-limit','2048','--network','none','--ulimit','core=0','--mount',f'type=bind,src={build},dst={mapped}','-w',mapped,IMAGE,'timeout','--kill-after=5s',str(cap)+'s',*argv];row=dict(argv=cmd,resource_before=g,timeout_seconds=cap);r['commands'].append(row);began=time.monotonic();stop=None;last=-5;pressure=0
  with(out/name).open('w')as log:
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
  row.update(exit_code=code,stop_reason=stop,wall_seconds=time.monotonic()-began);write(out/'progress.json',r)
  if negative:
   s=(out/name).read_text();assert code==134 and not stop and 'stale staging response'in s and 'EXPECTED_ASSERTION_ARMED'in s and '"capture_enable":false'in s,(name,code,stop);row['status']='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'
  else:assert code==0 and not stop,(name,code,stop)
 try:
  for p in files:q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
  for p in V.iterdir():
   if p.is_file():shutil.copyfile(p,build/p.name)
  shutil.copyfile(parser,build/parser.name);shutil.copyfile(context,build/context.name)
  packets=[json.loads(x)for x in gzip.decompress(vectors.read_bytes()).splitlines()];(build/'packet-vectors.txt').write_text(''.join(' '.join(map(str,(x['id'],x['blocks'],x['packet_hex'],x['dense_hex'],x['packed_hex'])))+'\n'for x in packets))
  command(['verilator','--version'],'version.log',30)
  flags=['verilator','--cc','--exe','--build','-j','1','--assert','-Wall','--output-split','10000','--output-split-cfuncs','500','--language','1800-2017','-CFLAGS','-std=c++17 -O1 -Wall -Wextra -Werror']
  command([*flags,'--public-flat-rw','--top-module','ingress_capture_probe','--Mdir',mapped+'/ingress-obj',*[mapped+'/'+n for n in ['ingress_original.sv','ingress_candidate.sv','ingress_capture_probe.sv','br88_context_reference.sv','br88_context.sv','br88_rice_elastic.sv','tb_header.cpp']]],'compile.log',900)
  assert '%Warning-'not in(out/'compile.log').read_text();binary=mapped+'/ingress-obj/Vingress_capture_probe';r['binary_sha256']=sha(build/'ingress-obj/Vingress_capture_probe')
  for seed in r['seeds']:
   name=f'capture-{seed}.log';command([binary,str(seed),mapped+f'/capture-{seed}.csv'],name,180);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['positive_prepared_cases']==1728 and v['actual_raw_packets']==8 and v['high32_metadata_owners']==128 and v['capture_edge_abort_restarts']==3 and v['held_metadata_edges']==2312;r['capture_runs'].append(v)
   name=f'whole-{seed}.log';command([binary,str(seed),mapped+'/unused-trace.csv',mapped+'/packet-vectors.txt'],name,900);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['packets']==76 and v['cancel_retries']==36 and v['boundary_mask']==15;r['whole_ingress_runs'].append(v)
   name=f'header-{seed}.log';command([binary,str(seed)],name,300);v=json.loads((out/name).read_text().splitlines()[-1]);assert v['status']=='TEST_PASS' and v['synthetic_header_rows']==5896 and v['real_header_cases']==17 and v['extra_boundary_cancels']==30 and v['HEADER_cancels']==3;r['header_runs'].append(v)
  for mode in [1,2]:
   for index in [33,37,41]:
    name=f'negative-{mode}-{index}.log';command([binary,'111501',mapped+'/negative.csv',str(mode),str(index)],name,30,True);r['negative_owner_contract_rejections'].append(dict(mode=mode,index=index,status='PASS_EXPECTED_ORIGINAL_ASSERTION_REJECTION'))
  r['actual_RTL_run']=True;r['status']='PASS';assert all(sha(ROOT/n)==h for n,h in r['source_sha256'].items()),'Source drift during qualification'
 finally:
  for p in build.glob('capture-*.csv'):
   with p.open('rb')as a,gzip.GzipFile(filename=str(out/(p.name+'.gz')),mode='wb',mtime=0)as z:shutil.copyfileobj(a,z)
  r['wall_seconds']=time.monotonic()-started;r['artifacts_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()};write(out/'results.json',r);write(AREA/'results.json',dict(r,selected_report=str((out/'results.json').relative_to(ROOT)),selected_report_sha256=sha(out/'results.json')));print('HEADER_FOCUSED',r['status'],out,flush=True)
if __name__=='__main__':main()
