`timescale 1ns/1ps
`default_nettype none
// Four-phase held-value mailbox. Either reset rebaselines the link before send.
// Pixel reset also resets the raster; core reset never changes margin midframe.
module moonshine_margin_control(
 input wire core_clk,core_reset,pixel_clk,pixel_reset,frame_origin,
 input wire bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 output reg[31:0]bus_rdata,output reg[6:0]pixel_margin
);
 localparam [2:0] LINK_ARM=0,LINK_ONLINE=1,WAIT_APPLY=2,WAIT_CLEAR=3,IDLE=4;
 reg[2:0]state;
 (* DONT_TOUCH="TRUE" *)reg[6:0]requested_value;
 // Intentionally not reset: retain old wire payload until remote cancellation is acknowledged.
 (* DONT_TOUCH="TRUE" *)reg[6:0]transport_payload;
 reg[6:0]applied_value;
 reg applied_valid;
 reg[3:0]last_result;
 reg[7:0]applied_seq;
 reg core_online,request_level;
 reg[6:0]link_watchdog;
 reg pixel_online,pixel_armed,ack_level,pixel_pending;
 (* DONT_TOUCH="TRUE" *)reg[6:0]pending_margin;
 (* ASYNC_REG="TRUE" *)reg[1:0]ack_sync,online_sync,armed_sync;
 (* ASYNC_REG="TRUE" *)reg[1:0]core_online_sync,request_sync;
 wire range_ok=(bus_wdata[31:7]==0 && bus_wdata[6:0]<=7'd80);
 wire write_ready=(state==IDLE && online_sync[1]);
 always @*begin
  bus_rdata=0;
  case(bus_address)
   'h084:bus_rdata={25'd0,requested_value};
   'h088:bus_rdata={applied_seq,4'd0,last_result,5'd0,write_ready,online_sync[1],applied_valid,(state!=IDLE),applied_value};
   'h08c:bus_rdata=32'h4d524731;
   default:begin end
  endcase
 end
 always @(posedge core_clk)begin
  if(core_reset)begin
   state<=LINK_ARM;requested_value<=20;applied_value<=20;applied_valid<=0;
   last_result<=0;applied_seq<=0;core_online<=0;request_level<=0;
   ack_sync<=0;online_sync<=0;armed_sync<=0;link_watchdog<=0;
  end else begin
   ack_sync<={ack_sync[0],ack_level};online_sync<={online_sync[0],pixel_online};armed_sync<={armed_sync[0],pixel_armed};
   case(state)
    LINK_ARM:begin
     core_online<=0;request_level<=0;link_watchdog<=0;
     if(armed_sync[1] && !online_sync[1] && !ack_sync[1])begin transport_payload<=requested_value;core_online<=1;state<=LINK_ONLINE;end
    end
    LINK_ONLINE:begin
     if(online_sync[1])begin request_level<=1;state<=WAIT_APPLY;end
     else if(&link_watchdog)begin core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;end
     else link_watchdog<=link_watchdog+1'b1;
    end
    WAIT_APPLY:if(ack_sync[1])begin
     applied_value<=requested_value;applied_valid<=1;applied_seq<=applied_seq+1'b1;
     last_result<=2;request_level<=0;state<=WAIT_CLEAR;
    end
    WAIT_CLEAR:if(!ack_sync[1])state<=IDLE;
    IDLE:begin end
    default:begin core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;end
   endcase
   // Pixel reset holds its link offline until it has observed our low-online
   // phase; thus no reset pulse can be mistaken for an old completed request.
   if(state!=LINK_ARM && state!=LINK_ONLINE && !online_sync[1])begin
    core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;
   end
   if(bus_write && bus_address=='h084)begin
    if(!range_ok)last_result<=3;
    else if(!write_ready)last_result<=4;
    else begin requested_value<=bus_wdata[6:0];transport_payload<=bus_wdata[6:0];request_level<=1;state<=WAIT_APPLY;last_result<=1;end
   end
  end
 end
 always @(posedge pixel_clk)begin
  if(pixel_reset)begin
   pixel_margin<=20;pending_margin<=20;pixel_pending<=0;pixel_online<=0;pixel_armed<=0;ack_level<=0;
   core_online_sync<=2'b11;request_sync<=0;
  end else begin
   core_online_sync<={core_online_sync[0],core_online};request_sync<={request_sync[0],request_level};
   if(!core_online_sync[1])begin
    pixel_online<=0;pixel_armed<=1;pixel_pending<=0;ack_level<=0;
   end else if(pixel_armed)begin pixel_online<=1;pixel_armed<=0;ack_level<=0;pixel_pending<=0;end
   else if(pixel_online)begin
    if(!request_sync[1])begin ack_level<=0;pixel_pending<=0;end
    else if(!ack_level && !pixel_pending)begin pending_margin<=transport_payload;pixel_pending<=1;end
    else if(pixel_pending && frame_origin)begin pixel_margin<=pending_margin;ack_level<=1;pixel_pending<=0;end
   end
  end
 end
endmodule
`default_nettype wire
