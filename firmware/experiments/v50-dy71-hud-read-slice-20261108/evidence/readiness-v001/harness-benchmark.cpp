#include "native/endpoint.hpp"
#include "native/endpoint_c.h"
#include <array>
#include <chrono>
#include <fstream>
#include <iterator>
#include <iostream>
#include <cassert>
using Bytes=std::vector<uint8_t>;
static Bytes file(const std::string&p){std::ifstream f(p,std::ios::binary);assert(f);return {std::istreambuf_iterator<char>(f),{}};}
int main(int argc,char**argv){assert(argc==3);unsigned bursts=std::stoul(argv[2]);auto key=file(argv[1]);v34::Endpoint e(98304);std::array<uint8_t,548> out{};size_t n=0;assert(v34_hud_transact(&e,key.data(),key.size(),out.data(),out.size(),&n)==0&&v34::u32(out.data()+28)==0);const auto tag=e.gate->status().tag;
 std::array<std::array<uint8_t,44>,83> requests{};std::array<Bytes,83> replies;
 for(unsigned i=0;i<83;++i){auto&b=requests[i];std::copy(key.begin(),key.begin()+32,b.begin());b[5]=3;v34::put32(b.data()+8,8);v34::put32(b.data()+28,0);const unsigned off=i*256,count=std::min(256u,21120-off);v34::put32(b.data()+32,off);v34::put32(b.data()+36,count);v34::put32(b.data()+40,cu66::crc32({b.data(),40}));assert(v34_hud_transact(&e,b.data(),b.size(),out.data(),out.size(),&n)==0&&v34::u32(out.data()+28)==0);replies[i]=Bytes(out.begin(),out.begin()+n);}
 const auto live=e.arena.live,allocations=e.arena.allocations;uint64_t checksum=0;auto start=std::chrono::steady_clock::now();
 for(unsigned repeat=0;repeat<bursts;++repeat)for(unsigned i=0;i<83;++i){const auto&b=requests[i];assert(v34_hud_transact(&e,b.data(),b.size(),out.data(),out.size(),&n)==0);assert(n==replies[i].size());assert(std::equal(out.begin(),out.begin()+n,replies[i].begin()));checksum+=v34::u32(out.data()+n-4);}
 auto elapsed=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();assert(e.arena.live==live&&e.arena.allocations==allocations);assert(e.gate->candidate_ready()&&e.gate->status().tag==tag&&!e.gate->accepted());std::cout<<"bursts="<<bursts<<" transactions="<<bursts*83u<<" elapsed_us="<<elapsed<<" read_allocations=0 checksum="<<checksum<<"\n";
}
