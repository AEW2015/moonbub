#include "endpoint.hpp"
#include "endpoint_c.h"
extern "C" {
int v46_hud_set_largest_probe(void*p,size_t(*probe)()){if(!p||!probe)return-1;static_cast<v34::Endpoint*>(p)->arena.largest_probe=probe;return 0;}
int v46_hud_diagnostics(void*p,uint64_t*out,uint8_t*text,size_t cap,size_t*length){
 if(!p||!out||!text||!length)return-1;
 const auto&e=*static_cast<v34::Endpoint*>(p);const auto&a=e.arena;const auto&f=a.last_failure;const auto&s=e.gate->status();
 const auto accepted=e.gate->accepted();
 uint64_t values[24]={uint64_t(s.phase),uint64_t(s.decoded_verified),s.frame_id,s.reference_id,s.generation,s.words,f.kind,f.requested,f.live,f.free,f.largest,a.limit,a.live,a.peak,a.failures,f.probes,v34::u32(s.tag.data()),v34::u32(s.tag.data()+4),v34::u32(s.tag.data()+8),v34::u32(s.tag.data()+12),accepted?accepted->generation:0,accepted?accepted->id:0xffffffffu,accepted?accepted->reference_id:0xffffffffu,uint64_t(bool(accepted))};
 std::copy(values,values+24,out);*length=s.failure.size();const size_t n=std::min(cap,s.failure.size());if(n)std::memcpy(text,s.failure.data(),n);return 0;
}

int v41_hud_set_reserve(void*p,size_t(*probe)(),size_t reserve){if(!p||!probe||reserve<8192||reserve>32768)return-1;auto&a=static_cast<v34::Endpoint*>(p)->arena;a.free_probe=probe;a.reserve=reserve;return 0;}
void* v34_hud_create(size_t budget){try{return new v34::Endpoint(budget);}catch(...){return nullptr;}}
void v34_hud_destroy(void*p){delete static_cast<v34::Endpoint*>(p);}
int v34_hud_transact(void*p,const uint8_t*wire,size_t length,uint8_t*out,size_t cap,size_t*written){if(!p||!wire||!written)return-1;*written=0;try{*written=static_cast<v34::Endpoint*>(p)->transact(cu66::View(wire,length),out,cap);return 0;}catch(...){return-2;}}
int v34_hud_stats(void*p,size_t*out){if(!p||!out)return-1;const auto&a=static_cast<v34::Endpoint*>(p)->arena;out[0]=a.limit;out[1]=a.live;out[2]=a.peak;out[3]=a.maximum;out[4]=a.allocations;out[5]=a.failures;return 0;}
}
