#include "Vcu71_ab38_decoder_cfgpipe.h"
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
 std::printf("CFG_MODULO_EXHAUSTIVE_PASS checks=%llu valid=%u rejected=%u abort_positions=17\n",(unsigned long long)checks,valid,rejected); return 0;
}catch(const std::exception&e){std::fprintf(stderr,"CFG_MODULO_FAIL %s\n",e.what());return 1;}}
