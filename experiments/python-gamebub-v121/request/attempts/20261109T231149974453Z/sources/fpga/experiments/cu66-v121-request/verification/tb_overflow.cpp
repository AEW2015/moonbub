#include "Vbyte_refill_queue_v91i2b.h"
#include "verilated.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>

int main(int argc,char **argv) {
    if(argc!=2)throw std::runtime_error("overflow harness requires first address");
    const uint32_t first=uint32_t(std::stoul(argv[1]));
    Vbyte_refill_queue_v91i2b d;
    d.clk=0;d.reset=1;d.cancel=0;d.start=0;d.clear_stats=0;
    d.start_offset=first;d.start_length=4;d.start_epoch=73;
    d.req_ready=1;d.out_ready=1;d.rsp_valid=0;d.rsp_addr=0;d.rsp_epoch=0;d.rsp_data=0;
    auto edge=[&](){d.clk=0;d.eval();d.clk=1;d.eval();};
    edge();d.reset=0;d.start=1;edge();d.start=0;
    bool pending=false;uint32_t address=0,accepted=0;
    for(unsigned k=0;k<8;++k) {
        d.clk=0;d.rsp_valid=pending;d.rsp_addr=address;d.rsp_epoch=73;d.rsp_data=9;d.eval();
        pending=d.req_valid&&d.req_ready;address=d.req_addr;
        if(pending) {
            std::cout<<"NEGATIVE_ACCEPT edge="<<k<<" ordinal="<<accepted<<" address="<<address<<std::endl;
            ++accepted;
        }
        d.clk=1;d.eval();
    }
    std::cerr<<"MISSING_EXPECTED_SPAN_OVERFLOW_ASSERTION\n";return 1;
}
