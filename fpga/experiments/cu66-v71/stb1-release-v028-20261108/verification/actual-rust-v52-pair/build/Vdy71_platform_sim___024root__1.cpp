// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vdy71_platform_sim.h for the primary calling header

#include "Vdy71_platform_sim__pch.h"

extern const VlWide<16>/*511:0*/ Vdy71_platform_sim__ConstPool__CONST_4;
extern const VlWide<16>/*511:0*/ Vdy71_platform_sim__ConstPool__CONST_3;
extern const VlWide<16>/*511:0*/ Vdy71_platform_sim__ConstPool__CONST_11;

void Vdy71_platform_sim___024root___act_sequent__TOP__6(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__6\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254);
    SData/*10:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456 = 0;
    SData/*10:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457 = 0;
    SData/*10:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_139;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_139 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_140;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_140 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_141;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_141 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_146;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_146 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_159;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_159 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_160;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_160 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_184;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_184 = 0;
    IData/*31:0*/ __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_186;
    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_186 = 0;
    VlWide<4>/*127:0*/ __Vtemp_17;
    // Body
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_error_387 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__compact_424 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__plane_425 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_error_326 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_error_348 = 0U;
    } else {
        if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 
                    = (0x0000000fU & ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                       ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                           ? 0U : Vdy71_platform_sim__ConstPool__CONST_4
                                          [(0x07ffffffU 
                                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))])
                                       : Vdy71_platform_sim__ConstPool__CONST_4
                                      [(0x07ffffffU 
                                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]));
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 
                    = (0x0000000fU & ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                       ? Vdy71_platform_sim__ConstPool__CONST_4
                                      [(0x07ffffffU 
                                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]
                                       : (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group)) 
                                           | (0x000000ffU 
                                              == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group)))
                                           ? 9U : (
                                                   (0x000000ffU 
                                                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group))
                                                    ? 5U
                                                    : 1U))));
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__idct_out_ready) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_valid))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 = 0U;
                }
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 = 9U;
            }
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                          >> 2U)))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_error_348 
                            = (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group));
                    }
                }
            }
        } else {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 
                    = (0x0000000fU & ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                       ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                           ? Vdy71_platform_sim__ConstPool__CONST_3
                                          [(0x07ffffffU 
                                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]
                                           : 7U) : 
                                      ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                        ? Vdy71_platform_sim__ConstPool__CONST_3
                                       [(0x07ffffffU 
                                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]
                                        : ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k))
                                            ? ((3U 
                                                == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__group_index))
                                                ? (
                                                   (2U 
                                                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                                    ? 3U
                                                    : 9U)
                                                : (
                                                   (2U 
                                                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                                    ? 1U
                                                    : 3U))
                                            : ((2U 
                                                == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                                ? 1U
                                                : 3U)))));
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 
                    = (0x0000000fU & ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                       ? Vdy71_platform_sim__ConstPool__CONST_3
                                      [(0x07ffffffU 
                                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]
                                       : ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k))
                                           ? ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__group_index))
                                               ? ((2U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                                   ? 3U
                                                   : 9U)
                                               : ((2U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                                   ? 1U
                                                   : 3U))
                                           : ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                               ? 1U
                                               : 3U))));
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 
                    = (0x0000000fU & Vdy71_platform_sim__ConstPool__CONST_3
                       [(0x07ffffffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))]);
            } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__inverse__in_valid) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__in_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state_347 = 0x0aU;
            }
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__inverse__in_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__in_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_error_348 = 0U;
                        }
                    }
                }
            }
        }
        if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_error_387 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__input_bad;
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__dequant__in_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__in_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_error_387 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__cfg_ready))) {
            if ((1U & (~ (((2U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane)) 
                           | ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                              & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks 
                             != ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                                  ? ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                                      ? 0x00001418U
                                      : 0x00001518U)
                                  : ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                                      ? 0x00000533U
                                      : 0x00000546U))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__compact_424 
                    = (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__plane_425 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__slot_ready) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__reconstruct__in_valid) 
                 & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)) 
                    | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_error_326 
                    = (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key)) 
                        & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden))) 
                       & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_tag 
                          != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_id));
            }
        }
    }
    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_enable) {
        if ((0x02cfU >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_address))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__0__KET____DOT__read_data_297 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__0__KET____DOT__memory
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_address];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__1__KET____DOT__read_data_298 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__1__KET____DOT__memory
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_address];
        } else {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__0__KET____DOT__read_data_297 = 0ULL;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__strip_bank__BRA__1__KET____DOT__read_data_298 = 0ULL;
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_seen_692 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && (1U 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_sync) 
                                                    >> 1U)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_boundary_707 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_guard) 
                                                  >> 3U) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__requests_idle)));
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_next_8 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__presented_637 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__front_valid_536 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborted_546 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parsed_at_164 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_expected_sequence_188 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_slot_valid_230 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__ticket_817 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__diag_address_776 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_offset_864 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__owner_828 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__next_owner_829 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__pending_826 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__ticket_866 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__hud_index_676 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_expected_address_189 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__row_675 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_rr_137 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_abort_sent_652 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__bank_151 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__plane_152 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__index_153 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__prefer_write_149 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_owner_196 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_q_222 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presented_at_221 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__held_generation_863 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_opcode_793 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__background_phase_128 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_reserved_134 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_owner_135 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_word_end_796 = 4ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__0__KET___797 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__1__KET___798 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__8__KET___804 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__9__KET___805 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__10__KET___806 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__11__KET___807 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__operation_772 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__current_frame_303 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__vector_start_585 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__failed_148 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__rows_acked_259 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__memory_acked_258 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_committed_544 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__input_done_302 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_254 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_valid_539 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_ref_786 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_bs_50 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_fid_785 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__expected_packet_crc_787 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__reference_816 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__current_key_304 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fid_233 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_overwrites_q_223 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__last_started_generation_773 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__seen_busy_775 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_valid_876 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_frame_625 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_length_789 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_offset_788 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_ref_784 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_key_791 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_fid_783 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_547 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_valid_531 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready_812 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__failed_263 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__wanted_u_stage_642 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_identity_bank_202 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_transfer_fault_14 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync2_711 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_remainder_457 = 0U;
        vlSelfRef.__Vdly__front_bank_537 = 0U;
        vlSelfRef.__Vdly__error_206 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__arrived_at_217 = 0ULL;
        vlSelfRef.__Vdly__error_code_207 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__committed_at_220 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_reason_214 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_frame_212 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__generation_150 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_stage_213 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_gen_782 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_identity_199 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__bank_cache_186 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_generation_624 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_gen_781 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__read_identity_bank_201 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_addr_450 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_generation_211 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_held_166 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__q_expected_index_203 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_index_597 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_valid_633 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_black_658 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_context_706 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__identity_fault_830 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__aborted_205 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_fault_659 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__vector_end_586 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_good_180 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__prepared_at_219 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__0__KET___600 = 0U;
        VL_ASSIGN_W(512, vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253, Vdy71_platform_sim__ConstPool__CONST_11);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_fail_reason_621 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_identity_200 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_address_216 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__1__KET___602 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__2__KET___604 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_detail_215 = 0U;
    } else {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_choice_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_next_8 = 1U;
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__presented_637 = 0U;
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__safe_swap) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__front_valid_536 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_valid_539 = 0U;
            vlSelfRef.__Vdly__front_bank_537 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_bank;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborted_546 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__banks__drain_done) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborted_546 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_valid_531 = 0U;
            }
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_valid_531 = 0U;
            } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_ready))) {
                if ((1U & (~ (((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id) 
                               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid) 
                                  & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id 
                                     <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))) 
                              | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key) 
                                 & (0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)))))) {
                    if ((1U & (~ ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)) 
                                  & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid)) 
                                     | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id 
                                        != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id)))))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_valid_531 
                            = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)));
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__payload_start_clear) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parsed_at_164 = 0ULL;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_non_hud)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parsed_at_164 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_expected_sequence_188 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_sequence;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_expected_address_189 
                = (0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__calculated_packet_address);
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_owner_196 
                = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__rd_req_valid)));
        }
        if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_code))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_slot_valid_230 
                = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_slot_valid_230) 
                   | (0x00ffU & ((IData)(1U) << (7U 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence))));
        }
        if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_req_valid) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_ready)) 
             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_req_valid) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p1_ready)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__owner_828 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__choice;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__next_owner_829 
                = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__choice)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__pending_826 = 1U;
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__hud_index_676 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__row_675 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_row;
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_abort_sent_652 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_abort_valid) 
             & ((~ (IData)(vlSelfRef.rst)) & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_abort_sent_652 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
                if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)) 
                     | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__bank_151 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_bank;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__plane_152 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_plane;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__index_153 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_index;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__prefer_write_149 
                        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__choose_write)));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__generation_150 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                = (1U | (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p1_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                = (2U | (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p2_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                = (4U | (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p3_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                = (8U | (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state)))) {
                if (((0U != (IData)(vlSelfRef.__Vdfg_Regularize_14866)) 
                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_turn) 
                        | (~ (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_rr_137 
                        = (3U & ((IData)(1U) + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected)));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                        = ((~ ((IData)(1U) << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected))) 
                           & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
                } else if (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)) 
                            & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__hold_for_lcd)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123 
                        = ((~ ((IData)(1U) << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__selected))) 
                           & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__pending_123));
                }
            }
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__mem_req_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__request_ready))) {
                    if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__background_phase_128 
                            = ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))
                                ? 1U : ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))
                                         ? 2U : 0U));
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__group_phase) 
                                      & (4U <= ((IData)(1U) 
                                                + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_grants))))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_owner_135 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner;
                        }
                    }
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_reserved_134 
                        = ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner)) 
                           && (1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__group_phase) 
                                        & (4U <= ((IData)(1U) 
                                                  + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__bg_grants)))))));
                }
            }
        }
        if (vlSelfRef.transport_fault) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__begin_packet) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__blocked) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__expected_packet_crc_787 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__;
            if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__begin_ready) 
                            & (0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation)) 
                           & (0U != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__)) 
                          & (0x0000c000U >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (1U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__scalar_conflict) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
        }
        if (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__used)) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fifo_identity)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__alias_write) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__push)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
            }
        }
        if (vlSelfRef.bus_write) {
            if ((0x0200U == (IData)(vlSelfRef.bus_address))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__diag_address_776 
                    = (0x000003ffU & vlSelfRef.bus_wdata);
            }
            if ((0x0720U != (IData)(vlSelfRef.bus_address))) {
                if ((0x0724U != (IData)(vlSelfRef.bus_address))) {
                    if ((0x0728U == (IData)(vlSelfRef.bus_address))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_offset_864 
                            = vlSelfRef.bus_wdata;
                    }
                    if ((0x0728U != (IData)(vlSelfRef.bus_address))) {
                        if ((0x072cU != (IData)(vlSelfRef.bus_address))) {
                            if ((0x0730U == (IData)(vlSelfRef.bus_address))) {
                                if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__setup_legal) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__ticket_866 
                                        = vlSelfRef.bus_wdata;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__held_generation_863 
                                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation;
                                }
                                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__setup_legal)))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault_872 = 1U;
                                }
                            }
                        }
                    }
                }
            }
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_word_end_796 
                        = (0x00000001ffffffffULL & 
                           (4ULL + (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[4U]))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__0__KET___797 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[0U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__1__KET___798 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[1U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__8__KET___804 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[8U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__9__KET___805 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[9U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__10__KET___806 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[10U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__11__KET___807 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[11U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__operation_772 
                        = (0x000000ffU & vlSelfRef.bus_wdata);
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 1U;
                    if ((1U & (~ ((((((((1U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata)) 
                                        | (2U == (0x000000ffU 
                                                  & vlSelfRef.bus_wdata))) 
                                       | (3U == (0x000000ffU 
                                                 & vlSelfRef.bus_wdata))) 
                                      | (4U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata))) 
                                     | (5U == (0x000000ffU 
                                               & vlSelfRef.bus_wdata))) 
                                    | (6U == (0x000000ffU 
                                              & vlSelfRef.bus_wdata))) 
                                   | (0x10U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata))) 
                                  | ((0x11U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata)) 
                                     || (0x12U == (0x000000ffU 
                                                   & vlSelfRef.bus_wdata))))))) {
                        if ((0x13U != (0x000000ffU 
                                       & vlSelfRef.bus_wdata))) {
                            if ((0x14U != (0x000000ffU 
                                           & vlSelfRef.bus_wdata))) {
                                if ((0x16U != (0x000000ffU 
                                               & vlSelfRef.bus_wdata))) {
                                    if ((0x17U != (0x000000ffU 
                                                   & vlSelfRef.bus_wdata))) {
                                        if ((0x15U 
                                             != (0x000000ffU 
                                                 & vlSelfRef.bus_wdata))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000001U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_q_222 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_plus1;
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_overwrites_q_223 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_overwrites_plus1;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_presented) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presented_at_221 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__software_command_valid) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_pending)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_opcode_793 
                = ((0x0aU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))
                    ? 5U : 6U);
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_ref_786 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_fid_785 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_gen_782 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 1U;
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort)))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))) {
                if ((0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__current_frame_303 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__current_key_304 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key;
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
                      & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__vector_start_585 = 0x01daU;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__vector_end_586 
                                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0;
                                        }
                                    }
                                }
                            }
                        }
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated) {
                                                if (
                                                    ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                     == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__0__KET__))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__0__KET___600 
                                                        = 
                                                        ((6U 
                                                          == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte))
                                                          ? 1U
                                                          : 0x005aU);
                                                }
                                                if (
                                                    ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                     == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__1__KET__))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__1__KET___602 
                                                        = 
                                                        ((6U 
                                                          == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte))
                                                          ? 1U
                                                          : 0x002dU);
                                                }
                                                if (
                                                    ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                     == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__2__KET__))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__2__KET___604 
                                                        = 
                                                        ((6U 
                                                          == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte))
                                                          ? 1U
                                                          : 0x002dU);
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
        if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_rsp_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_rsp_ready))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__aborting)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__failed_148 = 1U;
                        }
                    }
                }
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)) 
                 | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__failed_148 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__bad_metadata;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__rows_fire) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__rows_acked_259 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__write_fire) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__memory_acked_258 = 1U;
        }
        if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
                        & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                       & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts)))) {
                                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_valid) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__s_ready))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__rows_acked_259 = 0U;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__memory_acked_258 = 0U;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[0U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[0U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[1U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[1U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[2U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[2U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__wanted_tag_236[3U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[3U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fid_233 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
                            }
                        }
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_committed_544 = 0U;
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__input_done_302 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))) {
            if ((0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__input_done_302 = 0U;
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bad_tile)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__active) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_busy) {
                    if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_row))) {
                        if ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_index 
                             == ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_plane))
                                  ? 0x00001517U : 0x00000545U))) {
                            if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_plane))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__input_done_302 = 1U;
                            }
                        }
                    }
                }
            }
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
               & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
              & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
             | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_254 = 1U;
            }
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                             >> 3U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__plane_cfg_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane_cfg_ready))) {
                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__next_plane) 
                                 != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_254 = 1U;
                            }
                        }
                    } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_254 = 0U;
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p3_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                = (7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                = (0x0eU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p1_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                = (0x0dU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p2_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                = (0x0bU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124));
        }
        if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state))) {
                if ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                        = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124) 
                           | (0x0fU & ((IData)(1U) 
                                       << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))));
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid) {
                if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__beat))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                        = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124) 
                           | (0x0fU & ((IData)(1U) 
                                       << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))));
                }
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state)))) {
            if (((0U != (IData)(vlSelfRef.__Vdfg_Regularize_14866)) 
                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_turn) 
                    | (~ (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124 
                    = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_valid_124) 
                       | (0x0fU & ((IData)(1U) << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected))));
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__frame_active) 
             & (IData)(vlSelfRef.busy))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__seen_busy_775 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_start) {
                                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_ready) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__last_started_generation_773 
                                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation;
                                }
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__release_packet) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__seen_busy_775 = 0U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_start) {
                                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_ready) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__seen_busy_775 = 0U;
                                }
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_valid_876 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending) 
             & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__ack_sync) 
                       >> 1U)) != (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__ack_seen)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_valid_876 
                = (((IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet) 
                    & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__invalidated))) 
                   & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id 
                      == vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame));
        }
        if (((IData)(vlSelfRef.bus_write) & (0x0384U 
                                             == (IData)(vlSelfRef.bus_address)))) {
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet) 
                  & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending))) 
                 & (1U == vlSelfRef.bus_wdata))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_valid_876 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_prepare_valid) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_pending)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_length_789 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_length;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_offset_788 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_offset;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_ref_784 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_key_791 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_fid_783 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_transfer_fault_14 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_gen_781 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[0U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[0U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[1U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[1U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[2U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[2U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_tag_792[3U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[3U];
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 1U;
        if (((((((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)) 
                   | (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                  | (2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                 | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                | (4U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
               | (5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
              | (0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
             | (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)))) {
            if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 = 0x0400U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 0U;
                } else {
                    if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                    } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                    } else if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((0x0eU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                            }
                        }
                    }
                    if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 = 0x0033U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 0U;
                        } else if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((0x0eU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 = 0U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 0U;
                                }
                            }
                        }
                    }
                }
                if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 0U;
                    } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 0U;
                    }
                    if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_bs_50 = 0U;
                        } else if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((0x0eU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_bs_50 
                                        = (3U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                                                 >> 0x16U));
                                }
                            }
                        }
                        if ((3U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    if ((0x02eeU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__refresh_count))) {
                                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__mem_req_valid) {
                                            if ((0U 
                                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[0U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[0U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[1U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[1U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[2U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[2U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[3U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[3U];
                                            } else if (
                                                       (3U 
                                                        == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[0U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[0U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[1U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[1U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[2U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[2U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44[3U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[3U];
                                            } else {
                                                __Vtemp_17[0U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__wdata
                                                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner];
                                                __Vtemp_17[1U] = 0U;
                                                __Vtemp_17[2U] = 0U;
                                                __Vtemp_17[3U] = 0U;
                                                VL_SHIFTL_WWI(128,128,32, vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_data_44, __Vtemp_17, 
                                                              (vlSelfRef.__Vdfg_Regularize_15015 
                                                               << 4U));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 
                    = (0x00001fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                                      >> 9U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_bs_50 
                    = (3U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                             >> 0x16U));
            } else {
                if ((8U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((0x0bU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((9U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((0x0aU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((0x0cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                                } else if ((0x0dU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ras_n_51 = 0U;
                                }
                            }
                        }
                    }
                }
                if ((8U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 
                        = (0x000001ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address);
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_bs_50 
                        = (3U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                                 >> 0x16U));
                } else if ((0x0bU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((9U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((0x0aU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((0x0cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_a_49 = 0x0400U;
                            }
                        }
                    }
                }
            }
            if ((7U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((8U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 0U;
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__is_write) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 0U;
                    }
                } else if ((0x0bU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((9U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((0x0aU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((0x0cU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((0x0dU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_cas_n_52 = 0U;
                                }
                            }
                            if ((0x0cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_we_n_53 = 0U;
                            }
                        }
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_547 = 0U;
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_committed_544 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_valid_539 = 1U;
                }
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))))) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_ready))) {
                        if ((((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id) 
                              | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid) 
                                 & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id 
                                    <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))) 
                             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key) 
                                & (0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_547 = 1U;
                        } else if ((1U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)) 
                                          & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid)) 
                                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id 
                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_547 = 1U;
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bad_access) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready_812 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 1U;
        }
        if (((0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__setup_legal) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__ticket_817 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_ticket;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__reference_816 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__3__KET__;
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready_812 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 
                = (1U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__setup_legal)) 
                         | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bad_access)));
        }
        if (((0x0fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready_812 = 0U;
            if ((1U & (((((0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                          | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured))) 
                         | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__command_matches))) 
                        | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed)) 
                       | ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read)) 
                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__packed_loaded) 
                             != (0x000000ffU & (((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                >> 1U))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 1U;
            }
        }
        if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
                if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT____Vcellinp__bulk__rsp_valid) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_error) 
                                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed))))) {
                            if ((((IData)(1U) + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__index)) 
                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready_812 
                                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read;
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__start_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__failed_263 = 0U;
            } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__active) 
                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error) 
                           | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__failed_263 = 1U;
            }
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                              >> 6U)))) {
                    if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_remainder_457 
                                                = (0x000000ffU 
                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_next));
                                        }
                                    }
                                }
                            }
                        }
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                            if ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_read_address 
                                                 < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__packet_bytes))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_addr_450 
                                                    = 
                                                    (0x0000ffffU 
                                                     & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_read_address);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                         >> 4U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 3U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 2U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 1U)))) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) {
                                            if ((1U 
                                                 & (~ 
                                                    (((((((((5U 
                                                             != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                                                            & (6U 
                                                               != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))) 
                                                           | (0x002eU 
                                                              > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                                                          | (0xc000U 
                                                             < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                                                         | (0U 
                                                            == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                                                        | (0x00001fa4U 
                                                           < vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                                                       | (0U 
                                                          == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                                                      | (0x0100U 
                                                         < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                                                     | ((6U 
                                                         == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                                                        & (1U 
                                                           != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_remainder_457 = 0U;
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
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__wanted_u_stage_642 
            = (0x000003ffU & (((~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active) 
                                   | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__invalid_line))) 
                               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_valid))
                               ? ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_line) 
                                  - (IData)(0x0028U))
                               : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u)));
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_identity_bank_202 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_identity_200 
                = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane) 
                    << 0x00000011U) | (0x0001ffffU 
                                       & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id));
        }
        if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 1U;
            }
        } else if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 1U;
            }
        } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT____Vcellinp__bulk__rsp_valid) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_error) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault_813 = 1U;
                }
            }
        }
        if ((((((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state)) 
                & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_owner))) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_write)) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__aux_rsp_valid)) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__m_rsp_ready))) {
            if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_transfer_fault_14 = 1U;
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync2_711 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync1;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) {
                vlSelfRef.__Vdly__error_206 = 1U;
                vlSelfRef.__Vdly__error_code_207 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_code;
            } else {
                vlSelfRef.__Vdly__error_206 = 0U;
                vlSelfRef.__Vdly__error_code_207 = 0x80U;
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
                 & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__first_fault)) 
                    | (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_reason_214 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_code;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_frame_212 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_stage_213 
                    = vlSelfRef.stage;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_generation_211 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_address_216 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_detail_215 
                    = ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))
                        ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code)
                        : ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))
                            ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code)
                            : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code)));
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
        } else {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                                vlSelfRef.__Vdly__error_206 = 0U;
                                vlSelfRef.__Vdly__error_code_207 = 0U;
                                if (((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                       | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                          <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                      | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                     | (0x0000c000U 
                                        < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))) {
                                    vlSelfRef.__Vdly__error_206 = 1U;
                                    vlSelfRef.__Vdly__error_code_207 = 1U;
                                    if ((1U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__first_fault)) 
                                               | (6U 
                                                  == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))))) {
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_reason_214 = 1U;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_frame_212 = 0xffffffffU;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_stage_213 = 0U;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_generation_211 
                                            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_address_216 = 0U;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_detail_215 = 0U;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if ((((((((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)) 
                                        & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                                       & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending))) 
                                      & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending))) 
                                     & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending))) 
                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory_drained)) 
                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__cache_worker_drained)) 
                                  & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested)) 
                                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged))) 
                                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active)))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
                            }
                        } else if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__software_ack_valid) 
                                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready)) 
                                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ack_match)) 
                                    & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__)) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
                        }
                    } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
                        }
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                 >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                            if ((1U & (~ ((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                            | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                               <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                           | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                          | (0x0000c000U 
                                             < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__command_issued_182 = 0U;
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__start_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__active) 
                    & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error) 
                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 0U;
        } else {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 1U;
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__result_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__canonical__result_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__complete_rows_262 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_identity_199 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__read_identity_bank_201 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_held_166 
                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear)
                    ? 0ULL : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_sample);
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__q_expected_index_203 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_index_597 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__presented_637 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__wanted_u_stage_642 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__descriptor_ready))) {
            if ((1U & (~ ((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation) 
                              | (2U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                                 [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot])) 
                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation)) 
                            | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                               [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                               != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id)) 
                           | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot]))) 
                          | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid) 
                             & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation 
                                 <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation) 
                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id 
                                   <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_valid_633 = 1U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_valid_633 = 0U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__address_pending) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_context_706 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__upload_valid) {
            if ((1U & (~ (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_ready) 
                             & (1U <= (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__upload_count))) 
                            & (4U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__upload_count))) 
                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__within_packet)) 
                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__upload_count) 
                             <= (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity)))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (2U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT____Vcellinp__staging__seal_valid) {
            if ((1U & (~ ((((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__state)) 
                            & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_count))) 
                           & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__written_bytes 
                              == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                          & ((~ vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__crc) 
                             == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__expected_crc))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (4U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__sealed_valid)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (8U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__pending_826 = 0U;
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_address) 
                  >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes) 
                 | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_generation 
                    != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (0x00000010U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__release_packet) {
            if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__active) 
                            & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__read_pending))) 
                           & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_valid))) 
                          & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__req_valid) 
                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_req_ready))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (0x00000020U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT____Vcellinp__staging__discard_valid) {
            if ((1U & (~ ((((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__state)) 
                            | (2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__state))) 
                           & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_count))) 
                          & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__upload_valid)))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846 
                    = (0x00000040U | vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults_846);
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__outstanding))) {
            if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_address) 
                   != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_address)) 
                  | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_generation 
                     != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_generation)) 
                 | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_sequence 
                    != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_sequence))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__identity_fault_830 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_valid) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__outstanding)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__identity_fault_830 = 1U;
        }
        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done) {
                                __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_139 
                                    = ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error)
                                        ? 0x8000000eU
                                        : 0U);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 
                                    = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_139;
                                __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_140 
                                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__completed_words;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 
                                    = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_140;
                            }
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)))) {
                        if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
                            __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_141 
                                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__setup_legal)
                                    ? 0U : 0x8000000dU);
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 
                                = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_141;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                        }
                    }
                } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p1_rsp_valid) {
                        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_address) 
                               != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_address)) 
                              | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_generation 
                                 != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation)) 
                             | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_sequence 
                                != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__pending_sequence))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x8000000cU;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                        } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_byte))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                            __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_146 
                                = (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_data) 
                                    << 0x00000018U) 
                                   | (0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_word));
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 
                                = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_146;
                        }
                    }
                } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_packet)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x8000000bU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_soft) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                        }
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x8000000aU;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                    }
                } else if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_identity) {
                    if (((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                    } else if (((0x0aU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000007U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                }
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_valid) {
                    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_159 
                        = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_error)
                            ? 0x80000009U : 0U);
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 
                        = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__status_159;
                    __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_160 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_data;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 
                        = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_160;
                }
            } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_aux)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000008U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
            }
        } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
            if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_identity) {
                        if (((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                        } else if (((0x0aU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                        }
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000007U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                }
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 
                    = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))
                        ? ((1U & ((~ (IData)(vlSelfRef.busy)) 
                                  | (9U <= (IData)(vlSelfRef.stage))))
                            ? 0x80000006U : 0U) : ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_discard)
                                                    ? 0U
                                                    : 0x80000005U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
            }
        } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_start) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_ready) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000004U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_seal) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0U;
                __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_184 
                    = (~ vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__crc);
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 
                    = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_184;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 = 0x80000003U;
                __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_186 
                    = (~ vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__crc);
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 
                    = __Vtask_dy71_platform_sim__DOT__control_plane__DOT__finish__data_186;
            }
        } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_status_769 
                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_begin)
                    ? 0U : 0x80000002U);
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__ack_data_770 = 0U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__aborted_205 = 0U;
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                                if ((1U & (~ ((((0ULL 
                                                 == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                                | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                                   <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                               | (0U 
                                                  == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                              | (0x0000c000U 
                                                 < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__arrived_at_217 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
                                }
                            }
                        }
                    }
                }
            }
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__committed_at_220 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
                                if ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__bank_cache_186 
                                        = (((~ ((IData)(1U) 
                                                << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                                            & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__bank_cache_186)) 
                                           | (7U & 
                                              ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot) 
                                               << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))));
                                }
                            }
                        }
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__result_valid) 
                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
                                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_match) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error)))) {
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_good_180 = 1U;
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__prepared_at_219 
                                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
                                    }
                                }
                            }
                        }
                    }
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if ((((((((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)) 
                                        & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                                       & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending))) 
                                      & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending))) 
                                     & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending))) 
                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory_drained)) 
                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__cache_worker_drained)) 
                                  & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested)) 
                                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged))) 
                                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active)))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__aborted_205 = 1U;
                            }
                        }
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                 >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                            if ((1U & (~ ((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                            | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                               <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                           | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                          | (0x0000c000U 
                                             < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__committed_at_220 = 0ULL;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_good_180 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__prepared_at_219 = 0ULL;
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_black_658 
                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__invalid_line) 
                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_fault
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot]);
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_fault_659 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_fault_659 = 1U;
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__valid) 
               >> 4U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active)) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__bad_pixel_tag))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_fault_659 = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_prepare_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_ready))) {
            if (((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation) 
                     | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation 
                        <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__latest_generation)) 
                    | (0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) 
                   | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                  | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                 | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot]))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_abort_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_abort_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_frame_625 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_frame;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_generation_624 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_generation;
            }
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__descriptor_ready))) {
            if ((1U & ((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation) 
                           | (2U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                              [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot])) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation)) 
                         | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                            [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id)) 
                        | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid
                                     [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot]))) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid) 
                          & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation 
                              <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation) 
                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id 
                                <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id)))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_req_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__invalid_line) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__valid) 
               >> 4U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active)) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__bad_pixel_tag))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
        }
        if (((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__next_cookie) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__fatal_dma)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_rejected) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_valid) {
            if ((1U & (~ (((((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight)) 
                             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_context) 
                                != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot))) 
                            | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_generation 
                               != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_generation)) 
                           | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_frame_id 
                              != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_frame)) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_cookie 
                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_cookie))))) {
                if ((1U & (~ (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending) 
                               | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__incoming_abort)) 
                              & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front)))))) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error) 
                         | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front) {
                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active) 
                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot) 
                                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot)))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_fault_659 = 1U;
                            }
                        }
                    }
                }
            }
            if ((1U & (((((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight)) 
                          | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_context) 
                             != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot))) 
                         | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_generation 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_generation)) 
                        | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_frame_id 
                           != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_frame)) 
                       | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_cookie 
                          != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_cookie)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_fail_reason_621 = 0x81U;
                }
            } else if ((1U & (~ (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending) 
                                  | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__incoming_abort)) 
                                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front)))))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__error_638 = 1U;
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_fail_reason_621 
                            = (0x40U | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason));
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__ref_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_rsp_ready))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[0U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[0U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[1U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[1U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[2U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[2U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[3U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[3U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[4U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[4U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[5U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[5U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[6U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[6U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[7U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[7U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[8U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[8U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[9U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[9U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[10U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[10U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[11U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[11U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[12U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[12U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[13U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[13U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[14U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[14U];
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_pixels_253[15U] 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels[15U];
            }
        }
    }
    if ((1U & (~ (IData)(vlSelfRef.rst)))) {
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending) 
             & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__ack_sync) 
                       >> 1U)) != (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__ack_seen)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem_884[0U] 
                = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[0U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem_884[1U] 
                = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[1U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem_884[2U] 
                = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[2U];
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                  >> 5U)))) {
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            if (VL_LTS_III(32, 
                                                           ((IData)(1U) 
                                                            + 
                                                            (((2U 
                                                               >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                               ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                                              [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                               : 0U) 
                                                             + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value)), 
                                                           ((2U 
                                                             >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                             ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits
                                                            [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                             : 0U))) {
                                                if (
                                                    (0x5fU 
                                                     >= 
                                                     (0x0000007fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                         << 5U)))) {
                                                    VL_ASSIGNSEL_WI(96, 32, 
                                                                    (0x0000007fU 
                                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                                        << 5U)), vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index_storage_519, 
                                                                    ((IData)(1U) 
                                                                     + 
                                                                     (((2U 
                                                                        >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                                        ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                                                       [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                                        : 0U) 
                                                                      + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value)));
                                                }
                                            }
                                        }
                                    } else if ((1U 
                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((0U == 
                                             ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                               ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left
                                              [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                               : 0U))) {
                                            if ((0x5fU 
                                                 >= 
                                                 (0x0000007fU 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                     << 5U)))) {
                                                VL_ASSIGNSEL_WI(96, 32, 
                                                                (0x0000007fU 
                                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                                    << 5U)), vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index_storage_519, 
                                                                ((2U 
                                                                  >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                                  ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits
                                                                 [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                                  : 0U));
                                            }
                                        }
                                    } else if ((0x5fU 
                                                >= 
                                                (0x0000007fU 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                    << 5U)))) {
                                        VL_ASSIGNSEL_WI(96, 32, 
                                                        (0x0000007fU 
                                                         & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band) 
                                                            << 5U)), vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index_storage_519, 0xffffffffU);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if ((1U & (~ ((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))))) {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__dequant__in_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__in_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__chroma_413 
                        = (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__scale_code_414 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scale_code;
                }
            }
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag4_717 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag3;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_ldqm_54 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)
                                                  ? 
                                                 (1U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask) 
                                                     >> 
                                                     (0x0000000fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_beat) 
                                                         << 1U))))
                                                  : 0U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_udqm_55 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)
                                                  ? 
                                                 (1U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask) 
                                                     >> 
                                                     (0x0000000fU 
                                                      & ((IData)(1U) 
                                                         + 
                                                         ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_beat) 
                                                          << 1U)))))
                                                  : 0U));
    if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__request_address_808 
            = (0x00ffffffU & ((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank))
                                 ? 0x00100000U : ((1U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank))
                                                   ? 0x00500000U
                                                   : 0x00900000U)) 
                               + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset)) 
                              + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__index)));
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_context_stage_742 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot;
    if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud_hit))) {
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCond_5 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud3;
    } else {
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red4;
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_2__clip 
            = (VL_GTS_III(32, 0U, VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456)))
                ? 0U : (VL_LTS_III(32, 0x000000ffU, 
                                   VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456)))
                         ? 0x000000ffU : (0x000000ffU 
                                          & (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_456))));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green4;
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_3__clip 
            = (VL_GTS_III(32, 0U, VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457)))
                ? 0U : (VL_LTS_III(32, 0x000000ffU, 
                                   VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457)))
                         ? 0x000000ffU : (0x000000ffU 
                                          & (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_457))));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue4;
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_4__clip 
            = (VL_GTS_III(32, 0U, VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458)))
                ? 0U : (VL_LTS_III(32, 0x000000ffU, 
                                   VL_EXTENDS_II(32,11, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458)))
                         ? 0x000000ffU : (0x000000ffU 
                                          & (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__clip__n_458))));
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCond_5 
            = ((0x0000f800U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_2__clip) 
                               << 8U)) | ((0x000007e0U 
                                           & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_3__clip) 
                                              << 3U)) 
                                          | (0x0000001fU 
                                             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_4__clip) 
                                                >> 3U))));
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__rgb5_740 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCond_5;
    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__dequant__in_valid) 
         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__in_ready))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xfeU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | (0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[0U] 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[1U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[2U]) 
                         | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[3U])));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xfdU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[4U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[5U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[6U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[7U])) 
                  << 1U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xfbU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[8U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[9U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[10U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[11U])) 
                  << 2U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xf7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[12U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[13U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[14U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[15U])) 
                  << 3U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xefU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[16U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[17U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[18U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[19U])) 
                  << 4U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xdfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[20U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[21U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[22U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[23U])) 
                  << 5U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0xbfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[24U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[25U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[26U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[27U])) 
                  << 6U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378 
            = ((0x7fU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__zero_group_378)) 
               | ((0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[28U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[29U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[30U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[31U])) 
                  << 7U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[0U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[1U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[2U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[3U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_240[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xfeU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_0__bad_eight));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[4U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[5U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[6U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[7U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_242[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xfdU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_1__bad_eight) 
                  << 1U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[8U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[9U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[10U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[11U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_244[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xfbU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_2__bad_eight) 
                  << 2U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[12U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[13U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[14U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[15U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_246[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xf7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_3__bad_eight) 
                  << 3U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[16U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[17U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[18U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[19U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_248[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xefU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_4__bad_eight) 
                  << 4U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[20U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[21U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[22U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[23U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_250[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xdfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_5__bad_eight) 
                  << 5U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[24U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[25U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[26U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[27U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_252[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0xbfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_6__bad_eight) 
                  << 6U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[28U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[29U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[30U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[31U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 0U;
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[0U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[0U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[0U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[1U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[1U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[1U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[1U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[2U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[2U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[2U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[2U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[3U])) 
             | VL_LTS_III(16, 0x0800U, (0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[3U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_GTS_III(16, 0xf800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[3U] 
                                      >> 0x00000010U)) 
             | VL_LTS_III(16, 0x0800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_eight__tile_254[3U] 
                                        >> 0x00000010U)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377 
            = ((0x7fU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__bad_group_377)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT____VlemCall_7__bad_eight) 
                  << 7U));
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__d2_hold_89 = 1U;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__data_out__DOT__d2_hold_57 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__15__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__data_out__DOT__d2_hold_59 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__14__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__data_out__DOT__d2_hold_61 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__13__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__data_out__DOT__d2_hold_63 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__12__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__data_out__DOT__d2_hold_65 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__11__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__data_out__DOT__d2_hold_67 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__10__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__data_out__DOT__d2_hold_69 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__9__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__data_out__DOT__d2_hold_71 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__8__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__data_out__DOT__d2_hold_73 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__7__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__data_out__DOT__d2_hold_75 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__6__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__data_out__DOT__d2_hold_77 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__5__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__data_out__DOT__d2_hold_79 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__4__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__data_out__DOT__d2_hold_81 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__3__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__data_out__DOT__d2_hold_83 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__2__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__data_out__DOT__d2_hold_85 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__1__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__data_out__DOT__d2_hold_87 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__0__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__d2_hold_91 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__d2_hold_93 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__d2_hold_95 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__d2_hold_97 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__d2_hold_99 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__d2_hold_101 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__d2_hold_103 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__d2_hold_105 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__d2_hold_107 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__d2_hold_109 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__d2_hold_111 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__d2_hold_113 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__d2_hold_115 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__d2_hold_117 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__d2_hold_119 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__d2_hold_121 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__cke0_33 
        = (1U & (~ (IData)(vlSelfRef.rst)));
}

void Vdy71_platform_sim___024root___act_comb__TOP__1(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_comb__TOP__1\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignVec__TOP.addForce(0U, 7U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignVec__TOP.release(0U, 7U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignVec__TOP.addForce(0U, 3U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignVec__TOP.release(0U, 3U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignVec__TOP.addForce(0U, 7U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopa_out_VassignVec__TOP.release(0U, 7U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignVec__TOP.addForce(0U, 3U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dopb_out_VassignVec__TOP.release(0U, 3U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.addForce(0U, 0U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP), (CData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.release(0U, 0U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.addForce(0U, 0U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP), (CData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.release(0U, 0U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.addForce(0U, 8U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP), (SData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.release(0U, 8U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.addForce(0U, 0U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignRHS0__TOP), (CData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dbiterr_out_VassignVec__TOP.release(0U, 0U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.addForce(0U, 0U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignRHS0__TOP), (CData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__sbiterr_out_VassignVec__TOP.release(0U, 0U);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.addForce(0U, 8U, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out 
            = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignRHS0__TOP), (SData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out)));
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__rdaddrecc_out_VassignVec__TOP.release(0U, 8U);
    }
}

VlCoroutine Vdy71_platform_sim___024root___act_hybrid__TOP__0____Vfork_1__0(Vdy71_platform_sim___024root* vlSelf);

void Vdy71_platform_sim___024root___act_hybrid__TOP__0(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_hybrid__TOP__0\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__Q) 
          != (IData)(vlSelfRef.__VassignWtmp_0)) || 
         ((1U & (~ (IData)(vlSymsp->__Vm_didInit))) 
          && (IData)(vlSelfRef.__VstlFirstIteration)))) {
        Vdy71_platform_sim___024root___act_hybrid__TOP__0____Vfork_1__0(vlSelf);
    }
}

VlCoroutine Vdy71_platform_sim___024root___act_hybrid__TOP__0____Vfork_1__0(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_hybrid__TOP__0____Vfork_1__0\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    QData/*63:0*/ __VassignWgen_0__local;
    __VassignWgen_0__local = 0;
    vlSelfRef.__VassignWgen_0 = ((QData)((IData)(1U)) 
                                 + vlSelfRef.__VassignWgen_0);
    __VassignWgen_0__local = vlSelfRef.__VassignWgen_0;
    vlSelfRef.__Vintraval_hea18e606__0 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__Q;
    vlSelfRef.__VassignWtmp_0 = vlSelfRef.__Vintraval_hea18e606__0;
    co_await vlSelfRef.__VdlySched.delay(0x00000000000002f5ULL, 
                                         nullptr, "/mnt/c/moon/dev/experiments/stb1-real-rust-system-20261108/support/model-verilator.sv", 
                                         10);
    if ((vlSelfRef.__VassignWgen_0 == __VassignWgen_0__local)) {
        vlSelfRef.dy71_platform_sim__DOT__model__DOT__device_clock 
            = vlSelfRef.__Vintraval_hea18e606__0;
    }
    co_return;
}

void Vdy71_platform_sim___024root___act_sequent__TOP__10(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__10\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux 
        = ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__cascade_a) 
             >> 1U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__addra_in_15_reg))
            ? (0xfffffffffffffffeULL & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux)
            : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP), (QData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out))));
}

void Vdy71_platform_sim___024root___act_sequent__TOP__11(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__11\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux 
        = ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__cascade_a) 
             >> 1U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__addra_in_15_reg))
            ? (0xfffffffffffffffeULL & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux)
            : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP), (QData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out))));
}

void Vdy71_platform_sim___024root___act_sequent__TOP__12(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__12\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux 
        = ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__cascade_b) 
             >> 1U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__addrb_in_15_reg))
            ? (0xfffffffffffffffeULL & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux)
            : (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP), (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out))))));
}

void Vdy71_platform_sim___024root___act_sequent__TOP__13(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__13\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux 
        = ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__cascade_b) 
             >> 1U) & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__addrb_in_15_reg))
            ? (0xfffffffffffffffeULL & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux)
            : (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.read(
                                                                                ((void)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP), (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out))))));
}

extern const VlWide<16>/*511:0*/ Vdy71_platform_sim__ConstPool__CONST_8;
extern const VlUnpacked<SData/*15:0*/, 8> Vdy71_platform_sim__ConstPool__TABLE_4;

void Vdy71_platform_sim___024root___act_sequent__TOP__14(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__14\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vtemp_1;
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out_919 
        = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__selected_rgb;
    if ((0x01dfU >= (0x000001ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x) 
                                    - (IData)(0x000eU))))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read0_887 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__bank0
            [(0x000001ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x) 
                             - (IData)(0x000eU)))];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read1_888 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__bank1
            [(0x000001ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x) 
                             - (IData)(0x000eU)))];
    } else {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read0_887 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read1_888 = 0U;
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_content_896 
        = ((IData)(vlSelfRef.pixel_reset_n) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__active) 
                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__canvas)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_pattern_898 
        = ((IData)(vlSelfRef.pixel_reset_n) && (1U 
                                                & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync) 
                                                   >> 1U)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_odd_899 
        = ((IData)(vlSelfRef.pixel_reset_n) && (1U 
                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y)));
    __Vtemp_1 = VL_MATCHMASKED_I(32, VL_DIV_III(32, 
                                                ((0x000003ffU 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y) 
                                                     - (IData)(0x0018U))) 
                                                 - (IData)(0x00000028U)), (IData)(0x0000005aU)), Vdy71_platform_sim__ConstPool__CONST_8);
    if (vlSelfRef.pixel_reset_n) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_sync_921 
            = ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_sync) 
                      << 1U)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_token));
        if (((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_sync) 
                    >> 1U)) != (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_seen))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_seen_924 
                = (1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_sync) 
                         >> 1U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame_925 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__collect_926 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927 = 0U;
        } else {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__frame_start))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame_925 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__collect_926 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927 = 0U;
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__collect) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__frame_start))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927 = 0U;
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__collect) 
                 & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__hit)))) {
                if ((0x0fU == ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__mask) 
                               | (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__hit)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__collect_926 = 0U;
                }
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927 
                    = ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__mask) 
                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__hit));
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync_892 
            = (2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync) 
                     << 1U));
        if ((0x021cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x_900 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y_901 
                = ((0x0341U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))
                    ? 0U : (0x000003ffU & ((IData)(1U) 
                                           + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))));
        } else {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x_900 
                = (0x000003ffU & ((IData)(1U) + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)));
        }
        if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_toggle_908 
                = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_toggle)));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0) 
             & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0) 
                       >> 1U)) == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0_902 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1) 
             & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1) 
                       >> 1U)) == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1_905 = 0U;
        }
        if ((((((0x01eeU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)) 
                & (0x003eU <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))) 
               & (0x030eU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))) 
              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync) 
                 >> 1U)) & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync) 
                               >> 1U)))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1_913 
                        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1)));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1_905 = 1U;
                }
            }
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y)))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0_916 
                        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0)));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0_902 = 1U;
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync_891 
            = ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync) 
                      << 1U)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync_922 
            = ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync) 
                      << 1U)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1_890 
            = ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1) 
                      << 1U)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done1));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0_889 
            = ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0) 
                      << 1U)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done0));
        if ((((((((0x000eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)) 
                  & (0x0018U <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))) 
                 & (0x0338U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y))) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__canvas)) 
               & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync) 
                  >> 1U)) & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync) 
                                >> 1U))) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_good)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_count_910 
                = ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_count);
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_pixel_912 
            = Vdy71_platform_sim__ConstPool__TABLE_4
            [__Vtemp_1];
        vlSelfRef.__Vdly__physical_y_886 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y;
        vlSelfRef.__Vdly__physical_x_885 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x;
    } else {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_sync_921 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_seen_924 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync_892 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x_900 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame_925 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y_901 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__collect_926 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_toggle_908 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1_913 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0_916 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0_902 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1_905 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync_891 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync_922 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1_890 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0_889 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_count_910 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_pixel_912 = 0U;
        vlSelfRef.__Vdly__physical_y_886 = 0U;
        vlSelfRef.__Vdly__physical_x_885 = 0U;
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__de_out_920 
        = ((IData)(vlSelfRef.pixel_reset_n) && (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__data_enable));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_good_897 
        = ((IData)(vlSelfRef.pixel_reset_n) && (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_good));
}

