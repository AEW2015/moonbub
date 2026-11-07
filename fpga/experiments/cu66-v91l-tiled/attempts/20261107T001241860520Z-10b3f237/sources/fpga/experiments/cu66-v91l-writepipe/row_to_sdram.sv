`timescale 1ns/1ps
`default_nettype none
// One logical eight-byte owner; up to four accepted x16 writes; idle fences physical drain.
module row_to_sdram(
 input logic clk,power_on_reset,reset,cancel,
 input logic req_valid,output logic req_ready,
 input logic [31:0] req_epoch,req_token,input logic [1:0] req_bank,
 input logic [19:0] req_addr,input logic [63:0] req_data,
 output logic rsp_valid,input logic rsp_ready,
 output logic [31:0] rsp_epoch,rsp_token,output logic [1:0] rsp_bank,
 output logic [19:0] rsp_addr,output logic rsp_error,
 output logic ctrl_valid,input logic ctrl_ready,ctrl_idle,
 output logic ctrl_write,output logic [23:0] ctrl_addr,output logic [15:0] ctrl_data,
 output logic busy,word_pending,drained,output logic [2:0] state,
 output logic [2:0] word_index,
 output logic [31:0] count_rows,count_words_accepted,count_words_retired,count_responses,count_cancels,count_invalid
);
 localparam logic [2:0] IDLE=0,ISSUE=1,WAIT_BUSY=2,WAIT_IDLE=3,RESPONSE=4;
 logic [63:0] payload;
 logic canceled,kill,initialized;
 logic [2:0] outstanding;
 logic [23:0] base_word;
 assign kill=reset||cancel;
 assign req_ready=state==IDLE&&ctrl_ready&&!kill&&!power_on_reset;
 assign rsp_valid=state==RESPONSE&&!power_on_reset;
 assign rsp_error=canceled;
 assign busy=state!=IDLE;
 assign drained=state==IDLE&&!word_pending;
 assign ctrl_valid=state==ISSUE&&!canceled&&!kill&&!power_on_reset;
 assign ctrl_write=1;
 assign ctrl_addr=base_word+24'(word_index);
 assign ctrl_data=payload[32'(word_index)*16+:16];
 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   state<=IDLE;payload<=0;canceled<=0;base_word<=0;word_pending<=0;word_index<=0;outstanding<=0;
   rsp_epoch<=0;rsp_token<=0;rsp_bank<=0;rsp_addr<=0;
   count_rows<=0;count_words_accepted<=0;count_words_retired<=0;count_responses<=0;count_cancels<=0;count_invalid<=0;
  end else begin
   if(kill&&state!=IDLE&&state!=RESPONSE)begin canceled<=1;count_cancels<=count_cancels+1;end
   case(state)
    IDLE:if(req_valid&&req_ready)begin
     rsp_epoch<=req_epoch;rsp_token<=req_token;rsp_bank<=req_bank;rsp_addr<=req_addr;
     payload<=req_data;word_index<=0;count_rows<=count_rows+1;canceled<=0;
     base_word<={req_bank,3'b000,req_addr[19:1]};
     if(req_epoch==0||req_bank>=3||req_addr[2:0]!=0||req_addr>560632)begin
      state<=RESPONSE;canceled<=1;count_invalid<=count_invalid+1;
     end else state<=ISSUE;
    end
    ISSUE:begin
     if(kill||canceled)begin
      if(outstanding==0)state<=RESPONSE;else state<=WAIT_BUSY;
     end else if(ctrl_valid&&ctrl_ready)begin
      word_pending<=1;outstanding<=outstanding+1'b1;count_words_accepted<=count_words_accepted+1;
      if(word_index==3)state<=WAIT_BUSY;else word_index<=word_index+1'b1;
     end
    end
    // Every acceptance has already crossed a controller rising edge. One fence
    // cycle also handles a prefix that drained during an input/refresh stall.
    WAIT_BUSY:state<=WAIT_IDLE;
    WAIT_IDLE:if(ctrl_idle)begin
     word_pending<=0;count_words_retired<=count_words_retired+32'(outstanding);outstanding<=0;
     state<=RESPONSE;
    end
    RESPONSE:if(rsp_valid&&rsp_ready)begin state<=IDLE;count_responses<=count_responses+1;end
    default:state<=IDLE;
   endcase
  end
 end
 initial initialized=0;
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!word_pending)else $fatal(1,"cold reset while physical write owned");
  if(!power_on_reset)begin
   assert(count_words_accepted>=count_words_retired);
   assert(count_words_accepted-count_words_retired<=4);
   assert(32'(outstanding)==count_words_accepted-count_words_retired);
   if(rsp_valid)assert(!word_pending);
   if(ctrl_valid)assert(word_index<4&&outstanding<4&&rsp_bank<3);
   if(req_valid&&!req_ready)assert(!drained||!ctrl_ready||kill||power_on_reset);
  end
 end
endmodule
`default_nettype wire
