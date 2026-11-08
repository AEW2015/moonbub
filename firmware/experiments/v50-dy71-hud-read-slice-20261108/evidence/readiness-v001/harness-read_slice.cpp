#include "native/endpoint.hpp"
#include "native/endpoint_c.h"
#include <fstream>
#include <iterator>
#include <iostream>
#include <iomanip>
#include <cassert>
using Bytes=std::vector<uint8_t>;
static Bytes file(const std::string&p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
static void crc(Bytes&b){v34::put32(b.data()+b.size()-4,cu66::crc32({b.data(),b.size()-4}));}
static Bytes request(uint8_t op,uint64_t gen,uint32_t f,uint32_t ref,uint32_t arg,const Bytes&p){Bytes b(36+p.size());std::memcpy(b.data(),"HC70",4);b[4]=1;b[5]=op;v34::put32(b.data()+8,p.size());v34::put64(b.data()+12,gen);v34::put32(b.data()+20,f);v34::put32(b.data()+24,ref);v34::put32(b.data()+28,arg);std::copy(p.begin(),p.end(),b.begin()+32);crc(b);return b;}
static Bytes read_request(uint64_t gen,uint32_t f,uint32_t ref,uint32_t off,uint32_t count){Bytes p(8);v34::put32(p.data(),off);v34::put32(p.data()+4,count);return request(3,gen,f,ref,0,p);}
static uint32_t accepted_crc(const v34::Endpoint&e){auto p=e.gate->accepted();if(!p)return 0;Bytes words;for(const auto&patch:p->patches)for(auto w:patch.words){words.push_back(uint8_t(w));words.push_back(uint8_t(w>>8));}assert(words.size()==42240);return cu66::crc32({words.data(),words.size()});}
static uint64_t rng=500711;static uint32_t random32(){rng^=rng<<13;rng^=rng>>7;rng^=rng<<17;return uint32_t(rng);}
struct Checks{explicit Checks(v34::Endpoint&x):e(x){}
 v34::Endpoint&e;cu66::SHA256 digest;size_t cases=0,valid_reads=0,errors=0;std::array<uint8_t,42308> out{};
 void observe(const Bytes&b,size_t cap,int expected_rc,uint32_t code,uint32_t off,uint32_t count,const Bytes*golden=nullptr,size_t input_n=SIZE_MAX){
  const auto live=e.arena.live,peak=e.arena.peak,allocations=e.arena.allocations;auto accepted=e.gate->accepted();auto native_tag=accepted?accepted->tag:cu66::Tag{};auto pointer=accepted.get();
  out.fill(0xa5);size_t n=12345;auto rc=v34_hud_transact(&e,b.data(),input_n==SIZE_MAX?b.size():input_n,out.data(),cap,&n);
  assert(rc==expected_rc);if(rc){++errors;assert(n==0);for(auto x:out)assert(x==0xa5);}else{
   assert(n>=36&&n<=cap);assert(std::memcmp(out.data(),"HR70",4)==0&&out[4]==1&&out[5]==b[5]&&out[6]==0&&out[7]==0);assert(!std::memcmp(out.data()+12,b.data()+12,16));assert(v34::u32(out.data()+28)==code);assert(v34::u32(out.data()+8)==n-36);assert(cu66::crc32({out.data(),n-4})==v34::u32(out.data()+n-4));
   if(code==0&&b[5]==3){assert(n==36+2*size_t(count));assert(golden&&golden->size()==42240);assert(std::equal(out.begin()+32,out.begin()+32+2*count,golden->begin()+2*size_t(off)));++valid_reads;}
   for(size_t i=n;i<out.size();++i)assert(out[i]==0xa5);
  }
  assert(e.arena.live==live&&e.arena.peak==peak&&e.arena.allocations==allocations);assert(e.gate->accepted().get()==pointer);if(accepted)assert(e.gate->accepted()->tag==native_tag);
  uint8_t meta[16];v34::put64(meta,cases++);v34::put32(meta+8,uint32_t(rc));v34::put32(meta+12,uint32_t(n));digest.update({meta,sizeof meta});digest.update({b.data(),input_n==SIZE_MAX?b.size():input_n});if(!rc)digest.update({out.data(),n});
 }
};
int main(int argc,char**argv){assert(argc==3);std::string fixtures=argv[1],goldens=argv[2];v34::Endpoint e(98304);Checks c{e};Bytes output(42276);
 auto transact=[&](const Bytes&b){auto n=e.transact({b.data(),b.size()},output.data(),output.size());assert(n>=36&&v34::u32(output.data()+28)==0);};
 // No candidate: a valid READ is a status failure, never an accepted-frame read.
 c.observe(read_request(1,0,0xffffffffu,0,1),108,0,5,0,1);
 for(uint32_t frame=0;frame<12;++frame){
  auto prepare=file(fixtures+"/prepare"+std::to_string(frame)+".bin");auto golden=file(goldens+"/frame"+std::to_string(frame)+".hud");const uint64_t gen=v34::u64(prepare.data()+12);const uint32_t ref=v34::u32(prepare.data()+24);transact(prepare);assert(e.gate->candidate_ready());const auto accepted_before=accepted_crc(e);
  // Every canonical word position, across all twelve independent goldens.
  for(uint32_t off=0;off<21120;++off)c.observe(read_request(gen,frame,ref,off,1),108,0,0,off,1,&golden);
  // Full frame and every actual network-sized burst cover all patch crossings.
  c.observe(read_request(gen,frame,ref,0,21120),42276,0,0,0,21120,&golden);
  for(uint32_t off=0;off<21120;off+=256){auto n=std::min(256u,21120-off);c.observe(read_request(gen,frame,ref,off,n),548,0,0,off,n,&golden);}
  const uint32_t boundaries[]={0,1,3839,3840,3841,7679,7680,7681,15359,15360,15361,21119,21120};
  for(auto off:boundaries)for(auto n:{0u,1u,2u,255u,256u,257u,511u,512u,513u,21120u-off})if(n<=21120-off)c.observe(read_request(gen,frame,ref,off,n),std::max(size_t(108),size_t(n)*2+36),0,0,off,n,&golden);
  for(unsigned i=0;i<500;++i){auto off=random32()%21121;auto count=random32()%(21121-off);c.observe(read_request(gen,frame,ref,off,count),std::max(size_t(108),size_t(count)*2+36),0,0,off,count,&golden);}
  for(auto off:{21120u,21121u,0xffffffffu})for(auto n:{0u,1u,21120u,0xffffffffu})if(off>21120||n>21120-off)c.observe(read_request(gen,frame,ref,off,n),108,0,5,off,n);
  for(auto b:{read_request(gen+1,frame,ref,0,1),read_request(gen,frame+1,ref,0,1),read_request(gen,frame,ref^1,0,1)})c.observe(b,108,0,5,0,1);
  auto good=read_request(gen,frame,ref,0,1);for(size_t n=0;n<good.size();++n)c.observe(good,108,-2,0,0,1,nullptr,n);
  auto badcrc=good;badcrc.back()^=1;c.observe(badcrc,108,-2,0,0,1);
  for(auto size:{0u,7u,9u})c.observe(request(3,gen,frame,ref,0,Bytes(size)),108,-2,0,0,1);
  for(auto cap:{0u,35u,36u,107u})c.observe(good,cap,-2,0,0,1);
  c.observe(read_request(gen,frame,ref,0,37),108,-2,0,0,37);
  c.observe(read_request(gen,frame,ref,21120,0),108,0,0,21120,0,&golden);
  assert(accepted_crc(e)==accepted_before);c.observe(read_request(gen,frame,ref,0,21120),42276,0,0,0,21120,&golden);
  Bytes ack(20);v34::put32(ack.data(),21120);std::copy(e.gate->status().tag.begin(),e.gate->status().tag.end(),ack.begin()+4);transact(request(4,gen,frame,ref,1,ack));transact(request(5,gen,frame,ref,0,{}));assert(!e.gate->candidate_ready());c.observe(good,108,0,5,0,1);
 }
 auto hash=c.digest.finish();std::cout<<"READ_SLICE_PASS cases="<<c.cases<<" valid_reads="<<c.valid_reads<<" rejected_ffi="<<c.errors<<" response_sha256=";for(auto x:hash)std::cout<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(x);std::cout<<"\n";
}

