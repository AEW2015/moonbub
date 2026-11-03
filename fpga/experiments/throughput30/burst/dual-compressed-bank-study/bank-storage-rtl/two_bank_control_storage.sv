`timescale 1ns/1ps
`default_nettype none
// Isolated, synchronous ownership/CRC experiment. No actual JPEG RAM, QSPI,
// framebuffer or CDC is instantiated. All inputs obey this one clock.
module two_bank_control_storage #(
 parameter integer CAP_BYTES = 49152
)(
 input wire clk,input wire reset,
 input wire begin_valid,input wire [31:0] begin_id,input wire [15:0] begin_length,input wire [31:0] begin_crc,
 input wire byte_valid,input wire [7:0] byte_data,input wire commit_valid,input wire abort_valid,input wire ingress_overflow,
 output reg begin_accept,output reg reject,output reg [3:0] reject_reason,
 output reg mem_we,output reg mem_bank,output reg [15:0] mem_addr,output reg [7:0] mem_data,
 input wire decode_request,input wire decode_done,input wire decode_fail,
 output reg decode_grant,output reg decode_bank,output reg [31:0] decode_id,output reg [15:0] decode_length,
 input wire vblank,output reg present,output reg front_valid,output reg [31:0] front_id,
 output reg [31:0] accepted_frames,output wire [31:0] dropped_frames
);
 localparam [2:0] FREE=0, RECEIVING=1, READY=2, DECODING=3, PENDING=4;
 localparam [3:0] R_LENGTH=1,R_BUSY=2,R_CRC=3,R_SHORT=4,R_OVERFLOW=5,R_CONFLICT=6,R_NO_ACTIVE=7;
 reg [2:0] state[0:1];
 reg [31:0] frame_id[0:1],frame_crc[0:1],frame_order[0:1];
 reg [15:0] frame_length[0:1],received[0:1];
 reg [31:0] recv_crc,order_next,rx_dropped,decode_dropped;
 assign dropped_frames=rx_dropped+decode_dropped;
 reg receiving,recv_bank,decoding,dec_bank,pending,pending_bank;
 integer k;
 reg choose_free,free_bank,choose_ready,ready_bank;
 wire conflicting=(begin_valid && (byte_valid || commit_valid)) || (byte_valid && commit_valid);
 function automatic [31:0] crc_byte(input [31:0] previous,input [7:0] datum);
  reg [31:0] v;integer b;
  begin v=previous^{24'd0,datum};for(b=0;b<8;b=b+1)v=v[0]?((v>>1)^32'hedb88320):(v>>1);crc_byte=v;end
 endfunction
 always @* begin
  choose_free=1'b0;free_bank=1'b0;
  if(state[0]==FREE)begin choose_free=1;free_bank=0;end
  else if(state[1]==FREE)begin choose_free=1;free_bank=1;end
  choose_ready=1'b0;ready_bank=1'b0;
  if(state[0]==READY && state[1]==READY)begin
   choose_ready=1;ready_bank=($signed(frame_order[0]-frame_order[1])<0)?0:1;
  end else if(state[0]==READY)begin choose_ready=1;ready_bank=0;end
  else if(state[1]==READY)begin choose_ready=1;ready_bank=1;end
 end
 always @(posedge clk)begin
  if(reset)begin
   for(k=0;k<2;k=k+1)begin state[k]<=FREE;frame_id[k]<=0;frame_crc[k]<=0;frame_order[k]<=0;frame_length[k]<=0;received[k]<=0;end
   receiving<=0;recv_bank<=0;decoding<=0;dec_bank<=0;pending<=0;pending_bank<=0;recv_crc<=32'hffffffff;order_next<=0;
   begin_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;mem_bank<=0;mem_addr<=0;mem_data<=0;
   decode_grant<=0;decode_bank<=0;decode_id<=0;decode_length<=0;present<=0;front_valid<=0;front_id<=0;accepted_frames<=0;rx_dropped<=0;decode_dropped<=0;
  end else begin
   begin_accept<=0;reject<=0;reject_reason<=0;mem_we<=0;decode_grant<=0;present<=0;
   // Abort and transport-overflow affect only the currently receiving bank.
   // They never cancel a distinct READY/DECODING/PENDING frame.
   if(abort_valid || ingress_overflow)begin
    if(receiving)begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;end
    if(ingress_overflow)begin reject<=1;reject_reason<=R_OVERFLOW;end
   end else if(conflicting)begin
    reject<=1;reject_reason<=R_CONFLICT;
    if(receiving)begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;end
   end else if(begin_valid)begin
    if(begin_length==0 || {16'd0,begin_length}>CAP_BYTES)begin reject<=1;reject_reason<=R_LENGTH;end
    else if(receiving || !choose_free)begin reject<=1;reject_reason<=R_BUSY;end
    else begin
     state[free_bank]<=RECEIVING;receiving<=1;recv_bank<=free_bank;frame_id[free_bank]<=begin_id;frame_length[free_bank]<=begin_length;frame_crc[free_bank]<=begin_crc;received[free_bank]<=0;recv_crc<=32'hffffffff;begin_accept<=1;
    end
   end else if(byte_valid)begin
    if(!receiving)begin reject<=1;reject_reason<=R_NO_ACTIVE;end
    else if(received[recv_bank]>=frame_length[recv_bank])begin
     state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;reject<=1;reject_reason<=R_OVERFLOW;
    end else begin
     mem_we<=1;mem_bank<=recv_bank;mem_addr<=received[recv_bank];mem_data<=byte_data;
     received[recv_bank]<=received[recv_bank]+1'b1;recv_crc<=crc_byte(recv_crc,byte_data);
    end
   end else if(commit_valid)begin
    if(!receiving)begin reject<=1;reject_reason<=R_NO_ACTIVE;end
    else if(received[recv_bank]!=frame_length[recv_bank])begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;reject<=1;reject_reason<=R_SHORT;end
    else if((~recv_crc)!=frame_crc[recv_bank])begin state[recv_bank]<=FREE;receiving<=0;rx_dropped<=rx_dropped+1;reject<=1;reject_reason<=R_CRC;end
    else begin state[recv_bank]<=READY;frame_order[recv_bank]<=order_next;order_next<=order_next+1'b1;receiving<=0;accepted_frames<=accepted_frames+1;end
   end
   // One decoder and one back framebuffer: do not decode another while a
   // completed frame is awaiting a display boundary.
   if(decode_request && !decoding && !pending && choose_ready)begin
    state[ready_bank]<=DECODING;decoding<=1;dec_bank<=ready_bank;decode_grant<=1;decode_bank<=ready_bank;decode_id<=frame_id[ready_bank];decode_length<=frame_length[ready_bank];
   end
   if(decoding && (decode_done || decode_fail))begin
    decoding<=0;
    if(decode_fail)begin state[dec_bank]<=FREE;decode_dropped<=decode_dropped+1;end
    else begin state[dec_bank]<=PENDING;pending<=1;pending_bank<=dec_bank;end
   end
   if(vblank && pending)begin
    front_id<=frame_id[pending_bank];front_valid<=1;present<=1;state[pending_bank]<=FREE;pending<=0;
   end
  end
 end
endmodule
`default_nettype wire
