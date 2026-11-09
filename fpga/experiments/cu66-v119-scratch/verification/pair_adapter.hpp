#pragma once
#include <stdexcept>
class Pipeline_checked:public Vbr88_pipeline_v91h {
public:
    void eval(){
        Vbr88_pipeline_v91h::eval();
        if(!pair_equal)throw std::runtime_error("V116B exact caller raw/valid/counter pair mismatch");
    }
};
