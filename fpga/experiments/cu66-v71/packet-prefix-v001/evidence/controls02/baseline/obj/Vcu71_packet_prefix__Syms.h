// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VCU71_PACKET_PREFIX__SYMS_H_
#define VERILATED_VCU71_PACKET_PREFIX__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vcu71_packet_prefix.h"

// INCLUDE MODULE CLASSES
#include "Vcu71_packet_prefix___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vcu71_packet_prefix__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vcu71_packet_prefix* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool& __Vm_didInit;

    // MODULE INSTANCE STATE
    Vcu71_packet_prefix___024root  TOP;

    // CONSTRUCTORS
    Vcu71_packet_prefix__Syms(VerilatedContext* contextp, const char* namep, Vcu71_packet_prefix* modelp);
    ~Vcu71_packet_prefix__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
