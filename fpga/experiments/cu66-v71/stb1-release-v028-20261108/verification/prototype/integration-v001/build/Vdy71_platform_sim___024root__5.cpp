// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vdy71_platform_sim.h for the primary calling header

#include "Vdy71_platform_sim__pch.h"

void Vdy71_platform_sim___024root___nba_sequent__TOP__1(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___nba_sequent__TOP__1\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*15:0*/ dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel;
    dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel = 0;
    CData/*3:0*/ __Vdfg_Regularize_15026;
    __Vdfg_Regularize_15026 = 0;
    // Body
    vlSelfRef.physical_x = vlSelfRef.__Vdly__physical_x_885;
    vlSelfRef.physical_y = vlSelfRef.__Vdly__physical_y_886;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync0_889;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__done_sync1_890;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__valid_sync_891;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_sync_892;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy0_902;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__loaded0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__loaded0_903;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__tag0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__tag0_904;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__busy1_905;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__loaded1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__loaded1_906;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__tag1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__tag1_907;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_toggle 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__frame_toggle_908;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_good 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__line_good_909;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_count 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_count_910;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_gray 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__underrun_gray_911;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request1_913;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_line1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_line1_914;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_epoch1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_epoch1_915;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request0_916;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_line0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_line0_917;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_epoch0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__request_epoch0_918;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_sync 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_sync_921;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__request_seen 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__request_seen_924;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__wait_frame_925;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__collect 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__collect_926;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__mask 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__mask_927;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[0U] 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel_928[0U];
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[1U] 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel_928[1U];
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel[2U] 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__snapshot_pixel_928[2U];
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__ack_token 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__ack_token_929;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__de_out 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__de_out_920;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x_900;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y_901;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync_922;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__applied_pattern 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__applied_pattern_923;
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out_919;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read0 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read0_887;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read1 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read1_888;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_content 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_content_896;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_good 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_good_897;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_pattern 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_pattern_898;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_odd 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_odd_899;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_pixel 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_pixel_912;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__data_enable 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__data_enable_893;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x_894;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y_895;
    vlSelfRef.data_enable = vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__de_out;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__canvas 
        = ((0x0028U <= (0x000003ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y) 
                                       - (IData)(0x0018U)))) 
           & (0x02f8U > (0x000003ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y) 
                                        - (IData)(0x0018U)))));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__active 
        = ((0x000eU <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)) 
           & ((0x01eeU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__x)) 
              & ((0x0018U <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y)) 
                 & (0x0338U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__y)))));
    vlSelfRef.red = (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out 
                                    >> 0x00000010U));
    vlSelfRef.green = (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out 
                                      >> 8U));
    vlSelfRef.blue = (0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__rgb_out);
    dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel 
        = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_pattern)
             ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pattern_pixel)
             : (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_odd)
                  ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read1)
                  : (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__read0)) 
                & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_good))))) 
           & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__scan_content))));
    __Vdfg_Regularize_15026 = (1U & (- (IData)(((0U 
                                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x)) 
                                                & (0x0028U 
                                                   == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))))));
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__frame_start 
        = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__data_enable) 
           & ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x)) 
              & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))));
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__hit 
        = ((- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__data_enable))) 
           & ((0x0000000eU & ((((((0x0190U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x)) 
                                  & (0x0280U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))) 
                                 << 2U) | ((((0x00dcU 
                                              == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x)) 
                                             & (0x0190U 
                                                == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))) 
                                            << 1U) 
                                           | ((0x003cU 
                                               == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x)) 
                                              & (0x0048U 
                                                 == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))))) 
                               | ((IData)(__Vdfg_Regularize_15026) 
                                  >> 1U)) << 1U)) | 
              (1U & (IData)(__Vdfg_Regularize_15026))));
    vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__selected_rgb 
        = (0x00ffffffU & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__frame_start)
                                  ? ((IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__pattern_sync) 
                                     >> 1U) : (IData)(vlSelfRef.dy71_platform_sim__DOT__lcd_observer__DOT__applied_pattern)))
                           ? (((0x00f0U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_x))
                                ? (((0x0118U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))
                                     ? 0x00808080U : 
                                    ((0x0190U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))
                                      ? 0x00ff0000U
                                      : ((0x0208U > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))
                                          ? 0x0000ff00U
                                          : (0x000000ffU 
                                             & (- (IData)(
                                                          (0x0280U 
                                                           > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y)))))))) 
                                   | (- (IData)((0x00a0U 
                                                 > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y)))))
                                : ((0x00ff0000U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y) 
                                                   << 0x00000010U)) 
                                   | ((0x0000ff00U 
                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y) 
                                          << 8U)) | 
                                      (0x000000ffU 
                                       & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))))) 
                              & (- (IData)(((0x0028U 
                                             <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y)) 
                                            & (0x02f8U 
                                               > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__physical_y))))))
                           : ((((0x000000f8U & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                                >> 8U)) 
                                | (7U & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                         >> 0x0000000dU))) 
                               << 0x00000010U) | ((
                                                   ((0x000000fcU 
                                                     & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                                        >> 3U)) 
                                                    | (3U 
                                                       & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                                          >> 9U))) 
                                                   << 8U) 
                                                  | ((0x000000f8U 
                                                      & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                                         << 3U)) 
                                                     | (7U 
                                                        & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__pixel) 
                                                           >> 2U)))))));
}

