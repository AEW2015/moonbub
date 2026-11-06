#include "Vdy71_platform_sim.h"
#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
#include <string>
#include <unistd.h>
#include <cerrno>
struct Sim {
 VerilatedContext c;Vdy71_platform_sim d{&c};uint64_t pixel=17029,cycles=0,next_report=1000000;unsigned csr_cycles;
 explicit Sim(unsigned latency):csr_cycles(latency){d.clk=0;d.read_clk=0;d.pixel_clk=0;d.rst=1;d.pixel_reset_n=0;d.bus_write=0;d.transport_fault=0;d.bus_address=0;d.bus_wdata=0;d.peek_address=0;d.eval();for(int i=0;i<8;++i)tick();d.rst=0;d.pixel_reset_n=1;for(int i=0;i<1000;++i)tick();}
 void advance(uint64_t target){while(c.time()<target){uint64_t n=std::min(target,pixel);if(d.eventsPending())n=std::min(n,d.nextTimeSlot());if(n<c.time())throw std::runtime_error("time reversal");c.timeInc(n-c.time());if(n==pixel){d.pixel_clk=!d.pixel_clk;pixel+=17029;}d.eval();if(c.gotFinish())throw std::runtime_error("HDL stopped");}}
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
  switch(request[2]){case 0:finish=true;break;case 1:result=cu71_sim_read(&sim,request[3]);break;case 2:cu71_sim_write(&sim,request[3],request[4]);break;case 3:if(request[3]>1000000)throw std::runtime_error("tick bound");cu71_sim_advance(&sim,request[3]);break;
   case 4:result=request[3]==0?sim.d.model_reads:request[3]==1?sim.d.model_writes:request[3]==2?sim.d.model_refreshes:sim.d.lcd_underruns;break;
   case 5:if(request[3]>=16777216)throw std::runtime_error("peek bound");sim.d.peek_address=request[3];sim.d.eval();result=sim.d.peek_data;break;
   default:throw std::runtime_error("RPC opcode");}
  uint64_t time=cu71_sim_us(&sim);reply[0]=0x43535231;reply[1]=expected;reply[2]=0;reply[3]=result;reply[4]=uint32_t(time);reply[5]=uint32_t(time>>32);
  if(!transfer(replyfd,reply,sizeof reply,true))throw std::runtime_error("RPC response closed");if(finish)break;
 }
 std::fprintf(stderr,"PLATFORM_SERVER_COMPLETE accepted=%u presented=%u rejected=%u underruns=%u clocks=%llu model_reads=%u model_writes=%u refreshes=%u\n",sim.d.accepted_count,sim.d.presented_count,sim.d.rejected_count,sim.d.lcd_underruns,(unsigned long long)sim.cycles,sim.d.model_reads,sim.d.model_writes,sim.d.model_refreshes);sim.d.final();return 0;
}catch(const std::exception&e){std::fprintf(stderr,"PLATFORM_FAIL %s\n",e.what());return 1;}}

