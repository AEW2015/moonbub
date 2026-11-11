#include "Vraw_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
static void need(bool value,const char*message){if(!value)throw std::runtime_error(message);}
struct Tuple{uint32_t epoch;uint16_t block;uint8_t index;int16_t value;uint8_t band;};
static const std::array<unsigned,64> ranks=[](){std::array<unsigned,64>a{};unsigned rank=0;for(unsigned diagonal=0;diagonal<15;++diagonal)for(unsigned step=0;step<8;++step){int row=(diagonal&1)?int(step):7-int(step),col=int(diagonal)-row;if(col>=0&&col<8)a[unsigned(row*8+col)]=rank++;}return a;}();
static unsigned raster(unsigned rank){for(unsigned i=0;i<64;++i)if(ranks[i]==rank)return i;throw std::runtime_error("raster rank");}
static bool band_matches(unsigned band,unsigned index){unsigned z=ranks[index];return band==1?(z>=1&&z<6):band==2?(z>=6&&z<21):band==3?z>=21:index==0;}
static void tuple(Vraw_probe&d,bool raw,const Tuple&t){if(raw){d.coef_raw_epoch=t.epoch;d.coef_raw_block=t.block;d.coef_raw_index=t.index;d.coef_raw_value=uint16_t(t.value);d.coef_raw_band=t.band;}else{d.coef_context_epoch=t.epoch;d.coef_context_block=t.block;d.coef_context_index=t.index;d.coef_context_value=uint16_t(t.value);d.coef_context_band=t.band;}}
static void defaults(Vraw_probe&d){
 d.clk=0;d.reset=1;d.begin_valid=0;d.begin_blocks=1;d.begin_raw=0;d.begin_serial_clear=0;d.begin_overlap=0;d.begin_prefetch=0;d.begin_tile_overlap=0;d.begin_count1=d.begin_count2=d.begin_count3=0;d.begin_epoch=0;d.begin_prefix1=d.begin_prefix12=d.begin_prefix123=0;d.begin_threshold1=d.begin_threshold2=d.begin_threshold3=0;d.begin_capacity_upper=131056;d.begin_capacity_lower=2147483624U;d.begin_capacity_wrap=0;
 d.coef_valid=0;d.coef_select_raw=0;tuple(d,true,{0,0,0,0,0});tuple(d,false,{0,0,0,0,0});d.band_end_valid=0;d.band_end_band=0;d.band_end_epoch=0;d.seal_valid=0;d.seal_epoch=0;d.abort_valid=0;d.abort_epoch=0;d.dense_ready=0;d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;for(unsigned i=0;i<4;++i)d.mem_rsp_data[i]=0;
 d.alg_raw_mode=0;d.alg_active_epoch=0;d.alg_blocks=0;d.alg_written=0;d.alg_previous_position=0;d.alg_previous_valid=0;d.alg_rank_threshold_mask=0;d.alg_phase=0;d.alg_count0=d.alg_count1=d.alg_count2=d.alg_count3=0;
}
static bool literal(const Vraw_probe&d,const Tuple&t,unsigned phase,bool use_literal){
 unsigned count=phase%4==0?d.alg_count0:phase%4==1?d.alg_count1:phase%4==2?d.alg_count2:d.alg_count3;
 bool order=use_literal?(uint32_t(t.block)*64U+ranks[t.index]<=d.alg_previous_position):
   ((d.alg_previous_position>>22)!=0 || t.block<((d.alg_previous_position>>6)&65535U) ||
    (t.block==((d.alg_previous_position>>6)&65535U)&&((d.alg_rank_threshold_mask>>t.index)&1U)));
 bool format=d.alg_raw_mode?(uint32_t(t.block)*64U+t.index!=d.alg_written):phase==0?
   (t.index!=0||uint32_t(t.block)!=d.alg_written):(!band_matches(t.band,t.index)||t.value==0||(d.alg_previous_valid&&order));
 return t.epoch!=d.alg_active_epoch||t.band!=(phase&3)||t.block>=uint16_t(d.alg_blocks)||t.value< -2048||t.value>2048||d.alg_written>=count||format;
}
static int wire_suite(unsigned seed){
 Vraw_probe d;defaults(d);std::mt19937 rng(seed);uint64_t cases=0,phase_checks=0,owned_literal_checks=0,good=0,bad=0,selected_only_bad=0,other_only_bad=0,high_epochs=0,high_blocks=0,arbitrary_masks=0;unsigned select_mask=0,format_mask=0,phase_mask=0;
 const std::array<uint32_t,8> words{0,1,63,64,0x003fffffU,0x00400000U,0x80000000U,0xffffffffU};
 const std::array<uint32_t,6> epochs{0,1,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU};
 const std::array<unsigned,8> blocks{0,1,63,8191,8192,32767,65535,65536};
 const std::array<int,9> values{-32768,-2049,-2048,-1,0,1,2048,2049,32767};
 const std::array<unsigned,8> indices{0,1,7,8,15,21,31,63};
 auto check=[&](const Tuple&r,const Tuple&c,bool coherent){
  tuple(d,true,r);tuple(d,false,c);d.eval();need(d.pair_equal&&d.pair_predicate_equal,"all-cycle real-scratch selected tuple/predicate identity");
  const Tuple&s=d.coef_select_raw?r:c;unsigned expected=0,mathematical=0;
  for(unsigned p=0;p<8;++p){expected|=unsigned(literal(d,s,p,false))<<p;mathematical|=unsigned(literal(d,s,p,true))<<p;++phase_checks;}
  need(d.alg_reference_phase_bad==expected&&d.alg_candidate_phase_bad==expected,"source-extracted all8 implemented decisions");
  need(d.alg_literal_phase_bad==mathematical,"independent literal-position expression");need(d.alg_block_limit_high==(d.alg_blocks>>16),"original17bit block-limit observation");
  need(d.alg_reference_epoch_bad==(s.epoch!=d.alg_active_epoch)&&d.alg_candidate_epoch_bad==d.alg_reference_epoch_bad,"full32 epoch error class");
  need(d.alg_reference_selected_bad==((expected>>d.alg_phase)&1U)&&d.alg_candidate_selected_bad==d.alg_reference_selected_bad,"selected phase decision");
  if(coherent){need(expected==mathematical,"coherent rank literal equivalence");++owned_literal_checks;}
  bool sb=literal(d,s,d.alg_phase,false),ob=literal(d,d.coef_select_raw?c:r,d.alg_phase,false);good+=!sb;bad+=sb;selected_only_bad+=sb&&!ob;other_only_bad+=!sb&&ob;
  select_mask|=1U<<d.coef_select_raw;format_mask|=1U<<d.alg_raw_mode;phase_mask|=1U<<d.alg_phase;high_epochs+=(s.epoch>>31)!=0;high_blocks+=(s.block>>15)!=0;arbitrary_masks+=!coherent;++cases;
 };
 for(unsigned format=0;format<2;++format)for(unsigned select=0;select<2;++select)for(unsigned phase=0;phase<8;++phase)for(unsigned n=0;n<4096;++n){
  d.alg_raw_mode=format;d.coef_select_raw=select;d.alg_phase=phase;d.alg_active_epoch=epochs[n%epochs.size()];d.alg_blocks=blocks[(n/3)%blocks.size()];d.alg_written=words[(n/5)%words.size()];d.alg_previous_position=words[(n/7)%words.size()];d.alg_previous_valid=(n>>4)&1;d.alg_rank_threshold_mask=(uint64_t(rng())<<32)|rng();d.alg_count0=words[(n/11)%8];d.alg_count1=words[(n/13)%8];d.alg_count2=words[(n/17)%8];d.alg_count3=words[(n/19)%8];
  Tuple r{epochs[(n/23)%6],uint16_t(blocks[(n/29)%8]),uint8_t(indices[(n/31)%8]),int16_t(values[(n/37)%9]),uint8_t((n/41)%4)};
  Tuple c{epochs[(n/43)%6],uint16_t(blocks[(n/47)%8]),uint8_t(indices[(n/53)%8]),int16_t(values[(n/59)%9]),uint8_t((n/61)%4)};
  bool coherent=(n&7)==0;
  if(coherent){uint64_t mask=0;for(unsigned i=0;i<64;++i)if(ranks[i]<=(d.alg_previous_position&63))mask|=uint64_t(1)<<i;d.alg_rank_threshold_mask=mask;}
  if((n&15)<4){d.alg_blocks=1;d.alg_written=0;d.alg_count0=d.alg_count1=d.alg_count2=d.alg_count3=2;d.alg_previous_valid=0;Tuple v{d.alg_active_epoch,0,uint8_t(format||phase==0?0:raster((phase&3)==1?1:(phase&3)==2?6:(phase&3)==3?21:0)),1,uint8_t(phase&3)};r=c=v;if((n&15)==1)r.epoch^=0x80000000U;if((n&15)==2)c.epoch^=0x80000000U;if((n&15)==3){r.value=-2049;c.block=65535;}}
  check(r,c,coherent);
 }
 for(unsigned n=0;n<65536;++n){d.alg_raw_mode=rng()&1;d.coef_select_raw=rng()&1;d.alg_phase=rng()&7;d.alg_active_epoch=rng();d.alg_blocks=rng()&131071;d.alg_written=rng();d.alg_previous_position=rng();d.alg_previous_valid=rng()&1;d.alg_rank_threshold_mask=(uint64_t(rng())<<32)|rng();d.alg_count0=rng();d.alg_count1=rng();d.alg_count2=rng();d.alg_count3=rng();Tuple r{uint32_t(rng()),uint16_t(rng()),uint8_t(rng()&63),int16_t(rng()),uint8_t(rng()&3)},c{uint32_t(rng()),uint16_t(rng()),uint8_t(rng()&63),int16_t(rng()),uint8_t(rng()&3)};check(r,c,false);}
 need(cases==196608&&phase_checks==1572864&&select_mask==3&&format_mask==3&&phase_mask==255,"wire coverage inventory");need(good&&bad&&selected_only_bad&&other_only_bad&&high_epochs&&high_blocks&&arbitrary_masks&&owned_literal_checks,"wire positive coverage");
 std::cout<<"{\"type\":\"v128_raw_wire_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"boundary_cases\":131072,\"random_cases\":65536,\"phase_checks\":"<<phase_checks<<",\"coherent_literal_checks\":"<<owned_literal_checks<<",\"good\":"<<good<<",\"bad\":"<<bad<<",\"selected_only_bad\":"<<selected_only_bad<<",\"other_only_bad\":"<<other_only_bad<<",\"high_epoch_cases\":"<<high_epochs<<",\"high_block_cases\":"<<high_blocks<<",\"arbitrary_mask_cases\":"<<arbitrary_masks<<",\"selector_mask\":"<<select_mask<<",\"format_mask\":"<<format_mask<<",\"phase_mask\":"<<phase_mask<<",\"DUT_clocks\":0,\"natural_packets\":false,\"new_result_forces\":0}\n";return 0;
}
struct ClockBench{
 Vraw_probe d;std::mt19937 rng;uint64_t clocks=0,evals=0,requests=0,acks=0;uint32_t epoch=1,owner=0;bool pending=false,hold=false,block_requests=false,force_ready=false,wrong=false,error_response=false;unsigned delay=0;bool malformed=false;
 explicit ClockBench(unsigned seed):rng(seed){defaults(d);tick();d.reset=0;}
 void check(){++evals;need(d.pair_equal&&d.pair_predicate_equal,"paired actual-scratch public/private mismatch");}
 void tick(){need(clocks<10000,"clock suite per-instance watchdog");d.mem_req_ready=!pending&&!block_requests&&(force_ready||rng()%3!=0);d.mem_rsp_valid=pending&&!hold&&delay==0;d.mem_rsp_epoch=owner^(wrong?0x80000000U:0);d.mem_rsp_error=error_response;d.clk=0;d.eval();check();bool accepted=d.mem_req_valid&&d.mem_req_ready,retired=d.mem_rsp_valid&&!wrong;uint32_t accepted_owner=d.mem_req_epoch;if(accepted)need(d.mem_req_write,"unexpected pre-seal read");d.clk=1;d.eval();check();++clocks;if(retired){pending=false;++acks;}if(accepted){need(!pending,"physical pending overwrite");pending=true;owner=accepted_owner;delay=1+rng()%4;++requests;}else if(pending&&delay)--delay;d.clk=0;d.eval();check();}
 void wait_ingest(){for(unsigned i=0;d.debug_state!=1||!d.coef_ready;++i){need(i<200,"INGEST watchdog");need(!d.error,"unexpected error awaiting INGEST");tick();}}
 void begin(bool raw,bool overlap,unsigned number=1){d.begin_blocks=1;d.begin_raw=raw;d.begin_overlap=overlap;d.begin_count1=raw?0:number;d.begin_count2=raw?0:1;d.begin_count3=raw?0:1;d.begin_epoch=epoch;
  auto align=[](uint32_t x){return (x+15U)&0xfffffff0U;};d.begin_prefix1=align(d.begin_count1*4);d.begin_prefix12=d.begin_prefix1+align(d.begin_count2*4);d.begin_prefix123=d.begin_prefix12+align(d.begin_count3*4);d.begin_threshold1=d.begin_count1/5+unsigned(d.begin_count1%5!=0);d.begin_threshold2=d.begin_count2/15+unsigned(d.begin_count2%15!=0);d.begin_threshold3=d.begin_count3/43+unsigned(d.begin_count3%43!=0);uint32_t a=((d.begin_prefix123>>4)+2)&0xfffffffU;d.begin_capacity_upper=((16384U-a)&0xfffffffU)<<3;d.begin_capacity_lower=((~a)&0xfffffffU)<<3;d.begin_capacity_wrap=a>16384;d.begin_valid=1;d.clk=0;d.eval();check();need(d.begin_ready,"begin not ready");tick();d.begin_valid=0;wait_ingest();need(d.active_epoch==epoch,"active full epoch");}
 void offer(const Tuple&t,bool select,bool other_bad=true){d.coef_select_raw=select;Tuple other=t;if(other_bad){other.epoch^=0x80000000U;other.block=65535;other.value=-2049;}tuple(d,select,t);tuple(d,!select,other);}
 void send(const Tuple&t,bool select){wait_ingest();offer(t,select);d.coef_valid=1;tick();d.coef_valid=0;if(!d.error)wait_ingest();}
 void end_band(unsigned band){wait_ingest();d.band_end_valid=1;d.band_end_band=band;d.band_end_epoch=epoch;tick();d.band_end_valid=0;if(!d.error&&band<3)wait_ingest();}
 void drain(bool reset){d.coef_valid=d.band_end_valid=0;d.abort_epoch=d.owned_abort_epoch;d.abort_valid=!reset;d.reset=reset;tick();d.abort_valid=d.reset=0;d.eval();check();hold=wrong=error_response=false;block_requests=false;for(unsigned i=0;pending||d.busy;++i){need(i<200,"physical debt drain watchdog");tick();}need(d.begin_ready&&!d.debug_outstanding,"cancel/retry not quiescent");}
};
static int clock_suite(unsigned seed){
 uint64_t clocks=0,evals=0,requests=0,acks=0;unsigned cases=0,epoch_errors=0,format_errors=0,phase_mask=0,selector_mask=0,format_mask=0,pending_faults=0,wrong_ack=0,cancel_cases=0,unready=0,band_errors=0,accept_fault=0,retries=0;
 auto collect=[&](const ClockBench&b){clocks+=b.clocks;evals+=b.evals;requests+=b.requests;acks+=b.acks;need(!b.pending&&b.requests==b.acks,"physical request/ACK conservation");};
 for(unsigned fmt=0;fmt<2;++fmt)for(unsigned select=0;select<2;++select)for(unsigned phase=0;phase<(fmt?1U:4U);++phase)for(unsigned kind=0;kind<6;++kind){
  ClockBench b(seed+cases);b.epoch=(cases&1)?0x80000001U:1;b.begin(fmt,true,2);selector_mask|=1U<<select;format_mask|=1U<<fmt;
  if(phase){b.send({b.epoch,0,0,5,0},select);b.end_band(0);for(unsigned p=1;p<phase;++p){unsigned count=p==1?2:1;for(unsigned j=0;j<count;++j)b.send({b.epoch,0,uint8_t(raster(p==1?1+j:p==2?6:21)),2,uint8_t(p)},select);b.end_band(p);}}
  phase_mask|=1U<<phase;Tuple t{b.epoch,0,uint8_t(fmt||phase==0?0:raster(phase==1?1:phase==2?6:21)),1,uint8_t(phase)};
  if(kind==0){t.epoch^=0x80000000U;t.value=-2049;}else if(kind==1)t.block=65535;else if(kind==2)t.value=-2049;else if(kind==3)t.value=2049;else if(kind==4)t.band=(t.band+1)&3;else if(!fmt&&phase){t.value=0;}else{t.index=63;}
  b.offer(t,select);b.d.coef_valid=1;b.tick();b.d.coef_valid=0;unsigned expected=kind==0?2:3;need(b.d.error==expected,"epoch-before-format fault priority");epoch_errors+=expected==2;format_errors+=expected==3;b.drain(false);++cases;collect(b);
 }
 for(unsigned select=0;select<2;++select)for(unsigned action=0;action<6;++action){ClockBench b(seed+cases);b.begin(true,true);b.hold=true;b.block_requests=true;for(unsigned i=0;i<8;++i)b.send({b.epoch,0,uint8_t(i),3,0},select);need(b.d.debug_state==1&&!b.pending,"pending setup INGEST");
  if(action!=5){b.block_requests=false;b.force_ready=true;for(unsigned i=0;!b.pending;++i){need(i<40,"accepted-write fixture watchdog");b.tick();}need(b.d.debug_outstanding,"real accepted write absent");}
  Tuple bad{b.epoch^0x80000000U,0,8,-2049,0};b.offer(bad,select);b.d.coef_valid=1;
  if(action<2){b.d.reset=action==1;b.d.abort_valid=action==0;b.d.abort_epoch=b.epoch;}
  if(action==2){b.hold=false;b.delay=0;}
  if(action==3){b.hold=false;b.delay=0;b.wrong=true;}
  if(action==5){b.block_requests=false;b.force_ready=true;}
  b.tick();b.d.coef_valid=0;b.d.reset=b.d.abort_valid=0;
  if(action<2){need(!b.d.error&&b.pending&&b.d.debug_outstanding,"cancel discarded real request debt");++cancel_cases;}
  else if(action==3){need(b.d.error==6&&b.pending&&b.d.debug_outstanding,"wrong ACK priority/debt");++wrong_ack;}
  else{need(b.d.error==2,"malformed pending coefficient error class");if(action==2)need(!b.pending&&!b.d.debug_outstanding,"matching ACK did not retire");else{need(b.pending&&b.d.debug_outstanding,"fault lost accepted memory debt");++pending_faults;if(action==5)++accept_fault;}}
  b.drain(false);++b.epoch;b.begin(false,false);b.send({b.epoch,0,0,1,0},select);b.drain(true);++retries;++cases;collect(b);
 }
 for(unsigned select=0;select<2;++select){ClockBench b(seed+cases);b.begin(false,false);b.offer({b.epoch,0,0,1,0},select);b.d.coef_valid=1;b.tick();need(b.d.debug_state==2&&!b.d.coef_ready,"expected original APPEND unready edge");b.offer({b.epoch^0x80000000U,65535,63,-32768,3},select);b.tick();b.d.coef_valid=0;need(!b.d.error&&b.d.debug_state==1,"unready offer improperly consumed");++unready;b.d.band_end_valid=1;b.d.band_end_band=0;b.d.band_end_epoch=b.epoch^0x80000000U;b.tick();b.d.band_end_valid=0;need(b.d.error==2,"band-end epoch priority");++band_errors;b.drain(false);++cases;collect(b);}
 need(cases==74&&epoch_errors==10&&format_errors==50&&phase_mask==15&&selector_mask==3&&format_mask==3,"clock coverage inventory");need(pending_faults==4&&wrong_ack==2&&cancel_cases==4&&unready==2&&band_errors==2&&accept_fault==2&&retries==12,"debt/cancel/held coverage inventory");
 std::cout<<"{\"type\":\"v128_raw_clock_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<cases<<",\"clock_edges\":"<<clocks<<",\"eval_checks\":"<<evals<<",\"requests\":"<<requests<<",\"acks\":"<<acks<<",\"epoch_errors\":"<<epoch_errors<<",\"format_errors\":"<<format_errors<<",\"phase_mask\":"<<phase_mask<<",\"selector_mask\":"<<selector_mask<<",\"format_mask\":"<<format_mask<<",\"pending_faults\":"<<pending_faults<<",\"wrong_ack_cases\":"<<wrong_ack<<",\"cancel_cases\":"<<cancel_cases<<",\"unready_offers\":"<<unready<<",\"band_epoch_errors\":"<<band_errors<<",\"same_edge_accept_faults\":"<<accept_fault<<",\"retries\":"<<retries<<",\"public_cycle_delta\":0,\"prepared_state_forces\":0,\"new_result_forces\":0}\n";return 0;
}
int main(int argc,char**argv){try{Verilated::commandArgs(argc,argv);need(argc==3,"usage wire|clock seed");unsigned seed=unsigned(std::stoul(argv[2]));if(std::string(argv[1])=="wire")return wire_suite(seed);need(std::string(argv[1])=="clock","unknown suite");return clock_suite(seed);}catch(const std::exception&e){std::cerr<<"V128_RAW_FAIL "<<e.what()<<'\n';return 1;}}
