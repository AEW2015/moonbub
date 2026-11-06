// CU71 successor: qualified memory backend and dedicated BL8 scanout.
// Integrated receiver, canonical memory, painter and native LCD descriptor path.
`timescale 1ns/1ps
module cu71_direct_system_sim #(
    parameter integer WATCHDOG_CYCLES=64000000,
    parameter integer COMMIT_RETRY_CYCLES=64,
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
    output logic front_valid,front_cache_slot,
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
    output wire [31:0] profile_magic,profile_abi,profile_capabilities,
    output wire cache_prepare_busy,cache_prepare_fault,
    output wire [31:0] cache_dma_reads,cache_line_misses,cache_generated_lines,cache_prepare_cycles,
    output wire [31:0] cache_accepted_prepares,cache_rejected_prepares,cache_rejected_descriptors,
    output wire [31:0] cache_unowned_responses,
    output logic memory_tile_busy,memory_aux_busy,memory_idle,
    output logic [31:0] memory_cache_hits,memory_cache_misses,memory_reads,memory_writes,
    input logic [23:0] peek_address,output logic [15:0] peek_data,
    output logic [31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,
    output logic [31:0] write_event_sequence,output logic [23:0] write_event_address,output logic [15:0] write_event_data,
    output wire [31:0] rgb_completed_writes,
    output wire [31:0] group_lcd_count,group_bg_count,group_idle,group_lcd_idle,group_bg_idle,group_lcd_expiry,group_bg_expiry,group_bg_wait,group_lcd_wait,
    output wire[3:0]prof_fs,prof_ts,
    output wire[31:0]prof_flags,prof_base_cycles,prof_base_tiles,prof_hash_rounds,prof_hash_blocks,
    output wire[15:0]prof_events,
    output wire[63:0]prof_clock,prof_base_at,prof_hud_at,prof_prepared_at,
    output wire[31:0]prof_entropy_decisions,prof_entropy_renorm,prof_entropy_reads,prof_entropy_stalls,
    output wire[31:0]prof_ref_flags,prof_current_tile,prof_adapter_tile,
    output wire[3:0]prof_controller_state,
    output wire[1:0]prof_adapter_state,prof_bridge_owner,prof_bridge_state,
    output wire[15:0]prof_physical_flags,
    output wire[63:0]prof_adapter_generation
);
 wire[12:0] sdram_a;wire[1:0] sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu71_system_direct_syncsafe #(.WATCHDOG_CYCLES(WATCHDOG_CYCLES),.COMMIT_RETRY_CYCLES(COMMIT_RETRY_CYCLES),.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) hardware(.*);
 sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS(2.223),.CLOCK_FLIGHT_NS(0.757),.T_OH_NS(2.223)) model(.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
 assign peek_data=model.mem[peek_address];
 assign model_writes=32'(model.writes);assign model_reads=32'(model.reads);assign model_refreshes=32'(model.refreshes);assign model_acts=32'(model.acts);assign model_pres=32'(model.pres);
 assign write_event_sequence=32'(model.writes);
 always @(posedge model.device_clock)begin
  if(rst)begin write_event_address<=0;write_event_data<=0;end
  else if(sdram_cke[0]&&!sdram_cs_n[0]&&{sdram_ras_n,sdram_cas_n,sdram_we_n}==3'b100)begin
   write_event_address<={sdram_bs,model.rows[sdram_bs],sdram_a[8:0]};write_event_data<=sdram_dq;
  end
 end
 assign rgb_completed_writes=hardware.memory.rgb_completed_writes;
 assign group_lcd_count=hardware.memory.bridge.group_lcd_accepted;
 assign group_bg_count=hardware.memory.bridge.group_bg_accepted;
 assign group_idle=hardware.memory.bridge.group_reserved_idle;
 assign group_lcd_idle=hardware.memory.bridge.group_lcd_reserved_idle;
 assign group_bg_idle=hardware.memory.bridge.group_bg_reserved_idle;
 assign group_lcd_expiry=hardware.memory.bridge.group_lcd_expiry;
 assign group_bg_expiry=hardware.memory.bridge.group_bg_expiry;
 assign group_bg_wait=hardware.memory.bridge.group_bg_max_wait;
 assign group_lcd_wait=hardware.memory.lcd_max_wait;
 assign prof_fs=hardware.receiver.base.fs;assign prof_ts=hardware.receiver.base.ts;
 assign prof_flags={(hardware.receiver.base.canonical.data_valid&&!hardware.receiver.base.canonical.data_ready),(hardware.receiver.base.e_valid&&!hardware.receiver.base.e_ready),(hardware.receiver.base.canonical.hash_core_state==1),hardware.receiver.base.canonical.write_busy,hardware.receiver.base.write_pending,(hardware.receiver.base.inverse.state!=0&&hardware.receiver.base.inverse.state!=9),hardware.receiver.base.e_ready,hardware.receiver.base.e_valid,hardware.receiver.base.idct_out_ready,hardware.receiver.base.rows_tile_ready,hardware.receiver.base.q_pending,hardware.receiver.base.byte_pending,hardware.receiver.base.canonical.rows_busy,hardware.receiver.base.canonical.hash_busy,hardware.receiver.base.e_busy,hardware.receiver.base.s_ready,hardware.receiver.base.s_valid,hardware.receiver.base.rows_fire,hardware.receiver.base.rows_acked,hardware.receiver.base.write_fire,hardware.receiver.base.memory_acked,hardware.receiver.base.recon_ready,hardware.receiver.base.idct_valid,hardware.receiver.write_pending,hardware.receiver.ref_pending,hardware.receiver.base.ref_received,hardware.receiver.base.hidden,hardware.receiver.base.is_key,hardware.receiver.memory_drained,hardware.receiver.hud_written,hardware.receiver.hud_good,hardware.receiver.base_good};
 assign prof_events={1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,hardware.receiver.base.entropy.done,hardware.receiver.base.tile_complete,hardware.receiver.base.rows_fire,(hardware.receiver.base.inverse.out_valid&&hardware.receiver.base.inverse.out_ready),(hardware.receiver.base.inverse.in_valid&&hardware.receiver.base.inverse.in_ready),(hardware.receiver.write_done_valid&&hardware.receiver.write_done_ready&&hardware.receiver.write_match),(hardware.receiver.write_valid&&hardware.receiver.write_ready),(hardware.receiver.ref_rsp_valid&&hardware.receiver.ref_rsp_ready&&hardware.receiver.ref_match),(hardware.receiver.ref_req_valid&&hardware.receiver.ref_req_ready)};
 assign prof_clock=hardware.receiver.clock_count;
 assign prof_base_at=hardware.receiver.base_at;
 assign prof_hud_at=hardware.receiver.hud_at;
 assign prof_prepared_at=hardware.receiver.prepared_at;
 assign prof_base_cycles=hardware.receiver.b_cycles;
 assign prof_base_tiles=hardware.receiver.b_tiles;
 assign prof_hash_rounds=hardware.receiver.base.canonical.hash_rounds;
 assign prof_hash_blocks=hardware.receiver.base.canonical.hash_blocks;
 assign prof_entropy_decisions=hardware.receiver.base.entropy.decoded_decisions;
 assign prof_entropy_renorm=hardware.receiver.base.entropy.renormalizations;
 assign prof_entropy_reads=hardware.receiver.base.entropy.memory_reads;
 assign prof_entropy_stalls=hardware.receiver.base.entropy.output_stall_cycles;
 assign prof_ref_flags={hardware.memory.tiles.word_rsp_valid,hardware.memory.tiles.word_req_ready,hardware.memory.tiles.word_req_valid,hardware.memory.tiles.choose_write,hardware.memory.tiles.prefer_write,hardware.memory.tiles.failed,hardware.memory.tiles.aborting,hardware.memory.tiles.abort_i,hardware.memory.tiles.write_done_ready,hardware.memory.tiles.write_done_valid,hardware.memory.tiles.write_ready,hardware.memory.tiles.write_valid,hardware.receiver.kill,hardware.receiver.base.kill,hardware.receiver.base.ref_req_ready,hardware.receiver.base.ref_req_valid,hardware.receiver.write_pending,hardware.memory.tiles.writing,hardware.memory.tiles.read_rsp_ready,hardware.memory.tiles.read_rsp_valid,hardware.memory.tiles.read_ready,hardware.memory.tiles.read_valid,hardware.receiver.base.ref_received,hardware.receiver.base.ref_rsp_ready,hardware.receiver.base.ref_rsp_valid,hardware.receiver.base.ref_pending,hardware.receiver.ref_match,hardware.receiver.ref_rsp_ready,hardware.receiver.ref_rsp_valid,hardware.receiver.ref_pending,hardware.receiver.ref_req_ready,hardware.receiver.ref_req_valid};
 assign prof_physical_flags={1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,1'b0,hardware.memory.bridge.group_phase,hardware.memory.bridge.physical_pending[0],hardware.memory.bridge.physical_pending[2],hardware.memory.bridge.physical_any,hardware.memory.bridge.hold_for_lcd,hardware.memory.controller.response_valid,hardware.memory.controller.idle,hardware.memory.controller.request_write,(hardware.memory.controller.request_valid&&hardware.memory.controller.request_ready)};
 assign prof_adapter_state=hardware.memory.tiles.state;assign prof_controller_state=hardware.memory.controller.state;assign prof_bridge_owner=hardware.memory.bridge.owner;assign prof_bridge_state=hardware.memory.bridge.state;
 assign prof_current_tile=hardware.receiver.base.tid;assign prof_adapter_tile={13'd0,hardware.memory.tiles.plane,hardware.memory.tiles.index};assign prof_adapter_generation=hardware.memory.tiles.generation;
endmodule
