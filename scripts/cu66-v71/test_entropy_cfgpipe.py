"""Execute actual entropy fixtures plus exhaustive supported configuration modulo."""
from pathlib import Path
import hashlib,json,shlex,subprocess,time
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/entropy';p=r/'fpga/experiments/cu66-v69/entropy'
o=d/'evidence/regression03';o.mkdir(parents=True,exist_ok=False)
source=d/'cu71_ab38_decoder_cfgpipe.sv';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pins={str(f.relative_to(r)).replace('\\','/'):sha(f) for f in [source,p/'cu66_ab38_decoder.sv',p/'tb_entropy.cpp',p/'actual.tsv',p/'directed.tsv',p/'stress.tsv']}
(o/'cu71_ab38_decoder_cfgpipe.sv').write_bytes(source.read_bytes());(o/'tb.cpp').write_text((p/'tb_entropy.cpp').read_text().replace('Vcu66_ab38_decoder','Vcu71_ab38_decoder_cfgpipe'),newline='\n')
sweep=r'''#include "Vcu71_ab38_decoder_cfgpipe.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <stdexcept>
static void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
int main(){try{
 VerilatedContext c;Vcu71_ab38_decoder_cfgpipe d{&c};
 auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();};
 d.rst=1;d.abort_i=0;d.cfg_valid=0;d.rd_req_ready=0;d.rd_rsp_valid=0;d.rd_rsp_data=0;d.tile_ready=0;tick();d.rst=0;tick();
 uint64_t checks=0;unsigned valid=0,rejected=0;
 for(unsigned n=1;n<=8100;n++)for(unsigned w=1;w<=256;w++){
  d.rst=1;tick();d.rst=0;tick();need(d.cfg_ready,"reset cfg readiness");
  d.cfg_dispatch=5;d.cfg_packet_bytes=100;d.cfg_blocks=n;d.cfg_blocks_w=w;d.cfg_valid=1;tick();d.cfg_valid=0;
  // Inputs can change after acceptance; divider must use its retained fields.
  d.cfg_blocks=1;d.cfg_blocks_w=1;d.cfg_dispatch=4;
  unsigned clocks=0;while(!d.error&&!d.rd_req_valid&&clocks++<40)tick();
  need(clocks<40,"bounded metadata validation");need(bool(d.error)==bool(n%w),"supported modulo mismatch");
  if(n%w){need(d.error_code==1&&!d.rd_req_valid,"invalid cfg performed memory read");rejected++;}else valid++;
  checks++;
 }
 for(unsigned at=0;at<17;at++){
  d.rst=1;tick();d.rst=0;tick();d.cfg_dispatch=5;d.cfg_packet_bytes=100;d.cfg_blocks=5400;d.cfg_blocks_w=90;d.cfg_valid=1;tick();d.cfg_valid=0;
  for(unsigned k=0;k<at;k++)tick();d.abort_i=1;tick();d.abort_i=0;tick();need(d.cfg_ready&&!d.busy&&!d.rd_req_valid,"abort metadata microstep");
 }
 std::printf("CFG_MODULO_EXHAUSTIVE_PASS checks=%llu valid=%u rejected=%u abort_positions=17\n",(unsigned long long)checks,valid,rejected);return0:
 return 0;
}catch(const std::exception&e){std::fprintf(stderr,"CFG_MODULO_FAIL %s\n",e.what());return1:return 1;}}
'''.replace('return0:\n','').replace('return1:','')
(o/'cfg.cpp').write_text(sweep,newline='\n')
win=lambda q:'/mnt/'+q.drive[0].lower()+str(q)[2:].replace('\\','/')
mdir='/tmp/cu71-entropy-cfgpipe-'+str(time.time_ns());script=o/'build.sh'
script.write_text('set -eu\nsource /opt/gamebub-openxc7-20261021/oss-cad-suite/environment\nverilator --version\nverilator --cc --exe --build -j 2 --Wall --top-module cu71_ab38_decoder_cfgpipe --Mdir '+shlex.quote(mdir)+" -CFLAGS '-O2 -std=c++17' -LDFLAGS '-lz' "+shlex.quote(win(o/'cu71_ab38_decoder_cfgpipe.sv'))+' '+shlex.quote(win(o/'tb.cpp'))+'\n'+
 'g++ -O2 -std=c++17 -pthread -I/opt/gamebub-openxc7-20261021/oss-cad-suite/share/verilator/include -I'+mdir+' '+shlex.quote(win(o/'cfg.cpp'))+' '+mdir+'/Vcu71_ab38_decoder_cfgpipe__ALL.a '+mdir+'/verilated.o '+mdir+'/verilated_threads.o -o '+mdir+'/cfg_sweep\n',newline='\n')
commands=[]
def run(label,args,seconds):
 start=time.monotonic()
 with (o/(label+'.log')).open('wb')as log:q=subprocess.run(args,cwd=r,stdout=log,stderr=subprocess.STDOUT,timeout=seconds)
 commands.append(dict(label=label,command=args,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(commands,indent=2)+'\n');assert q.returncode==0,(label,o)
 return (o/(label+'.log')).read_text()
base=['wsl','-d','MRS-HDL-Research','--','bash','-c']
run('build',['wsl','-d','MRS-HDL-Research','--','bash',win(script)],600)
run('modulo',base+['source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+mdir+'/cfg_sweep'],1800)
for index,seed,limit,extra in [('directed',6901,31,' --abort-tests'),('stress',6902,120,' --abort-tests'),('actual',6901,1371,'')]:
 text=run(index,base+['source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+mdir+'/Vcu71_ab38_decoder_cfgpipe '+shlex.quote(win(p/(index+'.tsv')))+' '+str(seed)+' '+str(limit)+extra],3600)
 assert 'TEST_PASS backend=Verilator' in text and 'TEST_FAIL' not in text
assert pins=={name:sha(r/name) for name in pins}
(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_ENTROPY_AND_EXHAUSTIVE_CONFIG_MICROPIPE',source_sha256=pins,hardware=False,scope='Exact coefficient/reject/abort behavior;17-cycle config validation changes latency, not payload'),indent=2)+'\n');print('CU71_ENTROPY_CFGPIPE_REGRESSION_PASS')
