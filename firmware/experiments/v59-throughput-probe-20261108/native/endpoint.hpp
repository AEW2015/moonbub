#pragma once
#include "hud_gate.hpp"
#include <optional>
namespace v34 {
using cu66::Tag;using cu66::View;
constexpr size_t MAX_PACKET=49152,HEADER=32,STATUS=72;
struct Identity {uint64_t generation;uint32_t frame,reference;};
inline uint16_t u16(const uint8_t*p){return uint16_t(p[0]|uint32_t(p[1])<<8);}
inline uint32_t u32(const uint8_t*p){return u16(p)|uint32_t(u16(p+2))<<16;}
inline uint64_t u64(const uint8_t*p){return u32(p)|uint64_t(u32(p+4))<<32;}
inline void put32(uint8_t*p,uint32_t v){for(unsigned i=0;i<4;++i)p[i]=uint8_t(v>>(8*i));}
inline void put64(uint8_t*p,uint64_t v){put32(p,uint32_t(v));put32(p+4,uint32_t(v>>32));}
struct Endpoint {
 cu66_port::Arena arena;std::optional<cu66_partition::HudGate> gate;
 bool aborted=false;Identity last_abort{};
 explicit Endpoint(size_t budget):arena(budget){cu66_port::Scope s(arena);gate.emplace();}
 ~Endpoint(){cu66_port::Scope s(arena);gate.reset();}
 bool candidate(Identity i){auto c=gate->read_candidate(i.generation,i.frame);return c&&c->reference_id==i.reference;}
 bool status_match(Identity i){const auto&s=gate->status();return s.generation==i.generation&&s.frame_id==i.frame&&s.reference_id==i.reference;}
 void status(uint8_t*p){const auto&s=gate->status();auto a=gate->accepted();std::memset(p,0,STATUS);p[0]=uint8_t(s.phase);p[1]=uint8_t(s.decoded_verified|(s.external_write_drain_acknowledged<<1)|(gate->candidate_ready()<<2)|(gate->candidate_transferred()<<3)|(bool(a)<<4)|((s.external_completion_evidence==2)<<5));put32(p+4,s.words);put64(p+8,s.generation);put32(p+16,s.frame_id);put32(p+20,s.reference_id);std::copy(s.tag.begin(),s.tag.end(),p+24);put64(p+40,a?a->generation:0);put32(p+48,a?a->id:0xffffffffu);put32(p+52,a?a->reference_id:0xffffffffu);if(a)std::copy(a->tag.begin(),a->tag.end(),p+56);}
 size_t transact(View wire,uint8_t*out,size_t capacity){
 cu66_port::Scope scope(arena);
 cu66::need(wire.n>=36&&wire.n<=MAX_PACKET+36,"HC70 wire bound");const uint8_t*p=wire.p;
 cu66::need(!std::memcmp(p,"HC70",4)&&p[4]==1&&p[5]>=1&&p[5]<=7&&!u16(p+6),"HC70 fixed header");
 uint8_t op=p[5];uint32_t length=u32(p+8),arg=u32(p+28);
 cu66::need(length<=MAX_PACKET&&size_t(length)+36==wire.n,"HC70 exact length");
 cu66::need(cu66::crc32(wire.sub(0,wire.n-4))==u32(p+wire.n-4),"HC70 CRC");
 cu66::need((op!=3||length==8)&&(op!=4||length==20)&&(!(op==2||op>=5)||length==0)&&(op!=7||arg==1),"HC70 payload shape");
 cu66::need(out&&capacity>=HEADER+STATUS+4,"HC70 response capacity");
 Identity id{u64(p+12),u32(p+20),u32(p+24)};auto payload=wire.sub(32,length);uint32_t code=5;size_t bytes=STATUS;
 switch(op){
 case 1:if(arg<=1)code=uint32_t(gate->prepare(id.generation,id.frame,id.reference,arg==1,payload));break;
 case 2:if(arg==0)code=0;break;
 case 3:if(arg==0&&candidate(id)){
  uint32_t off=u32(payload.p),count=u32(payload.p+4);if(off<=21120&&count<=21120-off){
   cu66::need(size_t(count)*2+36<=capacity,"HC70 READ response capacity");auto c=gate->read_candidate(id.generation,id.frame);bytes=size_t(count)*2;
   size_t skip=off,remaining=count,destination=0;
   for(const auto&patch:c->patches){
    if(!remaining)break;
    if(skip>=patch.words.size()){skip-=patch.words.size();continue;}
    const size_t take=std::min(remaining,patch.words.size()-skip);
    for(size_t i=0;i<take;++i){const auto word=patch.words[skip+i];const size_t n=32+(destination+i)*2;out[n]=uint8_t(word);out[n+1]=uint8_t(word>>8);}
    destination+=take;remaining-=take;skip=0;
   }
   code=0;
  }}break;
 case 4:if((arg==1||arg==2)&&candidate(id)){Tag t;std::copy(payload.p+4,payload.p+20,t.begin());if(gate->acknowledge_external_write_drain(id.generation,id.frame,u32(payload.p),t,uint8_t(arg)))code=0;}break;
 case 5:if(arg==0){auto a=gate->accepted();if(candidate(id)||(a&&a->generation==id.generation&&a->id==id.frame&&a->reference_id==id.reference))if(gate->commit(id.generation,id.frame))code=0;}break;
 case 6:if(arg==0){if(aborted&&last_abort.generation==id.generation&&last_abort.frame==id.frame&&last_abort.reference==id.reference)code=0;else if(status_match(id)&&gate->abort(id.generation,id.frame)){aborted=true;last_abort=id;code=0;}}break;
 case 7:if(gate->reset(id.generation,arg==1)){aborted=false;code=0;}break;
 }
 // Gate enum maps Accepted/Busy/Stale/InvalidIdentity/DecodeRejected to0..4.
 std::memcpy(out,"HR70",4);out[4]=1;out[5]=op;out[6]=out[7]=0;put32(out+8,uint32_t(bytes));put64(out+12,id.generation);put32(out+20,id.frame);put32(out+24,id.reference);put32(out+28,code);
 if(op!=3||code!=0)status(out+32);
 put32(out+32+bytes,cu66::crc32(View(out,32+bytes)));return bytes+36;
 }
};
}
