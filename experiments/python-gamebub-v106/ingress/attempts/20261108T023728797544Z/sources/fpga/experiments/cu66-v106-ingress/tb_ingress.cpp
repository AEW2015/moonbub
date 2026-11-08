#include "Vingress_probe.h"
#include "Vingress_probe___024root.h"
#include "Vingress_probe_br88_context.h"
#include <random>
static void ingress_pre(Vingress_probe&);
static void ingress_post(Vingress_probe&);
#include "historical_pipeline.cpp"
#define OLD(n) r.ingress_probe__DOT__old_dut__DOT__packet_decoder__DOT__synchronous__DOT__ingress__DOT__##n
#define NEW(n) r.ingress_probe__DOT__new_dut__DOT__packet_decoder__DOT__synchronous__DOT__ingress__DOT__##n
#define BOTH(n,v) do{const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
#define CTXO r.__PVT__ingress_probe__DOT__old_dut__DOT__packet_decoder__DOT__synchronous__DOT__ingress__DOT__context_decoder
#define CTXN r.__PVT__ingress_probe__DOT__new_dut__DOT__packet_decoder__DOT__synchronous__DOT__ingress__DOT__context_decoder
#define P(n) CTXN->parser__DOT__##n
#define CBOTH(n,v) do{const auto z=(v);CTXO->n=z;CTXN->n=z;}while(0)
#define PBOTH(n,v) CBOTH(parser__DOT__##n,v)
struct Oracle {
 uint32_t size=0,loaded=0,consumed=0;uint64_t reservoir=0;unsigned available=0;bool active=false,use16=false,serial=false;
 std::array<uint64_t,6> counts{};uint64_t clocks=0,loads=0,prefix_steps=0,suffix_steps=0,starts=0,resets=0,logged=0;std::string phase="prepared";std::ofstream* trace=nullptr;
} oracle;
static void verify(Vingress_probe&d){auto&r=*d.rootp;
 require(d.probe_outputs_equal&&d.probe_private_equal,"actual complete parser pre/post comparison");
 require(P(size_bits)==oracle.size&&P(loaded)==oracle.loaded&&P(consumed)==oracle.consumed,"independent size/loaded/consumed oracle");
 require(P(cached_remaining)==uint32_t(oracle.size-oracle.consumed)&&P(cached_load_remaining)==uint32_t(oracle.size-oracle.loaded),"independent modulo32 cache invariant");
 require(P(reservoir)==oracle.reservoir&&P(available)==oracle.available,"independent reservoir oracle");
 const std::array<uint64_t,6> actual={P(count_cycles),P(count_inputs),P(count_symbols),P(count_bits),P(count_input_wait),P(count_output_stall)};require(actual==oracle.counts,"independent public counter oracle");
}
static void parser_pre(Vingress_probe&d){auto&r=*d.rootp;
 verify(d);const uint32_t rem=oracle.size-oracle.consumed,loadrem=oracle.size-oracle.loaded;
 const unsigned expected=std::min(loadrem,oracle.use16?16U:32U),window=std::min(rem,15U);unsigned zeros=0;bool found=false;
 for(unsigned i=0;i<window;++i){if(!found){if(oracle.available>i&&((oracle.reservoir>>(oracle.available-1-i))&1U))found=true;else ++zeros;}}
 unsigned needed=0,take=0;if(P(state)==1){needed=oracle.serial?1U:window;take=oracle.serial?1U:zeros==15?15U:found?zeros+1:window;}
 else if(P(state)==2){needed=oracle.serial&&P(suffix_left)!=0?1U:P(suffix_left);take=needed;}
 require(P(zeros)==zeros&&bool(P(found_one))==found,"independent prefix rank/window oracle");
 const bool canstep=oracle.available>=needed;
 const bool bad=P(in_bits)!=expected||P(in_bits)==0||bool(P(in_last))!=(uint32_t(oracle.loaded+P(in_bits))==oracle.size)||(P(in_bits)<32&&(P(in_data)&(0xffffffffU>>P(in_bits)))!=0);
 require(bool(P(word_bad))==bad,"independent complete word validation/modular last predicate");
 if(P(reset)||P(stream_start)){oracle.size=P(stream_bits);oracle.loaded=oracle.consumed=0;oracle.reservoir=0;oracle.available=0;oracle.active=!P(reset);oracle.use16=P(word16);oracle.serial=P(serial_mode);oracle.counts.fill(0);oracle.starts+=P(stream_start);oracle.resets+=P(reset);}
 else if(oracle.active){
  ++oracle.counts[0];if(P(out_valid)&&!P(out_ready))++oracle.counts[5];
  if((P(state)==1||P(state)==2)&&needed!=0&&!canstep&&!(P(in_valid)&&P(in_ready))&&rem>=needed)++oracle.counts[4];
  if(P(out_valid)&&P(out_ready)&&P(out_error)==0)++oracle.counts[2];
  if(P(req_valid)&&P(req_ready)){}
  else if(P(in_valid)&&P(in_ready)){++oracle.counts[1];if(!bad){oracle.reservoir=(oracle.reservoir<<P(in_bits))|(uint64_t(P(in_data))>>(32-P(in_bits)));oracle.available+=P(in_bits);oracle.loaded+=P(in_bits);++oracle.loads;}}
  else if((P(state)==1&&!P(out_valid)&&P(failed)==0&&window!=0&&canstep)||(P(state)==2&&!P(out_valid)&&rem>=P(suffix_left)&&canstep)){
   require(take<=oracle.available,"oracle reservoir underflow");oracle.available-=take;const uint64_t mask=oracle.available==64?~uint64_t(0):oracle.available==0?0:((uint64_t(1)<<oracle.available)-1);oracle.reservoir&=mask;oracle.consumed+=take;oracle.counts[3]+=take;
   if(P(state)==1)++oracle.prefix_steps;else ++oracle.suffix_steps;
  }
 }
}


