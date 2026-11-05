#include "Vcu70_receiver.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
struct Event{bool start,packet_request,packet_response;uint64_t generation;uint32_t sequence;uint16_t address;};
struct Sim{
 Vcu70_receiver d;uint64_t clocks=0;unsigned assertions=0;
 Sim(){d.clk=0;d.rst=1;d.abort_i=0;d.clear_fault=0;d.start_valid=0;d.packet_req_ready=0;d.packet_rsp_valid=0;d.ref_req_ready=0;d.ref_rsp_valid=0;d.write_ready=0;d.write_done_valid=0;d.memory_drained=1;d.hud_prepare_ready=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_command_ready=0;d.software_ack_valid=0;d.paint_start_ready=0;d.paint_result_valid=0;d.painter_drained=1;d.presentation_ready=1;d.vblank=0;d.scanout_drained=1;d.diag_address=0;tick();tick();d.rst=0;tick();}
 void check(bool b,const char*s){assertions++;need(b,s);}
 Event tick(){need(clocks<2000,"ownercontrolwatchdog");d.clk=0;d.eval();Event e{bool(d.start_valid&&d.start_ready),bool(d.packet_req_valid&&d.packet_req_ready),bool(d.packet_rsp_valid&&d.packet_rsp_ready),d.packet_req_generation,d.packet_req_sequence,d.packet_req_address};d.clk=1;d.eval();clocks++;return e;}
 uint32_t reg(unsigned address){d.diag_address=uint16_t(address);d.clk=0;d.eval();return d.diag_data;}
 void bad_start(uint64_t generation,uint32_t bytes){check(d.start_ready,"badstartnotready");uint32_t before=d.rejected_count;d.start_generation=generation;d.start_packet_bytes=bytes;d.start_valid=1;check(tick().start,"startnothandshaken");d.start_valid=0;tick();check(!d.busy&&d.error&&d.error_code==1&&d.rejected_count==before+1&&!d.packet_req_valid,"badstartaccepted/truncated");}
 void stale(const Event&r,unsigned mode,bool simultaneous){uint32_t before=d.stale_completions;
  d.packet_rsp_valid=1;d.packet_rsp_generation=r.generation+(mode==2?1:0);d.packet_rsp_sequence=r.sequence+(mode==0?1:0);d.packet_rsp_address=uint16_t(r.address+(mode==1?1:0));d.packet_rsp_data=0x43;
  if(simultaneous){d.hud_result_valid=1;d.hud_result_generation=999;d.hud_result_frame_id=123;d.hud_result_reference_id=122;d.hud_result_success=1;d.hud_result_words=21120;d.hud_drain_valid=1;d.hud_drain_generation=999;d.hud_drain_frame_id=123;d.hud_drain_success=1;d.hud_drain_words=21120;d.software_ack_valid=1;d.software_ack_opcode=5;d.software_ack_generation=999;d.software_ack_frame_id=123;d.software_ack_success=1;}
  auto e=tick();check(e.packet_response,"staleresponsenotconsumed");check(d.stale_completions==before+(simultaneous?4:1),"simultaneousstalecounterlost");check(d.busy&&!d.start_ready&&!d.packet_req_valid,"staleresponsereleasedlease");d.packet_rsp_valid=0;d.hud_result_valid=0;d.hud_drain_valid=0;d.software_ack_valid=0;
 }
};
int main(){try{Sim s;s.check(s.reg(0)==0x43553730&&s.reg(4)==0x10000&&s.reg(8)==0x3f,"identityregisters");s.check((s.reg(0x48)&0x10000)==0,"initialfirstfault");
 s.bad_start(0,24758);s.check(s.reg(0x50)==0&&(s.reg(0x48)&255)==1,"firstfaultinvalidgeneration");
 s.bad_start(1,0);s.bad_start(2,65536);s.check(s.reg(0x50)==0&&(s.reg(0x48)&255)==1,"firstfaultnotsticky");
 s.d.clear_fault=1;s.tick();s.d.clear_fault=0;s.check((s.reg(0x48)&0x10000)==0,"clearfirstfault");
 s.d.start_generation=7;s.d.start_packet_bytes=24758;s.d.start_valid=1;s.check(s.tick().start,"freshstart");s.d.start_valid=0;s.d.packet_req_ready=1;Event request{};for(unsigned i=0;;i++){s.check(i<20,"firstpacketrequestmissing");auto e=s.tick();if(e.packet_request){request=e;break;}}
 s.d.packet_req_ready=0;s.check(request.generation==7&&request.address==0,"packetrequestidentity");s.check(s.d.busy&&!s.d.start_ready,"packetleasenotowned");s.stale(request,0,true);s.stale(request,1,false);s.stale(request,2,false);
 for(unsigned i=0;!s.d.error;i++){s.check(i<520,"watchdognofault");s.tick();}
 s.check(s.d.error_code==0x7f&&s.d.busy&&!s.d.start_ready&&s.d.stage==11,"watchdogdidnotdrain");
 s.check((s.reg(0x48)&0x100ff)==0x1007f&&s.reg(0x50)==7&&s.reg(0x54)==0&&s.reg(0x44)==request.address,"watchdogfirstfaultrecord");
 s.check(((s.reg(0x48)>>8)&255)==2&&s.reg(0x4c)==0xffffffff,"watchdogstageframe");s.check(s.reg(0x60)>0&&s.reg(0x64)==0&&s.reg(0x68)==0&&s.reg(0x70)==0&&s.reg(0x78)==0&&s.reg(0x80)==0&&s.reg(0x88)==0&&s.reg(0x90)==0,"stagedtimestamps");s.check(s.reg(0x34)>=512,"watchdogage");
 s.stale(request,1,true);s.check(s.d.stale_completions==10,"allstalecounts");
 s.d.start_valid=1;s.d.start_generation=8;s.d.start_packet_bytes=24758;for(unsigned i=0;i<12;i++){s.check(!s.tick().start&&s.d.busy&&!s.d.start_ready&&s.d.accepted_count==0,"watchdogfreedlivelease");}s.d.start_valid=0;
 s.d.packet_rsp_valid=1;s.d.packet_rsp_generation=request.generation;s.d.packet_rsp_sequence=request.sequence;s.d.packet_rsp_address=request.address;s.d.packet_rsp_data=0x43;s.check(s.tick().packet_response,"matchingresponsenotconsumed");s.d.packet_rsp_valid=0;
 for(unsigned i=0;s.d.busy;i++){s.check(i<20,"matchingresponsedidnotdrain");s.tick();}s.tick();
 s.check(s.d.start_ready&&!s.d.reference_valid&&!s.d.front_valid&&s.d.accepted_count==0&&s.d.presented_count==0&&s.d.rejected_count==4,"failedframepublished");
 s.bad_start(7,24758);s.check((s.reg(0x48)&0x100ff)==0x1007f&&s.reg(0x50)==7,"laterfailureoverwrotestickyfault");
 // Wrap and inspect the bounded eight-entry event ring through its public registers.
 for(unsigned i=0;i<8;i++)s.bad_start(0,24758);
 uint32_t events=s.reg(0x58);s.check(events>8&&s.reg(0x5c)==events-8,"eventringoverwritecount");uint32_t prior_time=0;for(uint32_t seq=events-8;seq<events;seq++){unsigned base=0x100+(seq%8)*32;s.check(s.reg(base)==seq,"eventsequence");uint32_t when=s.reg(base+4);s.check(when>=prior_time&&s.reg(base+8)==0,"eventtimestamporder");prior_time=when;s.check(s.reg(base+12)==0&&s.reg(base+16)==0&&s.reg(base+20)==0xffffffff&&((s.reg(base+24)>>16)&255)==1,"eventpayload");}
 uint32_t rejected=s.d.rejected_count;s.d.clear_fault=1;s.tick();s.d.clear_fault=0;s.check((s.reg(0x48)&0x10000)==0&&s.d.rejected_count==rejected&&s.d.stale_completions==10,"clearalteredcounters");s.bad_start(0,24758);s.check((s.reg(0x48)&0x100ff)==0x10001&&s.reg(0x50)==0,"faultnotrearmed");
 std::cout<<"OWNER_CONTROL_PASS assertions="<<s.assertions<<" clocks="<<s.clocks<<" invalid_start_rejections="<<s.d.rejected_count-1<<" watchdog_faults=1 simultaneous_stale_group=4 stale_total="<<s.d.stale_completions<<" accepted_frames="<<s.d.accepted_count<<" presented_frames="<<s.d.presented_count<<" event_sequence="<<s.reg(0x58)<<" event_overwrites="<<s.reg(0x5c)<<"\n";
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
