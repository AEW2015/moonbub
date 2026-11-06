// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_sha_pair.h for the primary calling header

#include "Vcu71_sha_pair__pch.h"

void Vcu71_sha_pair___024root___ctor_var_reset(Vcu71_sha_pair___024root* vlSelf);

Vcu71_sha_pair___024root::Vcu71_sha_pair___024root(Vcu71_sha_pair__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vcu71_sha_pair___024root___ctor_var_reset(this);
}

Vcu71_sha_pair___024root::~Vcu71_sha_pair___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
