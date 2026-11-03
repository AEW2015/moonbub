`timescale 1ns/1ps
`default_nettype none
// Isolated synchronous byte memories. Actual BRAM mapping is not established.
module two_bank_storage #(
 parameter integer CAP_BYTES=49152
)(
 input wire clk,input wire reset,
 input wire begin_valid,input wire[31:0] begin_id,input wire[15:0] begin_length,input wire[31:0] begin_crc,
 input wire byte_valid,input wire[7:0] byte_data,input wire commit_valid,input wire abort_valid,input wire ingress_overflow,
 output wire begin_accept,output wire reject,output wire[3:0] reject_reason,
 input wire decode_request,input wire decode_done,input wire decode_fail,
 output wire decode_grant,output wire decode_bank,output wire[31:0] decode_id,output wire[15:0] decode_length,
 input wire read_req,input wire[15:0] read_addr,
 output reg read_ready,output reg read_valid,output reg read_error,output reg[7:0] read_data,
 input wire vblank,output wire present,output wire front_valid,output wire[31:0] front_id,
 output wire[31:0] accepted_frames,output wire[31:0] dropped_frames
);
 wire mem_we,mem_bank;wire[15:0]mem_addr;wire[7:0]mem_data;
 (* ram_style="block" *) reg [7:0] compressed0[0:CAP_BYTES-1];
 (* ram_style="block" *) reg [7:0] compressed1[0:CAP_BYTES-1];
 reg owner_bank;reg[15:0] owner_length;
 two_bank_control_storage #(.CAP_BYTES(CAP_BYTES)) control(
  .clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),
  .byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid),.ingress_overflow(ingress_overflow),
  .begin_accept(begin_accept),.reject(reject),.reject_reason(reject_reason),.mem_we(mem_we),.mem_bank(mem_bank),.mem_addr(mem_addr),.mem_data(mem_data),
  .decode_request(decode_request),.decode_done(decode_done),.decode_fail(decode_fail),.decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.decode_length(decode_length),
  .vblank(vblank),.present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));
 // No RAM reset: contents are not a validity indicator. Same-clock registered
 // write/read ports; upstream QSPI CDC and physical read/write hazards absent.
 always @(posedge clk)begin
  if(!reset && mem_we)begin if(mem_bank)compressed1[mem_addr]<=mem_data;else compressed0[mem_addr]<=mem_data;end
 end
 always @(posedge clk)begin
  if(reset)begin read_ready<=0;read_valid<=0;read_error<=0;read_data<=0;owner_bank<=0;owner_length<=0;end
  else begin
   read_valid<=0;read_error<=0;
   if(decode_done||decode_fail)begin
    read_ready<=0;
    if(read_req)read_error<=1;
   end else if(decode_grant)begin
    owner_bank<=decode_bank;owner_length<=decode_length;read_ready<=1;
    if(read_req)read_error<=1;
   end else if(read_req)begin
    if(read_ready && read_addr<owner_length && {16'd0,read_addr}<CAP_BYTES)begin
     if(owner_bank)read_data<=compressed1[read_addr];else read_data<=compressed0[read_addr];
     read_valid<=1;
    end else read_error<=1;
   end
  end
 end
endmodule
`default_nettype wire
