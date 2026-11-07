#pragma once
#include "protocol97_c.h"
#include <deque>

struct LiveFixture {
 std::string name;
 std::vector<uint8_t> setup,payload;
 std::vector<std::vector<uint8_t>> packets;
 uint32_t profile=0,epoch=0,generation=0;
};
static std::vector<uint8_t> live_read(const std::string& name) {
 std::ifstream f(name,std::ios::binary);
 if(!f)throw std::runtime_error("live input open "+name);
 return std::vector<uint8_t>(std::istreambuf_iterator<char>(f),{});
}
static uint32_t live_be32(const std::vector<uint8_t>& p,size_t at) {
 if(at+4>p.size())throw std::runtime_error("live input truncated u32");
 return (uint32_t(p[at])<<24)|(uint32_t(p[at+1])<<16)|(uint32_t(p[at+2])<<8)|p[at+3];
}
static std::vector<LiveFixture> live_fixtures(const std::string& index) {
 std::ifstream f(index);if(!f)throw std::runtime_error("live index open");
 const auto slash=index.find_last_of('/');const auto parent=index.substr(0,slash+1);
 std::vector<LiveFixture> result;std::string line;
 while(std::getline(f,line)){
  if(line.empty()||line[0]=='#')continue;
  std::istringstream row(line);LiveFixture v;std::string hex,golden,packets;
  if(!(row>>v.name>>hex>>golden>>packets))throw std::runtime_error("live index row");
  for(size_t i=0;i<hex.size();i+=2)v.setup.push_back(uint8_t(std::stoul(hex.substr(i,2),nullptr,16)));
  v.profile=live_be32(v.setup,12);v.epoch=live_be32(v.setup,8);v.generation=live_be32(v.setup,32);
  v.payload=live_read(parent+golden);auto encoded=live_read(parent+packets);
  for(size_t off=0;off<encoded.size();){size_t n=live_be32(encoded,off);off+=4;if(n>encoded.size()-off)throw std::runtime_error("live datagram length");v.packets.emplace_back(encoded.begin()+off,encoded.begin()+off+n);off+=n;}
  result.push_back(std::move(v));
 }
 return result;
}
struct LiveStats {
 unsigned frames=0,rejected=0,dmas=0,padding=0,max_native_slots=0,max_native_reserved=0,wrong_acks=0;
 uint64_t bytes=0;
};
// Runs the actual Rust gateway against live RTL credit/ACK/commit observations.
// Host fixture/scoreboard storage is deliberately outside the firmware RAM bound.
static bool live_frame(Bench& b,void* gateway,const LiveFixture& f,int malformed,LiveStats& stats) {
 uint8_t setup_ack[40]={};b.need(v97_setup(gateway,f.setup.data(),f.setup.size(),setup_ack)==0,"live native setup");
 b.core(f.generation);b.generations();unsigned before=b.commits;bool started=false;
 struct Pending {V97Transfer transfer;uint32_t hardware_token;uint32_t epoch;};
 std::deque<Pending> pending;
 auto complete_front=[&](){
  b.need(!pending.empty(),"live pending ACK mapping");auto p=pending.front();
  b.d.eval();b.need(b.d.ack_valid&&b.d.ack_generation==f.generation&&b.d.ack_epoch==p.epoch&&b.d.ack_token==p.hardware_token,"live hardware completion identity");
  // A stale software token must not release the native stage or consume HW ACK.
  auto reserved=v97_reserved_bytes(gateway);
  b.need(v97_complete(gateway,p.transfer.token+1000000U,1)<0,"native wrong ACK token rejected");
  b.need(v97_reserved_bytes(gateway)==reserved,"wrong native ACK retained reservation");++stats.wrong_acks;
  b.ack(p.epoch,p.hardware_token);
  b.need(v97_complete(gateway,p.transfer.token,1)==0,"live native completion from hardware ACK");
  pending.pop_front();
 };
 for(size_t index=0;index<f.packets.size();index++){
  auto datagram=f.packets[index];
  if(malformed==1&&index+1==f.packets.size())datagram.back()^=1;
  if(malformed==2&&index==0)datagram.resize(11);
  V97Chunk chunk={};int status=1;unsigned retries=0;
  while(status==1){
   b.drain();
   b.need(v97_observe_free(gateway,f.epoch,f.generation,b.d.free_bytes)==0,"native credit from actual RTL free");
   status=v97_receive(gateway,datagram.data(),datagram.size(),&chunk);
   if(status==1){b.need(++retries<5&&!pending.empty(),"bounded native WouldBlock");complete_front();}
  }
  if(status!=0){
   b.need(malformed!=0,"unexpected native receive failure fixture="+f.name+" packet="+std::to_string(index)+" status="+std::to_string(status));
   b.need((index==0&&malformed==2) || (index+1==f.packets.size()&&malformed==1),"expected malformed phase");
   b.abort();
   while(!pending.empty()){auto p=pending.front();pending.pop_front();b.need(v97_complete(gateway,p.transfer.token,0)<0,"cancel native outstanding DMA");}
   b.need(v97_needs_drain(gateway)==1,"native cancellation fence");
   b.need(v97_drained(gateway)==0,"native quiescence after hardware abort and all DMA retired");
   b.need(v97_reserved_bytes(gateway)==0&&v97_inflight(gateway)==0,"native cancel bounded empty");
   b.need(b.commits==before,"malformed live frame never commits");++stats.rejected;return false;
  }
  b.need(malformed!=2,"truncated header accepted");
  b.need(chunk.frame.epoch==f.epoch&&chunk.frame.core_generation==f.generation,"live native context");
  b.need(chunk.frame.length==f.payload.size()&&chunk.transfer.logical_len>0&&chunk.transfer.logical_len<=1400,"live native bounds");
  if(!started){b.start(chunk.frame.epoch,chunk.frame.fid,f.payload,chunk.frame.crc);started=true;}
  const auto* data=v97_transfer_bytes(gateway,&chunk.transfer);
  const auto* storage=v97_staging_storage(gateway,&chunk.transfer);
  b.need(data!=nullptr&&storage!=nullptr&&reinterpret_cast<uintptr_t>(data)%4==0,"live native aligned staging");
  b.need(chunk.offset+chunk.transfer.logical_len<=f.payload.size(),"live native payload offset");
  b.need(std::equal(data,data+chunk.transfer.logical_len,f.payload.begin()+chunk.offset),"live native source vs independent golden");
  b.need(v97_issue(gateway,&chunk.transfer)==0,"live native issue");
  auto token=b.reserve(f.epoch,chunk.transfer.logical_len);
  pending.push_back({chunk.transfer,token,f.epoch});
  stats.max_native_slots=std::max(stats.max_native_slots,unsigned(pending.size()));
  stats.max_native_reserved=std::max(stats.max_native_reserved,v97_reserved_bytes(gateway));
  b.need(pending.size()<=2&&v97_reserved_bytes(gateway)<=2800,"live native memory bound");
  for(uint32_t i=0;i<chunk.transfer.logical_len;i++){
   b.d.sink_ready=(b.cycles%11)!=3;
   if(i%17==0){b.tick();b.tick();}
   b.d.data_epoch=f.epoch;b.d.data_generation=f.generation;b.d.data_token=token;b.d.data_byte=data[i];b.d.data_valid=1;b.d.eval();b.need(b.d.data_ready,"live RTL DMA accept");b.tick();b.d.data_valid=0;
  }
  b.tick();++stats.dmas;stats.padding+=chunk.transfer.storage_len-chunk.transfer.logical_len;
  V97Frame premature={};b.need(v97_take_commit(gateway,&premature)==1,"native no commit before DMA ACK retirement");
  // Preserve two queued descriptors where actual credit and profile permit it.
  if(pending.size()==2){for(unsigned hold=0;hold<9;hold++)b.tick();complete_front();}
 }
 b.need(malformed==0,"corrupt final payload accepted");
 while(!pending.empty())complete_front();
 b.drain();b.need(b.output==f.payload,"live actual drained bytes vs independent golden");
 V97Frame commit={};b.need(v97_take_commit(gateway,&commit)==0,"live native commit authorization");
 V97Chunk blocked={};b.need(v97_receive(gateway,f.packets.front().data(),f.packets.front().size(),&blocked)==1,"native commit pending blocks next receive");
 b.need(v97_commit_complete(gateway,commit.epoch^1U,commit.fid,commit.core_generation,1)<0,"native stale commit ACK rejected");
 b.commit(commit.epoch,commit.fid,true);
 b.need(b.commits==before+1,"actual RTL ingress commit observed");
 b.need(v97_commit_complete(gateway,commit.epoch,commit.fid,commit.core_generation,1)==0,"native completion from actual RTL commit");
 ++stats.frames;stats.bytes+=f.payload.size();
 std::cout<<"{\"type\":\"live_frame\",\"fixture\":\""<<f.name<<"\",\"profile\":"<<f.profile<<",\"epoch\":"<<commit.epoch<<",\"fid\":"<<commit.fid<<",\"bytes\":"<<b.output.size()<<",\"crc32\":"<<crc32(b.output)<<",\"status\":\"PASS\"}\n";
 return true;
}
static void live_run(Bench& b,const std::string& index){
 LiveStats stats;auto fixtures=live_fixtures(index);b.need(!fixtures.empty(),"live fixtures present");
 bool jpeg=false,opaque=false,negative=false;
 for(const auto& f:fixtures){
  void* g=v97_create(f.profile==1?0:f.profile,f.generation);b.need(g!=nullptr,"native gateway create");
  b.need(live_frame(b,g,f,0,stats),"live accepted frame");
  jpeg|=f.profile==1;opaque|=f.profile==0x43533932U;
  b.need(v97_destroy(g)==0,"native gateway destroy");
  if(!negative&&f.profile==1&&f.packets.size()>1){
   // Same native gateway recovers after actual aborted prefix/CRC failure.
   g=v97_create(0,f.generation);b.need(g!=nullptr,"native recovery gateway create");
   b.need(!live_frame(b,g,f,1,stats),"live CRC rejection");
   b.need(live_frame(b,g,f,0,stats),"live valid recovery after CRC cancel");
   b.need(v97_destroy(g)==0,"native recovery gateway destroy");
   g=v97_create(0,f.generation);b.need(g!=nullptr,"native malformed gateway create");
   b.need(!live_frame(b,g,f,2,stats),"live malformed rejection");
   b.need(live_frame(b,g,f,0,stats),"live valid recovery after malformed cancel");
   b.need(v97_destroy(g)==0,"native malformed gateway destroy");negative=true;
  }
 }
 b.need(jpeg&&opaque&&negative&&stats.max_native_slots==2,"live required profile and queue cases");
 std::cout<<"{\"type\":\"live_join\",\"frames\":"<<stats.frames<<",\"logical_bytes\":"<<stats.bytes<<",\"rejected_frames\":"<<stats.rejected<<",\"dma\":"<<stats.dmas<<",\"ignored_padding_bytes\":"<<stats.padding<<",\"max_native_slots\":"<<stats.max_native_slots<<",\"max_native_reserved\":"<<stats.max_native_reserved<<",\"wrong_ack_rejections\":"<<stats.wrong_acks<<",\"status\":\"PASS\"}\n";
}
