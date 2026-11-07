#include "codec.hpp"
#include <fstream>
#include <iostream>
#include <random>
#include <filesystem>
using namespace cu66;
static unsigned checks=0,rejections=0;
static void check(bool value,const char *message) {need(value,message);++checks;}
static void reject(Bytes bytes,unsigned blocks) {
  bool failed=false;try {cu93::decode(bytes,blocks);}catch(const std::exception &) {failed=true;}
  check(failed,"EC93 malformed accepted");++rejections;
}
static void crc(Bytes &bytes) {bytes.resize(bytes.size()-4);cu85::put32(bytes,crc32(bytes));}
static void write(const std::filesystem::path &path,const Bytes &bytes) {
  std::ofstream file(path,std::ios::binary);file.write(reinterpret_cast<const char*>(bytes.data()),std::streamsize(bytes.size()));need(bool(file),"fixture write");
}
int main(int argc,char **argv) {try {
  need(argc==2,"fixture output directory required");std::filesystem::path directory(argv[1]);std::filesystem::create_directories(directory);
  std::ofstream manifest(directory/"manifest.json");manifest<<"{\"schema\":\"ec93-native-fixtures-v1\",\"fixtures\":[";bool first=true;
  std::mt19937 random(930062);unsigned families=0;
  for(unsigned family=0;family<5;++family) {
    unsigned blocks=family==3?1:64;std::vector<int16_t> values(blocks*64);
    for(size_t i=0;i<values.size();++i) {
      if(family==1&&i%11==0)values[i]=int16_t((int(i)%5-2)*1024);
      if(family==2&&random()%17==0)values[i]=int16_t(int(random()%4097)-2048);
      if(family==3||family==4)values[i]=int16_t(int(random()%4097)-2048);
    }
    const auto prepared=cu93::prepare(values);Bytes packed;for(auto value:values)cu85::put16(packed,uint16_t(value));
    for(unsigned selector=0;selector<256;++selector) {
      auto packet=cu93::assemble(prepared,selector);cu93::DecodeStats stats;check(cu93::decode_ec93(packet,blocks,1,&stats)==values,"EC93 fixture parity");
      std::string name="family"+std::to_string(family)+"-selector"+std::to_string(selector)+".ec93";write(directory/name,packet);
      if(!first)manifest<<',';
      first=false;
      manifest<<"{\"path\":\""<<name<<"\",\"blocks\":"<<blocks<<",\"requested_selector\":"<<selector<<",\"wire_selector\":"<<unsigned(packet[6])<<",\"raw\":"<<(packet[5]?"true":"false")<<",\"coefficient_sha256\":\""<<hex(sha256(packed))<<"\",\"sha256\":\""<<hex(sha256(packet))<<"\"}";
      auto bad=packet;bad[12]=2;crc(bad);reject(bad,blocks);bad=packet;bad[7]=1;crc(bad);reject(bad,blocks);
      bad=packet;bad[14]=1;crc(bad);reject(bad,blocks);bad=packet;bad[5]=2;crc(bad);reject(bad,blocks);
      bad=packet;bad[0]='X';crc(bad);reject(bad,blocks);bad=packet;bad[4]=2;crc(bad);reject(bad,blocks);
      bad=packet;bad[8]^=1;crc(bad);reject(bad,blocks);bad=packet;bad[16]^=1;crc(bad);reject(bad,blocks);
      bad=packet;bad.back()^=1;reject(bad,blocks);bad=packet;bad.push_back(0);reject(bad,blocks);
      for(size_t cut=0;cut<std::min(size_t(48),packet.size());++cut)reject(Bytes(packet.begin(),packet.begin()+std::ptrdiff_t(cut)),blocks);
      if(packet[5]) {
        bad=packet;bad[6]=1;crc(bad);reject(bad,blocks);
        bad=packet;bad[44]=255;bad[45]=127;crc(bad);reject(bad,blocks);
      } else {
        Reader lengths(View(packet).sub(16,16));size_t offset=44;
        for(unsigned context=0;context<4;++context) {
          unsigned length=lengths.u32(),method=(selector>>(2*context))&3;
          if(method==3) {
            bad=packet;bad[offset]=31;crc(bad);reject(bad,blocks);
            bad=packet;bad[offset+1]=1;crc(bad);reject(bad,blocks);
            bad=packet;bad[offset+2]^=1;crc(bad);reject(bad,blocks);
            if(length>6) {bad=packet;bad[offset+6]=255;crc(bad);reject(bad,blocks);bad=packet;bad[offset+11]^=128;crc(bad);reject(bad,blocks);}
          } else {
            bad=packet;bad[offset]=255;crc(bad);reject(bad,blocks);
            bad=packet;bad[offset+5]^=128;crc(bad);reject(bad,blocks);
            Reader descriptor(View(packet).sub(offset,length));descriptor.u8();descriptor.u8();uint32_t bits=descriptor.u32();
            if(method==2) {bad=packet;bad[offset+9]^=128;crc(bad);reject(bad,blocks);descriptor.u32();}
            if(method!=1) {bad=packet;bad[offset+descriptor.pos+(bits-1)/8]^=uint8_t(1u<<(7-(bits-1)%8));crc(bad);reject(bad,blocks);}
            if(bits%8) {bad=packet;bad[offset+descriptor.pos+(bits-1)/8]|=1;crc(bad);reject(bad,blocks);}
          }
          offset+=length;
        }
      }
    }
    ++families;
  }
  manifest<<"]}\n";need(bool(manifest),"manifest write");
  std::cout<<"{\"status\":\"PASS\",\"families\":"<<families<<",\"fixtures\":1280,\"checks\":"<<checks<<",\"rejections\":"<<rejections<<"}\n";return 0;
}catch(const std::exception &error) {std::cerr<<"EC93_TEST_FAIL "<<error.what()<<'\n';return 1;}}
