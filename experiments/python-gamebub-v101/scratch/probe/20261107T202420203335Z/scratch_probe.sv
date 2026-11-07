// V91c byte-identical packed scratch, sequential functional implementation.
module scratch_probe (
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
    output logic [2:0] debug_head_valid
, output logic probe_outputs_equal, probe_internal_equal);
logic  old_begin_ready;
logic  old_coef_ready;
logic  old_band_end_ready;
logic  old_seal_ready;
logic  old_busy;
logic  old_sealed;
logic  old_done;
logic [3:0]  old_error;
logic [31:0]  old_active_epoch;
logic [18:0]  old_used_bytes;
logic  old_dense_valid;
logic [15:0]  old_dense_block;
logic [5:0]  old_dense_index;
logic signed [15:0]  old_dense_value;
logic [31:0]  old_dense_epoch;
logic  old_mem_req_valid;
logic  old_mem_req_write;
logic [17:0]  old_mem_req_addr;
logic [127:0]  old_mem_req_data;
logic [31:0]  old_mem_req_epoch;
logic  old_mem_rsp_ready;
logic [4:0]  old_debug_state;
logic [4:0]  old_debug_return_state;
logic  old_debug_outstanding;
logic [2:0]  old_debug_phase;
logic [4:0]  old_debug_assembly_bytes;
logic [3:0]  old_debug_cache_valid;
logic  old_debug_prefetch_offer;
logic  old_debug_prefetch_launch;
logic  old_debug_prefetch_use;
logic  old_debug_tile_mode;
logic  old_debug_tile_preparing;
logic  old_debug_prepare_bank;
logic  old_debug_emit_bank;
logic [1:0]  old_debug_bank_ready;
logic [1:0]  old_debug_bank_owned;
logic [1:0]  old_debug_emitter_state;
logic [15:0]  old_debug_prepare_block;
logic [15:0]  old_debug_bank_block[0:1];
logic [31:0]  old_debug_bank_epoch[0:1];
logic  old_debug_tile_prepare_start;
logic  old_debug_tile_publish;
logic  old_debug_tile_release;
logic  old_debug_write_slot_valid;
logic  old_debug_assembler_full;
logic  old_debug_write_enqueue;
logic [2:0]  old_debug_head_valid;
scratch_original old_dut(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_ready(old_begin_ready),.begin_blocks(begin_blocks),.begin_raw(begin_raw),.begin_serial_clear(begin_serial_clear),.begin_overlap(begin_overlap),.begin_prefetch(begin_prefetch),.begin_tile_overlap(begin_tile_overlap),.begin_count1(begin_count1),.begin_count2(begin_count2),.begin_count3(begin_count3),.begin_epoch(begin_epoch),.coef_valid(coef_valid),.coef_ready(old_coef_ready),.coef_band(coef_band),.coef_block(coef_block),.coef_index(coef_index),.coef_value(coef_value),.coef_epoch(coef_epoch),.band_end_valid(band_end_valid),.band_end_ready(old_band_end_ready),.band_end_band(band_end_band),.band_end_epoch(band_end_epoch),.seal_valid(seal_valid),.seal_ready(old_seal_ready),.seal_epoch(seal_epoch),.abort_valid(abort_valid),.abort_epoch(abort_epoch),.busy(old_busy),.sealed(old_sealed),.done(old_done),.error(old_error),.active_epoch(old_active_epoch),.used_bytes(old_used_bytes),.dense_valid(old_dense_valid),.dense_ready(dense_ready),.dense_block(old_dense_block),.dense_index(old_dense_index),.dense_value(old_dense_value),.dense_epoch(old_dense_epoch),.mem_req_valid(old_mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(old_mem_req_write),.mem_req_addr(old_mem_req_addr),.mem_req_data(old_mem_req_data),.mem_req_epoch(old_mem_req_epoch),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(old_mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_error(mem_rsp_error),.debug_state(old_debug_state),.debug_return_state(old_debug_return_state),.debug_outstanding(old_debug_outstanding),.debug_phase(old_debug_phase),.debug_assembly_bytes(old_debug_assembly_bytes),.debug_cache_valid(old_debug_cache_valid),.debug_prefetch_offer(old_debug_prefetch_offer),.debug_prefetch_launch(old_debug_prefetch_launch),.debug_prefetch_use(old_debug_prefetch_use),.debug_tile_mode(old_debug_tile_mode),.debug_tile_preparing(old_debug_tile_preparing),.debug_prepare_bank(old_debug_prepare_bank),.debug_emit_bank(old_debug_emit_bank),.debug_bank_ready(old_debug_bank_ready),.debug_bank_owned(old_debug_bank_owned),.debug_emitter_state(old_debug_emitter_state),.debug_prepare_block(old_debug_prepare_block),.debug_bank_block(old_debug_bank_block),.debug_bank_epoch(old_debug_bank_epoch),.debug_tile_prepare_start(old_debug_tile_prepare_start),.debug_tile_publish(old_debug_tile_publish),.debug_tile_release(old_debug_tile_release),.debug_write_slot_valid(old_debug_write_slot_valid),.debug_assembler_full(old_debug_assembler_full),.debug_write_enqueue(old_debug_write_enqueue),.debug_head_valid(old_debug_head_valid));
scratch_candidate new_dut(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_ready(begin_ready),.begin_blocks(begin_blocks),.begin_raw(begin_raw),.begin_serial_clear(begin_serial_clear),.begin_overlap(begin_overlap),.begin_prefetch(begin_prefetch),.begin_tile_overlap(begin_tile_overlap),.begin_count1(begin_count1),.begin_count2(begin_count2),.begin_count3(begin_count3),.begin_epoch(begin_epoch),.coef_valid(coef_valid),.coef_ready(coef_ready),.coef_band(coef_band),.coef_block(coef_block),.coef_index(coef_index),.coef_value(coef_value),.coef_epoch(coef_epoch),.band_end_valid(band_end_valid),.band_end_ready(band_end_ready),.band_end_band(band_end_band),.band_end_epoch(band_end_epoch),.seal_valid(seal_valid),.seal_ready(seal_ready),.seal_epoch(seal_epoch),.abort_valid(abort_valid),.abort_epoch(abort_epoch),.busy(busy),.sealed(sealed),.done(done),.error(error),.active_epoch(active_epoch),.used_bytes(used_bytes),.dense_valid(dense_valid),.dense_ready(dense_ready),.dense_block(dense_block),.dense_index(dense_index),.dense_value(dense_value),.dense_epoch(dense_epoch),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),.mem_req_addr(mem_req_addr),.mem_req_data(mem_req_data),.mem_req_epoch(mem_req_epoch),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_error(mem_rsp_error),.debug_state(debug_state),.debug_return_state(debug_return_state),.debug_outstanding(debug_outstanding),.debug_phase(debug_phase),.debug_assembly_bytes(debug_assembly_bytes),.debug_cache_valid(debug_cache_valid),.debug_prefetch_offer(debug_prefetch_offer),.debug_prefetch_launch(debug_prefetch_launch),.debug_prefetch_use(debug_prefetch_use),.debug_tile_mode(debug_tile_mode),.debug_tile_preparing(debug_tile_preparing),.debug_prepare_bank(debug_prepare_bank),.debug_emit_bank(debug_emit_bank),.debug_bank_ready(debug_bank_ready),.debug_bank_owned(debug_bank_owned),.debug_emitter_state(debug_emitter_state),.debug_prepare_block(debug_prepare_block),.debug_bank_block(debug_bank_block),.debug_bank_epoch(debug_bank_epoch),.debug_tile_prepare_start(debug_tile_prepare_start),.debug_tile_publish(debug_tile_publish),.debug_tile_release(debug_tile_release),.debug_write_slot_valid(debug_write_slot_valid),.debug_assembler_full(debug_assembler_full),.debug_write_enqueue(debug_write_enqueue),.debug_head_valid(debug_head_valid));
assign probe_outputs_equal = (old_begin_ready == begin_ready) && (old_coef_ready == coef_ready) && (old_band_end_ready == band_end_ready) && (old_seal_ready == seal_ready) && (old_busy == busy) && (old_sealed == sealed) && (old_done == done) && (old_error == error) && (old_active_epoch == active_epoch) && (old_used_bytes == used_bytes) && (old_dense_valid == dense_valid) && (old_dense_block == dense_block) && (old_dense_index == dense_index) && (old_dense_value == dense_value) && (old_dense_epoch == dense_epoch) && (old_mem_req_valid == mem_req_valid) && (old_mem_req_write == mem_req_write) && (old_mem_req_addr == mem_req_addr) && (old_mem_req_data == mem_req_data) && (old_mem_req_epoch == mem_req_epoch) && (old_mem_rsp_ready == mem_rsp_ready) && (old_debug_state == debug_state) && (old_debug_return_state == debug_return_state) && (old_debug_outstanding == debug_outstanding) && (old_debug_phase == debug_phase) && (old_debug_assembly_bytes == debug_assembly_bytes) && (old_debug_cache_valid == debug_cache_valid) && (old_debug_prefetch_offer == debug_prefetch_offer) && (old_debug_prefetch_launch == debug_prefetch_launch) && (old_debug_prefetch_use == debug_prefetch_use) && (old_debug_tile_mode == debug_tile_mode) && (old_debug_tile_preparing == debug_tile_preparing) && (old_debug_prepare_bank == debug_prepare_bank) && (old_debug_emit_bank == debug_emit_bank) && (old_debug_bank_ready == debug_bank_ready) && (old_debug_bank_owned == debug_bank_owned) && (old_debug_emitter_state == debug_emitter_state) && (old_debug_prepare_block == debug_prepare_block) && (old_debug_bank_block == debug_bank_block) && (old_debug_bank_epoch == debug_bank_epoch) && (old_debug_tile_prepare_start == debug_tile_prepare_start) && (old_debug_tile_publish == debug_tile_publish) && (old_debug_tile_release == debug_tile_release) && (old_debug_write_slot_valid == debug_write_slot_valid) && (old_debug_assembler_full == debug_assembler_full) && (old_debug_write_enqueue == debug_write_enqueue) && (old_debug_head_valid == debug_head_valid);
assign probe_internal_equal = (old_dut.candidate_valid == new_dut.candidate_valid) && (old_dut.candidate_segment == new_dut.candidate_segment) && (old_dut.candidate_address == new_dut.candidate_address) && (old_dut.candidate_word_address == new_dut.candidate_word_address) && (old_dut.prefetch_launch == new_dut.prefetch_launch);
endmodule
