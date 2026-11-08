// Actual-native rollback regression: late canonical patch CRC failure after large outputs.
#include "native/endpoint.hpp"
#include <cassert>
#include <fstream>
#include <iterator>
#include <iostream>
static std::vector<uint8_t> file(const std::string& p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
static uint32_t words_crc(const cu66_partition::HudCache& c){std::vector<uint8_t> b;for(const auto&p:c.patches)for(auto w:p.words){b.push_back(uint8_t(w));b.push_back(uint8_t(w>>8));}assert(b.size()==42240);return cu66::crc32({b.data(),b.size()});}
static std::vector<uint8_t> hu(const std::vector<uint8_t>& wire){assert(wire.size()>=36);size_t n=v34::u32(wire.data()+8);assert(wire.size()==n+36);return {wire.begin()+32,wire.end()-4};}
int main(int argc,char**argv){assert(argc==2);std::string root=argv[1];auto key=hu(file(root+"/prepare0.bin"));auto p=hu(file(root+"/prepare1.bin"));
 for(unsigned bad_patch: {0u,1u}){
  v34::Endpoint e(98304);cu66_port::Scope scope(e.arena);auto&g=*e.gate;
  assert(g.prepare(1,0,0xffffffffu,true,{key.data(),key.size()})==cu66_partition::Reply::Accepted);
  const auto key_tag=g.status().tag;assert(g.acknowledge_external_write_drain(1,0,21120,key_tag));assert(g.commit(1,0));
  const auto accepted=g.accepted();assert(accepted&&accepted->id==0);const auto crc=words_crc(*accepted);const auto prior_tag=accepted->tag;const size_t baseline=e.arena.live;
  auto bad=p;size_t off=106;for(unsigned i=0;i<bad_patch;++i)off+=v34::u32(bad.data()+54+i*4);size_t len=v34::u32(bad.data()+54+bad_patch*4);assert(len>=4&&off+len<=bad.size()-4);
  // Alter nested CRC only, preserving HU envelope CRC and all other components.
  bad[off+len-1]^=1;v34::put32(bad.data()+bad.size()-4,cu66::crc32({bad.data(),bad.size()-4}));
  const auto result=g.prepare(2,1,0,false,{bad.data(),bad.size()});assert(result==cu66_partition::Reply::DecodeRejected);assert(g.status().phase==cu66_partition::Phase::Failed);assert(!g.candidate_ready());assert(!g.read_candidate(2,1));
  assert(g.accepted().get()==accepted.get());assert(g.accepted()->id==0&&g.accepted()->reference_id==0xffffffffu&&g.accepted()->generation==1);assert(g.accepted()->tag==prior_tag);assert(words_crc(*g.accepted())==crc);
  // At least both larger fixed outputs have been allocated before this late rejection.
  assert(e.arena.peak>=baseline+15360+11520);const size_t failed_live=e.arena.live;assert(failed_live>=baseline&&failed_live<=baseline+256);
  assert(g.prepare(2,1,0,false,{p.data(),p.size()})==cu66_partition::Reply::Stale);assert(!g.candidate_ready());assert(e.arena.live==failed_live);assert(words_crc(*g.accepted())==crc);
  // A fresh generation can retry this exact semantic P frame after rejection.
  assert(g.prepare(3,1,0,false,{p.data(),p.size()})==cu66_partition::Reply::Accepted);assert(g.candidate_ready());assert(g.accepted()->id==0);assert(words_crc(*g.accepted())==crc);assert(g.abort(3,1));assert(!g.candidate_ready());assert(words_crc(*g.accepted())==crc);
  std::cout<<"LATE_PATCH_REJECT="<<bad_patch<<" ACCEPTED_CRC="<<std::hex<<crc<<std::dec<<" BASELINE="<<baseline<<" FAILED_LIVE="<<failed_live<<" PEAK="<<e.arena.peak<<" accepted_immutable=true stale_refused=true newer_retry=true\n";
 }
}