void Vdy71_platform_sim___024root___nba_sequent__TOP__5(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___nba_sequent__TOP__5\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__forward_clock__DOT__Q_88;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__data_out__DOT__Q_56;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__data_out__DOT__Q_58;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__data_out__DOT__Q_60;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__data_out__DOT__Q_62;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__data_out__DOT__Q_64;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__data_out__DOT__Q_66;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__data_out__DOT__Q_68;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__data_out__DOT__Q_70;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__data_out__DOT__Q_72;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__data_out__DOT__Q_74;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__data_out__DOT__Q_76;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__data_out__DOT__Q_78;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__data_out__DOT__Q_80;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__data_out__DOT__Q_82;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__data_out__DOT__Q_84;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__data_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__data_out__DOT__Q_86;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q_90;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q_92;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q_94;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q_96;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q_98;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q_100;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q_102;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q_104;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q_106;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q_108;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q_110;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q_112;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q_114;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q_116;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q_118;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q 
        = vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q_120;
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out31 
        = ((0x7fffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out31)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000fU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out30 
        = ((0xbfffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out30)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000eU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out29 
        = ((0xdfffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out29)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000dU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out28 
        = ((0xefffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out28)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000cU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out27 
        = ((0xf7ffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out27)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000bU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out26 
        = ((0xfbffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out26)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__data_out__DOT__Q)) 
              << 0x0000000aU));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out25 
        = ((0xfdffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out25)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__data_out__DOT__Q)) 
              << 9U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out24 
        = ((0xfeffU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out24)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__data_out__DOT__Q)) 
              << 8U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out23 
        = ((0xff7fU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out23)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__data_out__DOT__Q)) 
              << 7U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out22 
        = ((0xffbfU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out22)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__data_out__DOT__Q)) 
              << 6U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out21 
        = ((0xffdfU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out21)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__data_out__DOT__Q)) 
              << 5U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out20 
        = ((0xffefU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out20)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__data_out__DOT__Q)) 
              << 4U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out19 
        = ((0xfff7U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out19)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__data_out__DOT__Q)) 
              << 3U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out18 
        = ((0xfffbU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out18)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__data_out__DOT__Q)) 
              << 2U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out17 
        = ((0xfffdU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out17)) 
           | (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q)) 
               & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__data_out__DOT__Q)) 
              << 1U));
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out16 
        = ((0xfffeU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out16)) 
           | ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q)) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__data_out__DOT__Q)));
}

