#include "inherited_context.cpp"
static void domain_starts(unsigned seed) {
 Sim s(seed);unsigned cases=0,enabled=0,excluded=0;
 const std::array<unsigned,16> blocks={0,1,2,3,7,255,256,1023,1024,32767,32768,65534,65535,65536,65537,131071};
 for(bool serial:{false,true})for(bool word16:{false,true})for(unsigned b:blocks)for(unsigned band=0;band<6;++band) {
  const uint64_t width=band==1?5:band==2?15:band==3?43:1,lim=uint64_t(b)*width;
  std::vector<uint32_t> counts={0,1,uint32_t(lim?lim-1:0),uint32_t(lim),uint32_t(lim+1),0x80000000U,0xffffffffU};
  for(uint32_t count:counts)for(unsigned bad=0;bad<3;++bad) {
   Case c;c.id="domain-start";c.blocks=b;c.band=band;c.events=count;c.k0=bad==1?255:0;c.k1=band==0?255:bad==2?255:0;
   s.start(c,word16,serial,0x99112233);const bool domain=band==0||band>3||uint64_t(count)<=lim;
   require(bool(s.d.specialized_owner_domain)==domain,"independent specialized precondition ownership");
   const bool badcfg=b==0||b>65536||band>3||(band==0&&(c.k0>13||c.k1!=255||count!=b))||(band!=0&&(c.k0>19||c.k1>11||uint64_t(count)>lim));
   require(s.d.error==(badcfg?4:0),"independent unchanged generic config/error priority");
   if(domain)++enabled;else ++excluded;
   s.d.abort_context=1;s.step();s.d.abort_context=0;require(s.d.specialized_owner_domain,"abort restores comparator domain");++cases;
  }
 }
 std::cout<<"{\"type\":\"domain_start_verdict\",\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"enabled_cases\":"<<enabled<<",\"excluded_AC_count_cases\":"<<excluded<<"}\n";
}
static void timing_edges(unsigned seed) {
 Sim s(seed);unsigned checks=0;
 for(bool serial:{false,true})for(bool word16:{false,true}) {
  Case c;c.id="earliest-zero-suffix";c.band=1;c.k1=0;pack(c,{true,true});c.expected={{0,1,-1}};
  s.run(c,word16,serial,false);
  require(s.d.min_success_gap==3 && s.d.min_level_gap==3 && s.d.geometry_consumes==1,"earliest successful Rice edge is E+3");++checks;
  c=Case{};c.id="zero-stream-truncation";c.error=2;s.run(c,word16,serial,false);
  require(s.d.min_error_gap==2,"zero stream error consumed at E+2");++checks;
 }
 std::cout<<"{\"type\":\"edge_verdict\",\"status\":\"TEST_PASS\",\"checks\":"<<checks<<",\"minimum_success_request_response_gap\":3,\"zero_stream_error_gap\":2}\n";
}
int inherited_domain_main(int argc,char**argv){try{require(argc==4,"arguments");timing_edges(unsigned(std::stoul(argv[2])));domain_starts(unsigned(std::stoul(argv[2])));return inherited_context_main(argc,argv);}catch(const std::exception&e){std::cerr<<"COUNT_DOMAIN_FAIL "<<e.what()<<'\n';return 1;}}
