`timescale 1ns/1ps
module sdr1_engine(input wire clk,reset,go,
 output wire request_valid, input wire request_ready,output wire request_write,
 output wire[23:0] request_address,output wire[127:0]request_data,
 input wire response_valid,input wire[15:0]response_data,
 input wire observe_write_beat,observe_read_issue,input wire[15:0]raw_read,
 output wire[31:0]status,output reg[23:0]first_address,
 output reg[31:0]first_values,output reg[255:0]raw_trace,
 output reg[127:0]first_response,output reg[15:0]response_mask,
 output reg[31:0]run_id,output wire[31:0]counts);
 localparam IDLE=0,WAIT_READY=1,SEND_WRITE=2,WAIT_WRITE=3,SEND_READ=4,COLLECT=5;
 reg[2:0]state=IDLE;reg busy=0,done=0,timed_out=0,armed=0;
 reg[1:0]burst=0;reg[2:0]word_index=0;reg[7:0]errors=0,reads=0,writes=0,rejected=0;
 reg[16:0]watchdog=0;reg tracing=0,trace_started=0,trace_done=0;reg[3:0]trace_index=0;
 function automatic[23:0]base(input[1:0]b);
 begin case(b)0:base=24'h100000;1:base=24'h100008;2:base=24'h1001f8;3:base=24'h100200;endcase end endfunction
 function automatic[15:0]pattern(input[1:0]b,input[2:0]n);
 pattern=16'h1000+({14'd0,b}<<12)+({13'd0,n}*16'h0101);
 endfunction
 genvar i;
 generate for(i=0;i<8;i=i+1)begin:word_pattern
  assign request_data[i*16+:16]=pattern(burst,i);
 end endgenerate
 assign request_valid=state==SEND_WRITE||state==SEND_READ;
 assign request_write=state==SEND_WRITE;assign request_address=base(burst);
 assign status={8'hd1,errors,reads,2'b00,state,trace_done,done,busy};
 assign counts={rejected,writes,8'd0,4'd0,timed_out,armed,request_ready,trace_started};
 always @(posedge clk)begin
  if(reset)begin
   state<=IDLE;busy<=0;done<=0;timed_out<=0;armed<=0;burst<=0;word_index<=0;
   errors<=0;reads<=0;writes<=0;rejected<=0;watchdog<=0;run_id<=0;
   first_address<=0;first_values<=0;raw_trace<=0;first_response<=0;response_mask<=0;
   tracing<=0;trace_started<=0;trace_done<=0;trace_index<=0;
  end else begin
   if(!go)armed<=1;
   if(observe_write_beat&&busy)writes<=writes+1'b1;
   if(busy)begin
    watchdog<=watchdog+1'b1;
    if(!trace_started&&observe_read_issue)begin
     trace_started<=1;tracing<=1;trace_index<=0;
     raw_trace[15:0]<=raw_read;response_mask[0]<=response_valid;
    end else if(tracing)begin
     raw_trace[(trace_index+1'b1)*16+:16]<=raw_read;
     response_mask[trace_index+1'b1]<=response_valid;
     trace_index<=trace_index+1'b1;
     if(trace_index==14)begin tracing<=0;trace_done<=1;end
    end
   end
   if(go&&armed)begin
    armed<=0;
    if(busy)rejected<=rejected+1'b1;
    else begin
     busy<=1;done<=0;timed_out<=0;burst<=0;word_index<=0;errors<=0;reads<=0;writes<=0;
     first_address<=0;first_values<=0;raw_trace<=0;first_response<=0;response_mask<=0;
     tracing<=0;trace_started<=0;trace_done<=0;trace_index<=0;watchdog<=0;
     run_id<=run_id+1'b1;state<=WAIT_READY;
    end
   end
   // Rejected start requests must not suppress an in-flight handshake.
   if(busy)begin
    case(state)
     WAIT_READY:if(request_ready)state<=SEND_WRITE;
     SEND_WRITE:if(request_ready)state<=WAIT_WRITE;
     WAIT_WRITE:if(request_ready)state<=SEND_READ;
     SEND_READ:if(request_ready)begin state<=COLLECT;word_index<=0;end
     COLLECT:if(response_valid)begin
      reads<=reads+1'b1;
      if(burst==0)first_response[word_index*16+:16]<=response_data;
      if(response_data!==pattern(burst,word_index))begin
       errors<=errors+1'b1;
       if(errors==0)begin first_address<=base(burst)+word_index;first_values<={pattern(burst,word_index),response_data};end
      end
      if(word_index==7)begin
       if(burst==3)begin busy<=0;done<=1;state<=IDLE;end
       else begin burst<=burst+1'b1;state<=WAIT_READY;end
      end else word_index<=word_index+1'b1;
     end
     default:begin timed_out<=1;busy<=0;done<=1;state<=IDLE;end
    endcase
    if(watchdog==99999)begin timed_out<=1;busy<=0;done<=1;state<=IDLE;end
   end
  end
 end
endmodule
