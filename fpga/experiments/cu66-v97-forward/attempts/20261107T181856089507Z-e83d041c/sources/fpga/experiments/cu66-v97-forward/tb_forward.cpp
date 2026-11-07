#include "Vv97_forward.h"
#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

static uint32_t crc32(const std::vector<uint8_t>& v) {
 uint32_t c=0xffffffffU;
 for(auto b:v){c^=b;for(int i=0;i<8;i++)c=(c>>1)^((c&1)?0xedb88320U:0U);}
 return c^0xffffffffU;
}
static std::vector<uint8_t> bytes(size_t n){std::vector<uint8_t> v(n);for(size_t i=0;i<n;i++)v[i]=uint8_t((i*71U+i/11U+19U)&255U);return v;}
struct Bench {
 Vv97_forward d;
 uint64_t cycles=0; unsigned checks=0,commits=0,max_fifo=0,max_reserved=0,max_slots=0;
 std::vector<uint8_t> output;
 void need(bool b,const std::string& s){++checks;if(!b)throw std::runtime_error(s+" cycle="+std::to_string(cycles));}
 void tick(){
  d.clk=0;d.eval();
  if(d.sink_valid&&d.sink_ready){need(d.sink_generation==d.generation&&d.sink_epoch==d.start_epoch&&d.sink_fid==d.start_fid,"sink identity");output.push_back(d.sink_byte);}
  d.clk=1;d.eval();++cycles;
  if(d.commit_pulse)++commits;
  max_fifo=std::max(max_fifo,unsigned(d.fifo_used));max_reserved=std::max(max_reserved,unsigned(d.reserved_bytes));max_slots=std::max(max_slots,unsigned(d.queued_slots));
  need(cycles<10000000,"watchdog");need(d.fifo_used+d.reserved_bytes<=2048,"real credit capacity");need(d.queued_slots<=2,"slot bound");
 }
 void reset(){d.rst_n=0;tick();d.rst_n=1;tick();output.clear();}
 void generations(){d.start_generation=d.generation;d.req_generation=d.generation;d.data_generation=d.generation;d.commit_generation=d.generation;}
 void abort(){d.abort_frame=1;tick();need(d.cancel_pulse,"abort cancel");d.abort_frame=0;tick();output.clear();need(!d.active&&d.free_bytes==2048&&!d.ack_valid,"abort flush");}
 void core(uint32_t gen){d.new_generation=gen;d.core_change=1;tick();need(d.cancel_pulse,"core cancel");d.core_change=0;tick();generations();output.clear();need(d.generation==gen&&d.free_bytes==2048,"core flush");}
 void start(uint32_t e,uint32_t f,const std::vector<uint8_t>& v,uint32_t crc){generations();d.start_epoch=e;d.start_fid=f;d.start_total=uint32_t(v.size());d.start_crc=crc;d.start_valid=1;tick();d.start_valid=0;tick();need(d.active,"start accepted");output.clear();}
 uint32_t reserve(uint32_t e,unsigned n){d.req_epoch=e;d.req_len=n;d.req_valid=1;d.eval();need(d.req_ready,"reservation ready");uint32_t token=d.req_token;tick();d.req_valid=0;tick();return token;}
 void reject_req(uint32_t e,unsigned n){d.req_epoch=e;d.req_len=n;d.req_valid=1;d.eval();need(!d.req_ready,"reservation rejected");auto q=d.queued_slots;auto r=d.reserved_bytes;tick();need(d.reject_pulse,"reject pulse");d.req_valid=0;tick();need(q==d.queued_slots&&r==d.reserved_bytes,"rejected reservation no effect");}
 void feed(uint32_t e,uint32_t token,const std::vector<uint8_t>& v,size_t off,size_t n,bool stalls=true){
  for(size_t i=0;i<n;i++){
   d.sink_ready=stalls?((cycles%7)!=2):0;
   if(stalls&&i%13==0){tick();tick();}
   d.data_epoch=e;d.data_token=token;d.data_byte=v.at(off+i);d.data_valid=1;d.eval();need(d.data_ready,"DMA ready");tick();d.data_valid=0;
  }tick();
 }
 void ack(uint32_t e,uint32_t token){d.eval();need(d.ack_valid&&d.ack_epoch==e&&d.ack_token==token&&d.ack_generation==d.generation,"ACK identity");d.ack_ready=1;tick();d.ack_ready=0;tick();}
 void drain(){d.sink_ready=1;unsigned n=0;while(d.fifo_used){tick();need(++n<=2048,"drain watchdog");}tick();d.sink_ready=0;}
 void commit(uint32_t e,uint32_t f,bool good){unsigned before=commits;d.commit_epoch=e;d.commit_fid=f;d.commit_valid=1;tick();d.commit_valid=0;tick();need(commits==before+(good?1U:0U),"commit verdict");}
 void frame(uint32_t e,uint32_t f,const std::vector<uint8_t>& v){start(e,f,v,crc32(v));for(size_t off=0;off<v.size();){auto n=std::min(size_t(1400),v.size()-off);drain();auto t=reserve(e,unsigned(n));feed(e,t,v,off,n);ack(e,t);off+=n;}drain();need(output==v,"independent payload bytes");commit(e,f,true);}
 void units(){
  need(d.capability==0x56393743U&&d.version==1&&d.capacity==2048&&d.max_dma==1400&&d.dma_alignment==4,"explicit capability");
  for(size_t n:{size_t(1),size_t(2),size_t(3),size_t(1024),size_t(1400),size_t(1401),size_t(4097),size_t(262144)})frame(7,uint32_t(n),bytes(n));
  auto v=bytes(2048);start(8,1,v,crc32(v));reject_req(8,0);reject_req(8,1401);reject_req(99,1);
  auto a=reserve(8,1400);reject_req(8,649);auto b=reserve(8,648);need(d.free_bytes==0&&d.queued_slots==2,"two queued reservations");reject_req(8,1);
  feed(8,a,v,0,1400,false);need(d.ack_valid,"held ACK available");for(int i=0;i<17;i++)tick();need(d.queued_slots==2&&d.ack_token==a,"held ACK retains slot");
  d.data_epoch=99;d.data_token=b;d.data_byte=0;d.data_valid=1;d.eval();need(!d.data_ready,"stale epoch byte");tick();d.data_valid=0;
  d.data_epoch=8;d.data_token=a;d.data_valid=1;d.eval();need(!d.data_ready,"wrong token byte");tick();d.data_valid=0;
  feed(8,b,v,1400,648,false);need(d.fifo_used==2048&&d.free_bytes==0,"physical FIFO full");
  d.data_epoch=8;d.data_token=b;d.data_valid=1;d.eval();need(!d.data_ready,"extra byte cannot overflow completed descriptors");tick();d.data_valid=0;
  commit(8,1,false);ack(8,a);ack(8,b);commit(8,1,false);drain();need(output==v,"queued payload ordering");commit(99,1,false);commit(8,99,false);commit(8,1,true);
  start(9,2,bytes(3),0);auto c=reserve(9,3);feed(9,c,bytes(3),0,3);ack(9,c);drain();commit(9,2,false);need(d.crc_error,"CRC error latched");abort();frame(10,3,bytes(3));
  // Abort and replacement at started, reserved, partial, completed/heldACK and drained phases.
  for(unsigned phase=0;phase<7;phase++)for(unsigned change=0;change<2;change++){
   auto p=bytes(31);start(100+phase,phase,p,crc32(p));uint32_t t=0;
   if(phase>=1)t=reserve(100+phase,31);
   if(phase>=2)feed(100+phase,t,p,0,phase==2?7:31,false);
   if(phase==4){ack(100+phase,t);drain();}
   if(phase>=5){if(phase==6)ack(100+phase,t);d.sink_ready=1;for(int i=0;i<7;i++)tick();d.sink_ready=0;need(d.fifo_used>0&&!output.empty(),"partial tentative sink before cancel");}
   if(phase<4)commit(100+phase,phase,false);
   auto old_gen=d.generation;
   if(change)core(old_gen+1);else abort();
   commit(100+phase,phase,false);need(!d.ack_valid&&!d.sink_valid,"cancel removes outputs");
   frame(200+phase,phase+20,bytes(33));
  }
  auto retry=bytes(4);start(888,1,retry,crc32(retry));auto old=reserve(888,4);abort();start(888,1,retry,crc32(retry));auto fresh=reserve(888,4);need(fresh!=old,"abort preserves token uniqueness");d.data_epoch=888;d.data_token=old;d.data_valid=1;d.eval();need(!d.data_ready,"stale token after abort and same epoch");tick();d.data_valid=0;feed(888,fresh,retry,0,4);ack(888,fresh);drain();commit(888,1,true);
  auto small=bytes(3);start(700,1,small,crc32(small));auto s0=reserve(700,1);auto s1=reserve(700,1);need(d.free_bytes==2046,"slots independent of bytes");reject_req(700,1);feed(700,s0,small,0,1);feed(700,s1,small,1,1);ack(700,s0);ack(700,s1);auto s2=reserve(700,1);feed(700,s2,small,2,1);ack(700,s2);drain();commit(700,1,true);
  // New generation rejects old-generation DMA even with matching epoch and token.
  core(d.generation+1);auto p=bytes(4);start(777,1,p,crc32(p));auto t=reserve(777,4);
  d.data_generation=d.generation-1;d.data_epoch=777;d.data_token=t;d.data_valid=1;d.eval();need(!d.data_ready,"stale generation DMA");tick();d.data_valid=0;generations();feed(777,t,p,0,4);ack(777,t);drain();commit(777,1,true);
 }
 void trace(const std::string& path){
  std::ifstream f(path);need(bool(f),"native trace open");std::string line;std::vector<uint8_t> golden;size_t off=0;unsigned frames=0,dmas=0,pad=0;
  while(std::getline(f,line)){if(line.empty()||line[0]=='#')continue;std::istringstream s(line);std::string op;s>>op;
   if(op=="GOLDEN"){std::string name;s>>name;std::ifstream bin(name,std::ios::binary);need(bool(bin),"golden open "+name);golden.assign(std::istreambuf_iterator<char>(bin),{});}
   else if(op=="START"){uint32_t e,id,n;std::string crc;s>>e>>id>>n>>crc;need(n==golden.size(),"golden length");start(e,id,golden,uint32_t(std::stoul(crc,nullptr,16)));off=0;}
   else if(op=="DMA"){uint32_t e,n;std::string hex;s>>e>>n>>hex;need(n>0&&n<=1400&&hex.size()==((n+3U)&~3U)*2U,"native aligned DMA shape");std::vector<uint8_t> payload;for(size_t i=0;i<hex.size();i+=2)payload.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));need(off+n<=golden.size()&&std::equal(payload.begin(),payload.begin()+n,golden.begin()+off),"native DMA vs independent golden");drain();auto t=reserve(e,n);feed(e,t,payload,0,n);ack(e,t);off+=n;++dmas;pad+=unsigned(payload.size()-n);}
   else if(op=="COMMIT"){uint32_t e,id;s>>e>>id;drain();need(off==golden.size()&&output==golden,"native trace exact bytes");commit(e,id,true);++frames;std::cout<<"{\"type\":\"native_frame\",\"epoch\":"<<e<<",\"fid\":"<<id<<",\"bytes\":"<<output.size()<<",\"crc32\":"<<crc32(output)<<",\"status\":\"PASS\"}\n";}
   else if(op=="ABORT")abort();else if(op=="CORE"){uint32_t gen;s>>gen;core(gen);}else need(false,"unknown native trace operation "+op);
  }
  need(frames>0,"native frames present");std::cout<<"{\"type\":\"native_join\",\"frames\":"<<frames<<",\"dma\":"<<dmas<<",\"ignored_padding_bytes\":"<<pad<<",\"status\":\"PASS\"}\n";
 }
};
#ifdef V97_LIVE
#include "live_forward.hpp"
#endif
int main(int argc,char** argv){Verilated::commandArgs(argc,argv);try{Bench b;b.reset();b.need(!b.d.start_ready,"generation zero unconfigured");b.core(1);b.units();if(argc>1&&std::string(argv[1])!="-"){b.reset();b.trace(argv[1]);}
#ifdef V97_LIVE
if(argc>2){b.reset();live_run(b,argv[2]);}
#endif
std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"cycles\":"<<b.cycles<<",\"checks\":"<<b.checks<<",\"commits\":"<<b.commits<<",\"max_fifo\":"<<b.max_fifo<<",\"max_reserved\":"<<b.max_reserved<<",\"max_slots\":"<<b.max_slots<<"}\n";return 0;}catch(const std::exception& e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
