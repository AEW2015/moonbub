#include <verilated.h>
#include "Vpredicate_probe.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>

static bool oracle(unsigned p,unsigned t){
    const unsigned width=p==0?90:45;
    const unsigned x=t%width,y=t/width;
    if(p!=0)return x>=11&&x<30&&y==23;
    return (x>=3&&x<22&&((y>=7&&y<9)||(y>=11&&y<13)))||
           (x>=21&&x<61&&y>=45&&y<48)||(x>=21&&x<51&&y>=49&&y<51);
}
int main(int argc,char**argv){
    try {
    Verilated::commandArgs(argc,argv);
    if(argc!=2)throw std::runtime_error("trace pathname required");
    std::ofstream trace(argv[1]);if(!trace)throw std::runtime_error("trace open");
    Vpredicate_probe d;
    d.clk=0;
    d.reset=0;
    d.start=0;
    d.cancel=0;
    d.admitted_ready=0;
    d.key_frame=0;
    d.input_done=0;
    d.epoch=0;
    d.frame_fid=0;
    d.accepted_ref_valid=0;
    d.accepted_ref_fid=0;
    d.accepted_ref_generation=0;
    d.lookup_ready=0;
    d.lookup_rsp=0;
    d.lookup_mode=0;
    d.lookup_scale=0;
    d.in_valid=0;
    d.in_epoch=0;
    d.in_child_epoch=0;
    d.in_token=0;
    d.in_plane=0;
    d.in_qscale=0;
    d.in_block=0;
    d.in_tile=0;
    d.in_qcell=0;
    d.in_index=0;
    d.in_value=0;
    d.out_ready=0;
    d.ref_req_ready=0;
    d.ref_rsp_valid=0;
    d.ref_rsp_epoch=0;
    d.ref_rsp_fid=0;
    d.ref_rsp_generation=0;
    d.ref_rsp_plane=0;
    d.ref_rsp_tile=0;
    for(unsigned i=0;i<16;++i)d.ref_rsp_pixels[i]=0;
    d.ref_rsp_error=0;
    d.reset=1;d.probe_plane=0;d.probe_tile=0;d.eval();
    unsigned tested=0,true_counts[4]={0,0,0,0};
    for(unsigned p=0;p<4;++p)for(unsigned t=0;t<8192;++t){
        d.probe_plane=p;d.probe_tile=t;d.eval();
        const bool expected=oracle(p,t);
        if(bool(d.original_hidden)!=expected || bool(d.candidate_hidden)!=expected)
            throw std::runtime_error("predicate mismatch p="+std::to_string(p)+" t="+std::to_string(t));
        true_counts[p]+=expected;++tested;
        trace<<"{\"plane\":"<<p<<",\"tile\":"<<t<<",\"original\":"<<unsigned(d.original_hidden)
             <<",\"candidate\":"<<unsigned(d.candidate_hidden)<<",\"expected\":"<<unsigned(expected)<<"}\n";
    }
    d.final();trace.close();
    if(tested!=32768 || true_counts[0]!=256 || true_counts[1]!=19 || true_counts[2]!=19 || true_counts[3]!=19)
        throw std::runtime_error("domain completeness");
    std::cout<<"{\"status\":\"TEST_PASS\",\"cases\":"<<tested<<",\"clock_edges\":0,\"plane_true_counts\":["
             <<true_counts[0]<<","<<true_counts[1]<<","<<true_counts[2]<<","<<true_counts[3]<<"]}\n";
    return 0;
    } catch(const std::exception&e){std::cerr<<"TEST_FAIL: "<<e.what()<<"\n";return 1;}
}
