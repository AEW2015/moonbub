`timescale 1ns/1ps
// Two-client checked x16 word API over read-BL8/write-single controller.
// One eight-word read cache per client; any aliasing write invalidates both.
module cu70_word_bridge (
 input logic clk,rst,
 input logic p0_valid,output logic p0_ready,input logic p0_write,input logic [23:0] p0_addr,input logic [15:0] p0_data,
 output logic p0_rsp_valid,input logic p0_rsp_ready,output logic [15:0] p0_rsp_data,output logic p0_rsp_error,
 input logic p1_valid,output logic p1_ready,input logic p1_write,input logic [23:0] p1_addr,input logic [15:0] p1_data,
 output logic p1_rsp_valid,input logic p1_rsp_ready,output logic [15:0] p1_rsp_data,output logic p1_rsp_error,
 output logic mem_req_valid,input logic mem_req_ready,output logic mem_req_write,output logic [23:0] mem_req_addr,output logic [15:0] mem_req_data,
 input logic mem_rsp_valid,input logic [15:0] mem_rsp_data,input logic mem_idle,
 output logic bridge_busy,output logic [31:0] cache_hits,cache_misses,completed_reads,completed_writes
);
 `include "cu70_memory_map.svh"
 typedef enum logic [2:0] {IDLE,REQUEST,READ_BURST,WRITE_WAIT,RESPONSE} state_t;
 state_t state;
 logic owner,prefer_one,writing,failed;
 logic [23:0] address;
 logic [15:0] wdata,rdata;
 logic [2:0] beat;
 logic [1:0] cache_valid;
 logic [20:0] cache_tag [0:1];
 logic [15:0] cache_data [0:15];
 logic choose_one,selected_write;
 logic [23:0] selected_addr;
 logic [15:0] selected_data;
 always_comb begin
  choose_one=p1_valid&&(!p0_valid||prefer_one);
  selected_write=choose_one?p1_write:p0_write;
  selected_addr=choose_one?p1_addr:p0_addr;
  selected_data=choose_one?p1_data:p0_data;
  p0_ready=state==IDLE&&!rst&&!choose_one;p1_ready=state==IDLE&&!rst&&choose_one;
  p0_rsp_valid=state==RESPONSE&&!owner&&!rst;p1_rsp_valid=state==RESPONSE&&owner&&!rst;
  p0_rsp_data=rdata;p1_rsp_data=rdata;p0_rsp_error=failed;p1_rsp_error=failed;
  mem_req_valid=state==REQUEST&&!rst;mem_req_write=writing;
  mem_req_addr=writing?address:{address[23:3],3'b000};mem_req_data=wdata;
  bridge_busy=state!=IDLE;
 end
 always_ff @(posedge clk)begin
  if(rst)begin state<=IDLE;owner<=0;prefer_one<=0;writing<=0;failed<=0;address<=0;wdata<=0;rdata<=0;beat<=0;cache_valid<=0;
   cache_tag[0]<=0;cache_tag[1]<=0;cache_hits<=0;cache_misses<=0;completed_reads<=0;completed_writes<=0;
   for(integer i=0;i<16;i=i+1)cache_data[i]<=0;
  end else case(state)
   IDLE:if((p0_valid&&p0_ready)||(p1_valid&&p1_ready))begin
    owner<=choose_one;prefer_one<=!choose_one;writing<=selected_write;address<=selected_addr;wdata<=selected_data;failed<=0;rdata<=0;
    if(!map_word_allowed(selected_addr))begin failed<=1;state<=RESPONSE;end
    else if(!selected_write&&cache_valid[choose_one]&&cache_tag[choose_one]==selected_addr[23:3])begin
     rdata<=cache_data[{choose_one,selected_addr[2:0]}];state<=RESPONSE;cache_hits<=cache_hits+1;
    end else begin
     state<=REQUEST;
     if(!selected_write)cache_misses<=cache_misses+1;
     if(selected_write)for(integer i=0;i<2;i=i+1)if(cache_valid[i]&&cache_tag[i]==selected_addr[23:3])cache_valid[i]<=0;
    end
   end
   REQUEST:if(mem_req_valid&&mem_req_ready)begin
    beat<=0;
    if(writing)state<=WRITE_WAIT;
    else begin cache_valid[owner]<=0;state<=READ_BURST;end
   end
   READ_BURST:if(mem_rsp_valid)begin
    cache_data[{owner,beat}]<=mem_rsp_data;
    if(beat==address[2:0])rdata<=mem_rsp_data;
    if(beat==7)begin cache_valid[owner]<=1;cache_tag[owner]<=address[23:3];state<=RESPONSE;completed_reads<=completed_reads+1;end
    else beat<=beat+1;
   end
   WRITE_WAIT:if(mem_idle)begin state<=RESPONSE;completed_writes<=completed_writes+1;end
   RESPONSE:if(owner?p1_rsp_ready:p0_rsp_ready)state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
