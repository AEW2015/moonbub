#include "codec.hpp"
#include <fstream>
#include <iostream>
#include <random>
#include <filesystem>
using namespace cu66;
static unsigned checks=0,rejections=0;
static void check(bool v,const char *m) {need(v,m);++checks;}
static void reject(Bytes b,unsigned blocks) {bool failed=false;try {cu94::decode(b,blocks);}catch(const std::exception &) {failed=true;}if(!failed)std::cerr<<"accepted rejection index "<<rejections<<" checks "<<checks<<" selector "<<unsigned(b[6])<<" bytes "<<b.size()<<"\n";check(failed,"EC94 malformed accepted");++rejections;}
static void crc(Bytes &b) {b.resize(b.size()-4);cu85::put32(b,crc32(b));}
static void put(Bytes &b,size_t at,uint32_t v,unsigned width=4) {for(unsigned i=0;i<width;++i)b[at+i]=uint8_t(v>>(8*i));}
static void write(const std::filesystem::path &p,const Bytes &b) {std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),std::streamsize(b.size()));need(bool(f),"fixture write");}
int main(int argc,char **argv) {try {
  need(argc==2,"fixture output directory required");std::filesystem::path directory(argv[1]);std::filesystem::create_directories(directory);std::ofstream manifest(directory/"manifest.json");manifest<<"{\"schema\":\"ec94-native-fixtures-v1\",\"fixtures\":[";bool first=true;unsigned fixtures=0;
  std::mt19937 random(940062);
  for(unsigned family=0;family<6;++family) {
    unsigned blocks=family==4?1:64;std::vector<int16_t> values(blocks*64);
    for(size_t i=0;i<values.size();++i) {
      if(family==1&&i%11==0)values[i]=int16_t((int(i)%5-2)*1024);
      if(family==2&&random()%17==0)values[i]=int16_t(int(random()%4097)-2048);
      if(family==3)values[i]=(i%64==0)?int16_t(i%128?2048:-2048):int16_t(i%127==0?1:0);
      if(family>=4)values[i]=int16_t(int(random()%4097)-2048);
    }
    auto prepared=cu94::prepare(values);Bytes packed;for(auto value:values)cu85::put16(packed,uint16_t(value));
    for(unsigned scale=8;scale<=10;++scale)for(unsigned selector=0;selector<256;++selector) {
      auto packet=cu94::assemble(prepared,selector,scale);check(cu94::decode(packet,blocks)==values,"EC94 fixture parity");
      std::string name="family"+std::to_string(family)+"-scale"+std::to_string(scale)+"-selector"+std::to_string(selector)+".ec94";write(directory/name,packet);if(!first)manifest<<',';first=false;++fixtures;
      manifest<<"{\"path\":\""<<name<<"\",\"blocks\":"<<blocks<<",\"requested_selector\":"<<selector<<",\"scale\":"<<scale<<",\"wire_selector\":"<<unsigned(packet[6])<<",\"raw\":"<<(packet[5]?"true":"false")<<",\"coefficient_sha256\":\""<<hex(sha256(packed))<<"\",\"sha256\":\""<<hex(sha256(packet))<<"\"}";
      for(unsigned at: {0u,4u,5u,7u,8u,12u,14u,16u}) {auto bad=packet;bad[at]^=128;crc(bad);reject(bad,blocks);}
      auto bad=packet;bad.at(bad.size()-1)^=1;reject(bad,blocks);bad=packet;bad.push_back(0);reject(bad,blocks);
      if(selector==0)for(size_t cut=0;cut<48;++cut)reject(Bytes(packet.begin(),packet.begin()+std::ptrdiff_t(cut)),blocks);
      if(packet[5]) {bad=packet;bad[6]=1;crc(bad);reject(bad,blocks);bad=packet;bad[44]=255;bad[45]=127;crc(bad);reject(bad,blocks);}
      else {Reader lengths(View(packet).sub(16,16));size_t offset=44;for(unsigned context=0;context<4;++context) {unsigned length=lengths.u32(),method=(selector>>(2*context))&3;
        bad=packet;bad[offset]=255;crc(bad);reject(bad,blocks);
        if(method>=2) {
          for(unsigned at: {2u,3u,4u,8u,12u,16u}) {bad=packet;bad[offset+at]^=128;crc(bad);reject(bad,blocks);}
          bad=packet;bad[offset+3]=1;crc(bad);reject(bad,blocks);
          unsigned tables=context?64:32,state_at=unsigned(offset)+20+tables;
          bad=packet;put(bad,state_at,0);crc(bad);reject(bad,blocks);bad=packet;put(bad,state_at,1u<<31);crc(bad);reject(bad,blocks);
          
          bad=packet;put(bad,offset+20,0xffff,2);put(bad,offset+4,crc32(View(bad).sub(offset+20,tables)));crc(bad);reject(bad,blocks);
          Reader desc(View(packet).sub(offset,length));desc.u32();desc.u32();auto ans_bytes=desc.u32(),bits=desc.u32();
          if(bits%8) {bad=packet;bad[offset+20+tables+ans_bytes+(bits-1)/8]|=1;crc(bad);reject(bad,blocks);}
        }offset+=length;
      }}
    }
  }
  // Force rare and escape categories in bounded primitive streams independently
  // of the whole-plane best_k choice; prove model normalization and all lanes.
  for(unsigned scale=8;scale<=10;++scale) {
    std::array<uint64_t,16> hist{};auto empty=cu94::normalize(hist,scale);for(auto f:empty)check(f==(1u<<scale)/16,"empty model");hist[15]=1;auto single=cu94::normalize(hist,scale);check(single[15]==1u<<scale,"single category model");hist[0]=99999;hist[1]=1;auto rare=cu94::normalize(hist,scale);check(rare[1]>0&&rare[15]>0,"rare categories retained");
    for(unsigned lanes: {2u,4u})for(unsigned context=0;context<2;++context) {std::vector<uint32_t> a(1024),b(context?1024:0);a.back()=context?0xffffff:0x3fff;if(context)b.back()=0xfff;cu94::DecodeStats stats;auto stream=cu94::encode_stream(a,b,context,lanes,scale,stats);size_t i=0;cu94::read_stream(stream,lanes==2?2:3,context,unsigned(a.size()),[&](uint32_t x,uint32_t y) {check(x==a[i]&&(!context||y==b[i]),"primitive parity");++i;});}
  }
  manifest<<"],\"context_fixtures\":[";bool first_context=true;
  for(unsigned scale=8;scale<=10;++scale)for(unsigned lanes: {2u,4u})for(unsigned context=0;context<2;++context)for(unsigned family=0;family<3;++family) {
    std::vector<uint32_t> a(family==0?0:1024),b(context?a.size():0);if(family==2) {a.back()=context?0xffffff:0x3fff;if(context)b.back()=0xfff;}
    cu94::DecodeStats stats;auto stream=cu94::encode_stream(a,b,context,lanes,scale,stats);unsigned method=lanes==2?2:3;
    std::string name="context-f"+std::to_string(family)+"-c"+std::to_string(context)+"-n"+std::to_string(lanes)+"-s"+std::to_string(scale)+".stream";write(directory/name,stream);
    if(!first_context)manifest<<',';
    first_context=false;manifest<<"{\"path\":\""<<name<<"\",\"name\":\""<<(family==0?"empty":family==1?"single":"rare_escape")<<"\",\"context\":"<<context<<",\"method\":"<<method<<",\"events\":"<<a.size()<<",\"symbol_count\":"<<a.size()*(context?2:1)<<",\"fields\":[";
    for(size_t i=0;i<a.size();++i) {if(i)manifest<<',';manifest<<a[i];if(context)manifest<<','<<b[i];}manifest<<"]}";
    if(family==1) {auto malformed=stream;unsigned state_at=20+(context?64:32);put(malformed,state_at,cu94::L+1);bool failed=false;try {cu94::read_stream(malformed,method,context,unsigned(a.size()),[](uint32_t,uint32_t){});}catch(const std::exception &) {failed=true;}check(failed,"terminal state rejected");++rejections;}
  }
  manifest<<"]}\n";need(bool(manifest),"manifest write");std::cout<<"{\"status\":\"PASS\",\"families\":6,\"fixtures\":"<<fixtures<<",\"checks\":"<<checks<<",\"rejections\":"<<rejections<<"}\n";return 0;
}catch(const std::exception &e) {std::cerr<<"EC94_TEST_FAIL "<<e.what()<<'\n';return 1;}}
