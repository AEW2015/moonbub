// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vdy71_platform_sim.h for the primary calling header

#include "Vdy71_platform_sim__pch.h"

extern const VlWide<16>/*511:0*/ Vdy71_platform_sim__ConstPool__CONST_11;
extern const VlWide<32>/*1023:0*/ Vdy71_platform_sim__ConstPool__CONST_2;

void Vdy71_platform_sim___024root___act_sequent__TOP__26(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__26\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    SData/*13:0*/ dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    CData/*2:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 = 0;
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326);
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_374;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_374 = 0;
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_376;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_376 = 0;
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378);
    VlWide<4>/*127:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381;
    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381);
    CData/*7:0*/ __Vtask_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reject_packet__code_100;
    __Vtask_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reject_packet__code_100 = 0;
    // Body
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_bytes_865 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_address_9 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__source_674 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid_47 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_data_48 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address_40 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__c_281 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__g_285 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__2__KET___799 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_low_464 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_partition_466 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_data_10 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__done_449 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_tile_243 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_presented_545 = 0U;
        vlSelfRef.__Vdly__front_frame_id_538 = 0xffffffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address_204 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid_229 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_mask_144 = 0xffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_mask_142 = 0xffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_bank_790 = 0U;
        vlSelfRef.__Vdly__reference_bank_534 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_valid_596 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_code_598 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested_176 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured_810 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count_820 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_address_853 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_sequence_855 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_generation_854 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_cookie_654 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front_650 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot_651 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_generation_655 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_frame_656 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted_683 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_cookie_680 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_context_681 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_generation_678 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_frame_id_679 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot_623 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot_619 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot_643 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group_645 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data_19[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data_19[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data_19[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_data_19[3U] = 0U;
        VL_ASSIGN_W(512, vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155, Vdy71_platform_sim__ConstPool__CONST_11);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_validated_555 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes_556 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0_557 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_yu_558 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_y_559 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key_560 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id_561 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id_562 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_block_size_565 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_addr_566 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_bytes_567 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[3U] = 0U;
        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1479 = 1U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_code_267 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_266 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_321 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code_322 = 0U;
    } else {
        if (vlSelfRef.bus_write) {
            if ((0x0720U != (IData)(vlSelfRef.bus_address))) {
                if ((0x0724U != (IData)(vlSelfRef.bus_address))) {
                    if ((0x0728U != (IData)(vlSelfRef.bus_address))) {
                        if ((0x072cU == (IData)(vlSelfRef.bus_address))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__burst__DOT__shadow_bytes_865 
                                = vlSelfRef.bus_wdata;
                        }
                    }
                }
            }
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__2__KET___799 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[2U];
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_choice_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_address_9 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_aux_req_addr;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_data_10 
                        = (0x0000ffffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk_route)
                                           ? (((1U 
                                                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__index))
                                                ? (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux)
                                                : (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__doa_out_mux)) 
                                              & (- (IData)(
                                                           (1U 
                                                            & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read))))))
                                           : vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__));
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
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__source_674 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_source;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_cookie_680 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__next_cookie;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_context_681 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_generation_678 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot];
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_frame_id_679 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot];
                        }
                    }
                }
            }
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                    }
                } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                    }
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                    }
                } else if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_rsp_valid) 
                             & (~ (IData)(vlSelfRef.rst))) 
                            & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending))) {
                    if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                    }
                }
            } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 0U;
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__bad_command) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid_47 = 0U;
        if ((1U & (~ ((((((((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)) 
                            | (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                           | (2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                          | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                         | (4U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                        | (5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                       | (0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) 
                      | (6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state)))))) {
            if ((7U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                if ((8U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                    if ((0x0bU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                        if ((9U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__delay))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid_47 = 1U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_data_48 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_retime;
                            }
                        } else if ((0x0aU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__state))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_valid_47 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__response_data_48 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_retime;
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
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__address_40 
                                                = (0x00fffff8U 
                                                   & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__address
                                                       [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner] 
                                                       >> 3U) 
                                                      << 3U));
                                        }
                                    }
                                }
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
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_valid) 
                                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__result_ready))))) {
                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                            if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                if ((1U & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full) 
                                            >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__process_bank)) 
                                           & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending))))) {
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__c_281 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__2__KET__;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__g_285 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__6__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__c_281 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__g_285 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f;
                            }
                        }
                    }
                }
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__start_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__start_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_code_267 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_266 = 0U;
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bad_last) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_code_267 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_266 = 1U;
            } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_valid) 
                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__result_ready))))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                    if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                        if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                            if ((2U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_code_267 = 0xffU;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__error_266 = 1U;
                            }
                        }
                    }
                }
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_321 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code_322 = 0U;
                if ((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_321 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code_322 = 1U;
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bad_tile) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_321 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code_322 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_last) 
                        != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_last))
                        ? 3U : 2U);
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__active) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__prefix_pending)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__cache_valid) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__data_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__data_ready))) {
                            if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_byte))) {
                                if (((0x000003ffU & 
                                      ((IData)(1U) 
                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_word))) 
                                     == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_words
                                     [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank])) {
                                    if ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last) 
                                               >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__read_bank)))) {
                                        if ((0x0007e903U 
                                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__emitted_bytes)) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_321 = 1U;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__error_code_322 = 4U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__done_449 = 0U;
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                          >> 7U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                              >> 6U)))) {
                    if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
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
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_low_464 
                                                    = 
                                                    (0x0000ffffU 
                                                     & (IData)(
                                                               (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                >> 
                                                                (0x0000003fU 
                                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                    << 4U)))));
                                            }
                                        }
                                    }
                                }
                            }
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_partition_466 
                                                = (
                                                   (0U 
                                                    == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product)
                                                    ? 1U
                                                    : 
                                                   (0x0000ffffU 
                                                    & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product 
                                                        >= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_span)
                                                        ? 
                                                       (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_span 
                                                        - (IData)(1U))
                                                        : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product)));
                                        }
                                    }
                                }
                            }
                        }
                    }
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                  >> 5U)))) {
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))) {
                                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__in_ready) {
                                                if (
                                                    (((IData)(1U) 
                                                      + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__block_number) 
                                                     == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks)) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__done_449 = 1U;
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
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__last_tile_243 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_last;
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
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_presented_545 = 0U;
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__safe_swap) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__frame_presented_545 = 1U;
            vlSelfRef.__Vdly__front_frame_id_538 = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address_204 
                = (0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__calculated_packet_address);
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address_204 
                = (0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tid);
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__last_address_204 
                = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane) 
                    << 0x00000011U) | (0x0001ffffU 
                                       & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id));
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid_229 = 0U;
        if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_code))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__event_pending_valid_229 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__canonical_burst_mask_144 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126 
                = ((0x0eU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126)) 
                   | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p1_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126 
                = ((0x0dU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126)) 
                   | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_write) 
                      << 1U));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p2_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126 
                = (0x0bU & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p3_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__rgb_burst_mask_142 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_mask;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126 
                = (8U | (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__writing_126));
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_prepare_valid) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_pending)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_bank_790 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested_176 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                    vlSelfRef.__Vdly__reference_bank_534 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank;
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_valid_596 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_valid_596 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_rsp_code_598 
                = (3U & ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index))
                          ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index))
                              ? ((0x0151U >= (0x000001ffU 
                                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                 >> 2U)))
                                  ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_mem
                                 [(0x000001ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                  >> 2U))]
                                  : 0U) : (((0x0151U 
                                             >= (0x000001ffU 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                    >> 2U)))
                                             ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_mem
                                            [(0x000001ffU 
                                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                 >> 2U))]
                                             : 0U) 
                                           >> 2U)) : 
                         ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index))
                           ? (((0x0151U >= (0x000001ffU 
                                            & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                               >> 2U)))
                                ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_mem
                               [(0x000001ffU & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                >> 2U))]
                                : 0U) >> 4U) : (((0x0151U 
                                                  >= 
                                                  (0x000001ffU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                      >> 2U)))
                                                  ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__qmap_mem
                                                 [(0x000001ffU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index) 
                                                      >> 2U))]
                                                  : 0U) 
                                                >> 6U))));
        }
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
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_requested_176 = 0U;
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
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured_810 
                    = (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__bad_access)));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__count_820 
                    = (0x000001ffU & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__);
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured_810 = 0U;
            }
        }
        if (((0x0fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
             & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__state)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__configured_810 = 0U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__read_pending) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_address_853 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_address;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_sequence_855 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_sequence;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_generation_854 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_generation;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_cookie_654 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__next_cookie;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_front_650 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_active;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_slot_651 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_generation_655 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_generation
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_frame_656 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_frame
                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__command_slot];
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted_683 = 1U;
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                             >> 2U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_aborted_683 = 0U;
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_rsp_valid) 
             & (~ (IData)(vlSelfRef.rst)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting) 
                          | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match))))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__pending) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                } else if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_error_682 = 1U;
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_abort_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_abort_ready))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_slot_623 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_prepare_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_ready))) {
            if ((1U & (~ ((((((0ULL == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation) 
                              | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation 
                                 <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__latest_generation)) 
                             | (0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) 
                            | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                           | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank))) 
                          | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__context_state
                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot]))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__p_slot_619 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
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
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_slot_643 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__f_group_645 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__refill_group;
        }
        if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p0_rsp_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_rsp_ready))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__aborting)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error)))) {
                            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing)))) {
                                VL_ASSIGNSEL_WW(512, 128, 
                                                (0x000001ffU 
                                                 & VL_MULS_III(32, (IData)(0x00000010U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__word_index))), vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_data[0U]);
                            }
                        }
                    }
                }
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
            if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
                  & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)) 
                 | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__choose_write) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[0U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[0U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[1U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[1U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[2U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[2U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[3U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[3U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[4U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[4U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[5U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[5U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[6U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[6U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[7U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[7U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[8U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[8U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[9U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[9U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[10U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[10U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[11U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[11U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[12U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[12U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[13U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[13U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[14U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[14U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155[15U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[15U];
                } else {
                    VL_ASSIGN_W(512, vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__pixels_155, Vdy71_platform_sim__ConstPool__CONST_11);
                }
            }
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
             & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
            if ((((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)) 
                  | (9U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) 
                 & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__rd_rsp_valid)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 9U;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
            }
        } else if ((0x00000080U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
        } else if ((0x00000040U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
        } else if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
        } else if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
            } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0xffU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 
                        = ((0x004bU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index))
                            ? 3U : ((0x0087U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index))
                                     ? 0x0cU : (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_validated) 
                                                 & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                    == 
                                                    (0x0000ffffU 
                                                     & ((IData)(0x0069U) 
                                                        + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_addr)))))
                                                 ? 0x0fU
                                                 : 
                                                (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                  == 
                                                  (0x0000ffffU 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                      - (IData)(1U))))
                                                  ? 6U
                                                  : 1U))));
                }
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 
                    = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))
                        ? 5U : 0x11U);
            }
        } else if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 
                    = ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))
                        ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))
                            ? 0x10U : 4U) : ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))
                                              ? 0x0eU
                                              : 0x0dU));
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 
                    = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))
                        ? 1U : 0x0bU);
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__rd_rsp_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
            }
        } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__p_meta_ready) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 8U;
                    }
                } else if (((~ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__crc_outer) 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0x0dU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else if (((~ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__crc_inner) 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0x0eU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else if (((~ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__crc_hud) 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0x0fU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 7U;
                }
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_56__hud32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[9U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[8U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[7U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[6U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_57__hud32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[13U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[12U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[11U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[10U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_58__hud32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[17U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[16U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[15U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[14U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_59__hud16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[19U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[18U]);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_60__hud16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[21U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[20U]);
                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[3U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[38U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[39U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[40U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[2U] 
                    = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[41U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[42U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[43U])) 
                          << 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[3U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[41U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[42U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[43U])) 
                          >> 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[1U] 
                    = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[1U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[44U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[46U])) 
                          << 0x00000018U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[2U] 
                    = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[44U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[46U])) 
                          >> 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[1U] 
                    = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[47U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[48U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[49U])));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[0U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[0U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[51U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[52U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[0U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[0U]) 
                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[53U]);
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key) {
                    VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[3U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[24U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[2U] 
                        = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[3U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[1U] 
                        = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[1U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[2U] 
                        = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              >> 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[1U] 
                        = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[1U]) 
                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[33U])));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[0U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[0U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[36U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[0U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[0U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[37U]);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_64 
                        = (0U != (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[0U] 
                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[1U]) 
                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[2U]) 
                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_62__hud128[3U]));
                } else {
                    VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[3U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[24U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[2U] 
                        = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[3U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[1U] 
                        = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[1U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[2U] 
                        = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              >> 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[1U] 
                        = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[1U]) 
                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[33U])));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[0U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[0U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[36U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[0U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[0U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[37U]);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_64 
                        = (0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[0U] 
                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[1U]) 
                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[2U]) 
                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_63__hud128[3U]));
                }
                if (((((((((((((0x48553235U != (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[0U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[1U]) 
                                                 << 0x00000010U) 
                                                | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[2U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[3U]))) 
                               & (0x48583332U != ((
                                                   (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[0U]) 
                                                     << 8U) 
                                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[1U]) 
                                                   << 0x00000010U) 
                                                  | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[2U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[3U])))) 
                              & (0x48583333U != (((
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[0U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[1U]) 
                                                  << 0x00000010U) 
                                                 | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[2U]) 
                                                     << 8U) 
                                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[3U])))) 
                             | (1U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[4U])) 
                            | (4U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[5U])) 
                           | (0x00000019U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_56__hud32)) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_57__hud32 
                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id)) 
                         | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_58__hud32 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)) 
                        | (0x02d0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_59__hud16))) 
                       | (0x01e0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_60__hud16))) 
                      | (0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[0U] 
                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[1U]) 
                                 | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[2U]) 
                                | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_61__hud128[3U]))) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_64))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0x0bU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else if (((1U > vlSelfRef.__Vdfg_Regularize_15032) 
                            | ((vlSelfRef.__Vdfg_Regularize_15032 
                                > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes)) 
                               | ((1U > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[73U]) 
                                  | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[73U] 
                                      > (IData)(vlSelfRef.__Vdfg_Regularize_14877)) 
                                     | ((1U > vlSelfRef.__Vdfg_Regularize_15031) 
                                        | ((vlSelfRef.__Vdfg_Regularize_15031 
                                            > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes)) 
                                           | ((1U > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[72U]) 
                                              | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[72U] 
                                                  > (IData)(vlSelfRef.__Vdfg_Regularize_14877)) 
                                                 | ((1U 
                                                     > vlSelfRef.__Vdfg_Regularize_15030) 
                                                    | ((vlSelfRef.__Vdfg_Regularize_15030 
                                                        > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes)) 
                                                       | ((1U 
                                                           > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[71U]) 
                                                          | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[71U] 
                                                              > (IData)(vlSelfRef.__Vdfg_Regularize_14877)) 
                                                             | ((1U 
                                                                 > vlSelfRef.__Vdfg_Regularize_15029) 
                                                                | ((vlSelfRef.__Vdfg_Regularize_15029 
                                                                    > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes)) 
                                                                   | ((1U 
                                                                       > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[70U]) 
                                                                      | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[70U] 
                                                                          > (IData)(vlSelfRef.__Vdfg_Regularize_14877)) 
                                                                         | ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_length_total 
                                                                             != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_bytes)) 
                                                                            | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[103U]) 
                                                                               | ((0xf0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[102U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[101U]) 
                                                                                | ((0x86U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[100U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[99U]) 
                                                                                | ((0xa8U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[98U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[97U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[96U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[95U]) 
                                                                                | ((0x40U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[94U]) 
                                                                                | ((1U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[93U]) 
                                                                                | ((0x68U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[92U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[91U]) 
                                                                                | ((0xa8U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[90U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[89U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[88U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[87U]) 
                                                                                | ((0xa0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[86U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[85U]) 
                                                                                | ((0x52U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[84U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[83U]) 
                                                                                | ((0x16U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[82U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[81U]) 
                                                                                | ((0x18U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[80U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[79U]) 
                                                                                | ((0xa0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[78U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[77U]) 
                                                                                | ((0x36U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[76U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[75U]) 
                                                                                | ((0x16U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[74U]) 
                                                                                | ((0U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[105U]) 
                                                                                | (0x18U 
                                                                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[104U])))))))))))))))))))))))))))))))))))))))))))))))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0x0cU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323);
                    VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326);
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[3U] 
                        = ((0x000000ffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[22U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[24U])) 
                              << 8U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[3U] 
                        = ((0x000000ffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[38U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[39U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[40U])) 
                              << 8U));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 1U;
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[2U] 
                        = ((0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              << 0x00000010U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[3U] 
                        = ((0xffffff00U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[25U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[26U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[27U])) 
                              >> 0x00000010U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[2U] 
                        = ((0x0000ffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[41U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[42U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[43U])) 
                              << 0x00000010U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[3U] 
                        = ((0xffffff00U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[41U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[42U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[43U])) 
                              >> 0x00000010U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[1U] 
                        = ((0x00ffffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[1U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              << 0x00000018U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[2U] 
                        = ((0xffff0000U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[29U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[30U])) 
                              >> 8U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[1U] 
                        = ((0x00ffffffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[1U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[44U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[46U])) 
                              << 0x00000018U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[2U] 
                        = ((0xffff0000U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[44U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[46U])) 
                              >> 8U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[1U] 
                        = ((0xff000000U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[1U]) 
                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[31U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[32U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[33U])));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[1U] 
                        = ((0xff000000U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[1U]) 
                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[47U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[48U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[49U])));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[0U] 
                        = ((0x000000ffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[0U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[34U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[36U])) 
                              << 8U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[0U] 
                        = ((0x000000ffU & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[0U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[51U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[52U])) 
                              << 8U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[0U] 
                        = ((0xffffff00U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[0U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[37U]);
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[0U] 
                        = ((0xffffff00U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[0U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[53U]);
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[0U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[0U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[1U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[1U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[2U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[2U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_reference_tag_568[3U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_323[3U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[0U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[0U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[1U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[1U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[2U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[2U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_output_tag_569[3U] 
                        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud128__Vfuncout_326[3U];
                }
            } else {
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_33__inner32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[9U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[8U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[7U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[6U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_34__inner32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[13U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[12U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[11U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[10U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_35__inner32 
                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[17U]) 
                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[16U]) 
                        << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[15U]) 
                                            << 8U) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[14U]));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_36__inner16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[19U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[18U]);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_37__inner16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[21U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[20U]);
                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[3U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[24U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[25U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[26U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[2U] 
                    = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[27U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[28U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[29U])) 
                          << 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[3U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[27U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[28U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[29U])) 
                          >> 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[1U] 
                    = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[1U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[30U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[31U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[32U])) 
                          << 0x00000018U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[2U] 
                    = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[30U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[31U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[32U])) 
                          >> 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[1U] 
                    = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[33U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[34U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[35U])));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[0U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[0U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[36U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[37U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[38U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[0U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[0U]) 
                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[39U]);
                if ((((((((((((0x47553636U != (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[0U]) 
                                                  << 8U) 
                                                 | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[1U]) 
                                                << 0x00000010U) 
                                               | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[2U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[3U]))) 
                              | (1U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[4U])) 
                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[5U] 
                                != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key))) 
                            | (0x00000019U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_33__inner32)) 
                           | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_34__inner32 
                              != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id)) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_35__inner32 
                             != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id)) 
                         | (0x02d0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_36__inner16))) 
                        | (0x01e0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_37__inner16))) 
                       | ((0x10U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[22U]) 
                          & (0x20U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[22U]))) 
                      | (0x12U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[23U])) 
                     | (0U != ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[0U] 
                                  ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag[0U]) 
                                 | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[1U] 
                                    ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag[1U])) 
                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[2U] 
                                   ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag[2U])) 
                               | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_38__inner128[3U] 
                                  ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag[3U]))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 6U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_39__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[43U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[42U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[41U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[40U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_40__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[47U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[46U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[45U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[44U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_41__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_42__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_43__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[55U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[54U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[53U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[52U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_44__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[55U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[54U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[53U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[52U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_45__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[59U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[58U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[57U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[56U]));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_46__inner32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[59U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[58U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[57U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[56U]));
                    if ((((((((((0x00000152U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_39__inner32) 
                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_40__inner32 
                                   != ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key)
                                        ? 0U : 3U))) 
                               | (0x0000002fU > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_41__inner32)) 
                              | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_42__inner32 
                                 > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))) 
                             | (0x0000002fU > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_43__inner32)) 
                            | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_44__inner32 
                               > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))) 
                           | (0x0000002fU > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_45__inner32)) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_46__inner32 
                             > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))) 
                         | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_length_total 
                            != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 7U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                    } else {
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_47__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[47U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[46U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[45U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[44U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_48__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_50__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_49__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[55U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[54U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[52U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_block_size_565 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[22U];
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix0_557 
                            = (0x0000ffffU & ((IData)(0x01daU) 
                                              + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_47__inner32));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_yu_558 
                            = (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_48__inner32 
                                              + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_49__inner32));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__prefix_y_559 
                            = (0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_50__inner32);
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1480 
                            = (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                                              - (IData)(1U)));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1481 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0x0aU;
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[55U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[54U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[52U]));
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1482 
                            = (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                                              - (IData)(1U)));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1483 = 1U;
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[59U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[57U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[56U]));
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1484 
                            = (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_51__inner32 
                                              - (IData)(1U)));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_plane_bytes_1485 = 1U;
                    }
                }
            }
        } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_4__outer16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[7U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[6U]);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_5__outer16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[17U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[16U]);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_6__outer16 
                    = (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[19U]) 
                        << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[18U]);
                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128);
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[3U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[20U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[21U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[22U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[2U] 
                    = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[23U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[24U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[25U])) 
                          << 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[3U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[3U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[23U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[24U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[25U])) 
                          >> 0x00000010U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[1U] 
                    = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[1U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[26U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[27U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[28U])) 
                          << 0x00000018U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[2U] 
                    = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[2U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[26U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[27U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[28U])) 
                          >> 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[1U] 
                    = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[29U]) 
                           << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[30U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[31U])));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[0U] 
                    = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[0U]) 
                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[32U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[33U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[34U])) 
                          << 8U));
                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[0U] 
                    = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[0U]) 
                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[35U]);
                if ((((((((0x43553636U != (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[0U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[1U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[2U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[3U]))) 
                          | (1U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[4U])) 
                         | ((2U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[5U]) 
                            & (3U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[5U]))) 
                        | (0x0019U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_4__outer16))) 
                       | (0x02d0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_5__outer16))) 
                      | (0x01e0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_6__outer16))) 
                     | (0U != ((((0x5931494bU ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[0U]) 
                                 | (0x249e96c7U ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[1U])) 
                                | (0x7276c7c5U ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[2U])) 
                               | (0x16c99852U ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_7__outer128[3U]))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 2U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_8__outer32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[11U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[10U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[9U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[8U]));
                    VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[3U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[52U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[53U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[54U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[2U] 
                        = ((0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[55U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[56U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[57U])) 
                              << 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[3U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[3U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[55U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[56U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[57U])) 
                              >> 0x00000010U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[1U] 
                        = ((0x00ffffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[1U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[59U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[60U])) 
                              << 0x00000018U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[2U] 
                        = ((0xffff0000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[2U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[58U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[59U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[60U])) 
                              >> 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[1U] 
                        = ((0xff000000U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[1U]) 
                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[61U]) 
                               << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[62U]) 
                                                   << 8U) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[63U])));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[0U] 
                        = ((0x000000ffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[0U]) 
                           | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[64U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[65U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[66U])) 
                              << 8U));
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[0U] 
                        = ((0xffffff00U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[0U]) 
                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[67U]);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_10__outer32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[11U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[10U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[9U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[8U]));
                    if ((((0xffffffffU == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_8__outer32) 
                          | (0U == (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[0U] 
                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[1U]) 
                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[2U]) 
                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_9__outer128[3U]))) 
                         | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_valid) 
                            & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_10__outer32 
                               <= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_frame_id)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 3U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                    } else {
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_11__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[68U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_12__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[68U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_13__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[72U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_14__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[72U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_15__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[71U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[70U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[69U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[68U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_16__outer32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[75U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[74U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[73U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[72U]));
                        if ((((((0x0000021fU > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_11__outer32) 
                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_12__outer32 
                                   > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))) 
                               | (0x0000006eU > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_13__outer32)) 
                              | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_14__outer32 
                                 > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))) 
                             | ((0x00000001ffffffffULL 
                                 & (0x0000000000000050ULL 
                                    + ((QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_15__outer32)) 
                                       + (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_16__outer32))))) 
                                != (QData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 4U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                        } else {
                            if ((1U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[5U])) {
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_17__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[12U]));
                                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128);
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[1U]) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[47U])));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[0U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[51U]);
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_24 
                                    = ((0xffffffffU 
                                        != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_17__outer32) 
                                       | (0U != (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[0U] 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[1U]) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[2U]) 
                                                 | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_18__outer128[3U])));
                            } else {
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_19__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[12U]));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_20__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[12U]));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_21__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[11U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[10U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[9U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[8U]));
                                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128);
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[1U]) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[47U])));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[0U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[51U]);
                                VL_ZERO_RESET_W(128, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128);
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[3U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[38U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[2U] 
                                    = ((0x0000ffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[3U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[1U] 
                                    = ((0x00ffffffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[1U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[2U] 
                                    = ((0xffff0000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          >> 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[1U] 
                                    = ((0xff000000U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[1U]) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[47U])));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[0U] 
                                    = ((0x000000ffU 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[0U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[50U])) 
                                          << 8U));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[0U] 
                                    = ((0xffffff00U 
                                        & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[0U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[51U]);
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_24 
                                    = (1U & (((((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_valid)) 
                                                | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_19__outer32 
                                                   != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_id)) 
                                               | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_20__outer32 
                                                  >= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_21__outer32)) 
                                              | (0U 
                                                 == 
                                                 (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[0U] 
                                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[1U]) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[2U]) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_22__outer128[3U]))) 
                                             | (0U 
                                                != 
                                                ((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[0U] 
                                                    ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[0U]) 
                                                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[1U] 
                                                      ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[1U])) 
                                                  | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[2U] 
                                                     ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[2U])) 
                                                 | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_23__outer128[3U] 
                                                    ^ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[3U])))));
                            }
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCond_24) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 5U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                            } else {
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_374 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[11U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[10U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[9U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[8U]));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_376 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[15U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[14U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[13U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[12U]));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_25__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[71U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[70U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[69U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[68U]));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_26__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[71U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[70U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[69U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[68U]));
                                vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_27__outer32 
                                    = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[75U]) 
                                          << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[74U]) 
                                        << 0x00000010U) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[73U]) 
                                           << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[72U]));
                                VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378);
                                VL_ZERO_W(128, __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key_560 
                                    = (1U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[5U]);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_frame_id_561 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_374;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_id_562 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer32__Vfuncout_376;
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[3U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[36U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[37U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[38U])) 
                                          << 8U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[3U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[52U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[53U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[54U])) 
                                          << 8U));
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes_556 
                                    = (0x0000ffffU 
                                       & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_25__outer32);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_addr_566 
                                    = (0x0000ffffU 
                                       & ((IData)(0x004cU) 
                                          + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_26__outer32));
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_hud_bytes_567 
                                    = (0x0000ffffU 
                                       & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_27__outer32);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_validated_555 = 1U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 1U;
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[2U] 
                                    = ((0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          << 0x00000010U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[3U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[39U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[40U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[41U])) 
                                          >> 0x00000010U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[2U] 
                                    = ((0x0000ffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[55U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[56U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[57U])) 
                                          << 0x00000010U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[3U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[3U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[55U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[56U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[57U])) 
                                          >> 0x00000010U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[1U] 
                                    = ((0x00ffffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[1U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          << 0x00000018U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[2U] 
                                    = ((0xffff0000U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[42U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[43U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[44U])) 
                                          >> 8U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[1U] 
                                    = ((0x00ffffffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[1U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[58U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[59U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[60U])) 
                                          << 0x00000018U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[2U] 
                                    = ((0xffff0000U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[2U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[58U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[59U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[60U])) 
                                          >> 8U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[1U] 
                                    = ((0xff000000U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[1U]) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[45U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[46U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[47U])));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[1U] 
                                    = ((0xff000000U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[1U]) 
                                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[61U]) 
                                           << 0x00000010U) 
                                          | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[62U]) 
                                              << 8U) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[63U])));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[0U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[0U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[48U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[49U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[50U])) 
                                          << 8U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[0U] 
                                    = ((0x000000ffU 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[0U]) 
                                       | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[64U]) 
                                            << 0x00000010U) 
                                           | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[65U]) 
                                               << 8U) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[66U])) 
                                          << 8U));
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[0U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[0U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[51U]);
                                __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[0U] 
                                    = ((0xffffff00U 
                                        & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[0U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_header[67U]);
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[0U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[0U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[1U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[1U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[2U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[2U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_reference_tag_563[3U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_378[3U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[0U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[0U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[1U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[1U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[2U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[2U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag_564[3U] 
                                    = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer128__Vfuncout_381[3U];
                            }
                        }
                    }
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__rd_rsp_valid) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__byte_bad) {
                    __Vtask_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reject_packet__code_100 
                        = (((IData)(vlSelfRef.__Vdfg_Regularize_14984)
                             ? 0x0aU : ((IData)(vlSelfRef.__Vdfg_Regularize_14985)
                                         ? 0x0aU : 
                                        ((IData)(vlSelfRef.__Vdfg_Regularize_14986)
                                          ? 0x0aU : 
                                         ((IData)(vlSelfRef.__Vdfg_Regularize_14987)
                                           ? 9U : (
                                                   ((0x00000546U 
                                                     > 
                                                     ((IData)(3U) 
                                                      + 
                                                      (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__scan_addr) 
                                                        - (IData)(0x00000088U)) 
                                                       << 2U)))
                                                     ? 
                                                    ((3U 
                                                      == 
                                                      (3U 
                                                       & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_data)))
                                                      ? 8U
                                                      : (IData)(vlSelfRef.__Vdfg_Regularize_14953))
                                                     : 
                                                    ((0U 
                                                      != 
                                                      (3U 
                                                       & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_data)))
                                                      ? 8U
                                                      : (IData)(vlSelfRef.__Vdfg_Regularize_14953))) 
                                                   & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_14937)))))))) 
                           & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 
                        = __Vtask_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reject_packet__code_100;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0x12U;
                }
            }
        } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__p_req_ready) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 2U;
            }
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__cfg_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__cfg_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_validated_555 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 0U;
            if (((0x02ddU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length)) 
                 | (0xc000U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_553 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__error_code_554 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__done_552 = 1U;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state_551 = 1U;
            }
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__1__KET___340 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__2__KET___341 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__3__KET___342 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__4__KET___343 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__5__KET___344 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__6__KET___345 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__7__KET___346 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__samples__BRA__4__KET__;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                            << 2U))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__0__KET___332 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(1U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__1__KET___333 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(2U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__2__KET___334 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(3U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__3__KET___335 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                            << 2U))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__4__KET___336 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(1U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__5__KET___337 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(2U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__6__KET___338 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k;
    dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis 
        = (0x00003fffU & Vdy71_platform_sim__ConstPool__CONST_2
           [(3U | (0x07fffffcU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis__fk_131) 
                                  << 2U)))]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__basis_stage__BRA__7__KET___339 
        = dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT____VlemCall_8__basis;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__sample_stage__BRA__0__KET___331 
        = (0x00ffffffU & ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                           ? vlSelfRef.__Vdfg_Regularize_14927
                           : ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                               ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__intermediate
                              [(((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__k) 
                                 << 3U) | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__group_index) 
                                           << 1U))]
                               : ((5U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state))
                                   ? VL_EXTENDS_II(24,20, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__source_coeff[0U])
                                   : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__dc_middle 
                                      & (- (IData)(
                                                   (7U 
                                                    == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))))))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag2_715 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud2_721 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__red3_733 
        = (0x0007ffffU & VL_MULS_III(19, (IData)(0x00000167U), 
                                     (0x0007ffffU & 
                                      VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr2)))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__blue3_734 
        = (0x0007ffffU & VL_MULS_III(19, (IData)(0x000001c6U), 
                                     (0x0007ffffU & 
                                      VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb2)))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y3_725 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green_cb3_735 
        = (0x0007ffffU & VL_MULS_III(19, (IData)(0x00000058U), 
                                     (0x0007ffffU & 
                                      VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb2)))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__green_cr3_736 
        = (0x0007ffffU & VL_MULS_III(19, (IData)(0x000000b7U), 
                                     (0x0007ffffU & 
                                      VL_EXTENDS_II(19,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr2)))));
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error_code_441 = 0U;
    } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__cfg_ready))) {
        if ((((2U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane)) 
              | ((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                 & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)))) 
             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks 
                != ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                     ? ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                         ? 0x00001418U : 0x00001518U)
                     : ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))
                         ? 0x00000533U : 0x00000546U))))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error_code_441 = 1U;
        }
    } else if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__running) 
                  & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error))) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__slot)) 
                & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__omit) 
                   | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_valid)))) {
        if (((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__omit)) 
             & (((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__block_number 
                  != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__encoded_count) 
                 | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_last) 
                    != ((0x0001ffffU & ((IData)(1U) 
                                        + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__encoded_count)) 
                        == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__encoded_total))) 
                | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__hidden) 
                   & (0U != (((((((((((((((((((((((
                                                   ((((((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[0U] 
                                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[1U]) 
                                                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[2U]) 
                                                         | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[3U]) 
                                                        | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[4U]) 
                                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[5U]) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[6U]) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[7U]) 
                                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[8U]) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[9U]) 
                                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[10U]) 
                                                 | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[11U]) 
                                                | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[12U]) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[13U]) 
                                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[14U]) 
                                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[15U]) 
                                            | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[16U]) 
                                           | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[17U]) 
                                          | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[18U]) 
                                         | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[19U]) 
                                        | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[20U]) 
                                       | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[21U]) 
                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[22U]) 
                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[23U]) 
                                    | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[24U]) 
                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[25U]) 
                                  | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[26U]) 
                                 | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[27U]) 
                                | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[28U]) 
                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[29U]) 
                              | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[30U]) 
                             | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__tile_coefficients[31U])))))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__error_code_441 = 2U;
        }
    }
    if (((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
          & (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__fast_result))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U] 
            = (0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U] 
            = (0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
            = (0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
            = (0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
            = (0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U] 
            = (0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U] 
            = (0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
            = (0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
            = (0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
            = (0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U] 
            = (0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U]);
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U] 
            = (0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U]);
    } else {
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[0U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[1U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[2U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[3U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[4U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 1U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[5U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[6U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[7U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[8U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[9U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 2U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[10U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[11U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[12U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[13U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[14U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 3U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[15U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[16U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[17U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[18U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[19U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 4U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[20U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[21U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[22U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[23U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[24U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 5U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[25U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[26U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[27U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[28U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[29U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 6U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[30U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[31U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[32U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[33U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[34U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
        if ((((((~ (IData)(vlSelfRef.rst)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) 
               & (1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid)) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination) 
                >> 7U))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U] 
                = ((0xfff00000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U]) 
                   | (0x000fffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U] 
                = ((0x000fffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[35U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                      << 0x00000014U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
                = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]) 
                   | (0x000000ffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__ 
                                     >> 0x0000000cU)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
                = ((0xf00000ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]) 
                   | (0x0fffff00U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__ 
                                     << 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U] 
                = ((0x0fffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[36U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                      << 0x0000001cU));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U] 
                = ((0xffff0000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U]) 
                   | (0x0000ffffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__ 
                                     >> 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U] 
                = ((0x0000ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[37U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                      << 0x00000010U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
                = ((0xfffffff0U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]) 
                   | (0x0000000fU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__ 
                                     >> 0x00000010U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
                = ((0xff00000fU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]) 
                   | (0x00fffff0U & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__ 
                                     << 4U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U] 
                = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[38U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                      << 0x00000018U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U] 
                = ((0xfffff000U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U]) 
                   | (0x00000fffU & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__ 
                                     >> 8U)));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U] 
                = ((0x00000fffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_dequantized_415[39U]) 
                   | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__ 
                      << 0x0000000cU));
        }
    }
    if (((0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period) 
         & (0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period))) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_period 
            = ((vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period 
                <= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period)
                ? ((0x0000000000000bb8ULL >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period)
                    ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period
                    : 0x0000000000000bb8ULL) : ((0x0000000000000bb8ULL 
                                                 >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period)
                                                 ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_high__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period
                                                 : 0x0000000000000bb8ULL));
    }
    if (((0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period) 
         & (0ULL != vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period))) {
        vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_period 
            = ((vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period 
                <= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period)
                ? ((0x0000000000000bb8ULL >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period)
                    ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clka_period
                    : 0x0000000000000bb8ULL) : ((0x0000000000000bb8ULL 
                                                 >= vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period)
                                                 ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__payload_low__DOT__gen_tdp__DOT__INT_RAMB_TDP__DOT__time_clkb_period
                                                 : 0x0000000000000bb8ULL));
    }
}

void Vdy71_platform_sim___024root___act_sequent__TOP__28(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__28\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_retime_32 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_retime;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner_127 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b_280 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f_284 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product_463 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read_811 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_last_439 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_last;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id_541 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id_325 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag1_714 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_mask_20 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_mask;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_write_31 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_write;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index_246 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud1_720 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y2_724 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb2_731 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr2_732 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr2;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_pending_777 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET___802 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_address_849 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_address;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_sequence_851 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_sequence;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_generation_850 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error_756 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted_24 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting_670 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot_764 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank_530 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot_629 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing_146 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[4U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[5U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[6U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[7U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[8U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[9U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[10U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[11U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[12U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[13U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[14U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels[15U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated_578 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_valid_573 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_valid_574 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_frame_id_575 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_frame_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_id_576 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_length_total_595 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_length_total;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_length_total_591 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_length_total;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner_583 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer_582 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud_584 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET___404 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET___405 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET___406 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET___407 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET___408 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET___409 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET___410 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET__;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid_383 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination_385 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET___411 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET__;
}

void Vdy71_platform_sim___024root___act_sequent__TOP__30(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__30\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_1__average_byte;
    CData/*7:0*/ dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_0__average_byte;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_448;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_448 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_449;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_449 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_450;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_450 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_451;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_451 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_452;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_452 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_453;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_453 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_454;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_454 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_455;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_455 = 0;
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_retime_32 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__controller__DOT__dq_capture;
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner_127 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b_280 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f_284 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product_463 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read_811 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id_541 = 0xffffffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__b_mask_20 = 0xffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_write_31 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index_246 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_pending_777 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET___802 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_address_849 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_sequence_851 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_generation_850 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted_24 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting_670 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot_764 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank_530 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot_629 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing_146 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated_578 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_valid_573 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_valid_574 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_frame_id_575 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_id_576 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_length_total_595 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_length_total_591 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner_583 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer_582 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud_584 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306 = 0U;
    } else {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__state)))) {
                if ((1U & (~ ((0U != (IData)(vlSelfRef.__Vdfg_Regularize_14866)) 
                              & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_turn) 
                                 | (~ (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)))))))) {
                    if (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)) 
                         & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__hold_for_lcd)))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__owner_127 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__selected;
                    }
                }
                if (((0U != (IData)(vlSelfRef.__Vdfg_Regularize_14866)) 
                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_turn) 
                        | (~ (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125 
                        = (((~ ((IData)(1U) << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected))) 
                            & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125)) 
                           | (0x0fU & ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_error) 
                                              >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected))) 
                                       << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__local_selected))));
                } else if (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__physical_pending)) 
                            & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__hold_for_lcd)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125 
                        = ((~ ((IData)(1U) << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__selected))) 
                           & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__response_error_125));
                }
            }
        }
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort)))) {
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
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b_280 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__1__KET__;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f_284 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__5__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__b_280 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__a;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__f_284 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__e;
                            }
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
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_product_463 
                                                = (0x0001ffffU 
                                                   & ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_span 
                                                       * (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_probability)) 
                                                      >> 8U));
                                        }
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
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__bulk__DOT__mode_read_811 
                    = (1U & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__6__KET__);
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__safe_swap) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id_541 = 0xffffffffU;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__pending_id_541 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__candidate_id;
                }
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
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__write_bank_530 
                                    = ((IData)(vlSelfRef.__Vdfg_Regularize_14988)
                                        ? (1U & (- (IData)((IData)(vlSelfRef.__Vdfg_Regularize_14989))))
                                        : 2U);
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__m_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__aux_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__a_write_31 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_write;
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
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_index_246 
                                                    = 
                                                    (0x000007ffU 
                                                     & ((0U 
                                                         == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                                                         ? 
                                                        (VL_MULS_III(32, (IData)(0x0000002dU), 
                                                                     VL_DIVS_III(32, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_y), (IData)(2U))) 
                                                         + 
                                                         VL_DIVS_III(32, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_x), (IData)(2U)))
                                                         : 
                                                        (VL_MULS_III(32, (IData)(0x0000002dU), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_y)) 
                                                         + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_x))));
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
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__hud_prepare_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_prepare_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_pending_777 = 1U;
        }
        if ((1U & ((~ (IData)(vlSelfRef.busy)) & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__frame_active))))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__hud_pending_777 = 0U;
        }
        if (vlSelfRef.bus_write) {
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__5__KET___802 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[5U];
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_address_849 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_address;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_sequence_851 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_sequence;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__held_generation_850 
                = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_generation;
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted_24 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_active) 
             & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__lcd_abort_i) 
                | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_aborting)))) {
            if ((1U & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_issued)) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__bridge__DOT__p2_rsp_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_rsp_ready))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__lcd_aborted_24 = 1U;
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__abort_match) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting_670 = 1U;
        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                             >> 2U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state)))) {
                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__aborting_670 = 0U;
                    }
                }
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
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__held_slot_764 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_cache_slot_629 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_slot;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__state)))) {
                if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__ref_req_valid) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)) 
                     | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_valid) 
                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__write_ready)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__writing_146 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__choose_write;
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
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated_578 = 1U;
                                        }
                                    }
                                }
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_length_total_591 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum01 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum2);
                                        }
                                    }
                                }
                            } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                 >> 2U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 1U)))) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__cfg_valid) 
                                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__cfg_ready))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_validated_578 = 0U;
                                        }
                                    }
                                }
                            }
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__cfg_valid) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__cfg_ready))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_valid_573 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_valid_574 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__last_frame_id_575 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_id_576 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id;
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[0U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[0U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[1U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[1U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[2U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[2U];
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__reference_tag_577[3U] 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag[3U];
                                            }
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
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_length_total_595 
                                                = ((IData)(0x0000006eU) 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum01);
                                        }
                                    }
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__outer_validated) {
                                                if (
                                                    (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                      >= 
                                                      (0x0000ffffU 
                                                       & ((IData)(0x0048U) 
                                                          + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes)))) 
                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                        < 
                                                        (0x0000ffffU 
                                                         & ((IData)(0x004cU) 
                                                            + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes)))))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner_583 
                                                        = 
                                                        (((~ 
                                                           ((IData)(0x000000ffU) 
                                                            << 
                                                            (0x0000001fU 
                                                             & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                                 - 
                                                                 ((IData)(0x00000048U) 
                                                                  + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes))) 
                                                                << 3U)))) 
                                                          & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner_583) 
                                                         | (0x00000000ffffffffULL 
                                                            & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte) 
                                                               << 
                                                               (0x0000001fU 
                                                                & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                                    - 
                                                                    ((IData)(0x00000048U) 
                                                                     + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_bytes))) 
                                                                   << 3U)))));
                                                }
                                                if (
                                                    (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                      >= 
                                                      (0x0000ffffU 
                                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                          - (IData)(8U)))) 
                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                        < 
                                                        (0x0000ffffU 
                                                         & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                            - (IData)(4U)))))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud_584 
                                                        = 
                                                        (((~ 
                                                           ((IData)(0x000000ffU) 
                                                            << 
                                                            (0x0000001fU 
                                                             & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                                 - 
                                                                 ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                                  - (IData)(8U))) 
                                                                << 3U)))) 
                                                          & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud_584) 
                                                         | (0x00000000ffffffffULL 
                                                            & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte) 
                                                               << 
                                                               (0x0000001fU 
                                                                & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                                    - 
                                                                    ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                                     - (IData)(8U))) 
                                                                   << 3U)))));
                                                }
                                            }
                                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                 >= 
                                                 (0x0000ffffU 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                     - (IData)(4U))))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer_582 
                                                    = 
                                                    (((~ 
                                                       ((IData)(0x000000ffU) 
                                                        << 
                                                        (0x0000001fU 
                                                         & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                             - 
                                                             ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                              - (IData)(4U))) 
                                                            << 3U)))) 
                                                      & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer_582) 
                                                     | (0x00000000ffffffffULL 
                                                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte) 
                                                           << 
                                                           (0x0000001fU 
                                                            & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index) 
                                                                - 
                                                                ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes) 
                                                                 - (IData)(4U))) 
                                                               << 3U)))));
                                            }
                                        }
                                    }
                                }
                            }
                        } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                             >> 3U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 2U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 1U)))) {
                                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__cfg_valid) 
                                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__cfg_ready))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_inner_583 = 0U;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_outer_582 = 0U;
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__received_hud_584 = 0U;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__rows__start_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__start_ready))) {
            if ((0xffffffffU != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid)) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306 = 0U;
            }
        } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bad_tile)))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__active) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_busy) {
                    if ((7U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__write_row))) {
                        if (((0x0000007fU & ((IData)(1U) 
                                             + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__tile_column))) 
                             == ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_plane))
                                  ? 0x5aU : 0x2dU))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306 
                                = (((~ ((IData)(1U) 
                                        << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__fill_bank))) 
                                    & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__bank_last_306)) 
                                   | (3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__expected_last) 
                                            << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__rows__DOT__fill_bank))));
                        }
                    }
                }
            }
        }
    }
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_last_439 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id_325 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid_383 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination_385 = 0U;
    } else {
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_last_439 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__last_sample;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__slot_ready) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__reconstruct__in_valid) 
                 & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)) 
                    | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_id_325 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_id;
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_valid_383 
                = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)) 
                   && (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_valid));
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product_destination_385 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_destination;
                }
            }
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag1_714 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag0;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud1_720 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud0;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y2_724 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_450 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y_odd1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_449 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb_bottom1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_448 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb_top1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_451 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_448) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_449))));
    dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_0__average_byte 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_450)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_451) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_448)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb2_731 
        = (0x000001ffU & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_0__average_byte) 
                          - (IData)(0x0080U)));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_454 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y_odd1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_453 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr_bottom1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_452 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr_top1;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_455 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_452) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_453))));
    dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_1__average_byte 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_454)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_455) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_452)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr2_732 
        = (0x000001ffU & ((IData)(dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT____VlemCall_1__average_byte) 
                          - (IData)(0x0080U)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__wr_error_756 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cache_wr_valid) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__bad_write)));
    if ((1U & (~ ((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))))) {
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__slot_ready) {
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__reconstruct__in_valid) 
                 & (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key) 
                     | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)) 
                    | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__0__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__0__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__0__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__1__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__1__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__1__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__2__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__2__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__2__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[0U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__3__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__3__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__3__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__4__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__4__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__4__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__5__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__5__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__5__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__6__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__6__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__6__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[1U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__7__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__7__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__7__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__8__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__8__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__8__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__9__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__9__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__9__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__10__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__10__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__10__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[2U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__11__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__11__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__11__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__12__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__12__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__12__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__13__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__13__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__13__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__14__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__14__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__14__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[3U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__15__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__15__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__15__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__16__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__16__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__16__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__17__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__17__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__17__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__18__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__18__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__18__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[4U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__19__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__19__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__19__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__20__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__20__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__20__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__21__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__21__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__21__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__22__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__22__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__22__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[5U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__23__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__23__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__23__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__24__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__24__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__24__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__25__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__25__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__25__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__26__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__26__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__26__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[6U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__27__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__27__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__27__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__28__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__28__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__28__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__29__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__29__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__29__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__30__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__30__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__30__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[7U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__31__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__31__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__31__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__32__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__32__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__32__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__33__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__33__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__33__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__34__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__34__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__34__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[8U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__35__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__35__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__35__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__36__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__36__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__36__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__37__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__37__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__37__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__38__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__38__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__38__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[9U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__39__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__39__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__39__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__40__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__40__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__40__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__41__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__41__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__41__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__42__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__42__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__42__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[10U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__43__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__43__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__43__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__44__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__44__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__44__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__45__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__45__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__45__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__46__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__46__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__46__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[11U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__47__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__47__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__47__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__48__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__48__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__48__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__49__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__49__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__49__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__50__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__50__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__50__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[12U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__51__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__51__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__51__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__52__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__52__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__52__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__53__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__53__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__53__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__54__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__54__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__54__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[13U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__55__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__55__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__55__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__56__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__56__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__56__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__57__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__57__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__57__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__58__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__58__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__58__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[14U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__59__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__59__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__59__KET__)))) 
                          << 0x00000018U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U] 
                    = ((0xffffff00U & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U]) 
                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                           ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                       VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__60__KET__))
                                             ? 0U : 
                                            (VL_LTS_III(32, 0x000000ffU, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__60__KET__))
                                              ? 0x000000ffU
                                              : (0x000000ffU 
                                                 & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__60__KET__)))));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U] 
                    = ((0xffff00ffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__61__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__61__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__61__KET__)))) 
                          << 8U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U] 
                    = ((0xff00ffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__62__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__62__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__62__KET__)))) 
                          << 0x00000010U));
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U] 
                    = ((0x00ffffffU & vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__out_pixels_327[15U]) 
                       | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden)
                            ? 0x00000080U : (VL_GTS_III(32, 0U, 
                                                        VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__63__KET__))
                                              ? 0U : 
                                             (VL_LTS_III(32, 0x000000ffU, 
                                                         VL_EXTENDS_II(32,25, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__63__KET__))
                                               ? 0x000000ffU
                                               : (0x000000ffU 
                                                  & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__reconstruct__DOT__combined__BRA__63__KET__)))) 
                          << 0x00000018U));
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__0__KET___404 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__0__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__0__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__1__KET___405 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__1__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__1__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__2__KET___406 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__2__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__2__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__3__KET___407 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__3__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__3__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__4__KET___408 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__4__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__4__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__5__KET___409 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__5__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__5__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__6__KET___410 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__6__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__6__KET__)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__product__BRA__7__KET___411 
                        = (0x01ffffffU & VL_MULS_III(25, 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,16, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__7__KET__))), 
                                                     (0x01ffffffU 
                                                      & VL_EXTENDS_II(25,9, (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__7__KET__)))));
                }
            }
        }
    }
}

