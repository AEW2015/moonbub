module ingress_probe (
    input logic clk, reset, start, abort_packet,
    input logic [31:0] packet_bytes, epoch,
    input logic [16:0] blocks,
    input logic serial_clear, write_overlap, read_prefetch, tile_overlap,
    input logic in_valid,
    output logic in_ready,
    input logic [7:0] in_data,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_value,
    output logic [31:0] out_epoch,
    output logic done,
    output logic [7:0] error,
    output logic busy, draining, scratch_sealed,
    output logic [18:0] used_bytes,
    output logic [63:0] count_cycles, count_input_bytes, count_dense,
    output logic [63:0] count_reads, count_writes, count_dense_stall,
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
    output logic [3:0] packet_state,
    output logic metadata_wait,
    output logic dbg_running, dbg_allocation, dbg_seal_sent, dbg_packet_done,
    output logic dbg_coef_valid, dbg_coef_ready,
    output logic [1:0] dbg_coef_band,
    output logic [15:0] dbg_coef_block,
    output logic [5:0] dbg_coef_index,
    output logic signed [15:0] dbg_coef_value,
    output logic [31:0] dbg_coef_epoch,
    output logic dbg_meta_valid, dbg_meta_ready, dbg_meta_raw,
    output logic dbg_band_end_valid, dbg_band_end_ready,
    output logic [1:0] dbg_band_end_band,
    output logic dbg_seal_valid, dbg_seal_ready,
    output logic [4:0] dbg_scratch_state, dbg_scratch_return_state,
    output logic dbg_scratch_outstanding,
    output logic dbg_prefetch_offer, dbg_prefetch_launch, dbg_prefetch_use,
    output logic dbg_tile_mode, dbg_tile_preparing, dbg_prepare_bank, dbg_emit_bank,
    output logic [1:0] dbg_bank_ready, dbg_bank_owned, dbg_emitter_state,
    output logic [15:0] dbg_prepare_block,
    output logic [15:0] dbg_bank_block [0:1],
    output logic [31:0] dbg_bank_epoch [0:1],
    output logic dbg_tile_prepare_start, dbg_tile_publish, dbg_tile_release,
    output logic [63:0] count_emitter_state [0:3],
    output logic [63:0] count_tile_starts, count_tile_publishes, count_tile_releases,
    output logic [63:0] count_prepare_output_overlap, count_prepare_output_hold,
    output logic [63:0] count_tile_read_output_overlap, count_tile_bank_wait, count_both_ready_wait, count_tile_prep_done_wait, count_output_valid,
    output logic [63:0] count_publish_release_same_edge,
    output logic [1:0] max_tile_owned, max_tile_ready,
    output logic [63:0] count_prefetch_offers, count_prefetch_accepts, count_prefetch_acks,
    output logic [63:0] count_prefetch_uses, count_dense_during_read_pending, count_prefetch_drain_wait,
    output logic max_prefetch_offer,
    output logic dbg_write_slot_valid, dbg_assembler_full, dbg_write_enqueue,
    output logic [63:0] count_write_enqueues, count_write_accepts, count_write_acks, count_full_wait, count_packing_during_write_pending,
    output logic max_write_slot,
    output logic [1:0] max_owned_lines,
    output logic [2:0] dbg_scratch_phase,
    output logic [4:0] dbg_scratch_assembly_bytes,
    output logic [3:0] dbg_scratch_cache_valid,
    output logic [2:0] dbg_scratch_head_valid,
    output logic [63:0] count_packet_state [0:15],
    output logic [63:0] count_scratch_state [0:31],
    output logic [63:0] count_coef_stall, count_metadata_wait, count_band_end_stall,
    output logic [63:0] count_mem_req_stall, count_mem_pending, count_input_starved,
    output logic [63:0] ts_first_input, ts_last_input, ts_metadata_accept,
    output logic [63:0] ts_last_sparse_coef, ts_packet_done_observed,
    output logic [63:0] ts_seal_accepted, ts_scratch_sealed_observed,
    output logic [63:0] ts_first_dense, ts_last_dense, ts_integrated_done,
    output logic [63:0] ts_first_coef_band [0:3], ts_last_coef_band [0:3], ts_band_end [0:3],
    output logic [4:0] max_assembly_bytes,
    output logic [2:0] max_cache_valid, max_head_valid,
    output logic max_outstanding,
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_context_active, stage_cancel, stage_word_valid, stage_word_ready,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_write_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data, stage_write_data,
    output logic [5:0] stage_buffer_bytes, stage_buffer_highwater,
    output logic [2:0] stage_purpose,
    output logic [63:0] count_stage_reads, count_stage_responses, count_stage_writes,
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold,
    output logic probe_ingress_equal, probe_private_equal, probe_cache_update, probe_cache_init, probe_cancelled, probe_ctx_valid, probe_ctx_ready, probe_live,
    output logic [31:0] probe_cache, probe_replay, probe_size, probe_replay_word,
    output logic [5:0] probe_ctx_bits,
    output logic probe_ctx_last, probe_mode16,
    output logic [3:0] probe_state,
    output logic [63:0] probe_count_cycles, probe_count_inputs, probe_count_outputs, probe_count_stall,
    output logic probe_ingress_in_valid, probe_ingress_in_ready, probe_ingress_out_valid, probe_ingress_out_ready,
    output logic probe_outputs_equal
);
    logic  old_in_ready;
    logic  old_out_valid;
    logic [15:0] old_out_block;
    logic [5:0] old_out_index;
    logic signed [15:0] old_out_value;
    logic [31:0] old_out_epoch;
    logic  old_done;
    logic [7:0] old_error;
    logic  old_busy;
    logic  old_draining;
    logic  old_scratch_sealed;
    logic [18:0] old_used_bytes;
    logic [63:0] old_count_cycles;
    logic [63:0] old_count_input_bytes;
    logic [63:0] old_count_dense;
    logic [63:0] old_count_reads;
    logic [63:0] old_count_writes;
    logic [63:0] old_count_dense_stall;
    logic  old_mem_req_valid;
    logic  old_mem_req_write;
    logic [17:0] old_mem_req_addr;
    logic [127:0] old_mem_req_data;
    logic [31:0] old_mem_req_epoch;
    logic  old_mem_rsp_ready;
    logic [3:0] old_packet_state;
    logic  old_metadata_wait;
    logic  old_dbg_running;
    logic  old_dbg_allocation;
    logic  old_dbg_seal_sent;
    logic  old_dbg_packet_done;
    logic  old_dbg_coef_valid;
    logic  old_dbg_coef_ready;
    logic [1:0] old_dbg_coef_band;
    logic [15:0] old_dbg_coef_block;
    logic [5:0] old_dbg_coef_index;
    logic signed [15:0] old_dbg_coef_value;
    logic [31:0] old_dbg_coef_epoch;
    logic  old_dbg_meta_valid;
    logic  old_dbg_meta_ready;
    logic  old_dbg_meta_raw;
    logic  old_dbg_band_end_valid;
    logic  old_dbg_band_end_ready;
    logic [1:0] old_dbg_band_end_band;
    logic  old_dbg_seal_valid;
    logic  old_dbg_seal_ready;
    logic [4:0] old_dbg_scratch_state;
    logic [4:0] old_dbg_scratch_return_state;
    logic  old_dbg_scratch_outstanding;
    logic  old_dbg_prefetch_offer;
    logic  old_dbg_prefetch_launch;
    logic  old_dbg_prefetch_use;
    logic  old_dbg_tile_mode;
    logic  old_dbg_tile_preparing;
    logic  old_dbg_prepare_bank;
    logic  old_dbg_emit_bank;
    logic [1:0] old_dbg_bank_ready;
    logic [1:0] old_dbg_bank_owned;
    logic [1:0] old_dbg_emitter_state;
    logic [15:0] old_dbg_prepare_block;
    logic [15:0] old_dbg_bank_block[0:1];
    logic [31:0] old_dbg_bank_epoch[0:1];
    logic  old_dbg_tile_prepare_start;
    logic  old_dbg_tile_publish;
    logic  old_dbg_tile_release;
    logic [63:0] old_count_emitter_state[0:3];
    logic [63:0] old_count_tile_starts;
    logic [63:0] old_count_tile_publishes;
    logic [63:0] old_count_tile_releases;
    logic [63:0] old_count_prepare_output_overlap;
    logic [63:0] old_count_prepare_output_hold;
    logic [63:0] old_count_tile_read_output_overlap;
    logic [63:0] old_count_tile_bank_wait;
    logic [63:0] old_count_both_ready_wait;
    logic [63:0] old_count_tile_prep_done_wait;
    logic [63:0] old_count_output_valid;
    logic [63:0] old_count_publish_release_same_edge;
    logic [1:0] old_max_tile_owned;
    logic [1:0] old_max_tile_ready;
    logic [63:0] old_count_prefetch_offers;
    logic [63:0] old_count_prefetch_accepts;
    logic [63:0] old_count_prefetch_acks;
    logic [63:0] old_count_prefetch_uses;
    logic [63:0] old_count_dense_during_read_pending;
    logic [63:0] old_count_prefetch_drain_wait;
    logic  old_max_prefetch_offer;
    logic  old_dbg_write_slot_valid;
    logic  old_dbg_assembler_full;
    logic  old_dbg_write_enqueue;
    logic [63:0] old_count_write_enqueues;
    logic [63:0] old_count_write_accepts;
    logic [63:0] old_count_write_acks;
    logic [63:0] old_count_full_wait;
    logic [63:0] old_count_packing_during_write_pending;
    logic  old_max_write_slot;
    logic [1:0] old_max_owned_lines;
    logic [2:0] old_dbg_scratch_phase;
    logic [4:0] old_dbg_scratch_assembly_bytes;
    logic [3:0] old_dbg_scratch_cache_valid;
    logic [2:0] old_dbg_scratch_head_valid;
    logic [63:0] old_count_packet_state[0:15];
    logic [63:0] old_count_scratch_state[0:31];
    logic [63:0] old_count_coef_stall;
    logic [63:0] old_count_metadata_wait;
    logic [63:0] old_count_band_end_stall;
    logic [63:0] old_count_mem_req_stall;
    logic [63:0] old_count_mem_pending;
    logic [63:0] old_count_input_starved;
    logic [63:0] old_ts_first_input;
    logic [63:0] old_ts_last_input;
    logic [63:0] old_ts_metadata_accept;
    logic [63:0] old_ts_last_sparse_coef;
    logic [63:0] old_ts_packet_done_observed;
    logic [63:0] old_ts_seal_accepted;
    logic [63:0] old_ts_scratch_sealed_observed;
    logic [63:0] old_ts_first_dense;
    logic [63:0] old_ts_last_dense;
    logic [63:0] old_ts_integrated_done;
    logic [63:0] old_ts_first_coef_band[0:3];
    logic [63:0] old_ts_last_coef_band[0:3];
    logic [63:0] old_ts_band_end[0:3];
    logic [4:0] old_max_assembly_bytes;
    logic [2:0] old_max_cache_valid;
    logic [2:0] old_max_head_valid;
    logic  old_max_outstanding;
    logic  old_stage_read_req;
    logic  old_stage_read_rsp;
    logic  old_stage_write;
    logic  old_stage_pending;
    logic  old_stage_context_active;
    logic  old_stage_cancel;
    logic  old_stage_word_valid;
    logic  old_stage_word_ready;
    logic [31:0] old_stage_read_addr;
    logic [31:0] old_stage_rsp_addr;
    logic [31:0] old_stage_write_addr;
    logic [31:0] old_stage_req_epoch;
    logic [31:0] old_stage_rsp_epoch;
    logic [7:0] old_stage_read_data;
    logic [7:0] old_stage_write_data;
    logic [5:0] old_stage_buffer_bytes;
    logic [5:0] old_stage_buffer_highwater;
    logic [2:0] old_stage_purpose;
    logic [63:0] old_count_stage_reads;
    logic [63:0] old_count_stage_responses;
    logic [63:0] old_count_stage_writes;
    logic [63:0] old_count_stage_fetch_wait;
    logic [63:0] old_count_stage_word_hold;
    pipeline_original old_dut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .abort_packet(abort_packet),
        .packet_bytes(packet_bytes),
        .epoch(epoch),
        .blocks(blocks),
        .serial_clear(serial_clear),
        .write_overlap(write_overlap),
        .read_prefetch(read_prefetch),
        .tile_overlap(tile_overlap),
        .in_valid(in_valid),
        .in_ready(old_in_ready),
        .in_data(in_data),
        .in_last(in_last),
        .out_valid(old_out_valid),
        .out_ready(out_ready),
        .out_block(old_out_block),
        .out_index(old_out_index),
        .out_value(old_out_value),
        .out_epoch(old_out_epoch),
        .done(old_done),
        .error(old_error),
        .busy(old_busy),
        .draining(old_draining),
        .scratch_sealed(old_scratch_sealed),
        .used_bytes(old_used_bytes),
        .count_cycles(old_count_cycles),
        .count_input_bytes(old_count_input_bytes),
        .count_dense(old_count_dense),
        .count_reads(old_count_reads),
        .count_writes(old_count_writes),
        .count_dense_stall(old_count_dense_stall),
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
        .packet_state(old_packet_state),
        .metadata_wait(old_metadata_wait),
        .dbg_running(old_dbg_running),
        .dbg_allocation(old_dbg_allocation),
        .dbg_seal_sent(old_dbg_seal_sent),
        .dbg_packet_done(old_dbg_packet_done),
        .dbg_coef_valid(old_dbg_coef_valid),
        .dbg_coef_ready(old_dbg_coef_ready),
        .dbg_coef_band(old_dbg_coef_band),
        .dbg_coef_block(old_dbg_coef_block),
        .dbg_coef_index(old_dbg_coef_index),
        .dbg_coef_value(old_dbg_coef_value),
        .dbg_coef_epoch(old_dbg_coef_epoch),
        .dbg_meta_valid(old_dbg_meta_valid),
        .dbg_meta_ready(old_dbg_meta_ready),
        .dbg_meta_raw(old_dbg_meta_raw),
        .dbg_band_end_valid(old_dbg_band_end_valid),
        .dbg_band_end_ready(old_dbg_band_end_ready),
        .dbg_band_end_band(old_dbg_band_end_band),
        .dbg_seal_valid(old_dbg_seal_valid),
        .dbg_seal_ready(old_dbg_seal_ready),
        .dbg_scratch_state(old_dbg_scratch_state),
        .dbg_scratch_return_state(old_dbg_scratch_return_state),
        .dbg_scratch_outstanding(old_dbg_scratch_outstanding),
        .dbg_prefetch_offer(old_dbg_prefetch_offer),
        .dbg_prefetch_launch(old_dbg_prefetch_launch),
        .dbg_prefetch_use(old_dbg_prefetch_use),
        .dbg_tile_mode(old_dbg_tile_mode),
        .dbg_tile_preparing(old_dbg_tile_preparing),
        .dbg_prepare_bank(old_dbg_prepare_bank),
        .dbg_emit_bank(old_dbg_emit_bank),
        .dbg_bank_ready(old_dbg_bank_ready),
        .dbg_bank_owned(old_dbg_bank_owned),
        .dbg_emitter_state(old_dbg_emitter_state),
        .dbg_prepare_block(old_dbg_prepare_block),
        .dbg_bank_block(old_dbg_bank_block),
        .dbg_bank_epoch(old_dbg_bank_epoch),
        .dbg_tile_prepare_start(old_dbg_tile_prepare_start),
        .dbg_tile_publish(old_dbg_tile_publish),
        .dbg_tile_release(old_dbg_tile_release),
        .count_emitter_state(old_count_emitter_state),
        .count_tile_starts(old_count_tile_starts),
        .count_tile_publishes(old_count_tile_publishes),
        .count_tile_releases(old_count_tile_releases),
        .count_prepare_output_overlap(old_count_prepare_output_overlap),
        .count_prepare_output_hold(old_count_prepare_output_hold),
        .count_tile_read_output_overlap(old_count_tile_read_output_overlap),
        .count_tile_bank_wait(old_count_tile_bank_wait),
        .count_both_ready_wait(old_count_both_ready_wait),
        .count_tile_prep_done_wait(old_count_tile_prep_done_wait),
        .count_output_valid(old_count_output_valid),
        .count_publish_release_same_edge(old_count_publish_release_same_edge),
        .max_tile_owned(old_max_tile_owned),
        .max_tile_ready(old_max_tile_ready),
        .count_prefetch_offers(old_count_prefetch_offers),
        .count_prefetch_accepts(old_count_prefetch_accepts),
        .count_prefetch_acks(old_count_prefetch_acks),
        .count_prefetch_uses(old_count_prefetch_uses),
        .count_dense_during_read_pending(old_count_dense_during_read_pending),
        .count_prefetch_drain_wait(old_count_prefetch_drain_wait),
        .max_prefetch_offer(old_max_prefetch_offer),
        .dbg_write_slot_valid(old_dbg_write_slot_valid),
        .dbg_assembler_full(old_dbg_assembler_full),
        .dbg_write_enqueue(old_dbg_write_enqueue),
        .count_write_enqueues(old_count_write_enqueues),
        .count_write_accepts(old_count_write_accepts),
        .count_write_acks(old_count_write_acks),
        .count_full_wait(old_count_full_wait),
        .count_packing_during_write_pending(old_count_packing_during_write_pending),
        .max_write_slot(old_max_write_slot),
        .max_owned_lines(old_max_owned_lines),
        .dbg_scratch_phase(old_dbg_scratch_phase),
        .dbg_scratch_assembly_bytes(old_dbg_scratch_assembly_bytes),
        .dbg_scratch_cache_valid(old_dbg_scratch_cache_valid),
        .dbg_scratch_head_valid(old_dbg_scratch_head_valid),
        .count_packet_state(old_count_packet_state),
        .count_scratch_state(old_count_scratch_state),
        .count_coef_stall(old_count_coef_stall),
        .count_metadata_wait(old_count_metadata_wait),
        .count_band_end_stall(old_count_band_end_stall),
        .count_mem_req_stall(old_count_mem_req_stall),
        .count_mem_pending(old_count_mem_pending),
        .count_input_starved(old_count_input_starved),
        .ts_first_input(old_ts_first_input),
        .ts_last_input(old_ts_last_input),
        .ts_metadata_accept(old_ts_metadata_accept),
        .ts_last_sparse_coef(old_ts_last_sparse_coef),
        .ts_packet_done_observed(old_ts_packet_done_observed),
        .ts_seal_accepted(old_ts_seal_accepted),
        .ts_scratch_sealed_observed(old_ts_scratch_sealed_observed),
        .ts_first_dense(old_ts_first_dense),
        .ts_last_dense(old_ts_last_dense),
        .ts_integrated_done(old_ts_integrated_done),
        .ts_first_coef_band(old_ts_first_coef_band),
        .ts_last_coef_band(old_ts_last_coef_band),
        .ts_band_end(old_ts_band_end),
        .max_assembly_bytes(old_max_assembly_bytes),
        .max_cache_valid(old_max_cache_valid),
        .max_head_valid(old_max_head_valid),
        .max_outstanding(old_max_outstanding),
        .stage_read_req(old_stage_read_req),
        .stage_read_rsp(old_stage_read_rsp),
        .stage_write(old_stage_write),
        .stage_pending(old_stage_pending),
        .stage_context_active(old_stage_context_active),
        .stage_cancel(old_stage_cancel),
        .stage_word_valid(old_stage_word_valid),
        .stage_word_ready(old_stage_word_ready),
        .stage_read_addr(old_stage_read_addr),
        .stage_rsp_addr(old_stage_rsp_addr),
        .stage_write_addr(old_stage_write_addr),
        .stage_req_epoch(old_stage_req_epoch),
        .stage_rsp_epoch(old_stage_rsp_epoch),
        .stage_read_data(old_stage_read_data),
        .stage_write_data(old_stage_write_data),
        .stage_buffer_bytes(old_stage_buffer_bytes),
        .stage_buffer_highwater(old_stage_buffer_highwater),
        .stage_purpose(old_stage_purpose),
        .count_stage_reads(old_count_stage_reads),
        .count_stage_responses(old_count_stage_responses),
        .count_stage_writes(old_count_stage_writes),
        .count_stage_fetch_wait(old_count_stage_fetch_wait),
        .count_stage_word_hold(old_count_stage_word_hold));
    pipeline_candidate new_dut (
        .clk(clk),
        .reset(reset),
        .start(start),
        .abort_packet(abort_packet),
        .packet_bytes(packet_bytes),
        .epoch(epoch),
        .blocks(blocks),
        .serial_clear(serial_clear),
        .write_overlap(write_overlap),
        .read_prefetch(read_prefetch),
        .tile_overlap(tile_overlap),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_data(in_data),
        .in_last(in_last),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_block(out_block),
        .out_index(out_index),
        .out_value(out_value),
        .out_epoch(out_epoch),
        .done(done),
        .error(error),
        .busy(busy),
        .draining(draining),
        .scratch_sealed(scratch_sealed),
        .used_bytes(used_bytes),
        .count_cycles(count_cycles),
        .count_input_bytes(count_input_bytes),
        .count_dense(count_dense),
        .count_reads(count_reads),
        .count_writes(count_writes),
        .count_dense_stall(count_dense_stall),
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
        .packet_state(packet_state),
        .metadata_wait(metadata_wait),
        .dbg_running(dbg_running),
        .dbg_allocation(dbg_allocation),
        .dbg_seal_sent(dbg_seal_sent),
        .dbg_packet_done(dbg_packet_done),
        .dbg_coef_valid(dbg_coef_valid),
        .dbg_coef_ready(dbg_coef_ready),
        .dbg_coef_band(dbg_coef_band),
        .dbg_coef_block(dbg_coef_block),
        .dbg_coef_index(dbg_coef_index),
        .dbg_coef_value(dbg_coef_value),
        .dbg_coef_epoch(dbg_coef_epoch),
        .dbg_meta_valid(dbg_meta_valid),
        .dbg_meta_ready(dbg_meta_ready),
        .dbg_meta_raw(dbg_meta_raw),
        .dbg_band_end_valid(dbg_band_end_valid),
        .dbg_band_end_ready(dbg_band_end_ready),
        .dbg_band_end_band(dbg_band_end_band),
        .dbg_seal_valid(dbg_seal_valid),
        .dbg_seal_ready(dbg_seal_ready),
        .dbg_scratch_state(dbg_scratch_state),
        .dbg_scratch_return_state(dbg_scratch_return_state),
        .dbg_scratch_outstanding(dbg_scratch_outstanding),
        .dbg_prefetch_offer(dbg_prefetch_offer),
        .dbg_prefetch_launch(dbg_prefetch_launch),
        .dbg_prefetch_use(dbg_prefetch_use),
        .dbg_tile_mode(dbg_tile_mode),
        .dbg_tile_preparing(dbg_tile_preparing),
        .dbg_prepare_bank(dbg_prepare_bank),
        .dbg_emit_bank(dbg_emit_bank),
        .dbg_bank_ready(dbg_bank_ready),
        .dbg_bank_owned(dbg_bank_owned),
        .dbg_emitter_state(dbg_emitter_state),
        .dbg_prepare_block(dbg_prepare_block),
        .dbg_bank_block(dbg_bank_block),
        .dbg_bank_epoch(dbg_bank_epoch),
        .dbg_tile_prepare_start(dbg_tile_prepare_start),
        .dbg_tile_publish(dbg_tile_publish),
        .dbg_tile_release(dbg_tile_release),
        .count_emitter_state(count_emitter_state),
        .count_tile_starts(count_tile_starts),
        .count_tile_publishes(count_tile_publishes),
        .count_tile_releases(count_tile_releases),
        .count_prepare_output_overlap(count_prepare_output_overlap),
        .count_prepare_output_hold(count_prepare_output_hold),
        .count_tile_read_output_overlap(count_tile_read_output_overlap),
        .count_tile_bank_wait(count_tile_bank_wait),
        .count_both_ready_wait(count_both_ready_wait),
        .count_tile_prep_done_wait(count_tile_prep_done_wait),
        .count_output_valid(count_output_valid),
        .count_publish_release_same_edge(count_publish_release_same_edge),
        .max_tile_owned(max_tile_owned),
        .max_tile_ready(max_tile_ready),
        .count_prefetch_offers(count_prefetch_offers),
        .count_prefetch_accepts(count_prefetch_accepts),
        .count_prefetch_acks(count_prefetch_acks),
        .count_prefetch_uses(count_prefetch_uses),
        .count_dense_during_read_pending(count_dense_during_read_pending),
        .count_prefetch_drain_wait(count_prefetch_drain_wait),
        .max_prefetch_offer(max_prefetch_offer),
        .dbg_write_slot_valid(dbg_write_slot_valid),
        .dbg_assembler_full(dbg_assembler_full),
        .dbg_write_enqueue(dbg_write_enqueue),
        .count_write_enqueues(count_write_enqueues),
        .count_write_accepts(count_write_accepts),
        .count_write_acks(count_write_acks),
        .count_full_wait(count_full_wait),
        .count_packing_during_write_pending(count_packing_during_write_pending),
        .max_write_slot(max_write_slot),
        .max_owned_lines(max_owned_lines),
        .dbg_scratch_phase(dbg_scratch_phase),
        .dbg_scratch_assembly_bytes(dbg_scratch_assembly_bytes),
        .dbg_scratch_cache_valid(dbg_scratch_cache_valid),
        .dbg_scratch_head_valid(dbg_scratch_head_valid),
        .count_packet_state(count_packet_state),
        .count_scratch_state(count_scratch_state),
        .count_coef_stall(count_coef_stall),
        .count_metadata_wait(count_metadata_wait),
        .count_band_end_stall(count_band_end_stall),
        .count_mem_req_stall(count_mem_req_stall),
        .count_mem_pending(count_mem_pending),
        .count_input_starved(count_input_starved),
        .ts_first_input(ts_first_input),
        .ts_last_input(ts_last_input),
        .ts_metadata_accept(ts_metadata_accept),
        .ts_last_sparse_coef(ts_last_sparse_coef),
        .ts_packet_done_observed(ts_packet_done_observed),
        .ts_seal_accepted(ts_seal_accepted),
        .ts_scratch_sealed_observed(ts_scratch_sealed_observed),
        .ts_first_dense(ts_first_dense),
        .ts_last_dense(ts_last_dense),
        .ts_integrated_done(ts_integrated_done),
        .ts_first_coef_band(ts_first_coef_band),
        .ts_last_coef_band(ts_last_coef_band),
        .ts_band_end(ts_band_end),
        .max_assembly_bytes(max_assembly_bytes),
        .max_cache_valid(max_cache_valid),
        .max_head_valid(max_head_valid),
        .max_outstanding(max_outstanding),
        .stage_read_req(stage_read_req),
        .stage_read_rsp(stage_read_rsp),
        .stage_write(stage_write),
        .stage_pending(stage_pending),
        .stage_context_active(stage_context_active),
        .stage_cancel(stage_cancel),
        .stage_word_valid(stage_word_valid),
        .stage_word_ready(stage_word_ready),
        .stage_read_addr(stage_read_addr),
        .stage_rsp_addr(stage_rsp_addr),
        .stage_write_addr(stage_write_addr),
        .stage_req_epoch(stage_req_epoch),
        .stage_rsp_epoch(stage_rsp_epoch),
        .stage_read_data(stage_read_data),
        .stage_write_data(stage_write_data),
        .stage_buffer_bytes(stage_buffer_bytes),
        .stage_buffer_highwater(stage_buffer_highwater),
        .stage_purpose(stage_purpose),
        .count_stage_reads(count_stage_reads),
        .count_stage_responses(count_stage_responses),
        .count_stage_writes(count_stage_writes),
        .count_stage_fetch_wait(count_stage_fetch_wait),
        .count_stage_word_hold(count_stage_word_hold));
    assign probe_outputs_equal=(old_in_ready==in_ready) &&
        (old_out_valid==out_valid) &&
        (old_out_block==out_block) &&
        (old_out_index==out_index) &&
        (old_out_value==out_value) &&
        (old_out_epoch==out_epoch) &&
        (old_done==done) &&
        (old_error==error) &&
        (old_busy==busy) &&
        (old_draining==draining) &&
        (old_scratch_sealed==scratch_sealed) &&
        (old_used_bytes==used_bytes) &&
        (old_count_cycles==count_cycles) &&
        (old_count_input_bytes==count_input_bytes) &&
        (old_count_dense==count_dense) &&
        (old_count_reads==count_reads) &&
        (old_count_writes==count_writes) &&
        (old_count_dense_stall==count_dense_stall) &&
        (old_mem_req_valid==mem_req_valid) &&
        (old_mem_req_write==mem_req_write) &&
        (old_mem_req_addr==mem_req_addr) &&
        (old_mem_req_data==mem_req_data) &&
        (old_mem_req_epoch==mem_req_epoch) &&
        (old_mem_rsp_ready==mem_rsp_ready) &&
        (old_packet_state==packet_state) &&
        (old_metadata_wait==metadata_wait) &&
        (old_dbg_running==dbg_running) &&
        (old_dbg_allocation==dbg_allocation) &&
        (old_dbg_seal_sent==dbg_seal_sent) &&
        (old_dbg_packet_done==dbg_packet_done) &&
        (old_dbg_coef_valid==dbg_coef_valid) &&
        (old_dbg_coef_ready==dbg_coef_ready) &&
        (old_dbg_coef_band==dbg_coef_band) &&
        (old_dbg_coef_block==dbg_coef_block) &&
        (old_dbg_coef_index==dbg_coef_index) &&
        (old_dbg_coef_value==dbg_coef_value) &&
        (old_dbg_coef_epoch==dbg_coef_epoch) &&
        (old_dbg_meta_valid==dbg_meta_valid) &&
        (old_dbg_meta_ready==dbg_meta_ready) &&
        (old_dbg_meta_raw==dbg_meta_raw) &&
        (old_dbg_band_end_valid==dbg_band_end_valid) &&
        (old_dbg_band_end_ready==dbg_band_end_ready) &&
        (old_dbg_band_end_band==dbg_band_end_band) &&
        (old_dbg_seal_valid==dbg_seal_valid) &&
        (old_dbg_seal_ready==dbg_seal_ready) &&
        (old_dbg_scratch_state==dbg_scratch_state) &&
        (old_dbg_scratch_return_state==dbg_scratch_return_state) &&
        (old_dbg_scratch_outstanding==dbg_scratch_outstanding) &&
        (old_dbg_prefetch_offer==dbg_prefetch_offer) &&
        (old_dbg_prefetch_launch==dbg_prefetch_launch) &&
        (old_dbg_prefetch_use==dbg_prefetch_use) &&
        (old_dbg_tile_mode==dbg_tile_mode) &&
        (old_dbg_tile_preparing==dbg_tile_preparing) &&
        (old_dbg_prepare_bank==dbg_prepare_bank) &&
        (old_dbg_emit_bank==dbg_emit_bank) &&
        (old_dbg_bank_ready==dbg_bank_ready) &&
        (old_dbg_bank_owned==dbg_bank_owned) &&
        (old_dbg_emitter_state==dbg_emitter_state) &&
        (old_dbg_prepare_block==dbg_prepare_block) &&
        (old_dbg_bank_block[0]==dbg_bank_block[0]) &&
        (old_dbg_bank_block[1]==dbg_bank_block[1]) &&
        (old_dbg_bank_epoch[0]==dbg_bank_epoch[0]) &&
        (old_dbg_bank_epoch[1]==dbg_bank_epoch[1]) &&
        (old_dbg_tile_prepare_start==dbg_tile_prepare_start) &&
        (old_dbg_tile_publish==dbg_tile_publish) &&
        (old_dbg_tile_release==dbg_tile_release) &&
        (old_count_emitter_state[0]==count_emitter_state[0]) &&
        (old_count_emitter_state[1]==count_emitter_state[1]) &&
        (old_count_emitter_state[2]==count_emitter_state[2]) &&
        (old_count_emitter_state[3]==count_emitter_state[3]) &&
        (old_count_tile_starts==count_tile_starts) &&
        (old_count_tile_publishes==count_tile_publishes) &&
        (old_count_tile_releases==count_tile_releases) &&
        (old_count_prepare_output_overlap==count_prepare_output_overlap) &&
        (old_count_prepare_output_hold==count_prepare_output_hold) &&
        (old_count_tile_read_output_overlap==count_tile_read_output_overlap) &&
        (old_count_tile_bank_wait==count_tile_bank_wait) &&
        (old_count_both_ready_wait==count_both_ready_wait) &&
        (old_count_tile_prep_done_wait==count_tile_prep_done_wait) &&
        (old_count_output_valid==count_output_valid) &&
        (old_count_publish_release_same_edge==count_publish_release_same_edge) &&
        (old_max_tile_owned==max_tile_owned) &&
        (old_max_tile_ready==max_tile_ready) &&
        (old_count_prefetch_offers==count_prefetch_offers) &&
        (old_count_prefetch_accepts==count_prefetch_accepts) &&
        (old_count_prefetch_acks==count_prefetch_acks) &&
        (old_count_prefetch_uses==count_prefetch_uses) &&
        (old_count_dense_during_read_pending==count_dense_during_read_pending) &&
        (old_count_prefetch_drain_wait==count_prefetch_drain_wait) &&
        (old_max_prefetch_offer==max_prefetch_offer) &&
        (old_dbg_write_slot_valid==dbg_write_slot_valid) &&
        (old_dbg_assembler_full==dbg_assembler_full) &&
        (old_dbg_write_enqueue==dbg_write_enqueue) &&
        (old_count_write_enqueues==count_write_enqueues) &&
        (old_count_write_accepts==count_write_accepts) &&
        (old_count_write_acks==count_write_acks) &&
        (old_count_full_wait==count_full_wait) &&
        (old_count_packing_during_write_pending==count_packing_during_write_pending) &&
        (old_max_write_slot==max_write_slot) &&
        (old_max_owned_lines==max_owned_lines) &&
        (old_dbg_scratch_phase==dbg_scratch_phase) &&
        (old_dbg_scratch_assembly_bytes==dbg_scratch_assembly_bytes) &&
        (old_dbg_scratch_cache_valid==dbg_scratch_cache_valid) &&
        (old_dbg_scratch_head_valid==dbg_scratch_head_valid) &&
        (old_count_packet_state[0]==count_packet_state[0]) &&
        (old_count_packet_state[1]==count_packet_state[1]) &&
        (old_count_packet_state[2]==count_packet_state[2]) &&
        (old_count_packet_state[3]==count_packet_state[3]) &&
        (old_count_packet_state[4]==count_packet_state[4]) &&
        (old_count_packet_state[5]==count_packet_state[5]) &&
        (old_count_packet_state[6]==count_packet_state[6]) &&
        (old_count_packet_state[7]==count_packet_state[7]) &&
        (old_count_packet_state[8]==count_packet_state[8]) &&
        (old_count_packet_state[9]==count_packet_state[9]) &&
        (old_count_packet_state[10]==count_packet_state[10]) &&
        (old_count_packet_state[11]==count_packet_state[11]) &&
        (old_count_packet_state[12]==count_packet_state[12]) &&
        (old_count_packet_state[13]==count_packet_state[13]) &&
        (old_count_packet_state[14]==count_packet_state[14]) &&
        (old_count_packet_state[15]==count_packet_state[15]) &&
        (old_count_scratch_state[0]==count_scratch_state[0]) &&
        (old_count_scratch_state[1]==count_scratch_state[1]) &&
        (old_count_scratch_state[2]==count_scratch_state[2]) &&
        (old_count_scratch_state[3]==count_scratch_state[3]) &&
        (old_count_scratch_state[4]==count_scratch_state[4]) &&
        (old_count_scratch_state[5]==count_scratch_state[5]) &&
        (old_count_scratch_state[6]==count_scratch_state[6]) &&
        (old_count_scratch_state[7]==count_scratch_state[7]) &&
        (old_count_scratch_state[8]==count_scratch_state[8]) &&
        (old_count_scratch_state[9]==count_scratch_state[9]) &&
        (old_count_scratch_state[10]==count_scratch_state[10]) &&
        (old_count_scratch_state[11]==count_scratch_state[11]) &&
        (old_count_scratch_state[12]==count_scratch_state[12]) &&
        (old_count_scratch_state[13]==count_scratch_state[13]) &&
        (old_count_scratch_state[14]==count_scratch_state[14]) &&
        (old_count_scratch_state[15]==count_scratch_state[15]) &&
        (old_count_scratch_state[16]==count_scratch_state[16]) &&
        (old_count_scratch_state[17]==count_scratch_state[17]) &&
        (old_count_scratch_state[18]==count_scratch_state[18]) &&
        (old_count_scratch_state[19]==count_scratch_state[19]) &&
        (old_count_scratch_state[20]==count_scratch_state[20]) &&
        (old_count_scratch_state[21]==count_scratch_state[21]) &&
        (old_count_scratch_state[22]==count_scratch_state[22]) &&
        (old_count_scratch_state[23]==count_scratch_state[23]) &&
        (old_count_scratch_state[24]==count_scratch_state[24]) &&
        (old_count_scratch_state[25]==count_scratch_state[25]) &&
        (old_count_scratch_state[26]==count_scratch_state[26]) &&
        (old_count_scratch_state[27]==count_scratch_state[27]) &&
        (old_count_scratch_state[28]==count_scratch_state[28]) &&
        (old_count_scratch_state[29]==count_scratch_state[29]) &&
        (old_count_scratch_state[30]==count_scratch_state[30]) &&
        (old_count_scratch_state[31]==count_scratch_state[31]) &&
        (old_count_coef_stall==count_coef_stall) &&
        (old_count_metadata_wait==count_metadata_wait) &&
        (old_count_band_end_stall==count_band_end_stall) &&
        (old_count_mem_req_stall==count_mem_req_stall) &&
        (old_count_mem_pending==count_mem_pending) &&
        (old_count_input_starved==count_input_starved) &&
        (old_ts_first_input==ts_first_input) &&
        (old_ts_last_input==ts_last_input) &&
        (old_ts_metadata_accept==ts_metadata_accept) &&
        (old_ts_last_sparse_coef==ts_last_sparse_coef) &&
        (old_ts_packet_done_observed==ts_packet_done_observed) &&
        (old_ts_seal_accepted==ts_seal_accepted) &&
        (old_ts_scratch_sealed_observed==ts_scratch_sealed_observed) &&
        (old_ts_first_dense==ts_first_dense) &&
        (old_ts_last_dense==ts_last_dense) &&
        (old_ts_integrated_done==ts_integrated_done) &&
        (old_ts_first_coef_band[0]==ts_first_coef_band[0]) &&
        (old_ts_first_coef_band[1]==ts_first_coef_band[1]) &&
        (old_ts_first_coef_band[2]==ts_first_coef_band[2]) &&
        (old_ts_first_coef_band[3]==ts_first_coef_band[3]) &&
        (old_ts_last_coef_band[0]==ts_last_coef_band[0]) &&
        (old_ts_last_coef_band[1]==ts_last_coef_band[1]) &&
        (old_ts_last_coef_band[2]==ts_last_coef_band[2]) &&
        (old_ts_last_coef_band[3]==ts_last_coef_band[3]) &&
        (old_ts_band_end[0]==ts_band_end[0]) &&
        (old_ts_band_end[1]==ts_band_end[1]) &&
        (old_ts_band_end[2]==ts_band_end[2]) &&
        (old_ts_band_end[3]==ts_band_end[3]) &&
        (old_max_assembly_bytes==max_assembly_bytes) &&
        (old_max_cache_valid==max_cache_valid) &&
        (old_max_head_valid==max_head_valid) &&
        (old_max_outstanding==max_outstanding) &&
        (old_stage_read_req==stage_read_req) &&
        (old_stage_read_rsp==stage_read_rsp) &&
        (old_stage_write==stage_write) &&
        (old_stage_pending==stage_pending) &&
        (old_stage_context_active==stage_context_active) &&
        (old_stage_cancel==stage_cancel) &&
        (old_stage_word_valid==stage_word_valid) &&
        (old_stage_word_ready==stage_word_ready) &&
        (old_stage_read_addr==stage_read_addr) &&
        (old_stage_rsp_addr==stage_rsp_addr) &&
        (old_stage_write_addr==stage_write_addr) &&
        (old_stage_req_epoch==stage_req_epoch) &&
        (old_stage_rsp_epoch==stage_rsp_epoch) &&
        (old_stage_read_data==stage_read_data) &&
        (old_stage_write_data==stage_write_data) &&
        (old_stage_buffer_bytes==stage_buffer_bytes) &&
        (old_stage_buffer_highwater==stage_buffer_highwater) &&
        (old_stage_purpose==stage_purpose) &&
        (old_count_stage_reads==count_stage_reads) &&
        (old_count_stage_responses==count_stage_responses) &&
        (old_count_stage_writes==count_stage_writes) &&
        (old_count_stage_fetch_wait==count_stage_fetch_wait) &&
        (old_count_stage_word_hold==count_stage_word_hold);
