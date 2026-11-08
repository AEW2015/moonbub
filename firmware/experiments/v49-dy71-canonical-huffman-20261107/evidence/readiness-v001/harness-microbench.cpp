#include "native/hud.hpp"
#include <chrono>
#include <iostream>
#include <cassert>
int main(int argc,char**argv){assert(argc==2);unsigned repetitions=std::stoul(argv[1]);std::vector<uint8_t>b;auto put16=[&](unsigned n){b.push_back(uint8_t(n));b.push_back(uint8_t(n>>8));};put16(256);unsigned nbits=21120*8;for(unsigned i=0;i<4;++i)b.push_back(uint8_t(nbits>>(8*i)));for(unsigned i=0;i<256;++i){b.push_back(uint8_t(i));b.push_back(8);}for(unsigned i=0;i<21120;++i)b.push_back(uint8_t(i));const auto expected=cu66::crc32({b.data()+518,21120});
 cu66_port::Arena arena(98304);cu66_port::Scope scope(arena);auto start=std::chrono::steady_clock::now();uint32_t checksum=0;
 for(unsigned i=0;i<repetitions;++i){cu66::Reader r({b.data(),b.size()});auto out=cu66::huffman(r,21120,255);r.end();assert(cu66::crc32({out.data(),out.size()})==expected);checksum+=out[i%out.size()];}
 auto us=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();assert(arena.live==0);std::cout<<"repetitions="<<repetitions<<" elapsed_us="<<us<<" peak="<<arena.peak<<" allocations="<<arena.allocations<<" checksum="<<checksum<<"\n";
}