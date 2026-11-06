#include "encode.hpp"
#include "../../cu66-native-v69/decoder.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
using namespace cu66;
static Bytes load_file(const std::filesystem::path &path) {
  std::ifstream f(path,std::ios::binary);need(bool(f),"control packet open");return {std::istreambuf_iterator<char>(f),{}};
}
static unsigned tests() {
  unsigned cases=0,raw=0;uint32_t random=85001;
  for(unsigned n:{1u,2u,16u,64u})for(unsigned type=0;type<5;++type) {
    std::vector<int16_t> values(n*64);
    for(unsigned b=0;b<n;++b)for(unsigned i=0;i<64;++i) {
      int value=0;
      if(type==1 && i==0)value=(b%2)?2048:-2048;
      if(type==2 && i==63)value=(b%2)?-2048:2048;
      if(type>=3) {
        random=random*1664525u+1013904223u;
        value=int(random%4097)-2048;
        if(type==3 && random%10)value=0;
      }
      values[b*64+i]=int16_t(value);
    }
    auto packet=cu85::encode(values);need(decode_ab38(packet.packet,n,1)==values,"self-test independent coefficient parity");
    raw+=packet.raw;++cases;
  }
  need(raw>0 && raw<cases,"self-test compressed/raw coverage");
  bool rejected=false;try {cu85::encode({});}catch(const std::exception &) {rejected=true;}need(rejected,"empty input rejection");++cases;
  std::vector<int16_t> bad(64);bad[0]=2049;rejected=false;
  try {cu85::encode(bad);}catch(const std::exception &) {rejected=true;}need(rejected,"coefficient range rejection");++cases;
  std::cerr<<"V85_ENCODER_SELFTEST_PASS cases="<<cases<<" raw="<<raw<<"\n";return cases;
}
int main(int argc,char **argv) {try {
  need(argc==2,"control index argument");tests();std::filesystem::path index=argv[1];std::ifstream input(index);need(bool(input),"control index open");
  std::string line;unsigned frames=0;
  while(std::getline(input,line)) {
    std::stringstream fields(line);std::vector<std::string> f;std::string value;
    while(std::getline(fields,value,'\t'))f.push_back(value);
    need(f.size()==6,"control index fields");auto packet=load_file(index.parent_path()/f[2]);checked(packet,88,49152);
    need(hex(sha256(packet))==std::filesystem::path(f[2]).stem().string(),"control packet hash");
    bool key=packet[5]&1;Reader outer(View(packet).sub(68,packet.size()-68-4));auto nb=outer.u32();outer.u32();auto base=outer.take(nb);checked(base,67,49152);
    Reader gu(base.sub(0,base.n-4));gu.take(40);auto nq=gu.u32(),nv=gu.u32();need(nq==338,"control qmap");std::array<unsigned,3> length{};for(auto &x:length)x=gu.u32();gu.take(nq);gu.take(nv);
    uint64_t all_bytes=0,residual_bytes=0,all_decisions=0,residual_decisions=0;
    std::array<std::string,3> hashes;std::array<unsigned,3> sizes{};
    for(unsigned axis=0;axis<3;++axis) {
      unsigned blocks=axis?1350:5400,bw=axis?45:90;const auto *safe=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
      unsigned visible=0;for(unsigned b=0;b<blocks;++b)visible+=!safe[b];
      Reader p(gu.take(length[axis]));auto dispatch=p.u8();need(dispatch==5 || dispatch==6,"control dispatch");
      auto coefficients=decode_ab38(p.take(p.v.n-p.pos),dispatch==6?visible:blocks,dispatch==6?1:bw);
      std::vector<int16_t> all,residual;unsigned at=0;
      for(unsigned b=0;b<blocks;++b) {
        std::array<int16_t,64> tile{};
        if(dispatch!=6 || !safe[b]) {std::copy(coefficients.begin()+at*64,coefficients.begin()+(at+1)*64,tile.begin());++at;}
        if(!safe[b]) {
          all.insert(all.end(),tile.begin(),tile.end());
          if(key || std::any_of(tile.begin(),tile.end(),[](int x){return x!=0;}))residual.insert(residual.end(),tile.begin(),tile.end());
        }
      }
      auto encoded=cu85::encode(all);all_bytes+=encoded.packet.size();
      for(auto n:encoded.decisions)all_decisions+=n;
      if(!residual.empty()) {
        auto filtered=cu85::encode(residual);residual_bytes+=filtered.packet.size();hashes[axis]=hex(sha256(filtered.packet));sizes[axis]=unsigned(filtered.packet.size());
        for(auto n:filtered.decisions)residual_decisions+=n;
      }
    }
    gu.end();
    std::cout<<"{\"cohort\":"<<f[0]<<",\"fid\":"<<f[1]<<",\"key\":"<<(key?"true":"false")<<",\"all_visible_AB38_bytes\":"<<all_bytes<<",\"residual_AB38_bytes\":"<<residual_bytes
      <<",\"all_visible_encoder_decisions\":"<<all_decisions<<",\"residual_encoder_decisions\":"<<residual_decisions<<",\"residual_packet_sha256\":[";
    for(unsigned axis=0;axis<3;++axis) {if(axis)std::cout<<',';std::cout<<'\"'<<hashes[axis]<<'\"';}
    std::cout<<"],\"residual_packet_bytes\":[";
    for(unsigned axis=0;axis<3;++axis) {if(axis)std::cout<<',';std::cout<<sizes[axis];}
    std::cout<<"]}\n";++frames;
  }
  need(frames==457,"complete control corpus");std::cerr<<"V85_MATCHED_CONTROL_PASS frames="<<frames<<"\n";
}catch(const std::exception &e) {std::cerr<<"FAIL "<<e.what()<<'\n';return 1;} }
