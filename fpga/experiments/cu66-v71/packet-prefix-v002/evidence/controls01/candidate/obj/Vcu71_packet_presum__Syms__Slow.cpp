// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vcu71_packet_presum__pch.h"

Vcu71_packet_presum__Syms::Vcu71_packet_presum__Syms(VerilatedContext* contextp, const char* namep, Vcu71_packet_presum* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    , __Vm_didInit{modelp->m_didInit}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(233);
    // Setup sub module instances
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-12);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
}

Vcu71_packet_presum__Syms::~Vcu71_packet_presum__Syms() {
    // Tear down scopes
    // Tear down sub module instances
}
