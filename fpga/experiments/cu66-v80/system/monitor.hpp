#pragma once
#include <algorithm>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

// Verification-only monitors. The V78 RTL and all reset behavior stay unchanged.
struct CampaignMonitor {
 static constexpr uint64_t raster_deadline_cycles=10000000; // 100 ms at 100 MHz; functional liveness only.
 uint64_t watchdog_cycles=0,observations=0,first_fault_ps=0;
 bool saw_lcd_error=false,saw_memory_error=false,saw_underrun=false;
 unsigned max_waiting=0,max_in_service=0,max_total=0,waiting=0,in_service=0,total=0;
 unsigned admitted=0,acknowledged=0;
 std::string phase="reset";
 std::vector<uint64_t> releases;
 std::map<uint64_t,uint64_t> raster_due;
 explicit CampaignMonitor(unsigned count):watchdog_cycles(108+uint64_t(count)*110000000+10000000){}
 void configure_releases(unsigned count,uint64_t base,bool fixed){
  releases.assign(count,UINT64_MAX);
  if(fixed)for(unsigned i=0;i<count;i++)releases[i]=base+uint64_t(i)*100000000/30;
 }
 void queue(uint64_t cycle){
  unsigned released=unsigned(std::upper_bound(releases.begin(),releases.end(),cycle)-releases.begin());
  if(released<admitted||admitted<acknowledged)throw std::runtime_error("finite input queue accounting inconsistent");
  waiting=released-admitted;in_service=admitted-acknowledged;total=released-acknowledged;
  max_waiting=std::max(max_waiting,waiting);max_in_service=std::max(max_in_service,in_service);max_total=std::max(max_total,total);
 }
 template<class D>void observe(const D&d,uint64_t ps){
  observations++;
  saw_lcd_error|=bool(d.lcd_error);saw_memory_error|=d.lcd_memory_errors!=0;saw_underrun|=d.lcd_underruns!=0;
  if(saw_lcd_error||saw_memory_error||saw_underrun){
   if(!first_fault_ps)first_fault_ps=ps;
   throw std::runtime_error("sticky display health fault phase="+phase+" ps="+std::to_string(first_fault_ps)+" lcd_error="+std::to_string(saw_lcd_error)+" lcd_memory_errors="+std::to_string(d.lcd_memory_errors)+" lcd_underruns="+std::to_string(d.lcd_underruns));
  }
  const uint64_t cycle=ps/10000;queue(cycle);
  if(cycle>watchdog_cycles)throw std::runtime_error("finite campaign watchdog cycle="+std::to_string(cycle)+" bound="+std::to_string(watchdog_cycles));
  for(auto obligation:raster_due)if(cycle>obligation.second)throw std::runtime_error("full raster progress deadline phase="+phase+" generation="+std::to_string(obligation.first)+" cycle="+std::to_string(cycle)+" due_cycle="+std::to_string(obligation.second)+" bound_cycles="+std::to_string(raster_deadline_cycles));
 }
 void commit(uint64_t generation,uint64_t cycle,bool already_complete=false){acknowledged++;if(!already_complete)raster_due.emplace(generation,cycle+raster_deadline_cycles);}
 void complete(uint64_t generation){raster_due.erase(generation);}
};
