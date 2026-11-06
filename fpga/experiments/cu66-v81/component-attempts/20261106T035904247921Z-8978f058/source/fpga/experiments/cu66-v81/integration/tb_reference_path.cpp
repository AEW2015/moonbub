#include "Vcu81_reference_path.h"
#include "verilated.h"
#include <array>
#include <functional>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
static void need(bool v,const std::string&s){if(!v)throw std::runtime_error(s);}
static unsigned plane(unsigned n){return n<5400?0:n<6750?1:2;}
static unsigned tile(unsigned n){return n<5400?n:n<6750?n-5400:n-6750;}
static bool hidden(unsigned n){unsigned p=plane(n),t=tile(n),x=t%(p?45:90),y=t/(p?45:90);return p?(x>=11&&x<30&&y==23):((x>=3&&x<22&&((y>=7&&y<9)||(y>=11&&y<13)))||(x>=21&&x<61&&y>=45&&y<48)||(x>=21&&x<51&&y>=49&&y<51));}
static uint16_t word(unsigned a){return uint16_t(a*4051u^(a>>7)^0xa619u);}
struct Sim{
 std::unique_ptr<VerilatedContext> c=std::make_unique<VerilatedContext>();Vcu81_reference_path d{c.get()};
 unsigned cycles=0,address=0,cmds=0;bool backend=false,deliver=true;unsigned inject=0;uint64_t bg=0;unsigned bb=0,bp=0,bi=0,bk=0;
 Sim(){d.rst=1;d.lease_held=1;d.mem_write_ready=1;d.prefetch_req_ready=1;d.write_done_ready=1;step();step();d.rst=0;step();}
 void step(){
  need(cycles++<3000000,"watchdog");d.prefetch_rsp_valid=backend&&deliver;
  for(unsigned n=0;n<4;n++)d.prefetch_rsp_data[n]=uint32_t(word(address+2*n))|(uint32_t(word(address+2*n+1))<<16);
  d.prefetch_rsp_generation=bg-(inject==2);d.prefetch_rsp_bank=inject==3?2:bb;
  d.prefetch_rsp_plane=inject==4?2:bp;d.prefetch_rsp_index=bi+(inject==5);d.prefetch_rsp_block=bk^(inject==6);
  d.prefetch_rsp_error=inject==1;d.clk=0;d.eval();
  bool rq=d.prefetch_req_valid&&d.prefetch_req_ready,rs=d.prefetch_rsp_valid&&d.prefetch_rsp_ready;
  unsigned a=d.prefetch_req_address;uint64_t g=d.prefetch_req_generation;unsigned bank=d.prefetch_req_bank,p=d.prefetch_req_plane,i=d.prefetch_req_index,k=d.prefetch_req_block;
  d.clk=1;d.eval();d.clk=0;d.eval();c->timeInc(10);
  if(rs)backend=false;
  if(rq){need(!backend,"overlapping logical BL8");backend=true;address=a;bg=g;bb=bank;bp=p;bi=i;bk=k;cmds++;}
  d.prefetch_rsp_valid=0;d.eval();
 }
 void wait(const std::function<bool()>&f){d.eval();for(unsigned n=0;!f();n++){need(n<4000,"wait timeout cycles="+std::to_string(cycles)+" retired="+std::to_string(d.prefetch_tiles_retired)+" fault="+std::to_string(d.fault_code)+" filled="+std::to_string(d.prefetch_tiles_filled)+" cmds="+std::to_string(cmds)+" backend="+std::to_string(backend)+" read_valid="+std::to_string(d.read_valid)+" rsp="+std::to_string(d.read_rsp_valid)+" done="+std::to_string(d.write_done_valid));step();}}
 void start(unsigned gen=1){d.epoch_generation=gen;d.epoch_reference_bank=0;d.epoch_candidate_bank=1;d.epoch_reference_id=123;d.epoch_valid=1;wait([&]{return d.epoch_ready;});step();d.epoch_valid=0;}
 void lookup(unsigned n){d.read_generation=d.epoch_generation;d.read_bank=0;d.read_plane=plane(n);d.read_index=tile(n);d.read_valid=1;wait([&]{return d.read_ready;});step();d.read_valid=0;wait([&]{return d.read_rsp_valid;});need(!d.read_rsp_error,"reference returned error");unsigned a=0x080000+(plane(n)==0?0:plane(n)==1?172800:216000)+tile(n)*32;for(unsigned w=0;w<32;w++)need(uint16_t(d.read_rsp_pixels[w/2]>>(16*(w%2)))==word(a+w),"reference payload");}
 void receive(){d.read_rsp_ready=1;step();d.read_rsp_ready=0;}
 void write(unsigned n){d.write_generation=d.epoch_generation;d.write_bank=1;d.write_plane=plane(n);d.write_index=tile(n);d.write_valid=1;wait([&]{return d.write_ready;});step();d.write_valid=0;}
 void complete(unsigned n,unsigned mismatch=0){d.mem_done_generation=d.epoch_generation-(mismatch==1);d.mem_done_bank=mismatch==2?2:1;d.mem_done_plane=mismatch==3?2:plane(n);d.mem_done_index=tile(n)+(mismatch==4);d.mem_done_valid=1;wait([&]{return d.mem_done_ready;});step();d.mem_done_valid=0;}
 void finish_write(){wait([&]{return d.write_done_valid;});step();}
 void abort(){d.abort_i=1;step();wait([&]{return !d.busy;});d.abort_i=0;}
};
static void full(){Sim s;s.start();unsigned h=0;for(unsigned n=0;n<8100;n++){if(!hidden(n)){s.lookup(n);s.receive();}else h++;s.write(n);for(unsigned i=0;i<3;i++){s.step();need(!s.d.write_done_valid,"write forwarded before physical completion");}s.complete(n);s.finish_write();}s.wait([&]{return !s.d.busy;});need(h==294&&s.d.prefetch_lookups==7806&&s.d.prefetch_tiles_retired==8100&&s.d.prefetch_unused_retired==294&&s.cmds==32400&&s.d.prefetch_read_beats==259200,"full replay totals");need(s.d.captured_reference_id==123,"reference ID capture");std::cout<<"REFERENCE_PATH_CASE_PASS full_tiles=8100 lookups=7806 hidden=294 commands=32400 transactional_backend=1\n";}
static void lookahead(){Sim s;s.start();s.lookup(0);s.receive();s.write(0);s.lookup(1);s.receive();s.complete(0);s.finish_write();need(s.d.prefetch_tiles_retired==1,"lookahead clobbered served ledger");s.write(1);s.complete(1);s.finish_write();need(s.d.prefetch_tiles_retired==2,"second served ledger entry lost");s.abort();std::cout<<"REFERENCE_PATH_CASE_PASS lookahead_two_entry_ledger=1\n";}
static void cancel(){for(unsigned mode=0;mode<3;mode++){Sim s;s.start();s.lookup(0);s.deliver=false;s.d.abort_i=1;s.step();s.wait([&]{return s.d.read_rsp_valid;});need(s.d.read_rsp_error&&s.d.read_rsp_generation==1&&s.d.read_rsp_bank==0&&s.d.read_rsp_index==0,"matching cancel response missing");for(unsigned n=0;n<10;n++){need(s.d.read_rsp_valid&&s.d.read_rsp_error,"cancel not held");s.step();}s.receive();if(mode==0){s.d.abort_i=0;s.deliver=true;}else s.deliver=true;s.wait([&]{return !s.d.busy;});}std::cout<<"REFERENCE_PATH_CASE_PASS held_reference_cancel=3 exact_identity=1 error_held=1\n";}
static void authentication(){for(unsigned field=1;field<=4;field++){Sim s;s.start();s.lookup(0);s.receive();s.write(0);s.complete(0,field);need(s.d.fault,"mismatched candidate bank not faulted");s.wait([&]{return s.d.write_done_valid;});need(s.d.write_done_error&&s.d.write_done_bank==1&&s.d.write_done_index==0,"mismatched completion lacks accepted-identity error");s.step();s.wait([&]{return !s.d.busy;});need(s.d.prefetch_tiles_retired==0,"unauthenticated completion retired tile");std::cout<<"REFERENCE_PATH_CASE_PASS candidate_completion_identity_authentication=4 no_retire=1\n";}}
static void faults(){for(unsigned mode=0;mode<3;mode++){Sim s;s.start();if(mode==0){s.inject=1;s.wait([&]{return s.d.fault;});}else{s.lookup(0);s.receive();s.write(0);s.d.write_done_ready=0;if(mode==1){s.d.mem_write_aborted=1;s.step();s.d.mem_write_aborted=0;}else{s.complete(0);s.d.abort_i=1;}}if(mode){s.wait([&]{return s.d.write_done_valid;});need(s.d.write_done_error,"canceled write reported success");s.d.write_done_ready=1;s.step();s.d.abort_i=1;}s.wait([&]{return !s.d.busy;});need(s.d.prefetch_tiles_retired==0,"fault retired tile");}std::cout<<"REFERENCE_PATH_CASE_PASS raw_error_drain=1 aborted_write_error=1 held_done_abort=1\n";}
static void recovery(){Sim s;s.start();s.inject=1;s.wait([&]{return s.d.fault;});s.wait([&]{return !s.d.busy;});need(s.d.fault,"fault diagnostic cleared before acknowledgment");s.inject=0;s.d.clear_fault=1;s.step();s.d.clear_fault=0;need(!s.d.fault,"clear_fault did not release completed fault");s.write(0);s.complete(0);s.finish_write();need(!s.d.busy&&!s.d.fault&&s.d.prefetch_tiles_retired==0,"key bypass recovery");s.start(2);s.lookup(0);s.receive();s.write(0);s.complete(0);s.finish_write();need(s.d.prefetch_tiles_retired==1&&!s.d.fault,"fresh delta after fault recovery");s.abort();std::cout<<"REFERENCE_PATH_CASE_PASS fault_clear_key_fresh_delta_recovery=1\n";}
static void bad_request(){for(unsigned field=0;field<4;field++){Sim s;s.start();s.d.write_generation=field==0?2:1;s.d.write_bank=field==1?0:1;s.d.write_plane=field==2?3:0;s.d.write_index=field==3?5400:0;s.d.write_valid=1;s.d.write_done_ready=0;s.d.eval();need(s.d.write_ready&&!s.d.mem_write_valid,"bad candidate request reached physical backend");s.step();s.d.write_valid=0;s.wait([&]{return s.d.write_done_valid;});need(s.d.write_done_error&&s.d.fault,"bad candidate request lacked local error");s.d.write_done_ready=1;s.step();s.wait([&]{return !s.d.busy;});need(s.d.prefetch_tiles_retired==0,"bad candidate request retired");}std::cout<<"REFERENCE_PATH_CASE_PASS invalid_write_request_fields=4 physical_forwarded=0\n";}
static void block_authentication(){
 for(unsigned mode=1;mode<=6;mode++){
  Sim s;s.deliver=false;s.start();s.wait([&]{return s.backend;});s.inject=mode;
  for(unsigned n=0;n<12;n++){s.step();need(s.d.busy&&!s.d.epoch_ready,"unanswered block released lease");}
  s.deliver=true;s.step();need(s.d.fault,"bad block identity/error not faulted");
  s.wait([&]{return !s.d.busy;});need(s.d.prefetch_tiles_filled==0&&s.d.prefetch_read_beats==8&&s.cmds==1,"bad block committed/failed drain accounting");
 }
 std::cout<<"REFERENCE_PATH_CASE_PASS authenticated_blocks=6 drained_once=1 bad_block_never_published=1\n";
}
static void block_abort_edge(){
 Sim s;s.deliver=false;s.start();s.wait([&]{return s.backend;});unsigned commands=s.cmds;
 for(unsigned n=0;n<12;n++){s.step();need(s.d.busy&&!s.d.epoch_ready,"missing response released bank lease");}
 s.d.abort_i=1;s.deliver=true;s.step();s.wait([&]{return !s.d.busy;});
 need(!s.d.fault&&s.d.prefetch_tiles_filled==0&&s.d.prefetch_read_beats==8&&s.cmds==commands,"abort on block acceptance published or doubled work");
 std::cout<<"REFERENCE_PATH_CASE_PASS abort_on_block_accept=1 missing_response_retains_lease=1\n";
}
int main(int argc,char**argv){Verilated::commandArgs(argc,argv);try{full();lookahead();cancel();authentication();faults();recovery();bad_request();block_authentication();block_abort_edge();std::cout<<"REFERENCE_PATH_PASS cases=9 physical_sdram_model=0 system_integration=0\n";}catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
