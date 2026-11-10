#pragma once
// This adapter extends a declared synthetic HEADER_CHECK prestate with one
// genuine immediate-predecessor clock. It never forces the new predicate or
// restores state/error/counters afterward. Natural Bench traffic never calls it.
static uint64_t header_match_priming_edges=0;
static void prime_header_match(Vadmission_probe&d,Vadmission_probe___024root&r) {
    if(d.reset||d.start||d.abort_packet)return; // canceled CHECK cannot consume
    require(QOLD(state)==5U&&QNEW(state)==5U,"prime only direct CHECK fixture");
    require(QOLD(header_packet_total)==QNEW(header_packet_total)&&QOLD(size_bytes)==QNEW(size_bytes),"prime full35 tuple equality");
    const bool expected=uint64_t(QOLD(header_packet_total))==uint64_t(QOLD(size_bytes));
    const unsigned old_error=d.error;
    QBOTH(state,4U);QBOTH(header_index,127U);QBOTH(byte_value,QOLD(header)[127]);
    d.clk=0;d.eval();require(!d.mismatch,"priming public low comparison");
    require(!d.stage_read_req&&!d.stage_read_rsp&&!d.stage_write,"priming grants no physical transaction");
    d.clk=1;d.eval();require(!d.mismatch,"priming public high comparison");
    d.clk=0;d.eval();require(!d.mismatch,"priming public falling comparison");
    require(d.debug_state==5U&&d.error==old_error,"real predecessor returns CHECK without error restoration");
    require(bool(QNEW(prepared_header_total_matches))==expected,"independent priming full35 equality");
    ++header_match_priming_edges;
}
