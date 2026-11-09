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
    output logic probe_selection_context,
    output logic [2:0] probe_length_pipe, output logic probe_length_live,
    output logic [63:0] probe_public_pair_checks
);
    br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.packet_bytes(packet_bytes),.blocks(blocks),.epoch(epoch),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),.out_valid(out_valid),.out_ready(out_ready),.out_block(out_block),.out_index(out_index),.out_coefficient(out_coefficient),.out_epoch(out_epoch),.meta_valid(meta_valid),.meta_ready(meta_ready),.meta_blocks(meta_blocks),.meta_count1(meta_count1),.meta_count2(meta_count2),.meta_count3(meta_count3),.meta_epoch(meta_epoch),.meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),.meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),.meta_capacity_upper(meta_capacity_upper),.meta_capacity_lower(meta_capacity_lower),.meta_capacity_wrap(meta_capacity_wrap),.meta_raw(meta_raw),.out_band(out_band),.band_end_valid(band_end_valid),.band_end_ready(band_end_ready),.band_end_band(band_end_band),.band_end_epoch(band_end_epoch),.done(done),.error(error),.count_cycles(count_cycles),.count_inputs(count_inputs),.count_outputs(count_outputs),.count_output_stall(count_output_stall),.debug_state(debug_state),.stage_read_req(stage_read_req),.stage_read_rsp(stage_read_rsp),.stage_write(stage_write),.stage_pending(stage_pending),.stage_context_active(stage_context_active),.stage_cancel(stage_cancel),.stage_word_valid(stage_word_valid),.stage_word_ready(stage_word_ready),.stage_read_addr(stage_read_addr),.stage_rsp_addr(stage_rsp_addr),.stage_write_addr(stage_write_addr),.stage_req_epoch(stage_req_epoch),.stage_rsp_epoch(stage_rsp_epoch),.stage_read_data(stage_read_data),.stage_write_data(stage_write_data),.stage_buffer_bytes(stage_buffer_bytes),.stage_buffer_highwater(stage_buffer_highwater),.stage_purpose(stage_purpose),.count_stage_reads(count_stage_reads),.count_stage_responses(count_stage_responses),.count_stage_writes(count_stage_writes),.count_stage_fetch_wait(count_stage_fetch_wait),.count_stage_word_hold(count_stage_word_hold));
    assign probe_fetch_index=dut.fetch_index;
    assign probe_expected_addr=dut.expected_fetch_addr;
    assign probe_selection_context=dut.selection_context;
    logic reference_in_ready;
    logic reference_out_valid;
    logic [15:0] reference_out_block;
    logic [5:0] reference_out_index;
    logic signed [15:0] reference_out_coefficient;
    logic [31:0] reference_out_epoch;
    logic reference_meta_valid;
    logic [16:0] reference_meta_blocks;
    logic [31:0] reference_meta_count1, reference_meta_count2, reference_meta_count3, reference_meta_epoch;
    logic [31:0] reference_meta_prefix1, reference_meta_prefix12, reference_meta_prefix123;
    logic [31:0] reference_meta_threshold1, reference_meta_threshold2, reference_meta_threshold3;
    logic [31:0] reference_meta_capacity_upper, reference_meta_capacity_lower;
    logic reference_meta_capacity_wrap;
    logic reference_meta_raw;
    logic [1:0] reference_out_band;
    logic reference_band_end_valid;
    logic [1:0] reference_band_end_band;
    logic [31:0] reference_band_end_epoch;
    logic reference_done;
    logic [3:0] reference_error;
    logic [63:0] reference_count_cycles, reference_count_inputs, reference_count_outputs;
    logic [63:0] reference_count_output_stall;
    logic [3:0] reference_debug_state;
    logic reference_stage_read_req, reference_stage_read_rsp, reference_stage_write, reference_stage_pending, reference_stage_context_active, reference_stage_cancel, reference_stage_word_valid, reference_stage_word_ready;
    logic [31:0] reference_stage_read_addr, reference_stage_rsp_addr, reference_stage_write_addr, reference_stage_req_epoch, reference_stage_rsp_epoch;
    logic [7:0] reference_stage_read_data, reference_stage_write_data;
    logic [5:0] reference_stage_buffer_bytes, reference_stage_buffer_highwater;
    logic [2:0] reference_stage_purpose;
    logic [63:0] reference_count_stage_reads, reference_count_stage_responses, reference_count_stage_writes;
    logic [63:0] reference_count_stage_fetch_wait, reference_count_stage_word_hold;
    br88_packet_ingress_sync_v91h_reference #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) reference_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.packet_bytes(packet_bytes),.blocks(blocks),.epoch(epoch),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(reference_in_ready),.in_data(in_data),.in_last(in_last),.out_valid(reference_out_valid),.out_ready(out_ready),.out_block(reference_out_block),.out_index(reference_out_index),.out_coefficient(reference_out_coefficient),.out_epoch(reference_out_epoch),.meta_valid(reference_meta_valid),.meta_ready(meta_ready),.meta_blocks(reference_meta_blocks),.meta_count1(reference_meta_count1),.meta_count2(reference_meta_count2),.meta_count3(reference_meta_count3),.meta_epoch(reference_meta_epoch),.meta_prefix1(reference_meta_prefix1),.meta_prefix12(reference_meta_prefix12),.meta_prefix123(reference_meta_prefix123),.meta_threshold1(reference_meta_threshold1),.meta_threshold2(reference_meta_threshold2),.meta_threshold3(reference_meta_threshold3),.meta_capacity_upper(reference_meta_capacity_upper),.meta_capacity_lower(reference_meta_capacity_lower),.meta_capacity_wrap(reference_meta_capacity_wrap),.meta_raw(reference_meta_raw),.out_band(reference_out_band),.band_end_valid(reference_band_end_valid),.band_end_ready(band_end_ready),.band_end_band(reference_band_end_band),.band_end_epoch(reference_band_end_epoch),.done(reference_done),.error(reference_error),.count_cycles(reference_count_cycles),.count_inputs(reference_count_inputs),.count_outputs(reference_count_outputs),.count_output_stall(reference_count_output_stall),.debug_state(reference_debug_state),.stage_read_req(reference_stage_read_req),.stage_read_rsp(reference_stage_read_rsp),.stage_write(reference_stage_write),.stage_pending(reference_stage_pending),.stage_context_active(reference_stage_context_active),.stage_cancel(reference_stage_cancel),.stage_word_valid(reference_stage_word_valid),.stage_word_ready(reference_stage_word_ready),.stage_read_addr(reference_stage_read_addr),.stage_rsp_addr(reference_stage_rsp_addr),.stage_write_addr(reference_stage_write_addr),.stage_req_epoch(reference_stage_req_epoch),.stage_rsp_epoch(reference_stage_rsp_epoch),.stage_read_data(reference_stage_read_data),.stage_write_data(reference_stage_write_data),.stage_buffer_bytes(reference_stage_buffer_bytes),.stage_buffer_highwater(reference_stage_buffer_highwater),.stage_purpose(reference_stage_purpose),.count_stage_reads(reference_count_stage_reads),.count_stage_responses(reference_count_stage_responses),.count_stage_writes(reference_count_stage_writes),.count_stage_fetch_wait(reference_count_stage_fetch_wait),.count_stage_word_hold(reference_count_stage_word_hold));
    assign probe_length_pipe=dut.header_length_valid_pipe;
    assign probe_length_live=dut.header_length_live;
    initial probe_public_pair_checks=0;
    always_ff @(posedge clk)begin
        probe_public_pair_checks<=probe_public_pair_checks+1;
        assert(in_ready===reference_in_ready)else $fatal(1,"refined ingress public-cycle mismatch: in_ready");
        assert(out_valid===reference_out_valid)else $fatal(1,"refined ingress public-cycle mismatch: out_valid");
        assert(out_block===reference_out_block)else $fatal(1,"refined ingress public-cycle mismatch: out_block");
        assert(out_index===reference_out_index)else $fatal(1,"refined ingress public-cycle mismatch: out_index");
        assert(out_coefficient===reference_out_coefficient)else $fatal(1,"refined ingress public-cycle mismatch: out_coefficient");
        assert(out_epoch===reference_out_epoch)else $fatal(1,"refined ingress public-cycle mismatch: out_epoch");
        assert(meta_valid===reference_meta_valid)else $fatal(1,"refined ingress public-cycle mismatch: meta_valid");
        assert(meta_blocks===reference_meta_blocks)else $fatal(1,"refined ingress public-cycle mismatch: meta_blocks");
        assert(meta_count1===reference_meta_count1)else $fatal(1,"refined ingress public-cycle mismatch: meta_count1");
        assert(meta_count2===reference_meta_count2)else $fatal(1,"refined ingress public-cycle mismatch: meta_count2");
        assert(meta_count3===reference_meta_count3)else $fatal(1,"refined ingress public-cycle mismatch: meta_count3");
        assert(meta_epoch===reference_meta_epoch)else $fatal(1,"refined ingress public-cycle mismatch: meta_epoch");
        assert(meta_prefix1===reference_meta_prefix1)else $fatal(1,"refined ingress public-cycle mismatch: meta_prefix1");
        assert(meta_prefix12===reference_meta_prefix12)else $fatal(1,"refined ingress public-cycle mismatch: meta_prefix12");
        assert(meta_prefix123===reference_meta_prefix123)else $fatal(1,"refined ingress public-cycle mismatch: meta_prefix123");
        assert(meta_threshold1===reference_meta_threshold1)else $fatal(1,"refined ingress public-cycle mismatch: meta_threshold1");
        assert(meta_threshold2===reference_meta_threshold2)else $fatal(1,"refined ingress public-cycle mismatch: meta_threshold2");
        assert(meta_threshold3===reference_meta_threshold3)else $fatal(1,"refined ingress public-cycle mismatch: meta_threshold3");
        assert(meta_capacity_upper===reference_meta_capacity_upper)else $fatal(1,"refined ingress public-cycle mismatch: meta_capacity_upper");
        assert(meta_capacity_lower===reference_meta_capacity_lower)else $fatal(1,"refined ingress public-cycle mismatch: meta_capacity_lower");
        assert(meta_capacity_wrap===reference_meta_capacity_wrap)else $fatal(1,"refined ingress public-cycle mismatch: meta_capacity_wrap");
        assert(meta_raw===reference_meta_raw)else $fatal(1,"refined ingress public-cycle mismatch: meta_raw");
        assert(out_band===reference_out_band)else $fatal(1,"refined ingress public-cycle mismatch: out_band");
        assert(band_end_valid===reference_band_end_valid)else $fatal(1,"refined ingress public-cycle mismatch: band_end_valid");
        assert(band_end_band===reference_band_end_band)else $fatal(1,"refined ingress public-cycle mismatch: band_end_band");
        assert(band_end_epoch===reference_band_end_epoch)else $fatal(1,"refined ingress public-cycle mismatch: band_end_epoch");
        assert(done===reference_done)else $fatal(1,"refined ingress public-cycle mismatch: done");
        assert(error===reference_error)else $fatal(1,"refined ingress public-cycle mismatch: error");
        assert(count_cycles===reference_count_cycles)else $fatal(1,"refined ingress public-cycle mismatch: count_cycles");
        assert(count_inputs===reference_count_inputs)else $fatal(1,"refined ingress public-cycle mismatch: count_inputs");
        assert(count_outputs===reference_count_outputs)else $fatal(1,"refined ingress public-cycle mismatch: count_outputs");
        assert(count_output_stall===reference_count_output_stall)else $fatal(1,"refined ingress public-cycle mismatch: count_output_stall");
        assert(debug_state===reference_debug_state)else $fatal(1,"refined ingress public-cycle mismatch: debug_state");
        assert(stage_read_req===reference_stage_read_req)else $fatal(1,"refined ingress public-cycle mismatch: stage_read_req");
        assert(stage_read_rsp===reference_stage_read_rsp)else $fatal(1,"refined ingress public-cycle mismatch: stage_read_rsp");
        assert(stage_write===reference_stage_write)else $fatal(1,"refined ingress public-cycle mismatch: stage_write");
        assert(stage_pending===reference_stage_pending)else $fatal(1,"refined ingress public-cycle mismatch: stage_pending");
        assert(stage_context_active===reference_stage_context_active)else $fatal(1,"refined ingress public-cycle mismatch: stage_context_active");
        assert(stage_cancel===reference_stage_cancel)else $fatal(1,"refined ingress public-cycle mismatch: stage_cancel");
        assert(stage_word_valid===reference_stage_word_valid)else $fatal(1,"refined ingress public-cycle mismatch: stage_word_valid");
        assert(stage_word_ready===reference_stage_word_ready)else $fatal(1,"refined ingress public-cycle mismatch: stage_word_ready");
        assert(stage_read_addr===reference_stage_read_addr)else $fatal(1,"refined ingress public-cycle mismatch: stage_read_addr");
        assert(stage_rsp_addr===reference_stage_rsp_addr)else $fatal(1,"refined ingress public-cycle mismatch: stage_rsp_addr");
        assert(stage_write_addr===reference_stage_write_addr)else $fatal(1,"refined ingress public-cycle mismatch: stage_write_addr");
        assert(stage_req_epoch===reference_stage_req_epoch)else $fatal(1,"refined ingress public-cycle mismatch: stage_req_epoch");
        assert(stage_rsp_epoch===reference_stage_rsp_epoch)else $fatal(1,"refined ingress public-cycle mismatch: stage_rsp_epoch");
        assert(stage_read_data===reference_stage_read_data)else $fatal(1,"refined ingress public-cycle mismatch: stage_read_data");
        assert(stage_write_data===reference_stage_write_data)else $fatal(1,"refined ingress public-cycle mismatch: stage_write_data");
        assert(stage_buffer_bytes===reference_stage_buffer_bytes)else $fatal(1,"refined ingress public-cycle mismatch: stage_buffer_bytes");
        assert(stage_buffer_highwater===reference_stage_buffer_highwater)else $fatal(1,"refined ingress public-cycle mismatch: stage_buffer_highwater");
        assert(stage_purpose===reference_stage_purpose)else $fatal(1,"refined ingress public-cycle mismatch: stage_purpose");
        assert(count_stage_reads===reference_count_stage_reads)else $fatal(1,"refined ingress public-cycle mismatch: count_stage_reads");
        assert(count_stage_responses===reference_count_stage_responses)else $fatal(1,"refined ingress public-cycle mismatch: count_stage_responses");
        assert(count_stage_writes===reference_count_stage_writes)else $fatal(1,"refined ingress public-cycle mismatch: count_stage_writes");
        assert(count_stage_fetch_wait===reference_count_stage_fetch_wait)else $fatal(1,"refined ingress public-cycle mismatch: count_stage_fetch_wait");
        assert(count_stage_word_hold===reference_count_stage_word_hold)else $fatal(1,"refined ingress public-cycle mismatch: count_stage_word_hold");
    end
endmodule
