#include "Vmath_probe.h"
#include "verilated.h"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
int main(int argc,char **argv) {
    try {
        if(argc!=2)throw std::runtime_error("usage: Vmath_probe trace.tsv");
        Vmath_probe d;std::ofstream trace(argv[1]);
        if(!trace)throw std::runtime_error("cannot open trace");
        uint64_t cases=0;
        for(unsigned p=0;p<4;++p)for(unsigned t=0;t<8192;++t) {
            d.plane=p;d.tile=t;d.eval();
            const unsigned row=t/90,column=t%90;
            const unsigned expected=p==0?((row/2)*45+column/2)&2047:t&2047;
            if(d.original_cell!=expected||d.narrow_cell!=expected||d.lut_cell!=expected)
                throw std::runtime_error("exhaustive mismatch");
            trace<<p<<'\t'<<t<<'\t'<<d.original_cell<<'\t'<<d.narrow_cell<<'\t'<<d.lut_cell<<'\n';++cases;
        }
        d.final();std::cout<<"{\"status\":\"TEST_PASS\",\"cases\":"<<cases<<",\"planes\":4,\"tile_inputs_per_plane\":8192}\n";
        return 0;
    }catch(const std::exception &e){std::cerr<<"MATH_FAIL "<<e.what()<<'\n';return 1;}
}
