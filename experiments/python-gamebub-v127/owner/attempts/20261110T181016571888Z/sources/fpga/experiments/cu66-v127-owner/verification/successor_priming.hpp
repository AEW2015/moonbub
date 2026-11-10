#pragma once
#include <fstream>
static uint64_t successor_primer_edges=0,successor_contexts=0;
static void successor_prime_edge(Vready_probe&d,unsigned phase){
    const unsigned before=NEW(state);tick_owner(d);++successor_primer_edges;
    static std::ofstream trace("producer-primer.jsonl");require_owner(bool(trace),"producer primer trace open");
    trace<<"{\"type\":\"prepared_producer_primer\",\"edge\":"<<successor_primer_edges<<",\"phase\":"<<phase<<",\"before_state\":"<<before<<",\"after_state\":"<<unsigned(NEW(state))<<",\"plane\":"<<unsigned(NEW(plane))<<",\"tile\":"<<NEW(tile_cursor)<<",\"frame\":"<<NEW(frame_epoch)<<",\"child\":"<<NEW(current_child_epoch)<<",\"address\":"<<NEW(prepared_successor_tile)<<",\"cell\":"<<NEW(prepared_successor_cell)<<",\"equal\":true}\n";trace.flush();
}
// stop0: before PREP; stop1: before MAP_REQ; stop2: before earliest MAP_WAIT;
// stop3: after the real mode2 response. No new payload or owner is forced.
static void successor_context(Vready_probe&d,unsigned plane,unsigned mode,
                              uint32_t epoch,unsigned block,unsigned stop,
                              bool reconstruct=false){
    dispatch_context(d,epoch,block,0,63);++successor_contexts;
    require_owner(plane<3U&&stop<=3U,"bounded whole-producer prepared domain");
    d.out_ready=0;d.start=0;d.reconstruct_lookup_req=reconstruct;
    d.reconstruct_lookup_tile=8099;d.reconstruct_lookup_cell=1349;
    BOTH(plane,plane);BOTH(tile_cursor,0);BOTH(producer_cell_cache,0);
    BOTH(frame_epoch,0x24680000U+uint32_t(successor_contexts));
    BOTH(state,3);BOTH(frame_running_owned,1);BOTH(child_owned,0);
    const unsigned base=plane==0U?0U:plane==1U?5400U:6750U;
    for(unsigned p=0;p<3;++p){
        OLD_ADMISSION(plane_blocks)[p]=NEW_ADMISSION(plane_blocks)[p]=p==plane?block+2U:0U;
        OLD_ADMISSION(plane_offset)[p]=NEW_ADMISSION(plane_offset)[p]=0;
        OLD_ADMISSION(plane_length)[p]=NEW_ADMISSION(plane_length)[p]=32;
    }
    // Old fixture-only RAM/state initialization. All later lookup responses
    // come from actual synchronous mode/scale ports, including mode3 skips.
    OLD_ADMISSION(state)=NEW_ADMISSION(state)=26;
    OLD_ADMISSION(coord_valid)=NEW_ADMISSION(coord_valid)=0;
    OLD_ADMISSION(mode_store__DOT__words)[base]=NEW_ADMISSION(mode_store__DOT__words)[base]=mode;
    OLD_ADMISSION(mode_store__DOT__words)[8099]=NEW_ADMISSION(mode_store__DOT__words)[8099]=1;
    OLD_ADMISSION(scale_store__DOT__words)[0]=NEW_ADMISSION(scale_store__DOT__words)[0]=2;
    OLD_ADMISSION(scale_store__DOT__words)[1349]=NEW_ADMISSION(scale_store__DOT__words)[1349]=1;
    BS(blocks,block+2U);
    if(stop==0U)return;
    successor_prime_edge(d,0);require_owner(NEW(state)==4U&&NEW(address_owner_valid)&&NEW(prepared_successor_tile)==1U,"actual PREP zero writer establishes successor1");
    // Prepared control jump skips allocation/refill, not either geometry writer.
    // Natural allocation/refill/physical debt are retained in the caller tests.
    BOTH(state,9);BOTH(frame_running_owned,1);
    if(stop==1U)return;
    successor_prime_edge(d,1);
    require_owner(NEW(state)==10U&&NEW(cell_owner_valid)&&NEW(cell_owner_child_epoch)==epoch,"actual MAP_REQ ROM writer binds current child epoch");
    require_owner(NEW(lookup_rsp)&&NEW(lookup_mode)==mode,"earliest synchronous lookup response from initialized old RAM");
    if(stop==2U)return;
    require_owner(mode==2U,"dispatch primer uses a real mode2 reply");successor_prime_edge(d,2);
    require_owner(NEW(state)==11U&&NEW(tile_cursor)==0U&&NEW(producer_cell_cache)==0U&&NEW(cell_owner_valid),"real mode2 edge maps current geometry and holds successor");
    // The old V124 prepared block domain is independent of geometry. Reapply
    // only its original full16 counter, leaving every new key/value untouched.
    BOTH(expected_block,block);
}
