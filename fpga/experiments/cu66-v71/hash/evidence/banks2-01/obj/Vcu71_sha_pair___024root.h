// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vcu71_sha_pair.h for the primary calling header

#ifndef VERILATED_VCU71_SHA_PAIR___024ROOT_H_
#define VERILATED_VCU71_SHA_PAIR___024ROOT_H_  // guard

#include "verilated.h"


class Vcu71_sha_pair__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vcu71_sha_pair___024root final {
  public:

    // DESIGN-SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst,0,0);
        VL_IN8(abort_i,0,0);
        VL_IN8(start_valid,0,0);
        VL_OUT8(start_ready,0,0);
        VL_IN(total_bytes,31,0);
        VL_IN8(data_valid,0,0);
        VL_OUT8(data_ready,0,0);
        VL_IN8(data,7,0);
        VL_IN8(data_last,0,0);
        VL_OUT8(result_valid,0,0);
        VL_IN8(result_ready,0,0);
        VL_OUTW(digest,255,0,8);
        VL_OUT8(busy,0,0);
        VL_OUT8(error,0,0);
        VL_OUT8(aborted,0,0);
        VL_OUT8(error_code,7,0);
        VL_OUT(accepted_bytes,31,0);
        VL_OUT(compressed_blocks,31,0);
        VL_OUT(round_cycles,31,0);
        VL_OUT(padding_bytes,31,0);
        VL_OUT(input_stall_cycles,31,0);
        VL_OUT(output_stall_cycles,31,0);
        VL_OUT8(debug_fill_state,2,0);
        VL_OUT8(debug_core_state,1,0);
        VL_OUT8(mismatch_any,0,0);
        VL_OUT(mismatch_fields,31,0);
        VL_OUT(initial_word_reference,31,0);
        VL_OUT(initial_word_candidate,31,0);
        CData/*2:0*/ cu71_sha_pair__DOT__candidate__DOT__fill_state;
        CData/*1:0*/ cu71_sha_pair__DOT__candidate__DOT__core_state;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__active;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__result_pending;
        CData/*1:0*/ cu71_sha_pair__DOT__candidate__DOT__bank_full;
        CData/*1:0*/ cu71_sha_pair__DOT__candidate__DOT__bank_last;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__fill_bank;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__process_bank;
        CData/*5:0*/ cu71_sha_pair__DOT__candidate__DOT__byte_position;
        CData/*5:0*/ cu71_sha_pair__DOT__candidate__DOT__round_index;
        CData/*2:0*/ cu71_sha_pair__DOT__candidate__DOT__length_index;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__write_byte;
        CData/*0:0*/ cu71_sha_pair__DOT__candidate__DOT__bad_last;
        CData/*3:0*/ cu71_sha_pair__DOT__candidate__DOT__ring_index;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__start_ready;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__data_ready;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__result_valid;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__error;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__aborted;
        CData/*7:0*/ cu71_sha_pair__DOT__reference__DOT__error_code;
        CData/*2:0*/ cu71_sha_pair__DOT__reference__DOT__fill_state;
        CData/*1:0*/ cu71_sha_pair__DOT__reference__DOT__core_state;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__active;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__result_pending;
        CData/*1:0*/ cu71_sha_pair__DOT__reference__DOT__bank_full;
        CData/*1:0*/ cu71_sha_pair__DOT__reference__DOT__bank_last;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__fill_bank;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__process_bank;
        CData/*5:0*/ cu71_sha_pair__DOT__reference__DOT__byte_position;
        CData/*5:0*/ cu71_sha_pair__DOT__reference__DOT__round_index;
        CData/*2:0*/ cu71_sha_pair__DOT__reference__DOT__length_index;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__write_byte;
        CData/*0:0*/ cu71_sha_pair__DOT__reference__DOT__bad_last;
        CData/*3:0*/ cu71_sha_pair__DOT__reference__DOT__ring_index;
        CData/*0:0*/ __Vdfg_Regularize_237;
    };
    struct {
        CData/*0:0*/ __Vdfg_Regularize_239;
        CData/*0:0*/ __Vdfg_Regularize_240;
        CData/*0:0*/ __Vdfg_Regularize_241;
        CData/*0:0*/ __Vdfg_Regularize_242;
        CData/*0:0*/ __Vdfg_Regularize_243;
        CData/*0:0*/ __Vdfg_Regularize_244;
        CData/*0:0*/ __Vdfg_Regularize_245;
        CData/*0:0*/ __Vdfg_Regularize_246;
        CData/*0:0*/ __Vdfg_Regularize_247;
        CData/*0:0*/ __Vdfg_Regularize_248;
        CData/*0:0*/ __Vdfg_Regularize_249;
        CData/*0:0*/ __Vdfg_Regularize_250;
        CData/*0:0*/ __Vdfg_Regularize_251;
        CData/*0:0*/ __Vdfg_Regularize_252;
        CData/*0:0*/ __Vdfg_Regularize_253;
        CData/*0:0*/ __Vdfg_Regularize_254;
        CData/*0:0*/ __Vdfg_Regularize_255;
        CData/*0:0*/ __Vdfg_Regularize_256;
        CData/*0:0*/ __Vdfg_Regularize_257;
        CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__rst__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__abort_i__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__start_valid__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__data_valid__0;
        CData/*7:0*/ __Vtrigprevexpr___TOP__data__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__data_last__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__result_ready__0;
        CData/*0:0*/ __VicoDidInit;
        CData/*0:0*/ __Vtrigprevexpr___TOP__clk__1;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__message_bytes;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__a;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__b;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__c;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__d;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__e;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__f;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__g;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__h;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__future_word;
        IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__temp1;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT____VlemCall_1__small0;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT____VlemCall_0__small1;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__accepted_bytes;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__compressed_blocks;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__round_cycles;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__padding_bytes;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__input_stall_cycles;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__output_stall_cycles;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__message_bytes;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__;
    };
    struct {
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__a;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__b;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__c;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__d;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__e;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__f;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__g;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__h;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__schedule_word;
        IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT__temp1;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_1__ror_67;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_0__ror_68;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_69;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_70;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_72;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_73;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_1__ror_76;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_0__ror_77;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_78;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_79;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_81;
        IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_82;
        IData/*31:0*/ __Vtrigprevexpr___TOP__total_bytes__0;
        VlUnpacked<VlUnpacked<IData/*31:0*/, 16>, 2> cu71_sha_pair__DOT__candidate__DOT__words;
        VlUnpacked<VlUnpacked<IData/*31:0*/, 16>, 2> cu71_sha_pair__DOT__reference__DOT__words;
        VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 2> __VicoTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    };

    // INTERNAL VARIABLES
    Vcu71_sha_pair__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vcu71_sha_pair___024root(Vcu71_sha_pair__Syms* symsp, const char* namep);
    ~Vcu71_sha_pair___024root();
    VL_UNCOPYABLE(Vcu71_sha_pair___024root);

    // INTERNAL METHODS
};


#endif  // guard
