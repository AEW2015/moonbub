#include <verilated.h>
#include "Vadmission_probe.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>

static std::set<uint32_t> domain(){
    std::set<uint32_t> ts;
    for(uint32_t t=0;t<8192;++t)ts.insert(t);
    for(unsigned bit=0;bit<32;++bit)for(int delta : {-181,-180,-179,-91,-90,-89,-2,-1,0,1,2,44,45,46,89,90,91,179,180,181}){
        const int64_t t=(int64_t(1)<<bit)+delta;
        if(t>=0&&uint64_t(t)<=UINT32_MAX)ts.insert(uint32_t(t));
    }
    for(unsigned i=0;i<512;++i)ts.insert(UINT32_MAX-i);
    for(uint32_t i=0;i<1024;++i)for(uint32_t q : {i,UINT32_MAX/90-i})for(unsigned r : {0,1,44,45,46,88,89}){
        const uint64_t t=uint64_t(q)*90+r;
        if(t<=UINT32_MAX)ts.insert(uint32_t(t));
    }
    uint32_t rng=103501;
    for(unsigned i=0;i<10000;++i){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;ts.insert(rng);}
    return ts;
}
int main(int argc,char**argv){
    try {
    Verilated::commandArgs(argc,argv);
    if(argc!=2)throw std::runtime_error("trace pathname required");
    std::ofstream trace(argv[1]);if(!trace)throw std::runtime_error("trace open");
    Vadmission_probe d;
    d.clk=0;
    d.reset=0;
    d.start=0;
    d.abort_packet=0;
    d.cache_write=0;
    d.cache_index=0;
    d.cache_data=0;
    d.replay_req=0;
    d.replay_addr=0;
    d.lookup_req=0;
    d.lookup_tile=0;
    d.lookup_cell=0;
    d.packet_bytes=0;
    d.epoch=0;
    d.accepted_ref_valid=0;
    d.accepted_qcache_valid=0;
    d.accepted_ref_fid=0;
    d.accepted_ref_generation=0;
    d.in_valid=0;
    d.in_last=0;
    d.in_data=0;
    d.receipt_ready=0;
    d.reset=1;d.probe_plane=0;d.probe_tile=0;d.eval();
    uint64_t tested=0;
    const auto ts=domain();
    for(unsigned p=0;p<4;++p)for(uint32_t t:ts){
        d.probe_plane=p;d.probe_tile=t;d.eval();
        const uint32_t expected=p==0?uint32_t((uint64_t(t)/180)*45+(uint64_t(t)%90)/2):t;
        if(d.original_cell!=expected||d.candidate_cell!=expected)
            throw std::runtime_error("cell mismatch p="+std::to_string(p)+" t="+std::to_string(t));
        ++tested;
        trace<<"{\"plane\":"<<p<<",\"tile\":"<<t<<",\"original\":"<<d.original_cell
             <<",\"candidate\":"<<d.candidate_cell<<",\"expected\":"<<expected<<"}\n";
    }
    d.final();trace.close();
    std::cout<<"{\"status\":\"TEST_PASS\",\"cases\":"<<tested<<",\"clock_edges\":0,\"tiles_per_plane\":"<<ts.size()<<"}\n";
    return 0;
    } catch(const std::exception&e){std::cerr<<"TEST_FAIL: "<<e.what()<<"\n";return 1;}
}
