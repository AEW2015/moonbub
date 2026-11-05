`timescale 1ns/1ps
// Canonical tile + scalar auxiliary + BL8 LCD clients over frozen controller commands.
// aux_busy tracks only the admitted scalar auxiliary operation; lcd_busy tracks
// the admitted LCD burst through response drain. idle includes every client.
module cu73_memory_system #(
 parameter integer POWERUP_CYCLES=20000,REFRESH_CYCLES=750,P0_CACHE_LINES=8
)(
 input logic clk,read_clk,rst,abort_i,aux_abort_i,
 input logic read_valid,output logic read_ready,input logic [63:0] read_generation,
 input logic [1:0] read_bank,read_plane,input logic [16:0] read_index,
 output logic read_rsp_valid,input logic read_rsp_ready,output logic [63:0] read_rsp_generation,
 output logic [1:0] read_rsp_bank,read_rsp_plane,output logic [16:0] read_rsp_index,
 output logic [511:0] read_rsp_pixels,output logic read_rsp_error,
 input logic write_valid,output logic write_ready,input logic [63:0] write_generation,
 input logic [1:0] write_bank,write_plane,input logic [16:0] write_index,input logic [511:0] write_pixels,
 output logic write_done_valid,input logic write_done_ready,output logic [63:0] write_done_generation,
 output logic [1:0] write_done_bank,write_done_plane,output logic [16:0] write_done_index,output logic write_done_error,
 output logic tile_busy,tile_aborted,
 input logic aux_req_valid,output logic aux_req_ready,input logic aux_req_write,input logic [23:0] aux_req_addr,input logic [15:0] aux_req_data,
 input logic aux_req_burst,input logic [127:0] aux_req_burst_data,input logic [15:0] aux_req_byte_enable,
 output logic aux_rsp_valid,input logic aux_rsp_ready,output logic [15:0] aux_rsp_data,output logic aux_rsp_error,
 output logic aux_busy,aux_aborted,
 input logic lcd_req_valid,output logic lcd_req_ready,input logic [23:0] lcd_req_addr,
 output logic lcd_rsp_valid,input logic lcd_rsp_ready,output logic [15:0] lcd_rsp_data,output logic lcd_rsp_last,lcd_rsp_error,
 output logic lcd_busy,
 output logic [31:0] cache_hits,cache_misses,completed_reads,completed_writes,
 output logic [31:0] p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles,
 output wire [12:0] sdram_a,output wire [1:0] sdram_bs,sdram_cke,sdram_cs_n,inout wire [15:0] sdram_dq,
 output wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm,
 output logic idle
);
 logic t_valid,t_ready,t_write,t_rsp_valid,t_rsp_ready,t_rsp_error;
 logic [23:0] t_addr;logic [15:0] t_data,t_rsp_data,t_byte_enable;logic t_burst,t_read_burst;logic [127:0] t_burst_data;
 logic [127:0] t_rsp_burst_data;
 logic a_valid,a_ready,a_write,a_rsp_valid,a_rsp_ready,a_rsp_error;
 logic [23:0] a_addr;logic [15:0] a_data,a_rsp_data,a_byte_enable;logic a_burst;logic [127:0] a_burst_data;
 logic aux_active,aux_issued,aux_aborting;
 logic mem_req_valid,mem_req_ready,mem_req_write,mem_rsp_valid,mem_idle,bridge_busy;
 logic [23:0] mem_req_addr;logic [15:0] mem_req_byte_enable,mem_rsp_data;logic [127:0] mem_req_burst_data;
 assign aux_req_ready=!aux_active&&!rst&&!aux_abort_i;
 assign a_valid=aux_active&&!aux_issued&&!aux_aborting&&!aux_abort_i;
 assign aux_rsp_valid=aux_active&&aux_issued&&a_rsp_valid&&!aux_aborting&&!aux_abort_i&&!rst;
 assign aux_rsp_data=a_rsp_data;assign aux_rsp_error=a_rsp_error;
 assign a_rsp_ready=aux_active&&aux_issued&&(aux_aborting||aux_abort_i||aux_rsp_ready);
 assign aux_busy=aux_active;
 assign idle=!tile_busy&&!aux_busy&&!bridge_busy&&mem_idle;
 always_ff @(posedge clk)begin
  if(rst)begin aux_active<=0;aux_issued<=0;aux_aborting<=0;aux_aborted<=0;a_addr<=0;a_data<=0;a_write<=0;a_burst<=0;a_burst_data<=0;a_byte_enable<=0;end
  else begin
   aux_aborted<=0;
   if(aux_req_valid&&aux_req_ready)begin aux_active<=1;aux_issued<=0;aux_aborting<=0;a_addr<=aux_req_addr;a_data<=aux_req_data;a_write<=aux_req_write;a_burst<=aux_req_burst;a_burst_data<=aux_req_burst_data;a_byte_enable<=aux_req_byte_enable;end
   if(a_valid&&a_ready)aux_issued<=1;
   if(aux_active&&(aux_abort_i||aux_aborting))begin
    aux_aborting<=1;
    if(!aux_issued||(a_rsp_valid&&a_rsp_ready))begin aux_active<=0;aux_issued<=0;aux_aborting<=0;aux_aborted<=1;end
   end else if(a_rsp_valid&&a_rsp_ready)begin aux_active<=0;aux_issued<=0;end
  end
 end
 cu73_tile_memory tiles(
  .clk,.rst,.abort_i,.read_valid,.read_ready,.read_generation,.read_bank,.read_plane,.read_index,
  .read_rsp_valid,.read_rsp_ready,.read_rsp_generation,.read_rsp_bank,.read_rsp_plane,.read_rsp_index,.read_rsp_pixels,.read_rsp_error,
  .write_valid,.write_ready,.write_generation,.write_bank,.write_plane,.write_index,.write_pixels,
  .write_done_valid,.write_done_ready,.write_done_generation,.write_done_bank,.write_done_plane,.write_done_index,.write_done_error,
  .tile_busy,.tile_aborted,.word_req_valid(t_valid),.word_req_ready(t_ready),.word_req_write(t_write),.word_req_addr(t_addr),.word_req_data(t_data),
  .word_req_read_burst(t_read_burst),.word_rsp_burst_data(t_rsp_burst_data),
  .word_req_burst(t_burst),.word_req_burst_data(t_burst_data),.word_req_byte_enable(t_byte_enable),
  .word_rsp_valid(t_rsp_valid),.word_rsp_ready(t_rsp_ready),.word_rsp_data(t_rsp_data),.word_rsp_error(t_rsp_error));
 cu73_word_bridge #(.P0_CACHE_LINES(P0_CACHE_LINES)) bridge(
  .clk,.rst,.p0_valid(t_valid),.p0_ready(t_ready),.p0_write(t_write),.p0_addr(t_addr),.p0_data(t_data),.p0_burst(t_burst),.p0_burst_data(t_burst_data),.p0_byte_enable(t_byte_enable),
  .p0_read_burst(t_read_burst),.p0_rsp_burst_data(t_rsp_burst_data),
  .p0_rsp_valid(t_rsp_valid),.p0_rsp_ready(t_rsp_ready),.p0_rsp_data(t_rsp_data),.p0_rsp_error(t_rsp_error),
  .p1_valid(a_valid),.p1_ready(a_ready),.p1_write(a_write),.p1_addr(a_addr),.p1_data(a_data),.p1_burst(a_burst),.p1_burst_data(a_burst_data),.p1_byte_enable(a_byte_enable),
  .p1_rsp_valid(a_rsp_valid),.p1_rsp_ready(a_rsp_ready),.p1_rsp_data(a_rsp_data),.p1_rsp_error(a_rsp_error),
  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_burst_data,.mem_req_byte_enable,.mem_rsp_valid,.mem_rsp_data,.mem_idle,
  .lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,.lcd_rsp_data,.lcd_rsp_last,.lcd_rsp_error,.lcd_busy,
  .bridge_busy,.cache_hits,.cache_misses,.completed_reads,.completed_writes,
  .p0_cache_hits,.p0_cache_misses,.p0_row_reads,.p0_wait_cycles,.p0_service_cycles,.p1_cache_hits,.p1_cache_misses,.p0_read_wait_cycles,.p0_read_service_cycles);
 cu72_sdram_controller #(.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) controller(
  .clk,.read_clk,.reset(rst),.request_valid(mem_req_valid),.request_ready(mem_req_ready),.request_write(mem_req_write),.request_address(mem_req_addr),.request_burst_data(mem_req_burst_data),.request_byte_enable(mem_req_byte_enable),
  .response_valid(mem_rsp_valid),.response_data(mem_rsp_data),.idle(mem_idle),.sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,
  .sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm);
endmodule
