#include "range_base.cpp"

static std::string control_bits(uint32_t value,unsigned width){
 std::string out;
 for(unsigned bit=width;bit>0;--bit)out.push_back(((value>>(bit-1U))&1U)?'1':'0');
 return out;
}
static PacketCase control_error_packet(unsigned kind){
 PacketCase c;c.id="v120-natural-context-error-"+std::to_string(kind);c.blocks=1;c.dense.assign(128,0);
 std::array<std::string,4> streams{};std::array<uint32_t,4> counts{{1,0,0,0}};
 if(kind==0)streams[0]=std::string(15,'0')+control_bits(8191U,14); // DC -4096: error5.
 else if(kind==1)streams[0]="";                               // Required DC missing: error2.
 else if(kind==2){streams[0]="1";streams[1]=std::string(15,'0')+control_bits(5U,24);counts[1]=1;}
 else if(kind==3)streams[0]="10";                             // Final-count trailing bit: error7.
 else throw std::runtime_error("context error case domain");
 std::array<std::vector<uint8_t>,4> descriptors;
 for(unsigned band=0;band<4;++band){
  auto&v=descriptors[band];v.assign(6U+(streams[band].size()+7U)/8U,0);
  v[0]=0;v[1]=band==0?255:0;const uint32_t n=uint32_t(streams[band].size());
  for(unsigned i=0;i<4;++i)v[2+i]=uint8_t(n>>(8U*i));
  for(unsigned i=0;i<n;++i)if(streams[band][i]=='1')v[6+i/8]|=uint8_t(1U<<(7U-(i&7U)));
 }
 c.packet.assign(42,0);c.packet[0]='B';c.packet[1]='R';c.packet[2]='8';c.packet[3]='8';
 c.packet[4]=1;set32(c.packet,6,1);c.packet[10]=1;
 for(unsigned band=0;band<4;++band){set32(c.packet,14+4*band,uint32_t(descriptors[band].size()));if(band)set32(c.packet,26+4*band,counts[band]);c.packet.insert(c.packet.end(),descriptors[band].begin(),descriptors[band].end());}
 c.packet.resize(c.packet.size()+4,0);crc(c.packet);return c;
}
static void control_payload_reject(Run&w,const PacketCase&c,unsigned mode,unsigned profile,
                                   unsigned expected_error,unsigned expected_outputs){
 w.image=&c.packet;const uint32_t epoch=++w.next_epoch;
 w.d.start=1;w.d.packet_bytes=c.packet.size();w.d.blocks=c.blocks;w.d.epoch=epoch;
 w.d.word16=mode&1U;w.d.serial_mode=(mode>>1)&1U;w.d.in_valid=0;
 w.d.out_ready=w.d.meta_ready=w.d.band_end_ready=0;w.tick();w.d.start=0;
 unsigned at=0,out=0,ends=0;bool metadata=false;
 for(unsigned n=0;!w.d.error&&!w.d.done;++n){
  need(n<100000,"natural context-error watchdog");w.noise();
  w.d.in_valid=at<c.packet.size()&&(!profile||w.rng()%4!=0);
  if(w.d.in_valid){w.d.in_data=c.packet[at];w.d.in_last=at+1==c.packet.size();}
  w.d.out_ready=!profile||w.rng()%4!=0;w.d.meta_ready=w.d.band_end_ready=1;
  w.d.clk=0;w.d.eval();
  if(w.d.meta_valid){metadata=true;need(w.d.meta_epoch==epoch&&w.d.meta_blocks==1&&!w.d.meta_raw,"context-error metadata owner");}
  const bool input=w.d.in_valid&&w.d.in_ready,output=w.d.out_valid&&w.d.out_ready;
  if(output){need(out<expected_outputs&&w.d.out_band==0&&w.d.out_block==0&&w.d.out_index==0&&int16_t(w.d.out_coefficient)==0&&w.d.out_epoch==epoch,"context error leaked non-golden prefix");++out;++w.outputs;}
  if(w.d.band_end_valid){need(expected_outputs==1&&ends==0&&w.d.band_end_band==0&&w.d.band_end_epoch==epoch,"context error closed an unexpected band");++ends;}
  w.tick();if(input)++at;
 }
 need(metadata&&at==c.packet.size()&&w.d.error==expected_error&&!w.d.done&&out==expected_outputs&&ends==expected_outputs,
      "natural malformed context first-fault/output chronology");
 w.d.in_valid=0;w.tick();need(!w.pending&&!w.d.out_valid&&!w.d.stage_read_rsp,"context-error read debt did not quiesce");
 need(w.requests==w.responses+w.canceled_reads,"context-error physical read conservation");
}
static uint64_t control_unowned_domain(){
 Vingress_probe d;ExtentsCoverage edges;
 d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=0;
 d.packet_bytes=174;d.blocks=1;d.epoch=77;d.word16=d.serial_mode=d.in_data=0;
 d.out_ready=d.meta_ready=d.band_end_ready=0;extent_edge(d,edges);d.reset=0;
 const std::array<uint32_t,16>values{{0U,1U,2U,20U,21U,22U,49151U,65535U,65536U,
  0x3fffffffU,0x7fffffeaU,0x7fffffffU,0x80000000U,0xfffffff0U,0xfffffffeU,0xffffffffU}};
 const std::array<uint32_t,14>sizes{{0U,1U,3U,4U,45U,46U,47U,48U,174U,49152U,
  0x1fffffffU,0x2000002eU,0x80000000U,0xffffffffU}};
 uint64_t cases=0;
 auto edge=[&](unsigned phase,uint32_t size,uint32_t a,uint32_t b,unsigned action){
  // Complete canceled prestates. No cached register, physical owner, memory
  // response or expected poststate is forced. These are not natural frames.
  IBOTH(state,phase);IBOTH(done,0);IBOTH(error,0);IBOTH(context_active,0);
  IBOTH(size_bytes,size);IBOTH(context_blocks,1);IBOTH(context_epoch,77);IBOTH(received,0);
  IBOTH(raw_position,a);IBOTH(raw_valid,1);IBOTH(active_offset,a);IBOTH(replay_bits,b);
  IBOTH(word_valid,0);IBOTH(replay_nonzero,1);IBOTH(count_outputs,0);
  d.reset=action==0;d.abort_packet=action==1;d.start=action==2;
  d.packet_bytes=174;d.blocks=1;d.epoch=99;d.in_valid=0;d.eval();
  need(!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_write&&!d.stage_word_valid&&!d.out_valid,
       "prepared canceled payload context issued physical/public work");
  const uint32_t expected=phase==6?uint32_t(42U+2U*a):uint32_t(a+(b>>3));
  extent_edge(d,edges);
  need(INEW(prepared_request_addr)==expected&&bool(INEW(prepared_request_in_bounds))==(expected<size&&expected<49152U),
       "independent full32 canceled raw/replay payload equation");
  need(!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_write&&!d.out_valid,
       "prepared canceled payload poststate leaked physical/public work");
  d.reset=d.abort_packet=d.start=0;d.eval();++cases;
 };
 for(uint32_t size:sizes)for(uint32_t position:values)for(unsigned action=0;action<3;++action)
  edge(6,size,position,0,action);
 for(uint32_t size:sizes)for(uint32_t offset:values)for(uint32_t bits:values)for(unsigned action=0;action<3;++action)
  edge(5,size,offset,bits,action);
 need(cases==11424&&edges.edges==11425,"complete canceled-unowned full32 address/bounds matrix");
 return cases;
}
int main(int argc,char**argv){try{
 need(inherited_range_main(argc,argv)==0,"entire inherited ingress/extent/bytecount/range proof");
 const uint64_t unowned_domain_cases=control_unowned_domain();
 std::ifstream stream(argv[2]);need(bool(stream),"control packet vectors open");std::string p,d,s;std::vector<PacketCase> cases;
 for(PacketCase c;stream>>c.id>>c.blocks>>p>>d>>s;){c.packet=bytes(p);c.dense=bytes(d);cases.push_back(c);}
 const auto raw=std::find_if(cases.begin(),cases.end(),[](const PacketCase&c){return c.packet[5]==1;});
 const auto sparse=std::find_if(cases.begin(),cases.end(),[](const PacketCase&c){return c.packet[5]==0;});
 need(raw!=cases.end()&&sparse!=cases.end(),"control raw/sparse vectors");
 Run w(unsigned(std::stoul(argv[1]))^0x120c017U);uint64_t birth=0,first_read=0,retries=0,payload_errors=0;
 for(unsigned kind=0;kind<4;++kind)for(unsigned action=0;action<6;++action){
  const auto&c=kind==3?*raw:*sparse;
  need(!w.run(c,action%4,1,11+int(kind),0,action),"actual initial-call cancellation point not reached");++birth;
  need(w.run(c,action%4,1,-1,-1,0,0,false),"initial-call nonreset retry failed");++retries;
 }
 for(unsigned kind=0;kind<4;++kind)for(unsigned action=0;action<6;++action){
  const auto&c=kind==3?*raw:*sparse;
  need(!w.run(c,action%4,1,int(kind),0,action),"first real request/response cancellation point not reached");++first_read;
  need(w.run(c,action%4,1,-1,-1,0,0,false),"first request/response nonreset retry failed");++retries;
 }
 const std::array<unsigned,4> errors{{5,2,6,7}};
 for(unsigned kind=0;kind<4;++kind)for(unsigned mode=0;mode<4;++mode)for(unsigned profile=0;profile<2;++profile){
  const auto c=control_error_packet(kind);control_payload_reject(w,c,mode,profile,errors[kind],kind==2?1U:0U);++payload_errors;
  need(w.run(*sparse,mode,profile,-1,-1,0,0,false),"context-error nonreset retry failed");++retries;
 }
 need(birth==24&&first_read==24&&retries==80&&payload_errors==32,"complete control directed coverage");
 need(w.requests==w.responses+w.canceled_reads&&w.d.probe_public_pair_checks==w.edges,"control natural physical/public ledger");
 need(writer_coverage.edges>0&&writer_coverage.spec_only>0&&writer_coverage.owned_tuples>0&&
      std::all_of(writer_coverage.initial.begin(),writer_coverage.initial.end(),[](uint64_t n){return n>0;})&&
      writer_coverage.reset_spec>0&&writer_coverage.start_spec>0&&writer_coverage.abort_spec>0&&
      writer_coverage.bad_descriptor_spec>0&&writer_coverage.context_fault_spec>0&&writer_coverage.context_done_spec>0&&
      writer_coverage.held_replay_spec>0&&writer_coverage.cache_captures>0&&writer_coverage.owned_cache_wait_checks>0,
      "complete private writer phase/fault/cancel coverage");
 std::cout<<"{\"type\":\"v120_phase_payload_verdict\",\"status\":\"TEST_PASS\",\"initial_call_cancels\":"<<birth
  <<",\"first_request_response_cancels\":"<<first_read<<",\"natural_context_error_cases\":"<<payload_errors<<",\"nonreset_retries\":"<<retries
  <<",\"writer_edges\":"<<writer_coverage.edges<<",\"old_write_edges\":"<<writer_coverage.old_writes<<",\"phase_write_edges\":"<<writer_coverage.new_writes
  <<",\"unowned_speculation_edges\":"<<writer_coverage.spec_only<<",\"exact_owned_request_tuples\":"<<writer_coverage.owned_tuples
  <<",\"reset_speculation_edges\":"<<writer_coverage.reset_spec<<",\"start_speculation_edges\":"<<writer_coverage.start_spec<<",\"abort_speculation_edges\":"<<writer_coverage.abort_spec
  <<",\"bad_descriptor_speculation_edges\":"<<writer_coverage.bad_descriptor_spec<<",\"context_fault_speculation_edges\":"<<writer_coverage.context_fault_spec
  <<",\"context_done_speculation_edges\":"<<writer_coverage.context_done_spec<<",\"held_replay_speculation_edges\":"<<writer_coverage.held_replay_spec
  <<",\"prepared_unowned_full32_cases\":"<<unowned_domain_cases<<",\"independent_cache_captures\":"<<writer_coverage.cache_captures
  <<",\"owned_cache_wait_checks\":"<<writer_coverage.owned_cache_wait_checks<<",\"unowned_cache_input_edges\":"<<writer_coverage.unowned_cache_inputs
  <<",\"initial_header_calls\":"<<writer_coverage.initial[0]<<",\"initial_descriptor_calls\":"<<writer_coverage.initial[1]
  <<",\"initial_replay_calls\":"<<writer_coverage.initial[2]<<",\"initial_raw_calls\":"<<writer_coverage.initial[3]
  <<",\"requests\":"<<w.requests<<",\"responses\":"<<w.responses<<",\"canceled_read_owners\":"<<w.canceled_reads
  <<",\"candidate_private_comparison_edits\":1,\"changed_private_fields\":2,\"public_cycle_delta\":0,\"pair_skipped_edges\":0}\n";
 return 0;
}catch(const std::exception&e){std::cerr<<"V120_PHASE_PAYLOAD_FAIL "<<e.what()<<'\n';return 1;}}
