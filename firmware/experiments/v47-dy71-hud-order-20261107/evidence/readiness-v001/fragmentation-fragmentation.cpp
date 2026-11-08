#include <cstddef>
void* lab_alloc(size_t);void lab_free(void*);
#include "native/endpoint.hpp"
#include "tlsf.h"
#include <fstream>
#include <iterator>
#include <array>
#include <iostream>
#include <cstdlib>
#include <unordered_map>
#include <random>
#include <iomanip>
static tlsf_t pool;static bool trace=false;static unsigned frame=0,serial=0;static size_t current_req=0;
static std::unordered_map<void*,std::pair<unsigned,size_t>> live;
static bool walk(void*,size_t n,int used,void*u){if(!used){auto p=static_cast<std::pair<size_t,size_t>*>(u);p->first+=n;p->second=std::max(p->second,n);}return true;}
static std::pair<size_t,size_t> available(){std::pair<size_t,size_t> p{};tlsf_walk_pool(tlsf_get_pool(pool),walk,&p);return p;}
static size_t free_probe(){return available().first;}static size_t largest_probe(){return available().second;}
void* lab_alloc(size_t n){auto a=available();void*p=tlsf_malloc(pool,n);auto id=++serial;if(p)live[p]={id,n};if(trace)std::cout<<"A,"<<frame<<","<<id<<","<<n<<","<<bool(p)<<","<<a.first<<","<<a.second<<"\n";if(!p)current_req=n;return p;}
void lab_free(void*p){auto it=live.find(p);if(trace&&it!=live.end())std::cout<<"F,"<<frame<<","<<it->second.first<<","<<it->second.second<<"\n";if(it!=live.end())live.erase(it);tlsf_free(pool,p);}
static std::vector<uint8_t> read(const std::string&p){std::ifstream f(p,std::ios::binary);if(!f)throw std::runtime_error(p);return {std::istreambuf_iterator<char>(f),{}};}
static uint32_t call(v34::Endpoint&e,uint8_t op,uint32_t f,uint32_t ref,uint32_t arg,const std::vector<uint8_t>&payload,std::array<uint8_t,1060>&out){std::vector<uint8_t>b(36+payload.size());std::memcpy(b.data(),"HC70",4);b[4]=1;b[5]=op;v34::put32(b.data()+8,payload.size());v34::put64(b.data()+12,f+1);v34::put32(b.data()+20,f);v34::put32(b.data()+24,ref);v34::put32(b.data()+28,arg);std::copy(payload.begin(),payload.end(),b.begin()+32);v34::put32(b.data()+b.size()-4,cu66::crc32(cu66::View(b.data(),b.size()-4)));e.transact(cu66::View(b.data(),b.size()),out.data(),out.size());return v34::u32(out.data()+28);}
int main(int argc,char**argv){if(argc<4)return 2;unsigned seed=std::strtoul(argv[1],nullptr,10);size_t bytes=std::strtoul(argv[2],nullptr,10);trace=argc>4;alignas(16) static unsigned char backing[512000];if(bytes>sizeof backing)return 3;pool=tlsf_create_with_pool(backing,bytes,bytes);if(!pool)return 4;if(tlsf_check(pool)||tlsf_check_pool(tlsf_get_pool(pool))){std::cout<<"INITIAL_CHECK_FAIL seed="<<seed<<" bytes="<<bytes<<"\n";return 14;}
 std::mt19937 rnd(seed);std::vector<void*> holes,pins;size_t first=32768+(rnd()%7)*4096;holes.push_back(tlsf_malloc(pool,first));
 // Consume the rest into individually freed holes separated by long-lived pins.
 while(available().second>12000){size_t n=2048+(rnd()%25)*512;auto h=tlsf_malloc(pool,n);if(!h)break;holes.push_back(h);auto pin=tlsf_malloc(pool,64+(rnd()%8)*64);if(!pin)break;pins.push_back(pin);}
 for(auto h:holes)tlsf_free(pool,h);
 auto initial=available();v34::Endpoint e(98304);e.arena.free_probe=free_probe;e.arena.largest_probe=largest_probe;e.arena.reserve=8192;std::array<uint8_t,1060>out{};size_t verified=0;unsigned done=0;
 for(frame=0;frame<12;++frame){auto wire=read(std::string(argv[3])+"/prepare"+std::to_string(frame)+".bin");auto input=tlsf_malloc(pool,wire.size());if(!input){std::cout<<"RESULT seed="<<seed<<" bytes="<<bytes<<" stage=input frame="<<frame<<" done="<<done<<"\n";return 0;}std::memcpy(input,wire.data(),wire.size());auto ref=v34::u32(wire.data()+24);e.transact(cu66::View(static_cast<const uint8_t*>(input),wire.size()),out.data(),out.size());auto code=v34::u32(out.data()+28);if(code){auto f=e.arena.last_failure;if(tlsf_check(pool)||tlsf_check_pool(tlsf_get_pool(pool))){std::cout<<"FAILPATH_CHECK_FAIL seed="<<seed<<" bytes="<<bytes<<"\n";return 13;}std::cout<<"RESULT seed="<<seed<<" bytes="<<bytes<<" stage=prepare frame="<<frame<<" done="<<done<<" code="<<code<<" kind="<<f.kind<<" request="<<f.requested<<" live="<<f.live<<" free="<<f.free<<" largest="<<f.largest<<" peak="<<e.arena.peak<<" initial_free="<<initial.first<<" initial_largest="<<initial.second<<"\n";tlsf_free(pool,input);return 0;}
 tlsf_free(pool,input);std::array<uint8_t,16>tag;std::copy(out.begin()+56,out.begin()+72,tag.begin());auto golden=read("C:/moon/maintenance/v45-sequence/qualification/frame"+std::to_string(frame)+".hud");
 for(unsigned off=0;off<21120;off+=512){unsigned n=std::min(512u,21120-off);std::vector<uint8_t> p(8);v34::put32(p.data(),off);v34::put32(p.data()+4,n);if(call(e,3,frame,ref,0,p,out)||!std::equal(out.begin()+32,out.begin()+32+n*2,golden.begin()+off*2))return 10;verified+=n;}
 std::vector<uint8_t>ack(20);v34::put32(ack.data(),21120);std::copy(tag.begin(),tag.end(),ack.begin()+4);if(call(e,4,frame,ref,1,ack,out)||call(e,5,frame,ref,0,{},out))return 11;++done;
 }
 auto check=tlsf_check(pool),check_pool=tlsf_check_pool(tlsf_get_pool(pool));if(check||check_pool){std::cout<<"CHECK seed="<<seed<<" bytes="<<bytes<<" tlsf="<<check<<" pool="<<check_pool<<" words="<<verified<<"\n";return 12;}
 std::cout<<"RESULT seed="<<seed<<" bytes="<<bytes<<" stage=pass done="<<done<<" words="<<verified<<" peak="<<e.arena.peak<<" initial_free="<<initial.first<<" initial_largest="<<initial.second<<"\n";return 0;
}

