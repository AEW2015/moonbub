#include "decoder.hpp"
#include <fstream>
#include <iostream>
using namespace cu66;
Bytes readfile(const std::string &p) {
  std::ifstream f(p, std::ios::binary); need(bool(f), "open");
  return Bytes(std::istreambuf_iterator<char>(f), {});
}
Bytes signature(const std::shared_ptr<const Frame>& f) {
  if (!f) return {};
  Bytes b;
  for (const auto& p:f->planes) b.insert(b.end(),p.begin(),p.end());
  for (const auto& p:f->hud) { auto v=word_bytes(p.words);b.insert(b.end(),v.begin(),v.end()); }
  auto v=word_bytes(f->display);b.insert(b.end(),v.begin(),v.end());
  return b;
}
void seal(Bytes& p) {
  auto c=crc32(View(p.data(),p.size()-4));
  for(unsigned i=0;i<4;i++)p[p.size()-4+i]=uint8_t(c>>(8*i));
}
int main(int argc,char** argv) {
  try {
    need(argc==3,"sequence directory and count required");std::string dir=argv[1];auto count=std::stoul(argv[2]);need(count>=3&&count<=12,"count3..12");
    auto key=readfile(dir+"/frame000.cu66"),p1=readfile(dir+"/frame001.cu66"),p2=readfile(dir+"/frame002.cu66");
    Decoder rx;unsigned rejected=0;
    auto reject=[&](const Bytes& packet) {
      auto before=rx.state();auto bytes=signature(before);bool failed=false;
      try { rx.receive(packet); } catch(const std::exception&) {failed=true;}
      need(failed,"negative unexpectedly accepted");need(rx.state()==before,"failed publish pointer changed");
      need(signature(before)==bytes,"prior output mutated");rejected++;
    };
    reject(p1); // Missing KEY/reference.
    for(size_t cut:{size_t(0),size_t(79),key.size()-1})reject(Bytes(key.begin(),key.begin()+cut));
    auto bad=key;bad[100]^=1;reject(bad);
    auto accepted=rx.receive(key);auto retained=signature(accepted);reject(key); // Replay.
    bad=p1;bad[40]^=1;seal(bad);reject(bad); // Reference binding/CRC-repaired packet.
    for(size_t cut:{size_t(80),p1.size()-4})reject(Bytes(p1.begin(),p1.begin()+cut));
    bad=p1;bad[bad.size()-10]^=1;seal(bad);reject(bad); // Late HUD integrity failure.
    rx.receive(p1);need(signature(accepted)==retained,"older successful output mutated");
    reject(p1);rx.receive(p2);need(signature(accepted)==retained,"older key changed after P2");
    for(unsigned fid=3;fid<count;fid++){
      auto packet=readfile(dir+"/frame"+std::string(fid<10?"00":"0")+std::to_string(fid)+".cu66");
      reject(Bytes(packet.begin(),packet.end()-1));auto corrupt=packet;corrupt[corrupt.size()-10]^=1;seal(corrupt);reject(corrupt);
      rx.receive(packet);reject(packet);need(signature(accepted)==retained,"earlier KEY mutated");
    }
    std::cout<<"{\"negative_cases\":"<<rejected<<",\"final_frame\":"<<rx.state()->id<<",\"rollback_and_prior_ownership\":true}\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<e.what()<<"\n";return 1; }
}
