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
    void rgb_observe(){
      need(cycle<80000000,"finite shared live timed watchdog");
      if(d.start&&d.start_ready&&physical_events)physical_events<<"{\"type\":\"native_start\",\"id\":"<<quote(active->id)<<",\"fid\":"<<d.validation_start_fid<<",\"epoch\":"<<frame_epoch<<",\"generation\":"<<d.validation_start_generation<<",\"bank\":"<<unsigned(d.v_write_bank)<<",\"cycle\":"<<cycle<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
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
        if(!rgb_pixels)rgb_first=cycle;if(rgb_pixels%720==0)rgb_row_first=cycle;rgb_last=cycle;
        for(unsigned j=0;j<2;j++){const auto b=uint8_t(d.rgb_out_word>>(8*j));rgb_actual.push_back(b);rgb_row_hash=hash_byte(rgb_row_hash,b);}++rgb_pixels;
        if(rgb_pixels%720==0){physical_events<<"{\"type\":\"pixel_row\",\"id\":"<<quote(active->id)<<",\"row\":"<<rgb_pixels/720-1<<",\"pixels\":720,\"epoch\":"<<frame_epoch<<",\"first_cycle\":"<<rgb_row_first<<",\"last_cycle\":"<<cycle<<",\"hash_fnv64\":"<<rgb_row_hash<<"}\n";rgb_row_hash=1469598103934665603ULL;}
      }
    }
    void full_rgb(){
      need(commit_cycle&&d.rgb_start_ready&&!candidate_pending&&!d.fabric_wr_pending&&!d.fabric_rd_pending,"RGB began before actual candidate closure");
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
      rgb_checking=false;
    }
