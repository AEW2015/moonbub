#include "record_base.cpp"
struct ACCoverage {uint64_t edges=0,cases=0,hits=0,misses=0,forwards=0,kills=0,errors=0,wrong=0,drains=0,compares=0,domain_good=0,domain_bad=0;unsigned offsets=0,bands=0,segments=0,formats=0;};
static void ac_edge(Vscratch_probe&d,ACCoverage&c){
 d.clk=d.reference_clk=0;d.eval();need(!d.mismatch,"AC exact old/current preedge oracle");
 d.clk=d.reference_clk=1;d.eval();need(!d.mismatch,"AC exact old/current postedge oracle");
 d.clk=d.reference_clk=0;d.eval();need(!d.mismatch,"AC exact old/current held oracle");
 need(++c.edges<100000,"AC fixture finite edge watchdog");
}
static std::array<uint32_t,4> line(unsigned offset,unsigned band,unsigned format,unsigned salt,bool alternate=false){
 std::array<uint8_t,16>b{};for(unsigned i=0;i<16;++i)b[i]=uint8_t(salt*17U+i*47U);
 unsigned index=0;const unsigned rank=(band==1?1:band==2?6:21)+unsigned(alternate);for(unsigned i=0;i<64;++i)if(ranks[i]==rank)index=i;
 const int value=(format>=4?int(format-4):format==0?37:format==1?0:format==2?2049:-2048)+int(alternate);
 const uint32_t record=(format==3?uint32_t(1)<<19:0)|(index<<13)|(unsigned(value)&8191U);
 for(unsigned i=0;i<4&&offset+i<16;++i)b[offset+i]=uint8_t(record>>(8*i));
 std::array<uint32_t,4>a{};for(unsigned i=0;i<16;++i)a[i/4]|=uint32_t(b[i])<<(8*(i%4));return a;
}
static uint32_t selected(const std::array<uint32_t,4>&a,unsigned offset){uint32_t w=0;for(unsigned i=0;i<4&&offset+i<16;++i){const unsigned j=offset+i;w|=((a[j/4]>>(8*(j%4)))&255U)<<(8*i);}return w;}
static void cache_line(Vscratch_probe&d,unsigned band,const std::array<uint32_t,4>&a){
 for(unsigned i=0;i<4;++i)OLD(cache_data)[band][i]=NEW(cache_data)[band][i]=a[i];
 for(unsigned i=0;i<16;++i)OLD(cache_positions)[band][i]=NEW(cache_positions)[band][i]=position(selected(a,i));
}
static void ac_init(Vscratch_probe&d,ACCoverage&c){
 d.clk=d.reference_clk=0;d.pair_enable=1;d.reset=1;d.begin_valid=d.coef_valid=d.band_end_valid=d.seal_valid=d.abort_valid=d.mem_req_ready=d.mem_rsp_valid=d.mem_rsp_error=d.dense_ready=0;
 d.abort_epoch=0;d.begin_blocks=1;d.begin_raw=d.begin_serial_clear=d.begin_overlap=d.begin_prefetch=d.begin_tile_overlap=0;
 d.begin_count1=d.begin_count2=d.begin_count3=d.begin_epoch=d.coef_band=d.coef_block=d.coef_index=d.coef_value=d.coef_epoch=d.band_end_band=d.band_end_epoch=d.seal_epoch=d.mem_rsp_epoch=0;
 for(unsigned i=0;i<4;++i){d.mem_rsp_data[i]=0;}ac_edge(d,c);d.reset=0;
}
static void ac_check_payload(Vscratch_probe&d,ACCoverage&c,const std::array<uint32_t,4>&a,unsigned offset){
 d.eval();const uint32_t w=selected(a,offset);need(NEW(ac_selected_word)==w&&NEW(ac_selected_position)==position(w),"independent bytewise selected AC tuple");
 need(d.verify_read_word==w&&d.verify_read_position==position(w),"frozen old cache selected tuple");++c.compares;
}
static void ac_retire(Vscratch_probe&d,ACCoverage&c,const std::array<uint32_t,4>&a,unsigned offset,unsigned band,bool domain=false){
 const uint32_t w=selected(a,offset);const unsigned rank=ranks[(w>>13)&63U];int value=int(w&8191U);if(value&4096)value-=8192;
 const bool rank_ok=band==1?rank>=1&&rank<6:band==2?rank>=6&&rank<21:rank>=21;
 const bool bad=(w>>19)>=1||!rank_ok||value==0||value< -2048||value>2048;
 ac_edge(d,c);need(d.error==(bad?3U:0U)&&d.debug_state==(bad?24U:17U),"independent selected-word geometry/domain retirement");
 if(!bad)need(get(d.verify_heads,(band-1)*32,32)==w&&get(d.verify_head_positions,(band-1)*19,19)==position(w),"independent selected head write");
 if(domain){if(bad)++c.domain_bad;else ++c.domain_good;}
}
static void hit_or_miss(unsigned offset,unsigned band,unsigned format,unsigned action,ACCoverage&c){
 std::cerr<<"AC_FIXTURE hit_or_miss offset="<<offset<<" band="<<band<<" format="<<format<<" action="<<action<<std::endl;
 Vscratch_probe d;ac_init(d,c);setup(d,1,0,0,0);BOTH(state,17);BOTH(active_epoch,9);BOTH(read_band,band);BOTH(head_valid,0);BOTH(sealed,1);
 const unsigned addr=48+16*(band-1)+offset;OLD(starts)[band]=NEW(starts)[band]=addr;OLD(counts)[band]=NEW(counts)[band]=1;
 OLD(cursors)[band-1]=NEW(cursors)[band-1]=0;OLD(head_positions)[band-1]=NEW(head_positions)[band-1]=0;
 const auto original=line(offset,band,format,offset+band+17);const auto response=line(offset,band,format,offset+band+91,true);
 cache_line(d,band,original);OLD(cache_address)[band]=NEW(cache_address)[band]=addr&~15U;
 BOTH(cache_valid,action==1?0:1U<<band);d.begin_valid=d.coef_valid=d.band_end_valid=d.seal_valid=0;
 // Real predecessor edge matures original prepared_ac_line, then AC_FETCH.
 ac_edge(d,c);need(d.debug_state==18,"AC_CHECK did not reach existing AC_FETCH");
 if(action==2){need(selected(original,offset)!=selected(response,offset),"forward fixture must differ from old selected payload");if(offset<=12)need(position(selected(original,offset))!=position(selected(response,offset)),"forward fixture must differ from old selected position");BOTH(sealed,0);BOTH(prefetch_offer,1);BOTH(outstanding,1);BOTH(prefetch_segment,band);BOTH(transfer_address,addr&~15U);d.mem_rsp_valid=1;d.mem_rsp_epoch=9;for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=response[i];}
 if(action==3)d.reset=1;
 if(action==4){d.abort_valid=1;d.abort_epoch=9;}
 if(action==5){d.abort_valid=1;d.abort_epoch=10;}
 if(action==6){BOTH(sealed,0);BOTH(outstanding,1);d.mem_rsp_valid=d.mem_rsp_error=1;d.mem_rsp_epoch=9;}
 ac_edge(d,c);d.reset=d.abort_valid=d.mem_rsp_valid=d.mem_rsp_error=0;
 if(action==3||action==4){need(d.debug_state==0&&!d.busy,"AC fetch kill did not revoke owner");++c.kills;++c.cases;return;}
 need(d.debug_state==19,"AC_FETCH public schedule changed");
 if(action==1){
  ++c.misses;ac_edge(d,c);need(d.debug_state==10,"AC cache miss did not preserve READ_REQ");d.mem_req_ready=1;ac_edge(d,c);d.mem_req_ready=0;need(d.debug_state==11&&d.debug_outstanding,"AC read lease missing");
  // Physical read stays owned through arbitrary response absence.
  for(unsigned i=0;i<3;++i)ac_edge(d,c);
  d.mem_rsp_valid=1;d.mem_rsp_epoch=9;for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=response[i];ac_edge(d,c);d.mem_rsp_valid=0;
  need(d.debug_state==19&&!d.debug_outstanding,"matching fill did not return on original AC_EXTRACT edge");ac_check_payload(d,c,response,offset);
 }else{++c.hits;ac_check_payload(d,c,action==2?response:original,offset);if(action==2)++c.forwards;}
 ac_retire(d,c,action==1||action==2?response:original,offset,band,format>=4);++c.cases;c.offsets|=1U<<offset;c.bands|=1U<<band;c.segments|=1U<<band;if(format<4)c.formats|=1U<<format;
}
static void response_owner(unsigned offset,unsigned segment,unsigned band,unsigned action,ACCoverage&c){
 std::cerr<<"AC_FIXTURE response_owner offset="<<offset<<" segment="<<segment<<" band="<<band<<" action="<<action<<std::endl;
 Vscratch_probe d;ac_init(d,c);setup(d,11,0,0,0);BOTH(active_epoch,9);BOTH(read_segment,segment);BOTH(read_band,band);BOTH(outstanding,1);BOTH(return_state,19);BOTH(read_tag_match,0);BOTH(sealed,1);BOTH(used_bytes,128);
 const unsigned addr=48+16*segment+offset;BOTH(read_address,addr);BOTH(transfer_address,addr&~15U);BOTH(cache_valid,0);
 const auto response=line(offset,band,0,offset+segment+99);for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=response[i];
 d.mem_rsp_valid=1;d.mem_rsp_epoch=9;d.mem_rsp_error=action==1;if(action==2)d.mem_rsp_epoch=10;if(action==3)d.reset=1;if(action==4){d.abort_valid=1;d.abort_epoch=9;}
 ac_edge(d,c);d.mem_rsp_valid=d.mem_rsp_error=d.reset=d.abort_valid=0;
 if(action==0){need(d.debug_state==19&&!d.debug_outstanding,"owned READ_WAIT fill schedule");ac_check_payload(d,c,response,offset);ac_retire(d,c,response,offset,band);}
 else if(action==1){need(d.error==5&&d.debug_state==24&&!d.debug_outstanding,"matching READ_WAIT error priority");++c.errors;}
 else if(action==2){need(d.error==6&&d.debug_state==25&&d.debug_outstanding,"wrong owner retired pending read");++c.wrong;
  for(unsigned i=0;i<3;++i){ac_edge(d,c);}d.mem_rsp_valid=1;d.mem_rsp_epoch=9;ac_edge(d,c);d.mem_rsp_valid=0;need(d.debug_state==0&&!d.debug_outstanding,"matching late reply did not drain original read");++c.drains;
 }else{need(d.debug_state==0&&!d.debug_outstanding,"same-edge matching read reset/abort drain");++c.kills;}
 ++c.cases;c.offsets|=1U<<offset;c.bands|=1U<<band;c.segments|=1U<<segment;
}
int main(int argc,char**argv){try{
 need(inherited_record_main(argc,argv)==0,"complete immutable V116 C record/original control suites");ACCoverage c;
 for(unsigned offset=0;offset<16;++offset)for(unsigned band=1;band<=3;++band)for(unsigned format=0;format<4;++format)for(unsigned action=0;action<7;++action)hit_or_miss(offset,band,format,action,c);
 for(unsigned offset=0;offset<16;++offset)for(unsigned segment=0;segment<4;++segment)for(unsigned band=1;band<=3;++band)for(unsigned action=0;action<5;++action)response_owner(offset,segment,band,action,c);
 for(unsigned bits=0;bits<8192;++bits)hit_or_miss(0,1,4+bits,0,c);
 need(c.domain_good==4096&&c.domain_bad==4096,"all signed13 domain outcomes through real AC acquisition");
 need(c.cases==10496&&c.offsets==65535&&c.bands==14&&c.segments==15&&c.formats==15,"all offset/band/segment/format acquisition coverage");
 std::cout<<"{\"type\":\"v117_ac_verdict\",\"status\":\"TEST_PASS\",\"cached_signed13_cases\":8192,\"cached_signed13_good\":4096,\"cached_signed13_bad\":4096,\"cases\":"<<c.cases<<",\"edges\":"<<c.edges<<",\"hits\":"<<c.hits<<",\"misses\":"<<c.misses<<",\"same_edge_prefetch_forwards\":"<<c.forwards<<",\"kill_cases\":"<<c.kills<<",\"response_errors\":"<<c.errors<<",\"wrong_owner_cases\":"<<c.wrong<<",\"physical_drains\":"<<c.drains<<",\"payload_comparisons\":"<<c.compares<<",\"offset_mask\":"<<c.offsets<<",\"band_mask\":"<<c.bands<<",\"segment_mask\":"<<c.segments<<",\"format_mask\":"<<c.formats<<",\"public_cycle_delta\":0,\"pair_skipped_edges\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V117_AC_FAIL "<<e.what()<<'\n';return 1;}}
