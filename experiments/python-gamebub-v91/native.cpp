#include "native.hpp"
#include <chrono>
#include <iostream>
#include <random>
using namespace cu66;
struct Case { unsigned blocks; Bytes packet; bool benchmark, accepted; std::string expected; };
static uint32_t u32() {
  uint32_t x=0;
  for (unsigned i=0;i<4;++i) { int c=std::cin.get(); need(c!=EOF,"native harness EOF"); x|=uint32_t(c)<<(8*i); }
  return x;
}
static std::string coefficient_hash(const std::vector<int16_t> &a) {
  Bytes bytes; bytes.reserve(a.size()*2);
  for (auto v:a) { uint16_t u=uint16_t(v); bytes.push_back(uint8_t(u)); bytes.push_back(uint8_t(u>>8)); }
  return hex(sha256(bytes));
}
int main(int argc, char **argv) { try {
  need(argc == 1 || (argc == 2 && std::string(argv[1]) == "--verify-only"), "native arguments");
  unsigned count=u32();need(count<=2000,"native case bound");
  std::vector<Case> cases;
  for (unsigned i=0;i<count;++i) {
    Case c;c.blocks=u32();unsigned n=u32();c.benchmark=u32()!=0;c.accepted=u32()!=0;
    if (argc == 2) c.benchmark=false;
    need(n<=1000000,"native input bound");c.packet.resize(n);
    std::cin.read(reinterpret_cast<char*>(c.packet.data()),n);need(unsigned(std::cin.gcount())==n,"native packet EOF");
    char hash[64];std::cin.read(hash,64);need(std::cin.gcount()==64,"native hash EOF");c.expected.assign(hash,64);
    cases.push_back(std::move(c));
  }
  for (unsigned i=0;i<cases.size();++i) {
    const auto &c=cases[i];std::vector<int16_t> control,word;bool a=true,b=true;
    try {control=cu88::decode_br88(c.packet,c.blocks,1);} catch(const std::exception&) {a=false;}
    try {word=cu91::decode(c.packet,c.blocks);} catch(const std::exception&) {b=false;}
    need(a==c.accepted && b==c.accepted,"native accept/reject parity");
    if (a) need(control==word && coefficient_hash(word)==c.expected,"native coefficient parity");
    std::cout<<"{\"kind\":\"case\",\"id\":"<<i<<",\"accepted\":"<<(a?"true":"false")<<",\"status\":\"PASS\"}"<<std::endl;
  }
  // Every selected case has just been run by both readers: warm-up and exact
  // validation precede timings. Hashing is outside timed decode calls.
  std::vector<unsigned> selected;
  for(unsigned i=0;i<cases.size();++i)if(cases[i].benchmark)selected.push_back(i);
  std::minstd_rand rng(9191);
  uint64_t checksum=0;
  constexpr unsigned repetitions=7, iterations=20;
  for(unsigned repeat=0;repeat<repetitions;++repeat) {
    std::shuffle(selected.begin(),selected.end(),rng);
    for(unsigned ci=0;ci<selected.size();++ci)for(unsigned pass=0;pass<2;++pass) {
      unsigned variant=(pass+repeat+ci)%2;const auto &c=cases[selected[ci]];
      auto start=std::chrono::steady_clock::now();
      for(unsigned it=0;it<iterations;++it) {
        auto out=variant?cu91::decode(c.packet,c.blocks):cu88::decode_br88(c.packet,c.blocks,1);
        checksum+=uint16_t(out[(it*47)%out.size()]);
      }
      auto ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();
      std::cout<<"{\"kind\":\"timing\",\"repeat\":"<<repeat<<",\"id\":"<<selected[ci]<<",\"variant\":\""<<(variant?"word32":"bit")<<"\",\"iterations\":"<<iterations<<",\"ns\":"<<ns<<"}"<<std::endl;
    }
  }
  std::cout<<"{\"kind\":\"done\",\"status\":\"PASS\",\"cases\":"<<cases.size()<<",\"checksum\":"<<checksum<<"}"<<std::endl;
  return 0;
} catch(const std::exception &e) {std::cerr<<"V91_NATIVE_FAIL "<<e.what()<<std::endl;return 1;} }
