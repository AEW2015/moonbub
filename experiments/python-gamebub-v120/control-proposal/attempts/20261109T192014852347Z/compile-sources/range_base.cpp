#include "bytecount_base.cpp"

// These exhaustive contexts are prepared predicate owners, not natural frames.
// All legacy assertion blocks and the complete public pair remain enabled.
static void exhaustive_range(uint64_t& accepts,uint64_t& rejects,uint64_t& edges){
 Vingress_probe d;d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=0;
 d.packet_bytes=174;d.blocks=1;d.epoch=77;d.word16=d.serial_mode=d.in_data=0;
 d.out_ready=1;d.meta_ready=d.band_end_ready=0;
 d.eval();{ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);}d.reset=0;++edges;
 for(uint32_t word=0;word<65536;++word){
  const int value=word<32768?int(word):int(word)-65536;
  const bool valid=value>=-2048&&value<=2048;
  IBOTH(state,6);IBOTH(done,0);IBOTH(error,0);IBOTH(raw_mode,1);IBOTH(raw_valid,1);
  IBOTH(raw_coefficient,uint16_t(word));IBOTH(raw_position,0);IBOTH(context_epoch,77);
  IBOTH(context_blocks,1);IBOTH(context_active,0);IBOTH(size_bytes,174);
  IBOTH(received,0);IBOTH(count_outputs,0);
  d.clk=0;d.eval();
  need(bool(d.out_valid)==valid,"exhaustive original signed16 output predicate");
  need(d.out_coefficient==uint16_t(word)&&d.out_index==0&&d.out_block==0&&d.out_epoch==77,"prepared RAW tuple identity");
  need(!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_pending&&!d.meta_valid,"synthetic RAW context issued traffic");
  {ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);}++edges;
  need(d.error==(valid?0U:5U)&&d.debug_state==(valid?6U:8U)&&!d.done,"exhaustive same-edge RAW rejection reason/state");
  need(d.count_outputs==(valid?1U:0U),"invalid RAW predicate leaked accepted coefficient");
  if(valid)++accepts;else ++rejects;
 }
 need(accepts==4097&&rejects==61439,"complete signed16 range domain");
 need(d.probe_public_pair_checks==edges,"exhaustive public pair skipped edge");
}

