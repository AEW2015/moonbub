// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_sha_pair.h for the primary calling header

#include "Vcu71_sha_pair__pch.h"

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_static(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_static\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__rst__0 = vlSelfRef.rst;
    vlSelfRef.__Vtrigprevexpr___TOP__abort_i__0 = vlSelfRef.abort_i;
    vlSelfRef.__Vtrigprevexpr___TOP__start_valid__0 
        = vlSelfRef.start_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__total_bytes__0 
        = vlSelfRef.total_bytes;
    vlSelfRef.__Vtrigprevexpr___TOP__data_valid__0 
        = vlSelfRef.data_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__data__0 = vlSelfRef.data;
    vlSelfRef.__Vtrigprevexpr___TOP__data_last__0 = vlSelfRef.data_last;
    vlSelfRef.__Vtrigprevexpr___TOP__result_ready__0 
        = vlSelfRef.result_ready;
    vlSelfRef.__Vtrigprevexpr___TOP__clk__1 = vlSelfRef.clk;
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_initial(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_initial\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vcu71_sha_pair___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);
VL_ATTR_COLD void Vcu71_sha_pair___024root___stl_comb__TOP__0(Vcu71_sha_pair___024root* vlSelf);

VL_ATTR_COLD bool Vcu71_sha_pair___024root___eval_stl(Vcu71_sha_pair___024root* vlSelf, CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_stl\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(firstIteration)));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcu71_sha_pair___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vcu71_sha_pair___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        {
            // Inlined CFunc: _eval_body__stl
            if ((((1ULL & vlSelfRef.__VstlTriggered[0U])) != 0ULL)) {
                Vcu71_sha_pair___024root___stl_comb__TOP__0(vlSelf);
            }
        }
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__stl(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__stl\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_sha_pair___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__ico(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__ico\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_sha_pair___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__act(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__act\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_sha_pair___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__nba(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__nba\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_sha_pair___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__obs(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__obs\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__react(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_dump_triggers__react\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_final(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___eval_final\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_sha_pair___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vcu71_sha_pair___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vcu71_sha_pair___024root___stl_comb__TOP__0(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___stl_comb__TOP__0\n"); );
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
    // Body
    vlSelfRef.initial_word_reference = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words[0U][0U];
    vlSelfRef.initial_word_candidate = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words[0U][0U];
    vlSelfRef.busy = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active;
    vlSelfRef.debug_core_state = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state;
    vlSelfRef.debug_fill_state = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state;
    vlSelfRef.__Vdfg_Regularize_239 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active));
    vlSelfRef.__Vdfg_Regularize_240 = (vlSelfRef.accepted_bytes 
                                       != vlSelfRef.cu71_sha_pair__DOT__reference__DOT__accepted_bytes);
    vlSelfRef.__Vdfg_Regularize_241 = ((IData)(vlSelfRef.aborted) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__aborted));
    vlSelfRef.__Vdfg_Regularize_242 = (vlSelfRef.compressed_blocks 
                                       != vlSelfRef.cu71_sha_pair__DOT__reference__DOT__compressed_blocks);
    vlSelfRef.__Vdfg_Regularize_243 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state));
    vlSelfRef.__Vdfg_Regularize_244 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__core_state) 
                                       != (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__core_state));
    vlSelfRef.__Vdfg_Regularize_251 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__input_stall_cycles 
                                       != vlSelfRef.input_stall_cycles);
    vlSelfRef.__Vdfg_Regularize_252 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__output_stall_cycles 
                                       != vlSelfRef.output_stall_cycles);
    vlSelfRef.__Vdfg_Regularize_253 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_cycles 
                                       != vlSelfRef.round_cycles);
    vlSelfRef.__Vdfg_Regularize_254 = (vlSelfRef.cu71_sha_pair__DOT__reference__DOT__padding_bytes 
                                       != vlSelfRef.padding_bytes);
    vlSelfRef.__Vdfg_Regularize_255 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error_code) 
                                       != (IData)(vlSelfRef.error_code));
    vlSelfRef.__Vdfg_Regularize_257 = ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__error) 
                                       != (IData)(vlSelfRef.error));
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
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index 
        = (0x0000000fU & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index));
    vlSelfRef.cu71_sha_pair__DOT__reference__DOT__schedule_word 
        = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))]
        [vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index];
    if ((0x10U <= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__round_index))) {
        vlSelfRef.__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66 
            = vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
            [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
              && (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))]
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
            [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
              && (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))]
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
                 [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
                   && (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))]
                 [(0x0000000fU & ((IData)(9U) + (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__ring_index)))]) 
                + vlSelfRef.cu71_sha_pair__DOT__reference__DOT____VlemCall_1__small0) 
               + vlSelfRef.cu71_sha_pair__DOT__reference__DOT__words
               [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank)) 
                 && (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__process_bank))]
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
    vlSelfRef.__Vdfg_Regularize_245 = (1U & (~ ((0U 
                                                 >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank)) 
                                                && (1U 
                                                    & ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__bank_full) 
                                                       >> (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_bank))))));
    vlSelfRef.__Vdfg_Regularize_247 = (1U & (~ ((0U 
                                                 >= (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank)) 
                                                && (1U 
                                                    & ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__bank_full) 
                                                       >> (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_bank))))));
    vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index 
        = (0x0000000fU & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__round_index));
    cu71_sha_pair__DOT__candidate__DOT__schedule_word 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))]
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__small1__x_0 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))]
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
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))]
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
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))]
        [vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__ring_index];
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__z_21 
        = cu71_sha_pair__DOT__candidate__DOT____VlemCall_1__small0;
    __Vfunc_cu71_sha_pair__DOT__candidate__DOT__add4_mod__y_20 
        = vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__words
        [((0U >= (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank)) 
          && (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__process_bank))]
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
    vlSelfRef.__Vdfg_Regularize_237 = ((IData)(vlSelfRef.rst) 
                                       | (IData)(vlSelfRef.abort_i));
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
    vlSelfRef.__Vdfg_Regularize_250 = ((IData)(vlSelfRef.__Vdfg_Regularize_245) 
                                       & ((~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__fill_state) 
                                              >> 2U)) 
                                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__candidate__DOT__active)));
    vlSelfRef.__Vdfg_Regularize_249 = ((IData)(vlSelfRef.__Vdfg_Regularize_247) 
                                       & ((~ ((IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__fill_state) 
                                              >> 2U)) 
                                          & (IData)(vlSelfRef.cu71_sha_pair__DOT__reference__DOT__active)));
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

