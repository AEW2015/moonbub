#include "trace.hpp"
#include <iostream>
using namespace cu66;
static bool u32(std::istream &in,uint32_t &value) {
  char bytes[4];in.read(bytes,4);
  if(in.gcount()==0)return false;
  need(in.gcount()==4,"context bridge truncated u32");value=0;
  for(unsigned i=0;i<4;++i)value|=uint32_t(uint8_t(bytes[i]))<<(8*i);
  return true;
}
static void put(std::ostream &out,uint32_t value) {
  for(unsigned i=0;i<4;++i)out.put(char(value>>(8*i)));
}
static void work(std::ostream &out,const cu86::Work &w) {
  for(uint32_t value:{w.decisions,w.renorm,w.stream_bytes,w.rice_values,w.events,
                      w.raw_bytes,w.header_bytes,w.crc_bytes,w.emits,w.raw_bits,w.prob_init})put(out,value);
}
int main(){try {
  uint32_t blocks,length;uint64_t chunks=0,tiles=0;
  while(u32(std::cin,blocks)) {
    need(u32(std::cin,length)&&blocks&&blocks<=5400&&length>=46&&length<=46+128*blocks,"context bridge bounds");
    Bytes packet(length);std::cin.read(reinterpret_cast<char*>(packet.data()),length);
    need(size_t(std::cin.gcount())==length,"context bridge truncated AB38");
    auto original=decode_ab38(packet,blocks,1);
    auto observed=cu86::decode_interleaved(packet,blocks,1);
    need(original==observed.coefficients,"context bridge coefficient parity");
    put(std::cout,blocks);Bytes raw;raw.reserve(original.size()*2);
    for(auto v:original)put16(raw,uint16_t(v));
    std::cout.write(reinterpret_cast<const char*>(raw.data()),raw.size());
    for(unsigned i=0;i<blocks;++i) {
      work(std::cout,observed.work[i]);
      for(unsigned context=0;context<4;++context)work(std::cout,observed.context_work[i][context]);
    }
    std::cout.flush();need(bool(std::cout),"context bridge output");++chunks;tiles+=blocks;
  }
  std::cerr<<"V86_CONTEXT_BRIDGE_PASS chunks="<<chunks<<" encoded_tiles="<<tiles<<" exact_coefficients=1\n";
}catch(const std::exception &e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
