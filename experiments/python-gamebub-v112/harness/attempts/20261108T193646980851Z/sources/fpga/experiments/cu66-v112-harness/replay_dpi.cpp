// Explicit source adapter: not emulated GP-SPI/DMA and not MCU time.
// At most ONE 1039-byte event is resident. File is an immutable offered schedule,
// not a run-time ingress queue. The producer is blocked until its prior ACK.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "verilated.h"
namespace {
constexpr unsigned CAP=1039;
uint8_t body[CAP]; unsigned length=0,sequence=0,highwater=0;
uint64_t release=0,accepted=0; bool pending=false,inflight=false;
FILE *source=nullptr,*trace=nullptr;
unsigned u32(unsigned at){return (unsigned(body[at])<<24)|(unsigned(body[at+1])<<16)|(unsigned(body[at+2])<<8)|body[at+3];}
int init(){
 const char *p=getenv("V112_SCHEDULE"),*t=getenv("V112_TRACE");
 if(!p||!t)return -10;
 source=fopen(p,"r");trace=fopen(t,"wx");return source&&trace?0:-11;
}
}
extern "C" int bridge_next(){
 const uint64_t now=Verilated::threadContextp()->time();
 if(!source){int result=init();if(result)return result;}
 if(inflight)return -12;
 if(!pending){
  unsigned long long when=0;unsigned n=0;
  if(fscanf(source,"%llu %u",&when,&n)!=2)return -13;
  if(n<9||n>CAP)return -14; // reject before touching bounded storage
  for(unsigned i=0;i<n;i++){unsigned v;if(fscanf(source,"%2x",&v)!=1)return -15;body[i]=uint8_t(v);}
  length=n;release=when;sequence=u32(1);pending=true;
  if(length>highwater)highwater=length;
 }
 if(now<release)return 0;
 uint8_t kind=body[0];
 if((kind=='B'&&length!=17)||(kind=='D'&&(length<16||length!=15+((unsigned(body[13])<<8)|body[14])))||((kind=='A'||kind=='C')&&length!=9)||(kind!='B'&&kind!='D'&&kind!='A'&&kind!='C'))return -16;
 accepted=now;inflight=true;
 fprintf(trace,"{\"event\":\"source_accept\",\"clock\":\"rtl_ps\",\"time_ps\":%llu,\"offered_ps\":%llu,\"sequence\":%u,\"kind\":\"%c\",\"bytes\":%u,\"resident_bytes\":%u,\"capacity_bytes\":%u}\n",(unsigned long long)now,(unsigned long long)release,sequence,kind,length,length,CAP);fflush(trace);
 return int(length);
}
extern "C" int bridge_byte(int index){return inflight&&index>=0&&unsigned(index)<length?body[index]:-1;}
extern "C" int bridge_ack(int status){
 const uint64_t now=Verilated::threadContextp()->time();
 if(!inflight||now<accepted)return -20;
 fprintf(trace,"{\"event\":\"rtl_service_complete\",\"clock\":\"rtl_ps\",\"time_ps\":%llu,\"sequence\":%u,\"status\":%d,\"service_ps\":%llu,\"source_backpressure_ps\":%llu,\"highwater_bytes\":%u}\n",(unsigned long long)now,sequence,status,(unsigned long long)(now-accepted),(unsigned long long)(accepted>release?accepted-release:0),highwater);fflush(trace);
 pending=false;inflight=false;length=0;return 0;
}
