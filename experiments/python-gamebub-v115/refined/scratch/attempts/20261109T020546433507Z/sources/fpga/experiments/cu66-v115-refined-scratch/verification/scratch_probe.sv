module scratch_probe (
    input logic clk, reference_clk, pair_enable, reset,
    input logic begin_valid, output logic begin_ready,
    input logic [16:0] begin_blocks, input logic begin_raw, begin_serial_clear, begin_overlap, begin_prefetch, begin_tile_overlap,
    input logic [31:0] begin_count1, begin_count2, begin_count3, begin_epoch,
    input logic coef_valid, output logic coef_ready,
    input logic [1:0] coef_band, input logic [15:0] coef_block,
    input logic [5:0] coef_index, input logic signed [15:0] coef_value,
    input logic [31:0] coef_epoch,
    input logic band_end_valid, output logic band_end_ready,
    input logic [1:0] band_end_band, input logic [31:0] band_end_epoch,
    input logic seal_valid, output logic seal_ready, input logic [31:0] seal_epoch,
    input logic abort_valid, input logic [31:0] abort_epoch,
    output logic busy, sealed, done, output logic [3:0] error,
    output logic [31:0] active_epoch=0, output logic [18:0] used_bytes,
    output logic dense_valid, input logic dense_ready,
    output logic [15:0] dense_block, output logic [5:0] dense_index,
    output logic signed [15:0] dense_value, output logic [31:0] dense_epoch,
    output logic mem_req_valid, input logic mem_req_ready,
    output logic mem_req_write, output logic [17:0] mem_req_addr,
    output logic [127:0] mem_req_data, output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid, output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data, input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    // Direct views of existing registers; observability adds no state changes.
    output logic [4:0] debug_state, debug_return_state,
    output logic debug_outstanding,
    output logic [2:0] debug_phase,
    output logic [4:0] debug_assembly_bytes,
    output logic [3:0] debug_cache_valid,
    output logic debug_prefetch_offer, debug_prefetch_launch, debug_prefetch_use,
    output logic debug_tile_mode, debug_tile_preparing, debug_prepare_bank, debug_emit_bank,
    output logic [1:0] debug_bank_ready, debug_bank_owned, debug_emitter_state,
    output logic [15:0] debug_prepare_block,
    output logic [15:0] debug_bank_block [0:1],
    output logic [31:0] debug_bank_epoch [0:1],
    output logic debug_tile_prepare_start, debug_tile_publish, debug_tile_release,
    output logic debug_write_slot_valid, debug_assembler_full, debug_write_enqueue,
    output logic [2:0] debug_head_valid,
    output logic [2047:0] verify_tile_visible, verify_tile_private,
    output logic verify_tile_slot_valid, verify_tile_slot_bank,
    output logic [5:0] verify_tile_slot_index,
    output logic [15:0] verify_tile_slot_value,
    output logic verify_tile_event_valid,
    output logic [31:0] verify_tile_events, verify_tile_commits,
    output logic [31:0] verify_tile_back_to_back, verify_tile_zero_events, verify_tile_data_events,
    output logic mismatch,
    output logic verify_preparing, verify_prepare_cancel,
    output logic verify_cursor_equal, verify_cursor_owner_live,
    output logic [95:0] verify_reference_cursors,
    output logic [511:0] verify_cache_data,
    output logic [1215:0] verify_positions,
    output logic [95:0] verify_heads,
    output logic [56:0] verify_head_positions,
    output logic [95:0] verify_cursors,
    output logic [31:0] verify_read_word,
    output logic [31:0] verify_read_position,
    output logic [31:0] verify_read_address,
    output logic [1:0] verify_read_segment,
    output logic [1:0] verify_read_band,
    output logic  verify_position_use
);
    logic [31:0] aligned1,aligned12,aligned123,threshold1,threshold2,threshold3,capacity_upper,capacity_lower;
    logic [27:0] capacity_a;logic capacity_wrap;
    assign aligned1=(begin_count1*4+32'd15)&32'hfffffff0;
    assign aligned12=aligned1+((begin_count2*4+32'd15)&32'hfffffff0);
    assign aligned123=aligned12+((begin_count3*4+32'd15)&32'hfffffff0);
    assign threshold1=begin_count1/5+32'(begin_count1%5!=0);
    assign threshold2=begin_count2/15+32'(begin_count2%15!=0);
    assign threshold3=begin_count3/43+32'(begin_count3%43!=0);
    assign capacity_a=aligned123[31:4]+28'd2;
    assign capacity_upper={1'b0,(28'd16384-capacity_a),3'd0};
    assign capacity_lower={1'b0,(~capacity_a),3'd0};
    assign capacity_wrap=capacity_a>28'd16384;
    logic  old_begin_ready;
    logic  old_coef_ready;
    logic  old_band_end_ready;
    logic  old_seal_ready;
    logic  old_busy;
    logic  old_sealed;
    logic  old_done;
    logic [3:0] old_error;
    logic [31:0] old_active_epoch;
    logic [18:0] old_used_bytes;
    logic  old_dense_valid;
    logic [15:0] old_dense_block;
    logic [5:0] old_dense_index;
    logic signed [15:0] old_dense_value;
    logic [31:0] old_dense_epoch;
    logic  old_mem_req_valid;
    logic  old_mem_req_write;
    logic [17:0] old_mem_req_addr;
    logic [127:0] old_mem_req_data;
    logic [31:0] old_mem_req_epoch;
    logic  old_mem_rsp_ready;
    logic [4:0] old_debug_state;
    logic [4:0] old_debug_return_state;
    logic  old_debug_outstanding;
    logic [2:0] old_debug_phase;
    logic [4:0] old_debug_assembly_bytes;
    logic [3:0] old_debug_cache_valid;
    logic  old_debug_prefetch_offer;
    logic  old_debug_prefetch_launch;
    logic  old_debug_prefetch_use;
    logic  old_debug_tile_mode;
    logic  old_debug_tile_preparing;
    logic  old_debug_prepare_bank;
    logic  old_debug_emit_bank;
    logic [1:0] old_debug_bank_ready;
    logic [1:0] old_debug_bank_owned;
    logic [1:0] old_debug_emitter_state;
    logic [15:0] old_debug_prepare_block;
    logic [15:0] old_debug_bank_block[0:1];
    logic [31:0] old_debug_bank_epoch[0:1];
    logic  old_debug_tile_prepare_start;
    logic  old_debug_tile_publish;
    logic  old_debug_tile_release;
    logic  old_debug_write_slot_valid;
    logic  old_debug_assembler_full;
    logic  old_debug_write_enqueue;
    logic [2:0] old_debug_head_valid;
    logic [511:0] old_verify_cache_data;
    logic [1215:0] old_verify_positions;
    logic [95:0] old_verify_heads;
    logic [56:0] old_verify_head_positions;
    logic [95:0] old_verify_cursors;
    logic [31:0] old_verify_read_word;
    logic [31:0] old_verify_read_position;
    logic [31:0] old_verify_read_address;
    logic [1:0] old_verify_read_segment;
    logic [1:0] old_verify_read_band;
    logic  old_verify_position_use;
    observed_original original (
        .clk(reference_clk),
        .reset(reset),
        .begin_valid(begin_valid),
        .begin_ready(old_begin_ready),
        .begin_blocks(begin_blocks),
        .begin_raw(begin_raw),
        .begin_serial_clear(begin_serial_clear),
        .begin_overlap(begin_overlap),
        .begin_prefetch(begin_prefetch),
        .begin_tile_overlap(begin_tile_overlap),
        .begin_count1(begin_count1),
        .begin_count2(begin_count2),
        .begin_count3(begin_count3),
        .begin_epoch(begin_epoch),
        .begin_prefix1(aligned1),.begin_prefix12(aligned12),.begin_prefix123(aligned123),
        .begin_threshold1(threshold1),.begin_threshold2(threshold2),.begin_threshold3(threshold3),
        .begin_capacity_upper(capacity_upper),.begin_capacity_lower(capacity_lower),.begin_capacity_wrap(capacity_wrap),
        .coef_valid(coef_valid),
        .coef_ready(old_coef_ready),
        .coef_band(coef_band),
        .coef_block(coef_block),
        .coef_index(coef_index),
        .coef_value(coef_value),
        .coef_epoch(coef_epoch),
        .band_end_valid(band_end_valid),
        .band_end_ready(old_band_end_ready),
        .band_end_band(band_end_band),
        .band_end_epoch(band_end_epoch),
        .seal_valid(seal_valid),
        .seal_ready(old_seal_ready),
        .seal_epoch(seal_epoch),
        .abort_valid(abort_valid),
        .abort_epoch(abort_epoch),
        .busy(old_busy),
        .sealed(old_sealed),
        .done(old_done),
        .error(old_error),
        .active_epoch(old_active_epoch),
        .used_bytes(old_used_bytes),
        .dense_valid(old_dense_valid),
        .dense_ready(dense_ready),
        .dense_block(old_dense_block),
        .dense_index(old_dense_index),
        .dense_value(old_dense_value),
        .dense_epoch(old_dense_epoch),
        .mem_req_valid(old_mem_req_valid),
        .mem_req_ready(mem_req_ready),
        .mem_req_write(old_mem_req_write),
        .mem_req_addr(old_mem_req_addr),
        .mem_req_data(old_mem_req_data),
        .mem_req_epoch(old_mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),
        .mem_rsp_ready(old_mem_rsp_ready),
        .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch),
        .mem_rsp_error(mem_rsp_error),
        .debug_state(old_debug_state),
        .debug_return_state(old_debug_return_state),
        .debug_outstanding(old_debug_outstanding),
        .debug_phase(old_debug_phase),
        .debug_assembly_bytes(old_debug_assembly_bytes),
        .debug_cache_valid(old_debug_cache_valid),
        .debug_prefetch_offer(old_debug_prefetch_offer),
        .debug_prefetch_launch(old_debug_prefetch_launch),
        .debug_prefetch_use(old_debug_prefetch_use),
        .debug_tile_mode(old_debug_tile_mode),
        .debug_tile_preparing(old_debug_tile_preparing),
        .debug_prepare_bank(old_debug_prepare_bank),
        .debug_emit_bank(old_debug_emit_bank),
        .debug_bank_ready(old_debug_bank_ready),
        .debug_bank_owned(old_debug_bank_owned),
        .debug_emitter_state(old_debug_emitter_state),
        .debug_prepare_block(old_debug_prepare_block),
        .debug_bank_block(old_debug_bank_block),
        .debug_bank_epoch(old_debug_bank_epoch),
        .debug_tile_prepare_start(old_debug_tile_prepare_start),
        .debug_tile_publish(old_debug_tile_publish),
        .debug_tile_release(old_debug_tile_release),
        .debug_write_slot_valid(old_debug_write_slot_valid),
        .debug_assembler_full(old_debug_assembler_full),
        .debug_write_enqueue(old_debug_write_enqueue),
        .debug_head_valid(old_debug_head_valid),
        .verify_cache_data(old_verify_cache_data),
        .verify_positions(old_verify_positions),
        .verify_heads(old_verify_heads),
        .verify_head_positions(old_verify_head_positions),
        .verify_cursors(old_verify_cursors),
        .verify_read_word(old_verify_read_word),
        .verify_read_position(old_verify_read_position),
        .verify_read_address(old_verify_read_address),
        .verify_read_segment(old_verify_read_segment),
        .verify_read_band(old_verify_read_band),
        .verify_position_use(old_verify_position_use));
    observed_candidate candidate (
        .clk(clk),
        .reset(reset),
        .begin_valid(begin_valid),
        .begin_ready(begin_ready),
        .begin_blocks(begin_blocks),
        .begin_raw(begin_raw),
        .begin_serial_clear(begin_serial_clear),
        .begin_overlap(begin_overlap),
        .begin_prefetch(begin_prefetch),
        .begin_tile_overlap(begin_tile_overlap),
        .begin_count1(begin_count1),
        .begin_count2(begin_count2),
        .begin_count3(begin_count3),
        .begin_epoch(begin_epoch),
        .begin_prefix1(aligned1),.begin_prefix12(aligned12),.begin_prefix123(aligned123),
        .begin_threshold1(threshold1),.begin_threshold2(threshold2),.begin_threshold3(threshold3),
        .begin_capacity_upper(capacity_upper),.begin_capacity_lower(capacity_lower),.begin_capacity_wrap(capacity_wrap),
        .coef_valid(coef_valid),
        .coef_ready(coef_ready),
        .coef_band(coef_band),
        .coef_block(coef_block),
        .coef_index(coef_index),
        .coef_value(coef_value),
        .coef_epoch(coef_epoch),
        .band_end_valid(band_end_valid),
        .band_end_ready(band_end_ready),
        .band_end_band(band_end_band),
        .band_end_epoch(band_end_epoch),
        .seal_valid(seal_valid),
        .seal_ready(seal_ready),
        .seal_epoch(seal_epoch),
        .abort_valid(abort_valid),
        .abort_epoch(abort_epoch),
        .busy(busy),
        .sealed(sealed),
        .done(done),
        .error(error),
        .active_epoch(active_epoch),
        .used_bytes(used_bytes),
        .dense_valid(dense_valid),
        .dense_ready(dense_ready),
        .dense_block(dense_block),
        .dense_index(dense_index),
        .dense_value(dense_value),
        .dense_epoch(dense_epoch),
        .mem_req_valid(mem_req_valid),
        .mem_req_ready(mem_req_ready),
        .mem_req_write(mem_req_write),
        .mem_req_addr(mem_req_addr),
        .mem_req_data(mem_req_data),
        .mem_req_epoch(mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),
        .mem_rsp_ready(mem_rsp_ready),
        .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch),
        .mem_rsp_error(mem_rsp_error),
        .debug_state(debug_state),
        .debug_return_state(debug_return_state),
        .debug_outstanding(debug_outstanding),
        .debug_phase(debug_phase),
        .debug_assembly_bytes(debug_assembly_bytes),
        .debug_cache_valid(debug_cache_valid),
        .debug_prefetch_offer(debug_prefetch_offer),
        .debug_prefetch_launch(debug_prefetch_launch),
        .debug_prefetch_use(debug_prefetch_use),
        .debug_tile_mode(debug_tile_mode),
        .debug_tile_preparing(debug_tile_preparing),
        .debug_prepare_bank(debug_prepare_bank),
        .debug_emit_bank(debug_emit_bank),
        .debug_bank_ready(debug_bank_ready),
        .debug_bank_owned(debug_bank_owned),
        .debug_emitter_state(debug_emitter_state),
        .debug_prepare_block(debug_prepare_block),
        .debug_bank_block(debug_bank_block),
        .debug_bank_epoch(debug_bank_epoch),
        .debug_tile_prepare_start(debug_tile_prepare_start),
        .debug_tile_publish(debug_tile_publish),
        .debug_tile_release(debug_tile_release),
        .debug_write_slot_valid(debug_write_slot_valid),
        .debug_assembler_full(debug_assembler_full),
        .debug_write_enqueue(debug_write_enqueue),
        .debug_head_valid(debug_head_valid),
        .verify_cache_data(verify_cache_data),
        .verify_positions(verify_positions),
        .verify_heads(verify_heads),
        .verify_head_positions(verify_head_positions),
        .verify_cursors(verify_cursors),
        .verify_read_word(verify_read_word),
        .verify_read_position(verify_read_position),
        .verify_read_address(verify_read_address),
        .verify_read_segment(verify_read_segment),
        .verify_read_band(verify_read_band),
        .verify_position_use(verify_position_use));
    logic old_cursor_live,new_cursor_live;
    assign old_cursor_live=old_debug_state!=0 && old_debug_state!=23 && old_debug_state!=24 && old_debug_state!=25;
    assign new_cursor_live=debug_state!=0 && debug_state!=23 && debug_state!=24 && debug_state!=25;
    assign verify_cursor_equal=old_verify_cursors==verify_cursors;
    assign verify_cursor_owner_live=old_cursor_live || new_cursor_live;
    assign verify_reference_cursors=old_verify_cursors;
    // States and every noncursor observation remain equal before owner masking.
    always_ff @(posedge reference_clk)if(pair_enable)begin
        assert(old_debug_state==debug_state)else $fatal(1,"cursor state mismatch before owner scope");
        assert(old_verify_positions==verify_positions && old_verify_head_positions==verify_head_positions &&
            old_verify_read_position==verify_read_position)else $fatal(1,"cursor changed noncursor raw payload");
    end
    assign verify_preparing=candidate.preparing_begin;
    assign verify_prepare_cancel=candidate.cancel;
    always_ff @(posedge clk)if(!pair_enable && verify_preparing && !reset && !abort_valid && !mem_rsp_valid)
        assert(busy && !begin_ready && !coef_ready && !band_end_ready && !seal_ready &&
            !dense_valid && !mem_req_valid && !debug_outstanding && !sealed && !done && error==0)
            else $fatal(1,"paired scratch prepare interval leaked public work");
    // Additive raw-array equivalence includes every inactive word, not only
    // selected dense data. No original public/owner/raw check is removed.
    logic all_tile_words_equal;
    always_comb begin
        all_tile_words_equal=1;
        for(integer b=0;b<2;b=b+1)for(integer w=0;w<64;w=w+1)
            all_tile_words_equal=all_tile_words_equal && original.tile[b][w]==candidate.tile[b][w];
    end
    for(genvar b=0;b<2;b=b+1)begin: additional_tile_views
        for(genvar w=0;w<64;w=w+1)begin: word_view
            assign verify_tile_visible[(b*64+w)*16+:16]=candidate.tile[b][w];
            assign verify_tile_private[(b*64+w)*16+:16]=candidate.tile_payload[b][w];
        end
    end
    assign verify_tile_slot_valid=candidate.tile_pending_valid;
    assign verify_tile_slot_bank=candidate.tile_pending_bank;
    assign verify_tile_slot_index=candidate.tile_pending_index;
    assign verify_tile_slot_value=candidate.tile_pending_value;
    assign verify_tile_event_valid=candidate.tile_event_valid;
    initial begin verify_tile_events=0;verify_tile_commits=0;verify_tile_back_to_back=0;
        verify_tile_zero_events=0;verify_tile_data_events=0;end
    always_ff @(posedge clk)begin
        if(candidate.tile_event_valid)begin
            verify_tile_events<=verify_tile_events+1;
            if(candidate.tile_event_value==0)verify_tile_zero_events<=verify_tile_zero_events+1;
            else verify_tile_data_events<=verify_tile_data_events+1;
        end
        if(candidate.tile_pending_valid)verify_tile_commits<=verify_tile_commits+1;
        if(candidate.tile_pending_valid && candidate.tile_event_valid)
            verify_tile_back_to_back<=verify_tile_back_to_back+1;
        assert(verify_tile_events==verify_tile_commits+32'(candidate.tile_pending_valid))
            else $fatal(1,"finite tile slot conservation differs");
        if(candidate.tile_pending_valid)
            assert(candidate.tile[candidate.tile_pending_bank][candidate.tile_pending_index]==candidate.tile_pending_value)
                else $fatal(1,"newest visible tile write not forwarded");
    end
    assign mismatch=pair_enable && !(all_tile_words_equal && (old_begin_ready==begin_ready) &&
        (old_coef_ready==coef_ready) &&
        (old_band_end_ready==band_end_ready) &&
        (old_seal_ready==seal_ready) &&
        (old_busy==busy) &&
        (old_sealed==sealed) &&
        (old_done==done) &&
        (old_error==error) &&
        (old_active_epoch==active_epoch) &&
        (old_used_bytes==used_bytes) &&
        (old_dense_valid==dense_valid) &&
        (old_dense_block==dense_block) &&
        (old_dense_index==dense_index) &&
        (old_dense_value==dense_value) &&
        (old_dense_epoch==dense_epoch) &&
        (old_mem_req_valid==mem_req_valid) &&
        (old_mem_req_write==mem_req_write) &&
        (old_mem_req_addr==mem_req_addr) &&
        (old_mem_req_data==mem_req_data) &&
        (old_mem_req_epoch==mem_req_epoch) &&
        (old_mem_rsp_ready==mem_rsp_ready) &&
        (old_debug_state==debug_state) &&
        (old_debug_return_state==debug_return_state) &&
        (old_debug_outstanding==debug_outstanding) &&
        (old_debug_phase==debug_phase) &&
        (old_debug_assembly_bytes==debug_assembly_bytes) &&
        (old_debug_cache_valid==debug_cache_valid) &&
        (old_debug_prefetch_offer==debug_prefetch_offer) &&
        (old_debug_prefetch_launch==debug_prefetch_launch) &&
        (old_debug_prefetch_use==debug_prefetch_use) &&
        (old_debug_tile_mode==debug_tile_mode) &&
        (old_debug_tile_preparing==debug_tile_preparing) &&
        (old_debug_prepare_bank==debug_prepare_bank) &&
        (old_debug_emit_bank==debug_emit_bank) &&
        (old_debug_bank_ready==debug_bank_ready) &&
        (old_debug_bank_owned==debug_bank_owned) &&
        (old_debug_emitter_state==debug_emitter_state) &&
        (old_debug_prepare_block==debug_prepare_block) &&
        (old_debug_bank_block[0]==debug_bank_block[0]) &&
        (old_debug_bank_block[1]==debug_bank_block[1]) &&
        (old_debug_bank_epoch[0]==debug_bank_epoch[0]) &&
        (old_debug_bank_epoch[1]==debug_bank_epoch[1]) &&
        (old_debug_tile_prepare_start==debug_tile_prepare_start) &&
        (old_debug_tile_publish==debug_tile_publish) &&
        (old_debug_tile_release==debug_tile_release) &&
        (old_debug_write_slot_valid==debug_write_slot_valid) &&
        (old_debug_assembler_full==debug_assembler_full) &&
        (old_debug_write_enqueue==debug_write_enqueue) &&
        (old_debug_head_valid==debug_head_valid) &&
        (old_verify_cache_data==verify_cache_data) &&
        (old_verify_heads==verify_heads) &&
        (!(old_cursor_live || new_cursor_live) || old_verify_cursors==verify_cursors) &&
        (old_verify_read_word==verify_read_word) &&
        (old_verify_read_address==verify_read_address) &&
        (old_verify_read_segment==verify_read_segment) &&
        (old_verify_read_band==verify_read_band) &&
        (old_verify_position_use==verify_position_use) &&
        (!debug_cache_valid[0] || old_verify_positions[0+:304]==verify_positions[0+:304]) &&
        (!debug_cache_valid[1] || old_verify_positions[304+:304]==verify_positions[304+:304]) &&
        (!debug_cache_valid[2] || old_verify_positions[608+:304]==verify_positions[608+:304]) &&
        (!debug_cache_valid[3] || old_verify_positions[912+:304]==verify_positions[912+:304]) &&
        (!verify_position_use || old_verify_read_position==verify_read_position) &&
        (!(verify_position_use && verify_read_band==2'd1 && verify_cursors[0+:32]!=0) || old_verify_head_positions[0+:19]==verify_head_positions[0+:19]) &&
        (!(verify_position_use && verify_read_band==2'd2 && verify_cursors[32+:32]!=0) || old_verify_head_positions[19+:19]==verify_head_positions[19+:19]) &&
        (!(verify_position_use && verify_read_band==2'd3 && verify_cursors[64+:32]!=0) || old_verify_head_positions[38+:19]==verify_head_positions[38+:19]));
endmodule
