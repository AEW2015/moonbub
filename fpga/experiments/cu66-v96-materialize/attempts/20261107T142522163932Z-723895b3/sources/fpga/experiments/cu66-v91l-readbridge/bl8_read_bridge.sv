`timescale 1ns/1ps
`default_nettype none
// One tagged aligned16-byte read. Eight unbackpressured x16 controller beats
// drain into one128-bit response, followed by two observed idle fence clocks.
module bl8_read_bridge(
 input logic clk,power_on_reset,reset,cancel,
 input logic req_valid,output logic req_ready,
 input logic [18:0] req_addr,input logic [1:0] req_bank,
 input logic [31:0] req_epoch,req_generation,
 output logic rsp_valid,input logic rsp_ready,output logic [127:0] rsp_data,
 output logic [18:0] rsp_addr,output logic [1:0] rsp_bank,
 output logic [31:0] rsp_epoch,rsp_generation,output logic rsp_error,
 output logic ctrl_valid,input logic ctrl_ready,
 output logic ctrl_write,output logic [23:0] ctrl_addr,output logic [15:0] ctrl_data,
 input logic ctrl_read_valid,input logic [15:0] ctrl_read_data,input logic ctrl_idle,
 output logic busy,pending,output logic [2:0] state,output logic [3:0] beat_count,
 output logic [31:0] count_requests,count_commands,count_beats,count_responses,count_cancels,count_invalid
);
 localparam logic [2:0] IDLE=0,ISSUE=1,CAPTURE=2,FENCE=3,RESPONSE=4;
 logic canceled,initialized=0;
 logic [1:0] idle_count;
 wire kill=reset||cancel;
 assign busy=state!=IDLE;
 assign req_ready=state==IDLE&&!kill&&!power_on_reset;
 assign rsp_valid=state==RESPONSE&&!power_on_reset;
 assign ctrl_valid=state==ISSUE&&!kill&&!power_on_reset;
 assign ctrl_write=0;
 assign ctrl_addr={rsp_bank,4'b0000,rsp_addr[18:1]};
 assign ctrl_data=0;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   state<=IDLE;pending<=0;canceled<=0;idle_count<=0;beat_count<=0;
   rsp_data<=0;rsp_addr<=0;rsp_bank<=0;rsp_epoch<=0;rsp_generation<=0;rsp_error<=0;
   count_requests<=0;count_commands<=0;count_beats<=0;count_responses<=0;count_cancels<=0;count_invalid<=0;
  end else begin
   if(kill&&state!=IDLE&&state!=RESPONSE)begin canceled<=1;count_cancels<=count_cancels+1;end
   case(state)
    IDLE:if(req_valid&&req_ready)begin
     rsp_addr<=req_addr;rsp_bank<=req_bank;rsp_epoch<=req_epoch;rsp_generation<=req_generation;
     rsp_data<=0;rsp_error<=0;canceled<=0;beat_count<=0;idle_count<=0;count_requests<=count_requests+1;
     if(req_addr[3:0]!=0||req_addr>518384||req_bank>=3||req_epoch==0||req_generation==0)begin
      rsp_error<=1;state<=RESPONSE;count_invalid<=count_invalid+1;
     end else state<=ISSUE;
    end
    ISSUE:if(kill||canceled)begin rsp_error<=1;state<=RESPONSE;end
     else if(ctrl_valid&&ctrl_ready)begin pending<=1;state<=CAPTURE;count_commands<=count_commands+1;end
    CAPTURE:if(ctrl_read_valid)begin
     rsp_data[32'(beat_count)*16+:16]<=ctrl_read_data;
     beat_count<=beat_count+1'b1;count_beats<=count_beats+1;
     if(beat_count==7)begin state<=FENCE;idle_count<=0;end
    end
    FENCE:if(ctrl_idle)begin
     if(idle_count==1)begin
      pending<=0;rsp_error<=canceled||kill;
      if(canceled||kill)rsp_data<=0;
      state<=RESPONSE;
     end else idle_count<=idle_count+1'b1;
    end else idle_count<=0;
    RESPONSE:if(rsp_valid&&rsp_ready)begin state<=IDLE;count_responses<=count_responses+1;end
    default:state<=IDLE;
   endcase
  end
 end
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!pending)else $fatal(1,"cold reset while read owned");
  if(!power_on_reset)begin
   assert(state<=RESPONSE&&beat_count<=8);
   assert(count_requests>=count_responses&&count_requests-count_responses<=1);
   if(ctrl_read_valid)assert(pending&&state==CAPTURE&&beat_count<8)else $fatal(1,"unowned/excess controller read beat");
   if(ctrl_valid)assert(!pending&&rsp_addr[3:0]==0&&rsp_bank<3);
   if(rsp_valid)assert(!pending);
   if(state==FENCE)assert(pending&&beat_count==8);
  end
 end
endmodule
`default_nettype wire
