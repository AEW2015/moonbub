#pragma once
// Prepared-domain fixture only. Populate the final byte through the original
// RX port, then clock the real four-edge final-word predecessor sequence.
// No new payload/owner bit is forced, and no state/counter/error is restored.
static uint64_t bounds_priming_edges=0;
static bool prime_bounds(Vadmission_probe&d,Vadmission_probe___024root&r,
                         int cancel_phase=-1,unsigned flags=0) {
    require(!d.reset&&!d.start&&!d.abort_packet,"bounds priming live context");
    const unsigned continuation=QOLD(state);
    require((continuation==19U||continuation==21U)&&QNEW(state)==continuation,"bounds priming declared consume state");
    const uint32_t word=QOLD(word_value),cursor=QOLD(cursor),end=QOLD(residual_end);
    require(word==QNEW(word_value)&&cursor==QNEW(cursor)&&end==QNEW(residual_end),"bounds paired full32 tuple");
    auto edge=[&](int phase) {
        d.reset=phase==cancel_phase&&(flags&1U);
        d.start=phase==cancel_phase&&(flags&2U);
        d.abort_packet=phase==cancel_phase&&(flags&4U);
        d.clk=0;d.eval();require(!d.mismatch,"bounds fixture low public equality");
        d.clk=1;d.eval();require(!d.mismatch,"bounds fixture high public equality");
        d.clk=0;d.eval();require(!d.mismatch,"bounds fixture falling public equality");
        ++bounds_priming_edges;
        const bool canceled=d.reset||d.start||d.abort_packet;
        d.reset=d.start=d.abort_packet=0;
        if(canceled)require(!QNEW(bounds_owner_valid),"bounds owner cancellation priority");
        return canceled;
    };
    // This synthetic RX edge writes one safe address; it is separate from
    // natural packet traffic and from the original fixture's measured cycles.
    QBOTH(state,1U);QBOTH(received,0U);d.in_valid=1;d.in_last=0;d.in_data=uint8_t(word);
    require(QOLD(size_bytes)>1U,"safe fixture RX length");
    edge(-2);d.in_valid=0;
    QBOTH(state,30U);QBOTH(word_index,2U);QBOTH(word_return,continuation);
    QBOTH(fetch_return,30U);QBOTH(word_cursor,0xffffffffU);
    QBOTH(word_acc,word>>16U);QBOTH(byte_value,(word>>8U)&255U);
    if(edge(0))return false;
    require(d.debug_state==28U&&QNEW(word_index)==3U&&d.stage_read_addr==0U,"real final-byte request predecessor");
    if(edge(1))return false;
    require(d.debug_state==29U,"real final-byte synchronous read");
    if(edge(2))return false;
    require(d.debug_state==30U&&QNEW(byte_value)==uint8_t(word),"real final-byte response");
    if(edge(3))return false;
    require(d.debug_state==continuation&&QNEW(word_value)==word,"real final WORD_BYTE returns unchanged consume");
    require(QNEW(cursor)==cursor&&QNEW(residual_end)==end,"fixture preparation keeps full32 bounds");
    if(continuation==19U)
        require(bool(QNEW(prepared_number_outside))==(uint32_t(cursor+12U)>end),"independent full32 wrapped number bound");
    else {
        require(uint64_t(QNEW(bounds_length_total))==uint64_t(cursor)+4ULL+uint64_t(word),"independent complete full64 sum");
        require(bool(QNEW(prepared_length_invalid))==(word<46U||word>QOLD(selected_limit)||uint64_t(cursor)+4ULL+uint64_t(word)>uint64_t(end)),"independent complete full64 length fault");
    }
    return true;
}
