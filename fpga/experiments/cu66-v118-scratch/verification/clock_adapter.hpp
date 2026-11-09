#pragma once
#include "Vscratch_probe.h"
#include <array>
#include <cstdint>
#include <stdexcept>
struct PrepareStats {inline static uint64_t transactions=0,extra_edges=0,poisoned=0,preedge_comparisons=0;};
class Vscratch_probe_prepared:public Vscratch_probe {
    bool last_external_clk=false;
    static void need_local(bool v,const char*m){if(!v)throw std::runtime_error(m);}
    std::array<uint32_t,10> tuple()const{return {begin_blocks,begin_raw,begin_serial_clear,begin_overlap,begin_prefetch,begin_tile_overlap,begin_count1,begin_count2,begin_count3,begin_epoch};}
    void restore(const std::array<uint32_t,10>&a){begin_blocks=a[0];begin_raw=a[1];begin_serial_clear=a[2];begin_overlap=a[3];begin_prefetch=a[4];begin_tile_overlap=a[5];begin_count1=a[6];begin_count2=a[7];begin_count3=a[8];begin_epoch=a[9];}
    void checked_eval(){pair_enable=1;Vscratch_probe::eval();need_local(!mismatch,"V116B all-edge exact generic scratch pair");}
    void private_check(){need_local(verify_preparing&&busy&&!begin_ready&&!coef_ready&&!band_end_ready&&!seal_ready&&!dense_valid&&!mem_req_valid&&!debug_outstanding&&!sealed&&!done&&!error,"private scratch prepare edge leaked work");}
public:
    bool adapter_enabled=true;
    // Legacy name retained for inherited fixture source, but BOTH current-source
    // parsers clock and compare on EVERY edge. There are no skipped intervals.
    void candidate_only_edge(){reference_clk=clk=0;checked_eval();reference_clk=clk=1;checked_eval();reference_clk=clk=0;checked_eval();last_external_clk=false;}
    void eval(){
        const bool external_clk=clk;
        reference_clk=external_clk;
        if(!adapter_enabled){checked_eval();last_external_clk=external_clk;return;}
        if(external_clk&&!last_external_clk){
            clk=reference_clk=0;checked_eval();
            const bool accepted=begin_valid&&begin_ready&&!mem_rsp_valid;
            if(accepted){
                ++PrepareStats::preedge_comparisons;
                need_local(!mem_req_valid&&!debug_outstanding,"preparation entered with physical debt");
                const auto saved=tuple();clk=reference_clk=1;checked_eval();private_check();
                begin_blocks^=0x1ffffU;begin_raw^=1;begin_serial_clear^=1;begin_overlap^=1;begin_prefetch^=1;begin_tile_overlap^=1;
                begin_count1^=0xa5a55a5aU;begin_count2^=0x5a5aa5a5U;begin_count3^=0xffffffffU;begin_epoch^=0xffffffffU;++PrepareStats::poisoned;
                for(unsigned j=0;j<3;++j){clk=reference_clk=0;checked_eval();private_check();clk=reference_clk=1;checked_eval();++PrepareStats::extra_edges;if(j<2)private_check();}
                need_local(!verify_preparing,"scratch prepare exceeded fixed three edges");restore(saved);checked_eval();++PrepareStats::transactions;
            }else{clk=reference_clk=1;checked_eval();}
        }else checked_eval();
        last_external_clk=external_clk;
    }
};
#define Vscratch_probe Vscratch_probe_prepared
