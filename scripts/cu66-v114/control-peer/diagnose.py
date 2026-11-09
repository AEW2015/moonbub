#!/usr/bin/env python3
"""One bounded reproduction against the exact frozen failed model; never a PASS certificate."""
import datetime,hashlib,json,pathlib,shutil,subprocess,time
R=pathlib.Path(__file__).resolve().parents[3];A=R/'experiments/python-gamebub-v114/control-peer';P=A/'attempts/20261108T232958214656Z/receipt.json';B=pathlib.Path('/home/lori/gamebub-build/cu66-v69/v114-control-peer-20261108T232958214656Z');IMAGE='sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def memory():
 m={x.split(':')[0]:int(x.split()[1])*1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines()};f=next(x for x in pathlib.Path('/proc/pressure/memory').read_text().splitlines()if x.startswith('full '));return dict(available_bytes=m['MemAvailable'],psi_full_avg10=float(f.split('avg10=')[1].split()[0]))
def main():
 # Pin the same image as the failed actual compile, not a locally named tag.
 parent=json.loads(P.read_text());image=parent['image_id'];assert image==IMAGE
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/'diagnostics'/stamp;out.mkdir(parents=True);mapped='/build/'+B.name
 src=R/'fpga/experiments/cu66-v114-control-peer/tb_diagnostic.cpp';header=P.parent/'sources/fpga/experiments/cu66-v114-control-peer/bench_peer_base.hpp';model=B/'obj/Vcs88_pipeline_v91k__ALL.a';files=[src,header,P,pathlib.Path(__file__).resolve(),model,*[B/'obj'/n for n in ['verilated.o','verilated_dpi.o','verilated_threads.o']]];q=dict(status='DIAGNOSTIC_NOT_QUALIFICATION',parent_receipt=dict(path=str(P.relative_to(R)),sha256=sha(P)),input_sha256={str(p):sha(p)for p in files},commands=[],assertions_disabled=False)
 def run(argv,name):
  gate=memory();assert gate['available_bytes']>=8*1024**3 and gate['psi_full_avg10']<1,gate;container='gamebub-v114-peer-diagnostic-'+stamp.lower()+'-'+str(len(q['commands']));cmd=['docker','run','--rm','--init','--name',container,'--memory','8g','--memory-swap','8g','--cpus','2','--network','none','--ulimit','core=0','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={B},dst={mapped}','-w',mapped,image,'timeout','--kill-after=5s','120s',*argv];c=dict(argv=cmd,resource_before=gate);q['commands'].append(c);start=time.monotonic();hi=0
  with(out/name).open('w')as log:
   child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
   while child.poll()is None:
    sample=memory();hi=hi+1 if sample['psi_full_avg10']>=5 else 0
    if sample['available_bytes']<4*1024**3 or hi>=2 or time.monotonic()-start>140:subprocess.run(['docker','stop','--time','5',container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15);c['resource_stop']=sample;break
    time.sleep(2)
   c['exit_code']=child.wait(timeout=20)
  assert c['exit_code']==0 and 'resource_stop'not in c,name
 try:
  shutil.copyfile(src,B/'tb_diagnostic.cpp');shutil.copyfile(header,B/'bench_peer_base.hpp')
  run(['g++','-std=c++17','-O1','-Wall','-Wextra','-Werror','-DELASTIC=1','-DVM_SC=0','-DVM_TRACE=0','-DVM_COVERAGE=0','-DVM_TRACE_FST=0','-DVM_TRACE_VCD=0','-I'+mapped+'/obj','-isystem','/usr/share/verilator/include','-isystem','/usr/share/verilator/include/vltstd',mapped+'/tb_diagnostic.cpp',mapped+'/obj/Vcs88_pipeline_v91k__ALL.a',mapped+'/obj/verilated.o',mapped+'/obj/verilated_dpi.o',mapped+'/obj/verilated_threads.o','-pthread','-latomic','-o',mapped+'/diagnostic'],'compile.log')
  run([mapped+'/diagnostic',mapped+'/cases.tsv',mapped+'/transform_tiles.tsv',mapped+'/canonical_goldens.tsv','114401',mapped+'/diagnostic-events.jsonl',mapped+'/diagnostic-canonical.tsv'],'diagnostic.jsonl');q['observation']=json.loads((out/'diagnostic.jsonl').read_text().splitlines()[-1]);assert q['observation']['status']=='FAIL_REPRODUCED_OLD_INCOMPLETE_FIXTURE';q['status']='FAIL_REPRODUCED_OLD_INCOMPLETE_FIXTURE'
 finally:
  q['artifact_sha256']={p.name:sha(p)for p in out.iterdir()if p.is_file()};(out/'receipt.json').write_text(json.dumps(q,indent=2,sort_keys=True)+'\n');print(q['status'],out)
if __name__=='__main__':main()
