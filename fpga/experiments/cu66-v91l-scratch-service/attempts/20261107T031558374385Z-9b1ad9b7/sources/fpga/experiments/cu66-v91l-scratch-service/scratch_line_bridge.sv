`timescale 1ns/1ps
`default_nettype none
// One aligned, fully written/read 16-byte scratch line. Private bank3 aperture.
// Single-word writes match MRS=0x233; reads capture all eight BL8 beats.
module scratch_line_bridge(
 input logic clk,power_on_reset,reset,cancel,
 input logic req_valid,output logic req_ready,input logic req_write,
 input logic [17:0] req_addr,input logic [127:0] req_data,input logic [31:0] req_epoch,
 output logic rsp_valid,input logic rsp_ready,output logic [127:0] rsp_data,
 output logic [31:0] rsp_epoch,output logic rsp_error,
 output logic ctrl_valid,input logic ctrl_ready,ctrl_idle,
 output logic ctrl_write,output logic [23:0] ctrl_addr,output logic [15:0] ctrl_data,
 input logic ctrl_read_valid,input logic [15:0] ctrl_read_data,
 output logic busy,pending,output logic [2:0] state,output logic [3:0] beats,words,
 output logic [31:0] count_requests,count_commands,count_responses,count_cancels,count_invalid,
 output logic [31:0] count_write_requests,count_read_requests,count_write_words,count_read_words
);
 localparam logic [2:0] IDLE=0,ISSUE=1,WAIT_BUSY=2,WAIT_IDLE=3,CAPTURE=4,FENCE=5,RESPONSE=6;
 logic write_owned,canceled,initialized=0;
 logic [17:0] address_owned;
 logic [127:0] payload;
 logic [1:0] idle_count;
 wire kill=reset||cancel;
 assign req_ready=state==IDLE&&!kill&&!power_on_reset;
 assign rsp_valid=state==RESPONSE&&!power_on_reset;
 assign busy=state!=IDLE;
 assign ctrl_valid=state==ISSUE&&!kill&&!canceled&&!power_on_reset;
 assign ctrl_write=write_owned;
 assign ctrl_addr=24'hc00000+24'(address_owned>>1)+(write_owned?24'(words):24'd0);
 assign ctrl_data=write_owned?payload[32'(words)*16+:16]:16'd0;
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   state<=IDLE;pending<=0;write_owned<=0;canceled<=0;address_owned<=0;payload<=0;idle_count<=0;
   beats<=0;words<=0;rsp_data<=0;rsp_epoch<=0;rsp_error<=0;
   count_requests<=0;count_commands<=0;count_responses<=0;count_cancels<=0;count_invalid<=0;
   count_write_requests<=0;count_read_requests<=0;count_write_words<=0;count_read_words<=0;
  end else begin
   if(kill&&state!=IDLE&&state!=RESPONSE&&!canceled)begin canceled<=1;count_cancels<=count_cancels+1;end
   case(state)
    IDLE:if(req_valid&&req_ready)begin
     write_owned<=req_write;address_owned<=req_addr;payload<=req_data;rsp_epoch<=req_epoch;
     rsp_data<=0;rsp_error<=0;canceled<=0;words<=0;beats<=0;idle_count<=0;
     count_requests<=count_requests+1;
     if(req_write)count_write_requests<=count_write_requests+1;else count_read_requests<=count_read_requests+1;
     if(req_addr[3:0]!=0||req_epoch==0)begin rsp_error<=1;count_invalid<=count_invalid+1;state<=RESPONSE;end
     else state<=ISSUE;
    end
    ISSUE:if(kill||canceled)begin
     if(pending)state<=WAIT_BUSY;else begin rsp_error<=1;state<=RESPONSE;end
    end else if(ctrl_valid&&ctrl_ready)begin
     pending<=1;count_commands<=count_commands+1;
     if(write_owned)begin
      words<=words+1'b1;count_write_words<=count_write_words+1;
      if(words==7)state<=WAIT_BUSY;
     end else state<=CAPTURE;
    end
    WAIT_BUSY:begin state<=WAIT_IDLE;idle_count<=0;end
    WAIT_IDLE:if(ctrl_idle)begin
     if(idle_count==1)begin pending<=0;rsp_error<=canceled||kill;state<=RESPONSE;end
     else idle_count<=idle_count+1'b1;
    end else idle_count<=0;
    CAPTURE:if(ctrl_read_valid)begin
     rsp_data[32'(beats)*16+:16]<=ctrl_read_data;beats<=beats+1'b1;count_read_words<=count_read_words+1;
     if(beats==7)begin state<=FENCE;idle_count<=0;end
    end
    FENCE:if(ctrl_idle)begin
     if(idle_count==1)begin
      pending<=0;rsp_error<=canceled||kill;if(canceled||kill)rsp_data<=0;state<=RESPONSE;
     end else idle_count<=idle_count+1'b1;
    end else idle_count<=0;
    RESPONSE:if(rsp_valid&&rsp_ready)begin state<=IDLE;count_responses<=count_responses+1;end
    default:state<=IDLE;
   endcase
  end
 end
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!pending)else $fatal(1,"cold reset while scratch physical command owned");
  if(!power_on_reset)begin
   assert(state<=RESPONSE&&words<=8&&beats<=8);
   assert(count_requests>=count_responses&&count_requests-count_responses<=1);
   if(ctrl_valid)assert(address_owned[3:0]==0&&rsp_epoch!=0&&ctrl_addr>=24'hc00000&&ctrl_addr<=24'hc1ffff&&(!write_owned||words<8));
   if(ctrl_read_valid)assert(pending&&!write_owned&&state==CAPTURE&&beats<8)else $fatal(1,"unowned/excess scratch read beat");
   if(rsp_valid)assert(!pending);
   if(state==FENCE)assert(pending&&!write_owned&&beats==8);
  end
 end
 assert property(@(posedge clk) !power_on_reset&&rsp_valid&&!rsp_ready |=> power_on_reset||$stable({rsp_valid,rsp_data,rsp_epoch,rsp_error}));
endmodule
`default_nettype wire