struct NaturalRangeCoverage{uint64_t packets=0,valid=0,error5=0,held_edges=0,cancels=0,retries=0,crc_priority=0,header_priority=0;};
static void natural_packet(Run&w,const PacketCase&c,unsigned profile,bool valid,unsigned bad_index,NaturalRangeCoverage&coverage){
 w.clean();w.image=&c.packet;const auto gold=golden(c);const uint32_t epoch=++w.next_epoch;
 w.d.start=1;w.d.packet_bytes=c.packet.size();w.d.blocks=c.blocks;w.d.epoch=epoch;
 w.d.word16=w.d.serial_mode=0;w.d.in_valid=0;w.d.out_ready=w.d.meta_ready=w.d.band_end_ready=0;w.tick();w.d.start=0;
 unsigned at=0,out=0,ends=0,hold=0;bool metadata=false;
 for(unsigned n=0;!w.d.done&&!w.d.error;++n){
  need(n<100000,"natural RAW boundary watchdog");w.noise();
  w.d.in_valid=at<c.packet.size()&&(!profile||w.rng()%4!=0);
  if(w.d.in_valid){w.d.in_data=c.packet[at];w.d.in_last=at+1==c.packet.size();}
  w.d.meta_ready=1;w.d.band_end_ready=!profile||w.rng()%4!=0;
  w.d.out_ready=!profile||w.rng()%4!=0;w.d.clk=0;w.d.eval();
  if(w.d.out_valid&&w.d.out_index==0&&hold<13){w.d.out_ready=0;w.d.eval();++hold;++coverage.held_edges;}
  if(w.d.meta_valid){need(w.d.meta_raw&&w.d.meta_blocks==c.blocks&&w.d.meta_epoch==epoch,"RAW metadata owner");metadata=true;}
  const bool input=w.d.in_valid&&w.d.in_ready,output=w.d.out_valid&&w.d.out_ready,end=w.d.band_end_valid&&w.d.band_end_ready;
  if(output){need(out<gold.size(),"extra natural RAW coefficient");const auto&g=gold[out];need(w.d.out_band==g.band&&w.d.out_block==g.block&&w.d.out_index==g.index&&int16_t(w.d.out_coefficient)==g.value&&w.d.out_epoch==epoch,"natural RAW signed value/order/owner");++out;++w.outputs;}
  if(end){need(w.d.band_end_band==0&&w.d.band_end_epoch==epoch,"RAW final band owner");++ends;}
  w.tick();if(input)++at;
 }
 need(metadata&&at==c.packet.size()&&!w.pending,"natural RAW input/metadata/read drain");
 if(valid){need(w.d.done&&!w.d.error&&out==gold.size()&&ends==1,"natural RAW valid completion");++coverage.valid;}
 else{need(w.d.error==5&&!w.d.done&&out==bad_index&&ends==0&&!w.d.out_valid,"natural RAW first-invalid reason5/no-leak chronology");++coverage.error5;}
 need(w.requests==w.responses+w.canceled_reads,"natural RAW physical synchronous read conservation");++coverage.packets;
}
static void prepared_cancel(Run&w,const PacketCase&c,unsigned profile,unsigned action,NaturalRangeCoverage&coverage){
 auto&d=w.d;
 w.clean();w.image=&c.packet;const uint32_t epoch=++w.next_epoch;
 w.d.start=1;w.d.packet_bytes=c.packet.size();w.d.blocks=c.blocks;w.d.epoch=epoch;
 w.d.word16=w.d.serial_mode=0;w.d.in_valid=0;w.d.out_ready=w.d.meta_ready=w.d.band_end_ready=0;w.tick();w.d.start=0;
 unsigned at=0;bool canceled=false;
 for(unsigned n=0;n<100000;++n){
  w.noise();w.d.in_valid=at<c.packet.size()&&(!profile||w.rng()%4!=0);
  if(w.d.in_valid){w.d.in_data=c.packet[at];w.d.in_last=at+1==c.packet.size();}
  w.d.out_ready=0;w.d.meta_ready=w.d.band_end_ready=1;w.d.clk=0;w.d.eval();
  if(w.d.debug_state==6&&INEW(raw_valid)){
   need(!w.pending&&w.d.count_outputs==0,"natural prepared RAW cancellation acquired unexpected lease/output");
   if(action==0)w.d.abort_packet=1;else if(action==1)w.d.reset=1;
   else{w.d.start=1;w.d.packet_bytes=c.packet.size();w.d.blocks=c.blocks;w.d.epoch=++w.next_epoch;w.d.word16=w.d.serial_mode=0;}
   w.d.eval();need(!w.d.out_valid&&!w.d.stage_read_req&&!w.d.stage_read_rsp&&!w.d.meta_valid&&!w.d.stage_word_valid,"natural RAW cancel/first-fault public fence");
   w.tick();need(!w.d.error&&!w.d.done&&w.d.debug_state==(action==2?1U:0U),"RAW cancel/reset/start priority over range error5");
   w.d.abort_packet=w.d.reset=w.d.start=w.d.in_valid=0;w.tick();need(!w.pending&&!w.d.out_valid&&!w.d.stage_read_rsp,"natural RAW canceled owner leaked");
   ++coverage.cancels;canceled=true;break;
  }
  need(!w.d.error&&!w.d.done,"natural prepared RAW cancel point not reached");const bool input=w.d.in_valid&&w.d.in_ready;w.tick();if(input)++at;
 }
 need(canceled,"natural prepared RAW cancellation watchdog");
}
int inherited_range_main(int argc,char**argv){try{
 need(inherited_bytecount_main(argc,argv)==0,"all immutable ingress/descriptor/bytecount suites");
 uint64_t accepted=0,rejected=0,predicate_edges=0;exhaustive_range(accepted,rejected,predicate_edges);
 std::ifstream stream(argv[2]);need(bool(stream),"range vector open");std::string p,d,s;std::vector<PacketCase> cases;
 for(PacketCase c;stream>>c.id>>c.blocks>>p>>d>>s;){c.packet=bytes(p);c.dense=bytes(d);cases.push_back(c);}
 const auto raw=std::find_if(cases.begin(),cases.end(),[](const PacketCase&c){return c.blocks==1&&c.packet[5]==1;});need(raw!=cases.end()&&raw->packet.size()==174&&raw->dense.size()==128,"complete one-block RAW fixture");
 const std::array<int,9>values{{-32768,-2049,-2048,-1,0,2047,2048,2049,32767}};
 NaturalRangeCoverage coverage;Run w(unsigned(std::stoul(argv[1]))^0x1200120U);
 for(int value:values)for(unsigned index:{0U,63U})for(unsigned profile:{0U,1U}){
  auto c=*raw;c.id+="-v120-range-"+std::to_string(value)+"-"+std::to_string(index);
  const uint16_t word=uint16_t(value);c.packet[42+2*index]=uint8_t(word);c.packet[43+2*index]=uint8_t(word>>8);
  c.dense[2*index]=uint8_t(word);c.dense[2*index+1]=uint8_t(word>>8);crc(c.packet);
  natural_packet(w,c,profile,value>=-2048&&value<=2048,index,coverage);
  need(w.run(*raw,0,profile,-1,-1,0,0,false),"range reason5/complete nonreset retry");++coverage.retries;
 }
 for(int value:values)for(unsigned action=0;action<3;++action){
  auto c=*raw;const uint16_t word=uint16_t(value);c.packet[42]=c.dense[0]=uint8_t(word);c.packet[43]=c.dense[1]=uint8_t(word>>8);crc(c.packet);
  prepared_cancel(w,c,1,action,coverage);need(w.run(*raw,0,1,-1,-1,0,0,false),"natural canceled RAW nonreset retry");++coverage.retries;
 }
 for(int value:{-2049,2049}){
  auto c=*raw;const uint16_t word=uint16_t(value);c.packet[42]=c.dense[0]=uint8_t(word);c.packet[43]=c.dense[1]=uint8_t(word>>8);crc(c.packet);c.packet.back()^=1;
  need(w.run(c,0,1,-1,-1,0,3),"CRC first fault before bad RAW value");++coverage.crc_priority;need(w.run(*raw,0,1,-1,-1,0,0,false),"CRC priority retry");++coverage.retries;
  c=*raw;c.packet[42]=c.dense[0]=uint8_t(word);c.packet[43]=c.dense[1]=uint8_t(word>>8);c.packet[6]=0;crc(c.packet);
  need(w.run(c,0,1,-1,-1,0,4),"header first fault before bad RAW value");++coverage.header_priority;need(w.run(*raw,0,1,-1,-1,0,0,false),"header priority retry");++coverage.retries;
 }
 need(coverage.packets==36&&coverage.valid==20&&coverage.error5==16&&coverage.cancels==27&&coverage.retries==67&&coverage.crc_priority==2&&coverage.header_priority==2&&coverage.held_edges==364,"complete V120 natural range coverage");
 need(w.requests==w.responses+w.canceled_reads&&w.d.probe_public_pair_checks==w.edges,"V120 natural read/public-edge conservation");
 std::cout<<"{\"type\":\"v120_raw_range_verdict\",\"status\":\"TEST_PASS\",\"prepared_predicate_contexts\":65536,\"predicate_accepts\":"<<accepted<<",\"predicate_rejects\":"<<rejected<<",\"predicate_edges\":"<<predicate_edges<<",\"natural_boundary_packets\":"<<coverage.packets<<",\"natural_valid\":"<<coverage.valid<<",\"natural_error5\":"<<coverage.error5<<",\"natural_prepared_cancels\":"<<coverage.cancels<<",\"held_output_edges\":"<<coverage.held_edges<<",\"natural_retries\":"<<coverage.retries<<",\"crc_priority\":"<<coverage.crc_priority<<",\"header_priority\":"<<coverage.header_priority<<",\"natural_edges\":"<<w.edges<<",\"requests\":"<<w.requests<<",\"responses\":"<<w.responses<<",\"canceled_read_owners\":"<<w.canceled_reads<<",\"public_cycle_delta\":0,\"pair_skipped_edges\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V120_RAW_RANGE_FAIL "<<e.what()<<'\n';return 1;}}
