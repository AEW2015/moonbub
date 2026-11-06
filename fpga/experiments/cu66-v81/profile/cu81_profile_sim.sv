`timescale 1ns/1ps
module cu81_profile_sim #(parameter integer PREFETCH_ENABLE=3,parameter integer WATCHDOG_CYCLES=64000000,COMMIT_RETRY_CYCLES=64,P0_CACHE_LINES=8,POWERUP_CYCLES=20,REFRESH_CYCLES=750,parameter real TAC_NS=2.0)(
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
    output logic [4:0] trace_path_events,
    output logic [63:0] trace_pref_req_generation,output logic [1:0] trace_pref_req_bank,trace_pref_req_plane,output logic [16:0] trace_pref_req_index,output logic [23:0] trace_pref_req_address,
    output logic [63:0] trace_snapshot_generation,output logic [1:0] trace_snapshot_bank,trace_snapshot_plane,output logic [16:0] trace_snapshot_index,output logic [23:0] trace_snapshot_address,
    output logic [63:0] trace_block_generation,output logic [1:0] trace_block_bank,trace_block_plane,output logic [16:0] trace_block_index,output logic [23:0] trace_block_address,
    output logic [63:0] trace_backend_done_generation,output logic [1:0] trace_backend_done_bank,trace_backend_done_plane,output logic [16:0] trace_backend_done_index,
    output logic [3:0] profile_fs,profile_ts,profile_idct_state,profile_controller_state,
    output logic [2:0] profile_bridge_state,profile_hash_fill,
    output logic [1:0] profile_hash_core,
    output logic [23:0] profile_flags,
    input logic [23:0] peek_address,output logic [15:0] peek_data,
    output logic [31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,model_write_commands,model_write_bus_beats,
    output logic [31:0] write_event_sequence,output logic [23:0] write_event_address,output logic [15:0] write_event_data
);
 wire[12:0] sdram_a;wire[1:0] sdram_bs,sdram_cke,sdram_cs_n;wire[15:0]sdram_dq;
 wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm;
 cu81_system #(.PREFETCH_ENABLE(PREFETCH_ENABLE),.WATCHDOG_CYCLES(WATCHDOG_CYCLES),.P0_CACHE_LINES(P0_CACHE_LINES),.COMMIT_RETRY_CYCLES(COMMIT_RETRY_CYCLES),.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) hardware(.*);
 cu72_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES),.T_AC_NS(TAC_NS)) model(.reset(rst),.clk(sdram_clk),.a(sdram_a),.ba(sdram_bs),.cke(sdram_cke),.cs(sdram_cs_n),.ras(sdram_ras_n),.cas(sdram_cas_n),.we(sdram_we_n),.ldqm(sdram_ldqm),.udqm(sdram_udqm),.dq(sdram_dq));
  if(PREFETCH_ENABLE==0)begin:g_trace_legacy
  assign trace_command_valid=hardware.g_legacy.memory.mem_req_valid&&hardware.g_legacy.memory.mem_req_ready;
  assign trace_command_write=hardware.g_legacy.memory.mem_req_write;
  assign trace_command_address=hardware.g_legacy.memory.mem_req_addr;
  assign trace_command_client=hardware.g_legacy.memory.bridge.lcd_owner?2'd2:hardware.g_legacy.memory.bridge.owner?2'd1:2'd0;
 end else if(PREFETCH_ENABLE==3)begin:g_trace_wide
  assign trace_command_valid=hardware.g_wide.memory.command_valid;
  assign trace_command_write=hardware.g_wide.memory.command_write;
  assign trace_command_address=hardware.g_wide.memory.command_address;
  assign trace_command_client=hardware.g_wide.memory.command_client;
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
 assign trace_path_events[0]=hardware.ref_req_valid;
 generate if(PREFETCH_ENABLE==3)begin:g_path_wide
  assign trace_path_events[1]=hardware.g_wide.pr_valid&&hardware.g_wide.pr_ready;
  assign trace_path_events[2]=hardware.g_wide.memory.snapshot_valid;
  assign trace_path_events[3]=hardware.g_wide.reference_path.core.block_commit;
  assign trace_path_events[4]=hardware.g_wide.md_valid&&hardware.g_wide.md_ready;
  assign trace_pref_req_generation=hardware.g_wide.pr_generation;
  assign trace_snapshot_generation=hardware.g_wide.memory.owned_generation;
  assign trace_block_generation=hardware.g_wide.ps_generation;
  assign trace_backend_done_generation=hardware.g_wide.md_generation;
  assign trace_pref_req_bank=hardware.g_wide.pr_bank;
  assign trace_snapshot_bank=hardware.g_wide.memory.owned_bank;
  assign trace_block_bank=hardware.g_wide.ps_bank;
  assign trace_backend_done_bank=hardware.g_wide.md_bank;
  assign trace_pref_req_plane=hardware.g_wide.pr_plane;
  assign trace_snapshot_plane=hardware.g_wide.memory.owned_plane;
  assign trace_block_plane=hardware.g_wide.ps_plane;
  assign trace_backend_done_plane=hardware.g_wide.md_plane;
  assign trace_pref_req_index=hardware.g_wide.pr_index;
  assign trace_snapshot_index=hardware.g_wide.memory.owned_index;
  assign trace_block_index=hardware.g_wide.ps_index;
  assign trace_backend_done_index=hardware.g_wide.md_index;
  assign trace_pref_req_address=hardware.g_wide.pr_address;
  assign trace_snapshot_address=hardware.g_wide.memory.snapshot_address;
  assign trace_block_address=hardware.g_wide.reference_path.core.block_commit_address;
 end else begin:g_path_old
  assign trace_path_events[3:1]=0;
  assign trace_pref_req_generation=0;
  assign trace_pref_req_bank=0;
  assign trace_pref_req_plane=0;
  assign trace_pref_req_index=0;
  assign trace_pref_req_address=0;
  assign trace_snapshot_generation=0;
  assign trace_snapshot_bank=0;
  assign trace_snapshot_plane=0;
  assign trace_snapshot_index=0;
  assign trace_snapshot_address=0;
  assign trace_block_generation=0;
  assign trace_block_bank=0;
  assign trace_block_plane=0;
  assign trace_block_index=0;
  assign trace_block_address=0;
  if(PREFETCH_ENABLE==0)begin:g_backend_legacy
   assign trace_path_events[4]=hardware.write_done_valid&&hardware.write_done_ready;
   assign trace_backend_done_generation=hardware.write_done_generation;
   assign trace_backend_done_bank=hardware.write_done_bank;
   assign trace_backend_done_plane=hardware.write_done_plane;
   assign trace_backend_done_index=hardware.write_done_index;
  end else begin:g_backend_prefetch
   assign trace_path_events[4]=hardware.g_prefetch.md_valid&&hardware.g_prefetch.md_ready;
   assign trace_backend_done_generation=hardware.g_prefetch.md_generation;
   assign trace_backend_done_bank=hardware.g_prefetch.md_bank;
   assign trace_backend_done_plane=hardware.g_prefetch.md_plane;
   assign trace_backend_done_index=hardware.g_prefetch.md_index;
  end
 end endgenerate
 assign peek_data=model.mem[peek_address];
 assign model_writes=32'(model.writes);assign model_reads=32'(model.reads);assign model_refreshes=32'(model.refreshes);assign model_acts=32'(model.acts);assign model_pres=32'(model.pres);
 assign model_write_commands=32'(model.write_commands);assign model_write_bus_beats=32'(model.write_bus_beats);
 assign write_event_sequence=32'(model.writes);
 assign write_event_address=model.last_write_address;assign write_event_data=model.last_write_data;
 assign profile_fs=4'(hardware.receiver.base.fs);assign profile_ts=4'(hardware.receiver.base.ts);
 assign profile_idct_state=4'(hardware.receiver.base.inverse.state);
 assign profile_hash_fill=hardware.receiver.base.canonical.hash_fill_state;assign profile_hash_core=hardware.receiver.base.canonical.hash_core_state;
 assign profile_controller_state=4'(hardware.g_wide.memory.controller.state);assign profile_bridge_state=3'(hardware.g_wide.memory.bridge.state);
 assign profile_flags[0]=hardware.receiver.base.write_pending;
 assign profile_flags[1]=hardware.receiver.base.ref_pending;
 assign profile_flags[2]=hardware.receiver.base.ref_received;
 assign profile_flags[3]=hardware.receiver.base.q_pending;
 assign profile_flags[4]=hardware.receiver.base.dq_valid&&!hardware.receiver.base.dq_out_ready;
 assign profile_flags[5]=hardware.receiver.base.idct_valid&&!hardware.receiver.base.idct_out_ready;
 assign profile_flags[6]=hardware.receiver.base.recon_valid&&!hardware.receiver.base.tile_complete;
 assign profile_flags[7]=hardware.receiver.base.tile_valid&&!hardware.receiver.base.tile_ready;
 assign profile_flags[8]=hardware.receiver.base.fs==3&&hardware.receiver.base.ts==7&&hardware.receiver.base.write_pending;
 assign profile_flags[9]=hardware.receiver.base.fs==3&&hardware.receiver.base.ts==7&&!hardware.receiver.base.rows_acked&&!hardware.receiver.base.rows_tile_ready;
 assign profile_flags[10]=hardware.receiver.base.s_valid&&!hardware.receiver.base.s_ready;
 assign profile_flags[11]=hardware.receiver.base.e_valid&&!hardware.receiver.base.e_ready;
 assign profile_flags[12]=hardware.receiver.base.canonical.write_busy;
 assign profile_flags[13]=hardware.receiver.base.canonical.hash_busy;
 assign profile_flags[14]=hardware.receiver.base.canonical.rows_busy;
 assign profile_flags[15]=hardware.g_wide.memory.p_owned;
 assign profile_flags[16]=hardware.g_wide.memory.prefetch_req_valid&&!hardware.g_wide.memory.prefetch_req_ready;
 assign profile_flags[17]=hardware.g_wide.memory.lcd_req_valid&&!hardware.g_wide.memory.lcd_req_ready;
 assign profile_flags[18]=hardware.g_wide.memory.bridge.p0_valid&&!hardware.g_wide.memory.bridge.p0_ready;
 assign profile_flags[19]=hardware.g_wide.memory.bridge.p1_valid&&!hardware.g_wide.memory.bridge.p1_ready;
 assign profile_flags[20]=hardware.g_wide.memory.controller.request_valid&&!hardware.g_wide.memory.controller.request_ready;
 assign profile_flags[21]=hardware.g_wide.memory.controller.state==4;
 assign profile_flags[22]=hardware.receiver.base.rows_fire;
 assign profile_flags[23]=hardware.receiver.base.q_req_valid&&!hardware.receiver.base.q_req_ready;
endmodule
