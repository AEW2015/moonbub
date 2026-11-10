#include "tb_successor.cpp"

static void factor_campaign(unsigned seed){
    const uint64_t before_clocks=factor_prepared.clocks;
    factor_need(before_clocks==275334U,"retained V126 monitored clock ledger unchanged before V127 tests");
    uint64_t wire_cases=0,random_cases=0,clock_cases=0,cancel_cases=0,error67_cases=0,wrap_cases=0;
    unsigned patterns_seen=0,mode_mask=0,emit_mask=0,ready_mask=0,guard_mask=0;
    const std::array<uint32_t,8> epochs{{0U,1U,65535U,65536U,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}};
    const std::array<unsigned,6> blocks{{0U,1U,32767U,32768U,65534U,65535U}};
    {
        Driver driver(seed,"/dev/null");auto&d=driver.d;owner_reset(d);
        auto wire=[&](uint32_t epoch,unsigned block,uint32_t scalar_epoch,unsigned scalar_block,
                     uint32_t e0,uint32_t e1,unsigned b0,unsigned b1,unsigned mode,unsigned emit,unsigned ready,unsigned guards,unsigned pattern){
            set_wire_context(d,epoch,block,e0,e1,b0,b1,mode,emit,ready,1,true,guards);
            BS(active_epoch,scalar_epoch);BS(output_block,scalar_block);equal(d);
            const bool scalar=scalar_epoch==epoch&&scalar_block==block;
            const bool bank0=e0==epoch&&b0==block,bank1=e1==epoch&&b1==block;
            const bool match=mode==2U?(emit?bank1:bank0):scalar;
            const bool allowed=match&&!(guards&3U);
            require_owner(bool(NEW(scalar_owner_match))==scalar,"V127 independent raw scalar full32/full16 producer lane");
            require_owner(NEW(tile_owner_match)==unsigned(bank0|(bank1<<1U)),"V127 independently preserved both-bank lane values");
            require_owner(bool(NEW(child_owner_match))==match&&bool(OLD(child_owner_match))==match,"V127 all-mode selected-fields vs three-lane identity");
            require_owner(bool(NEW(child_out_ready))==allowed&&bool(OLD(child_out_ready))==allowed,"V127 invalid/unready full-width ready identity");
            ++wire_cases;mode_mask|=1U<<mode;emit_mask|=1U<<emit;ready_mask|=1U<<ready;guard_mask|=1U<<guards;patterns_seen|=1U<<(pattern&15U);
        };
        for(uint32_t epoch:epochs)for(unsigned block:blocks)for(unsigned pattern=0;pattern<64;++pattern)
          for(unsigned mode=0;mode<4;++mode)for(unsigned emit=0;emit<2;++emit)for(unsigned ready=0;ready<4;++ready)for(unsigned guards=0;guards<4;++guards){
            wire(epoch,block,epoch^((pattern&1U)?0U:0x80000000U),block^((pattern&2U)?0U:0x8000U),
                 epoch^((pattern&4U)?0U:0x80000000U),epoch^((pattern&16U)?0U:0x80000000U),
                 block^((pattern&8U)?0U:0x8000U),block^((pattern&32U)?0U:0x8000U),mode,emit,ready,guards,pattern);
        }
        factor_need(wire_cases==393216U,"exact V127 raw scalar/bank independent fullwidth matrix");
        std::mt19937 rng(seed);
        for(unsigned k=0;k<32768U;++k){
            const uint32_t epoch=rng();const unsigned block=rng()&65535U,pattern=k&63U;
            wire(epoch,block,(pattern&1U)?epoch:rng(),(pattern&2U)?block:rng()&65535U,
                 (pattern&4U)?epoch:rng(),(pattern&16U)?epoch:rng(),
                 (pattern&8U)?block:rng()&65535U,(pattern&32U)?block:rng()&65535U,k&3U,(k>>2U)&1U,(k>>3U)&3U,(k>>5U)&3U,pattern);
            ++random_cases;
        }
        owner_reset(d);
    }
    {
        Driver driver(seed,"/dev/null");auto&d=driver.d;owner_reset(d);
        for(uint32_t epoch:epochs)for(unsigned block:blocks)for(unsigned fault=0;fault<3;++fault)for(unsigned guards=0;guards<8;++guards){
            // Inherited coherent terminal fixture: bank tags/active child lease
            // agree; only original parent expected owner can be foreign.
            dispatch_context(d,epoch,block,fault);
            BS(output_block,block^0x8000U);equal(d);
            const bool scalar=NEW(raw_scalar_epoch)==NEW(current_child_epoch)&&NEW(raw_scalar_block)==NEW(expected_block);
            require_owner(bool(NEW(scalar_owner_match))==scalar,"V127 unrelated scalar block is live but unselected in tile mode");
            d.reset=guards&1U;d.abort_packet=bool(guards&2U);d.start=bool(guards&4U);
            tick_owner(d);++clock_cases;
            if(guards&3U){require_owner(d.frame_state==0U&&d.error==0&&!d.fault_o&&!d.out_valid,"V127 reset/abort still wins before foreign owner");++cancel_cases;}
            else if(fault){require_owner(d.frame_state==15U&&d.error==67U&&d.fault_o&&!d.done,"V127 coherent child/foreign parent remains error67 before release");++error67_cases;}
            else {
                require_owner(d.frame_state==12U&&d.error==0&&NEW(expected_block)==uint16_t(block+1U),"V127 terminal accepted count wrap/state unchanged");
                require_owner(NS(state)==23U&&NS(done)&&!NS(busy_owned),"V127 final scratch override and ready-return cycle unchanged");wrap_cases+=block==65535U;
            }
        }
        owner_reset(d);
    }
    const uint64_t added=factor_prepared.clocks-before_clocks;
    factor_need(wire_cases==425984U&&random_cases==32768U&&clock_cases==1152U&&cancel_cases==864U&&error67_cases==192U&&wrap_cases==16U,"V127 exact new semantic case counts");
    factor_need(added==2308U&&mode_mask==15U&&emit_mask==3U&&ready_mask==15U&&guard_mask==15U&&patterns_seen==65535U,"V127 exact separate extra clock/coverage ledger");
    std::cout<<"{\"type\":\"v127_owner_factor_verdict\",\"status\":\"TEST_PASS\",\"wire_cases\":"<<wire_cases<<",\"random_cases\":"<<random_cases<<",\"clock_cases\":"<<clock_cases<<",\"cancel_cases\":"<<cancel_cases<<",\"error67_cases\":"<<error67_cases<<",\"wrap_cases\":"<<wrap_cases<<",\"inherited_monitored_clock_edges\":"<<before_clocks<<",\"additional_clock_edges\":"<<added<<",\"reset_primer_edges\":1156,\"mode_mask\":"<<mode_mask<<",\"emit_mask\":"<<emit_mask<<",\"bank_ready_mask\":"<<ready_mask<<",\"guard_mask\":"<<guard_mask<<",\"all_cycle_identity_evals\":"<<factor_prepared.evals<<",\"scalar_true\":"<<factor_prepared.scalar_true<<",\"scalar_false\":"<<factor_prepared.scalar_false<<",\"invalid_selected_match\":"<<factor_prepared.invalid_ready<<",\"unready_selected_match\":"<<factor_prepared.unready_ready<<",\"added_public_cycles\":0,\"pair_skipped_edges\":0,\"old_checks_removed\":0,\"new_predicate_forces\":0,\"prepared_fixtures_are_natural_packets\":false}\n";
}
int main(int argc,char**argv){try{
    require_owner(inherited_successor_main(argc,argv)==0,"all retained V126 scalar/owner/caller contracts");
    if(std::string(argv[1])=="caller"){factor_natural_verdict();return 0;}
    factor_campaign(unsigned(std::stoul(argv[2])));return 0;
}catch(const std::exception&e){std::cerr<<"V127_OWNER_FACTOR_FAIL "<<e.what()<<'\n';return 1;}}
