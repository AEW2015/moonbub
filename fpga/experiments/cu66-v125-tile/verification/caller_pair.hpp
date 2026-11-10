#pragma once
#include "Vready_probe.h"
#include <stdexcept>
class WholeProducerChecked:public Vready_probe {
public:
    void eval() {
        Vready_probe::eval();
        if(!probe_public_equal||!probe_internal_equal||!probe_scale_equal)
            throw std::runtime_error("V124 actual controller whole public/private/raw-scale pair mismatch");
    }
};
using Vcs88_pipeline_v91i2b=WholeProducerChecked;
