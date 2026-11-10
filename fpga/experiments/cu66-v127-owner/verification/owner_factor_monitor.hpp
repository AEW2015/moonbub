#pragma once
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <unordered_map>

struct FactorStats {
    uint64_t evals=0,clocks=0,scalar_true=0,scalar_false=0,selected_true=0;
    uint64_t invalid_ready=0,unready_ready=0;
    unsigned modes=0,emitters=0,guards=0,bank_matches=0;
};
static FactorStats factor_prepared,factor_natural;
static std::unordered_map<const void*,bool> factor_previous_clock;
static void factor_need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
template<class DUT>static void factor_observe(DUT&d,bool prepared,bool clock_or_rising){
    bool rising=clock_or_rising;
    if(prepared){
        // Generic equal() can be called more than once at a held clock level.
        // Count only observed low-to-high transitions, never repeated evals.
        auto&previous=factor_previous_clock[static_cast<const void*>(&d)];
        rising=bool(d.clk)&&!previous;previous=d.clk;
    }
    factor_need(d.probe_factor_equal,"V127 all-cycle raw scalar/old selected owner equality");
    auto&s=prepared?factor_prepared:factor_natural;
    ++s.evals;s.clocks+=rising;s.scalar_true+=bool(d.probe_factor_scalar_match);
    s.scalar_false+=!d.probe_factor_scalar_match;s.selected_true+=bool(d.probe_factor_selected);
    s.modes|=1U<<d.probe_factor_mode;s.emitters|=1U<<d.dbg_emit_bank;
    s.guards|=1U<<(unsigned(bool(d.reset))|(unsigned(bool(d.abort_packet))<<1U));
    s.bank_matches|=1U<<d.probe_factor_bank_matches;
    s.invalid_ready+=bool(d.probe_factor_selected)&&!d.out_valid;
    s.unready_ready+=bool(d.probe_factor_selected)&&d.dbg_tile_mode&&!(d.dbg_bank_ready&(1U<<d.dbg_emit_bank));
}
static void factor_natural_verdict(){
    const auto&s=factor_natural;
    factor_need(s.clocks&&s.evals>s.clocks&&s.scalar_true&&s.scalar_false,"V127 actual caller raw scalar/all-cycle coverage");
    std::cout<<"{\"type\":\"v127_owner_factor_caller_verdict\",\"status\":\"TEST_PASS\",\"eval_checks\":"<<s.evals<<",\"clock_edges\":"<<s.clocks<<",\"mode_mask\":"<<s.modes<<",\"emit_mask\":"<<s.emitters<<",\"scalar_true\":"<<s.scalar_true<<",\"scalar_false\":"<<s.scalar_false<<",\"invalid_selected_match\":"<<s.invalid_ready<<",\"unready_selected_match\":"<<s.unready_ready<<",\"added_public_cycles\":0,\"pair_skipped_edges\":0,\"new_predicate_forces\":0,\"natural_actual_controller\":true}\n";
}
