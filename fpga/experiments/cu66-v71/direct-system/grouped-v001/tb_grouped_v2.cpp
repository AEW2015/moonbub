#include "Vcu71_word_bridge_direct.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <stdexcept>
static unsigned checks=0;
static void need(bool x,const char*w){++checks;if(!x)throw std::runtime_error(w);}
struct Sim{
 Vcu71_word_bridge_direct d;
 unsigned mode=0,cycle=0,physical=0,LCD=0,BG=0,hold_start=0,held_LCD=0,held_BG=0;
 std::array<unsigned,4>sent{},received{},target{},address{},mask{};
 std::array<bool,4>pending{};
 std::array<std::array<uint32_t,4>,4>payload{};
 bool active=false,writing=false;unsigned memory_address=0,delay=0,beat=0;
 static uint16_t word(unsigned a,unsigned i){return uint16_t((a^0x3456)+i);}
 template<class W>void data(W&w,unsigned base){for(unsigned i=0;i<4;i++)w[i]=uint32_t(uint16_t(base+i*2))|(uint32_t(uint16_t(base+i*2+1))<<16);}
 Sim(unsigned m,std::array<unsigned,4>t):mode(m),target(t){
  d.clk=0;d.rst=1;d.p0_valid=d.p1_valid=d.p2_valid=d.p3_valid=0;d.p0_rsp_ready=d.p1_rsp_ready=d.p2_rsp_ready=d.p3_rsp_ready=1;d.mem_req_ready=1;d.mem_idle=1;d.mem_rsp_valid=0;d.mem_rsp_data=0;clock();clock();d.rst=0;
 }
 void clock(){d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();}
 void tick(){
  need(cycle<50000,"bounded fairness watchdog");
  d.p0_valid=sent[0]<target[0];d.p1_valid=sent[1]<target[1];d.p2_valid=sent[2]<target[2];d.p3_valid=sent[3]<target[3];
  d.p0_write=1;d.p0_addr=0x080000+sent[0]*8;d.p0_data=0;data(d.p0_burst_data,0x1000+sent[0]*8);d.p0_burst_mask=sent[0]&1?0xaaaa:0;
  d.p1_write=0;d.p1_addr=mode==3?0x400000:0x500103+(mode==1?0:sent[1]*8);d.p1_data=0;
  d.p2_addr=0x480200+sent[2]*8;d.p3_addr=0xc00000+sent[3]*8;data(d.p3_data,0xa000+sent[3]*8);d.p3_mask=sent[3]&1?0x5555:0;
  d.p0_rsp_ready=mode!=2||(hold_start&&cycle>=hold_start+100);d.p1_rsp_ready=d.p2_rsp_ready=d.p3_rsp_ready=1;
  d.mem_req_ready=!active;d.mem_idle=!active;
  d.mem_rsp_valid=active&&!writing&&delay==0;d.mem_rsp_data=word(memory_address,beat);
  d.clk=0;d.eval();
  bool rsp[4]={bool(d.p0_rsp_valid&&d.p0_rsp_ready),bool(d.p1_rsp_valid&&d.p1_rsp_ready),bool(d.p2_rsp_valid&&d.p2_rsp_ready),bool(d.p3_rsp_valid&&d.p3_rsp_ready)};
  bool req[4]={bool(d.p0_valid&&d.p0_ready),bool(d.p1_valid&&d.p1_ready),bool(d.p2_valid&&d.p2_ready),bool(d.p3_valid&&d.p3_ready)};
  if(mode==2&&d.p0_rsp_valid&&!d.p0_rsp_ready){if(!hold_start){hold_start=cycle;held_LCD=LCD;held_BG=BG;}need(!d.p0_rsp_error&&d.p0_rsp_data==0,"held response changed");}
  if(mode==2&&hold_start&&cycle<hold_start+100){
   need(d.p0_rsp_valid&&!d.p0_rsp_error&&d.p0_rsp_data==0,"held valid/data/error did not persist");
   if(cycle==hold_start+99)need(LCD>held_LCD&&BG>held_BG,"unrelated progress occurred only after held response release");
  }
  for(unsigned i=0;i<4;i++)if(rsp[i]){
   need(pending[i],"response crossed owner/unaccepted request");
   bool error=i==0?d.p0_rsp_error:i==1?d.p1_rsp_error:i==2?d.p2_rsp_error:d.p3_rsp_error;
   need(error==(mode==3&&i==1),"wrong response error owner");
   if(i==1&&!error)need(d.p1_rsp_data==word(address[i]&~7u,address[i]&7),"scalar/cache read data changed");
   if(i==2)for(unsigned k=0;k<8;k++)need(uint16_t(d.p2_rsp_data[k/2]>>(16*(k&1)))==word(address[i],k),"LCD burst response crossed owner");
   pending[i]=false;received[i]++;
  }
  for(unsigned i=0;i<4;i++)if(req[i]){
   need(!pending[i],"request slot overwritten");pending[i]=true;
   address[i]=i==0?d.p0_addr:i==1?d.p1_addr:i==2?d.p2_addr:d.p3_addr;
   mask[i]=i==0?d.p0_burst_mask:i==3?d.p3_mask:0;
   if(i==0||i==3)for(unsigned k=0;k<4;k++)payload[i][k]=i==0?d.p0_burst_data[k]:d.p3_data[k];
   sent[i]++;
  }
  bool accept=d.mem_req_valid&&d.mem_req_ready;
  unsigned accept_address=d.mem_req_addr;bool accept_write=d.mem_req_write;
  if(accept){
   unsigned owner=accept_write?(accept_address>=0xc00000?3:0):(accept_address>=0x500000?1:2);
   need(pending[owner]&&(address[owner]&~7u)==accept_address,"physical command lost identity");
   if(mode==0)need((physical%12<8)==(owner==2),"continuous physical quota is not8LCD:4BG");
   if(owner==2)LCD++;else BG++;physical++;
   if(accept_write){need(d.mem_req_burst_mask==mask[owner],"held write mask corrupted");for(unsigned k=0;k<4;k++)need(d.mem_req_burst_data[k]==payload[owner][k],"held burst payload corrupted");}
  }
  bool old_active=active,old_response=d.mem_rsp_valid;clock();
  if(old_active){if(writing){if(delay)delay--;else active=false;}else if(delay)delay--;else if(old_response){if(beat==7)active=false;else beat++;}}
  if(accept){need(!old_active,"controller command overlap");active=true;writing=accept_write;memory_address=accept_address;delay=accept_write?3:2;beat=0;}
  cycle++;
 }
 void run(){while(received!=target||active||d.bridge_busy)tick();
  if(mode==0){need(LCD==384&&BG==192,"saturated physical command totals");need(received[0]==64&&received[1]==64&&received[3]==64,"BG client starvation");}
  if(mode==1){need(LCD==128&&BG==1&&d.cache_hits==127,"cache hits charged or starved physical work");}
  if(mode==2){need(hold_start&&LCD>held_LCD&&cycle>hold_start+100,"held response blocked unrelated LCD progress");}
  if(mode==3){need(LCD==128&&BG==0,"local errors charged quota or blocked LCD");}
  std::printf("GROUPED_FAIRNESS_CASE mode=%u cycles=%u physical=%u LCD=%u BG=%u cachehits=%u\n",mode,cycle,physical,LCD,BG,unsigned(d.cache_hits));
 }
};
int main(){try{Sim(0,{64,64,384,64}).run();Sim(1,{0,128,128,0}).run();Sim(2,{8,8,48,8}).run();Sim(3,{0,128,128,0}).run();std::printf("GROUPED_FAIRNESS_V2_PASS held_window_progress_checked=1 checks=%u continuous8to4=1 locals_noncharge=1 held_response_isolation=1\n",checks);return 0;}catch(const std::exception&e){std::fprintf(stderr,"GROUPED_FAIRNESS_FAIL %s\n",e.what());return 1;}}
