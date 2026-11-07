// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vtb_shared_sdram.h for the primary calling header

#include "Vtb_shared_sdram__pch.h"
#include "Vtb_shared_sdram__Syms.h"
#include "Vtb_shared_sdram___024root.h"

VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__0(Vtb_shared_sdram___024root* vlSelf);
VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__1(Vtb_shared_sdram___024root* vlSelf);

VL_INLINE_OPT VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1\n"); );
    // Init
    IData/*31:0*/ tb_shared_sdram__DOT__before_commands;
    tb_shared_sdram__DOT__before_commands = 0;
    IData/*31:0*/ tb_shared_sdram__DOT__before_writes;
    tb_shared_sdram__DOT__before_writes = 0;
    IData/*31:0*/ tb_shared_sdram__DOT__before_reads;
    tb_shared_sdram__DOT__before_reads = 0;
    IData/*31:0*/ tb_shared_sdram__DOT__grants_seen;
    tb_shared_sdram__DOT__grants_seen = 0;
    CData/*1:0*/ tb_shared_sdram__DOT__last_owner;
    tb_shared_sdram__DOT__last_owner = 0;
    VlWide<4>/*127:0*/ tb_shared_sdram__DOT__saved_read;
    VL_ZERO_W(128, tb_shared_sdram__DOT__saved_read);
    QData/*63:0*/ tb_shared_sdram__DOT__payload;
    tb_shared_sdram__DOT__payload = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__2__count;
    __Vtask_tb_shared_sdram__DOT__step__2__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__3__ok;
    __Vtask_tb_shared_sdram__DOT__check__3__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__3__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__10__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__10__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__11__count;
    __Vtask_tb_shared_sdram__DOT__step__11__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__12__ok;
    __Vtask_tb_shared_sdram__DOT__check__12__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__12__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__13__ok;
    __Vtask_tb_shared_sdram__DOT__check__13__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__13__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__14__count;
    __Vtask_tb_shared_sdram__DOT__step__14__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__16__count;
    __Vtask_tb_shared_sdram__DOT__step__16__count = 0;
    IData/*23:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__17__address;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__17__data;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__data = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__17__count;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__18__ok;
    __Vtask_tb_shared_sdram__DOT__check__18__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__18__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__19__ok;
    __Vtask_tb_shared_sdram__DOT__check__19__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__19__label_text;
    VlWide<4>/*127:0*/ __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout;
    VL_ZERO_W(128, __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout);
    IData/*23:0*/ __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address;
    __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address = 0;
    VlWide<4>/*127:0*/ __Vfunc_tb_shared_sdram__DOT__initial_line__20__result;
    VL_ZERO_W(128, __Vfunc_tb_shared_sdram__DOT__initial_line__20__result);
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__21__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__21__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__21__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__22__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__22__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__23__count;
    __Vtask_tb_shared_sdram__DOT__step__23__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__24__ok;
    __Vtask_tb_shared_sdram__DOT__check__24__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__24__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__25__count;
    __Vtask_tb_shared_sdram__DOT__step__25__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__27__count;
    __Vtask_tb_shared_sdram__DOT__step__27__count = 0;
    IData/*23:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__28__address;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__28__data;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__data = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__28__count;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__29__ok;
    __Vtask_tb_shared_sdram__DOT__check__29__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__29__label_text;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__30__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__30__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__30__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__30__bank = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__31__count;
    __Vtask_tb_shared_sdram__DOT__step__31__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__32__ok;
    __Vtask_tb_shared_sdram__DOT__check__32__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__32__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__33__count;
    __Vtask_tb_shared_sdram__DOT__step__33__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__34__ok;
    __Vtask_tb_shared_sdram__DOT__check__34__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__34__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__35__count;
    __Vtask_tb_shared_sdram__DOT__step__35__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__36__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__36__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__37__count;
    __Vtask_tb_shared_sdram__DOT__step__37__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__38__ok;
    __Vtask_tb_shared_sdram__DOT__check__38__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__38__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__39__count;
    __Vtask_tb_shared_sdram__DOT__step__39__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__41__count;
    __Vtask_tb_shared_sdram__DOT__step__41__count = 0;
    IData/*23:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__42__address;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__42__data;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__data = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__42__count;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__43__ok;
    __Vtask_tb_shared_sdram__DOT__check__43__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__43__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__44__count;
    __Vtask_tb_shared_sdram__DOT__step__44__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__45__ok;
    __Vtask_tb_shared_sdram__DOT__check__45__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__45__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__46__count;
    __Vtask_tb_shared_sdram__DOT__step__46__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__48__count;
    __Vtask_tb_shared_sdram__DOT__step__48__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__49__ok;
    __Vtask_tb_shared_sdram__DOT__check__49__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__49__label_text;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__50__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__50__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__50__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__51__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__51__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__52__count;
    __Vtask_tb_shared_sdram__DOT__step__52__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__53__ok;
    __Vtask_tb_shared_sdram__DOT__check__53__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__53__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__54__count;
    __Vtask_tb_shared_sdram__DOT__step__54__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__56__count;
    __Vtask_tb_shared_sdram__DOT__step__56__count = 0;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__57__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__57__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__57__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__58__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__58__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__59__count;
    __Vtask_tb_shared_sdram__DOT__step__59__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__60__ok;
    __Vtask_tb_shared_sdram__DOT__check__60__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__60__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__61__count;
    __Vtask_tb_shared_sdram__DOT__step__61__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__63__count;
    __Vtask_tb_shared_sdram__DOT__step__63__count = 0;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__64__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__64__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__64__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__65__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__65__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__66__count;
    __Vtask_tb_shared_sdram__DOT__step__66__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__67__ok;
    __Vtask_tb_shared_sdram__DOT__check__67__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__67__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__68__count;
    __Vtask_tb_shared_sdram__DOT__step__68__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__70__count;
    __Vtask_tb_shared_sdram__DOT__step__70__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__71__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__71__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__71__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__71__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__72__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__72__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__73__count;
    __Vtask_tb_shared_sdram__DOT__step__73__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__74__ok;
    __Vtask_tb_shared_sdram__DOT__check__74__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__74__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__75__ok;
    __Vtask_tb_shared_sdram__DOT__check__75__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__75__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__76__count;
    __Vtask_tb_shared_sdram__DOT__step__76__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__78__count;
    __Vtask_tb_shared_sdram__DOT__step__78__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__79__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__79__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__79__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__79__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__80__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__80__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__81__count;
    __Vtask_tb_shared_sdram__DOT__step__81__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__82__ok;
    __Vtask_tb_shared_sdram__DOT__check__82__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__82__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__83__ok;
    __Vtask_tb_shared_sdram__DOT__check__83__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__83__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__84__count;
    __Vtask_tb_shared_sdram__DOT__step__84__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__86__count;
    __Vtask_tb_shared_sdram__DOT__step__86__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__87__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__87__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__87__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__87__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__88__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__88__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__89__count;
    __Vtask_tb_shared_sdram__DOT__step__89__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__90__ok;
    __Vtask_tb_shared_sdram__DOT__check__90__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__90__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__91__ok;
    __Vtask_tb_shared_sdram__DOT__check__91__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__91__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__92__count;
    __Vtask_tb_shared_sdram__DOT__step__92__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__94__count;
    __Vtask_tb_shared_sdram__DOT__step__94__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__95__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__95__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__95__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__95__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__96__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__96__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__97__count;
    __Vtask_tb_shared_sdram__DOT__step__97__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__98__ok;
    __Vtask_tb_shared_sdram__DOT__check__98__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__98__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__99__ok;
    __Vtask_tb_shared_sdram__DOT__check__99__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__99__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__100__count;
    __Vtask_tb_shared_sdram__DOT__step__100__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__102__count;
    __Vtask_tb_shared_sdram__DOT__step__102__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__103__ok;
    __Vtask_tb_shared_sdram__DOT__check__103__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__103__label_text;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__104__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__104__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__104__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__105__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__105__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__106__count;
    __Vtask_tb_shared_sdram__DOT__step__106__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__107__ok;
    __Vtask_tb_shared_sdram__DOT__check__107__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__107__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__108__count;
    __Vtask_tb_shared_sdram__DOT__step__108__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__110__count;
    __Vtask_tb_shared_sdram__DOT__step__110__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__111__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__111__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__111__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__111__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__112__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__112__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__113__count;
    __Vtask_tb_shared_sdram__DOT__step__113__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__114__ok;
    __Vtask_tb_shared_sdram__DOT__check__114__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__114__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__115__ok;
    __Vtask_tb_shared_sdram__DOT__check__115__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__115__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__116__count;
    __Vtask_tb_shared_sdram__DOT__step__116__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__118__count;
    __Vtask_tb_shared_sdram__DOT__step__118__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__119__ok;
    __Vtask_tb_shared_sdram__DOT__check__119__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__119__label_text;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__120__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__120__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__121__count;
    __Vtask_tb_shared_sdram__DOT__step__121__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__123__count;
    __Vtask_tb_shared_sdram__DOT__step__123__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__124__ok;
    __Vtask_tb_shared_sdram__DOT__check__124__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__124__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__125__count;
    __Vtask_tb_shared_sdram__DOT__step__125__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__127__count;
    __Vtask_tb_shared_sdram__DOT__step__127__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__128__ok;
    __Vtask_tb_shared_sdram__DOT__check__128__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__128__label_text;
    IData/*23:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__129__address;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__129__data;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__data = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__129__count;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__130__ok;
    __Vtask_tb_shared_sdram__DOT__check__130__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__130__label_text;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__131__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__132__count;
    __Vtask_tb_shared_sdram__DOT__step__132__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__134__count;
    __Vtask_tb_shared_sdram__DOT__step__134__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__135__ok;
    __Vtask_tb_shared_sdram__DOT__check__135__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__135__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__136__ok;
    __Vtask_tb_shared_sdram__DOT__check__136__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__136__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__137__count;
    __Vtask_tb_shared_sdram__DOT__step__137__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__139__count;
    __Vtask_tb_shared_sdram__DOT__step__139__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__140__ok;
    __Vtask_tb_shared_sdram__DOT__check__140__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__140__label_text;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__141__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__141__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__141__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__bank = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__142__count;
    __Vtask_tb_shared_sdram__DOT__step__142__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__143__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__143__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__144__count;
    __Vtask_tb_shared_sdram__DOT__step__144__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__145__ok;
    __Vtask_tb_shared_sdram__DOT__check__145__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__145__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__146__count;
    __Vtask_tb_shared_sdram__DOT__step__146__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__148__count;
    __Vtask_tb_shared_sdram__DOT__step__148__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__149__ok;
    __Vtask_tb_shared_sdram__DOT__check__149__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__149__label_text;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__150__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__150__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__150__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__150__bank = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__151__count;
    __Vtask_tb_shared_sdram__DOT__step__151__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__152__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__152__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__153__count;
    __Vtask_tb_shared_sdram__DOT__step__153__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__154__ok;
    __Vtask_tb_shared_sdram__DOT__check__154__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__154__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__155__ok;
    __Vtask_tb_shared_sdram__DOT__check__155__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__155__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__156__count;
    __Vtask_tb_shared_sdram__DOT__step__156__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__158__count;
    __Vtask_tb_shared_sdram__DOT__step__158__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__159__ok;
    __Vtask_tb_shared_sdram__DOT__check__159__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__159__label_text;
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__160__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__160__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__160__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__161__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__161__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__162__count;
    __Vtask_tb_shared_sdram__DOT__step__162__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__163__ok;
    __Vtask_tb_shared_sdram__DOT__check__163__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__163__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__164__count;
    __Vtask_tb_shared_sdram__DOT__step__164__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__166__count;
    __Vtask_tb_shared_sdram__DOT__step__166__count = 0;
    IData/*18:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__167__address;
    __Vtask_tb_shared_sdram__DOT__rd_issue__167__address = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__rd_issue__167__bank;
    __Vtask_tb_shared_sdram__DOT__rd_issue__167__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__rd_finish__168__expected_error;
    __Vtask_tb_shared_sdram__DOT__rd_finish__168__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__169__count;
    __Vtask_tb_shared_sdram__DOT__step__169__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__170__ok;
    __Vtask_tb_shared_sdram__DOT__check__170__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__170__label_text;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__171__ok;
    __Vtask_tb_shared_sdram__DOT__check__171__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__171__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__172__count;
    __Vtask_tb_shared_sdram__DOT__step__172__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__174__count;
    __Vtask_tb_shared_sdram__DOT__step__174__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__175__count;
    __Vtask_tb_shared_sdram__DOT__step__175__count = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__177__count;
    __Vtask_tb_shared_sdram__DOT__step__177__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__178__ok;
    __Vtask_tb_shared_sdram__DOT__check__178__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__178__label_text;
    // Body
    vlSelf->tb_shared_sdram__DOT__power_on_reset = 1U;
    vlSelf->tb_shared_sdram__DOT__wr_req_epoch = 1U;
    vlSelf->tb_shared_sdram__DOT__rd_req_epoch = 2U;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation = 0xaU;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 4U;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__power_on_reset = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__2__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__2__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    VL_WRITEF("INIT_COUNTERS mrs=0 refreshes=0 writes=0\n");
    __Vtask_tb_shared_sdram__DOT__check__3__label_text = 
        std::string{"controller_initialized_real_pins"};
    __Vtask_tb_shared_sdram__DOT__check__3__ok = 0U;
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__3__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__3__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__3__label_text));
    vlSelf->__Vfork_1__sync.init(2U, nullptr);
    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__0(vlSelf);
    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__1(vlSelf);
    co_await vlSelf->__Vfork_1__sync.join(nullptr, 
                                          "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                          130);
    __Vtask_tb_shared_sdram__DOT__rd_finish__10__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__11__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__11__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__12__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__12__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__10__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__12__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__12__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__12__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__10__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__13__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__13__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__13__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__13__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__13__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__14__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__14__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__16__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__16__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__audit_words__17__count = 4U;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__data = 0x1122334455667788ULL;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__address = 0x400000U;
    __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__17__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__17__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__18__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__18__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__17__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__18__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__18__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__18__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__17__unnamedblk2__DOT__i);
    }
    __Vtask_tb_shared_sdram__DOT__check__19__label_text = 
        std::string{"concurrent_different_banks"};
    __Vtask_tb_shared_sdram__DOT__check__19__ok = VL_EQ_W(4, vlSelf->tb_shared_sdram__DOT__rd_rsp_data, 
                                                          ([&]() {
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address = 0x800000U;
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[0U] 
                    = ((0xffff0000U & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[0U]) 
                       | (0xffffU & (0x5a3cU ^ __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address)));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[0U] 
                    = ((0xffffU & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[0U]) 
                       | (0xffff0000U & (0x5a3c0000U 
                                         ^ (((IData)(1U) 
                                             + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address) 
                                            << 0x10U))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[1U] 
                    = ((0xffff0000U & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[1U]) 
                       | (0xffffU & (0x5a3cU ^ ((IData)(2U) 
                                                + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[1U] 
                    = ((0xffffU & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[1U]) 
                       | (0xffff0000U & (0x5a3c0000U 
                                         ^ (((IData)(3U) 
                                             + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address) 
                                            << 0x10U))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[2U] 
                    = ((0xffff0000U & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[2U]) 
                       | (0xffffU & (0x5a3cU ^ ((IData)(4U) 
                                                + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[2U] 
                    = ((0xffffU & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[2U]) 
                       | (0xffff0000U & (0x5a3c0000U 
                                         ^ (((IData)(5U) 
                                             + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address) 
                                            << 0x10U))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[3U] 
                    = ((0xffff0000U & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[3U]) 
                       | (0xffffU & (0x5a3cU ^ ((IData)(6U) 
                                                + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[3U] 
                    = ((0xffffU & __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[3U]) 
                       | (0xffff0000U & (0x5a3c0000U 
                                         ^ (((IData)(7U) 
                                             + __Vfunc_tb_shared_sdram__DOT__initial_line__20__word_address) 
                                            << 0x10U))));
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout[0U] 
                    = __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[0U];
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout[1U] 
                    = __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[1U];
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout[2U] 
                    = __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[2U];
                __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout[3U] 
                    = __Vfunc_tb_shared_sdram__DOT__initial_line__20__result[3U];
            }(), __Vfunc_tb_shared_sdram__DOT__initial_line__20__Vfuncout));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__19__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__19__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__19__label_text));
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__data = 0x123456789abcdefULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__21__address = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__21__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__21__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__21__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__22__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__23__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__23__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__24__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__24__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__22__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__24__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__24__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__24__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__25__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__25__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__27__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__27__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__audit_words__28__count = 4U;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__data = 0x123456789abcdefULL;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__address = 0U;
    __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__28__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__28__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__29__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__29__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__28__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__29__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__29__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__29__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__28__unnamedblk2__DOT__i);
    }
    __Vtask_tb_shared_sdram__DOT__rd_issue__30__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__30__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__30__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__30__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__31__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__31__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__32__label_text = 
        std::string{"write_ack_then_same_address_read"};
    __Vtask_tb_shared_sdram__DOT__check__32__ok = (0x123456789abcdefULL 
                                                   == 
                                                   (((QData)((IData)(
                                                                     vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U])) 
                                                     << 0x20U) 
                                                    | (QData)((IData)(
                                                                      vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U]))));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__32__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__32__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__32__label_text));
    tb_shared_sdram__DOT__saved_read[0U] = vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U];
    tb_shared_sdram__DOT__saved_read[1U] = vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U];
    tb_shared_sdram__DOT__saved_read[2U] = vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U];
    tb_shared_sdram__DOT__saved_read[3U] = vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U];
    tb_shared_sdram__DOT__before_commands = (vlSelf->tb_shared_sdram__DOT__writer_commands 
                                             + vlSelf->tb_shared_sdram__DOT__reader_commands);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = 8U;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = 0x8877665544332211ULL;
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 1U;
    vlSelf->tb_shared_sdram__DOT__rd_reset = 1U;
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    __Vtask_tb_shared_sdram__DOT__step__33__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__33__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    __Vtask_tb_shared_sdram__DOT__check__34__label_text = 
        std::string{"held_success_immutable_and_ownership_blocked"};
    __Vtask_tb_shared_sdram__DOT__check__34__ok = (
                                                   ((((2U 
                                                       == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)) 
                                                     & (0U 
                                                        == 
                                                        ((((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[0U]) 
                                                           | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] 
                                                              ^ 
                                                              tb_shared_sdram__DOT__saved_read[1U])) 
                                                          | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] 
                                                             ^ 
                                                             tb_shared_sdram__DOT__saved_read[2U])) 
                                                         | (vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] 
                                                            ^ 
                                                            tb_shared_sdram__DOT__saved_read[3U])))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error))) 
                                                   & ((vlSelf->tb_shared_sdram__DOT__writer_commands 
                                                       + vlSelf->tb_shared_sdram__DOT__reader_commands) 
                                                      == tb_shared_sdram__DOT__before_commands));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__34__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__34__label_text));
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_reset = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__35__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__35__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       147);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           147);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       148);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__36__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__37__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__37__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__38__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__38__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__36__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__38__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__38__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__38__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__39__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__39__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__41__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__41__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__audit_words__42__count = 4U;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__data = 0x8877665544332211ULL;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__address = 0x20U;
    __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__42__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__42__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__43__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__43__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__42__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__43__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__43__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__43__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__42__unnamedblk2__DOT__i);
    }
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = 0x20U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = 0x40U;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = 0x5555aaaa3333ccccULL;
    tb_shared_sdram__DOT__grants_seen = 0U;
    tb_shared_sdram__DOT__last_owner = 0U;
    while (VL_GTS_III(32, 8U, tb_shared_sdram__DOT__grants_seen)) {
        __Vtask_tb_shared_sdram__DOT__step__44__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__44__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
        if (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
             & ((IData)(vlSelf->tb_shared_sdram__DOT__source_owner) 
                != (IData)(tb_shared_sdram__DOT__last_owner)))) {
            if (VL_UNLIKELY((0U != (IData)(tb_shared_sdram__DOT__last_owner)))) {
                __Vtask_tb_shared_sdram__DOT__check__45__label_text = 
                    std::string{"round_robin_whole_transaction"};
                __Vtask_tb_shared_sdram__DOT__check__45__ok 
                    = ((IData)(vlSelf->tb_shared_sdram__DOT__source_owner) 
                       != (IData)(tb_shared_sdram__DOT__last_owner));
                if (vlSymsp->_vm_contextp__->assertOn()) {
                    if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__45__ok))))) {
                        if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                            VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                                      64,VL_TIME_UNITED_Q(1000),
                                      -9,vlSymsp->name(),
                                      -1,&(__Vtask_tb_shared_sdram__DOT__check__45__label_text));
                            VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                        }
                    }
                }
                vlSelf->tb_shared_sdram__DOT__checks 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__checks);
                VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                          -1,&(__Vtask_tb_shared_sdram__DOT__check__45__label_text));
            }
            tb_shared_sdram__DOT__last_owner = vlSelf->tb_shared_sdram__DOT__source_owner;
            tb_shared_sdram__DOT__grants_seen = ((IData)(1U) 
                                                 + tb_shared_sdram__DOT__grants_seen);
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    while ((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) {
        __Vtask_tb_shared_sdram__DOT__step__46__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__46__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__48__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__48__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__49__label_text = 
        std::string{"continuous_valid_reaccept_guard_and_fairness"};
    __Vtask_tb_shared_sdram__DOT__check__49__ok = (8U 
                                                   == tb_shared_sdram__DOT__grants_seen);
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__49__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__49__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__49__label_text));
    tb_shared_sdram__DOT__before_commands = (vlSelf->tb_shared_sdram__DOT__writer_commands 
                                             + vlSelf->tb_shared_sdram__DOT__reader_commands);
    vlSelf->tb_shared_sdram__DOT__wr_req_epoch = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__data = 0ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__50__address = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__50__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__50__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__50__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__51__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__52__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__52__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__53__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__53__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__51__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__53__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__53__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__53__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__54__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__54__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__56__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__56__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_req_epoch = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__data = 0ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__57__address = 1U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__57__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__57__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__57__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__58__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__59__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__59__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__60__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__60__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__58__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__60__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__60__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__60__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__61__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__61__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__63__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__63__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__bank = 3U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__data = 0ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__64__address = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__64__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__64__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__64__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__65__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__66__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__66__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__67__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__67__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__65__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__67__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__67__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__67__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__68__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__68__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__70__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__70__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__rd_req_epoch = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__71__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__71__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__71__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__71__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__72__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__73__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__73__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__74__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__74__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__72__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__74__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__74__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__74__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__72__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__75__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__75__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__75__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__75__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__75__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__76__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__76__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__78__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__78__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__rd_req_epoch = 2U;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation = 0xffffffffU;
    __Vtask_tb_shared_sdram__DOT__rd_issue__79__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__79__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__79__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__79__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__80__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__81__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__81__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__82__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__82__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__80__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__82__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__82__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__82__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__80__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__83__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__83__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__83__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__83__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__83__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__84__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__84__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__86__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__86__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__rd_issue__87__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__87__address = 1U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__87__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__87__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__88__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__89__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__89__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__90__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__90__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__88__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__90__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__90__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__90__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__88__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__91__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__91__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__91__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__91__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__91__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__92__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__92__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__94__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__94__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__rd_issue__95__bank = 3U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__95__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__95__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__95__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__96__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__97__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__97__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__98__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__98__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                                   == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__96__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__98__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__98__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__98__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__96__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__99__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__99__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__99__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__99__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__99__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__100__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__100__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__102__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__102__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__103__label_text = 
        std::string{"invalid_identities_no_physical_commands"};
    __Vtask_tb_shared_sdram__DOT__check__103__ok = 
        ((vlSelf->tb_shared_sdram__DOT__writer_commands 
          + vlSelf->tb_shared_sdram__DOT__reader_commands) 
         == tb_shared_sdram__DOT__before_commands);
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__103__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__103__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__103__label_text));
    tb_shared_sdram__DOT__before_commands = (vlSelf->tb_shared_sdram__DOT__writer_commands 
                                             + vlSelf->tb_shared_sdram__DOT__reader_commands);
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__data = 0ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__104__address = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__104__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__104__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__104__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__105__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__106__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__106__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__107__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__107__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__105__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__107__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__107__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__107__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__108__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__108__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__110__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__110__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__rd_issue__111__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__111__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__111__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__111__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__112__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__113__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__113__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__114__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__114__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__112__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__114__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__114__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__114__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__112__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__115__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__115__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__115__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__115__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__115__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__116__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__116__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__118__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__118__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__119__label_text = 
        std::string{"cancel_before_command"};
    __Vtask_tb_shared_sdram__DOT__check__119__ok = 
        ((vlSelf->tb_shared_sdram__DOT__writer_commands 
          + vlSelf->tb_shared_sdram__DOT__reader_commands) 
         == tb_shared_sdram__DOT__before_commands);
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__119__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__119__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__119__label_text));
    tb_shared_sdram__DOT__before_writes = vlSelf->tb_shared_sdram__DOT__writes;
    tb_shared_sdram__DOT__before_commands = vlSelf->tb_shared_sdram__DOT__writer_commands;
    tb_shared_sdram__DOT__payload = 0xf1e2d3c4b5a69789ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__address = 0x80U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__120__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__120__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    while (VL_GTS_III(32, 1U, (vlSelf->tb_shared_sdram__DOT__writer_commands 
                               - tb_shared_sdram__DOT__before_commands))) {
        __Vtask_tb_shared_sdram__DOT__step__121__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__121__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__123__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__123__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__124__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__124__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__124__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__125__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__125__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__127__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__127__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__128__label_text = 
        std::string{"canceled_writer_prefix_physically_drained"};
    __Vtask_tb_shared_sdram__DOT__check__128__ok = 
        (((1U == (vlSelf->tb_shared_sdram__DOT__writer_commands 
                  - tb_shared_sdram__DOT__before_commands)) 
          & (1U == (vlSelf->tb_shared_sdram__DOT__writes 
                    - tb_shared_sdram__DOT__before_writes))) 
         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending)));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__128__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
    __Vtask_tb_shared_sdram__DOT__audit_words__129__count = 1U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__address = 0x200U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__129__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__129__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__130__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__130__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__129__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__130__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i);
    }
    tb_shared_sdram__DOT__before_writes = vlSelf->tb_shared_sdram__DOT__writes;
    tb_shared_sdram__DOT__before_commands = vlSelf->tb_shared_sdram__DOT__writer_commands;
    tb_shared_sdram__DOT__payload = 0xf1e2d3c4b5a6978aULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__address = 0x80U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__120__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__120__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    while (VL_GTS_III(32, 2U, (vlSelf->tb_shared_sdram__DOT__writer_commands 
                               - tb_shared_sdram__DOT__before_commands))) {
        __Vtask_tb_shared_sdram__DOT__step__121__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__121__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__123__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__123__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__124__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__124__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__124__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__125__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__125__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__127__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__127__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__128__label_text = 
        std::string{"canceled_writer_prefix_physically_drained"};
    __Vtask_tb_shared_sdram__DOT__check__128__ok = 
        (((2U == (vlSelf->tb_shared_sdram__DOT__writer_commands 
                  - tb_shared_sdram__DOT__before_commands)) 
          & (2U == (vlSelf->tb_shared_sdram__DOT__writes 
                    - tb_shared_sdram__DOT__before_writes))) 
         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending)));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__128__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
    __Vtask_tb_shared_sdram__DOT__audit_words__129__count = 2U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__address = 0x200U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__129__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__129__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__130__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__130__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__129__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__130__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i);
    }
    tb_shared_sdram__DOT__before_writes = vlSelf->tb_shared_sdram__DOT__writes;
    tb_shared_sdram__DOT__before_commands = vlSelf->tb_shared_sdram__DOT__writer_commands;
    tb_shared_sdram__DOT__payload = 0xf1e2d3c4b5a6978bULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__wr_issue__120__address = 0x80U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__120__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__120__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__120__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    while (VL_GTS_III(32, 3U, (vlSelf->tb_shared_sdram__DOT__writer_commands 
                               - tb_shared_sdram__DOT__before_commands))) {
        __Vtask_tb_shared_sdram__DOT__step__121__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__121__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__123__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__123__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__124__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__124__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__122__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__124__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__124__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__125__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__125__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__127__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__127__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__128__label_text = 
        std::string{"canceled_writer_prefix_physically_drained"};
    __Vtask_tb_shared_sdram__DOT__check__128__ok = 
        (((3U == (vlSelf->tb_shared_sdram__DOT__writer_commands 
                  - tb_shared_sdram__DOT__before_commands)) 
          & (3U == (vlSelf->tb_shared_sdram__DOT__writes 
                    - tb_shared_sdram__DOT__before_writes))) 
         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending)));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__128__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__128__label_text));
    __Vtask_tb_shared_sdram__DOT__audit_words__129__count = 3U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__data 
        = tb_shared_sdram__DOT__payload;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__address = 0x200U;
    __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i = 0U;
    while (VL_LTS_III(32, __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i, __Vtask_tb_shared_sdram__DOT__audit_words__129__count)) {
        vlSelf->tb_shared_sdram__DOT__peek_addr = (0xffffffU 
                                                   & (__Vtask_tb_shared_sdram__DOT__audit_words__129__address 
                                                      + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i));
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                           117);
        __Vtask_tb_shared_sdram__DOT__check__130__label_text = 
            std::string{"actual_pin_memory_word"};
        __Vtask_tb_shared_sdram__DOT__check__130__ok 
            = ((IData)(vlSelf->tb_shared_sdram__DOT__peek_data) 
               == (0xffffU & (IData)((__Vtask_tb_shared_sdram__DOT__audit_words__129__data 
                                      >> (0x3fU & VL_MULS_III(32, (IData)(0x10U), __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i))))));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__130__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__130__label_text));
        __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i 
            = ((IData)(1U) + __Vtask_tb_shared_sdram__DOT__audit_words__129__unnamedblk2__DOT__i);
    }
    tb_shared_sdram__DOT__before_reads = vlSelf->tb_shared_sdram__DOT__readwords;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__131__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    while ((1U & ((~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)) 
                  | VL_GTS_III(32, 0U, (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))))) {
        __Vtask_tb_shared_sdram__DOT__step__132__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__132__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__134__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__134__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__135__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__135__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__135__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__135__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__135__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__136__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__136__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__136__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__136__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__136__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__137__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__137__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__139__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__139__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__140__label_text = 
        std::string{"canceled_read_all_eight_physical_beats_drained"};
    __Vtask_tb_shared_sdram__DOT__check__140__ok = 
        ((8U == (vlSelf->tb_shared_sdram__DOT__readwords 
                 - tb_shared_sdram__DOT__before_reads)) 
         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__140__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__140__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__140__label_text));
    tb_shared_sdram__DOT__before_reads = vlSelf->tb_shared_sdram__DOT__readwords;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__131__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__131__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__131__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    while ((1U & ((~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)) 
                  | VL_GTS_III(32, 3U, (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))))) {
        __Vtask_tb_shared_sdram__DOT__step__132__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__132__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 1U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__134__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__134__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__135__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__135__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__135__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__135__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__135__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__133__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__136__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__136__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__136__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__136__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__136__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__137__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__137__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_cancel = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__139__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__139__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__140__label_text = 
        std::string{"canceled_read_all_eight_physical_beats_drained"};
    __Vtask_tb_shared_sdram__DOT__check__140__ok = 
        ((8U == (vlSelf->tb_shared_sdram__DOT__readwords 
                 - tb_shared_sdram__DOT__before_reads)) 
         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__140__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__140__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__140__label_text));
    tb_shared_sdram__DOT__before_writes = vlSelf->tb_shared_sdram__DOT__writes;
    tb_shared_sdram__DOT__before_commands = vlSelf->tb_shared_sdram__DOT__writer_commands;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__data = 0xa0b0c0d0e0f0102ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__141__address = 0x100U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__141__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__141__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__141__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    while (VL_GTS_III(32, 2U, (vlSelf->tb_shared_sdram__DOT__writer_commands 
                               - tb_shared_sdram__DOT__before_commands))) {
        __Vtask_tb_shared_sdram__DOT__step__142__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__142__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__wr_reset = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__143__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__144__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__144__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__145__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__145__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__143__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__145__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__145__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__145__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__146__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__146__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_reset = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__148__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__148__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__149__label_text = 
        std::string{"warm_writer_reset_prefix_drain"};
    __Vtask_tb_shared_sdram__DOT__check__149__ok = 
        (2U == (vlSelf->tb_shared_sdram__DOT__writes 
                - tb_shared_sdram__DOT__before_writes));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__149__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__149__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__149__label_text));
    tb_shared_sdram__DOT__before_reads = vlSelf->tb_shared_sdram__DOT__readwords;
    __Vtask_tb_shared_sdram__DOT__rd_issue__150__bank = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__150__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__150__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__150__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    while ((3U > (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))) {
        __Vtask_tb_shared_sdram__DOT__step__151__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__151__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    vlSelf->tb_shared_sdram__DOT__rd_reset = 1U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__152__expected_error = 1U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__153__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__153__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__154__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__154__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__152__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__154__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__154__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__154__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__152__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__155__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__155__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__155__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__155__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__155__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__156__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__156__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_reset = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__158__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__158__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__159__label_text = 
        std::string{"warm_reader_reset_complete_drain"};
    __Vtask_tb_shared_sdram__DOT__check__159__ok = 
        (8U == (vlSelf->tb_shared_sdram__DOT__readwords 
                - tb_shared_sdram__DOT__before_reads));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__159__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__159__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__159__label_text));
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__bank = 2U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__data = 0xfeedfacec001d00dULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__160__address = 0x200U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__160__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__160__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__160__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__161__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__162__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__162__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__163__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__163__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__161__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__163__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__163__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__163__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__164__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__164__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__166__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__166__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__rd_issue__167__bank = 2U;
    __Vtask_tb_shared_sdram__DOT__rd_issue__167__address = 0U;
    vlSelf->tb_shared_sdram__DOT__rd_req_addr = __Vtask_tb_shared_sdram__DOT__rd_issue__167__address;
    vlSelf->tb_shared_sdram__DOT__rd_req_bank = __Vtask_tb_shared_sdram__DOT__rd_issue__167__bank;
    vlSelf->tb_shared_sdram__DOT__rd_req_generation 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_req_generation);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       96);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           96);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       97);
    vlSelf->tb_shared_sdram__DOT__rd_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__rd_finish__168__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__169__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__169__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__170__label_text = 
        std::string{"reader_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__170__ok = 
        ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
         == (IData)(__Vtask_tb_shared_sdram__DOT__rd_finish__168__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__170__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__170__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__170__label_text));
    if (VL_UNLIKELY(__Vtask_tb_shared_sdram__DOT__rd_finish__168__expected_error)) {
        __Vtask_tb_shared_sdram__DOT__check__171__label_text = 
            std::string{"canceled_read_data_zero"};
        __Vtask_tb_shared_sdram__DOT__check__171__ok 
            = (0U == (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                        | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                       | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                      | vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U]));
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__171__ok))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),-1,
                              &(__Vtask_tb_shared_sdram__DOT__check__171__label_text));
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
                }
            }
        }
        vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                                + vlSelf->tb_shared_sdram__DOT__checks);
        VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
                  -1,&(__Vtask_tb_shared_sdram__DOT__check__171__label_text));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__172__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__172__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__rd_rsp_ready = 0U;
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__174__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__174__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__step__175__count = 0xc8U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__175__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    while ((1U & (((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                   | (~ (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) 
                  | (5U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))))) {
        __Vtask_tb_shared_sdram__DOT__step__177__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__177__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__178__label_text = 
        std::string{"periodic_refresh_and_read_write_turnarounds"};
    __Vtask_tb_shared_sdram__DOT__check__178__ok = 
        ((VL_LTS_III(32, 3U, vlSelf->tb_shared_sdram__DOT__refreshes) 
          & VL_LTS_III(32, 3U, vlSelf->tb_shared_sdram__DOT__activates)) 
         & VL_LTS_III(32, 3U, vlSelf->tb_shared_sdram__DOT__precharges));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__178__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__178__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n{\"type\":\"verdict\",\"status\":\"TEST_PASS\",\"checks\":%0d,\"t_ac_ns\":2.000000,\"observation_checksum\":%0#}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__178__label_text),
              32,vlSelf->tb_shared_sdram__DOT__checks,
              1,(1U & ((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready) 
                       ^ ((((((((((IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) 
                                  ^ ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                     ^ ((VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_rsp_epoch) 
                                         ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_rsp_token)) 
                                        ^ (VL_REDXOR_2(vlSelf->tb_shared_sdram__DOT__wr_rsp_bank) 
                                           ^ (VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_rsp_addr) 
                                              ^ ((0U 
                                                  != (IData)(vlSelf->tb_shared_sdram__DOT__wr_state)) 
                                                 ^ 
                                                 ((IData)(vlSelf->tb_shared_sdram__DOT__wr_pending) 
                                                  ^ 
                                                  (VL_REDXOR_4(vlSelf->tb_shared_sdram__DOT__wr_state) 
                                                   ^ 
                                                   VL_REDXOR_4(vlSelf->tb_shared_sdram__DOT__wr_word_index))))))))) 
                                 ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_rows)) 
                                ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_words_accepted)) 
                               ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_words_retired)) 
                              ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_responses)) 
                             ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_cancels)) 
                            ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__wr_invalid)) 
                           ^ ((IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready) 
                              ^ (((((((((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) 
                                        ^ ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error) 
                                           ^ (((VL_REDXOR_32(
                                                             (((vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] 
                                                                ^ 
                                                                vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U]) 
                                                               ^ 
                                                               vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U]) 
                                                              ^ 
                                                              vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U])) 
                                                ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_rsp_epoch)) 
                                               ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_rsp_generation)) 
                                              ^ (VL_REDXOR_2(vlSelf->tb_shared_sdram__DOT__rd_rsp_bank) 
                                                 ^ 
                                                 (VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_rsp_addr) 
                                                  ^ 
                                                  ((0U 
                                                    != (IData)(vlSelf->tb_shared_sdram__DOT__rd_state)) 
                                                   ^ 
                                                   ((IData)(vlSelf->tb_shared_sdram__DOT__rd_pending) 
                                                    ^ 
                                                    (VL_REDXOR_4(vlSelf->tb_shared_sdram__DOT__rd_state) 
                                                     ^ 
                                                     VL_REDXOR_4(vlSelf->tb_shared_sdram__DOT__rd_beats))))))))) 
                                       ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_requests)) 
                                      ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_commands)) 
                                     ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_count_beats)) 
                                    ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_responses)) 
                                   ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_cancels)) 
                                  ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__rd_invalid)) 
                                 ^ (VL_REDXOR_2(vlSelf->tb_shared_sdram__DOT__source_owner) 
                                    ^ (((((VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__writer_grants) 
                                           ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__reader_grants)) 
                                          ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__writer_commands)) 
                                         ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__reader_commands)) 
                                        ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__owner_releases)) 
                                       ^ ((IData)(vlSelf->tb_shared_sdram__DOT__controller_valid) 
                                          ^ ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                             ^ (VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__controller_addr) 
                                                ^ (
                                                   VL_REDXOR_16(vlSelf->tb_shared_sdram__DOT__controller_data) 
                                                   ^ 
                                                   ((IData)(vlSelf->tb_shared_sdram__DOT__controller_ready) 
                                                    ^ 
                                                    ((5U 
                                                      == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state)) 
                                                     ^ 
                                                     ((IData)(vlSelf->tb_shared_sdram__DOT__controller_read_valid) 
                                                      ^ 
                                                      VL_REDXOR_16(vlSelf->tb_shared_sdram__DOT__controller_read_data))))))))))))) 
                          ^ (VL_REDXOR_16(vlSelf->tb_shared_sdram__DOT__peek_data) 
                             ^ (((((VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__writes) 
                                    ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__readwords)) 
                                   ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__refreshes)) 
                                  ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__mrs)) 
                                 ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__activates)) 
                                ^ VL_REDXOR_32(vlSelf->tb_shared_sdram__DOT__precharges)))))));
    VL_FINISH_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 204, "");
}

VL_INLINE_OPT VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__0(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__1____Vfork_1__0\n"); );
    // Init
    IData/*19:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__4__address;
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__address = 0;
    QData/*63:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__4__data;
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__data = 0;
    CData/*1:0*/ __Vtask_tb_shared_sdram__DOT__wr_issue__4__bank;
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__bank = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__wr_finish__5__expected_error;
    __Vtask_tb_shared_sdram__DOT__wr_finish__5__expected_error = 0;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__6__count;
    __Vtask_tb_shared_sdram__DOT__step__6__count = 0;
    CData/*0:0*/ __Vtask_tb_shared_sdram__DOT__check__7__ok;
    __Vtask_tb_shared_sdram__DOT__check__7__ok = 0;
    std::string __Vtask_tb_shared_sdram__DOT__check__7__label_text;
    IData/*31:0*/ __Vtask_tb_shared_sdram__DOT__step__8__count;
    __Vtask_tb_shared_sdram__DOT__step__8__count = 0;
    // Body
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__bank = 1U;
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__data = 0x1122334455667788ULL;
    __Vtask_tb_shared_sdram__DOT__wr_issue__4__address = 0U;
    vlSelf->tb_shared_sdram__DOT__wr_req_addr = __Vtask_tb_shared_sdram__DOT__wr_issue__4__address;
    vlSelf->tb_shared_sdram__DOT__wr_req_data = __Vtask_tb_shared_sdram__DOT__wr_issue__4__data;
    vlSelf->tb_shared_sdram__DOT__wr_req_bank = __Vtask_tb_shared_sdram__DOT__wr_issue__4__bank;
    vlSelf->tb_shared_sdram__DOT__wr_req_token = ((IData)(1U) 
                                                  + vlSelf->tb_shared_sdram__DOT__wr_req_token);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 1U;
    co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       91);
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
        co_await vlSelf->__VtrigSched_h9c81e2cd__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           91);
    }
    co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge tb_shared_sdram.clk)", 
                                                       "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                       92);
    vlSelf->tb_shared_sdram__DOT__wr_req_valid = 0U;
    __Vtask_tb_shared_sdram__DOT__wr_finish__5__expected_error = 0U;
    while ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid)))) {
        __Vtask_tb_shared_sdram__DOT__step__6__count = 1U;
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__6__count;
        while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
            co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(negedge tb_shared_sdram.clk)", 
                                                               "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                               87);
            vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                = (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
                   - (IData)(1U));
        }
    }
    __Vtask_tb_shared_sdram__DOT__check__7__label_text = 
        std::string{"writer_expected_error"};
    __Vtask_tb_shared_sdram__DOT__check__7__ok = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled) 
                                                  == (IData)(__Vtask_tb_shared_sdram__DOT__wr_finish__5__expected_error));
    if (vlSymsp->_vm_contextp__->assertOn()) {
        if (VL_LIKELY((1U & (~ (IData)(__Vtask_tb_shared_sdram__DOT__check__7__ok))))) {
            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:84: Assertion failed in %Ntb_shared_sdram.check: check FAILED: %@\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),-1,&(__Vtask_tb_shared_sdram__DOT__check__7__label_text));
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 84, "");
            }
        }
    }
    vlSelf->tb_shared_sdram__DOT__checks = ((IData)(1U) 
                                            + vlSelf->tb_shared_sdram__DOT__checks);
    VL_WRITEF("{\"type\":\"check\",\"status\":\"PASS\",\"name\":\"%@\"}\n",
              -1,&(__Vtask_tb_shared_sdram__DOT__check__7__label_text));
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 1U;
    __Vtask_tb_shared_sdram__DOT__step__8__count = 1U;
    vlSelf->tb_shared_sdram__DOT____Vrepeat0 = __Vtask_tb_shared_sdram__DOT__step__8__count;
    while (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT____Vrepeat0)) {
        co_await vlSelf->__VtrigSched_h9c81e28c__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge tb_shared_sdram.clk)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                                           87);
        vlSelf->tb_shared_sdram__DOT____Vrepeat0 = 
            (vlSelf->tb_shared_sdram__DOT____Vrepeat0 
             - (IData)(1U));
    }
    vlSelf->tb_shared_sdram__DOT__wr_rsp_ready = 0U;
    vlSelf->__Vfork_1__sync.done("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                 131);
}

