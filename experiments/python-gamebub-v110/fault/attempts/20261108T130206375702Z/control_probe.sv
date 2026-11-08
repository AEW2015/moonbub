module control_probe (
    input logic  clk,
    input logic  reset,
    input logic  start,
    input logic  cancel,
    input logic verify_abort_packet,
    input logic  admitted_ready,
    input logic  key_frame,
    input logic  input_done,
    input logic [31:0] epoch,
    input logic [31:0] frame_fid,
    input logic  accepted_ref_valid,
    input logic [31:0] accepted_ref_fid,
    input logic [63:0] accepted_ref_generation,
    output logic  lookup_req,
    input logic  lookup_ready,
    output logic [12:0] lookup_tile,
    output logic [10:0] lookup_cell,
    input logic  lookup_rsp,
    input logic [1:0] lookup_mode,
    input logic [1:0] lookup_scale,
    input logic  in_valid,
    output logic  in_ready,
    input logic [31:0] in_epoch,
    input logic [31:0] in_child_epoch,
    input logic [31:0] in_token,
    input logic [1:0] in_plane,
    input logic [1:0] in_qscale,
    input logic [15:0] in_block,
    input logic [12:0] in_tile,
    input logic [10:0] in_qcell,
    input logic [5:0] in_index,
    input logic signed [23:0] in_value,
    output logic  out_valid,
    input logic  out_ready,
    output logic [31:0] out_epoch,
    output logic [31:0] out_fid,
    output logic [1:0] out_plane,
    output logic [1:0] out_mode,
    output logic [12:0] out_tile,
    output logic [5:0] out_index,
    output logic [7:0] out_value,
    output logic  ref_req_valid,
    input logic  ref_req_ready,
    output logic [31:0] ref_req_epoch,
    output logic [31:0] ref_req_fid,
    output logic [63:0] ref_req_generation,
    output logic [1:0] ref_req_plane,
    output logic [12:0] ref_req_tile,
    input logic  ref_rsp_valid,
    output logic  ref_rsp_ready,
    input logic [31:0] ref_rsp_epoch,
    input logic [31:0] ref_rsp_fid,
    input logic [63:0] ref_rsp_generation,
    input logic [1:0] ref_rsp_plane,
    input logic [12:0] ref_rsp_tile,
    input logic [511:0] ref_rsp_pixels,
    input logic  ref_rsp_error,
    output logic  busy,
    output logic  done,
    output logic  ref_pending,
    output logic [7:0] error,
    output logic [3:0] state,
    output logic [63:0] count_modes,
    output logic [63:0] count_residuals,
    output logic [63:0] count_outputs,
    output logic [63:0] count_ref_requests,
    output logic [63:0] count_ref_acks,
    output logic [63:0] count_copy_tiles,
    output logic [63:0] count_const_tiles,
    output logic [63:0] count_residual_tiles,
    output logic [63:0] count_ref_discarded,
    output logic [63:0] count_output_stalls,
    output logic [63:0] count_ref_wait,
    output logic mismatch,
    output logic [1:0] verify_plane,
    output logic [12:0] verify_tile,
    output logic [5:0] verify_fill_index,verify_emit_index,
    output logic [10:0] verify_cell,
    output logic [6:0] verify_y_column,
    output logic verify_y_odd_row
);
    logic original_fault,candidate_fault;
    logic fault_ack,candidate_fault_pending;
    always_ff @(posedge clk)begin
        if(reset||verify_abort_packet||start)fault_ack<=0;
        else if(original_fault)fault_ack<=1;
    end
    logic  candidate_lookup_req;
    logic [12:0] candidate_lookup_tile;
    logic [10:0] candidate_lookup_cell;
    logic  candidate_in_ready;
    logic  candidate_out_valid;
    logic [31:0] candidate_out_epoch;
    logic [31:0] candidate_out_fid;
    logic [1:0] candidate_out_plane;
    logic [1:0] candidate_out_mode;
    logic [12:0] candidate_out_tile;
    logic [5:0] candidate_out_index;
    logic [7:0] candidate_out_value;
    logic  candidate_ref_req_valid;
    logic [31:0] candidate_ref_req_epoch;
    logic [31:0] candidate_ref_req_fid;
    logic [63:0] candidate_ref_req_generation;
    logic [1:0] candidate_ref_req_plane;
    logic [12:0] candidate_ref_req_tile;
    logic  candidate_ref_rsp_ready;
    logic  candidate_busy;
    logic  candidate_done;
    logic  candidate_ref_pending;
    logic [7:0] candidate_error;
    logic [3:0] candidate_state;
    logic [63:0] candidate_count_modes;
    logic [63:0] candidate_count_residuals;
    logic [63:0] candidate_count_outputs;
    logic [63:0] candidate_count_ref_requests;
    logic [63:0] candidate_count_ref_acks;
    logic [63:0] candidate_count_copy_tiles;
    logic [63:0] candidate_count_const_tiles;
    logic [63:0] candidate_count_residual_tiles;
    logic [63:0] candidate_count_ref_discarded;
    logic [63:0] candidate_count_output_stalls;
    logic [63:0] candidate_count_ref_wait;
    logic [1:0] original_plane;
    logic [12:0] original_tile;
    logic [5:0] original_fill_index;
    logic [5:0] original_emit_index;
    logic [10:0] original_cell;
    logic [6:0] original_y_column;
    logic  original_y_odd_row;
    control_original original (
        .fault_o(original_fault),
        .clk(clk),
        .reset(reset),
        .start(start),
        .cancel(cancel),
        .admitted_ready(admitted_ready),
        .key_frame(key_frame),
        .input_done(input_done),
        .epoch(epoch),
        .frame_fid(frame_fid),
        .accepted_ref_valid(accepted_ref_valid),
        .accepted_ref_fid(accepted_ref_fid),
        .accepted_ref_generation(accepted_ref_generation),
        .lookup_req(lookup_req),
        .lookup_ready(lookup_ready),
        .lookup_tile(lookup_tile),
        .lookup_cell(lookup_cell),
        .lookup_rsp(lookup_rsp),
        .lookup_mode(lookup_mode),
        .lookup_scale(lookup_scale),
        .in_valid(in_valid),
        .in_ready(in_ready),
        .in_epoch(in_epoch),
        .in_child_epoch(in_child_epoch),
        .in_token(in_token),
        .in_plane(in_plane),
        .in_qscale(in_qscale),
        .in_block(in_block),
        .in_tile(in_tile),
        .in_qcell(in_qcell),
        .in_index(in_index),
        .in_value(in_value),
        .out_valid(out_valid),
        .out_ready(out_ready),
        .out_epoch(out_epoch),
        .out_fid(out_fid),
        .out_plane(out_plane),
        .out_mode(out_mode),
        .out_tile(out_tile),
        .out_index(out_index),
        .out_value(out_value),
        .ref_req_valid(ref_req_valid),
        .ref_req_ready(ref_req_ready),
        .ref_req_epoch(ref_req_epoch),
        .ref_req_fid(ref_req_fid),
        .ref_req_generation(ref_req_generation),
        .ref_req_plane(ref_req_plane),
        .ref_req_tile(ref_req_tile),
        .ref_rsp_valid(ref_rsp_valid),
        .ref_rsp_ready(ref_rsp_ready),
        .ref_rsp_epoch(ref_rsp_epoch),
        .ref_rsp_fid(ref_rsp_fid),
        .ref_rsp_generation(ref_rsp_generation),
        .ref_rsp_plane(ref_rsp_plane),
        .ref_rsp_tile(ref_rsp_tile),
        .ref_rsp_pixels(ref_rsp_pixels),
        .ref_rsp_error(ref_rsp_error),
        .busy(busy),
        .done(done),
        .ref_pending(ref_pending),
        .error(error),
        .state(state),
        .count_modes(count_modes),
        .count_residuals(count_residuals),
        .count_outputs(count_outputs),
        .count_ref_requests(count_ref_requests),
        .count_ref_acks(count_ref_acks),
        .count_copy_tiles(count_copy_tiles),
        .count_const_tiles(count_const_tiles),
        .count_residual_tiles(count_residual_tiles),
        .count_ref_discarded(count_ref_discarded),
        .count_output_stalls(count_output_stalls),
        .count_ref_wait(count_ref_wait),
        .verify_plane(original_plane),
        .verify_tile(original_tile),
        .verify_fill_index(original_fill_index),
        .verify_emit_index(original_emit_index),
        .verify_cell(original_cell),
        .verify_y_column(original_y_column),
        .verify_y_odd_row(original_y_odd_row)
    );
    control_candidate candidate (
        .fault_ack_i(fault_ack),.fault_pending_o(candidate_fault_pending),
        .fault_o(candidate_fault),
        .clk(clk),
        .reset(reset),
        .start(start),
        .cancel(cancel),
        .admitted_ready(admitted_ready),
        .key_frame(key_frame),
        .input_done(input_done),
        .epoch(epoch),
        .frame_fid(frame_fid),
        .accepted_ref_valid(accepted_ref_valid),
        .accepted_ref_fid(accepted_ref_fid),
        .accepted_ref_generation(accepted_ref_generation),
        .lookup_req(candidate_lookup_req),
        .lookup_ready(lookup_ready),
        .lookup_tile(candidate_lookup_tile),
        .lookup_cell(candidate_lookup_cell),
        .lookup_rsp(lookup_rsp),
        .lookup_mode(lookup_mode),
        .lookup_scale(lookup_scale),
        .in_valid(in_valid),
        .in_ready(candidate_in_ready),
        .in_epoch(in_epoch),
        .in_child_epoch(in_child_epoch),
        .in_token(in_token),
        .in_plane(in_plane),
        .in_qscale(in_qscale),
        .in_block(in_block),
        .in_tile(in_tile),
        .in_qcell(in_qcell),
        .in_index(in_index),
        .in_value(in_value),
        .out_valid(candidate_out_valid),
        .out_ready(out_ready),
        .out_epoch(candidate_out_epoch),
        .out_fid(candidate_out_fid),
        .out_plane(candidate_out_plane),
        .out_mode(candidate_out_mode),
        .out_tile(candidate_out_tile),
        .out_index(candidate_out_index),
        .out_value(candidate_out_value),
        .ref_req_valid(candidate_ref_req_valid),
        .ref_req_ready(ref_req_ready),
        .ref_req_epoch(candidate_ref_req_epoch),
        .ref_req_fid(candidate_ref_req_fid),
        .ref_req_generation(candidate_ref_req_generation),
        .ref_req_plane(candidate_ref_req_plane),
        .ref_req_tile(candidate_ref_req_tile),
        .ref_rsp_valid(ref_rsp_valid),
        .ref_rsp_ready(candidate_ref_rsp_ready),
        .ref_rsp_epoch(ref_rsp_epoch),
        .ref_rsp_fid(ref_rsp_fid),
        .ref_rsp_generation(ref_rsp_generation),
        .ref_rsp_plane(ref_rsp_plane),
        .ref_rsp_tile(ref_rsp_tile),
        .ref_rsp_pixels(ref_rsp_pixels),
        .ref_rsp_error(ref_rsp_error),
        .busy(candidate_busy),
        .done(candidate_done),
        .ref_pending(candidate_ref_pending),
        .error(candidate_error),
        .state(candidate_state),
        .count_modes(candidate_count_modes),
        .count_residuals(candidate_count_residuals),
        .count_outputs(candidate_count_outputs),
        .count_ref_requests(candidate_count_ref_requests),
        .count_ref_acks(candidate_count_ref_acks),
        .count_copy_tiles(candidate_count_copy_tiles),
        .count_const_tiles(candidate_count_const_tiles),
        .count_residual_tiles(candidate_count_residual_tiles),
        .count_ref_discarded(candidate_count_ref_discarded),
        .count_output_stalls(candidate_count_output_stalls),
        .count_ref_wait(candidate_count_ref_wait),
        .verify_plane(verify_plane),
        .verify_tile(verify_tile),
        .verify_fill_index(verify_fill_index),
        .verify_emit_index(verify_emit_index),
        .verify_cell(verify_cell),
        .verify_y_column(verify_y_column),
        .verify_y_odd_row(verify_y_odd_row)
    );
    assign mismatch=(candidate_fault_pending !== (original_fault&&!fault_ack)) ||(original_fault !== candidate_fault) ||
        (lookup_req !== candidate_lookup_req) ||
        (lookup_tile !== candidate_lookup_tile) ||
        (lookup_cell !== candidate_lookup_cell) ||
        (in_ready !== candidate_in_ready) ||
        (out_valid !== candidate_out_valid) ||
        (out_epoch !== candidate_out_epoch) ||
        (out_fid !== candidate_out_fid) ||
        (out_plane !== candidate_out_plane) ||
        (out_mode !== candidate_out_mode) ||
        (out_tile !== candidate_out_tile) ||
        (out_index !== candidate_out_index) ||
        (out_value !== candidate_out_value) ||
        (ref_req_valid !== candidate_ref_req_valid) ||
        (ref_req_epoch !== candidate_ref_req_epoch) ||
        (ref_req_fid !== candidate_ref_req_fid) ||
        (ref_req_generation !== candidate_ref_req_generation) ||
        (ref_req_plane !== candidate_ref_req_plane) ||
        (ref_req_tile !== candidate_ref_req_tile) ||
        (ref_rsp_ready !== candidate_ref_rsp_ready) ||
        (busy !== candidate_busy) ||
        (done !== candidate_done) ||
        (ref_pending !== candidate_ref_pending) ||
        (error !== candidate_error) ||
        (state !== candidate_state) ||
        (count_modes !== candidate_count_modes) ||
        (count_residuals !== candidate_count_residuals) ||
        (count_outputs !== candidate_count_outputs) ||
        (count_ref_requests !== candidate_count_ref_requests) ||
        (count_ref_acks !== candidate_count_ref_acks) ||
        (count_copy_tiles !== candidate_count_copy_tiles) ||
        (count_const_tiles !== candidate_count_const_tiles) ||
        (count_residual_tiles !== candidate_count_residual_tiles) ||
        (count_ref_discarded !== candidate_count_ref_discarded) ||
        (count_output_stalls !== candidate_count_output_stalls) ||
        (count_ref_wait !== candidate_count_ref_wait) ||
        (original_plane !== verify_plane) ||
        (original_tile !== verify_tile) ||
        (original_fill_index !== verify_fill_index) ||
        (original_emit_index !== verify_emit_index) ||
        (original_cell !== verify_cell) ||
        (original_y_column !== verify_y_column) ||
        (original_y_odd_row !== verify_y_odd_row);
endmodule
