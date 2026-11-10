#pragma once
#include "Vready_probe.h"
#include <stdexcept>
#include "successor_monitor.hpp"
class WholeProducerChecked:public Vready_probe {
public:
    void eval() {
        const bool rising=clk&&!monitor_clock_;
        SuccessorBefore staged{};
        if(rising)staged=successor_before(*this,false);
        Vready_probe::eval();
        if(!probe_public_equal||!probe_internal_equal||!probe_scale_equal)
            throw std::runtime_error("V124 actual controller whole public/private/raw-scale pair mismatch");
        if(rising)successor_after(*this,staged,false);
        monitor_clock_=clk;
    }
private:
    bool monitor_clock_=false;
};
using Vcs88_pipeline_v91i2b=WholeProducerChecked;