void Vdy71_platform_sim___024root___act_sequent__TOP__36(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__36\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_428;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_428 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_429;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_429 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_430;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_430 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_431;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_431 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_432;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_432 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_433;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_433 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_434;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_434 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_435;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_435 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_436;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_436 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_437;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_437 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_438;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_438 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_439;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_439 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_440;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_440 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_441;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_441 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_442;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_442 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_443;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_443 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_444;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_444 = 0;
    CData/*7:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_445;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_445 = 0;
    CData/*0:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_446;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_446 = 0;
    SData/*8:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_447;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_447 = 0;
    SData/*31:0*/ __VExpandSel_Lsb_1;
    SData/*31:0*/ __VExpandSel_Lsb_2;
    SData/*31:0*/ __VExpandSel_Lsb_3;
    SData/*31:0*/ __VExpandSel_Lsb_4;
    SData/*31:0*/ __VExpandSel_Lsb_5;
    SData/*31:0*/ __VExpandSel_Lsb_6;
    SData/*31:0*/ __VExpandSel_Lsb_7;
    // Body
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__a_279 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__e_283 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_span_462 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_probability_461 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__6__KET___803 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_write_11 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__frame_active_774 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_sequence_833 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_done_626 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_slot_634 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key_235 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden_242 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid_533 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id_535 = 0xffffffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum01_594 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum2_589 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum01_590 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes_571 = 0U;
    } else {
        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort)))) {
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
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__a_279 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__0__KET__;
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__e_283 
                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__hash_state__BRA__4__KET__;
                                }
                            } else if ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__a_279 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__round_a;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__e_283 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__round_e;
                            }
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
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                      >> 4U)))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state) 
                                                  >> 1U)))) {
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
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_span_462 
                                                    = 
                                                    (0x0001ffffU 
                                                     & ((IData)(1U) 
                                                        + 
                                                        ((0x0000ffffU 
                                                          & (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                                     >> 
                                                                     ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                      << 4U)))) 
                                                         - 
                                                         (0x0000ffffU 
                                                          & (IData)(
                                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                                     >> 
                                                                     ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                                      << 4U)))))));
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arith_probability_461 
                                                    = 
                                                    ((0x015fU 
                                                      >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__probability_address))
                                                      ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__probabilities
                                                     [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__probability_address]
                                                      : 0U);
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
        if (vlSelfRef.bus_write) {
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__command_fields__BRA__6__KET___803 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__fields[6U];
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_state)))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__arb_choice_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__arb_write_11 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__hud_aux_req_write;
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__release_packet) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__frame_active_774 = 0U;
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
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__frame_active_774 = 1U;
                                }
                            }
                        }
                    }
                }
            }
        }
        if ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_req_valid) 
              & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p0_ready)) 
             | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__cpu_req_valid) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__p1_ready)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__expected_sequence_833 
                = ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__packet_arbiter__DOT__choice)
                    ? vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__pending_sequence
                    : vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_sequence);
        }
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_done_626 = 0U;
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__prepare_adapter__DOT__owner_abort_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__prepare_abort_ready))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_target)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_done_626 = 1U;
            }
        }
        if (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_pending) 
               & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight))) 
              & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__state))) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__l_active)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__abort_done_626 = 1U;
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
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_slot_634 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot;
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__ref_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_rsp_ready))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill)))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 1U;
            }
        }
        if ((1U & (~ ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort) 
                        & (0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                       & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) 
                      | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fail_now))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs)))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__is_key_235 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key;
                            }
                        }
                    }
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
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__hidden_242 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_hidden;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs)))) {
                            if ((1U & (((((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy)) 
                                          & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending))) 
                                         & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__q_pending))) 
                                        & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending))) 
                                       & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__write_pending))))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 0U;
                            }
                        }
                    }
                } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs))) {
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                      >> 3U)))) {
                            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts))) {
                                        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tile_complete) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 0U;
                                        }
                                    }
                                }
                            } else if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts) 
                                                 >> 1U)))) {
                                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ts)))) {
                                    if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_valid) 
                                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__s_ready))) {
                                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 0U;
                                    }
                                }
                            }
                        }
                    }
                } else if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__fs)))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__start_fire) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_received_251 = 0U;
                    }
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                      & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__aborting))))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__active) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort))))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__commit_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_valid_533 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__ref_id_535 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__banks__DOT__candidate_id;
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))))) {
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[0U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[0U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[1U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[1U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[2U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[2U];
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__accepted_tag_190[3U] 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[3U];
                            }
                        }
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
                        if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum01_594 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum0 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum1);
                                        }
                                    }
                                }
                            }
                        }
                        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                      >> 4U)))) {
                            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_32__inner32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[59U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[58U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[57U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[56U]));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum2_589 
                                                = ((IData)(0x00000040U) 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_32__inner32);
                                        }
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum01_590 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum0 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum1);
                                        }
                                    }
                                }
                            }
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__cfg_valid) 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__cfg_ready))) {
                                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__packet_bytes_571 
                                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length;
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
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__last_sample_421 
        = ((0x0001ffffU & ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_count)) 
           == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_total);
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_id_349 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_y_437 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_x_436 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_destination_384 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_valid_382 = 0U;
    } else {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                      >> 3U)))) {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__state)))) {
                        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__inverse__in_valid) 
                             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__in_ready))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__inverse__DOT__out_id_349 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_id;
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_y_437 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__y_sample;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_x_436 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__x_sample;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issued_all)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_destination_384 
                        = (0x000000ffU & ((IData)(1U) 
                                          << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)));
                }
            }
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__select_valid_382 
                = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)) 
                   && (1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issued_all))));
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__tag0_713 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_tag;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__hud0_719 
        = ((- (IData)((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error))))) 
           & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__hud_q) 
              & (- (IData)((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_hud_hit)))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y1_723 
        = (0x000000ffU & (((0U == (0x00000018U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                  << 3U)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q
                                    [(((IData)(7U) 
                                       + (0x00000078U 
                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                             << 3U))) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x00000018U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                      << 3U))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q
                             [(3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                     >> 2U))] >> (0x00000018U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                     << 3U)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_436 
        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_435 
        = (0x000000ffU & (((0U == (0x0000001fU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q
                                    [(((IData)(7U) 
                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x0000001fU 
                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q
                             [((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1) 
                               >> 5U)] >> (0x0000001fU 
                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_434 
        = (0x000000ffU & (((0U == (0x00000018U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                  << 2U)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q
                                    [(((IData)(7U) 
                                       + (0x00000078U 
                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                             << 2U))) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x00000018U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                      << 2U))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q
                             [(3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                     >> 3U))] >> (0x00000018U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                     << 2U)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_437 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_434) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_435))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_433 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_436)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_437) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_434)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb_bottom1_728 
        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_433;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_431 
        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_430 
        = (0x000000ffU & (((0U == (0x0000001fU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q
                                    [(((IData)(7U) 
                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x0000001fU 
                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q
                             [((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1) 
                               >> 5U)] >> (0x0000001fU 
                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_429 
        = (0x000000ffU & (((0U == (0x00000018U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                  << 2U)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q
                                    [(((IData)(7U) 
                                       + (0x00000078U 
                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                             << 2U))) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x00000018U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                      << 2U))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q
                             [(3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                     >> 3U))] >> (0x00000018U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                     << 2U)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_432 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_429) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_430))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_428 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_431)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_432) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_429)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cb_top1_727 
        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_428;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__y_odd1_726 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_odd_q;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_446 
        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_445 
        = (0x000000ffU & (((0U == (0x0000001fU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q
                                    [(((IData)(7U) 
                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x0000001fU 
                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q
                             [((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1) 
                               >> 5U)] >> (0x0000001fU 
                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_444 
        = (0x000000ffU & (((0U == (0x00000018U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                  << 2U)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q
                                    [(((IData)(7U) 
                                       + (0x00000078U 
                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                             << 2U))) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x00000018U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                      << 2U))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q
                             [(3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                     >> 3U))] >> (0x00000018U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                     << 2U)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_447 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_444) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_445))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_443 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_446)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_447) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_444)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr_bottom1_730 
        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_443;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_441 
        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_440 
        = (0x000000ffU & (((0U == (0x0000001fU & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q
                                    [(((IData)(7U) 
                                       + (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x0000001fU 
                                                   & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q
                             [((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1) 
                               >> 5U)] >> (0x0000001fU 
                                           & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ci1)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_439 
        = (0x000000ffU & (((0U == (0x00000018U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                  << 2U)))
                            ? 0U : (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q
                                    [(((IData)(7U) 
                                       + (0x00000078U 
                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                             << 2U))) 
                                      >> 5U)] << ((IData)(0x00000020U) 
                                                  - 
                                                  (0x00000018U 
                                                   & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                      << 2U))))) 
                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q
                             [(3U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                     >> 3U))] >> (0x00000018U 
                                                  & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q) 
                                                     << 2U)))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_442 
        = (0x000001ffU & ((IData)(1U) + ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_439) 
                                         + (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__b_440))));
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_438 
        = (0x000000ffU & ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__blend_441)
                           ? ((IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__unused_sum_lsb_442) 
                              >> 1U) : (IData)(__Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__a_439)));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__cr_top1_729 
        = __Vfunc_dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pixel__DOT__average_byte__Vfuncout_438;
    if ((1U & (~ (IData)(vlSelfRef.rst)))) {
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
                            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                          >> 3U)))) {
                                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                              >> 2U)))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__parser__rd_rsp_valid) {
                                                if (
                                                    (1U 
                                                     & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__byte_bad)))) {
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_index_606 
                                                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__scan_addr;
                                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__receive_byte_605 
                                                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_rsp_data;
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
    if ((1U & (~ ((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))))) {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state))) {
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issued_all)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__0__KET___389 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15034) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15034))))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__0__KET___388 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & VL_MULS_III(32, (IData)(0x00000080U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group))))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + (0x000003ffU 
                                                  & VL_MULS_III(32, (IData)(0x00000080U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & VL_MULS_III(32, (IData)(0x00000080U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(0x0000001fU 
                                               & (VL_MULS_III(32, (IData)(0x00000080U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)) 
                                                  >> 5U))] 
                                             >> (0x0000001fU 
                                                 & VL_MULS_III(32, (IData)(0x00000080U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group))))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__1__KET___391 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15036) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15036))))));
                    __VExpandSel_Lsb_1 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(1U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__1__KET___390 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_1))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_1) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_1)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_1 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_1))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__2__KET___393 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15038) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15038))))));
                    __VExpandSel_Lsb_2 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(2U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__2__KET___392 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_2))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_2) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_2)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_2 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_2))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__3__KET___395 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15040) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15040))))));
                    __VExpandSel_Lsb_3 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(3U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__3__KET___394 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_3))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_3) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_3)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_3 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_3))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__4__KET___397 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15042) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15042))))));
                    __VExpandSel_Lsb_4 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(4U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__4__KET___396 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_4))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_4) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_4)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_4 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_4))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__5__KET___399 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15044) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15044))))));
                    __VExpandSel_Lsb_5 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(5U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__5__KET___398 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_5))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_5) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_5)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_5 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_5))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__6__KET___401 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15046) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15046))))));
                    __VExpandSel_Lsb_6 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(6U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__6__KET___400 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_6))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_6) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_6)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_6 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_6))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_quantizer__BRA__7__KET___403 
                        = (0x000000ffU & ((IData)(vlSelfRef.__Vdfg_Regularize_15048) 
                                          | (- (IData)(
                                                       (0x00ffU 
                                                        < (IData)(vlSelfRef.__Vdfg_Regularize_15048))))));
                    __VExpandSel_Lsb_7 = (0x000003ffU 
                                          & VL_MULS_III(32, (IData)(0x00000010U), 
                                                        ((IData)(7U) 
                                                         + 
                                                         VL_MULS_III(32, (IData)(8U), (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__issue_group)))));
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__selected_coefficient__BRA__7__KET___402 
                        = (0x0000ffffU & (((0U == (0x0000001fU 
                                                   & __VExpandSel_Lsb_7))
                                            ? 0U : 
                                           (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                            [(((IData)(0x0000000fU) 
                                               + __VExpandSel_Lsb_7) 
                                              >> 5U)] 
                                            << ((IData)(0x00000020U) 
                                                - (0x0000001fU 
                                                   & __VExpandSel_Lsb_7)))) 
                                          | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients
                                             [(__VExpandSel_Lsb_7 
                                               >> 5U)] 
                                             >> (0x0000001fU 
                                                 & __VExpandSel_Lsb_7))));
                }
            }
        }
    }
}

