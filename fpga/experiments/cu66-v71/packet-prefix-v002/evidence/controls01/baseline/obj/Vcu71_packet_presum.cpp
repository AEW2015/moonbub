// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vcu71_packet_presum__pch.h"

//============================================================
// Constructors

Vcu71_packet_presum::Vcu71_packet_presum(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vcu71_packet_presum__Syms(contextp(), _vcname__, this)}
    , m_evalLoop{*this, /*convergeLimit:*/ 10000}
    , clk{vlSymsp->TOP.clk}
    , rst{vlSymsp->TOP.rst}
    , abort_i{vlSymsp->TOP.abort_i}
    , cfg_valid{vlSymsp->TOP.cfg_valid}
    , cfg_ready{vlSymsp->TOP.cfg_ready}
    , cfg_packet_bytes{vlSymsp->TOP.cfg_packet_bytes}
    , cfg_last_valid{vlSymsp->TOP.cfg_last_valid}
    , cfg_last_frame_id{vlSymsp->TOP.cfg_last_frame_id}
    , cfg_reference_valid{vlSymsp->TOP.cfg_reference_valid}
    , cfg_reference_id{vlSymsp->TOP.cfg_reference_id}
    , cfg_reference_tag{vlSymsp->TOP.cfg_reference_tag}
    , rd_req_valid{vlSymsp->TOP.rd_req_valid}
    , rd_req_ready{vlSymsp->TOP.rd_req_ready}
    , rd_req_addr{vlSymsp->TOP.rd_req_addr}
    , rd_rsp_valid{vlSymsp->TOP.rd_rsp_valid}
    , rd_rsp_ready{vlSymsp->TOP.rd_rsp_ready}
    , rd_rsp_data{vlSymsp->TOP.rd_rsp_data}
    , metadata_valid{vlSymsp->TOP.metadata_valid}
    , metadata_ready{vlSymsp->TOP.metadata_ready}
    , metadata_key{vlSymsp->TOP.metadata_key}
    , metadata_frame_id{vlSymsp->TOP.metadata_frame_id}
    , metadata_reference_id{vlSymsp->TOP.metadata_reference_id}
    , metadata_reference_tag{vlSymsp->TOP.metadata_reference_tag}
    , metadata_output_tag{vlSymsp->TOP.metadata_output_tag}
    , metadata_block_size{vlSymsp->TOP.metadata_block_size}
    , metadata_plane_addr{vlSymsp->TOP.metadata_plane_addr}
    , metadata_plane_bytes{vlSymsp->TOP.metadata_plane_bytes}
    , metadata_plane_dispatch{vlSymsp->TOP.metadata_plane_dispatch}
    , metadata_plane_blocks{vlSymsp->TOP.metadata_plane_blocks}
    , metadata_plane_blocks_w{vlSymsp->TOP.metadata_plane_blocks_w}
    , metadata_hud_addr{vlSymsp->TOP.metadata_hud_addr}
    , metadata_hud_bytes{vlSymsp->TOP.metadata_hud_bytes}
    , metadata_hud_reference_tag{vlSymsp->TOP.metadata_hud_reference_tag}
    , metadata_hud_output_tag{vlSymsp->TOP.metadata_hud_output_tag}
    , qmap_req_valid{vlSymsp->TOP.qmap_req_valid}
    , qmap_req_ready{vlSymsp->TOP.qmap_req_ready}
    , qmap_req_index{vlSymsp->TOP.qmap_req_index}
    , qmap_rsp_valid{vlSymsp->TOP.qmap_rsp_valid}
    , qmap_rsp_index{vlSymsp->TOP.qmap_rsp_index}
    , qmap_rsp_code{vlSymsp->TOP.qmap_rsp_code}
    , commit_valid{vlSymsp->TOP.commit_valid}
    , commit_ready{vlSymsp->TOP.commit_ready}
    , busy{vlSymsp->TOP.busy}
    , done{vlSymsp->TOP.done}
    , aborted{vlSymsp->TOP.aborted}
    , error{vlSymsp->TOP.error}
    , error_code{vlSymsp->TOP.error_code}
    , debug_state{vlSymsp->TOP.debug_state}
    , memory_reads{vlSymsp->TOP.memory_reads}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vcu71_packet_presum::Vcu71_packet_presum(const char* _vcname__)
    : Vcu71_packet_presum(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vcu71_packet_presum::~Vcu71_packet_presum() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vcu71_packet_presum___024root___eval_debug_assertions(Vcu71_packet_presum___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_static(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_initial(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD bool Vcu71_packet_presum___024root___eval_stl(Vcu71_packet_presum___024root* vlSelf, CData/*0:0*/ firstIteration);
void Vcu71_packet_presum___024root___eval_sample(Vcu71_packet_presum___024root* vlSelf);
bool Vcu71_packet_presum___024root___eval_ico(Vcu71_packet_presum___024root* vlSelf, CData/*0:0*/ firstIteration);
bool Vcu71_packet_presum___024root___eval_act(Vcu71_packet_presum___024root* vlSelf);
bool Vcu71_packet_presum___024root___eval_inact(Vcu71_packet_presum___024root* vlSelf);
bool Vcu71_packet_presum___024root___eval_nba(Vcu71_packet_presum___024root* vlSelf);
bool Vcu71_packet_presum___024root___eval_obs(Vcu71_packet_presum___024root* vlSelf);
bool Vcu71_packet_presum___024root___eval_react(Vcu71_packet_presum___024root* vlSelf);
void Vcu71_packet_presum___024root___eval_postponed(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_final(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__stl(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__ico(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__act(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__nba(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__obs(Vcu71_packet_presum___024root* vlSelf);
VL_ATTR_COLD void Vcu71_packet_presum___024root___eval_dump_triggers__react(Vcu71_packet_presum___024root* vlSelf);

void Vcu71_packet_presum::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcu71_packet_presum::eval_step\n"); );
    m_evalLoop.eval();
}

void Vcu71_packet_presum::evalBegin() {
#ifdef VL_DEBUG
    // Debug assertions
    Vcu71_packet_presum___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
}

void Vcu71_packet_presum::evalEnd() {
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

void Vcu71_packet_presum::evalStatic() {
    Vcu71_packet_presum___024root___eval_static(&(vlSymsp->TOP));
}

void Vcu71_packet_presum::evalInitial() {
    Vcu71_packet_presum___024root___eval_initial(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalStl(bool firstIteration) {
    return Vcu71_packet_presum___024root___eval_stl(&(vlSymsp->TOP), firstIteration);
}

void Vcu71_packet_presum::evalSample() {
    Vcu71_packet_presum___024root___eval_sample(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalIco(bool firstIteration) {
    return Vcu71_packet_presum___024root___eval_ico(&(vlSymsp->TOP), firstIteration);
}

bool Vcu71_packet_presum::evalAct() {
    return Vcu71_packet_presum___024root___eval_act(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalInact() {
    return Vcu71_packet_presum___024root___eval_inact(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalNba() {
    return Vcu71_packet_presum___024root___eval_nba(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalObs() {
    return Vcu71_packet_presum___024root___eval_obs(&(vlSymsp->TOP));
}

bool Vcu71_packet_presum::evalReact() {
    return Vcu71_packet_presum___024root___eval_react(&(vlSymsp->TOP));
}

void Vcu71_packet_presum::evalPostponed() {
    Vcu71_packet_presum___024root___eval_postponed(&(vlSymsp->TOP));
}

void Vcu71_packet_presum::evalFinal() {
    Vcu71_packet_presum___024root___eval_final(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersStl() {
    Vcu71_packet_presum___024root___eval_dump_triggers__stl(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersIco() {
    Vcu71_packet_presum___024root___eval_dump_triggers__ico(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersAct() {
    Vcu71_packet_presum___024root___eval_dump_triggers__act(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersNba() {
    Vcu71_packet_presum___024root___eval_dump_triggers__nba(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersObs() {
    Vcu71_packet_presum___024root___eval_dump_triggers__obs(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_packet_presum::dumpTriggersReact() {
    Vcu71_packet_presum___024root___eval_dump_triggers__react(&(vlSymsp->TOP));
}

//============================================================
// Events and timing
bool Vcu71_packet_presum::eventsPending() { return false; }

uint64_t Vcu71_packet_presum::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vcu71_packet_presum::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

VL_ATTR_COLD void Vcu71_packet_presum::final() {
    contextp()->executingFinal(true);
    evalFinal();
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vcu71_packet_presum::hierName() const { return vlSymsp->name(); }
const char* Vcu71_packet_presum::modelName() const { return "Vcu71_packet_presum"; }
unsigned Vcu71_packet_presum::threads() const { return 1; }
void Vcu71_packet_presum::prepareClone() const { contextp()->prepareClone(); }
void Vcu71_packet_presum::atClone() const {
    contextp()->threadPoolpOnClone();
}
