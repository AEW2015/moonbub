#include "Vcanonical_line_reader.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

// Directed adapter contract; separate from full-frame consumer qualification.
class Test {
    VerilatedContext context;
    Vcanonical_line_reader dut{&context};
    unsigned clocks = 0;
    unsigned checks = 0;
public:
    Test() {
        dut.clk=0; dut.reset=0; dut.start=0; dut.cancel=0; dut.finish=0;
        dut.start_epoch=0; dut.probe_valid=1; dut.probe_addr=0; dut.probe_epoch=17;
        dut.byte_req_valid=0; dut.byte_req_addr=0; dut.byte_req_epoch=17;
        dut.byte_rsp_ready=0; dut.mem_req_ready=0; dut.mem_rsp_valid=0;
        dut.mem_rsp_epoch=17; dut.mem_rsp_error=0;
        for(unsigned i=0;i<4;++i) dut.mem_rsp_data[i]=0;
        dut.reset=1; tick(); dut.reset=0; dut.eval();
    }
    void require(bool ok, const std::string& name) {
        if(!ok) throw std::runtime_error(name+" at clock "+std::to_string(clocks));
        ++checks;
    }
    void tick() {
        if(++clocks>400) throw std::runtime_error("finite 400-clock watchdog");
        dut.clk=0; dut.eval(); context.timeInc(5000);
        dut.clk=1; dut.eval(); context.timeInc(5000);
        dut.clk=0; dut.eval();
    }
    void probe(uint32_t address, uint32_t epoch, bool expected, uint8_t data=0) {
        dut.probe_addr=address; dut.probe_epoch=epoch; dut.eval();
        require(bool(dut.probe_hit)==expected,"probe eligibility at "+std::to_string(address));
        require(dut.probe_data==(expected?data:0),"probe payload or zero when unavailable");
    }
    void start(uint32_t epoch) {
        require(dut.start_ready,"new lease ready");
        dut.start=1; dut.start_epoch=epoch; dut.eval();
        require(!dut.probe_hit,"start edge suppresses stale probe");
        tick(); dut.start=0; dut.eval();
    }
    void request(uint32_t address, uint32_t epoch) {
        dut.byte_req_valid=1; dut.byte_req_addr=address; dut.byte_req_epoch=epoch; dut.eval();
        require(dut.byte_req_ready,"byte request can acquire lease");
        tick(); dut.byte_req_valid=0; dut.eval();
        require(dut.byte_pending&&!dut.probe_hit,"byte lease excludes probe before physical offer");
        require(dut.mem_req_valid&&dut.mem_req_addr==(address&~15u),"aligned physical offer");
    }
    void accept_read() {
        dut.mem_req_ready=1; tick(); dut.mem_req_ready=0; dut.eval();
        require(dut.physical_pending&&!dut.probe_hit,"accepted physical owner excludes probe");
    }
    void respond(uint32_t epoch, unsigned base, bool error=false) {
        for(unsigned w=0;w<4;++w) {
            uint32_t value=0;
            for(unsigned b=0;b<4;++b) value|=uint32_t((base+w*4+b)&255u)<<(b*8);
            dut.mem_rsp_data[w]=value;
        }
        dut.mem_rsp_epoch=epoch; dut.mem_rsp_error=error; dut.mem_rsp_valid=1; tick();
        dut.mem_rsp_valid=0; dut.mem_rsp_error=0; dut.eval();
    }
    void retire_byte() {
        require(dut.byte_rsp_valid,"byte response available");
        dut.byte_rsp_ready=1; tick(); dut.byte_rsp_ready=0; dut.eval();
        require(!dut.byte_rsp_valid&&!dut.byte_pending,"byte response owner retired");
    }
    void fill(uint32_t address, uint32_t epoch, unsigned base) {
        request(address,epoch); accept_read(); respond(epoch,base);
        require(!dut.physical_pending&&dut.byte_rsp_valid,"matching ACK installs held response");
        require(!dut.probe_hit,"held byte response excludes probe after ACK");
        require(!dut.byte_rsp_error&&dut.byte_rsp_data==((base+(address&15u))&255u),"byte response exact");
        tick(); require(!dut.probe_hit,"held response continues excluding probe");
        retire_byte();
    }
    void run() {
        probe(0,17,false); start(17); probe(0,17,false);
        fill(0,17,0); probe(4,17,true,4); probe(15,17,true,15);
        probe(4,18,false); probe(16,17,false); probe(518400,17,false);
        dut.probe_valid=0; probe(4,17,false); dut.probe_valid=1;
        probe(4,17,true,4);
        const uint64_t before=dut.count_byte_requests;
        for(unsigned i=0;i<16;++i) { probe(i,17,true,uint8_t(i)); tick(); }
        require(dut.count_byte_requests==before&&dut.count_physical_requests==1,
                "read-only probes create no byte or physical leases");
        request(16,17); probe(4,17,false); accept_read(); respond(17,16);
        probe(4,17,false); retire_byte(); probe(4,17,false); probe(31,17,true,31);

        // A 360-byte chroma row ends halfway through an aligned16B line.
        fill(345952,17,100); probe(345959,17,true,107); probe(345960,17,true,108);
        probe(345967,17,true,115); probe(31,17,true,31);
        fill(432352,17,200); probe(432359,17,true,207); probe(432360,17,true,208);
        probe(432367,17,true,215); probe(345960,17,true,108); probe(31,17,true,31);
        require(dut.line_valid==7,"all three plane payload slots remain independent");

        dut.finish=1; probe(31,17,false); tick(); dut.finish=0;
        probe(31,17,false); require(!dut.busy,"finish closes lease");
        start(17); probe(31,17,false); probe(345960,17,false); probe(432360,17,false);
        fill(0,17,40); probe(3,17,true,43);
        dut.cancel=1; probe(3,17,false); tick(); dut.cancel=0;
        probe(3,17,false); require(!dut.busy,"cancel invalidates idle cache");

        start(18); fill(0,18,60); probe(3,18,true,63);
        dut.reset=1; probe(3,18,false); tick(); dut.reset=0;
        probe(3,18,false); require(!dut.busy,"reset invalidates idle cache");

        start(19); request(0,19); accept_read(); respond(18,70);
        require(dut.error==1&&dut.physical_pending&&!dut.start_ready,
                "wrong-epoch ACK cannot release accepted physical owner");
        probe(0,19,false); retire_byte(); respond(19,70);
        require(!dut.busy&&dut.start_ready,"matching old ACK drains failed lease");
        probe(0,19,false); start(20); probe(0,20,false);
        request(0,20); accept_read(); dut.cancel=1; tick(); dut.cancel=0;
        require(dut.physical_pending&&!dut.start_ready,"cancel retains accepted physical owner");
        probe(0,20,false); retire_byte(); respond(20,80);
        require(!dut.busy,"matching ACK drains canceled lease"); probe(0,20,false);
        start(21); request(0,21); accept_read(); dut.reset=1; tick(); dut.reset=0;
        require(dut.physical_pending&&!dut.start_ready,"reset retains accepted physical owner");
        probe(0,21,false); retire_byte(); respond(21,90);
        require(!dut.busy,"matching ACK drains reset lease"); probe(0,21,false);
        start(22); fill(0,22,110); probe(3,22,true,113);
        request(16,22); accept_read(); respond(22,120,true);
        require(dut.error==2&&!dut.physical_pending&&dut.byte_pending,
                "matching bus-error ACK releases only physical owner");
        require(dut.line_valid==0&&dut.byte_rsp_valid&&dut.byte_rsp_error,
                "bus-error ACK invalidates all payload validity and returns error");
        require(dut.byte_rsp_epoch==22&&dut.byte_rsp_data==0&&!dut.start_ready,
                "error byte response retains epoch and lease until retirement");
        probe(0,22,false); probe(16,22,false); tick();
        require(dut.byte_rsp_valid&&dut.byte_rsp_error&&!dut.start_ready,
                "held error response remains owned");
        retire_byte(); require(!dut.busy&&dut.start_ready,"error byte retirement closes failed lease");
        start(23); probe(0,23,false); fill(0,23,130); probe(3,23,true,133);
        dut.finish=1; tick(); dut.finish=0; require(!dut.busy,"fresh lease recovers after bus error");
        dut.final();
        std::cout << "{\"status\":\"PASS_DIRECT_PROBE_OWNERSHIP\",\"checks\":" << checks
                  << ",\"clocks\":" << clocks << "}\n";
    }
};
int main() {
    try { Test test; test.run(); return 0; }
    catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
