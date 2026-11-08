#include "Vdy71_platform_sim.h"
#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <unistd.h>
#include <cerrno>
#include <vector>
#include <fstream>
struct Sim {
 VerilatedContext c;Vdy71_platform_sim d{&c};uint64_t pixel=17029,cycles=0,next_report=1000000;unsigned csr_cycles;
 bool observe=false; unsigned seen=0;
 std::vector<uint32_t> raster=std::vector<uint32_t>(384000,0xffffffffu);
 void sample(){if(observe && !d.pixel_clk && d.data_enable && d.physical_x<480 && d.physical_y<800){
  unsigned at=d.physical_x*800+d.physical_y;
  if(raster[at]==0xffffffffu)++seen;
  raster[at]=(uint32_t(d.red)<<16)|(uint32_t(d.green)<<8)|d.blue;
 }}

 explicit Sim(unsigned latency):csr_cycles(latency){d.clk=0;d.read_clk=0;d.pixel_clk=0;d.rst=1;d.pixel_reset_n=0;d.bus_write=0;d.transport_fault=0;d.bus_address=0;d.bus_wdata=0;d.peek_address=0;d.eval();for(int i=0;i<8;++i)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<1000;++i)tick();}
 void advance(uint64_t target){while(c.time()<target){uint64_t n=std::min(target,pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());if(n<c.time())throw std::runtime_error("time reversal");c.timeInc(n-c.time());if(n==pixel){d.pixel_clk=!d.pixel_clk;pixel+=17029;}d.eval();sample();if(c.gotFinish())throw std::runtime_error("HDL stopped");}}
 void tick(){if(cycles>=4000000000ull)throw std::runtime_error("simulation watchdog");uint64_t t=c.time();advance(t+2625);d.read_clk=1;d.eval();advance(t+5000);d.clk=1;d.eval();advance(t+7625);d.read_clk=0;d.eval();advance(t+10000);d.clk=0;d.eval();++cycles;if(cycles==next_report){std::fprintf(stderr,"PLATFORM_PROGRESS cycles=%llu stage=%u busy=%u accepted=%u presented=%u rejected=%u underruns=%u\n",(unsigned long long)cycles,unsigned(d.stage),unsigned(d.busy),d.accepted_count,d.presented_count,d.rejected_count,d.lcd_underruns);std::fflush(stderr);next_report+=1000000;}}
 uint32_t read(uint32_t offset){if(offset>=4096||offset&3)throw std::runtime_error("CSR bound");d.bus_address=offset;d.bus_write=0;d.eval();for(unsigned i=0;i<csr_cycles;++i)tick();return d.bus_rdata;}
 void write(uint32_t offset,uint32_t value){if(offset>=4096||offset&3)throw std::runtime_error("CSR bound");d.bus_address=offset;d.bus_wdata=value;d.bus_write=1;d.eval();tick();d.bus_write=0;d.eval();for(unsigned i=1;i<csr_cycles;++i)tick();}
};
extern "C" {
void* cu71_sim_create(unsigned cycles){return new Sim(cycles);}
void cu71_sim_destroy(void*p){auto*s=static_cast<Sim*>(p);s->d.final();delete s;}
uint32_t cu71_sim_read(void*p,uint32_t o){return static_cast<Sim*>(p)->read(o);}
void cu71_sim_write(void*p,uint32_t o,uint32_t v){static_cast<Sim*>(p)->write(o,v);}
void cu71_sim_advance(void*p,uint32_t n){auto*s=static_cast<Sim*>(p);for(uint32_t i=0;i<n;++i)s->tick();}
uint64_t cu71_sim_us(void*p){return static_cast<Sim*>(p)->c.time()/1000000ull;}
}
static bool transfer(int fd,void*buffer,size_t bytes,bool output){auto*p=static_cast<uint8_t*>(buffer);while(bytes){ssize_t n=output ? ::write(fd,p,bytes) : ::read(fd,p,bytes);if(n<0&&errno==EINTR)continue;if(n<=0)return false;p+=n;bytes-=size_t(n);}return true;}
int rpc_main(int argc,char**argv){int replyfd=dup(STDOUT_FILENO);if(replyfd<0)return 2;dup2(STDERR_FILENO,STDOUT_FILENO);try{
 unsigned latency=argc>1?unsigned(std::stoul(argv[1])):8;if(latency==0||latency>10000)throw std::runtime_error("CSR latency bound");Sim sim(latency);uint32_t request[5],reply[6];uint32_t expected=0;
 while(transfer(STDIN_FILENO,request,sizeof request,false)){
  if(request[0]!=0x43535231||request[1]!=++expected)throw std::runtime_error("RPC identity");uint32_t result=0;bool finish=false;
  switch(request[2]){case 0:{finish=true;break;}
case 6:{
 const std::string base="/mnt/c/moon/dev/experiments/stb1-v55-video12-real-rust-system-20261108";
 unsigned fid=request[3];
 for(unsigned bank=0;bank<3;++bank){
  std::ofstream f(base+"/frame"+std::to_string(fid)+"-bank"+std::to_string(bank)+".u16",std::ios::binary);
  for(unsigned i=0;i<259200;++i){sim.d.peek_address=0x80000+bank*0x400000+i;sim.d.eval();uint16_t v=sim.d.peek_data;f.write(reinterpret_cast<char*>(&v),2);}
 }
 sim.observe=true;sim.seen=0;std::fill(sim.raster.begin(),sim.raster.end(),0xffffffffu);
 uint64_t end=sim.cycles+3500000;
 while(sim.seen<384000 && sim.cycles<end)sim.tick();
 sim.observe=false;
 std::ofstream f(base+"/frame"+std::to_string(fid)+"-raster.u32",std::ios::binary);
 f.write(reinterpret_cast<const char*>(sim.raster.data()),sim.raster.size()*4);
 std::fprintf(stderr,"FRAME_SNAPSHOT frame=%u seen=%u front_bank=%u underruns=%u\n",fid,sim.seen,unsigned(sim.d.front_bank),sim.d.lcd_underruns);
 if(sim.seen!=384000)throw std::runtime_error("incomplete raster observation");
 result=sim.d.front_bank;break;}
case 1:result=cu71_sim_read(&sim,request[3]);break;case 2:cu71_sim_write(&sim,request[3],request[4]);break;case 3:if(request[3]>1000000)throw std::runtime_error("tick bound");cu71_sim_advance(&sim,request[3]);break;
   case 4:result=request[3]==0?sim.d.model_reads:request[3]==1?sim.d.model_writes:request[3]==2?sim.d.model_refreshes:sim.d.lcd_underruns;break;
   case 5:if(request[3]>=16777216)throw std::runtime_error("peek bound");sim.d.peek_address=request[3];sim.d.eval();result=sim.d.peek_data;break;
   default:throw std::runtime_error("RPC opcode");}
  uint64_t time=cu71_sim_us(&sim);reply[0]=0x43535231;reply[1]=expected;reply[2]=0;reply[3]=result;reply[4]=uint32_t(time);reply[5]=uint32_t(time>>32);
  if(!transfer(replyfd,reply,sizeof reply,true))throw std::runtime_error("RPC response closed");if(finish)break;
 }
 std::fprintf(stderr,"PLATFORM_SERVER_COMPLETE accepted=%u presented=%u rejected=%u underruns=%u clocks=%llu model_reads=%u model_writes=%u refreshes=%u\n",sim.d.accepted_count,sim.d.presented_count,sim.d.rejected_count,sim.d.lcd_underruns,(unsigned long long)sim.cycles,sim.d.model_reads,sim.d.model_writes,sim.d.model_refreshes);sim.d.final();return 0;
}catch(const std::exception&e){std::fprintf(stderr,"PLATFORM_FAIL %s\n",e.what());return 1;}}

int main(int argc,char**argv){return rpc_main(argc,argv);}
