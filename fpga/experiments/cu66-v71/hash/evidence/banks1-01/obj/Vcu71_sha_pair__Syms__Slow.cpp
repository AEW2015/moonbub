// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vcu71_sha_pair__pch.h"

Vcu71_sha_pair__Syms::Vcu71_sha_pair__Syms(VerilatedContext* contextp, const char* namep, Vcu71_sha_pair* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    , __Vm_didInit{modelp->m_didInit}
    // Setup top module instance
    , TOP{this, namep}
{
    // Check resources
    Verilated::stackCheck(410);
    // Setup sub module instances
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-12);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
}

Vcu71_sha_pair__Syms::~Vcu71_sha_pair__Syms() {
    // Tear down scopes
    // Tear down sub module instances
}
