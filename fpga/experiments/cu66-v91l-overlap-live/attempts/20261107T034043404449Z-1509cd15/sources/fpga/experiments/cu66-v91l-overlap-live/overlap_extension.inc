    struct RgbDescriptor {std::string id;uint32_t fid=0,epoch=0;uint64_t generation=0;unsigned bank=3;uint64_t begin=0,commit=0,input_complete=0;};
    std::optional<RgbDescriptor> rgb_owner;
    bool rgb_terminal_seen=false,guard_mode=false;
    uint64_t rgb_terminal_cycle=0,guard_release_cycle=0,guard_hold_cycles=0;
    uint64_t overlap_cycles=0,contended_offer_cycles=0,rgb_candidate_overlap_requests=0,rgb_reference_overlap_requests=0,rgb_scratch_overlap_requests=0;
    uint64_t last_rgb_close=0,key_rgb_close=0,key_rgb_start=0,delta_begin=0,delta_commit=0;
    void overlap_observe(){
      if(!rgb_owner)return;
      need(d.display_active||!d.rgb_busy,"RGB engine lacks actual protected display lease");
      if(d.display_active)need(d.display_bank==rgb_owner->bank&&d.display_epoch==rgb_owner->epoch&&d.display_fid==rgb_owner->fid&&d.display_generation==rgb_owner->generation,"display lease changed during overlapped decode");
      if(d.rgb_busy&&d.v_bank_active)++overlap_cycles;
      if(d.rgb_mem_req_valid&&(d.candidate_req_valid||d.fabric_ref_line_req_valid||d.mem_req_valid))++contended_offer_cycles;
      if(d.candidate_req_valid&&d.candidate_req_ready)++rgb_candidate_overlap_requests;
      if(d.ref_req_valid&&d.ref_req_ready)++rgb_reference_overlap_requests;
      if(d.mem_req_valid&&d.mem_req_ready)++rgb_scratch_overlap_requests;
    }
    void rgb_observe(){
      need(cycle<160000000,"finite shared overlapped live watchdog");
      if(d.display_engine_start){
        need(rgb_owner.has_value(),"actual RGB engine start lacks descriptor");const auto &r=*rgb_owner;
        physical_events<<"{\"type\":\"rgb_start\",\"id\":"<<quote(r.id)<<",\"fid\":"<<r.fid<<",\"epoch\":"<<r.epoch<<",\"generation\":"<<r.generation<<",\"bank\":"<<r.bank<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
      }
      if(d.rgb_mem_req_valid&&d.rgb_mem_req_ready){need(rgb_checking&&rgb_owner&&cycle>=rgb_owner->commit,"physical display read before its validated commit");++rgb_physical_requests;}
      if(d.rgb_mem_rsp_valid&&d.rgb_mem_rsp_ready){need(rgb_checking&&!d.rgb_mem_rsp_error,"physical read response outside immutable RGB owner");++rgb_physical_responses;}
      if(d.rgb_line_req_valid&&d.rgb_line_req_ready){need(rgb_checking&&rgb_owner&&d.rgb_line_req_epoch==rgb_owner->epoch,"RGB canonical line request immutable lease");++rgb_lines;
        physical_events<<"{\"type\":\"line_req\",\"id\":"<<quote(rgb_owner->id)<<",\"cycle\":"<<cycle<<",\"address\":"<<d.rgb_line_req_addr<<",\"epoch\":"<<d.rgb_line_req_epoch<<",\"token\":"<<d.rgb_line_req_token<<"}\n";}
      if(d.rgb_line_rsp_valid&&d.rgb_line_rsp_ready){need(rgb_checking&&rgb_owner&&!d.rgb_line_rsp_error&&d.rgb_line_rsp_epoch==rgb_owner->epoch,"RGB canonical line return immutable lease");++rgb_line_responses;
        for(unsigned i=0;i<16;i++)need(uint8_t(d.rgb_line_rsp_data[i/4]>>((i%4)*8))==candidate_memory[rgb_owner->bank][d.rgb_line_rsp_addr+i],"physical display line differs from immutable accepted-bank mirror");
        physical_events<<"{\"type\":\"line_rsp\",\"id\":"<<quote(rgb_owner->id)<<",\"cycle\":"<<cycle<<",\"address\":"<<d.rgb_line_rsp_addr<<",\"epoch\":"<<d.rgb_line_rsp_epoch<<",\"token\":"<<d.rgb_line_rsp_token<<",\"data\":"<<quote(hexwide(d.rgb_line_rsp_data))<<"}\n";}
      if(d.rgb_direct_consume)need(rgb_checking&&rgb_owner&&d.rgb_direct_epoch==rgb_owner->epoch&&d.rgb_direct_data==candidate_memory[rgb_owner->bank][d.rgb_direct_addr],"physical direct byte changed source during decode overlap");
      const RgbPixel now{d.rgb_out_addr,d.rgb_out_epoch,d.rgb_out_word};
      if(held_rgb)need(d.rgb_out_valid&&now==*held_rgb,"RGB pixel changed under backpressure");
      held_rgb=d.rgb_out_valid&&!d.rgb_out_ready?std::optional<RgbPixel>(now):std::nullopt;
      if(d.rgb_out_valid&&d.rgb_out_ready){
        need(rgb_checking&&rgb_owner&&rgb_pixels<345600&&d.rgb_out_addr==rgb_pixels&&d.rgb_out_epoch==rgb_owner->epoch,"overlapped RGB pixel lease/order");
        const auto& golden=rgb_goldens.at(rgb_owner->id);const unsigned expected=golden[2*rgb_pixels]|unsigned(golden[2*rgb_pixels+1])<<8;
        need(d.rgb_out_word==expected,"physical overlapped RGB pixel differs from original golden at "+std::to_string(rgb_pixels));
        if(!rgb_pixels)rgb_first=cycle;
        if(rgb_pixels%720==0)rgb_row_first=cycle;
        rgb_last=cycle;
        for(unsigned j=0;j<2;j++){const auto b=uint8_t(d.rgb_out_word>>(8*j));rgb_actual.push_back(b);rgb_row_hash=hash_byte(rgb_row_hash,b);}++rgb_pixels;
        if(rgb_pixels%720==0){physical_events<<"{\"type\":\"pixel_row\",\"id\":"<<quote(rgb_owner->id)<<",\"row\":"<<rgb_pixels/720-1<<",\"pixels\":720,\"epoch\":"<<rgb_owner->epoch<<",\"first_cycle\":"<<rgb_row_first<<",\"last_cycle\":"<<cycle<<",\"hash_fnv64\":"<<rgb_row_hash<<"}\n";rgb_row_hash=1469598103934665603ULL;}
      }
      overlap_observe();
    }
    void start_rgb(){
      need(!rgb_owner&&commit_cycle&&d.rgb_start_ready&&!candidate_pending&&!d.fabric_wr_pending&&!d.fabric_scratch_busy&&!d.fabric_scratch_pending,"RGB began before its validated candidate/scratch closure");
      need(d.v_accepted_generation<=0xffffffffU,"RGB explicit legacy generation width");
      rgb_owner=RgbDescriptor{active->id,d.v_accepted_fid,frame_epoch,d.v_accepted_generation,unsigned(d.v_reference_bank),begin_cycle,commit_cycle,last_input};
      rgb_pixels=rgb_first=rgb_last=rgb_physical_requests=rgb_physical_responses=rgb_lines=rgb_line_responses=0;rgb_actual.clear();rgb_checking=true;rgb_row_hash=1469598103934665603ULL;held_rgb.reset();rgb_terminal_seen=false;rgb_terminal_cycle=0;
      d.rgb_start_epoch=rgb_owner->epoch;d.rgb_start_generation=uint32_t(rgb_owner->generation);d.rgb_start_bank=rgb_owner->bank;d.rgb_start=1;rgb_start_cycle=cycle;if(rgb_owner->fid==0)key_rgb_start=cycle;tick();d.rgb_start=0;
      need(d.rgb_busy&&d.display_active&&!d.rgb_error&&!d.display_start_rejected,"RGB start accepted by real display lease");
      d.rgb_start_bank=3;d.rgb_start_epoch=~rgb_owner->epoch;d.rgb_start_generation=~uint32_t(rgb_owner->generation);
    }
    void rgb_after_edge(){
      if(!rgb_owner)return;
      if(d.rgb_done){need(!d.rgb_error&&!d.rgb_busy,"RGB terminal must be successful and idle");if(!rgb_terminal_seen){rgb_terminal_seen=true;rgb_terminal_cycle=cycle;}}
      need(!d.rgb_error&&!d.display_terminal_error&&!d.display_alias_fault,"overlapped display/lease error");
      if(!rgb_terminal_seen||d.display_active)return;
      need(!d.rgb_busy&&!d.rgb_draining&&!d.rgb_reader_busy&&!d.rgb_reader_pending,"display lease released with live consumer work");
      need(rgb_pixels==345600&&rgb_actual==rgb_goldens.at(rgb_owner->id),"full actual overlapped physical RGB");
      need(rgb_lines==rgb_line_responses&&rgb_lines==32400&&rgb_physical_requests==rgb_physical_responses&&rgb_physical_requests==32400,"physical display request/response closure");
      need(d.rgb_count_reads==32400&&d.rgb_count_responses==32400&&d.rgb_count_direct_consumes==486000&&d.rgb_count_canonical_consumed==518400&&d.rgb_count_pixels==345600,"burst RGB internal conservation");
      const auto r=*rgb_owner;const std::string file=r.id+".rgb565.bin";std::ofstream output(output_directory+"/"+file,std::ios::binary);output.write(reinterpret_cast<const char*>(rgb_actual.data()),std::streamsize(rgb_actual.size()));need(bool(output),"RGB output save");output.close();
      physical_events<<"{\"type\":\"rgb_frame\",\"id\":"<<quote(r.id)<<",\"fid\":"<<r.fid<<",\"epoch\":"<<r.epoch<<",\"generation\":"<<r.generation<<",\"bank\":"<<r.bank<<",\"native_start_cycle\":"<<r.begin<<",\"commit_cycle\":"<<r.commit<<",\"packet_complete_cycle\":"<<r.input_complete<<",\"start_cycle\":"<<rgb_start_cycle<<",\"first_pixel_cycle\":"<<rgb_first<<",\"last_pixel_cycle\":"<<rgb_last<<",\"engine_done_cycle\":"<<rgb_terminal_cycle<<",\"closed_cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()<<",\"pixels\":"<<rgb_pixels<<",\"bytes\":"<<rgb_actual.size()<<",\"logical_reads\":"<<rgb_lines<<",\"physical_reads\":"<<rgb_physical_requests<<",\"output\":"<<quote(file)<<"}\n";
      last_rgb_close=cycle;if(r.fid==0)key_rgb_close=cycle;
      rgb_owner.reset();rgb_checking=false;held_rgb.reset();
    }
    void wait_rgb(){for(unsigned n=0;n<16000000&&rgb_owner;++n)tick();need(!rgb_owner&&!d.display_active,"finite overlapped RGB drain");}
    void decode_summaries(){
      need(reference_line_requests==reference_line_responses&&reference_line_requests==4*reference_tile_responses&&reference_tile_responses==observed_ref_acks,"physical reference conservation at actual decode completion");
      physical_events<<"{\"type\":\"reference_frame\",\"id\":"<<quote(active->id)<<",\"tile_requests\":"<<observed_ref_requests<<",\"tile_responses\":"<<reference_tile_responses<<",\"line_requests\":"<<reference_line_requests<<",\"line_responses\":"<<reference_line_responses<<",\"x16_read_words\":"<<reference_line_responses*8<<",\"start_cycle\":"<<begin_cycle<<",\"stage_first_cycle\":"<<actual_stage_first<<",\"stage_last_cycle\":"<<actual_stage_last<<",\"input_complete_cycle\":"<<last_input<<",\"last_canonical_pixel_cycle\":"<<canonical_last<<",\"commit_cycle\":"<<commit_cycle<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()<<"}\n";
      scratch_frame();
    }
    void service_summary(){
      physical_events<<"{\"type\":\"service_counts\",\"writer_grants\":"<<d.fabric_writer_grants<<",\"reader_grants\":"<<d.fabric_reader_grants<<",\"writer_commands\":"<<d.fabric_writer_commands<<",\"reader_commands\":"<<d.fabric_reader_commands<<",\"wr_rows\":"<<d.fabric_wr_rows<<",\"wr_words_accepted\":"<<d.fabric_wr_words_accepted<<",\"wr_words_retired\":"<<d.fabric_wr_words_retired<<",\"rd_requests\":"<<d.fabric_rd_requests<<",\"rd_responses\":"<<d.fabric_rd_responses<<",\"rd_count_beats\":"<<d.fabric_rd_count_beats<<",\"writes\":"<<d.fabric_writes<<",\"readwords\":"<<d.fabric_readwords<<",\"refreshes\":"<<d.fabric_refreshes<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()<<"}\n";
      physical_events<<"{\"type\":\"overlap_summary\",\"guard_mode\":"<<(guard_mode?"true":"false")<<",\"key_rgb_start_cycle\":"<<key_rgb_start<<",\"key_rgb_closed_cycle\":"<<key_rgb_close<<",\"delta_start_cycle\":"<<delta_begin<<",\"delta_commit_cycle\":"<<delta_commit<<",\"last_rgb_closed_cycle\":"<<last_rgb_close<<",\"engine_bank_active_cycles\":"<<overlap_cycles<<",\"contended_offer_cycles\":"<<contended_offer_cycles<<",\"candidate_requests_while_rgb\":"<<rgb_candidate_overlap_requests<<",\"reference_requests_while_rgb\":"<<rgb_reference_overlap_requests<<",\"scratch_requests_while_rgb\":"<<rgb_scratch_overlap_requests<<",\"guard_hold_cycles\":"<<guard_hold_cycles<<",\"guard_release_cycle\":"<<guard_release_cycle<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()<<"}\n";
    }
