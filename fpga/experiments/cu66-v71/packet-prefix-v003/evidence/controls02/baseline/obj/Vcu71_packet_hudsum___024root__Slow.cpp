// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_packet_hudsum.h for the primary calling header

#include "Vcu71_packet_hudsum__pch.h"

void Vcu71_packet_hudsum___024root___ctor_var_reset(Vcu71_packet_hudsum___024root* vlSelf);

Vcu71_packet_hudsum___024root::Vcu71_packet_hudsum___024root(Vcu71_packet_hudsum__Syms* symsp, const char* namep)
 {
    vlSymsp = symsp;
    vlNamep = strdup(namep);
    // Reset structure values
    Vcu71_packet_hudsum___024root___ctor_var_reset(this);
}

Vcu71_packet_hudsum___024root::~Vcu71_packet_hudsum___024root() {
    VL_DO_DANGLING(std::free(const_cast<char*>(vlNamep)), vlNamep);
}
