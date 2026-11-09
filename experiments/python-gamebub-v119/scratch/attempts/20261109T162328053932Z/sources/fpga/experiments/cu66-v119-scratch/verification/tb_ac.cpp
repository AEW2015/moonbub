#include "tb_ac_base.cpp"
struct ValidationCoverage {uint64_t range_cases=0,bad=0,good=0,previous_true=0,output_cases=0,last_cases=0,wrapped_next=0,prefetch_requests=0,prefetch_responses=0;unsigned phase_mask=0;};
static bool independent_bad(const Vscratch_probe&d){
 const unsigned p=NEW(phase),block=d.coef_block,index=d.coef_index,band=d.coef_band;
 const int value=int16_t(d.coef_value);const uint32_t pos=NEW(raw_mode)?uint32_t(block*64U+index):p==0?block:uint32_t(block*64U+ranks[index]);
 bool bad=d.coef_epoch!=NEW(active_epoch)||band!=(p&3U)||block>=uint16_t(NEW(blocks))||value< -2048||value>2048||NEW(written)>=NEW(counts)[p&3U];
 if(NEW(raw_mode))bad=bad||pos!=NEW(written);
 else if(p==0)bad=bad||index!=0||block!=NEW(written);
 else {const unsigned z=ranks[index];const bool match=band==1?z>=1&&z<6:band==2?z>=6&&z<21:band==3?z>=21:index==0;bad=bad||!match||value==0||(NEW(previous_valid)&&pos<=NEW(previous_position));}
 return bad;
}
static void input_boundaries(ValidationCoverage&v){
 Vscratch_probe d;ACCoverage init;ac_init(d,init);setup(d,1,0,0,0);RecordCoverage c;
 const uint32_t frontiers[]={0U,1U,63U,64U,65U,65535U,65536U,0x3fffffU,0x400000U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU};
 const uint32_t limits[]={0U,1U,64U,0x3fffffU,0x400000U,0x80000000U,0xffffffffU};
 const unsigned blocks[]={0U,1U,8191U,8192U,65534U,65535U};const unsigned indices[]={0U,1U,5U,6U,20U,21U,63U};
 for(unsigned raw=0;raw<2;++raw)for(unsigned phase=0;phase<8;++phase)for(unsigned block:blocks)for(unsigned index:indices)
  for(uint32_t written:frontiers)for(uint32_t count:limits)for(unsigned order=0;order<4;++order)for(unsigned previous=0;previous<2;++previous){
   record_context(d,phase,raw!=0,37);BOTH(blocks,65535);d.coef_block=block;d.coef_index=index;BOTH(written,written);OLD(counts)[phase&3U]=NEW(counts)[phase&3U]=count;
   BOTH(previous_valid,previous);const uint32_t pos=raw?uint32_t(block*64U+index):phase==0?block:uint32_t(block*64U+ranks[index]);const uint32_t prev=order==0?pos-1U:order==1?pos:order==2?pos+1U:0xffffffffU;BOTH(previous_position,prev);
   d.eval();const bool bad=independent_bad(d);need(bool(OLD(input_bad))==bad&&bool(NEW(input_bad))==bad,"independent full32 format/range/order result");
   record_edge(d,c,!bad);need(d.error==(bad?3U:0U),"same-edge full32 input fault reason");++v.range_cases;v.phase_mask|=1U<<phase;if(bad)++v.bad;else ++v.good;if(previous)++v.previous_true;
  }
 need(v.range_cases==489216&&v.phase_mask==255&&v.good>0&&v.bad>0,"full32 boundary matrix dimensions");
}
static void output_boundaries(ValidationCoverage&v){
 Vscratch_probe d;ACCoverage c;ac_init(d,c);
 const unsigned blocks[]={0U,1U,2U,2046U,2047U,8191U,32767U,65534U,65535U};
 const unsigned limits[]={0U,1U,2U,2047U,2048U,8191U,32768U,65535U,65536U,131071U};
 for(unsigned raw=0;raw<2;++raw)for(unsigned prefetch=0;prefetch<2;++prefetch)for(unsigned block:blocks)for(unsigned limit:limits){
  setup(d,0,0,0,0);d.coef_valid=d.band_end_valid=d.seal_valid=d.begin_valid=0;BOTH(active_epoch,9);BOTH(output_block,block);BOTH(output_index,63);BOTH(blocks,limit);BOTH(raw_mode,raw);BOTH(prefetch_mode,prefetch);BOTH(cache_valid,0);BOTH(used_bytes,262144);BOTH(raw_value,37);ac_edge(d,c);
  // One actual stable-context predecessor edge matures the complete plan.
  // No plan or physical pending field is deposited by the fixture.
  BOTH(state,raw?22:20);BOTH(busy_owned,1);BOTH(sealed,1);d.dense_ready=1;d.eval();const bool launch=d.debug_prefetch_launch;
  const bool last=block+1U==limit;const unsigned next=uint16_t(block+1U);ac_edge(d,c);++v.output_cases;
  need(bool(d.done)==last,"full17 exact terminal decision");
  if(last){need(d.debug_state==23&&OLD(output_block)==block&&NEW(output_block)==block,"last output owner held");++v.last_cases;}
  else {need(OLD(output_block)==next&&NEW(output_block)==next,"full16 next block wraps exactly");if(block==65535U)++v.wrapped_next;
   if(launch){need(d.debug_state==27&&d.mem_req_valid&&!d.mem_req_write&&d.mem_req_epoch==9,"owned prefetch return plan");const unsigned address=d.mem_req_addr;d.mem_req_ready=1;ac_edge(d,c);d.mem_req_ready=0;++v.prefetch_requests;need(d.debug_outstanding&&d.debug_state==27&&d.mem_req_addr==address,"real accepted prefetch request");d.mem_rsp_valid=1;d.mem_rsp_epoch=9;for(unsigned j=0;j<4;++j)d.mem_rsp_data[j]=0;ac_edge(d,c);d.mem_rsp_valid=0;++v.prefetch_responses;need(!d.debug_outstanding&&d.debug_state==(raw?21U:14U),"matching response uses captured return plan");}
   else need(d.debug_state==(raw?21U:14U),"immediate next block plan");
  }
 }
 need(v.output_cases==360&&v.last_cases>0&&v.wrapped_next>0&&v.prefetch_requests==v.prefetch_responses&&v.prefetch_requests>0,"output endpoint/lease coverage");
}
int main(int argc,char**argv){try{
 need(inherited_v118_ac_main(argc,argv)==0,"complete immutable V118 scratch qualification");ValidationCoverage v;input_boundaries(v);output_boundaries(v);
 std::cout<<"{\"type\":\"v119_spatial_validation_verdict\",\"status\":\"TEST_PASS\",\"full32_cases\":"<<v.range_cases<<",\"full32_good\":"<<v.good<<",\"full32_bad\":"<<v.bad<<",\"phase_mask\":"<<v.phase_mask<<",\"output_plan_cases\":"<<v.output_cases<<",\"terminal_cases\":"<<v.last_cases<<",\"wrapped_next_cases\":"<<v.wrapped_next<<",\"real_prefetch_requests\":"<<v.prefetch_requests<<",\"matching_prefetch_responses\":"<<v.prefetch_responses<<",\"public_cycle_delta\":0,\"error_cycle_delta\":0,\"pair_skipped_edges\":0}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V119_SPATIAL_VALIDATION_FAIL "<<e.what()<<'\n';return 1;}}