void Vdy71_platform_sim___024root___act_sequent__TOP__38(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__38\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_total_429 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_total;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_id_386 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_tag_760 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_tag;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__y_sample_419 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__y_sample;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__x_sample_418 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__x_sample;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__hud_q_753 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__hud_q;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_hud_hit_757 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_hud_hit;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error_755 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_odd_q_759 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_odd_q;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q_758 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__pending_sequence_767 
        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__pending_sequence;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_649 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation_630 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id_631 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid_628 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id_193 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot_194 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation_192 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key_163 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_hidden_438 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_hidden;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending_248 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending_250 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum0_592 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum0;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum1_593 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum0_587 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum0;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum1_588 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length_173 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[0U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[0U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[1U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[1U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[2U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[2U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[3U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[3U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[4U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[4U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[5U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[5U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[6U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[6U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[7U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[7U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[8U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[8U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[9U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[9U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[10U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[10U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[11U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[11U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[12U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[12U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[13U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[13U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[14U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[14U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[15U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[15U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[16U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[16U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[17U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[17U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[18U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[18U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[19U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[19U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[20U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[20U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[21U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[21U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[22U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[22U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[23U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[23U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[24U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[24U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[25U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[25U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[26U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[26U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[27U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[27U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[28U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[28U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[29U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[29U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[30U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[30U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[31U] 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients[31U];
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad1_700 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad1;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad0_699 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad0;
}

void Vdy71_platform_sim___024root___act_sequent__TOP__40(Vdy71_platform_sim___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vdy71_platform_sim___024root___act_sequent__TOP__40\n"); );
    Vdy71_platform_sim__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268 = 0;
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269 = 0;
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270 = 0;
    IData/*31:0*/ __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271;
    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271 = 0;
    // Body
    if (vlSelfRef.rst) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__pending_sequence_767 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_649 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation_630 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id_631 = 0xffffffffU;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid_628 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id_193 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot_194 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation_192 = 0ULL;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key_163 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending_248 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending_250 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[0U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[1U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[2U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[3U] = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum0_592 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum1_593 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum0_587 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum1_588 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length_173 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad1_700 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad0_699 = 0U;
    } else {
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__internal_abort) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 0U;
        } else if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__start_valid) 
                    & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__start_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 0U;
        } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bad_last) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 0U;
        } else {
            if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_valid) 
                          & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__result_ready))))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__write_byte) {
                        if ((0x3fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__byte_position))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 
                                = ((IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270) 
                                   | (3U & ((IData)(1U) 
                                            << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__fill_bank))));
                        }
                    }
                    if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                        if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                            if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270 
                                    = ((~ ((IData)(1U) 
                                           << (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__process_bank))) 
                                       & (IData)(vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_full_270));
                            }
                        }
                    }
                }
            }
            if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_valid) 
                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT____Vcellinp__sha__result_ready))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 0U;
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__active) {
                if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                    if ((1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                        if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__core_state))) {
                            if ((1U & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__bank_last) 
                                       >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__process_bank)))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__canonical__DOT__sha__DOT__result_pending_265 = 1U;
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.bus_write) {
            if ((0x0024U == (IData)(vlSelfRef.bus_address))) {
                if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__command_state)) 
                     & (vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence 
                        > vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__ack_sequence))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__control_plane__DOT__pending_sequence_767 
                        = vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__submitted_sequence;
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma_cmd_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__cmd_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_649 = 1U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__dma__DOT__result_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__inflight_649 = 0U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__switch_now) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_generation_630 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_generation;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_frame_id_631 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__pending_frame;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__front_valid_628 = 1U;
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal) 
                      | ((IData)(vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__abort_i) 
                         & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__abort_allowed)))))) {
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__state))) {
                            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__commit_fire) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_frame_id_193 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fid;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_cache_slot_194 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_slot;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__presentation_generation_192 
                                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__active_generation;
                            }
                        }
                    }
                }
            }
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
                                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__packet_length_173 
                                        = (0x0000ffffU 
                                           & vlSelfRef.dy71_platform_sim__DOT__control_plane__DOT__staging__DOT__packet_bytes);
                                }
                            }
                        }
                    }
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__payload_start_clear) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key_163 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__meta_fire) 
             & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__fatal_non_hud)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__key_163 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_key;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[0U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag[0U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[1U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag[1U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[2U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag[2U];
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__canonical_expected_158[3U] 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__metadata_output_tag[3U];
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__b_req_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending_248 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__rd_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__byte_pending_248 = 0U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_req_valid) 
             & ((~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__cache_prepare_abort)) 
                & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__memory__DOT__tiles__DOT__read_ready)))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending_250 = 1U;
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__ref_rsp_valid) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_rsp_ready))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__ref_pending_250 = 0U;
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                = (((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)) 
                    | (3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)))
                    ? ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__rd_rsp_valid)
                        ? 0U : 3U) : ((((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state)) 
                                        & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid)) 
                                       & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__b_req_ready))
                                       ? 3U : 0U));
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
        } else if ((0x00000080U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0xffU;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
        } else if ((0x00000040U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0xffU;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
        } else if ((0x00000020U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0xffU;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0xffU;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_read_address 
                             >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__packet_bytes))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 6U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 1U;
                        }
                    } else if ((VL_GTS_III(32, 0xfffff800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__dc_prediction) 
                                | VL_LTS_III(32, 0x00000800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__dc_prediction))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x12U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x16U;
                    }
                } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                            if ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_total 
                                 != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__packet_bytes))) {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 4U;
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                            } else {
                                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 7U;
                            }
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x37U;
                        }
                    } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((((0x00000012U > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_bits) 
                              | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_bits 
                                 > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_capacity)) 
                             | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_encoded 
                                != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_length))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 8U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else if (((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_stream)) 
                                    & ((0x0dU < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_k0)) 
                                       | (0xffU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_k1))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 9U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else if (((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_stream)) 
                                    & (((0x13U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_k0)) 
                                        | (0x0bU < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_k1))) 
                                       | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_count 
                                          > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__param_limit)))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x0aU;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x0bU;
                        }
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x35U;
                    }
                } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x34U : 0x11U);
                } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x32U;
                } else if (VL_LTS_III(32, ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot))
                                            ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                           [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot]
                                            : 0U), vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_limit)) {
                    if (VL_LTS_III(32, ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot))
                                         ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot]
                                         : 0U), vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_base)) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x13U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x31U;
                    }
                } else if ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band_snapshot))) {
                    if (((((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__block_number) 
                          == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks) 
                         & ((((0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left[0U]) 
                              | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left[1U])) 
                             | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left[2U])) 
                            | (0x0fU != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_finished))))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x14U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1cU;
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x17U;
                }
            } else if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                                ? 0x30U : 0x21U) : 
                           ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                             ? 0x2eU : 0x2dU));
                } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x2cU;
                    } else if ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_bit))) {
                        if ((0U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__cfg_mod_next))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 4U;
                        }
                    }
                } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_bit_value) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x24U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__finish_return;
                    }
                } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_bit_value) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x24U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1dU;
                }
            } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((2U != (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_bits
                                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream] 
                                    - vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_position
                                    [(3U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream))]))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x23U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1dU;
                        }
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                            = ((1U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__suffix_left))
                                ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_return)
                                : 0x25U);
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x20U : (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arithmetic_bit) 
                                        | (0x0eU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_quotient)))
                                        ? (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arithmetic_bit) 
                                            & (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_k)))
                                            ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_return)
                                            : 0x25U)
                                        : 0x23U));
                }
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                    = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                        ? 0x20U : 0x21U);
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((0x8000U > (0x0000ffffU & (IData)(
                                                      (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                       >> 
                                                       (0x0000003fU 
                                                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                           << 4U))))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1dU;
                } else if ((0x8000U <= (0x0000ffffU 
                                        & (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                   >> 
                                                   (0x0000003fU 
                                                    & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                       << 4U))))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1dU;
                } else if (((0x4000U <= (0x0000ffffU 
                                         & (IData)(
                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                    >> 
                                                    (0x0000003fU 
                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                        << 4U)))))) 
                            & (0xc000U > (0x0000ffffU 
                                          & (IData)(
                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                     >> 
                                                     (0x0000003fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                         << 4U)))))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x1dU;
                } else if ((((0x0000ffffU & (IData)(
                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                     >> 
                                                     (0x0000003fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                         << 4U))))) 
                             < (0x0000ffffU & (IData)(
                                                      (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                       >> 
                                                       (0x0000003fU 
                                                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                           << 4U)))))) 
                            | ((0x0000ffffU & (IData)(
                                                      (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                       >> 
                                                       (0x0000003fU 
                                                        & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                           << 4U))))) 
                               > (0x0000ffffU & (IData)(
                                                        (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                         >> 
                                                         (0x0000003fU 
                                                          & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                             << 4U)))))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x22U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arithmetic_return;
                }
            } else if (((((0x58U <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__arithmetic_context)) 
                          | ((0x0000ffffU & (IData)(
                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                     >> 
                                                     (0x0000003fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                         << 4U))))) 
                             >= (0x0000ffffU & (IData)(
                                                       (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                        >> 
                                                        (0x0000003fU 
                                                         & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                            << 4U))))))) 
                         | ((0x0000ffffU & (IData)(
                                                   (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                    >> 
                                                    (0x0000003fU 
                                                     & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                        << 4U))))) 
                            < (0x0000ffffU & (IData)(
                                                     (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__low 
                                                      >> 
                                                      (0x0000003fU 
                                                       & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                          << 4U))))))) 
                        | ((0x0000ffffU & (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__code 
                                                   >> 
                                                   (0x0000003fU 
                                                    & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                       << 4U))))) 
                           > (0x0000ffffU & (IData)(
                                                    (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__high 
                                                     >> 
                                                     (0x0000003fU 
                                                      & ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream) 
                                                         << 4U)))))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x21U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x2bU;
            }
        } else if ((0x00000010U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                            = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                                ? (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_return)
                                : 0x1fU);
                    } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_position
                             [(3U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream))] 
                             >= vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_bits
                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream])) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x20U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                                = ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__byte_cache_valid) 
                                     >> (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream)) 
                                    & (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__byte_cache_offset
                                       [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream] 
                                       == (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_position
                                           [(3U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream))] 
                                           >> 3U)))
                                    ? 0x1fU : 0x39U);
                        }
                    } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__in_ready) {
                        if ((((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__block_number) 
                             == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks)) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x14U;
                        }
                    }
                } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                        if ((VL_GTS_III(32, 0xfffff800U, 
                                        VL_EXTENDS_II(32,16, 
                                                      (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__memory_byte) 
                                                        << 8U) 
                                                       | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_low_byte)))) 
                             | VL_LTS_III(32, 0x00000800U, 
                                          VL_EXTENDS_II(32,16, 
                                                        (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__memory_byte) 
                                                          << 8U) 
                                                         | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_low_byte)))))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x15U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                                = ((0x3fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_coefficient))
                                    ? 0x1cU : 0x19U);
                        }
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x39U;
                    }
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x39U : ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__initial_events)
                                        ? ((2U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                            ? 0x14U
                                            : 0x10U)
                                        : 0x17U));
                }
            } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                    = ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                        ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x2fU : ((((IData)(1U) 
                                         + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__block_number) 
                                        == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks)
                                        ? 0x27U : 0x17U))
                        : ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x38U : ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_mode)
                                        ? 0x19U : 0x23U)));
            } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268 
                        = ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_7__unzigzag 
                        = ((1U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268)
                            ? ((- (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268 
                                   >> 1U)) - (IData)(1U))
                            : (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_268 
                               >> 1U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269 
                        = ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_8__unzigzag 
                        = ((1U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269)
                            ? ((- (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269 
                                   >> 1U)) - (IData)(1U))
                            : (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_269 
                               >> 1U));
                    __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270 
                        = ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value);
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_9__unzigzag 
                        = ((1U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270)
                            ? ((- (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270 
                                   >> 1U)) - (IData)(1U))
                            : (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_270 
                               >> 1U));
                    if ((((0U == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_7__unzigzag) 
                          | VL_GTS_III(32, 0xfffff800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_8__unzigzag)) 
                         | VL_LTS_III(32, 0x00000800U, vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_9__unzigzag))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x11U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271 
                            = ((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value);
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_10__unzigzag 
                            = ((1U & __Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271)
                                ? ((- (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271 
                                       >> 1U)) - (IData)(1U))
                                : (__Vfunc_dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__unzigzag__value_271 
                                   >> 1U));
                        if ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))) {
                            vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1402 
                                = (((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                     ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left
                                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                     : 0U) - (IData)(1U));
                            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1403 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band;
                            vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1404 = 1U;
                            vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1405 
                                = (0x0000ffffU & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_10__unzigzag);
                            vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1406 
                                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band;
                            vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1407 = 1U;
                        }
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x18U;
                    }
                } else if (VL_GTES_III(32, ((IData)(1U) 
                                            + (((2U 
                                                 >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                                 ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_index
                                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                                 : 0U) 
                                               + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rice_value)), 
                                       ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                                         ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits
                                        [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                                         : 0U))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x10U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x23U;
                }
            } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((0U == ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                             ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left
                            [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                             : 0U))) {
                    if ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))) {
                        vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1408 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band;
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1409 = 1U;
                    }
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x27U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x23U;
                }
            } else {
                if ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))) {
                    vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1410 
                        = ((2U >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band))
                            ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts
                           [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band]
                            : 0U);
                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1411 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band;
                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_left_1412 = 1U;
                    vlSelfRef.__Vdly_Dim0__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1413 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__band;
                    vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__pending_value_1414 = 1U;
                }
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x11U;
            }
        } else if ((8U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? ((0x0fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__preload_count))
                                ? ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream))
                                    ? 0x10U : 0x0eU)
                                : 0x1dU) : 0x1dU);
                } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if ((0x015fU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__probability_index))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x0eU;
                    }
                } else if (((0U != (7U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_bits
                                    [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream])) 
                            & (0U != ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__memory_byte) 
                                      & (0x000000ffU 
                                         >> (7U & vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream_bits
                                             [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream])))))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0x0bU;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                } else {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                        = ((3U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream))
                            ? 0x0dU : 7U);
                }
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                    = ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                        ? ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                            ? 0x39U : 0x33U) : ((1U 
                                                 & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                                                 ? 
                                                ((5U 
                                                  == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__parameter_byte))
                                                  ? 0x0aU
                                                  : 8U)
                                                 : 0x39U));
            }
        } else if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                    if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__raw_mode) {
                        if ((((((((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[0U] 
                                   != (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks 
                                       << 7U)) | (0U 
                                                  != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[1U])) 
                                 | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[2U])) 
                                | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths[3U])) 
                               | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts[0U])) 
                              | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts[1U])) 
                             | (0U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts[2U]))) {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 5U;
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                        } else {
                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x14U;
                        }
                    } else if ((9U > vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths
                                [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__stream])) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 7U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 8U;
                    }
                } else if (((~ vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__crc) 
                            != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__received_crc)) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 2U;
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                } else {
                    vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_0__h32 
                        = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[9U]) 
                              << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[8U]) 
                            << 0x00000010U) | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[7U]) 
                                                << 8U) 
                                               | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[6U]));
                    if ((((((((((0x41U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[0U]) 
                                | (0x42U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[1U])) 
                               | (0x33U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[2U])) 
                              | (0x38U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[3U])) 
                             | (1U != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[4U])) 
                            | (1U < vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[5U])) 
                           | (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_0__h32 
                              != vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks)) 
                          | ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[11U]) 
                               << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[10U]) 
                             != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__blocks_w))) 
                         | (0U != (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[13U]) 
                                    << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[12U])))) {
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 3U;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                    } else {
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_1__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[17U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[16U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[15U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[14U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_3__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[25U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[24U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[22U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_2__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[21U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[20U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[19U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[18U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_4__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[29U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[27U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[26U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[17U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[16U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[15U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[14U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[33U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[32U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[31U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[30U]));
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair01_447 
                            = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_1__h32 
                               + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_2__h32);
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header_pair23_448 
                            = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_3__h32 
                               + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_4__h32);
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1415 
                            = (0x007fffffU & ((IData)(5U) 
                                              * vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1416 = 1U;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1417 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts_1418 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32;
                        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x36U;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1419 
                            = (0x007fffffU & ((IData)(0x0000000fU) 
                                              * vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1420 = 1U;
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[21U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[20U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[19U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[18U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[37U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[36U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[35U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[34U]));
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1421 
                            = (0x007fffffU & ((IData)(0x0000002bU) 
                                              * vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__nblocks));
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_limits_1422 = 1U;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1423 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts_1424 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32;
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[25U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[24U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[23U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[22U]));
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[41U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[40U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[39U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[38U]));
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1425 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32;
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1426 = 1U;
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__event_counts_1427 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_6__h32;
                        vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32 
                            = (((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[29U]) 
                                  << 8U) | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[28U]) 
                                << 0x00000010U) | (
                                                   ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[27U]) 
                                                    << 8U) 
                                                   | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__header[26U]));
                        vlSelfRef.__Vdly_Val__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1428 
                            = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT____VlemCall_5__h32;
                        vlSelfRef.__Vdly_Set__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__lengths_1429 = 1U;
                    }
                }
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                    = ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))
                        ? ((((IData)(1U) + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__scan_address) 
                            == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__packet_bytes))
                            ? 6U : 4U) : 0x39U);
            }
        } else if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__rd_rsp_valid) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                }
            } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT____Vcellinp__base__rd_rsp_valid) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 
                    = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__memory_return;
            }
        } else if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state))) {
            if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__b_req_ready) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 2U;
            }
        } else if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__configure_fire) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 0U;
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
            if ((((((((((5U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                        & (6U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch))) 
                       | (0x002eU > (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                      | (0xc000U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__packet_bytes))) 
                     | (0U == vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                    | (0x00001fa4U < vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__blocks)) 
                   | (0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                  | (0x0100U < (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))) 
                 | ((6U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dispatch)) 
                    & (1U != (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__entropy__cfg_blocks_w))))) {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 0U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_444 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__error_code_445 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__rd_req_valid_446 = 0U;
            } else {
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__busy_443 = 1U;
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__entropy__DOT__state_442 = 0x2aU;
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
                                if ((4U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                    if ((2U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                        if ((1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state))) {
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_52__hud32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[57U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[56U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[55U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[54U]));
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_53__hud32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[61U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[60U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[59U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[58U]));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum0_592 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_52__hud32 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_53__hud32);
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_54__hud32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[65U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[64U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[63U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[62U]));
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_55__hud32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[69U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[68U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[67U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_header[66U]));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__hud_sum1_593 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_54__hud32 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_55__hud32);
                                        }
                                    }
                                    if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state) 
                                                  >> 1U)))) {
                                        if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__state)))) {
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_28__inner32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[43U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[42U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[41U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[40U]));
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_29__inner32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[47U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[46U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[45U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[44U]));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum0_587 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_28__inner32 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_29__inner32);
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_30__inner32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[51U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[50U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[49U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[48U]));
                                            vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_31__inner32 
                                                = (
                                                   ((((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[55U]) 
                                                      << 8U) 
                                                     | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[54U]) 
                                                    << 0x00000010U) 
                                                   | (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[53U]) 
                                                       << 8U) 
                                                      | vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_header[52U]));
                                            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT__inner_sum1_588 
                                                = (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_30__inner32 
                                                   + vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__parser__DOT____VlemCall_31__inner32);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__receiving) 
             & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_data_valid))) {
            if ((0x01dfU == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__fill))) {
                if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__selected) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad1_700 
                        = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__receiving_bad) 
                           | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_data_error));
                }
                if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__selected)))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__completed_bad0_699 
                        = ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__lcd__DOT__receiving_bad) 
                           | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__line_data_error));
                }
            }
        }
    }
    if (((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))) {
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_total_429 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_id_386 = 0U;
        vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_hidden_438 = 0U;
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
                vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__full_total_429 
                    = ((0U == (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__plane))
                        ? 0x00001518U : 0x00000546U);
            }
        }
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__dequant__in_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__in_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__out_id_386 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__tid;
                }
            }
        }
        if (vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__pending_valid) {
            vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__out_hidden_438 
                = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__hidden_sample;
        }
    }
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_tag_760 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_tag_stage;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__y_sample_419 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__y;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__x_sample_418 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__scatter__DOT__x;
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__hud_q_753 
        = ((0xa4ffU >= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ha))
            ? vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__hud_mem
           [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ha]
            : 0U);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_hud_hit_757 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_hud_hit_stage));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__out_error_755 
        = ((1U & (~ (IData)(vlSelfRef.rst))) && ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_valid_stage) 
                                                 & ((0x02d0U 
                                                     <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_u_stage)) 
                                                    | ((0x01e0U 
                                                        <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_v_stage)) 
                                                       | ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_hud_hit_stage) 
                                                          & (0x5280U 
                                                             <= (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_hud_index_stage)))))));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[0U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__y_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ya]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[1U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__y_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ya] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[2U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__y_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ya]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_q_748[3U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__y_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ya] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[0U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cb_bottom_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[1U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cb_bottom_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[2U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cb_bottom_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_bottom_q_750[3U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cb_bottom_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[0U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cb_top_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[1U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cb_top_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[2U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cb_top_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cb_top_q_749[3U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cb_top_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__y_odd_q_759 
        = (1U & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_v_stage));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[0U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cr_bottom_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[1U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cr_bottom_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[2U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cr_bottom_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_bottom_q_752[3U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cr_bottom_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca1] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[0U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cr_top_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[1U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__0__KET____DOT__cr_top_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[2U] 
        = (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cr_top_mem
                  [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0]);
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__cr_top_q_751[3U] 
        = (IData)((vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__g_bank__BRA__1__KET____DOT__cr_top_mem
                   [vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__ca0] 
                   >> 0x00000020U));
    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__u_q_758 
        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__scanout__DOT__cache__DOT__rd_u_stage;
    if ((1U & (~ ((IData)(vlSelfRef.rst) | (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__kill))))) {
        if ((1U & (~ ((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state) 
                      >> 1U)))) {
            if ((1U & (~ (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__state)))) {
                if (((IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT____Vcellinp__dequant__in_valid) 
                     & (IData)(vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__in_ready))) {
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[0U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[0U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[1U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[1U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[2U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[2U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[3U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[3U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[4U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[4U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[5U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[5U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[6U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[6U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[7U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[7U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[8U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[8U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[9U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[9U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[10U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[10U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[11U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[11U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[12U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[12U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[13U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[13U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[14U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[14U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[15U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[15U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[16U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[16U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[17U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[17U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[18U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[18U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[19U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[19U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[20U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[20U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[21U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[21U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[22U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[22U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[23U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[23U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[24U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[24U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[25U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[25U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[26U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[26U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[27U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[27U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[28U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[28U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[29U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[29U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[30U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[30U];
                    vlSelfRef.__Vdly__dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__dequant__DOT__coefficients_412[31U] 
                        = vlSelfRef.dy71_platform_sim__DOT__system_core__DOT__receiver__DOT__base__DOT__held_coefficients[31U];
                }
            }
        }
    }
}
