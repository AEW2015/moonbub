#include "Vcs88_live_v91l.h"
#include "monitor.hpp"
#ifndef ROW_WRITES
#define ROW_WRITES 1
#endif
// Same full producer and C2/HUD oracles, separately compiled byte and row join.
static constexpr unsigned candidate_width=ROW_WRITES?8U:1U;
#include "verilated.h"
#include <string_view>
#include "../../../experiments/cu66-native-v69/hud.hpp"
#include "Vcs88_live_v91l___024root.h"
#include <deque>
#ifndef ELASTIC
#define ELASTIC 0
#endif
#ifndef REFILL_OVERLAP
#define REFILL_OVERLAP 1
#endif
#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <optional>
#include <random>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <utility>
#include <map>

static void need(bool test,const std::string &text){if(!test)throw std::runtime_error(text);}
static std::string quote(const std::string &s){std::string o="\"";for(char c:s){if(c=='"'||c=='\\')o+='\\';o+=c;}return o+'"';}
static std::vector<uint8_t> unhex(const std::string &s){
    if(s=="-")return {};
    need(s.size()%2==0,"odd hex");std::vector<uint8_t> r;
    for(size_t i=0;i<s.size();i+=2)r.push_back(uint8_t(std::stoul(s.substr(i,2),nullptr,16)));
    return r;
}
static uint64_t hash_byte(uint64_t h,uint8_t b){return (h^b)*1099511628211ULL;}
struct Case{
    std::string id;unsigned error=0;std::vector<uint8_t> packet,prior,scales,operations;
    unsigned ref_valid=0,qvalid=0;uint32_t ref_fid=0,cache_fid=0;uint64_t ref_gen=0,cache_gen=0;
    std::array<std::vector<uint8_t>,3> dense;
};
static std::vector<Case> load(const std::string &path){
    std::ifstream f(path);need(bool(f),"vectors missing");std::vector<Case> out;std::string line;
    while(std::getline(f,line)){if(line.empty())continue;std::istringstream in(line);Case c;std::string p,a,b,m,y,u,v;
        in>>c.id>>c.error>>p>>c.ref_valid>>c.ref_fid>>c.ref_gen>>c.qvalid>>c.cache_fid>>c.cache_gen>>a>>b>>m>>y>>u>>v;
        need(!in.fail(),"vector columns "+c.id);std::string extra;need(!(in>>extra),"extra vector column");
        c.packet=unhex(p);c.prior=unhex(a);c.scales=unhex(b);c.operations=unhex(m);c.dense={unhex(y),unhex(u),unhex(v)};
        if(c.error==0||c.error==147){need(c.operations.size()==8100&&c.scales.size()==1350,"missing mapping goldens");}
        out.push_back(std::move(c));}
    need(!out.empty(),"empty corpus");return out;
}

struct Golden {unsigned plane=0,block=0,tile=0,cell=0,scale=0;std::vector<uint8_t> coefficients,dequant,residual;};
static std::map<std::string,Golden> goldens;
static std::string tile_key(const std::string &id,unsigned p,unsigned b){return id+":"+std::to_string(p)+":"+std::to_string(b);}
static void load_tiles(const std::string &path){
    std::ifstream file(path);need(bool(file),"transform goldens missing");std::string line;
    while(std::getline(file,line)){if(line.empty())continue;std::istringstream row(line);std::string id,c,d,r;Golden g;
        row>>id>>g.plane>>g.block>>g.tile>>g.cell>>g.scale>>c>>d>>r;need(!row.fail(),"transform golden columns");
        g.coefficients=unhex(c);g.dequant=unhex(d);g.residual=unhex(r);need(g.coefficients.size()==128&&g.dequant.size()==256&&g.residual.size()==256,"transform golden widths");
        need(goldens.emplace(tile_key(id,g.plane,g.block),std::move(g)).second,"duplicate transform golden");}
}
static int signed32(const std::vector<uint8_t> &bytes,unsigned index){uint32_t word=0;for(unsigned j=0;j<4;++j)word|=uint32_t(bytes[4*index+j])<<(8*j);return int(int32_t(word));}
static int signed_bits(uint32_t word,unsigned width){const uint32_t mask=(uint32_t(1)<<width)-1;word&=mask;return word&(uint32_t(1)<<(width-1))?int(int64_t(word)-(int64_t(1)<<width)):int(word);}
template<class Wide>static int packed_signed(const Wide &bits,unsigned index,unsigned width){unsigned at=index*width,word=at/32,shift=at%32;uint64_t value=bits[word];if(shift+width>32)value|=uint64_t(bits[word+1])<<32;return signed_bits(uint32_t(value>>shift),width);}
template<class Wide>static bool has_ac(const Wide &bits){for(unsigned n=1;n<64;++n){if(packed_signed(bits,n,16)!=0)return true;}return false;}
static uint64_t mix32(uint64_t hash,int value){const auto word=uint32_t(int32_t(value));for(unsigned j=0;j<4;++j)hash=hash_byte(hash,uint8_t(word>>(8*j)));return hash;}


using Digest=std::array<uint8_t,32>;
using cu66::Bytes;using cu66::Patch;using cu66::View;
template<class W>static Digest get_digest(const W &p){Digest out{};for(unsigned i=0;i<32;++i)out[i]=uint8_t(p[(31-i)/4]>>((3-i%4)*8));return out;}
template<class W>static void set_digest(W &p,const Digest &v){for(unsigned i=0;i<8;++i)p[i]=0;for(unsigned i=0;i<32;++i)p[(31-i)/4]|=uint32_t(v[i])<<((3-i%4)*8);}
static Digest to_digest(const std::string &s){auto b=unhex(s);need(b.size()==32,"digest width");Digest d{};std::copy(b.begin(),b.end(),d.begin());return d;}
static uint64_t be64(const Bytes &b,unsigned at){uint64_t v=0;for(unsigned i=0;i<8;++i)v=v*256+b[at+i];return v;}
struct ValidationFixture {std::string id;Bytes packet,tiles,hud;Digest root,seal,hud_sha;};
static std::map<uint32_t,ValidationFixture> validation;
static void load_validation(const std::string &path){std::ifstream in(path);need(bool(in),"validation source");std::string l;
 while(std::getline(in,l)){std::istringstream row(l);std::array<std::string,10> c;for(auto &x:c)need(bool(std::getline(row,x,'\t')),"validation columns");if(c[0]=="id")continue;
  if(c[0]!="c0_f0"&&c[0]!="c0_f1")continue;
  ValidationFixture f{c[0],unhex(c[3]),unhex(c[4]),unhex(c[5]),to_digest(c[8]),to_digest(c[9]),to_digest(c[7])};
  uint32_t fid=0;for(unsigned i=8;i<12;++i)fid=fid*256+f.packet[i];need(validation.emplace(fid,std::move(f)).second,"validation duplicate");
 }need(validation.size()==2,"two original native chain fixtures");}

struct Tuple{
    unsigned plane=0,block=0,index=0,tile=0,cell=0,scale=0;uint32_t frame_epoch=0,child_epoch=0;int value=0;uint32_t token=0;
    bool operator==(const Tuple &b)const{return plane==b.plane&&block==b.block&&index==b.index&&tile==b.tile&&cell==b.cell&&scale==b.scale&&frame_epoch==b.frame_epoch&&child_epoch==b.child_epoch&&value==b.value&&token==b.token;}
};
struct Request{bool write=false;uint32_t addr=0,epoch=0;std::array<uint32_t,4> data{};bool operator==(const Request &b)const{return write==b.write&&addr==b.addr&&epoch==b.epoch&&data==b.data;}};
class Bench{
public:

    struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr;uint64_t value;unsigned bytes;
      bool operator==(const CandidateRequest &x)const{return epoch==x.epoch&&token==x.token&&bank==x.bank&&addr==x.addr&&value==x.value&&bytes==x.bytes;}};
    struct CandidatePending{CandidateRequest q;uint64_t due;};
    std::optional<CandidatePending> candidate_pending;std::optional<CandidateRequest> held_candidate;
    std::array<Bytes,3> candidate_memory{{Bytes(560640),Bytes(560640),Bytes(560640)}};
    std::vector<Patch> accepted_hud,provisional_patches;Bytes provisional_hud,accepted_qcache;
    Bytes actual_qcache;std::array<bool,1350> qcache_seen{};std::optional<unsigned> qcache_lookup;
    const ValidationFixture *vf=nullptr;size_t software_hud_pos=0;bool receipt_sent=false;
    uint64_t candidate_requests=0,candidate_acks=0,hash_deliveries=0,candidate_hash=0,commit_cycle=0;
    uint64_t first_outer=0,last_outer=0,first_write=0,last_write=0,first_token=0,last_token=0;
    uint64_t candidate_expanded_bytes=0,candidate_acked_bytes=0,service_data_edges=0,service_overhead_edges=0;
    uint64_t minimum_service=UINT64_MAX,maximum_service=0;
    std::array<std::vector<uint32_t>,3> candidate_ack_epoch{{std::vector<uint32_t>(560640),std::vector<uint32_t>(560640),std::vector<uint32_t>(560640)}};
    // Job tags are pinned to cs88_validate_publish_v91l's actual localparams.
    enum HashKind:unsigned {LEAF_JOB=0,EMPTY_LEAF_JOB=1,NODE_JOB=2,HUD_JOB=3,SEAL_JOB=4};
    uint64_t canonical_producer_bytes=0,canonical_request_bytes=0,canonical_ack_bytes=0,canonical_hash_bytes=0;
    uint64_t hud_request_bytes=0,hud_ack_bytes=0,hud_hash_bytes=0;
    uint64_t last_canonical_producer=0,last_canonical_ack=0,last_canonical_hash=0,reconstruct_done_fence=0;
    uint64_t root_complete=0,hud_complete=0,seal_complete=0,presentation_cycle=0;
    uint64_t last_hud_ack=0,last_hud_hash=0;
    std::array<uint64_t,5> hash_kind_counts{};
    std::array<uint64_t,9> phase_edges{};
    std::array<std::array<uint64_t,5>,9> phase_stalls{};
    std::array<uint64_t,4> slot_occupancy_edges{};
    uint64_t maximum_slots_owned=0,triple_phase_edges=0,triple_transfer_edges=0;
    uint64_t guard_private_residuals=0,guard_private_reads=0,guard_gap_edges=0,guard_checks=0;
    struct GuardRead {uint32_t addr,epoch;uint8_t data;bool private_gap;};
    std::optional<GuardRead> guard_raw_read;
    uint64_t guard_raw_reads=0,guard_raw_responses=0,guard_revoked_responses=0,guard_gap_read_responses=0;
    bool guard_gap_open=false;
    void parent_guard_observe(){
        const auto &r=*d.rootp;
        const bool enabled=r.cs88_live_v91l__DOT__parent_transfer_enable;
        const bool fault=r.cs88_live_v91l__DOT__fault_cancel;
        const bool registered=r.cs88_live_v91l__DOT__producer_fault_cancel;
        const bool external=d.power_on_reset||d.reset||d.abort_packet;
        const bool raw_valid=r.cs88_live_v91l__DOT__producer_residual_valid;
        const bool raw_read=r.cs88_live_v91l__DOT__producer_frame_read_req;
        const bool raw_take=raw_valid&&d.residual_ready;
        ++guard_checks;
        // Raw synchronous-RAM lease is independent of the masked public view.
        // Never drop its response because the parent fault/reset is asserted:
        // the preedge response from the previous accepted edge is still real.
        if(guard_raw_read){
            const auto lease=*guard_raw_read;
            need(d.frame_read_rsp&&d.frame_rsp_addr==lease.addr&&d.frame_rsp_epoch==lease.epoch&&d.frame_read_data==lease.data,"raw replay next-edge whole response lease");
            ++guard_raw_responses;
            if(!enabled)++guard_revoked_responses;
            if(lease.private_gap)++guard_gap_read_responses;
            guard_raw_read.reset();
        }else need(!d.frame_read_rsp,"raw replay unsolicited response without accepted lease");
        if(raw_read){
            need(active&&d.frame_read_addr<received.size(),"raw replay accepted address lacks actual received byte");
            guard_raw_read=GuardRead{d.frame_read_addr,frame_epoch,received[d.frame_read_addr],!enabled};
            ++guard_raw_reads;
        }
        need(guard_raw_reads==guard_raw_responses+unsigned(bool(guard_raw_read)),"raw replay accepted/response/owned conservation");
        if(enabled){
            need(bool(d.residual_valid)==raw_valid&&bool(d.frame_read_req)==raw_read,"enabled parent observation changed actual local traffic");
            guard_gap_open=false;
        }else{
            need(!d.residual_valid&&!d.frame_read_req,"revoked parent observation exposed local traffic");
            need(!d.in_ready&&!d.cache_ready&&!d.mem_req_valid&&!d.ref_req_valid,"parent observation guard hid external request eligibility");
            if(fault)need(!d.candidate_req_valid&&!d.join_output_valid&&!d.software_hud_ready&&!d.start_ready,"parent fault exposed write/hash/HUD/start grant");
            const bool first_gap=fault&&!registered&&!external;
            if(first_gap){
                need(!guard_gap_open,"parent fault delayed registered producer cancellation beyond one edge");
                guard_gap_open=true;++guard_gap_edges;
            }
            if(raw_take||raw_read)need(first_gap,"raw producer work survived registered or external cancellation");
            if(registered||external)need(!raw_valid&&!raw_read,"registered producer cancel left raw local offer");
            if(raw_take){
                need(active&&monitor_active,"private cancel-gap residual lacks live owner");
                const Tuple t=tuple();need(t.plane<3,"private cancel-gap residual plane");
                const auto &g=golden(t.plane,t.block);
                need(t.plane==residual_plane&&t.block==residual_counts[t.plane]/64&&t.index==residual_counts[t.plane]%64,"private cancel-gap residual ordering");
                need(t.tile==g.tile&&t.cell==g.cell&&t.scale==g.scale&&t.frame_epoch==frame_epoch&&t.child_epoch==child_for_plane(t.plane)&&t.token!=0,"private cancel-gap residual whole owner");
                need(t.value==signed32(g.residual,t.index),"private cancel-gap residual independent golden");
                if(t.index!=0)need(t.token==residual_token,"private cancel-gap residual token owner");
                ++guard_private_residuals;
            }
            if(raw_read){
                need(active&&d.frame_read_addr<received.size(),"private cancel-gap replay lacks admitted byte");
                ++guard_private_reads;
            }
        }
    }
    bool instrument_started=false;
    uint64_t spatial_inverse_inputs=0,spatial_inverse_run=0,spatial_inverse_max_run=0;
    uint64_t spatial_fill_emit=0,spatial_cross_tile=0,spatial_fill_held_head=0;

    bool hold_candidate=false,wrong_ack=false,bus_error=false,hold_presentation=false,hold_scanout=false;
    bool bad_root=false,bad_generation=false,bad_hud_index=false,bad_hud_last=false,extra_hud=false;
    std::optional<CandidateRequest> held_delivery;
    std::ofstream hash_events;
    CandidateRequest candidate_request()const{return {d.candidate_req_epoch,d.candidate_req_token,unsigned(d.candidate_req_bank),unsigned(d.candidate_req_addr),uint64_t(d.candidate_req_data),unsigned(d.candidate_req_bytes)};}
    void cold_live(){need(!pending&&!reference_pending&&!candidate_pending,"cold reset external owner");monitor_active=false;vf=nullptr;d.software_hud_valid=0;d.software_receipt_valid=0;
      d.power_on_reset=1;tick();d.power_on_reset=0;tick();accepted_hud.clear();accepted_qcache.clear();need(!d.v_accepted_valid&&!d.v_front_valid&&d.start_ready,"cold live baseline");}
    void stage_live(const Case &c){
      uint32_t fid=be32(c.packet,8);vf=&validation.at(fid);
      need(std::equal(vf->root.begin(),vf->root.end(),c.packet.begin()+52)&&std::equal(vf->seal.begin(),vf->seal.end(),c.packet.begin()+84),"live BR88 encoding changed original commitments");
      const unsigned off=128+be32(c.packet,36)+be32(c.packet,40)+be32(c.packet,48),n=be32(c.packet,44);
      Bytes payload(c.packet.begin()+off,c.packet.begin()+off+n);
      const auto &orig=vf->packet;const unsigned origoff=128+be32(orig,36)+be32(orig,40)+be32(orig,48),orign=be32(orig,44);
      need(n==orign&&std::equal(payload.begin(),payload.end(),orig.begin()+origoff),"live HUD body vs original CS88");
      provisional_patches=cu66::decode_hud(View(payload),c.packet[5]?nullptr:&accepted_hud,fid,be32(c.packet,12));
      provisional_hud.clear();for(const auto &p:provisional_patches){auto raw=cu66::word_bytes(p.words);provisional_hud.insert(provisional_hud.end(),raw.begin(),raw.end());}
      need(provisional_hud==vf->hud&&cu66::sha256(provisional_hud)==vf->hud_sha,"real HUD decode vs independent fixture");
      if(!c.packet[5])need(c.prior==accepted_qcache&&d.v_accepted_valid&&c.ref_fid==d.v_accepted_fid&&c.ref_gen==d.v_accepted_generation,"delta prior qcache/reference not actual accepted history");
      actual_qcache.assign(1350,0xff);qcache_seen.fill(false);qcache_lookup.reset();
      software_hud_pos=0;receipt_sent=false;candidate_requests=candidate_acks=hash_deliveries=commit_cycle=first_outer=last_outer=first_write=last_write=first_token=last_token=0;
      candidate_hash=1469598103934665603ULL;
      candidate_expanded_bytes=candidate_acked_bytes=service_data_edges=service_overhead_edges=0;
      minimum_service=UINT64_MAX;maximum_service=0;
      for(auto &bank:candidate_ack_epoch)std::fill(bank.begin(),bank.end(),0U);
      canonical_producer_bytes=canonical_request_bytes=canonical_ack_bytes=canonical_hash_bytes=0;
      hud_request_bytes=hud_ack_bytes=hud_hash_bytes=0;
      last_canonical_producer=last_canonical_ack=last_canonical_hash=reconstruct_done_fence=0;
      root_complete=hud_complete=seal_complete=presentation_cycle=last_hud_ack=last_hud_hash=0;
      hash_kind_counts.fill(0);phase_edges.fill(0);slot_occupancy_edges.fill(0);
      for(auto &phase:phase_stalls)phase.fill(0);
      maximum_slots_owned=triple_phase_edges=triple_transfer_edges=0;instrument_started=false;latency_monitor={};
      spatial_inverse_inputs=spatial_inverse_run=spatial_inverse_max_run=0;
      spatial_fill_emit=spatial_cross_tile=spatial_fill_held_head=0;

      d.validation_start_fid=fid;d.validation_start_refid=be32(c.packet,12);d.validation_start_generation=be64(c.packet,16)+(bad_generation?1:0);d.validation_start_key=c.packet[5];
      Digest root=vf->root;if(bad_root)root[0]^=1;set_digest(d.validation_expected_root,root);set_digest(d.validation_expected_seal,vf->seal);set_digest(d.software_hud_sha,vf->hud_sha);
      d.software_decoded_verified=1;
    }
    void live_before_eval(){
      d.candidate_req_ready=!candidate_pending&&(profile==0||random(4)!=0);
      d.candidate_rsp_valid=candidate_pending&&cycle>=candidate_pending->due&&!hold_candidate;
      if(candidate_pending){const auto &q=candidate_pending->q;d.candidate_rsp_epoch=q.epoch;d.candidate_rsp_token=q.token^(wrong_ack?1U:0U);d.candidate_rsp_bank=q.bank;d.candidate_rsp_addr=q.addr;d.candidate_rsp_error=bus_error;}
      d.software_hud_valid=vf&&(software_hud_pos<provisional_hud.size()||extra_hud);d.software_hud_data=software_hud_pos<provisional_hud.size()?provisional_hud[software_hud_pos]:0;
      d.software_hud_index=unsigned(software_hud_pos)+(bad_hud_index?1:0);d.software_hud_last=(software_hud_pos+1==42240)^(bad_hud_last&&software_hud_pos==17);
      d.software_receipt_valid=vf&&!receipt_sent;d.present_vblank=!hold_presentation;d.present_drained=!hold_scanout;
    }
    v129_observe::Monitor latency_monitor;
    void observe_fences(bool kill){
      if(d.start&&d.start_ready)instrument_started=true;
      if(!instrument_started||kill)return;
#if ELASTIC
      if(!commit_cycle) {
        const auto& m=*d.rootp;
        v129_observe::Sample s;
        s.coefficient={bool(d.coefficient_valid),bool(d.coefficient_ready)};
        s.inverse={bool(m.cs88_live_v91l__DOT__producer__DOT__staged_valid),bool(m.cs88_live_v91l__DOT__producer__DOT__staged_ready)};
        s.residual={bool(d.residual_valid),bool(d.residual_ready)};
        s.canonical={bool(d.out_valid),bool(d.out_ready)};
        s.hash={bool(d.join_output_valid),bool(d.join_output_ready)};
        s.request={bool(d.candidate_req_valid),bool(d.candidate_req_ready)};
        s.response={bool(d.candidate_rsp_valid),bool(d.candidate_rsp_ready)};
        s.pending_ack=bool(candidate_pending);
        latency_monitor.sample(s);
      }
#endif
      // Phase accounting uses priority in this exact order, not disjoint
      // hardware operation: HUD writes can overlap root computation.
      const unsigned phase=canonical_producer_bytes<518400?0U:canonical_hash_bytes<518400?1U:
        !root_complete?2U:hud_hash_bytes<42240?3U:!hud_complete?4U:!seal_complete?5U:!commit_cycle?6U:!presentation_cycle?7U:8U;
      ++phase_edges[phase];
      phase_stalls[phase][0]+=d.out_valid&&!d.out_ready;
      phase_stalls[phase][1]+=d.software_hud_valid&&!d.software_hud_ready;
      phase_stalls[phase][2]+=d.candidate_req_valid&&!d.candidate_req_ready;
      phase_stalls[phase][3]+=d.join_output_valid&&!d.join_output_ready;
      phase_stalls[phase][4]+=candidate_pending&&cycle<candidate_pending->due;
      need(d.join_slots_owned<=(ROW_WRITES?3U:1U),"reported bounded join slot occupancy");
      ++slot_occupancy_edges[d.join_slots_owned];maximum_slots_owned=std::max(maximum_slots_owned,uint64_t(d.join_slots_owned));
      triple_phase_edges+=d.join_phase_fill&&d.join_phase_wait&&d.join_phase_hash;
      triple_transfer_edges+=d.out_valid&&d.out_ready&&candidate_pending&&d.join_output_valid&&d.join_output_ready;
      if(d.out_valid&&d.out_ready){
        need(++canonical_producer_bytes<=518400,"count every canonical producer acceptance, independent of tile address order");
        if(canonical_producer_bytes==518400)last_canonical_producer=cycle+1;
      }
      if(d.v_hash_result){
        need(d.v_hash_job_kind<=SEAL_JOB,"actual validator hash job kind");
        ++hash_kind_counts[d.v_hash_job_kind];
        if(d.v_hash_job_kind==NODE_JOB&&d.v_hash_job_node==1){need(!root_complete,"one actual Merkle root completion");root_complete=cycle+1;}
        if(d.v_hash_job_kind==HUD_JOB){need(d.v_hash_job_node==0&&!hud_complete,"one actual HUD hash completion");hud_complete=cycle+1;}
        if(d.v_hash_job_kind==SEAL_JOB){need(d.v_hash_job_node==0&&!seal_complete,"one actual frame seal completion");seal_complete=cycle+1;}
      }
    }
    void report_fences(){
#if ELASTIC
      latency_monitor.report(std::cout,seed,profile,frame_epoch);
#endif
      need(canonical_producer_bytes==518400&&canonical_request_bytes==518400&&canonical_ack_bytes==518400&&canonical_hash_bytes==518400,"all canonical accepted/requested/successfully ACKed/hashed bytes");
      need(hud_request_bytes==42240&&hud_ack_bytes==42240&&hud_hash_bytes==42240,"all HUD requested/successfully ACKed/hashed bytes");
      need(last_canonical_producer&&last_canonical_ack&&last_canonical_hash&&reconstruct_done_fence&&root_complete&&hud_complete&&seal_complete&&commit_cycle&&presentation_cycle,"every actual completion fence observed");
      need(last_canonical_producer<=last_canonical_ack&&last_canonical_ack<=last_canonical_hash&&last_canonical_hash<=root_complete,"canonical byte/ACK/hash/root causal order");
      need(last_canonical_producer<=reconstruct_done_fence&&reconstruct_done_fence<=commit_cycle,"reconstruct completion before validated commit");
      need(last_hud_ack<=last_hud_hash&&last_hud_hash<=hud_complete,"HUD successful ACK/hash/digest causal order");
      need(root_complete<hud_complete&&hud_complete<seal_complete&&seal_complete<commit_cycle&&commit_cycle<presentation_cycle,"actual validator job and publication ordering");
      need(hash_kind_counts==std::array<uint64_t,5>{{508,4,511,1,1}},"actual complete validator hash job-kind counts");
      std::cout<<"{\"type\":\"live_fences\",\"status\":\"TEST_PASS\",\"cycle_convention\":\"accepted rising edge; preedge handshakes cycle+1\",\"canonical_producer_bytes\":"<<canonical_producer_bytes
        <<",\"canonical_request_bytes\":"<<canonical_request_bytes<<",\"canonical_successful_ack_bytes\":"<<canonical_ack_bytes<<",\"canonical_hash_bytes\":"<<canonical_hash_bytes
        <<",\"hud_request_bytes\":"<<hud_request_bytes<<",\"hud_successful_ack_bytes\":"<<hud_ack_bytes<<",\"hud_hash_bytes\":"<<hud_hash_bytes
        <<",\"last_canonical_producer_accept\":"<<last_canonical_producer<<",\"last_canonical_successful_ack\":"<<last_canonical_ack<<",\"last_canonical_hash_delivery\":"<<last_canonical_hash
        <<",\"reconstruct_done\":"<<reconstruct_done_fence<<",\"root_complete\":"<<root_complete<<",\"last_hud_successful_ack\":"<<last_hud_ack<<",\"last_hud_hash_delivery\":"<<last_hud_hash
        <<",\"hud_hash_complete\":"<<hud_complete<<",\"seal_complete\":"<<seal_complete<<",\"commit\":"<<commit_cycle<<",\"presentation\":"<<presentation_cycle
        <<",\"maximum_slots_owned\":"<<maximum_slots_owned<<",\"triple_phase_edges\":"<<triple_phase_edges<<",\"triple_transfer_edges\":"<<triple_transfer_edges<<",\"hash_kind_counts\":[";
      for(unsigned n=0;n<5;++n){if(n)std::cout<<',';std::cout<<hash_kind_counts[n];}
      std::cout<<"],\"slot_occupancy_edges\":[";for(unsigned n=0;n<4;++n){if(n)std::cout<<',';std::cout<<slot_occupancy_edges[n];}
      std::cout<<"],\"phase_order\":[\"canonical_input\",\"canonical_drain\",\"root\",\"HUD_delivery\",\"HUD_digest\",\"seal\",\"commit\",\"presentation\",\"terminal\"],\"phase_edges\":[";
      for(unsigned n=0;n<9;++n){if(n)std::cout<<',';std::cout<<phase_edges[n];}
      std::cout<<"],\"stall_order\":[\"producer\",\"software_HUD\",\"physical_request\",\"hash_delivery\",\"physical_service\"],\"phase_stalls\":[";
      for(unsigned p=0;p<9;++p){if(p)std::cout<<',';std::cout<<'[';for(unsigned n=0;n<5;++n){if(n)std::cout<<',';std::cout<<phase_stalls[p][n];}std::cout<<']';}
      std::cout<<"],\"stalled_profile_comparability\":\"same bounded service rule and seed; different RNG draw counts and accepted traffic prevent identical cycle-trace comparison\",\"physical_SDRAM\":false}\n";
    }
    void live_observe(){
      const bool kill=d.power_on_reset||d.reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;
      observe_fences(kill);
      if(kill)qcache_lookup.reset();
      if(!kill&&d.reconstruct_lookup_rsp){need(qcache_lookup.has_value(),"qcache response owner");unsigned cell=*qcache_lookup;need(cell<1350&&d.reconstruct_lookup_scale==active->scales[cell],"actual registered qcache value");actual_qcache[cell]=d.reconstruct_lookup_scale;qcache_seen[cell]=true;qcache_lookup.reset();}
      if(!kill&&d.reconstruct_lookup_req&&d.reconstruct_lookup_ready){need(!qcache_lookup,"qcache lookup owner bound");qcache_lookup=d.reconstruct_lookup_cell;}
      if(d.software_receipt_valid&&d.software_receipt_ready)receipt_sent=true;
      if(d.software_hud_valid&&d.software_hud_ready)++software_hud_pos;
      if(kill||d.join_error)held_candidate.reset();
      if(held_candidate)need(d.candidate_req_valid&&candidate_request()==*held_candidate,"held candidate write tuple changed");
      held_candidate=d.candidate_req_valid&&!d.candidate_req_ready?std::optional<CandidateRequest>(candidate_request()):std::nullopt;
      if(d.join_output_valid&&d.join_output_ready){
        need(vf&&d.join_output_addr<candidate_memory[d.v_write_bank].size(),"hash delivery bounds");
        need(candidate_memory[d.v_write_bank][d.join_output_addr]==d.join_output_data,"hash delivery before actual ACK-committed write");
        need(candidate_ack_epoch[d.v_write_bank][d.join_output_addr]==frame_epoch,"hash byte lacks successful matching ACK in current owner epoch");
        if(!d.join_output_hud){
          need(d.join_output_addr<518400&&++canonical_hash_bytes<=518400,"count every canonical hash byte");
          if(canonical_hash_bytes==518400)last_canonical_hash=cycle+1;
        }else{
          need(d.join_output_addr>=518400&&++hud_hash_bytes<=42240,"count every HUD hash byte");
          if(hud_hash_bytes==42240)last_hud_hash=cycle+1;
        }
        ++hash_deliveries;
      }
      if(d.candidate_rsp_valid&&d.candidate_rsp_ready&&!wrong_ack){need(bool(candidate_pending),"candidate ACK owner");auto q=candidate_pending->q;
        if(!bus_error)for(unsigned n=0;n<q.bytes;++n){
          candidate_memory[q.bank][q.addr+n]=uint8_t(q.value>>(8U*n));
          candidate_ack_epoch[q.bank][q.addr+n]=q.epoch;
          ++candidate_acked_bytes;
          if(q.addr+n<518400){need(++canonical_ack_bytes<=518400,"count every successful canonical ACK byte");if(canonical_ack_bytes==518400)last_canonical_ack=cycle+1;}
          else{need(++hud_ack_bytes<=42240,"count every successful HUD ACK byte");if(hud_ack_bytes==42240)last_hud_ack=cycle+1;}
        }
        candidate_pending.reset();++candidate_acks;last_write=cycle+1;
      }
      if(d.candidate_req_valid&&d.candidate_req_ready){need(!candidate_pending&&vf&&d.v_bank_active&&!kill,"candidate write lease");auto q=candidate_request();
        need(q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.addr<560640,"candidate request owner/bounds");
        need(q.bytes==candidate_width&&q.addr+q.bytes<=560640&&(!ROW_WRITES||(q.addr&7U)==0),"normalized bounded candidate row descriptor");
        need((!d.v_reference_bank_valid||q.bank!=d.v_reference_bank)&&(!d.v_front_valid||q.bank!=d.v_front_bank)&&(!d.v_pending_valid||q.bank!=d.v_pending_bank),"candidate write aliases immutable bank");
        if(!ROW_WRITES){
          uint8_t expected=q.addr<518400?canonical_golden().expected[q.addr]:provisional_hud[q.addr-518400];need(q.value==expected,"physical write byte vs actual independent expected");
        }
        for(unsigned n=0;n<q.bytes;++n){
          const unsigned address=q.addr+n;
          uint8_t expected=address<518400?canonical_golden().expected[address]:provisional_hud[address-518400];
          need(uint8_t(q.value>>(8U*n))==expected,"expanded physical request byte vs independent canonical/HUD oracle");
          need(candidate_ack_epoch[q.bank][address]!=q.epoch,"candidate byte rewritten in one frame owner");
          if(address<518400)++canonical_request_bytes;else ++hud_request_bytes;
        }
        candidate_expanded_bytes+=q.bytes;
        for(uint32_t x:{q.epoch,q.token,uint32_t(q.bank),uint32_t(q.addr)})for(unsigned k=0;k<4;++k)candidate_hash=hash_byte(candidate_hash,uint8_t(x>>(8*k)));
        for(unsigned n=0;n<q.bytes;++n)candidate_hash=hash_byte(candidate_hash,uint8_t(q.value>>(8U*n)));
        if(!first_write){first_write=cycle+1;first_token=q.token;}last_token=q.token;
        // A single physical lease bounds the abstract service queue. One 8B
        // request consumes four 16-bit data edges plus explicit overhead.
        const uint64_t data_edges=(q.bytes+1U)/2U;
        const uint64_t overhead=profile?8U+random(9):2U;
        const uint64_t service=data_edges+overhead;
        service_data_edges+=data_edges;service_overhead_edges+=overhead;
        minimum_service=std::min(minimum_service,service);maximum_service=std::max(maximum_service,service);
        candidate_pending=CandidatePending{q,cycle+service};++candidate_requests;
      }
      if(d.v_hash_result&&record){hash_events<<"{\"type\":\"hash\",\"id\":\""<<vf->id<<"\",\"pipeline_id\":\""<<active->id<<"\",\"profile\":"<<profile<<",\"epoch\":"<<frame_epoch<<",\"kind\":"<<unsigned(d.v_hash_job_kind)<<",\"node\":"<<d.v_hash_job_node<<",\"digest\":\""<<cu66::hex(get_digest(d.v_hash_digest))<<"\",\"cycle\":"<<(cycle+1)<<"}\n";}
    }
    void live_after_edge(){
      if(instrument_started&&vf){
        if(canonical_producer_bytes==518400&&d.reconstruct_done&&!reconstruct_done_fence)reconstruct_done_fence=cycle;
        if(d.v_frame_presented&&d.v_front_fid==be32(vf->packet,8))presentation_cycle=cycle;
      }

      if(d.v_frame_committed){need(!candidate_pending&&d.join_drained&&candidate_requests==candidate_acks&&hash_deliveries==560640,"commit before all actual write/hash fences");
        need(vf&&d.v_accepted_fid==be32(vf->packet,8)&&get_digest(d.v_accepted_root)==vf->root&&get_digest(d.v_accepted_hud)==vf->hud_sha&&get_digest(d.v_accepted_seal)==vf->seal,"accepted atomic commitments");
        auto &mem=candidate_memory[d.v_reference_bank];need(std::equal(mem.begin(),mem.begin()+518400,canonical_golden().expected.begin())&&std::equal(mem.begin()+518400,mem.end(),provisional_hud.begin()),"actual accepted candidate memory");commit_cycle=cycle;
      }
    }
    void drain_live(){d.in_valid=0;d.in_last=0;wrong_ack=false;bus_error=false;hold_candidate=false;
      for(unsigned n=0;n<200000&&!d.start_ready;++n){tick();}need(d.start_ready&&!candidate_pending&&!pending&&!reference_pending&&!d.v_bank_active,"live failed transaction drain: ps="+std::to_string(d.frame_state)+" vs="+std::to_string(d.v_state)+" js="+std::to_string(d.join_state)+" pe="+std::to_string(d.error)+" ve="+std::to_string(d.v_error)+" je="+std::to_string(d.join_error)+" pending="+std::to_string(bool(candidate_pending))+" flags="+std::to_string(bad_generation)+std::to_string(bad_root)+std::to_string(bad_hud_index)+std::to_string(bad_hud_last)+std::to_string(extra_hud));}
    void nominal(const Case &c,unsigned p){prepare(c,p,true);stage_live(c);preload(c);begin(c);
      d.validation_start_fid^=0x100;d.validation_start_generation^=0x100; // Accepted transaction must ignore changed hints.
      feed_until();finish(c);for(unsigned n=0;n<20000000&&!commit_cycle&&!d.v_error&&!d.join_error;++n)tick();
      need(commit_cycle&&!d.v_error&&!d.join_error&&d.v_hash_jobs==1025&&d.v_pixel_bytes==518400&&d.v_hud_bytes==42240,"live validated commit");
      if(!ROW_WRITES){
      need(d.join_inputs==560640&&d.join_requests==560640&&d.join_acks==560640&&d.join_outputs==560640,"live write/hash conservation");
      }else need(d.join_inputs==560640&&d.join_requests==70080&&d.join_acks==70080&&d.join_outputs==560640,"row physical requests/ACKs and original expanded-byte conservation");
      need(candidate_expanded_bytes==560640&&candidate_acked_bytes==560640,"all original bytes independently expanded and ACK committed");
      need(std::all_of(qcache_seen.begin(),qcache_seen.end(),[](bool x){return x;})&&actual_qcache==c.scales,"actual qcache registered coverage");
      accepted_hud=provisional_patches;accepted_qcache=actual_qcache;
      std::cout<<"{\"type\":\"live_case\",\"id\":\""<<vf->id<<"\",\"pipeline_id\":\""<<c.id<<"\",\"profile\":"<<profile<<",\"seed\":"<<seed<<",\"epoch\":"<<frame_epoch<<",\"fid\":"<<d.v_accepted_fid<<",\"generation\":"<<d.v_accepted_generation<<",\"canonical_bytes\":"<<d.v_pixel_bytes<<",\"hud_bytes\":"<<d.v_hud_bytes<<",\"hash_jobs\":"<<d.v_hash_jobs<<",\"hash_message_bytes\":"<<d.v_hash_message_bytes<<",\"hash_blocks\":"<<d.v_hash_blocks<<",\"write_requests\":"<<candidate_requests<<",\"write_acks\":"<<candidate_acks<<",\"hash_deliveries\":"<<hash_deliveries<<",\"write_descriptor_fnv\":"<<candidate_hash<<",\"first_token\":"<<first_token<<",\"last_token\":"<<last_token<<",\"first_outer_cycle\":"<<first_outer<<",\"last_outer_cycle\":"<<last_outer<<",\"start_cycle\":"<<begin_cycle<<",\"commit_cycle\":"<<commit_cycle<<",\"start_to_commit_cycles\":"<<commit_cycle-begin_cycle<<",\"first_outer_to_commit_cycles\":"<<commit_cycle-first_outer<<",\"last_outer_to_commit_cycles\":"<<commit_cycle-last_outer<<",\"qcache_preload_cycles\":"<<cache_cycles<<",\"qcache_bytes\":"<<cache_bytes<<",\"reference_requests\":"<<observed_ref_requests<<",\"accepted_bank\":"<<unsigned(d.v_reference_bank)<<",\"root\":\""<<cu66::hex(get_digest(d.v_accepted_root))<<"\",\"hud_sha256\":\""<<cu66::hex(get_digest(d.v_accepted_hud))<<"\",\"seal\":\""<<cu66::hex(get_digest(d.v_accepted_seal))<<"\",\"status\":\"PASS\"}\n";
      static const char hx[]="0123456789abcdef";actual_output<<"accepted_"<<c.id<<'\t'<<profile<<'\t';for(uint8_t b:candidate_memory[d.v_reference_bank])actual_output<<hx[b>>4]<<hx[b&15];actual_output<<'\n';
      actual_output<<"qcache_"<<c.id<<'\t'<<profile<<'\t';for(uint8_t b:accepted_qcache)actual_output<<hx[b>>4]<<hx[b&15];actual_output<<'\n';
      need(spatial_inverse_inputs==d.inverse_count_inputs&&spatial_inverse_max_run>=64,"actual staged inverse II1 acceptance and counter binding");
      need(spatial_fill_emit>0&&spatial_cross_tile>0,"actual different-tile residual fill and canonical emission overlap");
      std::cout<<"{\"type\":\"live_spatial_pipeline\",\"status\":\"TEST_PASS\",\"inverse_accepted_inputs\":"<<spatial_inverse_inputs
        <<",\"maximum_consecutive_inverse_accepts\":"<<spatial_inverse_max_run<<",\"residual_canonical_overlap_edges\":"<<spatial_fill_emit
        <<",\"different_tile_overlap_edges\":"<<spatial_cross_tile<<",\"residual_fill_while_head_held_edges\":"<<spatial_fill_held_head
        <<",\"cycle_skipping\":false,\"hardware\":false}\n";
      record=false;tick();report_fences();
    }

    Vcs88_live_v91l d;std::mt19937 rng;uint64_t cycle=0;unsigned seed,profile=0;
    std::array<uint8_t,262144> ram{};std::array<uint32_t,16384> line_epoch{};
    struct Pending{Request req;uint64_t due;};std::optional<Pending> pending;std::optional<Request> held_request;std::optional<Tuple> held_output,held_coefficient;
    struct Read{uint32_t addr,epoch;uint8_t data;};std::optional<Read> local_read;
    std::ofstream trace,actual_output;
    struct Canonical {std::vector<uint8_t> reference,expected;};
    std::map<std::string,Canonical> canonical;
    std::vector<uint8_t> actual_pixels;
    struct ReferenceRequest {uint32_t epoch,fid;uint64_t generation;unsigned plane,tile;
        bool operator==(const ReferenceRequest &b)const{return epoch==b.epoch&&fid==b.fid&&generation==b.generation&&plane==b.plane&&tile==b.tile;}};
    struct PendingReference {ReferenceRequest req;uint64_t due;};
    std::optional<PendingReference> reference_pending;
    std::optional<ReferenceRequest> held_reference;
    std::optional<std::array<uint32_t,8>> held_canonical;
    bool hold_reference_response=false,corrupt_reference_tag=false,reference_bus_error=false;
    uint64_t canonical_samples=0,canonical_comparisons=0,canonical_tiles=0,canonical_first=0,canonical_last=0,canonical_hash=0;
    uint64_t observed_ref_requests=0,observed_ref_acks=0,canonical_done_cycle=0;
    unsigned canonical_plane=0,canonical_tile=0,canonical_index=0;
    unsigned observed_copy=0,observed_const=0,observed_residual_tiles=0;

    const Case *active=nullptr;bool monitor_active=false,record=false,force_stall=false,hold_response=false,force_output_hold=false;
    uint32_t next_epoch=0,frame_epoch=0;uint64_t begin_cycle=0,cache_cycles=0,cache_bytes=0;
    uint64_t inputs=0,coefficients=0,requests=0,acks=0,refill_observed=0,first_input=0,last_input=0,first_coef=0,last_coef=0,done_cycle=0;
    uint64_t queue_req_observed=0,queue_rsp_observed=0,queue_pop_observed=0,queue_stall_observed=0;
    unsigned queue_count_observed=0,queue_owned_observed=0;
    uint64_t assemble_during_math=0;
    uint64_t residual_comparisons=0,dq_comparisons=0,assembly_comparisons=0;
    uint64_t residuals=0,dq_tiles=0,launches=0,residual_tiles=0,last_residual=0,coefficient_done_cycle=0,residual_hash=0,residual_first=0;
    unsigned residual_index=0,residual_plane=0;uint32_t residual_token=0;std::array<unsigned,3> residual_counts{};Tuple residual_metadata{};
    uint64_t dense_comparisons=0,directed_comparisons=0,tiles=0,tile_hash=1469598103934665603ULL,tile_first=0;
    std::array<unsigned,3> observed_blocks{},observed_coefficients{};std::vector<uint32_t> child_epochs;
    std::vector<uint8_t> received;std::array<std::vector<unsigned>,3> positions;
    std::array<uint32_t,3> span_offset{},span_length{};
    unsigned output_plane=0;std::optional<std::pair<unsigned,unsigned>> held_input;
    std::deque<Tuple> elastic_queue;
    uint64_t elastic_up=0,elastic_down=0,elastic_discard=0,inverse_input_model=0;
    uint64_t elastic_total_up=0,elastic_total_down=0,elastic_total_discard=0,elastic_fence_checks=0,elastic_hold_checks=0;
    bool elastic_fence_seen=false;
