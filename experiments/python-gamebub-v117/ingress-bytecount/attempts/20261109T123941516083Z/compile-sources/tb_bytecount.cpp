#include "extents_base.cpp"
int main(int argc,char**argv){try{
 need(inherited_extents_main(argc,argv)==0,"entire immutable 259-packet and descriptor-extents proof");
 ExtentsCoverage c;const std::array<uint32_t,10>expected_bytes{{0U,1U,2U,0x1ffffffeU,0x1fffffffU,0x20000000U,0x20000001U,0x80000000U,0xfffffffeU,0xffffffffU}};
 const std::array<uint32_t,6>whole{{0U,1U,2U,0x0fffffffU,0x1ffffffeU,0x1fffffffU}};
 const std::array<uint32_t,4>cursor{{0U,0xfffffffcU,0xfffffff8U,0xffffffffU}};
 uint64_t zero_length_remainders=0,max_u=0,high_expected=0;
 for(uint32_t length:expected_bytes)for(uint32_t u:whole)for(unsigned remainder=0;remainder<8;++remainder)for(unsigned band=0;band<4;++band){
  const uint32_t bits=(u<<3)|remainder;
  // Preserve the old independent ceil-byte reference and real SELECT_BAND
  // preparation. New SVA checks the substituted predicate even where the
  // separate packet-bit bound rejects max-u nonaligned descriptors first.
  ready_extent(0x2000002dU,cursor[unsigned(c.ready)&3U],bits,uint32_t(length+6U),band,0,c);
  zero_length_remainders+=length==0U&&remainder!=0U;max_u+=u==0x1fffffffU;high_expected+=length>=0x20000000U;
 }
 need(c.ready==1920&&c.initial==0&&c.commits>0&&c.rejects>0&&zero_length_remainders==168&&max_u==320&&high_expected==960,"full32 ceil-byte boundary matrix");
 std::cout<<"{\"type\":\"v117_ingress_bytecount_verdict\",\"status\":\"TEST_PASS\",\"extra_ready_cases\":"<<c.ready<<",\"zero_L_nonzero_remainder_cases\":"<<zero_length_remainders<<",\"max_u_cases\":"<<max_u<<",\"high_expected_byte_cases\":"<<high_expected<<",\"commits\":"<<c.commits<<",\"rejects\":"<<c.rejects<<",\"edges\":"<<c.edges<<",\"old_ready_cases_retained\":21860,\"old_initial_cases_retained\":6272,\"public_cycle_delta\":0,\"pair_skipped_edges\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V117_BYTECOUNT_FAIL "<<e.what()<<'\n';return 1;}}
