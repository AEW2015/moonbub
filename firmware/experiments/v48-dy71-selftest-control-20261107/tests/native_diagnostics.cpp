#include "../native/endpoint.hpp"
#include "../native/endpoint_c.h"
#include <cassert>
#include <cstring>
static size_t largest_calls=0,free_calls=0;
static size_t largest(){++largest_calls;return 777;}
static size_t free_bytes(){++free_calls;return 9000;}
int main(){
 using cu66_port::Arena;
 {Arena a(32);a.largest_probe=largest;auto p=a.allocate(16);assert(largest_calls==0);a.release(p,16);try{a.allocate(33);assert(false);}catch(const cu66_port::Error&){}assert(a.last_failure.kind==1&&a.last_failure.requested==33&&a.last_failure.largest==777);}
 {Arena a(100000);a.free_probe=free_bytes;a.largest_probe=largest;a.reserve=8192;try{a.allocate(1000);assert(false);}catch(const cu66_port::Error&){}assert(a.last_failure.kind==2&&a.last_failure.free==9000&&a.last_failure.live==0&&a.last_failure.probes==3);}
 {Arena a(SIZE_MAX);a.largest_probe=largest;volatile size_t n=SIZE_MAX;try{a.allocate(n);assert(false);}catch(const cu66_port::Error&){}assert(a.last_failure.kind==3&&a.last_failure.requested==SIZE_MAX);}
 v34::Endpoint e(98304);assert(v46_hud_set_largest_probe(&e,largest)==0);uint64_t before[24],after[24];uint8_t text[96];size_t n=0;auto count=largest_calls;auto frees=free_calls;assert(v46_hud_diagnostics(&e,before,text,96,&n)==0);assert(v46_hud_diagnostics(&e,after,text,96,&n)==0);assert(!std::memcmp(before,after,sizeof before));assert(largest_calls==count&&free_calls==frees);assert(e.arena.live==0&&n==0);
}
