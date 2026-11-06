// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vcu71_packet_prefix.h for the primary calling header

#ifndef VERILATED_VCU71_PACKET_PREFIX___024ROOT_H_
#define VERILATED_VCU71_PACKET_PREFIX___024ROOT_H_  // guard

#include "verilated.h"


class Vcu71_packet_prefix__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vcu71_packet_prefix___024root final {
  public:

    // DESIGN-SPECIFIC STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        VL_IN8(clk,0,0);
        VL_IN8(rst,0,0);
        VL_IN8(abort_i,0,0);
        VL_IN8(cfg_valid,0,0);
        VL_OUT8(cfg_ready,0,0);
        VL_IN16(cfg_packet_bytes,15,0);
        VL_IN8(cfg_last_valid,0,0);
        VL_IN(cfg_last_frame_id,31,0);
        VL_IN8(cfg_reference_valid,0,0);
        VL_IN(cfg_reference_id,31,0);
        VL_INW(cfg_reference_tag,127,0,4);
        VL_OUT8(rd_req_valid,0,0);
        VL_IN8(rd_req_ready,0,0);
        VL_OUT16(rd_req_addr,15,0);
        VL_IN8(rd_rsp_valid,0,0);
        VL_OUT8(rd_rsp_ready,0,0);
        VL_IN8(rd_rsp_data,7,0);
        VL_OUT8(metadata_valid,0,0);
        VL_IN8(metadata_ready,0,0);
        VL_OUT8(metadata_key,0,0);
        VL_OUT(metadata_frame_id,31,0);
        VL_OUT(metadata_reference_id,31,0);
        VL_OUTW(metadata_reference_tag,127,0,4);
        VL_OUTW(metadata_output_tag,127,0,4);
        VL_OUT8(metadata_block_size,7,0);
        VlUnpacked<SData/*15:0*/, 3> metadata_plane_addr;
        VlUnpacked<SData/*15:0*/, 3> metadata_plane_bytes;
        VlUnpacked<CData/*2:0*/, 3> metadata_plane_dispatch;
        VlUnpacked<IData/*16:0*/, 3> metadata_plane_blocks;
        VlUnpacked<SData/*8:0*/, 3> metadata_plane_blocks_w;
        VL_OUT16(metadata_hud_addr,15,0);
        VL_OUT16(metadata_hud_bytes,15,0);
        VL_OUTW(metadata_hud_reference_tag,127,0,4);
        VL_OUTW(metadata_hud_output_tag,127,0,4);
        VL_IN8(qmap_req_valid,0,0);
        VL_OUT8(qmap_req_ready,0,0);
        VL_IN16(qmap_req_index,10,0);
        VL_OUT8(qmap_rsp_valid,0,0);
        VL_OUT16(qmap_rsp_index,10,0);
        VL_OUT8(qmap_rsp_code,1,0);
        VL_IN8(commit_valid,0,0);
        VL_OUT8(commit_ready,0,0);
        VL_OUT8(busy,0,0);
        VL_OUT8(done,0,0);
        VL_OUT8(aborted,0,0);
        VL_OUT8(error,0,0);
        VL_OUT8(error_code,7,0);
        VL_OUT8(debug_state,7,0);
        VL_OUT(memory_reads,31,0);
        CData/*0:0*/ cu71_packet_prefix__DOT____VlemCond_64;
        CData/*0:0*/ cu71_packet_prefix__DOT____VlemCond_28;
        CData/*7:0*/ cu71_packet_prefix__DOT__state;
        CData/*0:0*/ cu71_packet_prefix__DOT__last_valid;
        CData/*0:0*/ cu71_packet_prefix__DOT__reference_valid;
        CData/*0:0*/ cu71_packet_prefix__DOT__outer_validated;
        CData/*0:0*/ cu71_packet_prefix__DOT__inner_validated;
        CData/*0:0*/ cu71_packet_prefix__DOT__byte_bad;
        CData/*7:0*/ __Vdfg_Regularize_502;
        CData/*0:0*/ __Vdfg_Regularize_507;
        CData/*7:0*/ __Vdfg_Regularize_523;
        CData/*0:0*/ __Vdfg_Regularize_524;
        CData/*0:0*/ __Vdfg_Regularize_525;
        CData/*0:0*/ __Vdfg_Regularize_526;
        CData/*0:0*/ __Vdfg_Regularize_527;
    };
    struct {
        CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__rst__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__abort_i__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cfg_valid__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cfg_last_valid__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__cfg_reference_valid__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__rd_req_ready__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__rd_rsp_valid__0;
        CData/*7:0*/ __Vtrigprevexpr___TOP__rd_rsp_data__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__metadata_ready__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__qmap_req_valid__0;
        CData/*0:0*/ __Vtrigprevexpr___TOP__commit_valid__0;
        CData/*0:0*/ __VicoDidInit;
        CData/*0:0*/ __Vtrigprevexpr___TOP__clk__1;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_60__hud16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_59__hud16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_36__inner16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_35__inner16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_10__outer16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_9__outer16;
        SData/*15:0*/ cu71_packet_prefix__DOT____VlemCall_8__outer16;
        SData/*15:0*/ cu71_packet_prefix__DOT__packet_bytes;
        SData/*15:0*/ cu71_packet_prefix__DOT__scan_addr;
        SData/*15:0*/ cu71_packet_prefix__DOT__inner_bytes;
        SData/*15:0*/ cu71_packet_prefix__DOT__plane_start__BRA__0__KET__;
        SData/*15:0*/ cu71_packet_prefix__DOT__plane_start__BRA__1__KET__;
        SData/*15:0*/ cu71_packet_prefix__DOT__plane_start__BRA__2__KET__;
        SData/*15:0*/ cu71_packet_prefix__DOT__vector_start;
        SData/*15:0*/ cu71_packet_prefix__DOT__vector_end;
        SData/*15:0*/ cu71_packet_prefix__DOT__prefix0;
        SData/*15:0*/ cu71_packet_prefix__DOT__prefix_yu;
        SData/*15:0*/ cu71_packet_prefix__DOT__prefix_y;
        SData/*15:0*/ __Vtrigprevexpr___TOP__cfg_packet_bytes__0;
        SData/*10:0*/ __Vtrigprevexpr___TOP__qmap_req_index__0;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_63__hud128;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_62__hud128;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_61__hud128;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_58__hud32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_57__hud32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_56__hud32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_55__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_54__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_53__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_52__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_51__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_50__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_49__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_48__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_47__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_46__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_45__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_44__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_43__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_42__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_41__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_40__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_39__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_38__inner32;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_37__inner128;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_34__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_33__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_32__inner32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_31__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_30__outer32;
    };
    struct {
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_29__outer32;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_27__outer128;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_26__outer128;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_25__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_24__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_23__outer32;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_22__outer128;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_21__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_20__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_19__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_18__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_17__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_16__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_15__outer32;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_14__outer32;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_13__outer128;
        IData/*31:0*/ cu71_packet_prefix__DOT____VlemCall_12__outer32;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT____VlemCall_11__outer128;
        IData/*31:0*/ cu71_packet_prefix__DOT__last_frame_id;
        IData/*31:0*/ cu71_packet_prefix__DOT__reference_id;
        VlWide<4>/*127:0*/ cu71_packet_prefix__DOT__reference_tag;
        IData/*31:0*/ cu71_packet_prefix__DOT__crc_outer;
        IData/*31:0*/ cu71_packet_prefix__DOT__crc_inner;
        IData/*31:0*/ cu71_packet_prefix__DOT__crc_hud;
        IData/*31:0*/ cu71_packet_prefix__DOT__received_outer;
        IData/*31:0*/ cu71_packet_prefix__DOT__received_inner;
        IData/*31:0*/ cu71_packet_prefix__DOT__received_hud;
        IData/*31:0*/ __Vdfg_Regularize_503;
        IData/*31:0*/ __Vdfg_Regularize_504;
        IData/*31:0*/ __Vdfg_Regularize_505;
        IData/*31:0*/ __Vdfg_Regularize_506;
        IData/*31:0*/ __Vtrigprevexpr___TOP__cfg_last_frame_id__0;
        IData/*31:0*/ __Vtrigprevexpr___TOP__cfg_reference_id__0;
        VlWide<4>/*127:0*/ __Vtrigprevexpr___TOP__cfg_reference_tag__0;
        VlUnpacked<CData/*7:0*/, 76> cu71_packet_prefix__DOT__outer_header;
        VlUnpacked<CData/*7:0*/, 60> cu71_packet_prefix__DOT__inner_header;
        VlUnpacked<CData/*7:0*/, 106> cu71_packet_prefix__DOT__hud_header;
        VlUnpacked<CData/*7:0*/, 338> cu71_packet_prefix__DOT__qmap_mem;
        VlUnpacked<QData/*63:0*/, 1> __VstlTriggered;
        VlUnpacked<QData/*63:0*/, 2> __VicoTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VactTriggered;
        VlUnpacked<QData/*63:0*/, 1> __VnbaTriggered;
    };

    // INTERNAL VARIABLES
    Vcu71_packet_prefix__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vcu71_packet_prefix___024root(Vcu71_packet_prefix__Syms* symsp, const char* namep);
    ~Vcu71_packet_prefix___024root();
    VL_UNCOPYABLE(Vcu71_packet_prefix___024root);

    // INTERNAL METHODS
};


#endif  // guard
