from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]; AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91k/tb_pipeline.cpp').read_text().split('int main(')[0]
s=s.replace('Vcs88_pipeline_v91k','Vcs88_live_v91l')
s=s.replace('#include "verilated.h"','#include "verilated.h"\n#include "../../../experiments/cu66-native-v69/hud.hpp"')
helper=r'''
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
'''
s=s.replace('struct Tuple{',helper+'\nstruct Tuple{')
fields=r'''
    struct CandidateRequest {uint32_t epoch,token;unsigned bank,addr;uint8_t value;
      bool operator==(const CandidateRequest &x)const{return epoch==x.epoch&&token==x.token&&bank==x.bank&&addr==x.addr&&value==x.value;}};
    struct CandidatePending{CandidateRequest q;uint64_t due;};
    std::optional<CandidatePending> candidate_pending;std::optional<CandidateRequest> held_candidate;
    std::array<Bytes,3> candidate_memory{{Bytes(560640),Bytes(560640),Bytes(560640)}};
    std::vector<Patch> accepted_hud,provisional_patches;Bytes provisional_hud,accepted_qcache;
    Bytes actual_qcache;std::array<bool,1350> qcache_seen{};std::optional<unsigned> qcache_lookup;
    const ValidationFixture *vf=nullptr;size_t software_hud_pos=0;bool receipt_sent=false;
    uint64_t candidate_requests=0,candidate_acks=0,hash_deliveries=0,candidate_hash=0,commit_cycle=0;
    uint64_t first_outer=0,last_outer=0,first_write=0,last_write=0,first_token=0,last_token=0;
    bool hold_candidate=false,wrong_ack=false,bus_error=false,hold_presentation=false,hold_scanout=false;
    bool bad_root=false,bad_generation=false,bad_hud_index=false,bad_hud_last=false,extra_hud=false;
    std::optional<CandidateRequest> held_delivery;
    std::ofstream hash_events;
    CandidateRequest candidate_request()const{return {d.candidate_req_epoch,d.candidate_req_token,unsigned(d.candidate_req_bank),unsigned(d.candidate_req_addr),uint8_t(d.candidate_req_data)};}
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
    void live_observe(){
      const bool kill=d.power_on_reset||d.reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;
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
        ++hash_deliveries;
      }
      if(d.candidate_rsp_valid&&d.candidate_rsp_ready&&!wrong_ack){need(bool(candidate_pending),"candidate ACK owner");auto q=candidate_pending->q;
        if(!bus_error)candidate_memory[q.bank][q.addr]=q.value;
        candidate_pending.reset();++candidate_acks;last_write=cycle+1;
      }
      if(d.candidate_req_valid&&d.candidate_req_ready){need(!candidate_pending&&vf&&d.v_bank_active&&!kill,"candidate write lease");auto q=candidate_request();
        need(q.epoch==frame_epoch&&q.bank==d.v_write_bank&&q.addr<560640,"candidate request owner/bounds");
        need((!d.v_reference_bank_valid||q.bank!=d.v_reference_bank)&&(!d.v_front_valid||q.bank!=d.v_front_bank)&&(!d.v_pending_valid||q.bank!=d.v_pending_bank),"candidate write aliases immutable bank");
        uint8_t expected=q.addr<518400?canonical_golden().expected[q.addr]:provisional_hud[q.addr-518400];need(q.value==expected,"physical write byte vs actual independent expected");
        for(uint32_t x:{q.epoch,q.token,uint32_t(q.bank),uint32_t(q.addr)})for(unsigned k=0;k<4;++k)candidate_hash=hash_byte(candidate_hash,uint8_t(x>>(8*k)));
        candidate_hash=hash_byte(candidate_hash,q.value);
        if(!first_write){first_write=cycle+1;first_token=q.token;}last_token=q.token;
        candidate_pending=CandidatePending{q,cycle+(profile?3+random(6):1)};++candidate_requests;
      }
      if(d.v_hash_result&&record){hash_events<<"{\"type\":\"hash\",\"id\":\""<<vf->id<<"\",\"pipeline_id\":\""<<active->id<<"\",\"profile\":"<<profile<<",\"epoch\":"<<frame_epoch<<",\"kind\":"<<unsigned(d.v_hash_job_kind)<<",\"node\":"<<d.v_hash_job_node<<",\"digest\":\""<<cu66::hex(get_digest(d.v_hash_digest))<<"\",\"cycle\":"<<cycle<<"}\n";}
    }
    void live_after_edge(){
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
      need(d.join_inputs==560640&&d.join_requests==560640&&d.join_acks==560640&&d.join_outputs==560640,"live write/hash conservation");
      need(std::all_of(qcache_seen.begin(),qcache_seen.end(),[](bool x){return x;})&&actual_qcache==c.scales,"actual qcache registered coverage");
      accepted_hud=provisional_patches;accepted_qcache=actual_qcache;
      std::cout<<"{\"type\":\"live_case\",\"id\":\""<<vf->id<<"\",\"pipeline_id\":\""<<c.id<<"\",\"profile\":"<<profile<<",\"seed\":"<<seed<<",\"epoch\":"<<frame_epoch<<",\"fid\":"<<d.v_accepted_fid<<",\"generation\":"<<d.v_accepted_generation<<",\"canonical_bytes\":"<<d.v_pixel_bytes<<",\"hud_bytes\":"<<d.v_hud_bytes<<",\"hash_jobs\":"<<d.v_hash_jobs<<",\"hash_message_bytes\":"<<d.v_hash_message_bytes<<",\"hash_blocks\":"<<d.v_hash_blocks<<",\"write_requests\":"<<candidate_requests<<",\"write_acks\":"<<candidate_acks<<",\"hash_deliveries\":"<<hash_deliveries<<",\"write_descriptor_fnv\":"<<candidate_hash<<",\"first_token\":"<<first_token<<",\"last_token\":"<<last_token<<",\"first_outer_cycle\":"<<first_outer<<",\"last_outer_cycle\":"<<last_outer<<",\"start_cycle\":"<<begin_cycle<<",\"commit_cycle\":"<<commit_cycle<<",\"start_to_commit_cycles\":"<<commit_cycle-begin_cycle<<",\"first_outer_to_commit_cycles\":"<<commit_cycle-first_outer<<",\"last_outer_to_commit_cycles\":"<<commit_cycle-last_outer<<",\"qcache_preload_cycles\":"<<cache_cycles<<",\"qcache_bytes\":"<<cache_bytes<<",\"reference_requests\":"<<observed_ref_requests<<",\"accepted_bank\":"<<unsigned(d.v_reference_bank)<<",\"root\":\""<<cu66::hex(get_digest(d.v_accepted_root))<<"\",\"hud_sha256\":\""<<cu66::hex(get_digest(d.v_accepted_hud))<<"\",\"seal\":\""<<cu66::hex(get_digest(d.v_accepted_seal))<<"\",\"status\":\"PASS\"}\n";
      static const char hx[]="0123456789abcdef";actual_output<<"accepted_"<<c.id<<'\t'<<profile<<'\t';for(uint8_t b:candidate_memory[d.v_reference_bank])actual_output<<hx[b>>4]<<hx[b&15];actual_output<<'\n';
      actual_output<<"qcache_"<<c.id<<'\t'<<profile<<'\t';for(uint8_t b:accepted_qcache)actual_output<<hx[b>>4]<<hx[b&15];actual_output<<'\n';
      record=false;tick();
    }
'''
s=s.replace('    Vcs88_live_v91l d;',fields+'\n    Vcs88_live_v91l d;')
s=s.replace('d.out_ready=0;','')
s=s.replace('d.cache_data=c.prior[i];','d.cache_data=accepted_qcache[i];')
s=s.replace('        tick();d.reset=0;tick();','        d.power_on_reset=1;d.software_hud_valid=0;d.software_receipt_valid=0;d.candidate_rsp_valid=0;d.candidate_req_ready=0;d.present_vblank=1;d.present_drained=1;\n        tick();d.power_on_reset=0;d.reset=0;tick();')
s=s.replace('d.clk=0;d.out_ready=!force_output_hold&&(profile==0||random(3)==0);','d.clk=0;live_before_eval();')
s=s.replace('const auto &pixels=canonical_golden().reference;need(pixels.size()==518400,"reference bytes unavailable");','need(d.v_reference_bank_valid,"reference has no actual validated bank");const auto &pixels=candidate_memory[d.v_reference_bank];need(pixels.size()==560640,"reference bytes unavailable");\n            for(unsigned n=0;n<64;++n)need(pixels[pixel_address(r.plane,r.tile,n)]==canonical_golden().reference[pixel_address(r.plane,r.tile,n)],"actual accepted reference differs from independent golden");')
s=s.replace('d.eval();const bool cancel=d.reset||d.abort_packet;','d.eval();live_observe();const bool cancel=d.reset||d.power_on_reset||d.abort_packet||d.v_error||d.join_error||d.metadata_mismatch;')
s=s.replace('if(d.in_valid&&d.in_ready){received.push_back(d.in_data);','if(d.in_valid&&d.in_ready){if(!first_outer)first_outer=cycle+1;last_outer=cycle+1;received.push_back(d.in_data);')
s=s.replace('d.clk=1;d.eval();++cycle;','d.clk=1;d.eval();++cycle;live_after_edge();')
# settle of frozen producer must not wait on validator start-ready, which would deadlock before HUD forwarding.
s=s.replace('if(!pending&&!reference_pending&&!d.busy&&d.start_ready)return;','if(!pending&&!reference_pending&&!d.busy)return;')
# feed stops on the real producer error, validation/join failure also stops, leaving drain to wrapper.
s=s.replace('if(d.error||d.done){','if(d.error||d.done||d.v_error||d.join_error||d.metadata_mismatch){')
# Frozen finish clears record via settle? It does not, retain checks but output own accepted artifact separately.
main=r'''
int main(int argc,char **argv){try{
 need(argc==9,"usage: live cases transforms canonical validation seed events actual hashes");auto cases=load(argv[1]);load_tiles(argv[2]);load_validation(argv[4]);unsigned seed=unsigned(std::stoul(argv[5]));Bench b(seed,argv[6],argv[3],argv[7]);b.hash_events.open(argv[8]);need(bool(b.hash_events),"hash events output");
 auto find=[&](const std::string &id)->const Case&{for(const auto &c:cases)if(c.id==id)return c;throw std::runtime_error("case missing "+id);};
 const auto &key=find("actual_001"),&delta=find("actual_006");std::vector<std::string> checks;unsigned rows=0;
 auto pass=[&](const std::string &s){checks.push_back(s);};
 for(unsigned p=0;p<2;++p){b.cold_live();b.nominal(key,p);++rows;uint32_t accepted=b.d.v_accepted_fid;auto accepted_root=get_digest(b.d.v_accepted_root);unsigned accepted_bank=b.d.v_reference_bank;
   // Every failure retries the same real delta against the still-accepted key and its actual bytes.
   for(unsigned fault=0;fault<9;++fault){b.prepare(delta,p,false);b.bad_generation=fault==5;b.bad_root=fault==4;b.bad_hud_index=fault==6;b.bad_hud_last=fault==7;b.extra_hud=fault==8;b.stage_live(delta);b.preload(delta);b.begin(delta);
     if(fault<4){b.hold_candidate=true;b.feed_until(11);for(unsigned n=0;n<6000000&&!b.candidate_pending&&!b.d.v_error;++n)b.tick();need(bool(b.candidate_pending),"owned candidate write for negative");
       const auto owned=b.candidate_pending->q;b.d.start=1;for(unsigned n=0;n<7;++n){b.tick();need(!b.d.start_ready&&b.candidate_pending&&b.candidate_pending->q==owned,"external start replaced pending writer");}b.d.start=0;pass("external_start_blocked_while_candidate_owned");
       if(fault==0){b.wrong_ack=true;b.hold_candidate=false;b.tick();need(b.d.join_error==0x81&&b.d.join_physical_pending&&b.candidate_pending,"wrong tagged ACK forgot lease");b.wrong_ack=false;}
       if(fault==1){b.bus_error=true;b.hold_candidate=false;b.tick();need(b.d.join_error==0x82&&!b.d.join_physical_pending&&!b.candidate_pending,"matching bus error failed retirement");b.bus_error=false;}
       if(fault==2||fault==3){b.d.reset=fault==3;b.d.abort_packet=fault==2;b.tick();b.d.reset=0;b.d.abort_packet=0;
          for(unsigned n=0;n<7;++n){b.tick();need(!b.d.start_ready&&b.d.join_physical_pending&&b.candidate_pending&&b.candidate_pending->q==owned,"warm kill forgot physical owner");}}
       b.hold_candidate=false;b.drain_live();
     }else{b.feed_until();for(unsigned n=0;n<20000000&&!b.d.v_error&&!b.d.metadata_mismatch;++n)b.tick();need(b.d.v_error||b.d.metadata_mismatch,"bad root/metadata accepted");b.drain_live();}
     need(b.d.v_accepted_valid&&b.d.v_accepted_fid==accepted&&get_digest(b.d.v_accepted_root)==accepted_root&&b.d.v_reference_bank==accepted_bank,"failure changed accepted reference");
     b.bad_generation=b.bad_root=b.bad_hud_index=b.bad_hud_last=b.extra_hud=false;pass(std::array<std::string,9>{{"wrong_write_ack_retains_then_drains","matching_write_bus_error_rejects","abort_owned_write_blocks_retry","warm_reset_owned_write_blocks_retry","live_bad_root_rejects_after_canonical","admitted_metadata_binds_start_hints","wrong_hud_index_rejects_without_write","wrong_hud_last_rejects_without_write","extra_hud_token_rejects_before_out_of_range_write"}}[fault]);
   }
   b.hold_presentation=true;b.nominal(delta,p);++rows;need(b.d.v_front_fid==0&&b.d.v_pending_valid&&b.d.v_pending_fid==1,"pending presentation fence");
   for(unsigned n=0;n<17;++n){b.tick();need(b.d.v_front_fid==0&&b.d.v_pending_valid,"front changed without vblank");}pass("front_waits_vblank");
   b.hold_presentation=false;b.hold_scanout=true;for(unsigned n=0;n<17;++n){b.tick();need(b.d.v_front_fid==0&&b.d.v_pending_valid,"front changed with scanout owner");}pass("front_waits_scanout_drain");
   b.hold_scanout=false;b.tick();need(b.d.v_frame_presented&&b.d.v_front_fid==1&&!b.d.v_pending_valid,"pending frame did not present");pass("front_presents_after_both_fences");
 }
 pass("live_parser_reconstruct_to_write_ack_to_hash");pass("actual_accepted_bank_is_delta_reference");pass("actual_hud_decode_and_acked_hash_transfer");pass("accepted_qcache_only_published_after_validated_commit");pass("all_1025_hash_jobs_real_rtl_per_frame");
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<rows<<",\"source_frames\":2,\"profiles\":2,\"directed_checks\":"<<checks.size()<<",\"directed_check_names\":[";
 for(size_t i=0;i<checks.size();++i){std::cout<<(i?",":"")<<quote(checks[i]);}std::cout<<"],\"live_canonical_producer\":true,\"full_rtl_hud_decoder\":false,\"hardware_30fps_proven\":false}\n";return 0;
}catch(const std::exception &e){std::cerr<<"LIVE_TEST_FAIL "<<e.what()<<'\n';return 1;}}
'''
(AREA/'tb_live.cpp').write_text('// Generated from frozen V91k bench by make_bench.py; existing assertions retained.\n'+s+main)
