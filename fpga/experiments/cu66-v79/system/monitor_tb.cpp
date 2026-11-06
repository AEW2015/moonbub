#include "monitor.hpp"
#include <functional>
#include <iostream>
#include <stdexcept>
struct FakeOutputs {bool lcd_error=false;unsigned lcd_memory_errors=0,lcd_underruns=0;};
static void need(bool value,const char*message){if(!value)throw std::runtime_error(message);}
static std::string throws(const std::function<void()>&action){try{action();}catch(const std::runtime_error&e){return e.what();}throw std::runtime_error("expected monitor rejection");}
int main(){try{
 unsigned tests=0;
 for(const std::string phase:{"release_wait","readiness_wait","final_tail"}){
  CampaignMonitor m(4);FakeOutputs d;m.phase=phase;m.observe(d,10000);d.lcd_error=true;
  auto reason=throws([&]{m.observe(d,10001);});need(m.saw_lcd_error,"LCD error pulse did not latch");need(reason.find("phase="+phase)!=std::string::npos,"missing fault phase");
  d.lcd_error=false;throws([&]{m.observe(d,10002);});tests++;std::cout<<"MONITOR_TEST_PASS case=lcd_error_pulse phase="<<phase<<" sticky_after_clear=1 observer_unit_only=1\n";
 }
 for(unsigned which=0;which<2;which++){
  CampaignMonitor m(4);FakeOutputs d;m.phase="readiness_wait";if(which)d.lcd_underruns++;else d.lcd_memory_errors++;
  throws([&]{m.observe(d,25000);});need(which?m.saw_underrun:m.saw_memory_error,"counter fault did not latch");tests++;std::cout<<"MONITOR_TEST_PASS case="<<(which?"underrun":"lcd_memory_errors")<<" observer_unit_only=1\n";
 }
 {
  CampaignMonitor m(4);FakeOutputs d;m.phase="final_tail";m.configure_releases(1,0,true);m.admitted=1;m.commit(7,10);m.observe(d,(10+CampaignMonitor::raster_deadline_cycles)*10000);
  auto reason=throws([&]{m.observe(d,(11+CampaignMonitor::raster_deadline_cycles)*10000);});need(reason.find("generation=7")!=std::string::npos,"missing stalled generation");tests++;std::cout<<"MONITOR_TEST_PASS case=raster_deadline_expired observer_unit_only=1\n";
 }
 {
  CampaignMonitor m(4);FakeOutputs d;m.configure_releases(2,0,true);m.admitted=2;m.commit(7,10);m.complete(7);m.observe(d,(11+CampaignMonitor::raster_deadline_cycles)*10000);need(m.raster_due.empty(),"fulfilled raster obligation retained");m.commit(8,20,true);need(m.raster_due.empty(),"already complete raster rearmed");tests++;std::cout<<"MONITOR_TEST_PASS case=raster_fulfilled_and_pre_ack_complete observer_unit_only=1\n";
 }
 {
  CampaignMonitor m(4);FakeOutputs d;m.phase="readiness_wait";m.configure_releases(4,100,true);m.admitted=1;m.queue(100);need(m.waiting==0&&m.in_service==1&&m.total==1,"initial finite queue");
  m.observe(d,(100ULL+100000000/30)*10000);need(m.waiting==1,"readiness wait missed second release");m.observe(d,(100+2ULL*100000000/30)*10000);need(m.waiting==2,"readiness wait missed third release");m.observe(d,20000000ULL*10000);need(m.waiting==3&&m.max_waiting==3&&m.max_total==4,"finite queue failed to cap at cohort");m.admitted=4;m.acknowledged=4;m.queue(20000000);need(m.waiting==0&&m.in_service==0&&m.total==0,"terminal finite queue");tests++;std::cout<<"MONITOR_TEST_PASS case=fixed_arrival_queue_during_readiness finite_cohort_cap=4 observer_unit_only=1\n";
 }
 {
  CampaignMonitor m(119);FakeOutputs d;m.observe(d,m.watchdog_cycles*10000);throws([&]{m.observe(d,(m.watchdog_cycles+1)*10000);});tests++;std::cout<<"MONITOR_TEST_PASS case=finite_full_cohort_watchdog observer_unit_only=1\n";
 }
 std::cout<<"MONITOR_UNIT_PASS tests="<<tests<<" observer_unit_only=1 hardware_fault_injection=0\n";
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
