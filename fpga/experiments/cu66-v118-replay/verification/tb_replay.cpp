#define main inherited_ready_main
#include "tb_ready.cpp"
#undef main
#ifndef REPLAY_TEST_MODE
#error REPLAY_TEST_MODE must name the independently compiled caller mode
#endif
#define OLD(n) d.rootp->ready_probe__DOT__old_dut__DOT__##n
#define NEW(n) d.rootp->ready_probe__DOT__new_dut__DOT__##n
#define BOTH(n,v) do { OLD(n)=(v); NEW(n)=(v); } while(0)
static uint64_t directed_edges=0,accepts=0,response_checks=0,tag_faults=0,cancels=0,bound_checks=0,mutations=0;
static void need(bool p,const std::string&s){if(!p)throw std::runtime_error(s);}
static void checked(Vready_probe&d){d.eval();need(d.probe_public_equal,"all public outputs differ");need(d.probe_internal_equal,"common whole caller owner/control differs");need(d.probe_scale_equal,"whole raw scale store differs");}
static void edge(Vready_probe&d){
 d.clk=0;checked(d);const bool request=d.frame_read_req;const uint32_t addr=d.frame_read_addr,epoch=NEW(frame_epoch);
 if(request)++accepts;
 d.clk=1;checked(d);d.clk=0;checked(d);++directed_edges;
 if(request){need(NEW(accepted_replay_address)==addr&&NEW(accepted_replay_epoch)==epoch,"actual accepted address/epoch was not captured whole");}
}
static void setup(Vready_probe&d,uint32_t offset,uint32_t cursor,uint32_t size,unsigned state){
 d.reset=d.abort_packet=d.start=0;BOTH(state,state);BOTH(frame_running_owned,1);BOTH(frame_epoch,9);BOTH(latched_size,size);
 BOTH(selected_offset,offset);BOTH(refill_cursor,cursor);BOTH(selected_length,256);BOTH(selected_blocks,1);BOTH(current_child_epoch,1);
 BOTH(admission__DOT__state,26);BOTH(admission__DOT__size_bytes,size);BOTH(admission__DOT__receipt_epoch,9);
}
static void mode0(unsigned seed){
 for(uint32_t address:{0U,1U,255U,32767U,49151U})for(unsigned action=0;action<5;++action){
  Driver driver(seed+address+action,"/dev/null");auto&d=driver.d;d.reset=1;edge(d);d.reset=0;
  setup(d,address,0,49152,6);BOTH(admission__DOT__memory[address],uint8_t(address^0x5aU));
  checked(d);need(d.frame_read_req&&d.frame_read_addr==address,"declared request did not actually accept");edge(d);
  need(d.frame_state==7&&d.frame_read_rsp,"real synchronous reply did not enter WAIT");
  need(NEW(accepted_replay_address)==address&&NEW(accepted_replay_epoch)==9,"request lease mixed owner");
  if(action==1){BOTH(admission__DOT__ram_addr,address^1U);++tag_faults;}
  if(action==2){BOTH(admission__DOT__ram_epoch,10);++tag_faults;}
  if(action==3){d.reset=1;++cancels;}
  if(action==4){d.abort_packet=1;++cancels;}
  edge(d);
  if(action==0){need(d.frame_state==8&&NEW(refill_data)==uint8_t(address^0x5aU),"matching physical reply lost data/owner");++response_checks;}
  else if(action<3)need(d.frame_state==15&&d.error==67,"wrong physical response tag escaped original error priority");
  else need(d.frame_state==0&&!d.error,"cancel/reset failed original immediate priority");
 }
 // Full32-bit request selection and bound behavior are retained literally.
 for(uint32_t offset:{49152U,65536U,0x7fffffffU,0xfffffffeU,0xffffffffU}){
  Driver driver(seed+offset,"/dev/null");auto&d=driver.d;d.reset=1;edge(d);d.reset=0;setup(d,offset,0,49152,6);
  for(unsigned n=0;n<3;++n){checked(d);need(!d.frame_read_req&&d.frame_read_addr==offset,"full32 admission bound narrowed or accepted");edge(d);need(d.frame_state==6,"blocked request changed original state");++bound_checks;}
 }
}
static void mode1(unsigned seed){
 for(uint32_t offset:{0U,255U,32767U,49136U}){
  Driver driver(seed+offset,"/dev/null");auto&d=driver.d;d.reset=1;edge(d);d.reset=0;setup(d,offset,0,49152,5);
  for(unsigned i=0;i<16;++i){BOTH(admission__DOT__memory[offset+i],uint8_t(i+0x31U));}
  edge(d);need(d.frame_state==16,"real CORE_START failed to start overlap queue");
  for(unsigned n=0;n<8;++n){
   checked(d);if(d.frame_read_rsp){need(d.frame_rsp_addr==NEW(accepted_replay_address)&&d.frame_rsp_epoch==NEW(accepted_replay_epoch),"reply owner differs from previous actual acceptance");++response_checks;}
   edge(d);
   // Once the queue has its actual start owner, the caller's selection is a
   // different private context. Both old and new callers get the same deposit;
   // no lease, queue tag, pending response or output is edited by this fixture.
   if(n==1){BOTH(selected_offset,0xf1234567U);BOTH(refill_cursor,0xfedcba98U);++mutations;}
  }
 }
}
int main(int argc,char**argv){try{
 need(inherited_ready_main(argc,argv)==0,"all inherited cache/readiness oracles");need(argc==3,"seed and trace required");const unsigned seed=unsigned(std::stoul(argv[1]));
 if(REPLAY_TEST_MODE==0)mode0(seed);else mode1(seed);
 std::cout<<"{\"type\":\"v118_replay_lease_verdict\",\"status\":\"TEST_PASS\",\"mode\":"<<REPLAY_TEST_MODE<<",\"directed_edges\":"<<directed_edges<<",\"actual_request_accepts\":"<<accepts<<",\"matching_response_checks\":"<<response_checks<<",\"wrong_tag_cases\":"<<tag_faults<<",\"reset_abort_cases\":"<<cancels<<",\"full32_bound_checks\":"<<bound_checks<<",\"unrelated_cursor_mutations\":"<<mutations<<",\"pair_skipped_edges\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V118_REPLAY_FAIL "<<e.what()<<'\n';return 1;}}
