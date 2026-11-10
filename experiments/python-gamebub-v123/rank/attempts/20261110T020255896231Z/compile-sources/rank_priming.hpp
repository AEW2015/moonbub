#pragma once
// Prepared-domain adapter only. The inherited arbitrary previous32 context
// keeps all its high bits; a real accepted RAW tuple and APPEND first establish
// its low6 rank threshold. New mask/owner fields are never forced.
static uint64_t rank_fixture_priming_edges=0;
static void rank_accept_predecessor(Vscratch_probe&d,RecordCoverage&c,unsigned phase,unsigned threshold) {
    record_context(d,phase,true,37);
    d.coef_block=0;d.coef_index=threshold;BOTH(written,threshold);
    record_edge(d,c,true);++rank_fixture_priming_edges;
    need(d.debug_state==2&&OLD(pending_position)==threshold&&NEW(pending_position)==threshold,"rank primer accepted complete original pending tuple");
}
static void prime_rank_threshold(Vscratch_probe&d,RecordCoverage&c,unsigned phase,unsigned threshold) {
    rank_accept_predecessor(d,c,phase,threshold);
    record_edge(d,c,false);++rank_fixture_priming_edges;
    need(d.debug_state==1&&NEW(previous_valid)&&NEW(previous_position)==threshold,"rank primer clocks original APPEND predecessor");
    uint64_t expected=0;
    for(unsigned k=0;k<64;++k)if(ranks[k]<=threshold)expected|=uint64_t(1)<<k;
    need(uint64_t(NEW(rank_threshold_mask))==expected,"independent all64 rank mask after real APPEND");
    need(NEW(rank_owner_valid)&&NEW(rank_owner_threshold)==threshold&&NEW(rank_owner_phase)==phase&&NEW(rank_owner_epoch)==9,"rank primer complete low6/phase/epoch owner");
}
