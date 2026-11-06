#include "../../cu66-native-v69/decoder.hpp"
#include "trace.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <set>
using namespace cu66;
static Bytes load(const std::filesystem::path &p) {
  std::ifstream f(p,std::ios::binary);need(bool(f),"fixture open");
  return {std::istreambuf_iterator<char>(f),{}};
}
static std::vector<std::string> split(const std::string &s) {
  std::vector<std::string> v;std::stringstream f(s);std::string x;
  while(std::getline(f,x,'\t'))v.push_back(x);
  return v;
}
static void emit(const cu84::Work &w) {
  std::cout<<'['<<w.decisions<<','<<w.renorm<<','<<w.stream_bytes<<','<<w.rice_values
    <<','<<w.events<<','<<w.raw_bytes<<','<<w.header_bytes<<','<<w.crc_bytes<<','
    <<w.emits<<','<<w.raw_bits<<','<<w.prob_init<<']';
}
int main(int argc,char **argv) {try {
  need(argc==2,"input index required");std::filesystem::path index=argv[1];
  std::ifstream input(index);need(bool(input),"index open");
  Decoder decoder;int old=-1;std::array<unsigned,4> ordinal{};
  unsigned frames=0,planes=0,keys=0;uint64_t decisions=0,renorm=0,zero=0;
  std::string line;
  while(std::getline(input,line)) {
    auto f=split(line);need(f.size()==6,"index fields");
    int cohort=std::stoi(f[0]);need(cohort>=0&&cohort<4,"cohort range");
    if(old!=cohort) {need(cohort==old+1,"history order");decoder=Decoder();old=cohort;}
    auto packet=load(index.parent_path()/f[2]);auto digest=hex(sha256(packet));
    need(digest==std::filesystem::path(f[2]).stem().string(),"packet SHA");
    auto current=decoder.receive(packet);need(current->id==unsigned(std::stoul(f[1])),"frame identity");
    SHA256 canonical;for(const auto &p:current->planes)canonical.update(p);
    need(hex(canonical.finish())==f[3],"canonical golden SHA");
    Bytes hud;for(const auto &p:current->hud) {auto bytes=word_bytes(p.words);hud.insert(hud.end(),bytes.begin(),bytes.end());}
    need(hex(sha256(hud))==f[4],"HUD golden SHA");
    need(hex(sha256(word_bytes(current->display)))==f[5],"display golden SHA");
    Reader sizes{View(packet).sub(68,8)};auto nb=sizes.u32(),nh=sizes.u32();
    need(80+nb+nh==packet.size(),"packet lengths");
    auto inner=View(packet).sub(76,nb);Reader q(inner.sub(0,inner.n-4));
    q.take(40);auto nq=q.u32(),nv=q.u32();std::array<unsigned,3> lengths{};
    for(auto &n:lengths)n=q.u32();
    q.take(nq);q.take(nv);
    std::vector<cu84::Work> work;work.reserve(8100);std::string zero_mask;
    std::array<unsigned,3> dispatches{},plane_bytes{};
    std::array<std::string,3> coefficient_digests{};
    for(unsigned axis=0;axis<3;++axis) {
      unsigned w=axis?360:720,blocks=axis?1350:5400;
      const auto *hidden=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
      Reader body(q.take(lengths[axis]));auto dispatch=body.u8();
      need(dispatch==5||dispatch==6,"plane dispatch");dispatches[axis]=dispatch;
      unsigned visible=0;for(unsigned b=0;b<blocks;++b)visible+=!hidden[b];
      auto encoded=dispatch==6?visible:blocks;auto bw=dispatch==6?1:w/8;
      auto encoded_body=body.take(body.v.n-body.pos);plane_bytes[axis]=unsigned(encoded_body.n);
      auto observed=cu84::decode_interleaved(encoded_body,encoded,bw);
      auto frozen=decode_ab38(encoded_body,encoded,bw);
      need(observed.coefficients==frozen,"interleaved coefficients vs frozen bulk exact");
      Bytes coefficient_bytes;coefficient_bytes.reserve(frozen.size()*2);
      for(auto c:frozen)put16(coefficient_bytes,uint16_t(c));
      coefficient_digests[axis]=hex(sha256(coefficient_bytes));
      unsigned cursor=0;
      for(unsigned b=0;b<blocks;++b) {
        cu84::Work item{};bool iszero=true;
        if(dispatch!=6||!hidden[b]) {
          item=observed.work[cursor];
          for(unsigned i=0;i<64;++i)iszero&=frozen[cursor*64+i]==0;
          ++cursor;
        }
        need(!hidden[b]||iszero,"hidden zero coefficients");
        zero_mask.push_back(iszero?'1':'0');zero+=iszero;item.emits=1;
        work.push_back(item);decisions+=item.decisions;renorm+=item.renorm;
      }
      need(cursor==encoded,"plane coverage");++planes;
    }
    q.end();need(work.size()==8100,"tile coverage");
    std::cout<<"{\"cohort\":"<<cohort<<",\"ordinal\":"<<ordinal[cohort]++
      <<",\"fid\":"<<current->id<<",\"key\":"<<(current->key?"true":"false")
      <<",\"packet_sha256\":\""<<digest<<"\",\"canonical_sha256\":\""<<f[3]
      <<"\",\"hud_sha256\":\""<<f[4]<<"\",\"display_sha256\":\""<<f[5]
      <<"\",\"zero_mask\":\""<<zero_mask<<"\",\"dispatches\":["<<dispatches[0]<<','<<dispatches[1]<<','<<dispatches[2]
      <<"],\"plane_bytes\":["<<plane_bytes[0]<<','<<plane_bytes[1]<<','<<plane_bytes[2]
      <<"],\"coefficient_sha256\":[\""<<coefficient_digests[0]<<"\",\""<<coefficient_digests[1]<<"\",\""<<coefficient_digests[2]
      <<"\"],\"work\":[";
    for(unsigned i=0;i<work.size();++i){if(i)std::cout<<',';emit(work[i]);}
    std::cout<<"]}\n";need(bool(std::cout),"trace output");++frames;keys+=current->key;
  }
  need(frames==457&&keys==20&&ordinal==std::array<unsigned,4>{119,119,119,100},"complete corpus");
  std::cerr<<"V84_NATIVE_ENTROPY_PASS frames="<<frames<<" planes="<<planes<<" keys="<<keys
    <<" decisions="<<decisions<<" renorm="<<renorm<<" zero_tiles="<<zero
    <<" frozen_coefficient_equality=1 packet_canonical_hud_display=1\n";
}catch(const std::exception &e){std::cerr<<"FAIL "<<e.what()<<'\n';return 1;}}
