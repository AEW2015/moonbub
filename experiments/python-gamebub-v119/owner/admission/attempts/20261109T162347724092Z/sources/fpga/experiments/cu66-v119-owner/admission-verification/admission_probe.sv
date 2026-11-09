module admission_probe (
    input logic clk, reset, start, abort_packet,
    input logic cache_write,
    input logic [10:0] cache_index,
    input logic [1:0] cache_data,
    input logic replay_req,
    input logic [31:0] replay_addr,
    output logic replay_ready, replay_rsp_valid,
    output logic [7:0] replay_data,
    output logic [31:0] replay_rsp_addr, replay_rsp_epoch,
    input logic lookup_req,
    input logic [12:0] lookup_tile,
    input logic [10:0] lookup_cell,
    output logic lookup_rsp_valid,
    output logic [1:0] lookup_mode, lookup_scale,
    input logic [31:0] packet_bytes, epoch,
    input logic accepted_ref_valid, accepted_qcache_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    input logic in_valid, in_last,
    input logic [7:0] in_data,
    output logic in_ready, busy,
    output logic receipt_valid,
    input logic receipt_ready,
    output logic [7:0] error,
    output logic [31:0] receipt_epoch, fid, refid,
    output logic [63:0] generation,
    output logic key_frame,
    output logic [31:0] mode_bytes, qmap_bytes, hud_bytes, data_bytes,
    output logic [31:0] plane_blocks [0:2],
    output logic [31:0] plane_offset [0:2],
    output logic [31:0] plane_length [0:2],
    output logic [1:0] plane_entropy [0:2],
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_cancel,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data,
    output logic [7:0] debug_state,
    output logic [63:0] count_cycles, count_inputs, count_stage_reads,
    output logic [63:0] count_stage_responses, count_receipt_wait,
    output logic [31:0] required_cells,
    output logic [31:0] verify_q_index,
    output logic [31:0] verify_q_runs,
    output logic [6:0] verify_q_remaining,
    output logic [1:0] verify_q_value,
    output logic [7:0] verify_q_selected,
    output logic [7:0] verify_q_cached,
    output logic [31:0] verify_header_index,
    output logic [34:0] verify_header_mode_start,
    output logic [34:0] verify_header_residual_start,
    output logic [34:0] verify_header_hud_tail,
    output logic [34:0] verify_header_residual_end,
    output logic [34:0] verify_header_packet_total,
    output logic mismatch,
    output logic verify_coord_valid,
    output logic [1:0] verify_plane,
    output logic [31:0] verify_tile,
    output logic [10:0] verify_cell,
    output logic [6:0] verify_column,
    output logic verify_odd,
    output logic [10:0] verify_pair_base,
    output logic verify_residual,
    output logic [10:0] verify_active_index,
    output logic verify_active_value
);
    logic [31:0] original_verify_q_index;
    logic [31:0] original_verify_q_runs;
    logic [6:0] original_verify_q_remaining;
    logic [1:0] original_verify_q_value;
    logic [7:0] original_verify_q_selected;
    logic [7:0] original_verify_q_cached;
    logic [31:0] original_verify_header_index;
    logic [34:0] original_verify_header_mode_start;
    logic [34:0] original_verify_header_residual_start;
    logic [34:0] original_verify_header_hud_tail;
    logic [34:0] original_verify_header_residual_end;
    logic [34:0] original_verify_header_packet_total;
    logic  original_replay_ready;
    logic  original_replay_rsp_valid;
    logic [7:0] original_replay_data;
    logic [31:0] original_replay_rsp_addr;
    logic [31:0] original_replay_rsp_epoch;
    logic  original_lookup_rsp_valid;
    logic [1:0] original_lookup_mode;
    logic [1:0] original_lookup_scale;
    logic  original_in_ready;
    logic  original_busy;
    logic  original_receipt_valid;
    logic [7:0] original_error;
    logic [31:0] original_receipt_epoch;
    logic [31:0] original_fid;
    logic [31:0] original_refid;
    logic [63:0] original_generation;
    logic  original_key_frame;
    logic [31:0] original_mode_bytes;
    logic [31:0] original_qmap_bytes;
    logic [31:0] original_hud_bytes;
    logic [31:0] original_data_bytes;
    logic [31:0] original_plane_blocks [0:2];
    logic [31:0] original_plane_offset [0:2];
    logic [31:0] original_plane_length [0:2];
    logic [1:0] original_plane_entropy [0:2];
    logic  original_stage_read_req;
    logic  original_stage_read_rsp;
    logic  original_stage_write;
    logic  original_stage_pending;
    logic  original_stage_cancel;
    logic [31:0] original_stage_read_addr;
    logic [31:0] original_stage_rsp_addr;
    logic [31:0] original_stage_req_epoch;
    logic [31:0] original_stage_rsp_epoch;
    logic [7:0] original_stage_read_data;
    logic [7:0] original_debug_state;
    logic [63:0] original_count_cycles;
    logic [63:0] original_count_inputs;
    logic [63:0] original_count_stage_reads;
    logic [63:0] original_count_stage_responses;
    logic [63:0] original_count_receipt_wait;
    logic [31:0] original_required_cells;
    logic original_verify_coord_valid;
    logic [1:0] original_verify_plane;
    logic [31:0] original_verify_tile;
    logic [10:0] original_verify_cell;
    logic [6:0] original_verify_column;
    logic original_verify_odd;
    logic [10:0] original_verify_pair_base;
    logic original_verify_residual;
    logic [10:0] original_verify_active_index;
    logic original_verify_active_value;
    admission_original original (
        .verify_header_index(original_verify_header_index),
        .verify_header_mode_start(original_verify_header_mode_start),
        .verify_header_residual_start(original_verify_header_residual_start),
        .verify_header_hud_tail(original_verify_header_hud_tail),
        .verify_header_residual_end(original_verify_header_residual_end),
        .verify_header_packet_total(original_verify_header_packet_total),
        .verify_q_index(original_verify_q_index),
        .verify_q_runs(original_verify_q_runs),
        .verify_q_remaining(original_verify_q_remaining),
        .verify_q_value(original_verify_q_value),
        .verify_q_selected(original_verify_q_selected),
        .verify_q_cached(original_verify_q_cached),
        .clk(clk),
        .reset(reset),
        .start(start),
        .abort_packet(abort_packet),
        .cache_write(cache_write),
        .cache_index(cache_index),
        .cache_data(cache_data),
        .replay_req(replay_req),
        .replay_addr(replay_addr),
        .replay_ready(original_replay_ready),
        .replay_rsp_valid(original_replay_rsp_valid),
        .replay_data(original_replay_data),
        .replay_rsp_addr(original_replay_rsp_addr),
        .replay_rsp_epoch(original_replay_rsp_epoch),
        .lookup_req(lookup_req),
        .lookup_tile(lookup_tile),
        .lookup_cell(lookup_cell),
        .lookup_rsp_valid(original_lookup_rsp_valid),
        .lookup_mode(original_lookup_mode),
        .lookup_scale(original_lookup_scale),
        .packet_bytes(packet_bytes),
        .epoch(epoch),
        .accepted_ref_valid(accepted_ref_valid),
        .accepted_qcache_valid(accepted_qcache_valid),
        .accepted_ref_fid(accepted_ref_fid),
        .accepted_ref_generation(accepted_ref_generation),
        .in_valid(in_valid),
        .in_last(in_last),
        .in_data(in_data),
        .in_ready(original_in_ready),
        .busy(original_busy),
        .receipt_valid(original_receipt_valid),
        .receipt_ready(receipt_ready),
        .error(original_error),
        .receipt_epoch(original_receipt_epoch),
        .fid(original_fid),
        .refid(original_refid),
        .generation(original_generation),
        .key_frame(original_key_frame),
        .mode_bytes(original_mode_bytes),
        .qmap_bytes(original_qmap_bytes),
        .hud_bytes(original_hud_bytes),
        .data_bytes(original_data_bytes),
        .plane_blocks(original_plane_blocks),
        .plane_offset(original_plane_offset),
        .plane_length(original_plane_length),
        .plane_entropy(original_plane_entropy),
        .stage_read_req(original_stage_read_req),
        .stage_read_rsp(original_stage_read_rsp),
        .stage_write(original_stage_write),
        .stage_pending(original_stage_pending),
        .stage_cancel(original_stage_cancel),
        .stage_read_addr(original_stage_read_addr),
        .stage_rsp_addr(original_stage_rsp_addr),
        .stage_req_epoch(original_stage_req_epoch),
        .stage_rsp_epoch(original_stage_rsp_epoch),
        .stage_read_data(original_stage_read_data),
        .debug_state(original_debug_state),
        .count_cycles(original_count_cycles),
        .count_inputs(original_count_inputs),
        .count_stage_reads(original_count_stage_reads),
        .count_stage_responses(original_count_stage_responses),
        .count_receipt_wait(original_count_receipt_wait),
        .required_cells(original_required_cells),
        .verify_coord_valid(original_verify_coord_valid),
        .verify_plane(original_verify_plane),
        .verify_tile(original_verify_tile),
        .verify_cell(original_verify_cell),
        .verify_column(original_verify_column),
        .verify_odd(original_verify_odd),
        .verify_pair_base(original_verify_pair_base),
        .verify_residual(original_verify_residual),
        .verify_active_index(original_verify_active_index),
        .verify_active_value(original_verify_active_value));
    admission_candidate candidate (
        .verify_header_index(verify_header_index),
        .verify_header_mode_start(verify_header_mode_start),
        .verify_header_residual_start(verify_header_residual_start),
        .verify_header_hud_tail(verify_header_hud_tail),
        .verify_header_residual_end(verify_header_residual_end),
        .verify_header_packet_total(verify_header_packet_total),
        .verify_q_index(verify_q_index),
        .verify_q_runs(verify_q_runs),
        .verify_q_remaining(verify_q_remaining),
        .verify_q_value(verify_q_value),
        .verify_q_selected(verify_q_selected),
        .verify_q_cached(verify_q_cached),
        .clk(clk),
        .reset(reset),
        .start(start),
        .abort_packet(abort_packet),
        .cache_write(cache_write),
        .cache_index(cache_index),
        .cache_data(cache_data),
        .replay_req(replay_req),
        .replay_addr(replay_addr),
        .replay_ready(replay_ready),
        .replay_rsp_valid(replay_rsp_valid),
        .replay_data(replay_data),
        .replay_rsp_addr(replay_rsp_addr),
        .replay_rsp_epoch(replay_rsp_epoch),
        .lookup_req(lookup_req),
        .lookup_tile(lookup_tile),
        .lookup_cell(lookup_cell),
        .lookup_rsp_valid(lookup_rsp_valid),
        .lookup_mode(lookup_mode),
        .lookup_scale(lookup_scale),
        .packet_bytes(packet_bytes),
        .epoch(epoch),
        .accepted_ref_valid(accepted_ref_valid),
        .accepted_qcache_valid(accepted_qcache_valid),
        .accepted_ref_fid(accepted_ref_fid),
        .accepted_ref_generation(accepted_ref_generation),
        .in_valid(in_valid),
        .in_last(in_last),
        .in_data(in_data),
        .in_ready(in_ready),
        .busy(busy),
        .receipt_valid(receipt_valid),
        .receipt_ready(receipt_ready),
        .error(error),
        .receipt_epoch(receipt_epoch),
        .fid(fid),
        .refid(refid),
        .generation(generation),
        .key_frame(key_frame),
        .mode_bytes(mode_bytes),
        .qmap_bytes(qmap_bytes),
        .hud_bytes(hud_bytes),
        .data_bytes(data_bytes),
        .plane_blocks(plane_blocks),
        .plane_offset(plane_offset),
        .plane_length(plane_length),
        .plane_entropy(plane_entropy),
        .stage_read_req(stage_read_req),
        .stage_read_rsp(stage_read_rsp),
        .stage_write(stage_write),
        .stage_pending(stage_pending),
        .stage_cancel(stage_cancel),
        .stage_read_addr(stage_read_addr),
        .stage_rsp_addr(stage_rsp_addr),
        .stage_req_epoch(stage_req_epoch),
        .stage_rsp_epoch(stage_rsp_epoch),
        .stage_read_data(stage_read_data),
        .debug_state(debug_state),
        .count_cycles(count_cycles),
        .count_inputs(count_inputs),
        .count_stage_reads(count_stage_reads),
        .count_stage_responses(count_stage_responses),
        .count_receipt_wait(count_receipt_wait),
        .required_cells(required_cells),
        .verify_coord_valid(verify_coord_valid),
        .verify_plane(verify_plane),
        .verify_tile(verify_tile),
        .verify_cell(verify_cell),
        .verify_column(verify_column),
        .verify_odd(verify_odd),
        .verify_pair_base(verify_pair_base),
        .verify_residual(verify_residual),
        .verify_active_index(verify_active_index),
        .verify_active_value(verify_active_value));
    always_comb begin
        mismatch=0;
        mismatch=mismatch || verify_header_index!=original_verify_header_index;
        if(!reset&&!start&&!abort_packet&&debug_state==5)begin
            mismatch=mismatch || verify_header_mode_start!=original_verify_header_mode_start;
            mismatch=mismatch || verify_header_residual_start!=original_verify_header_residual_start;
            mismatch=mismatch || verify_header_hud_tail!=original_verify_header_hud_tail;
            mismatch=mismatch || verify_header_residual_end!=original_verify_header_residual_end;
            mismatch=mismatch || verify_header_packet_total!=original_verify_header_packet_total;
        end
        if(!reset&&!start&&!abort_packet&&debug_state==17&&verify_q_index!=qmap_bytes-4)
            mismatch=mismatch || verify_q_cached!=original_verify_q_cached;
        mismatch=mismatch || verify_q_index!=original_verify_q_index;
        mismatch=mismatch || verify_q_runs!=original_verify_q_runs;
        mismatch=mismatch || verify_q_remaining!=original_verify_q_remaining;
        mismatch=mismatch || verify_q_value!=original_verify_q_value;
        mismatch=mismatch || verify_q_selected!=original_verify_q_selected;

        mismatch=mismatch || (replay_ready!=original_replay_ready);
        mismatch=mismatch || (replay_rsp_valid!=original_replay_rsp_valid);
        mismatch=mismatch || (replay_data!=original_replay_data);
        mismatch=mismatch || (replay_rsp_addr!=original_replay_rsp_addr);
        mismatch=mismatch || (replay_rsp_epoch!=original_replay_rsp_epoch);
        mismatch=mismatch || (lookup_rsp_valid!=original_lookup_rsp_valid);
        mismatch=mismatch || (lookup_mode!=original_lookup_mode);
        mismatch=mismatch || (lookup_scale!=original_lookup_scale);
        mismatch=mismatch || (in_ready!=original_in_ready);
        mismatch=mismatch || (busy!=original_busy);
        mismatch=mismatch || (receipt_valid!=original_receipt_valid);
        mismatch=mismatch || (error!=original_error);
        mismatch=mismatch || (receipt_epoch!=original_receipt_epoch);
        mismatch=mismatch || (fid!=original_fid);
        mismatch=mismatch || (refid!=original_refid);
        mismatch=mismatch || (generation!=original_generation);
        mismatch=mismatch || (key_frame!=original_key_frame);
        mismatch=mismatch || (mode_bytes!=original_mode_bytes);
        mismatch=mismatch || (qmap_bytes!=original_qmap_bytes);
        mismatch=mismatch || (hud_bytes!=original_hud_bytes);
        mismatch=mismatch || (data_bytes!=original_data_bytes);
        mismatch=mismatch || (plane_blocks[0]!=original_plane_blocks[0]);
        mismatch=mismatch || (plane_blocks[1]!=original_plane_blocks[1]);
        mismatch=mismatch || (plane_blocks[2]!=original_plane_blocks[2]);
        mismatch=mismatch || (plane_offset[0]!=original_plane_offset[0]);
        mismatch=mismatch || (plane_offset[1]!=original_plane_offset[1]);
        mismatch=mismatch || (plane_offset[2]!=original_plane_offset[2]);
        mismatch=mismatch || (plane_length[0]!=original_plane_length[0]);
        mismatch=mismatch || (plane_length[1]!=original_plane_length[1]);
        mismatch=mismatch || (plane_length[2]!=original_plane_length[2]);
        mismatch=mismatch || (plane_entropy[0]!=original_plane_entropy[0]);
        mismatch=mismatch || (plane_entropy[1]!=original_plane_entropy[1]);
        mismatch=mismatch || (plane_entropy[2]!=original_plane_entropy[2]);
        mismatch=mismatch || (stage_read_req!=original_stage_read_req);
        mismatch=mismatch || (stage_read_rsp!=original_stage_read_rsp);
        mismatch=mismatch || (stage_write!=original_stage_write);
        mismatch=mismatch || (stage_pending!=original_stage_pending);
        mismatch=mismatch || (stage_cancel!=original_stage_cancel);
        mismatch=mismatch || (stage_read_addr!=original_stage_read_addr);
        mismatch=mismatch || (stage_rsp_addr!=original_stage_rsp_addr);
        mismatch=mismatch || (stage_req_epoch!=original_stage_req_epoch);
        mismatch=mismatch || (stage_rsp_epoch!=original_stage_rsp_epoch);
        mismatch=mismatch || (stage_read_data!=original_stage_read_data);
        mismatch=mismatch || (debug_state!=original_debug_state);
        mismatch=mismatch || (count_cycles!=original_count_cycles);
        mismatch=mismatch || (count_inputs!=original_count_inputs);
        mismatch=mismatch || (count_stage_reads!=original_count_stage_reads);
        mismatch=mismatch || (count_stage_responses!=original_count_stage_responses);
        mismatch=mismatch || (count_receipt_wait!=original_count_receipt_wait);
        mismatch=mismatch || (required_cells!=original_required_cells);
        if(verify_coord_valid && original_verify_coord_valid)begin
            mismatch=mismatch || verify_plane!=original_verify_plane || verify_tile!=original_verify_tile ||
                verify_cell!=original_verify_cell || verify_column!=original_verify_column ||
                verify_odd!=original_verify_odd || verify_pair_base!=original_verify_pair_base ||
                verify_residual!=original_verify_residual;
        end
        mismatch=mismatch || verify_active_index!=original_verify_active_index || verify_active_value!=original_verify_active_value;
    end
endmodule