void Vdy71_platform_sim___024root___nba_comb__TOP__0(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___nba_comb__TOP__0\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_input 
        = (((IData)(vlSelfRef.dy71_platform_sim__DOT__model__DOT__outdata) 
            & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__model__DOT__drive)))) 
           | (((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q))) 
               | ((2U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q)) 
                         << 1U)) | ((4U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q)) 
                                           << 2U)) 
                                    | ((8U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q)) 
                                              << 3U)) 
                                       | ((0x00000010U 
                                           & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q)) 
                                              << 4U)) 
                                          | ((0x00000020U 
                                              & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q)) 
                                                 << 5U)) 
                                             | ((0x00000040U 
                                                 & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q)) 
                                                    << 6U)) 
                                                | ((0x00000080U 
                                                    & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q)) 
                                                       << 7U)) 
                                                   | ((0x00000100U 
                                                       & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q)) 
                                                          << 8U)) 
                                                      | ((0x00000200U 
                                                          & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q)) 
                                                             << 9U)) 
                                                         | ((0x00000400U 
                                                             & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q)) 
                                                                << 0x0000000aU)) 
                                                            | ((0x00000800U 
                                                                & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q)) 
                                                                   << 0x0000000bU)) 
                                                               | ((0x00001000U 
                                                                   & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q)) 
                                                                      << 0x0000000cU)) 
                                                                  | ((0x00002000U 
                                                                      & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q)) 
                                                                         << 0x0000000dU)) 
                                                                     | ((0x00008000U 
                                                                         & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q)) 
                                                                            << 0x0000000fU)) 
                                                                        | (0x00004000U 
                                                                           & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q)) 
                                                                              << 0x0000000eU))))))))))))))))) 
              & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out16) 
                        & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__0__KET____DOT__tri_out__DOT__Q)))) 
                 | ((2U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out17) 
                           & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__1__KET____DOT__tri_out__DOT__Q)) 
                              << 1U))) | ((4U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out18) 
                                                 & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__2__KET____DOT__tri_out__DOT__Q)) 
                                                    << 2U))) 
                                          | ((8U & 
                                              ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out19) 
                                               & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__3__KET____DOT__tri_out__DOT__Q)) 
                                                  << 3U))) 
                                             | ((0x00000010U 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out20) 
                                                    & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__4__KET____DOT__tri_out__DOT__Q)) 
                                                       << 4U))) 
                                                | ((0x00000020U 
                                                    & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out21) 
                                                       & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__5__KET____DOT__tri_out__DOT__Q)) 
                                                          << 5U))) 
                                                   | ((0x00000040U 
                                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out22) 
                                                          & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__6__KET____DOT__tri_out__DOT__Q)) 
                                                             << 6U))) 
                                                      | ((0x00000080U 
                                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out23) 
                                                             & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__7__KET____DOT__tri_out__DOT__Q)) 
                                                                << 7U))) 
                                                         | ((0x00000100U 
                                                             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out24) 
                                                                & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__8__KET____DOT__tri_out__DOT__Q)) 
                                                                   << 8U))) 
                                                            | ((0x00000200U 
                                                                & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out25) 
                                                                   & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__9__KET____DOT__tri_out__DOT__Q)) 
                                                                      << 9U))) 
                                                               | ((0x00000400U 
                                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out26) 
                                                                      & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__10__KET____DOT__tri_out__DOT__Q)) 
                                                                         << 0x0000000aU))) 
                                                                  | ((0x00000800U 
                                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out27) 
                                                                         & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__11__KET____DOT__tri_out__DOT__Q)) 
                                                                            << 0x0000000bU))) 
                                                                     | ((0x00001000U 
                                                                         & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out28) 
                                                                            & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__12__KET____DOT__tri_out__DOT__Q)) 
                                                                               << 0x0000000cU))) 
                                                                        | ((0x00002000U 
                                                                            & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out29) 
                                                                               & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__13__KET____DOT__tri_out__DOT__Q)) 
                                                                                << 0x0000000dU))) 
                                                                           | ((0x00004000U 
                                                                               & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out30) 
                                                                                & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__14__KET____DOT__tri_out__DOT__Q)) 
                                                                                << 0x0000000eU))) 
                                                                              | (0x00008000U 
                                                                                & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__sdram_dq__out__strong__out31) 
                                                                                & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_io__BRA__15__KET____DOT__tri_out__DOT__Q)) 
                                                                                << 0x0000000fU))))))))))))))))))));
}

void Vdy71_platform_sim___024root___timing_ready(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___timing_ready\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if ((((0x0000000008000000ULL & vlSelfRef.__VactTriggered[1U])) != 0ULL)) {
        vlSelfRef.__VtrigSched_h9582c18f__0.ready("@(posedge dy71_platform_sim.model.device_clock)");
    }
}

