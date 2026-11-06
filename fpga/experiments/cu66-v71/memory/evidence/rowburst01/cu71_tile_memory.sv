`timescale 1ns/1ps
// Canonical packed-u8 tile adapter. No memory arrays or golden reference path.
module cu71_tile_memory (
 input logic clk,rst,abort_i,
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
 output logic word_req_valid,input logic word_req_ready,output logic word_req_write,
 output logic [23:0] word_req_addr,output logic [15:0] word_req_data,output logic[127:0]word_req_burst_data,output logic[15:0]word_req_burst_mask,
 input logic word_rsp_valid,output logic word_rsp_ready,input logic [15:0] word_rsp_data,input logic word_rsp_error
);
 `include "cu70_memory_map.svh"
 typedef enum logic [1:0] {IDLE,ISSUE,WAIT_WORD,RESULT} state_t;
 state_t state;
 logic writing,aborting,failed,prefer_write;
 logic [63:0] generation;
 logic [1:0] bank,plane;
 logic [16:0] index;
 logic [4:0] word_index;
 logic [511:0] pixels;
 logic [23:0] tile_base;
 logic [8:0] pitch;
 logic choose_write;
 logic [1:0] chosen_bank,chosen_plane;
 logic [16:0] chosen_index;
 logic [63:0] chosen_generation;
 logic bad_metadata;
 always_comb begin
  choose_write=write_valid&&(!read_valid||prefer_write);
  chosen_bank=choose_write?write_bank:read_bank;
  chosen_plane=choose_write?write_plane:read_plane;
  chosen_index=choose_write?write_index:read_index;
  chosen_generation=choose_write?write_generation:read_generation;
  bad_metadata=chosen_bank>2||chosen_plane>2||chosen_generation==0||
      chosen_index>=(chosen_plane==0?17'd5400:17'd1350);
  read_ready=state==IDLE&&!rst&&!abort_i&&!choose_write;
  write_ready=state==IDLE&&!rst&&!abort_i&&choose_write;
  word_req_valid=state==ISSUE&&!rst&&!abort_i&&!aborting;
  word_req_write=writing;
  word_req_addr=tile_base+24'(int'(word_index[4:2])*int'(pitch))+24'(word_index[1:0]);
  word_req_data=pixels[int'(word_index)*16+:16];
  word_req_burst_data=128'(pixels[int'(word_index)*16+:64])<<(word_req_addr[2:0]*16);
  word_req_burst_mask=16'hffff^(16'h00ff<<(word_req_addr[2:0]*2));
  word_rsp_ready=state==WAIT_WORD&&!rst;
  read_rsp_valid=state==RESULT&&!writing&&!rst&&!abort_i&&!aborting;
  write_done_valid=state==RESULT&&writing&&!rst&&!abort_i&&!aborting;
  read_rsp_generation=generation;write_done_generation=generation;
  read_rsp_bank=bank;write_done_bank=bank;read_rsp_plane=plane;write_done_plane=plane;
  read_rsp_index=index;write_done_index=index;read_rsp_pixels=pixels;
  read_rsp_error=failed;write_done_error=failed;
  tile_busy=state!=IDLE;
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=IDLE;writing<=0;aborting<=0;failed<=0;prefer_write<=0;
   generation<=0;bank<=0;plane<=0;index<=0;word_index<=0;pixels<=0;tile_base<=0;pitch<=0;tile_aborted<=0;
  end else begin
   tile_aborted<=0;
   if(abort_i&&state!=IDLE)aborting<=1;
   case(state)
    IDLE:if((read_valid&&read_ready)||(write_valid&&write_ready))begin
     writing<=choose_write;prefer_write<=!choose_write;aborting<=0;failed<=bad_metadata;
     generation<=chosen_generation;bank<=chosen_bank;plane<=chosen_plane;index<=chosen_index;
     word_index<=0;pixels<=choose_write?write_pixels:512'd0;
     if(chosen_plane==0)begin
      pitch<=9'd360;
      tile_base<=canonical_base(chosen_bank)+24'((int'(chosen_index)/90)*8*360+(int'(chosen_index)%90)*4);
     end else begin
      pitch<=9'd180;
      tile_base<=canonical_base(chosen_bank)+(chosen_plane==1?24'd172800:24'd216000)+
         24'((int'(chosen_index)/45)*8*180+(int'(chosen_index)%45)*4);
     end
     state<=bad_metadata?RESULT:ISSUE;
    end
    ISSUE:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
          else if(word_req_valid&&word_req_ready)state<=WAIT_WORD;
    WAIT_WORD:if(word_rsp_valid&&word_rsp_ready)begin
     if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else if(word_rsp_error)begin failed<=1;state<=RESULT;end
     else begin
      if(!writing)pixels[int'(word_index)*16+:16]<=word_rsp_data;
      if(word_index==(writing?28:31))state<=RESULT;
      else begin word_index<=word_index+(writing?5'd4:5'd1);state<=ISSUE;end
     end
    end
    RESULT:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else if((read_rsp_valid&&read_rsp_ready)||(write_done_valid&&write_done_ready))state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
