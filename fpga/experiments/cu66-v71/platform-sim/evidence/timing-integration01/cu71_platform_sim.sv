`timescale 1ns/1ps
`default_nettype none
// Direct CSR platform co-simulation: no PLL, endpoint or physical SPI timing model.
module cu71_platform_sim(
 input wire clk,read_clk,pixel_clk,pixel_reset_n,rst,
 input wire bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 output wire[31:0]bus_rdata,
 input wire[23:0]peek_address,output wire[15:0]peek_data,
 output wire[31:0]model_reads,model_writes,model_refreshes,
 output wire  busy,
 output wire  error,
 output wire [7:0] stage,
 output wire [7:0] error_code,
 output wire [31:0] accepted_count,
 output wire [31:0] presented_count,
 output wire [31:0] rejected_count,
 output wire [31:0] lcd_underruns,
 output wire  quarantine,
 output wire [1:0] reference_bank,
 output wire [1:0] front_bank,
 output wire [31:0] front_frame_id,
 output wire  front_rgb_slot
);
 wire transport_fault=1'b0;
 wire[12:0]sdram_a;wire[1:0]sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 wire  abort_i;
 wire  aborted;
 wire [31:0] active_frame_id;
 wire [63:0] active_generation;
 wire  active_key;
 wire [31:0] active_reference_id;
 wire [7:0] blue;
 wire [1:0] candidate_bank;
 wire  clear_fault;
 wire  data_enable;
 wire [9:0] diag_address;
 wire [31:0] diag_data;
 wire  done;
 wire [127:0] expected_hud_tag;
 wire [63:0] front_generation;
 wire  front_valid;
 wire [7:0] green;
 wire  hsync;
 wire [15:0] hud_address;
 wire [31:0] hud_aux_frame_id;
 wire [63:0] hud_aux_generation;
 wire [23:0] hud_aux_req_addr;
 wire [15:0] hud_aux_req_data;
 wire  hud_aux_req_ready;
 wire  hud_aux_req_valid;
 wire  hud_aux_req_write;
 wire [15:0] hud_aux_rsp_data;
 wire  hud_aux_rsp_error;
 wire  hud_aux_rsp_ready;
 wire  hud_aux_rsp_valid;
 wire [15:0] hud_bytes;
 wire [1:0] hud_drain_bank;
 wire [31:0] hud_drain_frame_id;
 wire [63:0] hud_drain_generation;
 wire  hud_drain_ready;
 wire  hud_drain_success;
 wire [127:0] hud_drain_tag;
 wire  hud_drain_valid;
 wire [15:0] hud_drain_words;
 wire  hud_prepare_ready;
 wire  hud_prepare_valid;
 wire [31:0] hud_result_frame_id;
 wire [63:0] hud_result_generation;
 wire  hud_result_ready;
 wire [31:0] hud_result_reference_id;
 wire  hud_result_success;
 wire [127:0] hud_result_tag;
 wire  hud_result_valid;
 wire [15:0] hud_result_words;
 wire  lcd_error;
 wire  lcd_frame_boundary;
 wire [31:0] lcd_front_frame_id;
 wire [63:0] lcd_front_generation;
 wire  lcd_front_slot;
 wire  lcd_front_valid;
 wire [31:0] lcd_memory_errors;
 wire  lcd_pending;
 wire  lcd_presented;
 wire [31:0] lcd_presented_count;
 wire  lcd_scanout_drained;
 wire  memory_aux_busy;
 wire [31:0] memory_cache_hits;
 wire [31:0] memory_cache_misses;
 wire  memory_idle;
 wire [31:0] memory_reads;
 wire  memory_tile_busy;
 wire [31:0] memory_writes;
 wire [15:0] packet_req_address;
 wire [63:0] packet_req_generation;
 wire  packet_req_ready;
 wire [31:0] packet_req_sequence;
 wire  packet_req_valid;
 wire [15:0] packet_rsp_address;
 wire [7:0] packet_rsp_data;
 wire [63:0] packet_rsp_generation;
 wire  packet_rsp_ready;
 wire [31:0] packet_rsp_sequence;
 wire  packet_rsp_valid;
 wire  painter_busy;
 wire [31:0] painter_cycles;
 wire  painter_error;
 wire [7:0] painter_error_code;
 wire [31:0] painter_pixels;
 wire [31:0] painter_reads;
 wire [31:0] painter_writes;
 wire [9:0] physical_x;
 wire [9:0] physical_y;
 wire [7:0] red;
 wire [31:0] reference_frame_id;
 wire [127:0] reference_tag;
 wire  reference_valid;
 wire [31:0] software_ack_frame_id;
 wire [63:0] software_ack_generation;
 wire [2:0] software_ack_opcode;
 wire  software_ack_ready;
 wire  software_ack_success;
 wire  software_ack_valid;
 wire [2:0] software_command_opcode;
 wire  software_command_ready;
 wire  software_command_valid;
 wire [31:0] stale_completions;
 wire [63:0] start_generation;
 wire [31:0] start_packet_bytes;
 wire  start_ready;
 wire  start_valid;
 wire  vsync;
 cu71_local_control control_plane(.clk(clk),.rst(rst),.bus_write(bus_write),.bus_address(bus_address),.bus_wdata(bus_wdata),.bus_rdata(bus_rdata),.transport_fault(transport_fault),.start_valid(start_valid),.start_ready(start_ready),.start_generation(start_generation),.start_packet_bytes(start_packet_bytes),.abort_i(abort_i),.clear_fault(clear_fault),.busy(busy),.done(done),.error(error),.stage(stage),.error_code(error_code),.memory_tile_busy(memory_tile_busy),.memory_aux_busy(memory_aux_busy),.accepted_count(accepted_count),.presented_count(presented_count),.rejected_count(rejected_count),.lcd_underruns(lcd_underruns),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_address(packet_rsp_address),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_data(packet_rsp_data),.hud_prepare_valid(hud_prepare_valid),.hud_prepare_ready(hud_prepare_ready),.active_generation(active_generation),.active_frame_id(active_frame_id),.active_reference_id(active_reference_id),.active_key(active_key),.hud_address(hud_address),.hud_bytes(hud_bytes),.expected_hud_tag(expected_hud_tag),.candidate_bank(candidate_bank),.hud_result_valid(hud_result_valid),.hud_result_ready(hud_result_ready),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_ready(hud_drain_ready),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.software_command_valid(software_command_valid),.software_command_ready(software_command_ready),.software_command_opcode(software_command_opcode),.software_ack_valid(software_ack_valid),.software_ack_ready(software_ack_ready),.software_ack_opcode(software_ack_opcode),.software_ack_generation(software_ack_generation),.software_ack_frame_id(software_ack_frame_id),.software_ack_success(software_ack_success),.hud_aux_req_valid(hud_aux_req_valid),.hud_aux_req_ready(hud_aux_req_ready),.hud_aux_generation(hud_aux_generation),.hud_aux_frame_id(hud_aux_frame_id),.hud_aux_req_write(hud_aux_req_write),.hud_aux_req_addr(hud_aux_req_addr),.hud_aux_req_data(hud_aux_req_data),.hud_aux_rsp_valid(hud_aux_rsp_valid),.hud_aux_rsp_ready(hud_aux_rsp_ready),.hud_aux_rsp_data(hud_aux_rsp_data),.hud_aux_rsp_error(hud_aux_rsp_error),.diag_address(diag_address),.diag_data(diag_data),.quarantine(quarantine));
 cu71_system_timing #(.USE_STRIP(1),.WATCHDOG_CYCLES(32'd3000000000),.POWERUP_CYCLES(20),.REFRESH_CYCLES(750)) system_core(.clk(clk),.read_clk(read_clk),.pixel_clk(pixel_clk),.pixel_reset_n(pixel_reset_n),.rst(rst),.abort_i(abort_i),.clear_fault(clear_fault),.start_valid(start_valid),.start_ready(start_ready),.start_generation(start_generation),.start_packet_bytes(start_packet_bytes),.packet_req_valid(packet_req_valid),.packet_req_ready(packet_req_ready),.packet_req_address(packet_req_address),.packet_req_generation(packet_req_generation),.packet_req_sequence(packet_req_sequence),.packet_rsp_valid(packet_rsp_valid),.packet_rsp_ready(packet_rsp_ready),.packet_rsp_generation(packet_rsp_generation),.packet_rsp_sequence(packet_rsp_sequence),.packet_rsp_address(packet_rsp_address),.packet_rsp_data(packet_rsp_data),.hud_prepare_valid(hud_prepare_valid),.hud_prepare_ready(hud_prepare_ready),.active_generation(active_generation),.active_frame_id(active_frame_id),.active_reference_id(active_reference_id),.active_key(active_key),.hud_address(hud_address),.hud_bytes(hud_bytes),.expected_hud_tag(expected_hud_tag),.candidate_bank(candidate_bank),.hud_result_valid(hud_result_valid),.hud_result_ready(hud_result_ready),.hud_result_generation(hud_result_generation),.hud_result_frame_id(hud_result_frame_id),.hud_result_reference_id(hud_result_reference_id),.hud_result_tag(hud_result_tag),.hud_result_words(hud_result_words),.hud_result_success(hud_result_success),.hud_drain_valid(hud_drain_valid),.hud_drain_ready(hud_drain_ready),.hud_drain_generation(hud_drain_generation),.hud_drain_frame_id(hud_drain_frame_id),.hud_drain_bank(hud_drain_bank),.hud_drain_tag(hud_drain_tag),.hud_drain_words(hud_drain_words),.hud_drain_success(hud_drain_success),.software_command_valid(software_command_valid),.software_command_ready(software_command_ready),.software_command_opcode(software_command_opcode),.software_ack_valid(software_ack_valid),.software_ack_ready(software_ack_ready),.software_ack_opcode(software_ack_opcode),.software_ack_generation(software_ack_generation),.software_ack_frame_id(software_ack_frame_id),.software_ack_success(software_ack_success),.front_valid(front_valid),.front_rgb_slot(front_rgb_slot),.front_bank(front_bank),.front_generation(front_generation),.front_frame_id(front_frame_id),.reference_valid(reference_valid),.reference_bank(reference_bank),.reference_frame_id(reference_frame_id),.reference_tag(reference_tag),.busy(busy),.done(done),.aborted(aborted),.error(error),.error_code(error_code),.stage(stage),.accepted_count(accepted_count),.presented_count(presented_count),.rejected_count(rejected_count),.stale_completions(stale_completions),.diag_address(diag_address),.diag_data(diag_data),.hud_aux_req_valid(hud_aux_req_valid),.hud_aux_req_ready(hud_aux_req_ready),.hud_aux_generation(hud_aux_generation),.hud_aux_frame_id(hud_aux_frame_id),.hud_aux_req_write(hud_aux_req_write),.hud_aux_req_addr(hud_aux_req_addr),.hud_aux_req_data(hud_aux_req_data),.hud_aux_rsp_valid(hud_aux_rsp_valid),.hud_aux_rsp_ready(hud_aux_rsp_ready),.hud_aux_rsp_data(hud_aux_rsp_data),.hud_aux_rsp_error(hud_aux_rsp_error),.lcd_front_valid(lcd_front_valid),.lcd_front_slot(lcd_front_slot),.lcd_presented(lcd_presented),.lcd_pending(lcd_pending),.lcd_frame_boundary(lcd_frame_boundary),.lcd_scanout_drained(lcd_scanout_drained),.lcd_error(lcd_error),.lcd_front_generation(lcd_front_generation),.lcd_front_frame_id(lcd_front_frame_id),.lcd_presented_count(lcd_presented_count),.lcd_underruns(lcd_underruns),.lcd_memory_errors(lcd_memory_errors),.hsync(hsync),.vsync(vsync),.data_enable(data_enable),.physical_x(physical_x),.physical_y(physical_y),.red(red),.green(green),.blue(blue),.painter_busy(painter_busy),.painter_error(painter_error),.painter_error_code(painter_error_code),.painter_reads(painter_reads),.painter_writes(painter_writes),.painter_pixels(painter_pixels),.painter_cycles(painter_cycles),.memory_tile_busy(memory_tile_busy),.memory_aux_busy(memory_aux_busy),.memory_idle(memory_idle),.memory_cache_hits(memory_cache_hits),.memory_cache_misses(memory_cache_misses),.memory_reads(memory_reads),.memory_writes(memory_writes),.sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));

 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign peek_data=model.mem[peek_address];
 assign model_reads=32'(model.reads);assign model_writes=32'(model.writes);assign model_refreshes=32'(model.refreshes);
endmodule
`default_nettype wire
