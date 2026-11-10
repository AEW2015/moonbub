#include "Vrequest_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

static void need(bool v,const std::string &s){if(!v)throw std::runtime_error(s);}
class Bench {
public:
    Vrequest_probe d;
    unsigned seed;std::mt19937 rng;uint64_t cycles=0;
    struct Read{uint32_t addr,epoch;uint8_t byte;};
    std::optional<Read> flight;
    std::optional<std::pair<unsigned,unsigned>> held_output;
    std::optional<std::pair<uint32_t,uint32_t>> held_request;
    uint32_t offset=0,length=0,epoch=0;std::vector<uint8_t> bytes;
    bool child_ready=true,read_ready=true,missing=false,bad_epoch=false,extra=false;
    uint64_t simultaneous=0,read_edges=0,pop_edges=0;
    uint64_t physical_responses=0,physical_responses_on_revoke=0;
    explicit Bench(unsigned s):seed(s),rng(s){
        d.clk=0;d.reset=1;d.cancel=0;d.start=0;d.clear_stats=0;
        d.start_offset=0;d.start_length=0;d.start_epoch=0;
        tick();d.reset=0;tick();
    }
    unsigned random(unsigned n){return rng()%n;}
    uint8_t memory(uint32_t at)const{return uint8_t((at*37U)^(seed>>3));}
    void tick(){
        d.clk=0;d.req_ready=read_ready;d.out_ready=child_ready;
        d.rsp_valid=(flight.has_value()&&!missing)||extra;
        d.rsp_addr=flight?flight->addr:0;d.rsp_epoch=flight?(flight->epoch+unsigned(bad_epoch)):0;
        d.rsp_data=flight?flight->byte:0;d.eval();
        need(!d.mismatch,"V121 preedge exact public output mismatch");
        if(flight){++physical_responses;if(d.reset||d.cancel||d.start||d.clear_stats)++physical_responses_on_revoke;}
        const bool cancel=d.reset||d.cancel||d.start||d.clear_stats;
        if(cancel){
            need(!d.req_valid&&!d.out_valid&&!d.push_event&&!d.pop_event,"local cancel leaked traffic");
            flight.reset();held_output.reset();held_request.reset();
        }else{
            need(unsigned(d.fifo_count)+unsigned(d.pending)<=2,"queue owners exceeded two");
            need(bool(d.pending)==flight.has_value(),"one-edge registered response owner mismatch");
            if(held_output)need(d.out_valid&&std::make_pair(unsigned(d.out_data),unsigned(d.out_last))==*held_output,"held queue head changed");
            if(held_request)need(d.req_valid&&std::make_pair(uint32_t(d.req_addr),uint32_t(d.req_epoch))==*held_request,"held read offer changed");
            held_output=d.out_valid&&!d.out_ready?std::optional<std::pair<unsigned,unsigned>>(std::make_pair(unsigned(d.out_data),unsigned(d.out_last))):std::nullopt;
            held_request=d.req_valid&&!d.req_ready?std::optional<std::pair<uint32_t,uint32_t>>(std::make_pair(uint32_t(d.req_addr),uint32_t(d.req_epoch))):std::nullopt;
            const bool push=d.push_event,pop=d.pop_event;
            if(push&&pop)++simultaneous;
            flight.reset();
            if(d.req_valid&&d.req_ready){
                need(d.req_addr>=offset&&uint64_t(d.req_addr)<uint64_t(offset)+length,"read crossed chunk range");
                need(d.req_epoch==epoch,"read owner epoch changed");
                need(d.req_addr==uint32_t(offset+uint32_t(read_edges)),"independent exact full32 issue sequence");
                flight=Read{d.req_addr,d.req_epoch,memory(d.req_addr)};++read_edges;
            }
            if(pop){
                need(bytes.size()<length,"extra child byte");
                need(d.out_data==memory(offset+uint32_t(bytes.size())),"child byte order/data mismatch");
                need(bool(d.out_last)==(bytes.size()+1==length),"child last mismatch");
                bytes.push_back(d.out_data);++pop_edges;
            }
        }
        d.clk=1;d.eval();++cycles;
        need(!d.mismatch,"V121 postedge exact public output mismatch");
        need(unsigned(d.fifo_count)+unsigned(d.pending)<=2,"post-edge queue owner bound");
        need(d.max_count<=2&&d.max_owned<=2,"queue highwater bound");
    }
    void reset(){d.reset=1;tick();d.reset=0;tick();missing=bad_epoch=extra=false;}
    void begin(uint32_t n,uint32_t at=7,uint32_t tag=1,bool clear=true){
        child_ready=true;read_ready=true;missing=bad_epoch=extra=false;
        if(clear){d.clear_stats=1;tick();d.clear_stats=0;}
        offset=at;length=n;epoch=tag;bytes.clear();read_edges=pop_edges=simultaneous=0;
        d.start_offset=at;d.start_length=n;d.start_epoch=tag;d.start=1;tick();d.start=0;
    }
    void finish(bool randomized=true){
        for(unsigned k=0;k<100000&&!d.done&&!d.error;++k){
            child_ready=!randomized||random(4)!=0;read_ready=!randomized||random(3)!=0;tick();
        }
        need(!d.error&&d.done,"queue completion watchdog or error");
        need(bytes.size()==length,"queue omitted bytes");
        need(d.count_pops==length,"queue pop conservation");
        need(d.count_requests==d.count_responses+d.count_cancel_pending&&d.count_responses==d.count_pops+d.count_cancel_queued,"queue byte/cancel conservation");
        need(d.fifo_count==0&&!d.pending&&!flight,"queue done with local owners");
        const auto final_requests=d.count_requests;for(unsigned k=0;k<4;++k)tick();
        need(d.count_requests==final_requests,"read after final byte");
    }
    void cancel_now(bool warm_reset=false){
        if(warm_reset)d.reset=1;else d.cancel=1;tick();d.reset=0;d.cancel=0;
        for(unsigned k=0;k<4;++k)tick();
        need(!d.active&&!d.out_valid&&!d.pending&&d.fifo_count==0,"cancel retained owner");
    }
};
int inherited_main(int argc,char **argv){
    try{
        need(argc==2,"usage: Vbyte_refill_queue_v91i2b seed");unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed);std::vector<std::string> names;
        auto pass=[&](const std::string &name){names.push_back(name);std::cout<<"{\"type\":\"directed\",\"name\":\""<<name<<"\",\"status\":\"PASS\",\"requests\":"<<b.d.count_requests<<",\"responses\":"<<b.d.count_responses<<",\"pops\":"<<b.d.count_pops<<",\"cancel_queued\":"<<b.d.count_cancel_queued<<",\"cancel_pending\":"<<b.d.count_cancel_pending<<",\"max_count\":"<<unsigned(b.d.max_count)<<",\"max_owned\":"<<unsigned(b.d.max_owned)<<",\"final_count\":"<<unsigned(b.d.fifo_count)<<",\"final_pending\":"<<unsigned(b.d.pending)<<",\"error\":"<<unsigned(b.d.error)<<"}\n";};
        for(unsigned n:{0U,1U,2U,3U,257U}){b.begin(n,11+n,100+n);b.finish();}pass("empty_single_tail_and_random_stalls");
        b.begin(64,37,401);b.child_ready=false;
        for(unsigned k=0;k<6;++k)b.tick();
        need(b.d.fifo_count==2&&!b.d.pending&&b.d.count_requests==2,"full queue did not stop read launch");
        const auto byte=b.d.out_data;const auto last=b.d.out_last;
        for(unsigned k=0;k<17;++k){b.tick();need(b.d.out_data==byte&&b.d.out_last==last&&b.d.count_requests==2,"full held head/credit changed");}
        b.finish(false);need(b.simultaneous>0&&b.d.max_owned==2,"queue did not exercise overlap");pass("full_two_owner_hold_then_simultaneous_push_pop");
        b.begin(8,5,501);b.read_ready=false;for(unsigned k=0;k<11;++k)b.tick();need(b.d.count_requests==0,"read offer accepted without ready");b.finish(false);pass("read_offer_stable_under_ready_low");
        b.begin(12,9,601);b.child_ready=false;for(unsigned k=0;k<6;++k)b.tick();b.cancel_now();need(b.d.count_cancel_queued==2&&b.d.count_cancel_pending==0,"queued cancel counters");pass("abort_two_queued_bytes");
        b.begin(12,9,602);b.tick();need(b.d.pending,"pending setup absent");b.cancel_now();need(b.d.count_cancel_pending==1,"pending cancel owner count");pass("abort_registered_read_response");
        b.begin(12,9,603);b.child_ready=false;for(unsigned k=0;k<3;++k)b.tick();b.cancel_now(true);need(b.d.count_requests==0,"warm reset did not reset stats");pass("reset_owned_queue_and_response");
        b.begin(12,9,604);b.tick();need(b.d.pending,"replacement pending absent");b.begin(5,41,605,false);b.finish(false);pass("replacement_start_cancels_old_response");
        b.begin(12,9,606);b.child_ready=false;for(unsigned k=0;k<6;++k)b.tick();b.begin(3,91,607,false);b.finish(false);pass("replacement_start_cancels_full_queue");
        b.begin(4,9,701);b.tick();need(b.d.pending,"mismatched epoch setup");b.bad_epoch=true;b.tick();need(b.d.error==1&&!b.d.out_valid&&!b.d.req_valid,"bad response epoch leaked data");b.bad_epoch=false;pass("mismatched_response_epoch_rejected");
        b.begin(4,9,702);b.tick();b.missing=true;b.tick();need(b.d.error==1&&!b.d.out_valid,"missing registered response not rejected");b.missing=false;pass("missing_one_edge_response_rejected");
        b.begin(4,9,703);b.extra=true;b.tick();need(b.d.error==1&&!b.d.req_valid,"unsolicited response accepted");b.extra=false;pass("unsolicited_response_rejected");
        b.begin(49,123,801);b.finish();pass("clean_restart_after_response_fault");
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"directed_checks\":"<<names.size()<<",\"cycles\":"<<b.cycles<<",\"owner_bound\":2,\"directed_check_names\":[";
        for(size_t k=0;k<names.size();++k){if(k)std::cout<<',';std::cout<<'"'<<names[k]<<'"';}std::cout<<"]}\n";return 0;
    }catch(const std::exception &e){std::cerr<<"REFILL_QUEUE_TEST_FAIL "<<e.what()<<'\n';return 1;}
}