assign probe_ingress_equal = (old_dut.packet_decoder.synchronous.ingress.in_ready==new_dut.packet_decoder.synchronous.ingress.in_ready) && (old_dut.packet_decoder.synchronous.ingress.out_valid==new_dut.packet_decoder.synchronous.ingress.out_valid) && (old_dut.packet_decoder.synchronous.ingress.out_block==new_dut.packet_decoder.synchronous.ingress.out_block) && (old_dut.packet_decoder.synchronous.ingress.out_index==new_dut.packet_decoder.synchronous.ingress.out_index) && (old_dut.packet_decoder.synchronous.ingress.out_coefficient==new_dut.packet_decoder.synchronous.ingress.out_coefficient) && (old_dut.packet_decoder.synchronous.ingress.out_epoch==new_dut.packet_decoder.synchronous.ingress.out_epoch) && (old_dut.packet_decoder.synchronous.ingress.meta_valid==new_dut.packet_decoder.synchronous.ingress.meta_valid) && (old_dut.packet_decoder.synchronous.ingress.meta_blocks==new_dut.packet_decoder.synchronous.ingress.meta_blocks) && (old_dut.packet_decoder.synchronous.ingress.meta_count1==new_dut.packet_decoder.synchronous.ingress.meta_count1) && (old_dut.packet_decoder.synchronous.ingress.meta_count2==new_dut.packet_decoder.synchronous.ingress.meta_count2) && (old_dut.packet_decoder.synchronous.ingress.meta_count3==new_dut.packet_decoder.synchronous.ingress.meta_count3) && (old_dut.packet_decoder.synchronous.ingress.meta_epoch==new_dut.packet_decoder.synchronous.ingress.meta_epoch) && (old_dut.packet_decoder.synchronous.ingress.meta_raw==new_dut.packet_decoder.synchronous.ingress.meta_raw) && (old_dut.packet_decoder.synchronous.ingress.out_band==new_dut.packet_decoder.synchronous.ingress.out_band) && (old_dut.packet_decoder.synchronous.ingress.band_end_valid==new_dut.packet_decoder.synchronous.ingress.band_end_valid) && (old_dut.packet_decoder.synchronous.ingress.band_end_band==new_dut.packet_decoder.synchronous.ingress.band_end_band) && (old_dut.packet_decoder.synchronous.ingress.band_end_epoch==new_dut.packet_decoder.synchronous.ingress.band_end_epoch) && (old_dut.packet_decoder.synchronous.ingress.done==new_dut.packet_decoder.synchronous.ingress.done) && (old_dut.packet_decoder.synchronous.ingress.error==new_dut.packet_decoder.synchronous.ingress.error) && (old_dut.packet_decoder.synchronous.ingress.count_cycles==new_dut.packet_decoder.synchronous.ingress.count_cycles) && (old_dut.packet_decoder.synchronous.ingress.count_inputs==new_dut.packet_decoder.synchronous.ingress.count_inputs) && (old_dut.packet_decoder.synchronous.ingress.count_outputs==new_dut.packet_decoder.synchronous.ingress.count_outputs) && (old_dut.packet_decoder.synchronous.ingress.count_output_stall==new_dut.packet_decoder.synchronous.ingress.count_output_stall) && (old_dut.packet_decoder.synchronous.ingress.debug_state==new_dut.packet_decoder.synchronous.ingress.debug_state) && (old_dut.packet_decoder.synchronous.ingress.stage_read_req==new_dut.packet_decoder.synchronous.ingress.stage_read_req) && (old_dut.packet_decoder.synchronous.ingress.stage_read_rsp==new_dut.packet_decoder.synchronous.ingress.stage_read_rsp) && (old_dut.packet_decoder.synchronous.ingress.stage_write==new_dut.packet_decoder.synchronous.ingress.stage_write) && (old_dut.packet_decoder.synchronous.ingress.stage_pending==new_dut.packet_decoder.synchronous.ingress.stage_pending) && (old_dut.packet_decoder.synchronous.ingress.stage_context_active==new_dut.packet_decoder.synchronous.ingress.stage_context_active) && (old_dut.packet_decoder.synchronous.ingress.stage_cancel==new_dut.packet_decoder.synchronous.ingress.stage_cancel) && (old_dut.packet_decoder.synchronous.ingress.stage_word_valid==new_dut.packet_decoder.synchronous.ingress.stage_word_valid) && (old_dut.packet_decoder.synchronous.ingress.stage_word_ready==new_dut.packet_decoder.synchronous.ingress.stage_word_ready) && (old_dut.packet_decoder.synchronous.ingress.stage_read_addr==new_dut.packet_decoder.synchronous.ingress.stage_read_addr) && (old_dut.packet_decoder.synchronous.ingress.stage_rsp_addr==new_dut.packet_decoder.synchronous.ingress.stage_rsp_addr) && (old_dut.packet_decoder.synchronous.ingress.stage_write_addr==new_dut.packet_decoder.synchronous.ingress.stage_write_addr) && (old_dut.packet_decoder.synchronous.ingress.stage_req_epoch==new_dut.packet_decoder.synchronous.ingress.stage_req_epoch) && (old_dut.packet_decoder.synchronous.ingress.stage_rsp_epoch==new_dut.packet_decoder.synchronous.ingress.stage_rsp_epoch) && (old_dut.packet_decoder.synchronous.ingress.stage_read_data==new_dut.packet_decoder.synchronous.ingress.stage_read_data) && (old_dut.packet_decoder.synchronous.ingress.stage_write_data==new_dut.packet_decoder.synchronous.ingress.stage_write_data) && (old_dut.packet_decoder.synchronous.ingress.stage_buffer_bytes==new_dut.packet_decoder.synchronous.ingress.stage_buffer_bytes) && (old_dut.packet_decoder.synchronous.ingress.stage_buffer_highwater==new_dut.packet_decoder.synchronous.ingress.stage_buffer_highwater) && (old_dut.packet_decoder.synchronous.ingress.stage_purpose==new_dut.packet_decoder.synchronous.ingress.stage_purpose) && (old_dut.packet_decoder.synchronous.ingress.count_stage_reads==new_dut.packet_decoder.synchronous.ingress.count_stage_reads) && (old_dut.packet_decoder.synchronous.ingress.count_stage_responses==new_dut.packet_decoder.synchronous.ingress.count_stage_responses) && (old_dut.packet_decoder.synchronous.ingress.count_stage_writes==new_dut.packet_decoder.synchronous.ingress.count_stage_writes) && (old_dut.packet_decoder.synchronous.ingress.count_stage_fetch_wait==new_dut.packet_decoder.synchronous.ingress.count_stage_fetch_wait) && (old_dut.packet_decoder.synchronous.ingress.count_stage_word_hold==new_dut.packet_decoder.synchronous.ingress.count_stage_word_hold);
assign probe_private_equal = (old_dut.packet_decoder.synchronous.ingress.state==new_dut.packet_decoder.synchronous.ingress.state) && (old_dut.packet_decoder.synchronous.ingress.fetch_return==new_dut.packet_decoder.synchronous.ingress.fetch_return) && (old_dut.packet_decoder.synchronous.ingress.ram_valid==new_dut.packet_decoder.synchronous.ingress.ram_valid) && (old_dut.packet_decoder.synchronous.ingress.ram_data==new_dut.packet_decoder.synchronous.ingress.ram_data) && (old_dut.packet_decoder.synchronous.ingress.ram_addr==new_dut.packet_decoder.synchronous.ingress.ram_addr) && (old_dut.packet_decoder.synchronous.ingress.ram_epoch==new_dut.packet_decoder.synchronous.ingress.ram_epoch) && (old_dut.packet_decoder.synchronous.ingress.fetch_index==new_dut.packet_decoder.synchronous.ingress.fetch_index) && (old_dut.packet_decoder.synchronous.ingress.fetch_count==new_dut.packet_decoder.synchronous.ingress.fetch_count) && (old_dut.packet_decoder.synchronous.ingress.buffer_bytes==new_dut.packet_decoder.synchronous.ingress.buffer_bytes) && (old_dut.packet_decoder.synchronous.ingress.fetch_kind==new_dut.packet_decoder.synchronous.ingress.fetch_kind) && (old_dut.packet_decoder.synchronous.ingress.fetch_base==new_dut.packet_decoder.synchronous.ingress.fetch_base) && (old_dut.packet_decoder.synchronous.ingress.fetch_address==new_dut.packet_decoder.synchronous.ingress.fetch_address) && (old_dut.packet_decoder.synchronous.ingress.fetched_word==new_dut.packet_decoder.synchronous.ingress.fetched_word) && (old_dut.packet_decoder.synchronous.ingress.size_bytes==new_dut.packet_decoder.synchronous.ingress.size_bytes) && (old_dut.packet_decoder.synchronous.ingress.context_epoch==new_dut.packet_decoder.synchronous.ingress.context_epoch) && (old_dut.packet_decoder.synchronous.ingress.received==new_dut.packet_decoder.synchronous.ingress.received) && (old_dut.packet_decoder.synchronous.ingress.crc==new_dut.packet_decoder.synchronous.ingress.crc) && (old_dut.packet_decoder.synchronous.ingress.cursor==new_dut.packet_decoder.synchronous.ingress.cursor) && (old_dut.packet_decoder.synchronous.ingress.context_blocks==new_dut.packet_decoder.synchronous.ingress.context_blocks) && (old_dut.packet_decoder.synchronous.ingress.mode16==new_dut.packet_decoder.synchronous.ingress.mode16) && (old_dut.packet_decoder.synchronous.ingress.mode_serial==new_dut.packet_decoder.synchronous.ingress.mode_serial) && (old_dut.packet_decoder.synchronous.ingress.raw_mode==new_dut.packet_decoder.synchronous.ingress.raw_mode) && (old_dut.packet_decoder.synchronous.ingress.descriptor_ready==new_dut.packet_decoder.synchronous.ingress.descriptor_ready) && (old_dut.packet_decoder.synchronous.ingress.word_valid==new_dut.packet_decoder.synchronous.ingress.word_valid) && (old_dut.packet_decoder.synchronous.ingress.raw_valid==new_dut.packet_decoder.synchronous.ingress.raw_valid) && (old_dut.packet_decoder.synchronous.ingress.context_active==new_dut.packet_decoder.synchronous.ingress.context_active) && (old_dut.packet_decoder.synchronous.ingress.band==new_dut.packet_decoder.synchronous.ingress.band) && (old_dut.packet_decoder.synchronous.ingress.descriptor_bits==new_dut.packet_decoder.synchronous.ingress.descriptor_bits) && (old_dut.packet_decoder.synchronous.ingress.descriptor_bytes==new_dut.packet_decoder.synchronous.ingress.descriptor_bytes) && (old_dut.packet_decoder.synchronous.ingress.descriptor_limit==new_dut.packet_decoder.synchronous.ingress.descriptor_limit) && (old_dut.packet_decoder.synchronous.ingress.replay_bits==new_dut.packet_decoder.synchronous.ingress.replay_bits) && (old_dut.packet_decoder.synchronous.ingress.raw_position==new_dut.packet_decoder.synchronous.ingress.raw_position) && (old_dut.packet_decoder.synchronous.ingress.replay_word==new_dut.packet_decoder.synchronous.ingress.replay_word) && (old_dut.packet_decoder.synchronous.ingress.ctx_data==new_dut.packet_decoder.synchronous.ingress.ctx_data) && (old_dut.packet_decoder.synchronous.ingress.ctx_valid==new_dut.packet_decoder.synchronous.ingress.ctx_valid) && (old_dut.packet_decoder.synchronous.ingress.ctx_ready==new_dut.packet_decoder.synchronous.ingress.ctx_ready) && (old_dut.packet_decoder.synchronous.ingress.ctx_out_valid==new_dut.packet_decoder.synchronous.ingress.ctx_out_valid) && (old_dut.packet_decoder.synchronous.ingress.ctx_done==new_dut.packet_decoder.synchronous.ingress.ctx_done) && (old_dut.packet_decoder.synchronous.ingress.ctx_block==new_dut.packet_decoder.synchronous.ingress.ctx_block) && (old_dut.packet_decoder.synchronous.ingress.ctx_index==new_dut.packet_decoder.synchronous.ingress.ctx_index) && (old_dut.packet_decoder.synchronous.ingress.ctx_coefficient==new_dut.packet_decoder.synchronous.ingress.ctx_coefficient) && (old_dut.packet_decoder.synchronous.ingress.ctx_epoch==new_dut.packet_decoder.synchronous.ingress.ctx_epoch) && (old_dut.packet_decoder.synchronous.ingress.ctx_error==new_dut.packet_decoder.synchronous.ingress.ctx_error) && (old_dut.packet_decoder.synchronous.ingress.cancelled==new_dut.packet_decoder.synchronous.ingress.cancelled) && (old_dut.packet_decoder.synchronous.ingress.context_failure==new_dut.packet_decoder.synchronous.ingress.context_failure) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[0]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[0]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[1]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[1]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[2]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[2]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[3]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[3]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[4]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[4]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[5]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[5]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[6]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[6]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[7]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[7]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[8]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[8]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[9]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[9]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[10]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[10]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[11]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[11]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[12]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[12]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[13]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[13]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[14]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[14]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[15]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[15]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[16]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[16]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[17]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[17]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[18]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[18]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[19]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[19]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[20]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[20]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[21]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[21]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[22]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[22]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[23]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[23]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[24]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[24]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[25]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[25]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[26]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[26]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[27]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[27]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[28]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[28]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[29]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[29]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[30]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[30]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[31]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[31]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[32]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[32]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[33]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[33]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[34]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[34]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[35]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[35]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[36]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[36]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[37]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[37]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[38]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[38]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[39]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[39]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[40]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[40]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[41]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[41]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[42]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[42]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[43]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[43]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[44]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[44]) && (old_dut.packet_decoder.synchronous.ingress.fetch_bytes[45]==new_dut.packet_decoder.synchronous.ingress.fetch_bytes[45]) && (old_dut.packet_decoder.synchronous.ingress.lengths[0]==new_dut.packet_decoder.synchronous.ingress.lengths[0]) && (old_dut.packet_decoder.synchronous.ingress.lengths[1]==new_dut.packet_decoder.synchronous.ingress.lengths[1]) && (old_dut.packet_decoder.synchronous.ingress.lengths[2]==new_dut.packet_decoder.synchronous.ingress.lengths[2]) && (old_dut.packet_decoder.synchronous.ingress.lengths[3]==new_dut.packet_decoder.synchronous.ingress.lengths[3]) && (old_dut.packet_decoder.synchronous.ingress.counts[0]==new_dut.packet_decoder.synchronous.ingress.counts[0]) && (old_dut.packet_decoder.synchronous.ingress.counts[1]==new_dut.packet_decoder.synchronous.ingress.counts[1]) && (old_dut.packet_decoder.synchronous.ingress.counts[2]==new_dut.packet_decoder.synchronous.ingress.counts[2]) && (old_dut.packet_decoder.synchronous.ingress.counts[3]==new_dut.packet_decoder.synchronous.ingress.counts[3]) && (old_dut.packet_decoder.synchronous.ingress.offsets[0]==new_dut.packet_decoder.synchronous.ingress.offsets[0]) && (old_dut.packet_decoder.synchronous.ingress.offsets[1]==new_dut.packet_decoder.synchronous.ingress.offsets[1]) && (old_dut.packet_decoder.synchronous.ingress.offsets[2]==new_dut.packet_decoder.synchronous.ingress.offsets[2]) && (old_dut.packet_decoder.synchronous.ingress.offsets[3]==new_dut.packet_decoder.synchronous.ingress.offsets[3]) && (old_dut.packet_decoder.synchronous.ingress.sizes[0]==new_dut.packet_decoder.synchronous.ingress.sizes[0]) && (old_dut.packet_decoder.synchronous.ingress.sizes[1]==new_dut.packet_decoder.synchronous.ingress.sizes[1]) && (old_dut.packet_decoder.synchronous.ingress.sizes[2]==new_dut.packet_decoder.synchronous.ingress.sizes[2]) && (old_dut.packet_decoder.synchronous.ingress.sizes[3]==new_dut.packet_decoder.synchronous.ingress.sizes[3]) && (old_dut.packet_decoder.synchronous.ingress.k0s[0]==new_dut.packet_decoder.synchronous.ingress.k0s[0]) && (old_dut.packet_decoder.synchronous.ingress.k0s[1]==new_dut.packet_decoder.synchronous.ingress.k0s[1]) && (old_dut.packet_decoder.synchronous.ingress.k0s[2]==new_dut.packet_decoder.synchronous.ingress.k0s[2]) && (old_dut.packet_decoder.synchronous.ingress.k0s[3]==new_dut.packet_decoder.synchronous.ingress.k0s[3]) && (old_dut.packet_decoder.synchronous.ingress.k1s[0]==new_dut.packet_decoder.synchronous.ingress.k1s[0]) && (old_dut.packet_decoder.synchronous.ingress.k1s[1]==new_dut.packet_decoder.synchronous.ingress.k1s[1]) && (old_dut.packet_decoder.synchronous.ingress.k1s[2]==new_dut.packet_decoder.synchronous.ingress.k1s[2]) && (old_dut.packet_decoder.synchronous.ingress.k1s[3]==new_dut.packet_decoder.synchronous.ingress.k1s[3]) && ((new_dut.packet_decoder.synchronous.ingress.state!=5)||((old_dut.packet_decoder.synchronous.ingress.ctx_bits==new_dut.packet_decoder.synchronous.ingress.ctx_bits)&&(old_dut.packet_decoder.synchronous.ingress.ctx_last==new_dut.packet_decoder.synchronous.ingress.ctx_last))) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.state==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.state) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.active==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.active) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.use16==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.use16) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.serial==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.serial) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.failed==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.failed) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.size_bits==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.size_bits) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.loaded==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.loaded) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.consumed==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.consumed) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.reservoir==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.reservoir) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.available==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.available) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.k==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.k) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.escape_width==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.escape_width) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.quotient==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.quotient) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.suffix_left==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.suffix_left) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.suffix_acc==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.suffix_acc) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_valid==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_valid) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_value==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_value) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_consumed==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_consumed) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_error==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.out_error) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_cycles==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_cycles) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_inputs==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_inputs) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_symbols==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_symbols) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_bits==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_bits) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_input_wait==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_input_wait) && (old_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_output_stall==new_dut.packet_decoder.synchronous.ingress.context_decoder.parser.count_output_stall);
assign probe_cancelled=new_dut.packet_decoder.synchronous.ingress.cancelled;
assign probe_live=new_dut.packet_decoder.synchronous.ingress.state==5;
assign probe_ctx_valid=new_dut.packet_decoder.synchronous.ingress.ctx_valid;
assign probe_ctx_ready=new_dut.packet_decoder.synchronous.ingress.ctx_ready;
assign probe_cache=new_dut.packet_decoder.synchronous.ingress.cached_replay_remaining;
assign probe_replay=new_dut.packet_decoder.synchronous.ingress.replay_bits;
assign probe_size=new_dut.packet_decoder.synchronous.ingress.sizes[new_dut.packet_decoder.synchronous.ingress.band];
assign probe_replay_word=new_dut.packet_decoder.synchronous.ingress.replay_word;
assign probe_ctx_bits=new_dut.packet_decoder.synchronous.ingress.ctx_bits;
assign probe_ctx_last=new_dut.packet_decoder.synchronous.ingress.ctx_last;
assign probe_mode16=new_dut.packet_decoder.synchronous.ingress.mode16;
assign probe_state=new_dut.packet_decoder.synchronous.ingress.state;
assign probe_count_cycles=new_dut.packet_decoder.synchronous.ingress.count_cycles;
assign probe_count_inputs=new_dut.packet_decoder.synchronous.ingress.count_inputs;
assign probe_count_outputs=new_dut.packet_decoder.synchronous.ingress.count_outputs;
assign probe_count_stall=new_dut.packet_decoder.synchronous.ingress.count_output_stall;
assign probe_ingress_in_valid=new_dut.packet_decoder.synchronous.ingress.in_valid;
assign probe_ingress_in_ready=new_dut.packet_decoder.synchronous.ingress.in_ready;
assign probe_ingress_out_valid=new_dut.packet_decoder.synchronous.ingress.out_valid;
assign probe_ingress_out_ready=new_dut.packet_decoder.synchronous.ingress.out_ready;
assign probe_cache_update=(!new_dut.packet_decoder.synchronous.ingress.cancelled && new_dut.packet_decoder.synchronous.ingress.state!=0 && new_dut.packet_decoder.synchronous.ingress.state!=7 && new_dut.packet_decoder.synchronous.ingress.state!=8 && !(new_dut.packet_decoder.synchronous.ingress.context_active && (new_dut.packet_decoder.synchronous.ingress.ctx_error!=0 || new_dut.packet_decoder.synchronous.ingress.ctx_done))) && new_dut.packet_decoder.synchronous.ingress.state==5 && new_dut.packet_decoder.synchronous.ingress.ctx_valid && new_dut.packet_decoder.synchronous.ingress.ctx_ready;
assign probe_cache_init=(!new_dut.packet_decoder.synchronous.ingress.cancelled && new_dut.packet_decoder.synchronous.ingress.state!=0 && new_dut.packet_decoder.synchronous.ingress.state!=7 && new_dut.packet_decoder.synchronous.ingress.state!=8 && !(new_dut.packet_decoder.synchronous.ingress.context_active && (new_dut.packet_decoder.synchronous.ingress.ctx_error!=0 || new_dut.packet_decoder.synchronous.ingress.ctx_done))) && new_dut.packet_decoder.synchronous.ingress.state==4;
always_ff @(posedge clk) if(!new_dut.packet_decoder.synchronous.ingress.cancelled) begin if(new_dut.packet_decoder.synchronous.ingress.state!=5) assert(!new_dut.packet_decoder.synchronous.ingress.ctx_valid && !new_dut.packet_decoder.synchronous.ingress.stage_word_valid); end
endmodule
