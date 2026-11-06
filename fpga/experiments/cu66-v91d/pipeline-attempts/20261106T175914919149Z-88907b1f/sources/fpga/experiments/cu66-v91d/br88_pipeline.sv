// V91d coefficient pipeline: packet validation -> packed scratch -> dense tiles.
// This is not the pixel/reference/HUD/publication or physical memory controller.
module br88_pipeline (
    input logic clk, reset, start, abort_packet,
    input logic [31:0] packet_bytes, epoch,
    input logic [16:0] blocks,
    input logic serial_clear,
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
    output logic metadata_wait
);
    logic running, allocation, seal_sent, use_serial_clear;
    logic cancelled, packet_abort, store_abort;
    logic packet_ready, packet_done;
    logic [3:0] packet_error, store_error;
    logic meta_valid, meta_ready, meta_raw;
    logic [16:0] meta_blocks;
    logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch;
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

    br88_packet_ingress packet_decoder (
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
        .band_end_valid(end_valid), .band_end_ready(end_ready),
        .band_end_band(end_band), .band_end_epoch(end_epoch),
        .done(packet_done), .error(packet_error), .count_cycles(packet_cycles),
        .count_inputs(packet_inputs), .count_outputs(packet_outputs),
        .count_output_stall(packet_stall), .debug_state(packet_state)
    );

    packed_scratch scratch (
        .clk(clk), .reset(reset),
        .begin_valid(meta_valid && running && error==0), .begin_ready(meta_ready),
        .begin_blocks(meta_blocks), .begin_raw(meta_raw),
        .begin_count1(meta_count1), .begin_count2(meta_count2), .begin_count3(meta_count3),
        .begin_epoch(meta_epoch), .begin_serial_clear(use_serial_clear),
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
        .mem_rsp_epoch(mem_rsp_epoch), .mem_rsp_error(mem_rsp_error)
    );

    // Diagnostic signals are exposed indirectly by assertions; all counters
    // used in the published fence are maintained at this integrated boundary.
    always_ff @(posedge clk) begin
        if(reset || abort_packet) begin
            running<=0; allocation<=0; seal_sent<=0; use_serial_clear<=0;
            done<=0; error<=0; count_cycles<=0; count_input_bytes<=0; count_dense<=0;
            count_reads<=0; count_writes<=0; count_dense_stall<=0;
        end else if(start) begin
            running<=1; allocation<=0; seal_sent<=0; use_serial_clear<=serial_clear;
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
