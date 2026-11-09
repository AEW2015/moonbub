#include "count_domain_base.cpp"
#include "Vcontext_probe___024root.h"

// These are declared full-width predicate contexts, not reachable gameplay
// frames. Start/request phases are real; only the coherent count/epoch tuple
// is deposited before the actual request edge. No cached bit is forced.
#define TERM_FIELD(instance,n) d.rootp->context_probe__DOT__##instance##__DOT__##n
#define TERM_ALL(n,v) do{TERM_FIELD(original,n)=(v);TERM_FIELD(candidate,n)=(v);TERM_FIELD(specialized,n)=(v);}while(0)
struct TerminalCoverage {
 uint64_t cases=0,random_cases=0,hold_edges=0,true_cases=0,false_cases=0,wrapped_true=0;
 std::array<uint64_t,3> requests{};
};
static void terminal_capture(Sim&s,unsigned kind,uint32_t emitted,uint32_t target,
                             uint32_t epoch,TerminalCoverage&coverage){
 auto&d=s.d;d.in_valid=0;d.reset=1;d.start=d.abort_context=0;s.step();d.reset=0;
 Case c;c.id="v120-prepared-terminal";c.blocks=1;c.events=1;c.band=kind==0?0:1;
 c.k0=0;c.k1=kind==0?255:0;c.bits=32;c.data.assign(4,0);
 s.start(c,false,false,0x1200cafeU);
 if(kind==2){
  bool loaded=false;
  for(unsigned n=0;d.debug_state!=5;++n){
   require(n<100,"natural run-to-level setup watchdog");
   d.in_valid=!loaded;d.in_data=0x80000000U;d.in_bits=32;d.in_last=1;d.out_ready=0;
   if(s.step().input)loaded=true;
   require(!d.error&&!d.done&&!d.out_valid,"run setup produced unexpected output/error");
  }
  require(loaded,"level request lacks actual accepted run input");
 }
 d.in_valid=0;d.out_ready=0;d.clk=0;d.eval();
 require(d.debug_state==(kind==0?1U:kind==1?3U:5U)&&d.verify_terminal_req_fire,
         "terminal fixture lacks real DC/RUN/LEVEL request acceptance");
 TERM_ALL(emitted,emitted);TERM_ALL(target,target);TERM_ALL(context_epoch,epoch);
 d.eval();const bool expected=uint32_t(emitted+1U)==target;
 require(bool(d.verify_original_terminal)==expected,"original full32 wrapped comparison differs from integer oracle");
 require(d.verify_terminal_req_fire,"prepared count tuple changed real request eligibility");
 s.step();
 require(bool(d.verify_terminal_last)==expected&&bool(d.verify_terminal_special)==expected,
         "actual generic/specialized terminal register differs from full32 oracle");
 const unsigned waits=kind==2?0U:4U;
 for(unsigned i=0;i<waits;++i){
  d.in_valid=0;d.event_count=s.random();d.epoch=s.random();d.stream_bits=s.random();
  s.step();require(bool(d.verify_terminal_last)==expected&&bool(d.verify_terminal_special)==expected&&
                  bool(d.verify_original_terminal)==expected&&!d.error&&!d.done&&!d.out_valid,
                  "owned terminal tuple changed while waiting without input");++coverage.hold_edges;
 }
 ++coverage.cases;++coverage.requests[kind];coverage.true_cases+=expected;coverage.false_cases+=!expected;
 coverage.wrapped_true+=emitted==0xffffffffU&&target==0&&expected;
 d.reset=1;d.in_valid=0;s.step();d.reset=0;
 require(!d.out_valid&&!d.in_ready&&!d.done&&!d.error,"prepared terminal cleanup reset failed");
}
static TerminalCoverage terminal_domain(unsigned seed){
 Sim s(seed);TerminalCoverage c;
 const std::array<uint32_t,16> values{{0U,1U,2U,3U,65535U,65536U,65537U,0x3fffffffU,
  0x7ffffffeU,0x7fffffffU,0x80000000U,0x80000001U,0xffff0000U,0xfffffffdU,0xfffffffeU,0xffffffffU}};
 for(unsigned kind=0;kind<3;++kind){
  for(uint32_t emitted:values){
   for(uint32_t target:values)terminal_capture(s,kind,emitted,target,s.random(),c);
   for(uint32_t target:std::array<uint32_t,3>{{uint32_t(emitted-1U),uint32_t(emitted+1U),uint32_t(emitted+2U)}})
    terminal_capture(s,kind,emitted,target,s.random(),c);
  }
  for(unsigned i=0;i<32768;++i){const uint32_t emitted=s.random();const uint32_t target=i%4==0?uint32_t(emitted+1U):s.random();terminal_capture(s,kind,emitted,target,s.random(),c);++c.random_cases;}
 }
 require(c.cases==99216&&c.random_cases==98304&&c.hold_edges==264576&&c.true_cases>0&&c.false_cases>0&&c.wrapped_true>0&&
         c.requests[0]==33072&&c.requests[1]==33072&&c.requests[2]==33072,
         "full32 terminal domain/request/hold coverage incomplete");
 return c;
}
int main(int argc,char**argv){try{
 require(inherited_domain_main(argc,argv)==0,"whole unchanged context/count-domain/geometry/error/cancel proof");
 const auto c=terminal_domain(unsigned(std::stoul(argv[2]))^0x1207e12U);
 std::cout<<"{\"type\":\"v120_terminal_owner_verdict\",\"status\":\"TEST_PASS\",\"prepared_capture_cases\":"<<c.cases
  <<",\"random_full32\":"<<c.random_cases<<",\"owned_wait_edges\":"<<c.hold_edges<<",\"true_cases\":"<<c.true_cases
  <<",\"false_cases\":"<<c.false_cases<<",\"wrapped_true_cases\":"<<c.wrapped_true<<",\"dc_requests\":"<<c.requests[0]
  <<",\"run_requests\":"<<c.requests[1]<<",\"level_requests\":"<<c.requests[2]<<",\"public_cycle_delta\":0,\"prepared_contexts_are_natural_frames\":false}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V120_TERMINAL_OWNER_FAIL "<<e.what()<<'\n';return 1;}}