VL_INLINE_OPT VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__2(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__2\n"); );
    // Body
    co_await vlSelf->__VdlySched.delay(0x77359400ULL, 
                                       nullptr, "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 
                                       206);
    VL_WRITEF("[%0t] %%Fatal: tb_shared_sdram.sv:206: Assertion failed in %Ntb_shared_sdram: finite shared-service watchdog\n",
              64,VL_TIME_UNITED_Q(1000),-9,vlSymsp->name());
    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/tb_shared_sdram.sv", 206, "");
}

VL_INLINE_OPT VlCoroutine Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__3(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___eval_initial__TOP__Vtiming__3\n"); );
    // Body
    while (1U) {
        co_await vlSelf->__VtrigSched_h7b6f0010__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge tb_shared_sdram.dut.memory.device_clock)", 
                                                           "/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 
                                                           24);
        if (((IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)
              ? 0U : 1U)) {
            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle);
            if (VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__latency)) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__latency 
                    = (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__latency 
                       - (IData)(1U));
                if (VL_UNLIKELY((0U == vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__latency))) {
                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__data_request 
                        = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__mem
                        [(0xffffffU & vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr)];
                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive_request = 1U;
                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr);
                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__left = 7U;
                    vlSelf->tb_shared_sdram__DOT__readwords 
                        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__readwords);
                    VL_WRITEF("{\"type\":\"read\",\"cycle\":%0d,\"time_ps\":%0d,\"address\":%0d,\"data\":%0#}\n",
                              32,vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle,
                              64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                                   * (QData)(VL_TIME_UNITED_D(1000)))),
                              32,(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                                  - (IData)(1U)),16,
                              vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__mem
                              [(0xffffffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                                             - (IData)(1U)))]);
                }
            } else if (VL_UNLIKELY(VL_LTS_III(32, 0U, vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__left))) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__data_request 
                    = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__mem
                    [(0xffffffU & vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr)];
                vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr);
                vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__left 
                    = (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__left 
                       - (IData)(1U));
                vlSelf->tb_shared_sdram__DOT__readwords 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__readwords);
                VL_WRITEF("{\"type\":\"read\",\"cycle\":%0d,\"time_ps\":%0d,\"address\":%0d,\"data\":%0#}\n",
                          32,vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle,
                          64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                               * (QData)(VL_TIME_UNITED_D(1000)))),
                          32,(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                              - (IData)(1U)),16,vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__mem
                          [(0xffffffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                                         - (IData)(1U)))]);
            } else {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive_request = 0U;
            }
            if (VL_UNLIKELY((7U != (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ras) 
                                     << 2U) | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__cas) 
                                                << 1U) 
                                               | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__we)))))) {
                VL_WRITEF("{\"type\":\"pin\",\"cycle\":%0d,\"time_ps\":%0d,\"command\":%0#,\"bank\":%0#,\"address\":%0#,\"row\":%0#,\"dq\":%0#}\n",
                          32,vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle,
                          64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                               * (QData)(VL_TIME_UNITED_D(1000)))),
                          3,(((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ras) 
                              << 2U) | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__cas) 
                                         << 1U) | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__we))),
                          2,(IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba),
                          13,vlSelf->tb_shared_sdram__DOT__dut__DOT__a,
                          13,vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__rows
                          [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba],
                          16,((4U == (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ras) 
                                       << 2U) | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__cas) 
                                                  << 1U) 
                                                 | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__we))))
                               ? (((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                      ? (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__dq_out)
                                      : 0U) & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                                ? 0xffffU
                                                : 0U)) 
                                   & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                       ? 0xffffU : 0U)) 
                                  | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                       ? 0xffffU : 0U) 
                                     & (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                          ? (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__outdata)
                                          : 0U) & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                                    ? 0xffffU
                                                    : 0U))))
                               : 0U));
                if (vlSelf->tb_shared_sdram__DOT__dut__DOT__ras) {
                    if (VL_UNLIKELY(vlSelf->tb_shared_sdram__DOT__dut__DOT__cas)) {
                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:67: Assertion failed in %Ntb_shared_sdram.dut.memory: unexpected SDRAM command\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 67, "");
                    } else if (vlSelf->tb_shared_sdram__DOT__dut__DOT__we) {
                        if (vlSymsp->_vm_contextp__->assertOn()) {
                            if (VL_LIKELY((1U & (~ 
                                                 ((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                    >> (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba)) 
                                                   & VL_LTES_III(32, 2U, 
                                                                 (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                  - 
                                                                  vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                  [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba]))) 
                                                  & (0U 
                                                     == 
                                                     (7U 
                                                      & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__a)))))))) {
                                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                    VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:61: Assertion failed in %Ntb_shared_sdram.dut.memory: READ timing/alignment\n",
                                              64,VL_TIME_UNITED_Q(1000),
                                              -9,vlSymsp->name());
                                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 61, "");
                                }
                            }
                        }
                        if (vlSymsp->_vm_contextp__->assertOn()) {
                            if (VL_LIKELY(VL_GTS_III(32, 1U, 
                                                     (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                      - vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastcolumn)))) {
                                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                    VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:62: Assertion failed in %Ntb_shared_sdram.dut.memory: READ tCCD below one clock\n",
                                              64,VL_TIME_UNITED_Q(1000),
                                              -9,vlSymsp->name());
                                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 62, "");
                                }
                            }
                        }
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastcolumn 
                            = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__readaddr 
                            = (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba) 
                                << 0x16U) | ((vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__rows
                                              [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                                              << 9U) 
                                             | (0x1ffU 
                                                & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__a))));
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__latency = 3U;
                    } else {
                        if (vlSymsp->_vm_contextp__->assertOn()) {
                            if (VL_LIKELY((1U & (~ 
                                                 ((((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                      >> (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba)) 
                                                     & VL_LTES_III(32, 2U, 
                                                                   (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                    - 
                                                                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                    [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba]))) 
                                                    & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive))) 
                                                   & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ldqm))) 
                                                  & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__udqm))))))) {
                                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                    VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:56: Assertion failed in %Ntb_shared_sdram.dut.memory: WRITE timing/mask/contention\n",
                                              64,VL_TIME_UNITED_Q(1000),
                                              -9,vlSymsp->name());
                                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 56, "");
                                }
                            }
                        }
                        if (vlSymsp->_vm_contextp__->assertOn()) {
                            if (VL_LIKELY(VL_GTS_III(32, 1U, 
                                                     (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                      - vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastcolumn)))) {
                                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                    VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:57: Assertion failed in %Ntb_shared_sdram.dut.memory: WRITE tCCD below one clock\n",
                                              64,VL_TIME_UNITED_Q(1000),
                                              -9,vlSymsp->name());
                                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 57, "");
                                }
                            }
                        }
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastcolumn 
                            = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__mem[(
                                                                                ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba) 
                                                                                << 0x16U) 
                                                                                | ((vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__rows
                                                                                [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                                                                                << 9U) 
                                                                                | (0x1ffU 
                                                                                & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__a))))] 
                            = (((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                   ? (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__dq_out)
                                   : 0U) & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                             ? 0xffffU
                                             : 0U)) 
                                & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__drive)
                                    ? 0xffffU : 0U)) 
                               | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                    ? 0xffffU : 0U) 
                                  & (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                       ? (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__outdata)
                                       : 0U) & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__drive)
                                                 ? 0xffffU
                                                 : 0U))));
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite[vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                            = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                        vlSelf->tb_shared_sdram__DOT__writes 
                            = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__writes);
                    }
                } else if (vlSelf->tb_shared_sdram__DOT__dut__DOT__cas) {
                    if (vlSelf->tb_shared_sdram__DOT__dut__DOT__we) {
                        if (vlSymsp->_vm_contextp__->assertOn()) {
                            if (VL_LIKELY((1U & (~ 
                                                 (((~ 
                                                    ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                     >> (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba))) 
                                                   & VL_LTES_III(32, 2U, 
                                                                 (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                  - 
                                                                  vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre
                                                                  [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba]))) 
                                                  & VL_LTES_III(32, 8U, 
                                                                (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                 - vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastref))))))) {
                                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                    VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:41: Assertion failed in %Ntb_shared_sdram.dut.memory: ACT timing/open bank\n",
                                              64,VL_TIME_UNITED_Q(1000),
                                              -9,vlSymsp->name());
                                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 41, "");
                                }
                            }
                        }
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened 
                            = ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                               | (0xfU & ((IData)(1U) 
                                          << (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba))));
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__rows[vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                            = vlSelf->tb_shared_sdram__DOT__dut__DOT__a;
                        vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact[vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                            = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                        vlSelf->tb_shared_sdram__DOT__activates 
                            = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__activates);
                    } else {
                        if ((0x400U & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__a))) {
                            if (vlSymsp->_vm_contextp__->assertOn()) {
                                if (VL_LIKELY((1U & 
                                               (~ (
                                                   (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened)) 
                                                   | (VL_LTES_III(32, 5U, 
                                                                  (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                   - 
                                                                   vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                   [0U])) 
                                                      & VL_LTES_III(32, 2U, 
                                                                    (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                     - 
                                                                     vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite
                                                                     [0U])))))))) {
                                    if (VL_UNLIKELY(
                                                    vlSymsp->_vm_contextp__->assertOn())) {
                                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:47: Assertion failed in %Ntb_shared_sdram.dut.memory.unnamedblk3: all PRE timing\n",
                                                  64,
                                                  VL_TIME_UNITED_Q(1000),
                                                  -9,
                                                  vlSymsp->name());
                                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 47, "");
                                    }
                                }
                            }
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre[0U] 
                                = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                            if (vlSymsp->_vm_contextp__->assertOn()) {
                                if (VL_LIKELY((1U & 
                                               (~ (
                                                   (~ 
                                                    ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                     >> 1U)) 
                                                   | (VL_LTES_III(32, 5U, 
                                                                  (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                   - 
                                                                   vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                   [1U])) 
                                                      & VL_LTES_III(32, 2U, 
                                                                    (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                     - 
                                                                     vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite
                                                                     [1U])))))))) {
                                    if (VL_UNLIKELY(
                                                    vlSymsp->_vm_contextp__->assertOn())) {
                                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:47: Assertion failed in %Ntb_shared_sdram.dut.memory.unnamedblk3: all PRE timing\n",
                                                  64,
                                                  VL_TIME_UNITED_Q(1000),
                                                  -9,
                                                  vlSymsp->name());
                                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 47, "");
                                    }
                                }
                            }
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre[1U] 
                                = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                            if (vlSymsp->_vm_contextp__->assertOn()) {
                                if (VL_LIKELY((1U & 
                                               (~ (
                                                   (~ 
                                                    ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                     >> 2U)) 
                                                   | (VL_LTES_III(32, 5U, 
                                                                  (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                   - 
                                                                   vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                   [2U])) 
                                                      & VL_LTES_III(32, 2U, 
                                                                    (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                     - 
                                                                     vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite
                                                                     [2U])))))))) {
                                    if (VL_UNLIKELY(
                                                    vlSymsp->_vm_contextp__->assertOn())) {
                                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:47: Assertion failed in %Ntb_shared_sdram.dut.memory.unnamedblk3: all PRE timing\n",
                                                  64,
                                                  VL_TIME_UNITED_Q(1000),
                                                  -9,
                                                  vlSymsp->name());
                                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 47, "");
                                    }
                                }
                            }
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre[2U] 
                                = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                            if (vlSymsp->_vm_contextp__->assertOn()) {
                                if (VL_LIKELY((1U & 
                                               (~ (
                                                   (~ 
                                                    ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                     >> 3U)) 
                                                   | (VL_LTES_III(32, 5U, 
                                                                  (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                   - 
                                                                   vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                   [3U])) 
                                                      & VL_LTES_III(32, 2U, 
                                                                    (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                     - 
                                                                     vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite
                                                                     [3U])))))))) {
                                    if (VL_UNLIKELY(
                                                    vlSymsp->_vm_contextp__->assertOn())) {
                                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:47: Assertion failed in %Ntb_shared_sdram.dut.memory.unnamedblk3: all PRE timing\n",
                                                  64,
                                                  VL_TIME_UNITED_Q(1000),
                                                  -9,
                                                  vlSymsp->name());
                                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 47, "");
                                    }
                                }
                            }
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre[3U] 
                                = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened = 0U;
                        } else {
                            if (vlSymsp->_vm_contextp__->assertOn()) {
                                if (VL_LIKELY((1U & 
                                               (~ (
                                                   (~ 
                                                    ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened) 
                                                     >> (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba))) 
                                                   | (VL_LTES_III(32, 5U, 
                                                                  (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                   - 
                                                                   vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastact
                                                                   [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba])) 
                                                      & VL_LTES_III(32, 2U, 
                                                                    (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                                     - 
                                                                     vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastwrite
                                                                     [vlSelf->tb_shared_sdram__DOT__dut__DOT__ba])))))))) {
                                    if (VL_UNLIKELY(
                                                    vlSymsp->_vm_contextp__->assertOn())) {
                                        VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:51: Assertion failed in %Ntb_shared_sdram.dut.memory: PRE timing\n",
                                                  64,
                                                  VL_TIME_UNITED_Q(1000),
                                                  -9,
                                                  vlSymsp->name());
                                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 51, "");
                                    }
                                }
                            }
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened 
                                = ((~ ((IData)(1U) 
                                       << (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__ba))) 
                                   & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened));
                            vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastpre[vlSelf->tb_shared_sdram__DOT__dut__DOT__ba] 
                                = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                        }
                        vlSelf->tb_shared_sdram__DOT__precharges 
                            = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__precharges);
                    }
                } else if (vlSelf->tb_shared_sdram__DOT__dut__DOT__we) {
                    if (vlSymsp->_vm_contextp__->assertOn()) {
                        if (VL_LIKELY((1U & (~ ((0U 
                                                 == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__opened)) 
                                                & VL_LTES_III(32, 8U, 
                                                              (vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle 
                                                               - vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastref))))))) {
                            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:65: Assertion failed in %Ntb_shared_sdram.dut.memory: REF timing/open bank\n",
                                          64,VL_TIME_UNITED_Q(1000),
                                          -9,vlSymsp->name());
                                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 65, "");
                            }
                        }
                    }
                    vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__lastref 
                        = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__cycle;
                    vlSelf->tb_shared_sdram__DOT__refreshes 
                        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__refreshes);
                } else {
                    if (vlSymsp->_vm_contextp__->assertOn()) {
                        if (VL_LIKELY((0x233U != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__a)))) {
                            if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                                VL_WRITEF("[%0t] %%Fatal: sdram_pin_model.sv:66: Assertion failed in %Ntb_shared_sdram.dut.memory: MRS mismatch\n",
                                          64,VL_TIME_UNITED_Q(1000),
                                          -9,vlSymsp->name());
                                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv", 66, "");
                            }
                        }
                    }
                    vlSelf->tb_shared_sdram__DOT__mrs 
                        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__mrs);
                }
            }
        }
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vtb_shared_sdram___024root___dump_triggers__act(Vtb_shared_sdram___024root* vlSelf);
#endif  // VL_DEBUG

