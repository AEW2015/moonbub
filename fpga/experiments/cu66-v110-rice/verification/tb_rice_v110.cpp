// Additive inactive-state check. The complete inherited parser/golden/oracle
// suite executes first without edits or weaker stored-register comparisons.
#define main inherited_rice_main
#include "tb_rice.cpp"
#undef main
int main(int argc,char**argv){try{
 require(inherited_rice_main(argc,argv)==0,"complete inherited Rice suite");
 const unsigned seed=unsigned(std::stoul(argv[1]));std::mt19937 rng(seed^0xa510U);
 std::ofstream trace(std::string(argv[2])+"-unowned.jsonl");require(bool(trace),"unowned trace open");
 Vrice_probe d;auto&r=*d.rootp;unsigned cases=0;unsigned differing_unused_ranks=0;
 for(unsigned available=0;available<=64;++available)for(unsigned state=0;state<4;++state)
  for(unsigned mode=0;mode<4;++mode)for(unsigned long_window=0;long_window<2;++long_window)for(unsigned n=0;n<4;++n){
   const uint64_t raw=(uint64_t(rng())<<32)|rng();
   const uint32_t consumed=long_window?0:128-available;
   oracle=Oracle{};oracle.size=128;oracle.loaded=128;oracle.consumed=consumed;oracle.available=available;
   oracle.reservoir=available==0?0:available==64?raw:raw>>(64-available);
   oracle.active=false;oracle.use16=mode&1;oracle.serial=mode&2;oracle.counts[3]=consumed;
   BOTH(size_bits,128U);BOTH(loaded,128U);BOTH(consumed,consumed);
   BOTH(cached_remaining,128-consumed);BOTH(cached_load_remaining,0U);
   BOTH(reservoir,raw);BOTH(available,available);BOTH(active,0U);BOTH(use16,mode&1);BOTH(serial,(mode&2)!=0);
   BOTH(state,state);BOTH(failed,0U);BOTH(out_valid,0U);BOTH(out_value,0U);BOTH(out_consumed,0U);BOTH(out_error,0U);
   BOTH(k,19U);BOTH(escape_width,24U);BOTH(quotient,15U);BOTH(suffix_left,24U);BOTH(suffix_acc,0U);
   BOTH(count_cycles,0U);BOTH(count_inputs,0U);BOTH(count_symbols,0U);BOTH(count_bits,consumed);
   BOTH(count_input_wait,0U);BOTH(count_output_stall,0U);
   d.clk=0;d.reset=0;d.stream_start=0;d.stream_bits=128;d.word16=mode&1;d.serial_mode=(mode&2)!=0;
   d.in_valid=0;d.in_bits=0;d.in_data=rng();d.in_last=0;d.req_valid=0;d.req_k=0;d.req_escape=24;d.out_ready=0;
   d.eval();rice_pre(d);
   if(OLD(prefix_rank)!=NEW(prefix_rank))++differing_unused_ranks;
   d.clk=1;d.eval();rice_post(d);d.clk=0;d.eval();verify(d);
   require(OLD(reservoir)==raw&&NEW(reservoir)==raw,"inactive raw unowned reservoir retained");
   trace<<"{\"case\":"<<cases<<",\"available\":"<<available<<",\"state\":"<<state
        <<",\"serial\":"<<bool(mode&2)<<",\"long_window\":"<<long_window<<",\"raw\":"<<raw<<"}\n";
   ++cases;
  }
 require(cases==8320&&differing_unused_ranks>100,"arbitrary unowned-bit coverage");
 std::cout<<"{\"type\":\"inactive_unowned_reservoir_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
          <<",\"cases\":"<<cases<<",\"differing_unused_ranks\":"<<differing_unused_ranks<<"}\n";
 d.final();return 0;
}catch(const std::exception&e){std::cerr<<"RICE_UNOWNED_FAIL "<<e.what()<<'\n';return 1;}}
