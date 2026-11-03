`timescale 1ns/1ps
`default_nettype none
// Single-clock research reader: one aligned BL8 response buffered into four
// little-endian words. No transport, CRC, CDC, timeout or physical RAM proof.
module sdram_jpeg_reader #(
 parameter integer BASE_WORDS='h060000,
 parameter integer CAP_BYTES=262144,
 parameter integer END_WORDS='h080000
)(
 input wire clk,reset,start,owned,input wire[31:0]granted_length,
 output reg start_accept,active,error,frame_done,
 output wire mem_req_valid,input wire mem_req_ready,output wire[23:0]mem_req_addr,
 input wire mem_data_valid,input wire[15:0]mem_data,
 output wire out_valid,output wire[31:0]out_data,output wire[3:0]out_strb,input wire out_ready,
 output wire read_inflight,output reg faulted
);
 reg inflight,draining,block_valid;reg[2:0] beat;reg[1:0] word_index;
 reg[31:0] length,consumed,block_number;reg[127:0] block_data;
 wire[31:0] remaining=length-consumed;
 wire[2:0] word_bytes=remaining>=4?3'd4:remaining[2:0];
 assign out_strb=word_bytes==4?4'b1111:word_bytes==3?4'b0111:word_bytes==2?4'b0011:word_bytes==1?4'b0001:4'b0000;
 assign out_valid=active&&owned&&block_valid&&!faulted;
 wire[31:0] raw_word=block_data[word_index*32+:32];
 assign out_data=raw_word & {{8{out_strb[3]}},{8{out_strb[2]}},{8{out_strb[1]}},{8{out_strb[0]}}};
 assign mem_req_valid=active&&owned&&!inflight&&!draining&&!block_valid&&!faulted&&(consumed<length);
 assign mem_req_addr=24'(BASE_WORDS+block_number*8);
 assign read_inflight=inflight||draining;
 always @(posedge clk)begin
  if(reset)begin
   start_accept<=0;active<=0;error<=0;frame_done<=0;inflight<=0;draining<=0;block_valid<=0;beat<=0;word_index<=0;
   length<=0;consumed<=0;block_number<=0;block_data<=0;faulted<=0;
  end else begin
   start_accept<=0;error<=0;frame_done<=0;
   if(start)begin
    if(active||inflight||draining||faulted||!owned||granted_length==0||granted_length>CAP_BYTES||
       BASE_WORDS<0||BASE_WORDS%8!=0||END_WORDS>1048576||BASE_WORDS+((CAP_BYTES+15)/16)*8>END_WORDS)error<=1;
    else begin active<=1;length<=granted_length;consumed<=0;block_number<=0;block_valid<=0;word_index<=0;start_accept<=1;end
   end
   if(mem_req_valid&&mem_req_ready)begin inflight<=1;beat<=0;block_number<=block_number+1'b1;end
   if(mem_data_valid)begin
    if(!inflight)begin faulted<=1;active<=0;block_valid<=0;error<=1;end
    else begin
     if(active&&owned&&!draining)block_data[beat*16+:16]<=mem_data;
     if(beat==7)begin
      inflight<=0;beat<=0;
      if(active&&owned&&!draining)begin block_valid<=1;word_index<=0;end
      else draining<=0;
     end else beat<=beat+1'b1;
    end
   end
   if(active&&!owned)begin
    active<=0;block_valid<=0;error<=1;
    if(inflight&&!(mem_data_valid&&beat==7))draining<=1;
   end
   if(out_valid&&out_ready)begin
    consumed<=consumed+{29'd0,word_bytes};
    if(remaining<=4)begin active<=0;block_valid<=0;frame_done<=1;end
    else if(word_index==3)begin word_index<=0;block_valid<=0;end
    else word_index<=word_index+1'b1;
   end
  end
 end
endmodule
`default_nettype wire
