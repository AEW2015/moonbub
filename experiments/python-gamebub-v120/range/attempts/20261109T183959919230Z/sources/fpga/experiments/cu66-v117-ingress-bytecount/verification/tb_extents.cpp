#include "ingress_base.cpp"
#define IOLD(n) d.rootp->ingress_probe__DOT__reference_dut__DOT__##n
#define INEW(n) d.rootp->ingress_probe__DOT__dut__DOT__##n
#define IBOTH(n,v) do{IOLD(n)=(v);INEW(n)=(v);}while(0)
struct ExtentsCoverage {uint64_t edges=0,initial=0,ready=0,cancel=0,retries=0,commits=0,rejects=0;};
static void compare(Vingress_probe&d){
 need(IOLD(state)==INEW(state)&&IOLD(error)==INEW(error)&&IOLD(cursor)==INEW(cursor),"postedge state/error/cursor exact pair");
 need(IOLD(prepared_request_addr)==INEW(prepared_request_addr)&&IOLD(prepared_request_in_bounds)==INEW(prepared_request_in_bounds)&&IOLD(descriptor_last_addr)==INEW(descriptor_last_addr),"postedge request/last-address exact pair");
 for(unsigned i=0;i<4;++i)need(IOLD(offsets)[i]==INEW(offsets)[i]&&IOLD(sizes)[i]==INEW(sizes)[i]&&IOLD(k0s)[i]==INEW(k0s)[i]&&IOLD(k1s)[i]==INEW(k1s)[i],"all descriptor commit fields exact pair");
}
static void extent_edge(Vingress_probe&d,ExtentsCoverage&c){
 d.clk=0;d.eval();compare(d);d.clk=1;d.eval();d.clk=0;d.eval();compare(d);need(++c.edges<1000000,"extent finite edge watchdog");
}
static void extent_setup(Vingress_probe&d,ExtentsCoverage&c,uint32_t size,uint32_t cursor,uint32_t length,unsigned band,unsigned count=1){
 d.clk=0;d.reset=1;d.start=d.abort_packet=d.in_valid=d.in_last=d.out_ready=d.meta_ready=d.band_end_ready=0;d.packet_bytes=174;d.blocks=1;d.epoch=77;d.word16=d.serial_mode=d.in_data=0;extent_edge(d,c);d.reset=0;
 // Declared complete owner poststate. No packet RAM request is clocked here.
 // Existing FINISHED clocks mature the real new private size registers; they
 // are never forced or initialized by the bench.
 IBOTH(state,7);IBOTH(done,0);IBOTH(error,0);IBOTH(size_bytes,size);IBOTH(received,0);IBOTH(context_epoch,77);IBOTH(context_blocks,1);IBOTH(context_active,0);IBOTH(cursor,cursor);IBOTH(band,band);IBOTH(selection_context,0);IBOTH(descriptor_ready,0);
 IBOTH(plan_align1,16);IBOTH(plan_align2,16);IBOTH(plan_align3,16);IBOTH(threshold_live,7);IBOTH(capacity_live,1);IBOTH(capacity_upper,131032);IBOTH(capacity_lower,0x7fffffd0U);IBOTH(capacity_wrap,0);
 for(unsigned i=0;i<4;++i){IOLD(lengths)[i]=INEW(lengths)[i]=length;IOLD(counts)[i]=INEW(counts)[i]=i==band?count:1;IOLD(sizes)[i]=INEW(sizes)[i]=0;IOLD(offsets)[i]=INEW(offsets)[i]=0;IOLD(k0s)[i]=INEW(k0s)[i]=0;IOLD(k1s)[i]=INEW(k1s)[i]=0;}
 for(unsigned i=0;i<3;++i)IOLD(count_threshold)[i]=INEW(count_threshold)[i]=(i+1==band?count:1U)?1U:0U;
 for(unsigned i=0;i<3;++i){d.packet_bytes^=0xffffffffU;d.blocks^=0x1ffffU;d.epoch^=0xa5a55a5aU;extent_edge(d,c);}
 IBOTH(state,14);extent_edge(d,c);need(d.debug_state==3,"original SELECT_BAND edge not preserved");
 need(INEW(packet_payload_end)==uint32_t(size-4U)&&INEW(packet_bit_limit)==uint32_t(8U*uint32_t(size-46U)),"independent cached uint32 size extents");
 need(INEW(active_remaining)==uint32_t(uint32_t(size-4U)-cursor)&&INEW(active_cursor_bad)==unsigned(cursor>uint32_t(size-4U))&&INEW(active_length_minus6)==uint32_t(length-6U),"independent selected descriptor extents");
}
static void initial_extent(uint32_t size,uint32_t cursor,uint32_t length,unsigned band,ExtentsCoverage&c){
 Vingress_probe d;extent_setup(d,c,size,cursor,length,band);const uint32_t end=size-4U,remaining=end-cursor;const bool bad=length<6U||cursor>end||length>remaining;
 extent_edge(d,c);need(d.error==(bad?4U:0U)&&d.debug_state==(bad?8U:12U),"independent initial descriptor bounds/error priority");
 if(!bad){need(INEW(prepared_request_addr)==cursor&&INEW(descriptor_last_addr)==uint32_t(cursor+uint32_t(length-1U)),"exact wrapped first/last descriptor request");need(d.stage_read_req==unsigned(cursor<size&&cursor<49152U),"original MAX_PACKET_BYTES request eligibility");}
 ++c.initial;
}
static void ready_extent(uint32_t size,uint32_t cursor,uint32_t bits,uint32_t length,unsigned band,unsigned kind,ExtentsCoverage&c){
 const unsigned count=kind==3?0:1;Vingress_probe d;extent_setup(d,c,size,cursor,length,band,count);IBOTH(descriptor_ready,1);
 const unsigned k0=kind==1?255:0,k1=kind==2?254:band==0?255:0,pad=kind==4?255:0;
 IOLD(fetch_bytes)[0]=INEW(fetch_bytes)[0]=k0;IOLD(fetch_bytes)[1]=INEW(fetch_bytes)[1]=k1;
 for(unsigned i=0;i<4;++i){IOLD(fetch_bytes)[2+i]=INEW(fetch_bytes)[2+i]=uint8_t(bits>>(8*i));}IOLD(fetch_bytes)[6]=INEW(fetch_bytes)[6]=pad;
 const uint32_t bytes=(bits>>3)+unsigned((bits&7U)!=0),limit=uint32_t(8U*uint32_t(size-46U));unsigned error=0;
 if(bytes!=uint32_t(length-6U)||bits>limit)error=4;
 else if((band==0&&(k0>13||k1!=255))||(band!=0&&(k0>19||k1>11)))error=4;
 else if(band!=0&&count==0&&bits!=0)error=7;
 else if((bits&7U)!=0&&(pad&(255U>>(bits&7U)))!=0)error=7;
 extent_edge(d,c);need(d.error==error&&d.debug_state==(error?8U:band==3?9U:14U),"independent complete descriptor error/state priority");
 if(!error){need(INEW(offsets)[band]==uint32_t(cursor+6U)&&INEW(sizes)[band]==bits&&INEW(cursor)==uint32_t(cursor+length)&&INEW(k0s)[band]==k0&&INEW(k1s)[band]==k1,"independent same-edge descriptor offset/size/frontier commit");++c.commits;}else ++c.rejects;
 ++c.ready;
}
static void extent_cancellation(unsigned band,unsigned phase,unsigned flags,ExtentsCoverage&c){
 Vingress_probe d;extent_setup(d,c,174,42,7,band);if(phase==0)IBOTH(state,14);
 d.reset=flags&1;d.start=(flags>>1)&1;d.abort_packet=(flags>>2)&1;d.packet_bytes=174;d.blocks=1;d.epoch=91;extent_edge(d,c);
 need(!d.out_valid&&!d.meta_valid&&!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_word_valid,"same-edge extent cancellation public fence");
 need(d.debug_state==(flags==2?1U:0U),"unchanged reset/start/abort branch priority");need(!INEW(descriptor_extent_live),"cancel did not revoke selected extent certificate");++c.cancel;
 // Replacement owns the existing capture path again. This is a prepared
 // predicate retry; inherited packet suites retain complete physical retries.
 d.reset=d.start=d.abort_packet=0;extent_setup(d,c,174,42,7,band);extent_edge(d,c);need(!d.error&&d.debug_state==12,"fresh extent preparation retry failed");++c.retries;
}
int main(int argc,char**argv){try{
 need(inherited_ingress_main(argc,argv)==0,"complete immutable ingress/corruption/cancel/length suite");ExtentsCoverage c;
 const std::array<uint32_t,14>sizes{{0,1,3,4,45,46,47,48,174,49152,0x1fffffffU,0x2000002eU,0x80000000U,0xffffffffU}};
 const std::array<uint32_t,8>cursors{{0,1,42,49151,0xfffffff8U,0xfffffffeU,0xffffffffU,0x80000000U}};
 const std::array<uint32_t,14>lengths{{0,1,5,6,7,15,16,127,128,0x1fffffffU,0x20000000U,0x80000000U,0xfffffffeU,0xffffffffU}};
 for(uint32_t size:sizes)for(uint32_t cursor:cursors)for(uint32_t length:lengths)for(unsigned band=0;band<4;++band)initial_extent(size,cursor,length,band,c);
 const std::array<uint32_t,13>bits_values{{0,1,7,8,9,31,32,63,64,0x7fffffffU,0x80000000U,0xfffffff8U,0xffffffffU}};
 for(uint32_t size:sizes)for(unsigned ci=0;ci<6;++ci)for(uint32_t bits:bits_values){const uint32_t bytes=(bits>>3)+unsigned((bits&7U)!=0);const std::array<uint32_t,5>ls{{bytes+5U,bytes+6U,bytes+7U,0U,0xffffffffU}};for(uint32_t length:ls)for(unsigned band=0;band<4;++band)ready_extent(size,cursors[ci],bits,length,band,0,c);}
 for(unsigned band=0;band<4;++band)for(unsigned kind=0;kind<5;++kind)ready_extent(174,0xfffffff8U,9,8,band,kind,c);
 for(unsigned band=0;band<4;++band)for(unsigned phase=0;phase<2;++phase)for(unsigned flags=1;flags<8;++flags)extent_cancellation(band,phase,flags,c);
 need(c.initial==6272&&c.ready==21860&&c.cancel==56&&c.retries==56&&c.commits>0&&c.rejects>0,"complete selected extent boundary coverage");
 std::cout<<"{\"type\":\"v117_ingress_extent_verdict\",\"status\":\"TEST_PASS\",\"initial_cases\":"<<c.initial<<",\"ready_cases\":"<<c.ready<<",\"cancellation_cases\":"<<c.cancel<<",\"prepared_retries\":"<<c.retries<<",\"commits\":"<<c.commits<<",\"rejects\":"<<c.rejects<<",\"edges\":"<<c.edges<<",\"public_cycle_delta\":0,\"pair_skipped_edges\":0}\n";return 0;
 }catch(const std::exception&e){std::cerr<<"V117_INGRESS_EXTENTS_FAIL "<<e.what()<<'\n';return 1;}}
