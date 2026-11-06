#include "trace.hpp"
#include "../../python-gamebub-v88/entropy/codec.hpp"
#include <iostream>
#include <random>
using namespace cu66;
static unsigned checks=0;
static cu89::Decoded observe(const std::vector<int16_t> &values,const char *name) {
  auto encoded=cu88::encode_br88(values);auto n=unsigned(values.size()/64);
  auto out=cu89::decode_interleaved(encoded.packet,n,1);
  need(out.coefficients==values&&cu88::decode_br88(encoded.packet,n,1)==values,"test coefficient parity");
  uint64_t crc=0,raw=0,header=0;std::array<uint64_t,4> bits{},rice{},events{},fetched{};
  for(unsigned b=0;b<n;++b) {
    crc+=out.work[b].crc_bytes;raw+=out.work[b].raw_bytes;header+=out.work[b].header_bytes;
    need(b==0||(!out.work[b].crc_bytes&&!out.work[b].header_bytes),"test per-chunk setup attribution");
    for(unsigned c=0;c<4;++c) {const auto&w=out.context_work[b][c];
      need(!w.decisions&&!w.renorm&&!w.prob_init&&!w.raw_bits,"test no invented adaptive work");
      bits[c]+=w.plain_bits;rice[c]+=w.rice_values;events[c]+=w.events;fetched[c]+=w.stream_bytes;
    }
  }
  need(crc==encoded.packet.size(),"test exact chunk CRC pass");
  if(encoded.raw) {
    need(raw==128*n&&header==0,"test raw fetch accounting");
    need(bits==std::array<uint64_t,4>{},"test raw does not execute Rice reader");
  } else {
    need(bits==encoded.bits&&rice==encoded.values&&events==encoded.events,"test per-context primitive counts");
    for(unsigned c=0;c<4;++c)need(fetched[c]==(bits[c]+7)/8,"test bytes fetched once per stream");
    unsigned expected_header=24;for(auto nbits:encoded.bits)expected_header+=nbits%8!=0;
    need(header==expected_header,"test captured header and partial padding accounting");
  }
  ++checks;std::cout<<"TEST_PASS "<<name<<" raw="<<encoded.raw<<'\n';return out;
}
int main(){try {
  observe(std::vector<int16_t>(64,0),"empty_AC_zero_DC");
  observe(std::vector<int16_t>(64,1),"dense_unit");
  std::vector<int16_t> raw(64);for(unsigned i=0;i<64;++i)raw[i]=i%2?2048:-2048;
  auto rawout=observe(raw,"raw_extremes");need(rawout.raw,"test actual raw fallback");
  std::vector<int16_t> dc(8*64,0);for(unsigned i=0;i<8;++i)dc[i*64]=int16_t(i-4);observe(dc,"DC_resets_each_tile");
  std::vector<int16_t> future(4*64,0);future[3*64+cu85::order()[1]]=1;
  auto f=observe(future,"pending_AC_future_tile");
  need(f.context_work[0][1].events==1&&f.context_work[0][1].rice_values==2&&f.context_work[0][1].plain_bits>0,"test first event attributed to lookahead tile0");
  for(unsigned b=1;b<4;++b) {need(!f.context_work[b][1].plain_bits,"test future placement does not reread bits");}
  ++checks;
  future[cu85::order()[1]]=-2;auto two=observe(future,"two_events_lookahead");
  need(two.context_work[0][1].events==2,"test next event read at prior event placement");++checks;
  std::vector<int16_t> sparse(33*64,0);sparse.back()=-17;observe(sparse,"high_band_far_run");
  std::mt19937 rng(89017);for(unsigned seed=0;seed<8;++seed) {
    std::vector<int16_t> a((seed+1)*64);for(auto&v:a)v=(rng()%11==0)?int16_t(int(rng()%41)-20):0;observe(a,"seeded_sparse");
  }
  Bytes packet{'B','R','8','8',1,0};cu85::put32(packet,1);cu85::put16(packet,1);cu85::put16(packet,0);
  for(auto n:{10u,6u,6u,6u}) {cu85::put32(packet,n);}
  for(unsigned i=0;i<3;++i) {cu85::put32(packet,0);}
  packet.push_back(0);packet.push_back(255);cu85::put32(packet,29);
  // 15 zero unary bits, then fourteen literal bits containing 4096.
  packet.insert(packet.end(),{0,0,128,0});for(unsigned i=0;i<3;++i) {packet.push_back(0);packet.push_back(0);cu85::put32(packet,0);}
  cu85::put32(packet,crc32(packet));
  auto escaped=cu89::decode_interleaved(packet,1,1);need(escaped.coefficients[0]==2048&&escaped.context_work[0][0].plain_bits==29,"test exact unary escape bound");++checks;
  std::cout<<"V89_OBSERVER_TEST_PASS checks="<<checks<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
