#include "Vheader_index_pair.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

static void check(bool b, const char* message) { if (!b) throw std::runtime_error(message); }
static void put(std::vector<uint8_t>& p, unsigned at, uint32_t value) {
    for (unsigned i=0; i<4; ++i) p.at(at+i)=uint8_t(value>>(8*i));
}
static void crc(std::vector<uint8_t>& p) {
    uint32_t c=~uint32_t(0);
    for (size_t i=0; i+4<p.size(); ++i) {
        c^=p[i]; for (unsigned j=0; j<8; ++j) c=(c>>1)^((c&1)?0xedb88320U:0U);
    }
    put(p,unsigned(p.size()-4),~c);
}
static std::vector<uint8_t> packet(bool raw) {
    const unsigned n=raw ? 42+128+4 : 42+7+18+4;
    std::vector<uint8_t> p(n,0);p[0]='B';p[1]='R';p[2]='8';p[3]='8';p[4]=1;p[5]=raw;
    put(p,6,1);p[10]=1;
    if(raw) put(p,14,128);
    else { put(p,14,7); for(unsigned i=1;i<4;++i)put(p,14+4*i,6);p[43]=255;put(p,44,1);p[48]=0x80; }
    crc(p);return p;
}
struct Sim {
    Vheader_index_pair d;
    uint64_t cycles=0, comparisons=0; unsigned purposes=0;
    void eval() { d.eval(); ++comparisons; check(d.pair_equal,"public output mismatch"); }
    void edge() { d.clk=0;eval();d.clk=1;eval();++cycles;d.clk=0;eval(); }
    void reset() { d.reset=1;edge();d.reset=0; }
    void start(const std::vector<uint8_t>& p) {
        d.in_valid=0;d.packet_bytes=p.size();d.blocks=1;d.epoch=9;d.start=1;edge();d.start=0;
    }
    void send(const std::vector<uint8_t>& p) {
        for(size_t i=0;i<p.size();++i) {
            d.in_valid=1;d.in_data=p[i];d.in_last=i+1==p.size();
            d.clk=0;eval();check(d.in_ready,"not ready while receiving");edge();
        }
        d.in_valid=0;d.in_last=0;
    }
    void finish() {
        for(unsigned n=0;n<50000 && !d.done && !d.error;++n) {
            d.clk=0;eval();if(d.stage_read_req)purposes|=1U<<d.stage_purpose;edge();
        }
        check(d.done && !d.error,"valid packet did not finish");edge();
    }
};
int main(int argc,char**argv) {
    Verilated::commandArgs(argc,argv);
    try {
        Sim s;s.d.meta_ready=1;s.d.out_ready=1;s.d.band_end_ready=1;s.reset();
        auto raw=packet(true), coded=packet(false);
        for(unsigned race=0;race<4;++race) {
            s.start(raw);s.d.in_valid=1;s.d.in_data=raw[0];s.d.in_last=0;s.edge();
            // Assert controls while input valid is held: reset > abort > start.
            s.d.reset=(race==0 || race==3);s.d.abort_packet=(race==1 || race==3);s.d.start=(race==2 || race==3);
            s.edge();s.d.reset=0;s.d.abort_packet=0;s.d.start=0;s.d.in_valid=0;
            s.start(coded);s.send(coded);s.finish();
        }
        s.start(raw);s.send(raw);s.finish();
        check((s.purposes&15)==15,"fetch modes not all exercised");
        std::cout<<"{\"status\":\"TEST_PASS\",\"cycles\":"<<s.cycles<<",\"evaluations\":"<<s.comparisons<<",\"race_cases\":4,\"fetch_purpose_mask\":"<<s.purposes<<",\"coded_packets\":4,\"raw_packets\":1}"<<std::endl;
        return 0;
    } catch(const std::exception& e) { std::cerr<<"TEST_FAIL "<<e.what()<<std::endl;return 1; }
}
