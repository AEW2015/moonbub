// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vdy71_platform_sim__pch.h"

Vdy71_platform_sim__Syms::Vdy71_platform_sim__Syms(VerilatedContext* contextp, const char* namep, Vdy71_platform_sim* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    , __Vm_didInit{modelp->m_didInit}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(1540);
    // Setup sub module instances
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
}

Vdy71_platform_sim__Syms::~Vdy71_platform_sim__Syms() {
    // Tear down scopes
    // Tear down sub module instances
}