struct CacheOracle {uint32_t cache=0,replay=0;std::array<uint64_t,4> counts{};uint64_t clocks=0,init=0,updates=0,logged=0;unsigned guards=0;uint32_t before_cache=0,before_replay=0,selected_size=0;unsigned bits=0;bool cancel=false,initialize=false,update=false;std::ofstream*trace=nullptr;std::string phase="prepared";} cache;
static void cache_verify(Vingress_probe&d){
 require(d.probe_outputs_equal&&d.probe_ingress_equal&&d.probe_private_equal,"whole pipeline, every ingress port and retained private registers differ");
 require(d.probe_cache==cache.cache&&d.probe_replay==cache.replay,"independent live replay/cache state");
 const std::array<uint64_t,4> actual={d.probe_count_cycles,d.probe_count_inputs,d.probe_count_outputs,d.probe_count_stall};require(actual==cache.counts,"independent ingress counters");
 if(d.probe_live&&!d.probe_cancelled)require(d.probe_cache==uint32_t(d.probe_size-d.probe_replay),"full32 live cache invariant");
 if(d.probe_live){const auto bits=std::min(uint32_t(d.probe_size-d.probe_replay),d.probe_mode16?16U:32U);require(bits==d.probe_ctx_bits&&bool(d.probe_ctx_last)==(uint32_t(d.probe_replay+bits)==d.probe_size),"independent live clamp/last");}
}
static void ingress_pre(Vingress_probe&d){
 cache_verify(d);parser_pre(d);cache.before_cache=cache.cache;cache.before_replay=cache.replay;cache.selected_size=d.probe_size;cache.bits=d.probe_ctx_bits;cache.cancel=d.probe_cancelled;cache.initialize=d.probe_cache_init;cache.update=d.probe_cache_update;cache.guards=unsigned(d.reset)|2U*unsigned(d.start)|4U*unsigned(d.abort_packet);
 if(d.probe_cancelled){cache.cache=cache.replay=0;cache.counts.fill(0);}
 else{
  if(d.probe_state!=0&&d.probe_state!=7&&d.probe_state!=8){++cache.counts[0];if(d.probe_ingress_in_valid&&d.probe_ingress_in_ready)++cache.counts[1];if(d.probe_ingress_out_valid&&d.probe_ingress_out_ready)++cache.counts[2];if(d.probe_ingress_out_valid&&!d.probe_ingress_out_ready)++cache.counts[3];}
  if(d.probe_cache_init){cache.cache=d.probe_size;cache.replay=0;++cache.init;}
  if(d.probe_cache_update){cache.cache-=d.probe_ctx_bits;cache.replay+=d.probe_ctx_bits;++cache.updates;}
 }
}
static void ingress_post(Vingress_probe&d){
 cache_verify(d);verify(d);
 if(cache.trace&&(cache.phase=="prepared"||cache.clocks%256==0||cache.guards)){
  *cache.trace<<"{\"clock\":"<<cache.clocks<<",\"phase\":\""<<cache.phase<<"\",\"cache\":"<<cache.cache<<",\"replay\":"<<cache.replay<<",\"state\":"<<unsigned(d.probe_state)<<",\"live\":"<<bool(d.probe_live)<<",\"size\":"<<d.probe_size<<",\"before_cache\":"<<cache.before_cache<<",\"before_replay\":"<<cache.before_replay<<",\"selected_size\":"<<cache.selected_size<<",\"bits\":"<<cache.bits<<",\"cancel\":"<<cache.cancel<<",\"initialize\":"<<cache.initialize<<",\"update\":"<<cache.update<<",\"guards\":"<<cache.guards<<",\"parser_loaded\":"<<oracle.loaded<<",\"parser_consumed\":"<<oracle.consumed<<",\"parser_reservoir\":"<<oracle.reservoir<<",\"parser_available\":"<<oracle.available<<",\"equal\":true}\n";++cache.logged;
 }
 ++cache.clocks;require(cache.clocks<100000000,"finite clock watchdog");
}
int main(int argc,char**argv){try{
 require(argc==4,"seed trace vectors required");const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed);std::ofstream trace(argv[2]);require(bool(trace),"trace open");cache.trace=&trace;
 Vingress_probe d;auto&r=*d.rootp;d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=46;d.blocks=1;d.epoch=17;d.serial_clear=0;d.write_overlap=0;d.read_prefetch=0;d.tile_overlap=0;d.in_valid=0;d.in_data=0;d.in_last=0;d.out_ready=0;d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=0;
 auto tick=[&](){d.clk=0;d.eval();ingress_pre(d);d.clk=1;d.eval();ingress_post(d);d.clk=0;d.eval();};tick();d.reset=0;
 const std::array<uint32_t,15> boundaries={0,1,7,8,15,16,17,31,32,33,0x7fffffffU,0x80000000U,0xffffffe0U,0xfffffff0U,0xffffffffU};unsigned prepared=0;
 for(uint32_t size:boundaries)for(unsigned band=0;band<4;++band)for(unsigned mode=0;mode<4;++mode)for(unsigned guard=0;guard<8;++guard)for(unsigned action=0;action<3;++action){
  d.reset=1;d.start=0;d.abort_packet=0;tick();d.reset=0;
  const uint32_t rem=action==0?size:std::min(size,uint32_t(1+(rng()%63)));const uint32_t replay=action==0?0:size-rem;
  BOTH(state,action==0?4U:5U);BOTH(context_active,action!=0);BOTH(context_blocks,1U);BOTH(context_epoch,17U);BOTH(size_bytes,46U);BOTH(received,46U);BOTH(band,band);BOTH(sizes[band],size);BOTH(offsets[band],0U);BOTH(counts[band],1U);BOTH(k0s[band],0U);BOTH(k1s[band],band==0?255U:0U);BOTH(mode16,mode&1);BOTH(mode_serial,(mode>>1)&1);BOTH(replay_bits,replay);NEW(cached_replay_remaining)=rem;BOTH(word_valid,action==1);BOTH(replay_word,0U);BOTH(error,0U);BOTH(done,0U);
  CBOTH(state,2U);CBOTH(error,0U);CBOTH(done,0U);CBOTH(size_bits,size);CBOTH(target,1U);
  PBOTH(state,1U);PBOTH(active,1U);PBOTH(size_bits,size);PBOTH(loaded,replay);PBOTH(consumed,0U);PBOTH(cached_remaining,size);PBOTH(cached_load_remaining,rem);PBOTH(use16,mode&1);PBOTH(serial,(mode>>1)&1);
  oracle=Oracle{};oracle.size=size;oracle.loaded=replay;oracle.active=true;oracle.use16=mode&1;oracle.serial=(mode>>1)&1;cache.cache=rem;cache.replay=replay;cache.counts.fill(0);
  d.reset=guard&1;d.start=(guard>>1)&1;d.abort_packet=(guard>>2)&1;
  trace<<"{\"prepare\":true,\"case\":"<<prepared<<",\"size\":"<<size<<",\"remaining\":"<<rem<<",\"replay\":"<<replay<<",\"band\":"<<band<<",\"mode\":"<<mode<<",\"guards\":"<<guard<<",\"action\":"<<action<<"}\n";
  tick();++prepared;
 }
 auto prepared_edges=cache.clocks,prepared_updates=cache.updates,prepared_init=cache.init;d.final();trace<<"{\"model_start\":\"historical-whole-pipeline\"}\n";
 cache=CacheOracle{};cache.trace=&trace;cache.phase="historical";oracle=Oracle{};char*args[]={argv[0],argv[3],argv[1]};require(historical_pipeline_main(3,args)==0,"retained real packet/staging/memory suite failed");
 std::cout<<"{\"type\":\"ingress_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"prepared_cases\":"<<prepared<<",\"prepared_edges\":"<<prepared_edges<<",\"prepared_updates\":"<<prepared_updates<<",\"prepared_initializations\":"<<prepared_init<<",\"historical_edges\":"<<cache.clocks<<",\"historical_updates\":"<<cache.updates<<",\"historical_initializations\":"<<cache.init<<",\"historical_trace_rows\":"<<cache.logged<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"INGRESS_FAIL "<<e.what()<<'\n';return 1;}}
