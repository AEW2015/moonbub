#include "codec.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
using namespace cu66;
// Deliberately rare decoder fixture: admissible inline model, not an observed
// encoder model or a compression result. Forces the two-byte refill boundary.
int main(int argc,char **argv) {try {
  need(argc==2,"refill fixture directory required");std::filesystem::path directory(argv[1]);std::filesystem::create_directories(directory);std::ofstream manifest(directory/"refill-manifest.json");manifest<<"{\"schema\":\"ec94-native-refill-fixtures-v1\",\"source_path\":\"experiments/python-gamebub-v94/native/test_refill.cpp\",\"test_report_path\":\"experiments/python-gamebub-v94/native/refill-results.json\",\"qualification\":\"Handcrafted decoder adversarial inline model, outside measured corpus alternatives.\",\"context_fixtures\":[";bool first=true;unsigned count=0;
  for(unsigned scale=8;scale<=10;++scale)for(unsigned lanes: {2u,4u}) {
    constexpr unsigned symbols=96;unsigned mass=1u<<scale;Bytes tables;for(unsigned q=0;q<16;++q)cu85::put16(tables,uint16_t(q==0?1:q==1?mass-1:0));
    std::array<uint32_t,4> states{};states.fill(cu94::L);Bytes emitted;
    for(unsigned i=symbols;i-->0;) {auto &state=states[i%lanes];while(state>=((cu94::L>>scale)<<8)) {emitted.push_back(uint8_t(state));state>>=8;}state<<=scale;}
    Bytes stream{0,255,uint8_t(scale),0};cu85::put32(stream,crc32(tables));cu85::put32(stream,uint32_t(4*lanes+emitted.size()));cu85::put32(stream,0);cu85::put32(stream,symbols);stream.insert(stream.end(),tables.begin(),tables.end());for(unsigned lane=0;lane<lanes;++lane)cu85::put32(stream,states[lane]);stream.insert(stream.end(),emitted.rbegin(),emitted.rend());
    unsigned events=0;cu94::DecodeStats stats;cu94::read_stream(stream,lanes==2?2:3,0,symbols,[&](uint32_t a,uint32_t b){need(a==0&&b==0,"rare refill values");++events;},&stats);need(events==symbols&&stats.ans_renorm_bytes[0]==emitted.size(),"rare refill decode");
    // Independently count each bounded refill to bind the boundary assertion.
    Reader input(View(stream).sub(52,stream.size()-52));for(unsigned lane=0;lane<lanes;++lane)states[lane]=input.u32();unsigned maximum=0;
    for(unsigned i=0;i<symbols;++i) {auto &state=states[i%lanes];need((state&(mass-1))==0,"rare category slot");state>>=scale;unsigned refill=0;while(state<cu94::L) {state=state*256+input.u8();++refill;}maximum=std::max(maximum,refill);}input.end();need(maximum==(scale==8?1u:2u),"refill boundary coverage");for(unsigned lane=0;lane<lanes;++lane)need(states[lane]==cu94::L,"rare terminal");
    std::string name="forced-refill-n"+std::to_string(lanes)+"-s"+std::to_string(scale)+".stream";std::ofstream file(directory/name,std::ios::binary);file.write(reinterpret_cast<const char*>(stream.data()),std::streamsize(stream.size()));need(bool(file),"refill fixture write");
    if(!first)manifest<<',';
    first=false;manifest<<"{\"path\":\""<<name<<"\",\"name\":\"adversarial_rare_refill\",\"context\":0,\"method\":"<<(lanes==2?2:3)<<",\"events\":"<<symbols<<",\"symbol_count\":"<<symbols<<",\"max_refill\":"<<maximum<<",\"sha256\":\""<<hex(sha256(stream))<<"\",\"fields\":[";for(unsigned i=0;i<symbols;++i) {if(i)manifest<<',';manifest<<0;}manifest<<"]}";++count;
  }
  manifest<<"]}\n";need(bool(manifest),"refill manifest write");std::cout<<"{\"status\":\"PASS\",\"context_fixtures\":"<<count<<",\"max_refill\":2}\n";
}catch(const std::exception &e) {std::cerr<<"EC94_REFILL_TEST_FAIL "<<e.what()<<'\n';return 1;}}