#include <fstream>
#include <iostream>
#include <vector>
#include <zlib.h>
static void need(bool ok,const std::string&why){if(!ok)throw std::runtime_error(why);}
struct Test {
 Sim s{8};uint32_t sequence=0;unsigned checks=0;
 void eq(uint32_t a,uint32_t b,const char*why){++checks;need(a==b,std::string(why)+" actual="+std::to_string(a)+" expected="+std::to_string(b));}
 void context(uint64_t g,uint32_t f=0,uint32_t r=0){s.write(0x40,uint32_t(g));s.write(0x44,uint32_t(g>>32));s.write(0x48,f);s.write(0x4c,r);}
 uint32_t command(unsigned op,uint32_t expected){uint32_t seq=++sequence;s.write(0x20,seq);s.write(0x24,op);unsigned tries=0;while(s.read(0x28)!=seq)need(++tries<10000,"command timeout");eq(s.read(0x2c),expected,"command status");return s.read(0x30);}
 uint32_t diag(unsigned a){s.write(0x200,a);return s.read(0x204);}
 uint16_t peek(uint32_t a){s.d.peek_address=a;s.d.eval();return uint16_t(s.d.peek_data);}
 void upload(const std::vector<uint8_t>&bytes,uint64_t generation){
  context(generation);s.write(0x50,bytes.size());uint32_t crc=crc32(0,bytes.data(),bytes.size());s.write(0x54,crc);command(1,0);
  for(size_t at=0;at<bytes.size();at+=4){uint32_t v=0;for(size_t n=0;n<4&&at+n<bytes.size();++n)v|=uint32_t(bytes[at+n])<<(n*8);s.write(0x100,v);}
  eq(s.read(0x104),bytes.size(),"actual stored bytes");eq(s.read(0x10c),crc,"actual stager CRC");eq(s.read(0x110),0,"staging faults");command(2,0);
 }
 uint32_t packet_word(const std::vector<uint8_t>&p,unsigned at){uint32_t v=0;for(unsigned i=0;i<4;++i)v|=uint32_t(p[at+i])<<(i*8);return v;}
 void run(const std::vector<uint8_t>&packet){
  eq(s.read(0),0x44593731,"explicit DY71 CSR magic");eq(s.read(4),0x10000,"ABI");eq(s.read(8),15,"capabilities");
  eq(s.d.profile_magic,0x44593731,"actual PIPE profile");eq(s.d.profile_abi,0x10000,"actual PIPE ABI");eq(s.d.profile_capabilities,15,"actual PIPE capabilities");
  eq(s.read(0x354),0,"starting accepted");eq(s.read(0x358),0,"starting presented");
  eq(diag(0),0x43553730,"nested diagnostic identity retained, not CSR profile");
  eq(diag(0x1c),0xffffffff,"starting reference ID sentinel");eq(diag(0x20),0xffffffff,"starting front ID sentinel");for(unsigned a=0x98;a<=0xa4;a+=4)eq(diag(a),0,"starting accepted tag");
  uint32_t writes=s.d.model_writes;context(0);s.write(0x50,8);s.write(0x54,0x88aa689f);command(1,0x80000002);eq(s.read(0x114),0,"badgen no staged identity");eq(s.d.model_writes,writes,"badgen no physical write");
  context(1);s.write(0x50,49153);command(1,0x80000002);s.write(0x50,49152);command(1,0);command(4,0);
  upload({0,1,2,3,4,5,6,7},1);context(99);command(3,0x80000004);command(4,0x80000005);eq(s.read(0x354),0,"stale start no owner side effect");context(1);command(4,0);
  // Real packet accepted by the real owner. Cancel during parsing before any
  // CPU HUD request, so no software-success surrogate is needed to drain.
  upload(packet,2);command(3,0);need(s.d.busy,"real owner not active");eq(s.read(0x0c)&0x20,0,"early abort before HUD snapshot");command(5,0);
  unsigned wait=0;while(s.d.busy){s.tick();need(++wait<100000,"early owner abort drain");}
  for(unsigned i=0;i<50;++i)s.tick();eq(s.read(0x0c)&0x1c,0,"early abort releases frame/staging only after drain");eq(s.read(0x354),0,"abort no accepted");eq(s.d.cpu_software_ack_calls,0,"no invented abort ACK");
  // Fresh generation with actual parser/base/memory running concurrently.
  upload(packet,3);context(99);command(3,0x80000004);context(3);command(3,0);
  unsigned count=s.d.cpu_packet_requests;s.write(0x50,0);eq(command(21,0),packet_word(packet,0),"actual staged prefix");eq(s.d.cpu_packet_requests,count+4,"four real CPU packet replies");
  s.write(0x50,packet.size()-4);eq(command(21,0),packet_word(packet,packet.size()-4),"unaligned final valid window");
  count=s.d.cpu_packet_requests;s.write(0x50,packet.size()-3);command(21,0x8000000b);eq(s.d.cpu_packet_requests,count,"packet bounds no request");
  context(99);s.write(0x50,0);command(21,0x8000000b);eq(s.d.cpu_packet_requests,count,"badgen packet no request");eq(s.read(0x110),0,"bad CPU packets no stager fault");eq(s.d.quarantine,0,"bad CPU packets do not corrupt arbiter");
  wait=0;while(!(s.read(0x0c)&0x20))need(++wait<500000,"actual HUD preparation timeout");
  uint64_t generation=uint64_t(s.read(0x304))|(uint64_t(s.read(0x308))<<32);uint32_t fid=s.read(0x30c),reference=s.read(0x310),bank=s.read(0x318)&3;
  eq(uint32_t(generation),3,"actual HUD generation");need(bank<3,"HUD bank");uint32_t base=bank==0?0x100000:bank==1?0x500000:0x900000;
  uint32_t span=s.read(0x314);need((span&65535)+(span>>16)<=packet.size(),"actual original HU span");
  context(generation+1,fid,reference);s.write(0x50,0);s.write(0x54,0xbeef);count=s.d.cpu_aux_requests;command(17,0x80000008);eq(s.d.cpu_aux_requests,count,"bad HUD gen no aux side effect");
  context(generation,fid,reference);s.write(0x50,21120);command(17,0x80000008);eq(s.d.cpu_aux_requests,count,"HUD bounds no aux side effect");
  s.write(0x50,0);s.write(0x54,0xbeef);command(17,0);eq(s.d.cpu_aux_requests,count+1,"actual completed HUD write request");eq(peek(base),0xbeef,"actual SDRAM HUD word0");eq(command(18,0),0xbeef,"actual CSR SDRAM readback0");
  s.write(0x50,1);s.write(0x54,0x1234);command(17,0);eq(peek(base+1),0x1234,"actual SDRAM HUD word1");eq(command(18,0),0x1234,"actual CSR SDRAM readback1");
  uint16_t untouched=peek(base+3);s.write(0x50,3);s.write(0x54,0xf00d);command(17,0x80000009);eq(peek(base+3),untouched,"noncontiguous write denied by actual system permission");
  // Do not fabricate HUD_RESULT, HUD_DRAIN, COMMIT or ABORT success. A real
  // post-HUD abort must wait for the actual CPU endpoint's ABORT response.
  command(5,0);for(unsigned i=0;i<1000;++i)s.tick();uint32_t flags=s.read(0x0c);
  need(s.d.busy&&(flags&0x40)&&(flags&0x10),"post-HUD abort must retain pending ownership");eq(s.read(0x334)&7,6,"actual CPU ABORT request");
  eq(s.read(0x354),0,"no accepted frame without real HUD/commit");eq(s.read(0x358),0,"no presented frame without real HUD/commit");eq(s.d.cpu_hud_result_calls,0,"no fabricated HUD result");eq(s.d.cpu_hud_drain_calls,0,"no fabricated HUD drain");eq(s.d.cpu_software_ack_calls,0,"no fabricated software ACK");
  context(4);s.write(0x50,8);s.write(0x54,0);command(1,0x80000002);need(s.d.busy,"pending abort did not fence reuse");
  std::cout<<"DY71_LOCAL_CSR_PASS checks="<<checks<<" cpu_packet_requests="<<s.d.cpu_packet_requests<<" aux_requests="<<s.d.cpu_aux_requests<<" aux_completions="<<s.d.cpu_aux_completions<<" accepted="<<s.d.accepted_count<<" presented="<<s.d.presented_count<<" rejected="<<s.d.rejected_count<<" busy="<<unsigned(s.d.busy)<<" stage="<<unsigned(s.d.stage)<<" no_fake_ACK=1 pending_actual_native_ABORT=1 model_writes="<<s.d.model_writes<<" model_reads="<<s.d.model_reads<<" clocks="<<s.cycles<<"\n";
 }
};
int control_main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{need(argc==2,"packet argument");std::ifstream f(argv[1],std::ios::binary);need(bool(f),"original packet file");std::vector<uint8_t>p{std::istreambuf_iterator<char>(f),{}};need(!p.empty()&&p.size()<=49152,"packet cap");Test test;test.run(p);test.s.d.final();return 0;}catch(const std::exception&e){std::cerr<<"DY71_LOCAL_CSR_FAIL "<<e.what()<<"\n";return 1;}}

int main(int argc,char**argv){if(argc>1&&std::string(argv[1])=="--control")return control_main(argc-1,argv+1);return rpc_main(argc,argv);}
