#include "Vrice_probe.h"
#include "Vrice_probe___024root.h"
#include <random>
static void rice_pre(Vrice_probe&);
static void rice_post(Vrice_probe&);
#include "historical_rice.cpp"
#define OLD(n) r.rice_probe__DOT__old_dut__DOT__##n
#define NEW(n) r.rice_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do {const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
struct Oracle {
 uint32_t size=0,loaded=0,consumed=0;uint64_t reservoir=0;unsigned available=0;bool active=false,use16=false,serial=false;
 std::array<uint64_t,6> counts{};uint64_t clocks=0,loads=0,prefix_steps=0,suffix_steps=0,starts=0,resets=0,logged=0;std::string phase="prepared";std::ofstream* trace=nullptr;
} oracle;
static void verify(Vrice_probe&d){
 require(d.probe_outputs_equal&&d.probe_internal_equal,"actual complete parser pre/post comparison");
 require(d.probe_guarded_equal,"guarded prefix/suffix semantics");
 require(d.probe_size==oracle.size&&d.probe_loaded==oracle.loaded&&d.probe_consumed==oracle.consumed,"independent size/loaded/consumed oracle");
 require(d.probe_cache_remaining==uint32_t(oracle.size-oracle.consumed)&&d.probe_cache_load==uint32_t(oracle.size-oracle.loaded),"independent modulo32 cache invariant");
 require(d.probe_reservoir==oracle.reservoir&&d.reservoir_bits==oracle.available,"independent reservoir oracle");
 const std::array<uint64_t,6> actual={d.count_cycles,d.count_inputs,d.count_symbols,d.count_bits,d.count_input_wait,d.count_output_stall};require(actual==oracle.counts,"independent public counter oracle");
}
static void rice_pre(Vrice_probe&d){
 verify(d);const uint32_t rem=oracle.size-oracle.consumed,loadrem=oracle.size-oracle.loaded;
 const unsigned expected=std::min(loadrem,oracle.use16?16U:32U),window=std::min(rem,15U);unsigned zeros=0;bool found=false;
 for(unsigned i=0;i<window;++i){if(!found){if(oracle.available>i&&((oracle.reservoir>>(oracle.available-1-i))&1U))found=true;else ++zeros;}}
 unsigned needed=0,take=0;if(d.probe_state==1){needed=oracle.serial?1U:window;take=oracle.serial?1U:zeros==15?15U:found?zeros+1:window;}
 else if(d.probe_state==2){needed=oracle.serial&&d.probe_suffix_left!=0?1U:d.probe_suffix_left;take=needed;}
 const bool canstep=oracle.available>=needed;
 const bool bad=d.in_bits!=expected||d.in_bits==0||bool(d.in_last)!=(uint32_t(oracle.loaded+d.in_bits)==oracle.size)||(d.in_bits<32&&(d.in_data&(0xffffffffU>>d.in_bits))!=0);
 require(bool(d.probe_word_bad)==bad,"independent complete word validation/modular last predicate");
 if(d.reset||d.stream_start){oracle.size=d.stream_bits;oracle.loaded=oracle.consumed=0;oracle.reservoir=0;oracle.available=0;oracle.active=!d.reset;oracle.use16=d.word16;oracle.serial=d.serial_mode;oracle.counts.fill(0);oracle.starts+=d.stream_start;oracle.resets+=d.reset;}
 else if(oracle.active){
  ++oracle.counts[0];if(d.out_valid&&!d.out_ready)++oracle.counts[5];
  if((d.probe_state==1||d.probe_state==2)&&needed!=0&&!canstep&&!(d.in_valid&&d.in_ready)&&rem>=needed)++oracle.counts[4];
  if(d.out_valid&&d.out_ready&&d.out_error==0)++oracle.counts[2];
  if(d.req_valid&&d.req_ready){}
  else if(d.in_valid&&d.in_ready){++oracle.counts[1];if(!bad){oracle.reservoir=(oracle.reservoir<<d.in_bits)|(uint64_t(d.in_data)>>(32-d.in_bits));oracle.available+=d.in_bits;oracle.loaded+=d.in_bits;++oracle.loads;}}
  else if((d.probe_state==1&&!d.out_valid&&d.probe_failed==0&&window!=0&&canstep)||(d.probe_state==2&&!d.out_valid&&rem>=d.probe_suffix_left&&canstep)){
   require(take<=oracle.available,"oracle reservoir underflow");oracle.available-=take;const uint64_t mask=oracle.available==64?~uint64_t(0):oracle.available==0?0:((uint64_t(1)<<oracle.available)-1);oracle.reservoir&=mask;oracle.consumed+=take;oracle.counts[3]+=take;
   if(d.probe_state==1)++oracle.prefix_steps;else ++oracle.suffix_steps;
  }
 }
}
static void rice_post(Vrice_probe&d){
 verify(d);
 if(oracle.trace&&(oracle.phase=="prepared"||oracle.clocks%256==0||d.reset||d.stream_start)){
  *oracle.trace<<"{\"clock\":"<<oracle.clocks<<",\"phase\":\""<<oracle.phase<<"\",\"size\":"<<d.probe_size<<",\"loaded\":"<<d.probe_loaded<<",\"consumed\":"<<d.probe_consumed<<",\"remaining\":"<<d.probe_cache_remaining<<",\"load_remaining\":"<<d.probe_cache_load<<",\"reservoir\":"<<d.probe_reservoir<<",\"available\":"<<unsigned(d.reservoir_bits)<<",\"equal\":true}\n";++oracle.logged;
 }
 ++oracle.clocks;require(oracle.clocks<100000000,"finite clock watchdog");
}
int main(int argc,char**argv){try{
 require(argc==4,"seed trace vectors required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);std::ofstream trace(argv[2]);require(bool(trace),"trace open");oracle.trace=&trace;
 // Independent expected transcripts over every request parameter pair.
 // Legal ordinary and escape encodings are built directly from the bit grammar.
 oracle.phase="parameter";unsigned parameter_cases=0;
 {Sim sim(seed);
  for(bool serial:{false,true})for(bool word16:{false,true})
   for(unsigned k=0;k<32;++k)for(unsigned escape=0;escape<32;++escape) {
    if(k>19||escape>24) {
     sim.start(1,word16,serial);sim.request(k,escape);sim.response(1,0,0);++parameter_cases;
    } else {
     Case ordinary{"parameter:ordinary",1+k,std::vector<uint8_t>((1+k+7)/8,0),{{k,escape,0,1+k}}};
     ordinary.data[0]=0x80;sim.run(ordinary,word16,serial,true);++parameter_cases;
     Case escaped{"parameter:escape",15+escape,std::vector<uint8_t>((15+escape+7)/8,0),{{k,escape,0,15+escape}}};
     sim.run(escaped,word16,serial,true);++parameter_cases;
    }
   }
 }
 const auto parameter_clocks=oracle.clocks;
 oracle=Oracle{};oracle.trace=&trace;
 Vrice_probe d;auto&r=*d.rootp;d.clk=0;d.reset=1;d.stream_start=0;d.stream_bits=0;d.word16=0;d.serial_mode=0;d.in_valid=0;d.in_data=0;d.in_bits=0;d.in_last=0;d.req_valid=0;d.req_k=0;d.req_escape=0;d.out_ready=0;
 auto tick=[&](){d.clk=0;d.eval();rice_pre(d);d.clk=1;d.eval();rice_post(d);d.clk=0;d.eval();};tick();d.reset=0;
 auto prepare=[&](uint32_t size,uint32_t loaded,uint32_t consumed,unsigned state,unsigned available,bool active,bool use16,bool serial,unsigned guards,unsigned bits,bool word,unsigned last_override=2U,uint32_t data_override=0){
  oracle.size=size;oracle.loaded=loaded;oracle.consumed=consumed;oracle.available=available;oracle.reservoir=available?((uint64_t(rng())<<32)|rng())&(available==64?~uint64_t(0):((uint64_t(1)<<available)-1)):0;oracle.active=active;oracle.use16=use16;oracle.serial=serial;oracle.counts.fill(0);oracle.counts[3]=consumed;
  BOTH(size_bits,size);BOTH(loaded,loaded);BOTH(consumed,consumed);BOTH(cached_remaining,size-consumed);BOTH(cached_load_remaining,size-loaded);BOTH(reservoir,available?oracle.reservoir<<(64-available):0);BOTH(available,available);BOTH(active,active);BOTH(use16,use16);BOTH(serial,serial);BOTH(state,state);BOTH(failed,0U);BOTH(out_valid,0U);BOTH(out_value,0U);BOTH(out_consumed,0U);BOTH(out_error,0U);BOTH(k,19U);BOTH(escape_width,24U);BOTH(quotient,15U);BOTH(suffix_left,24U);BOTH(suffix_acc,0U);BOTH(count_cycles,0U);BOTH(count_inputs,0U);BOTH(count_symbols,0U);BOTH(count_bits,consumed);BOTH(count_input_wait,0U);BOTH(count_output_stall,0U);
  // Complete the new private prepared-state tuple. No old check changes.
  NEW(prefix_window)=std::min(uint32_t(size-consumed),uint32_t(15));
  NEW(remaining_nonzero)=uint32_t(size-consumed)!=0;NEW(load_nonzero)=loaded<size;
  d.reset=(guards&1)!=0;d.stream_start=(guards&2)!=0;d.stream_bits=rng();d.word16=use16;d.serial_mode=serial;d.in_valid=word;d.in_bits=bits;d.in_data=data_override;d.in_last=last_override<2U?last_override:uint32_t(loaded+bits)==size;d.req_valid=0;d.req_k=0;d.req_escape=24;d.out_ready=0;tick();
 };
 const std::array<uint32_t,13> boundaries={0U,1U,15U,16U,17U,31U,32U,33U,0x7fffffffU,0x80000000U,0xffffffe0U,0xfffffff0U,0xffffffffU};
 for(uint32_t size:boundaries)for(unsigned mode=0;mode<4;++mode)for(unsigned guard=0;guard<4;++guard){const unsigned bits=mode&1?16U:32U;const uint32_t loaded=size>=bits?size-bits:0;prepare(size,loaded,loaded,0,0,true,mode&1,mode&2,guard,std::min(size-loaded,bits),true);}
 // Successful PREFIX/SUFFIX steps near full32 boundaries retain exactly the
 // old arithmetic, including controls that are prepared rather than protocol-reached.
 for(uint32_t size:boundaries)if(size>=32)for(unsigned state:{1U,2U})for(unsigned mode=0;mode<4;++mode)for(unsigned guard=0;guard<4;++guard)prepare(size,size,size-32,state,32,true,mode&1,mode&2,guard,0,false);
 // Full valid aligned-reservoir domain; every length, PREFIX/SUFFIX,
 // parallel/serial, and start/reset priority. Prepared states supplement the
 // untouched real-interface suite and are never represented as reachability proof.
 for(unsigned available=0;available<=64;++available)
  for(unsigned state:{1U,2U})for(unsigned mode=0;mode<4;++mode)
   for(unsigned guard=0;guard<4;++guard)for(unsigned n=0;n<8;++n)
    prepare(128,128,128-available,state,available,true,mode&1,mode&2,guard,0,false);
 // Full32 boundaries and every 6-bit in_bits encoding, all last/data
 // combinations, and every controller state. Normal guards decide acceptance;
 // no malformed-word priority is assumed by the oracle.
 for(uint32_t size:boundaries)for(unsigned mode=0;mode<4;++mode)
  for(unsigned state=0;state<4;++state)for(unsigned bits=0;bits<64;++bits)
   for(unsigned last=0;last<2;++last)
    for(uint32_t data:{0U,0x80000000U,0x80000001U,0xffffffffU}) {
     const unsigned w=mode&1?16U:32U;const uint32_t loaded=size>=w?size-w:0;
     prepare(size,loaded,loaded,state,0,true,mode&1,mode&2,0,bits,true,last,data);
    }
 // Inactive, cache-consistent arbitrary32 states qualify the modular identity
 // and word-bad equality without asserting a legitimate active stream bound.
 for(unsigned n=0;n<65536;++n){const uint32_t size=rng(),loaded=rng(),consumed=rng();prepare(size,loaded,consumed,n%4,0,false,n&1,n&2,0,n%64,false);}
 const auto prepared=oracle.clocks,prepared_loads=oracle.loads,prepared_prefix=oracle.prefix_steps,prepared_suffix=oracle.suffix_steps,prepared_logs=oracle.logged;
 d.final();trace<<"{\"model_start\":\"historical-generic-rice\"}\n";oracle=Oracle{};oracle.trace=&trace;oracle.phase="historical";
 char* args[]={argv[0],argv[3],argv[1]};require(historical_rice_main(3,args)==0,"generic real-interface suite failed");
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"parameter_cases\":"<<parameter_cases<<",\"parameter_clocks\":"<<parameter_clocks<<",\"prepared_clocks\":"<<prepared<<",\"prepared_loads\":"<<prepared_loads<<",\"prepared_prefix_steps\":"<<prepared_prefix<<",\"prepared_suffix_steps\":"<<prepared_suffix<<",\"prepared_trace_records\":"<<prepared_logs<<",\"historical_clocks\":"<<oracle.clocks<<",\"historical_loads\":"<<oracle.loads<<",\"historical_prefix_steps\":"<<oracle.prefix_steps<<",\"historical_suffix_steps\":"<<oracle.suffix_steps<<",\"historical_trace_records\":"<<oracle.logged<<",\"historical_starts\":"<<oracle.starts<<",\"historical_resets\":"<<oracle.resets<<"}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
