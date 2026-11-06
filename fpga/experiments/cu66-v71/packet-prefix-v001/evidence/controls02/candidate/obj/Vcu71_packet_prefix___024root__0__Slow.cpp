// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_packet_prefix.h for the primary calling header

#include "Vcu71_packet_prefix__pch.h"

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_static(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_static\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__rst__0 = vlSelfRef.rst;
    vlSelfRef.__Vtrigprevexpr___TOP__abort_i__0 = vlSelfRef.abort_i;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_valid__0 = vlSelfRef.cfg_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_packet_bytes__0 
        = vlSelfRef.cfg_packet_bytes;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_last_valid__0 
        = vlSelfRef.cfg_last_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_last_frame_id__0 
        = vlSelfRef.cfg_last_frame_id;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_valid__0 
        = vlSelfRef.cfg_reference_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_id__0 
        = vlSelfRef.cfg_reference_id;
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[0U] 
        = vlSelfRef.cfg_reference_tag[0U];
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[1U] 
        = vlSelfRef.cfg_reference_tag[1U];
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[2U] 
        = vlSelfRef.cfg_reference_tag[2U];
    vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[3U] 
        = vlSelfRef.cfg_reference_tag[3U];
    vlSelfRef.__Vtrigprevexpr___TOP__rd_req_ready__0 
        = vlSelfRef.rd_req_ready;
    vlSelfRef.__Vtrigprevexpr___TOP__rd_rsp_valid__0 
        = vlSelfRef.rd_rsp_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__rd_rsp_data__0 
        = vlSelfRef.rd_rsp_data;
    vlSelfRef.__Vtrigprevexpr___TOP__metadata_ready__0 
        = vlSelfRef.metadata_ready;
    vlSelfRef.__Vtrigprevexpr___TOP__qmap_req_valid__0 
        = vlSelfRef.qmap_req_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__qmap_req_index__0 
        = vlSelfRef.qmap_req_index;
    vlSelfRef.__Vtrigprevexpr___TOP__commit_valid__0 
        = vlSelfRef.commit_valid;
    vlSelfRef.__Vtrigprevexpr___TOP__clk__1 = vlSelfRef.clk;
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_initial(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_initial\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vcu71_packet_prefix___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in);
VL_ATTR_COLD void Vcu71_packet_prefix___024root___stl_comb__TOP__0(Vcu71_packet_prefix___024root* vlSelf);

VL_ATTR_COLD bool Vcu71_packet_prefix___024root___eval_stl(Vcu71_packet_prefix___024root* vlSelf, CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_stl\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VstlExecute;
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (IData)((IData)(firstIteration)));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcu71_packet_prefix___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vcu71_packet_prefix___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        {
            // Inlined CFunc: _eval_body__stl
            if ((((1ULL & vlSelfRef.__VstlTriggered[0U])) != 0ULL)) {
                Vcu71_packet_prefix___024root___stl_comb__TOP__0(vlSelf);
            }
        }
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__stl(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__stl\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_packet_prefix___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__ico(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__ico\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_packet_prefix___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__act(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__act\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_packet_prefix___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__nba(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__nba\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vcu71_packet_prefix___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__obs(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__obs\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_dump_triggers__react(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_dump_triggers__react\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vcu71_packet_prefix___024root___eval_final(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_final\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__stl(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_packet_prefix___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vcu71_packet_prefix___024root___trigger_anySet__stl(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___trigger_anySet__stl\n"); );
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

VL_ATTR_COLD void Vcu71_packet_prefix___024root___stl_comb__TOP__0(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___stl_comb__TOP__0\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __Vdfg_Regularize_510;
    __Vdfg_Regularize_510 = 0;
    CData/*0:0*/ __Vdfg_Regularize_514;
    __Vdfg_Regularize_514 = 0;
    CData/*0:0*/ __Vdfg_Regularize_518;
    __Vdfg_Regularize_518 = 0;
    CData/*7:0*/ __Vdfg_Regularize_521;
    __Vdfg_Regularize_521 = 0;
    CData/*7:0*/ __Vdfg_Regularize_522;
    __Vdfg_Regularize_522 = 0;
    // Body
    vlSelfRef.rd_rsp_ready = ((2U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)) 
                              | (9U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.busy = (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state));
    vlSelfRef.debug_state = vlSelfRef.cu71_packet_prefix__DOT__state;
    vlSelfRef.rd_req_addr = vlSelfRef.cu71_packet_prefix__DOT__scan_addr;
    vlSelfRef.__Vdfg_Regularize_502 = ((0x32U == vlSelfRef.cu71_packet_prefix__DOT__hud_header[2U])
                                        ? 2U : ((0x32U 
                                                 == vlSelfRef.cu71_packet_prefix__DOT__hud_header[3U])
                                                 ? 3U
                                                 : 4U));
    vlSelfRef.__Vdfg_Regularize_503 = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[57U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[56U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[55U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[54U]));
    vlSelfRef.__Vdfg_Regularize_504 = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[61U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[60U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[59U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[58U]));
    vlSelfRef.__Vdfg_Regularize_505 = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[65U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[64U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[63U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[62U]));
    vlSelfRef.__Vdfg_Regularize_506 = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[69U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[68U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[67U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[66U]));
    vlSelfRef.cfg_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                           & (0U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.rd_req_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                              & (1U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.metadata_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                                & (7U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.commit_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                              & (8U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.__Vdfg_Regularize_507 = ((0x0088U <= (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)) 
                                       & (0x01daU > (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)));
    if ((0x00000546U > (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                         - (IData)(0x00000088U)) << 2U))) {
        __Vdfg_Regularize_521 = (8U & (- (IData)((3U 
                                                  == 
                                                  (3U 
                                                   & ((IData)(vlSelfRef.rd_rsp_data) 
                                                      >> 6U))))));
        __Vdfg_Regularize_510 = (3U == (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                              >> 6U)));
    } else {
        __Vdfg_Regularize_521 = (8U & (- (IData)((0U 
                                                  != 
                                                  (3U 
                                                   & ((IData)(vlSelfRef.rd_rsp_data) 
                                                      >> 6U))))));
        __Vdfg_Regularize_510 = (0U != (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                              >> 6U)));
    }
    vlSelfRef.__Vdfg_Regularize_524 = ((5U != (IData)(vlSelfRef.rd_rsp_data)) 
                                       & ((6U != (IData)(vlSelfRef.rd_rsp_data)) 
                                          & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                             == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__2__KET__))));
    vlSelfRef.__Vdfg_Regularize_525 = ((5U != (IData)(vlSelfRef.rd_rsp_data)) 
                                       & ((6U != (IData)(vlSelfRef.rd_rsp_data)) 
                                          & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                             == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__1__KET__))));
    vlSelfRef.__Vdfg_Regularize_526 = ((5U != (IData)(vlSelfRef.rd_rsp_data)) 
                                       & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                           == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__0__KET__)) 
                                          & (6U != (IData)(vlSelfRef.rd_rsp_data))));
    vlSelfRef.__Vdfg_Regularize_527 = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                        >= (IData)(vlSelfRef.cu71_packet_prefix__DOT__vector_start)) 
                                       & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                           < (IData)(vlSelfRef.cu71_packet_prefix__DOT__vector_end)) 
                                          & (0U != (IData)(vlSelfRef.rd_rsp_data))));
    vlSelfRef.qmap_req_ready = ((IData)(vlSelfRef.commit_ready) 
                                & ((~ (IData)(vlSelfRef.commit_valid)) 
                                   & (0x0546U > (IData)(vlSelfRef.qmap_req_index))));
    if ((0x00000546U > ((IData)(1U) + (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                        - (IData)(0x00000088U)) 
                                       << 2U)))) {
        __Vdfg_Regularize_522 = ((3U == (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                               >> 4U)))
                                  ? 8U : (IData)(__Vdfg_Regularize_521));
        __Vdfg_Regularize_514 = ((IData)(__Vdfg_Regularize_510) 
                                 | (3U == (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                                 >> 4U))));
    } else {
        __Vdfg_Regularize_522 = ((0U != (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                               >> 4U)))
                                  ? 8U : (IData)(__Vdfg_Regularize_521));
        __Vdfg_Regularize_514 = ((IData)(__Vdfg_Regularize_510) 
                                 | (0U != (0x30U & (IData)(vlSelfRef.rd_rsp_data))));
    }
    if ((0x00000546U > ((IData)(2U) + (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                        - (IData)(0x00000088U)) 
                                       << 2U)))) {
        vlSelfRef.__Vdfg_Regularize_523 = ((3U == (3U 
                                                   & ((IData)(vlSelfRef.rd_rsp_data) 
                                                      >> 2U)))
                                            ? 8U : (IData)(__Vdfg_Regularize_522));
        __Vdfg_Regularize_518 = ((IData)(__Vdfg_Regularize_514) 
                                 | (3U == (3U & ((IData)(vlSelfRef.rd_rsp_data) 
                                                 >> 2U))));
    } else {
        vlSelfRef.__Vdfg_Regularize_523 = ((0U != (3U 
                                                   & ((IData)(vlSelfRef.rd_rsp_data) 
                                                      >> 2U)))
                                            ? 8U : (IData)(__Vdfg_Regularize_522));
        __Vdfg_Regularize_518 = ((IData)(__Vdfg_Regularize_514) 
                                 | (0U != (0x0cU & (IData)(vlSelfRef.rd_rsp_data))));
    }
    vlSelfRef.cu71_packet_prefix__DOT__byte_bad = ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_validated) 
                                                   & ((IData)(vlSelfRef.__Vdfg_Regularize_525) 
                                                      | ((IData)(vlSelfRef.__Vdfg_Regularize_526) 
                                                         | ((IData)(vlSelfRef.__Vdfg_Regularize_527) 
                                                            | ((IData)(vlSelfRef.__Vdfg_Regularize_524) 
                                                               | (((0x00000546U 
                                                                    > 
                                                                    ((IData)(3U) 
                                                                     + 
                                                                     (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                       - (IData)(0x00000088U)) 
                                                                      << 2U)))
                                                                    ? 
                                                                   ((IData)(__Vdfg_Regularize_518) 
                                                                    | (3U 
                                                                       == 
                                                                       (3U 
                                                                        & (IData)(vlSelfRef.rd_rsp_data))))
                                                                    : 
                                                                   ((IData)(__Vdfg_Regularize_518) 
                                                                    | (0U 
                                                                       != 
                                                                       (3U 
                                                                        & (IData)(vlSelfRef.rd_rsp_data))))) 
                                                                  & (IData)(vlSelfRef.__Vdfg_Regularize_507)))))));
}

