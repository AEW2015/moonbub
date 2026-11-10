#include "tb_owner.cpp"
#include "Vready_probe_br88_pipeline_v91h.h"
#include "tb_controller.cpp"

#define OC(n) d.rootp->__PVT__ready_probe__DOT__old_dut__DOT__child->n
#define NC(n) d.rootp->__PVT__ready_probe__DOT__new_dut__DOT__child->n
#define BC(n,v) do{const auto owner_value=(v);OC(n)=owner_value;NC(n)=owner_value;}while(0)
#define OS(n) d.rootp->__PVT__ready_probe__DOT__old_dut__DOT__child->scratch__DOT__##n
#define NS(n) d.rootp->__PVT__ready_probe__DOT__new_dut__DOT__child->scratch__DOT__##n
#define BS(n,v) do{const auto owner_value=(v);OS(n)=owner_value;NS(n)=owner_value;}while(0)
struct LaneCoverage {
    uint64_t wire_cases=0,random_cases=0,state_cases=0,ready_true=0,ready_false=0,invalid_ready=0,unready_ready=0;
    uint64_t clock_cases=0,error67=0,cancels=0,wraps=0,holds=0,response_cases=0;
    unsigned modes=0,emitters=0,ready_masks=0,guard_masks=0;
};
static void owner_reset(Vready_probe&d) {
    d.start=d.abort_packet=0;d.reset=1;d.in_valid=d.cache_valid=0;d.mem_req_ready=0;
    // Retire a declared synthetic response owner if a preceding prepared
    // context retained it. Actual physical leases are tested by the caller.
    d.mem_rsp_valid=OS(outstanding);d.mem_rsp_epoch=OS(request_epoch);d.mem_rsp_error=0;
    tick_owner(d);d.reset=0;d.mem_rsp_valid=0;
}
static void set_wire_context(Vready_probe&d,uint32_t expected_epoch,unsigned expected_block,
                            uint32_t e0,uint32_t e1,unsigned b0,unsigned b1,
                            unsigned mode,unsigned emit,unsigned ready,unsigned running,
                            bool downstream,unsigned guards,unsigned parent_state=11) {
    d.reset=guards&1U;d.abort_packet=(guards>>1U)&1U;d.start=0;
    d.in_valid=d.cache_valid=d.mem_req_ready=d.mem_rsp_valid=d.mem_rsp_error=0;
    d.out_ready=downstream;
    BOTH(state,parent_state);BOTH(frame_running_owned,parent_state!=0&&parent_state!=14&&parent_state!=15);
    BOTH(error,0);BOTH(fault_o,0);BOTH(child_owned,0);
    BOTH(current_child_epoch,expected_epoch);BOTH(expected_block,expected_block);
    BC(running,running);BC(error,0);BC(allocation,1);BC(seal_sent,1);
    BS(raw_mode,mode&1U);BS(tile_overlap_mode,(mode>>1U)&1U);BS(emit_bank,emit);
    BS(state,mode==2U?29U:20U);BS(busy_owned,1);BS(sealed,1);BS(error,0);
    BS(tile_preparing,0);BS(prefetch_offer,0);BS(outstanding,0);BS(write_slot_valid,0);
    BS(overlap_mode,0);BS(prefetch_mode,0);BS(bank_ready,ready);
    BS(active_epoch,expected_epoch^((mode&1U)?0x80000000U:0U));
    BS(output_block,expected_block^((mode&1U)?0x8000U:0U));
    BS(output_index,0);BS(tile_emit_index,0);BS(tile_valid[0],0ULL);BS(tile_valid[1],0ULL);
    BS(bank_epoch[0],e0);BS(bank_epoch[1],e1);BS(bank_block[0],b0);BS(bank_block[1],b1);
}
static void check_wire(Vready_probe&d,LaneCoverage&v,uint32_t epoch,unsigned block,
                       uint32_t e0,uint32_t e1,unsigned b0,unsigned b1,
                       unsigned mode,unsigned emit,unsigned ready,unsigned running,
                       bool downstream,unsigned guards,unsigned parent_state=11) {
    set_wire_context(d,epoch,block,e0,e1,b0,b1,mode,emit,ready,running,downstream,guards,parent_state);
    equal(d);
    const bool lane0=e0==epoch&&b0==block,lane1=e1==epoch&&b1==block;
    const bool match=mode==2U?(emit?lane1:lane0):!(mode&1U);
    const bool allowed=parent_state==11U&&downstream&&match&&!(guards&3U);
    require_owner(NEW(tile_owner_match)==unsigned(lane0|(lane1<<1U)),"independent both-bank full32/full16 lane truth table");
    require_owner(bool(NEW(child_owner_match))==match,"independent selected owner/fallback");
    require_owner(bool(NEW(child_out_ready))==allowed&&bool(OLD(child_out_ready))==allowed,"ready return retains invalid/unready owner semantics");
    require_owner(bool(d.out_valid)==(parent_state==11U&&bool(OLD(child_out_valid))&&match&&!(guards&3U)),"same literal owner qualification for public valid");
    if(mode==2U)require_owner(NEW(child_out_epoch)==(emit?e1:e0)&&d.out_block==(emit?b1:b0),"all tile raw bank views including unready cycles");
    ++v.wire_cases;v.ready_true+=allowed;v.ready_false+=!allowed;
    v.invalid_ready+=allowed&&!OLD(child_out_valid);v.unready_ready+=allowed&&mode==2U&&!(ready&(1U<<emit));
    v.modes|=1U<<mode;v.emitters|=1U<<emit;v.ready_masks|=1U<<ready;v.guard_masks|=1U<<guards;
}
static void wire_domain(unsigned seed,LaneCoverage&v) {
    Driver driver(seed,"/dev/null");auto&d=driver.d;owner_reset(d);
    const std::array<uint32_t,8> epochs{{0U,1U,65535U,65536U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}};
    const std::array<unsigned,6> blocks{{0U,1U,32767U,32768U,65534U,65535U}};
    for(uint32_t epoch:epochs)for(unsigned block:blocks)for(unsigned pattern=0;pattern<16;++pattern)
      for(unsigned mode=0;mode<4;++mode)for(unsigned emit=0;emit<2;++emit)for(unsigned ready=0;ready<4;++ready)
       for(unsigned running=0;running<2;++running)for(unsigned downstream=0;downstream<2;++downstream)for(unsigned guards=0;guards<4;++guards)
        check_wire(d,v,epoch,block,epoch^((pattern&1U)?0U:0x80000000U),epoch^((pattern&4U)?0U:0x80000000U),
                   block^((pattern&2U)?0U:0x8000U),block^((pattern&8U)?0U:0x8000U),mode,emit,ready,running,downstream,guards);
    require_owner(v.wire_cases==393216U,"fixed bank owner boundary matrix");
    std::mt19937 random(seed);
    for(unsigned k=0;k<65536U;++k) {
        const uint32_t epoch=random();const unsigned block=random()&65535U,pattern=k&15U;
        check_wire(d,v,epoch,block,(pattern&1U)?epoch:random(),(pattern&4U)?epoch:random(),
                   (pattern&2U)?block:random()&65535U,(pattern&8U)?block:random()&65535U,
                   k&3U,(k>>2U)&1U,(k>>3U)&3U,(k>>5U)&1U,(k>>6U)&1U,(k>>7U)&3U);
        ++v.random_cases;
    }
    for(unsigned state=0;state<256;++state)for(unsigned mode=0;mode<4;++mode)for(unsigned emit=0;emit<2;++emit)for(unsigned guards=0;guards<4;++guards) {
        check_wire(d,v,0x80000000U,65535U,0x80000000U,0U,65535U,0U,mode,emit,3,1,true,guards,state);++v.state_cases;
    }
    require_owner(v.wire_cases==466944U&&v.random_cases==65536U&&v.state_cases==8192U,"full-width wire/state dimensions");
    require_owner(v.ready_true&&v.ready_false&&v.invalid_ready&&v.unready_ready&&v.modes==15&&v.emitters==3&&v.ready_masks==15&&v.guard_masks==15,"all bank/mode/invalid/ready branches");
    owner_reset(d);
}
static void dispatch_context(Vready_probe&d,uint32_t epoch,unsigned block,unsigned fault,unsigned index=63) {
    owner_reset(d);
    set_wire_context(d,epoch^(fault==1U?0x80000000U:0U),block^(fault==2U?0x8000U:0U),
                     epoch,epoch^0x80000000U,block,block^0x8000U,2,0,1,1,true,0);
    BOTH(selected_blocks,block+1U);BOTH(child_owned,1);BOTH(tile_cursor,0);BOTH(producer_cell_cache,0);BOTH(plane,0);
    BS(active_epoch,epoch);BS(blocks,block+1U);BS(tile_emit_index,index);
    BC(allocation,1);BC(seal_sent,1);
}
static void clocked_domain(unsigned seed,LaneCoverage&v) {
    Driver driver(seed,"/dev/null");auto&d=driver.d;owner_reset(d);
    const std::array<uint32_t,8> epochs{{0U,1U,65535U,65536U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}};
    const std::array<unsigned,6> blocks{{0U,1U,32767U,32768U,65534U,65535U}};
    for(uint32_t epoch:epochs)for(unsigned block:blocks)for(unsigned fault=0;fault<3;++fault)for(unsigned guards=0;guards<8;++guards) {
        dispatch_context(d,epoch,block,fault);
        d.reset=guards&1U;d.abort_packet=(guards>>1U)&1U;d.start=(guards>>2U)&1U;
        tick_owner(d);++v.clock_cases;
        if(guards&3U){require_owner(d.frame_state==0&&d.error==0&&!d.fault_o&&!d.out_valid,"reset/abort precedes bad-owner/last-output control");++v.cancels;}
        else if(fault){require_owner(d.frame_state==15&&d.error==67&&d.fault_o&&!d.done,"bad owner error67 wins before terminal acceptance");++v.error67;}
        else {
            require_owner(d.frame_state==12&&d.error==0&&NEW(expected_block)==uint16_t(block+1U),"same-edge expected-block wrap and WAIT_DONE transition");
            require_owner(NS(state)==23U&&NS(done)&&!NS(busy_owned),"last tile keeps final scratch FINISHED/busy override");
            v.wraps+=block==65535U;
        }
    }
    for(uint32_t epoch:epochs)for(unsigned block:blocks) {
        dispatch_context(d,epoch,block,0,62);d.out_ready=0;equal(d);
        const unsigned before_block=d.out_block,before_index=d.out_index,before_value=d.out_value;const uint32_t before_epoch=NEW(child_out_epoch);
        for(unsigned edge=0;edge<7;++edge) {
            BS(bank_epoch[1],epoch^(0x80000000U+edge));BS(bank_block[1],uint16_t(block+edge+1U));tick_owner(d);
            require_owner(d.out_valid&&d.out_block==before_block&&d.out_index==before_index&&d.out_value==before_value&&NEW(child_out_epoch)==before_epoch,"held selected output ignores poisoned unready opposite bank");++v.holds;
        }
        d.out_ready=1;tick_owner(d);require_owner(NS(tile_emit_index)==63&&NEW(expected_block)==block,"index62 acceptance is not a premature tile release");
        tick_owner(d);require_owner(d.frame_state==12&&NEW(expected_block)==uint16_t(block+1U)&&!NS(busy_owned),"index63 release preserves owner/busy timing");
    }
    // Coherent prepared response contexts; synthetic debt is labelled and
    // retired by owner_reset. Natural accepted requests/ACKs are caller-tested.
    for(uint32_t epoch:epochs)for(unsigned response=0;response<7;++response)for(unsigned guards=0;guards<4;++guards) {
        dispatch_context(d,epoch,0,0);BS(state,11);BS(sealed,0);BS(return_state,29);BS(blocks,2);
        BS(request_epoch,epoch);BS(read_segment,0);BS(read_address,32);BS(transfer_address,32);BS(used_bytes,4096);
        const bool debt=response>=2U;BS(outstanding,debt);BS(prefetch_offer,response==5U);BS(write_slot_valid,response==6U);BS(overlap_mode,response==6U);
        d.mem_rsp_valid=response!=0;d.mem_rsp_epoch=epoch^(response==2U?0x80000000U:0U);d.mem_rsp_error=response>=4U;
        for(unsigned word=0;word<4;++word)d.mem_rsp_data[word]=0;
        d.reset=guards&1U;d.abort_packet=(guards>>1U)&1U;tick_owner(d);++v.response_cases;
        unsigned state=11,error=0;bool outstanding=debt;
        if(guards){if(response==2U){state=25;error=6;}else{state=0;outstanding=false;}}
        else if(response==1U){state=24;error=6;}
        else if(response==2U){state=25;error=6;}
        else if(response>=4U){state=24;error=5;outstanding=false;}
        else if(response==3U){state=29;outstanding=false;}
        require_owner(NS(state)==state&&NS(error)==error&&bool(NS(outstanding))==outstanding,"independent original response/cancel/debt priority");
    }
    owner_reset(d);
    require_owner(v.clock_cases==1152&&v.error67==192&&v.cancels==864&&v.wraps==16&&v.holds==336&&v.response_cases==224,"all prepared clock/owner/response domains");
}
int inherited_lanes_main(int argc,char**argv) {
    try {
        require_owner(argc==5,"usage: ready_probe generic|caller seed vectors trace");
        const std::string mode=argv[1];
        if(mode=="caller") {
            char* caller[]={argv[0],argv[3],argv[2],argv[4]};return inherited_controller_main(4,caller);
        }
        require_owner(mode=="generic","known focused mode");
        char* generic[]={argv[0],argv[2],argv[4]};
        require_owner(inherited_owner_main(3,generic)==0,"all original producer/cache/nonce oracles");
        LaneCoverage v;wire_domain(unsigned(std::stoul(argv[2])),v);clocked_domain(unsigned(std::stoul(argv[2])),v);
        std::cout<<"{\"type\":\"v124_owner_lanes_verdict\",\"status\":\"TEST_PASS\",\"wire_cases\":"<<v.wire_cases<<",\"random_fullwidth_cases\":"<<v.random_cases<<",\"state_cases\":"<<v.state_cases<<",\"mode_mask\":"<<v.modes<<",\"emit_mask\":"<<v.emitters<<",\"bank_ready_mask\":"<<v.ready_masks<<",\"guard_mask\":"<<v.guard_masks<<",\"invalid_ready_true\":"<<v.invalid_ready<<",\"unready_ready_true\":"<<v.unready_ready<<",\"clock_cases\":"<<v.clock_cases<<",\"error67_cases\":"<<v.error67<<",\"cancel_cases\":"<<v.cancels<<",\"wrap_cases\":"<<v.wraps<<",\"held_edges\":"<<v.holds<<",\"response_contexts\":"<<v.response_cases<<",\"prepared_domain_fixtures_are_natural_packets\":false,\"added_public_cycles\":0,\"error_cycle_delta\":0,\"pair_skipped_edges\":0,\"old_checks_removed\":0}\n";
        return 0;
    }catch(const std::exception&e){std::cerr<<"V124_OWNER_LANES_FAIL "<<e.what()<<'\n';return 1;}
}
