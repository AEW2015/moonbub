module raw_probe (
    input logic clk,
    input logic reset,
    input logic begin_valid,
    output logic begin_ready,
    input logic [16:0] begin_blocks,
    input logic begin_raw,
    input logic begin_serial_clear,
    input logic begin_overlap,
    input logic begin_prefetch,
    input logic begin_tile_overlap,
    input logic [31:0] begin_count1,
    input logic [31:0] begin_count2,
    input logic [31:0] begin_count3,
    input logic [31:0] begin_epoch,
    input logic [31:0] begin_prefix1,
    input logic [31:0] begin_prefix12,
    input logic [31:0] begin_prefix123,
    input logic [31:0] begin_threshold1,
    input logic [31:0] begin_threshold2,
    input logic [31:0] begin_threshold3,
    input logic [31:0] begin_capacity_upper,
    input logic [31:0] begin_capacity_lower,
    input logic begin_capacity_wrap,
    input logic coef_valid,
    output logic coef_ready,
    input logic band_end_valid,
    output logic band_end_ready,
    input logic [1:0] band_end_band,
    input logic [31:0] band_end_epoch,
    input logic seal_valid,
    output logic seal_ready,
    input logic [31:0] seal_epoch,
    input logic abort_valid,
    input logic [31:0] abort_epoch,
    output logic busy,
    output logic sealed,
    output logic done,
    output logic [3:0] error,
    output logic [31:0] owned_abort_epoch,
    output logic [31:0] active_epoch,
    output logic [18:0] used_bytes,
    output logic dense_valid,
    input logic dense_ready,
    output logic [15:0] dense_block,
    output logic [5:0] dense_index,
    output logic signed [15:0] dense_value,
    output logic [31:0] dense_epoch,
    output logic mem_req_valid,
    input logic mem_req_ready,
    output logic mem_req_write,
    output logic [17:0] mem_req_addr,
    output logic [127:0] mem_req_data,
    output logic [31:0] mem_req_epoch,
    input logic mem_rsp_valid,
    output logic mem_rsp_ready,
    input logic [127:0] mem_rsp_data,
    input logic [31:0] mem_rsp_epoch,
    input logic mem_rsp_error,
    output logic [4:0] debug_state,
    output logic [4:0] debug_return_state,
    output logic debug_outstanding,
    output logic [2:0] debug_phase,
    output logic [4:0] debug_assembly_bytes,
    output logic [3:0] debug_cache_valid,
    output logic debug_prefetch_offer,
    output logic debug_prefetch_launch,
    output logic debug_prefetch_use,
    output logic debug_tile_mode,
    output logic debug_tile_preparing,
    output logic debug_prepare_bank,
    output logic debug_emit_bank,
    output logic [1:0] debug_bank_ready,
    output logic [1:0] debug_bank_owned,
    output logic [1:0] debug_emitter_state,
    output logic [15:0] debug_prepare_block,
    output logic [15:0] debug_bank_block [0:1],
    output logic [31:0] debug_bank_epoch [0:1],
    output logic [31:0] debug_scalar_epoch,
    output logic [15:0] debug_scalar_block,
    output logic debug_tile_prepare_start,
    output logic debug_tile_publish,
    output logic debug_tile_release,
    output logic debug_write_slot_valid,
    output logic debug_assembler_full,
    output logic debug_write_enqueue,
    output logic [2:0] debug_head_valid,
    input logic coef_select_raw,
    input logic [31:0] coef_raw_epoch,
    input logic [15:0] coef_raw_block,
    input logic [5:0] coef_raw_index,
    input logic signed [15:0] coef_raw_value,
    input logic [1:0] coef_raw_band,
    input logic [31:0] coef_context_epoch,
    input logic [15:0] coef_context_block,
    input logic [5:0] coef_context_index,
    input logic signed [15:0] coef_context_value,
    input logic [1:0] coef_context_band,
    input logic  alg_raw_mode,
    input logic [31:0] alg_active_epoch,
    input logic [16:0] alg_blocks,
    input logic [31:0] alg_written,
    input logic [31:0] alg_previous_position,
    input logic  alg_previous_valid,
    input logic [63:0] alg_rank_threshold_mask,
    input logic [2:0] alg_phase,
    input logic [31:0] alg_count0,
    input logic [31:0] alg_count1,
    input logic [31:0] alg_count2,
    input logic [31:0] alg_count3,
    output logic [7:0] alg_reference_phase_bad,
    output logic [7:0] alg_candidate_phase_bad,
    output logic [7:0] alg_literal_phase_bad,
    output logic  alg_reference_epoch_bad,
    output logic  alg_candidate_epoch_bad,
    output logic  alg_reference_selected_bad,
    output logic  alg_candidate_selected_bad,
    output logic  alg_block_limit_high,
    output logic pair_equal,
    output logic pair_predicate_equal
);
    logic b_begin_ready;
    logic b_coef_ready;
    logic b_band_end_ready;
    logic b_seal_ready;
    logic b_busy;
    logic b_sealed;
    logic b_done;
    logic [3:0] b_error;
    logic [31:0] b_owned_abort_epoch;
    logic [31:0] b_active_epoch;
    logic [18:0] b_used_bytes;
    logic b_dense_valid;
    logic [15:0] b_dense_block;
    logic [5:0] b_dense_index;
    logic signed [15:0] b_dense_value;
    logic [31:0] b_dense_epoch;
    logic b_mem_req_valid;
    logic b_mem_req_write;
    logic [17:0] b_mem_req_addr;
    logic [127:0] b_mem_req_data;
    logic [31:0] b_mem_req_epoch;
    logic b_mem_rsp_ready;
    logic [4:0] b_debug_state;
    logic [4:0] b_debug_return_state;
    logic b_debug_outstanding;
    logic [2:0] b_debug_phase;
    logic [4:0] b_debug_assembly_bytes;
    logic [3:0] b_debug_cache_valid;
    logic b_debug_prefetch_offer;
    logic b_debug_prefetch_launch;
    logic b_debug_prefetch_use;
    logic b_debug_tile_mode;
    logic b_debug_tile_preparing;
    logic b_debug_prepare_bank;
    logic b_debug_emit_bank;
    logic [1:0] b_debug_bank_ready;
    logic [1:0] b_debug_bank_owned;
    logic [1:0] b_debug_emitter_state;
    logic [15:0] b_debug_prepare_block;
    logic [15:0] b_debug_bank_block [0:1];
    logic [31:0] b_debug_bank_epoch [0:1];
    logic [31:0] b_debug_scalar_epoch;
    logic [15:0] b_debug_scalar_block;
    logic b_debug_tile_prepare_start;
    logic b_debug_tile_publish;
    logic b_debug_tile_release;
    logic b_debug_write_slot_valid;
    logic b_debug_assembler_full;
    logic b_debug_write_enqueue;
    logic [2:0] b_debug_head_valid;
    wire [31:0] coef_epoch=coef_select_raw ? coef_raw_epoch : coef_context_epoch;
    wire [15:0] coef_block=coef_select_raw ? coef_raw_block : coef_context_block;
    wire [5:0] coef_index=coef_select_raw ? coef_raw_index : coef_context_index;
    wire signed [15:0] coef_value=coef_select_raw ? coef_raw_value : coef_context_value;
    wire [1:0] coef_band=coef_select_raw ? coef_raw_band : coef_context_band;
    v128_scratch_baseline baseline (
        .clk(clk),
        .reset(reset),
        .begin_valid(begin_valid),
        .begin_ready(b_begin_ready),
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
        .begin_prefix1(begin_prefix1),
        .begin_prefix12(begin_prefix12),
        .begin_prefix123(begin_prefix123),
        .begin_threshold1(begin_threshold1),
        .begin_threshold2(begin_threshold2),
        .begin_threshold3(begin_threshold3),
        .begin_capacity_upper(begin_capacity_upper),
        .begin_capacity_lower(begin_capacity_lower),
        .begin_capacity_wrap(begin_capacity_wrap),
        .coef_valid(coef_valid),
        .coef_ready(b_coef_ready),
        .coef_band(coef_band),
        .coef_block(coef_block),
        .coef_index(coef_index),
        .coef_value(coef_value),
        .coef_epoch(coef_epoch),
        .band_end_valid(band_end_valid),
        .band_end_ready(b_band_end_ready),
        .band_end_band(band_end_band),
        .band_end_epoch(band_end_epoch),
        .seal_valid(seal_valid),
        .seal_ready(b_seal_ready),
        .seal_epoch(seal_epoch),
        .abort_valid(abort_valid),
        .abort_epoch(abort_epoch),
        .busy(b_busy),
        .sealed(b_sealed),
        .done(b_done),
        .error(b_error),
        .owned_abort_epoch(b_owned_abort_epoch),
        .active_epoch(b_active_epoch),
        .used_bytes(b_used_bytes),
        .dense_valid(b_dense_valid),
        .dense_ready(dense_ready),
        .dense_block(b_dense_block),
        .dense_index(b_dense_index),
        .dense_value(b_dense_value),
        .dense_epoch(b_dense_epoch),
        .mem_req_valid(b_mem_req_valid),
        .mem_req_ready(mem_req_ready),
        .mem_req_write(b_mem_req_write),
        .mem_req_addr(b_mem_req_addr),
        .mem_req_data(b_mem_req_data),
        .mem_req_epoch(b_mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),
        .mem_rsp_ready(b_mem_rsp_ready),
        .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch),
        .mem_rsp_error(mem_rsp_error),
        .debug_state(b_debug_state),
        .debug_return_state(b_debug_return_state),
        .debug_outstanding(b_debug_outstanding),
        .debug_phase(b_debug_phase),
        .debug_assembly_bytes(b_debug_assembly_bytes),
        .debug_cache_valid(b_debug_cache_valid),
        .debug_prefetch_offer(b_debug_prefetch_offer),
        .debug_prefetch_launch(b_debug_prefetch_launch),
        .debug_prefetch_use(b_debug_prefetch_use),
        .debug_tile_mode(b_debug_tile_mode),
        .debug_tile_preparing(b_debug_tile_preparing),
        .debug_prepare_bank(b_debug_prepare_bank),
        .debug_emit_bank(b_debug_emit_bank),
        .debug_bank_ready(b_debug_bank_ready),
        .debug_bank_owned(b_debug_bank_owned),
        .debug_emitter_state(b_debug_emitter_state),
        .debug_prepare_block(b_debug_prepare_block),
        .debug_bank_block(b_debug_bank_block),
        .debug_bank_epoch(b_debug_bank_epoch),
        .debug_scalar_epoch(b_debug_scalar_epoch),
        .debug_scalar_block(b_debug_scalar_block),
        .debug_tile_prepare_start(b_debug_tile_prepare_start),
        .debug_tile_publish(b_debug_tile_publish),
        .debug_tile_release(b_debug_tile_release),
        .debug_write_slot_valid(b_debug_write_slot_valid),
        .debug_assembler_full(b_debug_assembler_full),
        .debug_write_enqueue(b_debug_write_enqueue),
        .debug_head_valid(b_debug_head_valid)
    );
    packed_scratch_v91g2 candidate (
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
        .begin_prefix1(begin_prefix1),
        .begin_prefix12(begin_prefix12),
        .begin_prefix123(begin_prefix123),
        .begin_threshold1(begin_threshold1),
        .begin_threshold2(begin_threshold2),
        .begin_threshold3(begin_threshold3),
        .begin_capacity_upper(begin_capacity_upper),
        .begin_capacity_lower(begin_capacity_lower),
        .begin_capacity_wrap(begin_capacity_wrap),
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
        .owned_abort_epoch(owned_abort_epoch),
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
        .debug_scalar_epoch(debug_scalar_epoch),
        .debug_scalar_block(debug_scalar_block),
        .debug_tile_prepare_start(debug_tile_prepare_start),
        .debug_tile_publish(debug_tile_publish),
        .debug_tile_release(debug_tile_release),
        .debug_write_slot_valid(debug_write_slot_valid),
        .debug_assembler_full(debug_assembler_full),
        .debug_write_enqueue(debug_write_enqueue),
        .debug_head_valid(debug_head_valid),
        .coef_select_raw(coef_select_raw),
        .coef_raw_epoch(coef_raw_epoch),
        .coef_raw_block(coef_raw_block),
        .coef_raw_index(coef_raw_index),
        .coef_raw_value(coef_raw_value),
        .coef_raw_band(coef_raw_band),
        .coef_context_epoch(coef_context_epoch),
        .coef_context_block(coef_context_block),
        .coef_context_index(coef_context_index),
        .coef_context_value(coef_context_value),
        .coef_context_band(coef_context_band)
    );
    always_comb begin
        pair_equal=1;
        pair_equal=pair_equal && b_begin_ready==begin_ready;
        pair_equal=pair_equal && b_coef_ready==coef_ready;
        pair_equal=pair_equal && b_band_end_ready==band_end_ready;
        pair_equal=pair_equal && b_seal_ready==seal_ready;
        pair_equal=pair_equal && b_busy==busy;
        pair_equal=pair_equal && b_sealed==sealed;
        pair_equal=pair_equal && b_done==done;
        pair_equal=pair_equal && b_error==error;
        pair_equal=pair_equal && b_owned_abort_epoch==owned_abort_epoch;
        pair_equal=pair_equal && b_active_epoch==active_epoch;
        pair_equal=pair_equal && b_used_bytes==used_bytes;
        pair_equal=pair_equal && b_dense_valid==dense_valid;
        pair_equal=pair_equal && b_dense_block==dense_block;
        pair_equal=pair_equal && b_dense_index==dense_index;
        pair_equal=pair_equal && b_dense_value==dense_value;
        pair_equal=pair_equal && b_dense_epoch==dense_epoch;
        pair_equal=pair_equal && b_mem_req_valid==mem_req_valid;
        pair_equal=pair_equal && b_mem_req_write==mem_req_write;
        pair_equal=pair_equal && b_mem_req_addr==mem_req_addr;
        pair_equal=pair_equal && b_mem_req_data==mem_req_data;
        pair_equal=pair_equal && b_mem_req_epoch==mem_req_epoch;
        pair_equal=pair_equal && b_mem_rsp_ready==mem_rsp_ready;
        pair_equal=pair_equal && b_debug_state==debug_state;
        pair_equal=pair_equal && b_debug_return_state==debug_return_state;
        pair_equal=pair_equal && b_debug_outstanding==debug_outstanding;
        pair_equal=pair_equal && b_debug_phase==debug_phase;
        pair_equal=pair_equal && b_debug_assembly_bytes==debug_assembly_bytes;
        pair_equal=pair_equal && b_debug_cache_valid==debug_cache_valid;
        pair_equal=pair_equal && b_debug_prefetch_offer==debug_prefetch_offer;
        pair_equal=pair_equal && b_debug_prefetch_launch==debug_prefetch_launch;
        pair_equal=pair_equal && b_debug_prefetch_use==debug_prefetch_use;
        pair_equal=pair_equal && b_debug_tile_mode==debug_tile_mode;
        pair_equal=pair_equal && b_debug_tile_preparing==debug_tile_preparing;
        pair_equal=pair_equal && b_debug_prepare_bank==debug_prepare_bank;
        pair_equal=pair_equal && b_debug_emit_bank==debug_emit_bank;
        pair_equal=pair_equal && b_debug_bank_ready==debug_bank_ready;
        pair_equal=pair_equal && b_debug_bank_owned==debug_bank_owned;
        pair_equal=pair_equal && b_debug_emitter_state==debug_emitter_state;
        pair_equal=pair_equal && b_debug_prepare_block==debug_prepare_block;
        for(integer i=0;i<2;i=i+1)pair_equal=pair_equal && b_debug_bank_block[i]==debug_bank_block[i];
        for(integer i=0;i<2;i=i+1)pair_equal=pair_equal && b_debug_bank_epoch[i]==debug_bank_epoch[i];
        pair_equal=pair_equal && b_debug_scalar_epoch==debug_scalar_epoch;
        pair_equal=pair_equal && b_debug_scalar_block==debug_scalar_block;
        pair_equal=pair_equal && b_debug_tile_prepare_start==debug_tile_prepare_start;
        pair_equal=pair_equal && b_debug_tile_publish==debug_tile_publish;
        pair_equal=pair_equal && b_debug_tile_release==debug_tile_release;
        pair_equal=pair_equal && b_debug_write_slot_valid==debug_write_slot_valid;
        pair_equal=pair_equal && b_debug_assembler_full==debug_assembler_full;
        pair_equal=pair_equal && b_debug_write_enqueue==debug_write_enqueue;
        pair_equal=pair_equal && b_debug_head_valid==debug_head_valid;
        pair_predicate_equal=(baseline.input_bad==candidate.input_bad) && (baseline.phase_input_bad==candidate.phase_input_bad) && ((coef_epoch!=baseline.active_epoch)==candidate.input_epoch_bad);
    end
    logic [31:0] alg_counts [0:3];
    assign alg_counts[0]=alg_count0;
    assign alg_counts[1]=alg_count1;
    assign alg_counts[2]=alg_count2;
    assign alg_counts[3]=alg_count3;
    v128_raw_scalar_probe algebra (
        .coef_select_raw(coef_select_raw),
        .coef_raw_epoch(coef_raw_epoch),
        .coef_raw_block(coef_raw_block),
        .coef_raw_index(coef_raw_index),
        .coef_raw_value(coef_raw_value),
        .coef_raw_band(coef_raw_band),
        .coef_context_epoch(coef_context_epoch),
        .coef_context_block(coef_context_block),
        .coef_context_index(coef_context_index),
        .coef_context_value(coef_context_value),
        .coef_context_band(coef_context_band),
        .raw_mode(alg_raw_mode),
        .active_epoch(alg_active_epoch),
        .blocks(alg_blocks),
        .written(alg_written),
        .previous_position(alg_previous_position),
        .previous_valid(alg_previous_valid),
        .rank_threshold_mask(alg_rank_threshold_mask),
        .phase(alg_phase),
        .counts(alg_counts),
        .reference_phase_bad(alg_reference_phase_bad),
        .candidate_phase_bad(alg_candidate_phase_bad),
        .literal_phase_bad(alg_literal_phase_bad),
        .reference_epoch_bad(alg_reference_epoch_bad),
        .candidate_epoch_bad(alg_candidate_epoch_bad),
        .reference_selected_bad(alg_reference_selected_bad),
        .candidate_selected_bad(alg_candidate_selected_bad),
        .block_limit_high(alg_block_limit_high)
    );
endmodule
