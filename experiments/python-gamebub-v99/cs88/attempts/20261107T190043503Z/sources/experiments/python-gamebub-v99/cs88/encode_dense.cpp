// Fresh dense coefficients to actual BR88 bytes. No historical packet input.
#include "../../python-gamebub-v88/entropy/codec.hpp"
#include "../../cu66-native-v69/generated_constants.hpp"
#include <iostream>
#include <string>
using namespace cu66;
static bool read32(uint32_t &value) {
  char raw[4]; std::cin.read(raw,4);
  if(std::cin.gcount()==0) return false;
  need(std::cin.gcount()==4,"fresh dense length"); value=0;
  for(unsigned i=0;i<4;++i)value|=uint32_t(uint8_t(raw[i]))<<(8*i);
  return true;
}
int main(int argc,char **argv) {try {
  if(argc==2&&std::string(argv[1])=="--mask") {
    for(unsigned axis=0;axis<3;++axis) {
      const auto *safe=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
      for(unsigned tile=0;tile<(axis?1350u:5400u);++tile)std::cout.put(char(safe[tile]!=0));
    }
    return 0;
  }
  need(argc==1,"fresh dense arguments"); uint32_t blocks;
  while(read32(blocks)) {
    need(blocks>=1&&blocks<=5400,"fresh dense block bound");
    Bytes raw(size_t(blocks)*128);
    std::cin.read(reinterpret_cast<char*>(raw.data()),raw.size());
    need(size_t(std::cin.gcount())==raw.size(),"fresh dense truncated");
    Reader reader(raw); std::vector<int16_t> coefficients(size_t(blocks)*64);
    for(auto &value:coefficients)value=int16_t(signed16(reader.u16()));
    reader.end(); auto encoded=cu88::encode_br88(coefficients);
    need(cu88::decode_br88(encoded.packet,blocks,1)==coefficients,"fresh BR88 native parity");
    std::cout<<"{\"blocks\":"<<blocks<<",\"raw\":"<<(encoded.raw?"true":"false")<<",\"bits\":[";
    for(unsigned i=0;i<4;++i){if(i)std::cout<<',';std::cout<<encoded.bits[i];}
    std::cout<<"],\"values\":[";
    for(unsigned i=0;i<4;++i){if(i)std::cout<<',';std::cout<<encoded.values[i];}
    std::cout<<"],\"events\":[";
    for(unsigned i=0;i<4;++i){if(i)std::cout<<',';std::cout<<encoded.events[i];}
    std::cout<<"],\"bytes\":"<<encoded.packet.size()<<"}"<<std::endl;
    auto length=uint32_t(encoded.packet.size());
    for(unsigned i=0;i<4;++i)std::cout.put(char(length>>(8*i)));
    std::cout.write(reinterpret_cast<const char*>(encoded.packet.data()),encoded.packet.size());std::cout.flush();
  }
  return 0;
}catch(const std::exception &error){std::cerr<<"FRESH_BR88_FAIL "<<error.what()<<std::endl;return 1;}}
