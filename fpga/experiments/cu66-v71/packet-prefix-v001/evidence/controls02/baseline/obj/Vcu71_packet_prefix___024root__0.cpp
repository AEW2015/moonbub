// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vcu71_packet_prefix.h for the primary calling header

#include "Vcu71_packet_prefix__pch.h"

void Vcu71_packet_prefix___024root___eval_sample(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_sample\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

void Vcu71_packet_prefix___024root___eval_triggers_vec__ico(Vcu71_packet_prefix___024root* vlSelf);
#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__ico(const VlUnpacked<QData/*63:0*/, 2> &triggers, const std::string &tag);
#endif  // VL_DEBUG
bool Vcu71_packet_prefix___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in);
void Vcu71_packet_prefix___024root___ico_comb__TOP__1(Vcu71_packet_prefix___024root* vlSelf);

bool Vcu71_packet_prefix___024root___eval_ico(Vcu71_packet_prefix___024root* vlSelf, CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_ico\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VicoExecute;
    // Body
    vlSelfRef.__VicoTriggered[1U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VicoTriggered[1U]) 
                                     | (IData)((IData)(firstIteration)));
    Vcu71_packet_prefix___024root___eval_triggers_vec__ico(vlSelf);
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vcu71_packet_prefix___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
    }
#endif
    __VicoExecute = Vcu71_packet_prefix___024root___trigger_anySet__ico(vlSelfRef.__VicoTriggered);
    if (__VicoExecute) {
        {
            // Inlined CFunc: _eval_body__ico
            if ((((4ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
                {
                    // Inlined CFunc: _ico_comb__TOP__0
                    vlSelfRef.cfg_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                                           & (0U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
                    vlSelfRef.rd_req_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                                              & (1U 
                                                 == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
                    vlSelfRef.metadata_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                                                & (7U 
                                                   == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
                    vlSelfRef.commit_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                                              & (8U 
                                                 == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
                }
            }
            if ((((0x0000000000001000ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
                Vcu71_packet_prefix___024root___ico_comb__TOP__1(vlSelf);
            }
            if ((((0x0000000000018004ULL & vlSelfRef.__VicoTriggered[0U])) != 0ULL)) {
                {
                    // Inlined CFunc: _ico_comb__TOP__2
                    vlSelfRef.qmap_req_ready = ((IData)(vlSelfRef.commit_ready) 
                                                & ((~ (IData)(vlSelfRef.commit_valid)) 
                                                   & (0x0546U 
                                                      > (IData)(vlSelfRef.qmap_req_index))));
                }
            }
        }
    }
    return (__VicoExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_prefix___024root___dump_triggers__act(const VlUnpacked<QData/*63:0*/, 1> &triggers, const std::string &tag);
#endif  // VL_DEBUG
void Vcu71_packet_prefix___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in);

bool Vcu71_packet_prefix___024root___eval_act(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_act\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
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
        Vcu71_packet_prefix___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
    }
#endif
    Vcu71_packet_prefix___024root___trigger_orInto__act_vec_vec(vlSelfRef.__VnbaTriggered, vlSelfRef.__VactTriggered);
    return (0U);
}

bool Vcu71_packet_prefix___024root___eval_inact(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_inact\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vcu71_packet_prefix___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in);
void Vcu71_packet_prefix___024root___nba_sequent__TOP__0(Vcu71_packet_prefix___024root* vlSelf);
void Vcu71_packet_prefix___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out);

bool Vcu71_packet_prefix___024root___eval_nba(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_nba\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = Vcu71_packet_prefix___024root___trigger_anySet__act(vlSelfRef.__VnbaTriggered);
    if (__VnbaExecute) {
        {
            // Inlined CFunc: _eval_body__nba
            if ((((1ULL & vlSelfRef.__VnbaTriggered[0U])) != 0ULL)) {
                Vcu71_packet_prefix___024root___nba_sequent__TOP__0(vlSelf);
            }
        }
        Vcu71_packet_prefix___024root___trigger_clear__act(vlSelfRef.__VnbaTriggered);
    }
    return (__VnbaExecute);
}

bool Vcu71_packet_prefix___024root___eval_obs(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_obs\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

bool Vcu71_packet_prefix___024root___eval_react(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_react\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    return (0U);
}

void Vcu71_packet_prefix___024root___eval_postponed(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_postponed\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

void Vcu71_packet_prefix___024root___eval_triggers_vec__ico(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_triggers_vec__ico\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VicoTriggered[0U] = (QData)((IData)(
                                                    ((((IData)(vlSelfRef.commit_valid) 
                                                       != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__commit_valid__0)) 
                                                      << 0x00000010U) 
                                                     | ((((((((IData)(vlSelfRef.qmap_req_index) 
                                                              != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__qmap_req_index__0)) 
                                                             << 3U) 
                                                            | (((IData)(vlSelfRef.qmap_req_valid) 
                                                                != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__qmap_req_valid__0)) 
                                                               << 2U)) 
                                                           | ((((IData)(vlSelfRef.metadata_ready) 
                                                                != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__metadata_ready__0)) 
                                                               << 1U) 
                                                              | ((IData)(vlSelfRef.rd_rsp_data) 
                                                                 != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rd_rsp_data__0)))) 
                                                          << 0x0000000cU) 
                                                         | ((((((IData)(vlSelfRef.rd_rsp_valid) 
                                                                != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rd_rsp_valid__0)) 
                                                               << 3U) 
                                                              | (((IData)(vlSelfRef.rd_req_ready) 
                                                                  != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rd_req_ready__0)) 
                                                                 << 2U)) 
                                                             | (((0U 
                                                                  != 
                                                                  ((((vlSelfRef.cfg_reference_tag[0U] 
                                                                      ^ vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[0U]) 
                                                                     | (vlSelfRef.cfg_reference_tag[1U] 
                                                                        ^ vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[1U])) 
                                                                    | (vlSelfRef.cfg_reference_tag[2U] 
                                                                       ^ vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[2U])) 
                                                                   | (vlSelfRef.cfg_reference_tag[3U] 
                                                                      ^ vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_tag__0[3U]))) 
                                                                 << 1U) 
                                                                | (vlSelfRef.cfg_reference_id 
                                                                   != vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_id__0))) 
                                                            << 8U)) 
                                                        | (((((((IData)(vlSelfRef.cfg_reference_valid) 
                                                                != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__cfg_reference_valid__0)) 
                                                               << 3U) 
                                                              | ((vlSelfRef.cfg_last_frame_id 
                                                                  != vlSelfRef.__Vtrigprevexpr___TOP__cfg_last_frame_id__0) 
                                                                 << 2U)) 
                                                             | ((((IData)(vlSelfRef.cfg_last_valid) 
                                                                  != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__cfg_last_valid__0)) 
                                                                 << 1U) 
                                                                | ((IData)(vlSelfRef.cfg_packet_bytes) 
                                                                   != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__cfg_packet_bytes__0)))) 
                                                            << 4U) 
                                                           | (((((IData)(vlSelfRef.cfg_valid) 
                                                                 != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__cfg_valid__0)) 
                                                                << 3U) 
                                                               | (((IData)(vlSelfRef.abort_i) 
                                                                   != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__abort_i__0)) 
                                                                  << 2U)) 
                                                              | ((((IData)(vlSelfRef.rst) 
                                                                   != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__rst__0)) 
                                                                  << 1U) 
                                                                 | ((IData)(vlSelfRef.clk) 
                                                                    != (IData)(vlSelfRef.__Vtrigprevexpr___TOP__clk__0)))))))));
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
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000000200ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000000400ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000000800ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000001000ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000002000ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000004000ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000008000ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
        vlSelfRef.__VicoTriggered[0U] = (0x0000000000010000ULL 
                                         | vlSelfRef.__VicoTriggered[0U]);
    }
}