#if ELASTIC
    Tuple staged_tuple()const{const auto&r=*d.rootp;return {
        unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_plane),unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_block),
        unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_index),unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_tile),
        unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_qcell),unsigned(r.cs88_live_v91l__DOT__producer__DOT__staged_qscale),
        r.cs88_live_v91l__DOT__producer__DOT__staged_epoch,r.cs88_live_v91l__DOT__producer__DOT__staged_child_epoch,
        int(int16_t(r.cs88_live_v91l__DOT__producer__DOT__staged_value))};}
    void elastic_pre(){
        const auto&r=*d.rootp;
        const bool kill=d.reset||d.power_on_reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start||r.cs88_live_v91l__DOT__producer__DOT__coefficient_stage_cancel;
        const bool full=r.cs88_live_v91l__DOT__producer__DOT__coefficient_boundary__DOT__full;
        const bool valid=r.cs88_live_v91l__DOT__producer__DOT__staged_valid,ready=r.cs88_live_v91l__DOT__producer__DOT__staged_ready;
        if(record&&monitor_active&&!kill){
            if(valid&&ready){++spatial_inverse_inputs;++spatial_inverse_run;spatial_inverse_max_run=std::max(spatial_inverse_max_run,spatial_inverse_run);}
            else spatial_inverse_run=0;
        }else spatial_inverse_run=0;
        need(full==!elastic_queue.empty()&&elastic_queue.size()<=1,"independent staged occupancy/owner bound");
        need(bool(r.cs88_live_v91l__DOT__producer__DOT__coefficient_stage_occupied)==(full||bool(r.cs88_live_v91l__DOT__producer__DOT__coefficient_boundary__DOT__final_wait)),"stage occupied binding");
        if(d.reset||d.power_on_reset||r.cs88_live_v91l__DOT__producer__DOT__accepted_start)inverse_input_model=0;
        if(kill){
            need(!valid&&!d.coefficient_ready&&!r.cs88_live_v91l__DOT__producer__DOT__staged_done,"stage flush leaked valid/ready/done");
            elastic_discard+=elastic_queue.size();elastic_total_discard+=elastic_queue.size();elastic_queue.clear();elastic_fence_seen=false;
        }else{
            need(bool(r.cs88_live_v91l__DOT__producer__DOT__staged_done)==(elastic_fence_seen&&elastic_queue.empty()),"registered done fence ordering");
            if(r.cs88_live_v91l__DOT__producer__DOT__staged_done){need(d.coefficient_done&&!valid&&!full,"done overtook raw completion/queued token");++elastic_fence_checks;}
            need(!r.cs88_live_v91l__DOT__producer__DOT__coefficient_boundary__DOT__final_wait,"real sticky producer done preceded its final acceptance");
            if(valid){need(!elastic_queue.empty()&&staged_tuple()==elastic_queue.front(),"full coefficient ownership tuple changed/reordered");if(!ready)++elastic_hold_checks;}
            if(valid&&ready){elastic_queue.pop_front();++elastic_down;++elastic_total_down;++inverse_input_model;}
            if(d.coefficient_valid&&d.coefficient_ready){elastic_queue.push_back(coefficient_tuple());++elastic_up;++elastic_total_up;}
            if(d.coefficient_done)elastic_fence_seen=true;
        }
        need(elastic_up==elastic_down+elastic_discard+elastic_queue.size(),"up/down/discard accepted-token conservation");
    }
    void elastic_post(){const auto&r=*d.rootp;
        need(bool(r.cs88_live_v91l__DOT__producer__DOT__coefficient_boundary__DOT__full)==!elastic_queue.empty(),"registered slot owner after edge");
        need(d.inverse_count_inputs==inverse_input_model,"independent inverse accepted staged input counter");}
