// Reuse the unchanged integrated endpoint/oracle, with a separate fault campaign.
#define main cu78_positive_campaign_main
#include "tb_system.cpp"
#undef main

static void reject_candidate(Sim &s,cu66::Bytes bytes,bool partial_abort,
                             std::shared_ptr<const cu66::Frame> accepted){
 const auto accepted_count=s.d.accepted_count;
 const auto rejected_count=s.d.rejected_count;
 const auto bank=s.d.reference_bank;
 const auto front_bank=s.d.lcd_front_bank;
 const auto front_generation=s.d.lcd_front_generation;
 const auto accepted_hud=s.hud.accepted();
 const auto good_lines=s.good_lines;
 while(!s.d.start_ready)s.tick();
 s.generation++;s.packet=std::move(bytes);
 if(!partial_abort)s.packet.back()^=1;
 s.prepared=s.result_sent=s.drain_sent=s.aux_pending=false;
 s.candidate=nullptr;s.word_cursor=s.read_cursor=0;
 s.hud_write_requests=s.hud_read_requests=s.soft_calls=0;
 s.drop_ack=s.did_drop_ack=false;
 const auto writes=s.d.model_writes;
 const auto begin=s.cycles;
 s.d.start_generation=s.generation;s.d.start_packet_bytes=s.packet.size();
 s.d.start_valid=1;while(!s.tick().start){}s.d.start_valid=0;
 bool pulsed=false;unsigned seen_error=0,canonical_words=0;
 for(;;){
  need(s.cycles-begin<10000000,"fault campaign drain watchdog");
  if(partial_abort&&!pulsed&&canonical_words>=64&&s.d.memory_tile_busy){
   s.d.abort_i=1;s.prepared=false;pulsed=true;
  }
  const auto seq=s.d.write_event_sequence;
  s.tick();s.d.abort_i=0;
  if(s.d.write_event_sequence!=seq){
   const unsigned base=cu70_map::canonical_base(s.d.candidate_bank);
   if(s.d.write_event_address>=base&&s.d.write_event_address<base+259200)canonical_words+=s.d.write_event_sequence-seq;
  }
  if(s.d.error)seen_error=s.d.error_code;
  need(!s.d.done&&!s.d.validated_ready,"failed candidate reported success");
  need(!s.d.lcd_error&&s.d.lcd_underruns==0,"fault disturbed native scanout");
  need(s.d.reference_bank==bank&&s.d.reference_frame_id==accepted->id&&
       s.d.accepted_count==accepted_count,"failed candidate changed reference");
  need(s.d.lcd_front_bank==front_bank&&s.d.lcd_front_generation==front_generation,
       "failed candidate changed display front");
  if(s.d.aborted)break;
 }
 need(s.d.rejected_count==rejected_count+1,"fault rejection count");
 need(s.hud.accepted()==accepted_hud,"failed candidate changed accepted HUD");
 need(partial_abort?pulsed:seen_error!=0,"fault not exercised");
 if(!partial_abort)need(s.d.model_writes==writes,"bad CRC wrote memory");
 else need(canonical_words>=64&&s.d.model_writes>writes&&s.soft_calls>0,"canonical partial write/processor ABORT missing");
 s.verify(accepted);
 // Retain the old native front through at least one additional refresh.
 const auto rasters=s.timings[front_generation].complete_rasters;
 while(s.timings[front_generation].complete_rasters==rasters)s.tick();
 need(s.good_lines>good_lines&&s.black_lines==0,"old front did not remain exact");
 std::cout<<"SYSTEM_FAULT_PASS kind="<<(partial_abort?"partial_write_abort":"bad_crc")
  <<" generation="<<s.generation<<" cycles="<<s.cycles-begin
  <<" physical_write_words="<<s.d.model_writes-writes
  <<" canonical_write_words_observed="<<canonical_words
  <<" active_tile_at_abort="<<pulsed
  <<" error="<<seen_error<<" processor_abort_calls="<<s.soft_calls
  <<" accepted_count="<<s.d.accepted_count<<" old_front_full_raster=1"<<std::endl;
}

int main(int argc,char**argv){try{
 need(argc==2,"index path");std::filesystem::path index=argv[1];
 std::ifstream f(index);need(bool(f),"index open");
 std::vector<cu66::Bytes> packets;std::vector<std::shared_ptr<const cu66::Frame>> gold;
 cu66::Decoder decoder;std::string line;
 for(unsigned i=0;i<2;i++){
  need(bool(std::getline(f,line)),"two fixtures required");
  std::stringstream row(line);std::string chain,ordinal,path;
  std::getline(row,chain,'\t');std::getline(row,ordinal,'\t');std::getline(row,path,'\t');
  need(chain=="0","chronological cohort");packets.push_back(load(index.parent_path()/path));
  gold.push_back(decoder.receive(packets.back()));
 }
 Sim s(false);s.run(packets[0],gold[0],0);
 while(s.timings[1].complete_rasters==0)s.tick();
 reject_candidate(s,packets[1],false,gold[0]);
 reject_candidate(s,packets[1],true,gold[0]);
 s.run(packets[1],gold[1],1,true);
 while(s.timings[s.generation].complete_rasters==0)s.tick();
 need(s.d.accepted_count==2&&s.d.rejected_count==2&&s.d.lcd_underruns==0&&s.black_lines==0,
      "fault campaign final state");
 std::cout<<"SYSTEM_FAULT_CAMPAIGN_PASS rejected=2 accepted=2 no_per_source_reset=1"
  <<" underruns="<<s.d.lcd_underruns<<" black_lines="<<s.black_lines
  <<" clean_lines="<<s.good_lines<<std::endl;
 }catch(const std::exception&e){std::cerr<<"FAIL "<<e.what()<<std::endl;return 1;}}
