// Integrated receiver, canonical memory, painter and native LCD descriptor path.
`timescale 1ns/1ps
module cu74_system_sim #(
    parameter integer WATCHDOG_CYCLES=64000000,
    parameter integer COMMIT_RETRY_CYCLES=64,
    parameter integer USE_STRIP=1,
    parameter integer P0_CACHE_LINES=8,
    parameter integer POWERUP_CYCLES=20,REFRESH_CYCLES=750
)(
    input logic clk,read_clk,pixel_clk,pixel_reset_n,rst,abort_i,clear_fault,
    input logic start_valid,output logic start_ready,
    input logic [63:0] start_generation,
    input logic [31:0] start_packet_bytes,
    output logic packet_req_valid,input logic packet_req_ready,
    output logic [15:0] packet_req_address,
    output logic [63:0] packet_req_generation,
    output logic [31:0] packet_req_sequence,
    input logic packet_rsp_valid,output logic packet_rsp_ready,
    input logic [63:0] packet_rsp_generation,
    input logic [31:0] packet_rsp_sequence,input logic [15:0] packet_rsp_address,
    input logic [7:0] packet_rsp_data,
    output logic hud_prepare_valid,input logic hud_prepare_ready,
    output logic [63:0] active_generation,
    output logic [31:0] active_frame_id,active_reference_id,
    output logic active_key,
    output logic [15:0] hud_address,hud_bytes,
    output logic [127:0] expected_hud_tag,
    output logic [1:0] candidate_bank,
    input logic hud_result_valid,output logic hud_result_ready,
    input logic [63:0] hud_result_generation,
    input logic [31:0] hud_result_frame_id,hud_result_reference_id,
    input logic [127:0] hud_result_tag,
    input logic [15:0] hud_result_words,input logic hud_result_success,
    input logic hud_drain_valid,output logic hud_drain_ready,
    input logic [63:0] hud_drain_generation,
    input logic [31:0] hud_drain_frame_id,
    input logic [1:0] hud_drain_bank,
    input logic [127:0] hud_drain_tag,
    input logic [15:0] hud_drain_words,input logic hud_drain_success,
    output logic software_command_valid,input logic software_command_ready,
    output logic [2:0] software_command_opcode,
    input logic software_ack_valid,output logic software_ack_ready,
    input logic [2:0] software_ack_opcode,
    input logic [63:0] software_ack_generation,
    input logic [31:0] software_ack_frame_id,input logic software_ack_success,
    output logic front_valid,front_rgb_slot,
    output logic [1:0] front_bank,
    output logic [63:0] front_generation,
    output logic [31:0] front_frame_id,
    output logic reference_valid,
    output logic [1:0] reference_bank,
    output logic [31:0] reference_frame_id,
    output logic [127:0] reference_tag,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,stage,
    output logic [31:0] accepted_count,presented_count,rejected_count,stale_completions,
    input logic [9:0] diag_address,output logic [31:0] diag_data,
    input logic hud_aux_req_valid,output logic hud_aux_req_ready,
    input logic [63:0] hud_aux_generation,input logic [31:0] hud_aux_frame_id,
    input logic hud_aux_req_write,input logic [23:0] hud_aux_req_addr,input logic [15:0] hud_aux_req_data,
    output logic hud_aux_rsp_valid,input logic hud_aux_rsp_ready,
    output logic [15:0] hud_aux_rsp_data,output logic hud_aux_rsp_error,
    output logic lcd_front_valid,lcd_front_slot,lcd_presented,lcd_pending,lcd_frame_boundary,lcd_scanout_drained,lcd_error,
    output logic [63:0] lcd_front_generation,output logic [31:0] lcd_front_frame_id,lcd_presented_count,
    output logic [31:0] lcd_underruns,lcd_memory_errors,
    output logic hsync,vsync,data_enable,output logic [9:0] physical_x,physical_y,
    output logic [7:0] red,green,blue,
    output logic painter_busy,painter_error,output logic [7:0] painter_error_code,
    output logic [31:0] painter_reads,painter_read_words,painter_writes,painter_write_words,painter_pixels,painter_cycles,
    output logic memory_tile_busy,memory_aux_busy,memory_idle,
    output logic [31:0] memory_cache_hits,memory_cache_misses,memory_reads,memory_writes,
    output logic [31:0] p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles,
    input logic [23:0] peek_address,output logic [15:0] peek_data,
    output logic [31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,model_write_commands,model_write_bus_beats,
    output logic [31:0] write_event_sequence,output logic [23:0] write_event_address,output logic [15:0] write_event_data
);
 wire[12:0] sdram_a;wire[1:0] sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu74_system #(.WATCHDOG_CYCLES(WATCHDOG_CYCLES),.P0_CACHE_LINES(P0_CACHE_LINES),.USE_STRIP(USE_STRIP),.COMMIT_RETRY_CYCLES(COMMIT_RETRY_CYCLES),.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) hardware(.*);
 cu72_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign peek_data=model.mem[peek_address];
 assign model_writes=32'(model.writes);assign model_reads=32'(model.reads);assign model_refreshes=32'(model.refreshes);assign model_acts=32'(model.acts);assign model_pres=32'(model.pres);
 assign model_write_commands=32'(model.write_commands);assign model_write_bus_beats=32'(model.write_bus_beats);
 assign write_event_sequence=32'(model.writes);
 assign write_event_address=model.last_write_address;assign write_event_data=model.last_write_data;
endmodule
