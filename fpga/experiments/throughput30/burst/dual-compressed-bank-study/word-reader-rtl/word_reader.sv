`timescale 1ns/1ps
`default_nettype none
// Single-clock experiment over the separate owned byte-RAM interface.
// No CDC, DMA, JPEG decode, arbitration, or physical block-RAM timing model.
module word_reader #(
 parameter integer CAP_BYTES=49152
)(
 input wire clk,input wire reset,
 input wire start,input wire owned,input wire [15:0] granted_length,
 output reg start_accept,output reg active,output reg error,output reg frame_done,
 output reg byte_req,output reg [15:0] byte_addr,
 input wire byte_valid,input wire byte_error,input wire [7:0] byte_data,
 output wire out_valid,output reg [31:0] out_data,output reg [3:0] out_strb,input wire out_ready
);
 localparam [1:0] IDLE=0,ISSUE=1,WAIT_BYTE=2,HOLD_WORD=3;
 reg word_valid;
 assign out_valid=word_valid && owned;
 reg[1:0] state,lane;reg[15:0] length,next_addr;reg[31:0] partial;
 function automatic [3:0] strobe(input [1:0] n);
  case(n)2'd0:strobe=4'b0001;2'd1:strobe=4'b0011;2'd2:strobe=4'b0111;default:strobe=4'b1111;endcase
 endfunction
 always @(posedge clk)begin
  if(reset)begin state<=IDLE;lane<=0;length<=0;next_addr<=0;partial<=0;start_accept<=0;active<=0;error<=0;frame_done<=0;byte_req<=0;byte_addr<=0;word_valid<=0;out_data<=0;out_strb<=0;end
  else begin
   start_accept<=0;error<=0;frame_done<=0;byte_req<=0;
   if(active && !owned)begin
    // A revoked bank invalidates even a backpressured output word.
    state<=IDLE;active<=0;word_valid<=0;error<=1;
   end else begin
    if(start && active)error<=1; // Reject duplicate start without corrupting active work.
    case(state)
     IDLE:if(start)begin
      if(!owned||granted_length==0||{16'd0,granted_length}>CAP_BYTES)error<=1;
      else begin length<=granted_length;next_addr<=0;lane<=0;partial<=0;active<=1;start_accept<=1;state<=ISSUE;end
     end
     ISSUE:begin byte_addr<=next_addr;byte_req<=1;state<=WAIT_BYTE;end
     WAIT_BYTE:begin
      if(byte_error)begin state<=IDLE;active<=0;word_valid<=0;error<=1;end
      else if(byte_valid)begin
       next_addr<=next_addr+1'b1;
       if(lane==3 || next_addr+1'b1==length)begin
        out_data<=partial | ({24'd0,byte_data} << (lane*8));out_strb<=strobe(lane);word_valid<=1;state<=HOLD_WORD;
       end else begin partial<=partial | ({24'd0,byte_data} << (lane*8));lane<=lane+1'b1;state<=ISSUE;end
      end
     end
     HOLD_WORD:if(word_valid && out_ready)begin
      word_valid<=0;
      if(next_addr==length)begin state<=IDLE;active<=0;frame_done<=1;end
      else begin lane<=0;partial<=0;state<=ISSUE;end
     end
     default:begin state<=IDLE;active<=0;word_valid<=0;error<=1;end
    endcase
   end
  end
 end
endmodule
`default_nettype wire
