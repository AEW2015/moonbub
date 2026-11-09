#include "Vjpeg_wire.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <deque>
static void need(bool p,const char*m){if(!p)throw std::runtime_error(m);}
static std::vector<uint8_t> bytes(const char*p){std::ifstream f(p,std::ios::binary);need(bool(f),"missing input");return {std::istreambuf_iterator<char>(f),{}};}
static uint32_t be(const std::vector<uint8_t>&b,size_t n,unsigned k){uint32_t v=0;for(unsigned i=0;i<k;++i)v=(v<<8)|b.at(n+i);return v;}
struct Chunk{uint32_t offset;std::vector<uint8_t> data;};
struct Driver {
 Vjpeg_wire d;uint64_t ticks=0,core_edges=0,accepted=0,stalls=0,good_frames=0;unsigned phase;
 std::deque<std::pair<unsigned,uint32_t>> expected_writes;
 std::vector<uint16_t> golden;std::vector<uint8_t> seen;unsigned pixels=0;bool expected_back=true,held=false;uint32_t held_addr=0;uint16_t held_data=0;
 explicit Driver(std::vector<uint16_t>g,unsigned p):phase(p),golden(std::move(g)),seen(720*480,0){d.qspi_cs_n=1;d.qspi_sck=0;d.qspi_dq=0;d.reset=1;d.memory_idle=0;d.frame_boundary=0;d.pixel_ready=0;d.eval();}
 void step(){
  need(ticks<120000000,"finite complete-test watchdog");const auto next=ticks+1;const bool clk=((next+phase)/4)&1U;const bool rise=clk&&!d.core_clk;
  d.pixel_ready=!d.reset&&((core_edges%29)<23);d.eval();
  if(rise){++core_edges;
   if(!d.reset){
    need(!d.endpoint_sideband_changed,"JPEG core traffic changed endpoint native sideband");
    if(d.accepted_bus_write){need(!expected_writes.empty(),"unplanned accepted bus write");auto w=expected_writes.front();expected_writes.pop_front();need(w.first==d.accepted_address&&w.second==d.accepted_data,"ordered QSPI/CDC write tuple differs");++accepted;}
    if(held)need(d.pixel_valid&&d.pixel_address==held_addr&&d.pixel_rgb565==held_data,"held pixel tuple changed");
    if(d.pixel_valid&&!d.pixel_ready){held=true;held_addr=d.pixel_address;held_data=d.pixel_rgb565;++stalls;}else held=false;
    if(d.pixel_valid&&d.pixel_ready){const unsigned back=(d.pixel_address>>19)&1U,linear=d.pixel_address&0x7ffffU;need(back==unsigned(expected_back),"decoder writes visible front owner");const int x=int(linear/480)-40;const unsigned y=linear%480;need(x>=0&&x<720&&y<480,"pixel coordinate range");const size_t idx=y*720+unsigned(x);need(!seen[idx],"duplicate decoded pixel");need(d.pixel_rgb565==golden[idx],"independent RGB565 golden mismatch");seen[idx]=1;++pixels;}
   }else held=false;
  }
  ticks=next;d.endpoint_clk=(ticks/2)&1U;d.core_clk=clk;d.eval();
  need(!d.cdc_overflow&&!d.transport_lost,"actual CDC overflow");
 }
 void wait(unsigned n){for(unsigned i=0;i<n;++i)step();}
 void reset(){d.reset=1;d.qspi_cs_n=1;d.qspi_sck=0;d.frame_boundary=0;d.memory_idle=0;expected_writes.clear();wait(128);d.reset=0;wait(128);need(!d.front_valid&&!d.front_buffer&&d.pattern_enable,"reset publication owner");}
 void start_transaction(){d.qspi_sck=0;d.qspi_dq=0;d.qspi_cs_n=0;wait(80);}
 void end_transaction(){d.qspi_sck=0;d.qspi_cs_n=1;d.eval();need(d.qspi_oe==0,"raw CS did not revoke output ownership");wait(80);}
 void shift(uint32_t v,unsigned bits,unsigned lanes,unsigned half){for(int n=int(bits-lanes);n>=0;n-=int(lanes)){d.qspi_dq=(v>>n)&((1U<<lanes)-1);wait(half);d.qspi_sck=1;wait(half);d.qspi_sck=0;}}
 void header(uint8_t cmd,unsigned addr,unsigned half){start_transaction();shift(cmd,8,1,half);shift(0xe0000000U|addr,32,4,half);}
 void write(unsigned addr,uint32_t value){expected_writes.emplace_back(addr,value);header(0x54,addr,10);shift(value,32,4,10);end_transaction();}
 uint32_t read(unsigned addr){header(0x55,addr,25);shift(0,64,4,25);uint32_t value=0;for(unsigned k=0;k<8;++k){wait(25);d.qspi_sck=1;d.eval();need(d.qspi_oe==15,"read lacks quad output ownership");value=(value<<4)|d.qspi_out;wait(25);d.qspi_sck=0;}end_transaction();return value;}
 void begin(uint32_t id,uint32_t len,uint32_t crc){need(read(0)==0x4d425631&&read(4)==0x10000&&(read(8)&1),"firmware identity checks");need(read(0x10)&1,"core not ready for begin");write(0x14,id);write(0x18,len);write(0x1c,(720U<<16)|480U);write(0x20,crc);write(0x24,1);}
 void chunk(const Chunk&c,uint32_t total){need(read(0xc)==total-c.offset,"0x0c remaining frame bytes differs (not FIFO credit)");header(0x40,0x100,10);for(auto b:c.data){expected_writes.emplace_back(0x100,b);shift(b,8,4,10);}end_transaction();}
 void fresh_sink(){pixels=0;std::fill(seen.begin(),seen.end(),0);expected_back=!d.front_buffer;d.memory_idle=0;}
 void good(const std::vector<Chunk>&chunks,uint32_t id,uint32_t len,uint32_t crc,unsigned expected_count){fresh_sink();const auto start=core_edges;begin(id,len,crc);for(auto&c:chunks)chunk(c,len);need(read(0x28)==len,"core receive length");write(0x24,4);const auto commit=core_edges;
  while(pixels<720*480){need(core_edges-commit<5000000,"decode watchdog");step();}wait(128);
  need(read(0x30)==expected_count-1,"decoded before finite sink drain");need(read(0x34)==expected_count-1,"presented before sink drain");d.memory_idle=1;wait(128);
  need(read(0x30)==expected_count,"decode completion count");need(read(0x34)==expected_count-1,"publication before frame fence");need(bool(d.front_buffer)!=expected_back,"front changed before publication fence");
  d.frame_boundary=1;wait(16);d.frame_boundary=0;wait(16);
  need(read(0x2c)==expected_count&&read(0x30)==expected_count&&read(0x34)==expected_count&&read(0x48)==id,"exact accepted/decode/publication tuple");need(d.front_valid&&bool(d.front_buffer)==expected_back&&!d.pattern_enable,"published front owner tuple");need(read(0x38)==0&&read(0x3c)==0&&read(0x40)==0,"unexpected fault/drop/overflow");need(expected_writes.empty(),"accepted bus ledger not drained");++good_frames;
  std::cout<<"{\"type\":\"frame\",\"status\":\"PASS\",\"id\":"<<id<<",\"pixels\":"<<pixels<<",\"upload_core_cycles\":"<<commit-start<<",\"commit_to_publication_core_cycles\":"<<core_edges-commit<<"}\n";
 }
};
int main(int argc,char**argv){try{
 need(argc==4,"usage MSV1-fixture golden-rgb565 seed-phase");auto wire=bytes(argv[1]),gold=bytes(argv[2]);need(gold.size()==720*480*2,"golden size");std::vector<uint16_t> g;for(size_t i=0;i<gold.size();i+=2)g.push_back(uint16_t(gold[i])|(uint16_t(gold[i+1])<<8));std::vector<Chunk> chunks;uint32_t id=0,length=0,crc=0;size_t pos=0,offset=0;
 while(pos<wire.size()){const auto n=be(wire,pos,2);pos+=2;need(n>=40&&pos+n<=wire.size(),"fixture packet framing");need(be(wire,pos,4)==0x4d535631&&wire[pos+4]==1&&wire[pos+5]==1,"MSV1 header");if(chunks.empty()){id=be(wire,pos+8,4);length=be(wire,pos+16,4);crc=be(wire,pos+28,4);}const auto count=be(wire,pos+24,2);need(count<=1024&&count+40==n&&be(wire,pos+20,4)==offset&&be(wire,pos+8,4)==id&&be(wire,pos+16,4)==length&&be(wire,pos+28,4)==crc,"MSV1 ordered tuple");chunks.push_back({uint32_t(offset),{wire.begin()+pos+40,wire.begin()+pos+n}});offset+=count;pos+=n;}
 need(offset==length&&length==26159&&chunks.size()==26,"existing complete JPEG fixture");Driver b(std::move(g),unsigned(std::stoul(argv[3]))%4);b.reset();
 // Deliberate downstream corruption: production receiver normally rejects this
 // before COMMIT. Here the hardware's own full-frame CRC gate is exercised.
 b.begin(id,length,crc^1U);for(auto&c:chunks)b.chunk(c,length);b.write(0x24,4);b.wait(256);need(b.read(0x38)==1&&b.read(0x3c)==1&&b.read(0x2c)==0&&b.read(0x30)==0&&b.read(0x34)==0&&!b.d.front_valid&&b.pixels==0,"bad CRC escaped hardware gate");b.write(0x24,2);b.reset();
 b.good(chunks,id,length,crc,1);
 b.begin(id+1,length,crc);b.chunk(chunks.front(),length);need(b.read(0x28)==1024,"reset midreceive setup");b.reset();b.fresh_sink();b.good(chunks,id+2,length,crc,1);
 need(b.good_frames==2&&b.expected_writes.empty(),"campaign ledger");std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"actual_endpoint_CDC_JPEG\":true,\"good_frames\":2,\"bad_crc\":1,\"midreceive_reset_retry\":1,\"verified_pixels\":691200,\"accepted_bus_writes\":"<<b.accepted<<",\"held_pixel_cycles\":"<<b.stalls<<",\"core_cycles\":"<<b.core_edges<<",\"tick_ps\":1250}\n";return 0;
}catch(const std::exception&e){std::cerr<<"JPEG_WIRE_FAIL "<<e.what()<<'\n';return 1;}}