bool Vcu71_packet_prefix___024root___trigger_anySet__ico(const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___trigger_anySet__ico\n"); );
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

void Vcu71_packet_prefix___024root___ico_comb__TOP__1(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___ico_comb__TOP__1\n"); );
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

bool Vcu71_packet_prefix___024root___trigger_anySet__act(const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___trigger_anySet__act\n"); );
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

void Vcu71_packet_prefix___024root___nba_sequent__TOP__0(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___nba_sequent__TOP__0\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlWide<4>/*127:0*/ __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19;
    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19);
    VlWide<4>/*127:0*/ __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22;
    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22);
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_84;
    __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_84 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_86;
    __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_86 = 0;
    VlWide<4>/*127:0*/ __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88;
    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88);
    VlWide<4>/*127:0*/ __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91;
    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91);
    CData/*7:0*/ __Vtask_cu71_packet_prefix__DOT__reject_packet__code_17;
    __Vtask_cu71_packet_prefix__DOT__reject_packet__code_17 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_97;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_97 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_98;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_98 = 0;
    CData/*7:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_99;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_99 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_102;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_102 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_103;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_103 = 0;
    CData/*7:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_104;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_104 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_107;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_107 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_108;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_108 = 0;
    CData/*7:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_109;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_109 = 0;
    IData/*31:0*/ __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110;
    __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 = 0;
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
    CData/*7:0*/ __Vdly__cu71_packet_prefix__DOT__state_0;
    __Vdly__cu71_packet_prefix__DOT__state_0 = 0;
    CData/*0:0*/ __Vdly__cu71_packet_prefix__DOT__outer_validated_4;
    __Vdly__cu71_packet_prefix__DOT__outer_validated_4 = 0;
    CData/*0:0*/ __Vdly__cu71_packet_prefix__DOT__inner_validated_5;
    __Vdly__cu71_packet_prefix__DOT__inner_validated_5 = 0;
    SData/*15:0*/ __Vdly__cu71_packet_prefix__DOT__inner_bytes_6;
    __Vdly__cu71_packet_prefix__DOT__inner_bytes_6 = 0;
    CData/*0:0*/ __Vdly__metadata_key_9;
    __Vdly__metadata_key_9 = 0;
    IData/*31:0*/ __Vdly__metadata_frame_id_10;
    __Vdly__metadata_frame_id_10 = 0;
    IData/*31:0*/ __Vdly__metadata_reference_id_11;
    __Vdly__metadata_reference_id_11 = 0;
    VlWide<4>/*127:0*/ __Vdly__metadata_reference_tag_12;
    VL_ZERO_W(128, __Vdly__metadata_reference_tag_12);
    SData/*15:0*/ __Vdly__metadata_hud_addr_15;
    __Vdly__metadata_hud_addr_15 = 0;
    SData/*15:0*/ __Vdly__metadata_hud_bytes_16;
    __Vdly__metadata_hud_bytes_16 = 0;
    IData/*31:0*/ __Vdly__memory_reads_23;
    __Vdly__memory_reads_23 = 0;
    SData/*15:0*/ __Vdly__cu71_packet_prefix__DOT__scan_addr_25;
    __Vdly__cu71_packet_prefix__DOT__scan_addr_25 = 0;
    IData/*31:0*/ __Vdly__cu71_packet_prefix__DOT__crc_outer_31;
    __Vdly__cu71_packet_prefix__DOT__crc_outer_31 = 0;
    IData/*31:0*/ __Vdly__cu71_packet_prefix__DOT__crc_inner_32;
    __Vdly__cu71_packet_prefix__DOT__crc_inner_32 = 0;
    IData/*31:0*/ __Vdly__cu71_packet_prefix__DOT__crc_hud_33;
    __Vdly__cu71_packet_prefix__DOT__crc_hud_33 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_addr_40;
    __Vdly_Set__metadata_plane_addr_40 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_addr_41;
    __Vdly_Set__metadata_plane_addr_41 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_bytes_42;
    __Vdly_Val__metadata_plane_bytes_42 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_bytes_43;
    __Vdly_Set__metadata_plane_bytes_43 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_addr_44;
    __Vdly_Val__metadata_plane_addr_44 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_bytes_45;
    __Vdly_Val__metadata_plane_bytes_45 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_bytes_46;
    __Vdly_Set__metadata_plane_bytes_46 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_addr_47;
    __Vdly_Val__metadata_plane_addr_47 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_addr_48;
    __Vdly_Set__metadata_plane_addr_48 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_bytes_49;
    __Vdly_Val__metadata_plane_bytes_49 = 0;
    SData/*15:0*/ __Vdly_Val__metadata_plane_addr_50;
    __Vdly_Val__metadata_plane_addr_50 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_addr_51;
    __Vdly_Set__metadata_plane_addr_51 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_dispatch_52;
    __Vdly_Set__metadata_plane_dispatch_52 = 0;
    CData/*2:0*/ __Vdly_Val__metadata_plane_dispatch_53;
    __Vdly_Val__metadata_plane_dispatch_53 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_dispatch_54;
    __Vdly_Set__metadata_plane_dispatch_54 = 0;
    CData/*2:0*/ __Vdly_Val__metadata_plane_dispatch_55;
    __Vdly_Val__metadata_plane_dispatch_55 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_dispatch_56;
    __Vdly_Set__metadata_plane_dispatch_56 = 0;
    CData/*2:0*/ __Vdly_Val__metadata_plane_dispatch_57;
    __Vdly_Val__metadata_plane_dispatch_57 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_dispatch_58;
    __Vdly_Set__metadata_plane_dispatch_58 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_59;
    __Vdly_Set__metadata_plane_blocks_59 = 0;
    IData/*16:0*/ __Vdly_Val__metadata_plane_blocks_60;
    __Vdly_Val__metadata_plane_blocks_60 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_61;
    __Vdly_Set__metadata_plane_blocks_61 = 0;
    IData/*16:0*/ __Vdly_Val__metadata_plane_blocks_62;
    __Vdly_Val__metadata_plane_blocks_62 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_63;
    __Vdly_Set__metadata_plane_blocks_63 = 0;
    IData/*16:0*/ __Vdly_Val__metadata_plane_blocks_64;
    __Vdly_Val__metadata_plane_blocks_64 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_65;
    __Vdly_Set__metadata_plane_blocks_65 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_w_66;
    __Vdly_Set__metadata_plane_blocks_w_66 = 0;
    SData/*8:0*/ __Vdly_Val__metadata_plane_blocks_w_67;
    __Vdly_Val__metadata_plane_blocks_w_67 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_w_68;
    __Vdly_Set__metadata_plane_blocks_w_68 = 0;
    SData/*8:0*/ __Vdly_Val__metadata_plane_blocks_w_69;
    __Vdly_Val__metadata_plane_blocks_w_69 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_w_70;
    __Vdly_Set__metadata_plane_blocks_w_70 = 0;
    SData/*8:0*/ __Vdly_Val__metadata_plane_blocks_w_71;
    __Vdly_Val__metadata_plane_blocks_w_71 = 0;
    CData/*0:0*/ __Vdly_Set__metadata_plane_blocks_w_72;
    __Vdly_Set__metadata_plane_blocks_w_72 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_packet_prefix__DOT__outer_header_73;
    __Vdly_Val__cu71_packet_prefix__DOT__outer_header_73 = 0;
    CData/*6:0*/ __Vdly_Dim0__cu71_packet_prefix__DOT__outer_header_74;
    __Vdly_Dim0__cu71_packet_prefix__DOT__outer_header_74 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_packet_prefix__DOT__outer_header_75;
    __Vdly_Set__cu71_packet_prefix__DOT__outer_header_75 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_packet_prefix__DOT__inner_header_76;
    __Vdly_Val__cu71_packet_prefix__DOT__inner_header_76 = 0;
    CData/*5:0*/ __Vdly_Dim0__cu71_packet_prefix__DOT__inner_header_77;
    __Vdly_Dim0__cu71_packet_prefix__DOT__inner_header_77 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_packet_prefix__DOT__inner_header_78;
    __Vdly_Set__cu71_packet_prefix__DOT__inner_header_78 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_packet_prefix__DOT__hud_header_79;
    __Vdly_Val__cu71_packet_prefix__DOT__hud_header_79 = 0;
    CData/*6:0*/ __Vdly_Dim0__cu71_packet_prefix__DOT__hud_header_80;
    __Vdly_Dim0__cu71_packet_prefix__DOT__hud_header_80 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_packet_prefix__DOT__hud_header_81;
    __Vdly_Set__cu71_packet_prefix__DOT__hud_header_81 = 0;
    CData/*7:0*/ __Vdly_Val__cu71_packet_prefix__DOT__qmap_mem_82;
    __Vdly_Val__cu71_packet_prefix__DOT__qmap_mem_82 = 0;
    SData/*8:0*/ __Vdly_Dim0__cu71_packet_prefix__DOT__qmap_mem_83;
    __Vdly_Dim0__cu71_packet_prefix__DOT__qmap_mem_83 = 0;
    CData/*0:0*/ __Vdly_Set__cu71_packet_prefix__DOT__qmap_mem_84;
    __Vdly_Set__cu71_packet_prefix__DOT__qmap_mem_84 = 0;
    // Body
    __Vdly__memory_reads_23 = vlSelfRef.memory_reads;
    __Vdly_Set__cu71_packet_prefix__DOT__outer_header_75 = 0U;
    __Vdly_Set__cu71_packet_prefix__DOT__inner_header_78 = 0U;
    __Vdly_Set__cu71_packet_prefix__DOT__qmap_mem_84 = 0U;
    __Vdly_Set__cu71_packet_prefix__DOT__hud_header_81 = 0U;
    __Vdly__cu71_packet_prefix__DOT__crc_inner_32 = vlSelfRef.cu71_packet_prefix__DOT__crc_inner;
    __Vdly__cu71_packet_prefix__DOT__crc_outer_31 = vlSelfRef.cu71_packet_prefix__DOT__crc_outer;
    __Vdly__cu71_packet_prefix__DOT__crc_hud_33 = vlSelfRef.cu71_packet_prefix__DOT__crc_hud;
    __Vdly__cu71_packet_prefix__DOT__scan_addr_25 = vlSelfRef.cu71_packet_prefix__DOT__scan_addr;
    __Vdly__cu71_packet_prefix__DOT__outer_validated_4 
        = vlSelfRef.cu71_packet_prefix__DOT__outer_validated;
    __Vdly__cu71_packet_prefix__DOT__inner_bytes_6 
        = vlSelfRef.cu71_packet_prefix__DOT__inner_bytes;
    __Vdly__metadata_key_9 = vlSelfRef.metadata_key;
    __Vdly__metadata_frame_id_10 = vlSelfRef.metadata_frame_id;
    __Vdly__metadata_reference_id_11 = vlSelfRef.metadata_reference_id;
    __Vdly__metadata_reference_tag_12[0U] = vlSelfRef.metadata_reference_tag[0U];
    __Vdly__metadata_reference_tag_12[1U] = vlSelfRef.metadata_reference_tag[1U];
    __Vdly__metadata_reference_tag_12[2U] = vlSelfRef.metadata_reference_tag[2U];
    __Vdly__metadata_reference_tag_12[3U] = vlSelfRef.metadata_reference_tag[3U];
    __Vdly__metadata_hud_addr_15 = vlSelfRef.metadata_hud_addr;
    __Vdly__metadata_hud_bytes_16 = vlSelfRef.metadata_hud_bytes;
    __Vdly_Set__metadata_plane_addr_51 = 0U;
    __Vdly_Set__metadata_plane_bytes_46 = 0U;
    __Vdly__cu71_packet_prefix__DOT__inner_validated_5 
        = vlSelfRef.cu71_packet_prefix__DOT__inner_validated;
    __Vdly_Set__metadata_plane_addr_40 = 0U;
    __Vdly_Set__metadata_plane_addr_41 = 0U;
    __Vdly_Set__metadata_plane_addr_48 = 0U;
    __Vdly_Set__metadata_plane_bytes_43 = 0U;
    __Vdly__cu71_packet_prefix__DOT__state_0 = vlSelfRef.cu71_packet_prefix__DOT__state;
    __Vdly_Set__metadata_plane_dispatch_52 = 0U;
    __Vdly_Set__metadata_plane_dispatch_54 = 0U;
    __Vdly_Set__metadata_plane_dispatch_56 = 0U;
    __Vdly_Set__metadata_plane_dispatch_58 = 0U;
    __Vdly_Set__metadata_plane_blocks_59 = 0U;
    __Vdly_Set__metadata_plane_blocks_61 = 0U;
    __Vdly_Set__metadata_plane_blocks_63 = 0U;
    __Vdly_Set__metadata_plane_blocks_65 = 0U;
    __Vdly_Set__metadata_plane_blocks_w_66 = 0U;
    __Vdly_Set__metadata_plane_blocks_w_68 = 0U;
    __Vdly_Set__metadata_plane_blocks_w_70 = 0U;
    __Vdly_Set__metadata_plane_blocks_w_72 = 0U;
    if (vlSelfRef.rst) {
        __Vdly__memory_reads_23 = 0U;
        __Vdly__cu71_packet_prefix__DOT__crc_inner_32 = 0xffffffffU;
        __Vdly__cu71_packet_prefix__DOT__crc_outer_31 = 0xffffffffU;
        __Vdly__cu71_packet_prefix__DOT__crc_hud_33 = 0xffffffffU;
        __Vdly__cu71_packet_prefix__DOT__scan_addr_25 = 0U;
        __Vdly_Set__metadata_plane_dispatch_52 = 1U;
        __Vdly_Set__metadata_plane_blocks_59 = 1U;
        __Vdly_Set__metadata_plane_blocks_w_66 = 1U;
        vlSelfRef.qmap_rsp_valid = 0U;
        vlSelfRef.qmap_rsp_index = 0U;
        vlSelfRef.qmap_rsp_code = 0U;
        vlSelfRef.aborted = 0U;
        __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
        vlSelfRef.done = 0U;
        vlSelfRef.error = 0U;
        vlSelfRef.error_code = 0U;
        __Vdly__cu71_packet_prefix__DOT__outer_validated_4 = 0U;
        __Vdly__cu71_packet_prefix__DOT__inner_validated_5 = 0U;
        __Vdly__cu71_packet_prefix__DOT__inner_bytes_6 = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__vector_start = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__vector_end = 0U;
        __Vdly__metadata_key_9 = 0U;
        __Vdly__metadata_frame_id_10 = 0U;
        __Vdly__metadata_reference_id_11 = 0U;
        __Vdly__metadata_reference_tag_12[0U] = 0U;
        __Vdly__metadata_reference_tag_12[1U] = 0U;
        __Vdly__metadata_reference_tag_12[2U] = 0U;
        __Vdly__metadata_reference_tag_12[3U] = 0U;
        vlSelfRef.metadata_output_tag[0U] = 0U;
        vlSelfRef.metadata_output_tag[1U] = 0U;
        vlSelfRef.metadata_output_tag[2U] = 0U;
        vlSelfRef.metadata_output_tag[3U] = 0U;
        vlSelfRef.metadata_block_size = 0U;
        __Vdly__metadata_hud_addr_15 = 0U;
        __Vdly__metadata_hud_bytes_16 = 0U;
        vlSelfRef.metadata_hud_reference_tag[0U] = 0U;
        vlSelfRef.metadata_hud_reference_tag[1U] = 0U;
        vlSelfRef.metadata_hud_reference_tag[2U] = 0U;
        vlSelfRef.metadata_hud_reference_tag[3U] = 0U;
        vlSelfRef.metadata_hud_output_tag[0U] = 0U;
        vlSelfRef.metadata_hud_output_tag[1U] = 0U;
        vlSelfRef.metadata_hud_output_tag[2U] = 0U;
        vlSelfRef.metadata_hud_output_tag[3U] = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__0__KET__ = 0U;
        __Vdly_Set__metadata_plane_addr_40 = 1U;
        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__1__KET__ = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__2__KET__ = 0U;
        __Vdly_Set__metadata_plane_addr_41 = 1U;
        vlSelfRef.cu71_packet_prefix__DOT__last_valid = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__last_frame_id = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_valid = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_id = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_tag[0U] = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_tag[1U] = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_tag[2U] = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__reference_tag[3U] = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__received_inner = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__received_outer = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__received_hud = 0U;
        vlSelfRef.cu71_packet_prefix__DOT__packet_bytes = 0U;
    } else {
        vlSelfRef.qmap_rsp_valid = 0U;
        if (((IData)(vlSelfRef.qmap_req_valid) & (IData)(vlSelfRef.qmap_req_ready))) {
            vlSelfRef.qmap_rsp_valid = 1U;
            vlSelfRef.qmap_rsp_index = vlSelfRef.qmap_req_index;
            vlSelfRef.qmap_rsp_code = (3U & ((2U & (IData)(vlSelfRef.qmap_req_index))
                                              ? ((1U 
                                                  & (IData)(vlSelfRef.qmap_req_index))
                                                  ? 
                                                 ((0x0151U 
                                                   >= 
                                                   (0x000001ffU 
                                                    & ((IData)(vlSelfRef.qmap_req_index) 
                                                       >> 2U)))
                                                   ? vlSelfRef.cu71_packet_prefix__DOT__qmap_mem
                                                  [
                                                  (0x000001ffU 
                                                   & ((IData)(vlSelfRef.qmap_req_index) 
                                                      >> 2U))]
                                                   : 0U)
                                                  : 
                                                 (((0x0151U 
                                                    >= 
                                                    (0x000001ffU 
                                                     & ((IData)(vlSelfRef.qmap_req_index) 
                                                        >> 2U)))
                                                    ? vlSelfRef.cu71_packet_prefix__DOT__qmap_mem
                                                   [
                                                   (0x000001ffU 
                                                    & ((IData)(vlSelfRef.qmap_req_index) 
                                                       >> 2U))]
                                                    : 0U) 
                                                  >> 2U))
                                              : ((1U 
                                                  & (IData)(vlSelfRef.qmap_req_index))
                                                  ? 
                                                 (((0x0151U 
                                                    >= 
                                                    (0x000001ffU 
                                                     & ((IData)(vlSelfRef.qmap_req_index) 
                                                        >> 2U)))
                                                    ? vlSelfRef.cu71_packet_prefix__DOT__qmap_mem
                                                   [
                                                   (0x000001ffU 
                                                    & ((IData)(vlSelfRef.qmap_req_index) 
                                                       >> 2U))]
                                                    : 0U) 
                                                  >> 4U)
                                                  : 
                                                 (((0x0151U 
                                                    >= 
                                                    (0x000001ffU 
                                                     & ((IData)(vlSelfRef.qmap_req_index) 
                                                        >> 2U)))
                                                    ? vlSelfRef.cu71_packet_prefix__DOT__qmap_mem
                                                   [
                                                   (0x000001ffU 
                                                    & ((IData)(vlSelfRef.qmap_req_index) 
                                                       >> 2U))]
                                                    : 0U) 
                                                  >> 6U))));
        }
        vlSelfRef.done = 0U;
        if (((IData)(vlSelfRef.abort_i) & (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
            vlSelfRef.aborted = 1U;
        } else if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                             >> 7U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                          >> 6U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                              >> 5U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                  >> 4U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                      >> 3U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                          >> 2U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                              >> 1U)))) {
                                    if ((1U & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                        if (((IData)(vlSelfRef.cfg_valid) 
                                             & (IData)(vlSelfRef.cfg_ready))) {
                                            vlSelfRef.aborted = 0U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.abort_i) & 
                      (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                                            if (vlSelfRef.rd_req_ready) {
                                                __Vdly__memory_reads_23 
                                                    = 
                                                    ((IData)(1U) 
                                                     + vlSelfRef.memory_reads);
                                            }
                                        } else if (
                                                   ((IData)(vlSelfRef.cfg_valid) 
                                                    & (IData)(vlSelfRef.cfg_ready))) {
                                            __Vdly__memory_reads_23 = 0U;
                                        }
                                    }
                                    if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                            if (vlSelfRef.rd_rsp_valid) {
                                                if (
                                                    (1U 
                                                     & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__byte_bad)))) {
                                                    if (vlSelfRef.cu71_packet_prefix__DOT__outer_validated) {
                                                        if (
                                                            ((0x004cU 
                                                              <= (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)) 
                                                             & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                < 
                                                                (0x0000ffffU 
                                                                 & ((IData)(0x0048U) 
                                                                    + (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes)))))) {
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_104 
                                                                = vlSelfRef.rd_rsp_data;
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_103 
                                                                = vlSelfRef.cu71_packet_prefix__DOT__crc_inner;
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                (__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_103 
                                                                 ^ (IData)(__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_104));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_102 
                                                                = __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_105;
                                                            __Vdly__cu71_packet_prefix__DOT__crc_inner_32 
                                                                = __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_102;
                                                        }
                                                        if (
                                                            (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                              >= (IData)(vlSelfRef.metadata_hud_addr)) 
                                                             & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                < 
                                                                (0x0000ffffU 
                                                                 & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                    - (IData)(8U)))))) {
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_109 
                                                                = vlSelfRef.rd_rsp_data;
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_108 
                                                                = vlSelfRef.cu71_packet_prefix__DOT__crc_hud;
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                (__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_108 
                                                                 ^ (IData)(__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_109));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                = 
                                                                ((1U 
                                                                  & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110)
                                                                  ? 
                                                                 (0xedb88320U 
                                                                  ^ 
                                                                  (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                   >> 1U))
                                                                  : 
                                                                 (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110 
                                                                  >> 1U));
                                                            __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_107 
                                                                = __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_110;
                                                            __Vdly__cu71_packet_prefix__DOT__crc_hud_33 
                                                                = __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_107;
                                                        }
                                                    }
                                                    if (
                                                        ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                         < 
                                                         (0x0000ffffU 
                                                          & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                             - (IData)(4U))))) {
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_99 
                                                            = vlSelfRef.rd_rsp_data;
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_98 
                                                            = vlSelfRef.cu71_packet_prefix__DOT__crc_outer;
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            (__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_crc_98 
                                                             ^ (IData)(__Vfunc_cu71_packet_prefix__DOT__crc_byte__value_99));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                            = 
                                                            ((1U 
                                                              & __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100)
                                                              ? 
                                                             (0xedb88320U 
                                                              ^ 
                                                              (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                               >> 1U))
                                                              : 
                                                             (__Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100 
                                                              >> 1U));
                                                        __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_97 
                                                            = __Vfunc_cu71_packet_prefix__DOT__crc_byte__c_100;
                                                        __Vdly__cu71_packet_prefix__DOT__crc_outer_31 
                                                            = __Vfunc_cu71_packet_prefix__DOT__crc_byte__Vfuncout_97;
                                                    }
                                                    __Vdly__cu71_packet_prefix__DOT__scan_addr_25 
                                                        = 
                                                        (0x0000ffffU 
                                                         & ((IData)(1U) 
                                                            + (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)));
                                                    if (vlSelfRef.cu71_packet_prefix__DOT__inner_validated) {
                                                        if (
                                                            ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                             == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__0__KET__))) {
                                                            __Vdly_Val__metadata_plane_dispatch_53 
                                                                = 
                                                                (7U 
                                                                 & (IData)(vlSelfRef.rd_rsp_data));
                                                            __Vdly_Set__metadata_plane_dispatch_54 = 1U;
                                                            if (
                                                                (6U 
                                                                 == (IData)(vlSelfRef.rd_rsp_data))) {
                                                                __Vdly_Val__metadata_plane_blocks_60 = 0x00001418U;
                                                                __Vdly_Val__metadata_plane_blocks_w_67 = 1U;
                                                            } else {
                                                                __Vdly_Val__metadata_plane_blocks_60 = 0x00001518U;
                                                                __Vdly_Val__metadata_plane_blocks_w_67 = 0x005aU;
                                                            }
                                                            __Vdly_Set__metadata_plane_blocks_61 = 1U;
                                                            __Vdly_Set__metadata_plane_blocks_w_68 = 1U;
                                                        }
                                                        if (
                                                            ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                             == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__1__KET__))) {
                                                            __Vdly_Val__metadata_plane_dispatch_55 
                                                                = 
                                                                (7U 
                                                                 & (IData)(vlSelfRef.rd_rsp_data));
                                                            __Vdly_Set__metadata_plane_dispatch_56 = 1U;
                                                            if (
                                                                (6U 
                                                                 == (IData)(vlSelfRef.rd_rsp_data))) {
                                                                __Vdly_Val__metadata_plane_blocks_62 = 0x00000533U;
                                                                __Vdly_Val__metadata_plane_blocks_w_69 = 1U;
                                                            } else {
                                                                __Vdly_Val__metadata_plane_blocks_62 = 0x00000546U;
                                                                __Vdly_Val__metadata_plane_blocks_w_69 = 0x002dU;
                                                            }
                                                            __Vdly_Set__metadata_plane_blocks_63 = 1U;
                                                            __Vdly_Set__metadata_plane_blocks_w_70 = 1U;
                                                        }
                                                        if (
                                                            ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                             == (IData)(vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__2__KET__))) {
                                                            __Vdly_Val__metadata_plane_dispatch_57 
                                                                = 
                                                                (7U 
                                                                 & (IData)(vlSelfRef.rd_rsp_data));
                                                            __Vdly_Set__metadata_plane_dispatch_58 = 1U;
                                                            if (
                                                                (6U 
                                                                 == (IData)(vlSelfRef.rd_rsp_data))) {
                                                                __Vdly_Val__metadata_plane_blocks_64 = 0x00000533U;
                                                                __Vdly_Val__metadata_plane_blocks_w_71 = 1U;
                                                            } else {
                                                                __Vdly_Val__metadata_plane_blocks_64 = 0x00000546U;
                                                                __Vdly_Val__metadata_plane_blocks_w_71 = 0x002dU;
                                                            }
                                                            __Vdly_Set__metadata_plane_blocks_65 = 1U;
                                                            __Vdly_Set__metadata_plane_blocks_w_72 = 1U;
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    } else if ((1U 
                                                & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                        if (((IData)(vlSelfRef.cfg_valid) 
                                             & (IData)(vlSelfRef.cfg_ready))) {
                                            __Vdly__cu71_packet_prefix__DOT__crc_inner_32 = 0xffffffffU;
                                            __Vdly__cu71_packet_prefix__DOT__crc_outer_31 = 0xffffffffU;
                                            __Vdly__cu71_packet_prefix__DOT__crc_hud_33 = 0xffffffffU;
                                            __Vdly__cu71_packet_prefix__DOT__scan_addr_25 = 0U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.abort_i) & (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
            if ((((2U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)) 
                  | (9U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) 
                 & (~ (IData)(vlSelfRef.rd_rsp_valid)))) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 9U;
            } else {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                vlSelfRef.done = 1U;
            }
        } else if ((0x00000080U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
            vlSelfRef.error = 1U;
            vlSelfRef.error_code = 0xffU;
            vlSelfRef.done = 1U;
        } else if ((0x00000040U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
            vlSelfRef.error = 1U;
            vlSelfRef.error_code = 0xffU;
            vlSelfRef.done = 1U;
        } else if ((0x00000020U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
            vlSelfRef.error = 1U;
            vlSelfRef.error_code = 0xffU;
            vlSelfRef.done = 1U;
        } else if ((0x00000010U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
            vlSelfRef.error = 1U;
            vlSelfRef.error_code = 0xffU;
            vlSelfRef.done = 1U;
        } else if ((8U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            if ((4U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                vlSelfRef.error = 1U;
                vlSelfRef.error_code = 0xffU;
                vlSelfRef.done = 1U;
            } else if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                vlSelfRef.error = 1U;
                vlSelfRef.error_code = 0xffU;
                vlSelfRef.done = 1U;
            } else if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                if (vlSelfRef.rd_rsp_valid) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.done = 1U;
                }
            } else if (vlSelfRef.commit_valid) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                vlSelfRef.done = 1U;
            }
        } else if ((4U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                    if (vlSelfRef.metadata_ready) {
                        __Vdly__cu71_packet_prefix__DOT__state_0 = 8U;
                    }
                } else if (((~ vlSelfRef.cu71_packet_prefix__DOT__crc_outer) 
                            != vlSelfRef.cu71_packet_prefix__DOT__received_outer)) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 0x0dU;
                    vlSelfRef.done = 1U;
                } else if (((~ vlSelfRef.cu71_packet_prefix__DOT__crc_inner) 
                            != vlSelfRef.cu71_packet_prefix__DOT__received_inner)) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 0x0eU;
                    vlSelfRef.done = 1U;
                } else if (((~ vlSelfRef.cu71_packet_prefix__DOT__crc_hud) 
                            != vlSelfRef.cu71_packet_prefix__DOT__received_hud)) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 0x0fU;
                    vlSelfRef.done = 1U;
                } else {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 7U;
                }
            } else if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_65__hud32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[9U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[8U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[7U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[6U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_66__hud32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[13U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[12U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[11U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[10U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_67__hud32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[17U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[16U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[15U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[14U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_68__hud16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[19U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[18U]);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_69__hud16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[21U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__hud_header[20U]);
                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[3U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[38U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[39U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[40U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[2U] 
                    = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[41U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[42U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[43U])) 
                          << 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[3U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[41U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[42U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[43U])) 
                          >> 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[1U] 
                    = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[1U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[44U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[46U])) 
                          << 0x00000018U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[2U] 
                    = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[44U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[46U])) 
                          >> 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[1U] 
                    = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[1U]) 
                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[47U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[48U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__hud_header[49U])));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[0U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[0U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[51U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__hud_header[52U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[0U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[0U]) 
                       | vlSelfRef.cu71_packet_prefix__DOT__hud_header[53U]);
                if (vlSelfRef.metadata_key) {
                    VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[3U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[24U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[2U] 
                        = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[3U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[1U] 
                        = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[1U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[2U] 
                        = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              >> 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[1U] 
                        = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[1U]) 
                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__hud_header[33U])));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[0U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[0U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[36U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[0U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[0U]) 
                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[37U]);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCond_73 
                        = (0U != (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[0U] 
                                    | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[1U]) 
                                   | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[2U]) 
                                  | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_71__hud128[3U]));
                } else {
                    VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[3U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[24U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[2U] 
                        = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[3U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[1U] 
                        = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[1U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[2U] 
                        = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              >> 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[1U] 
                        = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[1U]) 
                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__hud_header[33U])));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[0U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[0U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[36U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[0U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[0U]) 
                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[37U]);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCond_73 
                        = (0U == (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[0U] 
                                    | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[1U]) 
                                   | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[2U]) 
                                  | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_72__hud128[3U]));
                }
                if (((((((((((((0x48553235U != (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[0U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__hud_header[1U]) 
                                                 << 0x00000010U) 
                                                | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[2U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[3U]))) 
                               & (0x48583332U != ((
                                                   (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[0U]) 
                                                     << 8U) 
                                                    | vlSelfRef.cu71_packet_prefix__DOT__hud_header[1U]) 
                                                   << 0x00000010U) 
                                                  | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[2U]) 
                                                      << 8U) 
                                                     | vlSelfRef.cu71_packet_prefix__DOT__hud_header[3U])))) 
                              & (0x48583333U != (((
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[0U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[1U]) 
                                                  << 0x00000010U) 
                                                 | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[2U]) 
                                                     << 8U) 
                                                    | vlSelfRef.cu71_packet_prefix__DOT__hud_header[3U])))) 
                             | (1U != vlSelfRef.cu71_packet_prefix__DOT__hud_header[4U])) 
                            | (4U != vlSelfRef.cu71_packet_prefix__DOT__hud_header[5U])) 
                           | (0x00000019U != vlSelfRef.cu71_packet_prefix__DOT____VlemCall_65__hud32)) 
                          | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_66__hud32 
                             != vlSelfRef.metadata_frame_id)) 
                         | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_67__hud32 
                            != vlSelfRef.metadata_reference_id)) 
                        | (0x02d0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_68__hud16))) 
                       | (0x01e0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_69__hud16))) 
                      | (0U == (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[0U] 
                                  | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[1U]) 
                                 | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[2U]) 
                                | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_70__hud128[3U]))) 
                     | (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCond_73))) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 0x0bU;
                    vlSelfRef.done = 1U;
                } else if (((1U > vlSelfRef.__Vdfg_Regularize_506) 
                            | ((vlSelfRef.__Vdfg_Regularize_506 
                                > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes)) 
                               | ((1U > vlSelfRef.cu71_packet_prefix__DOT__hud_header[73U]) 
                                  | ((vlSelfRef.cu71_packet_prefix__DOT__hud_header[73U] 
                                      > (IData)(vlSelfRef.__Vdfg_Regularize_502)) 
                                     | ((1U > vlSelfRef.__Vdfg_Regularize_505) 
                                        | ((vlSelfRef.__Vdfg_Regularize_505 
                                            > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes)) 
                                           | ((1U > vlSelfRef.cu71_packet_prefix__DOT__hud_header[72U]) 
                                              | ((vlSelfRef.cu71_packet_prefix__DOT__hud_header[72U] 
                                                  > (IData)(vlSelfRef.__Vdfg_Regularize_502)) 
                                                 | ((1U 
                                                     > vlSelfRef.__Vdfg_Regularize_504) 
                                                    | ((vlSelfRef.__Vdfg_Regularize_504 
                                                        > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes)) 
                                                       | ((1U 
                                                           > vlSelfRef.cu71_packet_prefix__DOT__hud_header[71U]) 
                                                          | ((vlSelfRef.cu71_packet_prefix__DOT__hud_header[71U] 
                                                              > (IData)(vlSelfRef.__Vdfg_Regularize_502)) 
                                                             | ((1U 
                                                                 > vlSelfRef.__Vdfg_Regularize_503) 
                                                                | ((vlSelfRef.__Vdfg_Regularize_503 
                                                                    > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes)) 
                                                                   | ((1U 
                                                                       > vlSelfRef.cu71_packet_prefix__DOT__hud_header[70U]) 
                                                                      | ((vlSelfRef.cu71_packet_prefix__DOT__hud_header[70U] 
                                                                          > (IData)(vlSelfRef.__Vdfg_Regularize_502)) 
                                                                         | (((IData)(vlSelfRef.metadata_hud_bytes) 
                                                                             != 
                                                                             ((IData)(0x0000006eU) 
                                                                              + 
                                                                              (vlSelfRef.__Vdfg_Regularize_503 
                                                                               + 
                                                                               (vlSelfRef.__Vdfg_Regularize_504 
                                                                                + 
                                                                                (vlSelfRef.__Vdfg_Regularize_505 
                                                                                + vlSelfRef.__Vdfg_Regularize_506))))) 
                                                                            | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[103U]) 
                                                                               | ((0xf0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[102U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[101U]) 
                                                                                | ((0x86U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[100U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[99U]) 
                                                                                | ((0xa8U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[98U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[97U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[96U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[95U]) 
                                                                                | ((0x40U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[94U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[93U]) 
                                                                                | ((0x68U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[92U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[91U]) 
                                                                                | ((0xa8U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[90U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[89U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[88U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[87U]) 
                                                                                | ((0xa0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[86U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[85U]) 
                                                                                | ((0x52U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[84U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[83U]) 
                                                                                | ((0x16U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[82U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[81U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[80U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[79U]) 
                                                                                | ((0xa0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[78U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[77U]) 
                                                                                | ((0x36U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[76U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[75U]) 
                                                                                | ((0x16U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[74U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[105U]) 
                                                                                | (0x18U 
                                                                                != vlSelfRef.cu71_packet_prefix__DOT__hud_header[104U])))))))))))))))))))))))))))))))))))))))))))))))))) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 0x0cU;
                    vlSelfRef.done = 1U;
                } else {
                    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19);
                    VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22);
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[3U] 
                        = ((0x000000ffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[24U])) 
                              << 8U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[3U] 
                        = ((0x000000ffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[38U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[39U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[40U])) 
                              << 8U));
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 1U;
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[2U] 
                        = ((0x0000ffffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[3U] 
                        = ((0xffffff00U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[2U] 
                        = ((0x0000ffffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[41U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[42U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[43U])) 
                              << 0x00000010U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[3U] 
                        = ((0xffffff00U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[41U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[42U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[43U])) 
                              >> 0x00000010U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[1U] 
                        = ((0x00ffffffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[1U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[2U] 
                        = ((0xffff0000U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[30U])) 
                              >> 8U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[1U] 
                        = ((0x00ffffffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[1U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[44U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[46U])) 
                              << 0x00000018U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[2U] 
                        = ((0xffff0000U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[44U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[46U])) 
                              >> 8U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[1U] 
                        = ((0xff000000U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[1U]) 
                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__hud_header[33U])));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[1U] 
                        = ((0xff000000U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[1U]) 
                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[47U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[48U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__hud_header[49U])));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[0U] 
                        = ((0x000000ffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[0U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[36U])) 
                              << 8U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[0U] 
                        = ((0x000000ffU & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[0U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__hud_header[51U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__hud_header[52U])) 
                              << 8U));
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[0U] 
                        = ((0xffffff00U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[0U]) 
                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[37U]);
                    __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[0U] 
                        = ((0xffffff00U & __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[0U]) 
                           | vlSelfRef.cu71_packet_prefix__DOT__hud_header[53U]);
                    vlSelfRef.metadata_hud_reference_tag[0U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[0U];
                    vlSelfRef.metadata_hud_reference_tag[1U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[1U];
                    vlSelfRef.metadata_hud_reference_tag[2U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[2U];
                    vlSelfRef.metadata_hud_reference_tag[3U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_19[3U];
                    vlSelfRef.metadata_hud_output_tag[0U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[0U];
                    vlSelfRef.metadata_hud_output_tag[1U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[1U];
                    vlSelfRef.metadata_hud_output_tag[2U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[2U];
                    vlSelfRef.metadata_hud_output_tag[3U] 
                        = __Vfunc_cu71_packet_prefix__DOT__hud128__Vfuncout_22[3U];
                }
            } else {
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_32__inner32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[9U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[8U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[7U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__inner_header[6U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_33__inner32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[13U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[12U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[11U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__inner_header[10U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_34__inner32 
                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[17U]) 
                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[16U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[15U]) 
                                            << 8U) 
                                           | vlSelfRef.cu71_packet_prefix__DOT__inner_header[14U]));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_35__inner16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[19U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[18U]);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_36__inner16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[21U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[20U]);
                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[3U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[24U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[25U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[26U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[2U] 
                    = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[27U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[28U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[29U])) 
                          << 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[3U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[27U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[28U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[29U])) 
                          >> 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[1U] 
                    = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[1U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[30U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[31U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[32U])) 
                          << 0x00000018U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[2U] 
                    = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[30U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[31U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[32U])) 
                          >> 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[1U] 
                    = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[1U]) 
                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[33U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[34U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__inner_header[35U])));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[0U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[0U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[36U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[37U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[38U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[0U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[0U]) 
                       | vlSelfRef.cu71_packet_prefix__DOT__inner_header[39U]);
                if ((((((((((((0x47553636U != (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[0U]) 
                                                  << 8U) 
                                                 | vlSelfRef.cu71_packet_prefix__DOT__inner_header[1U]) 
                                                << 0x00000010U) 
                                               | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[2U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__inner_header[3U]))) 
                              | (1U != vlSelfRef.cu71_packet_prefix__DOT__inner_header[4U])) 
                             | (vlSelfRef.cu71_packet_prefix__DOT__inner_header[5U] 
                                != (IData)(vlSelfRef.metadata_key))) 
                            | (0x00000019U != vlSelfRef.cu71_packet_prefix__DOT____VlemCall_32__inner32)) 
                           | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_33__inner32 
                              != vlSelfRef.metadata_frame_id)) 
                          | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_34__inner32 
                             != vlSelfRef.metadata_reference_id)) 
                         | (0x02d0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_35__inner16))) 
                        | (0x01e0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_36__inner16))) 
                       | ((0x10U != vlSelfRef.cu71_packet_prefix__DOT__inner_header[22U]) 
                          & (0x20U != vlSelfRef.cu71_packet_prefix__DOT__inner_header[22U]))) 
                      | (0x12U != vlSelfRef.cu71_packet_prefix__DOT__inner_header[23U])) 
                     | (0U != ((((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[0U] 
                                  ^ vlSelfRef.metadata_reference_tag[0U]) 
                                 | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[1U] 
                                    ^ vlSelfRef.metadata_reference_tag[1U])) 
                                | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[2U] 
                                   ^ vlSelfRef.metadata_reference_tag[2U])) 
                               | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_37__inner128[3U] 
                                  ^ vlSelfRef.metadata_reference_tag[3U]))))) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 6U;
                    vlSelfRef.done = 1U;
                } else {
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_38__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[43U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[42U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[41U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[40U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_39__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_40__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_41__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_42__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_43__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_44__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[59U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[58U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[57U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[56U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_45__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[59U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[58U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[57U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[56U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_46__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[43U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[42U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[41U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[40U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_47__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_48__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_49__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_50__inner32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[59U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[58U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[57U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__inner_header[56U]));
                    if ((((((((((0x00000152U != vlSelfRef.cu71_packet_prefix__DOT____VlemCall_38__inner32) 
                                | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_39__inner32 
                                   != ((IData)(vlSelfRef.metadata_key)
                                        ? 0U : 3U))) 
                               | (0x0000002fU > vlSelfRef.cu71_packet_prefix__DOT____VlemCall_40__inner32)) 
                              | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_41__inner32 
                                 > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))) 
                             | (0x0000002fU > vlSelfRef.cu71_packet_prefix__DOT____VlemCall_42__inner32)) 
                            | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_43__inner32 
                               > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))) 
                           | (0x0000002fU > vlSelfRef.cu71_packet_prefix__DOT____VlemCall_44__inner32)) 
                          | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_45__inner32 
                             > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))) 
                         | (((IData)(0x00000040U) + 
                             ((((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_46__inner32 
                                 + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_47__inner32) 
                                + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_48__inner32) 
                               + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_49__inner32) 
                              + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_50__inner32)) 
                            != (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes)))) {
                        __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                        vlSelfRef.error = 1U;
                        vlSelfRef.error_code = 7U;
                        vlSelfRef.done = 1U;
                    } else {
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_51__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_52__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_53__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_55__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_59__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_54__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_56__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                        vlSelfRef.metadata_block_size 
                            = vlSelfRef.cu71_packet_prefix__DOT__inner_header[22U];
                        vlSelfRef.cu71_packet_prefix__DOT__vector_start = 0x01daU;
                        vlSelfRef.cu71_packet_prefix__DOT__vector_end 
                            = (0x0000ffffU & ((IData)(0x01daU) 
                                              + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_51__inner32));
                        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__0__KET__ 
                            = (0x0000ffffU & ((IData)(0x01daU) 
                                              + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_52__inner32));
                        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__1__KET__ 
                            = (0x0000ffffU & ((IData)(0x01daU) 
                                              + (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_53__inner32 
                                                 + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_54__inner32)));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_57__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                        __Vdly_Val__metadata_plane_bytes_42 
                            = (0x0000ffffU & (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                                              - (IData)(1U)));
                        __Vdly_Set__metadata_plane_bytes_43 = 1U;
                        __Vdly_Val__metadata_plane_addr_44 
                            = (0x0000ffffU & ((IData)(0x01dbU) 
                                              + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_59__inner32));
                        __Vdly__cu71_packet_prefix__DOT__inner_validated_5 = 1U;
                        __Vdly__cu71_packet_prefix__DOT__state_0 = 1U;
                        vlSelfRef.cu71_packet_prefix__DOT__plane_start__BRA__2__KET__ 
                            = (0x0000ffffU & ((IData)(0x01daU) 
                                              + ((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_55__inner32 
                                                  + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_56__inner32) 
                                                 + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_57__inner32)));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_60__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        __Vdly_Val__metadata_plane_bytes_45 
                            = (0x0000ffffU & (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                                              - (IData)(1U)));
                        __Vdly_Set__metadata_plane_bytes_46 = 1U;
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_61__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[59U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[57U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[56U]));
                        __Vdly_Val__metadata_plane_addr_47 
                            = (0x0000ffffU & ((IData)(0x01dbU) 
                                              + (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_60__inner32 
                                                 + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_61__inner32)));
                        __Vdly_Set__metadata_plane_addr_48 = 1U;
                        __Vdly_Val__metadata_plane_bytes_49 
                            = (0x0000ffffU & (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_58__inner32 
                                              - (IData)(1U)));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_62__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[44U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_63__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[48U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_64__inner32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[55U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__inner_header[54U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__inner_header[52U]));
                        __Vdly_Val__metadata_plane_addr_50 
                            = (0x0000ffffU & ((IData)(0x01dbU) 
                                              + ((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_62__inner32 
                                                  + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_63__inner32) 
                                                 + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_64__inner32)));
                        __Vdly_Set__metadata_plane_addr_51 = 1U;
                    }
                }
            }
        } else if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_8__outer16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[7U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[6U]);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_9__outer16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[17U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[16U]);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_10__outer16 
                    = (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[19U]) 
                        << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[18U]);
                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128);
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[3U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[20U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[21U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[22U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[2U] 
                    = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[23U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[24U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[25U])) 
                          << 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[3U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[3U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[23U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[24U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[25U])) 
                          >> 0x00000010U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[1U] 
                    = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[1U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[26U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[27U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[28U])) 
                          << 0x00000018U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[2U] 
                    = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[2U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[26U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[27U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[28U])) 
                          >> 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[1U] 
                    = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[1U]) 
                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[29U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[30U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[31U])));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[0U] 
                    = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[0U]) 
                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[32U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[33U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[34U])) 
                          << 8U));
                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[0U] 
                    = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[0U]) 
                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[35U]);
                if ((((((((0x43553636U != (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[0U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[1U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[2U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[3U]))) 
                          | (1U != vlSelfRef.cu71_packet_prefix__DOT__outer_header[4U])) 
                         | ((2U != vlSelfRef.cu71_packet_prefix__DOT__outer_header[5U]) 
                            & (3U != vlSelfRef.cu71_packet_prefix__DOT__outer_header[5U]))) 
                        | (0x0019U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_8__outer16))) 
                       | (0x02d0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_9__outer16))) 
                      | (0x01e0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_10__outer16))) 
                     | (0U != ((((0x5931494bU ^ vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[0U]) 
                                 | (0x249e96c7U ^ vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[1U])) 
                                | (0x7276c7c5U ^ vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[2U])) 
                               | (0x16c99852U ^ vlSelfRef.cu71_packet_prefix__DOT____VlemCall_11__outer128[3U]))))) {
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = 2U;
                    vlSelfRef.done = 1U;
                } else {
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_12__outer32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[11U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[10U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[9U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[8U]));
                    VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[3U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[52U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[54U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[2U] 
                        = ((0x0000ffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[55U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[56U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[57U])) 
                              << 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[3U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[3U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[55U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[56U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[57U])) 
                              >> 0x00000010U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[1U] 
                        = ((0x00ffffffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[1U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[59U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[60U])) 
                              << 0x00000018U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[2U] 
                        = ((0xffff0000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[2U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[59U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[60U])) 
                              >> 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[1U] 
                        = ((0xff000000U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[1U]) 
                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[61U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[62U]) 
                                                   << 8U) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT__outer_header[63U])));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[0U] 
                        = ((0x000000ffU & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[0U]) 
                           | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[64U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[65U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[66U])) 
                              << 8U));
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[0U] 
                        = ((0xffffff00U & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[0U]) 
                           | vlSelfRef.cu71_packet_prefix__DOT__outer_header[67U]);
                    vlSelfRef.cu71_packet_prefix__DOT____VlemCall_14__outer32 
                        = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[11U]) 
                              << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[10U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[9U]) 
                                                << 8U) 
                                               | vlSelfRef.cu71_packet_prefix__DOT__outer_header[8U]));
                    if ((((0xffffffffU == vlSelfRef.cu71_packet_prefix__DOT____VlemCall_12__outer32) 
                          | (0U == (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[0U] 
                                      | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[1U]) 
                                     | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[2U]) 
                                    | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_13__outer128[3U]))) 
                         | ((IData)(vlSelfRef.cu71_packet_prefix__DOT__last_valid) 
                            & (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_14__outer32 
                               <= vlSelfRef.cu71_packet_prefix__DOT__last_frame_id)))) {
                        __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                        vlSelfRef.error = 1U;
                        vlSelfRef.error_code = 3U;
                        vlSelfRef.done = 1U;
                    } else {
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_15__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[68U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_16__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[68U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_17__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[72U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_18__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[72U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_19__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[68U]));
                        vlSelfRef.cu71_packet_prefix__DOT____VlemCall_20__outer32 
                            = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT__outer_header[72U]));
                        if ((((((0x0000021fU > vlSelfRef.cu71_packet_prefix__DOT____VlemCall_15__outer32) 
                                | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_16__outer32 
                                   > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))) 
                               | (0x0000006eU > vlSelfRef.cu71_packet_prefix__DOT____VlemCall_17__outer32)) 
                              | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_18__outer32 
                                 > (IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))) 
                             | ((0x00000001ffffffffULL 
                                 & (0x0000000000000050ULL 
                                    + ((QData)((IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_19__outer32)) 
                                       + (QData)((IData)(vlSelfRef.cu71_packet_prefix__DOT____VlemCall_20__outer32))))) 
                                != (QData)((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes))))) {
                            __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                            vlSelfRef.error = 1U;
                            vlSelfRef.error_code = 4U;
                            vlSelfRef.done = 1U;
                        } else {
                            if ((1U & vlSelfRef.cu71_packet_prefix__DOT__outer_header[5U])) {
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_21__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[12U]));
                                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128);
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[1U]) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[47U])));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[0U]) 
                                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[51U]);
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCond_28 
                                    = ((0xffffffffU 
                                        != vlSelfRef.cu71_packet_prefix__DOT____VlemCall_21__outer32) 
                                       | (0U != (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[0U] 
                                                   | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[1U]) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[2U]) 
                                                 | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_22__outer128[3U])));
                            } else {
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_23__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[12U]));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_24__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[12U]));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_25__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[11U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[10U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[9U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[8U]));
                                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128);
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[1U]) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[47U])));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[0U]) 
                                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[51U]);
                                VL_ZERO_RESET_W(128, vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128);
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[1U]) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[47U])));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[0U]) 
                                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[51U]);
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCond_28 
                                    = (1U & (((((~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__reference_valid)) 
                                                | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_23__outer32 
                                                   != vlSelfRef.cu71_packet_prefix__DOT__reference_id)) 
                                               | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_24__outer32 
                                                  >= vlSelfRef.cu71_packet_prefix__DOT____VlemCall_25__outer32)) 
                                              | (0U 
                                                 == 
                                                 (((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[0U] 
                                                    | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[1U]) 
                                                   | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[2U]) 
                                                  | vlSelfRef.cu71_packet_prefix__DOT____VlemCall_26__outer128[3U]))) 
                                             | (0U 
                                                != 
                                                ((((vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[0U] 
                                                    ^ vlSelfRef.cu71_packet_prefix__DOT__reference_tag[0U]) 
                                                   | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[1U] 
                                                      ^ vlSelfRef.cu71_packet_prefix__DOT__reference_tag[1U])) 
                                                  | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[2U] 
                                                     ^ vlSelfRef.cu71_packet_prefix__DOT__reference_tag[2U])) 
                                                 | (vlSelfRef.cu71_packet_prefix__DOT____VlemCall_27__outer128[3U] 
                                                    ^ vlSelfRef.cu71_packet_prefix__DOT__reference_tag[3U])))));
                            }
                            if (vlSelfRef.cu71_packet_prefix__DOT____VlemCond_28) {
                                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                                vlSelfRef.error = 1U;
                                vlSelfRef.error_code = 5U;
                                vlSelfRef.done = 1U;
                            } else {
                                __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_84 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[11U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[10U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[9U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[8U]));
                                __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_86 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[12U]));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_29__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[71U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[70U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[69U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[68U]));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_30__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[71U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[70U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[69U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[68U]));
                                vlSelfRef.cu71_packet_prefix__DOT____VlemCall_31__outer32 
                                    = (((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[75U]) 
                                          << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[74U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[73U]) 
                                           << 8U) | vlSelfRef.cu71_packet_prefix__DOT__outer_header[72U]));
                                VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88);
                                VL_ZERO_W(128, __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91);
                                __Vdly__metadata_key_9 
                                    = (1U & vlSelfRef.cu71_packet_prefix__DOT__outer_header[5U]);
                                __Vdly__metadata_frame_id_10 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_84;
                                __Vdly__metadata_reference_id_11 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer32__Vfuncout_86;
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[3U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[38U])) 
                                          << 8U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[3U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[52U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[53U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[54U])) 
                                          << 8U));
                                __Vdly__cu71_packet_prefix__DOT__inner_bytes_6 
                                    = (0x0000ffffU 
                                       & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_29__outer32);
                                __Vdly__metadata_hud_addr_15 
                                    = (0x0000ffffU 
                                       & ((IData)(0x004cU) 
                                          + vlSelfRef.cu71_packet_prefix__DOT____VlemCall_30__outer32));
                                __Vdly__metadata_hud_bytes_16 
                                    = (0x0000ffffU 
                                       & vlSelfRef.cu71_packet_prefix__DOT____VlemCall_31__outer32);
                                __Vdly__cu71_packet_prefix__DOT__outer_validated_4 = 1U;
                                __Vdly__cu71_packet_prefix__DOT__state_0 = 1U;
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[2U] 
                                    = ((0x0000ffffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[3U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[2U] 
                                    = ((0x0000ffffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[55U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[56U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[57U])) 
                                          << 0x00000010U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[3U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[3U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[55U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[56U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[57U])) 
                                          >> 0x00000010U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[1U] 
                                    = ((0x00ffffffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[1U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[2U] 
                                    = ((0xffff0000U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[44U])) 
                                          >> 8U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[1U] 
                                    = ((0x00ffffffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[1U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[58U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[59U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[60U])) 
                                          << 0x00000018U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[2U] 
                                    = ((0xffff0000U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[2U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[58U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[59U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[60U])) 
                                          >> 8U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[1U] 
                                    = ((0xff000000U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[1U]) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[47U])));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[1U] 
                                    = ((0xff000000U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[1U]) 
                                       | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[61U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[62U]) 
                                              << 8U) 
                                             | vlSelfRef.cu71_packet_prefix__DOT__outer_header[63U])));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[0U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[0U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[50U])) 
                                          << 8U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[0U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[0U]) 
                                       | ((((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[64U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_header[65U]) 
                                               << 8U) 
                                              | vlSelfRef.cu71_packet_prefix__DOT__outer_header[66U])) 
                                          << 8U));
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[0U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[0U]) 
                                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[51U]);
                                __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[0U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[0U]) 
                                       | vlSelfRef.cu71_packet_prefix__DOT__outer_header[67U]);
                                __Vdly__metadata_reference_tag_12[0U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[0U];
                                __Vdly__metadata_reference_tag_12[1U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[1U];
                                __Vdly__metadata_reference_tag_12[2U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[2U];
                                __Vdly__metadata_reference_tag_12[3U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_88[3U];
                                vlSelfRef.metadata_output_tag[0U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[0U];
                                vlSelfRef.metadata_output_tag[1U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[1U];
                                vlSelfRef.metadata_output_tag[2U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[2U];
                                vlSelfRef.metadata_output_tag[3U] 
                                    = __Vfunc_cu71_packet_prefix__DOT__outer128__Vfuncout_91[3U];
                            }
                        }
                    }
                }
            } else if (vlSelfRef.rd_rsp_valid) {
                if (vlSelfRef.cu71_packet_prefix__DOT__byte_bad) {
                    __Vtask_cu71_packet_prefix__DOT__reject_packet__code_17 
                        = (((IData)(vlSelfRef.__Vdfg_Regularize_524)
                             ? 0x0aU : ((IData)(vlSelfRef.__Vdfg_Regularize_525)
                                         ? 0x0aU : 
                                        ((IData)(vlSelfRef.__Vdfg_Regularize_526)
                                          ? 0x0aU : 
                                         ((IData)(vlSelfRef.__Vdfg_Regularize_527)
                                           ? 9U : (
                                                   ((0x00000546U 
                                                     > 
                                                     ((IData)(3U) 
                                                      + 
                                                      (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                        - (IData)(0x00000088U)) 
                                                       << 2U)))
                                                     ? 
                                                    ((3U 
                                                      == 
                                                      (3U 
                                                       & (IData)(vlSelfRef.rd_rsp_data)))
                                                      ? 8U
                                                      : (IData)(vlSelfRef.__Vdfg_Regularize_523))
                                                     : 
                                                    ((0U 
                                                      != 
                                                      (3U 
                                                       & (IData)(vlSelfRef.rd_rsp_data)))
                                                      ? 8U
                                                      : (IData)(vlSelfRef.__Vdfg_Regularize_523))) 
                                                   & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_507)))))))) 
                           & (- (IData)((IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_validated))));
                    __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                    vlSelfRef.error = 1U;
                    vlSelfRef.error_code = __Vtask_cu71_packet_prefix__DOT__reject_packet__code_17;
                    vlSelfRef.done = 1U;
                } else {
                    __Vdly__cu71_packet_prefix__DOT__state_0 
                        = ((0x004bU == (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr))
                            ? 3U : ((0x0087U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr))
                                     ? 4U : (((IData)(vlSelfRef.cu71_packet_prefix__DOT__outer_validated) 
                                              & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                 == 
                                                 (0x0000ffffU 
                                                  & ((IData)(0x0069U) 
                                                     + (IData)(vlSelfRef.metadata_hud_addr)))))
                                              ? 5U : 
                                             (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                               == (0x0000ffffU 
                                                   & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                      - (IData)(1U))))
                                               ? 6U
                                               : 1U))));
                }
            }
        } else if ((1U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
            if (vlSelfRef.rd_req_ready) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 2U;
            }
        } else if (((IData)(vlSelfRef.cfg_valid) & (IData)(vlSelfRef.cfg_ready))) {
            vlSelfRef.error = 0U;
            __Vdly__cu71_packet_prefix__DOT__outer_validated_4 = 0U;
            __Vdly__cu71_packet_prefix__DOT__inner_validated_5 = 0U;
            vlSelfRef.error_code = 0U;
            if (((0x02ddU > (IData)(vlSelfRef.cfg_packet_bytes)) 
                 | (0xc000U < (IData)(vlSelfRef.cfg_packet_bytes)))) {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 0U;
                vlSelfRef.error = 1U;
                vlSelfRef.error_code = 1U;
                vlSelfRef.done = 1U;
            } else {
                __Vdly__cu71_packet_prefix__DOT__state_0 = 1U;
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.abort_i) & 
                      (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                            if (vlSelfRef.rd_rsp_valid) {
                                                if (
                                                    (1U 
                                                     & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__byte_bad)))) {
                                                    if (vlSelfRef.cu71_packet_prefix__DOT__outer_validated) {
                                                        if (
                                                            (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                              >= 
                                                              (0x0000ffffU 
                                                               & ((IData)(0x0048U) 
                                                                  + (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes)))) 
                                                             & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                < 
                                                                (0x0000ffffU 
                                                                 & ((IData)(0x004cU) 
                                                                    + (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes)))))) {
                                                            vlSelfRef.cu71_packet_prefix__DOT__received_inner 
                                                                = 
                                                                (((~ 
                                                                   ((IData)(0x000000ffU) 
                                                                    << 
                                                                    (0x0000001fU 
                                                                     & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                         - 
                                                                         ((IData)(0x00000048U) 
                                                                          + (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes))) 
                                                                        << 3U)))) 
                                                                  & vlSelfRef.cu71_packet_prefix__DOT__received_inner) 
                                                                 | (0x00000000ffffffffULL 
                                                                    & ((IData)(vlSelfRef.rd_rsp_data) 
                                                                       << 
                                                                       (0x0000001fU 
                                                                        & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                            - 
                                                                            ((IData)(0x00000048U) 
                                                                             + (IData)(vlSelfRef.cu71_packet_prefix__DOT__inner_bytes))) 
                                                                           << 3U)))));
                                                        }
                                                        if (
                                                            (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                              >= 
                                                              (0x0000ffffU 
                                                               & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                  - (IData)(8U)))) 
                                                             & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                < 
                                                                (0x0000ffffU 
                                                                 & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                    - (IData)(4U)))))) {
                                                            vlSelfRef.cu71_packet_prefix__DOT__received_hud 
                                                                = 
                                                                (((~ 
                                                                   ((IData)(0x000000ffU) 
                                                                    << 
                                                                    (0x0000001fU 
                                                                     & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                         - 
                                                                         ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                          - (IData)(8U))) 
                                                                        << 3U)))) 
                                                                  & vlSelfRef.cu71_packet_prefix__DOT__received_hud) 
                                                                 | (0x00000000ffffffffULL 
                                                                    & ((IData)(vlSelfRef.rd_rsp_data) 
                                                                       << 
                                                                       (0x0000001fU 
                                                                        & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                            - 
                                                                            ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                             - (IData)(8U))) 
                                                                           << 3U)))));
                                                        }
                                                    }
                                                    if (
                                                        ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                         >= 
                                                         (0x0000ffffU 
                                                          & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                             - (IData)(4U))))) {
                                                        vlSelfRef.cu71_packet_prefix__DOT__received_outer 
                                                            = 
                                                            (((~ 
                                                               ((IData)(0x000000ffU) 
                                                                << 
                                                                (0x0000001fU 
                                                                 & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                     - 
                                                                     ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                      - (IData)(4U))) 
                                                                    << 3U)))) 
                                                              & vlSelfRef.cu71_packet_prefix__DOT__received_outer) 
                                                             | (0x00000000ffffffffULL 
                                                                & ((IData)(vlSelfRef.rd_rsp_data) 
                                                                   << 
                                                                   (0x0000001fU 
                                                                    & (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                        - 
                                                                        ((IData)(vlSelfRef.cu71_packet_prefix__DOT__packet_bytes) 
                                                                         - (IData)(4U))) 
                                                                       << 3U)))));
                                                    }
                                                }
                                            }
                                        }
                                    } else if ((1U 
                                                & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                        if (((IData)(vlSelfRef.cfg_valid) 
                                             & (IData)(vlSelfRef.cfg_ready))) {
                                            vlSelfRef.cu71_packet_prefix__DOT__received_inner = 0U;
                                            vlSelfRef.cu71_packet_prefix__DOT__received_outer = 0U;
                                            vlSelfRef.cu71_packet_prefix__DOT__received_hud = 0U;
                                        }
                                    }
                                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                            if (((IData)(vlSelfRef.cfg_valid) 
                                                 & (IData)(vlSelfRef.cfg_ready))) {
                                                vlSelfRef.cu71_packet_prefix__DOT__last_valid 
                                                    = vlSelfRef.cfg_last_valid;
                                                vlSelfRef.cu71_packet_prefix__DOT__last_frame_id 
                                                    = vlSelfRef.cfg_last_frame_id;
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_valid 
                                                    = vlSelfRef.cfg_reference_valid;
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_id 
                                                    = vlSelfRef.cfg_reference_id;
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_tag[0U] 
                                                    = vlSelfRef.cfg_reference_tag[0U];
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_tag[1U] 
                                                    = vlSelfRef.cfg_reference_tag[1U];
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_tag[2U] 
                                                    = vlSelfRef.cfg_reference_tag[2U];
                                                vlSelfRef.cu71_packet_prefix__DOT__reference_tag[3U] 
                                                    = vlSelfRef.cfg_reference_tag[3U];
                                                vlSelfRef.cu71_packet_prefix__DOT__packet_bytes 
                                                    = vlSelfRef.cfg_packet_bytes;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if ((1U & (~ (IData)(vlSelfRef.rst)))) {
        if ((1U & (~ ((IData)(vlSelfRef.abort_i) & 
                      (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.cu71_packet_prefix__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.cu71_packet_prefix__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)))) {
                                            if (vlSelfRef.rd_rsp_valid) {
                                                if (
                                                    (1U 
                                                     & (~ (IData)(vlSelfRef.cu71_packet_prefix__DOT__byte_bad)))) {
                                                    if (
                                                        (0x004cU 
                                                         > (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr))) {
                                                        if (
                                                            (0x4bU 
                                                             >= 
                                                             (0x0000007fU 
                                                              & (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)))) {
                                                            __Vdly_Val__cu71_packet_prefix__DOT__outer_header_73 
                                                                = vlSelfRef.rd_rsp_data;
                                                            __Vdly_Dim0__cu71_packet_prefix__DOT__outer_header_74 
                                                                = 
                                                                (0x0000007fU 
                                                                 & (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr));
                                                            __Vdly_Set__cu71_packet_prefix__DOT__outer_header_75 = 1U;
                                                        }
                                                    }
                                                    if (vlSelfRef.cu71_packet_prefix__DOT__outer_validated) {
                                                        if (
                                                            ((0x004cU 
                                                              <= (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)) 
                                                             & (0x0088U 
                                                                > (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)))) {
                                                            if (
                                                                (0x3bU 
                                                                 >= 
                                                                 (0x0000003fU 
                                                                  & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                     - (IData)(0x0cU))))) {
                                                                __Vdly_Val__cu71_packet_prefix__DOT__inner_header_76 
                                                                    = vlSelfRef.rd_rsp_data;
                                                                __Vdly_Dim0__cu71_packet_prefix__DOT__inner_header_77 
                                                                    = 
                                                                    (0x0000003fU 
                                                                     & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                        - (IData)(0x0cU)));
                                                                __Vdly_Set__cu71_packet_prefix__DOT__inner_header_78 = 1U;
                                                            }
                                                        }
                                                        if (
                                                            (((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                              >= (IData)(vlSelfRef.metadata_hud_addr)) 
                                                             & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                < 
                                                                (0x0000ffffU 
                                                                 & ((IData)(0x006aU) 
                                                                    + (IData)(vlSelfRef.metadata_hud_addr)))))) {
                                                            if (
                                                                (0x69U 
                                                                 >= 
                                                                 (0x0000007fU 
                                                                  & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                     - (IData)(vlSelfRef.metadata_hud_addr))))) {
                                                                __Vdly_Val__cu71_packet_prefix__DOT__hud_header_79 
                                                                    = vlSelfRef.rd_rsp_data;
                                                                __Vdly_Dim0__cu71_packet_prefix__DOT__hud_header_80 
                                                                    = 
                                                                    (0x0000007fU 
                                                                     & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                        - (IData)(vlSelfRef.metadata_hud_addr)));
                                                                __Vdly_Set__cu71_packet_prefix__DOT__hud_header_81 = 1U;
                                                            }
                                                        }
                                                    }
                                                    if (vlSelfRef.cu71_packet_prefix__DOT__inner_validated) {
                                                        if (
                                                            ((0x0088U 
                                                              <= (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)) 
                                                             & (0x01daU 
                                                                > (IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr)))) {
                                                            if (
                                                                (0x0151U 
                                                                 >= 
                                                                 (0x000001ffU 
                                                                  & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                     - (IData)(0x0088U))))) {
                                                                __Vdly_Val__cu71_packet_prefix__DOT__qmap_mem_82 
                                                                    = vlSelfRef.rd_rsp_data;
                                                                __Vdly_Dim0__cu71_packet_prefix__DOT__qmap_mem_83 
                                                                    = 
                                                                    (0x000001ffU 
                                                                     & ((IData)(vlSelfRef.cu71_packet_prefix__DOT__scan_addr) 
                                                                        - (IData)(0x0088U)));
                                                                __Vdly_Set__cu71_packet_prefix__DOT__qmap_mem_84 = 1U;
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelfRef.memory_reads = __Vdly__memory_reads_23;
    if (__Vdly_Set__metadata_plane_dispatch_52) {
        vlSelfRef.metadata_plane_dispatch[0U] = 0U;
        vlSelfRef.metadata_plane_dispatch[1U] = 0U;
        vlSelfRef.metadata_plane_dispatch[2U] = 0U;
    }
    if (__Vdly_Set__metadata_plane_dispatch_54) {
        vlSelfRef.metadata_plane_dispatch[0U] = __Vdly_Val__metadata_plane_dispatch_53;
    }
    if (__Vdly_Set__metadata_plane_dispatch_56) {
        vlSelfRef.metadata_plane_dispatch[1U] = __Vdly_Val__metadata_plane_dispatch_55;
    }
    if (__Vdly_Set__metadata_plane_dispatch_58) {
        vlSelfRef.metadata_plane_dispatch[2U] = __Vdly_Val__metadata_plane_dispatch_57;
    }
    if (__Vdly_Set__metadata_plane_blocks_59) {
        vlSelfRef.metadata_plane_blocks[0U] = 0U;
        vlSelfRef.metadata_plane_blocks[1U] = 0U;
        vlSelfRef.metadata_plane_blocks[2U] = 0U;
    }
    if (__Vdly_Set__metadata_plane_blocks_61) {
        vlSelfRef.metadata_plane_blocks[0U] = __Vdly_Val__metadata_plane_blocks_60;
    }
    if (__Vdly_Set__metadata_plane_blocks_63) {
        vlSelfRef.metadata_plane_blocks[1U] = __Vdly_Val__metadata_plane_blocks_62;
    }
    if (__Vdly_Set__metadata_plane_blocks_65) {
        vlSelfRef.metadata_plane_blocks[2U] = __Vdly_Val__metadata_plane_blocks_64;
    }
    if (__Vdly_Set__metadata_plane_blocks_w_66) {
        vlSelfRef.metadata_plane_blocks_w[0U] = 0U;
        vlSelfRef.metadata_plane_blocks_w[1U] = 0U;
        vlSelfRef.metadata_plane_blocks_w[2U] = 0U;
    }
    if (__Vdly_Set__metadata_plane_blocks_w_68) {
        vlSelfRef.metadata_plane_blocks_w[0U] = __Vdly_Val__metadata_plane_blocks_w_67;
    }
    if (__Vdly_Set__metadata_plane_blocks_w_70) {
        vlSelfRef.metadata_plane_blocks_w[1U] = __Vdly_Val__metadata_plane_blocks_w_69;
    }
    if (__Vdly_Set__metadata_plane_blocks_w_72) {
        vlSelfRef.metadata_plane_blocks_w[2U] = __Vdly_Val__metadata_plane_blocks_w_71;
    }
    if (__Vdly_Set__cu71_packet_prefix__DOT__qmap_mem_84) {
        vlSelfRef.cu71_packet_prefix__DOT__qmap_mem[__Vdly_Dim0__cu71_packet_prefix__DOT__qmap_mem_83] 
            = __Vdly_Val__cu71_packet_prefix__DOT__qmap_mem_82;
    }
    vlSelfRef.metadata_key = __Vdly__metadata_key_9;
    vlSelfRef.metadata_frame_id = __Vdly__metadata_frame_id_10;
    vlSelfRef.metadata_reference_id = __Vdly__metadata_reference_id_11;
    vlSelfRef.metadata_reference_tag[0U] = __Vdly__metadata_reference_tag_12[0U];
    vlSelfRef.metadata_reference_tag[1U] = __Vdly__metadata_reference_tag_12[1U];
    vlSelfRef.metadata_reference_tag[2U] = __Vdly__metadata_reference_tag_12[2U];
    vlSelfRef.metadata_reference_tag[3U] = __Vdly__metadata_reference_tag_12[3U];
    vlSelfRef.metadata_hud_bytes = __Vdly__metadata_hud_bytes_16;
    vlSelfRef.cu71_packet_prefix__DOT__crc_outer = __Vdly__cu71_packet_prefix__DOT__crc_outer_31;
    vlSelfRef.cu71_packet_prefix__DOT__crc_inner = __Vdly__cu71_packet_prefix__DOT__crc_inner_32;
    vlSelfRef.cu71_packet_prefix__DOT__crc_hud = __Vdly__cu71_packet_prefix__DOT__crc_hud_33;
    if (__Vdly_Set__cu71_packet_prefix__DOT__inner_header_78) {
        vlSelfRef.cu71_packet_prefix__DOT__inner_header[__Vdly_Dim0__cu71_packet_prefix__DOT__inner_header_77] 
            = __Vdly_Val__cu71_packet_prefix__DOT__inner_header_76;
    }
    if (__Vdly_Set__cu71_packet_prefix__DOT__outer_header_75) {
        vlSelfRef.cu71_packet_prefix__DOT__outer_header[__Vdly_Dim0__cu71_packet_prefix__DOT__outer_header_74] 
            = __Vdly_Val__cu71_packet_prefix__DOT__outer_header_73;
    }
    vlSelfRef.metadata_hud_addr = __Vdly__metadata_hud_addr_15;
    vlSelfRef.cu71_packet_prefix__DOT__inner_validated 
        = __Vdly__cu71_packet_prefix__DOT__inner_validated_5;
    if (__Vdly_Set__cu71_packet_prefix__DOT__hud_header_81) {
        vlSelfRef.cu71_packet_prefix__DOT__hud_header[__Vdly_Dim0__cu71_packet_prefix__DOT__hud_header_80] 
            = __Vdly_Val__cu71_packet_prefix__DOT__hud_header_79;
    }
    if (__Vdly_Set__metadata_plane_addr_40) {
        vlSelfRef.metadata_plane_addr[0U] = 0U;
        vlSelfRef.metadata_plane_bytes[0U] = 0U;
    }
    if (__Vdly_Set__metadata_plane_addr_41) {
        vlSelfRef.metadata_plane_addr[1U] = 0U;
        vlSelfRef.metadata_plane_addr[2U] = 0U;
        vlSelfRef.metadata_plane_bytes[1U] = 0U;
        vlSelfRef.metadata_plane_bytes[2U] = 0U;
    }
    if (__Vdly_Set__metadata_plane_bytes_43) {
        vlSelfRef.metadata_plane_addr[0U] = __Vdly_Val__metadata_plane_addr_44;
        vlSelfRef.metadata_plane_bytes[0U] = __Vdly_Val__metadata_plane_bytes_42;
    }
    if (__Vdly_Set__metadata_plane_addr_48) {
        vlSelfRef.metadata_plane_addr[1U] = __Vdly_Val__metadata_plane_addr_47;
    }
    if (__Vdly_Set__metadata_plane_addr_51) {
        vlSelfRef.metadata_plane_addr[2U] = __Vdly_Val__metadata_plane_addr_50;
    }
    if (__Vdly_Set__metadata_plane_bytes_46) {
        vlSelfRef.metadata_plane_bytes[1U] = __Vdly_Val__metadata_plane_bytes_45;
    }
    if (__Vdly_Set__metadata_plane_addr_48) {
        vlSelfRef.metadata_plane_bytes[2U] = __Vdly_Val__metadata_plane_bytes_49;
    }
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
    vlSelfRef.cu71_packet_prefix__DOT__inner_bytes 
        = __Vdly__cu71_packet_prefix__DOT__inner_bytes_6;
    vlSelfRef.cu71_packet_prefix__DOT__outer_validated 
        = __Vdly__cu71_packet_prefix__DOT__outer_validated_4;
    vlSelfRef.cu71_packet_prefix__DOT__scan_addr = __Vdly__cu71_packet_prefix__DOT__scan_addr_25;
    vlSelfRef.rd_req_addr = vlSelfRef.cu71_packet_prefix__DOT__scan_addr;
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
    vlSelfRef.cu71_packet_prefix__DOT__state = __Vdly__cu71_packet_prefix__DOT__state_0;
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
    vlSelfRef.rd_rsp_ready = ((2U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)) 
                              | (9U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.busy = (0U != (IData)(vlSelfRef.cu71_packet_prefix__DOT__state));
    vlSelfRef.debug_state = vlSelfRef.cu71_packet_prefix__DOT__state;
    vlSelfRef.cfg_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                           & (0U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.rd_req_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                              & (1U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.metadata_valid = ((~ (IData)(vlSelfRef.abort_i)) 
                                & (7U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
    vlSelfRef.commit_ready = ((~ (IData)(vlSelfRef.abort_i)) 
                              & (8U == (IData)(vlSelfRef.cu71_packet_prefix__DOT__state)));
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
    vlSelfRef.qmap_req_ready = ((IData)(vlSelfRef.commit_ready) 
                                & ((~ (IData)(vlSelfRef.commit_valid)) 
                                   & (0x0546U > (IData)(vlSelfRef.qmap_req_index))));
}

void Vcu71_packet_prefix___024root___trigger_orInto__act_vec_vec(VlUnpacked<QData/*63:0*/, 1> &out, const VlUnpacked<QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___trigger_orInto__act_vec_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((0U >= n));
}

void Vcu71_packet_prefix___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 1> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___trigger_clear__act\n"); );
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
void Vcu71_packet_prefix___024root___eval_debug_assertions(Vcu71_packet_prefix___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vcu71_packet_prefix___024root___eval_debug_assertions\n"); );
    Vcu71_packet_prefix__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
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
    if (VL_UNLIKELY(((vlSelfRef.cfg_valid & 0xfeU)))) {
        Verilated::overWidthError("cfg_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.cfg_last_valid & 0xfeU)))) {
        Verilated::overWidthError("cfg_last_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.cfg_reference_valid 
                      & 0xfeU)))) {
        Verilated::overWidthError("cfg_reference_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.rd_req_ready & 0xfeU)))) {
        Verilated::overWidthError("rd_req_ready");
    }
    if (VL_UNLIKELY(((vlSelfRef.rd_rsp_valid & 0xfeU)))) {
        Verilated::overWidthError("rd_rsp_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.metadata_ready & 0xfeU)))) {
        Verilated::overWidthError("metadata_ready");
    }
    if (VL_UNLIKELY(((vlSelfRef.qmap_req_valid & 0xfeU)))) {
        Verilated::overWidthError("qmap_req_valid");
    }
    if (VL_UNLIKELY(((vlSelfRef.qmap_req_index & 0xf800U)))) {
        Verilated::overWidthError("qmap_req_index");
    }
    if (VL_UNLIKELY(((vlSelfRef.commit_valid & 0xfeU)))) {
        Verilated::overWidthError("commit_valid");
    }
}
#endif  // VL_DEBUG
