#include "Vmeta_stage_probe.h"
#include "verilated.h"
#include <cstdint>
#include <stdexcept>

// The included frozen bench bytes are unchanged. Every one of its eval calls
// gains an unconditional exact old/new comparison, including invalid cycles.
class DomainPairAdapter:public Vmeta_stage_probe {
public:
 inline static uint64_t paired_evaluations=0;
 void eval(){Vmeta_stage_probe::eval();++paired_evaluations;if(mismatch)throw std::runtime_error("V116B exact all-public paired evaluation");}
};
#define Vmeta_stage_probe DomainPairAdapter
#define main frozen_stage_main
#include "tb_stage.frozen.cpp"
#undef main
#undef Vmeta_stage_probe

static void domain_suite(unsigned seed,const std::string &path){
 Bench b(seed,path.c_str());
 bool seen=false;Token held{};
 uint64_t domain_values=0,raw_checks=0,kill_cases=0,edges=0;
 auto check_raw=[&](){
  if(seen){
   require(b.output()==held,"initialized raw payload must hold even while invalid or killed");
   require(bool(b.d.out_metadata_bad)==metadata_bad(held),"initialized raw metadata flag vs independent integer oracle");
   require(bool(b.d.out_domain_bad)==domain_bad(held),"initialized raw signed16 domain flag vs independent integer oracle");
   ++raw_checks;
  }
 };
 auto tick=[&](){
  b.d.clk=0;b.d.eval();check_raw();
  const Token offered=b.input();const Event e=b.tick();
  if(e.push){held=offered;seen=true;}
  check_raw();require(++edges<2000000,"V116B finite focused edge watchdog");return e;
 };
 b.begin();b.static_mode=true;b.d.in_valid=1;b.d.out_ready=1;
 for(unsigned scale=0;scale<4;++scale)for(unsigned bits=0;bits<65536;++bits){
  // The bit-to-plane/tile mapping covers every helper input repeatedly while
  // metadata, epoch/child and payload all move independently of valid flags.
  Token t{seed^bits,~seed+bits,bits>>14,scale,bits,bits&8191U,(bits*37U)&2047U,bits&63U,bits};
  b.offer(t);require(tick().push,"exhaustive signed16/qscale replacement");++domain_values;
 }
 b.d.in_valid=0;require(tick().pop,"exhaustive final output pop");
 // Raw outputs are still part of the public contract after the last pop.
 for(unsigned n=0;n<8;++n){b.offer(b.token());tick();}
 const std::array<unsigned,10> limits{{0U,0x07ffU,0x0800U,0x0801U,0xf7ffU,0xf800U,0xf801U,0xffffU,0x7fffU,0x8000U}};
 for(unsigned scale=0;scale<4;++scale)for(unsigned value:limits)for(unsigned phase=0;phase<6;++phase)for(unsigned mask=1;mask<8;++mask){
  b.begin();check_raw();
  Token a{0xffffffffU,seed,0,scale,65535U,5399U,1349U,63U,value};
  Token foreign{0U,~seed,3U,scale^3U,0U,8191U,2047U,0U,value^65535U};
  b.offer(a);b.d.in_valid=1;b.d.out_ready=0;
  if(phase>0)require(tick().push,"directed boundary token accepted");
  if(phase==1){b.offer(foreign);for(unsigned n=0;n<7;++n)require(!tick().push,"stalled foreign tuple overwrote owner");}
  if(phase==2){b.offer(foreign);b.d.input_done=1;require(!tick().push&&b.pending_final,"final stalled offer owner");for(unsigned n=0;n<3;++n)tick();}
  if(phase==3){b.d.in_valid=0;b.d.out_ready=1;require(tick().pop,"invalid raw hold setup");}
  if(phase==4){b.d.in_valid=0;b.d.input_done=1;tick();b.d.out_ready=1;tick();b.d.input_done=0;tick();require(b.d.output_done,"done raw hold setup");}
  if(phase==5){b.offer(foreign);b.d.out_ready=1;}
  b.d.reset=mask&1U;b.d.start=(mask&2U)!=0;b.d.cancel=(mask&4U)!=0;
  const Event kill=tick();require(!kill.push&&!kill.pop&&!kill.done,"kill priority and raw held tuple");
  b.d.reset=0;b.d.start=0;b.d.cancel=0;b.d.in_valid=0;b.d.input_done=0;b.d.out_ready=1;
  for(unsigned n=0;n<3;++n){const Event e=tick();require(!e.pop&&!e.done,"late owner/fence after kill");}
  ++kill_cases;
  // Clean retry recaptures owner and domain without relying on cold reset.
  b.begin();check_raw();b.offer(foreign);b.d.in_valid=1;b.d.out_ready=1;require(tick().push,"retry capture");
  b.d.in_valid=0;require(tick().pop,"retry output");b.d.input_done=1;tick();require(tick().done,"retry done fence");b.d.input_done=0;
 }
 b.static_mode=false;
 require(domain_values==262144&&kill_cases==1680&&raw_checks>500000,"complete focused domain and raw hold coverage");
 require(b.pushes==b.pops+b.discarded+b.queue.size(),"focused accepted tuple conservation");
 std::cout<<"{\"type\":\"v116b_domain_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"signed16_qscale_values\":"<<domain_values
          <<",\"warm_kill_cases\":"<<kill_cases<<",\"raw_checks\":"<<raw_checks<<",\"focused_edges\":"<<edges<<",\"paired_evaluations\":"<<DomainPairAdapter::paired_evaluations<<"}\n";
 b.d.final();
}

int main(int argc,char **argv){
 try{
  require(argc==4,"seed transcript legacy-exhaustive-mode required");
  domain_suite(unsigned(std::stoul(argv[1])),std::string(argv[2])+".domain.jsonl");
  return frozen_stage_main(argc,argv);
 }catch(const std::exception &e){std::cerr<<"V116B_DOMAIN_FAIL "<<e.what()<<'\n';return 1;}
}
