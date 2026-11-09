"""Reporting-only C++ snippets; inserted by the reversible LIVE preparer."""

FIELDS = '''
    // Job tags are pinned to cs88_validate_publish_v91l's actual localparams.
    enum HashKind:unsigned {LEAF_JOB=0,EMPTY_LEAF_JOB=1,NODE_JOB=2,HUD_JOB=3,SEAL_JOB=4};
    uint64_t canonical_producer_bytes=0,canonical_request_bytes=0,canonical_ack_bytes=0,canonical_hash_bytes=0;
    uint64_t hud_request_bytes=0,hud_ack_bytes=0,hud_hash_bytes=0;
    uint64_t last_canonical_producer=0,last_canonical_ack=0,last_canonical_hash=0,reconstruct_done_fence=0;
    uint64_t root_complete=0,hud_complete=0,seal_complete=0,presentation_cycle=0;
    uint64_t last_hud_ack=0,last_hud_hash=0;
    std::array<uint64_t,5> hash_kind_counts{};
    std::array<uint64_t,9> phase_edges{};
    std::array<std::array<uint64_t,5>,9> phase_stalls{};
    std::array<uint64_t,4> slot_occupancy_edges{};
    uint64_t maximum_slots_owned=0,triple_phase_edges=0,triple_transfer_edges=0;
    bool instrument_started=false;
'''

RESET = '''
      canonical_producer_bytes=canonical_request_bytes=canonical_ack_bytes=canonical_hash_bytes=0;
      hud_request_bytes=hud_ack_bytes=hud_hash_bytes=0;
      last_canonical_producer=last_canonical_ack=last_canonical_hash=reconstruct_done_fence=0;
      root_complete=hud_complete=seal_complete=presentation_cycle=last_hud_ack=last_hud_hash=0;
      hash_kind_counts.fill(0);phase_edges.fill(0);slot_occupancy_edges.fill(0);
      for(auto &phase:phase_stalls)phase.fill(0);
      maximum_slots_owned=triple_phase_edges=triple_transfer_edges=0;instrument_started=false;
'''

