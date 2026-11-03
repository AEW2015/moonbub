// Simulation-only one-record lookahead; file contains actual recorded guest bytes.
#include <cstdint>
#include <cstdio>
namespace { FILE* f=nullptr; uint8_t body[1039]; uint32_t len=0,at=0;
uint32_t be(const uint8_t*p){return(uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3];}}
extern "C" int trace_open(const char*name){f=fopen(name,"rb");return f?0:-1;}
extern "C" int trace_next(){uint8_t h[8];size_t n=fread(h,1,8,f);if(n==0 && feof(f))return 0;if(n!=8)return -1;at=be(h);len=be(h+4);if(len<9||len>sizeof(body))return -2;if(fread(body,1,len,f)!=len)return -3;return int(len);}
extern "C" int trace_at(){return int(at);}
extern "C" int trace_byte(int i){return i>=0&&uint32_t(i)<len?body[i]:-1;}
