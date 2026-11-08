// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vdy71_platform_sim.h for the primary calling header

#include "Vdy71_platform_sim__pch.h"

void Vdy71_platform_sim___024root___ctor_var_reset(Vdy71_platform_sim___024root* vlSelf);

Vdy71_platform_sim___024root::Vdy71_platform_sim___024root(Vdy71_platform_sim__Syms* symsp, const char* namep)
    : __VdlySched{*symsp->_vm_contextp__}
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vdy71_platform_sim___024root___ctor_var_reset(this);
}

Vdy71_platform_sim___024root::~Vdy71_platform_sim___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
