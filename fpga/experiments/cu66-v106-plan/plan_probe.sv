module plan_probe (
    input logic clk, reset,
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
    output logic mismatch,
    output logic [31:0] verify_plan1,verify_plan2,verify_plan3,verify_used
);
    logic  original_begin_ready;
    logic  original_coef_ready;
    logic  original_band_end_ready;
    logic  original_seal_ready;
    logic  original_busy;
    logic  original_sealed;
    logic  original_done;
    logic [3:0] original_error;
    logic [31:0] original_active_epoch;
    logic [18:0] original_used_bytes;
    logic  original_dense_valid;
    logic [15:0] original_dense_block;
    logic [5:0] original_dense_index;
    logic signed [15:0] original_dense_value;
    logic [31:0] original_dense_epoch;
    logic  original_mem_req_valid;
    logic  original_mem_req_write;
    logic [17:0] original_mem_req_addr;
    logic [127:0] original_mem_req_data;
    logic [31:0] original_mem_req_epoch;
    logic  original_mem_rsp_ready;
    logic [4:0] original_debug_state;
    logic [4:0] original_debug_return_state;
    logic  original_debug_outstanding;
    logic [2:0] original_debug_phase;
    logic [4:0] original_debug_assembly_bytes;
    logic [3:0] original_debug_cache_valid;
    logic  original_debug_prefetch_offer;
    logic  original_debug_prefetch_launch;
    logic  original_debug_prefetch_use;
    logic  original_debug_tile_mode;
    logic  original_debug_tile_preparing;
    logic  original_debug_prepare_bank;
    logic  original_debug_emit_bank;
    logic [1:0] original_debug_bank_ready;
    logic [1:0] original_debug_bank_owned;
    logic [1:0] original_debug_emitter_state;
    logic [15:0] original_debug_prepare_block;
    logic [15:0] original_debug_bank_block[0:1];
    logic [31:0] original_debug_bank_epoch[0:1];
    logic  original_debug_tile_prepare_start;
    logic  original_debug_tile_publish;
    logic  original_debug_tile_release;
    logic  original_debug_write_slot_valid;
    logic  original_debug_assembler_full;
    logic  original_debug_write_enqueue;
    logic [2:0] original_debug_head_valid;
    logic [31:0] original_verify_plan1;
    logic [31:0] original_verify_plan2;
    logic [31:0] original_verify_plan3;
    logic [31:0] original_verify_used;
    plan_original original (
        .clk(clk),
        .reset(reset),
        .begin_valid(begin_valid),
        .begin_ready(original_begin_ready),
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
        .coef_valid(coef_valid),
        .coef_ready(original_coef_ready),
        .coef_band(coef_band),
        .coef_block(coef_block),
        .coef_index(coef_index),
        .coef_value(coef_value),
        .coef_epoch(coef_epoch),
        .band_end_valid(band_end_valid),
        .band_end_ready(original_band_end_ready),
        .band_end_band(band_end_band),
        .band_end_epoch(band_end_epoch),
        .seal_valid(seal_valid),
        .seal_ready(original_seal_ready),
        .seal_epoch(seal_epoch),
        .abort_valid(abort_valid),
        .abort_epoch(abort_epoch),
        .busy(original_busy),
        .sealed(original_sealed),
        .done(original_done),
        .error(original_error),
        .active_epoch(original_active_epoch),
        .used_bytes(original_used_bytes),
        .dense_valid(original_dense_valid),
        .dense_ready(dense_ready),
        .dense_block(original_dense_block),
        .dense_index(original_dense_index),
        .dense_value(original_dense_value),
        .dense_epoch(original_dense_epoch),
        .mem_req_valid(original_mem_req_valid),
        .mem_req_ready(mem_req_ready),
        .mem_req_write(original_mem_req_write),
        .mem_req_addr(original_mem_req_addr),
        .mem_req_data(original_mem_req_data),
        .mem_req_epoch(original_mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid),
        .mem_rsp_ready(original_mem_rsp_ready),
        .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch),
        .mem_rsp_error(mem_rsp_error),
        .debug_state(original_debug_state),
        .debug_return_state(original_debug_return_state),
        .debug_outstanding(original_debug_outstanding),
        .debug_phase(original_debug_phase),
        .debug_assembly_bytes(original_debug_assembly_bytes),
        .debug_cache_valid(original_debug_cache_valid),
        .debug_prefetch_offer(original_debug_prefetch_offer),
        .debug_prefetch_launch(original_debug_prefetch_launch),
        .debug_prefetch_use(original_debug_prefetch_use),
        .debug_tile_mode(original_debug_tile_mode),
        .debug_tile_preparing(original_debug_tile_preparing),
        .debug_prepare_bank(original_debug_prepare_bank),
        .debug_emit_bank(original_debug_emit_bank),
        .debug_bank_ready(original_debug_bank_ready),
        .debug_bank_owned(original_debug_bank_owned),
        .debug_emitter_state(original_debug_emitter_state),
        .debug_prepare_block(original_debug_prepare_block),
        .debug_bank_block(original_debug_bank_block),
        .debug_bank_epoch(original_debug_bank_epoch),
        .debug_tile_prepare_start(original_debug_tile_prepare_start),
        .debug_tile_publish(original_debug_tile_publish),
        .debug_tile_release(original_debug_tile_release),
        .debug_write_slot_valid(original_debug_write_slot_valid),
        .debug_assembler_full(original_debug_assembler_full),
        .debug_write_enqueue(original_debug_write_enqueue),
        .debug_head_valid(original_debug_head_valid),
        .verify_plan1(original_verify_plan1),
        .verify_plan2(original_verify_plan2),
        .verify_plan3(original_verify_plan3),
        .verify_used(original_verify_used));
    plan_candidate candidate (
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
        .verify_plan1(verify_plan1),
        .verify_plan2(verify_plan2),
        .verify_plan3(verify_plan3),
        .verify_used(verify_used));
    always_comb begin
        mismatch=0;
        mismatch=mismatch || begin_ready!=original_begin_ready;
        mismatch=mismatch || coef_ready!=original_coef_ready;
        mismatch=mismatch || band_end_ready!=original_band_end_ready;
        mismatch=mismatch || seal_ready!=original_seal_ready;
        mismatch=mismatch || busy!=original_busy;
        mismatch=mismatch || sealed!=original_sealed;
        mismatch=mismatch || done!=original_done;
        mismatch=mismatch || error!=original_error;
        mismatch=mismatch || active_epoch!=original_active_epoch;
        mismatch=mismatch || used_bytes!=original_used_bytes;
        mismatch=mismatch || dense_valid!=original_dense_valid;
        mismatch=mismatch || dense_block!=original_dense_block;
        mismatch=mismatch || dense_index!=original_dense_index;
        mismatch=mismatch || dense_value!=original_dense_value;
        mismatch=mismatch || dense_epoch!=original_dense_epoch;
        mismatch=mismatch || mem_req_valid!=original_mem_req_valid;
        mismatch=mismatch || mem_req_write!=original_mem_req_write;
        mismatch=mismatch || mem_req_addr!=original_mem_req_addr;
        mismatch=mismatch || mem_req_data!=original_mem_req_data;
        mismatch=mismatch || mem_req_epoch!=original_mem_req_epoch;
        mismatch=mismatch || mem_rsp_ready!=original_mem_rsp_ready;
        mismatch=mismatch || debug_state!=original_debug_state;
        mismatch=mismatch || debug_return_state!=original_debug_return_state;
        mismatch=mismatch || debug_outstanding!=original_debug_outstanding;
        mismatch=mismatch || debug_phase!=original_debug_phase;
        mismatch=mismatch || debug_assembly_bytes!=original_debug_assembly_bytes;
        mismatch=mismatch || debug_cache_valid!=original_debug_cache_valid;
        mismatch=mismatch || debug_prefetch_offer!=original_debug_prefetch_offer;
        mismatch=mismatch || debug_prefetch_launch!=original_debug_prefetch_launch;
        mismatch=mismatch || debug_prefetch_use!=original_debug_prefetch_use;
        mismatch=mismatch || debug_tile_mode!=original_debug_tile_mode;
        mismatch=mismatch || debug_tile_preparing!=original_debug_tile_preparing;
        mismatch=mismatch || debug_prepare_bank!=original_debug_prepare_bank;
        mismatch=mismatch || debug_emit_bank!=original_debug_emit_bank;
        mismatch=mismatch || debug_bank_ready!=original_debug_bank_ready;
        mismatch=mismatch || debug_bank_owned!=original_debug_bank_owned;
        mismatch=mismatch || debug_emitter_state!=original_debug_emitter_state;
        mismatch=mismatch || debug_prepare_block!=original_debug_prepare_block;
        mismatch=mismatch || debug_bank_block[0]!=original_debug_bank_block[0];
        mismatch=mismatch || debug_bank_block[1]!=original_debug_bank_block[1];
        mismatch=mismatch || debug_bank_epoch[0]!=original_debug_bank_epoch[0];
        mismatch=mismatch || debug_bank_epoch[1]!=original_debug_bank_epoch[1];
        mismatch=mismatch || debug_tile_prepare_start!=original_debug_tile_prepare_start;
        mismatch=mismatch || debug_tile_publish!=original_debug_tile_publish;
        mismatch=mismatch || debug_tile_release!=original_debug_tile_release;
        mismatch=mismatch || debug_write_slot_valid!=original_debug_write_slot_valid;
        mismatch=mismatch || debug_assembler_full!=original_debug_assembler_full;
        mismatch=mismatch || debug_write_enqueue!=original_debug_write_enqueue;
        mismatch=mismatch || debug_head_valid!=original_debug_head_valid;
        mismatch=mismatch || verify_plan1!=original_verify_plan1;
        mismatch=mismatch || verify_plan2!=original_verify_plan2;
        mismatch=mismatch || verify_plan3!=original_verify_plan3;
        mismatch=mismatch || verify_used!=original_verify_used;
    end
endmodule
