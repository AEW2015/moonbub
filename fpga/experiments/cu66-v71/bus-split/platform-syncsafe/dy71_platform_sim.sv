`timescale 1ns/1ps
`default_nettype none
// Actual DY71 SYNCsafe/math owner, typed local CSR, immutable stager/arbiter and checked
// SDRAM pins. No physical SPI endpoint/CDC/PLL model and no CPU ACK bypass.
module dy71_platform_sim(
 input wire  clk,
 input wire  read_clk,
 input wire  pixel_clk,
 input wire  pixel_reset_n,
 input wire  rst,
 input wire  bus_write,
 input wire [11:0] bus_address,
 input wire [31:0] bus_wdata,
 input wire  transport_fault,
 output wire [31:0] bus_rdata,
 input wire [23:0] peek_address,
 output wire [15:0] peek_data,
 output wire [31:0] model_reads,
 output wire [31:0] model_writes,
 output wire [31:0] model_refreshes,
 output wire [31:0] cpu_packet_requests,
 output wire [31:0] cpu_aux_requests,
 output wire [31:0] cpu_aux_completions,
 output wire [31:0] cpu_hud_result_calls,
 output wire [31:0] cpu_hud_drain_calls,
 output wire [31:0] cpu_software_ack_calls,
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
 output wire  front_cache_slot,
 output wire [31:0] profile_magic,
 output wire [31:0] profile_abi,
 output wire [31:0] profile_capabilities
);
 wire  start_valid;
 wire  start_ready;
 wire [63:0] start_generation;
 wire [31:0] start_packet_bytes;
 wire  abort_i;
 wire  clear_fault;
 wire  done;
 wire  memory_tile_busy;
 wire  memory_aux_busy;
 wire  packet_req_valid;
 wire  packet_req_ready;
 wire [15:0] packet_req_address;
 wire [63:0] packet_req_generation;
 wire [31:0] packet_req_sequence;
 wire  packet_rsp_valid;
 wire  packet_rsp_ready;
 wire [15:0] packet_rsp_address;
 wire [63:0] packet_rsp_generation;
 wire [31:0] packet_rsp_sequence;
 wire [7:0] packet_rsp_data;
 wire  hud_prepare_valid;
 wire  hud_prepare_ready;
 wire [63:0] active_generation;
 wire [31:0] active_frame_id;
 wire [31:0] active_reference_id;
 wire  active_key;
 wire [15:0] hud_address;
 wire [15:0] hud_bytes;
 wire [127:0] expected_hud_tag;
 wire [1:0] candidate_bank;
 wire  hud_result_valid;
 wire  hud_result_ready;
 wire [63:0] hud_result_generation;
 wire [31:0] hud_result_frame_id;
 wire [31:0] hud_result_reference_id;
 wire [127:0] hud_result_tag;
 wire [15:0] hud_result_words;
 wire  hud_result_success;
 wire  hud_drain_valid;
 wire  hud_drain_ready;
 wire [63:0] hud_drain_generation;
 wire [31:0] hud_drain_frame_id;
 wire [1:0] hud_drain_bank;
 wire [127:0] hud_drain_tag;
 wire [15:0] hud_drain_words;
 wire  hud_drain_success;
 wire  software_command_valid;
 wire  software_command_ready;
 wire [2:0] software_command_opcode;
 wire  software_ack_valid;
 wire  software_ack_ready;
 wire [2:0] software_ack_opcode;
 wire [63:0] software_ack_generation;
 wire [31:0] software_ack_frame_id;
 wire  software_ack_success;
 wire  hud_aux_req_valid;
 wire  hud_aux_req_ready;
 wire [63:0] hud_aux_generation;
 wire [31:0] hud_aux_frame_id;
 wire  hud_aux_req_write;
 wire [23:0] hud_aux_req_addr;
 wire [15:0] hud_aux_req_data;
 wire  hud_aux_rsp_valid;
 wire  hud_aux_rsp_ready;
 wire [15:0] hud_aux_rsp_data;
 wire  hud_aux_rsp_error;
 wire [9:0] diag_address;
 wire [31:0] diag_data;
 wire  front_valid;
 wire [63:0] front_generation;
 wire  reference_valid;
 wire [31:0] reference_frame_id;
 wire [127:0] reference_tag;
 wire  aborted;
 wire [31:0] stale_completions;
 wire  lcd_front_valid;
 wire  lcd_front_slot;
 wire  lcd_presented;
 wire  lcd_pending;
 wire  lcd_frame_boundary;
 wire  lcd_scanout_drained;
 wire  lcd_error;
 wire [63:0] lcd_front_generation;
 wire [31:0] lcd_front_frame_id;
 wire [31:0] lcd_presented_count;
 wire [31:0] lcd_memory_errors;
 wire  hsync;
 wire  vsync;
 wire  data_enable;
 wire [9:0] physical_x;
 wire [9:0] physical_y;
 wire [7:0] red;
 wire [7:0] green;
 wire [7:0] blue;
 wire  cache_prepare_busy;
 wire  cache_prepare_fault;
 wire [31:0] cache_dma_reads;
 wire [31:0] cache_line_misses;
 wire [31:0] cache_generated_lines;
 wire [31:0] cache_prepare_cycles;
 wire [31:0] cache_accepted_prepares;
 wire [31:0] cache_rejected_prepares;
 wire [31:0] cache_rejected_descriptors;
 wire [31:0] cache_unowned_responses;
 wire  memory_idle;
 wire [31:0] memory_cache_hits;
 wire [31:0] memory_cache_misses;
 wire [31:0] memory_reads;
 wire [31:0] memory_writes;
 wire [12:0] sdram_a;
 wire [1:0] sdram_bs;
 wire [1:0] sdram_cke;
 wire [1:0] sdram_cs_n;
 wire [15:0] sdram_dq;
 wire  sdram_clk;
 wire  sdram_ras_n;
 wire  sdram_cas_n;
 wire  sdram_we_n;
 wire  sdram_ldqm;
 wire  sdram_udqm;
 dy71_local_control_split control_plane(
 .bus_read_address(bus_address),
 .clk(clk),
 .rst(rst),
 .bus_write(bus_write),
 .bus_address(bus_address),
 .bus_wdata(bus_wdata),
 .bus_rdata(bus_rdata),
 .transport_fault(transport_fault),
 .start_valid(start_valid),
 .start_ready(start_ready),
 .start_generation(start_generation),
 .start_packet_bytes(start_packet_bytes),
 .abort_i(abort_i),
 .clear_fault(clear_fault),
 .busy(busy),
 .done(done),
 .error(error),
 .stage(stage),
 .error_code(error_code),
 .memory_tile_busy(memory_tile_busy),
 .memory_aux_busy(memory_aux_busy),
 .accepted_count(accepted_count),
 .presented_count(presented_count),
 .rejected_count(rejected_count),
 .lcd_underruns(lcd_underruns),
 .packet_req_valid(packet_req_valid),
 .packet_req_ready(packet_req_ready),
 .packet_req_address(packet_req_address),
 .packet_req_generation(packet_req_generation),
 .packet_req_sequence(packet_req_sequence),
 .packet_rsp_valid(packet_rsp_valid),
 .packet_rsp_ready(packet_rsp_ready),
 .packet_rsp_address(packet_rsp_address),
 .packet_rsp_generation(packet_rsp_generation),
 .packet_rsp_sequence(packet_rsp_sequence),
 .packet_rsp_data(packet_rsp_data),
 .hud_prepare_valid(hud_prepare_valid),
 .hud_prepare_ready(hud_prepare_ready),
 .active_generation(active_generation),
 .active_frame_id(active_frame_id),
 .active_reference_id(active_reference_id),
 .active_key(active_key),
 .hud_address(hud_address),
 .hud_bytes(hud_bytes),
 .expected_hud_tag(expected_hud_tag),
 .candidate_bank(candidate_bank),
 .hud_result_valid(hud_result_valid),
 .hud_result_ready(hud_result_ready),
 .hud_result_generation(hud_result_generation),
 .hud_result_frame_id(hud_result_frame_id),
 .hud_result_reference_id(hud_result_reference_id),
 .hud_result_tag(hud_result_tag),
 .hud_result_words(hud_result_words),
 .hud_result_success(hud_result_success),
 .hud_drain_valid(hud_drain_valid),
 .hud_drain_ready(hud_drain_ready),
 .hud_drain_generation(hud_drain_generation),
 .hud_drain_frame_id(hud_drain_frame_id),
 .hud_drain_bank(hud_drain_bank),
 .hud_drain_tag(hud_drain_tag),
 .hud_drain_words(hud_drain_words),
 .hud_drain_success(hud_drain_success),
 .software_command_valid(software_command_valid),
 .software_command_ready(software_command_ready),
 .software_command_opcode(software_command_opcode),
 .software_ack_valid(software_ack_valid),
 .software_ack_ready(software_ack_ready),
 .software_ack_opcode(software_ack_opcode),
 .software_ack_generation(software_ack_generation),
 .software_ack_frame_id(software_ack_frame_id),
 .software_ack_success(software_ack_success),
 .hud_aux_req_valid(hud_aux_req_valid),
 .hud_aux_req_ready(hud_aux_req_ready),
 .hud_aux_generation(hud_aux_generation),
 .hud_aux_frame_id(hud_aux_frame_id),
 .hud_aux_req_write(hud_aux_req_write),
 .hud_aux_req_addr(hud_aux_req_addr),
 .hud_aux_req_data(hud_aux_req_data),
 .hud_aux_rsp_valid(hud_aux_rsp_valid),
 .hud_aux_rsp_ready(hud_aux_rsp_ready),
 .hud_aux_rsp_data(hud_aux_rsp_data),
 .hud_aux_rsp_error(hud_aux_rsp_error),
 .diag_address(diag_address),
 .diag_data(diag_data),
 .quarantine(quarantine)
);
 cu71_system_direct_syncsafe #(.WATCHDOG_CYCLES(32'd3000000000),.POWERUP_CYCLES(20),.REFRESH_CYCLES(750)) system_core(
 .clk(clk),
 .read_clk(read_clk),
 .pixel_clk(pixel_clk),
 .pixel_reset_n(pixel_reset_n),
 .rst(rst),
 .abort_i(abort_i),
 .clear_fault(clear_fault),
 .start_valid(start_valid),
 .start_ready(start_ready),
 .start_generation(start_generation),
 .start_packet_bytes(start_packet_bytes),
 .packet_req_valid(packet_req_valid),
 .packet_req_ready(packet_req_ready),
 .packet_req_address(packet_req_address),
 .packet_req_generation(packet_req_generation),
 .packet_req_sequence(packet_req_sequence),
 .packet_rsp_valid(packet_rsp_valid),
 .packet_rsp_ready(packet_rsp_ready),
 .packet_rsp_generation(packet_rsp_generation),
 .packet_rsp_sequence(packet_rsp_sequence),
 .packet_rsp_address(packet_rsp_address),
 .packet_rsp_data(packet_rsp_data),
 .hud_prepare_valid(hud_prepare_valid),
 .hud_prepare_ready(hud_prepare_ready),
 .active_generation(active_generation),
 .active_frame_id(active_frame_id),
 .active_reference_id(active_reference_id),
 .active_key(active_key),
 .hud_address(hud_address),
 .hud_bytes(hud_bytes),
 .expected_hud_tag(expected_hud_tag),
 .candidate_bank(candidate_bank),
 .hud_result_valid(hud_result_valid),
 .hud_result_ready(hud_result_ready),
 .hud_result_generation(hud_result_generation),
 .hud_result_frame_id(hud_result_frame_id),
 .hud_result_reference_id(hud_result_reference_id),
 .hud_result_tag(hud_result_tag),
 .hud_result_words(hud_result_words),
 .hud_result_success(hud_result_success),
 .hud_drain_valid(hud_drain_valid),
 .hud_drain_ready(hud_drain_ready),
 .hud_drain_generation(hud_drain_generation),
 .hud_drain_frame_id(hud_drain_frame_id),
 .hud_drain_bank(hud_drain_bank),
 .hud_drain_tag(hud_drain_tag),
 .hud_drain_words(hud_drain_words),
 .hud_drain_success(hud_drain_success),
 .software_command_valid(software_command_valid),
 .software_command_ready(software_command_ready),
 .software_command_opcode(software_command_opcode),
 .software_ack_valid(software_ack_valid),
 .software_ack_ready(software_ack_ready),
 .software_ack_opcode(software_ack_opcode),
 .software_ack_generation(software_ack_generation),
 .software_ack_frame_id(software_ack_frame_id),
 .software_ack_success(software_ack_success),
 .front_valid(front_valid),
 .front_cache_slot(front_cache_slot),
 .front_bank(front_bank),
 .front_generation(front_generation),
 .front_frame_id(front_frame_id),
 .reference_valid(reference_valid),
 .reference_bank(reference_bank),
 .reference_frame_id(reference_frame_id),
 .reference_tag(reference_tag),
 .busy(busy),
 .done(done),
 .aborted(aborted),
 .error(error),
 .error_code(error_code),
 .stage(stage),
 .accepted_count(accepted_count),
 .presented_count(presented_count),
 .rejected_count(rejected_count),
 .stale_completions(stale_completions),
 .diag_address(diag_address),
 .diag_data(diag_data),
 .hud_aux_req_valid(hud_aux_req_valid),
 .hud_aux_req_ready(hud_aux_req_ready),
 .hud_aux_generation(hud_aux_generation),
 .hud_aux_frame_id(hud_aux_frame_id),
 .hud_aux_req_write(hud_aux_req_write),
 .hud_aux_req_addr(hud_aux_req_addr),
 .hud_aux_req_data(hud_aux_req_data),
 .hud_aux_rsp_valid(hud_aux_rsp_valid),
 .hud_aux_rsp_ready(hud_aux_rsp_ready),
 .hud_aux_rsp_data(hud_aux_rsp_data),
 .hud_aux_rsp_error(hud_aux_rsp_error),
 .lcd_front_valid(lcd_front_valid),
 .lcd_front_slot(lcd_front_slot),
 .lcd_presented(lcd_presented),
 .lcd_pending(lcd_pending),
 .lcd_frame_boundary(lcd_frame_boundary),
 .lcd_scanout_drained(lcd_scanout_drained),
 .lcd_error(lcd_error),
 .lcd_front_generation(lcd_front_generation),
 .lcd_front_frame_id(lcd_front_frame_id),
 .lcd_presented_count(lcd_presented_count),
 .lcd_underruns(lcd_underruns),
 .lcd_memory_errors(lcd_memory_errors),
 .hsync(hsync),
 .vsync(vsync),
 .data_enable(data_enable),
 .physical_x(physical_x),
 .physical_y(physical_y),
 .red(red),
 .green(green),
 .blue(blue),
 .profile_magic(profile_magic),
 .profile_abi(profile_abi),
 .profile_capabilities(profile_capabilities),
 .cache_prepare_busy(cache_prepare_busy),
 .cache_prepare_fault(cache_prepare_fault),
 .cache_dma_reads(cache_dma_reads),
 .cache_line_misses(cache_line_misses),
 .cache_generated_lines(cache_generated_lines),
 .cache_prepare_cycles(cache_prepare_cycles),
 .cache_accepted_prepares(cache_accepted_prepares),
 .cache_rejected_prepares(cache_rejected_prepares),
 .cache_rejected_descriptors(cache_rejected_descriptors),
 .cache_unowned_responses(cache_unowned_responses),
 .memory_tile_busy(memory_tile_busy),
 .memory_aux_busy(memory_aux_busy),
 .memory_idle(memory_idle),
 .memory_cache_hits(memory_cache_hits),
 .memory_cache_misses(memory_cache_misses),
 .memory_reads(memory_reads),
 .memory_writes(memory_writes),
 .sdram_a(sdram_a),
 .sdram_bs(sdram_bs),
 .sdram_cke(sdram_cke),
 .sdram_cs_n(sdram_cs_n),
 .sdram_dq(sdram_dq),
 .sdram_clk(sdram_clk),
 .sdram_ras_n(sdram_ras_n),
 .sdram_cas_n(sdram_cas_n),
 .sdram_we_n(sdram_we_n),
 .sdram_ldqm(sdram_ldqm),
 .sdram_udqm(sdram_udqm)
);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign peek_data=model.mem[peek_address];
 assign model_reads=32'(model.reads);assign model_writes=32'(model.writes);assign model_refreshes=32'(model.refreshes);
 reg[31:0]packet_observed=0,aux_observed=0,aux_completed=0,hud_results=0,hud_drains=0,software_acks=0;
 always @(posedge clk)begin
  if(rst)begin packet_observed<=0;aux_observed<=0;aux_completed<=0;hud_results<=0;hud_drains<=0;software_acks<=0;end
  else begin
   if(control_plane.cpu_req_valid&&control_plane.cpu_req_ready)packet_observed<=packet_observed+1;
   if(hud_aux_req_valid&&hud_aux_req_ready)aux_observed<=aux_observed+1;
   if(hud_aux_rsp_valid&&hud_aux_rsp_ready)aux_completed<=aux_completed+1;
   if(hud_result_valid&&hud_result_ready)hud_results<=hud_results+1;
   if(hud_drain_valid&&hud_drain_ready)hud_drains<=hud_drains+1;
   if(software_ack_valid&&software_ack_ready)software_acks<=software_acks+1;
  end
 end
 assign cpu_packet_requests=packet_observed;assign cpu_aux_requests=aux_observed;assign cpu_aux_completions=aux_completed;
 assign cpu_hud_result_calls=hud_results;assign cpu_hud_drain_calls=hud_drains;assign cpu_software_ack_calls=software_acks;
endmodule
`default_nettype wire