METHODS = '''    void observe_fences(bool kill){
      if(d.start&&d.start_ready)instrument_started=true;
      if(!instrument_started||kill)return;
      // Phase accounting uses priority in this exact order, not disjoint
      // hardware operation: HUD writes can overlap root computation.
      const unsigned phase=canonical_producer_bytes<518400?0U:canonical_hash_bytes<518400?1U:
        !root_complete?2U:hud_hash_bytes<42240?3U:!hud_complete?4U:!seal_complete?5U:!commit_cycle?6U:!presentation_cycle?7U:8U;
      ++phase_edges[phase];
      phase_stalls[phase][0]+=d.out_valid&&!d.out_ready;
      phase_stalls[phase][1]+=d.software_hud_valid&&!d.software_hud_ready;
      phase_stalls[phase][2]+=d.candidate_req_valid&&!d.candidate_req_ready;
      phase_stalls[phase][3]+=d.join_output_valid&&!d.join_output_ready;
      phase_stalls[phase][4]+=candidate_pending&&cycle<candidate_pending->due;
      need(d.join_slots_owned<=(ROW_WRITES?3U:1U),"reported bounded join slot occupancy");
      ++slot_occupancy_edges[d.join_slots_owned];maximum_slots_owned=std::max(maximum_slots_owned,uint64_t(d.join_slots_owned));
      triple_phase_edges+=d.join_phase_fill&&d.join_phase_wait&&d.join_phase_hash;
      triple_transfer_edges+=d.out_valid&&d.out_ready&&candidate_pending&&d.join_output_valid&&d.join_output_ready;
      if(d.out_valid&&d.out_ready){
        need(++canonical_producer_bytes<=518400,"count every canonical producer acceptance, independent of tile address order");
        if(canonical_producer_bytes==518400)last_canonical_producer=cycle+1;
      }
      if(d.v_hash_result){
        need(d.v_hash_job_kind<=SEAL_JOB,"actual validator hash job kind");
        ++hash_kind_counts[d.v_hash_job_kind];
        if(d.v_hash_job_kind==NODE_JOB&&d.v_hash_job_node==1){need(!root_complete,"one actual Merkle root completion");root_complete=cycle+1;}
        if(d.v_hash_job_kind==HUD_JOB){need(d.v_hash_job_node==0&&!hud_complete,"one actual HUD hash completion");hud_complete=cycle+1;}
        if(d.v_hash_job_kind==SEAL_JOB){need(d.v_hash_job_node==0&&!seal_complete,"one actual frame seal completion");seal_complete=cycle+1;}
      }
    }
    void report_fences(){
      need(canonical_producer_bytes==518400&&canonical_request_bytes==518400&&canonical_ack_bytes==518400&&canonical_hash_bytes==518400,"all canonical accepted/requested/successfully ACKed/hashed bytes");
      need(hud_request_bytes==42240&&hud_ack_bytes==42240&&hud_hash_bytes==42240,"all HUD requested/successfully ACKed/hashed bytes");
      need(last_canonical_producer&&last_canonical_ack&&last_canonical_hash&&reconstruct_done_fence&&root_complete&&hud_complete&&seal_complete&&commit_cycle&&presentation_cycle,"every actual completion fence observed");
      need(last_canonical_producer<=last_canonical_ack&&last_canonical_ack<=last_canonical_hash&&last_canonical_hash<=root_complete,"canonical byte/ACK/hash/root causal order");
      need(last_canonical_producer<=reconstruct_done_fence&&reconstruct_done_fence<=commit_cycle,"reconstruct completion before validated commit");
      need(last_hud_ack<=last_hud_hash&&last_hud_hash<=hud_complete,"HUD successful ACK/hash/digest causal order");
      need(root_complete<hud_complete&&hud_complete<seal_complete&&seal_complete<commit_cycle&&commit_cycle<presentation_cycle,"actual validator job and publication ordering");
      need(hash_kind_counts==std::array<uint64_t,5>{{508,4,511,1,1}},"actual complete validator hash job-kind counts");
      std::cout<<"{\\"type\\":\\"live_fences\\",\\"status\\":\\"TEST_PASS\\",\\"cycle_convention\\":\\"accepted rising edge; preedge handshakes cycle+1\\",\\"canonical_producer_bytes\\":"<<canonical_producer_bytes
        <<",\\"canonical_request_bytes\\":"<<canonical_request_bytes<<",\\"canonical_successful_ack_bytes\\":"<<canonical_ack_bytes<<",\\"canonical_hash_bytes\\":"<<canonical_hash_bytes
        <<",\\"hud_request_bytes\\":"<<hud_request_bytes<<",\\"hud_successful_ack_bytes\\":"<<hud_ack_bytes<<",\\"hud_hash_bytes\\":"<<hud_hash_bytes
        <<",\\"last_canonical_producer_accept\\":"<<last_canonical_producer<<",\\"last_canonical_successful_ack\\":"<<last_canonical_ack<<",\\"last_canonical_hash_delivery\\":"<<last_canonical_hash
        <<",\\"reconstruct_done\\":"<<reconstruct_done_fence<<",\\"root_complete\\":"<<root_complete<<",\\"last_hud_successful_ack\\":"<<last_hud_ack<<",\\"last_hud_hash_delivery\\":"<<last_hud_hash
        <<",\\"hud_hash_complete\\":"<<hud_complete<<",\\"seal_complete\\":"<<seal_complete<<",\\"commit\\":"<<commit_cycle<<",\\"presentation\\":"<<presentation_cycle
        <<",\\"maximum_slots_owned\\":"<<maximum_slots_owned<<",\\"triple_phase_edges\\":"<<triple_phase_edges<<",\\"triple_transfer_edges\\":"<<triple_transfer_edges<<",\\"hash_kind_counts\\":[";
      for(unsigned n=0;n<5;++n){if(n)std::cout<<',';std::cout<<hash_kind_counts[n];}
      std::cout<<"],\\"slot_occupancy_edges\\":[";for(unsigned n=0;n<4;++n){if(n)std::cout<<',';std::cout<<slot_occupancy_edges[n];}
      std::cout<<"],\\"phase_order\\":[\\"canonical_input\\",\\"canonical_drain\\",\\"root\\",\\"HUD_delivery\\",\\"HUD_digest\\",\\"seal\\",\\"commit\\",\\"presentation\\",\\"terminal\\"],\\"phase_edges\\":[";
      for(unsigned n=0;n<9;++n){if(n)std::cout<<',';std::cout<<phase_edges[n];}
      std::cout<<"],\\"stall_order\\":[\\"producer\\",\\"software_HUD\\",\\"physical_request\\",\\"hash_delivery\\",\\"physical_service\\"],\\"phase_stalls\\":[";
      for(unsigned p=0;p<9;++p){if(p)std::cout<<',';std::cout<<'[';for(unsigned n=0;n<5;++n){if(n)std::cout<<',';std::cout<<phase_stalls[p][n];}std::cout<<']';}
      std::cout<<"],\\"stalled_profile_comparability\\":\\"same bounded service rule and seed; different RNG draw counts and accepted traffic prevent identical cycle-trace comparison\\",\\"physical_SDRAM\\":false}\\n";
    }
'''

AFTER_EDGE = '''      if(instrument_started&&vf){
        if(canonical_producer_bytes==518400&&d.reconstruct_done&&!reconstruct_done_fence)reconstruct_done_fence=cycle;
        if(d.v_frame_presented&&d.v_front_fid==be32(vf->packet,8))presentation_cycle=cycle;
      }
'''
