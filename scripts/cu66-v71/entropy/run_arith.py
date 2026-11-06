"""Actual coefficient/reject campaign plus aborts at all appended arithmetic states."""
from pathlib import Path
import argparse,hashlib,json,re,shlex,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--source',type=Path);p.add_argument('--derivation',type=Path);a=p.parse_args();r=Path(__file__).resolve().parents[3]
d=r/'fpga/experiments/cu66-v71/entropy';old=r/'fpga/experiments/cu66-v69/entropy';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False)
src=a.source.resolve()if a.source else d/'cu71_ab38_decoder_arithpipe.sv';top=src.stem;sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();pins={}
for f in [src,old/'cu66_ab38_decoder.sv',old/'tb_entropy.cpp',old/'actual.tsv',old/'directed.tsv',old/'stress.tsv']:pins[f.relative_to(r).as_posix()]=sha(f)
for index in ['actual','directed','stress']:
 for line in(old/(index+'.tsv')).read_text().splitlines():
  if not line:continue
  fields=line.split('\t')
  for n in fields[1:3]:
   if n!='-':f=(old/n).resolve();pins[f.relative_to(r).as_posix()]=sha(f)
(o/src.name).write_bytes(src.read_bytes());tb=(old/'tb_entropy.cpp').read_text().replace('Vcu66_ab38_decoder','V'+top)
tb=tb.replace('#include "verilated.h"', '#include "verilated.h"\n#include "V'+top+'___024root.h"')
states=json.loads((a.derivation.resolve()if a.derivation else d/'arith-derivation.json').read_text())['new_states'];ids=','.join(map(str,states.values()))
method=''' void arithmetic_micro_abort_checks(const std::vector<Fixture>&cases){
  for(unsigned target:std::array<unsigned,STATE_COUNT>{STATE_IDS}){
   const Fixture*chosen=nullptr;
   for(const auto&candidate:cases){
    if(candidate.invalid)continue;
    load(candidate);unsigned count=0;
    while(d.debug_state!=target&&!d.done&&!d.error){step();demand(++count<20000000,"microstate setup watchdog");}
    if(d.debug_state==target){chosen=&candidate;break;}
    demand(d.done&&!d.error&&!pending,"valid setup fixture failed");
   }
   demand(chosen!=nullptr,"new microstate uncovered by valid fixtures");
   std::array<uint8_t,352> before{};
   for(unsigned i=0;i<352;i++)before[i]=d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i];
   unsigned decisions=d.decoded_decisions;d.abort_i=1;step(false);
   for(unsigned i=0;i<352;i++)demand(before[i]==d.rootp->cu71_ab38_decoder_arithpipe__DOT__probabilities[i],"probability write on arithmetic abort");
   demand(d.decoded_decisions==decisions,"aborted arithmetic decision committed");
   for(unsigned n=0;n<3;n++){step(false);demand(!d.cfg_ready,"held abort admitted config");}
   d.abort_i=0;step(false);held=false;request_held=false;
   demand(d.cfg_ready&&!d.busy&&!d.done&&!d.tile_valid&&!pending,"arithmetic abort did not quiesce");
   run(*chosen);
  }
  std::cout<<"ARITHMETIC_MICRO_ABORT_PASS appended_states=STATE_COUNT probability_writes_on_abort=0 valid_retry=STATE_COUNT\\n";
 }
'''.replace('STATE_IDS',ids).replace('STATE_COUNT',str(len(states))).replace('cu71_ab38_decoder_arithpipe__DOT__',top+'__DOT__')
tb=tb.replace(' void abort_checks(const Fixture&good){',method+' void abort_checks(const Fixture&good){')
tb=tb.replace('sim.abort_checks(*p);','sim.abort_checks(*p);sim.arithmetic_micro_abort_checks(fs);')
(o/'tb.cpp').write_text(tb,newline='\n');(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n')
lin=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
build='/tmp/cu71-entropy-arith-'+str(time.time_ns());env='source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '
commands=[]
def run(label,args,timeout):
 start=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(args,cwd=r,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append({'label':label,'command':args,'returncode':q.returncode,'seconds':time.monotonic()-start,'log_sha256':sha(o/(label+'.log'))});(o/'execution.json').write_text(json.dumps(commands,indent=2)+'\n')
 print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
 return(o/(label+'.log')).read_text()
def wsl(args):return['wsl','-d','MRS-HDL-Research','--','bash','-lc',env+shlex.join(args)]
run('build',wsl(['verilator','--cc','--exe','--build','-j','2','--Wall','--public-flat-rw','--top-module',top,'--Mdir',build,'-CFLAGS','-O2 -std=c++17','-LDFLAGS','-lz',lin(o/src.name),lin(o/'tb.cpp')]),600)
rows={}
for index,seed,count,abort in [('directed',6901,31,True),('stress',6902,120,True),('actual',6901,1371,False)]:
 args=[build+'/V'+top,lin(old/(index+'.tsv')),str(seed),str(count)]+(['--abort-tests']if abort else[])
 text=run(index,wsl(args),3600);assert 'TEST_PASS backend=Verilator'in text and 'TEST_FAIL'not in text
 if abort:assert f'ARITHMETIC_MICRO_ABORT_PASS appended_states={len(states)} probability_writes_on_abort=0 valid_retry={len(states)}'in text
 rows[index]=next(x for x in text.splitlines()if x.startswith('TEST_PASS'))
for n,h in pins.items():assert sha(r/n)==h,n
(o/'result.json').write_text(json.dumps({'status':'PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS','source_sha256':pins,'campaigns':rows,'new_states':states,'hardware':False,'routed_timing':False,'scope':'1371actual+31directed+120stresscoefficient/rejectionfixtures; inheritedabort/reset/backpressureandall4newmicrostateabortprobabilityRAM/counterchecks+validretry. Latencychanges, wireandroundingunchanged.'},indent=2)+'\n')
print('PASS_ARITHMETIC_MICROPIPE_ACTUAL_COEFFICIENTS_AND_ABORTS')
