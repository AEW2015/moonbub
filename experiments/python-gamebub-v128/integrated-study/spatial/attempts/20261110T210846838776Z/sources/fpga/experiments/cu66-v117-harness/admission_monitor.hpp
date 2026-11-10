// Independent public-command ledger for the actual full-top transport model.
// Candidate ownership bits never erase the ledger; only actual child delivery
// or externally driven reset/abort retire an expected local command.
struct AdmissionMonitor {
 Bench& b;
 using Command=std::array<uint64_t,10>;
 std::optional<Command> expected;
 Command last_accepted{};
 bool accepted_this_edge=false,delivered_this_edge=false,last_accepted_valid=false;
 uint64_t accepted_at=0,accepted_sequence=0,accepts=0,deliveries=0,cancelled_pending=0,poisoned=0;
 explicit AdmissionMonitor(Bench& bench):b(bench){}
 Command live()const{return {b.d.packet_bytes,b.d.epoch,b.d.accepted_ref_valid,b.d.accepted_qcache_valid,
  b.d.accepted_ref_fid,b.d.accepted_ref_generation,b.d.serial_clear,b.d.write_overlap,b.d.read_prefetch,b.d.tile_overlap};}
 Command captured()const{const auto&r=*b.d.rootp;return {
  r.cs88_pipeline_v91k__DOT__command_packet_bytes,r.cs88_pipeline_v91k__DOT__command_epoch,
  r.cs88_pipeline_v91k__DOT__command_accepted_ref_valid,r.cs88_pipeline_v91k__DOT__command_accepted_qcache_valid,
  r.cs88_pipeline_v91k__DOT__command_accepted_ref_fid,r.cs88_pipeline_v91k__DOT__command_accepted_ref_generation,
  r.cs88_pipeline_v91k__DOT__command_serial_clear,r.cs88_pipeline_v91k__DOT__command_write_overlap,
  r.cs88_pipeline_v91k__DOT__command_read_prefetch,r.cs88_pipeline_v91k__DOT__command_tile_overlap};}
 void pre(){
  const auto&r=*b.d.rootp;accepted_this_edge=false;delivered_this_edge=false;
  const bool kill=b.d.reset||b.d.abort_packet;
  const bool public_accept=b.d.start&&b.d.start_ready&&!kill;
  need(bool(r.cs88_pipeline_v91k__DOT__command_accept)==public_accept,"public reservation command acceptance binding");
  if(kill){
   need(!r.cs88_pipeline_v91k__DOT__accepted_start,"child command delivered under external revocation");
   if(expected){++cancelled_pending;expected.reset();}
   return;
  }
  if(r.cs88_pipeline_v91k__DOT__accepted_start){
   need(expected.has_value(),"unsolicited child command without accepted public owner");
   need(b.cycle==accepted_at+1,"registered command must deliver at E+1");
   need(captured()==*expected,"child command delivery changed complete captured tuple");
   need(r.cs88_pipeline_v91k__DOT__owner_sequence==accepted_sequence,"child command owner changed before delivery");
   expected.reset();++deliveries;delivered_this_edge=true;
  }
  if(public_accept){
   need(!expected&&!delivered_this_edge,"command reservation reused before retirement");
   expected=live();last_accepted=*expected;last_accepted_valid=true;accepted_at=b.cycle;
   accepted_this_edge=true;++accepts;
  }
 }
 void post(){const auto&r=*b.d.rootp;
  if(accepted_this_edge){
   need(expected&&captured()==*expected,"public command tuple not atomically captured");
   accepted_sequence=r.cs88_pipeline_v91k__DOT__owner_sequence;
   need(r.cs88_pipeline_v91k__DOT__command_pending&&!r.cs88_pipeline_v91k__DOT__admission_credit,"accepted command retained no exclusive pending reservation");
   need(!b.d.in_ready&&!b.d.cache_ready&&!b.d.out_valid&&!b.d.ref_req_valid&&!b.d.mem_req_valid&&!b.d.coefficient_valid&&!b.d.residual_valid,"pending command leaked public transfer eligibility");
   need(!b.d.done&&!b.d.error&&!b.d.cache_complete,"pending command exposed stale previous-owner status");
   poison();
  }
  if(delivered_this_edge)need(!r.cs88_pipeline_v91k__DOT__command_pending&&r.cs88_pipeline_v91k__DOT__owner_delivered,"child delivery did not retire pending command once");
 }
 void arm_controls(){b.d.serial_clear=0;b.d.write_overlap=1;b.d.read_prefetch=1;b.d.tile_overlap=1;}
 void poison(){
  need(last_accepted_valid,"poison without accepted command");const auto&c=last_accepted;
  b.d.packet_bytes=~uint32_t(c[0]);b.d.epoch=~uint32_t(c[1]);
  b.d.accepted_ref_valid=!c[2];b.d.accepted_qcache_valid=!c[3];
  b.d.accepted_ref_fid=~uint32_t(c[4]);b.d.accepted_ref_generation=~uint64_t(c[5]);
  b.d.serial_clear=!c[6];b.d.write_overlap=!c[7];b.d.read_prefetch=!c[8];b.d.tile_overlap=!c[9];++poisoned;
 }
};
