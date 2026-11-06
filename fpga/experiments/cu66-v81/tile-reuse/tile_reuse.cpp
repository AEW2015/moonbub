// Native-only screening: exact canonical tile equality, no RTL or memory injection.
#include "../../../../experiments/cu66-native-v69/decoder.hpp"
#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <set>
using namespace cu66;
static Bytes load(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);need(bool(f),"fixture open");return {std::istreambuf_iterator<char>(f),{}};}
static std::vector<std::string> split(const std::string&s){std::vector<std::string>v;std::stringstream in(s);std::string x;while(std::getline(in,x,'\t'))v.push_back(x);return v;}
int main(int argc,char**argv){try{
 need(argc==2,"native index path required");std::filesystem::path index=argv[1];std::ifstream input(index);need(bool(input),"index open");
 Decoder decoder;int prior_cohort=-1;unsigned frames=0,keys=0;std::array<unsigned,4>counts{};std::string line;std::set<std::pair<int,unsigned>>seen;
 while(std::getline(input,line)){
  auto fields=split(line);need(fields.size()==6,"six index fields");int cohort=std::stoi(fields[0]);unsigned fid=unsigned(std::stoul(fields[1]));need(cohort>=0&&cohort<4,"cohort bound");
  if(cohort!=prior_cohort){need(cohort==prior_cohort+1,"ordered independent histories");decoder=Decoder();prior_cohort=cohort;}
  auto previous=decoder.state();auto packet=load(index.parent_path()/fields[2]);
  need(hex(sha256(packet))==std::filesystem::path(fields[2]).stem().string(),"content-addressed packet hash");
  auto current=decoder.receive(packet);need(current->id==fid&&seen.emplace(cohort,fid).second,"unique fixture identity");
  SHA256 canonical;for(const auto&p:current->planes)canonical.update(p);need(hex(canonical.finish())==fields[3],"full golden canonical digest");
  Bytes hud;for(const auto&p:current->hud){auto b=word_bytes(p.words);hud.insert(hud.end(),b.begin(),b.end());}
  need(hex(sha256(hud))==fields[4],"golden HUD digest");need(hex(sha256(word_bytes(current->display)))==fields[5],"golden display digest");
  std::cout<<"{\"cohort\":"<<cohort<<",\"ordinal\":"<<counts[cohort]<<",\"fid\":"<<fid<<",\"key\":"<<(current->key?"true":"false")<<",\"comparable\":"<<(previous?"true":"false")<<",\"previous_fid\":"<<(previous?std::to_string(previous->id):"null")<<",\"canonical_tag\":\""<<hex(current->canonical_tag)<<"\",\"planes\":[";
  for(unsigned plane=0;plane<3;plane++){
   const unsigned width=plane?360:720,tiles=plane?1350:5400;const auto*hidden=plane==0?SAFE0:plane==1?SAFE1:SAFE2;
   unsigned equal_visible=0,equal_hidden=0,hidden_count=0;Bytes mask((tiles+7)/8,0);
   for(unsigned tile=0;tile<tiles;tile++){
    bool equal=bool(previous);unsigned y=(tile/(width/8))*8,x=(tile%(width/8))*8;hidden_count+=hidden[tile]!=0;
    for(unsigned yy=0;yy<8;yy++)for(unsigned xx=0;xx<8;xx++){
     unsigned at=(y+yy)*width+x+xx;if(previous&&current->planes[plane][at]!=previous->planes[plane][at])equal=false;
     if(hidden[tile])need(current->planes[plane][at]==128,"fixed hidden canonical byte");
    }
    if(equal){mask[tile/8]|=uint8_t(1u<<(tile%8));if(hidden[tile])equal_hidden++;else equal_visible++;}
   }
   need(hidden_count==(plane==0?256u:19u),"fixed hidden tile count");
   std::cout<<(plane?",":"")<<"{\"plane\":"<<plane<<",\"tiles\":"<<tiles<<",\"hidden_tiles\":"<<hidden_count<<",\"same_visible\":"<<equal_visible<<",\"same_hidden\":"<<equal_hidden<<",\"same_mask_u8_lsb_hex\":\""<<hex(mask)<<"\"}";
  }
  std::cout<<"]}"<<std::endl;frames++;counts[cohort]++;keys+=current->key;
 }
 need(frames==457&&counts==std::array<unsigned,4>{119,119,119,100},"complete immutable corpus");
 std::cout<<"TILE_REUSE_NATIVE_PASS frames="<<frames<<" keys="<<keys<<" deltas="<<frames-keys<<" reset_per_history=1 native_only=1 rtl_changed=0"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
