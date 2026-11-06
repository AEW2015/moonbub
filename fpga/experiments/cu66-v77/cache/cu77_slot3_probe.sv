`timescale 1ns/1ps
module cu77_slot3_probe (
 input logic clk,rst,abort_i,
 input logic desc_valid,output logic desc_ready,
 input logic [63:0] desc_generation,input logic [31:0] desc_frame_id,input logic [1:0] desc_bank,
 input logic finish_valid,output logic finish_ready,
 output logic active,aborted,error,output logic [7:0] error_code,
 output logic [63:0] active_generation,output logic [31:0] active_frame_id,
 input logic prefetch_valid,output logic prefetch_ready,input logic [6:0] prefetch_index,
 output logic prefetch_done_valid,input logic prefetch_done_ready,output logic [6:0] prefetch_done_index,
 input logic consume_valid,output logic consume_ready,input logic [6:0] consume_index,
 output logic [6:0] prefetched_count,consumed_count,
 output logic mem_req_valid,input logic mem_req_ready,output logic [23:0] mem_req_addr,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [15:0] mem_rsp_data,
 input logic mem_rsp_last,mem_rsp_error,
 input logic pixel_req_valid,output logic pixel_req_ready,input logic [9:0] pixel_u,input logic [8:0] pixel_v,
 output logic pixel_rsp_valid,input logic pixel_rsp_ready,
 output logic [9:0] pixel_rsp_u,output logic [8:0] pixel_rsp_v,
 output logic [7:0] pixel_y,cb00,cb10,cb01,cb11,cr00,cr10,cr01,cr11,
 output logic pixel_hud_hit,output logic [15:0] pixel_hud,output logic pixel_rsp_error,
 output logic [31:0] read_commands,read_words,pixel_queries,cache_misses
);
 cu77_direct_cache_bounded dut(.*);
 initial begin
  for(integer i=0;i<128;i=i+1)if(dut.slot3(7'(i))!==2'(i%3))$fatal(1,"slot3 mismatch %0d",i);
  #1;$display("SLOT3_PASS exhaustive_inputs=128");$finish;
 end
endmodule
