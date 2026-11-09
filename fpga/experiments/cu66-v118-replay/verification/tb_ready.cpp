#include "Vready_probe.h"
#include "Vready_probe___024root.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
struct Driver {
 Vready_probe d;std::ofstream trace;std::mt19937 rng;uint64_t edges=0,comparisons=0,beats=0,commits=0,loads=0,prepared=0,start_attempts=0;
 unsigned count=0,cache_error=0,state=0;bool complete=false;uint32_t fid=0,last_epoch=0,next_epoch=1;uint64_t generation=0;
 std::array<unsigned,1350> words{};std::array<bool,1350> known{};
 Driver(unsigned seed,const char*path):trace(path),rng(seed){if(!trace)throw std::runtime_error("trace open");
  d.clk=0;
  d.reset=0;
  d.start=0;
  d.abort_packet=0;
  d.reconstruct_lookup_req=0;
  d.reconstruct_lookup_tile=0;
  d.reconstruct_lookup_cell=0;
  d.cache_valid=0;
  d.cache_last=0;
  d.cache_data=0;
  d.cache_ref_fid=0;
  d.cache_ref_generation=0;
  d.accepted_ref_valid=0;
  d.accepted_qcache_valid=0;
  d.accepted_ref_fid=0;
  d.accepted_ref_generation=0;
  d.packet_bytes=0;
  d.epoch=0;
  d.serial_clear=0;
  d.write_overlap=0;
  d.read_prefetch=0;
  d.tile_overlap=0;
  d.in_valid=0;
  d.in_data=0;
  d.in_last=0;
  d.out_ready=0;
  d.mem_req_ready=0;
  d.mem_rsp_valid=0;
  for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=0;
  d.mem_rsp_epoch=0;
  d.mem_rsp_error=0;
  d.verify_scale_index=0;d.packet_bytes=256;d.cache_ref_fid=41;d.cache_ref_generation=73;d.out_ready=1;
 }
 void need(bool value,const std::string&why){if(!value)throw std::runtime_error(why+" edge="+std::to_string(edges)+" count="+std::to_string(count)+" actual="+std::to_string(d.probe_count));}
 void check(){d.eval();++comparisons;need(d.probe_public_equal,"every public field incl invalid/counter");need(d.probe_internal_equal,"producer control/owner/register equality");need(d.probe_scale_equal,"all raw scale RAM words old/new");need(d.probe_count==count,"independent cache count");need(d.cache_error==cache_error&&bool(d.cache_complete)==complete,"independent cache error/completion");need(d.probe_cached_fid==fid&&d.probe_cached_generation==generation,"independent cache first-beat tag");need(bool(d.probe_nonzero)==(count!=0),"same-edge cache ownership");need(d.frame_state==state&&bool(d.probe_running)==(state!=0&&state!=14&&state!=15),"independent running/control state");if(known[d.verify_scale_index])need(d.verify_scale_data==words[d.verify_scale_index],"independent retained scale word");}
 void tick(){d.clk=0;check();const bool take=d.cache_valid&&d.cache_ready,accepted=d.start&&d.start_ready;const unsigned old_count=count,old_error=cache_error;
  need(bool(d.probe_accepted_start)==accepted,"independent accepted start");if(d.start)++start_attempts;
  const bool commit=!d.reset&&!accepted&&!d.abort_packet&&take&&d.cache_data<3;
  need(bool(d.probe_scale_commit)==commit,"actual scale RAM A-commit");
  if(commit){need(old_count<1350,"owned RAM index bound");need(d.probe_scale_address==old_count&&d.probe_scale_data==d.cache_data,"RAM address/data tuple");known[old_count]=true;words[old_count]=d.cache_data;++commits;d.verify_scale_index=old_count;}
  if(d.reset||d.abort_packet){count=0;fid=0;generation=0;cache_error=0;complete=false;state=0;}
  else if(accepted){complete=false;state=d.epoch==0||d.epoch<=last_epoch?15:1;if(state==1)last_epoch=d.epoch;}
  else if(take){++beats;if(old_count==0){fid=d.cache_ref_fid;generation=d.cache_ref_generation;complete=false;cache_error=0;}
   if(d.cache_data==3)cache_error=3;else if(bool(d.cache_last)!=(old_count==1349))cache_error=1;
   if(d.cache_last||old_count==1349){count=0;if(d.cache_last&&old_count==1349&&d.cache_data<3&&(old_count==0||old_error==0))complete=true;}
   else count=(old_count+1)&2047;
  }
  d.clk=1;check();d.clk=0;check();++edges;trace<<"{\"edge\":"<<edges<<",\"count\":"<<count<<",\"error\":"<<cache_error<<",\"complete\":"<<complete<<",\"state\":"<<state<<",\"equal\":true}\n";need(edges<200000,"focused watchdog");
 }
 void idle(){d.start=d.reset=d.abort_packet=d.cache_valid=d.cache_last=0;}
 void reset(bool abort=false){idle();if(abort)d.abort_packet=1;else d.reset=1;tick();idle();check();}
 void load(unsigned length,unsigned bad=9999,bool missing=false){++loads;for(unsigned i=0;i<length;++i){idle();if((rng()&7)==0)tick();d.cache_valid=1;d.cache_data=i==bad?3:rng()%3;d.cache_last=i+1==length&&!missing;d.cache_ref_fid=100+unsigned(loads)+(i?1234:0);d.cache_ref_generation=1000+loads+(i?5678:0);tick();}idle();}
 void scan(){for(unsigned i=0;i<1350;++i){d.verify_scale_index=i;check();}}
 void start(bool bad=false){idle();d.start=1;d.epoch=bad?0:next_epoch++;tick();idle();}
 void prepared_count(unsigned value){
  // Declared verification-only counter preparation. It does not claim that
  // counts above1349 are reachable; data3 suppresses any out-of-range RAM write.
  idle();auto&r=*d.rootp;r.ready_probe__DOT__old_dut__DOT__cache_count=value;r.ready_probe__DOT__new_dut__DOT__cache_count=value;r.ready_probe__DOT__new_dut__DOT__cache_nonzero_owned=value!=0;r.ready_probe__DOT__old_dut__DOT__cache_nonzero_owned=value!=0;count=value;d.cache_valid=1;d.cache_data=3;d.cache_last=0;tick();++prepared;
 }
};
int main(int argc,char**argv){try{if(argc!=3)throw std::runtime_error("seed trace required");unsigned seed=unsigned(std::stoul(argv[1]));Driver s(seed,argv[2]);s.d.reset=1;s.tick();s.idle();
 s.load(1350);s.need(s.complete,"complete1350 preload");s.scan();s.start();s.need(s.state==1&&!s.complete,"accepted start consumes one-shot cache");for(unsigned i=0;i<5;++i)s.tick();s.reset(true);
 for(unsigned bad:{0U,1U,674U,1348U,1349U}){s.load(1350,bad);s.need(!s.complete&&s.cache_error==3,"invalid-data preload rejects");s.scan();s.reset();}
 for(unsigned n:{1U,2U,674U,1349U}){s.load(n);s.need(!s.complete&&s.cache_error==1&&s.count==0,"earlylast");s.start();s.need(s.state==1,"retry after bad preload does not deadlock");s.reset(true);}
 s.load(1350,9999,true);s.need(!s.complete&&s.cache_error==1&&s.count==0,"missinglast cap");s.load(1350);s.need(s.complete&&s.cache_error==0,"fresh first beat clears prior error");s.scan();s.reset();
 s.load(17,9999,true);s.need(s.count==17,"partial preload");for(unsigned i=0;i<8;++i){s.d.start=1;s.d.cache_valid=1;s.d.cache_last=1;s.d.cache_data=2;s.tick();s.need(s.count==17&&!s.d.start_ready&&!s.d.cache_ready,"start/finalbeat blocks partial");}s.reset(true);s.need(s.d.start_ready,"abort releases partial preload");
 s.d.start=1;s.d.cache_valid=1;s.d.cache_last=1;s.d.cache_data=2;s.d.epoch=s.next_epoch++;s.tick();s.need(s.state==1&&s.count==0,"start wins simultaneous first cache beat");s.reset();s.start(true);s.need(s.state==15&&!s.d.probe_running,"ADMIT then FAILED last-assignment priority");s.reset(true);
 for(unsigned value=0;value<2048;++value){s.prepared_count(value);}
 s.reset();
 for(unsigned guards=0;guards<8;++guards){s.idle();s.d.reset=guards&1;s.d.abort_packet=(guards>>1)&1;s.d.start=(guards>>2)&1;s.d.cache_valid=s.d.cache_last=1;s.d.cache_data=3;s.d.epoch=s.next_epoch++;s.tick();s.reset();}
 s.scan();s.d.final();std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"edges\":"<<s.edges<<",\"public_comparisons\":"<<s.comparisons<<",\"cache_beats\":"<<s.beats<<",\"scale_commits\":"<<s.commits<<",\"preloads\":"<<s.loads<<",\"prepared_counter_cases\":"<<s.prepared<<",\"start_attempts\":"<<s.start_attempts<<"}\n";return 0;}
 catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
