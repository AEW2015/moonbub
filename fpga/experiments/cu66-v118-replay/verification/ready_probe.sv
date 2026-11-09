// V91i2b bounded refill overlap; compile-time mode 0 retains V91i2a scheduling.
module ready_probe #(parameter integer REFILL_OVERLAP=1) (
    input logic clk, reset, start, abort_packet,
    input logic reconstruct_lookup_req,
    input logic [12:0] reconstruct_lookup_tile,
    input logic [10:0] reconstruct_lookup_cell,
    output logic reconstruct_lookup_ready, reconstruct_lookup_rsp,
    output logic [1:0] reconstruct_lookup_mode, reconstruct_lookup_scale,
    output logic admitted_ready, admitted_key,
    output logic [31:0] admitted_fid,
    output logic [63:0] admitted_generation,
    output logic start_ready,
    input logic cache_valid, cache_last,
    output logic cache_ready, cache_complete,
    input logic [1:0] cache_data,
    input logic [31:0] cache_ref_fid,
    input logic [63:0] cache_ref_generation,
    output logic [7:0] cache_error,
    input logic accepted_ref_valid, accepted_qcache_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    output logic [1:0] out_plane,
    output logic [12:0] out_tile,
    output logic [10:0] out_qcell,
    output logic [1:0] out_qscale,
    output logic [7:0] frame_state,
    output logic [31:0] frame_fid,
    output logic [31:0] core_starts, refill_bytes, blocked_starts,
    output logic [31:0] current_child_epoch,
    output logic [63:0] admission_reads,
    output logic [31:0] replay_reads,
    output logic [7:0] admission_error,
    output logic frame_read_req, frame_read_rsp,
    output logic [31:0] frame_read_addr, frame_rsp_addr, frame_rsp_epoch,
    output logic [7:0] frame_read_data,
    output logic [1:0] queue_count, queue_max_count, queue_max_owned,
    output logic queue_pending, queue_active, queue_push, queue_pop, queue_stall,
    output logic [31:0] queue_requests, queue_responses, queue_pops, queue_stalls,
    output logic [31:0] queue_cancel_queued, queue_cancel_pending,

    input logic [31:0] packet_bytes, epoch,
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
    // Same-edge next-status predicate, never a delayed sample of error.
    output logic fault_o,
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
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold
, output logic probe_public_equal,probe_internal_equal, output logic [10:0] probe_count, output logic [31:0] probe_cached_fid, output logic [63:0] probe_cached_generation, output logic probe_running,probe_nonzero,probe_accepted_start,probe_scale_commit, output logic [10:0] probe_scale_address, output logic [1:0] probe_scale_data, input logic [10:0] verify_scale_index, output logic [1:0] verify_scale_data, output logic probe_scale_equal);
logic old_reconstruct_lookup_ready;
logic old_reconstruct_lookup_rsp;
logic [1:0] old_reconstruct_lookup_mode;
logic [1:0] old_reconstruct_lookup_scale;
logic old_admitted_ready;
logic old_admitted_key;
logic [31:0] old_admitted_fid;
logic [63:0] old_admitted_generation;
logic old_start_ready;
logic old_cache_ready;
logic old_cache_complete;
logic [7:0] old_cache_error;
logic [1:0] old_out_plane;
logic [12:0] old_out_tile;
logic [10:0] old_out_qcell;
logic [1:0] old_out_qscale;
logic [7:0] old_frame_state;
logic [31:0] old_frame_fid;
logic [31:0] old_core_starts;
logic [31:0] old_refill_bytes;
logic [31:0] old_blocked_starts;
logic [31:0] old_current_child_epoch;
logic [63:0] old_admission_reads;
logic [31:0] old_replay_reads;
logic [7:0] old_admission_error;
logic old_frame_read_req;
logic old_frame_read_rsp;
logic [31:0] old_frame_read_addr;
logic [31:0] old_frame_rsp_addr;
logic [31:0] old_frame_rsp_epoch;
logic [7:0] old_frame_read_data;
logic [1:0] old_queue_count;
logic [1:0] old_queue_max_count;
logic [1:0] old_queue_max_owned;
logic old_queue_pending;
logic old_queue_active;
logic old_queue_push;
logic old_queue_pop;
logic old_queue_stall;
logic [31:0] old_queue_requests;
logic [31:0] old_queue_responses;
logic [31:0] old_queue_pops;
logic [31:0] old_queue_stalls;
logic [31:0] old_queue_cancel_queued;
logic [31:0] old_queue_cancel_pending;
logic old_in_ready;
logic old_out_valid;
logic [15:0] old_out_block;
logic [5:0] old_out_index;
logic signed [15:0] old_out_value;
logic [31:0] old_out_epoch;
logic old_done;
logic [7:0] old_error;
logic old_fault_o;
logic old_busy;
logic old_draining;
logic old_scratch_sealed;
logic [18:0] old_used_bytes;
logic [63:0] old_count_cycles;
logic [63:0] old_count_input_bytes;
logic [63:0] old_count_dense;
logic [63:0] old_count_reads;
logic [63:0] old_count_writes;
logic [63:0] old_count_dense_stall;
logic old_mem_req_valid;
logic old_mem_req_write;
logic [17:0] old_mem_req_addr;
logic [127:0] old_mem_req_data;
logic [31:0] old_mem_req_epoch;
logic old_mem_rsp_ready;
logic [3:0] old_packet_state;
logic old_metadata_wait;
logic old_dbg_running;
logic old_dbg_allocation;
logic old_dbg_seal_sent;
logic old_dbg_packet_done;
logic old_dbg_coef_valid;
logic old_dbg_coef_ready;
logic [1:0] old_dbg_coef_band;
logic [15:0] old_dbg_coef_block;
logic [5:0] old_dbg_coef_index;
logic signed [15:0] old_dbg_coef_value;
logic [31:0] old_dbg_coef_epoch;
logic old_dbg_meta_valid;
logic old_dbg_meta_ready;
logic old_dbg_meta_raw;
logic old_dbg_band_end_valid;
logic old_dbg_band_end_ready;
logic [1:0] old_dbg_band_end_band;
logic old_dbg_seal_valid;
logic old_dbg_seal_ready;
logic [4:0] old_dbg_scratch_state;
logic [4:0] old_dbg_scratch_return_state;
logic old_dbg_scratch_outstanding;
logic old_dbg_prefetch_offer;
logic old_dbg_prefetch_launch;
logic old_dbg_prefetch_use;
logic old_dbg_tile_mode;
logic old_dbg_tile_preparing;
logic old_dbg_prepare_bank;
logic old_dbg_emit_bank;
logic [1:0] old_dbg_bank_ready;
logic [1:0] old_dbg_bank_owned;
logic [1:0] old_dbg_emitter_state;
logic [15:0] old_dbg_prepare_block;
logic [15:0] old_dbg_bank_block [0:1];
logic [31:0] old_dbg_bank_epoch [0:1];
logic old_dbg_tile_prepare_start;
logic old_dbg_tile_publish;
logic old_dbg_tile_release;
logic [63:0] old_count_emitter_state [0:3];
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
logic old_max_prefetch_offer;
logic old_dbg_write_slot_valid;
logic old_dbg_assembler_full;
logic old_dbg_write_enqueue;
logic [63:0] old_count_write_enqueues;
logic [63:0] old_count_write_accepts;
logic [63:0] old_count_write_acks;
logic [63:0] old_count_full_wait;
logic [63:0] old_count_packing_during_write_pending;
logic old_max_write_slot;
logic [1:0] old_max_owned_lines;
logic [2:0] old_dbg_scratch_phase;
logic [4:0] old_dbg_scratch_assembly_bytes;
logic [3:0] old_dbg_scratch_cache_valid;
logic [2:0] old_dbg_scratch_head_valid;
logic [63:0] old_count_packet_state [0:15];
logic [63:0] old_count_scratch_state [0:31];
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
logic [63:0] old_ts_first_coef_band [0:3];
logic [63:0] old_ts_last_coef_band [0:3];
logic [63:0] old_ts_band_end [0:3];
logic [4:0] old_max_assembly_bytes;
logic [2:0] old_max_cache_valid;
logic [2:0] old_max_head_valid;
logic old_max_outstanding;
logic old_stage_read_req;
logic old_stage_read_rsp;
logic old_stage_write;
logic old_stage_pending;
logic old_stage_context_active;
logic old_stage_cancel;
logic old_stage_word_valid;
logic old_stage_word_ready;
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
ready_original #(.REFILL_OVERLAP(REFILL_OVERLAP)) old_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.reconstruct_lookup_req(reconstruct_lookup_req),.reconstruct_lookup_tile(reconstruct_lookup_tile),.reconstruct_lookup_cell(reconstruct_lookup_cell),.reconstruct_lookup_ready(old_reconstruct_lookup_ready),.reconstruct_lookup_rsp(old_reconstruct_lookup_rsp),.reconstruct_lookup_mode(old_reconstruct_lookup_mode),.reconstruct_lookup_scale(old_reconstruct_lookup_scale),.admitted_ready(old_admitted_ready),.admitted_key(old_admitted_key),.admitted_fid(old_admitted_fid),.admitted_generation(old_admitted_generation),.start_ready(old_start_ready),.cache_valid(cache_valid),.cache_last(cache_last),.cache_ready(old_cache_ready),.cache_complete(old_cache_complete),.cache_data(cache_data),.cache_ref_fid(cache_ref_fid),.cache_ref_generation(cache_ref_generation),.cache_error(old_cache_error),.accepted_ref_valid(accepted_ref_valid),.accepted_qcache_valid(accepted_qcache_valid),.accepted_ref_fid(accepted_ref_fid),.accepted_ref_generation(accepted_ref_generation),.out_plane(old_out_plane),.out_tile(old_out_tile),.out_qcell(old_out_qcell),.out_qscale(old_out_qscale),.frame_state(old_frame_state),.frame_fid(old_frame_fid),.core_starts(old_core_starts),.refill_bytes(old_refill_bytes),.blocked_starts(old_blocked_starts),.current_child_epoch(old_current_child_epoch),.admission_reads(old_admission_reads),.replay_reads(old_replay_reads),.admission_error(old_admission_error),.frame_read_req(old_frame_read_req),.frame_read_rsp(old_frame_read_rsp),.frame_read_addr(old_frame_read_addr),.frame_rsp_addr(old_frame_rsp_addr),.frame_rsp_epoch(old_frame_rsp_epoch),.frame_read_data(old_frame_read_data),.queue_count(old_queue_count),.queue_max_count(old_queue_max_count),.queue_max_owned(old_queue_max_owned),.queue_pending(old_queue_pending),.queue_active(old_queue_active),.queue_push(old_queue_push),.queue_pop(old_queue_pop),.queue_stall(old_queue_stall),.queue_requests(old_queue_requests),.queue_responses(old_queue_responses),.queue_pops(old_queue_pops),.queue_stalls(old_queue_stalls),.queue_cancel_queued(old_queue_cancel_queued),.queue_cancel_pending(old_queue_cancel_pending),.packet_bytes(packet_bytes),.epoch(epoch),.serial_clear(serial_clear),.write_overlap(write_overlap),.read_prefetch(read_prefetch),.tile_overlap(tile_overlap),.in_valid(in_valid),.in_ready(old_in_ready),.in_data(in_data),.in_last(in_last),.out_valid(old_out_valid),.out_ready(out_ready),.out_block(old_out_block),.out_index(old_out_index),.out_value(old_out_value),.out_epoch(old_out_epoch),.done(old_done),.error(old_error),.fault_o(old_fault_o),.busy(old_busy),.draining(old_draining),.scratch_sealed(old_scratch_sealed),.used_bytes(old_used_bytes),.count_cycles(old_count_cycles),.count_input_bytes(old_count_input_bytes),.count_dense(old_count_dense),.count_reads(old_count_reads),.count_writes(old_count_writes),.count_dense_stall(old_count_dense_stall),.mem_req_valid(old_mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(old_mem_req_write),.mem_req_addr(old_mem_req_addr),.mem_req_data(old_mem_req_data),.mem_req_epoch(old_mem_req_epoch),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(old_mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_error(mem_rsp_error),.packet_state(old_packet_state),.metadata_wait(old_metadata_wait),.dbg_running(old_dbg_running),.dbg_allocation(old_dbg_allocation),.dbg_seal_sent(old_dbg_seal_sent),.dbg_packet_done(old_dbg_packet_done),.dbg_coef_valid(old_dbg_coef_valid),.dbg_coef_ready(old_dbg_coef_ready),.dbg_coef_band(old_dbg_coef_band),.dbg_coef_block(old_dbg_coef_block),.dbg_coef_index(old_dbg_coef_index),.dbg_coef_value(old_dbg_coef_value),.dbg_coef_epoch(old_dbg_coef_epoch),.dbg_meta_valid(old_dbg_meta_valid),.dbg_meta_ready(old_dbg_meta_ready),.dbg_meta_raw(old_dbg_meta_raw),.dbg_band_end_valid(old_dbg_band_end_valid),.dbg_band_end_ready(old_dbg_band_end_ready),.dbg_band_end_band(old_dbg_band_end_band),.dbg_seal_valid(old_dbg_seal_valid),.dbg_seal_ready(old_dbg_seal_ready),.dbg_scratch_state(old_dbg_scratch_state),.dbg_scratch_return_state(old_dbg_scratch_return_state),.dbg_scratch_outstanding(old_dbg_scratch_outstanding),.dbg_prefetch_offer(old_dbg_prefetch_offer),.dbg_prefetch_launch(old_dbg_prefetch_launch),.dbg_prefetch_use(old_dbg_prefetch_use),.dbg_tile_mode(old_dbg_tile_mode),.dbg_tile_preparing(old_dbg_tile_preparing),.dbg_prepare_bank(old_dbg_prepare_bank),.dbg_emit_bank(old_dbg_emit_bank),.dbg_bank_ready(old_dbg_bank_ready),.dbg_bank_owned(old_dbg_bank_owned),.dbg_emitter_state(old_dbg_emitter_state),.dbg_prepare_block(old_dbg_prepare_block),.dbg_bank_block(old_dbg_bank_block),.dbg_bank_epoch(old_dbg_bank_epoch),.dbg_tile_prepare_start(old_dbg_tile_prepare_start),.dbg_tile_publish(old_dbg_tile_publish),.dbg_tile_release(old_dbg_tile_release),.count_emitter_state(old_count_emitter_state),.count_tile_starts(old_count_tile_starts),.count_tile_publishes(old_count_tile_publishes),.count_tile_releases(old_count_tile_releases),.count_prepare_output_overlap(old_count_prepare_output_overlap),.count_prepare_output_hold(old_count_prepare_output_hold),.count_tile_read_output_overlap(old_count_tile_read_output_overlap),.count_tile_bank_wait(old_count_tile_bank_wait),.count_both_ready_wait(old_count_both_ready_wait),.count_tile_prep_done_wait(old_count_tile_prep_done_wait),.count_output_valid(old_count_output_valid),.count_publish_release_same_edge(old_count_publish_release_same_edge),.max_tile_owned(old_max_tile_owned),.max_tile_ready(old_max_tile_ready),.count_prefetch_offers(old_count_prefetch_offers),.count_prefetch_accepts(old_count_prefetch_accepts),.count_prefetch_acks(old_count_prefetch_acks),.count_prefetch_uses(old_count_prefetch_uses),.count_dense_during_read_pending(old_count_dense_during_read_pending),.count_prefetch_drain_wait(old_count_prefetch_drain_wait),.max_prefetch_offer(old_max_prefetch_offer),.dbg_write_slot_valid(old_dbg_write_slot_valid),.dbg_assembler_full(old_dbg_assembler_full),.dbg_write_enqueue(old_dbg_write_enqueue),.count_write_enqueues(old_count_write_enqueues),.count_write_accepts(old_count_write_accepts),.count_write_acks(old_count_write_acks),.count_full_wait(old_count_full_wait),.count_packing_during_write_pending(old_count_packing_during_write_pending),.max_write_slot(old_max_write_slot),.max_owned_lines(old_max_owned_lines),.dbg_scratch_phase(old_dbg_scratch_phase),.dbg_scratch_assembly_bytes(old_dbg_scratch_assembly_bytes),.dbg_scratch_cache_valid(old_dbg_scratch_cache_valid),.dbg_scratch_head_valid(old_dbg_scratch_head_valid),.count_packet_state(old_count_packet_state),.count_scratch_state(old_count_scratch_state),.count_coef_stall(old_count_coef_stall),.count_metadata_wait(old_count_metadata_wait),.count_band_end_stall(old_count_band_end_stall),.count_mem_req_stall(old_count_mem_req_stall),.count_mem_pending(old_count_mem_pending),.count_input_starved(old_count_input_starved),.ts_first_input(old_ts_first_input),.ts_last_input(old_ts_last_input),.ts_metadata_accept(old_ts_metadata_accept),.ts_last_sparse_coef(old_ts_last_sparse_coef),.ts_packet_done_observed(old_ts_packet_done_observed),.ts_seal_accepted(old_ts_seal_accepted),.ts_scratch_sealed_observed(old_ts_scratch_sealed_observed),.ts_first_dense(old_ts_first_dense),.ts_last_dense(old_ts_last_dense),.ts_integrated_done(old_ts_integrated_done),.ts_first_coef_band(old_ts_first_coef_band),.ts_last_coef_band(old_ts_last_coef_band),.ts_band_end(old_ts_band_end),.max_assembly_bytes(old_max_assembly_bytes),.max_cache_valid(old_max_cache_valid),.max_head_valid(old_max_head_valid),.max_outstanding(old_max_outstanding),.stage_read_req(old_stage_read_req),.stage_read_rsp(old_stage_read_rsp),.stage_write(old_stage_write),.stage_pending(old_stage_pending),.stage_context_active(old_stage_context_active),.stage_cancel(old_stage_cancel),.stage_word_valid(old_stage_word_valid),.stage_word_ready(old_stage_word_ready),.stage_read_addr(old_stage_read_addr),.stage_rsp_addr(old_stage_rsp_addr),.stage_write_addr(old_stage_write_addr),.stage_req_epoch(old_stage_req_epoch),.stage_rsp_epoch(old_stage_rsp_epoch),.stage_read_data(old_stage_read_data),.stage_write_data(old_stage_write_data),.stage_buffer_bytes(old_stage_buffer_bytes),.stage_buffer_highwater(old_stage_buffer_highwater),.stage_purpose(old_stage_purpose),.count_stage_reads(old_count_stage_reads),.count_stage_responses(old_count_stage_responses),.count_stage_writes(old_count_stage_writes),.count_stage_fetch_wait(old_count_stage_fetch_wait),.count_stage_word_hold(old_count_stage_word_hold));
ready_candidate #(.REFILL_OVERLAP(REFILL_OVERLAP)) new_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.reconstruct_lookup_req(reconstruct_lookup_req),.reconstruct_lookup_tile(reconstruct_lookup_tile),.reconstruct_lookup_cell(reconstruct_lookup_cell),.reconstruct_lookup_ready(reconstruct_lookup_ready),.reconstruct_lookup_rsp(reconstruct_lookup_rsp),.reconstruct_lookup_mode(reconstruct_lookup_mode),.reconstruct_lookup_scale(reconstruct_lookup_scale),.admitted_ready(admitted_ready),.admitted_key(admitted_key),.admitted_fid(admitted_fid),.admitted_generation(admitted_generation),.start_ready(start_ready),.cache_valid(cache_valid),.cache_last(cache_last),.cache_ready(cache_ready),.cache_complete(cache_complete),.cache_data(cache_data),.cache_ref_fid(cache_ref_fid),.cache_ref_generation(cache_ref_generation),.cache_error(cache_error),.accepted_ref_valid(accepted_ref_valid),.accepted_qcache_valid(accepted_qcache_valid),.accepted_ref_fid(accepted_ref_fid),.accepted_ref_generation(accepted_ref_generation),.out_plane(out_plane),.out_tile(out_tile),.out_qcell(out_qcell),.out_qscale(out_qscale),.frame_state(frame_state),.frame_fid(frame_fid),.core_starts(core_starts),.refill_bytes(refill_bytes),.blocked_starts(blocked_starts),.current_child_epoch(current_child_epoch),.admission_reads(admission_reads),.replay_reads(replay_reads),.admission_error(admission_error),.frame_read_req(frame_read_req),.frame_read_rsp(frame_read_rsp),.frame_read_addr(frame_read_addr),.frame_rsp_addr(frame_rsp_addr),.frame_rsp_epoch(frame_rsp_epoch),.frame_read_data(frame_read_data),.queue_count(queue_count),.queue_max_count(queue_max_count),.queue_max_owned(queue_max_owned),.queue_pending(queue_pending),.queue_active(queue_active),.queue_push(queue_push),.queue_pop(queue_pop),.queue_stall(queue_stall),.queue_requests(queue_requests),.queue_responses(queue_responses),.queue_pops(queue_pops),.queue_stalls(queue_stalls),.queue_cancel_queued(queue_cancel_queued),.queue_cancel_pending(queue_cancel_pending),.packet_bytes(packet_bytes),.epoch(epoch),.serial_clear(serial_clear),.write_overlap(write_overlap),.read_prefetch(read_prefetch),.tile_overlap(tile_overlap),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),.out_valid(out_valid),.out_ready(out_ready),.out_block(out_block),.out_index(out_index),.out_value(out_value),.out_epoch(out_epoch),.done(done),.error(error),.fault_o(fault_o),.busy(busy),.draining(draining),.scratch_sealed(scratch_sealed),.used_bytes(used_bytes),.count_cycles(count_cycles),.count_input_bytes(count_input_bytes),.count_dense(count_dense),.count_reads(count_reads),.count_writes(count_writes),.count_dense_stall(count_dense_stall),.mem_req_valid(mem_req_valid),.mem_req_ready(mem_req_ready),.mem_req_write(mem_req_write),.mem_req_addr(mem_req_addr),.mem_req_data(mem_req_data),.mem_req_epoch(mem_req_epoch),.mem_rsp_valid(mem_rsp_valid),.mem_rsp_ready(mem_rsp_ready),.mem_rsp_data(mem_rsp_data),.mem_rsp_epoch(mem_rsp_epoch),.mem_rsp_error(mem_rsp_error),.packet_state(packet_state),.metadata_wait(metadata_wait),.dbg_running(dbg_running),.dbg_allocation(dbg_allocation),.dbg_seal_sent(dbg_seal_sent),.dbg_packet_done(dbg_packet_done),.dbg_coef_valid(dbg_coef_valid),.dbg_coef_ready(dbg_coef_ready),.dbg_coef_band(dbg_coef_band),.dbg_coef_block(dbg_coef_block),.dbg_coef_index(dbg_coef_index),.dbg_coef_value(dbg_coef_value),.dbg_coef_epoch(dbg_coef_epoch),.dbg_meta_valid(dbg_meta_valid),.dbg_meta_ready(dbg_meta_ready),.dbg_meta_raw(dbg_meta_raw),.dbg_band_end_valid(dbg_band_end_valid),.dbg_band_end_ready(dbg_band_end_ready),.dbg_band_end_band(dbg_band_end_band),.dbg_seal_valid(dbg_seal_valid),.dbg_seal_ready(dbg_seal_ready),.dbg_scratch_state(dbg_scratch_state),.dbg_scratch_return_state(dbg_scratch_return_state),.dbg_scratch_outstanding(dbg_scratch_outstanding),.dbg_prefetch_offer(dbg_prefetch_offer),.dbg_prefetch_launch(dbg_prefetch_launch),.dbg_prefetch_use(dbg_prefetch_use),.dbg_tile_mode(dbg_tile_mode),.dbg_tile_preparing(dbg_tile_preparing),.dbg_prepare_bank(dbg_prepare_bank),.dbg_emit_bank(dbg_emit_bank),.dbg_bank_ready(dbg_bank_ready),.dbg_bank_owned(dbg_bank_owned),.dbg_emitter_state(dbg_emitter_state),.dbg_prepare_block(dbg_prepare_block),.dbg_bank_block(dbg_bank_block),.dbg_bank_epoch(dbg_bank_epoch),.dbg_tile_prepare_start(dbg_tile_prepare_start),.dbg_tile_publish(dbg_tile_publish),.dbg_tile_release(dbg_tile_release),.count_emitter_state(count_emitter_state),.count_tile_starts(count_tile_starts),.count_tile_publishes(count_tile_publishes),.count_tile_releases(count_tile_releases),.count_prepare_output_overlap(count_prepare_output_overlap),.count_prepare_output_hold(count_prepare_output_hold),.count_tile_read_output_overlap(count_tile_read_output_overlap),.count_tile_bank_wait(count_tile_bank_wait),.count_both_ready_wait(count_both_ready_wait),.count_tile_prep_done_wait(count_tile_prep_done_wait),.count_output_valid(count_output_valid),.count_publish_release_same_edge(count_publish_release_same_edge),.max_tile_owned(max_tile_owned),.max_tile_ready(max_tile_ready),.count_prefetch_offers(count_prefetch_offers),.count_prefetch_accepts(count_prefetch_accepts),.count_prefetch_acks(count_prefetch_acks),.count_prefetch_uses(count_prefetch_uses),.count_dense_during_read_pending(count_dense_during_read_pending),.count_prefetch_drain_wait(count_prefetch_drain_wait),.max_prefetch_offer(max_prefetch_offer),.dbg_write_slot_valid(dbg_write_slot_valid),.dbg_assembler_full(dbg_assembler_full),.dbg_write_enqueue(dbg_write_enqueue),.count_write_enqueues(count_write_enqueues),.count_write_accepts(count_write_accepts),.count_write_acks(count_write_acks),.count_full_wait(count_full_wait),.count_packing_during_write_pending(count_packing_during_write_pending),.max_write_slot(max_write_slot),.max_owned_lines(max_owned_lines),.dbg_scratch_phase(dbg_scratch_phase),.dbg_scratch_assembly_bytes(dbg_scratch_assembly_bytes),.dbg_scratch_cache_valid(dbg_scratch_cache_valid),.dbg_scratch_head_valid(dbg_scratch_head_valid),.count_packet_state(count_packet_state),.count_scratch_state(count_scratch_state),.count_coef_stall(count_coef_stall),.count_metadata_wait(count_metadata_wait),.count_band_end_stall(count_band_end_stall),.count_mem_req_stall(count_mem_req_stall),.count_mem_pending(count_mem_pending),.count_input_starved(count_input_starved),.ts_first_input(ts_first_input),.ts_last_input(ts_last_input),.ts_metadata_accept(ts_metadata_accept),.ts_last_sparse_coef(ts_last_sparse_coef),.ts_packet_done_observed(ts_packet_done_observed),.ts_seal_accepted(ts_seal_accepted),.ts_scratch_sealed_observed(ts_scratch_sealed_observed),.ts_first_dense(ts_first_dense),.ts_last_dense(ts_last_dense),.ts_integrated_done(ts_integrated_done),.ts_first_coef_band(ts_first_coef_band),.ts_last_coef_band(ts_last_coef_band),.ts_band_end(ts_band_end),.max_assembly_bytes(max_assembly_bytes),.max_cache_valid(max_cache_valid),.max_head_valid(max_head_valid),.max_outstanding(max_outstanding),.stage_read_req(stage_read_req),.stage_read_rsp(stage_read_rsp),.stage_write(stage_write),.stage_pending(stage_pending),.stage_context_active(stage_context_active),.stage_cancel(stage_cancel),.stage_word_valid(stage_word_valid),.stage_word_ready(stage_word_ready),.stage_read_addr(stage_read_addr),.stage_rsp_addr(stage_rsp_addr),.stage_write_addr(stage_write_addr),.stage_req_epoch(stage_req_epoch),.stage_rsp_epoch(stage_rsp_epoch),.stage_read_data(stage_read_data),.stage_write_data(stage_write_data),.stage_buffer_bytes(stage_buffer_bytes),.stage_buffer_highwater(stage_buffer_highwater),.stage_purpose(stage_purpose),.count_stage_reads(count_stage_reads),.count_stage_responses(count_stage_responses),.count_stage_writes(count_stage_writes),.count_stage_fetch_wait(count_stage_fetch_wait),.count_stage_word_hold(count_stage_word_hold));
assign probe_public_equal=(old_reconstruct_lookup_ready==reconstruct_lookup_ready)&&(old_reconstruct_lookup_rsp==reconstruct_lookup_rsp)&&(old_reconstruct_lookup_mode==reconstruct_lookup_mode)&&(old_reconstruct_lookup_scale==reconstruct_lookup_scale)&&(old_admitted_ready==admitted_ready)&&(old_admitted_key==admitted_key)&&(old_admitted_fid==admitted_fid)&&(old_admitted_generation==admitted_generation)&&(old_start_ready==start_ready)&&(old_cache_ready==cache_ready)&&(old_cache_complete==cache_complete)&&(old_cache_error==cache_error)&&(old_out_plane==out_plane)&&(old_out_tile==out_tile)&&(old_out_qcell==out_qcell)&&(old_out_qscale==out_qscale)&&(old_frame_state==frame_state)&&(old_frame_fid==frame_fid)&&(old_core_starts==core_starts)&&(old_refill_bytes==refill_bytes)&&(old_blocked_starts==blocked_starts)&&(old_current_child_epoch==current_child_epoch)&&(old_admission_reads==admission_reads)&&(old_replay_reads==replay_reads)&&(old_admission_error==admission_error)&&(old_frame_read_req==frame_read_req)&&(old_frame_read_rsp==frame_read_rsp)&&(old_frame_read_addr==frame_read_addr)&&(old_frame_rsp_addr==frame_rsp_addr)&&(old_frame_rsp_epoch==frame_rsp_epoch)&&(old_frame_read_data==frame_read_data)&&(old_queue_count==queue_count)&&(old_queue_max_count==queue_max_count)&&(old_queue_max_owned==queue_max_owned)&&(old_queue_pending==queue_pending)&&(old_queue_active==queue_active)&&(old_queue_push==queue_push)&&(old_queue_pop==queue_pop)&&(old_queue_stall==queue_stall)&&(old_queue_requests==queue_requests)&&(old_queue_responses==queue_responses)&&(old_queue_pops==queue_pops)&&(old_queue_stalls==queue_stalls)&&(old_queue_cancel_queued==queue_cancel_queued)&&(old_queue_cancel_pending==queue_cancel_pending)&&(old_in_ready==in_ready)&&(old_out_valid==out_valid)&&(old_out_block==out_block)&&(old_out_index==out_index)&&(old_out_value==out_value)&&(old_out_epoch==out_epoch)&&(old_done==done)&&(old_error==error)&&(old_fault_o==fault_o)&&(old_busy==busy)&&(old_draining==draining)&&(old_scratch_sealed==scratch_sealed)&&(old_used_bytes==used_bytes)&&(old_count_cycles==count_cycles)&&(old_count_input_bytes==count_input_bytes)&&(old_count_dense==count_dense)&&(old_count_reads==count_reads)&&(old_count_writes==count_writes)&&(old_count_dense_stall==count_dense_stall)&&(old_mem_req_valid==mem_req_valid)&&(old_mem_req_write==mem_req_write)&&(old_mem_req_addr==mem_req_addr)&&(old_mem_req_data==mem_req_data)&&(old_mem_req_epoch==mem_req_epoch)&&(old_mem_rsp_ready==mem_rsp_ready)&&(old_packet_state==packet_state)&&(old_metadata_wait==metadata_wait)&&(old_dbg_running==dbg_running)&&(old_dbg_allocation==dbg_allocation)&&(old_dbg_seal_sent==dbg_seal_sent)&&(old_dbg_packet_done==dbg_packet_done)&&(old_dbg_coef_valid==dbg_coef_valid)&&(old_dbg_coef_ready==dbg_coef_ready)&&(old_dbg_coef_band==dbg_coef_band)&&(old_dbg_coef_block==dbg_coef_block)&&(old_dbg_coef_index==dbg_coef_index)&&(old_dbg_coef_value==dbg_coef_value)&&(old_dbg_coef_epoch==dbg_coef_epoch)&&(old_dbg_meta_valid==dbg_meta_valid)&&(old_dbg_meta_ready==dbg_meta_ready)&&(old_dbg_meta_raw==dbg_meta_raw)&&(old_dbg_band_end_valid==dbg_band_end_valid)&&(old_dbg_band_end_ready==dbg_band_end_ready)&&(old_dbg_band_end_band==dbg_band_end_band)&&(old_dbg_seal_valid==dbg_seal_valid)&&(old_dbg_seal_ready==dbg_seal_ready)&&(old_dbg_scratch_state==dbg_scratch_state)&&(old_dbg_scratch_return_state==dbg_scratch_return_state)&&(old_dbg_scratch_outstanding==dbg_scratch_outstanding)&&(old_dbg_prefetch_offer==dbg_prefetch_offer)&&(old_dbg_prefetch_launch==dbg_prefetch_launch)&&(old_dbg_prefetch_use==dbg_prefetch_use)&&(old_dbg_tile_mode==dbg_tile_mode)&&(old_dbg_tile_preparing==dbg_tile_preparing)&&(old_dbg_prepare_bank==dbg_prepare_bank)&&(old_dbg_emit_bank==dbg_emit_bank)&&(old_dbg_bank_ready==dbg_bank_ready)&&(old_dbg_bank_owned==dbg_bank_owned)&&(old_dbg_emitter_state==dbg_emitter_state)&&(old_dbg_prepare_block==dbg_prepare_block)&&(old_dbg_bank_block==dbg_bank_block)&&(old_dbg_bank_epoch==dbg_bank_epoch)&&(old_dbg_tile_prepare_start==dbg_tile_prepare_start)&&(old_dbg_tile_publish==dbg_tile_publish)&&(old_dbg_tile_release==dbg_tile_release)&&(old_count_emitter_state==count_emitter_state)&&(old_count_tile_starts==count_tile_starts)&&(old_count_tile_publishes==count_tile_publishes)&&(old_count_tile_releases==count_tile_releases)&&(old_count_prepare_output_overlap==count_prepare_output_overlap)&&(old_count_prepare_output_hold==count_prepare_output_hold)&&(old_count_tile_read_output_overlap==count_tile_read_output_overlap)&&(old_count_tile_bank_wait==count_tile_bank_wait)&&(old_count_both_ready_wait==count_both_ready_wait)&&(old_count_tile_prep_done_wait==count_tile_prep_done_wait)&&(old_count_output_valid==count_output_valid)&&(old_count_publish_release_same_edge==count_publish_release_same_edge)&&(old_max_tile_owned==max_tile_owned)&&(old_max_tile_ready==max_tile_ready)&&(old_count_prefetch_offers==count_prefetch_offers)&&(old_count_prefetch_accepts==count_prefetch_accepts)&&(old_count_prefetch_acks==count_prefetch_acks)&&(old_count_prefetch_uses==count_prefetch_uses)&&(old_count_dense_during_read_pending==count_dense_during_read_pending)&&(old_count_prefetch_drain_wait==count_prefetch_drain_wait)&&(old_max_prefetch_offer==max_prefetch_offer)&&(old_dbg_write_slot_valid==dbg_write_slot_valid)&&(old_dbg_assembler_full==dbg_assembler_full)&&(old_dbg_write_enqueue==dbg_write_enqueue)&&(old_count_write_enqueues==count_write_enqueues)&&(old_count_write_accepts==count_write_accepts)&&(old_count_write_acks==count_write_acks)&&(old_count_full_wait==count_full_wait)&&(old_count_packing_during_write_pending==count_packing_during_write_pending)&&(old_max_write_slot==max_write_slot)&&(old_max_owned_lines==max_owned_lines)&&(old_dbg_scratch_phase==dbg_scratch_phase)&&(old_dbg_scratch_assembly_bytes==dbg_scratch_assembly_bytes)&&(old_dbg_scratch_cache_valid==dbg_scratch_cache_valid)&&(old_dbg_scratch_head_valid==dbg_scratch_head_valid)&&(old_count_packet_state==count_packet_state)&&(old_count_scratch_state==count_scratch_state)&&(old_count_coef_stall==count_coef_stall)&&(old_count_metadata_wait==count_metadata_wait)&&(old_count_band_end_stall==count_band_end_stall)&&(old_count_mem_req_stall==count_mem_req_stall)&&(old_count_mem_pending==count_mem_pending)&&(old_count_input_starved==count_input_starved)&&(old_ts_first_input==ts_first_input)&&(old_ts_last_input==ts_last_input)&&(old_ts_metadata_accept==ts_metadata_accept)&&(old_ts_last_sparse_coef==ts_last_sparse_coef)&&(old_ts_packet_done_observed==ts_packet_done_observed)&&(old_ts_seal_accepted==ts_seal_accepted)&&(old_ts_scratch_sealed_observed==ts_scratch_sealed_observed)&&(old_ts_first_dense==ts_first_dense)&&(old_ts_last_dense==ts_last_dense)&&(old_ts_integrated_done==ts_integrated_done)&&(old_ts_first_coef_band==ts_first_coef_band)&&(old_ts_last_coef_band==ts_last_coef_band)&&(old_ts_band_end==ts_band_end)&&(old_max_assembly_bytes==max_assembly_bytes)&&(old_max_cache_valid==max_cache_valid)&&(old_max_head_valid==max_head_valid)&&(old_max_outstanding==max_outstanding)&&(old_stage_read_req==stage_read_req)&&(old_stage_read_rsp==stage_read_rsp)&&(old_stage_write==stage_write)&&(old_stage_pending==stage_pending)&&(old_stage_context_active==stage_context_active)&&(old_stage_cancel==stage_cancel)&&(old_stage_word_valid==stage_word_valid)&&(old_stage_word_ready==stage_word_ready)&&(old_stage_read_addr==stage_read_addr)&&(old_stage_rsp_addr==stage_rsp_addr)&&(old_stage_write_addr==stage_write_addr)&&(old_stage_req_epoch==stage_req_epoch)&&(old_stage_rsp_epoch==stage_rsp_epoch)&&(old_stage_read_data==stage_read_data)&&(old_stage_write_data==stage_write_data)&&(old_stage_buffer_bytes==stage_buffer_bytes)&&(old_stage_buffer_highwater==stage_buffer_highwater)&&(old_stage_purpose==stage_purpose)&&(old_count_stage_reads==count_stage_reads)&&(old_count_stage_responses==count_stage_responses)&&(old_count_stage_writes==count_stage_writes)&&(old_count_stage_fetch_wait==count_stage_fetch_wait)&&(old_count_stage_word_hold==count_stage_word_hold);
assign probe_internal_equal=(old_dut.state==new_dut.state)&&(old_dut.frame_epoch==new_dut.frame_epoch)&&(old_dut.latched_size==new_dut.latched_size)&&(old_dut.last_frame_epoch==new_dut.last_frame_epoch)&&(old_dut.child_nonce==new_dut.child_nonce)&&(old_dut.plane==new_dut.plane)&&(old_dut.tile_cursor==new_dut.tile_cursor)&&(old_dut.mapped_tile==new_dut.mapped_tile)&&(old_dut.mapped_cell==new_dut.mapped_cell)&&(old_dut.producer_cell_cache==new_dut.producer_cell_cache)&&(old_dut.mapped_scale==new_dut.mapped_scale)&&(old_dut.expected_block==new_dut.expected_block)&&(old_dut.refill_cursor==new_dut.refill_cursor)&&(old_dut.selected_offset==new_dut.selected_offset)&&(old_dut.selected_length==new_dut.selected_length)&&(old_dut.selected_blocks==new_dut.selected_blocks)&&(old_dut.refill_data==new_dut.refill_data)&&(old_dut.child_owned==new_dut.child_owned)&&(old_dut.cache_count==new_dut.cache_count)&&(old_dut.cached_fid==new_dut.cached_fid)&&(old_dut.cached_generation==new_dut.cached_generation)&&(old_dut.lookup_owner_reconstruct==new_dut.lookup_owner_reconstruct);
assign probe_count=new_dut.cache_count;
assign probe_cached_fid=new_dut.cached_fid;
assign probe_cached_generation=new_dut.cached_generation;
assign probe_running=new_dut.frame_running_owned;
assign probe_nonzero=new_dut.cache_nonzero_owned;
assign probe_accepted_start=new_dut.accepted_start;
assign probe_scale_commit=new_dut.admission.scale_store.a_commit;
assign probe_scale_address=new_dut.admission.scale_store.a_addr;
assign probe_scale_data=new_dut.admission.scale_store.a_data;
assign verify_scale_data=new_dut.admission.scale_store.words[verify_scale_index];
assign probe_scale_equal=(old_dut.admission.scale_store.words==new_dut.admission.scale_store.words);
endmodule