void Vdy71_platform_sim___024root___act_sequent__TOP__16(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__16\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__chunk_bytes_869 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__chunk_bytes;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fifo_q_857 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fifo_q;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_hud_671 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_hud;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_addr_18 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_addr;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__tile_base_156 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__tile_base;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_addr_29 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_addr;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_addr_25 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_addr;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__read_wait_42 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__read_wait;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__previous_dc_496 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__previous_dc;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__selected_read_bank_299 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__selected_read_bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__message_bytes_268 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__message_bytes;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_carry_reg_296 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_carry_reg;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_sum_reg_295 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_sum_reg;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape_481 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__d_282 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__d;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__h_286 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__h;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_chunk_523 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_chunk;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__width_432 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__width;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_672 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bank_673 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__generation_814 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__frame_815 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__frame;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_access_allowed_12 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_access_allowed;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_coefficient_490 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_coefficient;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset_479 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_stream_459 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_stream;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_code_465 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_code;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_address_460 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_address;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_boundary_467 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_boundary;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[4U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[4U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[5U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[5U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[6U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[6U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[7U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[7U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[8U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[8U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[9U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[9U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[10U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[10U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[11U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[11U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[12U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[12U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[13U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[13U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[14U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[14U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[15U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile[15U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_valid_324 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_data_30 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_data;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy_complete_244 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy_complete;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_written_245 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_written;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_write_index_228 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_write_index;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[4U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[4U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[5U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[5U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[6U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[6U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[7U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending[7U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_error_627 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_accepted_543 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_accepted;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_good_179 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_good;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_written_178 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_written;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_good_177 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_good;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair23_448 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair23;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix1_507 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix2_508 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix3_509 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix3;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__1__KET___353 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__2__KET___354 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__2__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__3__KET___355 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__3__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__4__KET___356 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__5__KET___357 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__5__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__6__KET___358 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__6__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__7__KET___359 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__7__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__0__KET___352 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__0__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__3__KET___800 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__3__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag3_716 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag3;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8_226 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__invalidated_877 
        = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__invalidated;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame_878 
        = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_frame_763 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_frame;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask_45 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_length_160 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_length;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_offset_159 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_offset;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid_162 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__is_write_41 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__is_write;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u_632 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_owner_7 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_owner;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync1_710 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_bank_540 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done_320 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_generation_762 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset_819 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank_818 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_532 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_sample_165 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_sample;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear_168 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid_167 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scale_code_247 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scale_code;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer_702 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity_844 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__expected_crc_840 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__expected_crc;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud3_722 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud3;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red4_737 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red4;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue4_739 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue4;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green4_738 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green4;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot_660 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending_195 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending_198 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_pending_778 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending_197 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged_183 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active_657 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_rejected_685 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_rejected;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_valid_754 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__cpu_word_795 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_word;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__0__KET___599 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__0__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_tag_252 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_tag;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__1__KET___601 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__2__KET___603 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__2__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code_548 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code_255 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern_873 
        = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done1_694 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done0_693 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done0;
}

extern const VlWide<8>/*255:0*/ Vdy71_platform_sim__ConstPool__CONST_0;
extern const VlUnpacked<IData/*23:0*/, 4> Vdy71_platform_sim__ConstPool__TABLE_1;

void Vdy71_platform_sim___024root___act_sequent__TOP__17(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__17\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*1:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__canonical_base__bank_13;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__canonical_base__bank_13 = 0;
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127);
    VlWide<5>/*159:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129;
    VL_ZERO_W(160, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129);
    CData/*1:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_low__which_band_263;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_low__which_band_263 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412 = 0;
    IData/*23:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__Vfuncout_413;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__Vfuncout_413 = 0;
    CData/*1:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__kind_414;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__kind_414 = 0;
    CData/*6:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__group_415;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__group_415 = 0;
    CData/*1:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__bank_416;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__bank_416 = 0;
    IData/*23:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start____VlefCall_0__canonical_base_417;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start____VlefCall_0__canonical_base_417 = 0;
    IData/*23:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__Vfuncout_418;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__Vfuncout_418 = 0;
    CData/*1:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__bank_419;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__bank_419 = 0;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420 = 0;
    IData/*31:0*/ __Vtemp_1;
    IData/*31:0*/ __Vtemp_37;
    IData/*31:0*/ __VExpandSel_WordIdx_2;
    IData/*31:0*/ __VExpandSel_LoShift_2;
    CData/*0:0*/ __VExpandSel_Aligned_2;
    IData/*31:0*/ __VExpandSel_HiShift_2;
    IData/*31:0*/ __VExpandSel_HiMask_2;
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__Q_88 = 0U;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__data_out__DOT__Q_56 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__15__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__data_out__DOT__Q_58 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__14__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__data_out__DOT__Q_60 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__13__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__data_out__DOT__Q_62 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__12__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__data_out__DOT__Q_64 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__11__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__data_out__DOT__Q_66 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__10__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__data_out__DOT__Q_68 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__9__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__data_out__DOT__Q_70 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__8__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__data_out__DOT__Q_72 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__7__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__data_out__DOT__Q_74 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__6__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__data_out__DOT__Q_76 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__5__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__data_out__DOT__Q_78 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__4__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__data_out__DOT__Q_80 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__3__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__data_out__DOT__Q_82 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__2__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__data_out__DOT__Q_84 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__1__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__data_out__DOT__Q_86 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT____Vcellinp__dq_io__BRA__0__KET____DOT__data_out__D1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q_90 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q_92 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q_94 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q_96 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q_98 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q_100 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q_102 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q_104 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q_106 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q_108 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q_110 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q_112 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q_114 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q_116 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q_118 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q_120 
        = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_cycle)));
    if ((1U & (~ (IData)(vlSelfRef.rst)))) {
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                          >> 2U)))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                        if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_rsp_valid) 
                              & (~ (IData)(vlSelfRef.rst))) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error) 
                                          >> 2U)))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[0U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_data[2U][0U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[1U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_data[2U][1U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[2U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_data[2U][2U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__payload_686[3U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_data[2U][3U];
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__start_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bad_last)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                        if (((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state)) 
                               & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full) 
                                  >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__process_bank))) 
                              & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending))) 
                             | ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state)) 
                                & (0x2fU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__round_index))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_carry_reg_296 
                                = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_csa 
                                           >> 0x20U));
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_sum_reg_295 
                                = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__schedule_csa);
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_chunk_523 
                                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_chunk
                                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream];
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix1_507 
                                                = ((IData)(0x0000002aU) 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[0U]);
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix2_508 
                                                = ((IData)(0x0000002aU) 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair01);
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_prefix3_509 
                                                = ((IData)(0x0000002aU) 
                                                   + 
                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair01 
                                                    + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[2U]));
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
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__chunk_bytes_869 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_hud_671 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_addr_18 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__tile_base_156 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_addr_29 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_addr_25 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__read_wait_42 = 5U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__previous_dc_496 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__message_bytes_268 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape_481 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__d_282 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__h_286 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_672 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bank_673 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__generation_814 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__frame_815 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_access_allowed_12 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_coefficient_490 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset_479 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_stream_459 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_code_465 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_address_460 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_boundary_467 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_data_30 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy_complete_244 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_written_245 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_error_627 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_accepted_543 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_good_179 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_written_178 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_good_177 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__3__KET___800 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8_226 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__invalidated_877 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame_878 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_frame_763 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask_45 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_length_160 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_offset_159 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid_162 = 0xffffffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__is_write_41 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u_632 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_owner_7 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync1_710 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_bank_540 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done_320 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_generation_762 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset_819 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank_818 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_532 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear_168 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid_167 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scale_code_247 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer_702 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity_844 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__expected_crc_840 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot_660 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending_195 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending_198 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_pending_778 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending_197 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged_183 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active_657 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__cpu_word_795 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__0__KET___599 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase_610 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y_611 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk_612 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset_613 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_base_614 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_generation_615 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_frame_id_616 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot_617 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 = 0U;
        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1517 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_tag_252 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__1__KET___601 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__2__KET___603 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code_548 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code_255 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern_873 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done1_694 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done0_693 = 0U;
    } else {
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__begin_packet) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__blocked)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__chunk_bytes_869 = 0U;
            }
            if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__begin_ready) 
                   & (0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation)) 
                  & (0U != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__)) 
                 & (0x0000c000U >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity_844 
                    = ((4U <= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__)
                        ? 4U : (7U & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__expected_crc_840 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__;
            }
        }
        if (vlSelfRef.bus_write) {
            if ((0x0720U != (IData)(vlSelfRef.bus_address))) {
                if ((0x0724U != (IData)(vlSelfRef.bus_address))) {
                    if ((0x0728U != (IData)(vlSelfRef.bus_address))) {
                        if ((0x072cU != (IData)(vlSelfRef.bus_address))) {
                            if ((0x0730U == (IData)(vlSelfRef.bus_address))) {
                                if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__setup_legal) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__chunk_bytes_869 
                                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_bytes;
                                }
                            }
                        }
                    }
                }
            }
            if ((0x0720U == (IData)(vlSelfRef.bus_address))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862 
                    = ((0xffffffff00000000ULL & vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862) 
                       | (IData)((IData)(vlSelfRef.bus_wdata)));
            } else if ((0x0724U == (IData)(vlSelfRef.bus_address))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862 
                    = ((0x00000000ffffffffULL & vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation_862) 
                       | ((QData)((IData)(vlSelfRef.bus_wdata)) 
                          << 0x00000020U));
            }
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__3__KET___800 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[3U];
                    if ((1U & (~ ((((((((1U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata)) 
                                        | (2U == (0x000000ffU 
                                                  & vlSelfRef.bus_wdata))) 
                                       | (3U == (0x000000ffU 
                                                 & vlSelfRef.bus_wdata))) 
                                      | (4U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata))) 
                                     | (5U == (0x000000ffU 
                                               & vlSelfRef.bus_wdata))) 
                                    | (6U == (0x000000ffU 
                                              & vlSelfRef.bus_wdata))) 
                                   | (0x10U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata))) 
                                  | ((0x11U == (0x000000ffU 
                                                & vlSelfRef.bus_wdata)) 
                                     || (0x12U == (0x000000ffU 
                                                   & vlSelfRef.bus_wdata))))))) {
                        if ((0x13U != (0x000000ffU 
                                       & vlSelfRef.bus_wdata))) {
                            if ((0x14U != (0x000000ffU 
                                           & vlSelfRef.bus_wdata))) {
                                if ((0x16U != (0x000000ffU 
                                               & vlSelfRef.bus_wdata))) {
                                    if ((0x17U != (0x000000ffU 
                                                   & vlSelfRef.bus_wdata))) {
                                        if ((0x15U 
                                             == (0x000000ffU 
                                                 & vlSelfRef.bus_wdata))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__cpu_word_795 = 0U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_hud_671 
                                = (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_kind));
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__kind_672 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_kind;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bank_673 
                                = (1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_active)
                                          ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group)
                                          : ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                             | ((2U 
                                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                                | (6U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase))))));
                        }
                    }
                }
            }
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 7U;
                    }
                } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 6U;
                    }
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 6U;
                    }
                } else if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_rsp_valid) 
                             & (~ (IData)(vlSelfRef.rst))) 
                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending))) {
                    if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 2U;
                    }
                }
            } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 0U;
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bad_command) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 1U;
                    }
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
                if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)) 
                     | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready)))) {
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__canonical_base__bank_13 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_bank;
                    __Vtemp_1 = VL_MATCHMASKED_I(32, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__canonical_base__bank_13), Vdy71_platform_sim__ConstPool__CONST_0);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT____VlemCall_0__canonical_base 
                        = Vdy71_platform_sim__ConstPool__TABLE_1
                        [__Vtemp_1];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__tile_base_156 
                        = (0x00ffffffU & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT____VlemCall_0__canonical_base 
                                           + ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_plane))
                                               ? 0U
                                               : ((1U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_plane))
                                                   ? 0x0002a300U
                                                   : 0x00034bc0U))) 
                                          + (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__chosen_index 
                                             << 5U)));
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__m_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__aux_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_addr_29 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_address;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_data_30 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_data;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__lcd_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_addr_25 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__source;
        }
        if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid) {
                    VL_ASSIGNSEL_WI(128, 16, (0x0000007fU 
                                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__beat) 
                                                 << 4U)), vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_data);
                }
            }
        } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__mem_req_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__request_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[0U] = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[1U] = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[2U] = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__read_payload_139[3U] = 0U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))) {
            if ((0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 = 0U;
            }
        } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bad_tile) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 = 0U;
        } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__active) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_busy) {
                if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_row))) {
                    if (((0x0000007fU & ((IData)(1U) 
                                         + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__tile_column))) 
                         == ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_plane))
                              ? 0x5aU : 0x2dU))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 
                            = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305) 
                               | (3U & ((IData)(1U) 
                                        << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__fill_bank))));
                    }
                }
            }
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__prefix_pending)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__cache_valid) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__data_valid) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__data_ready))) {
                        if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_byte))) {
                            if (((0x000003ffU & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_word))) 
                                 == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_words
                                 [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank])) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305 
                                    = ((~ ((IData)(1U) 
                                           << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank))) 
                                       & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_full_305));
                            }
                        }
                    }
                }
            }
        }
        if (((((((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)) 
                   | (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                  | (2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                 | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                | (4U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
               | (5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
              | (0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
             | (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)))) {
            if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((3U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                if ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    if ((0x02eeU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__refresh_count))) {
                                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__mem_req_valid) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__read_wait_42 = 4U;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__burst_mask_45 
                                                = (0x0000ffffU 
                                                   & ((0U 
                                                       == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))
                                                       ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_mask)
                                                       : 
                                                      ((3U 
                                                        == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner))
                                                        ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_mask)
                                                        : 
                                                       (~ 
                                                        VL_SHIFTL_III(16,16,32, (IData)(3U), 
                                                                      (vlSelfRef.__Vdfg_Regularize_15015 
                                                                       << 1U))))));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__is_write_41 
                                                = (1U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing) 
                                                      >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner)));
                                        }
                                    }
                                }
                                if ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                    if ((0x0eU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39 
                                            = ((~ ((IData)(1U) 
                                                   << 
                                                   (3U 
                                                    & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                                                       >> 0x16U)))) 
                                               & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39));
                                    }
                                }
                            }
                        }
                    }
                }
                if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 2U;
                } else if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 
                        = ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__init_refs))
                            ? 3U : 2U);
                } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 5U;
                } else if ((4U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((0x0eU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 7U;
                        }
                    }
                }
            }
        } else if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 8U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39 
                = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39) 
                   | (0x0fU & ((IData)(1U) << (3U & 
                                               (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address 
                                                >> 0x16U)))));
        } else if ((8U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
            if ((0x0bU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__write_beat))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 5U;
                }
            } else if ((9U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((0x0aU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((0x0cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 0x0dU;
                    } else if ((0x0dU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__next_state_35 = 5U;
                    }
                }
            }
            if ((0x0bU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((9U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((0x0aU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((0x0cU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__open_39 = 0U;
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                              >> 6U)))) {
                    if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            if ((1U 
                                                 & (~ 
                                                    (VL_GTS_III(32, 0xfffff800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__dc_prediction) 
                                                     | VL_LTS_III(32, 0x00000800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__dc_prediction))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__previous_dc_496 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__dc_prediction;
                                            }
                                        }
                                    }
                                }
                            }
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                            __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_low__which_band_263 
                                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot;
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_13__band_low 
                                                = (
                                                   (0U 
                                                    == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_low__which_band_263))
                                                    ? 1U
                                                    : 
                                                   ((1U 
                                                     == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_low__which_band_263))
                                                     ? 6U
                                                     : 0x15U));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_coefficient_490 
                                                = (0x0000003fU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_13__band_low) 
                                                      + 
                                                      (((2U 
                                                         >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot))
                                                         ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot]
                                                         : 0U) 
                                                       - vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_base)));
                                        }
                                    }
                                }
                            }
                        }
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                            if ((0x8000U 
                                                 > 
                                                 (0x0000ffffU 
                                                  & (IData)(
                                                            (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                             >> 
                                                             (0x0000003fU 
                                                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                 << 4U))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset_479 = 0U;
                                            } else if (
                                                       (0x8000U 
                                                        <= 
                                                        (0x0000ffffU 
                                                         & (IData)(
                                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                    >> 
                                                                    (0x0000003fU 
                                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                        << 4U))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset_479 = 0x8000U;
                                            } else if (
                                                       ((0x4000U 
                                                         <= 
                                                         (0x0000ffffU 
                                                          & (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                     >> 
                                                                     (0x0000003fU 
                                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                         << 4U)))))) 
                                                        & (0xc000U 
                                                           > 
                                                           (0x0000ffffU 
                                                            & (IData)(
                                                                      (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                                       >> 
                                                                       (0x0000003fU 
                                                                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                           << 4U)))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__renorm_offset_479 = 0x4000U;
                                            }
                                        }
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            if ((1U 
                                                 & (~ 
                                                    ((((0x58U 
                                                        <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arithmetic_context)) 
                                                       | ((0x0000ffffU 
                                                           & (IData)(
                                                                     (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                      >> 
                                                                      (0x0000003fU 
                                                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                          << 4U))))) 
                                                          >= 
                                                          (0x0000ffffU 
                                                           & (IData)(
                                                                     (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                                      >> 
                                                                      (0x0000003fU 
                                                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                          << 4U))))))) 
                                                      | ((0x0000ffffU 
                                                          & (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                                     >> 
                                                                     (0x0000003fU 
                                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                         << 4U))))) 
                                                         < 
                                                         (0x0000ffffU 
                                                          & (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                     >> 
                                                                     (0x0000003fU 
                                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                         << 4U))))))) 
                                                     | ((0x0000ffffU 
                                                         & (IData)(
                                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                                    >> 
                                                                    (0x0000003fU 
                                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                        << 4U))))) 
                                                        > 
                                                        (0x0000ffffU 
                                                         & (IData)(
                                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                                    >> 
                                                                    (0x0000003fU 
                                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                        << 4U)))))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_stream_459 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_code_465 
                                                    = 
                                                    (0x0000ffffU 
                                                     & (IData)(
                                                               (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                                >> 
                                                                (0x0000003fU 
                                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                    << 4U)))));
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_address_460 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__probability_address;
                                            }
                                        }
                                    }
                                }
                            }
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_boundary_467 
                                                = (0x0000ffffU 
                                                   & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_low) 
                                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_partition)) 
                                                      - (IData)(1U)));
                                        }
                                    }
                                }
                            }
                        }
                    } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                         >> 4U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 3U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 2U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 1U)))) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) {
                                            if ((1U 
                                                 & (~ 
                                                    (((((((((5U 
                                                             != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                                                            & (6U 
                                                               != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))) 
                                                           | (0x002eU 
                                                              > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                                                          | (0xc000U 
                                                             < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                                                         | (0U 
                                                            == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                                                        | (0x00001fa4U 
                                                           < vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                                                       | (0U 
                                                          == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                                                      | (0x0100U 
                                                         < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                                                     | ((6U 
                                                         == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                                                        & (1U 
                                                           != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__previous_dc_496 = 0U;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                  >> 5U)))) {
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            if ((1U 
                                                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_mode)))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape_481 = 0x0eU;
                                            }
                                        }
                                    }
                                } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                        if (VL_LTS_III(32, 
                                                       ((IData)(1U) 
                                                        + 
                                                        (((2U 
                                                           >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                           ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                                          [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                           : 0U) 
                                                         + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value)), 
                                                       ((2U 
                                                         >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                         ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits
                                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                         : 0U))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape_481 = 0x0cU;
                                        }
                                    }
                                } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((0U != ((2U 
                                                 >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                 ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left
                                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                 : 0U))) {
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_escape_481 = 0x18U;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (((0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__setup_legal) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__generation_814 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__frame_815 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__2__KET__;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset_819 
                    = (0x00007fffU & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__);
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bank_818 
                    = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_bank;
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_prepare_valid) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_pending)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_access_allowed_12 = 1U;
        }
        if ((1U & (((~ (IData)(vlSelfRef.busy)) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort)) 
                   | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_drain_valid) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready)) 
                       & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation 
                          == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation)) 
                      & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__2__KET__ 
                         == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid))))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__hud_access_allowed_12 = 0U;
        }
        if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
                        & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                       & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__done) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy_complete_244 = 1U;
                            }
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                          >> 3U)))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_complete) {
                                                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_tile) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_written_245 = 1U;
                                                }
                                            }
                                        }
                                    }
                                }
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts)))) {
                                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_valid) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_pending))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scale_code_247 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_code;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__plane_cfg_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane_cfg_ready))) {
                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__next_plane) 
                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy_complete_244 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_written_245 = 0U;
                            }
                        }
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_error_627 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_accepted_543 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_drain_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_match) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_drain_checked) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_written_178 = 1U;
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_match) {
                if ((1U & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__4__KET__)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_good_177 = 1U;
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8_226 
                = (8U <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_plus1);
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__invalidated_877 = 1U;
            }
        }
        if (((IData)(vlSelfRef.bus_write) & (0x0384U 
                                             == (IData)(vlSelfRef.bus_address)))) {
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet) 
                  & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending))) 
                 & (1U == vlSelfRef.bus_wdata))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__invalidated_877 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame_878 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id;
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT____Vcellinp__prepare_adapter__descriptor_accepted)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_abort_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_abort_ready))))) {
                if ((1U & (~ ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__state)) 
                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_done))))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__result_valid) 
                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_prepare_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_frame_763 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_generation_762 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__payload_start_clear) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid_162 = 0xffffffffU;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_non_hud)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_length_160 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_bytes;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_offset_159 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_addr;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__rid_162 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[0U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag[0U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[1U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag[1U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[2U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag[2U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_expected_157[3U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag[3U];
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u_632 = 0U;
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid) {
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1530 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
                vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1531 = 1U;
            }
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1532 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_slot;
            vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1533 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_choice_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_owner_7 = 0U;
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_sync1_710 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_gray;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done_320 = 0U;
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort)))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__start_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__start_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__message_bytes_268 = 0x0007e904U;
            }
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__start_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bad_last)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_valid) 
                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__result_ready))))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                            if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending))))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__d_282 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__3__KET__;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__h_286 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__7__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__d_282 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__c;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__h_286 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__g;
                            }
                        }
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bad_tile)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__active) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__prefix_pending)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__cache_valid) {
                                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__data_valid) 
                                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__data_ready))) {
                                    if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_byte))) {
                                        if (((0x000003ffU 
                                              & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_word))) 
                                             == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_words
                                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank])) {
                                            if ((1U 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last) 
                                                    >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank)))) {
                                                if (
                                                    (0x0007e903U 
                                                     == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__emitted_bytes)) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__done_320 = 1U;
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
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear_168 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid_167 = 0U;
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_tag_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_good_179 = 1U;
                            }
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                            if ((1U & (~ ((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                            | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                               <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                           | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                          | (0x0000c000U 
                                             < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_good_179 = 0U;
                            }
                        }
                    }
                }
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                                if ((1U & (~ ((((0ULL 
                                                 == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                                | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                                   <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                               | (0U 
                                                  == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                              | (0x0000c000U 
                                                 < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_written_178 = 0U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_good_177 = 0U;
                                }
                            }
                        }
                    }
                }
            }
            if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                    if ((1U & (~ ((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                    | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                       <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                   | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                  | (0x0000c000U < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_clear_168 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid_167 = 1U;
                    }
                }
            } else if ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_tag_fire) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_pending_valid_167 = 1U;
                }
            }
        }
        if ((1U & (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__receiving)) 
                    & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_valid))) 
                   & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__address_pending))))) {
            if (((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_sync0) 
                        >> 1U)) != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__seen0))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer_702 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
            } else if (((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_sync1) 
                               >> 1U)) != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__seen1))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__captured_buffer_702 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
            }
        }
        if (((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__state)) 
             & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_count)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_capacity_844 
                = (((4U < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__remaining_bytes) 
                    | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__remaining_bytes))
                    ? 4U : (7U & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__remaining_bytes 
                                  - (IData)(1U))));
        }
        if (((0x0fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 0U;
            if ((1U & (((((0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                          | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured))) 
                         | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__command_matches))) 
                        | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed)) 
                       | ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read)) 
                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__packed_loaded) 
                             != (0x000000ffU & (((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                >> 1U))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 1U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_slot_660 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active_657 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_data_valid) {
            if ((0x01dfU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__emit_count))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_next_u_632 
                    = ((0x02cfU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_u))
                        ? 0U : (0x000003ffU & ((IData)(1U) 
                                               + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_u))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__render_active_657 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending_195 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_rsp_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_match) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_pending_195 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending_198 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_done_valid) 
             & (~ (IData)(vlSelfRef.rst)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_match) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__write_pending_198 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__software_command_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__software_command_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_pending_778 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                      >> 4U)))) {
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__can_soft) {
                                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__soft_pending_778 = 0U;
                                }
                            }
                        }
                    }
                }
                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p1_rsp_valid) {
                                if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_address) 
                                                != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_address)) 
                                               | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_generation 
                                                  != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_result_generation)) 
                                              | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_sequence 
                                                 != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__pending_sequence))))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__cpu_word_795 
                                        = (((~ ((IData)(0x000000ffU) 
                                                << 
                                                (0x0000001fU 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_byte) 
                                                    << 3U)))) 
                                            & vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__cpu_word_795) 
                                           | (0x00000000ffffffffULL 
                                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_data) 
                                                 << 
                                                 (0x0000001fU 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_byte) 
                                                     << 3U)))));
                                }
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending_197 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_rsp_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_match) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_pending_197 = 0U;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged_183 
                = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested)));
        } else if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                          >> 2U)))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__software_ack_valid) 
                               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready)) 
                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ack_match)) 
                             & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__)) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged_183 = 1U;
                        }
                    }
                }
            }
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                             >> 2U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire) {
                        if ((1U & (~ ((((0ULL == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation) 
                                        | (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                           <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__latest_generation)) 
                                       | (0U == vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)) 
                                      | (0x0000c000U 
                                         < vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_acknowledged_183 = 0U;
                        }
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 0U;
        if (((0x0fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            if ((1U & (((((0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                          | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured))) 
                         | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__command_matches))) 
                        | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed)) 
                       | ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read)) 
                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__packed_loaded) 
                             != (0x000000ffU & (((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                >> 1U))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 1U;
            }
        }
        if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 1U;
            }
        } else if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
            if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT____Vcellinp__bulk__rsp_valid) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__hud_aux_rsp_error) 
                         | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__failed))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 1U;
                    } else if ((((IData)(1U) + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__index)) 
                                == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__error_825 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__done_824 = 1U;
                    }
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
                      & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                              >> 6U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                  >> 5U)))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__0__KET___599 
                                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__1__KET___601 
                                                = (0x0000ffffU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0) 
                                                      + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_y)));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__plane_start__BRA__2__KET___603 
                                                = (0x0000ffffU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0) 
                                                      + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_yu)));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_rsp_valid) 
             & (~ (IData)(vlSelfRef.rst)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 3U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting) 
                          | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match))))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 4U;
                } else if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_reason_684 = 4U;
                }
            }
        }
        if ((((~ ((IData)(vlSelfRef.__Vdfg_Regularize_14957) 
                  | ((IData)(vlSelfRef.__Vdfg_Regularize_14956) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__incoming_abort)))) 
              & (IData)(vlSelfRef.__Vdfg_Regularize_14983)) 
             & ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__state)) 
                & ((IData)(vlSelfRef.__Vdfg_Regularize_14976) 
                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_result_ready))))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_prepare_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_generation_615 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_frame_id_616 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot_617 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 = 0U;
            if (((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation) 
                     | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation 
                        <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__latest_generation)) 
                    | (0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) 
                   | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                  | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                 | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot]))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 = 1U;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase_610 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y_611 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk_612 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset_613 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_base_614 = 0U;
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1518 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
                vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1519 = 1U;
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1520 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1521 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid_1522 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_abort_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_abort_ready))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_error_627 = 1U;
            }
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held) 
                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot) 
                        == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 0U;
                }
            }
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending) 
               & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight))) 
              & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_active)))) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held) 
                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot) 
                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 0U;
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 = 0U;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1523 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot;
            vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1524 = 1U;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1525 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1526 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid_1527 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__descriptor_ready))) {
            if ((1U & (~ ((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation) 
                              | (2U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                                 [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot])) 
                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation)) 
                            | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                               [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot] 
                               != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id)) 
                           | (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot]))) 
                          | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid) 
                             & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation 
                                 <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation) 
                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id 
                                   <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id))))))) {
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1528 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot;
                vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1529 = 1U;
            }
        }
        if ((((((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid) 
                  & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_active))) 
                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__fatal_dma))) 
                & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_fault
                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot]))) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_needed)) 
              & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_hazard))) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now)))) {
            if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_kind))) {
                vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1534 
                    = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_group));
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1535 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
                vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1536 = 1U;
            } else {
                vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1537 
                    = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_group));
                vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1538 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
                vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1539 = 1U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_valid) {
            if ((1U & (~ (((((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight)) 
                             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_context) 
                                != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot))) 
                            | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_generation 
                               != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_generation)) 
                           | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_frame_id 
                              != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_frame)) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_cookie 
                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_cookie))))) {
                if ((1U & (~ (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending) 
                               | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__incoming_abort)) 
                              & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front)))))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error) 
                                  | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted))))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front) {
                            if (((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_chunk)) 
                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_tile_y) 
                                    == ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_kind))
                                         ? 0x0000003bU
                                         : 0x0000001dU)))) {
                                if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_kind))) {
                                    vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1540 
                                        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group));
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1541 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1542 = 1U;
                                    vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1543 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1544 
                                        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group));
                                    vlSelfRef.__Vdly_Dim1__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1545 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot;
                                } else if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_kind))) {
                                    vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1546 
                                        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group));
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1547 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1548 = 1U;
                                    vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1549 
                                        = (0x0000003fU 
                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group));
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1550 
                                        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group));
                                    vlSelfRef.__Vdly_Dim1__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1551 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot;
                                }
                            }
                        } else {
                            __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_4__phase_kind 
                                = ((0U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404))
                                    ? 3U : ((2U >= (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404))
                                             ? 0U : 
                                            (((3U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404)) 
                                              | (5U 
                                                 == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_404)))
                                              ? 1U : 2U)));
                            if ((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                  & (0x5278U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset))) 
                                 | (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                     & (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk))) 
                                    & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y) 
                                       == ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_4__phase_kind))
                                            ? 0x0000003bU
                                            : 0x0000001dU))))) {
                                if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase))) {
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid_1552 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid_1553 = 1U;
                                }
                                if (((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                     | (2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)))) {
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_5__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_405)));
                                    vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1554 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_5__phase_group;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1555 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1556 = 1U;
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_6__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_406)));
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_7__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_407)));
                                    vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1557 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_6__phase_group;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1558 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_7__phase_group;
                                    vlSelfRef.__Vdly_Dim1__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1559 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_tag_1560 = 1U;
                                }
                                if (((4U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)) 
                                     | (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)))) {
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_8__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_408)));
                                    vlSelfRef.__Vdly_Lsb__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1561 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_8__phase_group;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1562 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1563 = 1U;
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_9__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_409)));
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_10__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_410)));
                                    vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1564 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_9__phase_group;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1565 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_10__phase_group;
                                    vlSelfRef.__Vdly_Dim1__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1566 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_tag_1567 = 1U;
                                }
                                if ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 = 0U;
                                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1568 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1569 = 1U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 1U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_generation_615 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot];
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_frame_id_616 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot];
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot_617 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 = 0U;
                                } else {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase_610 
                                        = (7U & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)));
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411 
                                        = (7U & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)));
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y_611 = 0U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk_612 = 0U;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset_613 = 0U;
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_11__phase_kind 
                                        = ((0U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411))
                                            ? 3U : 
                                           ((2U >= (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411))
                                             ? 0U : 
                                            (((3U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411)) 
                                              | (5U 
                                                 == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_411)))
                                              ? 1U : 2U)));
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412 
                                        = (7U & ((IData)(1U) 
                                                 + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase)));
                                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_12__phase_group 
                                        = (((2U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412)) 
                                            | (5U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412))) 
                                           | (6U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_group__phase_412)));
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__bank_416 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_canonical
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot];
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__group_415 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_12__phase_group;
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__kind_414 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_11__phase_kind;
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__bank_419 
                                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__bank_416;
                                    __Vtemp_37 = VL_MATCHMASKED_I(32, (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__bank_419), Vdy71_platform_sim__ConstPool__CONST_0);
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__Vfuncout_418 
                                        = Vdy71_platform_sim__ConstPool__TABLE_1
                                        [__Vtemp_37];
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start____VlefCall_0__canonical_base_417 
                                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__canonical_base__Vfuncout_418;
                                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__Vfuncout_413 
                                        = (0x00ffffffU 
                                           & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start____VlefCall_0__canonical_base_417 
                                               + ((0U 
                                                   == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__kind_414))
                                                   ? 0U
                                                   : 
                                                  ((1U 
                                                    == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__kind_414))
                                                    ? 0x0002a300U
                                                    : 0x00034bc0U))) 
                                              + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__group_415) 
                                                 << 5U)));
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_base_614 
                                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__page_start__Vfuncout_413;
                                }
                            } else if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset_613 
                                    = (0x00007fffU 
                                       & ((IData)(8U) 
                                          + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_hud_offset)));
                            } else if ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y_611 
                                    = (0x0000003fU 
                                       & ((IData)(1U) 
                                          + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_y)));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_phase;
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_13__phase_kind 
                                    = ((0U == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420))
                                        ? 3U : ((2U 
                                                 >= (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420))
                                                 ? 0U
                                                 : 
                                                (((3U 
                                                   == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420)) 
                                                  | (5U 
                                                     == (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__phase_kind__phase_420)))
                                                  ? 1U
                                                  : 2U)));
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk_612 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_base_614 
                                    = (0x00ffffffU 
                                       & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_tile_base 
                                          + ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT____VlemCall_13__phase_kind))
                                              ? 0x00000b40U
                                              : 0x000005a0U)));
                            } else {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk_612 
                                    = (3U & ((IData)(1U) 
                                             + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_chunk)));
                            }
                        }
                    }
                }
            }
        }
        if ((((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_fail) 
                & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight))) 
               & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) 
              & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_active))) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_active_609 = 0U;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1570 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
            vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state_1571 = 1U;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__y_valid_1572 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__c_valid_1573 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__hud_valid_1574 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__result_held_608 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_generation_615 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_frame_id_616 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_cache_slot_617 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepared_error_618 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p3_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[0U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data[0U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[1U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data[1U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[2U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data[2U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_data_141[3U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data[3U];
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_ready))) {
            __VExpandSel_WordIdx_2 = (0x0000000fU & 
                                      (VL_MULS_III(32, (IData)(0x00000010U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_index)) 
                                       >> 5U));
            __VExpandSel_LoShift_2 = (0x0000001fU & 
                                      VL_MULS_III(32, (IData)(0x00000010U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_index)));
            __VExpandSel_Aligned_2 = (0U == __VExpandSel_LoShift_2);
            if (__VExpandSel_Aligned_2) {
                __VExpandSel_HiShift_2 = 0U;
                __VExpandSel_HiMask_2 = 0U;
            } else {
                __VExpandSel_HiShift_2 = ((IData)(0x00000020U) 
                                          - __VExpandSel_LoShift_2);
                __VExpandSel_HiMask_2 = 0xffffffffU;
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[0U] 
                = (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                     [((IData)(1U) + __VExpandSel_WordIdx_2)] 
                     << __VExpandSel_HiShift_2) & __VExpandSel_HiMask_2) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                      [__VExpandSel_WordIdx_2] >> __VExpandSel_LoShift_2));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[1U] 
                = (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                     [((IData)(2U) + __VExpandSel_WordIdx_2)] 
                     << __VExpandSel_HiShift_2) & __VExpandSel_HiMask_2) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                      [((IData)(1U) + __VExpandSel_WordIdx_2)] 
                      >> __VExpandSel_LoShift_2));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[2U] 
                = (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                     [((IData)(3U) + __VExpandSel_WordIdx_2)] 
                     << __VExpandSel_HiShift_2) & __VExpandSel_HiMask_2) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                      [((IData)(2U) + __VExpandSel_WordIdx_2)] 
                      >> __VExpandSel_LoShift_2));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_data_143[3U] 
                = (((((0x0000000cU <= __VExpandSel_WordIdx_2)
                       ? 0U : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                      [((IData)(4U) + __VExpandSel_WordIdx_2)]) 
                     << __VExpandSel_HiShift_2) & __VExpandSel_HiMask_2) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels
                      [((IData)(3U) + __VExpandSel_WordIdx_2)] 
                      >> __VExpandSel_LoShift_2));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__ref_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_rsp_ready))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_ref_tag_252 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__ref_rsp_tile;
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code_548 = 0U;
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))))) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_ready))) {
                        if ((1U & (~ (((0xffffffffU 
                                        == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id) 
                                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid) 
                                          & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id 
                                             <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))) 
                                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key) 
                                         & (0xffffffffU 
                                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)))))) {
                            if ((1U & (~ ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)) 
                                          & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid)) 
                                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id 
                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id)))))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__begin_accepted_543 = 1U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_532 
                                    = vlSelfRef.reference_bank;
                            }
                        }
                        if ((((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id) 
                              | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid) 
                                 & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id 
                                    <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))) 
                             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key) 
                                & (0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code_548 = 1U;
                        } else if ((1U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)) 
                                          & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid)) 
                                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id 
                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code_548 = 2U;
                        }
                    }
                }
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_bank_540 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank;
                }
            }
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
               & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
              & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
             | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code_255 
                    = (((IData)(vlSelfRef.__Vdfg_Regularize_14995)
                         ? 0x61U : ((IData)(vlSelfRef.__Vdfg_Regularize_14999)
                                     ? (0x10U | (0x0fU 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code)))
                                     : ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error)
                                         ? (0x20U | 
                                            (0x0fU 
                                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error_code)))
                                         : ((IData)(vlSelfRef.__Vdfg_Regularize_14998)
                                             ? 0x31U
                                             : ((IData)(vlSelfRef.__Vdfg_Regularize_14997)
                                                 ? 0x32U
                                                 : 
                                                ((IData)(vlSelfRef.__Vdfg_Regularize_14920)
                                                  ? 0x33U
                                                  : 
                                                 ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__error)
                                                   ? 
                                                  ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error)
                                                    ? 
                                                   (0x40U 
                                                    | (0x0fU 
                                                       & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code)))
                                                    : 
                                                   (0x40U 
                                                    | (0x0fU 
                                                       & ((0x80U 
                                                           | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_code)) 
                                                          & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error)))))))
                                                   : 
                                                  (0x50U 
                                                   & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_14994))))))))))) 
                       & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_14883))));
            }
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                             >> 3U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__plane_cfg_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane_cfg_ready))) {
                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__next_plane) 
                                 != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code_255 = 1U;
                            }
                        }
                    } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code_255 = 0U;
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.bus_write) & (0x0380U 
                                             == (IData)(vlSelfRef.bus_address)))) {
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet) 
                  & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending))) 
                 & (1U >= vlSelfRef.bus_wdata))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern_873 
                    = (1U & vlSelfRef.bus_wdata);
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__receiving) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_data_valid))) {
            if ((0x01dfU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__fill))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__selected) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done1_694 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__seen1;
                }
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__selected)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done0_693 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__seen0;
                }
            }
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fifo_q_857 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fifo
        [vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__rp];
    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_enable) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__selected_read_bank_299 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__ram_read_bank;
    }
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__width_432 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_valid_324 = 0U;
    } else {
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__cfg_ready))) {
            if ((1U & (~ (((2U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane)) 
                           | ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                              & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks 
                             != ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                                  ? ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                                      ? 0x00001418U
                                      : 0x00001518U)
                                  : ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                                      ? 0x00000533U
                                      : 0x00000546U))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__width_432 
                    = ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                        ? 0x5aU : 0x2dU);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__slot_ready) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_valid_324 
                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__reconstruct__in_valid) 
                   & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key) 
                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)) 
                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received)));
        }
    }
    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_busy)))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[0U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[1U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[2U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[3U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[4U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[5U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[5U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[6U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[6U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[7U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[7U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[8U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[8U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[9U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[9U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[10U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[10U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[11U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[11U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[12U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[12U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[13U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[13U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[14U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[14U];
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__captured_tile_300[15U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[15U];
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_write_index_228 
        = (7U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[1U] 
        = (IData)((((QData)((IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count 
                                     >> 0x20U))) << 0x00000020U) 
                   | (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[2U] 
        = (IData)(((((QData)((IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count 
                                      >> 0x20U))) << 0x00000020U) 
                    | (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count))) 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[3U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_generation);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[4U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_generation 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[5U] 
        = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_presented)
            ? vlSelfRef.front_frame_id : ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire)
                                           ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id
                                           : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid 
                                              | (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__start_fire))))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[6U] 
        = (IData)((((QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address)) 
                    << 0x00000020U) | (QData)((IData)(
                                                      ((((IData)(vlSelfRef.stage) 
                                                         << 0x00000018U) 
                                                        | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_code) 
                                                           << 0x00000010U)) 
                                                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_code) 
                                                          << 8U))))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_record_pending_227[7U] 
        = (IData)(((((QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address)) 
                     << 0x00000020U) | (QData)((IData)(
                                                       ((((IData)(vlSelfRef.stage) 
                                                          << 0x00000018U) 
                                                         | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_code) 
                                                            << 0x00000010U)) 
                                                        | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_code) 
                                                           << 8U))))) 
                   >> 0x00000020U));
    if ((1U & (~ ((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))))) {
        if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__1__KET___353 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__1__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__1__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__2__KET___354 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__2__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__2__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__3__KET___355 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__3__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__3__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__4__KET___356 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__4__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__4__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__5__KET___357 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__5__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__5__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__6__KET___358 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__6__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__6__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__7__KET___359 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__7__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__7__KET__)))));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__0__KET___352 
                            = (0x0000003fffffffffULL 
                               & VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                                  & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__0__KET__)), 
                                             (0x0000003fffffffffULL 
                                              & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__0__KET__)))));
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__1__KET___353 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__1__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__1__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__2__KET___354 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__2__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__2__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__3__KET___355 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__3__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__3__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__4__KET___356 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__4__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__4__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__5__KET___357 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__5__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__5__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__6__KET___358 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__6__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__6__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__7__KET___359 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__7__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__7__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__0__KET___352 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__0__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__0__KET__)))));
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__1__KET___353 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__1__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__1__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__2__KET___354 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__2__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__2__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__3__KET___355 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__3__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__3__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__4__KET___356 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__4__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__4__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__5__KET___357 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__5__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__5__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__6__KET___358 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__6__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__6__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__7__KET___359 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__7__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__7__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__products__BRA__0__KET___352 
                        = (0x0000003fffffffffULL & 
                           VL_MULS_QQQ(38, (0x0000003fffffffffULL 
                                            & VL_EXTENDS_QI(38,24, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__0__KET__)), 
                                       (0x0000003fffffffffULL 
                                        & VL_EXTENDS_QI(38,14, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__0__KET__)))));
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                      >> 3U)))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                        if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 = 0ULL;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 = 0ULL;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__0__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__0__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__1__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__1__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__2__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__2__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__3__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__3__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__4__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__4__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__5__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__5__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__6__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__6__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__7__KET__;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__7__KET__;
                        }
                    }
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                    if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 = 0ULL;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 = 0ULL;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__0__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__0__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__1__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__1__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__2__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__2__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__3__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__3__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__4__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__4__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__5__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__5__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__6__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__6__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_odd__BRA__7__KET__;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__next_even__BRA__7__KET__;
                    }
                }
            } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__inverse__in_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__in_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__0__KET___362 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__0__KET___361 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__1__KET___364 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__1__KET___363 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__2__KET___366 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__2__KET___365 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__3__KET___368 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__3__KET___367 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__4__KET___370 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__4__KET___369 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__5__KET___372 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__5__KET___371 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__6__KET___374 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__6__KET___373 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__odd_sum__BRA__7__KET___376 = 0ULL;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__even_sum__BRA__7__KET___375 = 0ULL;
                }
            }
        }
    }
    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__inverse__in_valid) 
         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__in_ready))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xfeU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | (0U == ((((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[1U] 
                              << 0x0000000cU) | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[0U] 
                                                 >> 0x00000014U)) 
                            | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[2U] 
                                << 0x0000000cU) | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[1U] 
                                                   >> 0x00000014U))) 
                           | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[3U] 
                               << 0x0000000cU) | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[2U] 
                                                  >> 0x00000014U))) 
                          | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[4U] 
                              << 0x0000000cU) | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[3U] 
                                                 >> 0x00000014U))) 
                         | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[4U] 
                            >> 0x00000014U))));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xfdU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[5U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[6U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[7U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[8U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[9U])) 
                  << 1U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xfbU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[10U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[11U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[12U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[13U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[14U])) 
                  << 2U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xf7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[15U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[16U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[17U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[18U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[19U])) 
                  << 3U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xefU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[20U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[21U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[22U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[23U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[24U])) 
                  << 4U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xdfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[25U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[26U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[27U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[28U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[29U])) 
                  << 5U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0xbfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[30U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[31U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[32U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[33U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[34U])) 
                  << 6U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330 
            = ((0x7fU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__ac_zero_group_330)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[35U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[36U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[37U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[38U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[39U])) 
                  << 7U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xfeU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | (0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[0U] 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[1U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[2U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[3U]) 
                         | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[4U])));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xfdU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[5U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[6U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[7U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[8U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[9U])) 
                  << 1U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xfbU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[10U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[11U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[12U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[13U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[14U])) 
                  << 2U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xf7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[15U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[16U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[17U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[18U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[19U])) 
                  << 3U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xefU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[20U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[21U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[22U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[23U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[24U])) 
                  << 4U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xdfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[25U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[26U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[27U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[28U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[29U])) 
                  << 5U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0xbfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[30U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[31U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[32U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[33U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[34U])) 
                  << 6U));
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329 
            = ((0x7fU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__zero_group_329)) 
               | ((0U == ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[35U] 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[36U]) 
                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[37U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[38U]) 
                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[39U])) 
                  << 7U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[0U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[1U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[2U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[3U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[4U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_115[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xfeU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_0__bad_eight));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[5U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[6U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[7U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[8U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[9U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_117[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xfdU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_1__bad_eight) 
                  << 1U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[10U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[11U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[12U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[13U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[14U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_119[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xfbU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_2__bad_eight) 
                  << 2U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[15U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[16U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[17U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[18U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[19U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_121[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xf7U & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_3__bad_eight) 
                  << 3U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[20U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[21U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[22U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[23U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[24U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_123[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xefU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_4__bad_eight) 
                  << 4U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[25U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[26U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[27U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[28U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[29U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_125[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xdfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_5__bad_eight) 
                  << 5U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[30U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[31U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[32U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[33U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[34U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_127[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0xbfU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_6__bad_eight) 
                  << 6U));
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[0U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[35U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[36U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[2U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[37U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[38U];
        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[4U] 
            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized[39U];
        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 0U;
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[0U])) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[0U])))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                              << 0x0000000cU) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[0U] 
                                                >> 0x00000014U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                                << 0x0000000cU) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[0U] 
                                                  >> 0x00000014U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                             >> 8U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                               >> 8U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[2U] 
                                              << 4U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                                >> 0x0000001cU)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[2U] 
                                                << 4U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[1U] 
                                                  >> 0x0000001cU)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                              << 0x00000010U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[2U] 
                                                >> 0x00000010U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                                << 0x00000010U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[2U] 
                                                  >> 0x00000010U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                             >> 4U))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                               >> 4U))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (0x000fffffU 
                                          & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[4U] 
                                              << 8U) 
                                             | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                                >> 0x00000018U)))) 
             | VL_GTS_III(20, 0x00080800U, (0x000fffffU 
                                            & ((__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[4U] 
                                                << 8U) 
                                               | (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[3U] 
                                                  >> 0x00000018U)))))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        if ((VL_LTS_III(20, 0x0007f800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[4U] 
                                          >> 0x0000000cU)) 
             | VL_GTS_III(20, 0x00080800U, (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_eight__tile_129[4U] 
                                            >> 0x0000000cU)))) {
            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight = 1U;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328 
            = ((0x7fU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__bad_group_328)) 
               | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_7__bad_eight) 
                  << 7U));
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag3_716 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at_sample_165 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__clock_count;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud3_722 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red4_737 
        = (0x000007ffU & ((0x0007ffffU & VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y3))) 
                          + (0x0007ffffU & VL_SHIFTRS_III(19,19,32, 
                                                          (0x0007ffffU 
                                                           & ((IData)(0x00000080U) 
                                                              + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red3)), 8U))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue4_739 
        = (0x000007ffU & ((0x0007ffffU & VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y3))) 
                          + (0x0007ffffU & VL_SHIFTRS_III(19,19,32, 
                                                          (0x0007ffffU 
                                                           & ((IData)(0x00000080U) 
                                                              + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue3)), 8U))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green4_738 
        = (0x000007ffU & ((0x0007ffffU & VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y3))) 
                          - (0x0007ffffU & VL_SHIFTRS_III(19,19,32, 
                                                          (0x0007ffffU 
                                                           & ((IData)(0x00000080U) 
                                                              + 
                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green_cb3 
                                                               + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green_cr3))), 8U))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_rejected_685 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_abort_valid) 
                                                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_valid_754 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_valid_stage));
}

void Vdy71_platform_sim___024root___act_comb__TOP__2(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_comb__TOP__2\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP = 0ULL;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.addForce(0U, 0x0000003fU, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.release(0U, 0x0000003fU);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP = 0ULL;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.addForce(0U, 0x0000003fU, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_VassignVec__TOP.release(0U, 0x0000003fU);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.addForce(0U, 0x0000001fU, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.release(0U, 0x0000001fU);
    }
    if (vlSelfRef.dy71_platform_sim__DOT__glbl__DOT__GSR_int) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP = 0U;
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.addForce(0U, 0x0000001fU, 
                                                                                &(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignRHS0__TOP), 0U);
    } else {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_VassignVec__TOP.release(0U, 0x0000001fU);
    }
}

void Vdy71_platform_sim___024root___act_comb__TOP__3(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_comb__TOP__3\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vdfg_Regularize_14846 = (((0x0700U 
                                           <= (IData)(vlSelfRef.bus_address)) 
                                          & (0x0730U 
                                             >= (IData)(vlSelfRef.bus_address)))
                                          ? ((0x0700U 
                                              == (IData)(vlSelfRef.bus_address))
                                              ? 0x53544231U
                                              : ((0x0704U 
                                                  == (IData)(vlSelfRef.bus_address))
                                                  ? 0x00010000U
                                                  : 
                                                 ((0x0708U 
                                                   == (IData)(vlSelfRef.bus_address))
                                                   ? 
                                                  ((((IData)(vlSelfRef.transport_fault) 
                                                     << 4U) 
                                                    | (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__blocked) 
                                                        << 3U) 
                                                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fence_ready) 
                                                          << 2U))) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__armed) 
                                                       << 1U) 
                                                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fault)))
                                                   : 
                                                  ((0x070cU 
                                                    == (IData)(vlSelfRef.bus_address))
                                                    ? 
                                                   (0x00000100U 
                                                    & (- (IData)(
                                                                 ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fence_ready) 
                                                                  & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__armed)) 
                                                                     & (IData)(vlSelfRef.__Vdfg_Regularize_14974))))))
                                                    : 
                                                   ((0x0710U 
                                                     == (IData)(vlSelfRef.bus_address))
                                                     ? 
                                                    (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__written_bytes 
                                                     & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fence_ready))))
                                                     : 
                                                    ((0x0714U 
                                                      == (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((~ vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__crc) 
                                                      & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__fence_ready))))
                                                      : 
                                                     ((0x0718U 
                                                       == (IData)(vlSelfRef.bus_address))
                                                       ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__ticket
                                                       : 
                                                      ((0x071cU 
                                                        == (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__rejected_words
                                                        : 
                                                       ((0x0720U 
                                                         == (IData)(vlSelfRef.bus_address))
                                                         ? (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation)
                                                         : 
                                                        ((0x0724U 
                                                          == (IData)(vlSelfRef.bus_address))
                                                          ? (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_generation 
                                                                     >> 0x00000020U))
                                                          : 
                                                         ((0x0728U 
                                                           == (IData)(vlSelfRef.bus_address))
                                                           ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_offset
                                                           : 
                                                          ((0x072cU 
                                                            == (IData)(vlSelfRef.bus_address))
                                                            ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_bytes
                                                            : 
                                                           ((- (IData)(
                                                                       (0x0730U 
                                                                        == (IData)(vlSelfRef.bus_address)))) 
                                                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__used))))))))))))))
                                          : (((0x0600U 
                                               == (IData)(vlSelfRef.bus_address))
                                               ? 0x48425531U
                                               : ((0x0604U 
                                                   == (IData)(vlSelfRef.bus_address))
                                                   ? 0x00010000U
                                                   : 
                                                  ((0x0608U 
                                                    == (IData)(vlSelfRef.bus_address))
                                                    ? 
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__fault) 
                                                      << 4U) 
                                                     | (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready) 
                                                         << 3U) 
                                                        | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read)) 
                                                            & ((0U 
                                                                != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                               & ((0x000000ffU 
                                                                   & (((IData)(1U) 
                                                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                                      >> 1U)) 
                                                                  == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__packed_loaded)))) 
                                                           << 2U))) 
                                                    | (((0U 
                                                         != (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)) 
                                                        << 1U) 
                                                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured)))
                                                    : 
                                                   ((0x060cU 
                                                     == (IData)(vlSelfRef.bus_address))
                                                     ? (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__packed_loaded)
                                                     : 
                                                    ((0x0610U 
                                                      == (IData)(vlSelfRef.bus_address))
                                                      ? (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__completed_words)
                                                      : 
                                                     ((0x0614U 
                                                       == (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count) 
                                                        << 0x00000010U) 
                                                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__offset))
                                                       : 
                                                      ((0x0618U 
                                                        == (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__ticket
                                                        : 
                                                       ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux) 
                                                          << 0x00000010U) 
                                                         | (0x0000ffffU 
                                                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__dob_out_mux))) 
                                                        & (- (IData)(
                                                                     ((IData)(vlSelfRef.__Vdfg_Regularize_14889) 
                                                                      & ((0U 
                                                                          == 
                                                                          (3U 
                                                                           & (IData)(vlSelfRef.bus_address))) 
                                                                         & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__result_ready) 
                                                                            & ((0x0000007fU 
                                                                                & ((IData)(vlSelfRef.bus_address) 
                                                                                >> 2U)) 
                                                                               < 
                                                                               (0x000000ffU 
                                                                                & (((IData)(1U) 
                                                                                + (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count)) 
                                                                                >> 1U)))))))))))))))) 
                                             & (- (IData)(
                                                          (((0x0600U 
                                                             <= (IData)(vlSelfRef.bus_address)) 
                                                            & (0x0618U 
                                                               >= (IData)(vlSelfRef.bus_address))) 
                                                           | (IData)(vlSelfRef.__Vdfg_Regularize_14889))))));
    vlSelfRef.bus_rdata = (((0x0380U <= (IData)(vlSelfRef.bus_address)) 
                            & (0x03acU >= (IData)(vlSelfRef.bus_address)))
                            ? ((0x0380U == (IData)(vlSelfRef.bus_address))
                                ? 0x4c443134U : ((0x0384U 
                                                  == (IData)(vlSelfRef.bus_address))
                                                  ? 
                                                 ((((IData)(vlSelfRef.dy71_platform_sim__DOT__observer_quiet) 
                                                    << 4U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_valid) 
                                                       << 3U) 
                                                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pending) 
                                                         << 2U))) 
                                                  | ((2U 
                                                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__applied_sync)) 
                                                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__requested_pattern)))
                                                  : 
                                                 ((0x0388U 
                                                   == (IData)(vlSelfRef.bus_address))
                                                   ? vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_sequence
                                                   : 
                                                  ((0x038cU 
                                                    == (IData)(vlSelfRef.bus_address))
                                                    ? vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_frame
                                                    : 
                                                   (((0x0390U 
                                                      == (IData)(vlSelfRef.bus_address)) 
                                                     | ((0x0394U 
                                                         == (IData)(vlSelfRef.bus_address)) 
                                                        | ((0x0398U 
                                                            == (IData)(vlSelfRef.bus_address)) 
                                                           | (0x039cU 
                                                              == (IData)(vlSelfRef.bus_address)))))
                                                     ? 
                                                    (0x00ffffffU 
                                                     & ((0x0390U 
                                                         == (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[0U]
                                                         : 
                                                        ((0x0394U 
                                                          == (IData)(vlSelfRef.bus_address))
                                                          ? 
                                                         ((vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[1U] 
                                                           << 8U) 
                                                          | (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[0U] 
                                                             >> 0x00000018U))
                                                          : 
                                                         ((0x0398U 
                                                           == (IData)(vlSelfRef.bus_address))
                                                           ? 
                                                          ((vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[2U] 
                                                            << 0x00000010U) 
                                                           | (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[1U] 
                                                              >> 0x00000010U))
                                                           : 
                                                          ((vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[2U] 
                                                            << 0x00000018U) 
                                                           | (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_mem[2U] 
                                                              >> 8U))))))
                                                     : 
                                                    ((0x03a0U 
                                                      == (IData)(vlSelfRef.bus_address))
                                                      ? vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__denied
                                                      : 
                                                     ((0x03a4U 
                                                       == (IData)(vlSelfRef.bus_address))
                                                       ? 0x00010000U
                                                       : 
                                                      ((0x03a8U 
                                                        == (IData)(vlSelfRef.bus_address))
                                                        ? 3U
                                                        : 
                                                       (0x0000000eU 
                                                        & (- (IData)(
                                                                     (0x03acU 
                                                                      == (IData)(vlSelfRef.bus_address)))))))))))))
                            : ((0x00000800U & (IData)(vlSelfRef.bus_address))
                                ? vlSelfRef.__Vdfg_Regularize_14846
                                : ((0x00000400U & (IData)(vlSelfRef.bus_address))
                                    ? vlSelfRef.__Vdfg_Regularize_14846
                                    : ((0x00000200U 
                                        & (IData)(vlSelfRef.bus_address))
                                        ? ((0x00000100U 
                                            & (IData)(vlSelfRef.bus_address))
                                            ? ((0x00000080U 
                                                & (IData)(vlSelfRef.bus_address))
                                                ? vlSelfRef.__Vdfg_Regularize_14846
                                                : (
                                                   (0x00000040U 
                                                    & (IData)(vlSelfRef.bus_address))
                                                    ? 
                                                   ((0x00000020U 
                                                     & (IData)(vlSelfRef.bus_address))
                                                     ? 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? vlSelfRef.__Vdfg_Regularize_14846
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? vlSelfRef.__Vdfg_Regularize_14846
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.__Vdfg_Regularize_14846
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.lcd_underruns)))))
                                                     : 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.rejected_count))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.presented_count)))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.accepted_count))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         (((IData)(vlSelfRef.error_code) 
                                                           << 9U) 
                                                          | (((IData)(vlSelfRef.stage) 
                                                              << 1U) 
                                                             | (IData)(vlSelfRef.busy)))))))
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? vlSelfRef.__Vdfg_Regularize_14846
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_ref))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_fid))))))
                                                    : 
                                                   ((0x00000020U 
                                                     & (IData)(vlSelfRef.bus_address))
                                                     ? 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_gen 
                                                                     >> 0x00000020U))))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_gen))))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_opcode)))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_ticket))))
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.__Vdfg_Regularize_14846
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_tag[0U])))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_tag[1U]))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_tag[2U])))))
                                                     : 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_tag[3U]))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_key) 
                                                           << 2U) 
                                                          | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_bank)))))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_length) 
                                                           << 0x00000010U) 
                                                          | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_offset))))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_ref))))
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_fid))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_gen 
                                                                     >> 0x00000020U)))))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_gen)))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_ticket))))))))
                                            : ((0x00000080U 
                                                & (IData)(vlSelfRef.bus_address))
                                                ? vlSelfRef.__Vdfg_Regularize_14846
                                                : (
                                                   (0x00000040U 
                                                    & (IData)(vlSelfRef.bus_address))
                                                    ? vlSelfRef.__Vdfg_Regularize_14846
                                                    : 
                                                   ((0x00000020U 
                                                     & (IData)(vlSelfRef.bus_address))
                                                     ? vlSelfRef.__Vdfg_Regularize_14846
                                                     : 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? vlSelfRef.__Vdfg_Regularize_14846
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? vlSelfRef.__Vdfg_Regularize_14846
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         ((0x00000200U 
                                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                           ? vlSelfRef.__Vdfg_Regularize_14847
                                                           : 
                                                          ((0x00000100U 
                                                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                            ? vlSelfRef.__Vdfg_Regularize_14847
                                                            : 
                                                           ((0x00000080U 
                                                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                             ? 
                                                            ((0x00000040U 
                                                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                              ? vlSelfRef.__Vdfg_Regularize_14847
                                                              : 
                                                             ((0x00000020U 
                                                               & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                               ? 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_detail) 
                                                                      << 0x00000018U) 
                                                                     | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code) 
                                                                        << 0x00000010U)) 
                                                                    | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__error_code) 
                                                                        << 8U) 
                                                                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__error_code)))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__read_bank_valid) 
                                                                      << 5U) 
                                                                     | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_committed) 
                                                                         << 4U) 
                                                                        | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborted) 
                                                                           << 3U))) 
                                                                    | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done) 
                                                                        << 2U) 
                                                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_last) 
                                                                           << 1U) 
                                                                          | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_valid))))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fid))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__0__KET__) 
                                                                     << 0x00000017U) 
                                                                    | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__1__KET__) 
                                                                        << 0x0000000eU) 
                                                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_blocks_w__BRA__2__KET__) 
                                                                           << 5U) 
                                                                          | (0x0000001fU 
                                                                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_block_size)))))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_block_size))))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[3U]))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[2U])))))
                                                               : 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[1U]))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[0U])))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presented_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presented_at)))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__committed_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__committed_at))))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__prepared_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__prepared_at))))))))
                                                             : 
                                                            ((0x00000040U 
                                                              & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                              ? 
                                                             ((0x00000020U 
                                                               & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                               ? 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_at))))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base_at)))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parsed_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parsed_at))))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__arrived_at 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__arrived_at))))))
                                                               : 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid) 
                                                                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence_ge8))
                                                                     ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_overwrites_plus1
                                                                     : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_overwrites_q)))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_sequence)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_generation 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_generation)))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_frame))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__first_fault) 
                                                                     << 0x00000010U) 
                                                                    | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_stage) 
                                                                        << 8U) 
                                                                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_reason))))))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fault_address))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__accepted_tiles))))))
                                                              : 
                                                             ((0x00000020U 
                                                               & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                               ? 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__cycle_count))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__memory_reads)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__age))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__stale_completions))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.rejected_count))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.presented_count)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.accepted_count))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.front_frame_id)))))
                                                               : 
                                                              ((0x00000010U 
                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                ? 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(
                                                                              (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation 
                                                                               >> 0x00000020U))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation)))))
                                                                : 
                                                               ((8U 
                                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                 ? 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 
                                                                   (((IData)(vlSelfRef.error_code) 
                                                                     << 8U) 
                                                                    | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__first_fault) 
                                                                         << 5U) 
                                                                        | ((IData)(vlSelfRef.error) 
                                                                           << 4U)) 
                                                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting) 
                                                                           << 3U) 
                                                                          | (((IData)(vlSelfRef.busy) 
                                                                              << 2U) 
                                                                             | (3U 
                                                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))))))))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 0x0000003fU)))
                                                                 : 
                                                                ((4U 
                                                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                  ? 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 0x00010000U))
                                                                  : 
                                                                 ((2U 
                                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                   ? vlSelfRef.__Vdfg_Regularize_14847
                                                                   : 
                                                                  ((1U 
                                                                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__diag_address))
                                                                    ? vlSelfRef.__Vdfg_Regularize_14847
                                                                    : 0x43553730U))))))))))))
                                                        : vlSelfRef.__Vdfg_Regularize_14846)))))))
                                        : ((0x00000100U 
                                            & (IData)(vlSelfRef.bus_address))
                                            ? ((0x00000080U 
                                                & (IData)(vlSelfRef.bus_address))
                                                ? vlSelfRef.__Vdfg_Regularize_14846
                                                : (
                                                   (0x00000040U 
                                                    & (IData)(vlSelfRef.bus_address))
                                                    ? vlSelfRef.__Vdfg_Regularize_14846
                                                    : 
                                                   ((0x00000020U 
                                                     & (IData)(vlSelfRef.bus_address))
                                                     ? vlSelfRef.__Vdfg_Regularize_14846
                                                     : 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.__Vdfg_Regularize_14846
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation 
                                                                     >> 0x00000020U)))))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__generation)))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__faults))))
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         (~ vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__crc)))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes)))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__written_bytes))
                                                        : vlSelfRef.__Vdfg_Regularize_14846))))))
                                            : ((0x00000080U 
                                                & (IData)(vlSelfRef.bus_address))
                                                ? vlSelfRef.__Vdfg_Regularize_14846
                                                : (
                                                   (0x00000040U 
                                                    & (IData)(vlSelfRef.bus_address))
                                                    ? vlSelfRef.__Vdfg_Regularize_14846
                                                    : 
                                                   ((0x00000020U 
                                                     & (IData)(vlSelfRef.bus_address))
                                                     ? 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? vlSelfRef.__Vdfg_Regularize_14846
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__rejected_commands))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_data))))
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_status))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence)))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? vlSelfRef.__Vdfg_Regularize_14846
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence)))))
                                                     : 
                                                    ((0x00000010U 
                                                      & (IData)(vlSelfRef.bus_address))
                                                      ? vlSelfRef.__Vdfg_Regularize_14846
                                                      : 
                                                     ((8U 
                                                       & (IData)(vlSelfRef.bus_address))
                                                       ? 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 
                                                         ((((((IData)(vlSelfRef.quarantine) 
                                                              << 3U) 
                                                             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__soft_pending) 
                                                                << 2U)) 
                                                            | (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_pending) 
                                                                << 1U) 
                                                               | (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__frame_active))) 
                                                           << 4U) 
                                                          | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__active) 
                                                               << 3U) 
                                                              | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__sealed_valid) 
                                                                 << 2U)) 
                                                             | (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__upload_ready) 
                                                                 << 1U) 
                                                                | (0U 
                                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)))))))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 0x0000003fU)))
                                                       : 
                                                      ((4U 
                                                        & (IData)(vlSelfRef.bus_address))
                                                        ? 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 0x00030000U))
                                                        : 
                                                       ((2U 
                                                         & (IData)(vlSelfRef.bus_address))
                                                         ? vlSelfRef.__Vdfg_Regularize_14846
                                                         : 
                                                        ((1U 
                                                          & (IData)(vlSelfRef.bus_address))
                                                          ? vlSelfRef.__Vdfg_Regularize_14846
                                                          : 0x44593731U)))))))))))));
}
