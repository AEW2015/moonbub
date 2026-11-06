#include "Vcu66_write_hash_join_v91l.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
#include <array>

static void need(bool ok,const std::string &why){if(!ok)throw std::runtime_error(why);}
struct Payload {
    uint32_t epoch,token,bank,addr,data,hud,fid,plane,tile,index,last;
    bool operator==(const Payload &b)const{return epoch==b.epoch&&token==b.token&&bank==b.bank&&addr==b.addr&&data==b.data&&hud==b.hud&&fid==b.fid&&plane==b.plane&&tile==b.tile&&index==b.index&&last==b.last;}
};
struct Bench {
    Vcu66_write_hash_join_v91l d;std::mt19937 rng;uint64_t cycles=0;unsigned checks=0;uint32_t epoch=1;
    explicit Bench(unsigned seed):rng(seed){d.power_on_reset=1;tick();d.power_on_reset=0;tick();}
    void eval(){d.clk=0;d.eval();}
    void tick(){eval();d.clk=1;d.eval();++cycles;need(cycles<2000000,"watchdog");}
    Payload payload()const{return {d.req_epoch,d.req_token,d.req_bank,d.req_addr,d.req_data,d.out_hud,d.out_fid,d.out_plane,d.out_tile,d.out_index,d.out_last};}
    void begin(){need(d.state==0&&!d.physical_pending,"begin before drain");d.start=1;tick();d.start=0;eval();need(d.in_ready&&!d.error,"begin failed");++epoch;}
    void put(unsigned i){
        need(d.in_ready,"input not ready");d.in_epoch=epoch;d.in_fid=31;d.in_bank=2;d.in_addr=i*7;d.in_data=(i*73+19)&255;
        d.in_hud=i&1;d.in_plane=i%3;d.in_tile=i%1350;d.in_index=i%64;d.in_last=i==999;d.in_valid=1;tick();d.in_valid=0;eval();
        need(d.req_valid&&d.state==1,"input not owned offer");
    }
    void accept(){d.req_ready=1;tick();d.req_ready=0;eval();need(d.physical_pending&&d.rsp_ready&&!d.req_valid,"request not retained");}
    void response(const Payload &p,bool error=false){d.rsp_epoch=p.epoch;d.rsp_token=p.token;d.rsp_bank=p.bank;d.rsp_addr=p.addr;d.rsp_error=error;d.rsp_valid=1;tick();d.rsp_valid=0;d.rsp_error=0;eval();}
    void retire(){need(d.out_valid,"delivery not ready");d.out_ready=1;tick();d.out_ready=0;eval();need(d.drained&&!d.busy,"delivery did not drain");}
    void pass(const std::string &name){++checks;std::cout<<"{\"type\":\"directed\",\"name\":\""<<name<<"\",\"status\":\"PASS\"}\n";}
    void nominal(unsigned profile){
        begin();const auto start=cycles;uint64_t outputs=0;
        for(unsigned i=0;i<1000;++i){
            put(i);const auto p=payload();
            for(unsigned n=0;n<(profile?rng()%5:0);++n){tick();need(payload()==p&&d.req_valid&&!d.out_valid,"held offer changed");}
            accept();
            // An unrelated producer offer cannot overwrite the outstanding byte.
            d.in_valid=1;d.in_data^=255;
            for(unsigned n=0;n<(profile?1+rng()%7:1);++n){tick();need(payload()==p&&!d.in_ready&&!d.out_valid&&d.physical_pending,"pending owner overwritten");}
            d.in_valid=0;response(p);need(d.out_valid&&!d.physical_pending&&payload()==p,"good ACK not delivered");
            for(unsigned n=0;n<(profile?rng()%6:0);++n){tick();need(d.out_valid&&payload()==p&&!d.in_ready&&!d.req_valid,"held output changed");}
            std::cout<<"{\"type\":\"sample\",\"profile\":"<<profile<<",\"ordinal\":"<<i<<",\"epoch\":"<<p.epoch<<",\"token\":"<<p.token<<",\"bank\":"<<p.bank<<",\"addr\":"<<p.addr<<",\"data\":"<<p.data<<",\"hud\":"<<p.hud<<",\"fid\":"<<p.fid<<",\"plane\":"<<p.plane<<",\"tile\":"<<p.tile<<",\"index\":"<<p.index<<",\"last\":"<<p.last<<"}\n";
            retire();++outputs;
        }
        need(d.count_inputs==1000&&d.count_requests==1000&&d.count_acks==1000&&d.count_outputs==1000&&d.count_wrong_acks==0&&d.count_drops==0,"nominal counters");
        std::cout<<"{\"type\":\"case\",\"profile\":"<<profile<<",\"status\":\"PASS\",\"bytes\":"<<outputs<<",\"cycles\":"<<cycles-start<<"}\n";
        pass(profile?"slow_exact_ack_before_hash_and_held_payload":"fast_exact_ack_before_hash_and_held_payload");
    }
    void unaccepted_kill(bool reset){
        begin();put(7);const auto p=payload();d.req_ready=1;if(reset)d.reset=1;else d.cancel=1;eval();need(!d.req_valid,"kill accepted unowned offer");tick();d.reset=d.cancel=0;d.req_ready=0;eval();
        need(d.drained&&!d.physical_pending&&!d.out_valid&&d.count_requests==0&&d.count_drops==1,"unaccepted kill leaked request");
        need(payload()==p,"kill overwrote payload unnecessarily");pass(reset?"reset_unaccepted_offer":"cancel_unaccepted_offer");
    }
    void pending_kill(bool reset,bool same_edge){
        begin();put(9);const auto p=payload();accept();if(reset)d.reset=1;else d.cancel=1;
        if(same_edge)response(p);else {tick();need(d.physical_pending&&!d.drained&&!d.in_ready&&!d.out_valid&&payload()==p,"kill lost accepted owner");}
        d.reset=d.cancel=0;eval();
        if(!same_edge){for(unsigned i=0;i<11;++i){tick();need(d.physical_pending&&payload()==p&&!d.out_valid&&!d.in_ready,"drain released without ACK");}response(p);}
        need(d.drained&&!d.out_valid&&d.count_requests==1&&d.count_acks==1&&d.count_outputs==0&&d.count_drops==1,"killed ACK was delivered");
        pass(std::string(reset?"reset":"cancel")+(same_edge?"_matching_ack_same_edge":"_pending_ack_drain"));
    }
    void delivered_kill(bool reset){
        begin();put(11);auto p=payload();accept();response(p);need(d.out_valid,"precondition output");
        d.out_ready=1;if(reset)d.reset=1;else d.cancel=1;eval();need(!d.out_valid,"kill output accepted");tick();d.out_ready=d.reset=d.cancel=0;eval();
        need(d.drained&&d.count_outputs==0&&d.count_drops==1&&d.count_acks==1,"delivered kill leaked hash byte");pass(reset?"reset_held_hash_output":"cancel_held_hash_output");
    }
    void wrong_ack(unsigned field){
        begin();put(13);const auto p=payload();accept();auto bad=p;
        switch(field){case 0:++bad.epoch;break;case 1:++bad.token;break;case 2:bad.bank^=1;break;default:++bad.addr;}
        response(bad);need(d.error==0x81&&d.physical_pending&&!d.drained&&!d.out_valid&&payload()==p,"wrong ACK retired owner");
        for(unsigned n=0;n<9;++n){tick();need(d.physical_pending&&!d.in_ready&&!d.out_valid&&payload()==p,"wrong ACK released before true ACK");}
        response(p);need(d.drained&&!d.out_valid&&d.count_wrong_acks==1&&d.count_acks==1&&d.count_outputs==0&&d.count_drops==1,"true ACK after error did not drain");
        pass(std::array<std::string,4>{{"wrong_epoch_ack_retains_lease","wrong_token_ack_retains_lease","wrong_bank_ack_retains_lease","wrong_addr_ack_retains_lease"}}[field]);
    }
    void bus_error(){begin();put(15);auto p=payload();accept();response(p,true);need(d.drained&&d.error==0x82&&!d.out_valid&&d.count_outputs==0&&d.count_acks==1,"bus error leaked hash");pass("matching_error_ack_retires_without_hash");}
    void clean_retry(){begin();put(17);auto p=payload();accept();response(p);retire();need(!d.error&&d.count_outputs==1,"clean retry failed");pass("clean_retry_after_fault");}
};
int main(int argc,char **argv){
    try {need(argc==2,"seed arg");const unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed);
        b.nominal(0);b.nominal(1);
        for(bool r:{false,true}){b.unaccepted_kill(r);b.pending_kill(r,false);b.pending_kill(r,true);b.delivered_kill(r);}
        for(unsigned i=0;i<4;++i)b.wrong_ack(i);
        b.bus_error();b.clean_retry();need(b.checks==16,"directed count");
        std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"directed_checks\":"<<b.checks<<",\"exact_bytes\":2000,\"cycles\":"<<b.cycles<<"}\n";return 0;
    }catch(const std::exception &e){std::cerr<<"TEST_FAIL: "<<e.what()<<'\n';return 1;}
}
