// One tagged internal cache-fill command per BL8. The scheduler can switch
// between front refill and provisional preparation at every completed burst.
`timescale 1ns/1ps
`default_nettype none
module cu71_cache_dma(
 input wire clk,rst,
 input wire cmd_valid,output wire cmd_ready,
 input wire[63:0]cmd_generation,input wire[31:0]cmd_frame_id,cmd_cookie,
 input wire cmd_context,cmd_bank,input wire[1:0]cmd_kind,
 input wire[23:0]cmd_source,input wire[8:0]cmd_row,input wire[14:0]cmd_hud_index,
 output wire result_valid,input wire result_ready,
 output reg[63:0]result_generation,output reg[31:0]result_frame_id,result_cookie,
 output reg result_context,result_error,result_aborted,output reg[7:0]result_reason,
 input wire abort_valid,output wire abort_ready,
 input wire[63:0]abort_generation,input wire[31:0]abort_frame_id,input wire abort_context,
 output reg abort_rejected,
 output wire lcd_req_valid,input wire lcd_req_ready,output wire[23:0]lcd_req_addr,
 input wire lcd_rsp_valid,output wire lcd_rsp_ready,input wire[127:0]lcd_rsp_data,input wire lcd_rsp_error,
 output wire lcd_abort_i,input wire lcd_busy,lcd_aborted,
 output wire cache_wr_valid,output wire cache_wr_context,cache_wr_bank,
 output wire[1:0]cache_wr_kind,output wire[8:0]cache_wr_row,
 output wire[63:0]cache_wr_data,output wire[14:0]cache_wr_hud_index,
 output wire[15:0]cache_wr_hud_word,input wire cache_wr_error,
 output reg[31:0]accepted_commands,accepted_reads,completed_commands,aborted_commands,unowned_responses,
 output reg[7:0]first_fault,output reg[63:0]fault_generation,
 output reg[31:0]fault_frame_id,fault_cookie,output reg[23:0]fault_source,
 output wire busy
);
 `include "cu70_memory_map.svh"
 localparam[2:0]IDLE=0,REQUEST=1,RESPONSE=2,WRITE_CACHE=3,CHECK_CACHE=4,DRAIN=5,RESULT=6;
 reg[2:0]state;
 reg pending,aborting,kind_hud,bank;
 reg[1:0]kind;
 reg[23:0]source;
 reg[8:0]row;
 reg[14:0]hud_index;
 reg[127:0]payload;
 reg[2:0]word_index;
 wire abort_match=abort_valid&&state!=IDLE&&abort_generation==result_generation&&abort_frame_id==result_frame_id&&abort_context==result_context;
 assign abort_ready=abort_match&&!rst;
 assign busy=state!=IDLE;
 assign cmd_ready=state==IDLE&&!lcd_busy&&!lcd_rsp_valid&&!rst&&!abort_valid;
 assign result_valid=state==RESULT&&!rst&&!abort_match;
 assign lcd_req_valid=state==REQUEST&&!rst&&!abort_match&&!lcd_rsp_valid;
 assign lcd_req_addr=source;
 // Drain unexpected/unowned replies as faults. Never map them into a cache.
 assign lcd_rsp_ready=!rst;
 assign lcd_abort_i=pending&&(aborting||abort_match)&&!rst;
 assign cache_wr_valid=state==WRITE_CACHE&&!rst&&!aborting&&!abort_match;
 assign cache_wr_context=result_context;assign cache_wr_bank=bank;assign cache_wr_kind=kind;
 assign cache_wr_row=row+9'(word_index);
 assign cache_wr_data=word_index[0]?payload[127:64]:payload[63:0];
 assign cache_wr_hud_index=hud_index+15'(word_index);
 assign cache_wr_hud_word=payload[16*word_index+:16];
 function automatic source_ok(input[1:0]k,input[23:0]address);
  reg yes;reg[24:0]last;
  begin
   yes=0;last={1'b0,address}+25'd7;
   if(k==3)begin
    if(address>=HUD0_BASE&&last<{1'b0,HUD0_BASE}+HUD0_WORDS)yes=1;
    if(address>=HUD1_BASE&&last<{1'b0,HUD1_BASE}+HUD1_WORDS)yes=1;
    if(address>=HUD2_BASE&&last<{1'b0,HUD2_BASE}+HUD2_WORDS)yes=1;
   end else begin
    if(address>=CANONICAL0_BASE&&last<{1'b0,CANONICAL0_BASE}+CANONICAL0_WORDS)yes=1;
    if(address>=CANONICAL1_BASE&&last<{1'b0,CANONICAL1_BASE}+CANONICAL1_WORDS)yes=1;
    if(address>=CANONICAL2_BASE&&last<{1'b0,CANONICAL2_BASE}+CANONICAL2_WORDS)yes=1;
   end
   source_ok=yes&&address[2:0]==0;
  end
 endfunction
 wire bad_command=cmd_generation==0||cmd_frame_id==32'hffffffff||!source_ok(cmd_kind,cmd_source)||
   (cmd_kind==0&&(cmd_row>=479||cmd_row[0]))||
   ((cmd_kind==1||cmd_kind==2)&&(cmd_row>=239||cmd_row[0]))||
   (cmd_kind==3&&(cmd_hud_index>21112||cmd_hud_index[2:0]!=0));
 task automatic fault(input[7:0]reason);
  begin
   result_error<=1;result_reason<=reason;state<=DRAIN;
   if(first_fault==0)begin first_fault<=reason;fault_generation<=result_generation;fault_frame_id<=result_frame_id;fault_cookie<=result_cookie;fault_source<=source;end
  end
 endtask
 always @(posedge clk)begin
  if(rst)begin
   state<=IDLE;pending<=0;aborting<=0;kind_hud<=0;kind<=0;bank<=0;source<=0;row<=0;hud_index<=0;word_index<=0;
   result_generation<=0;result_frame_id<=0;result_cookie<=0;result_context<=0;result_error<=0;result_aborted<=0;result_reason<=0;abort_rejected<=0;
   accepted_commands<=0;accepted_reads<=0;completed_commands<=0;aborted_commands<=0;unowned_responses<=0;first_fault<=0;
   fault_generation<=0;fault_frame_id<=0;fault_cookie<=0;fault_source<=0;
  end else begin
   abort_rejected<=abort_valid&&!abort_match;
   if(abort_match)begin aborting<=1;result_aborted<=1;state<=DRAIN;end
   else case(state)
    IDLE:if(cmd_valid&&cmd_ready)begin
     accepted_commands<=accepted_commands+1;result_generation<=cmd_generation;result_frame_id<=cmd_frame_id;result_cookie<=cmd_cookie;result_context<=cmd_context;
     result_error<=0;result_aborted<=0;result_reason<=0;aborting<=0;
     kind<=cmd_kind;kind_hud<=cmd_kind==3;bank<=cmd_bank;source<=cmd_source;row<=cmd_row;hud_index<=cmd_hud_index;word_index<=0;
     if(bad_command)begin
      result_error<=1;result_reason<=1;state<=DRAIN;
      if(first_fault==0)begin first_fault<=1;fault_generation<=cmd_generation;fault_frame_id<=cmd_frame_id;fault_cookie<=cmd_cookie;fault_source<=cmd_source;end
     end else state<=REQUEST;
    end
    REQUEST:if(lcd_req_valid&&lcd_req_ready)begin pending<=1;accepted_reads<=accepted_reads+1;state<=RESPONSE;end
    RESPONSE:if(lcd_rsp_valid&&lcd_rsp_ready&&pending)begin
     pending<=0;
     if(lcd_rsp_error)fault(2);
     else begin payload<=lcd_rsp_data;word_index<=0;state<=WRITE_CACHE;end
    end
    WRITE_CACHE:begin
     if(cache_wr_error)fault(6);
     else if((kind_hud&&word_index==7)||(!kind_hud&&word_index==1))state<=CHECK_CACHE;
     else word_index<=word_index+1'b1;
    end
    CHECK_CACHE:if(cache_wr_error)fault(6);else state<=DRAIN;
    DRAIN:if(!pending&&!lcd_busy)begin state<=RESULT;end
    RESULT:if(result_valid&&result_ready)begin
     if(result_aborted)aborted_commands<=aborted_commands+1;
     else if(!result_error)completed_commands<=completed_commands+1;
     state<=IDLE;
    end
    default:fault(7);
   endcase
   // Matching abort can coincide with completion. Consume/discard that
   // completion, retain the owned identity, then wait for busy to clear.
   if(lcd_rsp_valid&&lcd_rsp_ready)begin
    if(!pending)begin unowned_responses<=unowned_responses+1;fault(3);end
    else if(state==DRAIN||aborting||abort_match)pending<=0;
   end
   if(lcd_aborted)begin
    if(aborting||abort_match)pending<=0;
    else if(pending)begin pending<=0;fault(4);end
    else if(state!=IDLE)fault(4);
   end
  end
 end
endmodule
`default_nettype wire
