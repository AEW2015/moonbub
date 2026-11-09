#include "Vscratch_probe.h"
#include "verilated.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

static void require(bool value,const std::string& message) {
    if(!value)throw std::runtime_error(message);
}
class Scratch {
public:
    Vscratch_probe d;
    bool allow=false,pending=false,ack=false,stale=false,ack_error=false;
    unsigned owner_epoch=0,owner_address=0,next_epoch=0;
    uint64_t edges=0,accepts=0,acks=0;
    std::array<uint32_t,4> owner_data{};
    Scratch() {
        d.clk=0;d.reset=1;d.begin_valid=0;d.begin_blocks=1;d.begin_raw=1;
        d.begin_serial_clear=0;d.begin_overlap=1;d.begin_prefetch=0;d.begin_tile_overlap=0;d.begin_count1=0;d.begin_count2=0;d.begin_count3=0;d.begin_epoch=0;
        d.coef_valid=0;d.coef_band=0;d.coef_block=0;d.coef_index=0;d.coef_value=1;d.coef_epoch=0;
        d.band_end_valid=0;d.band_end_band=0;d.band_end_epoch=0;
        d.seal_valid=0;d.seal_epoch=0;d.abort_valid=0;d.abort_epoch=0;d.dense_ready=0;
        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;
        for(unsigned j=0;j<4;++j)d.mem_rsp_data[j]=0;
        tick();d.reset=0;
    }
    void tick() {
        require(++edges<100000,"scratch directed watchdog");
        d.mem_req_ready=allow&&!pending;
        d.mem_rsp_valid=pending&&(ack||stale);d.mem_rsp_epoch=owner_epoch+unsigned(stale);
        d.mem_rsp_error=ack_error;
        d.clk=0;d.eval();need(!d.mismatch,"historical whole scratch mismatch");
        const bool accepted=d.mem_req_valid&&d.mem_req_ready;
        const bool retired=d.mem_rsp_valid&&d.mem_rsp_ready&&!stale;
        if(accepted) {
            require(!pending&&d.mem_req_write,"directed physical write ownership");
            owner_epoch=d.mem_req_epoch;owner_address=d.mem_req_addr;
            require((owner_address&15)==0&&owner_address+16<=d.used_bytes,"directed accepted address range");
            for(unsigned j=0;j<4;++j)owner_data[j]=d.mem_req_data[j];
        }
        d.clk=1;d.eval();need(!d.mismatch,"historical whole scratch mismatch");d.clk=0;d.eval();need(!d.mismatch,"historical whole scratch mismatch");
        if(retired){require(pending,"directed ACK without owner");pending=false;++acks;}
        if(accepted){pending=true;++accepts;}
        require(bool(d.debug_outstanding)==pending,"directed accepted-owner flag");
        if(pending) {
            require(d.mem_req_epoch==owner_epoch&&d.mem_req_addr==owner_address,"accepted owner fields mutated");
            for(unsigned j=0;j<4;++j)require(d.mem_req_data[j]==owner_data[j],"accepted write payload mutated");
            require(!d.begin_ready,"new allocation while accepted request exists");
        }
        ack=false;stale=false;ack_error=false;
    }
    void begin() {
        require(!pending,"begin test has external hazard");
        d.begin_epoch=++next_epoch;d.begin_valid=1;d.eval();need(!d.mismatch,"historical whole scratch mismatch");require(d.begin_ready,"begin not ready");tick();d.begin_valid=0;
        require(d.busy&&!d.error,"begin failed");
        d.coef_epoch=next_epoch;
    }
    void coefficient(unsigned index,int value=1) {
        d.coef_index=index;d.coef_value=uint16_t(value);d.coef_valid=1;d.eval();need(!d.mismatch,"historical whole scratch mismatch");
        require(d.coef_ready,"directed coefficient not ready");tick();d.coef_valid=0;
        if(value>=-2048&&value<=2048)tick();
    }
    void first_line() {for(unsigned i=0;i<8;++i)coefficient(i);require(d.debug_write_slot_valid,"first line not queued");}
    void second_full() {for(unsigned i=8;i<16;++i)coefficient(i);require(d.debug_assembler_full&&d.debug_state==26,"second full line not held");}
    void physical_ack(bool error=false) {require(pending,"ACK test has no owner");ack=true;ack_error=error;tick();}
    void cancel() {d.abort_valid=1;d.abort_epoch=next_epoch;tick();d.abort_valid=0;}
    void idle() {if(pending)physical_ack();for(unsigned j=0;j<3&&d.busy;++j)tick();require(!pending&&!d.busy,"drain did not idle");}
};
int historical_hazards_main(int argc,char** argv) {
    Verilated::commandArgs(argc,argv);
    try {
        unsigned checks=0;uint64_t edges=0,accepts=0,acks=0;
        auto report=[&](const Scratch& s){edges+=s.edges;accepts+=s.accepts;acks+=s.acks;++checks;};
        {Scratch s;s.begin();s.first_line();s.coefficient(8,2049);
            require(s.d.error==3&&!s.pending&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes,"unaccepted semantic failure retained offer");
            require(!s.d.busy,"unaccepted failure left hazard");s.cancel();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.coefficient(8);s.coefficient(9,2049);
            require(s.pending&&s.d.busy&&s.d.debug_state==25&&s.d.error==3&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes,"accepted semantic failure did not drain");
            for(unsigned j=0;j<31;++j){s.tick();require(s.d.busy&&s.pending,"accepted error lost hazard");}
            s.idle();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;const auto before=s.accepts;s.coefficient(8,2049);
            require(s.accepts==before+1&&s.pending&&s.d.busy&&s.d.debug_state==25&&s.d.error==3,"same-edge accept/semantic failure lost owner");
            s.idle();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.coefficient(8);
            s.d.abort_valid=1;s.d.abort_epoch=s.next_epoch-1;s.tick();s.d.abort_valid=0;
            require(s.pending&&s.d.debug_write_slot_valid&&s.d.debug_assembly_bytes==2&&s.d.busy&&!s.d.error,"stale abort cancelled active owner");
            s.cancel();require(s.pending&&s.d.busy&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes,"matching abort lost accepted owner");
            s.idle();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.second_full();s.stale=true;s.tick();
            require(s.pending&&s.d.busy&&s.d.error==6&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes,"stale ACK retired actual owner");
            s.idle();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.second_full();s.physical_ack(true);
            require(!s.pending&&s.d.error==5&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes&&!s.d.sealed,"error ACK transferred waiting line");
            s.cancel();s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.second_full();const auto before=s.accepts;
            s.physical_ack();require(!s.pending&&s.d.debug_write_slot_valid&&!s.d.debug_assembler_full&&s.accepts==before,"ACK/enqueue accepted replacement too soon");
            s.tick();require(s.pending&&s.owner_address==48&&s.accepts==before+1,"ACK/enqueue replacement address");
            s.cancel();s.idle();report(s);}
        {Scratch s;s.begin();s.first_line();s.allow=true;s.tick();s.coefficient(8);s.d.reset=1;
            for(unsigned j=0;j<13;++j){s.tick();require(s.pending&&s.d.busy&&!s.d.debug_write_slot_valid&&!s.d.debug_assembly_bytes,"held reset dropped hazard");}
            s.physical_ack();require(!s.pending&&!s.d.begin_ready,"held reset permitted allocation");s.tick();s.d.reset=0;s.begin();report(s);}
        {Scratch s;s.begin();s.first_line();s.d.abort_valid=1;s.d.abort_epoch=s.next_epoch-1;
            for(unsigned j=0;j<17;++j){s.tick();require(s.d.mem_req_valid&&s.d.debug_write_slot_valid&&!s.pending,"stale abort withdrew offered write");}
            s.d.abort_valid=0;s.cancel();s.begin();report(s);}
        std::cout<<"{\"type\":\"scratch_hazards_verdict\",\"status\":\"TEST_PASS\",\"directed_checks\":"<<checks
            <<",\"edges\":"<<edges<<",\"physical_accepts\":"<<accepts<<",\"physical_acks\":"<<acks<<"}\n";
        return 0;
    }catch(const std::exception& e){std::cerr<<"TEST_FAIL "<<e.what()<<"\n";return 1;}
}
