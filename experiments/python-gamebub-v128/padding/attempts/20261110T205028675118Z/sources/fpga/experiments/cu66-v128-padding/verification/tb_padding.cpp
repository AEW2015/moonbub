#include "Vpadding_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

static void need(bool v,const std::string& s){if(!v)throw std::runtime_error(s);}
using Header=std::array<uint8_t,128>;
static void put(Header&h,unsigned n,uint32_t v){for(unsigned j=0;j<4;++j)h[n+j]=uint8_t(v>>(24-8*j));}
static uint32_t word(const Header&h,unsigned n){return uint32_t(h[n])<<24|uint32_t(h[n+1])<<16|uint32_t(h[n+2])<<8|h[n+3];}
static unsigned half(const Header&h,unsigned n){return unsigned(h[n])*256+h[n+1];}
static uint64_t total(const Header&h){return 132ULL+word(h,36)+word(h,40)+word(h,44)+word(h,48);}
static bool padding(const Header&h){for(unsigned j=116;j<128;++j)if(h[j])return false;return true;}
static Header good(){Header h{};put(h,0,0x43533838);h[4]=1;h[5]=0;h[6]=16;h[7]=3;put(h,8,5);put(h,12,4);put(h,20,5);h[24]=2;h[25]=0xd0;h[26]=1;h[27]=0xe0;h[29]=32;put(h,32,65536);put(h,40,16);put(h,44,110);return h;}
static unsigned expected(const Header&h,uint32_t size,bool sv,uint32_t fid,uint64_t generation){
 const uint64_t gen=uint64_t(word(h,16))<<32|word(h,20);
 if(word(h,0)!=0x43533838U||h[4]!=1||h[6]!=16||half(h,28)!=32||word(h,32)!=65536||(h[5]==1?h[7]!=0:h[7]!=3))return 4;
 if(h[5]>1||half(h,24)!=720||half(h,26)!=480||half(h,30)!=0||!padding(h)||word(h,36)>976||word(h,40)<16||word(h,40)>354||word(h,44)<110||word(h,44)>49152||total(h)!=size)return 5;
 if(word(h,8)==0xffffffffU||gen==0||(sv&&(word(h,8)<=fid||gen<=generation)))return 6;
 if(h[5]==1?word(h,12)!=0xffffffffU:(!sv||word(h,12)!=fid))return 7;
 if(h[5]==1&&word(h,36)!=0)return 8;
 return 0;
}
class Bench{
 public:
 Vpadding_probe d;std::mt19937 rng;uint64_t edges=0,evals=0,headers=0,payload_captures=0,unowned_payload_changes=0,view_checks=0;
 std::array<uint64_t,9> errors{};bool cache_known=false,cache_value=false;uint32_t epoch=0x80000000U;std::ofstream trace;
 explicit Bench(unsigned seed):rng(seed),trace("padding-cases.jsonl"){
  need(bool(trace),"trace open");d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.state=0;d.header_index=0;d.byte_value=0;d.receipt_epoch=epoch;d.size_bytes=258;d.header_packet_total=258;d.snapshot_valid=1;d.snapshot_fid=4;d.snapshot_generation=4;tick();d.reset=0;tick();
 }
 void eval(){d.eval();++evals;need(!d.mismatch,"paired original/candidate padding or error view mismatch");++view_checks;}
 void tick(){
  const bool capture=d.state==4&&d.header_index>=116&&d.header_index<=127;
  const bool killed=d.reset||d.start||d.abort_packet;
  const bool was_known=cache_known,prior=cache_value;
  if(capture){if(d.header_index==116){cache_value=d.byte_value==0;cache_known=true;}else if(cache_known)cache_value=cache_value&&d.byte_value==0;++payload_captures;}
  d.clk=0;eval();d.clk=1;eval();d.clk=0;eval();++edges;
  if(cache_known)need(bool(d.new_cache)==cache_value,"independent exact unreset payload writer/hold check");
  if(capture&&killed&&was_known&&cache_value!=prior)++unowned_payload_changes;
 }
 void cancel(){d.state=0;d.reset=1;d.start=0;d.abort_packet=0;tick();d.reset=0;tick();need(!d.new_owner_complete,"cancel retained eligible cache owner");}
 void configure(const Header&h,bool sv=true,uint32_t sf=4,uint64_t sg=4){d.receipt_epoch=++epoch;d.size_bytes=uint32_t(total(h));d.header_packet_total=total(h);d.snapshot_valid=sv;d.snapshot_fid=sf;d.snapshot_generation=sg;}
 void load(const Header&h,bool sv=true,uint32_t sf=4,uint64_t sg=4){
  configure(h,sv,sf,sg);
  for(unsigned j=0;j<128;++j){
   if((rng()&7U)==0){d.state=(rng()&1U)?3:29;d.header_index=j;d.byte_value=uint8_t(rng());tick();}
   d.state=4;d.header_index=j;d.byte_value=h[j];tick();
  }
  need(d.new_owner_complete,"full twelve-writer owner did not mature");need(bool(d.new_cache)==padding(h),"independent full96 padding fold differs before consume");
  d.state=5;d.header_index=127;tick();const unsigned e=expected(h,d.size_bytes,sv,sf,sg);
  need(d.old_error==e&&d.new_error==e,"original ordered error4..8 classification differs");need(bool(d.old_padding)==padding(h)&&bool(d.new_padding)==padding(h),"original logical padding view differs");
  need(!d.new_owner_complete,"consumed owner not retired");++headers;++errors[e];
  trace<<"{\"case\":"<<headers<<",\"error\":"<<e<<",\"padding\":"<<padding(h)<<",\"epoch\":"<<epoch<<",\"clock\":"<<edges<<"}\n";
  d.state=0;tick();
 }
};
int main(int argc,char**argv){try{
 need(argc==2,"usage: Vpadding_probe seed");const unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed);
 uint64_t exhaustive=0,random_cases=0,cancel_prefix=0,incomplete=0,nonwriter=0,nonpadding=0,last_forward=0;
 for(unsigned pos=116;pos<128;++pos)for(unsigned byte=0;byte<256;++byte){auto h=good();h[pos]=uint8_t(byte);b.load(h);++exhaustive;}
 for(unsigned i=0;i<4096;++i){auto h=good();bool sv=true;uint32_t sf=4;uint64_t sg=4;
  switch(i%12){
   case 0:h[0]^=1;h[116+(b.rng()%12)]=1;break;
   case 1:h[116+(b.rng()%12)]=uint8_t(1+b.rng()%255);put(h,8,0xffffffffU);break;
   case 2:put(h,8,0xffffffffU);break;
   case 3:put(h,12,3);break;
   case 4:h[5]=1;h[7]=0;put(h,12,0xffffffffU);put(h,36,1);break;
   case 5:put(h,16,b.rng());put(h,20,b.rng());sg=(uint64_t(b.rng())<<32)|b.rng();break;
   case 6:put(h,36,b.rng());put(h,40,b.rng());put(h,44,b.rng());put(h,48,b.rng());break;
   case 7:sv=false;break;
   case 8:sf=5;break;
   case 9:put(h,16,0x80000000U);put(h,20,b.rng());sg=0x7fffffffffffffffULL;break;
   case 10:for(unsigned j=116;j<128;++j)h[j]=uint8_t(b.rng());break;
   default:break;
  }
  b.load(h,sv,sf,sg);++random_cases;
 }
 for(unsigned byte:{1U,0U}){auto h=good();h[127]=uint8_t(byte);b.load(h);++last_forward;}
 b.load(good());
 for(unsigned index=116;index<128;++index)for(unsigned flags=1;flags<8;++flags){
  b.cancel();const auto h=good();b.configure(h);
  for(unsigned j=0;j<index;++j){b.d.state=4;b.d.header_index=j;b.d.byte_value=h[j];b.tick();}
  b.d.state=4;b.d.header_index=index;b.d.byte_value=1;b.d.reset=flags&1U;b.d.start=(flags&2U)!=0;b.d.abort_packet=(flags&4U)!=0;b.tick();
  need(!b.d.new_owner_complete,"canceled partial header acquired complete owner");
  b.d.reset=0;b.d.start=0;b.d.abort_packet=0;b.d.state=0;b.tick();
  b.load(good());++cancel_prefix;
 }
 for(unsigned prefix=0;prefix<12;++prefix){b.cancel();b.configure(good());
  for(unsigned n=0;n<prefix;++n){b.d.state=4;b.d.header_index=116+n;b.d.byte_value=0;b.tick();}
  need(!b.d.new_owner_complete,"incomplete prefix incorrectly eligible");++incomplete;
  // No impossible forced HEADER_CHECK consume. Actual complete caller tests
  // separately establish reachability; this is explicit prepared-context proof.
  b.cancel();b.load(good());
 }
 for(unsigned state=0;state<=32;++state)if(state!=4&&state!=5)
  for(uint32_t index:{0U,115U,116U,127U,128U,0xffffffffU})for(unsigned byte:{0U,1U,255U}){
   const bool held=b.d.new_cache;b.d.state=state;b.d.header_index=index;b.d.byte_value=uint8_t(byte);b.tick();need(bool(b.d.new_cache)==held,"nonwriter changed unreset cache payload");++nonwriter;
  }
 for(uint32_t index:{0U,1U,115U,128U,0x80000074U,0xffffffffU}){const bool held=b.d.new_cache;b.d.state=4;b.d.header_index=index;b.d.byte_value=1;b.tick();need(bool(b.d.new_cache)==held,"out-of-range full32 index changed cache payload");++nonpadding;}
 b.cancel();b.load(good());
 need(exhaustive==3072&&random_cases==4096&&cancel_prefix==84&&incomplete==12&&nonwriter==558&&nonpadding==6&&last_forward==2,"coverage count mismatch");
 need(b.unowned_payload_changes==84,"canceled payload updates were not actually observed");for(unsigned e:{0U,4U,5U,6U,7U,8U})need(b.errors[e]>0,"missing ordered error class");
 b.trace.close();need(bool(b.trace),"trace close");b.d.final();
 std::cout<<"{\"type\":\"v128_padding_clock_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"exhaustive_single_byte_cases\":"<<exhaustive<<",\"random_header_cases\":"<<random_cases<<",\"cancel_prefix_cases\":"<<cancel_prefix<<",\"incomplete_prefix_checks\":"<<incomplete<<",\"nonwriter_hold_checks\":"<<nonwriter<<",\"nonpadding_writer_hold_checks\":"<<nonpadding<<",\"last_byte_forwarding_cases\":"<<last_forward<<",\"unowned_canceled_payload_changes\":"<<b.unowned_payload_changes<<",\"completed_headers\":"<<b.headers<<",\"payload_captures\":"<<b.payload_captures<<",\"clock_edges\":"<<b.edges<<",\"equality_evaluations\":"<<b.evals<<",\"view_checks\":"<<b.view_checks<<",\"error_classes\":[";
 for(unsigned i=0;i<b.errors.size();++i){if(i)std::cout<<',';std::cout<<b.errors[i];}std::cout<<"],\"source_kernel\":true,\"actual_full_admission_FSM\":false,\"new_payload_or_owner_forces\":0,\"public_cycle_delta\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V128_PADDING_TEST_FAIL "<<e.what()<<'\n';return 1;}}
