#pragma once
// Prepared-key fixtures only. Clock the real non-jump tag-commit writer;
// then reapply the old fixture's already-forced context without touching any
// new predicate or owner field. No mode RAM/coordinate/residual write occurs.
static uint64_t tile_priming_edges=0;
static void prime_tile_key(Vadmission_probe&d,Vadmission_probe___024root&r) {
    require(!d.reset&&!d.start&&!d.abort_packet,"tile primer live context");
    const unsigned state=QOLD(state),bits=QOLD(bits_left),cache=QOLD(bit_cache);
    const unsigned mixed=QOLD(mixed_bit),second=QOLD(tag_second),first=QOLD(first_tag_bit);
    const unsigned visible=QOLD(group_visible),tag=QOLD(group_tag);
    const uint32_t tile=QOLD(tile),end=QOLD(group_end),epoch=QOLD(receipt_epoch);
    const unsigned plane=QOLD(plane);
    require(tile==QNEW(tile)&&end==QNEW(group_end)&&plane==QNEW(plane),"paired old tile fixture key");
    QBOTH(state,8U);QBOTH(bits_left,1U);QBOTH(bit_cache,0U);
    QBOTH(mixed_bit,0U);QBOTH(tag_second,1U);QBOTH(first_tag_bit,0U);QBOTH(group_visible,1U);
    d.clk=0;d.eval();require(!d.mismatch,"tile primer all-public low");
    require(!QOLD(mode_write_enable)&&!QNEW(mode_write_enable),"tag primer has no speculative mode write");
    const auto monitored=tile_before(d,false);
    d.clk=1;d.eval();require(!d.mismatch,"tile primer all-public high");
    tile_after(d,monitored,false);
    d.clk=0;d.eval();require(!d.mismatch,"tile primer all-public falling");
    ++tile_priming_edges;
    require(QOLD(state)==10U&&QNEW(state)==10U,"actual tag writer enters first group consume");
    require(QNEW(tile)==tile&&QNEW(group_end)==end&&QNEW(plane)==plane,"tag writer keeps full fixture key");
    require(QNEW(tile_pred_owner_valid)&&QNEW(group_pred_owner_valid)&&
        QNEW(tile_pred_owner_tile)==tile&&QNEW(group_pred_owner_tile)==tile&&
        QNEW(tile_pred_owner_epoch)==epoch&&QNEW(group_pred_owner_epoch)==epoch&&
        QNEW(group_pred_owner_end)==end,"real tag writer owns complete captured key");
    static std::ofstream trace("tile-primer.jsonl");
    require(bool(trace),"tile primer trace open");
    trace<<"{\"type\":\"prepared_key_primer\",\"edge\":"<<tile_priming_edges
         <<",\"target_state\":"<<state<<",\"plane\":"<<plane<<",\"tile\":"<<tile
         <<",\"end\":"<<end<<",\"epoch\":"<<epoch<<",\"real_writer_state\":8,\"next_state\":10,\"equal\":true}\n";
    trace.flush();
    // Preserve the original forced fixture, not a natural state chronology.
    // Actual clock/counter increments remain and are measured separately.
    QBOTH(state,state);QBOTH(bits_left,bits);QBOTH(bit_cache,cache);
    QBOTH(mixed_bit,mixed);QBOTH(tag_second,second);QBOTH(first_tag_bit,first);
    QBOTH(group_visible,visible);QBOTH(group_tag,tag);
}