void Vtb_shared_sdram___024root___eval_triggers__act(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___eval_triggers__act\n"); );
    // Body
    vlSelf->__VactTriggered.set(0U, ((IData)(vlSelf->tb_shared_sdram__DOT__clk) 
                                     & (~ (IData)(vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__clk__0))));
    vlSelf->__VactTriggered.set(1U, ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__read_clk) 
                                     & (~ (IData)(vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__dut__DOT__read_clk__0))));
    vlSelf->__VactTriggered.set(2U, ((~ (IData)(vlSelf->tb_shared_sdram__DOT__clk)) 
                                     & (IData)(vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__clk__0)));
    vlSelf->__VactTriggered.set(3U, vlSelf->__VdlySched.awaitingCurrentTime());
    vlSelf->__VactTriggered.set(4U, ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__device_clock) 
                                     & (~ (IData)(vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__dut__DOT__memory__DOT__device_clock__0))));
    vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__clk__0 
        = vlSelf->tb_shared_sdram__DOT__clk;
    vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__dut__DOT__read_clk__0 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__read_clk;
    vlSelf->__Vtrigprevexpr___TOP__tb_shared_sdram__DOT__dut__DOT__memory__DOT__device_clock__0 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__memory__DOT__device_clock;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vtb_shared_sdram___024root___dump_triggers__act(vlSelf);
    }
