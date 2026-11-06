// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VCU71_PACKET_PRESUM__SYMS_H_
#define VERILATED_VCU71_PACKET_PRESUM__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vcu71_packet_presum.h"

// INCLUDE MODULE CLASSES
#include "Vcu71_packet_presum___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vcu71_packet_presum__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vcu71_packet_presum* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool& __Vm_didInit;

    // MODULE INSTANCE STATE
    Vcu71_packet_presum___024root  TOP;

    // CONSTRUCTORS
    Vcu71_packet_presum__Syms(VerilatedContext* contextp, const char* namep, Vcu71_packet_presum* modelp);
    ~Vcu71_packet_presum__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