#endif
    explicit Bench(unsigned s,const std::string &path,const std::string &goldens_path,const std::string &actual_path):rng(s),seed(s),trace(path),actual_output(actual_path){
        std::ifstream gf(goldens_path);need(bool(gf)&&bool(actual_output),"canonical artifact open");std::string line;
        while(std::getline(gf,line)){if(line.empty())continue;std::istringstream row(line);std::string id,ref,pixels;row>>id>>ref>>pixels;need(!row.fail(),"canonical golden columns");
            auto a=unhex(ref),b=unhex(pixels);need((a.empty()||a.size()==518400)&&b.size()==518400,"canonical golden lengths");canonical.emplace(id,Canonical{std::move(a),std::move(b)});}

        need(bool(trace),"tile trace open");ram.fill(0xa5);line_epoch.fill(0xffffffffU);
        d.clk=0;d.reset=1;d.start=0;d.abort_packet=0;d.packet_bytes=0;d.epoch=0;
        d.serial_clear=0;d.write_overlap=1;d.read_prefetch=1;d.tile_overlap=1;
        d.in_valid=0;d.in_last=0;d.in_data=0;/* out_ready is driven by the unchanged ACK-coupled join. */
        d.cache_valid=0;d.cache_last=0;d.cache_data=0;d.cache_ref_fid=0;d.cache_ref_generation=0;
        d.accepted_ref_valid=0;d.accepted_qcache_valid=0;d.accepted_ref_fid=0;d.accepted_ref_generation=0;
        d.ref_req_ready=0;d.ref_rsp_valid=0;d.ref_rsp_epoch=0;d.ref_rsp_fid=0;d.ref_rsp_generation=0;d.ref_rsp_plane=0;d.ref_rsp_tile=0;d.ref_rsp_error=0;
        for(unsigned k=0;k<16;++k)d.ref_rsp_pixels[k]=0;
        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;
        for(unsigned k=0;k<4;++k)d.mem_rsp_data[k]=0;
        d.power_on_reset=1;d.software_hud_valid=0;d.software_receipt_valid=0;d.candidate_rsp_valid=0;d.candidate_req_ready=0;d.present_vblank=1;d.present_drained=1;
        tick();d.power_on_reset=0;d.reset=0;tick();
    }
    unsigned random(unsigned n){return rng()%n;}
    Tuple coefficient_tuple()const{return {unsigned(d.coefficient_plane),unsigned(d.coefficient_block),unsigned(d.coefficient_index),unsigned(d.coefficient_tile),unsigned(d.coefficient_qcell),unsigned(d.coefficient_qscale),d.coefficient_epoch,d.current_child_epoch,int(int16_t(d.coefficient_value))};}
    Tuple tuple()const{return {unsigned(d.residual_plane),unsigned(d.residual_block),unsigned(d.residual_index),unsigned(d.residual_tile),unsigned(d.residual_qcell),unsigned(d.residual_qscale),d.residual_epoch,d.residual_child_epoch,signed_bits(d.residual_value,24),d.residual_token};}
    Request request()const{Request q;q.write=d.mem_req_write;q.addr=d.mem_req_addr;q.epoch=d.mem_req_epoch;for(unsigned k=0;k<4;++k)q.data[k]=d.mem_req_data[k];return q;}
    void observe_coefficient(){
        need(active!=nullptr,"output without active frame");const Tuple t=coefficient_tuple();need(t.plane<3&&t.index<64&&t.plane==output_plane,"tuple range/global plane order");
        const unsigned ordinal=observed_coefficients[t.plane]/64,index=observed_coefficients[t.plane]%64;
        need(ordinal<positions[t.plane].size(),"too many coefficient blocks");
        const unsigned tile=positions[t.plane][ordinal],qcell=t.plane?tile:(tile/90/2)*45+(tile%90/2);
        need(t.block==ordinal&&t.index==index&&t.tile==tile&&t.cell==qcell&&t.scale==active->scales[qcell],"coefficient positional/scale tuple mismatch "+active->id);
        need(t.frame_epoch==frame_epoch&&t.child_epoch!=0,"tuple epoch mismatch");
        const auto &gold=active->dense[t.plane];const size_t at=2*observed_coefficients[t.plane];
        need(at+2<=gold.size(),"missing coefficient golden");const int expected=int(int16_t(unsigned(gold[at])|(unsigned(gold[at+1])<<8)));
        need(t.value==expected,"coefficient value mismatch "+active->id);
        if(index==0){tile_hash=1469598103934665603ULL;tile_first=cycle+1;}
        const uint16_t bits=uint16_t(int16_t(t.value));tile_hash=hash_byte(hash_byte(tile_hash,uint8_t(bits)),uint8_t(bits>>8));
        ++observed_coefficients[t.plane];++coefficients;if(record)++dense_comparisons;else ++directed_comparisons;if(first_coef==0)first_coef=cycle+1;last_coef=cycle+1;
        if(index==63){++observed_blocks[t.plane];if(record)++tiles;
            if(ordinal+1==positions[t.plane].size()){
                ++output_plane;while(output_plane<3&&positions[output_plane].empty())++output_plane;
            }

        }
    }

    const Golden &golden(unsigned plane,unsigned block)const {need(active!=nullptr,"transform without active case");auto it=goldens.find(tile_key(active->id,plane,block));need(it!=goldens.end(),"missing transform golden "+active->id);return it->second;}
    void event(const std::string &stage,const Tuple &t,uint32_t token,uint64_t hash,unsigned samples,uint64_t first,uint64_t last,bool complete=true){
        if(record)trace<<"{\"type\":\"transform\",\"stage\":"<<quote(stage)<<",\"id\":"<<quote(active->id)<<",\"memory_profile\":"<<profile<<",\"plane\":"<<t.plane<<",\"block\":"<<t.block<<",\"tile\":"<<t.tile<<",\"qcell\":"<<t.cell<<",\"qscale\":"<<t.scale<<",\"frame_epoch\":"<<t.frame_epoch<<",\"child_epoch\":"<<t.child_epoch<<",\"token\":"<<token<<",\"value_hash\":"<<hash<<",\"samples\":"<<samples<<",\"first_cycle\":"<<first<<",\"last_cycle\":"<<last<<",\"complete\":"<<(complete?"true":"false")<<"}\n";
    }
    uint32_t child_for_plane(unsigned plane)const{unsigned ordinal=0;for(unsigned p=0;p<plane;++p)if(span_length[p])++ordinal;need(ordinal<child_epochs.size(),"missing child epoch owner");return child_epochs[ordinal];}
    Tuple debug_tuple()const{return {unsigned(d.inverse_plane),unsigned(d.inverse_block),0,unsigned(d.inverse_tile),unsigned(d.inverse_qcell),unsigned(d.inverse_qscale),d.inverse_epoch,d.inverse_child_epoch,0};}
    void observe_transform_stage(bool dequant){
        const Tuple t=debug_tuple();const auto &g=golden(t.plane,t.block);
        need(t.tile==g.tile&&t.cell==g.cell&&t.scale==g.scale&&t.frame_epoch==frame_epoch&&t.child_epoch==child_for_plane(t.plane)&&d.inverse_token!=0,"inverse stage metadata mismatch");
        uint64_t hash=1469598103934665603ULL;
        for(unsigned i=0;i<64;++i){const int actual=dequant?packed_signed(d.inverse_dequantized,i,20):packed_signed(d.inverse_coefficients,i,16);
            const int expected=dequant?signed32(g.dequant,i):int(int16_t(unsigned(g.coefficients[2*i])|(unsigned(g.coefficients[2*i+1])<<8)));
            need(actual==expected,"assembled/dequant exact mismatch "+active->id);
            if(dequant){hash=mix32(hash,actual);if(record)++dq_comparisons;}else{const uint16_t bits=uint16_t(int16_t(actual));hash=hash_byte(hash_byte(hash,uint8_t(bits)),uint8_t(bits>>8));if(record)++assembly_comparisons;}}
        if(dequant)++dq_tiles;else ++launches;
        event(dequant?"dequant":"assemble",t,d.inverse_token,hash,64,cycle+1,cycle+1);
    }
    void observe_residual(){
        const Tuple t=tuple();const auto &g=golden(t.plane,t.block);
        need(t.plane<3&&t.plane==residual_plane&&t.block==residual_counts[t.plane]/64&&t.index==residual_counts[t.plane]%64,"residual ordering");
        need(t.tile==g.tile&&t.cell==g.cell&&t.scale==g.scale&&t.frame_epoch==frame_epoch&&t.child_epoch==child_for_plane(t.plane)&&t.token!=0,"residual metadata mismatch");
        need(t.value==signed32(g.residual,t.index),"residual value mismatch "+active->id);
        if(t.index==0){residual_hash=1469598103934665603ULL;residual_first=cycle+1;residual_metadata=t;residual_token=d.residual_token;}
        need(t.token==residual_token,"residual token changed within tile");
        residual_hash=mix32(residual_hash,t.value);++residuals;if(record)++residual_comparisons;++residual_counts[t.plane];residual_index=t.index+1;last_residual=cycle+1;
        if(t.index==63){++residual_tiles;event("residual",t,d.residual_token,residual_hash,64,residual_first,cycle+1);residual_index=0;
            if(residual_counts[t.plane]/64==positions[t.plane].size()){++residual_plane;while(residual_plane<3&&positions[residual_plane].empty())++residual_plane;}}
    }
    const Canonical &canonical_golden()const{need(active,"canonical without case");auto id=active->id=="actual_001_bad_third_inner_crc"?std::string("actual_001"):active->id;auto it=canonical.find(id);need(it!=canonical.end(),"missing canonical golden "+id);return it->second;}
    static unsigned pixel_address(unsigned plane,unsigned tile,unsigned index){unsigned w=plane?360:720,bw=plane?45:90,base=plane==0?0:plane==1?345600:432000;
        return base+(tile/bw*8+index/8)*w+tile%bw*8+index%8;}
    std::array<uint32_t,8> canonical_tuple()const{return {d.out_epoch,d.out_fid,d.out_plane,d.out_tile,d.out_index,d.out_value,d.out_mode,0};}
    ReferenceRequest reference_request()const{return {d.ref_req_epoch,d.ref_req_fid,d.ref_req_generation,unsigned(d.ref_req_plane),unsigned(d.ref_req_tile)};}
    void observe_canonical(){
        need(active&&canonical_plane<3,"canonical without active frame/range");
        need(d.out_epoch==frame_epoch&&d.out_fid==be32(active->packet,8)&&d.out_plane==canonical_plane&&d.out_tile==canonical_tile&&d.out_index==canonical_index,"canonical output order/identity");
        unsigned base=canonical_plane==0?0:canonical_plane==1?5400:6750;
        need(d.out_mode==active->operations[base+canonical_tile],"canonical admitted mode");
        const auto &g=canonical_golden();unsigned addr=pixel_address(canonical_plane,canonical_tile,canonical_index);
        need(d.out_value==g.expected[addr],"canonical exact pixel mismatch "+active->id+" at "+std::to_string(addr)+" observed "+std::to_string(d.out_value)+" expected "+std::to_string(g.expected[addr]));
        actual_pixels[addr]=d.out_value;if(record)++canonical_comparisons;
        if(canonical_index==0){canonical_hash=1469598103934665603ULL;canonical_first=cycle+1;
            if(d.out_mode==0)++observed_copy;else if(d.out_mode==1)++observed_const;else ++observed_residual_tiles;}
        canonical_hash=hash_byte(canonical_hash,d.out_value);++canonical_samples;canonical_last=cycle+1;
        if(canonical_index==63){++canonical_tiles;
            if(record)trace<<"{\"type\":\"canonical\",\"id\":"<<quote(active->id)<<",\"memory_profile\":"<<profile<<",\"plane\":"<<canonical_plane<<",\"tile\":"<<canonical_tile<<",\"mode\":"<<unsigned(d.out_mode)<<",\"frame_epoch\":"<<frame_epoch<<",\"fid\":"<<d.out_fid<<",\"value_hash\":"<<canonical_hash<<",\"samples\":64,\"first_cycle\":"<<canonical_first<<",\"last_cycle\":"<<canonical_last<<",\"complete\":true}\n";
            canonical_index=0;++canonical_tile;if(canonical_tile==(canonical_plane?1350U:5400U)){canonical_tile=0;++canonical_plane;}
        }else ++canonical_index;
    }
    void tick(){
        d.clk=0;live_before_eval();
        d.mem_req_ready=!pending&&!force_stall&&(profile==0||random(4)!=0);
        d.mem_rsp_valid=pending&&cycle>=pending->due&&!hold_response;
        if(d.mem_rsp_valid){d.mem_rsp_epoch=pending->req.epoch;d.mem_rsp_error=0;for(unsigned k=0;k<4;++k){
            uint32_t value=0;for(unsigned j=0;j<4;++j)value|=uint32_t(ram[pending->req.addr+4*k+j])<<(8*j);d.mem_rsp_data[k]=value;}}
        d.ref_req_ready=!reference_pending&&(profile==0||random(4)!=0);
        d.ref_rsp_valid=reference_pending&&cycle>=reference_pending->due&&!hold_reference_response;
        if(d.ref_rsp_valid){const auto &r=reference_pending->req;d.ref_rsp_epoch=r.epoch^(corrupt_reference_tag?1U:0U);d.ref_rsp_fid=r.fid;d.ref_rsp_generation=r.generation;d.ref_rsp_plane=r.plane;d.ref_rsp_tile=r.tile;d.ref_rsp_error=reference_bus_error;
            need(d.v_reference_bank_valid,"reference has no actual validated bank");const auto &bank_pixels=candidate_memory[d.v_reference_bank];need(bank_pixels.size()==560640,"actual candidate bank size");const std::basic_string_view<uint8_t> pixels(bank_pixels.data(),518400);need(pixels.size()==518400,"reference bytes unavailable");
            for(unsigned n=0;n<64;++n)need(pixels[pixel_address(r.plane,r.tile,n)]==canonical_golden().reference[pixel_address(r.plane,r.tile,n)],"actual accepted reference differs from independent golden");
            for(unsigned k=0;k<16;++k){uint32_t word=0;for(unsigned j=0;j<4;++j)word|=uint32_t(pixels[pixel_address(r.plane,r.tile,4*k+j)])<<(8*j);d.ref_rsp_pixels[k]=word;}}
        d.eval();parent_guard_observe();live_observe();const bool cancel=d.reset||d.power_on_reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;
#if ELASTIC
        elastic_pre();
#endif
        need(unsigned(d.queue_count)+unsigned(d.queue_pending)<=2,"refill owner bound");
        if(REFILL_OVERLAP==0)need(d.queue_count==0&&!d.queue_pending&&d.queue_requests==0,"disabled queue not static zero");
        if(record&&monitor_active&&!cancel&&!d.error&&!d.stage_cancel&&d.residual_valid&&d.residual_ready){
            if(d.out_valid&&d.out_ready){
                ++spatial_fill_emit;
                if(d.residual_plane!=d.out_plane||d.residual_tile!=d.out_tile)++spatial_cross_tile;
            }
            if(d.out_valid&&!d.out_ready)++spatial_fill_held_head;
        }
        if(cancel||d.error!=0||d.stage_cancel){held_request.reset();held_output.reset();held_coefficient.reset();held_canonical.reset();held_reference.reset();}
        if(REFILL_OVERLAP!=0&&monitor_active&&!cancel){
            if(d.frame_read_req)++queue_req_observed;
            if(d.frame_read_rsp)++queue_rsp_observed;
            if(d.stage_write)++queue_pop_observed;
            if(d.queue_stall)++queue_stall_observed;
            need(bool(d.queue_push)==bool(d.frame_read_rsp),"queue response push conservation");
            need(bool(d.queue_pop)==bool(d.stage_write),"queue pop/child write conservation");
        }
        if(cancel)held_input.reset();
        if(held_input)need(d.in_valid&&std::make_pair(unsigned(d.in_data),unsigned(d.in_last))==*held_input,"held outer input changed");
        held_input=d.in_valid&&!d.in_ready&&!cancel?std::optional<std::pair<unsigned,unsigned>>(std::make_pair(unsigned(d.in_data),unsigned(d.in_last))):std::nullopt;
        if(held_request)need(d.mem_req_valid&&request()==*held_request,"held memory offer changed");
        if(held_output)need(d.residual_valid&&tuple()==*held_output,"held coefficient tuple changed");
        held_request=d.mem_req_valid&&!d.mem_req_ready?std::optional<Request>(request()):std::nullopt;
        held_output=d.residual_valid&&!d.residual_ready?std::optional<Tuple>(tuple()):std::nullopt;
        if(cancel){local_read.reset();need(!d.residual_valid&&!d.frame_read_req,"cancel leaked local traffic");}
        else {
            if(local_read){need(d.frame_read_rsp&&d.frame_rsp_addr==local_read->addr&&d.frame_rsp_epoch==local_read->epoch&&d.frame_read_data==local_read->data,"outer synchronous replay response binding");local_read.reset();}
            else need(!d.frame_read_rsp,"unsolicited outer replay response");
            if(d.frame_read_req){need(d.frame_read_addr<received.size(),"outer replay reads unavailable byte");local_read=Read{d.frame_read_addr,frame_epoch,received[d.frame_read_addr]};}
        }
        if(d.in_valid&&d.in_ready){if(!first_outer)first_outer=cycle+1;last_outer=cycle+1;received.push_back(d.in_data);++inputs;if(first_input==0)first_input=cycle+1;last_input=cycle+1;}
        if(d.stage_write){++refill_observed;need(monitor_active&&active!=nullptr&&d.coefficient_plane<3,"child input without frame");const unsigned p=d.coefficient_plane,at=d.stage_write_addr;
            need(at<span_length[p]&&span_offset[p]+at<active->packet.size(),"child refill span range");need(d.stage_write_data==active->packet[span_offset[p]+at],"child refill byte provenance");}
        if(monitor_active&&d.core_starts>child_epochs.size()){
            need(d.core_starts==child_epochs.size()+1,"child start conservation");
            if(!child_epochs.empty())need(d.current_child_epoch>child_epochs.back(),"nonmonotonic cross-plane child epoch");
            child_epochs.push_back(d.current_child_epoch);
        }
        if(d.coefficient_valid&&d.coefficient_ready){need(monitor_active,"coefficient outside current frame");observe_coefficient();if(d.inverse_math_state!=0)++assemble_during_math;}
        if(d.inverse_launch)observe_transform_stage(false);
        if(d.inverse_dequant)observe_transform_stage(true);
        if(d.residual_valid&&d.residual_ready){need(monitor_active,"residual outside current frame");observe_residual();}
        if(held_canonical)need(d.out_valid&&canonical_tuple()==*held_canonical,"held canonical output changed");
        held_canonical=d.out_valid&&!d.out_ready?std::optional<std::array<uint32_t,8>>(canonical_tuple()):std::nullopt;
        if(d.out_valid&&d.out_ready){need(monitor_active,"canonical outside current frame");observe_canonical();}
        if(held_reference)need(d.ref_req_valid&&reference_request()==*held_reference,"held reference offer changed");
        held_reference=d.ref_req_valid&&!d.ref_req_ready?std::optional<ReferenceRequest>(reference_request()):std::nullopt;
        if(d.ref_rsp_valid&&d.ref_rsp_ready&&!corrupt_reference_tag){need(reference_pending.has_value(),"reference ACK without owner");reference_pending.reset();++observed_ref_acks;}
        if(d.ref_req_valid&&d.ref_req_ready){need(!reference_pending,"multiple reference owners");const auto r=reference_request();
            need(active&&r.epoch==frame_epoch&&r.fid==active->ref_fid&&r.generation==active->ref_gen&&r.plane<3&&r.tile<(r.plane?1350U:5400U),"reference descriptor snapshot mismatch");
            unsigned base=r.plane==0?0:r.plane==1?5400:6750;need(active->packet[5]==0&&active->operations[base+r.tile]!=1,"reference read on key/hidden");
            reference_pending=PendingReference{r,cycle+(profile==0?8:12+random(13))};++observed_ref_requests;
            if(record)trace<<"{\"type\":\"reference_request\",\"id\":"<<quote(active->id)<<",\"memory_profile\":"<<profile<<",\"frame_epoch\":"<<r.epoch<<",\"fid\":"<<r.fid<<",\"generation\":"<<r.generation<<",\"plane\":"<<r.plane<<",\"tile\":"<<r.tile<<",\"cycle\":"<<cycle+1<<"}\n";}

        need(d.inverse_owned_banks<=2&&d.inverse_max_owned_banks<=2,"inverse owner bound");
        if(held_coefficient)need(d.coefficient_valid&&coefficient_tuple()==*held_coefficient,"held coefficient changed at inverse boundary");
        held_coefficient=d.coefficient_valid&&!d.coefficient_ready?std::optional<Tuple>(coefficient_tuple()):std::nullopt;
        const bool response=d.mem_rsp_valid&&d.mem_rsp_ready;
        if(response){need(pending.has_value(),"response without accepted owner");const auto &q=pending->req;
            if(q.write){for(unsigned k=0;k<4;++k)for(unsigned j=0;j<4;++j)ram[q.addr+4*k+j]=uint8_t(q.data[k]>>(8*j));line_epoch[q.addr/16]=q.epoch;}
            else need(line_epoch[q.addr/16]==q.epoch,"read before matching epoch physical write ACK");
            pending.reset();++acks;
        }
        if(d.mem_req_valid&&d.mem_req_ready){need(!pending,"multiple accepted external requests");const Request q=request();need(q.addr%16==0&&q.addr+16<=ram.size(),"external memory request bounds");
            pending=Pending{q,cycle+(profile==0?1:(q.write?16:18)+unsigned(((q.addr>>4)^seed)&3))};++requests;}
        d.clk=1;d.eval();++cycle;live_after_edge();
#if ELASTIC
        elastic_post();
#endif
        if(REFILL_OVERLAP!=0&&monitor_active&&!cancel){
            queue_count_observed=std::max(queue_count_observed,unsigned(d.queue_count));
            queue_owned_observed=std::max(queue_owned_observed,unsigned(d.queue_count)+unsigned(d.queue_pending));
        }
        if(monitor_active&&d.done&&done_cycle==0)done_cycle=cycle;
        if(monitor_active&&d.coefficient_done&&coefficient_done_cycle==0)coefficient_done_cycle=cycle;
    }
    static uint32_t be32(const std::vector<uint8_t> &b,unsigned n){return uint32_t(b[n])<<24|uint32_t(b[n+1])<<16|uint32_t(b[n+2])<<8|uint32_t(b[n+3]);}
    void prepare(const Case &c,unsigned p,bool emit){
        need(!pending&&!reference_pending&&!d.busy&&d.start_ready,"prepare with outstanding ownership");active=&c;profile=p;record=emit;monitor_active=false;held_input.reset();
        need(elastic_queue.empty(),"prepare retained staged owner");elastic_up=elastic_down=elastic_discard=0;
        canonical_samples=canonical_tiles=canonical_first=canonical_last=canonical_hash=canonical_done_cycle=0;observed_ref_requests=observed_ref_acks=0;
        canonical_plane=canonical_tile=canonical_index=observed_copy=observed_const=observed_residual_tiles=0;
        actual_pixels.assign(518400,0x55);held_canonical.reset();held_reference.reset();
        assemble_during_math=0;residuals=0;dq_tiles=0;launches=0;residual_tiles=0;last_residual=0;coefficient_done_cycle=0;residual_index=0;residual_plane=0;residual_counts.fill(0);
        inputs=0;coefficients=0;requests=0;acks=0;refill_observed=0;first_input=last_input=first_coef=last_coef=done_cycle=0;cache_cycles=cache_bytes=0;
        queue_req_observed=queue_rsp_observed=queue_pop_observed=queue_stall_observed=0;
        queue_count_observed=queue_owned_observed=0;
        observed_blocks.fill(0);observed_coefficients.fill(0);received.clear();child_epochs.clear();local_read.reset();held_output.reset();held_request.reset();held_coefficient.reset();
        for(auto &v:positions)v.clear();
        if(c.operations.size()==8100){for(unsigned axis=0,base=0;axis<3;++axis){unsigned n=axis?1350:5400;for(unsigned t=0;t<n;++t)if(c.operations[base+t]==2)positions[axis].push_back(t);base+=n;}}
        output_plane=0;while(output_plane<3&&positions[output_plane].empty())++output_plane;
        span_offset.fill(0);span_length.fill(0);
        if(c.packet.size()>=132){unsigned cursor=128+be32(c.packet,36)+be32(c.packet,40),end=cursor+be32(c.packet,48);
            for(unsigned axis=0;axis<3&&cursor+4<=end;++axis){unsigned chunks=be32(c.packet,cursor);cursor+=4;if(chunks==1&&cursor+8<=end){span_length[axis]=be32(c.packet,cursor+4);cursor+=8;span_offset[axis]=cursor;cursor+=span_length[axis];}}}
    }
    void preload(const Case &c){
        if(!c.qvalid)return;
        need(c.prior.size()==1350,"prior qcache length");const uint64_t before=cycle;
        d.cache_ref_fid=c.cache_fid;d.cache_ref_generation=c.cache_gen;
        for(unsigned i=0;i<1350;++i){d.cache_valid=1;d.cache_data=accepted_qcache[i];d.cache_last=i==1349;
            need(d.cache_ready,"qcache preload unexpectedly blocked");tick();++cache_bytes;
            // Start's snapshot uses the tag latched at the first cache byte.
            if(i==0){d.cache_ref_fid=~c.cache_fid;d.cache_ref_generation=~c.cache_gen;}
        }
        d.cache_valid=0;d.cache_last=0;cache_cycles=cycle-before;
        const bool invalid=std::find(c.prior.begin(),c.prior.end(),uint8_t(3))!=c.prior.end();
        need(bool(d.cache_complete)==!invalid,"cache completion/invalid-value eligibility");if(invalid)need(d.cache_error==3,"invalid qcache reason");
    }
    void begin(const Case &c,std::optional<uint32_t> forced_epoch={}){
        need(d.start_ready,"start before drain");d.packet_bytes=c.packet.size();frame_epoch=forced_epoch.value_or(++next_epoch);d.epoch=frame_epoch;
        d.accepted_ref_valid=c.ref_valid;d.accepted_qcache_valid=c.qvalid;d.accepted_ref_fid=c.ref_fid;d.accepted_ref_generation=c.ref_gen;
        d.start=1;begin_cycle=cycle;tick();d.start=0;need(!d.cache_complete,"cache not consumed by frame start");
        d.accepted_ref_valid=!c.ref_valid;d.accepted_qcache_valid=!c.qvalid;d.accepted_ref_fid=~c.ref_fid;d.accepted_ref_generation=~c.ref_gen;
        need(!d.start_ready&&!d.in_ready&&!d.cache_ready&&!d.coefficient_valid&&!d.coefficient_ready&&!d.residual_valid&&!d.residual_ready&&!d.out_valid&&!d.mem_req_valid&&!d.ref_req_valid,"pending IV114 command exposed transfer eligibility");
        tick();monitor_active=true;
    }
    void feed_until(unsigned target=255){
        need(active!=nullptr,"no active input");size_t at=0;bool offered=false;
        for(unsigned watchdog=0;watchdog<12000000;++watchdog){
            d.clk=0;d.eval();if(d.frame_state==target){d.in_valid=0;d.in_last=0;return;}
            if(d.error||d.done||d.v_error||d.join_error||d.metadata_mismatch){d.in_valid=0;d.in_last=0;return;}
            if(!offered&&at<active->packet.size())offered=profile==0||random(4)!=0;
            d.in_valid=offered;d.in_data=at<active->packet.size()?active->packet[at]:0;d.in_last=at+1==active->packet.size();
            d.clk=0;d.eval();bool accepted=d.in_valid&&d.in_ready;tick();if(accepted){++at;offered=false;}
        }
        throw std::runtime_error("frame watchdog "+active->id);
    }
    void settle(){d.in_valid=0;d.in_last=0;for(unsigned k=0;k<20000000;++k){if(!pending&&!reference_pending&&!d.busy&&d.start_ready)return;tick();}throw std::runtime_error("ownership drain watchdog");}
    void finish(const Case &c){
        need(d.error==c.error,"frame error mismatch "+c.id+": got "+std::to_string(d.error)+" expected "+std::to_string(c.error));
        if(c.error==0){need(d.done&&!pending&&!reference_pending&&!d.inverse_busy&&d.inverse_owned_banks==0&&!d.reconstruct_busy,"inverse/canonical completion not quiescent");
            need(canonical_samples==518400&&canonical_tiles==8100&&canonical_plane==3,"canonical coverage");
            need(d.count_reconstruct_outputs==canonical_samples&&d.count_reconstruct_modes==8100&&d.count_reconstruct_residuals==residuals,"canonical counters");
            need(d.count_copy_tiles==observed_copy&&d.count_const_tiles==observed_const&&d.count_residual_tiles==observed_residual_tiles,"canonical mode counters");
            need(observed_ref_requests==observed_ref_acks&&d.count_ref_requests==observed_ref_requests&&d.count_ref_acks==observed_ref_acks,"reference request ACK counters");
            const auto &wanted=canonical_golden().expected;need(actual_pixels==wanted,"full canonical candidate memory mismatch");
            if(record){static const char hex[]="0123456789abcdef";actual_output<<c.id<<'\t'<<profile<<'\t';for(uint8_t v:actual_pixels)actual_output<<hex[v>>4]<<hex[v&15];actual_output<<'\n';}
for(unsigned p=0;p<3;++p){need(observed_coefficients[p]*2==c.dense[p].size(),"incomplete coefficient plane");need(residual_counts[p]==observed_coefficients[p],"incomplete residual plane");}need(launches==dq_tiles&&dq_tiles==residual_tiles,"inverse stage conservation");}
        else {need(!d.done,"failed frame completed");if(c.error==64||c.error==7||c.error==65)need(d.core_starts==0&&coefficients==0&&requests==0,"early reject produced decoder side effects");}
        if(c.error==147){need(observed_coefficients[0]*2==c.dense[0].size()&&observed_coefficients[1]*2==c.dense[1].size()&&observed_coefficients[2]==0,"late CRC provisional prefix scope");}
        if(c.error&&residual_index){event("residual",residual_metadata,residual_token,residual_hash,residual_index,residual_first,last_residual,false);residual_index=0;}
        if(c.error&&canonical_index&&record){unsigned base=canonical_plane==0?0:canonical_plane==1?5400:6750;
            trace<<"{\"type\":\"canonical\",\"id\":"<<quote(c.id)<<",\"memory_profile\":"<<profile<<",\"plane\":"<<canonical_plane<<",\"tile\":"<<canonical_tile<<",\"mode\":"<<unsigned(c.operations[base+canonical_tile])<<",\"frame_epoch\":"<<frame_epoch<<",\"fid\":"<<be32(c.packet,8)<<",\"value_hash\":"<<canonical_hash<<",\"samples\":"<<canonical_index<<",\"first_cycle\":"<<canonical_first<<",\"last_cycle\":"<<canonical_last<<",\"complete\":false}\n";}

        settle();need(requests==acks,"accepted memory request not acknowledged");
#if ELASTIC
        need(elastic_queue.empty(),"finished case retained staged owner");
        need(elastic_up==coefficients&&elastic_down==d.inverse_count_inputs,"upstream/downstream independently counted handshakes");
        need(d.inverse_count_inputs+elastic_discard==coefficients,"inverse input plus explicit stage flush discards");
        if(c.error==0)need(elastic_discard==0&&d.inverse_count_inputs==coefficients,"successful frame exact inverse input count");
#else
        need(d.inverse_count_inputs==coefficients,"inverse input count");
#endif
        need(d.inverse_count_outputs==residuals,"inverse output count");
        if(REFILL_OVERLAP!=0){
            need(d.queue_requests==d.queue_responses&&d.queue_responses==d.queue_pops,"refill queue conservation at completion");
            need(d.queue_pops==refill_observed,"refill queue/child byte conservation");
            need(d.queue_count==0&&!d.queue_pending,"local owners remain after case");
            need(d.queue_requests==queue_req_observed&&d.queue_responses==queue_rsp_observed&&d.queue_pops==queue_pop_observed&&d.queue_stalls==queue_stall_observed,"independent queue event counters");
            need(d.queue_max_count==queue_count_observed&&d.queue_max_owned==queue_owned_observed,"independent queue highwaters");
        }
        need(d.refill_bytes==refill_observed,"child input/refill conservation");
        if(c.error==0||c.error==147)need(refill_observed==uint64_t(span_length[0])+span_length[1]+span_length[2],"full chunk refill coverage");
        std::cout<<"{\"type\":\"case\",\"id\":"<<quote(c.id)<<",\"refill_overlap\":"<<REFILL_OVERLAP<<",\"memory_profile\":"<<profile<<",\"status\":\"PASS\",\"error\":"<<unsigned(d.error)<<",\"seed\":"<<seed<<",\"coefficients\":"<<coefficients<<",\"core_starts\":"<<d.core_starts<<",\"refill_bytes\":"<<d.refill_bytes<<",\"frame_epoch\":"<<frame_epoch<<",\"child_epochs\":[";
        for(size_t k=0;k<child_epochs.size();++k){if(k)std::cout<<',';std::cout<<child_epochs[k];}
        std::cout<<"],\"refill_queue\":{\"requests\":"<<d.queue_requests<<",\"responses\":"<<d.queue_responses<<",\"pops\":"<<d.queue_pops<<",\"stalls\":"<<d.queue_stalls<<",\"cancel_queued\":"<<d.queue_cancel_queued<<",\"cancel_pending\":"<<d.queue_cancel_pending<<",\"max_count\":"<<unsigned(d.queue_max_count)<<",\"max_owned\":"<<unsigned(d.queue_max_owned)<<",\"final_count\":"<<unsigned(d.queue_count)<<",\"final_pending\":"<<unsigned(d.queue_pending)<<",\"observed_requests\":"<<queue_req_observed<<",\"observed_responses\":"<<queue_rsp_observed<<",\"observed_pops\":"<<queue_pop_observed<<",\"observed_stalls\":"<<queue_stall_observed<<",\"observed_max_count\":"<<queue_count_observed<<",\"observed_max_owned\":"<<queue_owned_observed<<"},\"inverse\":{\"assembled_tiles\":"<<launches<<",\"dq_tiles\":"<<dq_tiles<<",\"residual_tiles\":"<<residual_tiles<<",\"residual_samples\":"<<residuals<<",\"owned_banks\":"<<unsigned(d.inverse_owned_banks)<<",\"max_owned_banks\":"<<unsigned(d.inverse_max_owned_banks)<<",\"assembly_during_math_inputs\":"<<assemble_during_math<<",\"cancelled_banks\":"<<d.inverse_count_cancelled_banks<<"},\"elastic\":{\"enabled\":"<<ELASTIC<<",\"accepted\":"<<elastic_up<<",\"delivered\":"<<elastic_down<<",\"discarded\":"<<elastic_discard<<",\"final_occupied\":"<<elastic_queue.size()<<"},\"coefficient_done_cycle\":"<<coefficient_done_cycle<<",\"last_residual\":"<<last_residual<<",\"cycles\":"<<cycle-begin_cycle<<",\"first_input\":"<<first_input<<",\"last_input\":"<<last_input<<",\"first_coef\":"<<first_coef<<",\"last_coef\":"<<last_coef<<",\"done_cycle\":"<<done_cycle<<",\"requests\":"<<requests<<",\"acks\":"<<acks<<",\"cache_cycles\":"<<cache_cycles<<",\"cache_bytes\":"<<cache_bytes<<",\"canonical\":{\"samples\":"<<canonical_samples<<",\"tiles\":"<<canonical_tiles<<",\"copy_tiles\":"<<observed_copy<<",\"const_tiles\":"<<observed_const<<",\"residual_tiles\":"<<observed_residual_tiles<<",\"last_pixel_cycle\":"<<canonical_last<<",\"reference_requests\":"<<observed_ref_requests<<",\"reference_acks\":"<<observed_ref_acks<<",\"ref_pending\":"<<unsigned(d.ref_pending)<<",\"state\":"<<unsigned(d.reconstruct_state)<<"},\"pending_drain\":false,\"full_frame_publication\":false}\n";
    }
    void abort_and_drain(bool warm_reset){
        d.in_valid=0;d.in_last=0;if(warm_reset)d.reset=1;else d.abort_packet=1;tick();d.reset=0;d.abort_packet=0;
        need(!d.residual_valid&&!d.done,"cancel left visible coefficient/completion");
        settle();
    }
};

