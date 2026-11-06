// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vcu71_sha_pair__pch.h"

//============================================================
// Constructors

Vcu71_sha_pair::Vcu71_sha_pair(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vcu71_sha_pair__Syms(contextp(), _vcname__, this)}
    , m_evalLoop{*this, /*convergeLimit:*/ 10000}
    , clk{vlSymsp->TOP.clk}
    , rst{vlSymsp->TOP.rst}
    , abort_i{vlSymsp->TOP.abort_i}
    , start_valid{vlSymsp->TOP.start_valid}
    , start_ready{vlSymsp->TOP.start_ready}
    , total_bytes{vlSymsp->TOP.total_bytes}
    , data_valid{vlSymsp->TOP.data_valid}
    , data_ready{vlSymsp->TOP.data_ready}
    , data{vlSymsp->TOP.data}
    , data_last{vlSymsp->TOP.data_last}
    , result_valid{vlSymsp->TOP.result_valid}
    , result_ready{vlSymsp->TOP.result_ready}
    , digest{vlSymsp->TOP.digest}
    , busy{vlSymsp->TOP.busy}
    , error{vlSymsp->TOP.error}
    , aborted{vlSymsp->TOP.aborted}
    , error_code{vlSymsp->TOP.error_code}
    , accepted_bytes{vlSymsp->TOP.accepted_bytes}
    , compressed_blocks{vlSymsp->TOP.compressed_blocks}
    , round_cycles{vlSymsp->TOP.round_cycles}
    , padding_bytes{vlSymsp->TOP.padding_bytes}
    , input_stall_cycles{vlSymsp->TOP.input_stall_cycles}
    , output_stall_cycles{vlSymsp->TOP.output_stall_cycles}
    , debug_fill_state{vlSymsp->TOP.debug_fill_state}
    , debug_core_state{vlSymsp->TOP.debug_core_state}
    , mismatch_any{vlSymsp->TOP.mismatch_any}
    , mismatch_fields{vlSymsp->TOP.mismatch_fields}
    , initial_word_reference{vlSymsp->TOP.initial_word_reference}
    , initial_word_candidate{vlSymsp->TOP.initial_word_candidate}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vcu71_sha_pair::Vcu71_sha_pair(const char* _vcname__)
    : Vcu71_sha_pair(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vcu71_sha_pair::~Vcu71_sha_pair() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vcu71_sha_pair___024root___eval_debug_assertions(Vcu71_sha_pair___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_static(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_initial(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD bool Vcu71_sha_pair___024root___eval_stl(Vcu71_sha_pair___024root* vlSelf, CData/*0:0*/ firstIteration);
void Vcu71_sha_pair___024root___eval_sample(Vcu71_sha_pair___024root* vlSelf);
bool Vcu71_sha_pair___024root___eval_ico(Vcu71_sha_pair___024root* vlSelf, CData/*0:0*/ firstIteration);
bool Vcu71_sha_pair___024root___eval_act(Vcu71_sha_pair___024root* vlSelf);
bool Vcu71_sha_pair___024root___eval_inact(Vcu71_sha_pair___024root* vlSelf);
bool Vcu71_sha_pair___024root___eval_nba(Vcu71_sha_pair___024root* vlSelf);
bool Vcu71_sha_pair___024root___eval_obs(Vcu71_sha_pair___024root* vlSelf);
bool Vcu71_sha_pair___024root___eval_react(Vcu71_sha_pair___024root* vlSelf);
void Vcu71_sha_pair___024root___eval_postponed(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_final(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__stl(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__ico(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__act(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__nba(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__obs(Vcu71_sha_pair___024root* vlSelf);
VL_ATTR_COLD void Vcu71_sha_pair___024root___eval_dump_triggers__react(Vcu71_sha_pair___024root* vlSelf);

void Vcu71_sha_pair::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vcu71_sha_pair::eval_step\n"); );
    m_evalLoop.eval();
}

void Vcu71_sha_pair::evalBegin() {
#ifdef VL_DEBUG
    // Debug assertions
    Vcu71_sha_pair___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
}

void Vcu71_sha_pair::evalEnd() {
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

void Vcu71_sha_pair::evalStatic() {
    Vcu71_sha_pair___024root___eval_static(&(vlSymsp->TOP));
}

void Vcu71_sha_pair::evalInitial() {
    Vcu71_sha_pair___024root___eval_initial(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalStl(bool firstIteration) {
    return Vcu71_sha_pair___024root___eval_stl(&(vlSymsp->TOP), firstIteration);
}

void Vcu71_sha_pair::evalSample() {
    Vcu71_sha_pair___024root___eval_sample(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalIco(bool firstIteration) {
    return Vcu71_sha_pair___024root___eval_ico(&(vlSymsp->TOP), firstIteration);
}

bool Vcu71_sha_pair::evalAct() {
    return Vcu71_sha_pair___024root___eval_act(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalInact() {
    return Vcu71_sha_pair___024root___eval_inact(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalNba() {
    return Vcu71_sha_pair___024root___eval_nba(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalObs() {
    return Vcu71_sha_pair___024root___eval_obs(&(vlSymsp->TOP));
}

bool Vcu71_sha_pair::evalReact() {
    return Vcu71_sha_pair___024root___eval_react(&(vlSymsp->TOP));
}

void Vcu71_sha_pair::evalPostponed() {
    Vcu71_sha_pair___024root___eval_postponed(&(vlSymsp->TOP));
}

void Vcu71_sha_pair::evalFinal() {
    Vcu71_sha_pair___024root___eval_final(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersStl() {
    Vcu71_sha_pair___024root___eval_dump_triggers__stl(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersIco() {
    Vcu71_sha_pair___024root___eval_dump_triggers__ico(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersAct() {
    Vcu71_sha_pair___024root___eval_dump_triggers__act(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersNba() {
    Vcu71_sha_pair___024root___eval_dump_triggers__nba(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersObs() {
    Vcu71_sha_pair___024root___eval_dump_triggers__obs(&(vlSymsp->TOP));
}

VL_ATTR_COLD void Vcu71_sha_pair::dumpTriggersReact() {
    Vcu71_sha_pair___024root___eval_dump_triggers__react(&(vlSymsp->TOP));
}

//============================================================
// Events and timing
bool Vcu71_sha_pair::eventsPending() { return false; }

uint64_t Vcu71_sha_pair::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vcu71_sha_pair::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

VL_ATTR_COLD void Vcu71_sha_pair::final() {
    contextp()->executingFinal(true);
    evalFinal();
    contextp()->executingFinal(false);
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vcu71_sha_pair::hierName() const { return vlSymsp->name(); }
const char* Vcu71_sha_pair::modelName() const { return "Vcu71_sha_pair"; }
unsigned Vcu71_sha_pair::threads() const { return 1; }
void Vcu71_sha_pair::prepareClone() const { contextp()->prepareClone(); }
void Vcu71_sha_pair::atClone() const {
    contextp()->threadPoolpOnClone();
}
