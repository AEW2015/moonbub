#include "codec.hpp"
#include <iostream>
using namespace cu66;
static bool read32(uint32_t &v) {
  char raw[4];std::cin.read(raw,4);if(std::cin.gcount()==0)return false;
  need(std::cin.gcount()==4,"test framing");v=0;for(unsigned i=0;i<4;++i)v|=uint32_t(uint8_t(raw[i]))<<(8*i);return true;
}
static void write32(uint32_t v) {for(unsigned i=0;i<4;++i)std::cout.put(char(v>>(8*i)));}
int main() {try {
  uint32_t mode,blocks,length;
  while(read32(mode)) {
    need(read32(blocks)&&read32(length)&&length<=128*5400+46,"test shape");Bytes bytes(length);
    std::cin.read(reinterpret_cast<char*>(bytes.data()),length);need(size_t(std::cin.gcount())==length,"test truncated");
    try {
      Bytes packet=bytes;std::vector<int16_t> values;
      if(mode==1) {
        need(length==blocks*128,"test flat shape");Reader r(bytes);for(unsigned i=0;i<blocks*64;++i)values.push_back(int16_t(signed16(r.u16())));
        packet=cu88::encode_br88(values).packet;need(cu88::decode_br88(packet,blocks,1)==values,"test native roundtrip");
      } else {need(mode==0,"test mode");values=cu88::decode_br88(packet,blocks,1);}
      Bytes raw;for(auto value:values)cu85::put16(raw,uint16_t(value));
      std::cout<<"{\"accepted\":true,\"coefficient_sha256\":\""<<hex(sha256(raw))<<"\",\"bytes\":"<<packet.size()<<",\"raw\":"<<(packet[5]?"true":"false")<<"}"<<std::endl;
      if(mode==1) {write32(uint32_t(packet.size()));std::cout.write(reinterpret_cast<const char*>(packet.data()),packet.size());std::cout.flush();}
    }catch(const std::exception &e) {std::cout<<"{\"accepted\":false,\"error\":\""<<e.what()<<"\"}"<<std::endl;}
  }return 0;
}catch(const std::exception &e) {std::cerr<<e.what()<<std::endl;return 1;}}
