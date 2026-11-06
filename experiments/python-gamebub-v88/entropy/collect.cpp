#include "codec.hpp"
#include <iostream>
using namespace cu66;
static bool u32(uint32_t &v) {char b[4];std::cin.read(b,4);if(std::cin.gcount()==0)return false;need(std::cin.gcount()==4,"helper framing");v=0;for(unsigned i=0;i<4;++i)v|=uint32_t(uint8_t(b[i]))<<(8*i);return true;}
static void write32(uint32_t v) {for(unsigned i=0;i<4;++i)std::cout.put(char(v>>(8*i)));}
int main() {try {
  uint32_t blocks,length;
  while(u32(blocks)) {
    need(u32(length)&&blocks>=1&&blocks<=5400&&length<=46+128*blocks,"helper bounds");Bytes packet(length);
    std::cin.read(reinterpret_cast<char*>(packet.data()),length);need(size_t(std::cin.gcount())==length,"helper truncated");
    auto a=decode_ab38(packet,blocks,1);auto old=cu85::encode(a);need(old.packet==packet,"exact old re-encoding");auto plain=cu88::encode_br88(a);
    if(old.raw) {old.decisions.fill(0);old.renorm.fill(0);}
    need(cu88::decode_br88(plain.packet,blocks,1)==a,"native BR88 coefficient parity");Bytes coefficients;for(auto v:a)cu85::put16(coefficients,uint16_t(v));
    std::cout<<"{\"blocks\":"<<blocks<<",\"old_bytes\":"<<packet.size()<<",\"new_bytes\":"<<plain.packet.size()<<",\"coefficient_sha256\":\""<<hex(sha256(coefficients))<<"\",\"raw\":"<<(plain.raw?"true":"false")<<",\"old_decisions\":[";
    for(unsigned i=0;i<4;++i) {if(i)std::cout<<',';std::cout<<old.decisions[i];}std::cout<<"],\"old_renorm\":[";
    for(unsigned i=0;i<4;++i) {if(i)std::cout<<',';std::cout<<old.renorm[i];}std::cout<<"],\"new_bits\":[";
    for(unsigned i=0;i<4;++i) {if(i)std::cout<<',';std::cout<<plain.bits[i];}std::cout<<"],\"rice_values\":[";
    for(unsigned i=0;i<4;++i) {if(i)std::cout<<',';std::cout<<plain.values[i];}std::cout<<"],\"events\":[";
    for(unsigned i=0;i<4;++i) {if(i)std::cout<<',';std::cout<<plain.events[i];}std::cout<<"]}"<<std::endl;
    write32(uint32_t(plain.packet.size()));std::cout.write(reinterpret_cast<const char*>(plain.packet.data()),plain.packet.size());std::cout.flush();
  }return 0;
}catch(const std::exception &e) {std::cerr<<"BR88_HELPER_FAIL "<<e.what()<<std::endl;return 1;}}
