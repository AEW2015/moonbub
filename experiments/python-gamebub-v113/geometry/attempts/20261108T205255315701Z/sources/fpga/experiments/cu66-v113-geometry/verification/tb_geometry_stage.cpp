#include "Vgeometry_stage_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
static void need(bool p,const char*message){if(!p)throw std::runtime_error(message);}
int main(int argc,char**argv){
 Verilated::commandArgs(argc,argv);
 try{
 Vgeometry_stage_probe d;uint64_t rng=argc>1?std::stoull(argv[1]):113001;
 const std::array<unsigned,64> zz={0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63};
 auto tick=[&](){d.clk=0;d.eval();d.clk=1;d.eval();d.clk=0;d.eval();};
 auto random=[&](){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);};
 d.clk=0;d.reset=1;d.start=0;d.abort_context=0;d.state=0;d.context_band=0;d.position=0;d.emitted=0;tick();d.reset=0;
 uint64_t cases=0,cancels=0,stalls=0;
 auto check=[&](uint32_t b,uint32_t n,uint32_t e,unsigned mode){
  d.context_band=b;d.position=n;d.emitted=e;d.state=b==0?1:5;tick();need(d.geometry_bytes_valid&&!d.geometry_valid,"stage one edge");
  if(mode%7==0){tick();need(!d.geometry_valid,"request stall cannot publish geometry");++stalls;}
  if(mode%11==0){d.abort_context=1;tick();d.abort_context=0;need(!d.geometry_valid&&!d.geometry_bytes_valid,"abort invalidates both stages");++cancels;d.state=b==0?1:5;tick();}
  d.state=b==0?2:6;tick();need(d.geometry_valid,"stage two ready E+1");
  const uint32_t divisor=b==1?5:b==2?15:43,offset=b==1?1:b==2?6:21;
  const uint32_t expected=b>=1&&b<=3?(((n/divisor)&65535)<<6)|zz[offset+n%divisor]:(e&65535)<<6;
  need(d.prepared_geometry==expected,"independent full32 division/modulo geometry");
  need(d.geometry_band==b&&d.geometry_position==n&&d.geometry_emitted==(e&65535),"prepared coherent key");
  tick();need(d.prepared_geometry==expected,"E+2 retained");tick();need(d.prepared_geometry==expected,"E+3 earliest consumption");
  d.start=1;tick();d.start=0;need(!d.geometry_valid&&!d.geometry_bytes_valid,"start revokes old key");
  ++cases;
 };
 for(unsigned b=0;b<256;++b)for(uint32_t n:std::array<uint32_t,18>{0,1,4,5,14,15,42,43,65535,65536,327679,983039,2818047,0x7fffffff,0x80000000,0xffffff00,0xfffffffe,0xffffffff})for(uint32_t e:std::array<uint32_t,5>{0,1,65535,65536,0xffffffff})check(b,n,e,unsigned(cases));
 for(unsigned b=1;b<=3;++b)for(unsigned byte=0;byte<4;++byte)for(unsigned v=0;v<256;++v)check(b,uint32_t(v)<<(8*byte),random(),unsigned(cases));
 for(unsigned i=0;i<131072;++i)check(i%3+1,random(),random(),i);
 std::cout<<"{\"status\":\"TEST_PASS\",\"stage_cases\":"<<cases<<",\"random_full32\":131072,\"cancel_cases\":"<<cancels<<",\"request_stall_cases\":"<<stalls<<"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"GEOMETRY_STAGE_FAIL "<<e.what()<<'\n';return 1;}
}
