// Cache -> elastic converter integration, one core clock; no pixel-clock CDC.
module cu77_render_sim (
 input logic clk,rst,abort_i,
 input logic desc_valid,output logic desc_ready,
 input logic [63:0] desc_generation,input logic [31:0] desc_frame_id,input logic [1:0] desc_bank,
 input logic finish_valid,output logic finish_ready,
 output logic active,aborted,error,output logic [7:0] error_code,
 output logic [63:0] active_generation,output logic [31:0] active_frame_id,
 input logic prefetch_valid,output logic prefetch_ready,input logic [6:0] prefetch_index,
 output logic prefetch_done_valid,input logic prefetch_done_ready,output logic [6:0] prefetch_done_index,
 input logic consume_valid,output logic consume_ready,input logic [6:0] consume_index,
 output logic [6:0] prefetched_count,consumed_count,
 output logic mem_req_valid,input logic mem_req_ready,output logic [23:0] mem_req_addr,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [15:0] mem_rsp_data,
 input logic mem_rsp_last,mem_rsp_error,
 input logic pixel_req_valid,output logic pixel_req_ready,input logic [9:0] pixel_u,input logic [8:0] pixel_v,
 output logic rgb_valid,input logic rgb_ready,output logic [9:0] rgb_u,output logic [8:0] rgb_v,
 output logic [15:0] rgb_data,output logic rgb_error,
 output logic [31:0] read_commands,read_words,pixel_queries,cache_misses,
 output logic [3:0] pixel_inflight
);
 logic cache_desc_ready,cache_finish_ready,cache_consume_ready,cache_pixel_ready;
 logic px_valid,px_ready,px_error,px_hud_hit;logic[9:0]px_u;logic[8:0]px_v;
 logic[7:0]px_y,cb00,cb10,cb01,cb11,cr00,cr10,cr01,cr11;logic[15:0]px_hud;
 logic pipe_empty,request_fire,response_fire;
 assign pipe_empty=pixel_inflight==0;
 assign desc_ready=cache_desc_ready&&pipe_empty;
 assign finish_ready=cache_finish_ready&&pipe_empty;
 assign consume_ready=cache_consume_ready&&pipe_empty;
 assign pixel_req_ready=cache_pixel_ready&&!finish_valid;
 assign request_fire=pixel_req_valid&&pixel_req_ready;
 assign response_fire=rgb_valid&&rgb_ready;
 always_ff @(posedge clk)begin
  if(rst||abort_i)pixel_inflight<=0;
  else case({request_fire,response_fire})
   2'b10:pixel_inflight<=pixel_inflight+1'b1;
   2'b01:pixel_inflight<=pixel_inflight-1'b1;
   default:begin end
  endcase
 end
 cu77_direct_cache cache(
  .clk,.rst,.abort_i,.desc_valid(desc_valid&&pipe_empty),.desc_ready(cache_desc_ready),.desc_generation,.desc_frame_id,.desc_bank,
  .finish_valid(finish_valid&&pipe_empty),.finish_ready(cache_finish_ready),.active,.aborted,.error,.error_code,.active_generation,.active_frame_id,
  .prefetch_valid,.prefetch_ready,.prefetch_index,.prefetch_done_valid,.prefetch_done_ready,.prefetch_done_index,
  .consume_valid(consume_valid&&pipe_empty),.consume_ready(cache_consume_ready),.consume_index,.prefetched_count,.consumed_count,
  .mem_req_valid,.mem_req_ready,.mem_req_addr,.mem_rsp_valid,.mem_rsp_ready,.mem_rsp_data,.mem_rsp_last,.mem_rsp_error,
  .pixel_req_valid(pixel_req_valid&&!finish_valid),.pixel_req_ready(cache_pixel_ready),.pixel_u,.pixel_v,
  .pixel_rsp_valid(px_valid),.pixel_rsp_ready(px_ready),.pixel_rsp_u(px_u),.pixel_rsp_v(px_v),
  .pixel_y(px_y),.cb00,.cb10,.cb01,.cb11,.cr00,.cr10,.cr01,.cr11,.pixel_hud_hit(px_hud_hit),.pixel_hud(px_hud),.pixel_rsp_error(px_error),
  .read_commands,.read_words,.pixel_queries,.cache_misses);
 cu77_yuv_rgb converter(
  .clk,.rst,.abort_i,.in_valid(px_valid),.in_ready(px_ready),.in_u(px_u),.in_v(px_v),.in_y(px_y),
  .in_cb00(cb00),.in_cb10(cb10),.in_cb01(cb01),.in_cb11(cb11),.in_cr00(cr00),.in_cr10(cr10),.in_cr01(cr01),.in_cr11(cr11),
  .in_hud_hit(px_hud_hit),.in_hud(px_hud),.in_error(px_error),
  .out_valid(rgb_valid),.out_ready(rgb_ready),.out_u(rgb_u),.out_v(rgb_v),.out_rgb(rgb_data),.out_error(rgb_error));
endmodule
