`timescale 1ns/1ps
// Scalar clients plus a bounded-priority, aligned BL8 scanout client.
// Reads and writes use BL8. No response acknowledges a
// write until controller recovery has completed. Cache tags are physical words.
module cu72_word_bridge (
 input logic clk,rst,
 input logic p0_valid,output logic p0_ready,input logic p0_write,input logic [23:0] p0_addr,input logic [15:0] p0_data,
 input logic p0_burst,input logic [127:0] p0_burst_data,input logic [15:0] p0_byte_enable,
 output logic p0_rsp_valid,input logic p0_rsp_ready,output logic [15:0] p0_rsp_data,output logic p0_rsp_error,
 input logic p1_valid,output logic p1_ready,input logic p1_write,input logic [23:0] p1_addr,input logic [15:0] p1_data,
 input logic p1_burst,input logic [127:0] p1_burst_data,input logic [15:0] p1_byte_enable,
 output logic p1_rsp_valid,input logic p1_rsp_ready,output logic [15:0] p1_rsp_data,output logic p1_rsp_error,
 input logic lcd_req_valid,output logic lcd_req_ready,input logic [23:0] lcd_req_addr,
 output logic lcd_rsp_valid,input logic lcd_rsp_ready,output logic [15:0] lcd_rsp_data,output logic lcd_rsp_last,lcd_rsp_error,
 output logic mem_req_valid,input logic mem_req_ready,output logic mem_req_write,output logic [23:0] mem_req_addr,output logic [127:0] mem_req_burst_data,output logic [15:0] mem_req_byte_enable,
 input logic mem_rsp_valid,input logic [15:0] mem_rsp_data,input logic mem_idle,
 output logic bridge_busy,lcd_busy,output logic [31:0] cache_hits,cache_misses,completed_reads,completed_writes
);
 `include "cu70_memory_map.svh"
 typedef enum logic [2:0] {IDLE,REQUEST,READ_BURST,WRITE_WAIT,RESPONSE,LCD_RESPONSE} state_t;
 state_t state;
 logic owner,prefer_one,writing,failed,lcd_owner,lcd_grace;
 logic [23:0] address;
 logic [15:0] rdata,write_mask;
 logic [127:0] write_data;
 logic [2:0] beat,lcd_streak;
 logic [3:0] lcd_received,lcd_delivered;
 logic p0_cache_valid;
 logic [20:0] p0_cache_tag;
 logic [15:0] p0_cache_data [0:7];
 logic [3:0] p1_cache_valid;
 logic [20:0] p1_cache_tag [0:3];
 logic [15:0] p1_cache_data [0:31];
 logic [1:0] p1_replace,fill_line,hit_line;
 logic [15:0] lcd_buffer [0:7];
 logic choose_one,choose_lcd,selected_write,selected_burst,selected_ok,p1_hit,lcd_address_ok;
 logic [23:0] selected_addr;
 logic [15:0] selected_data,selected_mask;
 logic [127:0] selected_burst_data;
 always_comb begin
  choose_one=p1_valid&&(!p0_valid||prefer_one);
  choose_lcd=lcd_req_valid&&(!(p0_valid||p1_valid)||lcd_streak<3'd4);
  selected_write=choose_one?p1_write:p0_write;
  selected_addr=choose_one?p1_addr:p0_addr;
  selected_data=choose_one?p1_data:p0_data;
  selected_burst=choose_one?p1_burst:p0_burst;
  selected_burst_data=choose_one?p1_burst_data:p0_burst_data;
  selected_mask=choose_one?p1_byte_enable:p0_byte_enable;
  selected_ok=map_word_allowed(selected_addr);
  if(selected_burst)begin
   selected_ok=selected_write&&selected_addr[2:0]==0&&selected_mask!=0;
   for(integer i=0;i<8;i=i+1)
    if((|selected_mask[2*i+:2])&&!map_word_allowed(selected_addr+24'(i)))selected_ok=0;
  end
  p1_hit=0;hit_line=0;
  for(integer i=0;i<4;i=i+1)begin
   if(p1_cache_valid[i]&&p1_cache_tag[i]==selected_addr[23:3])begin p1_hit=1;hit_line=2'(i);end
  end
  lcd_address_ok=lcd_req_addr[2:0]==0;
  for(integer i=0;i<8;i=i+1)begin
   if(!map_word_allowed(lcd_req_addr+24'(i)))lcd_address_ok=0;
  end
  p0_ready=state==IDLE&&!rst&&!choose_lcd&&!choose_one&&!(lcd_grace&&!lcd_req_valid&&lcd_streak<4);
  p1_ready=state==IDLE&&!rst&&!choose_lcd&&choose_one&&!(lcd_grace&&!lcd_req_valid&&lcd_streak<4);
  lcd_req_ready=state==IDLE&&!rst&&choose_lcd;
  p0_rsp_valid=state==RESPONSE&&!owner&&!rst;p1_rsp_valid=state==RESPONSE&&owner&&!rst;
  p0_rsp_data=rdata;p1_rsp_data=rdata;p0_rsp_error=failed;p1_rsp_error=failed;
  // Eight entries absorb the entire unbackpressured SDRAM burst. Delivery
  // starts as soon as one entry is available and stays stable under stalls.
  lcd_rsp_valid=lcd_owner&&(state==READ_BURST||state==LCD_RESPONSE)&&lcd_received>lcd_delivered&&!rst;
  lcd_rsp_data=lcd_buffer[lcd_delivered[2:0]];lcd_rsp_last=lcd_delivered==7;lcd_rsp_error=failed;
  mem_req_valid=state==REQUEST&&!rst;mem_req_write=writing;
  mem_req_addr={address[23:3],3'b000};mem_req_burst_data=write_data;mem_req_byte_enable=write_mask;
  bridge_busy=state!=IDLE;lcd_busy=state!=IDLE&&lcd_owner;
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=IDLE;owner<=0;prefer_one<=0;writing<=0;failed<=0;lcd_owner<=0;lcd_grace<=0;address<=0;write_data<=0;write_mask<=0;rdata<=0;beat<=0;lcd_streak<=0;lcd_received<=0;lcd_delivered<=0;
   p0_cache_valid<=0;p0_cache_tag<=0;p1_cache_valid<=0;p1_replace<=0;fill_line<=0;
   cache_hits<=0;cache_misses<=0;completed_reads<=0;completed_writes<=0;
   for(integer i=0;i<8;i=i+1)begin p0_cache_data[i]<=0;lcd_buffer[i]<=0;end
   for(integer i=0;i<4;i=i+1)p1_cache_tag[i]<=0;
   for(integer i=0;i<32;i=i+1)p1_cache_data[i]<=0;
  end else begin
   if(lcd_rsp_valid&&lcd_rsp_ready)lcd_delivered<=lcd_delivered+1'b1;
   case(state)
   IDLE:begin
    // One finite grace clock catches a one-clock request-adapter gap. The
    // fourth LCD grant never reserves grace while scalar service is due.
    lcd_grace<=0;
    if(lcd_req_valid&&lcd_req_ready)begin
    lcd_owner<=1;writing<=0;address<=lcd_req_addr;write_data<=0;write_mask<=0;beat<=0;failed<=!lcd_address_ok;lcd_received<=0;lcd_delivered<=0;
    if(lcd_streak<4)lcd_streak<=lcd_streak+1'b1;
    if(!lcd_address_ok)begin
     for(integer i=0;i<8;i=i+1)lcd_buffer[i]<=0;
     lcd_received<=8;state<=LCD_RESPONSE;
    end else state<=REQUEST;
   end else if((p0_valid&&p0_ready)||(p1_valid&&p1_ready))begin
    lcd_owner<=0;lcd_streak<=0;
    owner<=choose_one;prefer_one<=!choose_one;writing<=selected_write;address<=selected_addr;
    write_data<=selected_burst?selected_burst_data:(128'(selected_data)<<(16*int'(selected_addr[2:0])));
    write_mask<=selected_burst?selected_mask:(16'h0003<<(2*int'(selected_addr[2:0])));
    failed<=0;rdata<=0;
    if(!selected_ok)begin failed<=1;state<=RESPONSE;end
    else if(!selected_write&&((!choose_one&&p0_cache_valid&&p0_cache_tag==selected_addr[23:3])||(choose_one&&p1_hit)))begin
     rdata<=choose_one?p1_cache_data[{hit_line,selected_addr[2:0]}]:p0_cache_data[selected_addr[2:0]];
     state<=RESPONSE;cache_hits<=cache_hits+1;
    end else begin
     state<=REQUEST;
     if(!selected_write)begin
      cache_misses<=cache_misses+1;fill_line<=p1_replace;
      if(choose_one)p1_replace<=p1_replace+1'b1;
     end
     if(selected_write)begin
      if(p0_cache_valid&&p0_cache_tag==selected_addr[23:3])p0_cache_valid<=0;
      for(integer i=0;i<4;i=i+1)if(p1_cache_valid[i]&&p1_cache_tag[i]==selected_addr[23:3])p1_cache_valid[i]<=0;
     end
    end
   end
   end
   REQUEST:if(mem_req_valid&&mem_req_ready)begin
    beat<=0;
    if(writing)state<=WRITE_WAIT;
    else begin
     if(!lcd_owner)begin
      if(owner)p1_cache_valid[fill_line]<=0;else p0_cache_valid<=0;
     end
     state<=READ_BURST;
    end
   end
   READ_BURST:if(mem_rsp_valid)begin
    if(lcd_owner)begin
     lcd_buffer[beat]<=mem_rsp_data;lcd_received<=lcd_received+1'b1;
    end
    else if(owner)p1_cache_data[{fill_line,beat}]<=mem_rsp_data;
    else p0_cache_data[beat]<=mem_rsp_data;
    if(beat==address[2:0])rdata<=mem_rsp_data;
    if(beat==7)begin
     completed_reads<=completed_reads+1;beat<=0;
     if(lcd_owner)state<=LCD_RESPONSE;
     else begin
      if(owner)begin p1_cache_valid[fill_line]<=1;p1_cache_tag[fill_line]<=address[23:3];end
      else begin p0_cache_valid<=1;p0_cache_tag<=address[23:3];end
      state<=RESPONSE;
     end
    end else beat<=beat+1'b1;
   end
   WRITE_WAIT:if(mem_idle)begin state<=RESPONSE;completed_writes<=completed_writes+1;end
   RESPONSE:if(owner?p1_rsp_ready:p0_rsp_ready)state<=IDLE;
   LCD_RESPONSE:if(lcd_rsp_valid&&lcd_rsp_ready&&lcd_rsp_last)begin
    state<=IDLE;lcd_grace<=lcd_streak<4;
   end
   default:state<=IDLE;
   endcase
  end
 end
endmodule
