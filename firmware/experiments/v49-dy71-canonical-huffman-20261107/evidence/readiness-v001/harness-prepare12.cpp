#include "native/endpoint.hpp"
#include <fstream>
#include <iterator>
#include <iostream>
#include <array>
#include <cstdlib>

static v34::Endpoint* endpoint=nullptr;
static size_t baseline=0,external=0,min_free=SIZE_MAX;
static size_t probe(){size_t used=endpoint->arena.live+external;size_t free=used>baseline?0:baseline-used;min_free=std::min(min_free,free);return free;}
static std::vector<uint8_t> read(const std::string&path){std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("input");return std::vector<uint8_t>{std::istreambuf_iterator<char>(f),{}};}
static uint32_t transact(v34::Endpoint&e,uint8_t op,uint32_t frame,uint32_t ref,uint32_t arg,const std::vector<uint8_t>&payload,std::array<uint8_t,1060>&out){
 std::vector<uint8_t> req(36+payload.size());std::memcpy(req.data(),"HC70",4);req[4]=1;req[5]=op;
 v34::put32(req.data()+8,payload.size());v34::put64(req.data()+12,frame+1);v34::put32(req.data()+20,frame);v34::put32(req.data()+24,ref);v34::put32(req.data()+28,arg);
 std::copy(payload.begin(),payload.end(),req.begin()+32);v34::put32(req.data()+32+payload.size(),cu66::crc32(cu66::View(req.data(),req.size()-4)));
 external=op==1?req.size():0;e.transact(cu66::View(req.data(),req.size()),out.data(),out.size());external=0;return v34::u32(out.data()+28);
}
int main(int argc,char**argv){
 if(argc!=3){return 2;}
 std::string golden_dir=argv[2];
 baseline=std::strtoull(argv[1],nullptr,10);
 v34::Endpoint e(98304);endpoint=&e;e.arena.free_probe=probe;e.arena.reserve=8192;
 std::array<uint8_t,1060> out{};size_t verified=0;
 for(unsigned frame=0;frame<12;++frame){
  auto wire=read("handheld/src/cu66/fixtures/prepare12/prepare"+std::to_string(frame)+".bin");
  uint32_t ref=v34::u32(wire.data()+24),nh=v34::u32(wire.data()+8);
  if(wire.size()!=nh+36)return 3;
  e.transact(cu66::View(wire.data(),wire.size()),out.data(),out.size());auto code=v34::u32(out.data()+28);
  std::cout<<"BASE "<<baseline<<" FRAME "<<frame<<" PREPARE_CODE "<<code<<" LIVE "<<e.arena.live<<" PEAK "<<e.arena.peak<<" MIN_MODELED_FREE "<<min_free<<" FAILURES "<<e.arena.failures<<" HU_WIRE "<<nh+36<<"\n";
  if(code!=0)return 9;
  std::array<uint8_t,16>tag{};std::copy(out.begin()+56,out.begin()+72,tag.begin());
  auto golden=read(golden_dir+"/frame"+std::to_string(frame)+".hud");
  if(golden.size()!=42240){return 6;}
  for(unsigned offset=0;offset<21120;offset+=256){unsigned count=std::min(256u,21120-offset);
   std::vector<uint8_t> arg(8);v34::put32(arg.data(),offset);v34::put32(arg.data()+4,count);
   if(transact(e,3,frame,ref,0,arg,out)!=0){return 7;}
   if(!std::equal(out.begin()+32,out.begin()+32+count*2,golden.begin()+offset*2)){return 8;}
   verified+=count;
  }
  std::vector<uint8_t> ack(20);v34::put32(ack.data(),21120);std::copy(tag.begin(),tag.end(),ack.begin()+4);
  if(transact(e,4,frame,ref,1,ack,out)!=0)return 4;
  if(transact(e,5,frame,ref,0,{},out)!=0)return 5;
 }
 std::cout<<"TWELVE_PREPARED_COMMITTED baseline "<<baseline<<" peak "<<e.arena.peak<<" min "<<min_free<<" HUD_WORDS_VERIFIED "<<verified<<"\n";
 auto key=read("handheld/src/cu66/fixtures/prepare12/prepare0.bin");
 v34::Endpoint limited(1024);limited.arena.reserve=8192;limited.arena.free_probe=[]()->size_t{return 150000;};
 limited.transact(cu66::View(key.data(),key.size()),out.data(),out.size());
 if(v34::u32(out.data()+28)!=4||limited.arena.failures==0)return 10;
 auto before=limited.arena.live;limited.transact(cu66::View(key.data(),key.size()),out.data(),out.size());
 if(v34::u32(out.data()+28)!=2||limited.arena.live!=before)return 11;
 std::cout<<"NEGATIVE_ALLOCATION_THROW_CAUGHT_AND_STALE_STATE_PRESERVED\n";
 return 0;
}