int main(int argc,char **argv){try{
 need(argc==10,"usage: live cases transforms canonical validation seed events actual hashes profile");
 auto cases=load(argv[1]);load_tiles(argv[2]);load_validation(argv[4]);unsigned seed=unsigned(std::stoul(argv[5])),profile=unsigned(std::stoul(argv[9]));need(profile<2,"finite service profile");
 Bench b(seed,argv[6],argv[3],argv[7]);b.hash_events.open(argv[8]);need(bool(b.hash_events),"hash events output");
 const Case*key=nullptr;for(const auto&c:cases)if(c.id=="actual_001")key=&c;need(key!=nullptr,"original keyframe fixture");
 b.cold_live();
 // Exercise a real accepted physical write before the newly registered local
 // producer cancellation. Parent hash/publication must remain invalid.
 b.prepare(*key,profile,false);b.stage_live(*key);b.preload(*key);b.begin(*key);b.hold_candidate=true;b.feed_until(11);
 for(unsigned n=0;n<6000000&&!b.candidate_pending&&!b.d.v_error;++n)b.tick();
 need(bool(b.candidate_pending),"owned candidate write before registered parent cancellation");
 const auto failed_owner=b.candidate_pending->q;
 const uint64_t wrong_acks_before=b.d.join_wrong_acks;
 // Hold the real response until its actual finite-service due cycle. Advance
 // real RTL clocks; a stalled profile does not promise next-edge ACK validity.
 for(unsigned n=0;b.cycle<b.candidate_pending->due;++n){
  need(n<32&&b.hold_candidate&&b.candidate_pending&&b.candidate_pending->q==failed_owner,"finite wrong-ACK due wait lost physical owner");
  need(b.d.join_wrong_acks==wrong_acks_before&&!b.d.v_accepted_valid,"wrong ACK observed or frame accepted before any response offer");b.tick();
 }
 b.wrong_ack=true;b.hold_candidate=false;b.tick();
 need(b.d.candidate_rsp_valid&&b.d.candidate_rsp_ready&&b.d.join_wrong_acks==wrong_acks_before+1,"wrong-token ACK was not actually offered and accepted once");
 const uint64_t observed_wrong_acks=b.d.join_wrong_acks-wrong_acks_before;
 need(b.d.join_error==0x81&&b.d.join_physical_pending&&b.candidate_pending&&b.candidate_pending->q==failed_owner,"wrong ACK must retain actual physical debt");
 b.wrong_ack=false;b.drain_live();
 need(!b.d.v_accepted_valid&&!b.d.v_front_valid&&!b.d.v_pending_valid&&!b.candidate_pending&&!b.d.join_physical_pending,"failed parent transaction published or retained physical debt");
 b.nominal(*key,profile);
 need(b.d.v_accepted_valid&&b.d.v_front_valid&&b.d.v_front_fid==0&&!b.d.v_pending_valid,"validated keyframe abstract publication");
 if(!ROW_WRITES){
 need(b.candidate_requests==560640&&b.candidate_acks==560640&&b.hash_deliveries==560640,"exact finite candidate write/ACK/hash conservation");
 }else need(b.candidate_requests==70080&&b.candidate_acks==70080&&b.hash_deliveries==560640,"exact finite row request/ACK and original hash-byte conservation");
 need(b.candidate_expanded_bytes==560640&&b.candidate_acked_bytes==560640,"original full candidate byte oracle after independent row expansion");
 need(!b.pending&&!b.reference_pending&&!b.candidate_pending&&!b.d.join_physical_pending&&b.d.join_drained,"physical owners remain after publication");
 need(b.d.v_hash_jobs==1025&&b.d.v_pixel_bytes==518400&&b.d.v_hud_bytes==42240,"complete C2/HUD work");
 std::cout<<"{\"type\":\"live_service_verdict\",\"status\":\"TEST_PASS\",\"row_writes\":"<<unsigned(ROW_WRITES)
          <<",\"request_bytes\":"<<candidate_width<<",\"expanded_bytes\":"<<b.candidate_expanded_bytes<<",\"acked_bytes\":"<<b.candidate_acked_bytes
          <<",\"service_queue_bound\":1,\"service_bus_bits\":16,\"service_data_edges\":"<<b.service_data_edges<<",\"service_overhead_edges\":"<<b.service_overhead_edges
          <<",\"minimum_service_edges\":"<<b.minimum_service<<",\"maximum_service_edges\":"<<b.maximum_service<<",\"physical_SDRAM\":false}\n";
 need(b.guard_checks>0&&b.guard_gap_edges==1&&b.guard_private_residuals<=1,"actual bounded one-edge private residual cancellation witness");
 need(!b.guard_raw_read&&b.guard_raw_reads==b.guard_raw_responses&&b.guard_gap_read_responses==b.guard_private_reads,"raw replay complete lease drain including canceled responses");
 std::cout<<"{\"type\":\"parent_guard_verdict\",\"status\":\"TEST_PASS\",\"checks\":"<<b.guard_checks
          <<",\"parent_fault_gap_edges\":"<<b.guard_gap_edges<<",\"private_residual_handshakes\":"<<b.guard_private_residuals
          <<",\"private_local_reads\":"<<b.guard_private_reads
          <<",\"raw_local_reads\":"<<b.guard_raw_reads<<",\"raw_local_responses\":"<<b.guard_raw_responses
          <<",\"revoked_local_responses\":"<<b.guard_revoked_responses<<",\"private_gap_local_responses\":"<<b.guard_gap_read_responses
          <<",\"raw_local_pending\":"<<bool(b.guard_raw_read)
          <<",\"raw_internal_work_blocked_by_observation_masks\":false,\"physical_responses_masked\":false,\"original_cancel_need_retained\":true}\n";
 std::cout<<"{\"type\":\"live_parent_verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"profile\":"<<profile<<",\"keyframes\":1,\"canonical_bytes\":518400,\"hud_bytes\":42240,\"candidate_write_requests\":"<<b.candidate_requests<<",\"candidate_write_acks\":"<<b.candidate_acks<<",\"hash_deliveries\":"<<b.hash_deliveries<<",\"hash_jobs\":1025,\"elastic_accepted\":"<<b.elastic_total_up<<",\"elastic_delivered\":"<<b.elastic_total_down<<",\"elastic_discarded\":"<<b.elastic_total_discard<<",\"clock_edges\":"<<b.cycle<<",\"observed_wrong_ack_count\":"<<observed_wrong_acks<<",\"directed_checks\":2,\"wrong_ack_owned_write_drained\":true,\"clean_retry_without_reset\":true,\"actual_C2_HUD_seal_validation\":true,\"abstract_publication\":true,\"software_HUD_decode\":true,\"physical_SDRAM\":false,\"hardware_30fps\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<"V115_LIVE_PARENT_FAIL "<<e.what()<<'\n';return 1;}}
