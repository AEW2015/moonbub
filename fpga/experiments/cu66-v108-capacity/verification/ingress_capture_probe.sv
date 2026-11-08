module ingress_capture_probe (
 input logic clk,
 input logic reset,
 input logic start,
 input logic abort_packet,
 input logic [31:0] packet_bytes,
 input logic [16:0] blocks,
 input logic [31:0] epoch,
 input logic word16,
 input logic serial_mode,
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
 output logic [31:0] meta_count1,
 output logic [31:0] meta_count2,
 output logic [31:0] meta_count3,
 output logic [31:0] meta_epoch,
 output logic [31:0] meta_prefix1,
 output logic [31:0] meta_prefix12,
 output logic [31:0] meta_prefix123,
 output logic [31:0] meta_threshold1,
 output logic [31:0] meta_threshold2,
 output logic [31:0] meta_threshold3,
 output logic meta_raw,
 output logic [1:0] out_band,
 output logic band_end_valid,
 input logic band_end_ready,
 output logic [1:0] band_end_band,
 output logic [31:0] band_end_epoch,
 output logic done,
 output logic [3:0] error,
 output logic [63:0] count_cycles,
 output logic [63:0] count_inputs,
 output logic [63:0] count_outputs,
 output logic [63:0] count_output_stall,
 output logic [3:0] debug_state,
 output logic stage_read_req,
 output logic stage_read_rsp,
 output logic stage_write,
 output logic stage_pending,
 output logic stage_context_active,
 output logic stage_cancel,
 output logic stage_word_valid,
 output logic stage_word_ready,
 output logic [31:0] stage_read_addr,
 output logic [31:0] stage_rsp_addr,
 output logic [31:0] stage_write_addr,
 output logic [31:0] stage_req_epoch,
 output logic [31:0] stage_rsp_epoch,
 output logic [7:0] stage_read_data,
 output logic [7:0] stage_write_data,
 output logic [5:0] stage_buffer_bytes,
 output logic [5:0] stage_buffer_highwater,
 output logic [2:0] stage_purpose,
 output logic [63:0] count_stage_reads,
 output logic [63:0] count_stage_responses,
 output logic [63:0] count_stage_writes,
 output logic [63:0] count_stage_fetch_wait,
 output logic [63:0] count_stage_word_hold,
 output logic mismatch,
 output logic verify_capture,
 output logic [31:0] verify_a1,verify_a2,verify_a3,
 output logic [2:0] verify_threshold_live,
 output logic [31:0] verify_capacity_upper,verify_capacity_lower,
 output logic verify_capacity_wrap,verify_capacity_live
);
 logic old_in_ready;
 logic old_out_valid;
 logic [15:0] old_out_block;
 logic [5:0] old_out_index;
 logic signed [15:0] old_out_coefficient;
 logic [31:0] old_out_epoch;
 logic old_meta_valid;
 logic [16:0] old_meta_blocks;
 logic [31:0] old_meta_count1;
 logic [31:0] old_meta_count2;
 logic [31:0] old_meta_count3;
 logic [31:0] old_meta_epoch;
 logic [31:0] old_meta_prefix1;
 logic [31:0] old_meta_prefix12;
 logic [31:0] old_meta_prefix123;
 logic [31:0] old_meta_threshold1;
 logic [31:0] old_meta_threshold2;
 logic [31:0] old_meta_threshold3;
 logic old_meta_raw;
 logic [1:0] old_out_band;
 logic old_band_end_valid;
 logic [1:0] old_band_end_band;
 logic [31:0] old_band_end_epoch;
 logic old_done;
 logic [3:0] old_error;
 logic [63:0] old_count_cycles;
 logic [63:0] old_count_inputs;
 logic [63:0] old_count_outputs;
 logic [63:0] old_count_output_stall;
 logic [3:0] old_debug_state;
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
 ingress_original old_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.packet_bytes(packet_bytes),.blocks(blocks),.epoch(epoch),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(old_in_ready),.in_data(in_data),.in_last(in_last),.out_valid(old_out_valid),.out_ready(out_ready),.out_block(old_out_block),.out_index(old_out_index),.out_coefficient(old_out_coefficient),.out_epoch(old_out_epoch),.meta_valid(old_meta_valid),.meta_ready(meta_ready),.meta_blocks(old_meta_blocks),.meta_count1(old_meta_count1),.meta_count2(old_meta_count2),.meta_count3(old_meta_count3),.meta_epoch(old_meta_epoch),.meta_prefix1(old_meta_prefix1),.meta_prefix12(old_meta_prefix12),.meta_prefix123(old_meta_prefix123),.meta_threshold1(old_meta_threshold1),.meta_threshold2(old_meta_threshold2),.meta_threshold3(old_meta_threshold3),.meta_raw(old_meta_raw),.out_band(old_out_band),.band_end_valid(old_band_end_valid),.band_end_ready(band_end_ready),.band_end_band(old_band_end_band),.band_end_epoch(old_band_end_epoch),.done(old_done),.error(old_error),.count_cycles(old_count_cycles),.count_inputs(old_count_inputs),.count_outputs(old_count_outputs),.count_output_stall(old_count_output_stall),.debug_state(old_debug_state),.stage_read_req(old_stage_read_req),.stage_read_rsp(old_stage_read_rsp),.stage_write(old_stage_write),.stage_pending(old_stage_pending),.stage_context_active(old_stage_context_active),.stage_cancel(old_stage_cancel),.stage_word_valid(old_stage_word_valid),.stage_word_ready(old_stage_word_ready),.stage_read_addr(old_stage_read_addr),.stage_rsp_addr(old_stage_rsp_addr),.stage_write_addr(old_stage_write_addr),.stage_req_epoch(old_stage_req_epoch),.stage_rsp_epoch(old_stage_rsp_epoch),.stage_read_data(old_stage_read_data),.stage_write_data(old_stage_write_data),.stage_buffer_bytes(old_stage_buffer_bytes),.stage_buffer_highwater(old_stage_buffer_highwater),.stage_purpose(old_stage_purpose),.count_stage_reads(old_count_stage_reads),.count_stage_responses(old_count_stage_responses),.count_stage_writes(old_count_stage_writes),.count_stage_fetch_wait(old_count_stage_fetch_wait),.count_stage_word_hold(old_count_stage_word_hold));
 ingress_candidate new_dut(.clk(clk),.reset(reset),.start(start),.abort_packet(abort_packet),.packet_bytes(packet_bytes),.blocks(blocks),.epoch(epoch),.word16(word16),.serial_mode(serial_mode),.in_valid(in_valid),.in_ready(in_ready),.in_data(in_data),.in_last(in_last),.out_valid(out_valid),.out_ready(out_ready),.out_block(out_block),.out_index(out_index),.out_coefficient(out_coefficient),.out_epoch(out_epoch),.meta_valid(meta_valid),.meta_ready(meta_ready),.meta_blocks(meta_blocks),.meta_count1(meta_count1),.meta_count2(meta_count2),.meta_count3(meta_count3),.meta_epoch(meta_epoch),.meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),.meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),.meta_raw(meta_raw),.out_band(out_band),.band_end_valid(band_end_valid),.band_end_ready(band_end_ready),.band_end_band(band_end_band),.band_end_epoch(band_end_epoch),.done(done),.error(error),.count_cycles(count_cycles),.count_inputs(count_inputs),.count_outputs(count_outputs),.count_output_stall(count_output_stall),.debug_state(debug_state),.stage_read_req(stage_read_req),.stage_read_rsp(stage_read_rsp),.stage_write(stage_write),.stage_pending(stage_pending),.stage_context_active(stage_context_active),.stage_cancel(stage_cancel),.stage_word_valid(stage_word_valid),.stage_word_ready(stage_word_ready),.stage_read_addr(stage_read_addr),.stage_rsp_addr(stage_rsp_addr),.stage_write_addr(stage_write_addr),.stage_req_epoch(stage_req_epoch),.stage_rsp_epoch(stage_rsp_epoch),.stage_read_data(stage_read_data),.stage_write_data(stage_write_data),.stage_buffer_bytes(stage_buffer_bytes),.stage_buffer_highwater(stage_buffer_highwater),.stage_purpose(stage_purpose),.count_stage_reads(count_stage_reads),.count_stage_responses(count_stage_responses),.count_stage_writes(count_stage_writes),.count_stage_fetch_wait(count_stage_fetch_wait),.count_stage_word_hold(count_stage_word_hold),.meta_capacity_upper(verify_capacity_upper),.meta_capacity_lower(verify_capacity_lower),.meta_capacity_wrap(verify_capacity_wrap));
 assign mismatch=!((old_in_ready==in_ready)&&(old_out_valid==out_valid)&&(old_out_block==out_block)&&(old_out_index==out_index)&&(old_out_coefficient==out_coefficient)&&(old_out_epoch==out_epoch)&&(old_meta_valid==meta_valid)&&(old_meta_blocks==meta_blocks)&&(old_meta_count1==meta_count1)&&(old_meta_count2==meta_count2)&&(old_meta_count3==meta_count3)&&(old_meta_epoch==meta_epoch)&&(old_meta_prefix1==meta_prefix1)&&(old_meta_prefix12==meta_prefix12)&&(old_meta_prefix123==meta_prefix123)&&(old_meta_threshold1==meta_threshold1)&&(old_meta_threshold2==meta_threshold2)&&(old_meta_threshold3==meta_threshold3)&&(old_meta_raw==meta_raw)&&(old_out_band==out_band)&&(old_band_end_valid==band_end_valid)&&(old_band_end_band==band_end_band)&&(old_band_end_epoch==band_end_epoch)&&(old_done==done)&&(old_error==error)&&(old_count_cycles==count_cycles)&&(old_count_inputs==count_inputs)&&(old_count_outputs==count_outputs)&&(old_count_output_stall==count_output_stall)&&(old_debug_state==debug_state)&&(old_stage_read_req==stage_read_req)&&(old_stage_read_rsp==stage_read_rsp)&&(old_stage_write==stage_write)&&(old_stage_pending==stage_pending)&&(old_stage_context_active==stage_context_active)&&(old_stage_cancel==stage_cancel)&&(old_stage_word_valid==stage_word_valid)&&(old_stage_word_ready==stage_word_ready)&&(old_stage_read_addr==stage_read_addr)&&(old_stage_rsp_addr==stage_rsp_addr)&&(old_stage_write_addr==stage_write_addr)&&(old_stage_req_epoch==stage_req_epoch)&&(old_stage_rsp_epoch==stage_rsp_epoch)&&(old_stage_read_data==stage_read_data)&&(old_stage_write_data==stage_write_data)&&(old_stage_buffer_bytes==stage_buffer_bytes)&&(old_stage_buffer_highwater==stage_buffer_highwater)&&(old_stage_purpose==stage_purpose)&&(old_count_stage_reads==count_stage_reads)&&(old_count_stage_responses==count_stage_responses)&&(old_count_stage_writes==count_stage_writes)&&(old_count_stage_fetch_wait==count_stage_fetch_wait)&&(old_count_stage_word_hold==count_stage_word_hold));
 assign verify_capture=new_dut.prefix_header_capture;
 assign verify_a1=new_dut.plan_align1;assign verify_a2=new_dut.plan_align2;assign verify_a3=new_dut.plan_align3;
 assign verify_threshold_live=new_dut.threshold_live;
 assign verify_capacity_live=new_dut.capacity_live;

endmodule
