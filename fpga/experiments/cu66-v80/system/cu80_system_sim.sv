`timescale 1ns/1ps
module cu80_system_sim #(parameter integer PREFETCH_ENABLE=1,parameter integer WATCHDOG_CYCLES=64000000,COMMIT_RETRY_CYCLES=64,P0_CACHE_LINES=8,POWERUP_CYCLES=20,REFRESH_CYCLES=750,parameter real TAC_NS=2.0)(
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
    output logic front_valid,validated_ready,
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
    input logic hud_aux_req_burst,hud_aux_req_read_burst,
    input logic [127:0] hud_aux_req_burst_data,input logic [15:0] hud_aux_req_byte_enable,
    output logic [127:0] hud_aux_rsp_burst_data,
    output logic hud_aux_rsp_valid,input logic hud_aux_rsp_ready,
    output logic [15:0] hud_aux_rsp_data,output logic hud_aux_rsp_error,
    output logic lcd_front_valid,output logic [1:0] lcd_front_bank,output logic lcd_presented,lcd_pending,lcd_frame_boundary,lcd_scanout_drained,lcd_error,
    output logic [63:0] lcd_front_generation,output logic [31:0] lcd_front_frame_id,lcd_presented_count,
    output logic [31:0] lcd_underruns,lcd_memory_errors,
    output logic hsync,vsync,data_enable,output logic [9:0] physical_x,physical_y,
    output logic [7:0] red,green,blue,
    output logic [31:0] cache_read_commands,cache_read_words,cache_pixel_queries,lcd_raster_count,
    output logic memory_tile_busy,memory_aux_busy,memory_idle,
    output logic [31:0] memory_cache_hits,memory_cache_misses,memory_reads,memory_writes,
    output logic [31:0] p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles,
    output logic [31:0] stream_candidate_wait_cycles,stream_idle_candidate_wait_cycles,stream_write_accepts,
    output logic prefetch_busy,prefetch_fault,prefetch_epoch_done,prefetch_epoch_aborted,
    output logic [3:0] prefetch_fault_code,
    output logic [63:0] prefetch_epoch_generation,
    output logic [31:0] prefetch_read_commands,prefetch_read_beats,prefetch_tiles_filled,prefetch_lookups,prefetch_tiles_retired,prefetch_unused_retired,
    output logic trace_command_valid,trace_command_write,output logic [23:0] trace_command_address,output logic [1:0] trace_command_client,
    output logic [3:0] trace_tile_events,
    output logic [63:0] trace_ref_req_generation,output logic [1:0] trace_ref_req_bank,trace_ref_req_plane,output logic [16:0] trace_ref_req_index,
    output logic [63:0] trace_ref_rsp_generation,output logic [1:0] trace_ref_rsp_bank,trace_ref_rsp_plane,output logic [16:0] trace_ref_rsp_index,
    output logic [63:0] trace_write_req_generation,output logic [1:0] trace_write_req_bank,trace_write_req_plane,output logic [16:0] trace_write_req_index,
    output logic [63:0] trace_write_done_generation,output logic [1:0] trace_write_done_bank,trace_write_done_plane,output logic [16:0] trace_write_done_index,
    input logic [23:0] peek_address,output logic [15:0] peek_data,
    output logic [31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,model_write_commands,model_write_bus_beats,
    output logic [31:0] write_event_sequence,output logic [23:0] write_event_address,output logic [15:0] write_event_data
);
 wire[12:0] sdram_a;wire[1:0] sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu80_system #(.PREFETCH_ENABLE(PREFETCH_ENABLE),.WATCHDOG_CYCLES(WATCHDOG_CYCLES),.P0_CACHE_LINES(P0_CACHE_LINES),.COMMIT_RETRY_CYCLES(COMMIT_RETRY_CYCLES),.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) hardware(.*);
 cu72_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES),.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
  if(PREFETCH_ENABLE==0)begin:g_trace_legacy
  assign trace_command_valid=hardware.g_legacy.memory.mem_req_valid&&hardware.g_legacy.memory.mem_req_ready;
  assign trace_command_write=hardware.g_legacy.memory.mem_req_write;
  assign trace_command_address=hardware.g_legacy.memory.mem_req_addr;
  assign trace_command_client=hardware.g_legacy.memory.bridge.lcd_owner?2'd2:hardware.g_legacy.memory.bridge.owner?2'd1:2'd0;
 end else begin:g_trace_prefetch
  assign trace_command_valid=hardware.g_prefetch.memory.command_valid;
  assign trace_command_write=hardware.g_prefetch.memory.command_write;
  assign trace_command_address=hardware.g_prefetch.memory.command_address;
  assign trace_command_client=hardware.g_prefetch.memory.command_client;
 end
 assign trace_tile_events={hardware.write_done_valid&&hardware.write_done_ready,hardware.write_valid&&hardware.write_ready,hardware.ref_rsp_valid&&hardware.ref_rsp_ready,hardware.ref_req_valid&&hardware.ref_req_ready};
 assign trace_ref_req_generation=hardware.ref_req_generation;
 assign trace_ref_req_bank=hardware.ref_req_bank;
 assign trace_ref_req_plane=hardware.ref_req_plane;
 assign trace_ref_req_index=hardware.ref_req_index;
 assign trace_ref_rsp_generation=hardware.ref_rsp_generation;
 assign trace_ref_rsp_bank=hardware.ref_rsp_bank;
 assign trace_ref_rsp_plane=hardware.ref_rsp_plane;
 assign trace_ref_rsp_index=hardware.ref_rsp_index;
 assign trace_write_req_generation=hardware.write_generation;
 assign trace_write_req_bank=hardware.write_bank;
 assign trace_write_req_plane=hardware.write_plane;
 assign trace_write_req_index=hardware.write_index;
 assign trace_write_done_generation=hardware.write_done_generation;
 assign trace_write_done_bank=hardware.write_done_bank;
 assign trace_write_done_plane=hardware.write_done_plane;
 assign trace_write_done_index=hardware.write_done_index;
 assign peek_data=model.mem[peek_address];
 assign model_writes=32'(model.writes);assign model_reads=32'(model.reads);assign model_refreshes=32'(model.refreshes);assign model_acts=32'(model.acts);assign model_pres=32'(model.pres);
 assign model_write_commands=32'(model.write_commands);assign model_write_bus_beats=32'(model.write_bus_beats);
 assign write_event_sequence=32'(model.writes);
 assign write_event_address=model.last_write_address;assign write_event_data=model.last_write_data;
endmodule
