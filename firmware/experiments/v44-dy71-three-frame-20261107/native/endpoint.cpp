#include "endpoint.hpp"
#include "endpoint_c.h"
extern "C" {
int v41_hud_set_reserve(void*p,size_t(*probe)(),size_t reserve){if(!p||!probe||reserve<8192||reserve>32768)return-1;auto&a=static_cast<v34::Endpoint*>(p)->arena;a.free_probe=probe;a.reserve=reserve;return 0;}
void* v34_hud_create(size_t budget){try{return new v34::Endpoint(budget);}catch(...){return nullptr;}}
void v34_hud_destroy(void*p){delete static_cast<v34::Endpoint*>(p);}
int v34_hud_transact(void*p,const uint8_t*wire,size_t length,uint8_t*out,size_t cap,size_t*written){if(!p||!wire||!written)return-1;*written=0;try{*written=static_cast<v34::Endpoint*>(p)->transact(cu66::View(wire,length),out,cap);return 0;}catch(...){return-2;}}
int v34_hud_stats(void*p,size_t*out){if(!p||!out)return-1;const auto&a=static_cast<v34::Endpoint*>(p)->arena;out[0]=a.limit;out[1]=a.live;out[2]=a.peak;out[3]=a.maximum;out[4]=a.allocations;out[5]=a.failures;return 0;}
}
