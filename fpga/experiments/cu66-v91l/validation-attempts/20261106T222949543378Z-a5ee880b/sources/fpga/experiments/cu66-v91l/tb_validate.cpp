#include "Vcs88_validate_publish_v91l.h"
#include "verilated.h"
#include "../../../experiments/cu66-native-v69/hud.hpp"
#include <array>
#include <fstream>
#include <functional>
#include <iostream>
#include <optional>
#include <random>
#include <sstream>
using cu66::Bytes;
using cu66::Patch;
using cu66::View;
using Digest=std::array<uint8_t,32>;
static void need(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
static Bytes unhex(const std::string &text){need(text.size()%2==0,"hex size");Bytes out;for(size_t i=0;i<text.size();i+=2)out.push_back(uint8_t(std::stoul(text.substr(i,2),nullptr,16)));return out;}
static Digest digest(const std::string &text){auto b=unhex(text);need(b.size()==32,"digest width");Digest d;std::copy(b.begin(),b.end(),d.begin());return d;}
static uint32_t be32(const Bytes &b,unsigned at){need(at+4<=b.size(),"BE field bound");return uint32_t(b[at])<<24|uint32_t(b[at+1])<<16|uint32_t(b[at+2])<<8|b[at+3];}
static uint64_t be64(const Bytes &b,unsigned at){return uint64_t(be32(b,at))<<32|be32(b,at+4);}
static void repair_crc(Bytes &b){uint32_t crc=cu66::crc32(View(b).sub(0,b.size()-4));for(unsigned i=0;i<4;++i)b[b.size()-4+i]=uint8_t(crc>>(24-8*i));}
static Bytes semantic(const std::vector<Patch> &patches){Bytes out;for(const auto &p:patches){auto b=cu66::word_bytes(p.words);out.insert(out.end(),b.begin(),b.end());}need(out.size()==42240,"semantic HUD byte count");return out;}
struct Fixture {
    std::string id,role;unsigned cohort;Bytes packet,tiles,hud_expected;Digest canonical_sha,hud_sha,root,seal;
    uint32_t fid=0,refid=0;uint64_t generation=0;bool key=false;Bytes hud_packet;
};
static void parse_header(Fixture &f){
    auto &p=f.packet;need(p.size()>=132&&std::string(p.begin(),p.begin()+4)=="CS88"&&p[4]==1,"CS88 header");
    need(cu66::crc32(View(p).sub(0,p.size()-4))==be32(p,unsigned(p.size()-4)),"CS88 original outer CRC");
    need(p[5]<=1,"CS88 key flag");f.key=p[5]!=0;f.fid=be32(p,8);f.refid=be32(p,12);f.generation=be64(p,16);
    unsigned mode_n=be32(p,36),q_n=be32(p,40),hud_n=be32(p,44),data_n=be32(p,48);
    // CS88 lengths occupy bytes32..51; commitments begin at52, per original receiver.
    need(uint64_t(128)+mode_n+q_n+hud_n+data_n+4==p.size(),"CS88 body exact length");
    unsigned off=128+mode_n+q_n+data_n;f.hud_packet=Bytes(p.begin()+off,p.begin()+off+hud_n);
    need(std::equal(f.root.begin(),f.root.end(),p.begin()+52)&&std::equal(f.seal.begin(),f.seal.end(),p.begin()+84),"computed fixture commitment vs original CS88 header");
}
static std::vector<Fixture> load(const std::string &path){
    std::ifstream in(path);need(bool(in),"validation TSV");std::string line;std::vector<Fixture> out;
    while(std::getline(in,line)){std::istringstream row(line);std::array<std::string,10> c;for(auto &s:c)need(bool(std::getline(row,s,'\t')),"ten validation fields");
        if(c[0]=="id"&&c[1]=="cohort")continue;
        Fixture f;f.id=c[0];f.cohort=unsigned(std::stoul(c[1]));f.role=c[2];f.packet=unhex(c[3]);f.tiles=unhex(c[4]);f.hud_expected=unhex(c[5]);f.canonical_sha=digest(c[6]);f.hud_sha=digest(c[7]);f.root=digest(c[8]);f.seal=digest(c[9]);
        need(f.tiles.size()==518400&&f.hud_expected.size()==42240,"fixture frame lengths");parse_header(f);out.push_back(std::move(f));}
    need(!out.empty(),"validation fixtures absent");return out;
}
template<class W>static Digest get_digest(const W &port){Digest out{};for(unsigned i=0;i<32;++i)out[i]=uint8_t(port[(31-i)/4]>>((3-i%4)*8));return out;}
template<class W>static void set_digest(W &port,const Digest &value){for(unsigned i=0;i<8;++i)port[i]=0;for(unsigned i=0;i<32;++i)port[(31-i)/4]|=uint32_t(value[i])<<((3-i%4)*8);}
struct Metadata {bool valid;uint32_t fid;uint64_t generation;Digest root,hud,seal;bool operator==(const Metadata &x)const{return valid==x.valid&&fid==x.fid&&generation==x.generation&&root==x.root&&hud==x.hud&&seal==x.seal;}};
struct Write {unsigned bank,offset;uint8_t value;uint32_t epoch;uint64_t due;};
struct Bench {
    Vcs88_validate_publish_v91l d;std::mt19937 rng;uint64_t cycle=0;unsigned profile=0,epoch=0;bool record=false;
    const Fixture *fixture=nullptr;Bytes candidate_hud;Digest candidate_hud_digest{};std::vector<Patch> accepted_hud,candidate_patches;
    std::array<Bytes,3> memory{{Bytes(560640),Bytes(560640),Bytes(560640)}};
    std::optional<Write> pending;std::ofstream trace;size_t pixel_pos=0,hud_pos=0;bool receipt_sent=false;
    bool hold_writes=false,force_undrained=false,hold_present=false,hold_scanout=false,source_off=false;
    bool wrong_pixel=false,wrong_hud=false,wrong_receipt=false,false_receipt=false,alter_pixel=false,alter_hud=false,wrong_producer=false,force_producer_error=false;
    Metadata last_metadata{};uint64_t begin_cycle=0,pixel_last=0,hud_last=0,commit_cycle=0,writes=0,acks=0;
    uint32_t held_front=0;unsigned held_front_bank=0;bool previous_front=false;
    explicit Bench(unsigned seed,const std::string &events):rng(seed),trace(events){need(bool(trace),"validation events");cold();}
    unsigned random(unsigned n){return rng()%n;}
    Metadata metadata()const{return {bool(d.accepted_valid),d.accepted_fid,d.accepted_generation,get_digest(d.accepted_root),get_digest(d.accepted_hud),get_digest(d.accepted_seal)};}
    void cold(){need(!pending,"cold reset with external write owner");source_off=true;d.power_on_reset=1;d.reset=0;d.abort_i=0;d.start_valid=0;d.pixel_valid=0;d.hud_valid=0;d.hud_receipt_valid=0;tick();d.power_on_reset=0;tick();source_off=false;accepted_hud.clear();last_metadata=metadata();previous_front=d.front_valid;held_front=d.front_fid;held_front_bank=d.front_bank;}
    void tick(){
        d.clk=0;d.writes_drained=!pending&&!force_undrained;d.vblank=!hold_present;d.scanout_drained=!hold_scanout;
        d.pixel_valid=fixture&&!source_off&&pixel_pos<fixture->tiles.size()&&!pending;
        d.pixel_data=fixture&&pixel_pos<fixture->tiles.size()?fixture->tiles[pixel_pos]:0;
        if(alter_pixel&&pixel_pos==17)d.pixel_data^=1;
        d.pixel_epoch=epoch+(wrong_pixel?1:0);
        unsigned global=unsigned(pixel_pos/64);d.pixel_plane=global<5400?0:global<6750?1:2;
        d.pixel_tile=global<5400?global:global<6750?global-5400:global-6750;d.pixel_index=pixel_pos%64;d.pixel_last=pixel_pos+1==518400;
        d.hud_valid=fixture&&!source_off&&hud_pos<candidate_hud.size()&&!pending;
        d.hud_data=hud_pos<candidate_hud.size()?candidate_hud[hud_pos]:0;if(alter_hud&&hud_pos==17)d.hud_data^=1;
        d.hud_last=hud_pos+1==42240;d.hud_epoch=epoch+(wrong_hud?1:0);
        d.hud_fid=fixture?fixture->fid:0;d.hud_refid=fixture?fixture->refid:0;d.hud_generation=fixture?fixture->generation:0;
        d.hud_receipt_valid=fixture&&!source_off&&!receipt_sent;d.hud_decoded_verified=!false_receipt;
        d.hud_receipt_epoch=epoch+(wrong_receipt?1:0);d.hud_receipt_fid=fixture?fixture->fid:0;d.hud_receipt_refid=fixture?fixture->refid:0;d.hud_receipt_generation=fixture?fixture->generation:0;
        set_digest(d.hud_receipt_sha256,candidate_hud_digest);
        d.producer_done=fixture&&pixel_pos==fixture->tiles.size();d.producer_epoch=epoch+(wrong_producer?1:0);d.producer_error=force_producer_error;d.eval();
        const bool kill=d.power_on_reset||d.reset||d.abort_i;
        bool old_drained=d.writes_drained;bool old_vblank=d.vblank&&d.scanout_drained;
        if(d.hud_receipt_valid&&d.hud_receipt_ready)receipt_sent=true;
        if(d.hash_result&&record)trace<<"{\"type\":\"hash\",\"id\":\""<<fixture->id<<"\",\"profile\":"<<profile<<",\"epoch\":"<<epoch<<",\"kind\":"<<unsigned(d.hash_job_kind)<<",\"node\":"<<d.hash_job_node<<",\"digest\":\""<<cu66::hex(get_digest(d.hash_digest))<<"\",\"cycle\":"<<cycle<<"}\n";
        const bool p=d.pixel_valid&&d.pixel_ready,h=d.hud_valid&&d.hud_ready;
        need(!(p&&h),"simultaneous canonical/HUD write from one-byte service");
        if(p||h){
            need(!pending&&d.bank_active&&!kill,"write without candidate bank lease");
            need((!d.reference_bank_valid||d.write_bank!=d.reference_bank)&&(!d.front_valid||d.write_bank!=d.front_bank)&&(!d.pending_valid||d.write_bank!=d.pending_bank),"candidate overwrites accepted/front/pending owner");
            unsigned at=p?unsigned(pixel_pos):518400+unsigned(hud_pos);uint8_t value=p?d.pixel_data:d.hud_data;
            pending=Write{unsigned(d.write_bank),at,value,epoch,cycle+(profile?3+random(6):1)};++writes;
            if(p){++pixel_pos;pixel_last=cycle;}else{++hud_pos;hud_last=cycle;}
        }
        if(pending&&!hold_writes&&pending->due<=cycle){
            need(pending->offset<memory[pending->bank].size(),"write bank range");memory[pending->bank][pending->offset]=pending->value;pending.reset();++acks;
        }
        d.clk=1;d.eval();++cycle;
        auto now=metadata();
        if(!d.power_on_reset&&!(now==last_metadata)){
            need(d.frame_committed&&!kill&&old_drained&&fixture,"accepted metadata changed without atomic validated commit");
            need(now.valid&&now.fid==fixture->fid&&now.generation==fixture->generation&&now.root==fixture->root&&now.seal==fixture->seal&&now.hud==fixture->hud_sha,"accepted commitment identity");
            need(pixel_pos==518400&&hud_pos==42240&&!pending&&writes==acks,"commit before actual external writes drain");
            const auto &bank=memory[d.reference_bank];need(std::equal(fixture->tiles.begin(),fixture->tiles.end(),bank.begin())&&std::equal(candidate_hud.begin(),candidate_hud.end(),bank.begin()+518400),"accepted bank bytes differ from validated canonical/HUD");
            commit_cycle=cycle;
        }
        last_metadata=now;
        if(!d.power_on_reset&&(bool(d.front_valid)!=previous_front||d.front_fid!=held_front||d.front_bank!=held_front_bank))
            need(d.frame_presented&&old_vblank,"front changed before vblank/scanout drain");
        previous_front=d.front_valid;held_front=d.front_fid;held_front_bank=d.front_bank;
    }
    void reject_start(uint32_t requested_epoch,uint32_t fid,uint32_t refid,uint64_t generation,bool key,const std::string &name){
        need(d.start_ready&&!d.bank_active&&!pending,"start-only rejection requires quiescent writer");
        const auto prior=metadata();const uint64_t prior_writes=writes,prior_acks=acks;
        const std::array<uint32_t,3> prior_work{{d.hash_jobs,d.pixel_bytes,d.hud_bytes}};
        const std::array<uint32_t,6> prior_ownership{{unsigned(d.front_valid),unsigned(d.front_bank),d.front_fid,unsigned(d.pending_valid),unsigned(d.pending_bank),d.pending_fid}};
        const bool prior_source_off=source_off;source_off=true;
        d.start_epoch=requested_epoch;d.start_fid=fid;d.start_refid=refid;d.start_generation=generation;d.start_key=key;d.start_valid=1;
        tick();d.start_valid=0;
        const std::array<uint32_t,6> after_ownership{{unsigned(d.front_valid),unsigned(d.front_bank),d.front_fid,unsigned(d.pending_valid),unsigned(d.pending_bank),d.pending_fid}};
        need(d.error==1&&!d.done&&!d.bank_active&&!d.busy&&!pending,"start identity was not rejected: "+name);
        need(metadata()==prior&&after_ownership==prior_ownership&&writes==prior_writes&&acks==prior_acks,"invalid start changed accepted/front/writes: "+name);
        const std::array<uint32_t,3> after_work{{d.hash_jobs,d.pixel_bytes,d.hud_bytes}};
        need(d.start_ready&&!d.hash_result&&after_work==prior_work,"invalid start retained work or changed hash/stream counts: "+name);
        source_off=prior_source_off;
    }
    void begin(const Fixture &f,unsigned service,bool emit){
        need(d.start_ready&&!d.busy&&!pending,"validation begin before drain");fixture=&f;profile=service;record=emit;
        candidate_patches=cu66::decode_hud(View(f.hud_packet),f.key?nullptr:&accepted_hud,f.fid,f.refid);
        candidate_hud=semantic(candidate_patches);candidate_hud_digest=cu66::sha256(candidate_hud);need(candidate_hud==f.hud_expected&&candidate_hud_digest==f.hud_sha,"actual software HUD decode vs independent golden");
        pixel_pos=hud_pos=0;receipt_sent=false;writes=acks=0;pixel_last=hud_last=commit_cycle=0;
        ++epoch;d.start_epoch=epoch;d.start_fid=f.fid;d.start_refid=f.refid;d.start_generation=f.generation;d.start_key=f.key;
        set_digest(d.start_expected_root,f.root);set_digest(d.start_expected_seal,f.seal);d.start_valid=1;begin_cycle=cycle;tick();d.start_valid=0;
        need(d.bank_active&&!d.error,"validation start not admitted");
        d.start_epoch=epoch+123;d.start_fid=f.fid+999;d.start_generation=f.generation+999;
    }
    void drain(){source_off=true;hold_writes=false;force_undrained=false;d.producer_error=0;
        for(unsigned n=0;n<10000&&(!d.start_ready||pending);++n){tick();}
        need(d.start_ready&&!d.busy&&!pending,"validation abort physical drain");source_off=false;record=false;
    }
    void expect_fault(const Fixture &f,unsigned service,unsigned code,const std::string &name){
        begin(f,service,false);for(unsigned n=0;n<20000000&&!d.error&&!d.done;++n){tick();}
        need(d.error==code&&!d.done&&metadata().fid!=f.fid,"expected validation rejection "+name+" got "+std::to_string(d.error));drain();
    }
    void run(const Fixture &f,unsigned service){
        begin(f,service,true);for(unsigned n=0;n<20000000&&!d.done&&!d.error;++n){tick();}
        need(d.done&&!d.error&&commit_cycle>0&&pixel_pos==518400&&hud_pos==42240,"validation nominal completion");
        need(d.hash_jobs==1025&&d.hash_message_bytes==628815&&d.hash_blocks==10298,"actual SHA work accounting");
        need(get_digest(d.computed_root)==f.root&&get_digest(d.computed_seal)==f.seal&&get_digest(d.computed_hud)==f.hud_sha,"computed full commitments");
        accepted_hud=candidate_patches;
        std::cout<<"{\"type\":\"case\",\"id\":\""<<f.id<<"\",\"cohort\":"<<f.cohort<<",\"role\":\""<<f.role<<"\",\"profile\":"<<profile<<",\"status\":\"PASS\",\"epoch\":"<<epoch<<",\"fid\":"<<f.fid<<",\"generation\":"<<f.generation<<",\"canonical_bytes\":"<<d.pixel_bytes<<",\"hud_bytes\":"<<d.hud_bytes<<",\"hash_jobs\":"<<d.hash_jobs<<",\"hash_message_bytes\":"<<d.hash_message_bytes<<",\"hash_blocks\":"<<d.hash_blocks<<",\"root\":\""<<cu66::hex(get_digest(d.computed_root))<<"\",\"hud_sha256\":\""<<cu66::hex(get_digest(d.computed_hud))<<"\",\"seal\":\""<<cu66::hex(get_digest(d.computed_seal))<<"\",\"write_requests\":"<<writes<<",\"write_acks\":"<<acks<<",\"cycles\":"<<cycle-begin_cycle<<",\"last_pixel_cycle\":"<<pixel_last<<",\"last_hud_cycle\":"<<hud_last<<",\"commit_cycle\":"<<commit_cycle<<",\"accepted_bank\":"<<unsigned(d.reference_bank)<<",\"scope\":\"Real RTL C2/HUD hash and atomic bank commit; actual C++ HUD decoder; captured canonical replay\"}\n";
        record=false;source_off=true;tick();source_off=false;
    }
};
int main(int argc,char **argv){try{
    need(argc==4,"usage: Vcs88_validate_publish_v91l validation.tsv seed events.jsonl");auto fixtures=load(argv[1]);unsigned seed=unsigned(std::stoul(argv[2]));Bench b(seed,argv[3]);std::vector<std::string> checks;unsigned rows=0;
    auto pass=[&](const std::string &name){checks.push_back(name);};
    for(unsigned profile=0;profile<2;++profile){unsigned cohort=999;
        for(const auto &f:fixtures){
            if(cohort!=f.cohort){
                b.cold();cohort=f.cohort;need(f.key,"historical validation chain must begin at a real key");
                if(f.cohort==0){b.reject_start(b.epoch+1,f.fid,0,f.generation,false,"cold delta without reference");pass("cold_delta_requires_accepted_reference");}
            }
            if(f.cohort==0&&f.fid==1){
                const auto accepted=b.metadata();const uint32_t next_epoch=b.epoch+1;
                b.reject_start(0,f.fid,f.refid,f.generation,false,"zero epoch");pass("zero_epoch_start_rejects");
                b.reject_start(next_epoch,f.fid,f.refid,0,false,"zero generation");pass("zero_generation_start_rejects");
                b.reject_start(next_epoch,0xffffffffU,f.refid,f.generation,false,"reserved fid");pass("reserved_frame_id_start_rejects");
                b.reject_start(next_epoch,accepted.fid,f.refid,f.generation,false,"frame replay");pass("replayed_frame_id_start_rejects");
                b.reject_start(next_epoch,f.fid,f.refid,accepted.generation,false,"stale generation");pass("stale_generation_start_rejects");
                b.reject_start(next_epoch,f.fid,f.refid+1,f.generation,false,"wrong delta reference");pass("wrong_delta_reference_start_rejects");
                b.reject_start(next_epoch,f.fid,f.refid,f.generation,true,"key with delta reference");pass("key_non_sentinel_reference_start_rejects");
                auto bad=f.hud_packet;bad.back()^=1;bool rejected=false;try{cu66::decode_hud(View(bad),&b.accepted_hud,f.fid,f.refid);}catch(const std::exception &){rejected=true;}need(rejected,"actual HUD CRC accepted");pass("actual_software_hud_crc_rejects");
                auto prior=b.metadata();b.wrong_receipt=true;b.expect_fault(f,profile,5,"stale HUD receipt");b.wrong_receipt=false;need(b.metadata()==prior,"stale receipt changed accepted state");pass("stale_hud_receipt_rejects");
                b.false_receipt=true;b.expect_fault(f,profile,5,"unverified HUD receipt");b.false_receipt=false;pass("unverified_software_hud_receipt_rejects");
                b.wrong_pixel=true;b.expect_fault(f,profile,2,"pixel epoch");b.wrong_pixel=false;pass("canonical_tuple_owner_rejects");
                b.wrong_hud=true;b.expect_fault(f,profile,3,"HUD byte epoch");b.wrong_hud=false;pass("hud_byte_owner_rejects");
                b.alter_pixel=true;b.expect_fault(f,profile,6,"canonical content root");b.alter_pixel=false;pass("late_canonical_root_rejects");
                b.alter_hud=true;b.expect_fault(f,profile,7,"semantic HUD hash");b.alter_hud=false;pass("late_hud_semantic_hash_rejects");
                b.wrong_producer=true;b.expect_fault(f,profile,4,"producer completion owner");b.wrong_producer=false;pass("producer_done_owner_rejects");
                b.begin(f,profile,false);for(unsigned n=0;n<100000&&b.pixel_pos<128;++n){b.tick();}b.force_producer_error=true;b.tick();b.force_producer_error=false;need(b.d.error==10&&!b.d.done&&b.metadata()==prior,"producer failure published");b.drain();pass("upstream_producer_failure_aborts");
                auto bad_seal=f;bad_seal.seal[0]^=1;bad_seal.packet[84]^=1;repair_crc(bad_seal.packet);b.expect_fault(bad_seal,profile,8,"frame seal");pass("late_frame_seal_rejects");
                for(bool reset:{false,true}){
                    b.begin(f,profile,false);for(unsigned n=0;n<100000&&!(b.pixel_pos>128&&b.pending);++n){b.tick();}need(bool(b.pending),"cancel pending write absent");b.hold_writes=true;
                    b.d.reset=reset;b.d.abort_i=!reset;b.tick();b.d.reset=0;b.d.abort_i=0;b.source_off=true;
                    for(unsigned n=0;n<7;++n){b.d.start_valid=1;b.tick();need(!b.d.start_ready&&b.d.bank_active,"replacement bypassed external drain");}b.d.start_valid=0;
                    need(b.metadata()==prior,"warm reset/abort lost accepted metadata");b.drain();pass(reset?"warm_reset_preserves_accepted_and_pending_write_owner":"abort_preserves_accepted_and_pending_write_owner");
                }
                b.force_undrained=true;b.begin(f,profile,false);for(unsigned n=0;n<20000000&&b.d.state!=7&&!b.d.error;++n){b.tick();}need(b.d.state==7&&!b.d.error,"validated commit hold absent");
                for(unsigned n=0;n<17;++n){b.tick();need(!b.d.done&&b.metadata()==prior,"publication before explicit write drain");}
                b.d.abort_i=1;b.tick();b.d.abort_i=0;b.drain();pass("fully_hashed_candidate_waits_for_external_drain");
            }
            if(f.cohort==0&&f.fid==1)b.hold_present=true;
            b.run(f,profile);++rows;
            if(f.cohort==0&&f.fid==1){
                auto committed=b.metadata();need(b.d.front_valid&&b.d.front_fid==0&&b.d.pending_valid&&b.d.pending_fid==1,"front advanced without vblank");
                for(unsigned n=0;n<17;++n){b.tick();need(b.d.front_fid==0&&b.d.pending_valid&&b.metadata()==committed,"held vblank changed front/accepted state");}pass("validated_pending_frame_waits_for_vblank");
                b.hold_present=false;b.hold_scanout=true;
                for(unsigned n=0;n<17;++n){b.tick();need(b.d.front_fid==0&&b.d.pending_valid&&b.metadata()==committed,"undrained scanout released old front");}pass("validated_pending_frame_waits_for_scanout_drain");
                b.hold_scanout=false;b.tick();need(b.d.frame_presented&&b.d.front_fid==1&&!b.d.pending_valid&&b.metadata()==committed,"vblank plus drain did not atomically present pending frame");pass("pending_frame_presents_after_both_fences");
            }
        }
    }
    pass("all_c2_root_and_seal_hash_jobs_real_rtl");pass("actual_hud_decode_and_transferred_words_match");pass("accepted_bank_atomic_with_metadata");pass("scanout_front_changes_only_after_vblank_drain");pass("accepted_start_snapshot_immutable");pass("good_retry_after_each_rejection_and_cancel");
    std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"cases\":"<<rows<<",\"source_fixture_frames\":"<<fixtures.size()<<",\"directed_checks\":"<<checks.size()<<",\"directed_check_names\":[";
    for(size_t i=0;i<checks.size();++i){std::cout<<(i?",":"")<<'"'<<checks[i]<<'"';}std::cout<<"],\"full_rtl_hud_decoder\":false,\"hardware_30fps_proven\":false}\n";return 0;
}catch(const std::exception &error){std::cerr<<"TEST_FAIL "<<error.what()<<'\n';return 1;}}
