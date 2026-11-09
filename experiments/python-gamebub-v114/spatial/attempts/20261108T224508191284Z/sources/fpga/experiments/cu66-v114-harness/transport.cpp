// Verification-only synchronous parallel DMA adapter. No firmware/QSPI claim.
#include "bench_transport_base.hpp"
#include "Vv97_forward.h"
#include "admission_monitor.hpp"
static uint32_t transport_crc(const std::vector<uint8_t>&v){uint32_t c=0xffffffffU;for(uint8_t b:v){c^=b;for(unsigned i=0;i<8;++i)c=(c>>1)^((c&1U)?0xedb88320U:0U);}return c^0xffffffffU;}
struct Transport {
 Bench&b;Vv97_forward f{"v97_transport"};AdmissionMonitor admission;
 struct Descriptor{uint32_t token;unsigned length,written;};
 std::deque<Descriptor> descriptors;std::deque<uint8_t> fifo;
 std::vector<uint8_t> drained;const Case* active=nullptr;
 uint32_t owner_epoch=0,owner_fid=0,owner_generation=0,next_token=1;
 uint64_t accepted=0,issued=0,acknowledged=0,commits=0,source_stalls=0,sink_stalls=0,held_ack_cycles=0,wrong_dma=0,wrong_ack=0,commit_cycle=0,start_cycle=0;
 unsigned max_fifo=0,max_reserved=0,max_descriptors=0;
 bool connected=false,killed=false,reserve=false,push=false,pop=false,ack=false,start=false,commit=false;
 unsigned len=0;uint32_t token=0;uint8_t byte=0;
 std::optional<std::array<uint32_t,3>> held_ack;
 std::optional<std::array<uint32_t,4>> held_sink;
 explicit Transport(Bench& bench):b(bench),admission(bench){
  f.clk=0;f.rst_n=0;f.abort_frame=f.core_change=f.start_valid=f.req_valid=f.data_valid=f.ack_ready=f.commit_valid=f.sink_ready=0;
  f.new_generation=f.start_generation=f.req_generation=f.data_generation=f.commit_generation=0;
  f.start_epoch=f.start_fid=f.start_total=f.start_crc=f.req_epoch=f.req_len=f.data_epoch=f.data_token=f.data_byte=f.commit_epoch=f.commit_fid=0;
  b.before_edge=[this](){pre();};b.after_edge=[this](){post();};b.tick();f.rst_n=1;configure(1);
  need(f.capability==0x56393743U&&f.version==1&&f.capacity==2048&&f.max_dma==1400&&f.dma_alignment==4,"actual transport capability");
 }
 ~Transport(){b.before_edge={};b.after_edge={};}
 void generations(){f.start_generation=f.req_generation=f.data_generation=f.commit_generation=f.generation;}
 void configure(unsigned gen){f.core_change=1;f.new_generation=gen;b.tick();f.core_change=0;b.tick();generations();need(f.generation==gen,"transport generation configuration");}
 void pre(){
  admission.pre();
  f.clk=0;f.eval();killed=!f.rst_n||f.abort_frame||f.core_change;
  const bool public_kill=b.d.reset||b.d.abort_packet||killed;
  for(unsigned n=0;n<2;++n){
   b.d.in_valid=connected&&f.sink_valid&&!public_kill;
   b.d.in_data=f.sink_byte;b.d.in_last=active&&drained.size()+1==active->packet.size();b.d.eval();
   f.sink_ready=connected&&b.d.in_ready&&!public_kill;f.eval();
  }
  need(bool(b.d.in_valid&&b.d.in_ready)==bool(f.sink_valid&&f.sink_ready),"public ready/valid transfer coupling");
  if(!killed){
   if(held_ack)need(f.ack_valid&&std::array<uint32_t,3>{f.ack_generation,f.ack_epoch,f.ack_token}==*held_ack,"held transport ACK identity");
   if(held_sink)need(f.sink_valid&&std::array<uint32_t,4>{f.sink_generation,f.sink_epoch,f.sink_fid,f.sink_byte}==*held_sink,"held transport sink tuple");
   held_ack=f.ack_valid&&!f.ack_ready?std::optional<std::array<uint32_t,3>>({f.ack_generation,f.ack_epoch,f.ack_token}):std::nullopt;
   held_sink=f.sink_valid&&!f.sink_ready?std::optional<std::array<uint32_t,4>>({f.sink_generation,f.sink_epoch,f.sink_fid,f.sink_byte}):std::nullopt;
   if(f.data_valid&&!f.data_ready)++source_stalls;
   if(f.sink_valid&&!f.sink_ready)++sink_stalls;
   if(f.ack_valid&&!f.ack_ready)++held_ack_cycles;
  }else{held_ack.reset();held_sink.reset();}
  reserve=f.req_valid&&f.req_ready;push=f.data_valid&&f.data_ready;pop=f.sink_valid&&f.sink_ready;ack=f.ack_valid&&f.ack_ready;
  start=f.start_valid&&f.start_ready;commit=f.commit_valid;len=f.req_len;token=f.req_token;byte=f.data_byte;
  if(!killed&&pop){need(active&&!fifo.empty()&&f.sink_byte==fifo.front(),"independent FIFO ordered sink bytes");need(f.sink_generation==owner_generation&&f.sink_epoch==owner_epoch&&f.sink_fid==owner_fid,"sink complete owner tuple");need(drained.size()<active->packet.size()&&f.sink_byte==active->packet[drained.size()],"actual custom packet byte provenance");}
  if(!killed&&ack)need(!descriptors.empty()&&descriptors.front().written==descriptors.front().length&&f.ack_generation==owner_generation&&f.ack_epoch==owner_epoch&&f.ack_token==descriptors.front().token,"independent ACK descriptor owner");
 }
 void post(){
  admission.post();
  if(killed){fifo.clear();descriptors.clear();drained.clear();accepted=issued=acknowledged=0;next_token=(!f.rst_n||f.core_change)?1:next_token;}
  else {
   if(start){need(active&&f.start_total==active->packet.size(),"start complete command");fifo.clear();descriptors.clear();drained.clear();accepted=issued=acknowledged=0;}
   if(reserve){need(token==next_token&&len&&len<=1400,"independent reservation token/length");descriptors.push_back({token,len,0});issued+=len;++next_token;}
   if(push){need(active&&accepted<active->packet.size()&&byte==active->packet[accepted],"independent DMA source bytes");auto i=std::find_if(descriptors.begin(),descriptors.end(),[](const Descriptor&d){return d.written<d.length;});need(i!=descriptors.end()&&i->token==f.data_token,"independent DMA token owner");++i->written;fifo.push_back(byte);++accepted;}
   if(pop){drained.push_back(fifo.front());fifo.pop_front();}
   if(ack){descriptors.pop_front();++acknowledged;}
  }
  f.clk=1;f.eval();f.clk=0;f.eval();
  unsigned reserved=0;for(const auto&d:descriptors)reserved+=d.length-d.written;
  need(f.fifo_used==fifo.size()&&f.reserved_bytes==reserved&&f.queued_slots==descriptors.size(),"independent FIFO/reservation/descriptor occupancy");
  need(f.received_bytes==accepted&&f.drained_bytes==drained.size(),"independent transport byte counters");
  need(fifo.size()+reserved<=2048&&descriptors.size()<=2,"finite transport resources");
  max_fifo=std::max(max_fifo,unsigned(fifo.size()));max_reserved=std::max(max_reserved,reserved);max_descriptors=std::max(max_descriptors,unsigned(descriptors.size()));
  if(f.commit_pulse){need(commit&&active&&drained==active->packet&&fifo.empty()&&descriptors.empty()&&accepted==active->packet.size()&&f.committed_fid==owner_fid,"ingress commit independent full-byte/ACK/CRC fence");++commits;commit_cycle=b.cycle;need(!b.d.done,"ingress commit must be distinguished from decoder completion");}
 }
 void begin(const Case&c,uint32_t epoch){
  need(!f.active&&f.start_ready&&c.packet.size()<=49152,"transport bounded clean admission");active=&c;owner_epoch=epoch;owner_fid=Bench::be32(c.packet,8);owner_generation=f.generation;generations();connected=true;commit_cycle=0;start_cycle=b.cycle;
  f.start_epoch=epoch;f.start_fid=owner_fid;f.start_total=c.packet.size();f.start_crc=transport_crc(c.packet);f.start_valid=1;b.tick();f.start_valid=0;b.tick();need(f.active,"transport accepted start");
 }
 uint32_t reservation(unsigned n){f.req_epoch=owner_epoch;f.req_len=n;f.req_valid=1;for(unsigned k=0;;++k){need(k<100000,"credit reservation watchdog");f.eval();bool ready=f.req_ready;uint32_t t=f.req_token;b.tick();if(ready){f.req_valid=0;return t;}}}
 void feed(uint32_t t,unsigned off,unsigned n){f.data_epoch=owner_epoch;f.data_token=t;for(unsigned i=0;i<n;++i){if(b.profile&&i%19==0){f.data_valid=0;b.tick();}f.data_byte=active->packet.at(off+i);f.data_valid=1;for(unsigned k=0;;++k){need(k<100000,"DMA write watchdog");f.eval();bool ready=f.data_ready;b.tick();if(ready)break;}}f.data_valid=0;}
 bool complete(uint32_t generation,uint32_t epoch,uint32_t t){
  f.eval();if(descriptors.empty()||descriptors.front().token!=t||generation!=owner_generation||epoch!=owner_epoch){need(!f.ack_ready,"wrong completion cannot consume hardware ACK");++wrong_ack;return false;}
  need(f.ack_valid&&f.ack_token==t&&f.ack_generation==generation&&f.ack_epoch==epoch,"real held ACK before adapter completion");f.ack_ready=1;b.tick();f.ack_ready=0;return true;
 }
 void prime(){
  const auto a=reservation(1024),z=reservation(1024);need(f.free_bytes==0&&f.queued_slots==2,"two actual descriptors reserve 2048 bytes");
  // Wrong DMA token is presented to actual RTL, with a genuine reserved slot.
  f.data_epoch=owner_epoch;f.data_token=a+1000000U;f.data_byte=active->packet[0];f.data_valid=1;f.eval();need(!f.data_ready,"actual stale DMA token rejection");b.tick();f.data_valid=0;need(f.reject_pulse&&accepted==0,"wrong DMA no accepted byte");++wrong_dma;
  feed(a,0,1024);feed(z,1024,1024);need(f.fifo_used==2048&&f.queued_slots==2&&drained.empty(),"actual FIFO full while decoder awaits start");
  need(!complete(owner_generation,owner_epoch,a+1000000U),"wrong software completion rejected");
  for(unsigned k=0;k<17;++k){b.tick();}
  need(f.ack_valid&&f.ack_token==a&&descriptors.size()==2,"held ACK retains finite descriptor ownership");
 }
 void stream_rest(){
  while(!descriptors.empty()){const auto t=descriptors.front().token;complete(owner_generation,owner_epoch,t);}
  for(unsigned off=2048;off<active->packet.size();){unsigned n=std::min(1400U,unsigned(active->packet.size())-off);auto t=reservation(n);feed(t,off,n);complete(owner_generation,owner_epoch,t);off+=n;}
  for(unsigned k=0;!fifo.empty();++k){need(k<100000,"sink drain watchdog");b.tick();}
  need(drained==active->packet&&accepted==active->packet.size(),"transport whole actual packet exact");
  auto old=commits;f.commit_epoch=owner_epoch;f.commit_fid=owner_fid;f.commit_valid=1;b.tick();f.commit_valid=0;b.tick();need(commits==old+1&&f.start_ready,"actual transport commit complete");
 }
 void cancel(bool reset){
  auto new_generation=owner_generation+1;if(reset){b.d.reset=1;f.rst_n=0;}else{b.d.abort_packet=1;f.abort_frame=1;}b.tick();b.d.reset=b.d.abort_packet=0;f.rst_n=1;f.abort_frame=0;connected=false;b.tick();need(!f.active&&!f.ack_valid&&!f.sink_valid&&fifo.empty()&&descriptors.empty(),"cancel physical local transport flush");b.settle();if(reset)configure(new_generation);
 }
 void report(const Case&c,unsigned profile){std::cout<<"{\"type\":\"custom_transport\",\"id\":"<<quote(c.id)<<",\"profile\":"<<profile<<",\"epoch\":"<<owner_epoch<<",\"generation\":"<<owner_generation<<",\"logical_bytes\":"<<drained.size()<<",\"ingress_commit_cycle\":"<<commit_cycle<<",\"decoder_done_cycle\":"<<b.done_cycle<<",\"elapsed_cycles\":"<<b.cycle-start_cycle<<",\"canonical_samples\":"<<b.canonical_samples<<",\"inverse_input_stalls\":"<<b.d.inverse_count_input_stalls<<",\"inverse_output_stalls\":"<<b.d.inverse_count_output_stalls<<",\"reconstruct_output_stalls\":"<<b.d.count_reconstruct_output_stalls<<",\"reconstruct_reference_wait\":"<<b.d.count_reconstruct_ref_wait<<",\"memory_request_stalls\":"<<b.d.count_mem_req_stall<<",\"memory_pending_cycles\":"<<b.d.count_mem_pending<<",\"decoder_input_starved\":"<<b.d.count_input_starved<<",\"status\":\"PASS\"}\n";}
};
int main(int argc,char**argv){try{
 need(argc==7,"transport usage cases transforms canonical seed events actual");auto cases=load(argv[1]);load_tiles(argv[2]);unsigned seed=unsigned(std::stoul(argv[4]));Bench b(seed,argv[5],argv[3],argv[6]);Transport t(b);const Case*good=nullptr;unsigned rows=0,retries=0;
 for(const auto&c:cases){if(c.id=="actual_001")good=&c;}
 need(good,"actual custom recovery packet");
 for(unsigned profile=0;profile<2;++profile)for(const auto&c:cases)if(!c.error){
  b.prepare(c,profile,true);b.preload(c);uint32_t e=++b.next_epoch;t.begin(c,e);t.prime();t.admission.arm_controls();b.begin(c,e);t.admission.poison();t.stream_rest();for(unsigned k=0;!b.d.done&&!b.d.error;++k){need(k<12000000,"custom decoder watchdog");b.tick();}b.finish(c);need(t.commit_cycle&&t.commit_cycle<b.done_cycle,"separate ingress and decoder completion fences");t.report(c,profile);++rows;
 }
 for(bool reset:{false,true}){
  b.prepare(*good,1,false);b.preload(*good);uint32_t e=++b.next_epoch;t.begin(*good,e);t.prime();t.admission.arm_controls();b.begin(*good,e);t.admission.poison();for(unsigned k=0;k<9;++k)b.tick();auto old=t.commits;t.cancel(reset);need(t.commits==old,"canceled prefix cannot commit");
  b.prepare(*good,1,false);b.preload(*good);e=++b.next_epoch;t.begin(*good,e);t.prime();t.admission.arm_controls();b.begin(*good,e);t.admission.poison();t.stream_rest();for(unsigned k=0;!b.d.done&&!b.d.error;++k){need(k<12000000,"retry decoder watchdog");b.tick();}b.finish(*good);++retries;
 }
 need(t.admission.accepts==16&&t.admission.deliveries==16&&t.admission.poisoned==16&&!t.admission.expected,"all actual public commands delivered once from captured poisoned-pin tuples");
 need(rows==12&&retries==2&&t.max_fifo==2048&&t.max_reserved==2048&&t.max_descriptors==2&&t.wrong_dma&&t.wrong_ack,"transport required coverage");
 std::cout<<"{\"type\":\"transport_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"successful_case_profiles\":"<<rows<<",\"abort_reset_retries\":"<<retries<<",\"max_fifo_bytes\":"<<t.max_fifo<<",\"max_reserved_bytes\":"<<t.max_reserved<<",\"max_descriptors\":"<<t.max_descriptors<<",\"wrong_dma_tokens\":"<<t.wrong_dma<<",\"wrong_completion_tokens\":"<<t.wrong_ack<<",\"held_ack_cycles\":"<<t.held_ack_cycles<<",\"source_stalls\":"<<t.source_stalls<<",\"sink_stalls\":"<<t.sink_stalls<<",\"public_command_accepts\":"<<t.admission.accepts<<",\"registered_child_deliveries\":"<<t.admission.deliveries<<",\"poisoned_command_tuples\":"<<t.admission.poisoned<<",\"clock_edges\":"<<b.cycle<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"CUSTOM_TRANSPORT_FAIL "<<e.what()<<'\n';return 1;}}