bool Vcu71_sha_pair___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_sha_pair___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @( clk)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @( rst)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @( abort_i)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 3U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 3 is active: @( start_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 4U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 4 is active: @( total_bytes)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 5U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 5 is active: @( data_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 6U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 6 is active: @( data)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 7U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 7 is active: @( data_last)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 8U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 8 is active: @( result_ready)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vcu71_sha_pair___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_sha_pair___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_sha_pair___024root___ctor_var_reset(Vcu71_sha_pair___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_sha_pair___024root___ctor_var_reset\n"); );
    Vcu71_sha_pair__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->rst = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18209466448985614591ull);
    vlSelf->abort_i = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1110857442356679346ull);
    vlSelf->start_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15236367654457824803ull);
    vlSelf->start_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12792651944731561107ull);
    vlSelf->total_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4650379409647283494ull);
    vlSelf->data_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10948900208641353254ull);
    vlSelf->data_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3296321098809439440ull);
    vlSelf->data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 10363016170300574568ull);
    vlSelf->data_last = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18421896132961756864ull);
    vlSelf->result_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8916821378957780047ull);
    vlSelf->result_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16967871585272011918ull);
    VL_SCOPED_RAND_RESET_W(256, vlSelf->digest, __VscopeHash, 154021876994649933ull);
    vlSelf->busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6386567572483775230ull);
    vlSelf->error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10895628271336369153ull);
    vlSelf->aborted = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4868682049854349875ull);
    vlSelf->error_code = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16220268221051066965ull);
    vlSelf->accepted_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1782420654644358480ull);
    vlSelf->compressed_blocks = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3224024065536689750ull);
    vlSelf->round_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12896224388562779730ull);
    vlSelf->padding_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12644861653052941298ull);
    vlSelf->input_stall_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14793041772824781412ull);
    vlSelf->output_stall_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10850329943875679309ull);
    vlSelf->debug_fill_state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 7196795588089458417ull);
    vlSelf->debug_core_state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 3080167396509140498ull);
    vlSelf->mismatch_any = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11110810788871031894ull);
    vlSelf->mismatch_fields = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7545416991321955152ull);
    vlSelf->initial_word_reference = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8468191381426051657ull);
    vlSelf->initial_word_candidate = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6713399876289175001ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__fill_state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 6064463290180329744ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__core_state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 13849377993742633639ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__active = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 9733989752066197636ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__result_pending = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7533633561667009452ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__message_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7990437644400651414ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 16; ++__Vi1) {
            vlSelf->cu71_sha_pair__DOT__candidate__DOT__words[__Vi0][__Vi1] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11138770661492783747ull);
        }
    }
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__0__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1975573684823944077ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__1__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16525267366554756638ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__2__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11073030106904035659ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__3__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14732845160011515345ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__4__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13179548449482917996ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__5__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16559368379883336695ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__6__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17415485847728243975ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__hash_state__BRA__7__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11517829049071909312ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__a = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3159845087892154361ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__b = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10982850306845718910ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__c = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 116187459180169196ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__d = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4753863440185560798ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__e = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13594930197762537837ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__f = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9160346010074796468ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__g = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3125481424733636700ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__h = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4893410282375796600ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__bank_full = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13449556423203756587ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__bank_last = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16542452697066337909ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__fill_bank = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5004102661604146294ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__process_bank = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13396654203232700665ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__byte_position = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 3842157007978270958ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__round_index = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 14854867959472910710ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__length_index = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 15289274472276219466ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__write_byte = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15729788757171337993ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__bad_last = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15151216935024035655ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__future_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6108229897363391462ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__temp1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16934840857932156400ull);
    vlSelf->cu71_sha_pair__DOT__candidate__DOT__ring_index = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 5704872261975849677ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__start_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16587949195362239126ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__data_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1518726912315477076ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__result_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14765236698232027256ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16846872087045567232ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__aborted = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2522733536863171366ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__error_code = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 13156423501637360326ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__accepted_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15832679389893839408ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__compressed_blocks = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 334950168424460589ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__round_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4051450425980342368ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__padding_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1534102090228580501ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__input_stall_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17574017369298753623ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__output_stall_cycles = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 10391271864056470833ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__fill_state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 52320137370393092ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__core_state = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 583230213650084583ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__active = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16591609491076523288ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__result_pending = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 15329764755839164199ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__message_bytes = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6452552954746042369ull);
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 16; ++__Vi1) {
            vlSelf->cu71_sha_pair__DOT__reference__DOT__words[__Vi0][__Vi1] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6806334331414300667ull);
        }
    }
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__0__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5641642477118207816ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__1__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1469191155797152257ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__2__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1694146235102256454ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__3__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6492636703869925151ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__4__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15402495279927560193ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__5__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7538440410516126272ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__6__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3512897361552892368ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__hash_state__BRA__7__KET__ = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7475395513470503491ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__a = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 17596458862019062750ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__b = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6164509277895337325ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__c = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14512417168398829743ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__d = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2238679926861177099ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__e = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8121054272332239744ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__f = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9623340326684761347ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__g = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15436095716122569206ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__h = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3656758544384920056ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__bank_full = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2436627433437991080ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__bank_last = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17118213742565265493ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__fill_bank = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1140131024837265558ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__process_bank = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18077181622061066705ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__byte_position = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 15824709662536260655ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__round_index = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 8301763004636335144ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__length_index = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 9981104836516954941ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__write_byte = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16497271218334625972ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__bad_last = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14229834590177014208ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__schedule_word = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15643813991667653636ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__temp1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13162147608024086944ull);
    vlSelf->cu71_sha_pair__DOT__reference__DOT__ring_index = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 12591885187516920381ull);
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1__x_66 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_1__ror_67 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small1____VlefCall_0__ror_68 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_69 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_70 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_72 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_73 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0__x_75 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_1__ror_76 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__small0____VlefCall_0__ror_77 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_78 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_79 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__Vfuncout_81 = 0;
    vlSelf->__Vfunc_cu71_sha_pair__DOT__reference__DOT__ror__x_82 = 0;
    vlSelf->__Vdfg_Regularize_237 = 0;
    vlSelf->__Vdfg_Regularize_239 = 0;
    vlSelf->__Vdfg_Regularize_240 = 0;
    vlSelf->__Vdfg_Regularize_241 = 0;
    vlSelf->__Vdfg_Regularize_242 = 0;
    vlSelf->__Vdfg_Regularize_243 = 0;
    vlSelf->__Vdfg_Regularize_244 = 0;
    vlSelf->__Vdfg_Regularize_245 = 0;
    vlSelf->__Vdfg_Regularize_246 = 0;
    vlSelf->__Vdfg_Regularize_247 = 0;
    vlSelf->__Vdfg_Regularize_248 = 0;
    vlSelf->__Vdfg_Regularize_249 = 0;
    vlSelf->__Vdfg_Regularize_250 = 0;
    vlSelf->__Vdfg_Regularize_251 = 0;
    vlSelf->__Vdfg_Regularize_252 = 0;
    vlSelf->__Vdfg_Regularize_253 = 0;
    vlSelf->__Vdfg_Regularize_254 = 0;
    vlSelf->__Vdfg_Regularize_255 = 0;
    vlSelf->__Vdfg_Regularize_256 = 0;
    vlSelf->__Vdfg_Regularize_257 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rst__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__abort_i__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__start_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__total_bytes__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__data_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__data__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__data_last__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__result_ready__0 = 0;
    vlSelf->__VicoDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__1 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
