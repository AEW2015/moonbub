    std::ofstream physical_events;
    std::map<std::string,Bytes> rgb_goldens;
    std::string output_directory;
    Bytes rgb_actual;
    bool rgb_checking=false;
    uint64_t rgb_pixels=0,rgb_first=0,rgb_last=0,rgb_start_cycle=0,rgb_row_first=0,rgb_row_hash=1469598103934665603ULL;
    uint64_t rgb_physical_requests=0,rgb_physical_responses=0,rgb_lines=0,rgb_line_responses=0;
    struct RgbPixel {uint32_t address,epoch,word;bool operator==(const RgbPixel&)const=default;};
    std::optional<RgbPixel> held_rgb;
    void advance(uint64_t target){
      unsigned events=0;
      while(d.eventsPending()&&d.nextTimeSlot()<=target){need(events++<1000,"timed event loop watchdog");const auto next=d.nextTimeSlot();need(next>=Verilated::time(),"time reversed");Verilated::timeInc(next-Verilated::time());d.eval();}
      if(target>Verilated::time()){Verilated::timeInc(target-Verilated::time());d.eval();}
    }
    void configure_rgb(const std::string& goldens_path,const std::string& events_path,const std::string& directory){
      physical_events.open(events_path);need(bool(physical_events),"physical event artifact");output_directory=directory;
      std::ifstream input(goldens_path);need(bool(input),"native RGB goldens");std::string line;
      while(std::getline(input,line)){const auto split=line.find('\t');need(split!=std::string::npos,"RGB golden row");rgb_goldens.emplace(line.substr(0,split),unhex(line.substr(split+1)));}
      need(rgb_goldens.at("actual_001").size()==691200&&rgb_goldens.at("actual_006").size()==691200,"RGB oracle extents");
    }
    static std::string hexwide(const VlWide<4>& words){static const char hx[]="0123456789abcdef";std::string out;for(unsigned i=0;i<16;i++){const auto b=uint8_t(words[i/4]>>((i%4)*8));out+=hx[b>>4];out+=hx[b&15];}return out;}
    uint64_t actual_stage_first=0,actual_stage_last=0;
    unsigned reference_source_bank=3;
    uint64_t reference_line_requests=0,reference_line_responses=0,reference_tile_responses=0;
    static std::string hex512(const VlWide<16>& words){static const char hx[]="0123456789abcdef";std::string out;for(unsigned i=0;i<64;i++){const auto b=uint8_t(words[i/4]>>((i%4)*8));out+=hx[b>>4];out+=hx[b&15];}return out;}
    void physical_reference_request(const ReferenceRequest& r){
      need(d.v_reference_bank_valid&&d.v_accepted_fid==r.fid&&d.v_accepted_generation==r.generation,"physical reference accepted source lease");
      reference_source_bank=d.v_reference_bank;
      need(reference_source_bank<3&&reference_source_bank!=d.v_write_bank,"physical reference bank overlaps candidate");
      physical_events<<"{\"type\":\"reference_req\",\"id\":"<<quote(active->id)<<",\"epoch\":"<<r.epoch<<",\"fid\":"<<r.fid<<",\"generation\":"<<r.generation<<",\"plane\":"<<r.plane<<",\"tile\":"<<r.tile<<",\"source_bank\":"<<reference_source_bank<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
    }
    void physical_reference_response(){
      const auto &r=reference_pending->req;
      need(!d.ref_rsp_error&&d.ref_rsp_epoch==r.epoch&&d.ref_rsp_fid==r.fid&&d.ref_rsp_generation==r.generation&&d.ref_rsp_plane==r.plane&&d.ref_rsp_tile==r.tile,"physical reference response identity");
      need(d.fabric_ref_source_bank==reference_source_bank&&d.v_reference_bank_valid&&d.v_reference_bank==reference_source_bank,"physical reference source snapshot");
      for(unsigned n=0;n<64;++n){const auto address=pixel_address(r.plane,r.tile,n);const auto actual=uint8_t(d.ref_rsp_pixels[n/4]>>((n%4)*8));need(actual==candidate_memory[reference_source_bank][address]&&actual==canonical_golden().reference[address],"physical reference response differs from accepted mirror/golden");}
      ++reference_tile_responses;
      physical_events<<"{\"type\":\"reference_rsp\",\"id\":"<<quote(active->id)<<",\"epoch\":"<<r.epoch<<",\"fid\":"<<r.fid<<",\"generation\":"<<r.generation<<",\"plane\":"<<r.plane<<",\"tile\":"<<r.tile<<",\"source_bank\":"<<reference_source_bank<<",\"error\":"<<unsigned(d.ref_rsp_error)<<",\"data\":"<<quote(hex512(d.ref_rsp_pixels))<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
    }
    void reference_lines_observe(){
      if(d.stage_write){if(!actual_stage_first)actual_stage_first=cycle+1;actual_stage_last=cycle+1;}
      if(d.fabric_ref_line_req_valid&&d.fabric_ref_line_req_ready){
        need(reference_pending.has_value()&&d.fabric_ref_line_req_bank==reference_source_bank,"physical reference line source");++reference_line_requests;
        physical_events<<"{\"type\":\"reference_line_req\",\"epoch\":"<<d.fabric_ref_line_req_epoch<<",\"generation\":"<<d.fabric_ref_line_req_generation<<",\"bank\":"<<unsigned(d.fabric_ref_line_req_bank)<<",\"address\":"<<d.fabric_ref_line_req_addr<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
      }
      if(d.fabric_ref_line_rsp_valid&&d.fabric_ref_line_rsp_ready){
        need(reference_pending.has_value()&&!d.fabric_ref_line_rsp_error&&d.fabric_ref_line_rsp_bank==reference_source_bank,"physical reference line response source");++reference_line_responses;
        const auto &r=reference_pending->req;const unsigned physical_base=(r.plane==0?0:r.plane==1?345600:432000)+r.tile*64;
        need(d.fabric_ref_line_rsp_addr>=physical_base&&d.fabric_ref_line_rsp_addr<physical_base+64&&d.fabric_ref_line_rsp_addr%16==0,"physical reference tile-major line address");
        for(unsigned n=0;n<16;++n)need(uint8_t(d.fabric_ref_line_rsp_data[n/4]>>((n%4)*8))==candidate_memory[reference_source_bank][pixel_address(r.plane,r.tile,d.fabric_ref_line_rsp_addr-physical_base+n)],"physical reference line differs from accepted mirror");
        physical_events<<"{\"type\":\"reference_line_rsp\",\"epoch\":"<<d.fabric_ref_line_rsp_epoch<<",\"generation\":"<<d.fabric_ref_line_rsp_generation<<",\"bank\":"<<unsigned(d.fabric_ref_line_rsp_bank)<<",\"address\":"<<d.fabric_ref_line_rsp_addr<<",\"error\":"<<unsigned(d.fabric_ref_line_rsp_error)<<",\"data\":"<<quote(hexwide(d.fabric_ref_line_rsp_data))<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
      }
    }
    void native_roles(const std::string& type,uint64_t event_time,uint64_t event_cycle){
      physical_events<<"{\"type\":"<<quote(type)<<",\"id\":"<<quote(active->id)<<",\"fid\":"<<be32(vf->packet,8)<<",\"epoch\":"<<frame_epoch<<",\"generation\":"<<be64(vf->packet,16)<<",\"bank\":"<<unsigned(d.v_write_bank)<<",\"accepted_ref_valid\":"<<unsigned(d.v_reference_bank_valid)<<",\"accepted_ref_bank\":"<<unsigned(d.v_reference_bank)<<",\"accepted_fid\":"<<d.v_accepted_fid<<",\"accepted_generation\":"<<d.v_accepted_generation<<",\"front_valid\":"<<unsigned(d.v_front_valid)<<",\"front_bank\":"<<unsigned(d.v_front_bank)<<",\"front_fid\":"<<d.v_front_fid<<",\"pending_valid\":"<<unsigned(d.v_pending_valid)<<",\"pending_bank\":"<<unsigned(d.v_pending_bank)<<",\"pending_fid\":"<<d.v_pending_fid<<",\"bank_active\":"<<unsigned(d.v_bank_active)<<",\"v_commit\":"<<unsigned(d.v_frame_committed)<<",\"v_presented\":"<<unsigned(d.v_frame_presented)<<",\"vblank\":"<<unsigned(d.present_vblank)<<",\"scanout_drained\":"<<unsigned(d.present_drained)<<",\"cycle\":"<<event_cycle<<",\"time_ps\":"<<event_time<<"}\n";
    }
    void rgb_observe(){
      need(cycle<80000000,"finite shared live timed watchdog");
      if(d.rgb_start&&d.rgb_start_ready)physical_events<<"{\"type\":\"rgb_start\",\"id\":"<<quote(active->id)<<",\"fid\":"<<d.v_accepted_fid<<",\"epoch\":"<<d.rgb_start_epoch<<",\"generation\":"<<d.rgb_start_generation<<",\"bank\":"<<unsigned(d.rgb_start_bank)<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
      if(d.rgb_mem_req_valid&&d.rgb_mem_req_ready){need(rgb_checking&&commit_cycle&&cycle>=commit_cycle,"physical read before validated live commit");++rgb_physical_requests;}
      if(d.rgb_mem_rsp_valid&&d.rgb_mem_rsp_ready){need(rgb_checking&&!d.rgb_mem_rsp_error,"physical read response outside live frame");++rgb_physical_responses;}
      if(d.rgb_line_req_valid&&d.rgb_line_req_ready){need(rgb_checking&&d.rgb_line_req_epoch==frame_epoch,"RGB canonical line request lease");++rgb_lines;
        physical_events<<"{\"type\":\"line_req\",\"cycle\":"<<cycle<<",\"address\":"<<d.rgb_line_req_addr<<",\"epoch\":"<<d.rgb_line_req_epoch<<",\"token\":"<<d.rgb_line_req_token<<"}\n";}
      if(d.rgb_line_rsp_valid&&d.rgb_line_rsp_ready){need(rgb_checking&&!d.rgb_line_rsp_error&&d.rgb_line_rsp_epoch==frame_epoch,"RGB canonical line return lease");++rgb_line_responses;
        for(unsigned i=0;i<16;i++)need(uint8_t(d.rgb_line_rsp_data[i/4]>>((i%4)*8))==candidate_memory[d.v_reference_bank][d.rgb_line_rsp_addr+i],"physical line differs from ACK-backed accepted mirror");
        physical_events<<"{\"type\":\"line_rsp\",\"cycle\":"<<cycle<<",\"address\":"<<d.rgb_line_rsp_addr<<",\"epoch\":"<<d.rgb_line_rsp_epoch<<",\"token\":"<<d.rgb_line_rsp_token<<",\"data\":"<<quote(hexwide(d.rgb_line_rsp_data))<<"}\n";}
      if(d.rgb_direct_consume){need(rgb_checking&&d.rgb_direct_epoch==frame_epoch&&d.rgb_direct_data==candidate_memory[d.v_reference_bank][d.rgb_direct_addr],"physical direct byte mismatch");}
      const RgbPixel now{d.rgb_out_addr,d.rgb_out_epoch,d.rgb_out_word};
      if(held_rgb)need(d.rgb_out_valid&&now==*held_rgb,"RGB pixel changed under backpressure");
      held_rgb=d.rgb_out_valid&&!d.rgb_out_ready?std::optional<RgbPixel>(now):std::nullopt;
      if(d.rgb_out_valid&&d.rgb_out_ready){
        need(rgb_checking&&rgb_pixels<345600&&d.rgb_out_addr==rgb_pixels&&d.rgb_out_epoch==frame_epoch,"live RGB pixel lease/order");
        const auto& golden=rgb_goldens.at(active->id);const unsigned expected=golden[2*rgb_pixels]|unsigned(golden[2*rgb_pixels+1])<<8;
        need(d.rgb_out_word==expected,"physical live RGB pixel differs from native golden at "+std::to_string(rgb_pixels));
        if(!rgb_pixels){rgb_first=cycle;}
        if(rgb_pixels%720==0){rgb_row_first=cycle;}
        rgb_last=cycle;
        for(unsigned j=0;j<2;j++){const auto b=uint8_t(d.rgb_out_word>>(8*j));rgb_actual.push_back(b);rgb_row_hash=hash_byte(rgb_row_hash,b);}++rgb_pixels;
        if(rgb_pixels%720==0){physical_events<<"{\"type\":\"pixel_row\",\"id\":"<<quote(active->id)<<",\"row\":"<<rgb_pixels/720-1<<",\"pixels\":720,\"epoch\":"<<frame_epoch<<",\"first_cycle\":"<<rgb_row_first<<",\"last_cycle\":"<<cycle<<",\"hash_fnv64\":"<<rgb_row_hash<<"}\n";rgb_row_hash=1469598103934665603ULL;}
      }
    }
    void full_rgb(){
      need(commit_cycle&&d.rgb_start_ready&&!candidate_pending&&!d.fabric_wr_pending&&!d.fabric_rd_pending&&!d.fabric_ref_busy&&!d.fabric_ref_pending&&d.fabric_mux_owner==0,"RGB began before actual candidate closure");
      need(d.v_accepted_generation<=0xffffffffU,"RGB generation width");
      rgb_pixels=rgb_first=rgb_last=rgb_physical_requests=rgb_physical_responses=rgb_lines=rgb_line_responses=0;rgb_actual.clear();rgb_checking=true;rgb_row_hash=1469598103934665603ULL;
      d.rgb_start_epoch=frame_epoch;d.rgb_start_generation=uint32_t(d.v_accepted_generation);d.rgb_start_bank=d.v_reference_bank;d.rgb_start=1;rgb_start_cycle=cycle;tick();d.rgb_start=0;
      need(d.rgb_busy&&!d.rgb_error,"RGB start accepted");
      // Snapshot must remain bound to accepted bank despite changed external hints.
      d.rgb_start_bank=3;d.rgb_start_epoch=~frame_epoch;d.rgb_start_generation=~uint32_t(d.v_accepted_generation);
      for(unsigned n=0;n<6500000&&!d.rgb_done&&!d.rgb_error;++n)tick();
      need(d.rgb_done&&!d.rgb_busy&&!d.rgb_error&&d.rgb_start_ready&&!d.fabric_rd_pending&&!d.fabric_wr_pending,"live shared RGB closure");
      need(rgb_pixels==345600&&rgb_actual==rgb_goldens.at(active->id),"full actual live physical RGB");
      need(rgb_lines==rgb_line_responses&&rgb_lines==32400&&rgb_physical_requests==rgb_physical_responses&&rgb_physical_requests==32400,"real physical reader closure");
      need(d.rgb_count_reads==32400&&d.rgb_count_responses==32400&&d.rgb_count_direct_consumes==486000&&d.rgb_count_canonical_consumed==518400&&d.rgb_count_pixels==345600,"burst RGB internal conservation");
      const std::string file=active->id+".rgb565.bin";std::ofstream output(output_directory+"/"+file,std::ios::binary);output.write(reinterpret_cast<const char*>(rgb_actual.data()),std::streamsize(rgb_actual.size()));need(bool(output),"RGB output save");output.close();
      physical_events<<"{\"type\":\"rgb_frame\",\"id\":"<<quote(active->id)<<",\"fid\":"<<d.v_accepted_fid<<",\"epoch\":"<<frame_epoch<<",\"generation\":"<<d.v_accepted_generation<<",\"bank\":"<<unsigned(d.v_reference_bank)<<",\"native_start_cycle\":"<<begin_cycle<<",\"commit_cycle\":"<<commit_cycle<<",\"start_cycle\":"<<rgb_start_cycle<<",\"first_pixel_cycle\":"<<rgb_first<<",\"last_pixel_cycle\":"<<rgb_last<<",\"closed_cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()<<",\"pixels\":"<<rgb_pixels<<",\"bytes\":"<<rgb_actual.size()<<",\"logical_reads\":"<<rgb_lines<<",\"physical_reads\":"<<rgb_physical_requests<<",\"output\":"<<quote(file)<<"}\n";
      need(reference_line_requests==reference_line_responses&&reference_line_requests==4*reference_tile_responses,"physical reference line/tile conservation");
      need(reference_tile_responses==observed_ref_acks,"physical reference tile response conservation");
      physical_events<<"{\"type\":\"reference_frame\",\"id\":"<<quote(active->id)<<",\"tile_requests\":"<<observed_ref_requests<<",\"tile_responses\":"<<reference_tile_responses<<",\"line_requests\":"<<reference_line_requests<<",\"line_responses\":"<<reference_line_responses<<",\"x16_read_words\":"<<reference_line_responses*8<<",\"start_cycle\":"<<begin_cycle<<",\"stage_first_cycle\":"<<actual_stage_first<<",\"stage_last_cycle\":"<<actual_stage_last<<",\"input_complete_cycle\":"<<last_input<<",\"last_canonical_pixel_cycle\":"<<canonical_last<<",\"commit_cycle\":"<<commit_cycle<<",\"rgb_closed_cycle\":"<<cycle<<"}\n";
      physical_events<<"{\"type\":\"service_counts\",\"id\":"<<quote(active->id)<<",\"writer_grants\":"<<d.fabric_writer_grants<<",\"reader_grants\":"<<d.fabric_reader_grants<<",\"writer_commands\":"<<d.fabric_writer_commands<<",\"reader_commands\":"<<d.fabric_reader_commands<<",\"wr_rows\":"<<d.fabric_wr_rows<<",\"wr_words_accepted\":"<<d.fabric_wr_words_accepted<<",\"wr_words_retired\":"<<d.fabric_wr_words_retired<<",\"rd_requests\":"<<d.fabric_rd_requests<<",\"rd_responses\":"<<d.fabric_rd_responses<<",\"rd_count_beats\":"<<d.fabric_rd_count_beats<<",\"reference_tiles\":"<<reference_tile_responses<<",\"reference_lines\":"<<reference_line_responses<<",\"writes\":"<<d.fabric_writes<<",\"readwords\":"<<d.fabric_readwords<<",\"refreshes\":"<<d.fabric_refreshes<<",\"cycle\":"<<cycle<<"}\n";
      rgb_checking=false;
    }
