    uint64_t scratch_read_requests=0,scratch_write_requests=0,scratch_read_responses=0,scratch_write_responses=0;
    uint64_t scratch_first=0,scratch_last=0,scratch_wait_cycles=0,scratch_pending_cycles=0,scratch_max_address=0;
    std::optional<std::array<uint32_t,6>> held_scratch_response;
    std::array<uint32_t,6> scratch_response_tuple()const{return {d.mem_rsp_epoch,unsigned(d.mem_rsp_error),d.mem_rsp_data[0],d.mem_rsp_data[1],d.mem_rsp_data[2],d.mem_rsp_data[3]};}
    static std::string hexrequest(const Request& request){static const char hx[]="0123456789abcdef";std::string out;for(unsigned i=0;i<16;i++){const auto b=uint8_t(request.data[i/4]>>((i%4)*8));out+=hx[b>>4];out+=hx[b&15];}return out;}
    void physical_scratch_request(const Request& q){
      need(profile==0&&q.addr%16==0&&q.addr<=262128&&q.epoch!=0,"physical scratch request contract");
      if(!scratch_first)scratch_first=cycle+1;
      scratch_max_address=std::max(scratch_max_address,uint64_t(q.addr));
      if(q.write)++scratch_write_requests;else ++scratch_read_requests;
      physical_events<<"{\"type\":\"scratch_live_req\",\"id\":"<<quote(active->id)<<",\"index\":"<<requests<<",\"write\":"<<q.write<<",\"epoch\":"<<q.epoch<<",\"address\":"<<q.addr<<",\"data\":"<<quote(hexrequest(q))<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
    }
    void physical_scratch_response(const Request& q){
      need(d.mem_rsp_epoch==q.epoch&&!d.mem_rsp_error,"physical scratch response identity/error");
      if(q.write)++scratch_write_responses;else{
        ++scratch_read_responses;
        need(line_epoch[q.addr/16]==q.epoch,"scratch read before matching epoch physical write ACK");
        for(unsigned k=0;k<4;++k)for(unsigned j=0;j<4;++j)need(uint8_t(d.mem_rsp_data[k]>>(8*j))==ram[q.addr+4*k+j],"physical scratch read differs from ACK-only mirror");
      }
      scratch_last=cycle+1;
      physical_events<<"{\"type\":\"scratch_live_rsp\",\"id\":"<<quote(active->id)<<",\"index\":"<<acks<<",\"write\":"<<q.write<<",\"epoch\":"<<d.mem_rsp_epoch<<",\"address\":"<<q.addr<<",\"error\":"<<unsigned(d.mem_rsp_error)<<",\"data\":"<<quote(hexwide(d.mem_rsp_data))<<",\"cycle\":"<<cycle+1<<",\"time_ps\":"<<Verilated::time()+5000<<"}\n";
    }
    void scratch_observe(){
      if(held_scratch_response)need(d.mem_rsp_valid&&scratch_response_tuple()==*held_scratch_response,"held scratch response changed");
      held_scratch_response=d.mem_rsp_valid&&!d.mem_rsp_ready?std::optional<std::array<uint32_t,6>>(scratch_response_tuple()):std::nullopt;
      if(d.mem_req_valid&&!d.mem_req_ready)++scratch_wait_cycles;
      if(pending)++scratch_pending_cycles;
    }
    void scratch_frame(){
      need(!pending&&!d.fabric_scratch_pending&&!d.fabric_scratch_busy,"scratch terminal drain");
      need(scratch_read_requests==scratch_read_responses&&scratch_write_requests==scratch_write_responses,"scratch request/response conservation");
      need(requests==scratch_read_requests+scratch_write_requests&&acks==scratch_read_responses+scratch_write_responses,"scratch endpoint observer conservation");
      physical_events<<"{\"type\":\"scratch_frame\",\"id\":"<<quote(active->id)<<",\"requests\":"<<requests<<",\"responses\":"<<acks<<",\"write_requests\":"<<scratch_write_requests<<",\"write_responses\":"<<scratch_write_responses<<",\"read_requests\":"<<scratch_read_requests<<",\"read_responses\":"<<scratch_read_responses<<",\"write_words\":"<<scratch_write_responses*8<<",\"read_words\":"<<scratch_read_responses*8<<",\"first_cycle\":"<<scratch_first<<",\"last_cycle\":"<<scratch_last<<",\"wait_cycles\":"<<scratch_wait_cycles<<",\"pending_cycles\":"<<scratch_pending_cycles<<",\"max_address\":"<<scratch_max_address<<",\"physical_requests\":"<<d.fabric_scratch_requests<<",\"physical_responses\":"<<d.fabric_scratch_responses<<",\"physical_commands\":"<<d.fabric_scratch_commands<<",\"memory_owner\":"<<unsigned(d.fabric_memory_owner)<<",\"cycle\":"<<cycle<<"}\n";
    }
