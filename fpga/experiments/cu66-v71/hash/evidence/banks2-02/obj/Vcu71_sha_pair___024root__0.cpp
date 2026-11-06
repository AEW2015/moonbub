// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_sha_pair.h for the primary calling header

#include "Vcu71_sha_pair__pch.h"

void Vcu71_sha_pair___024root___eval_sample(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_sample\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
bool Vcu71_sha_pair___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in);
void Vcu71_sha_pair___024root___eval_body__ico(Vcu71_sha_pair___024root* vlSelf);

bool Vcu71_sha_pair___024root___eval_ico(Vcu71_sha_pair___024root* vlSelf, CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_ico\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    vlSelfRef.__VicoTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VicoTriggered[1U]) 
                                     | (IData)((IData)(firstIteration)));
    {
        // Inlined CFunc: _eval_triggers_vec__ico
        vlSelfRef.__VicoTriggered[0U] = (QData)((IData)(
                                                        ((((IData)(vlSelfRef.result_ready) 
                                                           != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__result_ready__0)) 
                                                          << 8U) 
                                                         | (((((((IData)(vlSelfRef.data_last) 
                                                                 != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__data_last__0)) 
                                                                << 3U) 
                                                               | (((IData)(vlSelfRef.data) 
                                                                   != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__data__0)) 
                                                                  << 2U)) 
                                                              | ((((IData)(vlSelfRef.data_valid) 
                                                                   != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__data_valid__0)) 
                                                                  << 1U) 
                                                                 | (vlSelfRef.total_bytes 
                                                                    != vlSelfRef.__Vtrigprevexpr___TOP__total_bytes__0))) 
                                                             << 4U) 
                                                            | (((((IData)(vlSelfRef.start_valid) 
                                                                  != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__start_valid__0)) 
                                                                 << 3U) 
                                                                | (((IData)(vlSelfRef.abort_i) 
                                                                    != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__abort_i__0)) 
                                                                   << 2U)) 
                                                               | ((((IData)(vlSelfRef.rst) 
                                                                    != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rst__0)) 
                                                                   << 1U) 
                                                                  | ((IData)(vlSelfRef.clk) 
                                                                     != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__0))))))));
        vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
        vlSelfRef.__Vtrigprevexpr___TOP__rst__0 = vlSelfRef.rst;
        vlSelfRef.__Vtrigprevexpr___TOP__abort_i__0 
            = vlSelfRef.abort_i;
        vlSelfRef.__Vtrigprevexpr___TOP__start_valid__0 
            = vlSelfRef.start_valid;
        vlSelfRef.__Vtrigprevexpr___TOP__total_bytes__0 
            = vlSelfRef.total_bytes;
        vlSelfRef.__Vtrigprevexpr___TOP__data_valid__0 
            = vlSelfRef.data_valid;
        vlSelfRef.__Vtrigprevexpr___TOP__data__0 = vlSelfRef.data;
        vlSelfRef.__Vtrigprevexpr___TOP__data_last__0 
            = vlSelfRef.data_last;
        vlSelfRef.__Vtrigprevexpr___TOP__result_ready__0 
            = vlSelfRef.result_ready;
        if (VL_UNLIKELY(((1U & (~ (IData)(vlSelfRef.__VicoDidInit)))))) {
            vlSelfRef.__VicoDidInit = 1U;
            vlSelfRef.__VicoTriggered[0U] = (1ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (2ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (4ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (8ULL | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (0x0000000000000010ULL 
                                             | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (0x0000000000000020ULL 
                                             | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (0x0000000000000040ULL 
                                             | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (0x0000000000000080ULL 
                                             | vlSelfRef.__VicoTriggered[0U]);
            vlSelfRef.__VicoTriggered[0U] = (0x0000000000000100ULL 
                                             | vlSelfRef.__VicoTriggered[0U]);
        }
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcu71_sha_pair___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    __VicoExecute = Vcu71_sha_pair___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        Vcu71_sha_pair___024root___eval_body__ico(vlSelf);
    }
    return (__VicoExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
void Vcu71_sha_pair___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in);

bool Vcu71_sha_pair___024root___eval_act(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_act\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_triggers_vec__act
        vlSelfRef.__VactTriggered[0U] = (QData)((IData)(
                                                        ((IData)(vlSelfRef.clk) 
                                                         & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__1)))));
        vlSelfRef.__Vtrigprevexpr___TOP__clk__1 = vlSelfRef.clk;
    }
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcu71_sha_pair___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vcu71_sha_pair___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

bool Vcu71_sha_pair___024root___eval_inact(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_inact\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vcu71_sha_pair___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);
void Vcu71_sha_pair___024root___nba_sequent__TOP__0(Vcu71_sha_pair___024root* vlSelf);
void Vcu71_sha_pair___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out);

bool Vcu71_sha_pair___024root___eval_nba(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_nba\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vcu71_sha_pair___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        {
            // Inlined CFunc: _eval_body__nba
            if ((((1ULL & vlSelfRef.__VnbaTriggered[0U])) != 0ULL)) {
                Vcu71_sha_pair___024root___nba_sequent__TOP__0(vlSelf);
            }
        }
        Vcu71_sha_pair___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

bool Vcu71_sha_pair___024root___eval_obs(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_obs\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vcu71_sha_pair___024root___eval_react(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_react\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

void Vcu71_sha_pair___024root___eval_postponed(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_postponed\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

bool Vcu71_sha_pair___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___trigger_anySet__ico\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((2U > n));
    return (0U);
}

void Vcu71_sha_pair___024root___eval_body__ico(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_body__ico\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((((6ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
        {
            // Inlined CFunc: _ico_comb__TOP__0
            CData/*0:0*/ __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_238;
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_238 = 0;
            CData/*0:0*/ __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_258;
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_258 = 0;
            CData/*0:0*/ __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_259;
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_259 = 0;
            vlSelfRef.__Vdfg_Regularize_237 = ((IData)(vlSelfRef.rst) 
                                               | (IData)(vlSelfRef.abort_i));
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready 
                = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
                            | (IData)(vlSelfRef.__Vdfg_Regularize_237))));
            vlSelfRef.start_ready = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                              | (IData)(vlSelfRef.__Vdfg_Regularize_237))));
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid 
                = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
                   & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                      & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending)));
            vlSelfRef.result_valid = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                      & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                                         & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending)));
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready 
                = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
                   & ((IData)(vlSelfRef.__Vdfg_Regularize_247) 
                      & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                         & ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)) 
                            & (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes 
                               < vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes)))));
            vlSelfRef.data_ready = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                    & ((IData)(vlSelfRef.__Vdfg_Regularize_245) 
                                       & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                                          & ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)) 
                                             & (vlSelfRef.accepted_bytes 
                                                < vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes)))));
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_238 
                = ((IData)(vlSelfRef.start_ready) != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready));
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_259 
                = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                   != (IData)(vlSelfRef.result_valid));
            __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_258 
                = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready) 
                   != (IData)(vlSelfRef.data_ready));
            vlSelfRef.mismatch_fields = (((((((IData)(vlSelfRef.__Vdfg_Regularize_244) 
                                              << 3U) 
                                             | ((IData)(vlSelfRef.__Vdfg_Regularize_243) 
                                                << 2U)) 
                                            | (((IData)(vlSelfRef.__Vdfg_Regularize_252) 
                                                << 1U) 
                                               | (IData)(vlSelfRef.__Vdfg_Regularize_251))) 
                                           << 0x0000000cU) 
                                          | (((((IData)(vlSelfRef.__Vdfg_Regularize_254) 
                                                << 3U) 
                                               | ((IData)(vlSelfRef.__Vdfg_Regularize_253) 
                                                  << 2U)) 
                                              | (((IData)(vlSelfRef.__Vdfg_Regularize_242) 
                                                  << 1U) 
                                                 | (IData)(vlSelfRef.__Vdfg_Regularize_240))) 
                                             << 8U)) 
                                         | ((((((IData)(vlSelfRef.__Vdfg_Regularize_255) 
                                                << 3U) 
                                               | ((IData)(vlSelfRef.__Vdfg_Regularize_241) 
                                                  << 2U)) 
                                              | (((IData)(vlSelfRef.__Vdfg_Regularize_257) 
                                                  << 1U) 
                                                 | (IData)(vlSelfRef.__Vdfg_Regularize_239))) 
                                             << 4U) 
                                            | ((((IData)(vlSelfRef.__Vdfg_Regularize_256) 
                                                 << 3U) 
                                                | ((IData)(__Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_259) 
                                                   << 2U)) 
                                               | (((IData)(__Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_258) 
                                                   << 1U) 
                                                  | __Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_238))));
            vlSelfRef.mismatch_any = ((IData)(vlSelfRef.__Vdfg_Regularize_244) 
                                      | ((IData)(vlSelfRef.__Vdfg_Regularize_243) 
                                         | ((IData)(vlSelfRef.__Vdfg_Regularize_252) 
                                            | ((IData)(vlSelfRef.__Vdfg_Regularize_251) 
                                               | ((IData)(vlSelfRef.__Vdfg_Regularize_254) 
                                                  | ((IData)(vlSelfRef.__Vdfg_Regularize_253) 
                                                     | ((IData)(vlSelfRef.__Vdfg_Regularize_242) 
                                                        | ((IData)(vlSelfRef.__Vdfg_Regularize_240) 
                                                           | ((IData)(vlSelfRef.__Vdfg_Regularize_255) 
                                                              | ((IData)(vlSelfRef.__Vdfg_Regularize_241) 
                                                                 | ((IData)(vlSelfRef.__Vdfg_Regularize_257) 
                                                                    | (__Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_238 
                                                                       | (__Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_258 
                                                                          | (__Vinline_0__ico_comb__TOP__0___Vdfg_Regularize_259 
                                                                             | ((IData)(vlSelfRef.__Vdfg_Regularize_239) 
                                                                                | (IData)(vlSelfRef.__Vdfg_Regularize_256))))))))))))))));
        }
    }
    if ((((0x0000000000000026ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
        {
            // Inlined CFunc: _ico_comb__TOP__1
            vlSelfRef.__Vdfg_Regularize_248 = ((IData)(vlSelfRef.data_valid) 
                                               & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready));
            vlSelfRef.__Vdfg_Regularize_246 = ((IData)(vlSelfRef.data_valid) 
                                               & (IData)(vlSelfRef.data_ready));
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte 
                = (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))
                     ? ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                        | (0x38U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position)))
                     : ((IData)(vlSelfRef.__Vdfg_Regularize_248) 
                        | (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) 
                   & (IData)(vlSelfRef.__Vdfg_Regularize_249));
            vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte 
                = (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))
                     ? ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                        | (0x38U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position)))
                     : ((IData)(vlSelfRef.__Vdfg_Regularize_246) 
                        | (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) 
                   & (IData)(vlSelfRef.__Vdfg_Regularize_250));
        }
    }
    if ((((0x00000000000000a6ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
        {
            // Inlined CFunc: _ico_comb__TOP__2
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last 
                = (((IData)(vlSelfRef.data_last) != 
                    (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes 
                     == ((IData)(1U) + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes))) 
                   & (IData)(vlSelfRef.__Vdfg_Regularize_248));
            vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last 
                = (((IData)(vlSelfRef.data_last) != 
                    (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes 
                     == ((IData)(1U) + vlSelfRef.accepted_bytes))) 
                   & (IData)(vlSelfRef.__Vdfg_Regularize_246));
        }
    }
}

bool Vcu71_sha_pair___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___trigger_anySet__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

extern const VlWide<64>/*2047:0*/ Vcu71_sha_pair__ConstPool__CONST_0;

void Vcu71_sha_pair___024root___nba_sequent__TOP__0(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___nba_sequent__TOP__0\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT____VlemCall_3__constant_k;
    IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT____VlemCall_2__big1;
    IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT____VlemCall_1__small0;
    IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT____VlemCall_0__small1;
    IData/*31:0*/ cu71_sha_pair__DOT__candidate__DOT__schedule_word;
    cu71_sha_pair__DOT__candidate__DOT__schedule_word = 0;
    IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT____VlemCall_3__constant_k;
    IData/*31:0*/ cu71_sha_pair__DOT__reference__DOT____VlemCall_2__big1;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_1__ror_1;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_1__ror_1 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_0__ror_2;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_0__ror_2 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_3;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_3 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_4;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_4 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_6;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_6 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_7;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_7 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_1__ror_10;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_1__ror_10 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_0__ror_11;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_0__ror_11 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_12;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_12 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_13;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_13 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_15;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_15 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_16;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_16 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__Vfuncout_18;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__Vfuncout_18 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__x_19;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__x_19 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s0_23;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s0_23 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s1_25;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s1_25 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c1_26;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c1_26 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_2__ror_28;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_2__ror_28 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_1__ror_29;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_1__ror_29 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_0__ror_30;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_0__ror_30 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_31;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_31 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_32;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_32 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_34;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_34 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_35;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_35 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_37;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_37 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_38;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_38 = 0;
    CData/*5:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__constant_k__t_40;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__constant_k__t_40 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__Vfuncout_41;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__Vfuncout_41 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__x_42;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__x_42 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s0_47;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s0_47 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s1_49;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s1_49 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s2_51;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s2_51 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c2_52;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c2_52 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_2__ror_85;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_2__ror_85 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_1__ror_86;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_1__ror_86 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_0__ror_87;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_0__ror_87 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_88;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_88 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_89;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_89 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_91;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_91 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_92;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_92 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_94;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_94 = 0;
    IData/*31:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_95;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_95 = 0;
    CData/*5:0*/ __Vfunc_cu71_sha_pair__DOT__reference__DOT__constant_k__t_97;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__constant_k__t_97 = 0;
    CData/*0:0*/ __Vdfg_Regularize_238;
    __Vdfg_Regularize_238 = 0;
    CData/*0:0*/ __Vdfg_Regularize_258;
    __Vdfg_Regularize_258 = 0;
    CData/*0:0*/ __Vdfg_Regularize_259;
    __Vdfg_Regularize_259 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0;
    IData/*31:0*/ __Vdly__accepted_bytes_6;
    __Vdly__accepted_bytes_6 = 0;
    IData/*31:0*/ __Vdly__compressed_blocks_7;
    __Vdly__compressed_blocks_7 = 0;
    IData/*31:0*/ __Vdly__round_cycles_8;
    __Vdly__round_cycles_8 = 0;
    IData/*31:0*/ __Vdly__padding_bytes_9;
    __Vdly__padding_bytes_9 = 0;
    IData/*31:0*/ __Vdly__input_stall_cycles_10;
    __Vdly__input_stall_cycles_10 = 0;
    IData/*31:0*/ __Vdly__output_stall_cycles_11;
    __Vdly__output_stall_cycles_11 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15 = 0;
    CData/*5:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 = 0;
    CData/*5:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 = 0;
    CData/*2:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 = 0;
    CData/*2:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 0;
    CData/*1:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51 = 0;
    CData/*0:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52 = 0;
    CData/*5:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 = 0;
    CData/*5:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 = 0;
    CData/*2:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 = 0;
    CData/*2:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 0;
    CData/*1:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72 = 0;
    IData/*31:0*/ __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_74;
    __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_74 = 0;
    CData/*4:0*/ __Vdly_Lsb__cu71_sha_pair__DOT__candidate__DOT__words_75;
    __Vdly_Lsb__cu71_sha_pair__DOT__candidate__DOT__words_75 = 0;
    CData/*3:0*/ __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_76;
    __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_76 = 0;
    CData/*0:0*/ __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_77;
    __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_77 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_78;
    __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_78 = 0;
    IData/*31:0*/ __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_79;
    __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_79 = 0;
    CData/*3:0*/ __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_80;
    __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_80 = 0;
    CData/*0:0*/ __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_81;
    __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_81 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_82;
    __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_82 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_83;
    __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_83 = 0;
    CData/*4:0*/ __Vdly_Lsb__cu71_sha_pair__DOT__reference__DOT__words_84;
    __Vdly_Lsb__cu71_sha_pair__DOT__reference__DOT__words_84 = 0;
    CData/*3:0*/ __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_85;
    __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_85 = 0;
    CData/*0:0*/ __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_86;
    __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_86 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_87;
    __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_87 = 0;
    IData/*31:0*/ __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_88;
    __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_88 = 0;
    CData/*3:0*/ __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_89;
    __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_89 = 0;
    CData/*0:0*/ __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_90;
    __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_90 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_91;
    __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_91 = 0;
    // Body
    __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__output_stall_cycles;
    __Vdly__output_stall_cycles_11 = vlSelfRef.output_stall_cycles;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__compressed_blocks;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_cycles;
    __Vdly__compressed_blocks_7 = vlSelfRef.compressed_blocks;
    __Vdly__round_cycles_8 = vlSelfRef.round_cycles;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__;
    __Vdly__padding_bytes_9 = vlSelfRef.padding_bytes;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__input_stall_cycles;
    __Vdly__input_stall_cycles_10 = vlSelfRef.input_stall_cycles;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes;
    __Vdly__accepted_bytes_6 = vlSelfRef.accepted_bytes;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state;
    __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_87 = 0U;
    __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_91 = 0U;
    __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_78 = 0U;
    __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_82 = 0U;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__;
    __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__;
    __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__;
    if ((1U & (~ (IData)(vlSelfRef.rst)))) {
        if ((1U & (~ (IData)(vlSelfRef.abort_i)))) {
            if ((1U & (~ ((IData)(vlSelfRef.start_valid) 
                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte) {
                                __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_83 
                                    = (0x000000ffU 
                                       & (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))
                                            ? ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))
                                                ? (IData)(
                                                          (((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes)) 
                                                            << 3U) 
                                                           >> 
                                                           (0x0000003fU 
                                                            & (((IData)(0x3fU) 
                                                                - 
                                                                ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index) 
                                                                 << 3U)) 
                                                               - (IData)(7U)))))
                                                : 0U)
                                            : ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))
                                                ? 0x80U
                                                : (IData)(vlSelfRef.data))) 
                                          & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_249)))));
                                __Vdly_Lsb__cu71_sha_pair__DOT__reference__DOT__words_84 
                                    = (0x0000001fU 
                                       & (((IData)(0x1fU) 
                                           - (0x00000018U 
                                              & ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position) 
                                                 << 3U))) 
                                          - (IData)(7U)));
                                __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_85 
                                    = (0x0000000fU 
                                       & ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position) 
                                          >> 2U));
                                __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_86 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank;
                                __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_87 = 1U;
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    if ((0x10U <= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index))) {
                                        __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_88 
                                            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__schedule_word;
                                        __Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_89 
                                            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index;
                                        __Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_90 
                                            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank;
                                        __Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_91 = 1U;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelfRef.start_valid) 
                          & (IData)(vlSelfRef.start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte) {
                                __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_74 
                                    = (0x000000ffU 
                                       & (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))
                                            ? ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))
                                                ? (IData)(
                                                          (((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes)) 
                                                            << 3U) 
                                                           >> 
                                                           (0x0000003fU 
                                                            & (((IData)(0x3fU) 
                                                                - 
                                                                ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index) 
                                                                 << 3U)) 
                                                               - (IData)(7U)))))
                                                : 0U)
                                            : ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))
                                                ? 0x80U
                                                : (IData)(vlSelfRef.data))) 
                                          & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_250)))));
                                __Vdly_Lsb__cu71_sha_pair__DOT__candidate__DOT__words_75 
                                    = (0x0000001fU 
                                       & (((IData)(0x1fU) 
                                           - (0x00000018U 
                                              & ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position) 
                                                 << 3U))) 
                                          - (IData)(7U)));
                                __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_76 
                                    = (0x0000000fU 
                                       & ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position) 
                                          >> 2U));
                                __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_77 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank;
                                __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_78 = 1U;
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    if ((0x30U > (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index))) {
                                        __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_79 
                                            = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__future_word;
                                        __Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_80 
                                            = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index;
                                        __Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_81 
                                            = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank;
                                        __Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_82 = 1U;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelfRef.rst) {
        __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48 = 0U;
        __Vdly__output_stall_cycles_11 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45 = 0U;
        __Vdly__compressed_blocks_7 = 0U;
        __Vdly__round_cycles_8 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29 = 0U;
        __Vdly__padding_bytes_9 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47 = 0U;
        __Vdly__input_stall_cycles_10 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43 = 0U;
        __Vdly__accepted_bytes_6 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 4U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 4U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35 = 0U;
        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73 = 0U;
        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36 = 0U;
        vlSelfRef.aborted = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__aborted = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code = 0U;
        vlSelfRef.error = 0U;
        vlSelfRef.error_code = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__h = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__h = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__d = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__d = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last = 0U;
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last = 0U;
    } else {
        if ((1U & (~ (IData)(vlSelfRef.abort_i)))) {
            if (((IData)(vlSelfRef.start_valid) & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready))) {
                __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66 = 0x6a09e667U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 = 0U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67 = 0xbb67ae85U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68 = 0x3c6ef372U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69 = 0xa54ff53aU;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70 = 0x510e527fU;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71 = 0x9b05688cU;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72 = 0x1f83d9abU;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73 = 0x5be0cd19U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error = 0U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code = 0U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes 
                    = vlSelfRef.total_bytes;
            } else {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if (((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                 & (~ (IData)(vlSelfRef.result_ready)))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48 
                                    = ((IData)(1U) 
                                       + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__output_stall_cycles);
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44 
                                            = ((IData)(1U) 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__compressed_blocks);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a);
                                        if ((1U & (~ 
                                                   ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last) 
                                                    >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))))) {
                                            __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52 
                                                = (1U 
                                                   & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)));
                                        }
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__d);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g);
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73 
                                            = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__h);
                                    }
                                }
                                if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45 
                                        = ((IData)(1U) 
                                           + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_cycles);
                                }
                            }
                            if ((((IData)(vlSelfRef.data_valid) 
                                  & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready))) 
                                 & (0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47 
                                    = ((IData)(1U) 
                                       + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__input_stall_cycles);
                            }
                            if ((((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)) 
                                  & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                        >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank)))) 
                                 & (0x38U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position)))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 = 0U;
                            }
                            if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 = 0U;
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51 
                                        = (1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank)));
                                } else {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53 
                                        = (0x0000003fU 
                                           & ((IData)(1U) 
                                              + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position)));
                                }
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                        if ((1U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                            __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes);
                                            if ((7U 
                                                 != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index))) {
                                                __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55 
                                                    = 
                                                    (7U 
                                                     & ((IData)(1U) 
                                                        + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index)));
                                            }
                                        } else {
                                            __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes);
                                        }
                                    } else if ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46 
                                            = ((IData)(1U) 
                                               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes);
                                    }
                                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)))) {
                                            __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes);
                                        }
                                    }
                                }
                            }
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 = 0U;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((0x3fU != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54 
                                        = (0x0000003fU 
                                           & ((IData)(1U) 
                                              + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index)));
                                }
                            }
                        }
                    }
                }
                if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last) {
                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error = 1U;
                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code = 1U;
                } else if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                     & (IData)(vlSelfRef.result_ready))))) {
                    if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                        if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                            if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((2U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error = 1U;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code = 0xffU;
                                }
                            }
                        }
                    }
                }
            }
            if (((IData)(vlSelfRef.start_valid) & (IData)(vlSelfRef.start_ready))) {
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 = 0U;
                __Vdly__output_stall_cycles_11 = 0U;
                __Vdly__compressed_blocks_7 = 0U;
                __Vdly__round_cycles_8 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29 = 0x6a09e667U;
                __Vdly__padding_bytes_9 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14 = 0U;
                __Vdly__input_stall_cycles_10 = 0U;
                __Vdly__accepted_bytes_6 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 = 0U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30 = 0xbb67ae85U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31 = 0x3c6ef372U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32 = 0xa54ff53aU;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33 = 0x510e527fU;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34 = 0x9b05688cU;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35 = 0x1f83d9abU;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36 = 0x5be0cd19U;
                vlSelfRef.error = 0U;
                vlSelfRef.error_code = 0U;
                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes 
                    = vlSelfRef.total_bytes;
            } else {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if (((IData)(vlSelfRef.result_valid) 
                                 & (~ (IData)(vlSelfRef.result_ready)))) {
                                __Vdly__output_stall_cycles_11 
                                    = ((IData)(1U) 
                                       + vlSelfRef.output_stall_cycles);
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                        __Vdly__compressed_blocks_7 
                                            = ((IData)(1U) 
                                               + vlSelfRef.compressed_blocks);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a);
                                        if ((1U & (~ 
                                                   ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last) 
                                                    >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))))) {
                                            __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15 
                                                = (1U 
                                                   & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)));
                                        }
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__d);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g);
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36 
                                            = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__ 
                                               + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__h);
                                    }
                                }
                                if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    __Vdly__round_cycles_8 
                                        = ((IData)(1U) 
                                           + vlSelfRef.round_cycles);
                                }
                            }
                            if ((((IData)(vlSelfRef.data_valid) 
                                  & (~ (IData)(vlSelfRef.data_ready))) 
                                 & (0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)))) {
                                __Vdly__input_stall_cycles_10 
                                    = ((IData)(1U) 
                                       + vlSelfRef.input_stall_cycles);
                            }
                            if ((((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)) 
                                  & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                        >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank)))) 
                                 & (0x38U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position)))) {
                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 = 0U;
                            }
                            if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 = 0U;
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14 
                                        = (1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank)));
                                } else {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16 
                                        = (0x0000003fU 
                                           & ((IData)(1U) 
                                              + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position)));
                                }
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                        if ((1U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                            __Vdly__padding_bytes_9 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.padding_bytes);
                                            if ((7U 
                                                 != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index))) {
                                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18 
                                                    = 
                                                    (7U 
                                                     & ((IData)(1U) 
                                                        + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index)));
                                            }
                                        } else {
                                            __Vdly__padding_bytes_9 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.padding_bytes);
                                        }
                                    } else if ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                        __Vdly__padding_bytes_9 
                                            = ((IData)(1U) 
                                               + vlSelfRef.padding_bytes);
                                    }
                                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)))) {
                                            __Vdly__accepted_bytes_6 
                                                = ((IData)(1U) 
                                                   + vlSelfRef.accepted_bytes);
                                        }
                                    }
                                }
                            }
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 = 0U;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((0x3fU != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17 
                                        = (0x0000003fU 
                                           & ((IData)(1U) 
                                              + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index)));
                                }
                            }
                        }
                    }
                }
                if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last) {
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 1U;
                } else if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                     & (IData)(vlSelfRef.result_ready))))) {
                    if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                        if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                            if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((2U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    vlSelfRef.error = 1U;
                                    vlSelfRef.error_code = 0xffU;
                                }
                            }
                        }
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelfRef.start_valid) 
                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__h 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__d 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b 
                                        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58 
                                    = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__temp1 
                                       + (((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                            & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b) 
                                           ^ ((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                               & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c) 
                                              ^ (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b 
                                                 & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c))) 
                                          + (((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                               >> 2U) 
                                              | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                                 << 0x0000001eU)) 
                                             ^ (((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                                  >> 0x0000000dU) 
                                                 | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                                    << 0x00000013U)) 
                                                ^ (
                                                   (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                                    >> 0x00000016U) 
                                                   | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
                                                      << 0x0000000aU))))));
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__h 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g;
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f;
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e;
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e 
                                    = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__d 
                                       + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__temp1);
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__d 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c;
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__c 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b;
                                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__b 
                                    = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a;
                            }
                        }
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelfRef.start_valid) 
                          & (IData)(vlSelfRef.start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__h 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__d 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__;
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b 
                                        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21 
                                    = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__temp1 
                                       + (((vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                            & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b) 
                                           ^ ((vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                               & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c) 
                                              ^ (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b 
                                                 & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c))) 
                                          + (((vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                               >> 2U) 
                                              | (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                                 << 0x0000001eU)) 
                                             ^ (((vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                                  >> 0x0000000dU) 
                                                 | (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                                    << 0x00000013U)) 
                                                ^ (
                                                   (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                                    >> 0x00000016U) 
                                                   | (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
                                                      << 0x0000000aU))))));
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__h 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g;
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f;
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e;
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e 
                                    = (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__d 
                                       + vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__temp1);
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__d 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c;
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__c 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b;
                                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__b 
                                    = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a;
                            }
                        }
                    }
                }
            }
        }
        vlSelfRef.aborted = 0U;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__aborted = 0U;
        if (vlSelfRef.abort_i) {
            __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0U;
            __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0U;
            __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 4U;
            __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 4U;
            __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0U;
            __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0U;
            vlSelfRef.aborted = 1U;
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__aborted = 1U;
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full = 0U;
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 0U;
            vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full = 0U;
            vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 0U;
            vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last = 0U;
            vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last = 0U;
        } else {
            if (((IData)(vlSelfRef.start_valid) & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready))) {
                __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 1U;
                __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 
                    = ((0U == vlSelfRef.total_bytes)
                        ? 1U : 0U);
                __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full = 0U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 0U;
                vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last = 0U;
            } else {
                if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last) {
                    __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0U;
                    __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 4U;
                    __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0U;
                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full = 0U;
                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 0U;
                } else {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if ((((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)) 
                                  & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                        >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank)))) 
                                 & (0x38U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position)))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 3U;
                            }
                            if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                        if ((1U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                            if ((7U 
                                                 == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index))) {
                                                __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 4U;
                                            }
                                        }
                                    } else if ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) {
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 2U;
                                    } else if (vlSelfRef.data_last) {
                                        __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56 = 1U;
                                    }
                                }
                            }
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 1U;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 2U;
                                }
                            } else if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57 = 0U;
                            }
                        }
                    }
                    if (((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                         & (IData)(vlSelfRef.result_ready))) {
                        __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0U;
                        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 0U;
                    } else if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                        if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                            if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((2U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37 = 0U;
                                }
                                if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    if ((1U & ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last) 
                                               >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)))) {
                                        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending = 1U;
                                    }
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position))) {
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full 
                                        = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                           | (3U & 
                                              ((IData)(1U) 
                                               << (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank))));
                                }
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                    if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state))) {
                                        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full 
                                            = ((~ ((IData)(1U) 
                                                   << (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))) 
                                               & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full));
                                    }
                                }
                            }
                        }
                    }
                }
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position))) {
                                    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last 
                                        = (((~ ((IData)(1U) 
                                                << (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank))) 
                                            & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_last)) 
                                           | (3U & 
                                              (((3U 
                                                 == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)) 
                                                & (7U 
                                                   == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index))) 
                                               << (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank))));
                                }
                            }
                        }
                    }
                }
            }
            if (((IData)(vlSelfRef.start_valid) & (IData)(vlSelfRef.start_ready))) {
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 1U;
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 
                    = ((0U == vlSelfRef.total_bytes)
                        ? 1U : 0U);
                __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0U;
                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full = 0U;
                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 0U;
                vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last = 0U;
            } else {
                if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last) {
                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0U;
                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 4U;
                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0U;
                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full = 0U;
                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 0U;
                } else {
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if ((((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)) 
                                  & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                        >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank)))) 
                                 & (0x38U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position)))) {
                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 3U;
                            }
                            if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                        if ((1U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                            if ((7U 
                                                 == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index))) {
                                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 4U;
                                            }
                                        }
                                    } else if ((1U 
                                                & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) {
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 2U;
                                    } else if (vlSelfRef.data_last) {
                                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19 = 1U;
                                    }
                                }
                            }
                            if ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending))))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 1U;
                                }
                            } else if ((1U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 2U;
                                }
                            } else if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20 = 0U;
                            }
                        }
                    }
                    if (((IData)(vlSelfRef.result_valid) 
                         & (IData)(vlSelfRef.result_ready))) {
                        __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0U;
                        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 0U;
                    } else if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                        if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                            if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((2U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0 = 0U;
                                }
                                if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    if ((1U & ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last) 
                                               >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)))) {
                                        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending = 1U;
                                    }
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position))) {
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full 
                                        = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                           | (3U & 
                                              ((IData)(1U) 
                                               << (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank))));
                                }
                            }
                            if ((0U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                if ((1U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                    if ((2U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state))) {
                                        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full 
                                            = ((~ ((IData)(1U) 
                                                   << (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))) 
                                               & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full));
                                    }
                                }
                            }
                        }
                    }
                }
                if ((1U & (~ (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.result_valid) 
                                  & (IData)(vlSelfRef.result_ready))))) {
                        if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) {
                            if (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte) {
                                if ((0x3fU == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position))) {
                                    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last 
                                        = (((~ ((IData)(1U) 
                                                << (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank))) 
                                            & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_last)) 
                                           | (3U & 
                                              (((3U 
                                                 == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)) 
                                                & (7U 
                                                   == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index))) 
                                               << (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank))));
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__output_stall_cycles 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__output_stall_cycles_48;
    vlSelfRef.output_stall_cycles = __Vdly__output_stall_cycles_11;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__compressed_blocks 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__compressed_blocks_44;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_cycles 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__round_cycles_45;
    vlSelfRef.compressed_blocks = __Vdly__compressed_blocks_7;
    vlSelfRef.round_cycles = __Vdly__round_cycles_8;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__padding_bytes_46;
    vlSelfRef.padding_bytes = __Vdly__padding_bytes_9;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__input_stall_cycles 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__input_stall_cycles_47;
    vlSelfRef.input_stall_cycles = __Vdly__input_stall_cycles_10;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__accepted_bytes_43;
    vlSelfRef.accepted_bytes = __Vdly__accepted_bytes_6;
    if (__Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_87) {
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words[__Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_86][__Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_85] 
            = (((~ ((IData)(0x000000ffU) << (IData)(__Vdly_Lsb__cu71_sha_pair__DOT__reference__DOT__words_84))) 
                & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
                [__Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_86]
                [__Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_85]) 
               | (0x00000000ffffffffULL & ((IData)(__Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_83) 
                                           << (IData)(__Vdly_Lsb__cu71_sha_pair__DOT__reference__DOT__words_84))));
    }
    if (__Vdly_Set__cu71_sha_pair__DOT__reference__DOT__words_91) {
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words[__Vdly_Dim1__cu71_sha_pair__DOT__reference__DOT__words_90][__Vdly_Dim0__cu71_sha_pair__DOT__reference__DOT__words_89] 
            = __Vdly_Val__cu71_sha_pair__DOT__reference__DOT__words_88;
    }
    if (__Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_78) {
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words[__Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_77][__Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_76] 
            = (((~ ((IData)(0x000000ffU) << (IData)(__Vdly_Lsb__cu71_sha_pair__DOT__candidate__DOT__words_75))) 
                & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
                [__Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_77]
                [__Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_76]) 
               | (0x00000000ffffffffULL & ((IData)(__Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_74) 
                                           << (IData)(__Vdly_Lsb__cu71_sha_pair__DOT__candidate__DOT__words_75))));
    }
    if (__Vdly_Set__cu71_sha_pair__DOT__candidate__DOT__words_82) {
        vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words[__Vdly_Dim1__cu71_sha_pair__DOT__candidate__DOT__words_81][__Vdly_Dim0__cu71_sha_pair__DOT__candidate__DOT__words_80] 
            = __Vdly_Val__cu71_sha_pair__DOT__candidate__DOT__words_79;
    }
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__round_index_54;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__round_index_17;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET___66;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET___29;
    vlSelfRef.__Vdfg_Regularize_252 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__output_stall_cycles 
                                       != vlSelfRef.output_stall_cycles);
    vlSelfRef.__Vdfg_Regularize_242 = (vlSelfRef.compressed_blocks 
                                       != vlSelfRef.cu71_sha_pair__DOT__reference__DOT__compressed_blocks);
    vlSelfRef.__Vdfg_Regularize_253 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_cycles 
                                       != vlSelfRef.round_cycles);
    vlSelfRef.__Vdfg_Regularize_254 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes 
                                       != vlSelfRef.padding_bytes);
    vlSelfRef.__Vdfg_Regularize_251 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__input_stall_cycles 
                                       != vlSelfRef.input_stall_cycles);
    vlSelfRef.__Vdfg_Regularize_240 = (vlSelfRef.accepted_bytes 
                                       != vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes);
    vlSelfRef.initial_word_reference = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words[0U][0U];
    vlSelfRef.initial_word_candidate = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words[0U][0U];
    vlSelfRef.__Vdfg_Regularize_241 = ((IData)(vlSelfRef.aborted) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__aborted));
    vlSelfRef.__Vdfg_Regularize_257 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error) 
                                       != (IData)(vlSelfRef.error));
    vlSelfRef.__Vdfg_Regularize_255 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code) 
                                       != (IData)(vlSelfRef.error_code));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET___73;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET___36;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET___72;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET___35;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET___71;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET___34;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET___70;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET___33;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET___69;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET___32;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET___68;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET___31;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__a 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__a_58;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__ 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET___67;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__a 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__a_21;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__ 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET___30;
    vlSelfRef.digest[0U] = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__;
    vlSelfRef.digest[1U] = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__;
    vlSelfRef.digest[2U] = (IData)((((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__)) 
                                     << 0x00000020U) 
                                    | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__))));
    vlSelfRef.digest[3U] = (IData)(((((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__)) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__))) 
                                    >> 0x00000020U));
    vlSelfRef.digest[4U] = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__;
    vlSelfRef.digest[5U] = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__;
    vlSelfRef.digest[6U] = (IData)((((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__)) 
                                     << 0x00000020U) 
                                    | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__))));
    vlSelfRef.digest[7U] = (IData)(((((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__)) 
                                      << 0x00000020U) 
                                     | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__))) 
                                    >> 0x00000020U));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__core_state_57;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__process_bank_52;
    vlSelfRef.__Vdfg_Regularize_256 = (0U != ((((((
                                                   ((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__ 
                                                     ^ vlSelfRef.digest[0U]) 
                                                    | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__ 
                                                       ^ vlSelfRef.digest[1U])) 
                                                   | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__ 
                                                      ^ vlSelfRef.digest[2U])) 
                                                  | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__ 
                                                     ^ vlSelfRef.digest[3U])) 
                                                 | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__ 
                                                    ^ vlSelfRef.digest[4U])) 
                                                | (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__ 
                                                   ^ vlSelfRef.digest[5U])) 
                                               | ((IData)(
                                                          (((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__)) 
                                                            << 0x00000020U) 
                                                           | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__)))) 
                                                  ^ vlSelfRef.digest[6U])) 
                                              | ((IData)(
                                                         ((((QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__)) 
                                                            << 0x00000020U) 
                                                           | (QData)((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__))) 
                                                          >> 0x00000020U)) 
                                                 ^ vlSelfRef.digest[7U])));
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__core_state_20;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__process_bank_15;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index 
        = (0x0000000fU & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__schedule_word 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank]
        [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index];
    if ((0x10U <= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index))) {
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66 
            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
            [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank]
            [(0x0000000fU & ((IData)(0x0eU) + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index)))];
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_70 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_69 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_70 
                >> 0x00000011U) | (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_70 
                                   << 0x0000000fU));
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_0__ror_68 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_69;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_73 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_72 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_73 
                >> 0x00000013U) | (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_73 
                                   << 0x0000000dU));
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_1__ror_67 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_72;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT____VlemCall_0__small1 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_0__ror_68 
                ^ vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_1__ror_67) 
               ^ (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66 
                  >> 0x0000000aU));
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75 
            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
            [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank]
            [(0x0000000fU & ((IData)(1U) + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index)))];
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_79 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_78 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_79 
                >> 7U) | (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_79 
                          << 0x00000019U));
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_0__ror_77 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_78;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_82 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75;
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_81 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_82 
                >> 0x00000012U) | (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_82 
                                   << 0x0000000eU));
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_1__ror_76 
            = vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_81;
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT____VlemCall_1__small0 
            = ((vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_0__ror_77 
                ^ vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_1__ror_76) 
               ^ (vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75 
                  >> 3U));
        vlSelfRef.cu71_sha_pair__DOT__reference__DOT__schedule_word 
            = (((vlSelfRef.cu71_sha_pair__DOT__reference__DOT____VlemCall_0__small1 
                 + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
                 [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank]
                 [(0x0000000fU & ((IData)(9U) + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index)))]) 
                + vlSelfRef.cu71_sha_pair__DOT__reference__DOT____VlemCall_1__small0) 
               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
               [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank]
               [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index]);
    }
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_89 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_88 
        = ((__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_89 
            >> 6U) | (__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_89 
                      << 0x0000001aU));
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_0__ror_87 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_88;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_92 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_91 
        = ((__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_92 
            >> 0x0000000bU) | (__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_92 
                               << 0x00000015U));
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_1__ror_86 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_91;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_95 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1__x_84;
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_94 
        = ((__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_95 
            >> 0x00000019U) | (__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_95 
                               << 7U));
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_2__ror_85 
        = __Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_94;
    cu71_sha_pair__DOT__reference__DOT____VlemCall_2__big1 
        = ((__Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_0__ror_87 
            ^ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_1__ror_86) 
           ^ __Vfunc_cu71_sha_pair__DOT__reference__DOT__big1____VlefCall_2__ror_85);
    __Vfunc_cu71_sha_pair__DOT__reference__DOT__constant_k__t_97 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index;
    cu71_sha_pair__DOT__reference__DOT____VlemCall_3__constant_k 
        = Vcu71_sha_pair__ConstPool__CONST_0[(0x07ffffffU 
                                              & (IData)(__Vfunc_cu71_sha_pair__DOT__reference__DOT__constant_k__t_97))];
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__temp1 
        = ((((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__h 
              + cu71_sha_pair__DOT__reference__DOT____VlemCall_2__big1) 
             + ((vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e 
                 & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__f) 
                ^ ((~ vlSelfRef.cu71_sha_pair__DOT__reference__DOT__e) 
                   & vlSelfRef.cu71_sha_pair__DOT__reference__DOT__g))) 
            + cu71_sha_pair__DOT__reference__DOT____VlemCall_3__constant_k) 
           + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__schedule_word);
    vlSelfRef.debug_core_state = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state;
    vlSelfRef.__Vdfg_Regularize_244 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state));
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index 
        = (0x0000000fU & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index));
    cu71_sha_pair__DOT__candidate__DOT__schedule_word 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank]
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank]
        [(0x0000000fU & ((IData)(0x0eU) + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index)))];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_4 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_3 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_4 
            >> 0x00000011U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_4 
                               << 0x0000000fU));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_0__ror_2 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_3;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_7 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_6 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_7 
            >> 0x00000013U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_7 
                               << 0x0000000dU));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_1__ror_1 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_6;
    cu71_sha_pair__DOT__candidate__DOT____VlemCall_0__small1 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_0__ror_2 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1____VlefCall_1__ror_1) 
           ^ (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0 
              >> 0x0000000aU));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank]
        [(0x0000000fU & ((IData)(1U) + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index)))];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_13 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_12 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_13 
            >> 7U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_13 
                      << 0x00000019U));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_0__ror_11 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_12;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_16 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_15 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_16 
            >> 0x00000012U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_16 
                               << 0x0000000eU));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_1__ror_10 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_15;
    cu71_sha_pair__DOT__candidate__DOT____VlemCall_1__small0 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_0__ror_11 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0____VlefCall_1__ror_10) 
           ^ (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__small0__x_9 
              >> 3U));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank]
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21 
        = cu71_sha_pair__DOT__candidate__DOT____VlemCall_1__small0;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank]
        [(0x0000000fU & ((IData)(9U) + (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index)))];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__x_19 
        = cu71_sha_pair__DOT__candidate__DOT____VlemCall_0__small1;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s0_23 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__x_19 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24 
        = (((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__x_19 
             & (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20 
                | __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21)) 
            | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20 
               & __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21)) 
           << 1U);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s1_25 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s0_23 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c1_26 
        = (((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s0_23 
             & (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24 
                | __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22)) 
            | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c0_24 
               & __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__w_22)) 
           << 1U);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__Vfuncout_18 
        = (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__s1_25 
           + __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__c1_26);
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__future_word 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__Vfuncout_18;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_32 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_31 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_32 
            >> 6U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_32 
                      << 0x0000001aU));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_0__ror_30 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_31;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_35 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_34 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_35 
            >> 0x0000000bU) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_35 
                               << 0x00000015U));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_1__ror_29 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_34;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_38 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1__x_27;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_37 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_38 
            >> 0x00000019U) | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__x_38 
                               << 7U));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_2__ror_28 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__ror__Vfuncout_37;
    cu71_sha_pair__DOT__candidate__DOT____VlemCall_2__big1 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_0__ror_30 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_1__ror_29) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__big1____VlefCall_2__ror_28);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__constant_k__t_40 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index;
    cu71_sha_pair__DOT__candidate__DOT____VlemCall_3__constant_k 
        = Vcu71_sha_pair__ConstPool__CONST_0[(0x07ffffffU 
                                              & (IData)(__Vfunc_cu71_sha_pair__DOT__candidate__DOT__constant_k__t_40))];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46 
        = cu71_sha_pair__DOT__candidate__DOT__schedule_word;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45 
        = cu71_sha_pair__DOT__candidate__DOT____VlemCall_3__constant_k;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44 
        = ((vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e 
            & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__f) 
           ^ ((~ vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__e) 
              & vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__g));
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43 
        = cu71_sha_pair__DOT__candidate__DOT____VlemCall_2__big1;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__x_42 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__h;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s0_47 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__x_42 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48 
        = (((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__x_42 
             & (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43 
                | __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44)) 
            | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__y_43 
               & __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__z_44)) 
           << 1U);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s1_49 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s0_47 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50 
        = (((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s0_47 
             & (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48 
                | __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45)) 
            | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c0_48 
               & __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__w_45)) 
           << 1U);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s2_51 
        = ((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s1_49 
            ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50) 
           ^ __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c2_52 
        = (((__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s1_49 
             & (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50 
                | __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46)) 
            | (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c1_50 
               & __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__v_46)) 
           << 1U);
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__Vfuncout_41 
        = (__Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__s2_51 
           + __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__c2_52);
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__temp1 
        = __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add5_mod__Vfuncout_41;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__length_index 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__length_index_55;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__byte_position_53;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_bank_51;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__fill_state_56;
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active 
        = __Vdly__cu71_sha_pair__DOT__reference__DOT__active_37;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__length_index 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__length_index_18;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__byte_position_16;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_bank_14;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__fill_state_19;
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active 
        = __Vdly__cu71_sha_pair__DOT__candidate__DOT__active_0;
    vlSelfRef.__Vdfg_Regularize_247 = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                                >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank))));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready 
        = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
                    | (IData)(vlSelfRef.__Vdfg_Regularize_237))));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid 
        = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
           & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
              & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_pending)));
    vlSelfRef.__Vdfg_Regularize_245 = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                                >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank))));
    vlSelfRef.debug_fill_state = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state;
    vlSelfRef.__Vdfg_Regularize_243 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state));
    vlSelfRef.busy = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active;
    vlSelfRef.__Vdfg_Regularize_239 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active));
    vlSelfRef.start_ready = (1U & (~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                      | (IData)(vlSelfRef.__Vdfg_Regularize_237))));
    vlSelfRef.result_valid = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                              & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                                 & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__result_pending)));
    vlSelfRef.__Vdfg_Regularize_249 = ((IData)(vlSelfRef.__Vdfg_Regularize_247) 
                                       & ((~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                                              >> 2U)) 
                                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active)));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready 
        = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active) 
           & ((IData)(vlSelfRef.__Vdfg_Regularize_247) 
              & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                 & ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state)) 
                    & (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes 
                       < vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes)))));
    vlSelfRef.__Vdfg_Regularize_250 = ((IData)(vlSelfRef.__Vdfg_Regularize_245) 
                                       & ((~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                              >> 2U)) 
                                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active)));
    vlSelfRef.data_ready = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                            & ((IData)(vlSelfRef.__Vdfg_Regularize_245) 
                               & ((~ (IData)(vlSelfRef.__Vdfg_Regularize_237)) 
                                  & ((0U == (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state)) 
                                     & (vlSelfRef.accepted_bytes 
                                        < vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes)))));
    __Vdfg_Regularize_238 = ((IData)(vlSelfRef.start_ready) 
                             != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__start_ready));
    __Vdfg_Regularize_259 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__result_valid) 
                             != (IData)(vlSelfRef.result_valid));
    vlSelfRef.__Vdfg_Regularize_248 = ((IData)(vlSelfRef.data_valid) 
                                       & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready));
    vlSelfRef.__Vdfg_Regularize_246 = ((IData)(vlSelfRef.data_valid) 
                                       & (IData)(vlSelfRef.data_ready));
    __Vdfg_Regularize_258 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__data_ready) 
                             != (IData)(vlSelfRef.data_ready));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bad_last 
        = (((IData)(vlSelfRef.data_last) != (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__message_bytes 
                                             == ((IData)(1U) 
                                                 + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes))) 
           & (IData)(vlSelfRef.__Vdfg_Regularize_248));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__write_byte 
        = (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))
             ? ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                | (0x38U != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__byte_position)))
             : ((IData)(vlSelfRef.__Vdfg_Regularize_248) 
                | (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state))) 
           & (IData)(vlSelfRef.__Vdfg_Regularize_249));
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bad_last 
        = (((IData)(vlSelfRef.data_last) != (vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__message_bytes 
                                             == ((IData)(1U) 
                                                 + vlSelfRef.accepted_bytes))) 
           & (IData)(vlSelfRef.__Vdfg_Regularize_246));
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__write_byte 
        = (((2U & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))
             ? ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                | (0x38U != (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__byte_position)))
             : ((IData)(vlSelfRef.__Vdfg_Regularize_246) 
                | (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state))) 
           & (IData)(vlSelfRef.__Vdfg_Regularize_250));
    vlSelfRef.mismatch_fields = (((((((IData)(vlSelfRef.__Vdfg_Regularize_244) 
                                      << 3U) | ((IData)(vlSelfRef.__Vdfg_Regularize_243) 
                                                << 2U)) 
                                    | (((IData)(vlSelfRef.__Vdfg_Regularize_252) 
                                        << 1U) | (IData)(vlSelfRef.__Vdfg_Regularize_251))) 
                                   << 0x0000000cU) 
                                  | (((((IData)(vlSelfRef.__Vdfg_Regularize_254) 
                                        << 3U) | ((IData)(vlSelfRef.__Vdfg_Regularize_253) 
                                                  << 2U)) 
                                      | (((IData)(vlSelfRef.__Vdfg_Regularize_242) 
                                          << 1U) | (IData)(vlSelfRef.__Vdfg_Regularize_240))) 
                                     << 8U)) | ((((
                                                   ((IData)(vlSelfRef.__Vdfg_Regularize_255) 
                                                    << 3U) 
                                                   | ((IData)(vlSelfRef.__Vdfg_Regularize_241) 
                                                      << 2U)) 
                                                  | (((IData)(vlSelfRef.__Vdfg_Regularize_257) 
                                                      << 1U) 
                                                     | (IData)(vlSelfRef.__Vdfg_Regularize_239))) 
                                                 << 4U) 
                                                | ((((IData)(vlSelfRef.__Vdfg_Regularize_256) 
                                                     << 3U) 
                                                    | ((IData)(__Vdfg_Regularize_259) 
                                                       << 2U)) 
                                                   | (((IData)(__Vdfg_Regularize_258) 
                                                       << 1U) 
                                                      | (IData)(__Vdfg_Regularize_238)))));
    vlSelfRef.mismatch_any = ((IData)(vlSelfRef.__Vdfg_Regularize_244) 
                              | ((IData)(vlSelfRef.__Vdfg_Regularize_243) 
                                 | ((IData)(vlSelfRef.__Vdfg_Regularize_252) 
                                    | ((IData)(vlSelfRef.__Vdfg_Regularize_251) 
                                       | ((IData)(vlSelfRef.__Vdfg_Regularize_254) 
                                          | ((IData)(vlSelfRef.__Vdfg_Regularize_253) 
                                             | ((IData)(vlSelfRef.__Vdfg_Regularize_242) 
                                                | ((IData)(vlSelfRef.__Vdfg_Regularize_240) 
                                                   | ((IData)(vlSelfRef.__Vdfg_Regularize_255) 
                                                      | ((IData)(vlSelfRef.__Vdfg_Regularize_241) 
                                                         | ((IData)(vlSelfRef.__Vdfg_Regularize_257) 
                                                            | ((IData)(__Vdfg_Regularize_238) 
                                                               | ((IData)(__Vdfg_Regularize_258) 
                                                                  | ((IData)(__Vdfg_Regularize_259) 
                                                                     | ((IData)(vlSelfRef.__Vdfg_Regularize_239) 
                                                                        | (IData)(vlSelfRef.__Vdfg_Regularize_256))))))))))))))));
}

void Vcu71_sha_pair___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

void Vcu71_sha_pair___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((1U > n));
}

#ifdef VL_DEBUG
void Vcu71_sha_pair___024root___eval_debug_assertions(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_debug_assertions\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst & 0xfeU)))) {
        Verilated::overWidthError("rst");
    }
    if (VL_UNLIKELY(((vlSelfRef.abort_i & 0xfeU)))) {
        Verilated::overWidthError("abort_i");
    }
    if (VL_UNLIKELY(((vlSelfRef.start_valid & 0xfeU)))) {
        Verilated::overWidthError("start_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.data_valid & 0xfeU)))) {
        Verilated::overWidthError("data_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.data_last & 0xfeU)))) {
        Verilated::overWidthError("data_last");
    }
    if (VL_UNLIKELY(((vlSelfRef.result_ready & 0xfeU)))) {
        Verilated::overWidthError("result_ready");
    }
}
#endif  // VL_DEBUG
