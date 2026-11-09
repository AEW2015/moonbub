#include "Vhelpers_probe.h"
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
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
static int32_t sign(uint32_t a,unsigned bits){a&=(1U<<bits)-1;return a&(1U<<(bits-1))?int32_t(int64_t(a)-(1LL<<bits)):int32_t(a);}
template<class W>static void set(W&v,unsigned at,unsigned n,uint32_t x){for(unsigned i=0;i<n;++i){const uint32_t mask=1U<<((at+i)%32);v[(at+i)/32]=(v[(at+i)/32]&~mask)|((x>>i&1)?mask:0);}}
template<class W>static int32_t get(const W&v,unsigned at,unsigned n){uint32_t x=0;for(unsigned i=0;i<n;++i)x|=((v[(at+i)/32]>>((at+i)%32))&1)<<i;return sign(x,n);}
static std::vector<uint8_t> bytes(const std::string&s){if(s=="-")return {};std::vector<uint8_t>v;for(size_t n=0;n<s.size();n+=2)v.push_back(uint8_t(std::stoul(s.substr(n,2),nullptr,16)));return v;}
static int32_t word(const std::vector<uint8_t>&v,unsigned n){uint32_t x=0;for(unsigned i=0;i<4;++i)x|=uint32_t(v[n*4+i])<<(8*i);return int32_t(x);}
struct Fixture{std::string name;unsigned error,plane,scale;std::vector<uint8_t>coef,dq,res;};
static std::vector<Fixture> load(const std::string&p){std::ifstream f(p);need(bool(f),"fixture open");std::vector<Fixture>v;std::string l;while(std::getline(f,l)){Fixture a;std::string x,y,z;std::istringstream s(l);s>>a.name>>a.error>>a.plane>>a.scale>>x>>y>>z;need(!s.fail(),"fixture row");a.coef=bytes(x);a.dq=bytes(y);a.res=bytes(z);v.push_back(a);}return v;}
using Tile=std::array<int32_t,64>;
static int basis(unsigned k,unsigned p){static const int b[8][4]={{5793,5793,5793,5793},{8035,6811,4551,1598},{7568,3135,-3135,-7568},{6811,-1598,-8035,-4551},{5793,-5793,-5793,5793},{4551,-8035,1598,6811},{3135,-7568,7568,-3135},{1598,-4551,6811,-8035}};return p<4?b[k][p]:((k&1)?-1:1)*b[k][7-p];}
static int32_t round24(int64_t sum){const int64_t x=sum+8192;const int64_t floor=x>=0?x/16384:-((-x+16383)/16384);return sign(uint32_t(floor),24);}
static bool invalid(const Tile&t){for(int32_t x:t)if(x < -522240||x>522240)return true;return false;}
static Tile inverse(const Tile&t){Tile middle{},out{};for(unsigned r=0;r<8;++r)for(unsigned p=0;p<8;++p){int64_t a=0;for(unsigned k=0;k<8;++k)a+=int64_t(t[r*8+k])*basis(k,p);middle[r*8+p]=round24(a);}for(unsigned c=0;c<8;++c)for(unsigned p=0;p<8;++p){int64_t a=0;for(unsigned k=0;k<8;++k)a+=int64_t(middle[k*8+c])*basis(k,p);out[p*8+c]=round24(a);}return out;}
struct Bench{
 Vhelpers_probe d;uint64_t clocks=0;unsigned id=0,dq_cases=0,id_cases=0,cancels=0,retries=0;std::mt19937 rng;
 explicit Bench(unsigned seed):rng(seed){d.clk=0;d.rst=1;d.dq_abort=d.id_abort=d.dq_in_valid=d.id_in_valid=d.dq_out_ready=d.id_out_ready=0;d.dq_in_id=d.id_in_id=d.dq_chroma=d.dq_scale=d.domain_value=0;d.dq_coeff=VlWide<32>{};d.id_in_tile=VlWide<40>{};tick();d.rst=0;tick();}
 void tick(){d.clk=0;d.eval();d.clk=1;d.eval();++clocks;need(clocks<3000000,"helper watchdog");d.clk=0;d.eval();}
 void setdq(const Fixture&c){d.dq_coeff=VlWide<32>{};for(unsigned n=0;n<64;++n)set(d.dq_coeff,n*16,16,uint16_t(c.coef[2*n]|unsigned(c.coef[2*n+1])<<8));d.dq_chroma=c.plane!=0;d.dq_scale=c.scale;d.dq_in_id=++id;}
 void setid(const Tile&t){d.id_in_tile=VlWide<40>{};for(unsigned n=0;n<64;++n)set(d.id_in_tile,n*20,20,uint32_t(t[n]));d.id_in_id=++id;}
 void acceptdq(const Fixture&c){setdq(c);d.dq_in_valid=1;d.eval();need(d.dq_in_ready,"DQ idle ready");tick();d.dq_in_valid=0;need(d.dq_phase==3&&!d.dq_out_valid,"DQ accepted PREPARE owner");d.dq_coeff=VlWide<32>{};for(unsigned n=0;n<64;++n)set(d.dq_coeff,n*16,16,32767);d.dq_scale=3;d.dq_in_id=0xdeadbeef;}
 void acceptid(const Tile&t){setid(t);d.id_in_valid=1;d.eval();need(d.id_in_ready,"IDCT idle ready");tick();d.id_in_valid=0;need(d.id_phase==10&&!d.id_out_valid,"IDCT accepted PREPARE owner");for(unsigned n=0;n<64;++n)set(d.id_in_tile,n*20,20,524287);d.id_in_id=0xf00dcafe;}
 void run_dq(const Fixture&c){const unsigned expected=id+1;acceptdq(c);for(unsigned n=0;!d.dq_out_valid;++n){need(n<32,"DQ completion watchdog");tick();}need(d.dq_out_id==expected&&bool(d.dq_out_error)==bool(c.error),"DQ id/error");for(unsigned n=0;n<64;++n)need(get(d.dq_out_tile,n*20,20)==(c.error?0:word(c.dq,n)),"DQ frozen golden "+c.name);const auto data=d.dq_out_tile;const auto err=d.dq_out_error;for(unsigned h=0;h<17;++h){tick();need(d.dq_out_valid&&d.dq_out_id==expected&&d.dq_out_error==err,"DQ held qualifier");for(unsigned w=0;w<40;++w)need(d.dq_out_tile[w]==data[w],"DQ held payload");}d.dq_out_ready=1;tick();d.dq_out_ready=0;need(d.dq_in_ready&&!d.dq_out_valid,"DQ retire");++dq_cases;}
 void run_id(const Tile&t){const unsigned expected=id+1;const bool bad=invalid(t);const Tile gold=bad?Tile{}:inverse(t);acceptid(t);for(unsigned n=0;!d.id_out_valid;++n){need(n<512,"IDCT completion watchdog");tick();}need(d.id_out_id==expected&&bool(d.id_out_error)==bad,"IDCT id/error");for(unsigned n=0;n<64;++n)need(get(d.id_out_tile,n*24,24)==gold[n],"IDCT direct matrix golden sample "+std::to_string(n));const auto data=d.id_out_tile;for(unsigned h=0;h<13;++h){tick();need(d.id_out_valid&&d.id_out_id==expected&&bool(d.id_out_error)==bad,"IDCT held qualifier");for(unsigned w=0;w<48;++w)need(d.id_out_tile[w]==data[w],"IDCT held payload");}d.id_out_ready=1;tick();d.id_out_ready=0;need(d.id_in_ready&&!d.id_out_valid,"IDCT retire");++id_cases;}
 void cancel_id(const Tile&t,unsigned phase,bool reset){acceptid(t);for(unsigned n=0;d.id_phase!=phase;++n){need(n<512,"IDCT cancel phase reachability");tick();}if(reset)d.rst=1;else d.id_abort=1;d.eval();need(!d.id_out_valid&&!d.id_in_ready,"IDCT immediate revoke");tick();d.rst=d.id_abort=0;for(unsigned n=0;n<20;++n){tick();need(!d.id_out_valid&&d.id_in_ready&&!d.id_out_error,"IDCT stale owner after kill");for(unsigned w=0;w<48;++w)need(!d.id_out_tile[w],"IDCT killed word exposed");}++cancels;run_id(t);++retries;}
 void cancel_dq(const Fixture&c,unsigned phase,unsigned group,bool reset){acceptdq(c);for(unsigned n=0;d.dq_phase!=phase||(phase==1&&d.dq_group!=group);++n){need(n<32,"DQ cancel phase reachability");tick();}if(reset)d.rst=1;else d.dq_abort=1;d.eval();need(!d.dq_out_valid&&!d.dq_in_ready,"DQ immediate revoke");tick();d.rst=d.dq_abort=0;for(unsigned n=0;n<20;++n){tick();need(!d.dq_out_valid&&d.dq_in_ready&&!d.dq_out_error,"DQ stale owner after kill");for(unsigned w=0;w<40;++w)need(!d.dq_out_tile[w],"DQ killed word exposed");}++cancels;run_dq(c);++retries;}
};
int main(int argc,char**argv){try{need(argc==3,"usage boundary.tsv seed");const unsigned seed=unsigned(std::stoul(argv[2]));const auto cases=load(argv[1]);Bench b(seed);uint64_t domain_checks=0;for(uint32_t x=0;x<(1U<<20);++x){b.d.domain_value=x;b.d.eval();const int32_t s=sign(x,20);need(bool(b.d.domain_bad)==(s < -522240||s>522240),"exhaustive signed20 range equivalence");++domain_checks;}
 const Fixture*good=nullptr;for(const auto&c:cases){b.run_dq(c);if(!c.error){Tile t{};for(unsigned n=0;n<64;++n)t[n]=word(c.dq,n);const Tile gold=inverse(t);for(unsigned n=0;n<64;++n)need(gold[n]==word(c.res,n),"independent matrix vs frozen golden "+c.name);b.run_id(t);if(c.name.find("ac")!=std::string::npos)good=&c;}}
 need(good,"nonzero AC fixture");Tile ac{};for(unsigned n=0;n<64;++n)ac[n]=word(good->dq,n);Tile dc{};dc[0]=522240;
 for(int32_t x:{-524288,-522241,-522240,-1,0,1,522240,522241,524287}){Tile t{};t[0]=x;b.run_id(t);t[63]=x;b.run_id(t);}
 for(unsigned i=0;i<36;++i){Tile t{};for(int32_t&v:t)v=int32_t(b.rng()%1044481)-522240;b.run_id(t);}
 for(bool reset:{false,true}){for(unsigned phase=1;phase<=10;++phase)b.cancel_id((phase>=5&&phase<=8)?dc:ac,phase,reset);for(unsigned g:{0U,4U,7U})b.cancel_dq(*good,1,g,reset);b.cancel_dq(*good,3,0,reset);b.cancel_dq(*good,2,0,reset);}
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"exhaustive_signed20_domain_checks\":"<<domain_checks<<",\"dequant_cases\":"<<b.dq_cases<<",\"idct_cases\":"<<b.id_cases<<",\"cancel_phase_checks\":"<<b.cancels<<",\"clean_retries\":"<<b.retries<<",\"clock_edges\":"<<b.clocks<<",\"independent_matrix_checked_against_frozen_goldens\":true,\"new_preparation_states_executed\":true}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V115_HELPER_TEST_FAIL "<<e.what()<<'\n';return 1;}}
