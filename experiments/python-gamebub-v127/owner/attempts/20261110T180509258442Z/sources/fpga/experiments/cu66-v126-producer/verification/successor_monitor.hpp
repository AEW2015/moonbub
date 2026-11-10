#pragma once
#include "Vready_probe___024root.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>

static void successor_need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
static unsigned successor_oracle(unsigned p,unsigned t){
    t&=8191U;
    const unsigned wide=p? t:((t/90U)/2U)*45U+(t%90U)/2U;
    return wide&2047U;
}
struct SuccessorStats {
    std::array<uint64_t,14> events{};
    uint64_t clocks=0,address_captures=0,rom_captures=0,cell_consumes=0,held_owned=0;
    uint64_t earliest_mode2=0,earliest_skip=0,blocked_starts=0,accepted_starts=0;
    uint64_t last_rom=0,max_age=0,current_checks=0;
    std::array<uint64_t,4> kills{};
};
static SuccessorStats successor_prepared,successor_natural;
struct SuccessorBefore {
    unsigned state,p,t,current,address,cell,lookup_mode,index,block,blocks;
    uint32_t frame,child;bool reset,abort,start,accepted,queue_fault,child_fault;
    bool lookup_rsp,out_valid,out_ready,child_valid,owner_match,address_valid,cell_valid,nonempty;
};
#define SP(n) d.rootp->ready_probe__DOT__new_dut__DOT__##n
static SuccessorBefore successor_before(Vready_probe&d,bool prepared){
    auto&s=prepared?successor_prepared:successor_natural;
    SuccessorBefore b{SP(state),SP(plane),SP(tile_cursor),SP(producer_cell_cache),SP(prepared_successor_tile),SP(prepared_successor_cell),SP(lookup_mode),unsigned(d.out_index),SP(expected_block),SP(selected_blocks),SP(frame_epoch),SP(current_child_epoch),bool(d.reset),bool(d.abort_packet),bool(d.start),bool(SP(accepted_start)),bool(d.probe_refill_overlap&&SP(frame_running)&&SP(queue_error)!=0),bool(SP(frame_running)&&SP(child_owned)&&SP(child_error)!=0),bool(SP(lookup_rsp)),bool(d.out_valid),bool(d.out_ready),bool(SP(child_out_valid)),bool(SP(child_owner_match)),bool(SP(address_owner_valid)),bool(SP(cell_owner_valid)),false};
    if(b.state==3U)b.nonempty=SP(fork_blocks)[b.p]!=0;
    ++s.clocks;
    const bool live=!b.reset&&!b.abort&&!b.accepted&&!b.queue_fault&&!b.child_fault;
    if(live&&b.state==9U&&b.t<(b.p?1350U:5400U)){
        successor_need(b.address_valid&&SP(address_owner_frame)==b.frame&&SP(address_owner_plane)==b.p&&SP(address_owner_tile)==b.t&&b.address==((b.t+1U)&8191U),"independent address first/held consume full13 key");
    }
    const bool consume=live&&((b.state==10U&&b.lookup_rsp&&b.lookup_mode!=2U)||
        (b.state==11U&&!(b.child_valid&&!b.owner_match)&&b.out_valid&&b.out_ready&&b.index==63U&&uint32_t(b.block)+1U!=b.blocks));
    if(consume){
        successor_need(b.cell_valid&&b.address_valid&&SP(cell_owner_frame)==b.frame&&SP(cell_owner_child_epoch)==b.child&&SP(cell_owner_plane)==b.p&&SP(cell_owner_tile)==b.t&&SP(cell_owner_address)==b.address&&b.cell==successor_oracle(b.p,(b.t+1U)&8191U),"independent complete cell key at original advance");++s.cell_consumes;
    }
    return b;
}
static void successor_after(Vready_probe&d,const SuccessorBefore&b,bool prepared){
    auto&s=prepared?successor_prepared:successor_natural;unsigned event=13;
    if(b.reset||b.abort){event=11;++s.kills[unsigned(b.reset)|unsigned(b.abort)*2U];}
    else if(b.accepted){event=10;++s.accepted_starts;}
    else if(b.queue_fault||b.child_fault)event=8;
    else if(b.state==3U)event=b.nonempty?0U:12U;
    else if(b.state==9U)event=b.t<(b.p?1350U:5400U)?1U:7U;
    else if(b.state==10U&&b.lookup_rsp)event=b.lookup_mode==2U?4U:2U;
    else if(b.state==11U){
        if(b.child_valid&&!b.owner_match)event=9;
        else if(b.out_valid&&b.out_ready&&b.index==63U)event=uint32_t(b.block)+1U==b.blocks?6U:3U;
    }else if(b.state==13U)event=5;
    ++s.events[event];
    const bool address_write=event==0U||event==2U||event==3U;
    if(address_write){
        const unsigned expected=event==0U?1U:(b.t+2U)&8191U;
        successor_need(SP(prepared_successor_tile)==expected&&SP(address_owner_valid)&&!SP(cell_owner_valid),"actual writer owns next full13 address and revokes consumed cell");++s.address_captures;
    }else successor_need(SP(prepared_successor_tile)==b.address,"nonwriter/cancel leaves unreset address payload unchanged");
    // The ROM's original-state phase intentionally samples even on cancellation.
    if(b.state==9U){successor_need(SP(prepared_successor_cell)==successor_oracle(b.p,b.address),"ROM-only register uses previous prepared address, including canceled sample");++s.rom_captures;}
    else successor_need(SP(prepared_successor_cell)==b.cell,"non-MAP_REQ edge holds successor cell payload");
    if(event==1U){
        successor_need(SP(cell_owner_valid)&&SP(cell_owner_frame)==b.frame&&SP(cell_owner_child_epoch)==b.child&&SP(cell_owner_plane)==b.p&&SP(cell_owner_tile)==b.t&&SP(cell_owner_address)==b.address,"MAP_REQ captures complete allocated-child lookup key");s.last_rom=s.clocks;
    }
    if(event==2U||event==4U){
        successor_need(s.last_rom!=0&&s.clocks>s.last_rom,"lookup never consumes ROM result before registered request edge");
        const uint64_t age=s.clocks-s.last_rom;s.max_age=age>s.max_age?age:s.max_age;
        if(age==1U){if(event==4U)++s.earliest_mode2;else ++s.earliest_skip;}
    }
    if(event==5U||event==7U||event==8U||event==9U||event==10U||event==11U||event==12U)
        successor_need(!SP(address_owner_valid)&&!SP(cell_owner_valid),"revocation/fault/empty-plane cannot authorize new pipeline consume");
    if(b.start&&!b.accepted&&!b.reset&&!b.abort)++s.blocked_starts;
    if(b.cell_valid&&event==13U&&!b.reset&&!b.abort&&!b.accepted){
        successor_need(SP(cell_owner_valid)&&SP(prepared_successor_cell)==b.cell&&SP(cell_owner_frame)==b.frame&&SP(cell_owner_child_epoch)==b.child&&SP(cell_owner_plane)==b.p&&SP(cell_owner_tile)==b.t,"held lookup/child tuple retains complete cell ownership");++s.held_owned;
    }
    successor_need(SP(producer_cell_cache)==successor_oracle(SP(plane),SP(tile_cursor)),"independent original current-cache invariant on every monitored edge");++s.current_checks;
    if(event==2U||event==3U)successor_need(SP(tile_cursor)==((b.t+1U)&8191U)&&SP(producer_cell_cache)==b.cell,"original advance copies staged value on same edge");
    if(event==4U)successor_need(SP(tile_cursor)==b.t&&SP(producer_cell_cache)==b.current&&SP(mapped_cell)==b.current&&SP(mapped_tile)==b.t,"earliest mode2 maps current cell and retains successor");
    if(event==6U)successor_need(SP(tile_cursor)==b.t&&SP(producer_cell_cache)==b.current,"terminal dispatch never advances geometry");
    if(event==5U)successor_need(SP(tile_cursor)==b.t&&SP(plane)==(b.p==2U?b.p:(b.p+1U)&3U),"NEXT_PLANE retains full original intermediate geometry");
    if(event==0U||event==2U||event==3U||event==5U||event==7U||event==8U||event==9U||event==10U||event==11U||event==12U)s.last_rom=0;
}
#undef SP
static void successor_verdict(bool prepared){
    const auto&s=prepared?successor_prepared:successor_natural;
    std::cout<<"{\"type\":\""<<(prepared?"v126_successor_generic_monitor":"v126_successor_caller_monitor")<<"\",\"status\":\"TEST_PASS\",\"events\":[";
    for(unsigned i=0;i<s.events.size();++i){if(i)std::cout<<',';std::cout<<s.events[i];}
    std::cout<<"],\"monitored_clocks\":"<<s.clocks<<",\"address_captures\":"<<s.address_captures<<",\"rom_samples\":"<<s.rom_captures<<",\"cell_consumes\":"<<s.cell_consumes<<",\"held_owned_edges\":"<<s.held_owned<<",\"earliest_mode2\":"<<s.earliest_mode2<<",\"earliest_skip\":"<<s.earliest_skip<<",\"max_lookup_age\":"<<s.max_age<<",\"blocked_raw_starts\":"<<s.blocked_starts<<",\"accepted_starts\":"<<s.accepted_starts<<",\"current_cache_checks\":"<<s.current_checks<<",\"added_public_cycles\":0,\"new_payload_or_owner_forces\":0}\n";
}
