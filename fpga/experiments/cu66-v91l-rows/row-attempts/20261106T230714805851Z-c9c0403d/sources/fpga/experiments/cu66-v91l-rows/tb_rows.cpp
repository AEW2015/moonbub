#include "Vcu66_row_write_hash_join_v91l.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <string>

static void need(bool ok,const std::string &s){if(!ok)throw std::runtime_error(s);}
struct Row {
    uint32_t epoch,token,bank,addr,fid,plane,tile,index;bool hud,last;uint64_t data;
    bool operator==(const Row &b)const{return epoch==b.epoch&&token==b.token&&bank==b.bank&&addr==b.addr&&fid==b.fid&&plane==b.plane&&tile==b.tile&&index==b.index&&hud==b.hud&&last==b.last&&data==b.data;}
};
struct Bench {
    Vcu66_row_write_hash_join_v91l d;std::mt19937 rng;uint64_t cycle=0;unsigned checks=0;uint32_t epoch=1,next_token=1;
    explicit Bench(unsigned seed):rng(seed){d.power_on_reset=1;tick();d.power_on_reset=0;tick();}
    void eval(){d.clk=0;d.eval();}
    void tick(){eval();d.clk=1;d.eval();++cycle;need(cycle<2000000,"watchdog");}
    void begin(){need(d.drained&&!d.physical_pending,"start before drain");d.start=1;tick();d.start=0;eval();++epoch;need(d.in_ready&&!d.error,"start failed");}
    Row make(unsigned n){
        Row r{};r.epoch=epoch;r.token=next_token;r.bank=2;r.fid=31;r.hud=n>=192;r.last=n==255;
        if(r.hud){r.addr=518400+(n-192)*8;r.plane=r.tile=r.index=0;}
        else {r.plane=n/64;r.tile=(n%64)/8;r.index=(n%8)*8;unsigned w=r.plane?360:720;unsigned base=r.plane==0?0:r.plane==1?345600:432000;r.addr=base+r.tile*8+(r.index/8)*w;}
        for(unsigned j=0;j<8;++j)r.data|=uint64_t((n*17+j*37+11)&255)<<(8*j);
        return r;
    }
    void drive(const Row &r,unsigned j){
        d.in_epoch=r.epoch;d.in_fid=r.fid;d.in_bank=r.bank;d.in_addr=r.addr+j;d.in_hud=r.hud;
        d.in_plane=r.plane;d.in_tile=r.tile;d.in_index=r.hud?0:r.index+j;d.in_data=uint8_t(r.data>>(8*j));d.in_last=r.last&&j==7;
    }
    void byte(const Row &r,unsigned j){eval();need(d.in_ready,"fill input not ready");drive(r,j);d.in_valid=1;tick();d.in_valid=0;eval();}
    void fill(const Row &r){for(unsigned j=0;j<8;++j)byte(r,j);++next_token;need(d.req_valid&&d.req_bytes==8,"complete row not offered");check_request(r);}
    void check_request(const Row &r){need(d.req_epoch==r.epoch&&d.req_token==r.token&&d.req_bank==r.bank&&d.req_addr==r.addr&&d.req_data==r.data&&d.req_bytes==8,"row request differs from input");}
    void accept(){d.req_ready=1;tick();d.req_ready=0;eval();need(d.physical_pending&&d.rsp_ready&&!d.req_valid,"accepted row lease missing");}
    void response(const Row &r,bool error=false){d.rsp_epoch=r.epoch;d.rsp_token=r.token;d.rsp_bank=r.bank;d.rsp_addr=r.addr;d.rsp_error=error;d.rsp_valid=1;tick();d.rsp_valid=d.rsp_error=0;eval();}
    void check_output(const Row &r,unsigned j){
        need(d.out_valid&&!d.physical_pending&&d.out_epoch==r.epoch&&d.out_fid==r.fid&&d.out_bank==r.bank&&d.out_addr==r.addr+j&&d.out_data==uint8_t(r.data>>(8*j)),"actual hash output data/identity differs");
        need(d.out_hud==r.hud&&d.out_plane==r.plane&&d.out_tile==r.tile&&d.out_index==(r.hud?0:r.index+j)&&bool(d.out_last)==(r.last&&j==7),"actual hash output tuple/last differs");
    }
    void deliver(const Row &r,unsigned j){check_output(r,j);d.out_ready=1;tick();d.out_ready=0;eval();}
    void pass(const std::string &name){++checks;std::cout<<"{\"type\":\"directed\",\"name\":\""<<name<<"\",\"status\":\"PASS\"}\n";}
    void nominal(unsigned profile){
        begin();const auto start=cycle;
        for(unsigned n=0;n<256;++n){auto r=make(n);fill(r);
            for(unsigned k=0;k<(profile?rng()%5:0);++k){tick();need(d.req_valid&&!d.out_valid,"held offer lost");check_request(r);}
            accept();d.in_valid=1;d.in_data^=255;
            for(unsigned k=0;k<(profile?5+rng()%7:5);++k){tick();need(!d.in_ready&&!d.out_valid&&d.physical_pending,"pending row admits/outputs before ACK");check_request(r);}
            d.in_valid=0;response(r);
            for(unsigned j=0;j<8;++j){
                for(unsigned k=0;k<(profile?rng()%5:0);++k){tick();check_output(r,j);need(!d.in_ready&&!d.req_valid,"held delivery admits another row");}
                check_output(r,j);
                std::cout<<"{\"type\":\"sample\",\"profile\":"<<profile<<",\"row\":"<<n<<",\"byte\":"<<j<<",\"epoch\":"<<d.out_epoch<<",\"token\":"<<d.req_token<<",\"bank\":"<<unsigned(d.out_bank)<<",\"addr\":"<<d.out_addr<<",\"data\":"<<unsigned(d.out_data)<<",\"hud\":"<<unsigned(d.out_hud)<<",\"fid\":"<<d.out_fid<<",\"plane\":"<<unsigned(d.out_plane)<<",\"tile\":"<<d.out_tile<<",\"index\":"<<unsigned(d.out_index)<<",\"last\":"<<unsigned(d.out_last)<<"}\n";
                deliver(r,j);
            }
            need(d.drained&&!d.out_valid&&!d.physical_pending,"delivered row not drained");
        }
        need(d.count_inputs==2048&&d.count_requests==256&&d.count_acks==256&&d.count_outputs==2048,"nominal row conservation");
        std::cout<<"{\"type\":\"case\",\"status\":\"PASS\",\"profile\":"<<profile<<",\"rows\":256,\"bytes\":2048,\"cycles\":"<<cycle-start<<"}\n";
        pass(profile?"slow_exact_row_ack_before_all_hash_bytes":"fast_exact_row_ack_before_all_hash_bytes");
    }
    void kill_local(bool reset,unsigned stage){
        begin();auto r=make(4);
        if(stage==0){for(unsigned j=0;j<3;++j)byte(r,j);++next_token;}
        else {fill(r);if(stage==2){accept();response(r);for(unsigned j=0;j<3;++j)deliver(r,j);}}
        if(reset)d.reset=1;else d.cancel=1;
        d.req_ready=d.out_ready=1;eval();need(!d.req_valid&&!d.out_valid&&!d.in_ready,"kill exposes local work");tick();d.reset=d.cancel=d.req_ready=d.out_ready=0;eval();
        need(d.drained&&!d.physical_pending&&!d.out_valid,"local kill retained owner");
        pass(std::string(reset?"reset":"cancel")+std::array<std::string,3>{{"_partial_fill","_unaccepted_offer","_partial_hash_delivery"}}[stage]);
    }
    void kill_pending(bool reset,bool same_edge){
        begin();auto r=make(8);fill(r);accept();if(reset)d.reset=1;else d.cancel=1;
        if(same_edge)response(r);else tick();
        d.reset=d.cancel=0;eval();
        if(!same_edge){for(unsigned i=0;i<9;++i){tick();need(d.physical_pending&&!d.drained&&!d.in_ready&&!d.out_valid,"pending kill released without ACK");check_request(r);}response(r);}
        need(d.drained&&!d.out_valid&&!d.physical_pending&&d.count_outputs==0,"killed row emitted hash bytes");
        pass(std::string(reset?"reset":"cancel")+(same_edge?"_matching_ack_same_edge":"_pending_row_ack_drain"));
    }
    void wrong_ack(unsigned field){
        begin();auto r=make(12);fill(r);accept();auto bad=r;
        switch(field){case 0:++bad.epoch;break;case 1:++bad.token;break;case 2:bad.bank^=1;break;default:++bad.addr;}
        response(bad);need(d.error&&d.physical_pending&&!d.out_valid&&!d.drained,"wrong ACK retired row");
        for(unsigned i=0;i<9;++i){tick();check_request(r);need(d.physical_pending&&!d.in_ready&&!d.out_valid,"wrong ACK owner lost");}
        response(r);need(d.drained&&!d.out_valid&&d.count_outputs==0,"true ACK after fault leaked row");
        pass(std::array<std::string,4>{{"wrong_epoch_ack_retains_row","wrong_token_ack_retains_row","wrong_bank_ack_retains_row","wrong_addr_ack_retains_row"}}[field]);
    }
    void bus_error(){begin();auto r=make(16);fill(r);accept();response(r,true);need(d.error&&d.drained&&!d.out_valid&&d.count_outputs==0,"error ACK leaked data");pass("matching_bus_error_drains_without_hash");}
    void bad_fill(unsigned field){
        begin();auto r=make(20);byte(r,0);++next_token;drive(r,1);
        switch(field){case 0:++d.in_epoch;break;case 1:++d.in_fid;break;case 2:d.in_bank^=1;break;case 3:d.in_plane^=1;break;case 4:++d.in_tile;break;case 5:++d.in_index;break;case 6:++d.in_addr;break;case 7:d.in_hud^=1;break;default:d.in_last=1;}
        d.in_valid=1;tick();d.in_valid=0;eval();need(d.error&&d.drained&&!d.req_valid&&!d.physical_pending&&!d.out_valid,"bad fill tuple issued partial row");
        pass(std::array<std::string,9>{{"fill_epoch_mismatch","fill_fid_mismatch","fill_bank_mismatch","fill_plane_mismatch","fill_tile_mismatch","fill_index_mismatch","fill_address_mismatch","fill_kind_mismatch","fill_early_last_mismatch"}}[field]);
    }
    void bad_first(unsigned field){
        begin();auto r=make(24);drive(r,0);
        switch(field){case 0:d.in_epoch=0;break;case 1:++d.in_addr;break;case 2:++d.in_index;break;case 3:d.in_plane=3;break;default:d.in_last=1;}
        d.in_valid=1;tick();d.in_valid=0;eval();need(d.error==0x83&&d.drained&&!d.req_valid&&!d.physical_pending&&!d.out_valid,"invalid first byte acquired row");
        pass(std::array<std::string,5>{{"first_zero_epoch","first_unaligned_address","first_unaligned_index","first_invalid_plane","first_early_last"}}[field]);
    }
    void retry(){begin();auto r=make(255);fill(r);accept();response(r);for(unsigned j=0;j<8;++j)deliver(r,j);need(d.drained&&!d.error,"row retry failed");pass("clean_row_retry_after_faults");}
};
int main(int argc,char **argv){try{need(argc==2,"seed arg");unsigned seed=unsigned(std::stoul(argv[1]));Bench b(seed);
 b.nominal(0);b.nominal(1);for(bool r:{false,true}){for(unsigned s=0;s<3;++s)b.kill_local(r,s);b.kill_pending(r,false);b.kill_pending(r,true);}
 for(unsigned f=0;f<4;++f){b.wrong_ack(f);}b.bus_error();for(unsigned f=0;f<9;++f){b.bad_fill(f);}for(unsigned f=0;f<5;++f){b.bad_first(f);}b.retry();need(b.checks==32,"directed count");
 std::cout<<"{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"seed\":"<<seed<<",\"directed_checks\":"<<b.checks<<",\"exact_bytes\":4096,\"cycles\":"<<b.cycle<<"}\n";return 0;
}catch(const std::exception &e){std::cerr<<"TEST_FAIL "<<e.what()<<'\n';return 1;}}
