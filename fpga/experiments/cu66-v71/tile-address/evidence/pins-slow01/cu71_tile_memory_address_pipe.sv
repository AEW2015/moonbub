`timescale 1ns/1ps
// Canonical packed-u8 tile adapter, original row-major map, bounded address microsteps.
// No PHY/map change, memory arrays, or golden reference path.
module cu71_tile_memory_address_pipe (
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
 typedef enum logic [3:0] {IDLE,ADDR_INIT,ADDR_DIVIDE,ADDR_SCALE,ADDR_ROW,ADDR_COLUMN,ISSUE,WAIT_WORD,RESULT} state_t;
 state_t state;
 logic writing,aborting,failed,prefer_write;
 logic [63:0] generation;
 logic [1:0] bank,plane;
 logic [16:0] index;
 logic [4:0] word_index;
 logic [511:0] pixels;
 // Metadata is captured before the bounded six-step quotient calculation.
 // For valid tiles quotient is0..59, remainder0..89 (Y) or0..44 (C).
 logic [23:0] plane_base,row_base,word_address;
 logic [17:0] row_offset;
 logic [8:0] column_offset,pitch_minus_three;
 logic [12:0] remainder,divisor;
 logic [5:0] tile_row;
 logic [2:0] divide_bit;
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
  word_req_addr=word_address;
  word_req_data=pixels[int'(word_index)*16+:16];
  word_req_burst_data=128'(pixels[int'(word_index[4:2])*64+:64])<<(word_req_addr[2:0]*16);
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
   generation<=0;bank<=0;plane<=0;index<=0;word_index<=0;pixels<=0;plane_base<=0;row_base<=0;word_address<=0;row_offset<=0;column_offset<=0;pitch<=0;pitch_minus_three<=0;remainder<=0;divisor<=0;tile_row<=0;divide_bit<=0;tile_aborted<=0;
  end else begin
   tile_aborted<=0;
   if(abort_i&&state!=IDLE)aborting<=1;
   case(state)
    IDLE:if((read_valid&&read_ready)||(write_valid&&write_ready))begin
     writing<=choose_write;prefer_write<=!choose_write;aborting<=0;failed<=bad_metadata;
     generation<=chosen_generation;bank<=chosen_bank;plane<=chosen_plane;index<=chosen_index;
     word_index<=0;pixels<=choose_write?write_pixels:512'd0;
     state<=bad_metadata?RESULT:ADDR_INIT;
    end
    ADDR_INIT:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else begin
      // Only held bank/plane/index feed address work; no upstream arbitration
      // or command-state path can propagate through the division/address sum.
      plane_base<=canonical_base(bank)+(plane==0?24'd0:plane==1?24'd172800:24'd216000);
      pitch<=plane==0?9'd360:9'd180;
      pitch_minus_three<=plane==0?9'd357:9'd177;
      remainder<=index[12:0];tile_row<=0;divide_bit<=5;
      divisor<=plane==0?13'd2880:13'd1440;
      state<=ADDR_DIVIDE;
     end
    ADDR_DIVIDE:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else begin
      if(remainder>=divisor)begin
       remainder<=remainder-divisor;tile_row[divide_bit]<=1'b1;
      end
      divisor<=divisor>>1;
      if(divide_bit==0)state<=ADDR_SCALE;else divide_bit<=divide_bit-1'b1;
     end
    ADDR_SCALE:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else begin
      row_offset<=plane==0?18'(tile_row*12'd2880):18'(tile_row*11'd1440);
      column_offset<={remainder[6:0],2'b00};state<=ADDR_ROW;
     end
    ADDR_ROW:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else begin row_base<=plane_base+24'(row_offset);state<=ADDR_COLUMN;end
    ADDR_COLUMN:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else begin word_address<=row_base+24'(column_offset);state<=ISSUE;end
    ISSUE:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
          else if(word_req_valid&&word_req_ready)state<=WAIT_WORD;
    WAIT_WORD:if(word_rsp_valid&&word_rsp_ready)begin
     if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else if(word_rsp_error)begin failed<=1;state<=RESULT;end
     else begin
      if(!writing)pixels[int'(word_index)*16+:16]<=word_rsp_data;
      if(word_index==(writing?28:31))state<=RESULT;
      else begin
       word_index<=word_index+(writing?5'd4:5'd1);
       // Registered row-major cursor removes the per-word pitch multiplier
       // from the public request-address path. Accepted words drain as before.
       if(writing)word_address<=word_address+24'(pitch);
       else word_address<=word_address+(word_index[1:0]==3?24'(pitch_minus_three):24'd1);
       state<=ISSUE;
      end
     end
    end
    RESULT:if(abort_i||aborting)begin state<=IDLE;aborting<=0;tile_aborted<=1;end
     else if((read_rsp_valid&&read_rsp_ready)||(write_done_valid&&write_done_ready))state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
