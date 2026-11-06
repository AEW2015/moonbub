// Frozen decoder validates independently; the fork only observes c[64] pre-IDCT.
#include "../../cu66-native-v69/decoder.hpp"
#include "instrumented_decoder.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
using namespace cu66;
static Bytes load(const std::filesystem::path &p) {
  std::ifstream f(p, std::ios::binary); need(bool(f), "fixture open");
  return {std::istreambuf_iterator<char>(f), {}};
}
static std::vector<std::string> split(const std::string &s) {
  std::vector<std::string> v; std::stringstream in(s); std::string x;
  while (std::getline(in, x, '\t')) v.push_back(x);
  return v;
}
static void write_bytes(std::ostream &out, const Bytes &v) {
  out.write(reinterpret_cast<const char *>(v.data()), v.size());
}
static void write_u32(std::ostream &out, uint32_t n) {
  for (unsigned i=0; i<4; ++i) out.put(char(n >> (8*i)));
}
int main(int argc, char **argv) { try {
  need(argc == 2, "index argument required");
  std::filesystem::path index = argv[1]; std::ifstream input(index);
  need(bool(input), "oracle input open");
  Decoder decoder; InstrumentedDecoder instrumented;
  int prior_cohort = -1; unsigned frames = 0, keys = 0;
  std::array<unsigned,4> counts{}; std::string line;
  std::set<std::pair<int,unsigned>> seen;
  uint64_t safe_copy=0, oracle_copy=0, zero_hidden=0, nonzero_equal=0;
  while (std::getline(input,line)) {
    auto f=split(line); need(f.size()==6,"six index fields");
    int cohort=std::stoi(f[0]); unsigned fid=unsigned(std::stoul(f[1]));
    need(cohort>=0 && cohort<4,"cohort bound");
    if(cohort!=prior_cohort) {
      need(cohort==prior_cohort+1,"ordered histories");
      decoder=Decoder(); instrumented=InstrumentedDecoder(); prior_cohort=cohort;
    }
    auto previous=decoder.state(); auto packet=load(index.parent_path()/f[2]);
    auto packet_hash=hex(sha256(packet));
    need(packet_hash==std::filesystem::path(f[2]).stem().string(),"packet SHA256");
    auto current=decoder.receive(packet); auto trace=instrumented.receive(packet);
    need(current->planes==trace->planes,"independent frozen/fork complete plane byte equality");
    need(current->id==fid && seen.emplace(cohort,fid).second,"unique fixture");
    SHA256 canonical; for(const auto &p:current->planes) canonical.update(p);
    need(hex(canonical.finish())==f[3],"golden canonical SHA256");
    Bytes hud; for(const auto &p:current->hud) {
      auto b=word_bytes(p.words); hud.insert(hud.end(),b.begin(),b.end());
    }
    need(hex(sha256(hud))==f[4],"golden HUD SHA256");
    need(hex(sha256(word_bytes(current->display)))==f[5],"golden display SHA256");
    Reader r{View(packet).sub(68,8)}; unsigned nb=r.u32(), nh=r.u32();
    need(76+nb+nh+4==packet.size(),"encoded body sizes");
    auto base=View(packet).sub(76,nb), encoded_hud=View(packet).sub(76+nb,nh);
    Bytes tiles, same, zero_coeff, hidden, copy;
    tiles.reserve(8100*64); unsigned frame_copy=0, frame_equal=0, frame_nonzero_equal=0;
    for(unsigned axis=0;axis<3;++axis) {
      unsigned w=axis?360:720, nt=axis?1350:5400;
      const auto *safe=axis==0?SAFE0:axis==1?SAFE1:SAFE2;
      need(trace->zero_coefficients[axis].size()==nt,"coefficient coverage");
      unsigned nhidden=0;
      for(unsigned b=0;b<nt;++b) {
        unsigned by=b/(w/8), bx=b%(w/8); bool equal=bool(previous);
        for(unsigned y=0;y<8;++y) for(unsigned x=0;x<8;++x) {
          auto at=(by*8+y)*w+bx*8+x; auto value=current->planes[axis][at];
          tiles.push_back(value);
          if(previous && value!=previous->planes[axis][at]) equal=false;
          if(safe[b]) need(value==128,"hidden CONST128 byte");
        }
        bool z=trace->zero_coefficients[axis][b];
        bool cp=!current->key && !safe[b] && z;
        need(!cp || equal,"all zero coefficient COPY must be byte equal");
        same.push_back(equal); zero_coeff.push_back(z); hidden.push_back(safe[b]!=0); copy.push_back(cp);
        if(safe[b]) { ++nhidden; zero_hidden+=z; }
        if(cp) ++frame_copy;
        if(!current->key && !safe[b] && equal) { ++frame_equal; if(!z) ++frame_nonzero_equal; }
      }
      need(nhidden==(axis==0?256u:19u),"294 hidden tiles per frame");
    }
    safe_copy+=frame_copy; oracle_copy+=frame_equal; nonzero_equal+=frame_nonzero_equal;
    std::ostringstream meta;
    meta << "{\"cohort\":"<<cohort<<",\"ordinal\":"<<counts[cohort]
      <<",\"fid\":"<<fid<<",\"refid\":"<<current->reference_id
      <<",\"key\":"<<(current->key?"true":"false")
      <<",\"previous_fid\":"<<(previous?std::to_string(previous->id):"null")
      <<",\"encoded_base_bytes\":"<<nb<<",\"hud_bytes\":"<<nh
      <<",\"packet_bytes\":"<<packet.size()<<",\"packet_sha256\":\""<<packet_hash
      <<"\",\"canonical_sha256\":\""<<f[3]<<"\",\"hud_sha256\":\""<<f[4]
      <<"\",\"display_sha256\":\""<<f[5]<<"\",\"canonical_tag\":\""<<hex(current->canonical_tag)
      <<"\",\"encoded_base_sha256\":\""<<hex(sha256(base))
      <<"\",\"encoded_hud_sha256\":\""<<hex(sha256(encoded_hud))
      <<"\",\"copy_ref_count\":"<<frame_copy<<",\"same_visible_delta_count\":"<<frame_equal
      <<",\"nonzero_equal_visible_delta_count\":"<<frame_nonzero_equal<<"}";
    auto m=meta.str(); write_u32(std::cout,uint32_t(m.size())); std::cout.write(m.data(),m.size());
    write_bytes(std::cout,tiles); write_bytes(std::cout,same); write_bytes(std::cout,zero_coeff);
    write_bytes(std::cout,hidden); write_bytes(std::cout,copy);
    need(bool(std::cout),"binary output complete"); ++frames; ++counts[cohort]; keys+=current->key;
  }
  need(frames==457 && keys==20 && counts==std::array<unsigned,4>{119,119,119,100},"complete corpus");
  std::cerr<<"NATIVE_V82_PASS frames="<<frames<<" keys="<<keys<<" deltas="<<frames-keys
    <<" safe_zero_copy="<<safe_copy<<" oracle_equal_visible_delta="<<oracle_copy
    <<" nonzero_equal_visible_delta="<<nonzero_equal<<" hidden_zero="<<zero_hidden
    <<" frozen_packet_canonical_hud_display=1 complete_plane_crosscheck=1\n";
} catch(const std::exception &e) { std::cerr<<"FAIL "<<e.what()<<std::endl; return 1; } }
