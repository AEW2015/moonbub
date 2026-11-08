#include "Vingress_probe.h"
#include "Vingress_probe___024root.h"
#include "Vingress_probe_packet_original.h"
#include "Vingress_probe_packet_candidate.h"
#include <random>
static void ingress_pre(Vingress_probe&);
static void ingress_post(Vingress_probe&);
#include "historical_pipeline.cpp"
#define OLD(n) r.__PVT__ingress_probe__DOT__old_dut__DOT__packet_decoder->synchronous__DOT__ingress__DOT__##n
#define NEW(n) r.__PVT__ingress_probe__DOT__new_dut__DOT__packet_decoder->synchronous__DOT__ingress__DOT__##n
#define BOTH(n,v) do{const auto z=(v);OLD(n)=z;NEW(n)=z;}while(0)
#define P(n) NEW(context_decoder__DOT__parser__DOT__##n)

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
  BOTH(context_decoder__DOT__state,2U);BOTH(context_decoder__DOT__error,0U);BOTH(context_decoder__DOT__done,0U);BOTH(context_decoder__DOT__size_bits,size);BOTH(context_decoder__DOT__target,1U);
  BOTH(context_decoder__DOT__parser__DOT__state,1U);BOTH(context_decoder__DOT__parser__DOT__active,1U);BOTH(context_decoder__DOT__parser__DOT__size_bits,size);BOTH(context_decoder__DOT__parser__DOT__loaded,replay);BOTH(context_decoder__DOT__parser__DOT__consumed,0U);BOTH(context_decoder__DOT__parser__DOT__cached_remaining,size);BOTH(context_decoder__DOT__parser__DOT__cached_load_remaining,rem);BOTH(context_decoder__DOT__parser__DOT__use16,mode&1);BOTH(context_decoder__DOT__parser__DOT__serial,(mode>>1)&1);
  oracle=Oracle{};oracle.size=size;oracle.loaded=replay;oracle.active=true;oracle.use16=mode&1;oracle.serial=(mode>>1)&1;cache.cache=rem;cache.replay=replay;cache.counts.fill(0);
  d.reset=guard&1;d.start=(guard>>1)&1;d.abort_packet=(guard>>2)&1;
  trace<<"{\"prepare\":true,\"case\":"<<prepared<<",\"size\":"<<size<<",\"remaining\":"<<rem<<",\"replay\":"<<replay<<",\"band\":"<<band<<",\"mode\":"<<mode<<",\"guards\":"<<guard<<",\"action\":"<<action<<"}\n";
  tick();++prepared;
 }
 auto prepared_edges=cache.clocks,prepared_updates=cache.updates,prepared_init=cache.init;d.final();trace<<"{\"model_start\":\"historical-whole-pipeline\"}\n";
 cache=CacheOracle{};cache.trace=&trace;cache.phase="historical";oracle=Oracle{};char*args[]={argv[0],argv[3],argv[1]};require(historical_pipeline_main(3,args)==0,"retained real packet/staging/memory suite failed");
 std::cout<<"{\"type\":\"ingress_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"prepared_cases\":"<<prepared<<",\"prepared_edges\":"<<prepared_edges<<",\"prepared_updates\":"<<prepared_updates<<",\"prepared_initializations\":"<<prepared_init<<",\"historical_edges\":"<<cache.clocks<<",\"historical_updates\":"<<cache.updates<<",\"historical_initializations\":"<<cache.init<<",\"historical_trace_rows\":"<<cache.logged<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"INGRESS_FAIL "<<e.what()<<'\n';return 1;}}
