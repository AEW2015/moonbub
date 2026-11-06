`timescale 1ns/1ps
// Canonical tile + scalar auxiliary memory clients over real controller commands.
module cu71_memory_system_burst #(
 parameter integer POWERUP_CYCLES=20000,REFRESH_CYCLES=750
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
 output logic aux_rsp_valid,input logic aux_rsp_ready,output logic [15:0] aux_rsp_data,output logic aux_rsp_error,
 output logic aux_busy,aux_aborted,
 output logic [31:0] cache_hits,cache_misses,completed_reads,completed_writes,
 output wire [12:0] sdram_a,output wire [1:0] sdram_bs,sdram_cke,sdram_cs_n,inout wire [15:0] sdram_dq,
 output wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm,
 input logic lcd_req_valid,output logic lcd_req_ready,input logic[23:0]lcd_req_addr,
 output logic lcd_rsp_valid,input logic lcd_rsp_ready,output logic[127:0]lcd_rsp_data,output logic lcd_rsp_error,
 input logic lcd_abort_i,output logic lcd_busy,lcd_aborted,
 output logic[31:0]lcd_completed_reads,lcd_max_wait,
 input logic rgb_req_valid,output logic rgb_req_ready,input logic[23:0]rgb_req_addr,input logic[127:0]rgb_req_data,input logic[15:0]rgb_req_mask,
 output logic rgb_rsp_valid,input logic rgb_rsp_ready,output logic rgb_rsp_error,
 input logic rgb_abort_i,output logic rgb_busy,rgb_aborted,
 output logic[31:0]rgb_completed_writes,rgb_max_wait,
 output logic idle
);
 logic b_valid,b_ready,b_rsp_valid,b_rsp_ready,b_rsp_error,b_active,b_issued,b_aborting;
 logic[23:0]b_addr;logic[127:0]b_data;logic[15:0]b_mask;
 assign rgb_req_ready=!b_active&&!rst&&!rgb_abort_i;
 assign b_valid=b_active&&!b_issued&&!b_aborting&&!rgb_abort_i;
 assign rgb_rsp_valid=b_active&&b_issued&&b_rsp_valid&&!b_aborting&&!rgb_abort_i&&!rst;
 assign rgb_rsp_error=b_rsp_error;
 assign b_rsp_ready=b_active&&b_issued&&(b_aborting||rgb_abort_i||rgb_rsp_ready);
 assign rgb_busy=b_active;
 always_ff @(posedge clk)begin
  if(rst)begin b_active<=0;b_issued<=0;b_aborting<=0;rgb_aborted<=0;b_addr<=0;b_data<=0;b_mask<=16'hffff;end
  else begin
   rgb_aborted<=0;
   if(rgb_req_valid&&rgb_req_ready)begin b_active<=1;b_issued<=0;b_aborting<=0;b_addr<=rgb_req_addr;b_data<=rgb_req_data;b_mask<=rgb_req_mask;end
   if(b_valid&&b_ready)b_issued<=1;
   if(b_active&&(rgb_abort_i||b_aborting))begin
    b_aborting<=1;
    if(!b_issued||(b_rsp_valid&&b_rsp_ready))begin b_active<=0;b_issued<=0;b_aborting<=0;rgb_aborted<=1;end
   end else if(b_rsp_valid&&b_rsp_ready)begin b_active<=0;b_issued<=0;end
  end
 end
 logic t_valid,t_ready,t_write,t_rsp_valid,t_rsp_ready,t_rsp_error;logic[127:0]t_burst_data;logic[15:0]t_burst_mask;
 logic [23:0] t_addr;logic [15:0] t_data,t_rsp_data;
 logic a_valid,a_ready,a_write,a_rsp_valid,a_rsp_ready,a_rsp_error;
 logic [23:0] a_addr;logic [15:0] a_data,a_rsp_data;
 logic aux_active,aux_issued,aux_aborting;
 logic mem_req_valid,mem_req_ready,mem_req_write,mem_rsp_valid,mem_idle,bridge_busy;
 logic [23:0] mem_req_addr;logic[127:0]mem_req_burst_data;logic[15:0]mem_req_burst_mask,mem_rsp_data;
 logic l_valid,l_ready,l_rsp_valid,l_rsp_ready,l_rsp_error,l_active,l_issued,l_aborting;
 logic[23:0]l_addr;logic[127:0]l_rsp_data;
 assign lcd_req_ready=!l_active&&!rst&&!lcd_abort_i;
 assign l_valid=l_active&&!l_issued&&!l_aborting&&!lcd_abort_i;
 assign lcd_rsp_valid=l_active&&l_issued&&l_rsp_valid&&!l_aborting&&!lcd_abort_i&&!rst;
 assign lcd_rsp_data=l_rsp_data;assign lcd_rsp_error=l_rsp_error;
 assign l_rsp_ready=l_active&&l_issued&&(l_aborting||lcd_abort_i||lcd_rsp_ready);
 assign lcd_busy=l_active;
 always_ff @(posedge clk)begin
  if(rst)begin l_active<=0;l_issued<=0;l_aborting<=0;lcd_aborted<=0;l_addr<=0;end
  else begin
   lcd_aborted<=0;
   if(lcd_req_valid&&lcd_req_ready)begin l_active<=1;l_issued<=0;l_aborting<=0;l_addr<=lcd_req_addr;end
   if(l_valid&&l_ready)l_issued<=1;
   if(l_active&&(lcd_abort_i||l_aborting))begin
    l_aborting<=1;
    if(!l_issued||(l_rsp_valid&&l_rsp_ready))begin l_active<=0;l_issued<=0;l_aborting<=0;lcd_aborted<=1;end
   end else if(l_rsp_valid&&l_rsp_ready)begin l_active<=0;l_issued<=0;end
  end
 end
 assign aux_req_ready=!aux_active&&!rst&&!aux_abort_i;
 assign a_valid=aux_active&&!aux_issued&&!aux_aborting&&!aux_abort_i;
 assign aux_rsp_valid=aux_active&&aux_issued&&a_rsp_valid&&!aux_aborting&&!aux_abort_i&&!rst;
 assign aux_rsp_data=a_rsp_data;assign aux_rsp_error=a_rsp_error;
 assign a_rsp_ready=aux_active&&aux_issued&&(aux_aborting||aux_abort_i||aux_rsp_ready);
 assign aux_busy=aux_active;
 assign idle=!tile_busy&&!aux_busy&&!lcd_busy&&!rgb_busy&&!bridge_busy&&mem_idle;
 always_ff @(posedge clk)begin
  if(rst)begin aux_active<=0;aux_issued<=0;aux_aborting<=0;aux_aborted<=0;a_addr<=0;a_data<=0;a_write<=0;end
  else begin
   aux_aborted<=0;
   if(aux_req_valid&&aux_req_ready)begin aux_active<=1;aux_issued<=0;aux_aborting<=0;a_addr<=aux_req_addr;a_data<=aux_req_data;a_write<=aux_req_write;end
   if(a_valid&&a_ready)aux_issued<=1;
   if(aux_active&&(aux_abort_i||aux_aborting))begin
    aux_aborting<=1;
    if(!aux_issued||(a_rsp_valid&&a_rsp_ready))begin aux_active<=0;aux_issued<=0;aux_aborting<=0;aux_aborted<=1;end
   end else if(a_rsp_valid&&a_rsp_ready)begin aux_active<=0;aux_issued<=0;end
  end
 end
 cu71_tile_memory_address_pipe tiles(
  .clk,.rst,.abort_i,.read_valid,.read_ready,.read_generation,.read_bank,.read_plane,.read_index,
  .read_rsp_valid,.read_rsp_ready,.read_rsp_generation,.read_rsp_bank,.read_rsp_plane,.read_rsp_index,.read_rsp_pixels,.read_rsp_error,
  .write_valid,.write_ready,.write_generation,.write_bank,.write_plane,.write_index,.write_pixels,
  .write_done_valid,.write_done_ready,.write_done_generation,.write_done_bank,.write_done_plane,.write_done_index,.write_done_error,
  .tile_busy,.tile_aborted,.word_req_valid(t_valid),.word_req_ready(t_ready),.word_req_write(t_write),.word_req_addr(t_addr),.word_req_data(t_data),.word_req_burst_data(t_burst_data),.word_req_burst_mask(t_burst_mask),
  .word_rsp_valid(t_rsp_valid),.word_rsp_ready(t_rsp_ready),.word_rsp_data(t_rsp_data),.word_rsp_error(t_rsp_error));
 cu71_word_bridge_burst bridge(
  .clk,.rst,.p0_valid(t_valid),.p0_ready(t_ready),.p0_write(t_write),.p0_addr(t_addr),.p0_data(t_data),.p0_burst_data(t_burst_data),.p0_burst_mask(t_burst_mask),
  .p0_rsp_valid(t_rsp_valid),.p0_rsp_ready(t_rsp_ready),.p0_rsp_data(t_rsp_data),.p0_rsp_error(t_rsp_error),
  .p1_valid(a_valid),.p1_ready(a_ready),.p1_write(a_write),.p1_addr(a_addr),.p1_data(a_data),
  .p1_rsp_valid(a_rsp_valid),.p1_rsp_ready(a_rsp_ready),.p1_rsp_data(a_rsp_data),.p1_rsp_error(a_rsp_error),
  .p2_valid(l_valid),.p2_ready(l_ready),.p2_addr(l_addr),.p2_rsp_valid(l_rsp_valid),.p2_rsp_ready(l_rsp_ready),.p2_rsp_data(l_rsp_data),.p2_rsp_error(l_rsp_error),
  .p3_valid(b_valid),.p3_ready(b_ready),.p3_addr(b_addr),.p3_data(b_data),.p3_mask(b_mask),
  .p3_rsp_valid(b_rsp_valid),.p3_rsp_ready(b_rsp_ready),.p3_rsp_error(b_rsp_error),.rgb_completed_writes,.rgb_max_wait,
  .mem_req_valid,.mem_req_ready,.mem_req_write,.mem_req_addr,.mem_req_burst_data,.mem_req_burst_mask,.mem_rsp_valid,.mem_rsp_data,.mem_idle,
  .lcd_completed_reads,.lcd_max_wait,
  .bridge_busy,.cache_hits,.cache_misses,.completed_reads,.completed_writes);
 moonshine_sdram_burst #(.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) controller(
  .clk,.read_clk,.reset(rst),.request_valid(mem_req_valid),.request_ready(mem_req_ready),.request_write(mem_req_write),.request_read_wait(4'd4),.request_address(mem_req_addr),.request_burst_data(mem_req_burst_data),.request_burst_mask(mem_req_burst_mask),
  .response_valid(mem_rsp_valid),.response_data(mem_rsp_data),.idle(mem_idle),.sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,
  .sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm);
endmodule
