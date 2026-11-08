#include "Vidct_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool x,const std::string&m){if(!x)throw std::runtime_error(m);}
struct Case{unsigned id=0,error=0;std::array<uint32_t,40> data{};std::array<uint32_t,48> expected{};};
template<size_t N>static void unhex(const std::string&s,std::array<uint32_t,N>&out){need(s.size()==N*8,"hex width");for(unsigned i=0;i<N;++i)out[i]=uint32_t(std::stoul(s.substr(s.size()-8*(i+1),8),nullptr,16));}
static std::vector<Case> read_cases(const std::string&path){std::ifstream f(path);need(bool(f),"open vectors");std::vector<Case> all;std::string a,b;Case c;while(f>>c.id>>a>>b>>c.error){unhex(a,c.data);unhex(b,c.expected);all.push_back(c);}need(all.size()==4303,"fixture count");return all;}
template<size_t N>static uint64_t bits(const VlWide<N>&v,unsigned at,unsigned width){const unsigned w=at/32,s=at%32;uint64_t x=uint64_t(v[w])>>s;if(s+width>32)x|=uint64_t(v[w+1])<<(32-s);if(s+width>64)x|=uint64_t(v[w+2])<<(64-s);return x&((uint64_t(1)<<width)-1);}
static int64_t signed_bits(uint64_t x,unsigned width){return x&(uint64_t(1)<<(width-1))?int64_t(x)-int64_t(uint64_t(1)<<width):int64_t(x);}
static bool dc_only(const Case&c){if(c.data[0]>>20)return false;for(unsigned i=1;i<40;++i)if(c.data[i])return false;return true;}
static bool zero(const Case&c){for(auto x:c.data)if(x)return false;return true;}
class Bench{public:
 Vidct_probe d;std::mt19937 rng;std::ofstream trace;uint64_t clocks=0,muls=0,outputs=0;unsigned states=0;std::array<uint32_t,40> accepted_source{};bool source_owned=false;uint64_t source_owner_checks=0,idle_noise_edges=0;
 explicit Bench(unsigned seed,const std::string&path):rng(seed),trace(path){need(bool(trace),"trace open");d.clk=0;d.rst=1;d.abort_frame=0;d.in_valid=0;d.in_id=0;d.out_ready=0;for(unsigned i=0;i<40;++i)d.in_tile[i]=0;tick();d.rst=0;}
 void tick(){
  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT preedge mismatch");unsigned state=d.verify_state;states|=1U<<state;
  std::array<uint64_t,8> expected{},samples{},basis{};const bool kill=d.rst||d.abort_frame,mul=state==1||state==3||state==5||state==7;
  for(unsigned lane=0;lane<8;++lane){samples[lane]=bits(d.verify_samples,lane*24,24);basis[lane]=bits(d.verify_basis,lane*14,14);expected[lane]=kill?0:mul?(uint64_t(signed_bits(samples[lane],24)*signed_bits(basis[lane],14))&((uint64_t(1)<<38)-1)):bits(d.verify_products,lane*38,38);}
  if(state!=0&&!kill){need(source_owned,"owned IDCT state without accepted source");for(unsigned i=0;i<40;++i)need(d.verify_source_tile[i]==accepted_source[i],"accepted source tile changed during work/hold");++source_owner_checks;}
  if(kill)source_owned=false;
  else if(state==0&&d.in_valid&&d.in_ready){for(unsigned i=0;i<40;++i)accepted_source[i]=d.in_tile[i];source_owned=true;}
  else if(state==9&&d.out_valid&&d.out_ready)source_owned=false;
  const uint32_t cycles=kill?0:state==0&&d.in_valid&&d.in_ready?0:state!=0&&state!=9?d.active_cycles+1:d.active_cycles;
  trace<<"{\"clock\":"<<clocks<<",\"state\":"<<state<<",\"k\":"<<unsigned(d.verify_k)<<",\"group\":"<<unsigned(d.verify_group)<<",\"kill\":"<<kill<<",\"mul\":"<<mul<<",\"rst\":"<<unsigned(d.rst)<<",\"abort\":"<<unsigned(d.abort_frame)<<",\"in_valid\":"<<unsigned(d.in_valid)<<",\"in_ready\":"<<unsigned(d.in_ready)<<",\"out_ready\":"<<unsigned(d.out_ready)<<",\"samples\":[";
  for(unsigned i=0;i<8;++i){if(i)trace<<',';trace<<signed_bits(samples[i],24);}trace<<"],\"basis\":[";for(unsigned i=0;i<8;++i){if(i)trace<<',';trace<<signed_bits(basis[i],14);}trace<<"]";
  d.clk=1;d.eval();need(d.probe_equal,"whole IDCT postedge mismatch");need(d.active_cycles==cycles,"independent active cycle oracle");
  if(d.verify_state!=0){need(source_owned,"postedge owned state without source");for(unsigned i=0;i<40;++i)need(d.verify_source_tile[i]==accepted_source[i],"accepted source tile capture/binding");++source_owner_checks;}
  trace<<",\"products\":[";for(unsigned i=0;i<8;++i){const auto actual=bits(d.verify_products,i*38,38);need(actual==expected[i],"signed24x14 product oracle");if(i)trace<<',';trace<<signed_bits(actual,38);}trace<<"],\"cycles\":"<<d.active_cycles<<",\"next_state\":"<<unsigned(d.verify_state)<<"}\n";
  if(mul&&!kill){++muls;}
  d.clk=0;d.eval();need(d.probe_equal,"whole IDCT falling evaluation mismatch");++clocks;need(clocks<2000000,"clock watchdog");
 }
 void send(const Case&c){need(d.in_ready,"input not ready");for(unsigned i=0;i<40;++i)d.in_tile[i]=c.data[i];d.in_id=c.id;d.in_valid=1;d.out_ready=0;tick();d.in_valid=0;}
 void run(const Case&c){
  send(c);unsigned work=0;
  while(!d.out_valid){need(++work<=130,"tile watchdog");d.in_valid=rng()&1;d.in_id=rng();for(unsigned i=0;i<40;++i)d.in_tile[i]=rng();tick();}
  need(d.out_id==c.id&&d.out_error==c.error,"golden metadata/error");for(unsigned i=0;i<48;++i)need(d.out_tile[i]==c.expected[i],"golden residual mismatch id"+std::to_string(c.id));
  const unsigned expected_cycles=c.error||zero(c)?0:dc_only(c)?4:128;need(d.active_cycles==expected_cycles,"shortcut/full active cycle count");
  for(unsigned stall=0,n=rng()%7;stall<n;++stall){d.in_valid=1;d.out_ready=0;tick();need(d.out_valid&&d.out_id==c.id&&d.active_cycles==expected_cycles,"held output metadata/cycles");for(unsigned i=0;i<48;++i)need(d.out_tile[i]==c.expected[i],"held output changed");}
  d.in_valid=0;d.out_ready=1;tick();d.out_ready=0;++outputs;need(d.in_ready,"output did not release");
 }
 void flush(unsigned guards){d.rst=guards&1;d.abort_frame=(guards&2)!=0;tick();need(!d.out_valid&&!d.out_error&&d.active_cycles==0,"kill did not clear");d.rst=0;d.abort_frame=0;d.in_valid=0;d.clk=0;d.eval();need(d.in_ready,"kill did not idle");}
};
int main(int argc,char**argv){try{
 need(argc==4,"usage vectors seed trace");const auto all=read_cases(argv[1]);const unsigned seed=unsigned(std::stoul(argv[2]));Bench b(seed,argv[3]);const Case*ac=nullptr,*dc=nullptr;
 for(const auto&c:all)if(!c.error&&!zero(c)){if(dc_only(c)&&!dc)dc=&c;if(!dc_only(c)&&!ac)ac=&c;}
 need(ac&&dc,"missing general/DC vectors");unsigned directed=0,abort_mask=0;
 for(unsigned n=0;n<1024;++n){b.d.in_valid=0;b.d.in_id=b.rng();for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.tick();++b.idle_noise_edges;}
 for(unsigned state=0;state<10;++state)for(unsigned guards=1;guards<=3;++guards){
  b.flush(1);if(state!=0){b.send(state>=5&&state<=8?*dc:*ac);unsigned watchdog=0;while(b.d.verify_state!=state){need(++watchdog<=130,"abort state unreachable");b.tick();}}
  b.d.in_valid=1;for(unsigned i=0;i<40;++i)b.d.in_tile[i]=b.rng();b.flush(guards);abort_mask|=1U<<state;b.run(*ac);++directed;
 }
 for(const auto&c:all){for(unsigned n=b.rng()%3;n;--n)b.tick();b.run(c);}
 need(abort_mask==1023&&b.states==1023,"all FSM states coverage");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"tiles\":"<<all.size()<<",\"directed_abort_reset_cases\":"<<directed<<",\"abort_state_mask\":"<<abort_mask<<",\"states\":"<<b.states<<",\"source_owner_checks\":"<<b.source_owner_checks<<",\"idle_noise_edges\":"<<b.idle_noise_edges<<",\"clock_edges\":"<<b.clocks<<",\"multiply_edges\":"<<b.muls<<",\"completed_tiles\":"<<b.outputs<<"}\n";b.d.final();return 0;
}catch(const std::exception&e){std::cerr<<"IDCT_PREFETCH_FAIL "<<e.what()<<'\n';return 1;}}
