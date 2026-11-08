#include "Vguard_probe.h"
#include "verilated.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
static void need(bool yes,const char*why){if(!yes)throw std::runtime_error(why);}
int main(int argc,char**argv){try{
 need(argc==2,"trace required");std::ofstream trace(argv[1]);need(bool(trace),"trace open");Vguard_probe d;std::mt19937 rng(107943);uint64_t rows=0,high=0;const uint32_t mask=(1U<<17)-1;
 for(uint32_t n=0;n<=mask;++n){
  const uint32_t c=mask-n,p=n*43U,q=c*43U;
  for(unsigned corner=0;corner<9;++corner){
   auto count=[&](uint32_t limit){switch(corner){case 0:return 0U;case 1:return limit-1U;case 2:return limit;case 3:return limit+1U;case 4:return 0x7fffffffU;case 5:return 0x80000000U;case 6:return 0xfffffffeU;case 7:return 0xffffffffU;default:return uint32_t(rng());}};
   d.begin_blocks=n;d.context_blocks=c;d.scratch_count=count(p);d.ingress_count=count(q);d.eval();
   need(d.scratch_original==p&&d.scratch_candidate==p,"full17 scratch product");need(d.ingress_original==q&&d.ingress_candidate==q,"full17 ingress product");
   need(bool(d.scratch_old_reject)==(d.scratch_count>p)&&bool(d.scratch_new_reject)==(d.scratch_count>p),"full32 scratch strict comparison");need(bool(d.ingress_old_reject)==(d.ingress_count>q)&&bool(d.ingress_new_reject)==(d.ingress_count>q),"full32 ingress strict comparison");
   trace<<n<<','<<c<<','<<d.scratch_count<<','<<d.ingress_count<<','<<d.scratch_candidate<<','<<d.ingress_candidate<<','<<unsigned(d.scratch_new_reject)<<','<<unsigned(d.ingress_new_reject)<<'\n';++rows;high+=d.scratch_count>=0x80000000U;
  }
 }
 d.final();need(rows==1179648,"finite domain rows");std::cout<<"{\"status\":\"TEST_PASS\",\"rows\":"<<rows<<",\"all17bit_operands_per_product\":131072,\"count_cases_per_operand\":9,\"high32_scratch_counts\":"<<high<<",\"seed\":107943}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