bool Vcu71_packet_prefix___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_packet_prefix___024root___trigger_anySet__ico(triggers))))) {
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
        VL_DBG_MSGS("         '" + tag + "' region trigger index 3 is active: @( cfg_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 4U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 4 is active: @( cfg_packet_bytes)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 5U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 5 is active: @( cfg_last_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 6U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 6 is active: @( cfg_last_frame_id)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 7U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 7 is active: @( cfg_reference_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 8U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 8 is active: @( cfg_reference_id)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 9U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 9 is active: @( cfg_reference_tag)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000aU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 10 is active: @( rd_req_ready)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000bU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 11 is active: @( rd_rsp_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000cU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 12 is active: @( rd_rsp_data)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000dU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 13 is active: @( metadata_ready)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000eU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 14 is active: @( qmap_req_valid)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x0000000fU)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 15 is active: @( qmap_req_index)\n");
    }
    if ((1U & (IData)((triggers[0U] >> 0x00000010U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 16 is active: @( commit_valid)\n");
    }
    if ((1U & (IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vcu71_packet_prefix___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(Vcu71_packet_prefix___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vcu71_packet_prefix___024root___ctor_var_reset(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___ctor_var_reset\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->rst = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18209466448985614591ull);
    vlSelf->abort_i = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1110857442356679346ull);
    vlSelf->cfg_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6248242304995844936ull);
    vlSelf->cfg_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3984417237715664170ull);
    vlSelf->cfg_packet_bytes = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5182761544599301980ull);
    vlSelf->cfg_last_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10402121523179797374ull);
    vlSelf->cfg_last_frame_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 3862458190147396584ull);
    vlSelf->cfg_reference_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4096155665525079173ull);
    vlSelf->cfg_reference_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7140759645596293714ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->cfg_reference_tag, __VscopeHash, 8075345733609605071ull);
    vlSelf->rd_req_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 14395838297848667942ull);
    vlSelf->rd_req_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1408878927844005764ull);
    vlSelf->rd_req_addr = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6349957078451657563ull);
    vlSelf->rd_rsp_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4497649227636690041ull);
    vlSelf->rd_rsp_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16948567579569796019ull);
    vlSelf->rd_rsp_data = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 14467625881183713250ull);
    vlSelf->metadata_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1570816583568163034ull);
    vlSelf->metadata_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6512428564259405864ull);
    vlSelf->metadata_key = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 17113609300880771613ull);
    vlSelf->metadata_frame_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6155427824713209552ull);
    vlSelf->metadata_reference_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5415375063078241664ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->metadata_reference_tag, __VscopeHash, 5696693109566803841ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->metadata_output_tag, __VscopeHash, 974598148730611453ull);
    vlSelf->metadata_block_size = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 15044074678957590634ull);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->metadata_plane_addr[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6134827458080916260ull);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->metadata_plane_bytes[__Vi0] = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 3636340828435420274ull);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->metadata_plane_dispatch[__Vi0] = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 18279272381123738273ull);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->metadata_plane_blocks[__Vi0] = VL_SCOPED_RAND_RESET_I(17, __VscopeHash, 8555902721737881215ull);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->metadata_plane_blocks_w[__Vi0] = VL_SCOPED_RAND_RESET_I(9, __VscopeHash, 8564105698843232940ull);
    }
    vlSelf->metadata_hud_addr = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 16824865943161492944ull);
    vlSelf->metadata_hud_bytes = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7114496926145080447ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->metadata_hud_reference_tag, __VscopeHash, 15413427755210128612ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->metadata_hud_output_tag, __VscopeHash, 15534408082436544782ull);
    vlSelf->qmap_req_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 18315493681243850043ull);
    vlSelf->qmap_req_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7399887505117530765ull);
    vlSelf->qmap_req_index = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 9665485154675757955ull);
    vlSelf->qmap_rsp_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6193495485187288439ull);
    vlSelf->qmap_rsp_index = VL_SCOPED_RAND_RESET_I(11, __VscopeHash, 3867326904647874440ull);
    vlSelf->qmap_rsp_code = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 11370553000561508534ull);
    vlSelf->commit_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1248538124957539926ull);
    vlSelf->commit_ready = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11432617204652597901ull);
    vlSelf->busy = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6386567572483775230ull);
    vlSelf->done = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10296494685231209730ull);
    vlSelf->aborted = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 4868682049854349875ull);
    vlSelf->error = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 10895628271336369153ull);
    vlSelf->error_code = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 16220268221051066965ull);
    vlSelf->debug_state = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 17458634628187422603ull);
    vlSelf->memory_reads = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2288127246205879336ull);
    vlSelf->cu71_packet_prefix__DOT__state = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 1964262566061171213ull);
    vlSelf->cu71_packet_prefix__DOT__packet_bytes = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1158923468407387310ull);
    vlSelf->cu71_packet_prefix__DOT__scan_addr = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 1289731015273108906ull);
    vlSelf->cu71_packet_prefix__DOT__last_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12034370901795885589ull);
    vlSelf->cu71_packet_prefix__DOT__reference_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11594527641680929165ull);
    vlSelf->cu71_packet_prefix__DOT__outer_validated = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 6917741263079702886ull);
    vlSelf->cu71_packet_prefix__DOT__inner_validated = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11282378934058283612ull);
    vlSelf->cu71_packet_prefix__DOT__last_frame_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 12306103527890727005ull);
    vlSelf->cu71_packet_prefix__DOT__reference_id = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1641719240508595889ull);
    VL_SCOPED_RAND_RESET_W(128, vlSelf->cu71_packet_prefix__DOT__reference_tag, __VscopeHash, 12337078151663809527ull);
    for (int __Vi0 = 0; __Vi0 < 76; ++__Vi0) {
        vlSelf->cu71_packet_prefix__DOT__outer_header[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 15838854354822950748ull);
    }
    for (int __Vi0 = 0; __Vi0 < 60; ++__Vi0) {
        vlSelf->cu71_packet_prefix__DOT__inner_header[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8726239553015146817ull);
    }
    for (int __Vi0 = 0; __Vi0 < 106; ++__Vi0) {
        vlSelf->cu71_packet_prefix__DOT__hud_header[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 5720613272795930449ull);
    }
    for (int __Vi0 = 0; __Vi0 < 338; ++__Vi0) {
        vlSelf->cu71_packet_prefix__DOT__qmap_mem[__Vi0] = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 2153309757948959320ull);
    }
    vlSelf->cu71_packet_prefix__DOT__crc_outer = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2201675915556861107ull);
    vlSelf->cu71_packet_prefix__DOT__crc_inner = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9263990776748393370ull);
    vlSelf->cu71_packet_prefix__DOT__crc_hud = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5060917505145291064ull);
    vlSelf->cu71_packet_prefix__DOT__received_outer = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 4380861926654414718ull);
    vlSelf->cu71_packet_prefix__DOT__received_inner = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 16462491333552066646ull);
    vlSelf->cu71_packet_prefix__DOT__received_hud = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 1157057150646321788ull);
    vlSelf->cu71_packet_prefix__DOT__inner_bytes = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 8863852716647270727ull);
    vlSelf->cu71_packet_prefix__DOT__plane_start__BRA__0__KET__ = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7116046778828910319ull);
    vlSelf->cu71_packet_prefix__DOT__plane_start__BRA__1__KET__ = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 14638707762809874709ull);
    vlSelf->cu71_packet_prefix__DOT__plane_start__BRA__2__KET__ = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 6306808463058310084ull);
    vlSelf->cu71_packet_prefix__DOT__vector_start = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 12469958487311461909ull);
    vlSelf->cu71_packet_prefix__DOT__vector_end = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7972322681739973426ull);
    vlSelf->cu71_packet_prefix__DOT__prefix0 = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 7801559180515330953ull);
    vlSelf->cu71_packet_prefix__DOT__prefix_yu = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 13075351396114628994ull);
    vlSelf->cu71_packet_prefix__DOT__prefix_y = VL_SCOPED_RAND_RESET_I(16, __VscopeHash, 5028399525457821961ull);
    vlSelf->cu71_packet_prefix__DOT__byte_bad = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1687339572815514205ull);
    vlSelf->__Vdfg_Regularize_502 = 0;
    vlSelf->__Vdfg_Regularize_503 = 0;
    vlSelf->__Vdfg_Regularize_504 = 0;
    vlSelf->__Vdfg_Regularize_505 = 0;
    vlSelf->__Vdfg_Regularize_506 = 0;
    vlSelf->__Vdfg_Regularize_507 = 0;
    vlSelf->__Vdfg_Regularize_523 = 0;
    vlSelf->__Vdfg_Regularize_524 = 0;
    vlSelf->__Vdfg_Regularize_525 = 0;
    vlSelf->__Vdfg_Regularize_526 = 0;
    vlSelf->__Vdfg_Regularize_527 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rst__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__abort_i__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_packet_bytes__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_last_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_last_frame_id__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_reference_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__cfg_reference_id__0 = 0;
    VL_ZERO_RESET_W(128, vlSelf->__Vtrigprevexpr___TOP__cfg_reference_tag__0);
    vlSelf->__Vtrigprevexpr___TOP__rd_req_ready__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rd_rsp_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__rd_rsp_data__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__metadata_ready__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__qmap_req_valid__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__qmap_req_index__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__commit_valid__0 = 0;
    vlSelf->__VicoDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__1 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
