// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vdy71_platform_sim__pch.h"

//============================================================
// Constructors

Vdy71_platform_sim::Vdy71_platform_sim(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vdy71_platform_sim__Syms(contextp(), _vcname__, this)}
    , m_evalLoop{*this, /*convergeLimit:*/ 10000}
    , red{vlSymsp->TOP.red}
    , green{vlSymsp->TOP.green}
    , blue{vlSymsp->TOP.blue}
    , physical_x{vlSymsp->TOP.physical_x}
    , physical_y{vlSymsp->TOP.physical_y}
    , data_enable{vlSymsp->TOP.data_enable}
    , clk{vlSymsp->TOP.clk}
    , read_clk{vlSymsp->TOP.read_clk}
    , pixel_clk{vlSymsp->TOP.pixel_clk}
    , pixel_reset_n{vlSymsp->TOP.pixel_reset_n}
    , rst{vlSymsp->TOP.rst}
    , bus_write{vlSymsp->TOP.bus_write}
    , bus_address{vlSymsp->TOP.bus_address}
    , bus_wdata{vlSymsp->TOP.bus_wdata}
    , transport_fault{vlSymsp->TOP.transport_fault}
    , bus_rdata{vlSymsp->TOP.bus_rdata}
    , peek_address{vlSymsp->TOP.peek_address}
    , peek_data{vlSymsp->TOP.peek_data}
    , model_reads{vlSymsp->TOP.model_reads}
    , model_writes{vlSymsp->TOP.model_writes}
    , model_refreshes{vlSymsp->TOP.model_refreshes}
    , cpu_packet_requests{vlSymsp->TOP.cpu_packet_requests}
    , cpu_aux_requests{vlSymsp->TOP.cpu_aux_requests}
    , cpu_aux_completions{vlSymsp->TOP.cpu_aux_completions}
    , cpu_hud_result_calls{vlSymsp->TOP.cpu_hud_result_calls}
    , cpu_hud_drain_calls{vlSymsp->TOP.cpu_hud_drain_calls}
    , cpu_software_ack_calls{vlSymsp->TOP.cpu_software_ack_calls}
    , busy{vlSymsp->TOP.busy}
    , error{vlSymsp->TOP.error}
    , stage{vlSymsp->TOP.stage}
    , error_code{vlSymsp->TOP.error_code}
    , accepted_count{vlSymsp->TOP.accepted_count}
    , presented_count{vlSymsp->TOP.presented_count}
    , rejected_count{vlSymsp->TOP.rejected_count}
    , lcd_underruns{vlSymsp->TOP.lcd_underruns}
    , quarantine{vlSymsp->TOP.quarantine}
    , reference_bank{vlSymsp->TOP.reference_bank}
    , front_bank{vlSymsp->TOP.front_bank}
    , front_frame_id{vlSymsp->TOP.front_frame_id}
    , front_cache_slot{vlSymsp->TOP.front_cache_slot}
    , profile_magic{vlSymsp->TOP.profile_magic}
    , profile_abi{vlSymsp->TOP.profile_abi}
    , profile_capabilities{vlSymsp->TOP.profile_capabilities}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vdy71_platform_sim::Vdy71_platform_sim(const char* _vcname__)
    : Vdy71_platform_sim(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vdy71_platform_sim::~Vdy71_platform_sim() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vdy71_platform_sim___024root___eval_debug_assertions(Vdy71_platform_sim___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_static(Vdy71_platform_sim___024root* vlSelf);
void Vdy71_platform_sim___024root___eval_initial(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD bool Vdy71_platform_sim___024root___eval_stl(Vdy71_platform_sim___024root* vlSelf, CData/*0:0*/ firstIteration);
void Vdy71_platform_sim___024root___eval_sample(Vdy71_platform_sim___024root* vlSelf);
bool Vdy71_platform_sim___024root___eval_ico(Vdy71_platform_sim___024root* vlSelf, CData/*0:0*/ firstIteration);
bool Vdy71_platform_sim___024root___eval_act(Vdy71_platform_sim___024root* vlSelf);
bool Vdy71_platform_sim___024root___eval_inact(Vdy71_platform_sim___024root* vlSelf);
bool Vdy71_platform_sim___024root___eval_nba(Vdy71_platform_sim___024root* vlSelf);
bool Vdy71_platform_sim___024root___eval_obs(Vdy71_platform_sim___024root* vlSelf);
bool Vdy71_platform_sim___024root___eval_react(Vdy71_platform_sim___024root* vlSelf);
void Vdy71_platform_sim___024root___eval_postponed(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_final(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__stl(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__ico(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__act(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__nba(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__obs(Vdy71_platform_sim___024root* vlSelf);
VL_ATTR_COLD void Vdy71_platform_sim___024root___eval_dump_triggers__react(Vdy71_platform_sim___024root* vlSelf);

void Vdy71_platform_sim::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vdy71_platform_sim::eval_step\n"); );
    m_evalLoop.eval();
}

void Vdy71_platform_sim::evalBegin() {
#ifdef VL_DEBUG
    // Debug assertions
    Vdy71_platform_sim___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
}

void Vdy71_platform_sim::evalEnd() {
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
    vlSymsp->TOP.__VdlySched.cleanupForevered();
}

void Vdy71_platform_sim::evalStatic() {
    Vdy71_platform_sim___024root___eval_static(&(vlSymsp->TOP));
}

void Vdy71_platform_sim::evalInitial() {
    Vdy71_platform_sim___024root___eval_initial(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalStl(bool firstIteration) {
    return Vdy71_platform_sim___024root___eval_stl(&(vlSymsp->TOP), firstIteration);
}

void Vdy71_platform_sim::evalSample() {
    Vdy71_platform_sim___024root___eval_sample(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalIco(bool firstIteration) {
    return Vdy71_platform_sim___024root___eval_ico(&(vlSymsp->TOP), firstIteration);
}

bool Vdy71_platform_sim::evalAct() {
    return Vdy71_platform_sim___024root___eval_act(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalInact() {
    return Vdy71_platform_sim___024root___eval_inact(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalNba() {
    return Vdy71_platform_sim___024root___eval_nba(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalObs() {
    return Vdy71_platform_sim___024root___eval_obs(&(vlSymsp->TOP));
}

bool Vdy71_platform_sim::evalReact() {
    return Vdy71_platform_sim___024root___eval_react(&(vlSymsp->TOP));
}

void Vdy71_platform_sim::evalPostponed() {
    Vdy71_platform_sim___024root___eval_postponed(&(vlSymsp->TOP));
}

void Vdy71_platform_sim::evalFinal() {
    Vdy71_platform_sim___024root___eval_final(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersStl() {
    Vdy71_platform_sim___024root___eval_dump_triggers__stl(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersIco() {
    Vdy71_platform_sim___024root___eval_dump_triggers__ico(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersAct() {
    Vdy71_platform_sim___024root___eval_dump_triggers__act(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersNba() {
    Vdy71_platform_sim___024root___eval_dump_triggers__nba(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersObs() {
    Vdy71_platform_sim___024root___eval_dump_triggers__obs(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vdy71_platform_sim::dumpTriggersReact() {
    Vdy71_platform_sim___024root___eval_dump_triggers__react(&(vlSymsp->TOP));
}

//============================================================
// Events and timing
bool Vdy71_platform_sim::eventsPending() { return !vlSymsp->TOP.__VdlySched.empty() && !contextp()->gotFinish(); }

uint64_t Vdy71_platform_sim::nextTimeSlot() { return vlSymsp->TOP.__VdlySched.nextTimeSlot(); }

//============================================================
// Utilities

const char* Vdy71_platform_sim::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

VL_ATTR_COLD void Vdy71_platform_sim::final() {
    contextp()->executingFinal(true);
    evalFinal();
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vdy71_platform_sim::hierName() const { return vlSymsp->name(); }
const char* Vdy71_platform_sim::modelName() const { return "Vdy71_platform_sim"; }
unsigned Vdy71_platform_sim::threads() const { return 1; }
void Vdy71_platform_sim::prepareClone() const { contextp()->prepareClone(); }
void Vdy71_platform_sim::atClone() const {
    contextp()->threadPoolpOnClone();
}
