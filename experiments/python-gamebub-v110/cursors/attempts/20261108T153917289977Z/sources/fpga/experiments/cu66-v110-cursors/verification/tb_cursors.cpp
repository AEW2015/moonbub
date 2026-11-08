// The complete original whole-scratch/golden/hazard/boundary suite runs first.
#include "inherited_bank.cpp"
static bool reference_cursor_nonzero(const ProbeBench&b){
 for(unsigned bank=0;bank<3;++bank)if(get(b.d.verify_reference_cursors,bank*32,32))return true;
 return false;
}
static void restart_and_finish(ProbeBench&b,const Transaction&p,unsigned profile){
 b.active=&p;b.verify_dense=true;b.outputs=0;++b.epoch;
 b.d.begin_epoch=b.epoch;b.d.begin_blocks=p.blocks;b.d.begin_raw=p.raw;
 b.d.begin_serial_clear=profile&1;b.d.begin_overlap=(profile>>1)&1;
 b.d.begin_prefetch=(profile>>2)&1;b.d.begin_tile_overlap=(profile>>3)&1;
 b.d.begin_count1=p.records[1].size();b.d.begin_count2=p.records[2].size();b.d.begin_count3=p.records[3].size();
 b.starts[0]=32;b.starts[1]=32+((p.blocks*2+15)&~15U);
 b.starts[2]=b.starts[1]+((p.records[1].size()*4+15)&~15U);
 b.starts[3]=b.starts[2]+((p.records[2].size()*4+15)&~15U);
 b.d.reset=0;b.d.abort_valid=0;b.d.coef_valid=0;b.d.band_end_valid=0;b.d.seal_valid=0;
 b.d.begin_valid=1;b.d.eval();need(b.d.begin_ready,"new owner not accepted after drain");b.tick();b.d.begin_valid=0;
 need(b.d.verify_cursor_owner_live&&b.d.verify_cursor_equal,"live new owner cursors not restored");
 for(unsigned bank=0;bank<3;++bank)need(get(b.d.verify_cursors,bank*32,32)==0,"new owner cursor not zero");
 for(unsigned band=0;band<4;++band){
  for(const auto&r:p.records[band]){
   while(!b.d.coef_ready){b.tick();}
   b.d.coef_band=band;b.d.coef_block=r.block;b.d.coef_index=r.index;
   b.d.coef_value=uint16_t(r.value);b.d.coef_epoch=b.epoch;b.d.coef_valid=1;b.tick();b.d.coef_valid=0;
   while(!b.d.coef_ready){b.tick();}
   need(!b.d.error,"restored owner coefficient rejected");
  }
  b.d.band_end_valid=1;b.d.band_end_band=band;b.d.band_end_epoch=b.epoch;b.tick();b.d.band_end_valid=0;
  if(band<3)b.wait(1);
 }
 while(!b.d.seal_ready){b.tick();}
 b.d.seal_valid=1;b.d.seal_epoch=b.epoch;b.tick();b.d.seal_valid=0;b.finish();
}
int main(int argc,char**argv){try{
 need(inherited_bank_main(argc,argv)==0,"complete inherited scratch/boundary suite");
 const unsigned seed=unsigned(std::stoul(argv[1]));
 std::ofstream trace(std::string(argv[2])+"-retirement.jsonl");need(bool(trace),"retirement trace open");
 unsigned cases=0,divergences=0,restored=0;
 for(unsigned action=0;action<6;++action){
  auto p=packet(9,false,seed+action);ProbeBench b(seed+action+2000,trace);b.ingest(p,6);
  if(action==2){const unsigned addr=b.starts[1]+4;for(unsigned byte=0;byte<4;++byte)b.ram[addr+byte]=0;}
  for(unsigned n=0;;++n){
   need(n<100000,"cursor retirement target watchdog");b.d.dense_ready=1;b.d.eval();
   const bool hit=b.d.verify_position_use&&get(b.d.verify_reference_cursors,(b.d.verify_read_band-1)*32,32)>0;
   const bool bad=hit&&b.d.verify_read_band==1&&b.d.verify_read_word==0;
   const bool physical=b.pending&&!b.owner_write&&b.d.debug_state==11&&reference_cursor_nonzero(b);
   if((action<2&&hit)||(action==2&&bad)||(action==3&&hit&&!b.pending&&!b.d.debug_outstanding)||(action>=4&&physical))break;
   b.tick();need(!b.d.done&&!b.d.error,"target retired before directed event");
  }
  if(action<2)b.abort_and_drain(action==1);
  else if(action==2){b.tick();need(b.d.error==3&&!b.d.verify_cursor_owner_live,"bad record did not retire");b.abort_and_drain(false);}
  else if(action==3){
   // Deliberate unowned interface response, without depositing internal state.
   b.d.mem_req_ready=0;b.d.mem_rsp_valid=1;b.d.mem_rsp_epoch=b.epoch+99;b.d.mem_rsp_error=0;
   b.d.clk=0;b.d.eval();b.check();b.d.clk=1;b.d.eval();b.check();b.d.clk=0;b.d.eval();b.check();
   ++b.clocks;++totals.edges;b.d.mem_rsp_valid=0;
   need(b.d.error==6&&!b.d.verify_cursor_owner_live,"stray response did not retire");b.abort_and_drain(false);
  }else{
   b.hold_ack=true;for(unsigned n=0;n<8;++n)b.tick();
   b.d.reset=action==5;b.d.abort_valid=action==4;b.d.abort_epoch=b.epoch;b.tick();
   b.d.reset=0;b.d.abort_valid=0;
   need(b.pending&&b.d.debug_state==25&&!b.d.begin_ready,"accepted read owner was discarded");
   b.d.begin_valid=1;b.d.begin_epoch=b.epoch+1;
   for(unsigned n=0;n<4;++n){b.tick();need(b.d.debug_state==25&&!b.d.begin_ready,"begin escaped physical drain");}
   b.d.begin_valid=0;b.hold_ack=false;b.stale=true;b.tick();
   need(b.pending&&b.d.debug_state==25,"wrong ACK retired owner");b.tick();
   need(!b.pending&&b.d.debug_state==0,"matching late ACK did not restore IDLE");b.tick();
  }
  need(!b.d.verify_cursor_owner_live&&!b.d.verify_cursor_equal,"inactive cursor divergence not exercised");
  ++divergences;
  auto next=packet(3,false,seed+action+100);restart_and_finish(b,next,6);++restored;++cases;
 }
 need(cases==6&&divergences==6&&restored==6,"cursor retirement/restoration coverage");
 std::cout<<"{\"type\":\"cursor_retirement_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed
          <<",\"cursor_retirement_cases\":"<<cases<<",\"inactive_divergence_cases\":"<<divergences
          <<",\"restored_new_owner_cases\":"<<restored<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"CURSOR_RETIREMENT_FAIL "<<e.what()<<'\n';return 1;}}
