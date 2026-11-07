`timescale 1ns/1ps
// Isolated grouped8LCD:4BG scheduler. Original request/response/drain paths retained.
// Scalar writes are masked BL8; completion follows actual controller recovery.
module cu71_word_bridge_cache_v021 #(
 parameter integer LCD_BURSTS_PER_BACKGROUND=2,LCD_LOOKAHEAD_CYCLES=4,
 parameter integer LCD_GROUP_COMMANDS=8,BG_GROUP_COMMANDS=4,LCD_GROUP_GRACE=18,BG_GROUP_GRACE=4
)(
 input logic clk,rst,
 input logic p0_valid,output logic p0_ready,input logic p0_write,input logic[23:0]p0_addr,input logic[15:0]p0_data,
 input logic[127:0]p0_burst_data,input logic[15:0]p0_burst_mask,
 output logic p0_rsp_valid,input logic p0_rsp_ready,output logic[15:0]p0_rsp_data,output logic[127:0]p0_rsp_burst_data,output logic p0_rsp_error,
 input logic p1_valid,output logic p1_ready,input logic p1_write,input logic[23:0]p1_addr,input logic[15:0]p1_data,
 output logic p1_rsp_valid,input logic p1_rsp_ready,output logic[15:0]p1_rsp_data,output logic p1_rsp_error,
 input logic p2_valid,output logic p2_ready,input logic[23:0]p2_addr,
 output logic p2_rsp_valid,input logic p2_rsp_ready,output logic[127:0]p2_rsp_data,output logic p2_rsp_error,
 input logic p3_valid,output logic p3_ready,input logic[23:0]p3_addr,input logic[127:0]p3_data,input logic[15:0]p3_mask,
 output logic p3_rsp_valid,input logic p3_rsp_ready,output logic p3_rsp_error,
 output logic mem_req_valid,input logic mem_req_ready,output logic mem_req_write,output logic[23:0]mem_req_addr,
 output logic[127:0]mem_req_burst_data,output logic[15:0]mem_req_burst_mask,
 input logic mem_rsp_valid,input logic[15:0]mem_rsp_data,input logic mem_idle,
 output logic bridge_busy,output logic[31:0]cache_hits,cache_misses,completed_reads,completed_writes,
 output logic[31:0]lcd_completed_reads,lcd_max_wait,rgb_completed_writes,rgb_max_wait
);
 `include "cu70_memory_map.svh"
 typedef enum logic[1:0]{IDLE,REQUEST,READ_BURST,WRITE_WAIT}state_t;
 state_t state;
 logic[3:0]pending,response_valid,response_error,writing;
 logic[23:0]address[0:3];logic[15:0]wdata[0:3];logic[127:0]response_data[0:3];
 logic[127:0]canonical_burst_data,rgb_burst_data;logic[15:0]canonical_burst_mask,rgb_burst_mask;
 logic[31:0]wait_cycles[0:3];logic[1:0]owner,selected;
 logic[1:0]background_phase,background_selected;
 // Group quotas charge accepted controller commands, never local/cache replies.
 logic group_phase; //0=LCD,1=background
 logic[7:0]lcd_grants,bg_grants,lcd_grace,bg_grace;
 logic bg_reserved,local_turn;
 logic[1:0]bg_owner,local_selected,local_rr;
 logic[3:0]local_error,local_hit,local_pending,physical_pending;
 logic background_pending,physical_any,local_any,hold_for_lcd;
 logic[31:0]group_lcd_accepted,group_bg_accepted,group_reserved_idle;
 logic[31:0]group_lcd_reserved_idle,group_bg_reserved_idle,group_lcd_expiry,group_bg_expiry,group_uncharged;
 logic[31:0]group_bg_max_wait;

 logic[2:0]beat;logic[127:0]read_payload;
 logic[1:0]cache_valid;logic[20:0]cache_tag[0:1];logic[15:0]cache_data[0:15];
 function automatic logic rgb_block_allowed(input logic[23:0]addr);
  rgb_block_allowed=(addr>=RGB0_BASE&&{1'b0,addr}+25'd7<{1'b0,RGB0_BASE}+RGB0_WORDS)||
                    (addr>=RGB1_BASE&&{1'b0,addr}+25'd7<{1'b0,RGB1_BASE}+RGB1_WORDS);
 endfunction
 wire any_pending=|pending;
 function automatic logic bad_request(input integer k);
  bad_request=!map_word_allowed(address[k])||!map_word_allowed({address[k][23:3],3'b000})||
   !map_word_allowed({address[k][23:3],3'b111})||((k==2||k==3)&&address[k][2:0]!=0)||(k==3&&!rgb_block_allowed(address[k]));
 endfunction
 always_comb begin
  for(integer k=0;k<4;k=k+1)begin
   local_error[k]=pending[k]&&bad_request(k);
   local_hit[k]=pending[k]&&k==1&&!writing[k]&&cache_valid[1]&&cache_tag[1]==address[k][23:3]&&!local_error[k];
  end
  local_pending=local_error|local_hit;
  physical_pending=pending&~local_pending;
  physical_any=|physical_pending;local_any=|local_pending;
  local_selected=local_rr;
  for(integer n=3;n>=0;n=n-1)if(local_pending[(int'(local_rr)+n)&3])local_selected=2'((int'(local_rr)+n)&3);
  background_pending=physical_pending[0]||physical_pending[1]||physical_pending[3];
  case(background_phase)
   0:background_selected=physical_pending[0]?0:physical_pending[1]?1:3;
   1:background_selected=physical_pending[1]?1:physical_pending[3]?3:0;
   default:background_selected=physical_pending[3]?3:physical_pending[0]?0:1;
  endcase
  selected=2;hold_for_lcd=0;
  if(!group_phase)begin
   if(physical_pending[2])selected=2;
   else begin selected=background_selected;hold_for_lcd=background_pending&&lcd_grace!=0;end
  end else begin
   if(bg_reserved&&physical_pending[bg_owner])selected=bg_owner;
   else if(bg_reserved&&bg_grace!=0&&physical_any)begin selected=bg_owner;hold_for_lcd=1;end
   else selected=background_pending?background_selected:2;
  end
  p0_ready=!rst&&!pending[0]&&!response_valid[0]&&!(state!=IDLE&&owner==0);
  p1_ready=!rst&&!pending[1]&&!response_valid[1]&&!(state!=IDLE&&owner==1);
  p2_ready=!rst&&!pending[2]&&!response_valid[2]&&!(state!=IDLE&&owner==2);
  p3_ready=!rst&&!pending[3]&&!response_valid[3]&&!(state!=IDLE&&owner==3);
  p3_rsp_valid=response_valid[3]&&!rst;p3_rsp_error=response_error[3];
  p0_rsp_valid=response_valid[0]&&!rst;p1_rsp_valid=response_valid[1]&&!rst;p2_rsp_valid=response_valid[2]&&!rst;
  p0_rsp_burst_data=response_data[0];p0_rsp_data=response_data[0][15:0];p1_rsp_data=response_data[1][15:0];p2_rsp_data=response_data[2];
  p0_rsp_error=response_error[0];p1_rsp_error=response_error[1];p2_rsp_error=response_error[2];
  mem_req_valid=state==REQUEST&&!rst;mem_req_write=writing[owner];
  mem_req_addr={address[owner][23:3],3'b000};
  mem_req_burst_data=owner==0?canonical_burst_data:owner==3?rgb_burst_data:128'(wdata[owner])<<(address[owner][2:0]*16);
  mem_req_burst_mask=owner==0?canonical_burst_mask:owner==3?rgb_burst_mask:16'hffff^(16'h0003<<(address[owner][2:0]*2));
  bridge_busy=state!=IDLE||any_pending||(|response_valid);
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=IDLE;pending<=0;response_valid<=0;response_error<=0;writing<=0;owner<=0;background_phase<=0;lcd_grants<=0;bg_grants<=0;lcd_grace<=0;bg_grace<=0;group_phase<=0;bg_reserved<=0;bg_owner<=0;local_turn<=1;local_rr<=0;
   group_lcd_accepted<=0;group_bg_accepted<=0;group_reserved_idle<=0;group_lcd_reserved_idle<=0;group_bg_reserved_idle<=0;group_lcd_expiry<=0;group_bg_expiry<=0;group_uncharged<=0;group_bg_max_wait<=0;
   beat<=0;read_payload<=0;cache_valid<=0;cache_hits<=0;cache_misses<=0;completed_reads<=0;completed_writes<=0;
   lcd_completed_reads<=0;lcd_max_wait<=0;rgb_completed_writes<=0;rgb_max_wait<=0;rgb_burst_data<=0;rgb_burst_mask<=16'hffff;
   canonical_burst_data<=0;canonical_burst_mask<=16'hffff;
   for(integer i=0;i<4;i=i+1)begin address[i]<=0;wdata[i]<=0;response_data[i]<=0;wait_cycles[i]<=0;end
   // Cache data has no reset; valid/tag ownership makes uninitialized bits unreachable.
   cache_tag[0]<=0;cache_tag[1]<=0;
  end else begin
   if(lcd_grace!=0)lcd_grace<=lcd_grace-1;
   if(bg_grace!=0)bg_grace<=bg_grace-1;
   if(lcd_grace==1&&!physical_pending[2]&&background_pending)group_lcd_expiry<=group_lcd_expiry+1;
   if(bg_grace==1&&bg_reserved&&!physical_pending[bg_owner]&&physical_any)group_bg_expiry<=group_bg_expiry+1;
   if(state==IDLE&&physical_any&&hold_for_lcd&&!(local_any&&local_turn))begin
    group_reserved_idle<=group_reserved_idle+1;
    if(group_phase)group_bg_reserved_idle<=group_bg_reserved_idle+1;else group_lcd_reserved_idle<=group_lcd_reserved_idle+1;
   end
   if(p3_rsp_valid&&p3_rsp_ready)response_valid[3]<=0;
   if(p0_rsp_valid&&p0_rsp_ready)response_valid[0]<=0;
   if(p1_rsp_valid&&p1_rsp_ready)response_valid[1]<=0;
   if(p2_rsp_valid&&p2_rsp_ready)response_valid[2]<=0;
   for(integer i=0;i<4;i=i+1)if(pending[i]||(state!=IDLE&&owner==i))wait_cycles[i]<=wait_cycles[i]+1;
   if(p0_valid&&p0_ready)begin pending[0]<=1;address[0]<=p0_addr;wdata[0]<=p0_data;writing[0]<=p0_write;wait_cycles[0]<=0;canonical_burst_data<=p0_burst_data;canonical_burst_mask<=p0_burst_mask;end
   if(p1_valid&&p1_ready)begin pending[1]<=1;address[1]<=p1_addr;wdata[1]<=p1_data;writing[1]<=p1_write;wait_cycles[1]<=0;end
   if(p2_valid&&p2_ready)begin pending[2]<=1;address[2]<=p2_addr;wdata[2]<=0;writing[2]<=0;wait_cycles[2]<=0;end
   if(p3_valid&&p3_ready)begin pending[3]<=1;address[3]<=p3_addr;wdata[3]<=0;writing[3]<=1;wait_cycles[3]<=0;rgb_burst_data<=p3_data;rgb_burst_mask<=p3_mask;end
   case(state)
    IDLE:begin
     // At most one uncharged local reply before an eligible physical command.
     // Local traffic cannot hold a quota open forever or extend its grace.
     if(local_any&&(local_turn||!physical_any))begin
      pending[local_selected]<=0;response_error[local_selected]<=local_error[local_selected];
      response_valid[local_selected]<=1;group_uncharged<=group_uncharged+1;
      local_rr<=local_selected+2'd1;local_turn<=0;
      if(local_error[local_selected])response_data[local_selected]<=0;
      else begin response_data[1]<={112'd0,cache_data[{1'b1,address[1][2:0]}]};cache_hits<=cache_hits+1;end
     end else if(physical_any&&!hold_for_lcd)begin
      pending[selected]<=0;owner<=selected;response_error[selected]<=0;state<=REQUEST;local_turn<=1;
      if(!writing[selected])cache_misses<=cache_misses+1;
      if(writing[selected])for(integer i=0;i<2;i=i+1)if(cache_valid[i]&&cache_tag[i]==address[selected][23:3])cache_valid[i]<=0;
     end
    end
    REQUEST:if(mem_req_valid&&mem_req_ready)begin
     beat<=0;read_payload<=0;state<=writing[owner]?WRITE_WAIT:READ_BURST;
     if(owner==2)begin
      group_lcd_accepted<=group_lcd_accepted+1;bg_grants<=0;bg_grace<=0;bg_reserved<=0;
      if(!group_phase&&lcd_grants+1>=LCD_GROUP_COMMANDS)begin group_phase<=1;lcd_grants<=0;lcd_grace<=0;end
      else begin group_phase<=0;lcd_grants<=group_phase?8'd1:lcd_grants+1;end
     end else begin
      group_bg_accepted<=group_bg_accepted+1;lcd_grants<=0;lcd_grace<=0;
      background_phase<=owner==0?1:owner==1?2:0;
      if(group_phase&&bg_grants+1>=BG_GROUP_COMMANDS)begin group_phase<=0;bg_grants<=0;bg_reserved<=0;bg_grace<=0;end
      else begin group_phase<=1;bg_grants<=group_phase?bg_grants+1:8'd1;bg_reserved<=1;bg_owner<=owner;end
     end
    end
    READ_BURST:if(mem_rsp_valid)begin
     read_payload[beat*16+:16]<=mem_rsp_data;
     if(owner==1)cache_data[owner*8+beat]<=mem_rsp_data;
     if(beat==7)begin
      if(owner==0)begin
       response_data[0]<={mem_rsp_data,read_payload[111:0]};
      end else if(owner==1)begin
       cache_valid[owner]<=1;cache_tag[owner]<=address[owner][23:3];
       response_data[owner]<={112'd0,address[owner][2:0]==7?mem_rsp_data:read_payload[address[owner][2:0]*16+:16]};
      end else begin
       response_data[2]<={mem_rsp_data,read_payload[111:0]};lcd_completed_reads<=lcd_completed_reads+1;
       if(!group_phase&&lcd_grants!=0)lcd_grace<=8'(LCD_GROUP_GRACE);
       if(wait_cycles[2]>lcd_max_wait)lcd_max_wait<=wait_cycles[2];
      end
      response_valid[owner]<=1;completed_reads<=completed_reads+1;state<=IDLE;
      if(owner!=2)begin
       if(wait_cycles[owner]>group_bg_max_wait)group_bg_max_wait<=wait_cycles[owner];
       if(group_phase&&bg_grants!=0)bg_grace<=8'(BG_GROUP_GRACE);
      end
     end else beat<=beat+1;
    end
    WRITE_WAIT:if(mem_idle)begin
     response_data[owner]<=0;response_valid[owner]<=1;completed_writes<=completed_writes+1;state<=IDLE;
     if(wait_cycles[owner]>group_bg_max_wait)group_bg_max_wait<=wait_cycles[owner];
     if(group_phase&&bg_grants!=0)bg_grace<=8'(BG_GROUP_GRACE);
     if(owner==3)begin rgb_completed_writes<=rgb_completed_writes+1;if(wait_cycles[3]>rgb_max_wait)rgb_max_wait<=wait_cycles[3];end
     for(integer i=0;i<2;i=i+1)if(cache_valid[i]&&cache_tag[i]==address[owner][23:3])cache_valid[i]<=0;
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