#endif
}

VL_INLINE_OPT void Vtb_shared_sdram___024root___nba_sequent__TOP__0(Vtb_shared_sdram___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vtb_shared_sdram__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vtb_shared_sdram___024root___nba_sequent__TOP__0\n"); );
    // Init
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__receipt_cycle;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__receipt_cycle = 0;
    CData/*1:0*/ __Vdly__tb_shared_sdram__DOT__source_owner;
    __Vdly__tb_shared_sdram__DOT__source_owner = 0;
    CData/*0:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader = 0;
    CData/*0:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__writer_grants;
    __Vdly__tb_shared_sdram__DOT__writer_grants = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__reader_grants;
    __Vdly__tb_shared_sdram__DOT__reader_grants = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__owner_releases;
    __Vdly__tb_shared_sdram__DOT__owner_releases = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__writer_commands;
    __Vdly__tb_shared_sdram__DOT__writer_commands = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__reader_commands;
    __Vdly__tb_shared_sdram__DOT__reader_commands = 0;
    CData/*2:0*/ __Vdly__tb_shared_sdram__DOT__wr_state;
    __Vdly__tb_shared_sdram__DOT__wr_state = 0;
    CData/*0:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled = 0;
    CData/*2:0*/ __Vdly__tb_shared_sdram__DOT__wr_word_index;
    __Vdly__tb_shared_sdram__DOT__wr_word_index = 0;
    CData/*2:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_rows;
    __Vdly__tb_shared_sdram__DOT__wr_rows = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_words_accepted;
    __Vdly__tb_shared_sdram__DOT__wr_words_accepted = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_words_retired;
    __Vdly__tb_shared_sdram__DOT__wr_words_retired = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_responses;
    __Vdly__tb_shared_sdram__DOT__wr_responses = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_cancels;
    __Vdly__tb_shared_sdram__DOT__wr_cancels = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__wr_invalid;
    __Vdly__tb_shared_sdram__DOT__wr_invalid = 0;
    CData/*2:0*/ __Vdly__tb_shared_sdram__DOT__rd_state;
    __Vdly__tb_shared_sdram__DOT__rd_state = 0;
    CData/*0:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled = 0;
    CData/*1:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count = 0;
    CData/*3:0*/ __Vdly__tb_shared_sdram__DOT__rd_beats;
    __Vdly__tb_shared_sdram__DOT__rd_beats = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_requests;
    __Vdly__tb_shared_sdram__DOT__rd_requests = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_commands;
    __Vdly__tb_shared_sdram__DOT__rd_commands = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_count_beats;
    __Vdly__tb_shared_sdram__DOT__rd_count_beats = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_responses;
    __Vdly__tb_shared_sdram__DOT__rd_responses = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_cancels;
    __Vdly__tb_shared_sdram__DOT__rd_cancels = 0;
    IData/*31:0*/ __Vdly__tb_shared_sdram__DOT__rd_invalid;
    __Vdly__tb_shared_sdram__DOT__rd_invalid = 0;
    CData/*3:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 0;
    CData/*3:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 0;
    SData/*15:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 0;
    SData/*15:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count = 0;
    CData/*1:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs = 0;
    CData/*3:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open = 0;
    IData/*23:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address = 0;
    CData/*0:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write = 0;
    CData/*2:0*/ __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat = 0;
    CData/*1:0*/ __Vdlyvdim0__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0;
    __Vdlyvdim0__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 = 0;
    SData/*12:0*/ __Vdlyvval__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0;
    __Vdlyvval__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 = 0;
    CData/*0:0*/ __Vdlyvset__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0;
    __Vdlyvset__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 = 0;
    // Body
    __Vdly__tb_shared_sdram__DOT__reader_commands = vlSelf->tb_shared_sdram__DOT__reader_commands;
    __Vdly__tb_shared_sdram__DOT__writer_commands = vlSelf->tb_shared_sdram__DOT__writer_commands;
    __Vdly__tb_shared_sdram__DOT__owner_releases = vlSelf->tb_shared_sdram__DOT__owner_releases;
    __Vdly__tb_shared_sdram__DOT__reader_grants = vlSelf->tb_shared_sdram__DOT__reader_grants;
    __Vdly__tb_shared_sdram__DOT__writer_grants = vlSelf->tb_shared_sdram__DOT__writer_grants;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted;
    __Vdly__tb_shared_sdram__DOT__source_owner = vlSelf->tb_shared_sdram__DOT__source_owner;
    __Vdly__tb_shared_sdram__DOT__wr_invalid = vlSelf->tb_shared_sdram__DOT__wr_invalid;
    __Vdly__tb_shared_sdram__DOT__wr_cancels = vlSelf->tb_shared_sdram__DOT__wr_cancels;
    __Vdly__tb_shared_sdram__DOT__wr_responses = vlSelf->tb_shared_sdram__DOT__wr_responses;
    __Vdly__tb_shared_sdram__DOT__wr_words_retired 
        = vlSelf->tb_shared_sdram__DOT__wr_words_retired;
    __Vdly__tb_shared_sdram__DOT__wr_words_accepted 
        = vlSelf->tb_shared_sdram__DOT__wr_words_accepted;
    __Vdly__tb_shared_sdram__DOT__wr_rows = vlSelf->tb_shared_sdram__DOT__wr_rows;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled;
    __Vdly__tb_shared_sdram__DOT__wr_state = vlSelf->tb_shared_sdram__DOT__wr_state;
    __Vdly__tb_shared_sdram__DOT__wr_word_index = vlSelf->tb_shared_sdram__DOT__wr_word_index;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat;
    vlSelf->__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__wdata 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__wdata;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__open;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state;
    __Vdlyvset__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 = 0U;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state;
    if (((IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset) 
         & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__initialized))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY(vlSelf->tb_shared_sdram__DOT__wr_pending)) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: row_to_sdram.sv:87: Assertion failed in %Ntb_shared_sdram.dut.service.writer: cold reset while physical write owned\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 87, "");
                }
            }
        }
    }
    if ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY((vlSelf->tb_shared_sdram__DOT__wr_words_accepted 
                             < vlSelf->tb_shared_sdram__DOT__wr_words_retired))) {
                VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:89: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 89, "");
            }
        }
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY((4U < (vlSelf->tb_shared_sdram__DOT__wr_words_accepted 
                                   - vlSelf->tb_shared_sdram__DOT__wr_words_retired)))) {
                VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:90: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 90, "");
            }
        }
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding) 
                             != (vlSelf->tb_shared_sdram__DOT__wr_words_accepted 
                                 - vlSelf->tb_shared_sdram__DOT__wr_words_retired)))) {
                VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:91: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 91, "");
            }
        }
        if ((((((((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                  & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a457916__0)) 
                 & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_ready)) 
                & (0U != vlSelf->tb_shared_sdram__DOT__wr_req_epoch)) 
               & (3U > (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_bank))) 
              & (0U == (7U & vlSelf->tb_shared_sdram__DOT__wr_req_addr))) 
             & (0x88df8U >= vlSelf->tb_shared_sdram__DOT__wr_req_addr))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((0U != (7U & vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__mapped_addr)))) {
                    VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:92: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 92, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY(vlSelf->tb_shared_sdram__DOT__wr_pending)) {
                    VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:93: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 93, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_ctrl_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ (((4U > (IData)(vlSelf->tb_shared_sdram__DOT__wr_word_index)) 
                                           & (4U > (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding))) 
                                          & (3U > (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_bank))))))) {
                    VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:94: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 94, "");
                }
            }
        }
        if ((((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
              & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a457916__0)) 
             & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_ready)))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ ((((~ ((~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending)) 
                                                & (0U 
                                                   == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state)))) 
                                            | (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____Vcellinp__writer__ctrl_ready))) 
                                           | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__kill)) 
                                          | (IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)))))) {
                    VL_WRITEF("[%0t] %%Error: row_to_sdram.sv:95: Assertion failed in %Ntb_shared_sdram.dut.service.writer: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-tiled/row_to_sdram.sv", 95, "");
                }
            }
        }
    }
    __Vdly__tb_shared_sdram__DOT__rd_invalid = vlSelf->tb_shared_sdram__DOT__rd_invalid;
    __Vdly__tb_shared_sdram__DOT__rd_cancels = vlSelf->tb_shared_sdram__DOT__rd_cancels;
    __Vdly__tb_shared_sdram__DOT__rd_responses = vlSelf->tb_shared_sdram__DOT__rd_responses;
    __Vdly__tb_shared_sdram__DOT__rd_count_beats = vlSelf->tb_shared_sdram__DOT__rd_count_beats;
    __Vdly__tb_shared_sdram__DOT__rd_commands = vlSelf->tb_shared_sdram__DOT__rd_commands;
    __Vdly__tb_shared_sdram__DOT__rd_requests = vlSelf->tb_shared_sdram__DOT__rd_requests;
    __Vdly__tb_shared_sdram__DOT__rd_beats = vlSelf->tb_shared_sdram__DOT__rd_beats;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled;
    __Vdly__tb_shared_sdram__DOT__rd_state = vlSelf->tb_shared_sdram__DOT__rd_state;
    if (((IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset) 
         & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__initialized))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY((1U & (~ (((0U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                     & (0U == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) 
                                    & (0U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))))))) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: shared_sdram_service.sv:189: Assertion failed in %Ntb_shared_sdram.dut.service: cold reset requires quiescent service\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 189, "");
                }
            }
        }
    }
    if ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY((2U < (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))) {
                VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:191: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 191, "");
            }
        }
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY(((0U != (IData)(vlSelf->tb_shared_sdram__DOT__wr_state)) 
                             & (0U != (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))))) {
                VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:192: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 192, "");
            }
        }
        if ((0U != (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))) {
                    VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:193: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 193, "");
                }
            }
        }
        if ((0U != (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((2U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))) {
                    VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:194: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 194, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__controller_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ ((IData)((1U 
                                                   == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) 
                                          | ((2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                             & (1U 
                                                != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))))))) {
                    VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:195: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 195, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__controller_read_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_LIKELY((1U & (~ ((2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                        & (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)))))) {
                    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                        VL_WRITEF("[%0t] %%Fatal: shared_sdram_service.sv:196: Assertion failed in %Ntb_shared_sdram.dut.service: unowned physical read beat\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 196, "");
                    }
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ (((1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                           & (~ ((~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending)) 
                                                 & (0U 
                                                    == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))))) 
                                          & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_pending))))))) {
                    VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:197: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 197, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ ((2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                                          & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending))))))) {
                    VL_WRITEF("[%0t] %%Error: shared_sdram_service.sv:198: Assertion failed in %Ntb_shared_sdram.dut.service: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-shared-service/shared_sdram_service.sv", 198, "");
                }
            }
        }
    }
    if (((IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset) 
         & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__initialized))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_LIKELY(vlSelf->tb_shared_sdram__DOT__rd_pending)) {
                if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                    VL_WRITEF("[%0t] %%Fatal: bl8_read_bridge.sv:66: Assertion failed in %Ntb_shared_sdram.dut.service.reader: cold reset while read owned\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 66, "");
                }
            }
        }
    }
    if ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)))) {
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY((1U & (~ ((4U >= (IData)(vlSelf->tb_shared_sdram__DOT__rd_state)) 
                                      & (8U >= (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))))))) {
                VL_WRITEF("[%0t] %%Error: bl8_read_bridge.sv:68: Assertion failed in %Ntb_shared_sdram.dut.service.reader: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 68, "");
            }
        }
        if (vlSymsp->_vm_contextp__->assertOn()) {
            if (VL_UNLIKELY((1U & (~ ((vlSelf->tb_shared_sdram__DOT__rd_requests 
                                       >= vlSelf->tb_shared_sdram__DOT__rd_responses) 
                                      & (1U >= (vlSelf->tb_shared_sdram__DOT__rd_requests 
                                                - vlSelf->tb_shared_sdram__DOT__rd_responses))))))) {
                VL_WRITEF("[%0t] %%Error: bl8_read_bridge.sv:69: Assertion failed in %Ntb_shared_sdram.dut.service.reader: 'assert' failed.\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 69, "");
            }
        }
        if (((IData)(vlSelf->tb_shared_sdram__DOT__controller_read_valid) 
             & (2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_LIKELY((1U & (~ (((IData)(vlSelf->tb_shared_sdram__DOT__rd_pending) 
                                         & (2U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) 
                                        & (8U > (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))))))) {
                    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->assertOn())) {
                        VL_WRITEF("[%0t] %%Fatal: bl8_read_bridge.sv:70: Assertion failed in %Ntb_shared_sdram.dut.service.reader: unowned/excess controller read beat\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 70, "");
                    }
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_ctrl_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ (((~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_pending)) 
                                           & (0U == 
                                              (0xfU 
                                               & vlSelf->tb_shared_sdram__DOT__rd_rsp_addr))) 
                                          & (3U > (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_bank))))))) {
                    VL_WRITEF("[%0t] %%Error: bl8_read_bridge.sv:71: Assertion failed in %Ntb_shared_sdram.dut.service.reader: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 71, "");
                }
            }
        }
        if (vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY(vlSelf->tb_shared_sdram__DOT__rd_pending)) {
                    VL_WRITEF("[%0t] %%Error: bl8_read_bridge.sv:72: Assertion failed in %Ntb_shared_sdram.dut.service.reader: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 72, "");
                }
            }
        }
        if ((3U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
            if (vlSymsp->_vm_contextp__->assertOn()) {
                if (VL_UNLIKELY((1U & (~ ((IData)(vlSelf->tb_shared_sdram__DOT__rd_pending) 
                                          & (8U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))))))) {
                    VL_WRITEF("[%0t] %%Error: bl8_read_bridge.sv:73: Assertion failed in %Ntb_shared_sdram.dut.service.reader: 'assert' failed.\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study/fpga/experiments/cu66-v91l-shared-service/attempts/20261107T012546373204Z-2ec9c533/sources/fpga/experiments/cu66-v91l-readbridge/bl8_read_bridge.sv", 73, "");
                }
            }
        }
    }
    __Vdly__tb_shared_sdram__DOT__dut__DOT__receipt_cycle 
        = vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle;
    __Vdly__tb_shared_sdram__DOT__dut__DOT__receipt_cycle 
        = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle);
    if (vlSelf->tb_shared_sdram__DOT__power_on_reset) {
        __Vdly__tb_shared_sdram__DOT__reader_commands = 0U;
        __Vdly__tb_shared_sdram__DOT__writer_commands = 0U;
        __Vdly__tb_shared_sdram__DOT__source_owner = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader = 1U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted = 0U;
        __Vdly__tb_shared_sdram__DOT__writer_grants = 0U;
        __Vdly__tb_shared_sdram__DOT__reader_grants = 0U;
        __Vdly__tb_shared_sdram__DOT__owner_releases = 0U;
    } else {
        if (((IData)(vlSelf->tb_shared_sdram__DOT__controller_valid) 
             & (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) {
            if ((2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) {
                __Vdly__tb_shared_sdram__DOT__reader_commands 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__reader_commands);
            }
            if ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) {
                __Vdly__tb_shared_sdram__DOT__writer_commands 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__writer_commands);
            }
        }
        if ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) {
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted = 0U;
            if (((((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                   & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_reset))) 
                  & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_cancel))) 
                 & ((((~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid)) 
                      | (IData)(vlSelf->tb_shared_sdram__DOT__rd_reset)) 
                     | (IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel)) 
                    | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader)))) {
                __Vdly__tb_shared_sdram__DOT__writer_grants 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__writer_grants);
                __Vdly__tb_shared_sdram__DOT__source_owner = 1U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader = 0U;
            } else if ((((IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid) 
                         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_reset))) 
                        & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel)))) {
                __Vdly__tb_shared_sdram__DOT__reader_grants 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__reader_grants);
                __Vdly__tb_shared_sdram__DOT__source_owner = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader = 1U;
            }
        } else {
            if (((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_owned) 
                   & (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid)) 
                  & (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)) 
                 | (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_owned) 
                     & (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid)) 
                    & (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted = 1U;
            }
            if ((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted) 
                  & (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_owned) 
                      & (0U == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) 
                     | ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_owned) 
                        & (0U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))))) 
                 | ((~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted)) 
                    & (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_owned) 
                        & (((IData)(vlSelf->tb_shared_sdram__DOT__wr_reset) 
                            | (IData)(vlSelf->tb_shared_sdram__DOT__wr_cancel)) 
                           | (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid)))) 
                       | ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_owned) 
                          & (((IData)(vlSelf->tb_shared_sdram__DOT__rd_reset) 
                              | (IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel)) 
                             | (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid)))))))) {
                __Vdly__tb_shared_sdram__DOT__owner_releases 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__owner_releases);
                __Vdly__tb_shared_sdram__DOT__source_owner = 0U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted = 0U;
            }
        }
    }
    if ((1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__power_on_reset)))) {
        if (VL_UNLIKELY(((((IData)(vlSelf->tb_shared_sdram__DOT__wr_reset) 
                           | (IData)(vlSelf->tb_shared_sdram__DOT__wr_cancel)) 
                          | (IData)(vlSelf->tb_shared_sdram__DOT__rd_reset)) 
                         | (IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel)))) {
            VL_WRITEF("{\"type\":\"kill\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"wr_reset\":%0#,\"wr_cancel\":%0#,\"rd_reset\":%0#,\"rd_cancel\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      1,vlSelf->tb_shared_sdram__DOT__wr_reset,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__wr_cancel),
                      1,vlSelf->tb_shared_sdram__DOT__rd_reset,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel));
        }
        if (VL_UNLIKELY(((0U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                         & ((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                            | (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid))))) {
            VL_WRITEF("{\"type\":\"arbitrate\",\"cycle\":%0d,\"time_ps\":%0d,\"wr_offer\":%0#,\"rd_offer\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      1,(((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                          & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_reset))) 
                         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_cancel))),
                      1,(((IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid) 
                          & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_reset))) 
                         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_cancel))));
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__source_owner) 
                         != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_owner)))) {
            VL_WRITEF("{\"type\":\"ownership\",\"cycle\":%0d,\"time_ps\":%0d,\"old_owner\":%0#,\"owner\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_owner),
                      2,vlSelf->tb_shared_sdram__DOT__source_owner);
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                         & (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_ready)))) {
            VL_WRITEF("{\"type\":\"wr_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"token\":%0#,\"bank\":%0#,\"address\":%0#,\"data\":\"%016x\"}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__wr_req_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__wr_req_token,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__wr_req_bank),
                      20,vlSelf->tb_shared_sdram__DOT__wr_req_addr,
                      64,vlSelf->tb_shared_sdram__DOT__wr_req_data);
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid) 
                         & (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_ready)))) {
            VL_WRITEF("{\"type\":\"rd_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"generation\":%0#,\"bank\":%0#,\"address\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__rd_req_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__rd_req_generation,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__rd_req_bank),
                      19,vlSelf->tb_shared_sdram__DOT__rd_req_addr);
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__controller_valid) 
                         & (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready)))) {
            VL_WRITEF("{\"type\":\"ctrl_req\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"write\":%0#,\"address\":%0#,\"data\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      1,(1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)),
                      24,vlSelf->tb_shared_sdram__DOT__controller_addr,
                      16,(IData)(vlSelf->tb_shared_sdram__DOT__controller_data));
        }
        if (VL_UNLIKELY(vlSelf->tb_shared_sdram__DOT__controller_read_valid)) {
            VL_WRITEF("{\"type\":\"controller_read\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"data\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      16,vlSelf->tb_shared_sdram__DOT__controller_read_data);
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) 
                         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__wr_offered))))) {
            VL_WRITEF("{\"type\":\"wr_rsp_offer\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"token\":%0#,\"bank\":%0#,\"address\":%0#,\"error\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__wr_rsp_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__wr_rsp_token,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_bank),
                      20,vlSelf->tb_shared_sdram__DOT__wr_rsp_addr,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled));
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) 
                         & (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_ready)))) {
            VL_WRITEF("{\"type\":\"wr_rsp\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"token\":%0#,\"bank\":%0#,\"address\":%0#,\"error\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__wr_rsp_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__wr_rsp_token,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_bank),
                      20,vlSelf->tb_shared_sdram__DOT__wr_rsp_addr,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled));
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) 
                         & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__rd_offered))))) {
            VL_WRITEF("{\"type\":\"rd_rsp_offer\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"generation\":%0#,\"bank\":%0#,\"address\":%0#,\"error\":%0#,\"data\":\"%032x\"}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__rd_rsp_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__rd_rsp_generation,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_bank),
                      19,vlSelf->tb_shared_sdram__DOT__rd_rsp_addr,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error),
                      128,vlSelf->tb_shared_sdram__DOT__rd_rsp_data.data());
        }
        if (VL_UNLIKELY(((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) 
                         & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_ready)))) {
            VL_WRITEF("{\"type\":\"rd_rsp\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"epoch\":%0#,\"generation\":%0#,\"bank\":%0#,\"address\":%0#,\"error\":%0#,\"data\":\"%032x\"}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      32,vlSelf->tb_shared_sdram__DOT__rd_rsp_epoch,
                      32,vlSelf->tb_shared_sdram__DOT__rd_rsp_generation,
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_bank),
                      19,vlSelf->tb_shared_sdram__DOT__rd_rsp_addr,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_error),
                      128,vlSelf->tb_shared_sdram__DOT__rd_rsp_data.data());
        }
        if (VL_UNLIKELY(((0U != (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)) 
                         & (((((((IData)(vlSelf->tb_shared_sdram__DOT__wr_state) 
                                 != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_wr_state)) 
                                | ((IData)(vlSelf->tb_shared_sdram__DOT__rd_state) 
                                   != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_rd_state))) 
                               | ((5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state)) 
                                  != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_idle))) 
                              | (2U == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) 
                             | (3U == (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) 
                            | (3U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_state)))))) {
            VL_WRITEF("{\"type\":\"fence\",\"cycle\":%0d,\"time_ps\":%0d,\"owner\":%0#,\"wr_state\":%0#,\"rd_state\":%0#,\"wr_pending\":%0#,\"rd_pending\":%0#,\"controller_idle\":%0#,\"wr_words_accepted\":%0#,\"wr_words_retired\":%0#,\"rd_beats\":%0#}\n",
                      32,((IData)(1U) + vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle),
                      64,VL_RTOIROUND_Q_D((1.00000000000000000e+03 
                                           * (QData)(VL_TIME_UNITED_D(1000)))),
                      2,(IData)(vlSelf->tb_shared_sdram__DOT__source_owner),
                      3,vlSelf->tb_shared_sdram__DOT__wr_state,
                      3,(IData)(vlSelf->tb_shared_sdram__DOT__rd_state),
                      1,vlSelf->tb_shared_sdram__DOT__wr_pending,
                      1,(IData)(vlSelf->tb_shared_sdram__DOT__rd_pending),
                      1,(5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state)),
                      32,vlSelf->tb_shared_sdram__DOT__wr_words_accepted,
                      32,vlSelf->tb_shared_sdram__DOT__wr_words_retired,
                      4,(IData)(vlSelf->tb_shared_sdram__DOT__rd_beats));
        }
    }
    if (vlSelf->tb_shared_sdram__DOT__power_on_reset) {
        vlSelf->tb_shared_sdram__DOT__dut__DOT__ldqm = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__udqm = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_state = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__payload = 0ULL;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__base_word = 0U;
        vlSelf->tb_shared_sdram__DOT__wr_pending = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_word_index = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding = 0U;
        vlSelf->tb_shared_sdram__DOT__wr_rsp_epoch = 0U;
        vlSelf->tb_shared_sdram__DOT__wr_rsp_token = 0U;
        vlSelf->tb_shared_sdram__DOT__wr_rsp_bank = 0U;
        vlSelf->tb_shared_sdram__DOT__wr_rsp_addr = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_rows = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_words_accepted = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_words_retired = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_responses = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_cancels = 0U;
        __Vdly__tb_shared_sdram__DOT__wr_invalid = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_state = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_pending = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_beats = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_addr = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_bank = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_epoch = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_generation = 0U;
        vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_requests = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_commands = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_count_beats = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_responses = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_cancels = 0U;
        __Vdly__tb_shared_sdram__DOT__rd_invalid = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 1U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 0x1eU;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address = 0U;
        vlSelf->__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__wdata = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write = 0U;
        __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat = 0U;
        vlSelf->tb_shared_sdram__DOT__controller_read_valid = 0U;
        vlSelf->tb_shared_sdram__DOT__controller_read_data = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__a = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__ba = 0U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 1U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 1U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 1U;
    } else {
        if ((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__kill) 
              & (0U != (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) 
             & (4U != (IData)(vlSelf->tb_shared_sdram__DOT__wr_state)))) {
            __Vdly__tb_shared_sdram__DOT__wr_cancels 
                = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__wr_cancels);
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled = 1U;
        }
        if ((4U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
            if ((2U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
                __Vdly__tb_shared_sdram__DOT__wr_state = 0U;
            } else if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
                __Vdly__tb_shared_sdram__DOT__wr_state = 0U;
            } else if (((IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) 
                        & (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_ready))) {
                __Vdly__tb_shared_sdram__DOT__wr_responses 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__wr_responses);
                __Vdly__tb_shared_sdram__DOT__wr_state = 0U;
            }
        } else if ((2U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
            if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
                if ((5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                    __Vdly__tb_shared_sdram__DOT__wr_words_retired 
                        = (vlSelf->tb_shared_sdram__DOT__wr_words_retired 
                           + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding));
                    vlSelf->tb_shared_sdram__DOT__wr_pending = 0U;
                    __Vdly__tb_shared_sdram__DOT__wr_state = 4U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding = 0U;
                }
            } else {
                __Vdly__tb_shared_sdram__DOT__wr_state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__wr_state))) {
            if (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__kill) 
                 | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled))) {
                __Vdly__tb_shared_sdram__DOT__wr_state 
                    = ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding))
                        ? 4U : 2U);
            } else if (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_ctrl_valid) 
                        & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____Vcellinp__writer__ctrl_ready))) {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding 
                    = (7U & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding)));
                __Vdly__tb_shared_sdram__DOT__wr_words_accepted 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__wr_words_accepted);
                vlSelf->tb_shared_sdram__DOT__wr_pending = 1U;
                if ((3U == (IData)(vlSelf->tb_shared_sdram__DOT__wr_word_index))) {
                    __Vdly__tb_shared_sdram__DOT__wr_state = 2U;
                } else {
                    __Vdly__tb_shared_sdram__DOT__wr_word_index 
                        = (7U & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__wr_word_index)));
                }
            }
        } else if ((((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_valid) 
                     & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a457916__0)) 
                    & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_ready))) {
            __Vdly__tb_shared_sdram__DOT__wr_rows = 
                ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__wr_rows);
            vlSelf->tb_shared_sdram__DOT__wr_rsp_epoch 
                = vlSelf->tb_shared_sdram__DOT__wr_req_epoch;
            vlSelf->tb_shared_sdram__DOT__wr_rsp_token 
                = vlSelf->tb_shared_sdram__DOT__wr_req_token;
            vlSelf->tb_shared_sdram__DOT__wr_rsp_bank 
                = vlSelf->tb_shared_sdram__DOT__wr_req_bank;
            vlSelf->tb_shared_sdram__DOT__wr_rsp_addr 
                = vlSelf->tb_shared_sdram__DOT__wr_req_addr;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__payload 
                = vlSelf->tb_shared_sdram__DOT__wr_req_data;
            __Vdly__tb_shared_sdram__DOT__wr_word_index = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled = 0U;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__base_word 
                = (((IData)(vlSelf->tb_shared_sdram__DOT__wr_req_bank) 
                    << 0x16U) | (0x7ffffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__mapped_addr 
                                             >> 1U)));
            if (((((0U == vlSelf->tb_shared_sdram__DOT__wr_req_epoch) 
                   | (3U <= (IData)(vlSelf->tb_shared_sdram__DOT__wr_req_bank))) 
                  | (0U != (7U & vlSelf->tb_shared_sdram__DOT__wr_req_addr))) 
                 | (0x88df8U < vlSelf->tb_shared_sdram__DOT__wr_req_addr))) {
                __Vdly__tb_shared_sdram__DOT__wr_invalid 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__wr_invalid);
                __Vdly__tb_shared_sdram__DOT__wr_state = 4U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled = 1U;
            } else {
                __Vdly__tb_shared_sdram__DOT__wr_state = 1U;
            }
        }
        if ((((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__kill) 
              & (0U != (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) 
             & (4U != (IData)(vlSelf->tb_shared_sdram__DOT__rd_state)))) {
            __Vdly__tb_shared_sdram__DOT__rd_cancels 
                = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_cancels);
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled = 1U;
        }
        if ((4U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
            if ((2U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
                __Vdly__tb_shared_sdram__DOT__rd_state = 0U;
            } else if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
                __Vdly__tb_shared_sdram__DOT__rd_state = 0U;
            } else if (((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) 
                        & (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_ready))) {
                __Vdly__tb_shared_sdram__DOT__rd_responses 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_responses);
                __Vdly__tb_shared_sdram__DOT__rd_state = 0U;
            }
        } else if ((2U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
            if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
                if ((5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                    if ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count))) {
                        vlSelf->tb_shared_sdram__DOT__rd_pending = 0U;
                        if (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled) 
                             | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__kill))) {
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 1U;
                            __Vdly__tb_shared_sdram__DOT__rd_state = 4U;
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] = 0U;
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] = 0U;
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] = 0U;
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] = 0U;
                        } else {
                            vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 0U;
                            __Vdly__tb_shared_sdram__DOT__rd_state = 4U;
                        }
                    } else {
                        __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count 
                            = (3U & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count)));
                    }
                } else {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count = 0U;
                }
            } else if (((IData)(vlSelf->tb_shared_sdram__DOT__controller_read_valid) 
                        & (2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)))) {
                __Vdly__tb_shared_sdram__DOT__rd_count_beats 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_count_beats);
                VL_ASSIGNSEL_WI(128,16,(0x7fU & VL_SHIFTL_III(7,32,32, (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats), 4U)), vlSelf->tb_shared_sdram__DOT__rd_rsp_data, vlSelf->tb_shared_sdram__DOT__controller_read_data);
                __Vdly__tb_shared_sdram__DOT__rd_beats 
                    = (0xfU & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats)));
                if ((7U == (IData)(vlSelf->tb_shared_sdram__DOT__rd_beats))) {
                    __Vdly__tb_shared_sdram__DOT__rd_state = 3U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count = 0U;
                }
            }
        } else if ((1U & (IData)(vlSelf->tb_shared_sdram__DOT__rd_state))) {
            if (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__kill) 
                 | (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled))) {
                vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 1U;
                __Vdly__tb_shared_sdram__DOT__rd_state = 4U;
            } else if (((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_ctrl_valid) 
                        & ((IData)(vlSelf->tb_shared_sdram__DOT__controller_ready) 
                           & (2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))))) {
                __Vdly__tb_shared_sdram__DOT__rd_commands 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_commands);
                vlSelf->tb_shared_sdram__DOT__rd_pending = 1U;
                __Vdly__tb_shared_sdram__DOT__rd_state = 2U;
            }
        } else if ((((IData)(vlSelf->tb_shared_sdram__DOT__rd_req_valid) 
                     & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a496acb__0)) 
                    & (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_ready))) {
            __Vdly__tb_shared_sdram__DOT__rd_requests 
                = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_requests);
            vlSelf->tb_shared_sdram__DOT__rd_rsp_addr 
                = vlSelf->tb_shared_sdram__DOT__rd_req_addr;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_bank 
                = vlSelf->tb_shared_sdram__DOT__rd_req_bank;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_epoch 
                = vlSelf->tb_shared_sdram__DOT__rd_req_epoch;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_generation 
                = vlSelf->tb_shared_sdram__DOT__rd_req_generation;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[0U] = 0U;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[1U] = 0U;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[2U] = 0U;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_data[3U] = 0U;
            vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled = 0U;
            __Vdly__tb_shared_sdram__DOT__rd_beats = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count = 0U;
            if ((((((0U != (0xfU & vlSelf->tb_shared_sdram__DOT__rd_req_addr)) 
                    | (0x7e8f0U < vlSelf->tb_shared_sdram__DOT__rd_req_addr)) 
                   | (3U <= (IData)(vlSelf->tb_shared_sdram__DOT__rd_req_bank))) 
                  | (0U == vlSelf->tb_shared_sdram__DOT__rd_req_epoch)) 
                 | (0U == vlSelf->tb_shared_sdram__DOT__rd_req_generation))) {
                __Vdly__tb_shared_sdram__DOT__rd_invalid 
                    = ((IData)(1U) + vlSelf->tb_shared_sdram__DOT__rd_invalid);
                vlSelf->tb_shared_sdram__DOT__rd_rsp_error = 1U;
                __Vdly__tb_shared_sdram__DOT__rd_state = 4U;
            } else {
                __Vdly__tb_shared_sdram__DOT__rd_state = 1U;
            }
        }
        vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 1U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 1U;
        vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 1U;
        vlSelf->tb_shared_sdram__DOT__controller_read_valid = 0U;
        if ((0xffffU != (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count))) {
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count 
                = (0xffffU & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count)));
        }
        if (((((((((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state)) 
                   | (1U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
                  | (2U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
                 | (3U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
                | (4U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
               | (5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
              | (6U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) 
             | (7U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state)))) {
            if ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                if ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay))) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 1U;
                } else {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay 
                        = (0xffffU & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay) 
                                      - (IData)(1U)));
                }
            } else if ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__a = 0x400U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
            } else if ((2U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs 
                    = (3U & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs)));
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 0U;
                if ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs))) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 8U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 3U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
                } else {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 8U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 2U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
                }
            } else if ((3U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__a = 0x233U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ba = 0U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count = 0U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 5U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
            } else if ((4U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                if ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay))) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state 
                        = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state;
                } else {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay 
                        = (0xffffU & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay) 
                                      - (IData)(1U)));
                }
            } else if ((5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                if ((0x50U <= (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count))) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 0xcU;
                } else if (vlSelf->tb_shared_sdram__DOT__controller_valid) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                        = vlSelf->tb_shared_sdram__DOT__controller_addr;
                    vlSelf->__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__wdata 
                        = vlSelf->tb_shared_sdram__DOT__controller_data;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write 
                        = (1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner));
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state 
                        = ((1U & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__open) 
                                  >> (3U & (vlSelf->tb_shared_sdram__DOT__controller_addr 
                                            >> 0x16U))))
                            ? ((vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows
                                [(3U & (vlSelf->tb_shared_sdram__DOT__controller_addr 
                                        >> 0x16U))] 
                                == (0x1fffU & (vlSelf->tb_shared_sdram__DOT__controller_addr 
                                               >> 9U)))
                                ? 8U : 6U) : 7U);
                }
            } else if ((6U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__a = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ba 
                    = (3U & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                             >> 0x16U));
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 7U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open 
                    = ((~ ((IData)(1U) << (3U & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                                                 >> 0x16U)))) 
                       & (IData)(__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open));
            } else {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__a 
                    = (0x1fffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                                  >> 9U));
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 2U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 8U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
                vlSelf->tb_shared_sdram__DOT__dut__DOT__ba 
                    = (3U & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                             >> 0x16U));
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open 
                    = ((IData)(__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open) 
                       | (0xfU & ((IData)(1U) << (3U 
                                                  & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                                                     >> 0x16U)))));
                __Vdlyvval__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 
                    = (0x1fffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                                  >> 9U));
                __Vdlyvset__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 = 1U;
                __Vdlyvdim0__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0 
                    = (3U & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                             >> 0x16U));
            }
        } else if ((8U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
            vlSelf->tb_shared_sdram__DOT__dut__DOT__a 
                = (0x1ffU & vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address);
            vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 0U;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__ba 
                = (3U & (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                         >> 0x16U));
            if (vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write) {
                vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 0U;
                if (((IData)(vlSelf->tb_shared_sdram__DOT__controller_valid) 
                     & (IData)(vlSelf->tb_shared_sdram__DOT__controller_ready))) {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
                        = vlSelf->tb_shared_sdram__DOT__controller_addr;
                    vlSelf->__Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__wdata 
                        = vlSelf->tb_shared_sdram__DOT__controller_data;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write = 1U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 8U;
                } else {
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 3U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 5U;
                    __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
                }
            } else {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 5U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 9U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat = 0U;
            }
        } else if ((9U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
            if ((0U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay))) {
                vlSelf->tb_shared_sdram__DOT__controller_read_valid = 1U;
                vlSelf->tb_shared_sdram__DOT__controller_read_data 
                    = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__dq_retime;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat = 1U;
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 0xaU;
            } else {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay 
                    = (0xffffU & ((IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay) 
                                  - (IData)(1U)));
            }
        } else if ((0xaU == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat 
                = (7U & ((IData)(1U) + (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat)));
            vlSelf->tb_shared_sdram__DOT__controller_read_valid = 1U;
            vlSelf->tb_shared_sdram__DOT__controller_read_data 
                = vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__dq_retime;
            if ((7U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat))) {
                __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 5U;
            }
        } else if ((0xcU == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
            vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__we = 0U;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__a = 0x400U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 2U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 0xdU;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
        } else if ((0xdU == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state))) {
            vlSelf->tb_shared_sdram__DOT__dut__DOT__ras = 0U;
            vlSelf->tb_shared_sdram__DOT__dut__DOT__cas = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count = 0U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay = 8U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state = 5U;
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 4U;
        } else {
            __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state = 0U;
        }
    }
    vlSelf->tb_shared_sdram__DOT__reader_commands = __Vdly__tb_shared_sdram__DOT__reader_commands;
    vlSelf->tb_shared_sdram__DOT__writer_commands = __Vdly__tb_shared_sdram__DOT__writer_commands;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__last_reader;
    vlSelf->tb_shared_sdram__DOT__writer_grants = __Vdly__tb_shared_sdram__DOT__writer_grants;
    vlSelf->tb_shared_sdram__DOT__reader_grants = __Vdly__tb_shared_sdram__DOT__reader_grants;
    vlSelf->tb_shared_sdram__DOT__owner_releases = __Vdly__tb_shared_sdram__DOT__owner_releases;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__initialized = 1U;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__initialized = 1U;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__initialized = 1U;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_cycle 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__receipt_cycle;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__wr_offered 
        = ((IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_valid) 
           & (~ (IData)(vlSelf->tb_shared_sdram__DOT__wr_rsp_ready)));
    vlSelf->tb_shared_sdram__DOT__dut__DOT__rd_offered 
        = ((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_valid) 
           & (~ (IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_ready)));
    vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_rd_state 
        = vlSelf->tb_shared_sdram__DOT__rd_state;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_wr_state 
        = vlSelf->tb_shared_sdram__DOT__wr_state;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_idle 
        = (5U == (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state));
    vlSelf->tb_shared_sdram__DOT__dut__DOT__receipt_owner 
        = vlSelf->tb_shared_sdram__DOT__source_owner;
    vlSelf->tb_shared_sdram__DOT__wr_rows = __Vdly__tb_shared_sdram__DOT__wr_rows;
    vlSelf->tb_shared_sdram__DOT__wr_responses = __Vdly__tb_shared_sdram__DOT__wr_responses;
    vlSelf->tb_shared_sdram__DOT__wr_cancels = __Vdly__tb_shared_sdram__DOT__wr_cancels;
    vlSelf->tb_shared_sdram__DOT__wr_invalid = __Vdly__tb_shared_sdram__DOT__wr_invalid;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__outstanding;
    vlSelf->tb_shared_sdram__DOT__wr_words_retired 
        = __Vdly__tb_shared_sdram__DOT__wr_words_retired;
    vlSelf->tb_shared_sdram__DOT__wr_words_accepted 
        = __Vdly__tb_shared_sdram__DOT__wr_words_accepted;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__canceled;
    vlSelf->tb_shared_sdram__DOT__wr_state = __Vdly__tb_shared_sdram__DOT__wr_state;
    vlSelf->tb_shared_sdram__DOT__wr_word_index = __Vdly__tb_shared_sdram__DOT__wr_word_index;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__canceled;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__service__DOT__reader__DOT__idle_count;
    vlSelf->tb_shared_sdram__DOT__rd_commands = __Vdly__tb_shared_sdram__DOT__rd_commands;
    vlSelf->tb_shared_sdram__DOT__rd_count_beats = __Vdly__tb_shared_sdram__DOT__rd_count_beats;
    vlSelf->tb_shared_sdram__DOT__rd_cancels = __Vdly__tb_shared_sdram__DOT__rd_cancels;
    vlSelf->tb_shared_sdram__DOT__rd_invalid = __Vdly__tb_shared_sdram__DOT__rd_invalid;
    vlSelf->tb_shared_sdram__DOT__rd_responses = __Vdly__tb_shared_sdram__DOT__rd_responses;
    vlSelf->tb_shared_sdram__DOT__rd_requests = __Vdly__tb_shared_sdram__DOT__rd_requests;
    vlSelf->tb_shared_sdram__DOT__rd_beats = __Vdly__tb_shared_sdram__DOT__rd_beats;
    vlSelf->tb_shared_sdram__DOT__rd_state = __Vdly__tb_shared_sdram__DOT__rd_state;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__next_state;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__delay;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__init_refs;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__open 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__open;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__beat;
    if (__Vdlyvset__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0) {
        vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows[__Vdlyvdim0__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0] 
            = __Vdlyvval__tb_shared_sdram__DOT__dut__DOT__controller__DOT__rows__v0;
    }
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__refresh_count;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__address 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__address;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__is_write;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__controller__DOT__state 
        = __Vdly__tb_shared_sdram__DOT__dut__DOT__controller__DOT__state;
    vlSelf->tb_shared_sdram__DOT__source_owner = __Vdly__tb_shared_sdram__DOT__source_owner;
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__wr_owned 
        = (1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner));
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__rd_owned 
        = (2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner));
    if ((1U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner))) {
        vlSelf->tb_shared_sdram__DOT__controller_data 
            = (0xffffU & (IData)((vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__payload 
                                  >> (0x3fU & VL_SHIFTL_III(6,6,32, (IData)(vlSelf->tb_shared_sdram__DOT__wr_word_index), 4U)))));
        vlSelf->tb_shared_sdram__DOT__controller_addr 
            = (0xffffffU & (vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__writer__DOT__base_word 
                            + (IData)(vlSelf->tb_shared_sdram__DOT__wr_word_index)));
        vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a457916__0 
            = (1U & (~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted)));
    } else {
        vlSelf->tb_shared_sdram__DOT__controller_data = 0U;
        vlSelf->tb_shared_sdram__DOT__controller_addr 
            = (0xffffffU & (((IData)(vlSelf->tb_shared_sdram__DOT__rd_rsp_bank) 
                             << 0x16U) | (0x3ffffU 
                                          & (vlSelf->tb_shared_sdram__DOT__rd_rsp_addr 
                                             >> 1U))));
        vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a457916__0 = 0U;
    }
    vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT____VdfgTmp_h9a496acb__0 
        = ((~ (IData)(vlSelf->tb_shared_sdram__DOT__dut__DOT__service__DOT__accepted)) 
           & (2U == (IData)(vlSelf->tb_shared_sdram__DOT__source_owner)));
}
