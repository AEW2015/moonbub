#include "tb_owner_lanes.cpp"
#include "successor_priming.hpp"

static void prepared_successor_campaign(unsigned seed){
    Driver driver(seed,"/dev/null");auto&d=driver.d;
    const uint64_t start_clocks=successor_prepared.clocks,start_primers=successor_primer_edges,start_contexts=successor_contexts;
    uint64_t early_cases=0,walk_skips=0,walk_holds=0,advance_cases=0,cancel_cases=0,bad_owner=0,bad_bounds=0,empty_cases=0,accept_cases=0,stage_cases=0;
    // All lookup modes and reconstruction arbitration use actual one-edge RAM.
    for(unsigned p=0;p<3;++p)for(unsigned mode=0;mode<4;++mode)for(unsigned recon=0;recon<2;++recon){
        successor_context(d,p,mode,0x80000000U+seed,0,2,recon);tick_owner(d);
        require_owner(NEW(state)==(mode==2U?11U:9U)&&NEW(tile_cursor)==(mode==2U?0U:1U)&&NEW(producer_cell_cache)==successor_oracle(p,mode==2U?0U:1U),"actual earliest mode2/skip producer result");
        if(mode==2U)require_owner(d.out_qcell==0U&&d.out_qscale==2U&&NEW(cell_owner_valid),"mode2 uses old current scale/cell, not successor or reconstruction result");
        if(recon){
            require_owner(d.reconstruct_lookup_rsp,"concurrent reconstruction response remains separately owned");
        }
        ++early_cases;
    }
    // Consecutive real skips cross pair/row and LUT bank boundaries without
    // restoring cursor under an old owner. Full13 wrap is isolated scalar proof.
    for(unsigned p=0;p<3;++p){
        successor_context(d,p,0,seed,0,2);const unsigned base=p==0U?0U:p==1U?5400U:6750U;
        for(unsigned t=1;t<185;++t)OLD_ADMISSION(mode_store__DOT__words)[base+t]=NEW_ADMISSION(mode_store__DOT__words)[base+t]=(t%3U==2U?3U:t%3U);
        OLD_ADMISSION(mode_store__DOT__words)[base+185]=NEW_ADMISSION(mode_store__DOT__words)[base+185]=2;
        for(unsigned cell=0;cell<1350;++cell)OLD_ADMISSION(scale_store__DOT__words)[cell]=NEW_ADMISSION(scale_store__DOT__words)[cell]=2;
        for(unsigned t=0;t<185;++t){tick_owner(d);require_owner(NEW(state)==9U&&NEW(tile_cursor)==t+1U&&NEW(producer_cell_cache)==successor_oracle(p,t+1U),"coherent consecutive skip key/current-cell");tick_owner(d);++walk_skips;}
        tick_owner(d);require_owner(NEW(state)==11U&&NEW(tile_cursor)==185U&&NEW(mapped_cell)==successor_oracle(p,185U),"walk reaches real mode2 response at owned odd tile185");
        for(unsigned hold=0;hold<7;++hold){d.start=hold>=4;BS(bank_epoch[1],seed^(0x80000000U+hold));tick_owner(d);require_owner(NEW(state)==11U&&NEW(cell_owner_valid)&&NEW(prepared_successor_cell)==successor_oracle(p,186U),"held child/blocked raw start does not revoke successor");++walk_holds;}
        d.start=0;d.out_ready=1;tick_owner(d);require_owner(NEW(state)==9U&&NEW(tile_cursor)==186U&&NEW(producer_cell_cache)==successor_oracle(p,186U)&&NEW(prepared_successor_tile)==187U,"nonterminal dispatch consumes discriminating odd-Y successor cell");
    }
    const std::array<uint32_t,8> epochs{{0,1,65535,65536,0x7fffffffU,0x80000000U,0xfffffffeU,0xffffffffU}};
    for(unsigned p=0;p<3;++p)for(uint32_t epoch:epochs)for(unsigned block:{0U,65535U})for(unsigned guards=0;guards<8;++guards){
        successor_context(d,p,2,epoch,block,3);d.out_ready=1;d.reset=guards&1U;d.abort_packet=bool(guards&2U);d.start=bool(guards&4U);d.epoch=NEW(frame_epoch)^0x80000000U;
        tick_owner(d);
        if(guards&3U){require_owner(NEW(state)==0U&&d.error==0&&!NEW(address_owner_valid)&&!NEW(cell_owner_valid),"reset/abort precedes prepared nonterminal accept");++cancel_cases;}
        else {require_owner(NEW(state)==9U&&NEW(tile_cursor)==1U&&NEW(producer_cell_cache)==successor_oracle(p,1U)&&NEW(expected_block)==uint16_t(block+1U),"full16 nonterminal wrap uses original full17 terminal comparison");++advance_cases;}
        d.reset=d.abort_packet=d.start=0;
    }
    for(unsigned p=0;p<3;++p)for(uint32_t epoch:epochs)for(unsigned fault=0;fault<2;++fault){
        successor_context(d,p,2,epoch,65535U,3);d.out_ready=1;
        if(fault==0U)BOTH(current_child_epoch,epoch^0x80000000U);else BOTH(expected_block,65535U^0x8000U);
        tick_owner(d);require_owner(NEW(state)==15U&&d.error==67U&&NEW(tile_cursor)==0U&&NEW(producer_cell_cache)==0U&&!NEW(cell_owner_valid),"original bad owner wins before prepared cell consumption");++bad_owner;
    }
    // Every actual preparation/earliest-response stage sees reset, abort and
    // blocked raw start. No accepted_start is forced.
    for(unsigned p=0;p<3;++p)for(unsigned phase=0;phase<3;++phase)for(unsigned guards=0;guards<8;++guards){
        successor_context(d,p,2,seed,0,phase);d.reset=guards&1U;d.abort_packet=bool(guards&2U);d.start=bool(guards&4U);tick_owner(d);
        if(guards&3U)require_owner(NEW(state)==0U&&!NEW(address_owner_valid)&&!NEW(cell_owner_valid),"canceled producer stage invalidates both owners");
        else require_owner(NEW(state)==(phase==0U?4U:phase==1U?10U:11U)&&NEW(address_owner_valid)&&bool(NEW(cell_owner_valid))==(phase!=0U),"blocked raw start preserves actual stage work");
        d.reset=d.abort_packet=d.start=0;++stage_cases;
    }
    // Bounds rejection intentionally starts unowned; it cannot manufacture a
    // certificate by forcing the old cursor. No bad-bound cell is consumed.
    for(unsigned p=0;p<3;++p)for(unsigned t:{p?1350U:5400U,8190U,8191U}){
        owner_reset(d);BOTH(state,9);BOTH(frame_running_owned,1);BOTH(plane,p);BOTH(tile_cursor,t);BOTH(producer_cell_cache,successor_oracle(p,t));BOTH(child_owned,0);
        tick_owner(d);require_owner(NEW(state)==15U&&d.error==67U&&!NEW(address_owner_valid)&&!NEW(cell_owner_valid),"unowned malformed MAP_REQ retains error67");++bad_bounds;
    }
    // Explicit quiescent old geometry for empty-plane intermediates, without
    // owning or forcing either new pipeline payload.
    for(unsigned p=0;p<3;++p){
        owner_reset(d);BOTH(state,13);BOTH(frame_running_owned,1);BOTH(plane,p);BOTH(tile_cursor,185);BOTH(producer_cell_cache,successor_oracle(p,185U));BOTH(child_owned,0);
        for(unsigned k=p;k<3;++k)OLD_ADMISSION(plane_blocks)[k]=NEW_ADMISSION(plane_blocks)[k]=0;
        for(unsigned k=p;k<3;++k){tick_owner(d);if(k<2U){require_owner(NEW(state)==3U&&NEW(tile_cursor)==185U,"NEXT_PLANE keeps intermediate tile");tick_owner(d);require_owner(NEW(state)==13U&&NEW(tile_cursor)==185U,"empty PREP never invents tile clear");}}
        require_owner(NEW(state)==14U&&d.done&&NEW(tile_cursor)==185U,"final empty-plane completion retains exact current cache");tick_owner(d);++empty_cases;
    }
    // Clear only a declared prepared child lease with no accepted requests;
    // actual accepted-start gating then revokes an otherwise valid snapshot.
    for(unsigned epoch:{0U,3U,4U}){
        successor_context(d,0,2,seed,0,2);BOTH(state,0);BOTH(frame_running_owned,0);BOTH(child_owned,0);BOTH(last_frame_epoch,3U);
        require_owner(!OS(outstanding)&&!NS(outstanding)&&!d.mem_req_ready&&!d.mem_rsp_valid,"prepared lease has no accepted physical debt to erase");
        BC(running,0);BC(allocation,0);BC(seal_sent,0);BS(state,0);BS(busy_owned,0);BS(sealed,0);BS(bank_ready,0);BS(tile_preparing,0);BS(prefetch_offer,0);BS(write_slot_valid,0);BS(overlap_mode,0);BS(prefetch_mode,0);
        equal(d);require_owner(d.start_ready&&!d.draining&&NEW(cell_owner_valid),"quiescent prepared lease permits actual accepted start");d.start=1;d.epoch=epoch;tick_owner(d);
        require_owner(NEW(state)==(epoch<=3U?15U:1U)&&d.error==(epoch<=3U?65U:0U)&&!NEW(address_owner_valid)&&!NEW(cell_owner_valid),"actual accepted start preserves epoch65 priority and revokes old preparation");d.start=0;++accept_cases;
    }
    owner_reset(d);
    require_owner(early_cases==24U&&walk_skips==555U&&walk_holds==21U&&advance_cases==96U&&cancel_cases==288U&&bad_owner==48U&&stage_cases==72U&&bad_bounds==9U&&empty_cases==3U&&accept_cases==3U,"all new producer pipeline semantic dimensions");
    require_owner(successor_contexts-start_contexts==534U&&successor_primer_edges-start_primers==1428U&&successor_prepared.clocks-start_clocks==3664U,"exact actual-writer/context/clock ledger");
    std::cout<<"{\"type\":\"v126_successor_campaign\",\"status\":\"TEST_PASS\",\"contexts\":"<<successor_contexts-start_contexts<<",\"actual_clock_edges\":"<<successor_prepared.clocks-start_clocks<<",\"primer_clock_edges\":"<<successor_primer_edges-start_primers<<",\"nonprimer_clock_edges\":"<<successor_prepared.clocks-start_clocks-(successor_primer_edges-start_primers)<<",\"earliest_cases\":"<<early_cases<<",\"walk_skip_advances\":"<<walk_skips<<",\"held_child_edges\":"<<walk_holds<<",\"nonterminal_advances\":"<<advance_cases<<",\"cancel_cases\":"<<cancel_cases<<",\"bad_owner_cases\":"<<bad_owner<<",\"stage_overlap_cases\":"<<stage_cases<<",\"unowned_bad_bound_cases\":"<<bad_bounds<<",\"empty_plane_cases\":"<<empty_cases<<",\"accepted_start_cases\":"<<accept_cases<<",\"new_payload_or_owner_forces\":0,\"prepared_domain_is_natural_packets\":false}\n";
}
int main(int argc,char**argv){try{
    require_owner(argc==5,"generic|caller seed vectors trace required");
    if(std::string(argv[1])=="caller"){
        require_owner(inherited_lanes_main(argc,argv)==0,"unchanged actual controller packet/physical debt oracle");
        successor_need(successor_natural.address_captures&&successor_natural.cell_consumes&&successor_natural.earliest_mode2&&successor_natural.earliest_skip&&successor_natural.held_owned,"natural callers exercise both stages/earliest responses/holds");successor_verdict(false);return 0;
    }
    require_owner(inherited_lanes_main(argc,argv)==0,"all V119 cache/nonce and V124 owner-lane checks retained");
    prepared_successor_campaign(unsigned(std::stoul(argv[2])));
    std::cerr<<"DIAGNOSTIC_MONITORED_CLOCKS "<<successor_prepared.clocks<<"\n";
    successor_need(successor_prepared.clocks==275333U,"new monitor covers retained tick_owner clocks plus exact prepared campaign");
    successor_verdict(true);return 0;
}catch(const std::exception&e){std::cerr<<"V126_SUCCESSOR_FAIL "<<e.what()<<'\n';return 1;}}
