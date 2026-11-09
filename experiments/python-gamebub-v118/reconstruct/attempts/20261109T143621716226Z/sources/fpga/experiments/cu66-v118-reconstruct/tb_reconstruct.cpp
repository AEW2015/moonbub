#include "Vreconstruct_probe.h"
#include "Vreconstruct_probe___024root.h"
#include "verilated.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <fstream>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
static void need(bool b,const std::string&s){if(!b)throw std::runtime_error(s);}
// Exact independent row/column oracle retained from the V103 focused bench.
static unsigned oracle(unsigned p,unsigned t){
    if(p!=0)return t&2047u;
    const unsigned row=t/90u,col=t%90u;
    return ((row/2u)*45u+col/2u)&2047u;
}
static unsigned plane_of(unsigned id){return id<5400?0:id<6750?1:2;}
static unsigned tile_of(unsigned id){return id-(id<5400?0:id<6750?5400:6750);}
static bool hidden(unsigned p,unsigned t){return p==0?((t>=633&&t<=651)||(t>=723&&t<=741)||(t>=993&&t<=1011)||(t>=1083&&t<=1101)||(t>=4071&&t<=4110)||(t>=4161&&t<=4200)||(t>=4251&&t<=4290)||(t>=4431&&t<=4460)||(t>=4521&&t<=4550)):(t>=1046&&t<=1064);}
static int residual(unsigned id,unsigned ix){if(ix%16==0)return -8388608;if(ix%16==1)return 8388607;return int((id*29+ix*31)%801)-400;}
static unsigned reference(unsigned id,unsigned ix,uint64_t generation){return unsigned((id*17+ix*13+generation*7)&255U);}
struct Job{unsigned id=0,mode=0,scale=0,token=0,block=0;};
struct PendingRef{uint32_t epoch=0,fid=0;uint64_t generation=0;unsigned plane=0,tile=0,delay=0;};
struct Held{std::array<uint64_t,7> v;bool operator==(const Held&o)const{return v==o.v;}};
class Bench{
public:
 Vreconstruct_probe d;std::ofstream trace;std::string phase="initial";bool diagnostics=false;unsigned previous_state=99;std::mt19937 rng;uint64_t clocks=0,total_outputs=0,total_inputs=0,overlap=0,held_checks=0,geometry=0,frame_start=0,last_frame_cycles=0;
 uint64_t physical_copy_edges=0,physical_copy_bits=0;std::array<uint64_t,4> copy_lanes{};unsigned pipeline_fault_cases=0;
 unsigned emitted=0,next_lookup=0,input_index=0,next_token=0,max_owners=0,full_owner_cycles=0,fixture_drains=0,private_copy_cancel_cases=0;std::array<unsigned,3> blocks{};std::vector<Job> jobs;
 std::optional<Job> mode_pending,input_job;std::optional<PendingRef> physical;std::optional<Held> held;
 bool key=true,no_stalls=false,hold_output=false,hold_mode=false,hold_ref=false,pause_residual=false;unsigned pause_after=64;
 int input_fault=-1,ref_fault=-1,mode_fault=-1;bool matching_ref_error=false;
 uint32_t frame_epoch=200,frame_id=300,ref_id=99;uint64_t generation=0x100000001ULL;
 explicit Bench(unsigned seed):rng(seed){d.clk=0;d.reset=1;d.start=d.cancel=d.input_done=d.in_valid=0;d.admitted_ready=1;d.key_frame=1;d.epoch=frame_epoch;d.frame_fid=frame_id;d.accepted_ref_valid=1;d.accepted_ref_fid=ref_id;d.accepted_ref_generation=generation;d.lookup_ready=d.lookup_rsp=d.lookup_mode=d.lookup_scale=0;d.in_epoch=d.in_child_epoch=d.in_token=d.in_plane=d.in_qscale=d.in_block=d.in_tile=d.in_qcell=d.in_index=d.in_value=0;d.out_ready=0;d.ref_req_ready=0;d.ref_rsp_valid=d.ref_rsp_epoch=d.ref_rsp_fid=d.ref_rsp_generation=d.ref_rsp_plane=d.ref_rsp_tile=d.ref_rsp_error=0;d.fault_ack_i=0;d.probe_plane=d.probe_tile=0;for(unsigned i=0;i<16;++i)d.ref_rsp_pixels[i]=0;edge();d.reset=0;edge();}
 auto&r(){return *d.rootp;}
 std::array<uint32_t,16> storage(unsigned bank){std::array<uint32_t,16> a{};for(unsigned w=0;w<16;++w)a[w]=r().reconstruct_probe__DOT__owner_pixels[bank][w];return a;}
 std::array<uint32_t,16> engine_storage(){std::array<uint32_t,16> a{};for(unsigned w=0;w<16;++w)a[w]=r().reconstruct_probe__DOT__engine_out_pixels[w];return a;}
 unsigned owners(){return r().reconstruct_probe__DOT__owned_tiles;}
 Held output(){return {{d.out_epoch,d.out_fid,d.out_plane,d.out_tile,d.out_mode,d.out_index,d.out_value}};}
 void edge(){d.clk=0;d.eval();
  const unsigned lane0=r().reconstruct_probe__DOT__storage_copy_lane0,lane1=r().reconstruct_probe__DOT__storage_copy_lane1;
  const auto before0=storage(0),before1=storage(1),engine=engine_storage();
  const auto id=r().reconstruct_probe__DOT__engine_out_id;const auto err=r().reconstruct_probe__DOT__engine_out_error;
  need((lane0&lane1)==0&&(!lane0||!lane1),"copy wrote both banks");
  const unsigned lanes=lane0|lane1;
  need(!lanes||(lanes&(lanes-1))==0,"copy wrote more than one128-bit lane");
  d.clk=1;d.eval();d.clk=0;d.eval();++clocks;
  const auto after0=storage(0),after1=storage(1);
  for(unsigned w=0;w<16;++w){
   need(after0[w]==((lane0&(1U<<(w/4)))?engine[w]:before0[w]),"bank0 physical copy lane/value conservation");
   need(after1[w]==((lane1&(1U<<(w/4)))?engine[w]:before1[w]),"bank1 physical copy lane/value conservation");
  }
  if(lanes){++physical_copy_edges;physical_copy_bits+=128;for(unsigned n=0;n<4;++n)if(lanes&(1U<<n))++copy_lanes[n];}
  for(unsigned bank=0;bank<2;++bank)if((bank?lane1:lane0)&8U)
   need(r().reconstruct_probe__DOT__owner_math_id[bank]==id&&r().reconstruct_probe__DOT__owner_math_error[bank]==err,"last lane complete response metadata copy");
  need(clocks<20000000,"global reconstruction watchdog");
 }
 unsigned mode_for(unsigned id){unsigned p=plane_of(id),t=tile_of(id);return hidden(p,t)?1:!key&&t%5==0?0:2;}
 void begin(bool is_key,bool ref_valid=true,bool preserve_old_debt=false){if(physical&&!preserve_old_debt){need(!r().reconstruct_probe__DOT__running,"fixture drain while old logical frame active");++fixture_drains;drain();}need(!d.busy||physical.has_value(),"start with nonreference owner");key=is_key;++frame_epoch;++frame_id;++generation;emitted=next_lookup=input_index=next_token=0;blocks={};jobs.clear();mode_pending.reset();input_job.reset();held.reset();hold_output=hold_mode=hold_ref=pause_residual=false;pause_after=64;input_fault=ref_fault=mode_fault=-1;matching_ref_error=false;d.reset=d.cancel=0;d.start=1;d.input_done=0;d.in_valid=d.lookup_rsp=d.ref_rsp_valid=0;d.admitted_ready=1;d.epoch=frame_epoch;d.frame_fid=frame_id;d.key_frame=key;d.accepted_ref_valid=ref_valid;d.accepted_ref_fid=ref_id;d.accepted_ref_generation=generation;edge();d.start=0;frame_start=clocks;}
 void step(){
  d.clk=0;d.lookup_ready=no_stalls||rng()%4!=0;d.out_ready=!hold_output&&(no_stalls||rng()%5!=0);d.ref_req_ready=no_stalls||rng()%3!=0;
  const bool reply=mode_pending.has_value()&&!hold_mode;d.lookup_rsp=reply;Job reply_job;if(reply){reply_job=*mode_pending;d.lookup_mode=reply_job.mode;d.lookup_scale=reply_job.scale;if(mode_fault>=0){d.lookup_mode=unsigned(mode_fault);reply_job.mode=unsigned(mode_fault);mode_fault=-1;}}
  d.in_valid=input_job.has_value()&&!pause_residual&&input_index<pause_after&&(no_stalls||rng()%8!=0);bool altered=false;
  if(input_job){const Job&j=*input_job;unsigned p=plane_of(j.id),t=tile_of(j.id);d.in_epoch=frame_epoch;d.in_child_epoch=101+p;d.in_token=j.token;d.in_plane=p;d.in_qscale=j.scale;d.in_block=j.block;d.in_tile=t;d.in_qcell=oracle(p,t);d.in_index=input_index;d.in_value=uint32_t(residual(j.id,input_index))&0xffffffU;
   if(d.in_valid&&input_fault>=0){switch(input_fault){case 0:++d.in_epoch;break;case 1:d.in_child_epoch=0;break;case 2:d.in_token=0;break;case 3:d.in_plane=(p+1)%3;break;case 4:d.in_qscale=3;break;case 5:++d.in_block;break;case 6:++d.in_tile;break;case 7:++d.in_qcell;break;case 8:d.in_index=(input_index+1)&63;break;case 9:d.in_child_epoch=777;break;case 10:d.in_token=778;break;default:need(false,"bad input injection");}altered=true;}
  }
  bool send_ref=physical.has_value()&&!hold_ref&&physical->delay==0;bool bad_ref=false;d.ref_rsp_valid=send_ref;d.ref_rsp_error=send_ref&&matching_ref_error;
  if(send_ref){const PendingRef&p=*physical;d.ref_rsp_epoch=p.epoch;d.ref_rsp_fid=p.fid;d.ref_rsp_generation=p.generation;d.ref_rsp_plane=p.plane;d.ref_rsp_tile=p.tile;for(unsigned w=0;w<16;++w){uint32_t value=0;const unsigned id=(p.plane==0?0:p.plane==1?5400:6750)+p.tile;for(unsigned b=0;b<4;++b)value|=reference(id,w*4+b,p.generation)<<(8*b);d.ref_rsp_pixels[w]=value;}
   if(ref_fault>=0){switch(ref_fault){case 0:++d.ref_rsp_epoch;break;case 1:++d.ref_rsp_fid;break;case 2:d.ref_rsp_generation^=1ULL;break;case 3:d.ref_rsp_plane=(p.plane+1)%3;break;case 4:++d.ref_rsp_tile;break;default:need(false,"bad ref injection");}bad_ref=true;ref_fault=-1;}
  }
  d.eval();const bool take_in=d.in_valid&&d.in_ready,request=d.lookup_req&&d.lookup_ready,request_ref=d.ref_req_valid&&d.ref_req_ready,take_out=d.out_valid&&d.out_ready,take_ref=d.ref_rsp_valid&&d.ref_rsp_ready;
  if(trace&&diagnostics&&(previous_state!=d.state||request||request_ref||take_ref||(take_out&&d.out_index==0))){
   trace<<"{\"cycle\":"<<clocks<<",\"phase\":\""<<phase<<"\",\"state\":"<<unsigned(d.state)<<",\"running\":"<<unsigned(r().reconstruct_probe__DOT__running)<<",\"key\":"<<key<<",\"plane\":"<<unsigned(r().reconstruct_probe__DOT__plane)<<",\"tile\":"<<unsigned(r().reconstruct_probe__DOT__tile)<<",\"owners\":"<<owners()<<",\"tail\":"<<unsigned(r().reconstruct_probe__DOT__owner_tail)<<",\"head\":"<<unsigned(r().reconstruct_probe__DOT__owner_head)<<",\"lookup_req\":"<<unsigned(d.lookup_req)<<",\"lookup_rsp\":"<<reply<<",\"in_valid\":"<<unsigned(d.in_valid)<<",\"in_ready\":"<<unsigned(d.in_ready)<<",\"ref_req\":"<<request_ref<<",\"ref_rsp\":"<<take_ref<<",\"ref_pending\":"<<unsigned(d.ref_pending)<<",\"model_pending\":"<<physical.has_value()<<",\"hold_ref\":"<<hold_ref<<",\"discard_ref\":"<<unsigned(r().reconstruct_probe__DOT__discard_ref)<<",\"emitted\":"<<emitted<<",\"lookups\":"<<next_lookup<<",\"error\":"<<unsigned(d.error)<<"}\n";trace.flush();
  }
  previous_state=d.state;
  if(held){need(d.out_valid&&output()==*held,"held canonical tuple changed");++held_checks;}
  held=d.out_valid&&!d.out_ready?std::optional<Held>(output()):std::nullopt;
  if(take_in&&take_out)++overlap;
  if(take_out){unsigned ji=emitted/64,ix=emitted%64;need(ji<jobs.size(),"output without lookup owner");const Job&j=jobs[ji];unsigned p=plane_of(j.id),t=tile_of(j.id);need(d.out_epoch==frame_epoch&&d.out_fid==frame_id&&d.out_plane==p&&d.out_tile==t&&d.out_mode==j.mode&&d.out_index==ix,"canonical owner/order");int base=key?128:int(reference(j.id,ix,generation));int expected=j.mode==1?128:j.mode==0?base:std::clamp(base+residual(j.id,ix),0,255);need(d.out_value==unsigned(expected),"canonical clamp/value id="+std::to_string(j.id)+" ix="+std::to_string(ix));++emitted;++total_outputs;}
  std::optional<Job> new_mode;
  if(request){need(!mode_pending,"duplicate mode request");unsigned p=plane_of(next_lookup),t=tile_of(next_lookup);need(next_lookup<8100&&d.lookup_tile==next_lookup&&d.lookup_cell==oracle(p,t),"mode lookup coordinate/frontier");Job j{next_lookup,mode_for(next_lookup),oracle(p,t)%3,0,0};jobs.push_back(j);new_mode=j;++next_lookup;}
  std::optional<PendingRef> new_ref;
  if(request_ref){need(!physical,"second physical reference request");need(d.ref_req_epoch==frame_epoch&&d.ref_req_fid==ref_id&&d.ref_req_generation==generation,"reference snapshot lease");new_ref=PendingRef{d.ref_req_epoch,d.ref_req_fid,d.ref_req_generation,unsigned(d.ref_req_plane),unsigned(d.ref_req_tile),no_stalls?1U:2U+unsigned(rng()%6U)};}
  if(physical&&physical->delay) --physical->delay;
  edge();
  if(take_ref&&!bad_ref){physical.reset();matching_ref_error=false;}
  if(new_ref)physical=new_ref;
  if(reply){mode_pending.reset();if(reply_job.mode==2&&!d.error){unsigned p=plane_of(reply_job.id);reply_job.token=++next_token;reply_job.block=blocks[p];input_job=reply_job;input_index=0;} }
  if(new_mode)mode_pending=new_mode;
  if(take_in){++total_inputs;if(altered)input_fault=-1;if(++input_index==64){if(input_job)++blocks[plane_of(input_job->id)];input_job.reset();input_index=0;}}
  max_owners=std::max(max_owners,owners());need(owners()<=2,"more than two logical owners");if(owners()==2)++full_owner_cycles;
  need(d.fault_o==(d.error!=0),"same edge error/fault");
  if(d.error){held.reset();mode_pending.reset();input_job.reset();}
  need(bool(d.ref_pending)==physical.has_value(),"physical reference ledger divergence");
 }
 void until_state(unsigned state,unsigned cap=3000){for(unsigned n=0;n<cap;++n){if(d.state==state)return;step();need(!d.error,"unexpected fault reaching phase "+std::to_string(state));}need(false,"state watchdog target="+std::to_string(state)+" phase="+phase+" actual="+std::to_string(d.state)+" key="+std::to_string(key)+" lookup="+std::to_string(next_lookup)+" emitted="+std::to_string(emitted)+" owners="+std::to_string(owners())+" ref_pending="+std::to_string(d.ref_pending)+" model_ref="+std::to_string(physical.has_value())+" hold_ref="+std::to_string(hold_ref));}
 void prefix(unsigned tiles=4){for(unsigned n=0;n<10000&&emitted<tiles*64;++n){step();need(!d.error,"retry prefix fault");}need(emitted>=tiles*64,"prefix watchdog");}
 void finish(){for(unsigned n=0;n<2000000&&!d.done&&!d.error;++n){if(next_lookup==8100&&!input_job&&!mode_pending)d.input_done=1;step();}need(!d.error&&d.done&&!d.busy&&!d.ref_pending&&owners()==0,"full-frame completion/drain");need(emitted==518400&&d.count_outputs==emitted&&d.count_modes==8100,"full-grid counts");last_frame_cycles=clocks-frame_start;}
 void cancel(bool reset=false){d.in_valid=d.lookup_rsp=d.ref_rsp_valid=0;d.cancel=!reset;d.reset=reset;d.input_done=0;edge();d.cancel=d.reset=0;held.reset();mode_pending.reset();input_job.reset();need(!d.out_valid&&!d.done&&owners()==0,"cancel/reset retained logical tile");need(bool(d.ref_pending)==physical.has_value(),"cancel/reset forgot physical reference");}
 void drain(){hold_ref=false;for(unsigned n=0;n<100&&physical;++n)step();need(!physical&&!d.ref_pending,"reference drain watchdog");}
};
int main(int argc,char**argv){try{need(argc==3,"usage seed trace.jsonl");unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed);b.trace.open(argv[2]);need(bool(b.trace),"trace open");unsigned directed=0,full_frames=0;
 // Retained V103 4x8192 geometry domain, now on the actual new source adapter.
 b.d.reset=1;for(unsigned p=0;p<4;++p)for(unsigned t=0;t<8192;++t){b.d.probe_plane=p;b.d.probe_tile=t;b.d.eval();need(b.d.probe_cell==oracle(p,t),"exhaustive geometry mismatch");++b.geometry;}b.d.reset=0;
 b.no_stalls=true;b.begin(true);b.finish();const uint64_t key_cycles=b.last_frame_cycles;++full_frames;
 b.no_stalls=false;b.begin(false);b.finish();const uint64_t inter_cycles=b.last_frame_cycles;++full_frames;
 need(b.overlap>0&&b.max_owners==2&&b.held_checks>0,"overlap/held/bounded-owner coverage absent");
 b.diagnostics=true;
 for(bool reset:{false,true}){b.phase="full_owners_"+std::to_string(reset);b.begin(true);b.hold_output=true;for(unsigned n=0;n<1000;++n)b.step();need(b.owners()==2&&b.emitted==0&&!b.d.in_ready&&!b.d.lookup_req,"full owners did not backpressure third tile");b.cancel(reset);b.begin(true);b.prefix();b.cancel();++directed;}
 // An independent fixture must retire the prior canceled physical response
 // before it starts withholding a new fixture's response. This is a real drain,
 // not a cleared model/DUT owner. Warm-start debt tests below opt out explicitly.
 b.phase="fixture_reference_drain";b.begin(false);b.hold_ref=true;b.until_state(6);b.cancel();b.begin(true);need(!b.physical&&!b.d.ref_pending&&b.fixture_drains>0,"independent fixture failed to retire prior debt");b.prefix();b.cancel();++directed;
 // Kill at each of four physical beats of a second owner while an older
 // READY head stalls. Only the selected128-bit lane may change on kill; no
 // partially copied bank may publish. The per-edge512-bit ledger above checks
 // every byte, including unchanged lanes, in all normal and reset/cancel cases.
 for(unsigned beat=0;beat<4;++beat)for(bool reset:{false,true}){b.phase="private_copy_kill_"+std::to_string(beat)+"_"+std::to_string(reset);b.begin(true);b.hold_output=true;b.until_state(11);
  while(b.d.state==11)b.step();b.until_state(11);for(unsigned n=0;n<beat;++n)b.step();
  const unsigned head=b.r().reconstruct_probe__DOT__owner_head,tail=b.r().reconstruct_probe__DOT__owner_tail;
  need(head!=tail&&b.d.out_valid&&!b.d.out_ready&&b.r().reconstruct_probe__DOT__copy_beat==beat,"second COPY beat did not retain older stalled head");
  const auto saved_head=b.storage(head),before=b.storage(tail),engine=b.engine_storage();
  b.cancel(reset);need(b.storage(head)==saved_head,"kill COPY overwrote stalled head storage");
  const auto after=b.storage(tail);for(unsigned w=0;w<16;++w)need(after[w]==(w/4==beat?engine[w]:before[w]),"kill edge copied wrong128-bit lane");
  need(!b.d.out_valid&&b.owners()==0&&!b.d.done,"killed partial COPY published a logical owner");
  ++b.private_copy_cancel_cases;++directed;b.begin(true);b.prefix();b.cancel();
 }
 // Reset/cancel over all gather/memory/conversion/copy phases and stalled final byte.
 for(unsigned phase:{1U,2U,3U,4U,5U,6U,7U,8U,11U})for(bool reset:{false,true}){b.phase="cancel_phase_"+std::to_string(phase)+"_reset_"+std::to_string(reset);b.begin(phase!=5&&phase!=6);if(phase==3)b.hold_mode=true;if(phase==6)b.hold_ref=true;b.until_state(phase);if(phase==6)need(b.physical.has_value(),"reference pending phase absent");b.cancel(reset);if(b.physical){b.begin(true,true,true);b.hold_ref=true;for(unsigned n=0;n<8;++n){b.step();need(!b.d.lookup_req&&!b.d.out_valid,"new frame used old reference debt");}b.drain();}else b.begin(true);b.prefix();b.cancel();++directed;}
 b.phase="held_final_byte";b.begin(true);while(b.emitted<63)b.step();b.hold_output=true;for(unsigned n=0;n<30;++n)b.step();need(b.d.out_index==63&&!b.d.done,"held final byte fence");b.cancel();++directed;
 for(unsigned field=0;field<5;++field){b.phase="wrong_ref_"+std::to_string(field);b.begin(false);b.hold_ref=true;b.until_state(6);b.ref_fault=int(field);b.hold_ref=false;for(unsigned n=0;n<100&&!b.d.error;++n)b.step();need(b.d.error==3&&b.physical&&b.d.ref_pending&&!b.d.out_valid,"wrong reference ACK debt");b.drain();b.begin(false);b.prefix();b.cancel();++directed;}
 b.phase="matching_ref_error";b.begin(false);b.hold_ref=true;b.until_state(6);b.matching_ref_error=true;b.hold_ref=false;for(unsigned n=0;n<100&&!b.d.error;++n)b.step();need(b.d.error==3&&!b.physical&&!b.d.ref_pending,"matching reference error did not retire");b.diagnostics=false;b.begin(false);b.finish();b.diagnostics=true;++full_frames;++directed;
 for(unsigned field=0;field<11;++field){b.phase="input_corruption_"+std::to_string(field);b.begin(true);b.until_state(4);if(field>=9){while(b.input_index<7)b.step();}b.input_fault=int(field);for(unsigned n=0;n<100&&!b.d.error;++n)b.step();need(b.d.error==4&&!b.d.out_valid&&b.owners()==0,"residual tuple corruption escaped");b.begin(true);b.prefix();b.cancel();++directed;}
 // A malformed accepted word may be followed by two younger accepted
 // tuples before validation commits its fault. Those younger words must never
 // commit. This checks the declared acceptance/commit latency directly.
 for(unsigned index:{0U,7U,61U,63U}){b.phase="pipeline_ordered_fault_"+std::to_string(index);b.no_stalls=true;b.begin(true);b.until_state(4);
  while(b.input_index<index)b.step();const uint64_t before=b.d.count_residuals;
  const unsigned accepted_before=b.input_index;b.input_fault=0;unsigned steps=0;
  while(!b.d.error&&steps<8){b.step();++steps;}
  need(b.d.error==4&&steps==3,"owned residual validation fault did not commit at E+2");
  need(b.d.count_residuals==accepted_before,"malformed or younger residual committed");
  need(b.d.count_residuals>=before&&b.owners()==0&&!b.d.out_valid,"pipeline fault leaked a tile");
  ++b.pipeline_fault_cases;++directed;b.begin(true);b.prefix();b.cancel();
 }
 b.no_stalls=false;
 for(unsigned mode:{0U,1U,3U}){b.phase="bad_mode_"+std::to_string(mode);b.begin(true);b.mode_fault=int(mode);for(unsigned n=0;n<100&&!b.d.error;++n)b.step();need(b.d.error==1,"invalid key/hidden mode priority");b.cancel();++directed;}
 b.phase="missing_reference";b.begin(false,false);for(unsigned n=0;n<100&&!b.d.error;++n)b.step();need(b.d.error==2&&!b.physical,"missing reference lease");b.cancel();++directed;
 b.phase="partial_eof";b.begin(true);b.pause_after=7;b.until_state(4);for(unsigned n=0;n<200&&b.input_index<7;++n)b.step();need(b.input_index==7,"partial EOF setup");b.d.input_done=1;for(unsigned n=0;n<100;++n)b.step();need(!b.d.done&&b.owners()>0&&!b.d.error,"partial input falsely completed");b.cancel();b.begin(true);b.prefix();b.cancel();++directed;
 std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"geometry_cases\":"<<b.geometry<<",\"full_frames\":"<<full_frames<<",\"directed_checks\":"<<directed<<",\"canonical_bytes\":"<<b.total_outputs<<",\"residual_handshakes\":"<<b.total_inputs<<",\"fill_emit_overlap_edges\":"<<b.overlap<<",\"held_tuple_checks\":"<<b.held_checks<<",\"max_tile_owners\":"<<b.max_owners<<",\"full_owner_cycles\":"<<b.full_owner_cycles<<",\"fixture_reference_drains\":"<<b.fixture_drains<<",\"physical_copy_edges\":"<<b.physical_copy_edges<<",\"physical_copy_bits\":"<<b.physical_copy_bits<<",\"copy_lane0_edges\":"<<b.copy_lanes[0]<<",\"copy_lane1_edges\":"<<b.copy_lanes[1]<<",\"copy_lane2_edges\":"<<b.copy_lanes[2]<<",\"copy_lane3_edges\":"<<b.copy_lanes[3]<<",\"pipeline_fault_cases\":"<<b.pipeline_fault_cases<<",\"private_copy_cancel_cases\":"<<b.private_copy_cancel_cases<<",\"key_frame_cycles\":"<<key_cycles<<",\"inter_frame_cycles\":"<<inter_cycles<<",\"clock_edges\":"<<b.clocks<<"}\n";return 0;
}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}}