void Vdy71_platform_sim___024root___timing_resume(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___timing_resume\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__VtrigSched_h9582c18f__0.moveToResumeQueue(
                                                          "@(posedge dy71_platform_sim.model.device_clock)");
    vlSelfRef.__VtrigSched_h9582c18f__0.resume("@(posedge dy71_platform_sim.model.device_clock)");
    if ((((0x0000000010000000ULL & vlSelfRef.__VactTriggered[1U])) != 0ULL)) {
        vlSelfRef.__VdlySched.resume();
    }
}

void Vdy71_platform_sim___024root___trigger_orInto__act_vec_ext(VlUnpacked<QData/*63:0*/, 3> &out, const VlUnpacked<QData/*63:0*/, 2> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___trigger_orInto__act_vec_ext\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((1U >= n));
}

void Vdy71_platform_sim___024root___trigger_orInto__act_ext_vec(VlUnpacked<QData/*63:0*/, 2> &out, const VlUnpacked<QData/*63:0*/, 3> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___trigger_orInto__act_ext_vec\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = (out[n] | in[n]);
        n = ((IData)(1U) + n);
    } while ((1U >= n));
}

bool Vdy71_platform_sim___024root___trigger_anySet__act_ext(const VlUnpacked<QData/*63:0*/, 3> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___trigger_anySet__act_ext\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((IData)(1U) + n);
    } while ((3U > n));
    return (0U);
}

void Vdy71_platform_sim___024root___trigger_clear__act(VlUnpacked<QData/*63:0*/, 2> &out) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___trigger_clear__act\n"); );
    // Locals
    IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        out[n] = 0ULL;
        n = ((IData)(1U) + n);
    } while ((2U > n));
}

void Vdy71_platform_sim___024root____VbeforeTrig_h9582c18f__0(Vdy71_platform_sim___024root* vlSelf, const char* __VeventDescription) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root____VbeforeTrig_h9582c18f__0\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    VlUnpacked<QData/*63:0*/, 2> __VTmp;
    // Body
    __VTmp[0U] = 0ULL;
    __VTmp[1U] = (QData)((IData)((((IData)(vlSelfRef.dy71_platform_sim__DOT__model__DOT__device_clock) 
                                   & (~ (IData)(vlSelfRef.__Vtrigprevexpr___TOP__dy71_platform_sim__DOT__model__DOT__device_clock__0))) 
                                  << 0x0000001bU)));
    vlSelfRef.__Vtrigprevexpr___TOP__dy71_platform_sim__DOT__model__DOT__device_clock__0 
        = vlSelfRef.dy71_platform_sim__DOT__model__DOT__device_clock;
    if ((0x0000000008000000ULL & __VTmp[1U])) {
        vlSelfRef.__VtrigSched_h9582c18f__0.ready(__VeventDescription);
        vlSelfRef.__VtrigSched_h9582c18f__0.ready(__VeventDescription);
    }
    vlSelfRef.__VactTriggeredAcc[1U] = (vlSelfRef.__VactTriggeredAcc[1U] 
                                        | __VTmp[1U]);
}

#ifdef VL_DEBUG
void Vdy71_platform_sim___024root___eval_debug_assertions(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___eval_debug_assertions\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    if (VL_UNLIKELY(((vlSelfRef.clk & 0xfeU)))) {
        Verilated::overWidthError("clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.read_clk & 0xfeU)))) {
        Verilated::overWidthError("read_clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.pixel_clk & 0xfeU)))) {
        Verilated::overWidthError("pixel_clk");
    }
    if (VL_UNLIKELY(((vlSelfRef.pixel_reset_n & 0xfeU)))) {
        Verilated::overWidthError("pixel_reset_n");
    }
    if (VL_UNLIKELY(((vlSelfRef.rst & 0xfeU)))) {
        Verilated::overWidthError("rst");
    }
    if (VL_UNLIKELY(((vlSelfRef.bus_write & 0xfeU)))) {
        Verilated::overWidthError("bus_write");
    }
    if (VL_UNLIKELY(((vlSelfRef.bus_address & 0xf000U)))) {
        Verilated::overWidthError("bus_address");
    }
    if (VL_UNLIKELY(((vlSelfRef.transport_fault & 0xfeU)))) {
        Verilated::overWidthError("transport_fault");
    }
    if (VL_UNLIKELY(((vlSelfRef.peek_address & 0xff000000U)))) {
        Verilated::overWidthError("peek_address");
    }
}
#endif  // VL_DEBUG
