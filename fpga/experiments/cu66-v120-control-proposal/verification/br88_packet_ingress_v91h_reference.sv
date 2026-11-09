module br88_packet_ingress_v91h_reference #(
    parameter integer MAX_PACKET_BYTES=49152,
    parameter integer SYNC_STAGING=1
) (
    input logic clk, reset, start, abort_packet,
    input logic [31:0] packet_bytes,
    input logic [16:0] blocks,
    input logic [31:0] epoch,
    input logic word16, serial_mode,
    input logic in_valid,
    output logic in_ready,
    input logic [7:0] in_data,
    input logic in_last,
    output logic out_valid,
    input logic out_ready,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_coefficient,
    output logic [31:0] out_epoch,
    output logic meta_valid,
    input logic meta_ready,
    output logic [16:0] meta_blocks,
    output logic [31:0] meta_count1, meta_count2, meta_count3, meta_epoch,
    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,
    output logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3,
    output logic [31:0] meta_capacity_upper, meta_capacity_lower,
    output logic meta_capacity_wrap,
    output logic meta_raw,
    output logic [1:0] out_band,
    output logic band_end_valid,
    input logic band_end_ready,
    output logic [1:0] band_end_band,
    output logic [31:0] band_end_epoch,
    output logic done,
    output logic [3:0] error,
    output logic [63:0] count_cycles, count_inputs, count_outputs,
    output logic [63:0] count_output_stall,
    output logic [3:0] debug_state,
    output logic stage_read_req, stage_read_rsp, stage_write, stage_pending, stage_context_active, stage_cancel, stage_word_valid, stage_word_ready,
    output logic [31:0] stage_read_addr, stage_rsp_addr, stage_write_addr, stage_req_epoch, stage_rsp_epoch,
    output logic [7:0] stage_read_data, stage_write_data,
    output logic [5:0] stage_buffer_bytes, stage_buffer_highwater,
    output logic [2:0] stage_purpose,
    output logic [63:0] count_stage_reads, count_stage_responses, count_stage_writes,
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold
);
    generate if(SYNC_STAGING==0) begin: legacy
        br88_packet_ingress #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress (
            .clk(clk),
            .reset(reset),
            .start(start),
            .abort_packet(abort_packet),
            .packet_bytes(packet_bytes),
            .blocks(blocks),
            .epoch(epoch),
            .word16(word16),
            .serial_mode(serial_mode),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .in_last(in_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_block(out_block),
            .out_index(out_index),
            .out_coefficient(out_coefficient),
            .out_epoch(out_epoch),
            .meta_valid(meta_valid),
            .meta_ready(meta_ready),
            .meta_blocks(meta_blocks),
            .meta_count1(meta_count1),
            .meta_count2(meta_count2),
            .meta_count3(meta_count3),
            .meta_epoch(meta_epoch),
            .meta_raw(meta_raw),
            .out_band(out_band),
            .band_end_valid(band_end_valid),
            .band_end_ready(band_end_ready),
            .band_end_band(band_end_band),
            .band_end_epoch(band_end_epoch),
            .done(done),
            .error(error),
            .count_cycles(count_cycles),
            .count_inputs(count_inputs),
            .count_outputs(count_outputs),
            .count_output_stall(count_output_stall),
            .debug_state(debug_state)
        );
    function automatic logic [31:0] capacity_legacy_upper(input logic [27:0] units);
        logic [27:0] a,u;
        begin a=units+28'd2;u=28'd16384-a;return {1'b0,u,3'd0};end
    endfunction
    function automatic logic [31:0] capacity_legacy_lower(input logic [27:0] units);
        logic [27:0] a,l;
        begin a=units+28'd2;l=~a;return {1'b0,l,3'd0};end
    endfunction
    function automatic logic capacity_legacy_wrap(input logic [27:0] units);
        logic [27:0] a;
        begin a=units+28'd2;return a>28'd16384;end
    endfunction
        // Legacy has no header staging; preserve exact modular capacity bounds.
        assign meta_capacity_upper=capacity_legacy_upper(meta_prefix123[31:4]);
        assign meta_capacity_lower=capacity_legacy_lower(meta_prefix123[31:4]);
        assign meta_capacity_wrap=capacity_legacy_wrap(meta_prefix123[31:4]);
        // Exact legacy fallback has no timing claim and avoids n+d-1 overflow.
        assign meta_threshold1=meta_count1/32'd5+32'(meta_count1%32'd5!=0);
        assign meta_threshold2=meta_count2/32'd15+32'(meta_count2%32'd15!=0);
        assign meta_threshold3=meta_count3/32'd43+32'(meta_count3%32'd43!=0);
        // Legacy branch has no header-fetch cache; preserve exact count algebra.
        assign meta_prefix1=((meta_count1<<2)+32'd15)&32'hfffffff0;
        assign meta_prefix12=meta_prefix1+(((meta_count2<<2)+32'd15)&32'hfffffff0);
        assign meta_prefix123=meta_prefix12+(((meta_count3<<2)+32'd15)&32'hfffffff0);
        assign stage_read_req='0;
        assign stage_read_rsp='0;
        assign stage_write='0;
        assign stage_pending='0;
        assign stage_context_active='0;
        assign stage_cancel=reset || start || abort_packet;
        assign stage_word_valid='0;
        assign stage_word_ready='0;
        assign stage_read_addr='0;
        assign stage_rsp_addr='0;
        assign stage_write_addr='0;
        assign stage_req_epoch='0;
        assign stage_rsp_epoch='0;
        assign stage_read_data='0;
        assign stage_write_data='0;
        assign stage_buffer_bytes='0;
        assign stage_buffer_highwater='0;
        assign stage_purpose='0;
        assign count_stage_reads='0;
        assign count_stage_responses='0;
        assign count_stage_writes='0;
        assign count_stage_fetch_wait='0;
        assign count_stage_word_hold='0;
    end else begin: synchronous
        br88_packet_ingress_sync_v91h_reference #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) ingress (
            .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),
            .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),
            .meta_capacity_upper(meta_capacity_upper),.meta_capacity_lower(meta_capacity_lower),.meta_capacity_wrap(meta_capacity_wrap),
            .clk(clk),
            .reset(reset),
            .start(start),
            .abort_packet(abort_packet),
            .packet_bytes(packet_bytes),
            .blocks(blocks),
            .epoch(epoch),
            .word16(word16),
            .serial_mode(serial_mode),
            .in_valid(in_valid),
            .in_ready(in_ready),
            .in_data(in_data),
            .in_last(in_last),
            .out_valid(out_valid),
            .out_ready(out_ready),
            .out_block(out_block),
            .out_index(out_index),
            .out_coefficient(out_coefficient),
            .out_epoch(out_epoch),
            .meta_valid(meta_valid),
            .meta_ready(meta_ready),
            .meta_blocks(meta_blocks),
            .meta_count1(meta_count1),
            .meta_count2(meta_count2),
            .meta_count3(meta_count3),
            .meta_epoch(meta_epoch),
            .meta_raw(meta_raw),
            .out_band(out_band),
            .band_end_valid(band_end_valid),
            .band_end_ready(band_end_ready),
            .band_end_band(band_end_band),
            .band_end_epoch(band_end_epoch),
            .done(done),
            .error(error),
            .count_cycles(count_cycles),
            .count_inputs(count_inputs),
            .count_outputs(count_outputs),
            .count_output_stall(count_output_stall),
            .debug_state(debug_state),
            .stage_read_req(stage_read_req),
            .stage_read_rsp(stage_read_rsp),
            .stage_write(stage_write),
            .stage_pending(stage_pending),
            .stage_context_active(stage_context_active),
            .stage_cancel(stage_cancel),
            .stage_word_valid(stage_word_valid), .stage_word_ready(stage_word_ready),
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
            .count_stage_word_hold(count_stage_word_hold)
        );
    end endgenerate
endmodule

