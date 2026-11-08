#include "Vdequant_probe.h"
#include "verilated.h"
#include "generated_constants.hpp"
#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
static void need(bool value,const std::string& why){if(!value)throw std::runtime_error(why);}
using Coeff=std::array<int16_t,64>;
struct Bench{
 Vdequant_probe d;std::mt19937 random;std::ofstream trace;unsigned state=0,group=0;uint32_t id=0;bool error=false;Coeff owned{};unsigned chroma=0,scale=0;std::array<uint32_t,64> visible{};
 uint64_t edges=0,accepted=0,retired=0,discarded=0,multiply_edges=0,held_edges=0,kills=0,idle_invalid=0,owned_noise=0;
 Bench(unsigned seed,const char*path):random(seed),trace(path){need(bool(trace),"trace open");d.clk=0;d.rst=1;d.abort_i=0;d.in_valid=0;d.out_ready=0;d.in_id=0;d.in_chroma=0;d.in_scale_code=0;for(unsigned i=0;i<32;++i)d.in_coefficients[i]=0;tick();d.rst=0;}
 static std::string hex(const uint32_t*data,unsigned n){std::ostringstream s;s<<std::hex<<std::setfill('0');for(unsigned i=n;i>0;i--)s<<std::setw(8)<<data[i-1];return s.str();}
 uint32_t output(unsigned i)const{const unsigned bit=i*20,word=bit/32,shift=bit%32;uint64_t x=d.out_dequantized[word];if(word+1<40)x|=uint64_t(d.out_dequantized[word+1])<<32;return uint32_t(x>>shift)&0xfffffU;}
 void check(){const bool kill=d.rst||d.abort_i;need(!d.mismatch,"all public old/new outputs differ");need(bool(d.in_ready)==(state==0&&!kill),"independent ready");need(bool(d.out_valid)==(state==2&&!kill),"independent valid");need(d.out_id==id&&bool(d.out_error)==error,"public id/error including invalid cycles");for(unsigned i=0;i<64;i++)need(output(i)==visible[i],"public partial/held/reset dequant data word="+std::to_string(i)+" edge="+std::to_string(edges));}
 void poison(){for(unsigned i=0;i<32;++i)d.in_coefficients[i]=uint32_t(random());d.in_id=uint32_t(random());d.in_chroma=random()%2;d.in_scale_code=random()%4;d.in_valid=random()%2;}
 void offer(const Coeff&c,unsigned chr,unsigned sc,uint32_t identifier){for(unsigned i=0;i<32;i++)d.in_coefficients[i]=uint32_t(uint16_t(c[i*2]))|(uint32_t(uint16_t(c[i*2+1]))<<16);d.in_chroma=chr;d.in_scale_code=sc;d.in_id=identifier;d.in_valid=1;}
 void tick(){
  d.clk=0;d.eval();check();const bool kill=d.rst||d.abort_i;const bool take=d.in_valid&&d.in_ready;const bool pop=d.out_valid&&d.out_ready;const unsigned oldstate=state;
  std::string input=take?hex(d.in_coefficients.data(),32):"-";
  if(kill){if(state!=0)++discarded;state=0;group=0;id=0;error=false;visible.fill(0);++kills;}
  else if(state==0){if(take){++accepted;id=d.in_id;chroma=d.in_chroma;scale=d.in_scale_code;bool zero=true;error=scale==3;for(unsigned i=0;i<64;i++){owned[i]=int16_t(uint16_t(d.in_coefficients[i/2]>>(16*(i%2))));zero=zero&&owned[i]==0;error=error||owned[i]<-2048||owned[i]>2048;}group=0;if(error||zero){visible.fill(0);state=2;}else state=1;}else ++idle_invalid;}
  else if(state==1){for(unsigned i=group*8;i<group*8+8;i++)visible[i]=uint32_t(int32_t(owned[i])*cu66::QTABLES[chroma][scale][i/8][i%8])&0xfffffU;++multiply_edges;if(group==7)state=2;else ++group;}
  else if(pop){state=0;++retired;}else ++held_edges;
  if(oldstate!=0)++owned_noise;
  d.clk=1;d.eval();check();
  trace<<edges<<','<<unsigned(d.rst)<<','<<unsigned(d.abort_i)<<','<<take<<','<<pop<<','<<unsigned(d.out_ready)<<','<<unsigned(d.in_ready)<<','<<unsigned(d.out_valid)<<','<<d.in_id<<','<<unsigned(d.in_chroma)<<','<<unsigned(d.in_scale_code)<<','<<input<<','<<d.out_id<<','<<unsigned(d.out_error)<<','<<hex(d.out_dequantized.data(),40)<<'\n';
  d.clk=0;d.eval();check();++edges;need(edges<2000000,"dequant finite watchdog");
 }
 void frame(const Coeff&c,unsigned chr,unsigned sc,uint32_t identifier){need(state==0,"frame IDLE precondition");offer(c,chr,sc,identifier);d.out_ready=0;tick();need(state!=0,"accepted transaction missing");for(unsigned watchdog=0;watchdog<64;watchdog++){poison();d.out_ready=random()%3!=0;tick();if(state==0){d.in_valid=0;return;}}throw std::runtime_error("frame progress watchdog");}
};
int main(int argc,char**argv){try{
 need(argc==3,"seed and trace required");const unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed,argv[2]);uint32_t identifier=0;
 Coeff c{};
 for(unsigned chr=0;chr<2;chr++)for(unsigned scale=0;scale<4;scale++)for(unsigned at=0;at<64;at++)for(int value:{-32768,-2049,-2048,-1,0,1,2048,2049,32767}){c.fill(0);c[at]=int16_t(value);b.frame(c,chr,scale,identifier++);}
 for(unsigned n=0;n<2048;n++){for(auto&v:c)v=int16_t(int(b.random()%4097)-2048);if(n%17==0)c.fill(0);if(n%11==0)c[b.random()%64]=int16_t(2049);b.frame(c,b.random()%2,b.random()%4,identifier++);}
 // Reset/abort in every multiply group and held-output state. All public
 // outputs remain checked even with invalid or changing raw inputs.
 for(unsigned mask=1;mask<4;mask++)for(unsigned phase=0;phase<10;phase++){
  c.fill(1);b.offer(c,phase%2,phase%3,identifier++);b.d.out_ready=0;b.tick();for(unsigned i=0;i<phase&&b.state==1;i++){b.poison();b.d.out_ready=0;b.tick();}
  b.d.rst=mask&1;b.d.abort_i=(mask&2)!=0;for(unsigned k=0;k<3;k++){b.poison();b.tick();}b.d.rst=0;b.d.abort_i=0;b.d.in_valid=0;b.d.out_ready=1;b.tick();b.frame(c,0,1,identifier++);
 }
 for(unsigned n=0;n<512;n++){b.poison();b.d.in_valid=0;b.d.rst=n%5==0;b.d.abort_i=n%7==0;b.tick();}b.d.rst=0;b.d.abort_i=0;b.d.in_valid=0;b.tick();
 need(b.accepted==b.retired+b.discarded,"accepted/retired/reset conservation");need(b.multiply_edges>5000&&b.held_edges>100&&b.kills>100&&b.idle_invalid>100,"coverage floor");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"edges\":"<<b.edges<<",\"accepted\":"<<b.accepted<<",\"retired\":"<<b.retired<<",\"discarded\":"<<b.discarded<<",\"multiply_edges\":"<<b.multiply_edges<<",\"held_edges\":"<<b.held_edges<<",\"kill_edges\":"<<b.kills<<",\"idle_invalid_edges\":"<<b.idle_invalid<<",\"owned_input_noise_edges\":"<<b.owned_noise<<"}\n";
 b.d.final();return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
