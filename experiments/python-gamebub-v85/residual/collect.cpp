#include "../../cu66-native-v69/decoder.hpp"
#include "encode.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
using namespace cu66;
static Bytes load(const std::filesystem::path &path) {
  std::ifstream f(path,std::ios::binary);need(bool(f),"fixture open");
  return {std::istreambuf_iterator<char>(f),{}};
}
static std::vector<std::string> split(const std::string &line) {
  std::vector<std::string> out;std::stringstream input(line);std::string value;
  while(std::getline(input,value,'\t'))out.push_back(value);
  return out;
}
static void write32(uint32_t value) {for(unsigned i=0;i<4;++i)std::cout.put(char(value>>(i*8)));}
static void write_bytes(const Bytes &bytes) {std::cout.write(reinterpret_cast<const char *>(bytes.data()),bytes.size());}
struct Chunk {unsigned blocks;cu85::Encoded encoded;};
struct Variant {
  std::array<std::vector<Chunk>,3> planes;
  uint64_t bytes=0,chunks=0,raw=0,max_bytes=0;
  std::array<uint64_t,4> attempted_decisions{},attempted_renorm{};
};
int main(int argc,char **argv) {try {
  need(argc==2,"fixture index required");std::filesystem::path index=argv[1];std::ifstream input(index);
  need(bool(input),"fixture index open");std::string line;int prior=-1;Decoder decoder;
  unsigned frames=0,keys=0;std::array<unsigned,4> history{};
  const unsigned caps[4]={16,64,256,65536};uint64_t chunks_checked=0,coefficients_checked=0;
  while(std::getline(input,line)) {
    auto fields=split(line);need(fields.size()==6,"index fields");int cohort=std::stoi(fields[0]);unsigned fid=unsigned(std::stoul(fields[1]));
    need(cohort>=0 && cohort<4,"cohort bound");
    if(cohort!=prior) {need(cohort==prior+1,"ordered histories");decoder=Decoder();prior=cohort;}
    auto packet=load(index.parent_path()/fields[2]);std::string packet_sha=hex(sha256(packet));
    need(packet_sha==std::filesystem::path(fields[2]).stem().string(),"original packet SHA");
    auto current=decoder.receive(packet);need(current->id==fid,"frame identity");
    SHA256 canonical;for(const auto &p:current->planes)canonical.update(p);
    need(hex(canonical.finish())==fields[3],"original canonical SHA");
    Bytes semantic_hud;for(const auto &patch:current->hud) {auto b=word_bytes(patch.words);semantic_hud.insert(semantic_hud.end(),b.begin(),b.end());}
    need(hex(sha256(semantic_hud))==fields[4],"original HUD SHA");
    need(hex(sha256(word_bytes(current->display)))==fields[5],"original display SHA");
    Reader outer{View(packet).sub(68,packet.size()-68-4)};unsigned base_bytes=outer.u32(),hud_bytes=outer.u32();
    auto original_base=outer.take(base_bytes),original_hud=outer.take(hud_bytes);outer.end();
    Reader gu(original_base.sub(0,original_base.n-4));
    gu.take(22);unsigned block_size=gu.u8();need(gu.u8()==18,"native profile limit");gu.take(16);
    unsigned nq=gu.u32(),nv=gu.u32();std::array<unsigned,3> length{};for(auto &v:length)v=gu.u32();
    need(nq==338,"qmap fixed length");auto quant=gu.take(nq);gu.take(nv);
    Bytes qmap(quant.p,quant.p+quant.n),hud(original_hud.p,original_hud.p+original_hud.n);
    std::array<std::vector<int16_t>,3> residual;
    std::array<unsigned,3> residual_counts{};std::string zeros;zeros.reserve(8100);Bytes canonical_coefficients;canonical_coefficients.reserve(8100*128);
    for(unsigned axis=0;axis<3;++axis) {
      unsigned blocks=axis?1350:5400,bw=axis?45:90;const auto *safe=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
      Reader plane(gu.take(length[axis]));unsigned dispatch=plane.u8();need(dispatch==5 || dispatch==6,"native AB38 dispatch");
      unsigned visible=0;for(unsigned b=0;b<blocks;++b)visible+=!safe[b];
      unsigned encoded=dispatch==6?visible:blocks;
      auto coefficients=decode_ab38(plane.take(plane.v.n-plane.pos),encoded,dispatch==6?1:bw);plane.end();
      unsigned cursor=0;
      for(unsigned b=0;b<blocks;++b) {
        std::array<int16_t,64> c{};
        if(dispatch!=6 || !safe[b]) {std::copy(coefficients.begin()+cursor*64,coefficients.begin()+(cursor+1)*64,c.begin());++cursor;}
        bool zero=std::all_of(c.begin(),c.end(),[](int value){return value==0;});zeros.push_back(zero?'1':'0');
        need(!safe[b] || zero,"hidden coefficients zero");
        for(auto value:c)cu85::put16(canonical_coefficients,uint16_t(value));
        if(!safe[b] && (current->key || !zero)) {residual[axis].insert(residual[axis].end(),c.begin(),c.end());++residual_counts[axis];}
      }
      need(cursor==encoded,"original coefficient coverage");
    }
    gu.end();need(zeros.size()==8100,"canonical mask coverage");
    std::array<Variant,4> variants;
    for(unsigned vi=0;vi<4;++vi)for(unsigned axis=0;axis<3;++axis) {
      auto &variant=variants[vi];unsigned blocks=residual_counts[axis];
      for(unsigned start=0;start<blocks;start+=caps[vi]) {
        unsigned count=std::min(caps[vi],blocks-start);
        std::vector<int16_t> coefficients(residual[axis].begin()+start*64,residual[axis].begin()+(start+count)*64);
        auto encoded=cu85::encode(coefficients);variant.bytes+=encoded.packet.size();++variant.chunks;variant.raw+=encoded.raw;
        variant.max_bytes=std::max<uint64_t>(variant.max_bytes,encoded.packet.size());
        for(unsigned stream=0;stream<4;++stream) {variant.attempted_decisions[stream]+=encoded.decisions[stream];variant.attempted_renorm[stream]+=encoded.renorm[stream];}
        variant.planes[axis].push_back({count,std::move(encoded)});++chunks_checked;coefficients_checked+=uint64_t(count)*64;
      }
    }
    std::ostringstream meta;
    meta<<"{\"cohort\":"<<cohort<<",\"ordinal\":"<<history[cohort]<<",\"fid\":"<<fid<<",\"refid\":"<<current->reference_id
      <<",\"key\":"<<(current->key?"true":"false")<<",\"block_size\":"<<block_size
      <<",\"packet_path\":\""<<fields[2]<<"\",\"packet_bytes\":"<<packet.size()<<",\"encoded_base_bytes\":"<<base_bytes<<",\"hud_bytes\":"<<hud.size()
      <<",\"packet_sha256\":\""<<packet_sha<<"\",\"canonical_sha256\":\""<<fields[3]<<"\",\"hud_sha256\":\""<<fields[4]<<"\",\"display_sha256\":\""<<fields[5]
      <<"\",\"canonical_coefficients_sha256\":\""<<hex(sha256(canonical_coefficients))<<"\",\"zero_mask\":\""<<zeros<<"\",\"residual_counts\":[";
    for(unsigned axis=0;axis<3;++axis) {if(axis)meta<<',';meta<<residual_counts[axis];}
    meta<<"],\"variant_stats\":{ ";
    for(unsigned vi=0;vi<4;++vi) {
      if(vi)meta<<',';
      const auto &v=variants[vi];meta<<'\"'<<caps[vi]<<"\":{\"AB38_bytes\":"<<v.bytes<<",\"chunks\":"<<v.chunks<<",\"raw_chunks\":"<<v.raw<<",\"max_chunk_bytes\":"<<v.max_bytes<<",\"attempted_encoder_decisions\":[";
      for(unsigned i=0;i<4;++i) {if(i)meta<<',';meta<<v.attempted_decisions[i];}
      meta<<"],\"attempted_encoder_renorm\":[";
      for(unsigned i=0;i<4;++i) {if(i)meta<<',';meta<<v.attempted_renorm[i];}
      meta<<"]}";
    }
    meta<<"}}";auto json=meta.str();write32(uint32_t(json.size()));std::cout.write(json.data(),json.size());
    write32(uint32_t(qmap.size()));write_bytes(qmap);write32(uint32_t(hud.size()));write_bytes(hud);
    for(const auto &variant:variants)for(const auto &plane:variant.planes) {
      write32(uint32_t(plane.size()));for(const auto &chunk:plane) {write32(chunk.blocks);write32(uint32_t(chunk.encoded.packet.size()));write_bytes(chunk.encoded.packet);}
    }
    need(bool(std::cout),"complete component stream");++history[cohort];++frames;keys+=current->key;
    if(frames%25==0)std::cerr<<"RESIDUAL_PROGRESS frames="<<frames<<" chunks="<<chunks_checked<<'\n';
  }
  need(frames==457 && keys==20 && history==std::array<unsigned,4>{119,119,119,100},"full residual corpus");
  std::cerr<<"NATIVE_V85_RESIDUAL_PASS frames="<<frames<<" keys="<<keys<<" chunks="<<chunks_checked<<" coefficient_values="<<coefficients_checked<<" original_digest_parity=1 generated_chunk_native_decode_parity=1\n";
}catch(const std::exception &e) {std::cerr<<"FAIL "<<e.what()<<'\n';return 1;} }
