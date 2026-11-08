// V91e observed coefficient pipeline: packet validation -> packed scratch -> dense tiles.
// This is not the pixel/reference/HUD/publication or physical memory controller.
module br88_pipeline_v91h #(parameter integer SYNC_STAGING=1) (
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
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold
);
    logic running, allocation, seal_sent, use_serial_clear, use_write_overlap, use_read_prefetch, use_tile_overlap;
    logic [63:0] unused_stage_reads, unused_stage_responses, unused_stage_writes,
        unused_stage_fetch_wait, unused_stage_word_hold;
    logic [5:0] unused_stage_buffer_highwater;
    logic cancelled, packet_abort, store_abort;
    logic packet_ready, packet_done;
    logic [3:0] packet_error, store_error;
    logic meta_valid, meta_ready, meta_raw;
    logic [16:0] meta_blocks;
    logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch;
    logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123;
    logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3;
    logic coef_valid, coef_ready;
    logic [1:0] coef_band;
    logic [15:0] coef_block;
    logic [5:0] coef_index;
    logic signed [15:0] coef_value;
    logic [31:0] coef_epoch;
    logic end_valid, end_ready;
    logic [1:0] end_band;
    logic [31:0] end_epoch;
    logic store_busy, store_done, seal_ready;
    logic dense_valid;
    logic [31:0] store_epoch;
    logic [63:0] packet_cycles, packet_inputs, packet_outputs, packet_stall;

    assign cancelled=reset || start || abort_packet;
    // A replacement start owns this edge. Old-owner error cancellation must
    // not defeat ingress start while the outer controller accepts the restart.
    assign packet_abort=abort_packet || (!start && running && store_error!=0);
    assign store_abort=start || abort_packet || (running && packet_error!=0);
    assign in_ready=packet_ready && running && error==0 && !cancelled;
    assign out_valid=dense_valid && running && error==0 && !cancelled;
    assign busy=running || store_busy;
    assign draining=store_busy && !running;
    assign metadata_wait=meta_valid && !meta_ready;

    assign dbg_running=running;
    assign dbg_allocation=allocation;
    assign dbg_seal_sent=seal_sent;
    assign dbg_packet_done=packet_done;
    assign dbg_coef_valid=coef_valid;
    assign dbg_coef_ready=coef_ready;
    assign dbg_coef_band=coef_band;
    assign dbg_coef_block=coef_block; assign dbg_coef_index=coef_index;
    assign dbg_coef_value=coef_value; assign dbg_coef_epoch=coef_epoch;
    assign dbg_meta_valid=meta_valid;
    assign dbg_meta_ready=meta_ready;
    assign dbg_meta_raw=meta_raw;
    assign dbg_band_end_valid=end_valid;
    assign dbg_band_end_ready=end_ready;
    assign dbg_band_end_band=end_band;
    assign dbg_seal_valid=packet_done && allocation && !seal_sent && running && error==0;
    assign dbg_seal_ready=seal_ready;

    br88_packet_ingress_v91h #(.SYNC_STAGING(SYNC_STAGING)) packet_decoder (
        .clk(clk), .reset(reset), .start(start), .abort_packet(packet_abort),
        .packet_bytes(packet_bytes), .blocks(blocks), .epoch(epoch),
        .word16(1'b0), .serial_mode(1'b0),
        .in_valid(in_valid && running && error==0), .in_ready(packet_ready),
        .in_data(in_data), .in_last(in_last),
        .out_valid(coef_valid), .out_ready(coef_ready), .out_block(coef_block),
        .out_index(coef_index), .out_coefficient(coef_value), .out_epoch(coef_epoch),
        .out_band(coef_band), .meta_valid(meta_valid), .meta_ready(meta_ready),
        .meta_blocks(meta_blocks), .meta_count1(meta_count1), .meta_count2(meta_count2),
        .meta_count3(meta_count3), .meta_epoch(meta_epoch), .meta_raw(meta_raw),
        .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),
        .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),
        .band_end_valid(end_valid), .band_end_ready(end_ready),
        .band_end_band(end_band), .band_end_epoch(end_epoch),
        .done(packet_done), .error(packet_error), .count_cycles(packet_cycles),
        .count_inputs(packet_inputs), .count_outputs(packet_outputs),
        .count_output_stall(packet_stall), .debug_state(packet_state),
        .stage_read_req(stage_read_req), .stage_read_rsp(stage_read_rsp), .stage_write(stage_write),
        .stage_pending(stage_pending), .stage_context_active(stage_context_active), .stage_cancel(stage_cancel),
        .stage_word_valid(stage_word_valid), .stage_word_ready(stage_word_ready),
        .stage_read_addr(stage_read_addr), .stage_rsp_addr(stage_rsp_addr), .stage_write_addr(stage_write_addr),
        .stage_req_epoch(stage_req_epoch), .stage_rsp_epoch(stage_rsp_epoch),
        .stage_read_data(stage_read_data), .stage_write_data(stage_write_data),
        .stage_buffer_bytes(stage_buffer_bytes), .stage_buffer_highwater(unused_stage_buffer_highwater), .stage_purpose(stage_purpose),
        .count_stage_reads(unused_stage_reads), .count_stage_responses(unused_stage_responses), .count_stage_writes(unused_stage_writes),
        .count_stage_fetch_wait(unused_stage_fetch_wait), .count_stage_word_hold(unused_stage_word_hold)
    );

    packed_scratch_v91g2 scratch (
        .clk(clk), .reset(reset),
        .begin_valid(meta_valid && running && error==0), .begin_ready(meta_ready),
        .begin_blocks(meta_blocks), .begin_raw(meta_raw),
        .begin_count1(meta_count1), .begin_count2(meta_count2), .begin_count3(meta_count3),
        .begin_prefix1(meta_prefix1),.begin_prefix12(meta_prefix12),.begin_prefix123(meta_prefix123),
        .begin_threshold1(meta_threshold1),.begin_threshold2(meta_threshold2),.begin_threshold3(meta_threshold3),
        .begin_epoch(meta_epoch), .begin_serial_clear(use_serial_clear), .begin_overlap(use_write_overlap), .begin_prefetch(use_read_prefetch), .begin_tile_overlap(use_tile_overlap),
        .coef_valid(coef_valid && running && error==0), .coef_ready(coef_ready),
        .coef_band(coef_band), .coef_block(coef_block), .coef_index(coef_index),
        .coef_value(coef_value), .coef_epoch(coef_epoch),
        .band_end_valid(end_valid && running && error==0), .band_end_ready(end_ready),
        .band_end_band(end_band), .band_end_epoch(end_epoch),
        .seal_valid(packet_done && allocation && !seal_sent && running && error==0),
        .seal_ready(seal_ready), .seal_epoch(meta_epoch),
        .abort_valid(store_abort), .abort_epoch(store_epoch),
        .busy(store_busy), .sealed(scratch_sealed), .done(store_done), .error(store_error),
        .active_epoch(store_epoch), .used_bytes(used_bytes),
        .dense_valid(dense_valid), .dense_ready(out_ready && running && error==0 && !cancelled),
        .dense_block(out_block), .dense_index(out_index), .dense_value(out_value), .dense_epoch(out_epoch),
        .mem_req_valid(mem_req_valid), .mem_req_ready(mem_req_ready), .mem_req_write(mem_req_write),
        .mem_req_addr(mem_req_addr), .mem_req_data(mem_req_data), .mem_req_epoch(mem_req_epoch),
        .mem_rsp_valid(mem_rsp_valid), .mem_rsp_ready(mem_rsp_ready), .mem_rsp_data(mem_rsp_data),
        .mem_rsp_epoch(mem_rsp_epoch), .mem_rsp_error(mem_rsp_error),
        .debug_state(dbg_scratch_state), .debug_return_state(dbg_scratch_return_state),
        .debug_outstanding(dbg_scratch_outstanding), .debug_phase(dbg_scratch_phase),
        .debug_assembly_bytes(dbg_scratch_assembly_bytes),
        .debug_tile_mode(dbg_tile_mode), .debug_tile_preparing(dbg_tile_preparing),
        .debug_prepare_bank(dbg_prepare_bank), .debug_emit_bank(dbg_emit_bank),
        .debug_bank_ready(dbg_bank_ready), .debug_bank_owned(dbg_bank_owned), .debug_emitter_state(dbg_emitter_state),
        .debug_prepare_block(dbg_prepare_block), .debug_bank_block(dbg_bank_block), .debug_bank_epoch(dbg_bank_epoch), .debug_tile_prepare_start(dbg_tile_prepare_start),
        .debug_tile_publish(dbg_tile_publish), .debug_tile_release(dbg_tile_release),
        .debug_prefetch_offer(dbg_prefetch_offer), .debug_prefetch_launch(dbg_prefetch_launch), .debug_prefetch_use(dbg_prefetch_use),
        .debug_write_slot_valid(dbg_write_slot_valid), .debug_assembler_full(dbg_assembler_full), .debug_write_enqueue(dbg_write_enqueue),
        .debug_cache_valid(dbg_scratch_cache_valid), .debug_head_valid(dbg_scratch_head_valid)
    );

    // All telemetry samples the pre-edge registered states on each running
    // edge, including the edge observing store_done. Start is excluded.
    always_ff @(posedge clk) begin
        if(reset || abort_packet || start) begin
            count_stage_reads<=0; count_stage_responses<=0; count_stage_writes<=0;
            count_stage_fetch_wait<=0; count_stage_word_hold<=0; stage_buffer_highwater<=0;
            for(integer i=0;i<16;i=i+1) count_packet_state[i]<=0;
            for(integer i=0;i<32;i=i+1) count_scratch_state[i]<=0;
            count_coef_stall<=0; count_metadata_wait<=0; count_band_end_stall<=0;
            count_mem_req_stall<=0; count_mem_pending<=0; count_input_starved<=0;
            ts_first_input<=0; ts_last_input<=0; ts_metadata_accept<=0;
            ts_last_sparse_coef<=0; ts_packet_done_observed<=0;
            ts_seal_accepted<=0; ts_scratch_sealed_observed<=0;
            ts_first_dense<=0; ts_last_dense<=0; ts_integrated_done<=0;
            for(integer i=0;i<4;i=i+1) begin
                ts_first_coef_band[i]<=0; ts_last_coef_band[i]<=0; ts_band_end[i]<=0;
            end
            max_assembly_bytes<=0; max_cache_valid<=0; max_head_valid<=0; max_outstanding<=0;
            count_write_enqueues<=0; count_write_accepts<=0; count_packing_during_write_pending<=0; count_write_acks<=0; count_full_wait<=0;
            max_write_slot<=0; max_owned_lines<=0;
            count_prefetch_offers<=0; count_prefetch_accepts<=0; count_prefetch_acks<=0;
            count_prefetch_uses<=0; count_dense_during_read_pending<=0; count_prefetch_drain_wait<=0;
            max_prefetch_offer<=0;
            for(integer i=0;i<4;i=i+1) count_emitter_state[i]<=0;
            count_tile_starts<=0; count_tile_publishes<=0; count_tile_releases<=0;
            count_prepare_output_overlap<=0; count_prepare_output_hold<=0;
            count_tile_read_output_overlap<=0; count_tile_bank_wait<=0; count_both_ready_wait<=0; count_tile_prep_done_wait<=0; count_output_valid<=0;
            count_publish_release_same_edge<=0; max_tile_owned<=0; max_tile_ready<=0;
        end else if(running) begin
            // Parent receipt scope survives an internally generated ingress
            // cancellation; only outer reset/start/abort resets these totals.
            if(!stage_cancel) begin
                if(stage_read_req) count_stage_reads<=count_stage_reads+1'b1;
                if(stage_read_rsp) count_stage_responses<=count_stage_responses+1'b1;
                if(stage_write) count_stage_writes<=count_stage_writes+1'b1;
                if(packet_state==13) count_stage_fetch_wait<=count_stage_fetch_wait+1'b1;
                if(stage_word_valid && !stage_word_ready) count_stage_word_hold<=count_stage_word_hold+1'b1;
                if(stage_buffer_bytes>stage_buffer_highwater) stage_buffer_highwater<=stage_buffer_bytes;
            end
            for(integer emitter_word=0;emitter_word<4;emitter_word=emitter_word+1)
                if(dbg_emitter_state==2'(emitter_word))count_emitter_state[emitter_word]<=count_emitter_state[emitter_word]+1'b1;
            if(dbg_tile_prepare_start) count_tile_starts<=count_tile_starts+1'b1;
            if(dbg_tile_publish) count_tile_publishes<=count_tile_publishes+1'b1;
            if(dbg_tile_release) count_tile_releases<=count_tile_releases+1'b1;
            if(dbg_tile_preparing && out_valid && out_ready) count_prepare_output_overlap<=count_prepare_output_overlap+1'b1;
            if(dbg_tile_preparing && out_valid && !out_ready) count_prepare_output_hold<=count_prepare_output_hold+1'b1;
            if(dbg_tile_mode && dbg_scratch_outstanding && !mem_req_write && out_valid && out_ready)
                count_tile_read_output_overlap<=count_tile_read_output_overlap+1'b1;
            if(out_valid) count_output_valid<=count_output_valid+1'b1;
            if(dbg_tile_mode && dbg_scratch_state==29) count_tile_prep_done_wait<=count_tile_prep_done_wait+1'b1;
            if(dbg_tile_mode && dbg_scratch_state==28) count_tile_bank_wait<=count_tile_bank_wait+1'b1;
            if(dbg_tile_mode && dbg_scratch_state==28 && dbg_bank_ready==2'b11) count_both_ready_wait<=count_both_ready_wait+1'b1;
            if(dbg_tile_publish && dbg_tile_release) count_publish_release_same_edge<=count_publish_release_same_edge+1'b1;
            if(2'($countones(dbg_bank_owned))>max_tile_owned) max_tile_owned<=2'($countones(dbg_bank_owned));
            if(2'($countones(dbg_bank_ready))>max_tile_ready) max_tile_ready<=2'($countones(dbg_bank_ready));
            for(integer packet_word=0;packet_word<16;packet_word=packet_word+1)
                if(packet_state==4'(packet_word))count_packet_state[packet_word]<=count_packet_state[packet_word]+1'b1;
            for(integer scratch_word=0;scratch_word<32;scratch_word=scratch_word+1)
                if(dbg_scratch_state==5'(scratch_word))count_scratch_state[scratch_word]<=count_scratch_state[scratch_word]+1'b1;
            if(coef_valid && !coef_ready) count_coef_stall<=count_coef_stall+1'b1;
            if(meta_valid && !meta_ready) count_metadata_wait<=count_metadata_wait+1'b1;
            if(end_valid && !end_ready) count_band_end_stall<=count_band_end_stall+1'b1;
            if(mem_req_valid && !mem_req_ready) count_mem_req_stall<=count_mem_req_stall+1'b1;
            if(dbg_scratch_outstanding) count_mem_pending<=count_mem_pending+1'b1;
            if(in_ready && !in_valid) count_input_starved<=count_input_starved+1'b1;
            if(in_valid && in_ready) begin
                if(ts_first_input==0) ts_first_input<=count_cycles+1'b1;
                ts_last_input<=count_cycles+1'b1;
            end
            if(meta_valid && meta_ready) ts_metadata_accept<=count_cycles+1'b1;
            if(coef_valid && coef_ready) begin
                ts_last_sparse_coef<=count_cycles+1'b1;
                if(ts_first_coef_band[coef_band]==0) ts_first_coef_band[coef_band]<=count_cycles+1'b1;
                ts_last_coef_band[coef_band]<=count_cycles+1'b1;
            end
            if(end_valid && end_ready) ts_band_end[end_band]<=count_cycles+1'b1;
            if(dbg_scratch_assembly_bytes>max_assembly_bytes) max_assembly_bytes<=dbg_scratch_assembly_bytes;
            if(3'($countones(dbg_scratch_cache_valid))>max_cache_valid) max_cache_valid<=3'($countones(dbg_scratch_cache_valid));
            if(3'($countones(dbg_scratch_head_valid))>max_head_valid) max_head_valid<=3'($countones(dbg_scratch_head_valid));
            if(dbg_scratch_outstanding) max_outstanding<=1;
            if(dbg_write_slot_valid) max_write_slot<=1;
            if(2'(dbg_write_slot_valid)+2'(dbg_scratch_assembly_bytes!=0)>max_owned_lines)
                max_owned_lines<=2'(dbg_write_slot_valid)+2'(dbg_scratch_assembly_bytes!=0);
            if(dbg_prefetch_offer) max_prefetch_offer<=1;
            if(dbg_prefetch_launch) count_prefetch_offers<=count_prefetch_offers+1'b1;
            if(dbg_prefetch_offer && mem_req_valid && mem_req_ready) count_prefetch_accepts<=count_prefetch_accepts+1'b1;
            if(dbg_prefetch_offer && dbg_scratch_outstanding && mem_rsp_valid && mem_rsp_epoch==store_epoch && !mem_rsp_error)
                count_prefetch_acks<=count_prefetch_acks+1'b1;
            if(dbg_prefetch_use) count_prefetch_uses<=count_prefetch_uses+1'b1;
            if(dbg_prefetch_offer && dbg_scratch_outstanding && out_valid && out_ready)
                count_dense_during_read_pending<=count_dense_during_read_pending+1'b1;
            if(dbg_scratch_state==27) count_prefetch_drain_wait<=count_prefetch_drain_wait+1'b1;
            if(dbg_write_enqueue) count_write_enqueues<=count_write_enqueues+1'b1;
            if(dbg_write_slot_valid && mem_req_valid && mem_req_ready) count_write_accepts<=count_write_accepts+1'b1;
            if(dbg_scratch_outstanding && mem_req_write && (dbg_scratch_state==1 || dbg_scratch_state==2))
                count_packing_during_write_pending<=count_packing_during_write_pending+1'b1;
            if(dbg_write_slot_valid && dbg_scratch_outstanding && mem_rsp_valid && mem_rsp_epoch==store_epoch)
                count_write_acks<=count_write_acks+1'b1;
            if(dbg_scratch_state==26) count_full_wait<=count_full_wait+1'b1;
            if(packet_done && ts_packet_done_observed==0) ts_packet_done_observed<=count_cycles+1'b1;
            if(dbg_seal_valid && seal_ready) ts_seal_accepted<=count_cycles+1'b1;
            if(scratch_sealed && ts_scratch_sealed_observed==0) ts_scratch_sealed_observed<=count_cycles+1'b1;
            if(out_valid && out_ready) begin
                if(ts_first_dense==0) ts_first_dense<=count_cycles+1'b1;
                ts_last_dense<=count_cycles+1'b1;
            end
            if(store_done) ts_integrated_done<=count_cycles+1'b1;
        end
    end
    always_ff @(posedge clk) begin
        if(reset || abort_packet) begin
            running<=0; allocation<=0; seal_sent<=0; use_serial_clear<=0; use_write_overlap<=0; use_read_prefetch<=0; use_tile_overlap<=0;
            done<=0; error<=0; count_cycles<=0; count_input_bytes<=0; count_dense<=0;
            count_reads<=0; count_writes<=0; count_dense_stall<=0;
        end else if(start) begin
            running<=1; allocation<=0; seal_sent<=0; use_serial_clear<=serial_clear; use_write_overlap<=write_overlap; use_read_prefetch<=read_prefetch; use_tile_overlap<=tile_overlap;
            done<=0; error<=0; count_cycles<=0; count_input_bytes<=0; count_dense<=0;
            count_reads<=0; count_writes<=0; count_dense_stall<=0;
        end else if(running) begin
            count_cycles<=count_cycles+1'b1;
            if(in_valid && in_ready) count_input_bytes<=count_input_bytes+1'b1;
            if(out_valid && out_ready) count_dense<=count_dense+1'b1;
            if(out_valid && !out_ready) count_dense_stall<=count_dense_stall+1'b1;
            if(mem_req_valid && mem_req_ready) begin
                if(mem_req_write) count_writes<=count_writes+1'b1;
                else count_reads<=count_reads+1'b1;
            end
            if(meta_valid && meta_ready) allocation<=1;
            if(packet_done && allocation && !seal_sent && seal_ready) seal_sent<=1;
            if(packet_error!=0) begin error<={4'h1,packet_error}; running<=0; end
            else if(store_error!=0) begin error<={4'h2,store_error}; running<=0; end
            else if(store_done) begin done<=1; running<=0; end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk) if(!cancelled) begin
        assert(!out_valid || (scratch_sealed && seal_sent && allocation))
            else $fatal(1,"dense output before packet/store validation");
        assert(!done || (!out_valid && !running)) else $fatal(1,"terminal publication fence");
        assert(packet_inputs==count_input_bytes || !running) else $fatal(1,"packet ingress counter");
        assert(packet_outputs<=packet_inputs*64'd64+64'd64) else $fatal(1,"diagnostic range");
        assert(packet_cycles>=packet_stall) else $fatal(1,"packet stall diagnostic");
    end
`endif
endmodule
