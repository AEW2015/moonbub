// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VCU71_SHA_PAIR__SYMS_H_
#define VERILATED_VCU71_SHA_PAIR__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vcu71_sha_pair.h"

// INCLUDE MODULE CLASSES
#include "Vcu71_sha_pair___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vcu71_sha_pair__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vcu71_sha_pair* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool& __Vm_didInit;

    // MODULE INSTANCE STATE
    Vcu71_sha_pair___024root       TOP;

    // CONSTRUCTORS
    Vcu71_sha_pair__Syms(VerilatedContext* contextp, const char* namep, Vcu71_sha_pair* modelp);
    ~Vcu71_sha_pair__Syms();

    // METHODS
    const char* name() const { return TOP.vlNamep; }
};

#endif  // guard
