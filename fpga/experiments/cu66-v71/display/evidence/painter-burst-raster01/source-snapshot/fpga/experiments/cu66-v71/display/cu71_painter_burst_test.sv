// Optional v70 11520-byte RGB-strip candidate; baseline cu70_painter is frozen.
// Fixed 720x480 canonical YUV420/HUD -> native portrait RGB565 presentation.
// Word addresses are x16, canonical samples are packed low-byte first.
// One scalar memory operation outstanding. A write reply means visible/drained.
`timescale 1ns/1ps
module cu71_painter_burst_test (
    input logic clk,rst,abort_i,
    input logic start_valid,output logic start_ready,
    input logic [63:0] generation,
    input logic [31:0] frame_id,
    input logic [23:0] y_base,u_base,v_base,hud_base,rgb_base,
    output logic aux_req_valid,input logic aux_req_ready,
    output logic aux_req_write,
    output logic [23:0] aux_req_addr,
    output logic [15:0] aux_req_data,
    input logic aux_rsp_valid,output logic aux_rsp_ready,
    input logic [15:0] aux_rsp_data,input logic aux_rsp_error,
    output logic result_valid,input logic result_ready,
    output logic [63:0] result_generation,
    output logic [31:0] result_frame_id,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,
    output logic [31:0] memory_reads,memory_writes,painted_pixels,cycle_count
);

 logic p_req_valid,p_req_ready,p_req_write,p_rsp_valid,p_rsp_ready;
 logic[23:0]p_req_addr;logic[15:0]p_req_data;
 logic rgb_req_valid,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready,rgb_rsp_error,rgb_abort_i,rgb_busy,rgb_aborted;
 logic[23:0]rgb_req_addr;logic[127:0]rgb_req_data;logic[15:0]rgb_req_mask;
 logic active,word_pending,completion,aborting,read_pending,failed;
 logic[2:0]lane;logic[23:0]address;logic[127:0]payload;
 logic held_rgb;logic[23:0]held_address;logic[127:0]held_payload;
 logic[31:0]burst_count;
 // This verification-only adapter exposes every word of a burst to the
 // independent native raster scoreboard. A successful fence follows all8
 // replies; abort also drains the accepted burst before acknowledgment.
 assign rgb_req_ready=!active&&!read_pending&&aux_req_ready&&!rst;
 assign rgb_busy=active;
 assign rgb_rsp_valid=active&&completion&&!aborting&&!rgb_abort_i&&!rst;
 assign rgb_rsp_error=failed;
 assign p_req_ready=!active&&aux_req_ready&&!rst;
 assign p_rsp_valid=!active&&aux_rsp_valid;
 assign aux_req_valid=active?(!word_pending&&!completion&&!rst):p_req_valid;
 assign aux_req_write=active?1'b1:p_req_write;
 assign aux_req_addr=active?(address+24'(lane)):p_req_addr;
 assign aux_req_data=active?payload[16*lane+:16]:p_req_data;
 assign aux_rsp_ready=active?word_pending:p_rsp_ready;
 always_ff @(posedge clk)begin
  if(rst)begin active<=0;word_pending<=0;completion<=0;aborting<=0;read_pending<=0;failed<=0;lane<=0;address<=0;payload<=0;rgb_aborted<=0;held_rgb<=0;held_address<=0;held_payload<=0;burst_count<=0;end
  else begin
   rgb_aborted<=0;
   if(held_rgb&&!abort_i)begin
    if(!rgb_req_valid||rgb_req_addr!==held_address||rgb_req_data!==held_payload||rgb_req_mask!==0)$fatal(1,"held RGB burst changed");
   end
   held_rgb<=rgb_req_valid&&!rgb_req_ready&&!abort_i;
   held_address<=rgb_req_addr;held_payload<=rgb_req_data;
   if(p_req_valid&&p_req_ready)begin
    if(p_req_write||active)$fatal(1,"painter scalar port write/overlap");read_pending<=1;
   end
   if(p_rsp_valid&&p_rsp_ready)read_pending<=0;
   if(rgb_req_valid&&rgb_req_ready)begin
    if(rgb_req_addr[2:0]!=0||rgb_req_mask!=0||read_pending)$fatal(1,"RGB bounds/mask/ownership");
    active<=1;word_pending<=0;completion<=0;aborting<=0;failed<=0;lane<=0;address<=rgb_req_addr;payload<=rgb_req_data;burst_count<=burst_count+1;
   end
   if(active&&rgb_abort_i)aborting<=1;
   if(active&&aux_req_valid&&aux_req_ready)word_pending<=1;
   if(active&&aux_rsp_valid&&aux_rsp_ready)begin
    word_pending<=0;if(aux_rsp_error)failed<=1;
    if(lane==7)completion<=1;else lane<=lane+1'b1;
   end
   if(active&&completion)begin
    if(aborting||rgb_abort_i)begin active<=0;completion<=0;aborting<=0;rgb_aborted<=1;end
    else if(rgb_rsp_valid&&rgb_rsp_ready)begin active<=0;completion<=0;end
   end
  end
 end
 cu71_painter_strip_burst painter(
 .clk,.rst,.abort_i,.start_valid,.start_ready,.generation,.frame_id,.y_base,.u_base,.v_base,.hud_base,.rgb_base,
 .aux_req_valid(p_req_valid),.aux_req_ready(p_req_ready),.aux_req_write(p_req_write),.aux_req_addr(p_req_addr),.aux_req_data(p_req_data),
 .aux_rsp_valid(p_rsp_valid),.aux_rsp_ready(p_rsp_ready),.aux_rsp_data,.aux_rsp_error,
 .rgb_req_valid,.rgb_req_ready,.rgb_req_addr,.rgb_req_data,.rgb_req_mask,.rgb_rsp_valid,.rgb_rsp_ready,.rgb_rsp_error,.rgb_abort_i,.rgb_busy,.rgb_aborted,
 .result_valid,.result_ready,.result_generation,.result_frame_id,.busy,.done,.aborted,.error,.error_code,.memory_reads,.memory_writes,.painted_pixels,.cycle_count);
endmodule
