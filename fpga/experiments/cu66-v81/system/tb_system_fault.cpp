// Actual V81 mode-3 endpoint/oracle. Producer and observer files remain unchanged.
#define main cu81_positive_campaign_main
#include "tb_system.cpp"
#undef main

static unsigned aborted_endpoint_releases=0;
static void reject_candidate(Sim&s,cu66::Bytes bytes,bool partial_abort,unsigned ordinal,
                             std::shared_ptr<const cu66::Frame>accepted){
 const auto accepted_count=s.d.accepted_count,rejected_count=s.d.rejected_count;
 const auto bank=s.d.reference_bank,front_bank=s.d.lcd_front_bank;
 const auto front_generation=s.d.lcd_front_generation;
 const auto accepted_hud=s.hud.accepted();const auto good_lines=s.good_lines;
 s.monitor.phase="fault_readiness_wait";const auto readiness=s.cycles;
 while(!s.d.start_ready){need(s.cycles-readiness<10000000,"fault readiness watchdog");s.tick();}
 s.monitor.releases.at(ordinal)=s.cycles;s.monitor.queue(s.cycles);
 s.generation++;s.packet=std::move(bytes);if(!partial_abort)s.packet.back()^=1;
 s.prepared=s.result_sent=s.drain_sent=s.aux_pending=false;s.candidate=nullptr;
 s.word_cursor=s.read_cursor=s.hud_write_requests=s.hud_read_requests=s.soft_calls=0;
 s.drop_ack=s.did_drop_ack=false;s.packet_pending=false;
 s.occupancy_bins.fill(0);s.stage_bins.fill(0);s.command_reads.fill(0);s.command_writes.fill(0);
 s.tile_events.fill(0);s.tile_masks.fill(0);s.fill_events=0;s.path_events.fill(0);s.offered_masks.fill(0);s.backend_masks.fill(0);s.raw_masks.fill(0);s.snapshot_masks.fill(0);s.block_masks.fill(0);s.profiling=true;
 const auto writes=s.d.model_writes;const auto begin=s.cycles;
 s.monitor.phase=partial_abort?"partial_write_read_accept_abort":"bad_crc";
 s.d.start_generation=s.generation;s.d.start_packet_bytes=s.packet.size();s.d.start_valid=1;
 while(!s.tick().start)need(s.cycles-begin<10000000,"fault admission watchdog");s.d.start_valid=0;
 bool pulsed=false,producer_stopped=false,pending_lookup=false;
 unsigned seen_error=0,canonical_words=0,abort_address=0;
 uint64_t abort_cycle=0,accepted_at_abort=0;
 for(;;){
  need(s.cycles-begin<10000000,"fault candidate watchdog");
  if(partial_abort&&!producer_stopped&&canonical_words>=64){s.prepared=false;producer_stopped=true;}
  if(partial_abort&&!pulsed&&producer_stopped&&!s.aux_pending&&
     s.d.trace_command_valid&&s.d.trace_command_client==3&&!s.d.trace_command_write){
   const bool pending=s.tile_events[0]>s.tile_events[1]&&!(s.d.trace_tile_events&2);
   // Prefer the combined pending-lookup case, with a bounded fallback explicitly reported.
   if(pending||s.cycles-begin>200000){
    need(!s.d.clk&&s.c->time()%10000==0,"abort injection must precede next tick at falling edge");
    s.d.abort_i=1;s.prepared=false;s.drive();s.eval();
    need(s.d.trace_command_valid&&s.d.trace_command_client==3&&!s.d.trace_command_write,
         "external abort withdrew selected physical read accept");
    abort_address=s.d.trace_command_address;abort_cycle=s.cycles+1;
    accepted_at_abort=s.command_reads[3];pending_lookup=pending;pulsed=true;
   }
  }
  const auto seq=s.d.write_event_sequence;s.tick();
  if(pulsed&&s.cycles==abort_cycle){
   need(s.command_reads[3]==accepted_at_abort+1,"abort did not coincide with actual client3 controller accept");
   std::cout<<"SYSTEM_FAULT_ABORT_ACCEPT generation="<<s.generation<<" cycle="<<abort_cycle
    <<" address="<<abort_address<<" client=3 write=0 canonical_words_before_abort="<<canonical_words
    <<" pending_lookup="<<pending_lookup<<std::endl;
  }
  s.d.abort_i=0;
  const unsigned candidate_base=cu70_map::canonical_base(s.d.candidate_bank);
  if(s.d.write_event_sequence!=seq&&s.d.write_event_address>=candidate_base&&s.d.write_event_address<candidate_base+259200)
   canonical_words+=s.d.write_event_sequence-seq;
  if(s.d.error)seen_error=s.d.error_code;
  if(s.d.done||s.d.validated_ready)throw std::runtime_error("failed candidate reported success canonical_words="+std::to_string(canonical_words)+" physical_prefetch_accepts="+std::to_string(s.command_reads[3])+" abort_pulsed="+std::to_string(pulsed));
  need(s.d.reference_valid&&s.d.reference_bank==bank&&s.d.reference_frame_id==accepted->id&&s.d.accepted_count==accepted_count,"failed candidate changed accepted reference");
  need(s.d.lcd_front_bank==front_bank&&s.d.lcd_front_generation==front_generation,"failed candidate changed physical front");
  if(s.d.aborted)break;
 }
 s.profiling=false;
 // These are endpoint releases, not successful commits or fabricated raster obligations.
 s.monitor.acknowledged++;aborted_endpoint_releases++;s.monitor.queue(s.cycles);
 std::cout<<"SYSTEM_FAULT_ENDPOINT_RELEASE generation="<<s.generation<<" cycle="<<s.cycles
  <<" aborted_endpoint_releases="<<aborted_endpoint_releases<<" successful_commit=0"<<std::endl;
 need(s.d.rejected_count==rejected_count+1&&s.hud.accepted()==accepted_hud,"fault changed rejection/HUD acceptance state");
 if(!partial_abort)need(seen_error!=0&&s.d.model_writes==writes&&s.command_reads[3]==0,"bad CRC issued writes or launched prefetch");
 else need(pulsed&&canonical_words>=64&&s.d.model_writes>writes&&s.soft_calls>0,"partial canonical write/accepted-read abort/CPU abort missing");
 s.monitor.phase="fault_quiescence_wait";const auto drain_begin=s.cycles;
 while(s.d.busy||s.d.prefetch_busy||s.d.memory_tile_busy||s.d.memory_aux_busy||!s.d.memory_idle){
  need(s.cycles-drain_begin<1000000,"fault backend quiescence watchdog");s.tick();
 }
 need(!s.d.prefetch_fault,"normal external abort raised prefetch fault");
 if(partial_abort){auto found=s.prefetch_events.find(s.generation);need(found!=s.prefetch_events.end()&&found->second.aborted==1&&found->second.done==1,"partial abort epoch event accounting");}
 s.verify(accepted);
 const auto rasters=s.timings[front_generation].complete_rasters;
 s.monitor.phase="fault_old_front_full_raster";
 while(s.timings[front_generation].complete_rasters==rasters){need(s.cycles-drain_begin<10000000,"fault old-front raster watchdog");s.tick();}
 need(s.good_lines>good_lines&&s.black_lines==0&&s.hud.accepted()==accepted_hud,"old native front/HUD did not remain exact");
 const auto event_position=s.prefetch_events.find(s.generation);const auto epoch_events=event_position==s.prefetch_events.end()?PrefetchEvents{}:event_position->second;
 std::cout<<"SYSTEM_FAULT_PASS kind="<<(partial_abort?"partial_write_read_accept_abort":"bad_crc")
  <<" generation="<<s.generation<<" cycles="<<s.cycles-begin<<" physical_write_words="<<s.d.model_writes-writes
  <<" canonical_write_words_observed="<<canonical_words<<" actual_prefetch_read_accepts="<<s.command_reads[3]
  <<" read_accept_coincident_abort="<<pulsed<<" pending_lookup_at_abort="<<pending_lookup
  <<" abort_cycle="<<abort_cycle<<" abort_read_address="<<abort_address<<" error="<<seen_error
  <<" epoch_done_events="<<epoch_events.done<<" epoch_aborted_events="<<epoch_events.aborted<<" epoch_done_cycle="<<epoch_events.done_cycle<<" epoch_aborted_cycle="<<epoch_events.aborted_cycle
  <<" processor_abort_calls="<<s.soft_calls<<" accepted_count="<<s.d.accepted_count
  <<" wrapper_and_prefetch_drained=1 raw_bridge_and_controller_idle_observed=1 accepted_reference_unchanged=1 accepted_HUD_unchanged=1 old_front_full_raster=1"<<std::endl;
}
int main(int argc,char**argv){try{
 need(argc==2,"native index path");std::filesystem::path index=argv[1];std::ifstream f(index);need(bool(f),"index open");
 std::vector<cu66::Bytes> packets;std::vector<std::shared_ptr<const cu66::Frame>> gold;cu66::Decoder decoder;std::string line;
 for(unsigned i=0;i<2;i++){
  need(bool(std::getline(f,line)),"two fixtures required");std::stringstream row(line);std::string chain,ordinal,path;
  std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');need(chain=="0"&&unsigned(std::stoul(ordinal))==i,"chronological cohort0 fixtures");
  packets.push_back(load(index.parent_path()/path));gold.push_back(decoder.receive(packets.back()));
 }
 need(gold[0]->key&&!gold[1]->key,"key then delta fixtures");
 Sim s(false,4,3);s.run(packets[0],gold[0],0);
 while(s.timings[1].complete_rasters==0)s.tick();
 reject_candidate(s,packets[1],false,1,gold[0]);
 reject_candidate(s,packets[1],true,2,gold[0]);
 s.run(packets[1],gold[1],3,true);
 s.monitor.phase="fault_recovery_final_tail";const auto tail=s.cycles;
 while(!s.monitor.raster_due.empty()||s.cycles-tail<3500000)s.tick();
 need(s.timings[4].complete_rasters>0&&s.d.accepted_count==2&&s.d.rejected_count==2&&aborted_endpoint_releases==2,"fault campaign recovery state");
 need(s.monitor.admitted==4&&s.monitor.acknowledged==4&&s.monitor.total==0&&s.monitor.in_service==0&&s.monitor.waiting==0,"fault endpoint queue accounting");
 need(s.d.lcd_underruns==0&&s.black_lines==0&&!s.monitor.saw_lcd_error&&!s.monitor.saw_memory_error&&!s.monitor.saw_underrun,"fault display health");
 std::cout<<"SYSTEM_FAULT_CAMPAIGN_PASS rejected=2 accepted=2 attempts=4 prefetch_mode=3 no_per_source_reset=1 aborted_endpoint_releases="<<aborted_endpoint_releases
  <<" underruns="<<s.d.lcd_underruns<<" black_lines="<<s.black_lines<<" clean_lines="<<s.good_lines
  <<" health_observations="<<s.monitor.observations<<" admitted="<<s.monitor.admitted<<" endpoint_releases="<<s.monitor.acknowledged
  <<" recovery_complete_rasters="<<s.timings[4].complete_rasters<<" recovery_commit_calls="<<s.soft_calls<<" observer_unit_only=0 hardware_fault_injection=0 normal_external_abort=1"<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
