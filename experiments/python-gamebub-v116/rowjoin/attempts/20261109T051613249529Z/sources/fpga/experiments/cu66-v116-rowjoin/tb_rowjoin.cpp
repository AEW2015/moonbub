#include "Vcu66_row_write_hash_join_v91l.h"
#include "Vcu66_row_write_hash_join_v91l___024root.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <deque>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>
static void need(bool ok,const std::string&s){if(!ok)throw std::runtime_error(s);}
struct Row {
    uint32_t epoch=0,token=0,bank=0,addr=0,fid=0,plane=0,tile=0,index=0;
    bool hud=false,last=false;uint64_t data=0;unsigned filled=0,delivered=0;
};
struct Bench {
    Vcu66_row_write_hash_join_v91l d;
    std::mt19937 rng;uint64_t cycles=0;unsigned checks=0,triples=0,ack_hash_fill=0;
    unsigned exact_bytes=0,wrong_checks=0;uint32_t epoch=1,next_token=1;
    std::deque<Row> rows;bool pending=false,poisoned=false;
    Row debt;uint32_t inputs=0,requests=0,acks=0,outputs=0,wrong=0,drops=0;
    explicit Bench(unsigned seed):rng(seed){d.power_on_reset=1;tick();d.power_on_reset=0;eval();}
    void eval(){d.clk=0;d.eval();}
    bool first_ok()const{return d.in_epoch!=0&&(d.in_addr&7)==0&&!d.in_last&&(d.in_hud||(d.in_plane<3&&(d.in_index&7)==0));}
    bool continuation_ok(const Row&r)const{
        return d.in_epoch==r.epoch&&d.in_fid==r.fid&&d.in_bank==r.bank&&bool(d.in_hud)==r.hud&&
            d.in_addr==((r.addr+r.filled)&0xfffffU)&&(!d.in_last||r.filled==7)&&
            (r.hud||(d.in_plane==r.plane&&d.in_tile==r.tile&&d.in_index==((r.index+r.filled)&63U)));
    }
    void request_equal(const Row&r){need(d.req_epoch==r.epoch&&d.req_token==r.token&&d.req_bank==r.bank&&d.req_addr==r.addr&&d.req_data==r.data&&d.req_bytes==8,"independent request row/lease");}
    void output_equal(const Row&r){
        const auto j=r.delivered;
        need(d.out_epoch==r.epoch&&d.out_fid==r.fid&&d.out_bank==r.bank&&d.out_addr==((r.addr+j)&0xfffffU)&&d.out_data==uint8_t(r.data>>(8*j)),"independent expanded output bytes/identity");
        need(bool(d.out_hud)==r.hud&&d.out_plane==r.plane&&d.out_tile==r.tile&&d.out_index==(r.hud?r.index:((r.index+j)&63U))&&bool(d.out_last)==(r.last&&j==7),"independent canonical/HUD/last metadata");
    }
    void tick(){
        eval();need(++cycles<2000000,"finite clock watchdog");
        const bool kill=d.reset||d.cancel;
        const bool input=d.in_valid&&d.in_ready,request=d.req_valid&&d.req_ready,response=d.rsp_valid&&d.rsp_ready,output=d.out_valid&&d.out_ready;
        const bool match=pending&&d.rsp_epoch==debt.epoch&&d.rsp_token==debt.token&&d.rsp_bank==debt.bank&&d.rsp_addr==debt.addr;
        if(!d.power_on_reset){
            need(bool(d.physical_pending)==pending,"physical debt model");
            if(pending)request_equal(debt);
            if(d.req_valid){need(!pending,"second physical request");auto it=rows.begin();while(it!=rows.end()&&it->filled==9)++it;need(it!=rows.end()&&it->filled==8,"request before full accepted row");request_equal(*it);}
            if(d.out_valid){need(!rows.empty()&&rows.front().filled==9,"hash before successful ACK");output_equal(rows.front());}
            if(kill)need(!d.in_ready&&!d.req_valid&&!d.out_valid,"immediate warm-kill masks");
            if(d.in_ready&&pending&&d.out_valid)++triples;
            if(input&&response&&output&&rows.back().filled==7)++ack_hash_fill;
        }
        if(d.power_on_reset){rows.clear();pending=poisoned=false;inputs=requests=acks=outputs=wrong=drops=0;next_token=1;}
        else if(d.start){need(d.drained&&!pending&&!kill,"start before physical/local drain");rows.clear();poisoned=false;inputs=requests=acks=outputs=wrong=drops=0;}
        else {
            bool malformed=false;
            // Validate accepted public tuples; this scoreboard stores transactions,
            // never mirrors DUT pointers, slot state or scheduling decisions.
            if(input){
                ++inputs;
                if(rows.empty()||rows.back().filled!=7){
                    if(!rows.empty()&&rows.back().filled<8){malformed=!continuation_ok(rows.back());}
                    else malformed=!first_ok();
                }else malformed=!continuation_ok(rows.back());
                if(!malformed){
                    if(rows.empty()||rows.back().filled>=8){Row r;r.epoch=d.in_epoch;r.token=next_token++;r.bank=d.in_bank;r.addr=d.in_addr;r.fid=d.in_fid;r.plane=d.in_plane;r.tile=d.in_tile;r.index=d.in_index;r.hud=d.in_hud;rows.push_back(r);}
                    auto&r=rows.back();r.data|=uint64_t(d.in_data)<<(8*r.filled);++r.filled;r.last=d.in_last;
                }
            }
            if(output){need(!rows.empty(),"unowned output");++outputs;++exact_bytes;if(++rows.front().delivered==8)rows.pop_front();}
            if(request){
                auto it=rows.begin();while(it!=rows.end()&&it->filled==9)++it;
                need(it!=rows.end()&&it->filled==8,"request FIFO ownership");debt=*it;pending=true;++requests;
                // 10 denotes issued but not ACKed; 9 denotes ACKed hash data.
                it->filled=10;
            }
            const bool bad=response&&!match,buserr=response&&match&&d.rsp_error;
            if(response){need(pending,"unsolicited response accepted");if(!match){++wrong;++wrong_checks;}else{pending=false;++acks;if(!poisoned&&!kill&&!malformed&&!buserr){auto it=rows.begin();while(it!=rows.end()&&it->token!=debt.token)++it;need(it!=rows.end()&&it->filled==10,"ACK row ownership");it->filled=9;}}}
            if(kill||malformed||bad||buserr){poisoned=true;rows.clear();drops=inputs-outputs;}
            if(input&&!malformed&&!pending&&rows.size()==1)poisoned=false;
            if(response&&match&&poisoned)rows.clear();
        }
        d.clk=1;d.eval();eval();
        need(d.count_inputs==inputs&&d.count_requests==requests&&d.count_acks==acks&&d.count_outputs==outputs&&d.count_wrong_acks==wrong&&d.count_drops==drops,"independent public counters");
        need(bool(d.physical_pending)==pending,"postedge physical debt");
        if(poisoned)need(!d.out_valid&&!d.req_valid,"fault publishes stale queued data");
    }
    void begin(){eval();need(d.drained&&!pending,"begin requires drain");d.start=1;tick();d.start=0;++epoch;eval();need(!d.error&&d.in_ready,"clean retry start");}
    Row make(unsigned n,bool hud_override=false){
        Row r;r.epoch=epoch;r.bank=n%3;r.fid=123;r.hud=hud_override||n>=192;r.last=n==255;
        if(r.hud){r.addr=518400+(n%64)*8;r.plane=3;r.tile=37;r.index=9;}
        else{r.plane=n/64;r.tile=(n%64)/8;r.index=(n%8)*8;const unsigned width=r.plane?360:720,base=r.plane==0?0:r.plane==1?345600:432000;r.addr=base+r.tile*8+(r.index/8)*width;}
        for(unsigned j=0;j<8;++j)r.data|=uint64_t((n*17+j*37+11)&255)<<(8*j);
        return r;
    }
    void drive(const Row&r,unsigned j){d.in_epoch=r.epoch;d.in_fid=r.fid;d.in_bank=r.bank;d.in_addr=(r.addr+j)&0xfffffU;d.in_hud=r.hud;d.in_plane=r.hud&&j?j%4:r.plane;d.in_tile=r.hud&&j?j*17:r.tile;d.in_index=r.hud?(j?j*3:r.index):((r.index+j)&63U);d.in_data=uint8_t(r.data>>(8*j));d.in_last=r.last&&j==7;}
    void byte(const Row&r,unsigned j){drive(r,j);d.in_valid=1;eval();need(d.in_ready,"directed byte blocked");tick();d.in_valid=0;eval();}
    void fill(const Row&r){for(unsigned j=0;j<8;++j)byte(r,j);}
    void accept(){d.req_ready=1;eval();need(d.req_valid,"directed offer missing");tick();d.req_ready=0;eval();}
    void rsp(const Row&r,bool error=false){d.rsp_epoch=r.epoch;d.rsp_token=r.token;d.rsp_bank=r.bank;d.rsp_addr=r.addr;d.rsp_error=error;d.rsp_valid=1;tick();d.rsp_valid=d.rsp_error=0;eval();}
    void ack(){const auto r=debt;rsp(r);}
    void drain(){d.out_ready=1;for(unsigned n=0;n<100&&!d.drained;++n){if(d.req_valid){accept();}if(pending){ack();}else tick();}d.out_ready=0;eval();need(d.drained,"finite directed drain watchdog");}
    void pass(const std::string&s){++checks;std::cout<<"{\"type\":\"directed\",\"status\":\"PASS\",\"name\":\""<<s<<"\"}\n";}
    void nominal(unsigned profile){
        begin();unsigned sent=0;bool offer=false;unsigned delay=0;
        for(unsigned n=0;n<100000&&!((sent==2048)&&d.drained);++n){
            if(!offer&&sent<2048&&(profile==0||rng()%4!=0))offer=true;
            if(offer)drive(make(sent/8),sent%8);
            d.in_valid=offer;d.req_ready=profile==0||rng()%4!=0;d.out_ready=profile==0||rng()%3!=0;
            d.rsp_valid=0;d.rsp_error=0;
            if(pending){if(delay==0){const auto r=debt;d.rsp_epoch=r.epoch;d.rsp_token=r.token;d.rsp_bank=r.bank;d.rsp_addr=r.addr;d.rsp_valid=1;}else --delay;}
            eval();const bool input=d.in_valid&&d.in_ready,request=d.req_valid&&d.req_ready;
            tick();if(input){++sent;offer=false;}if(request)delay=profile==0?4:2+rng()%15;
        }
        d.in_valid=d.req_ready=d.out_ready=d.rsp_valid=0;eval();
        need(sent==2048&&d.drained&&inputs==2048&&outputs==2048&&requests==256&&acks==256&&drops==0,"nominal complete byte conservation");
        pass(profile?"random_stalls_ack_latency_full_metadata":"fast_full_canonical_hud_expansion");
    }
    void overlap(){
        begin();fill(make(0));accept();ack(); // A hash-ready
        fill(make(1));accept(); // B physical debt, A held
        for(unsigned j=0;j<7;++j)byte(make(2),j); // C filling
        need(d.out_valid&&pending&&d.in_ready,"three-way overlap absent");
        drive(make(2),7);d.in_valid=1;d.out_ready=1;
        const auto r=debt;d.rsp_epoch=r.epoch;d.rsp_token=r.token;d.rsp_bank=r.bank;d.rsp_addr=r.addr;d.rsp_valid=1;
        tick();d.in_valid=d.out_ready=d.rsp_valid=0;drain();
        need(outputs==24&&requests==3&&acks==3&&ack_hash_fill>0,"same-edge ACK/hash/last-fill lost event");
        pass("three_slots_same_edge_ack_hash_last_fill");
    }
    void bounded_backlog(){
        begin();for(unsigned n=0;n<3;++n){fill(make(n));}
        need(d.req_valid&&!d.in_ready&&!d.physical_pending,"three-slot capacity/held offer");
        for(unsigned n=0;n<12;++n){tick();need(d.req_valid&&!d.in_ready,"held full queue changed");}
        drain();need(outputs==24&&requests==3&&acks==3,"backlog ordered drain");pass("three_slot_full_capacity_stalled_offer_ordered_drain");
    }
    void killed(bool reset_abort,bool same_edge){
        begin();fill(make(0));accept();ack();fill(make(1));accept();for(unsigned j=0;j<3;++j)byte(make(2),j);
        if(reset_abort)d.reset=1;else d.cancel=1;
        if(same_edge)ack();else tick();
        d.reset=d.cancel=0;eval();
        if(!same_edge){for(unsigned n=0;n<9;++n){tick();need(pending&&!d.drained&&!d.in_ready&&!d.out_valid,"killed physical lease escaped");}ack();}
        need(d.drained&&!pending&&outputs==0&&drops==19,"kill slot accounting/stale publication");
        pass(std::string(reset_abort?"reset":"cancel")+(same_edge?"_matching_ack_same_edge_three_slots":"_physical_debt_three_slots"));
    }
    void wrong_ack(unsigned field){
        begin();fill(make(0));accept();ack();fill(make(1));accept();fill(make(2));auto bad=debt;
        switch(field){case 0:++bad.epoch;break;case 1:++bad.token;break;case 2:bad.bank^=1;break;default:++bad.addr;}
        rsp(bad);need(d.error==0x81&&pending&&!d.out_valid&&!d.req_valid,"wrong ACK releases debt");
        for(unsigned n=0;n<9;++n){tick();}const auto right=debt;ack();need(d.drained&&drops==24&&outputs==0,"poisoned matching ACK publishes");
        // Old matching tuple replay has no ready lease after retirement.
        d.rsp_valid=1;d.rsp_epoch=right.epoch;d.rsp_token=right.token;d.rsp_bank=right.bank;d.rsp_addr=right.addr;tick();d.rsp_valid=0;
        pass("wrong_ack_field_"+std::to_string(field)+"_retains_debt_then_retry");
    }
    void malformed(unsigned field,bool first){
        begin();if(!first){fill(make(0));accept();byte(make(1),0);}auto r=make(first?0:1);drive(r,first?0:1);
        switch(field){case 0:d.in_epoch=first?0:d.in_epoch+1;break;case 1:++d.in_fid;break;case 2:d.in_bank^=1;break;case 3:d.in_plane=3;break;case 4:++d.in_tile;break;case 5:++d.in_index;break;case 6:++d.in_addr;break;case 7:d.in_hud^=1;break;default:d.in_last=1;}
        d.in_valid=1;tick();d.in_valid=0;eval();need(d.error==(first?0x83:0x84)&&!d.out_valid&&!d.req_valid,"malformed tuple not poisoned");if(pending)ack();need(d.drained,"malformed failed debt drain");
        pass(std::string(first?"first":"continuation")+"_malformed_"+std::to_string(field));
    }
    void token_wrap(){
        begin();need(d.drained,"token fixture requires drain");
        d.rootp->cu66_row_write_hash_join_v91l__DOT__next_token=0xfffffffeU;next_token=0xfffffffeU;
        for(unsigned n=0;n<4;++n){fill(make(n));accept();need(debt.token==uint32_t(0xfffffffeU+n),"token wrap model");if(n==1){d.cancel=1;tick();d.cancel=0;ack();begin();}else{ack();drain();}}
        fill(make(4));accept();auto bad=debt;++bad.token;rsp(bad);need(pending&&d.error==0x81,"wrapped wrong-token ACK debt");ack();begin();fill(make(5));accept();need(debt.token==3,"warm error/start reset token");ack();drain();pass("token_wrap_warm_cancel_wrong_ack_error_retention");
    }
    void bus_error(){begin();fill(make(0));accept();ack();fill(make(1));accept();fill(make(2));auto r=debt;d.out_ready=1;rsp(r,true);d.out_ready=0;need(d.error==0x82&&d.drained&&drops==23&&outputs==1&&!d.out_valid,"bus error queued publication/same-edge prior ACKed byte");pass("bus_error_drops_all_local_and_matching_debt");}
    void malformed_request_sameedge(){begin();fill(make(0));drive(make(1),0);d.in_epoch=0;d.in_valid=1;d.req_ready=1;tick();d.in_valid=d.req_ready=0;eval();need(pending&&d.error==0x83,"same-edge malformed input lost accepted physical debt");ack();need(d.drained&&drops==9,"malformed and accepted request drain");pass("malformed_first_and_request_same_edge_preserves_debt");}
};
int main(int argc,char**argv){try{Verilated::commandArgs(argc,argv);need(argc==2,"seed required");Bench b(unsigned(std::stoul(argv[1])));b.nominal(0);b.nominal(1);b.overlap();b.bounded_backlog();for(bool reset:{false,true})for(bool same:{false,true})b.killed(reset,same);for(unsigned f=0;f<4;++f)b.wrong_ack(f);b.bus_error();for(unsigned f=0;f<9;++f)b.malformed(f,false);for(unsigned f:{0U,3U,5U,6U,8U})b.malformed(f,true);b.token_wrap();b.malformed_request_sameedge();b.begin();b.fill(b.make(255));b.accept();b.ack();b.drain();b.pass("clean_final_hud_retry");need(b.triples>0&&b.ack_hash_fill>0,"overlap coverage");std::cout<<"{\"status\":\"TEST_PASS\",\"seed\":"<<argv[1]<<",\"directed_checks\":"<<b.checks<<",\"exact_bytes\":"<<b.exact_bytes<<",\"triple_overlap_cycles\":"<<b.triples<<",\"same_edge_ack_hash_last_fill\":"<<b.ack_hash_fill<<",\"wrong_ack_checks\":"<<b.wrong_checks<<",\"cycles\":"<<b.cycles<<"}\n";return 0;}catch(const std::exception&e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
