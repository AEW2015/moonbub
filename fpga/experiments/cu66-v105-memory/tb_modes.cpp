#include "Vmode_probe.h"
#include "Vmode_probe___024root.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#define OLD(n) r.mode_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.mode_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do { const auto z=(v); OLD(n)=z; NEW(n)=z; } while(0)
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
static bool hidden(unsigned p,unsigned t){
 if(p)return t>=1046&&t<=1064;
 const std::array<std::array<unsigned,2>,9> intervals={{{633,651},{723,741},{993,1011},{1083,1101},{4071,4110},{4161,4200},{4251,4290},{4431,4460},{4521,4550}}};
 for(const auto& x:intervals)if(t>=x[0]&&t<=x[1])return true;
 return false;
}
struct Case {unsigned state=0,p=0,t=0,index=0,end=16,tag=0,bits=8,mixed=1,bit=0,guard=0,addr=0;bool lookup=true;};
int main(int argc,char** argv){try{
 need(argc==3,"seed and trace path required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);
 Vmode_probe d;auto&r=*d.rootp;std::ofstream trace(argv[2]);need(bool(trace),"trace open");
 std::array<uint8_t,8100> modes{};
 d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.cache_write=0;d.cache_index=0;d.cache_data=0;d.replay_req=0;d.replay_addr=0;d.lookup_req=0;d.lookup_tile=0;d.lookup_cell=0;d.packet_bytes=49152;d.epoch=seed;d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;d.in_valid=0;d.in_last=0;d.in_data=0;d.receipt_ready=0;
 d.eval();d.clk=1;d.eval();d.clk=0;d.eval();d.reset=0;
 for(unsigned i=0;i<8100;++i){modes[i]=uint8_t(((i*131U+(i>>3))^seed)&3U);OLD(modes)[i]=modes[i];NEW(modes)[i]=modes[i];}
 for(unsigned i=0;i<1350;++i){BOTH(scales[i],i%3U);}
 BOTH(lookup_mode,3U);BOTH(lookup_scale,2U);unsigned held=3,cases=0,reads=0,writes=0,guarded=0;std::array<unsigned,5> branches{};
 auto run=[&](const Case& c){
  need(c.addr<8100,"valid lookup domain");d.clk=0;d.reset=(c.guard&1)!=0;d.start=(c.guard&2)!=0;d.abort_packet=(c.guard&4)!=0;
  d.lookup_req=c.lookup;d.lookup_tile=c.addr;d.lookup_cell=c.addr%1350;
  BOTH(state,c.state);BOTH(plane,c.p);BOTH(tile,c.t);BOTH(active_index,c.index);BOTH(group_end,c.end);BOTH(group_tag,c.tag);BOTH(bits_left,c.bits);BOTH(mixed_bit,c.mixed);BOTH(bit_cache,c.bit?128U:0U);BOTH(group_visible,16U);BOTH(mixed_ones,5U);BOTH(tag_second,0U);BOTH(first_tag_bit,0U);BOTH(mode_cursor,128U);BOTH(mode_bytes,64U);BOTH(size_bytes,49152U);
  d.eval();need(d.probe_outputs_equal,"preedge public output mismatch");need(d.lookup_mode==held,"lookup changed without clock");
  int branch=-1;unsigned wi=0,wd=0;const unsigned base=c.p==0?0U:c.p==1?5400U:6750U;const unsigned count=c.p==0?5400U:1350U;
  if(c.guard==0){
   if(c.state==31&&c.index!=8100){branch=0;wi=c.index&8191U;wd=1;}
   else if(c.state==6&&c.t!=count){branch=1;wi=(base+c.t)&8191U;wd=hidden(c.p,c.t)?1U:2U;}
   else if(c.state==8&&c.bits!=0&&c.mixed){branch=2;wi=(base+c.t)&8191U;wd=c.bit?2U:0U;}
   else if(c.state==10&&c.t!=c.end){
    if(hidden(c.p,c.t)||c.tag==0){branch=3;wi=(base+c.t)&8191U;wd=hidden(c.p,c.t)?1U:0U;}
    else if(c.tag==1){branch=4;wi=(base+c.t)&8191U;wd=2;}
   }
  }
  const bool read=c.lookup&&c.state==26&&c.guard==0;
  if(read){held=modes[c.addr];++reads;}
  if(branch>=0){need(wi<8100,"valid write domain");modes[wi]=uint8_t(wd);++writes;++branches[unsigned(branch)];}
  if(c.guard)++guarded;
  d.clk=1;d.eval();need(d.probe_outputs_equal,"postedge public output mismatch");need(d.lookup_mode==held,"independent sync-read and hold oracle");need(bool(d.lookup_rsp_valid)==read,"lookup response guard oracle");
  if(branch>=0)need(OLD(modes)[wi]==modes[wi]&&NEW(modes)[wi]==modes[wi],"independent mode write oracle");
  // Check the only potentially touched word even when its write is suppressed.
  const unsigned touched=c.state==31?(c.index&8191U):((base+c.t)&8191U);
  if(touched<8100)need(OLD(modes)[touched]==modes[touched]&&NEW(modes)[touched]==modes[touched],"immediate guard/no-write retention oracle");
  trace<<"{\"case\":"<<cases<<",\"state\":"<<c.state<<",\"plane\":"<<c.p<<",\"tile\":"<<c.t<<",\"index\":"<<c.index<<",\"end\":"<<c.end<<",\"tag\":"<<c.tag<<",\"bits\":"<<c.bits<<",\"mixed\":"<<c.mixed<<",\"bit\":"<<c.bit<<",\"guard\":"<<c.guard<<",\"lookup\":"<<c.lookup<<",\"addr\":"<<c.addr<<",\"branch\":"<<branch<<",\"write_addr\":"<<wi<<",\"write_data\":"<<wd<<",\"read\":"<<read<<",\"held\":"<<held<<",\"equal\":true}\n";
  ++cases;d.clk=0;d.eval();need(cases<300000,"finite clock watchdog");
 };
 auto scan=[&](){for(unsigned i=0;i<8100;++i){Case c;c.state=26;c.addr=i;run(c);}};
 scan(); // all initialized values, including otherwise ungenerated value 3
 for(unsigned i=0;i<=8100;++i){Case c;c.state=31;c.index=i;c.addr=i%8100;run(c);}
 scan();
 for(unsigned p=0;p<3;++p)for(unsigned t=0;t<=(p?1350U:5400U);++t){Case c;c.state=6;c.p=p;c.t=t;c.addr=(p==0?0U:p==1?5400U:6750U)+(t%(p?1350U:5400U));run(c);}
 scan();
 for(unsigned tag=0;tag<4;++tag){
  for(unsigned p=0;p<3;++p)for(unsigned t=0;t<(p?1350U:5400U);++t){Case c;c.state=10;c.p=p;c.t=t;c.end=t+1;c.tag=tag;c.addr=(p==0?0U:p==1?5400U:6750U)+t;run(c);}
 scan();
 }
 for(unsigned bit=0;bit<2;++bit){for(unsigned p=0;p<3;++p)for(unsigned t=0;t<(p?1350U:5400U);++t){Case c;c.state=8;c.p=p;c.t=t;c.bit=bit;c.addr=(p==0?0U:p==1?5400U:6750U)+t;run(c);}
 scan();}
 // Exhaustive state/guard combinations and branch boundary cases. Prepared
 // states are verification-only; these are not complete packet transactions.
 for(unsigned s=0;s<=32;++s)for(unsigned g=0;g<8;++g)for(unsigned k=0;k<16;++k){Case c;c.state=s;c.guard=g;c.p=k%3;c.t=(k*373U)%(c.p?1350U:5400U);c.index=k&1?8100U:k*539U;c.tag=k%4;c.end=k&1?c.t:c.t+1;c.bits=k&2?0U:8U;c.mixed=k&4?0U:1U;c.bit=k&8?1U:0U;c.lookup=k&1;c.addr=rng()%8100;run(c);}
 for(unsigned k=0;k<8192;++k){Case c;const unsigned states[]={0,6,8,10,26,31};c.state=states[rng()%6];c.guard=rng()%8;c.p=rng()%3;c.t=rng()%(c.p?1350U:5400U);c.index=rng()%8101;c.tag=rng()%4;c.end=(rng()&1)?c.t:c.t+1;c.bits=(rng()&1)?8U:0U;c.mixed=rng()%2;c.bit=rng()%2;c.lookup=rng()%2;c.addr=rng()%8100;run(c);}
 scan();
 for(unsigned i=0;i<8100;++i){need(OLD(modes)[i]==modes[i]&&NEW(modes)[i]==modes[i],"final complete mode store oracle");trace<<"{\"final_addr\":"<<i<<",\"value\":"<<unsigned(modes[i])<<"}\n";}
 for(unsigned n:branches)need(n>0,"missing write branch");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"clock_edges\":"<<cases+1<<",\"reads\":"<<reads<<",\"writes\":"<<writes<<",\"guarded_cases\":"<<guarded<<",\"write_branches\":["<<branches[0]<<","<<branches[1]<<","<<branches[2]<<","<<branches[3]<<","<<branches[4]<<"],\"final_mode_entries\":8100}\n";
 d.final();return 0;
 }catch(const std::exception& e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
