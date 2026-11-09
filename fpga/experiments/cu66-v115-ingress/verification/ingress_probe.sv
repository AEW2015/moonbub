module ingress_probe #(
    parameter integer MAX_PACKET_BYTES=49152
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
    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold,
    output logic [5:0] probe_fetch_index, output logic [31:0] probe_expected_addr,
    output logic probe_selection_context
);
    br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.packet_bytes(packet_bytes),.blocks(blocks),.epoch(epoch),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),.out_valid(out_valid),.out_ready(out_ready),.out_block(out_block),.out_index(out_index),.out_coefficient(out_coefficient),.out_epoch(out_epoch),.meta_valid(meta_valid),.meta_ready(meta_ready),.meta_blocks(meta_blocks),.meta_count1(meta_count1),.meta_count2(meta_count2),.meta_count3(meta_count3),.meta_epoch(meta_epoch),.meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),.meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),.meta_capacity_upper(meta_capacity_upper),.meta_capacity_lower(meta_capacity_lower),.meta_capacity_wrap(meta_capacity_wrap),.meta_raw(meta_raw),.out_band(out_band),.band_end_valid(band_end_valid),.band_end_ready(band_end_ready),.band_end_band(band_end_band),.band_end_epoch(band_end_epoch),.done(done),.error(error),.count_cycles(count_cycles),.count_inputs(count_inputs),.count_outputs(count_outputs),.count_output_stall(count_output_stall),.debug_state(debug_state),.stage_read_req(stage_read_req),.stage_read_rsp(stage_read_rsp),.stage_write(stage_write),.stage_pending(stage_pending),.stage_context_active(stage_context_active),.stage_cancel(stage_cancel),.stage_word_valid(stage_word_valid),.stage_word_ready(stage_word_ready),.stage_read_addr(stage_read_addr),.stage_rsp_addr(stage_rsp_addr),.stage_write_addr(stage_write_addr),.stage_req_epoch(stage_req_epoch),.stage_rsp_epoch(stage_rsp_epoch),.stage_read_data(stage_read_data),.stage_write_data(stage_write_data),.stage_buffer_bytes(stage_buffer_bytes),.stage_buffer_highwater(stage_buffer_highwater),.stage_purpose(stage_purpose),.count_stage_reads(count_stage_reads),.count_stage_responses(count_stage_responses),.count_stage_writes(count_stage_writes),.count_stage_fetch_wait(count_stage_fetch_wait),.count_stage_word_hold(count_stage_word_hold));
    assign probe_fetch_index=dut.fetch_index;
    assign probe_expected_addr=dut.expected_fetch_addr;
    assign probe_selection_context=dut.selection_context;
endmodule
